"""Candidate selection from scored factor datasets."""

from __future__ import annotations

from typing import Any

import pandas as pd

from quant_replay_system.config import CandidateSelectionSettings
from quant_replay_system.score_engine import ACTION_ORDER


def select_candidates(
    scored_df: pd.DataFrame,
    top_n: int = 5,
    min_action: str = "PAPER_TRADE",
    config: CandidateSelectionSettings | dict[str, Any] | None = None,
    *,
    min_final_score: float | None = None,
) -> pd.DataFrame:
    """Select ranked candidates while preserving score explanations."""

    cfg = _coerce_config(config)
    effective_top_n = cfg.top_n if config is not None else top_n
    effective_min_action = cfg.min_action if config is not None else min_action
    effective_min_final_score = cfg.min_final_score if min_final_score is None else min_final_score

    frame = scored_df.copy(deep=True)
    if frame.empty:
        return frame

    _require_columns(frame, ["final_score", "score_action"])
    if cfg.exclude_blocked:
        frame = frame.loc[frame["score_action"] != "BLOCKED"].copy()

    min_rank = _action_rank(effective_min_action)
    frame = frame.loc[frame["score_action"].map(_action_rank) >= min_rank].copy()

    if effective_min_final_score is not None:
        frame = frame.loc[frame["final_score"] >= effective_min_final_score].copy()

    sort_columns = ["final_score"]
    ascending = [False]
    for optional_column in ["decision_date", "symbol"]:
        if optional_column in frame.columns:
            sort_columns.append(optional_column)
            ascending.append(True)

    return frame.sort_values(sort_columns, ascending=ascending).head(effective_top_n).reset_index(drop=True)


def _coerce_config(config: CandidateSelectionSettings | dict[str, Any] | None) -> CandidateSelectionSettings:
    if config is None:
        return CandidateSelectionSettings()
    if isinstance(config, CandidateSelectionSettings):
        return config
    if isinstance(config, dict):
        return CandidateSelectionSettings(**config)
    if hasattr(config, "model_dump"):
        return CandidateSelectionSettings(**config.model_dump())
    raise TypeError("config must be a CandidateSelectionSettings instance, dict, or None")


def _action_rank(action: Any) -> int:
    return ACTION_ORDER.get(str(action), -1)


def _require_columns(frame: pd.DataFrame, required_columns: list[str]) -> None:
    missing = sorted(set(required_columns).difference(frame.columns))
    if missing:
        raise ValueError(f"Candidate selection input missing required columns: {missing}")
