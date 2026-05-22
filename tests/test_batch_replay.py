import json
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quant_replay_system.batch_replay import BatchReplayResult, aggregate_batch_performance, run_batch_replay
from quant_replay_system.calendar import TradingCalendar
from quant_replay_system.config import load_settings


DECISION_DATES = [pd.Timestamp("2024-03-01"), pd.Timestamp("2024-03-02"), pd.Timestamp("2024-03-04")]


@pytest.fixture(scope="module")
def batch_result_bundle(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, BatchReplayResult]:
    tmp_path = tmp_path_factory.mktemp("batch_result")
    return tmp_path, _run_batch(tmp_path)


@pytest.fixture(scope="module")
def batch_result(batch_result_bundle: tuple[Path, BatchReplayResult]) -> BatchReplayResult:
    return batch_result_bundle[1]


@pytest.fixture(scope="module")
def batch_tmp_path(batch_result_bundle: tuple[Path, BatchReplayResult]) -> Path:
    return batch_result_bundle[0]


def test_run_batch_replay_returns_structured_result(batch_result: BatchReplayResult) -> None:
    result = batch_result

    assert isinstance(result, BatchReplayResult)
    assert result.universe_name == "batch_test"
    assert result.top_n == 2
    assert result.holding_horizon == 2
    assert isinstance(result.aggregate_performance, dict)


def test_multiple_decision_dates_collect_replay_results(batch_result: BatchReplayResult) -> None:
    result = batch_result

    assert result.executed_decision_dates == [pd.Timestamp("2024-03-01"), pd.Timestamp("2024-03-04")]
    assert len(result.replay_results) == 2
    assert set(result.batch_index["decision_date"]) == set(result.executed_decision_dates)


def test_non_trading_dates_are_skipped_by_default(batch_result: BatchReplayResult) -> None:
    result = batch_result

    skipped = result.skipped_decision_dates
    assert len(skipped) == 1
    assert skipped.iloc[0]["decision_date"] == pd.Timestamp("2024-03-02")
    assert skipped.iloc[0]["reason"] == "NON_TRADING_DAY"


def test_fail_fast_false_continues_after_date_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original_run_replay = _batch_replay_module().run_replay

    def flaky_run_replay(*args, **kwargs):
        decision_date = pd.Timestamp(kwargs["decision_date"]).normalize()
        if decision_date == pd.Timestamp("2024-03-01"):
            raise RuntimeError("boom")
        return original_run_replay(*args, **kwargs)

    monkeypatch.setattr("quant_replay_system.batch_replay.run_replay", flaky_run_replay)
    result = _run_batch(tmp_path, decision_dates=[pd.Timestamp("2024-03-01"), pd.Timestamp("2024-03-04")])

    assert result.executed_decision_dates == [pd.Timestamp("2024-03-04")]
    failed = result.skipped_decision_dates.loc[result.skipped_decision_dates["reason"] == "RUN_FAILED"]
    assert len(failed) == 1
    assert "boom" in failed.iloc[0]["detail"]


def test_fail_fast_true_raises_on_date_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_run_replay(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("quant_replay_system.batch_replay.run_replay", failing_run_replay)
    settings = _settings(tmp_path)
    settings = settings.model_copy(
        update={"batch_replay": settings.batch_replay.model_copy(update={"fail_fast": True})}
    )

    with pytest.raises(RuntimeError, match="boom"):
        _run_batch(tmp_path, settings=settings, decision_dates=[pd.Timestamp("2024-03-01")])


@pytest.mark.slow
def test_batch_artifact_folder_is_created(batch_result: BatchReplayResult, batch_tmp_path: Path) -> None:
    result = batch_result

    assert result.artifact_paths["artifact_dir"].exists()
    assert result.artifact_paths["artifact_dir"].parent == batch_tmp_path / "batch_replays"


@pytest.mark.slow
def test_batch_report_md_is_written(batch_result: BatchReplayResult) -> None:
    result = batch_result

    assert result.artifact_paths["batch_report"].exists()
    assert result.artifact_paths["batch_report"].name == "batch_report.md"


@pytest.mark.slow
def test_batch_index_csv_is_written_and_readable(batch_result: BatchReplayResult) -> None:
    result = batch_result

    exported = pd.read_csv(result.artifact_paths["batch_index"])
    assert len(exported) == len(result.replay_results)


@pytest.mark.slow
def test_aggregate_performance_csv_is_written_and_readable(batch_result: BatchReplayResult) -> None:
    result = batch_result

    exported = pd.read_csv(result.artifact_paths["aggregate_performance"])
    assert exported.iloc[0]["number_of_executed_dates"] == len(result.replay_results)


@pytest.mark.slow
def test_replay_runs_csv_is_written_and_readable(batch_result: BatchReplayResult) -> None:
    result = batch_result

    exported = pd.read_csv(result.artifact_paths["replay_runs"])
    assert len(exported) == len(result.replay_results)


@pytest.mark.slow
def test_skipped_dates_csv_is_written_when_dates_are_skipped(batch_result: BatchReplayResult) -> None:
    result = batch_result

    exported = pd.read_csv(result.artifact_paths["skipped_dates"])
    assert exported.iloc[0]["reason"] == "NON_TRADING_DAY"


@pytest.mark.slow
def test_metadata_json_is_written(batch_result: BatchReplayResult) -> None:
    result = batch_result
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["batch_id"] == result.batch_id
    assert metadata["universe_name"] == "batch_test"
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


@pytest.mark.slow
def test_batch_id_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    first = _run_batch(tmp_path)
    second = _run_batch(tmp_path)

    assert first.batch_id == second.batch_id
    assert first.artifact_paths["artifact_dir"] == second.artifact_paths["artifact_dir"]


def test_aggregate_performance_calculations_are_correct_on_mock_results(batch_result: BatchReplayResult) -> None:
    result = batch_result
    expected_equal_weight = pd.Series(
        [
            replay.performance_summary["total_equal_weight_return"]
            for replay in result.replay_results
            if replay.performance_summary["total_equal_weight_return"] is not None
        ],
        dtype="float64",
    ).mean()
    recomputed = aggregate_batch_performance(
        result.replay_results,
        requested_count=3,
        skipped_dates=result.skipped_decision_dates,
    )

    assert recomputed["number_of_requested_dates"] == 3
    assert recomputed["number_of_executed_dates"] == 2
    assert recomputed["number_of_skipped_dates"] == 1
    assert recomputed["total_candidates"] == sum(
        replay.performance_summary["number_of_candidates"] for replay in result.replay_results
    )
    assert recomputed["average_equal_weight_return_by_run"] == pytest.approx(expected_equal_weight)


@pytest.mark.slow
def test_batch_output_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    first = _run_batch(tmp_path)
    second = _run_batch(tmp_path)

    assert first.aggregate_performance == second.aggregate_performance
    assert_frame_equal(first.batch_index, second.batch_index)
    assert_frame_equal(first.replay_runs_frame, second.replay_runs_frame)
    assert_frame_equal(first.skipped_decision_dates, second.skipped_decision_dates)


def test_no_live_trading_or_broker_integration_is_invoked(batch_result: BatchReplayResult) -> None:
    result = batch_result

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False
    for replay in result.replay_results:
        assert replay.audit_metadata["live_trading_enabled"] is False
        assert replay.audit_metadata["broker_api_invoked"] is False


def test_batch_replay_can_run_with_portfolio_simulation_enabled(batch_result: BatchReplayResult) -> None:
    result = batch_result

    assert result.portfolio_result is not None
    assert result.portfolio_result.artifact_paths["portfolio_report"].exists()


def test_batch_replay_can_run_with_portfolio_simulation_disabled(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    settings = settings.model_copy(
        update={"batch_replay": settings.batch_replay.model_copy(update={"enable_portfolio_simulation": False})}
    )
    result = _run_batch(tmp_path, settings=settings)

    assert result.portfolio_result is None
    assert result.aggregate_performance["portfolio_simulation_enabled"] is False


def test_batch_index_includes_portfolio_metrics_when_enabled(batch_result: BatchReplayResult) -> None:
    result = batch_result

    assert "portfolio_total_return" in result.batch_index.columns
    assert result.batch_index["portfolio_simulation_enabled"].all()
    assert result.batch_index["portfolio_report_path"].notna().all()


def test_aggregate_performance_includes_portfolio_metrics_when_enabled(batch_result: BatchReplayResult) -> None:
    result = batch_result

    assert result.aggregate_performance["portfolio_initial_cash"] == 10_000.0
    assert result.aggregate_performance["portfolio_final_equity"] is not None
    assert result.aggregate_performance["portfolio_total_return"] is not None


def test_batch_metadata_records_portfolio_simulation_settings(batch_result: BatchReplayResult) -> None:
    result = batch_result
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["portfolio_simulation_enabled"] is True
    assert metadata["config_summary"]["portfolio_simulation"]["enabled"] is True
    assert metadata["config_summary"]["portfolio_simulation"]["initial_cash"] == 10_000.0
    assert "portfolio_report" in metadata["portfolio_artifact_paths"]


@pytest.mark.slow
def test_batch_report_contains_portfolio_performance_section(batch_result: BatchReplayResult) -> None:
    result = batch_result
    content = result.artifact_paths["batch_report"].read_text(encoding="utf-8")

    assert "## Portfolio Performance Summary" in content
    assert "portfolio_total_return" in content


def _batch_replay_module():
    import quant_replay_system.batch_replay as module

    return module


def _run_batch(
    tmp_path: Path,
    *,
    settings=None,
    decision_dates: list[pd.Timestamp] | None = None,
) -> BatchReplayResult:
    return run_batch_replay(
        decision_dates=decision_dates or DECISION_DATES,
        universe_name="batch_test",
        top_n=2,
        holding_horizon=2,
        config=settings or _settings(tmp_path),
        market_data=_make_market_data(["AAA", "BBB"]),
        universe_snapshot=_make_universe_snapshot(["AAA", "BBB"]),
        benchmark_data=_make_benchmark_data(),
        trading_calendar=_make_calendar(),
    )


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "replay_run": settings.replay_run.model_copy(
                update={
                    "output_dir": tmp_path / "replay_runs",
                    "min_action": "NO_TRADE",
                    "min_final_score": None,
                    "default_top_n": 2,
                    "default_holding_horizon": 2,
                }
            ),
            "batch_replay": settings.batch_replay.model_copy(
                update={
                    "output_dir": tmp_path / "batch_replays",
                    "default_top_n": 2,
                    "default_holding_horizon": 2,
                    "enable_portfolio_simulation": True,
                }
            ),
            "portfolio_simulation": settings.portfolio_simulation.model_copy(
                update={
                    "output_dir": tmp_path / "portfolio_simulations",
                    "initial_cash": 10_000.0,
                    "max_gross_exposure": 0.60,
                    "max_position_weight": 0.20,
                    "reserve_cash_pct": 0.40,
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
                "as_of_date": pd.Timestamp("2024-03-01"),
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
