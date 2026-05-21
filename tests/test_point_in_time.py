from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quant_replay_system.config import load_settings
from quant_replay_system.data import (
    assert_no_future_leak,
    build_replay_dataset,
    decision_time_for_as_of_date,
    filter_available_records,
    load_corporate_actions,
    load_market_data,
    load_universe_snapshot,
)
from quant_replay_system.replay import replay_decision_date


def test_available_records_at_or_before_decision_time_are_included() -> None:
    records = pd.DataFrame(
        {
            "symbol": ["A", "B", "C"],
            "available_time": [
                "2024-01-03 15:29:59",
                "2024-01-03 15:30:00",
                "2024-01-03 15:30:01",
            ],
        }
    )

    available = filter_available_records(records, "2024-01-03 15:30:00")

    assert list(available["symbol"]) == ["A", "B"]


def test_records_after_decision_time_are_excluded() -> None:
    records = pd.DataFrame(
        {
            "symbol": ["A", "B"],
            "available_time": ["2024-01-03 15:30:00", "2024-01-03 16:00:00"],
        }
    )

    available = filter_available_records(records, "2024-01-03 15:30:00")

    assert list(available["symbol"]) == ["A"]


def test_missing_available_time_raises_clear_validation_error() -> None:
    records = pd.DataFrame({"symbol": ["A"]})

    with pytest.raises(ValueError, match="available_time"):
        filter_available_records(records, "2024-01-03 15:30:00")


def test_replay_dataset_cannot_use_future_corporate_action() -> None:
    market = load_market_data(Path("data/mock/prices.csv"))
    universe = load_universe_snapshot(Path("data/mock/universe_snapshots.csv"))
    actions = load_corporate_actions(Path("data/mock/corporate_actions.csv"))
    decision_time = decision_time_for_as_of_date("2024-01-03")

    dataset = build_replay_dataset("2024-01-03", decision_time, market, universe, actions)

    assert list(dataset.corporate_actions["symbol"]) == ["510300.SH"]
    assert dataset.corporate_actions["ex_date"].max() <= pd.Timestamp("2024-01-03")
    assert dataset.corporate_actions["available_time"].max() <= decision_time


def test_universe_snapshot_excludes_inactive_suspended_and_st_symbols() -> None:
    market = load_market_data(Path("data/mock/prices.csv"))
    universe = load_universe_snapshot(Path("data/mock/universe_snapshots.csv"))
    actions = load_corporate_actions(Path("data/mock/corporate_actions.csv"))

    dataset = build_replay_dataset("2024-01-03", "2024-01-03 15:30:00", market, universe, actions)

    assert set(dataset.universe["symbol"]) == {"510300.SH", "510500.SH"}
    assert "000001.SZ" not in set(dataset.universe["symbol"])
    assert "512800.SH" not in set(dataset.universe["symbol"])
    assert "600519.SH" not in set(dataset.universe["symbol"])


def test_assert_no_future_leak_fails_when_future_data_is_present() -> None:
    records = pd.DataFrame(
        {
            "symbol": ["A"],
            "available_time": ["2024-01-03 16:00:00"],
        }
    )

    with pytest.raises(ValueError, match="Future data leak"):
        assert_no_future_leak(records, "2024-01-03 15:30:00")


def test_replay_result_is_deterministic_for_same_inputs() -> None:
    settings = load_settings(Path("config/default.yaml"))
    market = load_market_data(settings.data.mock_prices)
    universe = load_universe_snapshot(settings.data.mock_universe_snapshots)
    actions = load_corporate_actions(settings.data.mock_corporate_actions)

    first = replay_decision_date("2024-01-03", market, settings, universe, actions)
    second = replay_decision_date("2024-01-03", market, settings, universe, actions)

    assert first.decision_time == second.decision_time
    assert_frame_equal(first.candidates, second.candidates)
    assert_frame_equal(first.executions, second.executions)
    assert first.dataset is not None
    assert second.dataset is not None
    assert_frame_equal(first.dataset.market_data, second.dataset.market_data)
    assert_frame_equal(first.dataset.universe, second.dataset.universe)
    assert_frame_equal(first.dataset.corporate_actions, second.dataset.corporate_actions)
