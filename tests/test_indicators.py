import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quant_replay_system.indicators import compute_technical_indicators, compute_technical_score


def test_ma_calculation_correctness() -> None:
    market = _make_market_data(["AAA"], periods=70)

    result = compute_technical_indicators(market)
    row_5 = result.loc[result["trade_date"] == pd.Timestamp("2024-01-05")].iloc[0]
    row_20 = result.loc[result["trade_date"] == pd.Timestamp("2024-01-20")].iloc[0]
    row_60 = result.loc[result["trade_date"] == pd.Timestamp("2024-02-29")].iloc[0]

    assert row_5["ma5"] == pytest.approx(np.mean([10, 11, 12, 13, 14]))
    assert row_20["ma20"] == pytest.approx(np.mean(range(10, 30)))
    assert row_60["ma60"] == pytest.approx(np.mean(range(10, 70)))


def test_macd_columns_exist_and_are_numeric() -> None:
    market = _make_market_data(["AAA"], periods=40)

    result = compute_technical_indicators(market)

    for column in ["macd_dif", "macd_dea", "macd_histogram"]:
        assert column in result.columns
        assert pd.api.types.is_numeric_dtype(result[column])


def test_rsi_is_between_zero_and_one_hundred() -> None:
    market = _make_market_data(["AAA"], periods=40)

    result = compute_technical_indicators(market)
    rsi = result["rsi_14"].dropna()

    assert not rsi.empty
    assert rsi.between(0, 100).all()


def test_atr_is_non_negative() -> None:
    market = _make_market_data(["AAA"], periods=40)

    result = compute_technical_indicators(market)
    atr = result["atr_14"].dropna()

    assert not atr.empty
    assert (atr >= 0).all()


def test_volume_ratio_20_is_calculated_correctly() -> None:
    market = _make_market_data(["AAA"], periods=25)

    result = compute_technical_indicators(market)
    row_20 = result.loc[result["trade_date"] == pd.Timestamp("2024-01-20")].iloc[0]
    expected_volume_ma20 = np.mean([1000 + idx * 10 for idx in range(20)])

    assert row_20["volume_ma20"] == pytest.approx(expected_volume_ma20)
    assert row_20["volume_ratio_20"] == pytest.approx((1000 + 19 * 10) / expected_volume_ma20)


def test_indicators_are_grouped_by_symbol_without_cross_symbol_leak() -> None:
    market = _make_market_data(["AAA", "BBB"], periods=10)

    result = compute_technical_indicators(market)
    aaa_row_5 = result.loc[
        (result["symbol"] == "AAA") & (result["trade_date"] == pd.Timestamp("2024-01-05"))
    ].iloc[0]
    bbb_row_5 = result.loc[
        (result["symbol"] == "BBB") & (result["trade_date"] == pd.Timestamp("2024-01-05"))
    ].iloc[0]

    assert aaa_row_5["ma5"] == pytest.approx(np.mean([10, 11, 12, 13, 14]))
    assert bbb_row_5["ma5"] == pytest.approx(np.mean([110, 111, 112, 113, 114]))


def test_relative_strength_aligns_with_benchmark_dates() -> None:
    market = _make_market_data(["AAA"], periods=30)
    benchmark = _make_benchmark_data(periods=30)

    result = compute_technical_indicators(market, benchmark_df=benchmark)
    row_20 = result.loc[result["trade_date"] == pd.Timestamp("2024-01-21")].iloc[0]
    symbol_return = (30 / 10) - 1.0
    benchmark_return = (240 / 200) - 1.0

    assert row_20["return_20d"] == pytest.approx(symbol_return)
    assert row_20["benchmark_return_20d"] == pytest.approx(benchmark_return)
    assert row_20["relative_return_20d"] == pytest.approx(symbol_return - benchmark_return)


def test_indicators_do_not_use_records_after_decision_time() -> None:
    market = _make_market_data(["AAA"], periods=21)
    market.loc[market["trade_date"] == pd.Timestamp("2024-01-21"), "close"] = 10_000.0
    market.loc[
        market["trade_date"] == pd.Timestamp("2024-01-21"),
        "available_time",
    ] = pd.Timestamp("2024-01-21 16:00:00")

    result = compute_technical_indicators(market, decision_time="2024-01-20 15:30:00")

    assert result["trade_date"].max() == pd.Timestamp("2024-01-20")
    row_20 = result.loc[result["trade_date"] == pd.Timestamp("2024-01-20")].iloc[0]
    assert row_20["ma20"] == pytest.approx(np.mean(range(10, 30)))


def test_missing_available_time_raises_existing_validation_error() -> None:
    market = _make_market_data(["AAA"], periods=5).drop(columns=["available_time"])

    with pytest.raises(ValueError, match="available_time"):
        compute_technical_indicators(market, decision_time="2024-01-05 15:30:00")


def test_indicator_calculation_is_deterministic_for_same_input() -> None:
    market = _make_market_data(["AAA", "BBB"], periods=30)
    benchmark = _make_benchmark_data(periods=30)

    first = compute_technical_indicators(market, decision_time="2024-01-30 15:30:00", benchmark_df=benchmark)
    second = compute_technical_indicators(market, decision_time="2024-01-30 15:30:00", benchmark_df=benchmark)

    assert_frame_equal(first, second)


def test_technical_score_v01_is_optional_and_separate() -> None:
    market = _make_market_data(["AAA"], periods=25)
    indicators = compute_technical_indicators(market)

    scored = compute_technical_score(indicators)

    assert "technical_score_v01" not in indicators.columns
    assert "technical_score_v01" in scored.columns
    assert pd.api.types.is_numeric_dtype(scored["technical_score_v01"])


def _make_market_data(symbols: list[str], periods: int) -> pd.DataFrame:
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
                    "is_suspended": False,
                    "limit_up": close * 1.1,
                    "limit_down": close * 0.9,
                    "event_time": trade_date + pd.Timedelta(hours=15),
                    "publish_time": trade_date + pd.Timedelta(hours=15, minutes=5),
                    "ingest_time": trade_date + pd.Timedelta(hours=15, minutes=10),
                    "available_time": trade_date + pd.Timedelta(hours=15, minutes=10),
                    "revision_id": "r1",
                    "source": "test",
                }
            )
            previous_close = close
    return pd.DataFrame(rows)


def _make_benchmark_data(periods: int) -> pd.DataFrame:
    rows = []
    for idx, trade_date in enumerate(pd.date_range("2024-01-01", periods=periods, freq="D")):
        close = 200 + idx * 2
        rows.append(
            {
                "symbol": "BENCH",
                "trade_date": trade_date,
                "close": close,
                "available_time": trade_date + pd.Timedelta(hours=15, minutes=10),
                "revision_id": "r1",
                "source": "test",
            }
        )
    return pd.DataFrame(rows)
