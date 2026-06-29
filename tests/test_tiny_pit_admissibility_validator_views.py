from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

from quant_replay_system.tiny_pit_admissibility_validator import (
    SAFETY_FALSE_FLAGS,
    TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED,
    build_synthetic_validator_artifacts,
)
from quant_replay_system.tiny_pit_admissibility_validator_health import (
    check_tiny_pit_admissibility_validator_health,
)
from quant_replay_system.tiny_pit_admissibility_validator_index import (
    build_tiny_pit_admissibility_validator_index,
)
from quant_replay_system.tiny_pit_admissibility_validator_status import (
    VIEWS_NEXT_ACTION,
    run_tiny_pit_admissibility_validator_status,
)


def _root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "tiny_pit_admissibility_validator_v0_1"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_index_discovers_run_ignores_view_dirs_and_reports_malformed_metadata(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run = build_synthetic_validator_artifacts(output_dir=root)
    (root / "index").mkdir(parents=True)
    (root / "health").mkdir()
    (root / "status").mkdir()
    malformed = root / "malformed_run"
    malformed.mkdir()
    (malformed / "metadata.json").write_text("{bad json", encoding="utf-8")

    result = build_tiny_pit_admissibility_validator_index(root=root, output_dir=root / "index")
    rows = _read_csv(result.artifact_paths["index_csv"])

    assert result.artifact_count == 1
    assert result.latest_validator_run_id == run.validator_run_id
    assert result.latest_status == "PASS"
    assert result.latest_workflow_stage == TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED
    assert result.latest_case_count == 14
    assert result.latest_pass_candidate_count == 1
    assert result.latest_warning_count > 0
    assert result.latest_blocker_count > 0
    assert result.warnings
    assert rows[0]["validator_run_id"] == run.validator_run_id
    assert rows[0]["report_only"] == "True"
    assert rows[0]["diagnostic_only"] == "True"
    assert rows[0]["synthetic_only"] == "True"
    assert not any(row["validator_run_id"] in {"index", "health", "status"} for row in rows)


def test_health_passes_for_valid_run_and_fails_for_forbidden_mutations(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run = build_synthetic_validator_artifacts(output_dir=root)

    healthy = check_tiny_pit_admissibility_validator_health(root=root, output_dir=root / "health")
    assert healthy.status == "PASS"
    assert healthy.checked_artifact_count == 1
    assert healthy.issue_count == 0

    safety = json.loads(run.artifact_paths["safety_flags"].read_text(encoding="utf-8"))
    safety["trading_allowed"] = True
    run.artifact_paths["safety_flags"].write_text(json.dumps(safety, indent=2), encoding="utf-8")
    unhealthy = check_tiny_pit_admissibility_validator_health(root=root, output_dir=root / "health_bad_flag")
    assert unhealthy.status == "FAIL"
    assert "FORBIDDEN_SAFETY_FLAG_TRUE" in {row["issue_code"] for row in unhealthy.health_frame.to_dict("records")}


def test_health_fails_for_invalid_status_missing_artifact_and_active_flags(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run = build_synthetic_validator_artifacts(output_dir=root)

    metadata = json.loads(run.artifact_paths["metadata"].read_text(encoding="utf-8"))
    metadata["status"] = "ACTIVE_REPLAY_INPUT_READY"
    metadata["active_replay_input"] = True
    metadata["data_raw_written"] = True
    run.artifact_paths["metadata"].write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    invalid = check_tiny_pit_admissibility_validator_health(root=root, output_dir=root / "health_invalid")
    issue_codes = {row["issue_code"] for row in invalid.health_frame.to_dict("records")}
    assert invalid.status == "FAIL"
    assert "INVALID_STATUS" in issue_codes
    assert "FORBIDDEN_METADATA_FLAG_TRUE" in issue_codes

    missing_root = _root(tmp_path / "missing")
    missing_run = build_synthetic_validator_artifacts(output_dir=missing_root)
    missing_run.artifact_paths["report"].unlink()
    missing = check_tiny_pit_admissibility_validator_health(
        root=missing_root,
        output_dir=missing_root / "health",
    )
    assert missing.status == "FAIL"
    assert "MISSING_REQUIRED_ARTIFACT" in {row["issue_code"] for row in missing.health_frame.to_dict("records")}


def test_status_selects_latest_and_preserves_safe_boundaries(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = build_synthetic_validator_artifacts(output_dir=root)
    first_metadata = json.loads(first.artifact_paths["metadata"].read_text(encoding="utf-8"))
    first_metadata["validator_run_id"] = "aaa_first"
    first_metadata["created_at"] = "2026-01-01T00:00:00Z"
    first.artifact_paths["metadata"].write_text(json.dumps(first_metadata, indent=2), encoding="utf-8")

    second = build_synthetic_validator_artifacts(
        output_dir=root,
        package_cases=[
            {
                "case_id": "custom_valid",
                "case_name": "valid_diagnostic_only_package",
                "blocker_count": 0,
                "warning_count": 0,
                "forbidden_interpretation": "Synthetic diagnostic case only.",
                "limitation_note": "Second run for deterministic latest selection.",
            }
        ],
    )
    second_metadata = json.loads(second.artifact_paths["metadata"].read_text(encoding="utf-8"))
    second_metadata["validator_run_id"] = "zzz_second"
    second_metadata["created_at"] = "2026-02-01T00:00:00Z"
    second.artifact_paths["metadata"].write_text(json.dumps(second_metadata, indent=2), encoding="utf-8")

    status = run_tiny_pit_admissibility_validator_status(root=root, output_dir=root / "status")

    assert status.latest_tiny_pit_admissibility_validator_id == "zzz_second"
    assert status.latest_tiny_pit_admissibility_validator_status == "PASS"
    assert status.latest_tiny_pit_admissibility_validator_health_status == "PASS"
    assert status.latest_tiny_pit_admissibility_validator_workflow_stage == (
        TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED
    )
    assert status.latest_tiny_pit_admissibility_validator_report_only is True
    assert status.latest_tiny_pit_admissibility_validator_diagnostic_only is True
    assert status.latest_tiny_pit_admissibility_validator_synthetic_only is True
    assert status.latest_tiny_pit_admissibility_validator_active_replay_input is False
    assert status.latest_tiny_pit_admissibility_validator_trading_allowed is False
    assert status.recommended_next_task == VIEWS_NEXT_ACTION
    assert "Post-Checkpoint Governance Audit" in status.recommended_next_task
    for flag in SAFETY_FALSE_FLAGS:
        assert getattr(status, flag) is False


def test_cli_core_index_health_status_smoke_remains_report_only(tmp_path: Path) -> None:
    root = _root(tmp_path)
    env = {**os.environ, "PYTHONPATH": "src"}

    core = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "tiny-pit-admissibility-validator",
            "--output-dir",
            str(root),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "status: PASS" in core.stdout
    assert "workflow_stage: TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED" in core.stdout
    assert "active_replay_input: False" in core.stdout
    assert "trading_allowed: False" in core.stdout

    index = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "tiny-pit-admissibility-validator-index",
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
    assert "latest_status: PASS" in index.stdout

    health = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "tiny-pit-admissibility-validator-health",
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
            "tiny-pit-admissibility-validator-status",
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
    assert "latest_tiny_pit_admissibility_validator_status: PASS" in status.stdout
    assert "latest_tiny_pit_admissibility_validator_active_replay_input: False" in status.stdout
    assert "latest_tiny_pit_admissibility_validator_trading_allowed: False" in status.stdout
    assert "buy_review_allowed: False" in status.stdout
    assert "ACTIVE_REPLAY_INPUT_READY" not in status.stdout
    assert "trading_allowed: True" not in status.stdout
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()
