import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from quant_replay_system import batch_replay as batch_module
from quant_replay_system import calibration as calibration_module
from quant_replay_system import walk_forward as walk_module
from quant_replay_system.calibration import DEFAULT_WEIGHT_PROFILES, CalibrationParameterSet
from quant_replay_system.config import load_settings
from quant_replay_system.replay_run import run_replay
from quant_replay_system.snapshot_quality_preflight import (
    SnapshotQualityPreflightError,
    SnapshotQualityPreflightResult,
    run_snapshot_quality_preflight,
)


def test_run_replay_unchanged_when_preflight_disabled(tmp_path: Path) -> None:
    result = run_replay("2024-01-03", config=_settings(tmp_path))

    assert result.audit_metadata["snapshot_quality_preflight_enabled"] is False
    assert result.audit_metadata["snapshot_quality_status"] is None


def test_run_replay_executes_preflight_when_enabled(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)
    settings = _settings(tmp_path, preflight_enabled=True, manifest_path=manifest)

    result = run_replay("2024-01-03", config=settings)

    assert result.audit_metadata["snapshot_quality_preflight_enabled"] is True
    assert result.audit_metadata["snapshot_quality_status"] == "PASS"
    assert Path(result.audit_metadata["snapshot_quality_report_path"]).exists()
    assert result.audit_metadata["snapshot_quality_gate_id"]


def test_run_replay_blocks_on_fail_when_configured(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, bad_market=True)
    settings = _settings(tmp_path, preflight_enabled=True, manifest_path=manifest)

    with pytest.raises(SnapshotQualityPreflightError, match="blocked run_replay: status=FAIL"):
        run_replay("2024-01-03", config=settings)


def test_run_replay_continues_on_warn_when_not_blocking(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, bad_benchmark=True)
    settings = _settings(tmp_path, preflight_enabled=True, manifest_path=manifest, block_on_warn=False)

    result = run_replay("2024-01-03", config=settings)

    assert result.audit_metadata["snapshot_quality_status"] == "WARN"
    assert any("Snapshot quality preflight warning" in warning for warning in result.warnings)


def test_run_replay_blocks_on_warn_when_configured(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, bad_benchmark=True)
    settings = _settings(tmp_path, preflight_enabled=True, manifest_path=manifest, block_on_warn=True)

    with pytest.raises(SnapshotQualityPreflightError, match="blocked run_replay: status=WARN"):
        run_replay("2024-01-03", config=settings)


def test_run_batch_replay_executes_preflight_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = _write_manifest(tmp_path)
    settings = _settings(tmp_path, preflight_enabled=True, manifest_path=manifest)
    settings = settings.model_copy(
        update={"batch_replay": settings.batch_replay.model_copy(update={"enable_portfolio_simulation": False})}
    )
    calls = []

    original_gate = _preflight_module().run_snapshot_quality_gate

    def counting_gate(*args, **kwargs):
        calls.append(args[0])
        return original_gate(*args, **kwargs)

    def fake_run_replay(*args, **kwargs):
        assert kwargs["config"].snapshot_quality_preflight.enabled is False
        return _fake_replay_result(pd.Timestamp(kwargs["decision_date"]).normalize())

    monkeypatch.setattr("quant_replay_system.snapshot_quality_preflight.run_snapshot_quality_gate", counting_gate)
    monkeypatch.setattr("quant_replay_system.batch_replay.run_replay", fake_run_replay)

    result = batch_module.run_batch_replay(
        ["2024-01-03", "2024-01-04"],
        config=settings,
        market_data=pd.DataFrame(),
        universe_snapshot=pd.DataFrame(),
        trading_calendar=_calendar(),
    )

    assert len(calls) == 1
    assert result.snapshot_quality_preflight["snapshot_quality_status"] == "PASS"


def test_run_batch_replay_blocks_on_fail(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, bad_market=True)
    settings = _settings(tmp_path, preflight_enabled=True, manifest_path=manifest)

    with pytest.raises(SnapshotQualityPreflightError, match="blocked run_batch_replay: status=FAIL"):
        batch_module.run_batch_replay(["2024-01-03"], config=settings, trading_calendar=_calendar())


def test_calibration_executes_preflight_before_parameter_grid_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = {"preflight_done": False}
    settings = _settings(tmp_path, preflight_enabled=True, manifest_path=tmp_path / "manifest.json")

    def fake_preflight(*args, **kwargs):
        state["preflight_done"] = True
        return SnapshotQualityPreflightResult(enabled=True, status="PASS", warnings=[])

    def fake_grid(*args, **kwargs):
        assert state["preflight_done"] is True
        return [_parameter_set()]

    def fake_batch(*args, **kwargs):
        assert kwargs["config"].snapshot_quality_preflight.enabled is False
        return _fake_batch_result("calibration-batch")

    monkeypatch.setattr("quant_replay_system.calibration.run_snapshot_quality_preflight", fake_preflight)
    monkeypatch.setattr("quant_replay_system.calibration.build_parameter_grid", fake_grid)
    monkeypatch.setattr("quant_replay_system.calibration.run_batch_replay", fake_batch)

    result = calibration_module.run_parameter_calibration(
        decision_dates=["2024-01-03"],
        config=settings,
    )

    assert result.snapshot_quality_preflight["snapshot_quality_status"] == "PASS"


def test_walk_forward_executes_preflight_before_calibration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = {"preflight_done": False}
    settings = _settings(tmp_path, preflight_enabled=True, manifest_path=tmp_path / "manifest.json")
    settings = settings.model_copy(
        update={
            "walk_forward": settings.walk_forward.model_copy(
                update={"min_train_dates": 1, "min_validation_dates": 1, "require_test": False}
            )
        }
    )

    def fake_preflight(*args, **kwargs):
        state["preflight_done"] = True
        return SnapshotQualityPreflightResult(enabled=True, status="PASS", warnings=[])

    def fake_calibration(*args, **kwargs):
        assert state["preflight_done"] is True
        assert kwargs["config"].snapshot_quality_preflight.enabled is False
        parameter_sets = list(kwargs["parameter_sets"])
        return _fake_calibration_result(parameter_sets[0])

    monkeypatch.setattr("quant_replay_system.walk_forward.run_snapshot_quality_preflight", fake_preflight)
    monkeypatch.setattr("quant_replay_system.walk_forward.run_parameter_calibration", fake_calibration)

    result = walk_module.run_walk_forward_validation(
        train_dates=["2024-01-03"],
        validation_dates=["2024-01-04"],
        universe_name="wf",
        parameter_sets=[_parameter_set()],
        config=settings,
    )

    assert result.snapshot_quality_preflight["snapshot_quality_status"] == "PASS"


def test_metadata_includes_snapshot_quality_fields_when_enabled(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)
    settings = _settings(tmp_path, preflight_enabled=True, manifest_path=manifest)

    result = run_replay("2024-01-03", config=settings)
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["audit_metadata"]["snapshot_quality_preflight_enabled"] is True
    assert metadata["audit_metadata"]["snapshot_quality_status"] == "PASS"
    assert metadata["audit_metadata"]["snapshot_quality_report_path"]


def test_missing_manifest_path_when_enabled_raises_clear_error(tmp_path: Path) -> None:
    settings = _settings(tmp_path, preflight_enabled=True, manifest_path=None)

    with pytest.raises(SnapshotQualityPreflightError, match="no manifest_path was provided"):
        run_snapshot_quality_preflight(settings, context="unit-test")


def test_no_live_trading_or_broker_integration_is_invoked(tmp_path: Path) -> None:
    result = run_replay("2024-01-03", config=_settings(tmp_path))

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False


def test_no_network_calls_are_made(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)
    settings = _settings(tmp_path, preflight_enabled=True, manifest_path=manifest)

    result = run_snapshot_quality_preflight(settings, context="unit-test")

    assert result.gate_result is not None
    assert result.gate_result.audit_metadata["snapshot_quality_only"] is True


def _settings(
    tmp_path: Path,
    *,
    preflight_enabled: bool = False,
    manifest_path: Path | None = None,
    block_on_warn: bool = False,
):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "snapshot_quality_gate": settings.snapshot_quality_gate.model_copy(
                update={"output_dir": tmp_path / "snapshot_quality"}
            ),
            "snapshot_quality_preflight": settings.snapshot_quality_preflight.model_copy(
                update={
                    "enabled": preflight_enabled,
                    "manifest_path": manifest_path,
                    "block_on_warn": block_on_warn,
                }
            ),
            "replay_run": settings.replay_run.model_copy(
                update={
                    "output_dir": tmp_path / "replay_runs",
                    "min_action": "NO_TRADE",
                    "min_final_score": None,
                    "default_top_n": 2,
                    "default_holding_horizon": 1,
                }
            ),
            "batch_replay": settings.batch_replay.model_copy(
                update={
                    "output_dir": tmp_path / "batch_replays",
                    "enable_portfolio_simulation": False,
                }
            ),
            "calibration": settings.calibration.model_copy(
                update={"output_dir": tmp_path / "calibrations", "write_artifacts": False}
            ),
            "walk_forward": settings.walk_forward.model_copy(
                update={"output_dir": tmp_path / "walk_forward", "write_artifacts": False}
            ),
        }
    )


def _write_manifest(tmp_path: Path, *, bad_market: bool = False, bad_benchmark: bool = False) -> Path:
    data_dir = tmp_path / "snapshot"
    data_dir.mkdir(parents=True, exist_ok=True)
    market = pd.read_csv("data/mock/prices.csv")
    if bad_market:
        market.loc[0, "close"] = -1
    market_path = data_dir / "market.csv"
    market.to_csv(market_path, index=False)

    benchmark_path = None
    if bad_benchmark:
        benchmark = market.iloc[[0]].copy()
        benchmark["symbol"] = "BENCH"
        benchmark.loc[benchmark.index[0], "high"] = 0.01
        benchmark_path = data_dir / "benchmark.csv"
        benchmark.to_csv(benchmark_path, index=False)

    payload = {
        "snapshot_id": "preflight-test",
        "created_at": "2024-01-03T00:00:00",
        "market_path": str(market_path),
        "universe_path": str(Path("data/mock/universe_snapshots.csv").resolve()),
        "trading_calendar_path": str(Path("data/mock/trading_calendar.csv").resolve()),
        "source": "TEST",
        "revision_id": "v1",
    }
    if benchmark_path is not None:
        payload["benchmark_path"] = str(benchmark_path)
    manifest = tmp_path / "snapshot_manifest.json"
    manifest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return manifest


def _calendar():
    return SimpleNamespace(
        is_trading_day=lambda date: True,
        frame=pd.DataFrame(),
    )


def _fake_replay_result(decision_date: pd.Timestamp):
    return SimpleNamespace(
        decision_date=decision_date,
        run_id=f"run-{decision_date.date()}",
        artifact_paths={
            "report": Path("report.md"),
            "candidates": Path("candidates.csv"),
            "simulated_trades": Path("simulated_trades.csv"),
        },
        report_path=Path("report.md"),
        performance_summary={
            "number_of_candidates": 1,
            "number_of_simulated_buys": 1,
            "number_of_skipped_buys": 0,
            "average_return": 0.01,
            "win_rate": 1.0,
            "benchmark_return": None,
            "excess_return": None,
        },
        warnings=[],
        simulated_trades=pd.DataFrame([{"trade_return": 0.01, "trade_status": "FILLED"}]),
        selected_candidates=pd.DataFrame([{"symbol": "AAA"}]),
        decision_time=decision_date + pd.Timedelta(hours=15, minutes=30),
        universe_name="default",
        top_n=1,
        holding_horizon=1,
        factor_dataset_row_count=0,
        scored_dataset_row_count=0,
    )


def _fake_batch_result(batch_id: str):
    return SimpleNamespace(
        batch_id=batch_id,
        aggregate_performance={
            "number_of_requested_dates": 1,
            "number_of_executed_dates": 1,
            "number_of_skipped_dates": 0,
            "number_of_failed_dates": 0,
            "total_candidates": 1,
            "total_simulated_trades": 1,
            "total_skipped_trades": 0,
            "average_return": 0.01,
            "median_return": 0.01,
            "win_rate": 1.0,
            "best_return": 0.01,
            "worst_return": 0.01,
            "average_equal_weight_return_by_run": 0.01,
            "average_benchmark_return": None,
            "average_excess_return": None,
        },
        replay_results=[],
        artifact_paths={},
        warnings=[],
    )


def _fake_calibration_result(parameter_set: CalibrationParameterSet):
    ranked = pd.DataFrame(
        [
            {
                "parameter_set_id": parameter_set.parameter_set_id,
                "ranking_score": 60.0,
                "objective_score": 60.0,
                "average_return": 0.01,
                "portfolio_total_return": 0.01,
                "portfolio_max_drawdown": -0.01,
                "portfolio_number_of_trades": 3,
                "total_trades": 3,
            }
        ]
    )
    return SimpleNamespace(
        calibration_id="fake-calibration",
        parameter_sets=[parameter_set],
        best_parameter_set=parameter_set,
        ranked_results=ranked,
        warnings=[],
        batch_results=[],
    )


def _parameter_set() -> CalibrationParameterSet:
    return CalibrationParameterSet(
        parameter_set_id="baseline",
        scoring_weights=DEFAULT_WEIGHT_PROFILES["baseline"],
        min_final_score=None,
        min_action="NO_TRADE",
        top_n=1,
        holding_horizon=1,
        label="baseline",
        weight_profile="baseline",
    )


def _preflight_module():
    import quant_replay_system.snapshot_quality_preflight as module

    return module
