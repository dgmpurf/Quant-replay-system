from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

from quant_replay_system.tiny_pit_reviewed_package_fixture import (
    SAFETY_FALSE_FLAGS,
    TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY,
    build_tiny_pit_reviewed_package_fixture_artifacts,
)
from quant_replay_system.tiny_pit_reviewed_package_fixture_health import (
    check_tiny_pit_reviewed_package_fixture_health,
)
from quant_replay_system.tiny_pit_reviewed_package_fixture_index import (
    build_tiny_pit_reviewed_package_fixture_index,
)
from quant_replay_system.tiny_pit_reviewed_package_fixture_status import (
    VIEWS_NEXT_ACTION,
    run_tiny_pit_reviewed_package_fixture_status,
)


def _root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "tiny_pit_reviewed_package_fixture_v0_1"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _metadata(path: Path) -> dict[str, object]:
    return json.loads((path / "metadata.json").read_text(encoding="utf-8"))


def _write_metadata(path: Path, metadata: dict[str, object]) -> None:
    (path / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_run(tmp_path: Path):
    return build_tiny_pit_reviewed_package_fixture_artifacts(output_root=_root(tmp_path))


def test_index_discovers_run_ignores_view_dirs_and_reports_malformed_metadata(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run = build_tiny_pit_reviewed_package_fixture_artifacts(output_root=root)
    (root / "index").mkdir(parents=True)
    (root / "health").mkdir()
    (root / "status").mkdir()
    malformed = root / "malformed_run"
    malformed.mkdir()
    (malformed / "metadata.json").write_text("{bad json", encoding="utf-8")

    result = build_tiny_pit_reviewed_package_fixture_index(root=root, output_dir=root / "index")
    rows = _read_csv(result.artifact_paths["index_csv"])

    assert result.artifact_count == 1
    assert result.latest_fixture_id == run.fixture_id
    assert result.latest_status == TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY
    assert result.latest_health_status == "PASS"
    assert result.latest_workflow_stage == TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY
    assert result.latest_case_count == 15
    assert result.latest_blocker_count > 0
    assert result.latest_warning_count > 0
    assert result.warnings
    assert rows[0]["fixture_id"] == run.fixture_id
    assert rows[0]["report_only"] == "True"
    assert rows[0]["diagnostic_only"] == "True"
    assert rows[0]["synthetic_only"] == "True"
    assert rows[0]["real_reviewed_csv_package_created"] == "False"
    assert rows[0]["active_reviewed_input_candidate_created"] == "False"
    assert rows[0]["active_replay_input"] == "False"
    assert rows[0]["trading_allowed"] == "False"
    assert not any(row["fixture_id"] in {"index", "health", "status"} for row in rows)


def test_health_passes_for_valid_synthetic_fixture_run(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _build_run(tmp_path)

    result = check_tiny_pit_reviewed_package_fixture_health(root=root, output_dir=root / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0
    assert result.error_count == 0


def test_health_fails_for_forbidden_downstream_safety_flag(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run = _build_run(tmp_path)
    flags = json.loads(run.artifact_paths["forbidden_downstream_flags"].read_text(encoding="utf-8"))
    flags["trading_allowed"] = True
    run.artifact_paths["forbidden_downstream_flags"].write_text(json.dumps(flags, indent=2), encoding="utf-8")

    result = check_tiny_pit_reviewed_package_fixture_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert "FORBIDDEN_SAFETY_FLAG_TRUE" in {row["issue_code"] for row in result.health_frame.to_dict("records")}


def test_health_fails_for_forbidden_metadata_flags(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run = _build_run(tmp_path)
    metadata = _metadata(run.artifact_path)
    for flag in [
        "real_reviewed_csv_package_created",
        "active_reviewed_input_candidate_created",
        "active_replay_input",
        "active_replay_input_ready_emitted",
        "trading_allowed",
        "data_raw_written",
        "data_processed_written",
        "data_cache_written",
    ]:
        metadata[flag] = True
    _write_metadata(run.artifact_path, metadata)

    result = check_tiny_pit_reviewed_package_fixture_health(root=root, output_dir=root / "health")
    issue_codes = {row["issue_code"] for row in result.health_frame.to_dict("records")}

    assert result.status == "FAIL"
    assert "FORBIDDEN_METADATA_FLAG_TRUE" in issue_codes


def test_health_fails_for_invalid_status_missing_artifact_and_active_ready_wording(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run = _build_run(tmp_path)
    metadata = _metadata(run.artifact_path)
    metadata["status"] = "ACTIVE_REPLAY_INPUT_READY"
    _write_metadata(run.artifact_path, metadata)
    run.artifact_paths["report"].write_text("This would grant ACTIVE_REPLAY_INPUT_READY permission.", encoding="utf-8")
    run.artifact_paths["reviewed_source_manifest"].unlink()

    result = check_tiny_pit_reviewed_package_fixture_health(root=root, output_dir=root / "health")
    issue_codes = {row["issue_code"] for row in result.health_frame.to_dict("records")}

    assert result.status == "FAIL"
    assert "INVALID_STATUS" in issue_codes
    assert "MISSING_REQUIRED_ARTIFACT" in issue_codes
    assert "FORBIDDEN_ACTIVE_READY_TEXT" in issue_codes


def test_status_selects_latest_artifact_deterministically_and_preserves_safe_boundaries(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = _build_run(tmp_path)
    first_metadata = _metadata(first.artifact_path)
    first_metadata["fixture_id"] = "aaa_first"
    first_metadata["created_at"] = "2026-01-01T00:00:00Z"
    _write_metadata(first.artifact_path, first_metadata)

    second = _build_run(tmp_path)
    second_metadata = _metadata(second.artifact_path)
    second_metadata["fixture_id"] = "zzz_second"
    second_metadata["created_at"] = "2026-02-01T00:00:00Z"
    _write_metadata(second.artifact_path, second_metadata)

    result = run_tiny_pit_reviewed_package_fixture_status(root=root, output_dir=root / "status")

    assert result.latest_tiny_pit_reviewed_package_fixture_id == "zzz_second"
    assert result.latest_tiny_pit_reviewed_package_fixture_status == TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY
    assert result.latest_tiny_pit_reviewed_package_fixture_health_status == "PASS"
    assert result.latest_tiny_pit_reviewed_package_fixture_workflow_stage == TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY
    assert result.latest_tiny_pit_reviewed_package_fixture_report_only is True
    assert result.latest_tiny_pit_reviewed_package_fixture_diagnostic_only is True
    assert result.latest_tiny_pit_reviewed_package_fixture_synthetic_only is True
    assert result.latest_tiny_pit_reviewed_package_fixture_real_reviewed_csv_package_created is False
    assert result.latest_tiny_pit_reviewed_package_fixture_active_reviewed_input_candidate_created is False
    assert result.latest_tiny_pit_reviewed_package_fixture_active_replay_input is False
    assert result.latest_tiny_pit_reviewed_package_fixture_trading_allowed is False
    assert result.recommended_next_task == VIEWS_NEXT_ACTION
    assert "Research-Status and Checkpoint" in result.recommended_next_task


def test_cli_core_index_health_status_smoke_remains_report_only(tmp_path: Path) -> None:
    root = _root(tmp_path)
    env = {**os.environ, "PYTHONPATH": "src"}

    core = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "tiny-pit-reviewed-package-fixture",
            "--output-root",
            str(root),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "status: TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY" in core.stdout
    assert "health_status: PASS" in core.stdout
    assert "active_replay_input: False" in core.stdout
    assert "trading_allowed: False" in core.stdout

    index = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "tiny-pit-reviewed-package-fixture-index",
            "--root",
            str(root),
            "--output-dir",
            str(root / "index"),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "latest_status: TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY" in index.stdout

    health = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "tiny-pit-reviewed-package-fixture-health",
            "--root",
            str(root),
            "--output-dir",
            str(root / "health"),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "health_status: PASS" in health.stdout

    status = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "tiny-pit-reviewed-package-fixture-status",
            "--root",
            str(root),
            "--output-dir",
            str(root / "status"),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "latest_tiny_pit_reviewed_package_fixture_status: TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY" in status.stdout
    assert "latest_tiny_pit_reviewed_package_fixture_active_replay_input: False" in status.stdout
    assert "latest_tiny_pit_reviewed_package_fixture_trading_allowed: False" in status.stdout
    assert "ACTIVE_REPLAY_INPUT_READY,true" not in status.stdout
    assert "trading_allowed: True" not in status.stdout
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()


def test_no_artifact_writes_to_data_or_docs_project_sources(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _build_run(tmp_path)
    build_tiny_pit_reviewed_package_fixture_index(root=root, output_dir=root / "index")
    check_tiny_pit_reviewed_package_fixture_health(root=root, output_dir=root / "health")
    run_tiny_pit_reviewed_package_fixture_status(root=root, output_dir=root / "status")

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()
    assert not Path("docs/project_sources").exists()


def test_status_no_artifact_case_is_non_active(tmp_path: Path) -> None:
    root = _root(tmp_path)

    result = run_tiny_pit_reviewed_package_fixture_status(root=root, output_dir=root / "status")

    assert result.latest_tiny_pit_reviewed_package_fixture_status == "NO_PACKAGE_FIXTURE"
    assert result.latest_tiny_pit_reviewed_package_fixture_active_replay_input is False
    assert result.latest_tiny_pit_reviewed_package_fixture_trading_allowed is False
    for flag in SAFETY_FALSE_FLAGS:
        assert getattr(result, flag) is False
