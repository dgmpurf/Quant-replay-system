"""Historical decision-date replay orchestration."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from quant_replay_system.calendar import TradingCalendar
from quant_replay_system.config import Settings
from quant_replay_system.data import ReplayDataset, build_replay_dataset, decision_time_for_as_of_date, point_in_time_prices
from quant_replay_system.execution import simulate_t_plus_1_execution
from quant_replay_system.risk import validate_research_risk_settings
from quant_replay_system.scoring import score_candidates


@dataclass(frozen=True)
class ReplayResult:
    decision_date: pd.Timestamp
    decision_time: pd.Timestamp
    candidates: pd.DataFrame
    executions: pd.DataFrame
    dataset: ReplayDataset | None = None


def replay_decision_date(
    decision_date: str | pd.Timestamp,
    prices: pd.DataFrame,
    settings: Settings,
    universe_snapshot: pd.DataFrame | None = None,
    corporate_actions: pd.DataFrame | None = None,
    trading_calendar: TradingCalendar | None = None,
    *,
    exclude_st: bool = True,
    exclude_suspended: bool = True,
) -> ReplayResult:
    """Replay one historical decision date with point-in-time inputs."""

    validate_research_risk_settings(settings.risk)
    decision_timestamp = pd.Timestamp(decision_date).normalize()
    decision_time = (
        trading_calendar.decision_time_for(decision_timestamp)
        if trading_calendar is not None
        else decision_time_for_as_of_date(decision_timestamp)
    )

    dataset = None
    if universe_snapshot is None:
        available_prices = point_in_time_prices(prices, decision_timestamp)
    else:
        dataset = build_replay_dataset(
            as_of_date=decision_timestamp,
            decision_time=decision_time,
            market_data=prices,
            universe_snapshot=universe_snapshot,
            corporate_actions=corporate_actions,
            exclude_st=exclude_st,
            exclude_suspended=exclude_suspended,
        )
        available_prices = dataset.market_data

    candidates = score_candidates(available_prices, settings.scoring)
    executions = simulate_t_plus_1_execution(
        candidates,
        prices,
        decision_timestamp,
        settings.execution,
        calendar=trading_calendar,
    )
    return ReplayResult(
        decision_date=decision_timestamp,
        decision_time=decision_time,
        candidates=candidates,
        executions=executions,
        dataset=dataset,
    )
