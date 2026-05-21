"""Point-in-time factor dataset builder."""

from __future__ import annotations

from typing import Any, Iterable

import pandas as pd

from quant_replay_system.calendar import TradingCalendar
from quant_replay_system.config import FactorDatasetSettings
from quant_replay_system.data import MARKET_DATA_SCHEMA, UNIVERSE_SNAPSHOT_SCHEMA, build_replay_dataset
from quant_replay_system.indicators import compute_technical_indicators, compute_technical_score


UNIVERSE_COLUMNS = [
    "decision_date",
    "decision_time",
    "symbol",
    "name",
    "instrument_type",
    "exchange",
    "industry",
    "is_active",
    "is_st",
    "is_suspended",
    "min_lot",
    "t_plus_rule",
]

MARKET_COLUMNS = [
    "close",
    "open",
    "high",
    "low",
    "volume",
    "amount",
    "pre_close",
    "limit_up",
    "limit_down",
    "adj_factor",
]

TECHNICAL_COLUMNS = [
    "ma5",
    "ma10",
    "ma20",
    "ma60",
    "macd_dif",
    "macd_dea",
    "macd_hist",
    "rsi14",
    "atr14",
    "volume_ma5",
    "volume_ma10",
    "volume_ma20",
    "volume_ratio_20",
    "rel_return_5",
    "rel_return_10",
    "rel_return_20",
]

AUDIT_COLUMNS = [
    "latest_market_available_time",
    "universe_available_time",
    "data_revision_id",
    "source",
]

ELIGIBILITY_COLUMNS = [
    "universe_eligible",
    "market_data_available",
    "execution_data_available",
    "risk_precheck_status",
    "risk_precheck_reason",
]


def build_factor_dataset(
    decision_date: str | pd.Timestamp,
    market_data: pd.DataFrame,
    universe_snapshot: pd.DataFrame,
    trading_calendar: TradingCalendar,
    benchmark_data: pd.DataFrame | None = None,
    config: FactorDatasetSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Build one point-in-time research row per eligible symbol."""

    cfg = _coerce_config(config)
    _require_columns(market_data, MARKET_DATA_SCHEMA, "market_data")
    _require_columns(universe_snapshot, UNIVERSE_SNAPSHOT_SCHEMA, "universe_snapshot")

    as_of_date = pd.Timestamp(decision_date).normalize()
    decision_time = trading_calendar.decision_time_for(as_of_date)

    replay_dataset = build_replay_dataset(
        as_of_date=as_of_date,
        decision_time=decision_time,
        market_data=market_data,
        universe_snapshot=universe_snapshot,
        corporate_actions=None,
        exclude_st=cfg.exclude_st,
        exclude_suspended=cfg.exclude_suspended,
    )

    indicators = compute_technical_indicators(
        replay_dataset.market_data,
        decision_time=decision_time,
        benchmark_df=benchmark_data,
    )
    if cfg.include_technical_score and not indicators.empty:
        indicators = compute_technical_score(indicators)
    elif cfg.include_technical_score:
        indicators = indicators.copy()
        indicators["technical_score_v01"] = pd.NA

    latest_features = _latest_indicator_rows(indicators)
    factor_frame = _merge_universe_and_features(
        replay_dataset.universe,
        latest_features,
        as_of_date,
        decision_time,
        include_technical_score=cfg.include_technical_score,
    )

    if cfg.require_market_data:
        factor_frame = factor_frame.loc[factor_frame["market_data_available"]].copy()

    return _finalize_columns(factor_frame, include_technical_score=cfg.include_technical_score)


def _latest_indicator_rows(indicators: pd.DataFrame) -> pd.DataFrame:
    if indicators.empty:
        return pd.DataFrame(columns=["symbol"])

    sort_columns = ["symbol", "trade_date"]
    for optional_column in ["available_time", "revision_id"]:
        if optional_column in indicators.columns:
            sort_columns.append(optional_column)

    latest = indicators.sort_values(sort_columns).groupby("symbol", as_index=False).tail(1).copy()
    rename_map = {
        "available_time": "latest_market_available_time",
        "revision_id": "market_revision_id",
        "source": "market_source",
        "is_suspended": "market_is_suspended",
        "macd_histogram": "macd_hist",
        "rsi_14": "rsi14",
        "atr_14": "atr14",
        "relative_return_5d": "rel_return_5",
        "relative_return_10d": "rel_return_10",
        "relative_return_20d": "rel_return_20",
    }
    return latest.rename(columns=rename_map)


def _merge_universe_and_features(
    universe: pd.DataFrame,
    latest_features: pd.DataFrame,
    decision_date: pd.Timestamp,
    decision_time: pd.Timestamp,
    *,
    include_technical_score: bool,
) -> pd.DataFrame:
    universe_frame = universe.copy().rename(
        columns={
            "available_time": "universe_available_time",
            "revision_id": "universe_revision_id",
            "source": "universe_source",
        }
    )

    selected_market_columns = [
        "symbol",
        "trade_date",
        *MARKET_COLUMNS,
        "market_is_suspended",
        "latest_market_available_time",
        "market_revision_id",
        "market_source",
        *[column for column in TECHNICAL_COLUMNS if column in latest_features.columns],
    ]
    if include_technical_score and "technical_score_v01" in latest_features.columns:
        selected_market_columns.append("technical_score_v01")

    available_columns = [column for column in selected_market_columns if column in latest_features.columns]
    merged = universe_frame.merge(latest_features[available_columns], on="symbol", how="left")

    for column in [
        *MARKET_COLUMNS,
        "market_is_suspended",
        "latest_market_available_time",
        "market_revision_id",
        "market_source",
        *TECHNICAL_COLUMNS,
    ]:
        if column not in merged.columns:
            merged[column] = pd.NA
    if include_technical_score and "technical_score_v01" not in merged.columns:
        merged["technical_score_v01"] = pd.NA

    merged["decision_date"] = decision_date
    merged["decision_time"] = decision_time
    merged["universe_eligible"] = True
    merged["market_data_available"] = merged["latest_market_available_time"].notna()
    merged["execution_data_available"] = (
        merged["market_data_available"]
        & merged["open"].notna()
        & merged["limit_up"].notna()
        & merged["limit_down"].notna()
    )

    precheck = merged.apply(_risk_precheck, axis=1, result_type="expand")
    merged["risk_precheck_status"] = precheck[0]
    merged["risk_precheck_reason"] = precheck[1]
    merged["data_revision_id"] = merged.apply(_join_revision_ids, axis=1)
    merged["source"] = merged.apply(_join_sources, axis=1)

    return merged


def _risk_precheck(row: pd.Series) -> tuple[str, str]:
    if not bool(row.get("market_data_available", False)):
        return "BLOCK", "missing market data as of decision date"
    if not bool(row.get("execution_data_available", False)):
        return "BLOCK", "missing execution precheck fields as of decision date"
    if _is_true(row.get("is_suspended", False)) or _is_true(row.get("market_is_suspended", False)):
        return "BLOCK", "suspended as of decision date"
    if pd.notna(row.get("open")) and pd.notna(row.get("limit_up")) and float(row["open"]) >= float(row["limit_up"]):
        return "BLOCK", "limit-up as of decision date"
    if pd.notna(row.get("open")) and pd.notna(row.get("limit_down")) and float(row["open"]) <= float(row["limit_down"]):
        return "WARN", "limit-down as of decision date"
    return "PASS", "eligible"


def _is_true(value: Any) -> bool:
    if pd.isna(value):
        return False
    return bool(value)


def _join_revision_ids(row: pd.Series) -> str:
    parts = []
    if pd.notna(row.get("market_revision_id")):
        parts.append(f"market:{row['market_revision_id']}")
    if pd.notna(row.get("universe_revision_id")):
        parts.append(f"universe:{row['universe_revision_id']}")
    return "|".join(parts)


def _join_sources(row: pd.Series) -> str:
    parts = []
    if pd.notna(row.get("market_source")):
        parts.append(f"market:{row['market_source']}")
    if pd.notna(row.get("universe_source")):
        parts.append(f"universe:{row['universe_source']}")
    return "|".join(parts)


def _finalize_columns(frame: pd.DataFrame, *, include_technical_score: bool) -> pd.DataFrame:
    output_columns = [
        *UNIVERSE_COLUMNS,
        *MARKET_COLUMNS,
        *TECHNICAL_COLUMNS,
    ]
    if include_technical_score:
        output_columns.append("technical_score_v01")
    output_columns.extend([*AUDIT_COLUMNS, *ELIGIBILITY_COLUMNS])

    finalized = frame.copy()
    for column in output_columns:
        if column not in finalized.columns:
            finalized[column] = pd.NA

    finalized = finalized.sort_values(["decision_date", "symbol"]).reset_index(drop=True)
    return finalized[output_columns]


def _coerce_config(config: FactorDatasetSettings | dict[str, Any] | None) -> FactorDatasetSettings:
    if config is None:
        return FactorDatasetSettings()
    if isinstance(config, FactorDatasetSettings):
        return config
    if isinstance(config, dict):
        return FactorDatasetSettings(**config)
    if hasattr(config, "model_dump"):
        return FactorDatasetSettings(**config.model_dump())
    raise TypeError("config must be a FactorDatasetSettings instance, dict, or None")


def _require_columns(frame: pd.DataFrame, required_columns: Iterable[str], name: str) -> None:
    missing = sorted(set(required_columns).difference(frame.columns))
    if missing:
        raise ValueError(f"Factor dataset {name} missing required columns: {missing}")
