import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quant_replay_system.calendar import TradingCalendar
from quant_replay_system.factor_dataset import build_factor_dataset


DECISION_DATE = pd.Timestamp("2024-03-05")
DECISION_TIME = pd.Timestamp("2024-03-05 15:30:00")


def test_factor_dataset_has_one_row_per_eligible_symbol() -> None:
    result = build_factor_dataset(
        DECISION_DATE,
        _make_market_data(["AAA", "BBB", "STS", "SUS", "INA", "FUT"]),
        _make_universe_snapshot(),
        _make_calendar(),
    )

    assert list(result["symbol"]) == ["AAA", "BBB"]
    assert result[["decision_date", "symbol"]].duplicated().sum() == 0
    assert set(_required_output_columns()).issubset(result.columns)


def test_inactive_symbols_are_excluded() -> None:
    result = build_factor_dataset(DECISION_DATE, _make_market_data(["AAA", "INA"]), _make_universe_snapshot(), _make_calendar())

    assert "INA" not in set(result["symbol"])


def test_st_symbols_are_excluded_by_default() -> None:
    result = build_factor_dataset(DECISION_DATE, _make_market_data(["AAA", "STS"]), _make_universe_snapshot(), _make_calendar())

    assert "STS" not in set(result["symbol"])


def test_suspended_symbols_are_excluded_by_default() -> None:
    result = build_factor_dataset(DECISION_DATE, _make_market_data(["AAA", "SUS"]), _make_universe_snapshot(), _make_calendar())

    assert "SUS" not in set(result["symbol"])


def test_future_market_rows_are_not_used() -> None:
    market = _make_market_data(["AAA"])
    future_revision = market.loc[market["trade_date"] == DECISION_DATE].tail(1).copy()
    future_revision["close"] = 9999.0
    future_revision["available_time"] = pd.Timestamp("2024-03-05 16:00:00")
    future_revision["revision_id"] = "r2"
    market = pd.concat([market, future_revision], ignore_index=True)

    result = build_factor_dataset(DECISION_DATE, market, _make_universe_snapshot(), _make_calendar())

    assert result.loc[0, "close"] != 9999.0
    assert result.loc[0, "latest_market_available_time"] <= DECISION_TIME


def test_future_universe_rows_are_not_used() -> None:
    result = build_factor_dataset(
        DECISION_DATE,
        _make_market_data(["AAA", "FUT"]),
        _make_universe_snapshot(),
        _make_calendar(),
    )

    assert "FUT" not in set(result["symbol"])


def test_technical_indicator_columns_exist() -> None:
    result = build_factor_dataset(DECISION_DATE, _make_market_data(["AAA"]), _make_universe_snapshot(), _make_calendar())

    for column in ["ma5", "ma10", "ma20", "ma60", "macd_dif", "macd_dea", "macd_hist", "rsi14", "atr14"]:
        assert column in result.columns


def test_benchmark_relative_columns_exist_when_benchmark_is_provided() -> None:
    result = build_factor_dataset(
        DECISION_DATE,
        _make_market_data(["AAA"]),
        _make_universe_snapshot(),
        _make_calendar(),
        benchmark_data=_make_benchmark_data(),
    )

    for column in ["rel_return_5", "rel_return_10", "rel_return_20"]:
        assert column in result.columns
        assert pd.notna(result.loc[0, column])


def test_factor_dataset_output_is_deterministic() -> None:
    market = _make_market_data(["AAA", "BBB"])
    universe = _make_universe_snapshot()
    calendar = _make_calendar()
    benchmark = _make_benchmark_data()

    first = build_factor_dataset(DECISION_DATE, market, universe, calendar, benchmark)
    second = build_factor_dataset(DECISION_DATE, market, universe, calendar, benchmark)

    assert_frame_equal(first, second)


def test_missing_required_columns_raise_clear_errors() -> None:
    market = _make_market_data(["AAA"]).drop(columns=["close"])

    with pytest.raises(ValueError, match="market_data missing required columns"):
        build_factor_dataset(DECISION_DATE, market, _make_universe_snapshot(), _make_calendar())


def test_config_can_include_st_and_suspended_symbols() -> None:
    result = build_factor_dataset(
        DECISION_DATE,
        _make_market_data(["AAA", "STS", "SUS"]),
        _make_universe_snapshot(),
        _make_calendar(),
        config={"exclude_st": False, "exclude_suspended": False},
    )

    assert set(result["symbol"]) == {"AAA", "STS", "SUS"}
    suspended = result.loc[result["symbol"] == "SUS"].iloc[0]
    assert suspended["risk_precheck_status"] == "BLOCK"
    assert "suspended" in suspended["risk_precheck_reason"]


def _required_output_columns() -> list[str]:
    return [
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
        "latest_market_available_time",
        "universe_available_time",
        "data_revision_id",
        "source",
        "universe_eligible",
        "market_data_available",
        "execution_data_available",
        "risk_precheck_status",
        "risk_precheck_reason",
    ]


def _make_calendar() -> TradingCalendar:
    dates = pd.date_range("2024-01-01", periods=90, freq="D")
    return TradingCalendar(
        pd.DataFrame(
            {
                "trade_date": dates,
                "is_trading_day": True,
                "session_open": "09:30",
                "session_close": "15:00",
                "decision_time": "15:30",
                "reason": "normal",
            }
        )
    )


def _make_universe_snapshot() -> pd.DataFrame:
    rows = [
        _universe_row("AAA", "Alpha ETF", is_active=True, is_st=False, is_suspended=False),
        _universe_row("BBB", "Beta ETF", is_active=True, is_st=False, is_suspended=False),
        _universe_row("STS", "ST Stock", is_active=True, is_st=True, is_suspended=False),
        _universe_row("SUS", "Suspended ETF", is_active=True, is_st=False, is_suspended=True),
        _universe_row("INA", "Inactive Stock", is_active=False, is_st=False, is_suspended=False),
        _universe_row(
            "FUT",
            "Future Stock",
            is_active=True,
            is_st=False,
            is_suspended=False,
            as_of_date=DECISION_DATE + pd.Timedelta(days=1),
        ),
    ]
    return pd.DataFrame(rows)


def _universe_row(
    symbol: str,
    name: str,
    *,
    is_active: bool,
    is_st: bool,
    is_suspended: bool,
    as_of_date: pd.Timestamp = DECISION_DATE,
) -> dict:
    return {
        "as_of_date": as_of_date,
        "symbol": symbol,
        "name": name,
        "instrument_type": "ETF" if symbol != "STS" else "stock",
        "exchange": "SSE",
        "listed_date": pd.Timestamp("2023-01-01"),
        "delisted_date": pd.NaT,
        "is_active": is_active,
        "is_st": is_st,
        "is_suspended": is_suspended,
        "industry": "Test Industry",
        "min_lot": 100,
        "t_plus_rule": "t_plus_1",
        "available_time": pd.Timestamp("2024-03-05 09:00:00"),
        "revision_id": "u1",
        "source": "unit-test",
    }


def _make_market_data(symbols: list[str], periods: int = 70) -> pd.DataFrame:
    rows = []
    dates = pd.date_range("2024-01-01", periods=periods, freq="D")
    for symbol_index, symbol in enumerate(symbols):
        offset = symbol_index * 100
        previous_close = None
        for idx, trade_date in enumerate(dates):
            close = 10 + offset + idx
            open_price = close - 0.2
            high = close + 1.0
            low = close - 1.0
            pre_close = previous_close if previous_close is not None else close - 1.0
            rows.append(
                {
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": 1000 + idx * 10 + symbol_index * 100,
                    "amount": (1000 + idx * 10) * close,
                    "pre_close": pre_close,
                    "adj_factor": 1.0,
                    "is_suspended": symbol == "SUS",
                    "limit_up": close * 1.1,
                    "limit_down": close * 0.9,
                    "event_time": trade_date + pd.Timedelta(hours=15),
                    "publish_time": trade_date + pd.Timedelta(hours=15, minutes=5),
                    "ingest_time": trade_date + pd.Timedelta(hours=15, minutes=10),
                    "available_time": trade_date + pd.Timedelta(hours=15, minutes=10),
                    "revision_id": "m1",
                    "source": "unit-test",
                }
            )
            previous_close = close
    return pd.DataFrame(rows)


def _make_benchmark_data(periods: int = 70) -> pd.DataFrame:
    rows = []
    for idx, trade_date in enumerate(pd.date_range("2024-01-01", periods=periods, freq="D")):
        rows.append(
            {
                "symbol": "BENCH",
                "trade_date": trade_date,
                "close": 200 + idx * 2,
                "available_time": trade_date + pd.Timedelta(hours=15, minutes=10),
                "revision_id": "b1",
                "source": "unit-test",
            }
        )
    return pd.DataFrame(rows)
