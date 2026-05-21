"""Risk rule placeholders for research replay."""

from __future__ import annotations

from quant_replay_system.config import RiskSettings


def validate_research_risk_settings(settings: RiskSettings) -> None:
    """Validate conservative MVP risk assumptions."""

    if settings.allow_live_trading:
        raise ValueError("Live broker trading is disabled for MVP v0.1")
    if not 0 < settings.max_single_position_pct <= 1:
        raise ValueError("max_single_position_pct must be between 0 and 1")
    if not 0 < settings.max_drawdown_stop_pct <= 1:
        raise ValueError("max_drawdown_stop_pct must be between 0 and 1")
