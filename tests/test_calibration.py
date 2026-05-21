import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quant_replay_system.calibration import (
    DEFAULT_WEIGHT_PROFILES,
    CalibrationParameterSet,
    CalibrationResult,
    build_parameter_grid,
    rank_calibration_results,
    run_parameter_calibration,
)
from quant_replay_system.calendar import TradingCalendar
from quant_replay_system.config import CalibrationSettings, load_settings


DECISION_DATES = [pd.Timestamp("2024-03-01"), pd.Timestamp("2024-03-02")]


def test_parameter_grid_generation_works() -> None:
    grid = build_parameter_grid(
        top_n_values=[1, 2],
        holding_horizon_values=[3],
        min_final_score_values=[60.0],
        weight_profiles={"baseline": DEFAULT_WEIGHT_PROFILES["baseline"]},
        min_action_values=["PAPER_TRADE"],
    )

    assert len(grid) == 2
    assert [item.top_n for item in grid] == [1, 2]
    assert all(item.holding_horizon == 3 for item in grid)
    assert all(item.weight_profile == "baseline" for item in grid)


def test_calibration_runs_multiple_parameter_sets(tmp_path: Path) -> None:
    result = _run_calibration(tmp_path)

    assert isinstance(result, CalibrationResult)
    assert len(result.parameter_sets) == 2
    assert len(result.batch_results) == 2
    assert len(result.ranked_results) == 2


def test_calibration_calls_batch_replay_for_each_parameter_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def fake_run_batch_replay(*args, **kwargs):
        calls.append(kwargs["top_n"])
        return _fake_batch_result(f"batch-{kwargs['top_n']}", total_trades=kwargs["top_n"])

    monkeypatch.setattr("quant_replay_system.calibration.run_batch_replay", fake_run_batch_replay)
    settings = _settings(tmp_path)
    settings = settings.model_copy(
        update={"calibration": settings.calibration.model_copy(update={"write_artifacts": False})}
    )

    result = run_parameter_calibration(
        decision_dates=DECISION_DATES,
        universe_name="calibration_test",
        parameter_sets=_parameter_sets(),
        config=settings,
    )

    assert calls == [2, 2]
    assert len(result.batch_results) == 2


def test_ranked_results_are_sorted_by_objective_score_descending() -> None:
    parameter_sets = _parameter_sets()
    ranked = rank_calibration_results(
        parameter_sets,
        [
            _fake_batch_result("weak", average_return=-0.01, win_rate=0.25, total_trades=3),
            _fake_batch_result("strong", average_return=0.03, win_rate=0.75, total_trades=3),
        ],
        CalibrationSettings(min_trade_count=1),
    )

    scores = ranked["objective_score"].tolist()
    assert scores == sorted(scores, reverse=True)
    assert ranked.iloc[0]["batch_id"] == "strong"


def test_best_parameter_set_is_deterministic(tmp_path: Path) -> None:
    first = _run_calibration(tmp_path)
    second = _run_calibration(tmp_path)

    assert first.best_parameter_set is not None
    assert second.best_parameter_set is not None
    assert first.best_parameter_set.parameter_set_id == second.best_parameter_set.parameter_set_id


def test_low_trade_count_penalty_is_applied() -> None:
    ranked = rank_calibration_results(
        [_parameter_sets()[0]],
        [_fake_batch_result("low", total_trades=1)],
        CalibrationSettings(min_trade_count=4),
    )

    assert ranked.iloc[0]["penalty_for_low_trade_count"] == pytest.approx(75.0)


def test_missing_benchmark_or_excess_fields_are_handled_gracefully() -> None:
    batch = _fake_batch_result("no-benchmark", average_excess_return=None)
    ranked = rank_calibration_results([_parameter_sets()[0]], [batch], CalibrationSettings(min_trade_count=1))

    assert pd.notna(ranked.iloc[0]["normalized_average_excess_return"])
    assert pd.notna(ranked.iloc[0]["objective_score"])


def test_calibration_artifacts_folder_is_created(tmp_path: Path) -> None:
    result = _run_calibration(tmp_path)

    assert result.artifact_paths["artifact_dir"].exists()
    assert result.artifact_paths["artifact_dir"].parent == tmp_path / "calibrations"


def test_ranked_results_csv_is_written_and_readable(tmp_path: Path) -> None:
    result = _run_calibration(tmp_path)

    exported = pd.read_csv(result.artifact_paths["ranked_results"])
    assert len(exported) == len(result.parameter_sets)


def test_parameter_sets_csv_is_written_and_readable(tmp_path: Path) -> None:
    result = _run_calibration(tmp_path)

    exported = pd.read_csv(result.artifact_paths["parameter_sets"])
    assert len(exported) == len(result.parameter_sets)


def test_batch_runs_csv_is_written_and_readable(tmp_path: Path) -> None:
    result = _run_calibration(tmp_path)

    exported = pd.read_csv(result.artifact_paths["batch_runs"])
    assert len(exported) == len(result.batch_results)


def test_aggregate_metrics_csv_is_written_and_readable(tmp_path: Path) -> None:
    result = _run_calibration(tmp_path)

    exported = pd.read_csv(result.artifact_paths["aggregate_metrics"])
    assert "objective_score" in exported.columns


def test_metadata_json_is_written(tmp_path: Path) -> None:
    result = _run_calibration(tmp_path)
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["calibration_id"] == result.calibration_id
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_calibration_report_md_is_written(tmp_path: Path) -> None:
    result = _run_calibration(tmp_path)

    assert result.artifact_paths["calibration_report"].exists()
    assert result.artifact_paths["calibration_report"].name == "calibration_report.md"


def test_report_includes_best_parameter_set(tmp_path: Path) -> None:
    result = _run_calibration(tmp_path)
    content = result.artifact_paths["calibration_report"].read_text(encoding="utf-8")

    assert "## Best Parameter Set" in content
    assert "parameter_set_id" in content
    assert result.best_parameter_set is not None
    assert result.best_parameter_set.parameter_set_id in content


def test_calibration_output_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    first = _run_calibration(tmp_path)
    second = _run_calibration(tmp_path)

    assert first.calibration_id == second.calibration_id
    assert first.best_parameter_set == second.best_parameter_set
    assert_frame_equal(first.ranked_results, second.ranked_results)
    assert_frame_equal(first.parameter_sets_frame, second.parameter_sets_frame)
    assert_frame_equal(first.batch_runs_frame, second.batch_runs_frame)


def test_no_live_trading_or_broker_integration_is_invoked(tmp_path: Path) -> None:
    result = _run_calibration(tmp_path)
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False
    for batch in result.batch_results:
        for replay in batch.replay_results:
            assert replay.audit_metadata["live_trading_enabled"] is False
            assert replay.audit_metadata["broker_api_invoked"] is False


def test_point_in_time_and_replay_contracts_are_not_bypassed(tmp_path: Path) -> None:
    result = _run_calibration(tmp_path)

    for batch in result.batch_results:
        for replay in batch.replay_results:
            assert replay.audit_metadata["point_in_time_rule"] == "available_time <= decision_time"
            latest_market = replay.audit_metadata["latest_market_available_time"]
            if latest_market is not None:
                assert latest_market <= replay.decision_time


def _run_calibration(tmp_path: Path) -> CalibrationResult:
    return run_parameter_calibration(
        decision_dates=DECISION_DATES,
        universe_name="calibration_test",
        parameter_sets=_parameter_sets(),
        config=_settings(tmp_path),
        market_data=_make_market_data(["AAA", "BBB"]),
        universe_snapshot=_make_universe_snapshot(["AAA", "BBB"]),
        benchmark_data=_make_benchmark_data(),
        trading_calendar=_make_calendar(),
        split_name="full",
        train_dates=[pd.Timestamp("2024-03-01")],
        validation_dates=[pd.Timestamp("2024-03-04")],
    )


def _parameter_sets() -> list[CalibrationParameterSet]:
    return [
        CalibrationParameterSet(
            parameter_set_id="baseline",
            scoring_weights=DEFAULT_WEIGHT_PROFILES["baseline"],
            min_final_score=None,
            min_action="NO_TRADE",
            top_n=2,
            holding_horizon=2,
            label="baseline",
            weight_profile="baseline",
        ),
        CalibrationParameterSet(
            parameter_set_id="risk_heavy",
            scoring_weights=DEFAULT_WEIGHT_PROFILES["risk_heavy"],
            min_final_score=None,
            min_action="NO_TRADE",
            top_n=2,
            holding_horizon=2,
            label="risk_heavy",
            weight_profile="risk_heavy",
        ),
    ]


def _fake_batch_result(
    batch_id: str,
    *,
    average_return: float | None = 0.02,
    median_return: float | None = 0.015,
    win_rate: float | None = 0.6,
    best_return: float | None = 0.04,
    worst_return: float | None = -0.01,
    average_excess_return: float | None = 0.005,
    total_trades: int = 3,
) -> SimpleNamespace:
    aggregate = {
        "number_of_requested_dates": 2,
        "number_of_executed_dates": 2,
        "number_of_skipped_dates": 0,
        "number_of_failed_dates": 0,
        "total_candidates": 4,
        "total_simulated_trades": total_trades,
        "total_skipped_trades": 0,
        "average_return": average_return,
        "median_return": median_return,
        "win_rate": win_rate,
        "best_return": best_return,
        "worst_return": worst_return,
        "average_equal_weight_return_by_run": average_return,
        "average_benchmark_return": 0.001,
        "average_excess_return": average_excess_return,
    }
    return SimpleNamespace(
        batch_id=batch_id,
        aggregate_performance=aggregate,
        replay_results=[],
        artifact_paths={},
        warnings=[],
    )


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "replay_run": settings.replay_run.model_copy(
                update={
                    "output_dir": tmp_path / "single_replays",
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
                }
            ),
            "calibration": settings.calibration.model_copy(
                update={
                    "output_dir": tmp_path / "calibrations",
                    "min_trade_count": 1,
                    "write_artifacts": True,
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
