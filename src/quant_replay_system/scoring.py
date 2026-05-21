"""Explainable placeholder scoring logic."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_replay_system.config import ScoringSettings


def score_candidates(point_in_time_data: pd.DataFrame, settings: ScoringSettings) -> pd.DataFrame:
    """Score candidates using only point-in-time data.

    MVP scoring is intentionally simple and explainable. It uses the last
    available row per symbol and names each component so later research can
    replace the placeholders without changing the replay contract.
    """

    if point_in_time_data.empty:
        return pd.DataFrame(columns=["symbol", "score", "momentum_20d", "liquidity", "volatility_penalty"])

    date_column = "trade_date" if "trade_date" in point_in_time_data.columns else "date"
    latest = (
        point_in_time_data.sort_values(["symbol", date_column])
        .groupby("symbol", as_index=False)
        .tail(1)
        .copy()
    )

    latest["momentum_20d"] = latest["close"] / latest["open"] - 1.0
    latest["liquidity"] = np.log1p(latest["volume"])
    latest["volatility_penalty"] = 0.0

    latest["score"] = 0.0
    for component, weight in settings.weights.items():
        if component in latest:
            latest["score"] += latest[component] * weight

    selected = latest.loc[latest["score"] >= settings.min_score].copy()
    selected = selected.sort_values("score", ascending=False).head(settings.max_candidates)
    return selected[["symbol", "score", "momentum_20d", "liquidity", "volatility_penalty"]].reset_index(drop=True)
