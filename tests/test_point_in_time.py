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


def test_missing_listed_date_does_not_make_active_symbol_ineligible() -> None:
    market = _minimal_market(["AAA"])
    universe = _minimal_universe(["AAA"])
    universe.loc[0, "listed_date"] = pd.NaT

    dataset = build_replay_dataset("2024-01-03", "2024-01-03 15:30:00", market, universe)

    assert list(dataset.universe["symbol"]) == ["AAA"]
    assert list(dataset.market_data["symbol"].unique()) == ["AAA"]


def test_present_future_listed_date_still_makes_symbol_ineligible() -> None:
    market = _minimal_market(["AAA"])
    universe = _minimal_universe(["AAA"])
    universe.loc[0, "listed_date"] = pd.Timestamp("2024-01-04")

    dataset = build_replay_dataset("2024-01-03", "2024-01-03 15:30:00", market, universe)

    assert dataset.universe.empty
    assert dataset.market_data.empty


def test_present_delisted_date_before_or_equal_decision_makes_symbol_ineligible() -> None:
    market = _minimal_market(["AAA", "BBB"])
    universe = _minimal_universe(["AAA", "BBB"])
    universe.loc[universe["symbol"] == "AAA", "delisted_date"] = pd.Timestamp("2024-01-02")
    universe.loc[universe["symbol"] == "BBB", "delisted_date"] = pd.Timestamp("2024-01-03")

    dataset = build_replay_dataset("2024-01-03", "2024-01-03 15:30:00", market, universe)

    assert dataset.universe.empty
    assert dataset.market_data.empty


def test_invalid_non_empty_listed_date_raises_clear_downstream_error() -> None:
    market = _minimal_market(["AAA"])
    universe = _minimal_universe(["AAA"])
    universe["listed_date"] = universe["listed_date"].astype("object")
    universe.loc[0, "listed_date"] = "not-a-date"

    with pytest.raises(ValueError, match="listed_date contains invalid non-empty universe dates"):
        build_replay_dataset("2024-01-03", "2024-01-03 15:30:00", market, universe)


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


def _minimal_market(symbols: list[str]) -> pd.DataFrame:
    rows = []
    for symbol in symbols:
        for trade_date in pd.date_range("2024-01-02", "2024-01-03"):
            rows.append(
                {
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "open": 10.0,
                    "high": 10.5,
                    "low": 9.8,
                    "close": 10.2,
                    "volume": 1000,
                    "amount": 10200,
                    "pre_close": 10.0,
                    "adj_factor": 1.0,
                    "is_suspended": False,
                    "limit_up": 11.0,
                    "limit_down": 9.0,
                    "event_time": trade_date + pd.Timedelta(hours=15),
                    "publish_time": trade_date + pd.Timedelta(hours=15, minutes=5),
                    "ingest_time": trade_date + pd.Timedelta(hours=15, minutes=10),
                    "available_time": trade_date + pd.Timedelta(hours=15, minutes=10),
                    "revision_id": "m1",
                    "source": "unit-test",
                }
            )
    return pd.DataFrame(rows)


def _minimal_universe(symbols: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "as_of_date": pd.Timestamp("2024-01-03"),
                "symbol": symbol,
                "name": f"{symbol} Fund",
                "instrument_type": "ETF",
                "exchange": "SSE",
                "listed_date": pd.Timestamp("2020-01-01"),
                "delisted_date": pd.NaT,
                "is_active": True,
                "is_st": False,
                "is_suspended": False,
                "industry": "ETF",
                "min_lot": 100,
                "t_plus_rule": "T+1",
                "available_time": pd.Timestamp("2024-01-03 08:00:00"),
                "revision_id": "u1",
                "source": "unit-test",
            }
            for symbol in symbols
        ]
    )
