"""Explainable score engine for factor datasets."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from quant_replay_system.config import ScoreEngineSettings


ACTION_ORDER = {
    "BLOCKED": -1,
    "NO_TRADE": 0,
    "OBSERVE": 1,
    "PAPER_TRADE": 2,
    "LIVE_CANDIDATE_SMALL": 3,
    "STRONG_CANDIDATE_REVIEW_REQUIRED": 4,
}


def score_factor_dataset(
    factor_df: pd.DataFrame,
    config: ScoreEngineSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Convert factor rows into explainable component scores and actions."""

    cfg = _coerce_config(config)
    frame = factor_df.copy(deep=True)

    if frame.empty:
        return _empty_scored_frame(frame)

    frame["technical_score"] = frame.apply(lambda row: _technical_score(row, cfg), axis=1)
    frame["liquidity_score"] = frame.apply(lambda row: _liquidity_score(row, cfg), axis=1)
    frame["expectation_score_v01"] = frame.apply(lambda row: _expectation_score(row, cfg), axis=1)
    frame["expectation_score"] = frame["expectation_score_v01"]
    frame["risk_penalty"] = frame.apply(lambda row: _risk_penalty(row, cfg), axis=1)
    frame["reality_score_v01"] = frame.apply(lambda row: _default_or_column(row, "reality_score_v01", cfg.reality_score_default), axis=1)
    frame["reality_score"] = frame["reality_score_v01"].apply(_clip_score)
    frame["sentiment_score"] = frame.apply(lambda row: _default_or_column(row, "sentiment_score", cfg.sentiment_score_default), axis=1)
    frame["sentiment_score"] = frame["sentiment_score"].apply(_clip_score)

    frame["final_score_raw"] = frame.apply(lambda row: _final_score(row, cfg), axis=1)
    frame["final_score"] = frame["final_score_raw"].apply(_clip_score)
    frame["score_action"] = frame.apply(lambda row: map_score_to_action(row["final_score"], row, cfg), axis=1)
    frame["score_breakdown"] = frame.apply(lambda row: _score_breakdown(row, cfg), axis=1)
    frame["score_reason"] = frame.apply(_score_reason, axis=1)

    return frame.sort_values(["decision_date", "symbol"] if "decision_date" in frame.columns else ["symbol"]).reset_index(drop=True)


def map_score_to_action(
    final_score: float,
    row: pd.Series | dict[str, Any] | None = None,
    config: ScoreEngineSettings | dict[str, Any] | None = None,
) -> str:
    """Map final score and hard risk flags to an action bucket."""

    cfg = _coerce_config(config)
    if row is not None and _hard_block(row, cfg):
        return "BLOCKED"

    score = _clip_score(final_score)
    if score < 60:
        return "NO_TRADE"
    if score < 70:
        return "OBSERVE"
    if score < 80:
        return "PAPER_TRADE"
    if score < 90:
        return "LIVE_CANDIDATE_SMALL"
    return "STRONG_CANDIDATE_REVIEW_REQUIRED"


def _technical_score(row: pd.Series, config: ScoreEngineSettings) -> float:
    raw = _to_float(row.get("technical_score_v01"))
    if raw is not None:
        if 0 <= raw <= 100 and raw > 10:
            return _clip_score(raw)
        return _clip_score(50.0 + raw * 10.0)

    score = config.technical_score_default
    close = _to_float(row.get("close"))
    ma5 = _to_float(row.get("ma5"))
    ma20 = _to_float(row.get("ma20"))
    volume_ratio = _to_float(row.get("volume_ratio_20"))
    rsi = _to_float(row.get("rsi14"))

    if close is not None and ma20 is not None:
        score += 15.0 if close > ma20 else -15.0
    if ma5 is not None and ma20 is not None:
        score += 15.0 if ma5 > ma20 else -10.0
    if volume_ratio is not None and volume_ratio > 1.2:
        score += 10.0
    if rsi is not None and rsi > config.rsi_overheat_threshold:
        score -= 15.0
    return _clip_score(score)


def _liquidity_score(row: pd.Series, config: ScoreEngineSettings) -> float:
    amount = _to_float(row.get("amount"))
    volume = _to_float(row.get("volume"))
    volume_ratio = _to_float(row.get("volume_ratio_20"))

    if amount is None or volume is None or amount <= 0 or volume <= 0:
        return _clip_score(config.liquidity_score_default)

    amount_score = _clip_score((np.log10(amount) - 5.0) * 20.0)
    ratio_score = _clip_score((volume_ratio if volume_ratio is not None else 1.0) * 50.0)
    return _clip_score(amount_score * 0.70 + ratio_score * 0.30)


def _expectation_score(row: pd.Series, config: ScoreEngineSettings) -> float:
    weighted_returns = []
    for column, weight in [("rel_return_5", 0.50), ("rel_return_10", 0.30), ("rel_return_20", 0.20)]:
        value = _to_float(row.get(column))
        if value is not None:
            weighted_returns.append((value, weight))

    if weighted_returns:
        numerator = sum(value * weight for value, weight in weighted_returns)
        denominator = sum(weight for _, weight in weighted_returns)
        score = 50.0 + (numerator / denominator) * 100.0
    else:
        score = config.expectation_score_default

    rsi = _to_float(row.get("rsi14"))
    if rsi is not None and rsi > config.rsi_overheat_threshold:
        score -= min(20.0, (rsi - config.rsi_overheat_threshold) * 2.0)
    return _clip_score(score)


def _risk_penalty(row: pd.Series, config: ScoreEngineSettings) -> float:
    penalty = 0.0
    status = str(row.get("risk_precheck_status", "")).upper()
    if status == "BLOCK":
        penalty += 100.0
    elif status == "WARN":
        penalty += 25.0

    if _is_true(row.get("is_st")):
        penalty += 40.0
    if _is_true(row.get("is_suspended")):
        penalty += 80.0
    if not _is_true(row.get("market_data_available", True)):
        penalty += 70.0
    if not _is_true(row.get("execution_data_available", True)):
        penalty += 40.0

    rsi = _to_float(row.get("rsi14"))
    if rsi is not None and rsi > config.rsi_overheat_threshold:
        penalty += min(30.0, rsi - config.rsi_overheat_threshold)

    amount = _to_float(row.get("amount"))
    volume = _to_float(row.get("volume"))
    liquidity = _liquidity_score(row, config)
    if amount is None or volume is None or amount <= 0 or volume <= 0:
        penalty += 40.0
    elif liquidity < 30.0:
        penalty += 20.0

    open_price = _to_float(row.get("open"))
    limit_up = _to_float(row.get("limit_up"))
    limit_down = _to_float(row.get("limit_down"))
    if open_price is not None and limit_up is not None and open_price >= limit_up:
        penalty += 50.0
    if open_price is not None and limit_down is not None and open_price <= limit_down:
        penalty += 30.0

    return _clip_score(penalty)


def _final_score(row: pd.Series, config: ScoreEngineSettings) -> float:
    weights = config.weights
    return (
        weights.get("reality_score", 0.35) * _clip_score(row["reality_score"])
        + weights.get("technical_score", 0.25) * _clip_score(row["technical_score"])
        + weights.get("expectation_score", 0.15) * _clip_score(row["expectation_score"])
        + weights.get("liquidity_score", 0.10) * _clip_score(row["liquidity_score"])
        + weights.get("sentiment_score", 0.05) * _clip_score(row["sentiment_score"])
        - weights.get("risk_penalty", 0.25) * _clip_score(row["risk_penalty"])
    )


def _hard_block(row: pd.Series | dict[str, Any], config: ScoreEngineSettings) -> bool:
    status = str(_row_get(row, "risk_precheck_status", "")).upper()
    if status == "BLOCK":
        return True
    if config.hard_block_st and _is_true(_row_get(row, "is_st", False)):
        return True
    if config.hard_block_suspended and _is_true(_row_get(row, "is_suspended", False)):
        return True
    if config.hard_block_missing_market and not _is_true(_row_get(row, "market_data_available", True)):
        return True
    if config.hard_block_missing_market and not _is_true(_row_get(row, "execution_data_available", True)):
        return True

    open_price = _to_float(_row_get(row, "open"))
    limit_up = _to_float(_row_get(row, "limit_up"))
    if config.hard_block_limit_up and open_price is not None and limit_up is not None and open_price >= limit_up:
        return True
    return False


def _score_breakdown(row: pd.Series, config: ScoreEngineSettings) -> dict[str, Any]:
    weights = config.weights
    return {
        "components": {
            "reality_score": _clip_score(row["reality_score"]),
            "technical_score": _clip_score(row["technical_score"]),
            "expectation_score": _clip_score(row["expectation_score"]),
            "liquidity_score": _clip_score(row["liquidity_score"]),
            "sentiment_score": _clip_score(row["sentiment_score"]),
            "risk_penalty": _clip_score(row["risk_penalty"]),
        },
        "weights": {
            "reality_score": weights.get("reality_score", 0.35),
            "technical_score": weights.get("technical_score", 0.25),
            "expectation_score": weights.get("expectation_score", 0.15),
            "liquidity_score": weights.get("liquidity_score", 0.10),
            "sentiment_score": weights.get("sentiment_score", 0.05),
            "risk_penalty": weights.get("risk_penalty", 0.25),
        },
        "raw_final_score": _to_float(row.get("final_score_raw")),
        "final_score": _clip_score(row["final_score"]),
        "action": row["score_action"],
    }


def _score_reason(row: pd.Series) -> str:
    return (
        f"action={row['score_action']}; "
        f"final={row['final_score']:.2f}; "
        f"technical={row['technical_score']:.2f}; "
        f"expectation={row['expectation_score']:.2f}; "
        f"liquidity={row['liquidity_score']:.2f}; "
        f"risk_penalty={row['risk_penalty']:.2f}; "
        f"risk_precheck={row.get('risk_precheck_status', 'UNKNOWN')}"
    )


def _default_or_column(row: pd.Series, column: str, default: float) -> float:
    value = _to_float(row.get(column))
    return default if value is None else value


def _clip_score(value: Any) -> float:
    numeric = _to_float(value)
    if numeric is None:
        numeric = 0.0
    return float(np.clip(numeric, 0.0, 100.0))


def _to_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_true(value: Any) -> bool:
    if value is None or pd.isna(value):
        return False
    return bool(value)


def _row_get(row: pd.Series | dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(row, pd.Series):
        return row.get(key, default)
    return row.get(key, default)


def _coerce_config(config: ScoreEngineSettings | dict[str, Any] | None) -> ScoreEngineSettings:
    if config is None:
        return ScoreEngineSettings()
    if isinstance(config, ScoreEngineSettings):
        return config
    if isinstance(config, dict):
        return ScoreEngineSettings(**config)
    if hasattr(config, "model_dump"):
        return ScoreEngineSettings(**config.model_dump())
    raise TypeError("config must be a ScoreEngineSettings instance, dict, or None")


def _empty_scored_frame(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in [
        "technical_score",
        "liquidity_score",
        "expectation_score_v01",
        "expectation_score",
        "risk_penalty",
        "reality_score_v01",
        "reality_score",
        "sentiment_score",
        "final_score_raw",
        "final_score",
        "score_action",
        "score_breakdown",
        "score_reason",
    ]:
        result[column] = pd.Series(dtype="object")
    return result
