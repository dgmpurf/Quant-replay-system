from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.snapshot_quality_preflight import (
    SnapshotQualityPreflightError,
    SnapshotQualityPreflightResult,
)


def test_cli_replay_accepts_snapshot_manifest(tmp_path: Path, monkeypatch, capsys) -> None:
    manifest = _manifest(tmp_path)
    calls = {}

    def fake_run_replay(*args, **kwargs):
        calls.update(kwargs)
        assert kwargs["config"].snapshot_quality_preflight.enabled is True
        assert Path(kwargs["snapshot_manifest_path"]) == manifest
        return _fake_replay_result(status="PASS")

    monkeypatch.setattr("quant_replay_system.cli.run_replay", fake_run_replay)

    code = cli.main(["replay-run", "--date", "2024-01-03", "--snapshot-manifest", str(manifest)])
    output = capsys.readouterr()

    assert code == 0
    assert calls
    assert "Snapshot quality status: PASS" in output.out
    assert "Snapshot quality report path:" in output.out


def test_cli_batch_replay_accepts_snapshot_manifest(tmp_path: Path, monkeypatch, capsys) -> None:
    manifest = _manifest(tmp_path)

    def fake_batch_replay(*args, **kwargs):
        assert kwargs["config"].snapshot_quality_preflight.enabled is True
        assert Path(kwargs["snapshot_manifest_path"]) == manifest
        return _fake_batch_result(status="PASS")

    monkeypatch.setattr("quant_replay_system.cli.run_batch_replay", fake_batch_replay)

    code = cli.main(["batch-replay", "--dates", "2024-01-03,2024-01-04", "--snapshot-manifest", str(manifest)])
    output = capsys.readouterr()

    assert code == 0
    assert "batch_id:" in output.out
    assert "Snapshot quality status: PASS" in output.out


def test_cli_calibration_accepts_snapshot_manifest(tmp_path: Path, monkeypatch, capsys) -> None:
    manifest = _manifest(tmp_path)

    def fake_calibration(*args, **kwargs):
        assert kwargs["config"].snapshot_quality_preflight.enabled is True
        assert Path(kwargs["snapshot_manifest_path"]) == manifest
        return _fake_calibration_result(status="PASS")

    monkeypatch.setattr("quant_replay_system.cli.run_parameter_calibration", fake_calibration)

    code = cli.main(["parameter-calibration", "--dates", "2024-01-03", "--snapshot-manifest", str(manifest)])
    output = capsys.readouterr()

    assert code == 0
    assert "calibration_id:" in output.out
    assert "Snapshot quality status: PASS" in output.out


def test_cli_walk_forward_accepts_snapshot_manifest(tmp_path: Path, monkeypatch, capsys) -> None:
    manifest = _manifest(tmp_path)

    def fake_walk_forward(*args, **kwargs):
        assert kwargs["config"].snapshot_quality_preflight.enabled is True
        assert Path(kwargs["snapshot_manifest_path"]) == manifest
        return _fake_walk_forward_result(status="PASS")

    monkeypatch.setattr("quant_replay_system.cli.run_walk_forward_validation", fake_walk_forward)

    code = cli.main(
        [
            "walk-forward",
            "--train-dates",
            "2024-01-03",
            "--validation-dates",
            "2024-01-04",
            "--snapshot-manifest",
            str(manifest),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "walk_forward_id:" in output.out
    assert "Snapshot quality status: PASS" in output.out


def test_snapshot_manifest_enables_preflight_by_default(tmp_path: Path, monkeypatch) -> None:
    manifest = _manifest(tmp_path)

    def fake_run_replay(*args, **kwargs):
        assert kwargs["config"].snapshot_quality_preflight.enabled is True
        return _fake_replay_result(status="PASS")

    monkeypatch.setattr("quant_replay_system.cli.run_replay", fake_run_replay)

    assert cli.main(["replay", "--date", "2024-01-03", "--snapshot-manifest", str(manifest)]) == 0


def test_disable_snapshot_preflight_forces_disabled_behavior(tmp_path: Path, monkeypatch) -> None:
    manifest = _manifest(tmp_path)

    def fake_run_replay(*args, **kwargs):
        assert kwargs["config"].snapshot_quality_preflight.enabled is False
        return _fake_replay_result(status=None, enabled=False)

    monkeypatch.setattr("quant_replay_system.cli.run_replay", fake_run_replay)

    code = cli.main(
        [
            "replay-run",
            "--date",
            "2024-01-03",
            "--snapshot-manifest",
            str(manifest),
            "--disable-snapshot-preflight",
        ]
    )

    assert code == 0


def test_preflight_fail_exits_nonzero_by_default(tmp_path: Path, monkeypatch, capsys) -> None:
    manifest = _manifest(tmp_path)

    def fake_run_replay(*args, **kwargs):
        raise SnapshotQualityPreflightError(
            "Snapshot quality preflight blocked replay-run",
            _preflight_result("FAIL"),
        )

    monkeypatch.setattr("quant_replay_system.cli.run_replay", fake_run_replay)

    code = cli.main(["replay-run", "--date", "2024-01-03", "--snapshot-manifest", str(manifest)])
    output = capsys.readouterr()

    assert code == 1
    assert "Snapshot quality status: FAIL" in output.out
    assert "ERROR: Snapshot quality preflight blocked replay-run" in output.err


def test_preflight_fail_continues_when_allow_fail_is_set(tmp_path: Path, monkeypatch, capsys) -> None:
    manifest = _manifest(tmp_path)

    def fake_run_replay(*args, **kwargs):
        assert kwargs["config"].snapshot_quality_preflight.block_on_fail is False
        return _fake_replay_result(status="FAIL", warnings=["required dataset failed"])

    monkeypatch.setattr("quant_replay_system.cli.run_replay", fake_run_replay)

    code = cli.main(
        [
            "replay-run",
            "--date",
            "2024-01-03",
            "--snapshot-manifest",
            str(manifest),
            "--allow-fail",
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Snapshot quality status: FAIL" in output.out
    assert "WARNING: required dataset failed" in output.out


def test_preflight_warn_continues_when_allow_warn_is_set(tmp_path: Path, monkeypatch, capsys) -> None:
    manifest = _manifest(tmp_path)

    def fake_run_replay(*args, **kwargs):
        assert kwargs["config"].snapshot_quality_preflight.block_on_warn is False
        return _fake_replay_result(status="WARN", warnings=["optional dataset failed"])

    monkeypatch.setattr("quant_replay_system.cli.run_replay", fake_run_replay)

    code = cli.main(
        [
            "replay-run",
            "--date",
            "2024-01-03",
            "--snapshot-manifest",
            str(manifest),
            "--allow-warn",
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Snapshot quality status: WARN" in output.out
    assert "WARNING: optional dataset failed" in output.out


def test_preflight_warn_exits_nonzero_when_block_on_warn_is_set(tmp_path: Path, monkeypatch, capsys) -> None:
    manifest = _manifest(tmp_path)

    def fake_run_replay(*args, **kwargs):
        assert kwargs["config"].snapshot_quality_preflight.block_on_warn is True
        raise SnapshotQualityPreflightError(
            "Snapshot quality preflight blocked replay-run",
            _preflight_result("WARN"),
        )

    monkeypatch.setattr("quant_replay_system.cli.run_replay", fake_run_replay)

    code = cli.main(
        [
            "replay-run",
            "--date",
            "2024-01-03",
            "--snapshot-manifest",
            str(manifest),
            "--block-on-warn",
        ]
    )
    output = capsys.readouterr()

    assert code == 1
    assert "Snapshot quality status: WARN" in output.out
    assert "ERROR: Snapshot quality preflight blocked replay-run" in output.err


def test_cli_prints_no_live_trading_statement(tmp_path: Path, monkeypatch, capsys) -> None:
    manifest = _manifest(tmp_path)

    def fake_run_replay(*args, **kwargs):
        return _fake_replay_result(status="PASS")

    monkeypatch.setattr("quant_replay_system.cli.run_replay", fake_run_replay)

    code = cli.main(["replay-run", "--date", "2024-01-03", "--snapshot-manifest", str(manifest)])
    output = capsys.readouterr()

    assert code == 0
    assert "No live trading or broker API was invoked." in output.out


def test_cli_does_not_invoke_live_trading_or_network(tmp_path: Path, monkeypatch) -> None:
    manifest = _manifest(tmp_path)

    def fake_run_replay(*args, **kwargs):
        assert kwargs["config"].snapshot_quality_preflight.enabled is True
        return _fake_replay_result(status="PASS")

    monkeypatch.setattr("quant_replay_system.cli.run_replay", fake_run_replay)

    assert cli.main(["replay-run", "--date", "2024-01-03", "--snapshot-manifest", str(manifest)]) == 0


def _manifest(tmp_path: Path) -> Path:
    path = tmp_path / "snapshot_manifest.json"
    path.write_text("{}", encoding="utf-8")
    return path


def _preflight_metadata(status: str | None, *, enabled: bool = True, warnings: list[str] | None = None) -> dict:
    return {
        "snapshot_quality_preflight_enabled": enabled,
        "snapshot_quality_status": status,
        "snapshot_quality_report_path": Path("snapshot_quality_gate_report.md") if enabled else None,
        "snapshot_quality_gate_id": "gate123" if enabled else None,
        "snapshot_quality_warnings": warnings or [],
    }


def _preflight_result(status: str) -> SnapshotQualityPreflightResult:
    return SnapshotQualityPreflightResult(
        enabled=True,
        status=status,
        report_path=Path("snapshot_quality_gate_report.md"),
        quality_gate_id="gate123",
        warnings=[f"preflight {status.lower()}"],
    )


def _fake_replay_result(
    *,
    status: str | None,
    enabled: bool = True,
    warnings: list[str] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        run_id="replay123",
        decision_date=pd.Timestamp("2024-01-03"),
        report_path=Path("report.md"),
        performance_summary={"number_of_candidates": 2, "number_of_simulated_buys": 1},
        audit_metadata=_preflight_metadata(status, enabled=enabled, warnings=warnings),
        warnings=[],
    )


def _fake_batch_result(*, status: str) -> SimpleNamespace:
    return SimpleNamespace(
        batch_id="batch123",
        artifact_paths={"batch_report": Path("batch_report.md")},
        executed_decision_dates=[pd.Timestamp("2024-01-03")],
        skipped_decision_dates=pd.DataFrame(),
        snapshot_quality_preflight=_preflight_metadata(status),
        warnings=[],
    )


def _fake_calibration_result(*, status: str) -> SimpleNamespace:
    return SimpleNamespace(
        calibration_id="calibration123",
        artifact_paths={"calibration_report": Path("calibration_report.md")},
        parameter_sets=[SimpleNamespace(parameter_set_id="baseline")],
        best_parameter_set=SimpleNamespace(parameter_set_id="baseline"),
        snapshot_quality_preflight=_preflight_metadata(status),
        warnings=[],
    )


def _fake_walk_forward_result(*, status: str) -> SimpleNamespace:
    return SimpleNamespace(
        walk_forward_id="walk123",
        artifact_paths={"walk_forward_report": Path("walk_forward_report.md")},
        selected_parameter_set=SimpleNamespace(parameter_set_id="baseline"),
        snapshot_quality_preflight=_preflight_metadata(status),
        warnings=[],
    )
