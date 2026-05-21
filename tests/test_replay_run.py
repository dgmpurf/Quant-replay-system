from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

from quant_replay_system.calendar import TradingCalendar
from quant_replay_system.config import load_settings
from quant_replay_system.replay_run import ReplayRunResult, run_replay


DECISION_DATE = pd.Timestamp("2024-03-01")
DECISION_TIME = pd.Timestamp("2024-03-01 15:30:00")


def test_run_replay_returns_structured_result(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert isinstance(result, ReplayRunResult)
    assert result.decision_date == DECISION_DATE
    assert result.decision_time == DECISION_TIME
    assert result.universe_name == "unit_test"
    assert isinstance(result.performance_summary, dict)
    assert isinstance(result.audit_metadata, dict)


def test_run_replay_builds_factor_dataset(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result.factor_dataset_row_count == len(result.factor_dataset)
    assert result.factor_dataset_row_count > 0
    assert {"decision_date", "symbol", "latest_market_available_time"}.issubset(result.factor_dataset.columns)


def test_run_replay_scores_candidates(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result.scored_dataset_row_count == len(result.scored_dataset)
    assert {"final_score", "score_action", "score_breakdown", "score_reason"}.issubset(result.scored_dataset.columns)


def test_run_replay_selects_candidates_sorted_by_final_score(tmp_path: Path) -> None:
    result = _run(tmp_path, top_n=3)

    scores = result.selected_candidates["final_score"].tolist()
    assert scores == sorted(scores, reverse=True)
    assert len(result.selected_candidates) <= 3


def test_run_replay_simulates_t_plus_1_buy_date(tmp_path: Path) -> None:
    result = _run(tmp_path, top_n=2)

    assert not result.simulated_trades.empty
    assert set(result.simulated_trades["buy_date"]) == {pd.Timestamp("2024-03-04")}


def test_run_replay_uses_trading_day_holding_horizon(tmp_path: Path) -> None:
    result = _run(tmp_path, top_n=2, holding_horizon=2)

    filled_or_skipped = result.simulated_trades
    filled = filled_or_skipped.loc[filled_or_skipped["trade_status"] == "FILLED"]
    assert not filled.empty
    assert set(filled["planned_sell_date"]) == {pd.Timestamp("2024-03-07")}


def test_blocked_buys_are_recorded_as_skipped_trades(tmp_path: Path) -> None:
    market = _make_market_data(["AAA"])
    market.loc[
        (market["symbol"] == "AAA") & (market["trade_date"] == pd.Timestamp("2024-03-04")),
        "open",
    ] = market.loc[
        (market["symbol"] == "AAA") & (market["trade_date"] == pd.Timestamp("2024-03-04")),
        "limit_up",
    ]

    result = _run(tmp_path, market_data=market)
    skipped = result.simulated_trades.loc[result.simulated_trades["trade_status"] == "SKIPPED_BUY"]

    assert not skipped.empty
    assert "limit-up" in skipped.iloc[0]["buy_reason"]


def test_report_file_is_written(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result.report_path.exists()
    assert result.report_path.parent == tmp_path


def test_report_contains_candidate_table_and_performance_summary(tmp_path: Path) -> None:
    result = _run(tmp_path)
    content = result.report_path.read_text(encoding="utf-8")

    assert "## 3. Candidate Table" in content
    assert "## 6. Performance Summary" in content
    assert "| symbol | final_score | action |" in content


def test_run_replay_output_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    market = _make_market_data(["AAA", "BBB"])
    universe = _make_universe_snapshot(["AAA", "BBB"])
    benchmark = _make_benchmark_data()
    calendar = _make_calendar()
    settings = _settings(tmp_path)

    first = run_replay(
        DECISION_DATE,
        universe_name="unit_test",
        top_n=2,
        holding_horizon=2,
        config=settings,
        market_data=market,
        universe_snapshot=universe,
        benchmark_data=benchmark,
        trading_calendar=calendar,
        report_output_path=tmp_path / "first.md",
    )
    second = run_replay(
        DECISION_DATE,
        universe_name="unit_test",
        top_n=2,
        holding_horizon=2,
        config=settings,
        market_data=market,
        universe_snapshot=universe,
        benchmark_data=benchmark,
        trading_calendar=calendar,
        report_output_path=tmp_path / "second.md",
    )

    assert_frame_equal(first.factor_dataset, second.factor_dataset)
    assert_frame_equal(first.scored_dataset, second.scored_dataset)
    assert_frame_equal(first.selected_candidates, second.selected_candidates)
    assert_frame_equal(first.simulated_trades, second.simulated_trades)
    assert first.performance_summary == second.performance_summary


def test_no_live_trading_or_broker_integration_is_invoked(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False


def test_no_future_factor_data_is_used(tmp_path: Path) -> None:
    market = _make_market_data(["AAA"])
    future_revision = market.loc[
        (market["symbol"] == "AAA") & (market["trade_date"] == DECISION_DATE)
    ].tail(1).copy()
    future_revision["close"] = 9999.0
    future_revision["available_time"] = pd.Timestamp("2024-03-01 16:00:00")
    future_revision["revision_id"] = "m2"
    market = pd.concat([market, future_revision], ignore_index=True)

    result = _run(tmp_path, market_data=market)

    assert result.audit_metadata["latest_market_available_time"] <= DECISION_TIME
    assert 9999.0 not in set(result.factor_dataset["close"])


def _run(
    tmp_path: Path,
    *,
    top_n: int = 2,
    holding_horizon: int = 2,
    market_data: pd.DataFrame | None = None,
) -> ReplayRunResult:
    symbols = ["AAA", "BBB"] if market_data is None else sorted(market_data["symbol"].unique())
    return run_replay(
        DECISION_DATE,
        universe_name="unit_test",
        top_n=top_n,
        holding_horizon=holding_horizon,
        config=_settings(tmp_path),
        market_data=market_data if market_data is not None else _make_market_data(symbols),
        universe_snapshot=_make_universe_snapshot(symbols),
        benchmark_data=_make_benchmark_data(),
        trading_calendar=_make_calendar(),
        report_output_path=tmp_path / "replay_report.md",
    )


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "replay_run": settings.replay_run.model_copy(
                update={
                    "output_dir": tmp_path,
                    "min_action": "NO_TRADE",
                    "min_final_score": None,
                    "default_top_n": 2,
                    "default_holding_horizon": 2,
                }
            ),
            "candidate_selection": settings.candidate_selection.model_copy(update={"exclude_blocked": True}),
        }
    )


def _make_calendar() -> TradingCalendar:
    dates = pd.date_range("2024-01-01", "2024-03-15", freq="D")
    rows = []
    for date in dates:
        is_weekend = date.weekday() >= 5
        is_holiday = date == pd.Timestamp("2024-03-06")
        is_trading = not is_weekend and not is_holiday
        rows.append(
            {
                "trade_date": date,
                "is_trading_day": is_trading,
                "session_open": "09:30" if is_trading else "",
                "session_close": "15:00" if is_trading else "",
                "decision_time": "15:30" if is_trading else "",
                "reason": "normal" if is_trading else ("holiday" if is_holiday else "weekend"),
            }
        )
    return TradingCalendar(pd.DataFrame(rows))


def _make_universe_snapshot(symbols: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "as_of_date": DECISION_DATE,
                "symbol": symbol,
                "name": f"{symbol} Fund",
                "instrument_type": "ETF",
                "exchange": "SSE",
                "listed_date": pd.Timestamp("2023-01-01"),
                "delisted_date": pd.NaT,
                "is_active": True,
                "is_st": False,
                "is_suspended": False,
                "industry": "Test",
                "min_lot": 100,
                "t_plus_rule": "t_plus_1",
                "available_time": pd.Timestamp("2024-03-01 09:00:00"),
                "revision_id": "u1",
                "source": "unit-test",
            }
            for symbol in symbols
        ]
    )


def _make_market_data(symbols: list[str]) -> pd.DataFrame:
    rows = []
    dates = pd.bdate_range("2024-01-01", "2024-03-15")
    dates = dates[dates != pd.Timestamp("2024-03-06")]
    for symbol_index, symbol in enumerate(symbols):
        offset = symbol_index * 25
        previous_close = None
        for idx, trade_date in enumerate(dates):
            close = 20 + offset + idx * (1.0 + symbol_index * 0.1)
            open_price = close - 0.25
            high = close + 0.8
            low = close - 0.8
            pre_close = previous_close if previous_close is not None else close - 1.0
            rows.append(
                {
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": 1_000_000 + idx * 1_000 + symbol_index * 5_000,
                    "amount": 50_000_000 + idx * 500_000 + symbol_index * 1_000_000,
                    "pre_close": pre_close,
                    "adj_factor": 1.0,
                    "is_suspended": False,
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


def _make_benchmark_data() -> pd.DataFrame:
    rows = []
    for idx, trade_date in enumerate(pd.bdate_range("2024-01-01", "2024-03-15")):
        if trade_date == pd.Timestamp("2024-03-06"):
            continue
        rows.append(
            {
                "symbol": "BENCH",
                "trade_date": trade_date,
                "close": 100 + idx * 0.5,
                "available_time": trade_date + pd.Timedelta(hours=15, minutes=10),
                "revision_id": "b1",
                "source": "unit-test",
            }
        )
    return pd.DataFrame(rows)
