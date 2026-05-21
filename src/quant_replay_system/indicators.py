"""Point-in-time-safe technical indicators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from quant_replay_system.data import filter_available_records


@dataclass(frozen=True)
class TechnicalIndicatorConfig:
    ma_windows: tuple[int, ...] = (5, 10, 20, 60)
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    rsi_period: int = 14
    atr_period: int = 14
    volume_windows: tuple[int, ...] = (5, 10, 20)
    relative_strength_windows: tuple[int, ...] = (5, 10, 20)


def compute_technical_indicators(
    df: pd.DataFrame,
    decision_time: str | pd.Timestamp | None = None,
    benchmark_df: pd.DataFrame | None = None,
    config: TechnicalIndicatorConfig | None = None,
) -> pd.DataFrame:
    """Compute technical indicators without using records unavailable at decision_time.

    The input frame is copied. When decision_time is provided, this function
    reuses the project point-in-time availability filter before any indicator
    calculations are performed.
    """

    cfg = config or TechnicalIndicatorConfig()
    frame = filter_available_records(df, decision_time) if decision_time is not None else df.copy()
    _require_columns(frame, ["symbol", "trade_date", "open", "high", "low", "close", "volume"])

    frame = _prepare_market_frame(frame)
    pieces = [_compute_symbol_indicators(group, cfg) for _, group in frame.groupby("symbol", sort=False)]
    result = pd.concat(pieces, ignore_index=True) if pieces else frame.copy()

    if benchmark_df is not None:
        result = _add_relative_strength(result, benchmark_df, decision_time, cfg)

    return result.sort_values(["symbol", "trade_date"]).reset_index(drop=True)


def compute_technical_score(indicator_df: pd.DataFrame) -> pd.DataFrame:
    """Add a simple optional TechnicalScore v0.1 without changing final scoring."""

    frame = indicator_df.copy()
    _require_columns(frame, ["close", "ma5", "ma20", "volume_ratio_20", "rsi_14"])

    frame["technical_score_v01"] = 0.0
    frame["technical_close_above_ma20"] = frame["close"] > frame["ma20"]
    frame["technical_ma5_above_ma20"] = frame["ma5"] > frame["ma20"]
    frame["technical_volume_expansion"] = frame["volume_ratio_20"] > 1.2
    frame["technical_rsi_overheated"] = frame["rsi_14"] > 80
    frame["technical_close_below_ma20"] = frame["close"] < frame["ma20"]

    frame.loc[frame["technical_close_above_ma20"], "technical_score_v01"] += 1.0
    frame.loc[frame["technical_ma5_above_ma20"], "technical_score_v01"] += 1.0
    frame.loc[frame["technical_volume_expansion"], "technical_score_v01"] += 1.0
    frame.loc[frame["technical_rsi_overheated"], "technical_score_v01"] -= 1.0
    frame.loc[frame["technical_close_below_ma20"], "technical_score_v01"] -= 1.0
    return frame


def _compute_symbol_indicators(group: pd.DataFrame, config: TechnicalIndicatorConfig) -> pd.DataFrame:
    frame = group.sort_values("trade_date").copy()

    for window in config.ma_windows:
        frame[f"ma{window}"] = frame["close"].rolling(window=window, min_periods=window).mean()

    ema_fast = frame["close"].ewm(span=config.macd_fast, adjust=False).mean()
    ema_slow = frame["close"].ewm(span=config.macd_slow, adjust=False).mean()
    frame["macd_dif"] = ema_fast - ema_slow
    frame["macd_dea"] = frame["macd_dif"].ewm(span=config.macd_signal, adjust=False).mean()
    frame["macd_histogram"] = frame["macd_dif"] - frame["macd_dea"]

    frame[f"rsi_{config.rsi_period}"] = _compute_rsi(frame["close"], config.rsi_period)
    frame[f"atr_{config.atr_period}"] = _compute_atr(frame, config.atr_period)

    for window in config.volume_windows:
        frame[f"volume_ma{window}"] = frame["volume"].rolling(window=window, min_periods=window).mean()
    frame["volume_ratio_20"] = frame["volume"] / frame["volume_ma20"]

    for window in config.relative_strength_windows:
        frame[f"return_{window}d"] = frame["close"] / frame["close"].shift(window) - 1.0

    return frame


def _compute_rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi = rsi.mask((avg_loss == 0) & (avg_gain > 0), 100.0)
    rsi = rsi.mask((avg_loss == 0) & (avg_gain == 0), 50.0)
    return rsi.clip(lower=0.0, upper=100.0)


def _compute_atr(frame: pd.DataFrame, period: int) -> pd.Series:
    previous_close = frame["close"].shift(1)
    if "pre_close" in frame.columns:
        previous_close = previous_close.fillna(frame["pre_close"])

    true_range = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous_close).abs(),
            (frame["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.rolling(window=period, min_periods=period).mean().clip(lower=0.0)


def _add_relative_strength(
    indicator_frame: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    decision_time: str | pd.Timestamp | None,
    config: TechnicalIndicatorConfig,
) -> pd.DataFrame:
    benchmark = filter_available_records(benchmark_df, decision_time) if decision_time is not None else benchmark_df.copy()
    _require_columns(benchmark, ["trade_date", "close"])
    benchmark = _prepare_benchmark_frame(benchmark)

    for window in config.relative_strength_windows:
        benchmark[f"benchmark_return_{window}d"] = benchmark["close"] / benchmark["close"].shift(window) - 1.0

    columns = ["trade_date", *[f"benchmark_return_{window}d" for window in config.relative_strength_windows]]
    merged = indicator_frame.merge(benchmark[columns], on="trade_date", how="left")
    for window in config.relative_strength_windows:
        merged[f"relative_return_{window}d"] = merged[f"return_{window}d"] - merged[f"benchmark_return_{window}d"]
    return merged


def _prepare_market_frame(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy()
    prepared["trade_date"] = pd.to_datetime(prepared["trade_date"], errors="coerce").dt.normalize()
    if prepared["trade_date"].isna().any():
        raise ValueError("trade_date contains missing or invalid dates")

    for column in ["open", "high", "low", "close", "volume", "amount", "pre_close"]:
        if column in prepared.columns:
            prepared[column] = pd.to_numeric(prepared[column], errors="coerce")

    sort_columns = ["symbol", "trade_date"]
    for optional_column in ["available_time", "revision_id"]:
        if optional_column in prepared.columns:
            sort_columns.append(optional_column)
    return prepared.sort_values(sort_columns).reset_index(drop=True)


def _prepare_benchmark_frame(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy()
    prepared["trade_date"] = pd.to_datetime(prepared["trade_date"], errors="coerce").dt.normalize()
    if prepared["trade_date"].isna().any():
        raise ValueError("benchmark trade_date contains missing or invalid dates")

    prepared["close"] = pd.to_numeric(prepared["close"], errors="coerce")
    sort_columns = ["trade_date"]
    if "symbol" in prepared.columns:
        sort_columns.insert(0, "symbol")
    for optional_column in ["available_time", "revision_id"]:
        if optional_column in prepared.columns:
            sort_columns.append(optional_column)

    prepared = prepared.sort_values(sort_columns)
    if "symbol" in prepared.columns and prepared["symbol"].nunique(dropna=True) > 1:
        first_symbol = sorted(prepared["symbol"].dropna().unique())[0]
        prepared = prepared.loc[prepared["symbol"] == first_symbol].copy()
    return prepared.drop_duplicates(subset=["trade_date"], keep="last").sort_values("trade_date").reset_index(drop=True)


def _require_columns(frame: pd.DataFrame, required_columns: Iterable[str]) -> None:
    missing = sorted(set(required_columns).difference(frame.columns))
    if missing:
        raise ValueError(f"Technical indicator input is missing required columns: {missing}")
