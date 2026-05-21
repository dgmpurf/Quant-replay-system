from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quant_replay_system.calendar import load_trading_calendar
from quant_replay_system.config import load_settings
from quant_replay_system.data import load_corporate_actions, load_market_data, load_universe_snapshot
from quant_replay_system.execution import (
    BLOCK,
    PASS,
    BUY,
    SELL,
    check_execution_eligibility,
    get_buy_execution_date,
    get_planned_sell_date,
    get_sellable_date,
    is_position_sellable,
)
from quant_replay_system.replay import replay_decision_date


def test_weekend_is_skipped_by_next_trading_day() -> None:
    calendar = load_trading_calendar(Path("data/mock/trading_calendar.csv"))

    assert calendar.next_trading_day("2024-01-05") == pd.Timestamp("2024-01-08")


def test_holiday_non_trading_day_is_skipped() -> None:
    calendar = load_trading_calendar(Path("data/mock/trading_calendar.csv"))

    assert calendar.next_trading_day("2024-01-08") == pd.Timestamp("2024-01-10")


def test_nth_next_trading_day_works_correctly() -> None:
    calendar = load_trading_calendar(Path("data/mock/trading_calendar.csv"))

    assert calendar.nth_next_trading_day("2024-01-04", 1) == pd.Timestamp("2024-01-05")
    assert calendar.nth_next_trading_day("2024-01-04", 2) == pd.Timestamp("2024-01-08")
    assert calendar.nth_next_trading_day("2024-01-08", 1) == pd.Timestamp("2024-01-10")


def test_previous_and_between_helpers_use_trading_days() -> None:
    calendar = load_trading_calendar(Path("data/mock/trading_calendar.csv"))

    assert calendar.previous_trading_day("2024-01-08") == pd.Timestamp("2024-01-05")
    assert calendar.nth_previous_trading_day("2024-01-10", 2) == pd.Timestamp("2024-01-05")
    assert calendar.trading_days_between("2024-01-05", "2024-01-10") == [
        pd.Timestamp("2024-01-05"),
        pd.Timestamp("2024-01-08"),
        pd.Timestamp("2024-01-10"),
    ]


def test_decision_time_for_non_trading_day_raises_error() -> None:
    calendar = load_trading_calendar(Path("data/mock/trading_calendar.csv"))

    with pytest.raises(ValueError, match="not a trading day"):
        calendar.decision_time_for("2024-01-06")


def test_buy_signal_on_friday_executes_next_monday() -> None:
    calendar = load_trading_calendar(Path("data/mock/trading_calendar.csv"))

    assert get_buy_execution_date("2024-01-05", calendar) == pd.Timestamp("2024-01-08")


def test_buy_signal_before_holiday_executes_after_holiday() -> None:
    calendar = load_trading_calendar(Path("data/mock/trading_calendar.csv"))

    assert get_buy_execution_date("2024-01-08", calendar) == pd.Timestamp("2024-01-10")


def test_buy_date_has_t_plus_1_sellable_date() -> None:
    calendar = load_trading_calendar(Path("data/mock/trading_calendar.csv"))

    assert get_sellable_date("2024-01-04", calendar) == pd.Timestamp("2024-01-05")
    assert get_sellable_date("2024-01-05", calendar) == pd.Timestamp("2024-01-08")


def test_position_bought_today_is_not_sellable_today() -> None:
    calendar = load_trading_calendar(Path("data/mock/trading_calendar.csv"))

    assert is_position_sellable("2024-01-04", "2024-01-04", calendar) is False


def test_position_bought_on_previous_trading_day_is_sellable() -> None:
    calendar = load_trading_calendar(Path("data/mock/trading_calendar.csv"))

    assert is_position_sellable("2024-01-04", "2024-01-05", calendar) is True


def test_holding_horizon_uses_trading_days_not_calendar_days() -> None:
    calendar = load_trading_calendar(Path("data/mock/trading_calendar.csv"))

    assert get_planned_sell_date("2024-01-05", 1, calendar) == pd.Timestamp("2024-01-08")
    assert get_planned_sell_date("2024-01-05", 2, calendar) == pd.Timestamp("2024-01-10")


def test_suspended_symbol_blocks_buy() -> None:
    calendar = load_trading_calendar(Path("data/mock/trading_calendar.csv"))
    market = load_market_data(Path("data/mock/prices.csv"))

    result = check_execution_eligibility("512800.SH", "2024-01-03", BUY, market, calendar)

    assert result.status == BLOCK
    assert "suspended" in result.reason


def test_suspended_symbol_blocks_sell() -> None:
    calendar = load_trading_calendar(Path("data/mock/trading_calendar.csv"))
    market = load_market_data(Path("data/mock/prices.csv"))

    result = check_execution_eligibility("512800.SH", "2024-01-03", SELL, market, calendar)

    assert result.status == BLOCK
    assert "suspended" in result.reason


def test_limit_up_open_blocks_buy() -> None:
    calendar = load_trading_calendar(Path("data/mock/trading_calendar.csv"))
    market = load_market_data(Path("data/mock/prices.csv"))

    result = check_execution_eligibility("510300.SH", "2024-01-08", BUY, market, calendar)

    assert result.status == BLOCK
    assert "limit-up" in result.reason


def test_limit_down_open_blocks_sell() -> None:
    calendar = load_trading_calendar(Path("data/mock/trading_calendar.csv"))
    market = load_market_data(Path("data/mock/prices.csv"))

    result = check_execution_eligibility("510300.SH", "2024-01-05", SELL, market, calendar)

    assert result.status == BLOCK
    assert "limit-down" in result.reason


def test_replay_skips_blocked_buys_with_reason() -> None:
    settings = load_settings(Path("config/default.yaml"))
    calendar = load_trading_calendar(settings.data.mock_trading_calendar)
    market = load_market_data(settings.data.mock_prices)
    universe = load_universe_snapshot(settings.data.mock_universe_snapshots)
    actions = load_corporate_actions(settings.data.mock_corporate_actions)
    market.loc[
        (market["symbol"] == "510300.SH") & (market["trade_date"] == pd.Timestamp("2024-01-04")),
        "open",
    ] = 3.96

    result = replay_decision_date("2024-01-03", market, settings, universe, actions, calendar)
    skipped = result.executions.loc[result.executions["symbol"] == "510300.SH"].iloc[0]

    assert skipped["trade_status"] == "SKIPPED_BUY"
    assert skipped["buy_status"] == BLOCK
    assert "limit-up" in skipped["buy_reason"]


def test_replay_delays_blocked_sells_up_to_max_exit_delay() -> None:
    settings = load_settings(Path("config/default.yaml"))
    calendar = load_trading_calendar(settings.data.mock_trading_calendar)
    market = load_market_data(settings.data.mock_prices)
    universe = load_universe_snapshot(settings.data.mock_universe_snapshots)
    actions = load_corporate_actions(settings.data.mock_corporate_actions)

    result = replay_decision_date("2024-01-03", market, settings, universe, actions, calendar)
    filled = result.executions.loc[result.executions["symbol"] == "510300.SH"].iloc[0]

    assert filled["trade_status"] == "FILLED"
    assert filled["planned_sell_date"] == pd.Timestamp("2024-01-05")
    assert filled["sell_date"] == pd.Timestamp("2024-01-08")
    assert filled["sell_delay_trading_days"] == 1
    assert [attempt["status"] for attempt in filled["sell_attempts"]] == [BLOCK, PASS]


def test_replay_remains_deterministic_for_same_inputs_with_calendar() -> None:
    settings = load_settings(Path("config/default.yaml"))
    calendar = load_trading_calendar(settings.data.mock_trading_calendar)
    market = load_market_data(settings.data.mock_prices)
    universe = load_universe_snapshot(settings.data.mock_universe_snapshots)
    actions = load_corporate_actions(settings.data.mock_corporate_actions)

    first = replay_decision_date("2024-01-03", market, settings, universe, actions, calendar)
    second = replay_decision_date("2024-01-03", market, settings, universe, actions, calendar)

    assert_frame_equal(first.candidates, second.candidates)
    assert_frame_equal(first.executions, second.executions)
