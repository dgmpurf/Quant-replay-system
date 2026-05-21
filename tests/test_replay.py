from pathlib import Path

import pandas as pd

from quant_replay_system.config import load_settings
from quant_replay_system.data import (
    MARKET_DATA_SCHEMA,
    decision_time_for_as_of_date,
    load_corporate_actions,
    load_market_data,
    load_universe_snapshot,
    point_in_time_prices,
)
from quant_replay_system.replay import replay_decision_date


def test_load_mock_market_data() -> None:
    prices = load_market_data(Path("data/mock/prices.csv"))

    assert list(prices.columns) == MARKET_DATA_SCHEMA
    assert not prices.empty


def test_point_in_time_prices_exclude_future_rows() -> None:
    prices = load_market_data(Path("data/mock/prices.csv"))
    available = point_in_time_prices(prices, "2024-01-03")

    assert available["trade_date"].max() == pd.Timestamp("2024-01-03")
    assert pd.Timestamp("2024-01-04") not in set(available["trade_date"])
    assert available["available_time"].max() <= decision_time_for_as_of_date("2024-01-03")


def test_replay_decision_date_scores_and_executes_t_plus_1() -> None:
    settings = load_settings(Path("config/default.yaml"))
    prices = load_market_data(settings.data.mock_prices)
    universe = load_universe_snapshot(settings.data.mock_universe_snapshots)
    actions = load_corporate_actions(settings.data.mock_corporate_actions)

    result = replay_decision_date("2024-01-03", prices, settings, universe, actions)

    assert result.decision_date == pd.Timestamp("2024-01-03")
    assert result.decision_time == pd.Timestamp("2024-01-03 15:30:00")
    assert result.dataset is not None
    assert set(result.dataset.universe["symbol"]) == {"510300.SH", "510500.SH"}
    assert not result.candidates.empty
    assert "score" in result.candidates.columns
    assert set(result.candidates["symbol"]).issubset({"510300.SH", "510500.SH"})
    assert set(result.executions["execution_date"]) == {pd.Timestamp("2024-01-04")}
    assert "execution_price" in result.executions.columns
