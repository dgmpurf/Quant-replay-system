from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system.tiny_pit_admissibility_validator_contract_fixture import (
    SAFETY_FALSE_FLAGS,
    TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED,
    build_tiny_pit_admissibility_validator_contract_fixture,
)
from quant_replay_system.tiny_pit_admissibility_validator_contract_fixture_health import (
    check_tiny_pit_admissibility_validator_contract_fixture_health,
)
from quant_replay_system.tiny_pit_admissibility_validator_contract_fixture_index import (
    NO_TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE,
    build_tiny_pit_admissibility_validator_contract_fixture_index,
)
from quant_replay_system.tiny_pit_admissibility_validator_contract_fixture_status import (
    TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_INVALID,
    VIEWS_NEXT_ACTION,
    run_tiny_pit_admissibility_validator_contract_fixture_status,
)


FORBIDDEN_FUTURE_STATUSES = {
    "ACTIVE_REPLAY_INPUT_READY",
    "REAL_REPLAY_READY",
    "FORWARD_LABEL_READY",
    "TRAINING_READY",
    "STOCK_PROFILE_READY",
    "BUY_REVIEW_READY",
}


def test_index_discovers_latest_fixture_and_preserves_summary(tmp_path: Path) -> None:
    fixture = build_tiny_pit_admissibility_validator_contract_fixture(output_dir=tmp_path)
    metadata = json.loads(fixture.artifact_paths["metadata"].read_text(encoding="utf-8"))
    metadata["tiny_pit_admissibility_validator_contract_fixture_id"] = "885637683024"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    result = build_tiny_pit_admissibility_validator_contract_fixture_index(
        root=tmp_path,
        output_dir=tmp_path / "index",
    )
    row = result.index_frame.iloc[0].to_dict()
    written = pd.read_csv(result.artifact_paths["index_csv"], dtype=str).fillna("")

    assert result.artifact_count == 1
    assert result.latest_fixture_id == "885637683024"
    assert result.latest_status == "PASS"
    assert result.latest_workflow_stage == TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED
    assert result.latest_health_status == "PASS"
    assert row["case_count"] == 12
    assert row["package_section_count"] == 12
    assert row["gate_group_count"] == 24
    assert row["timing_rule_count"] == 10
    assert row["validation_issue_count"] == 0
    assert written.loc[0, "tiny_pit_admissibility_validator_contract_fixture_id"] == "885637683024"
    assert written.loc[0, "report_path"].endswith("tiny_pit_admissibility_validator_contract_fixture_report.md")


def test_index_empty_root_reports_no_input_stage(tmp_path: Path) -> None:
    result = build_tiny_pit_admissibility_validator_contract_fixture_index(
        root=tmp_path / "missing",
        output_dir=tmp_path / "index",
    )

    assert result.artifact_count == 0
    assert result.latest_status == "NO_INPUT"
    assert result.latest_workflow_stage == NO_TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE
    assert result.latest_health_status == "PASS"


def test_health_passes_for_valid_fixture_and_fails_for_forbidden_flag(tmp_path: Path) -> None:
    fixture = build_tiny_pit_admissibility_validator_contract_fixture(output_dir=tmp_path)
    healthy = check_tiny_pit_admissibility_validator_contract_fixture_health(
        root=tmp_path,
        output_dir=tmp_path / "health",
    )

    assert healthy.status == "PASS"
    assert healthy.checked_artifact_count == 1
    assert healthy.issue_count == 0

    metadata = json.loads(fixture.artifact_paths["metadata"].read_text(encoding="utf-8"))
    metadata["pit_admissibility_validator_implemented"] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    unhealthy = check_tiny_pit_admissibility_validator_contract_fixture_health(
        root=tmp_path,
        output_dir=tmp_path / "health_bad",
    )
    assert unhealthy.status == "FAIL"
    assert "FORBIDDEN_METADATA_FLAG_TRUE" in set(unhealthy.health_frame["issue_code"])


def test_health_detects_missing_artifacts_counts_and_forbidden_statuses(tmp_path: Path) -> None:
    fixture = build_tiny_pit_admissibility_validator_contract_fixture(output_dir=tmp_path)
    fixture.artifact_paths["limitations"].unlink()

    missing = check_tiny_pit_admissibility_validator_contract_fixture_health(
        root=tmp_path,
        output_dir=tmp_path / "health_missing",
    )
    assert missing.status == "FAIL"
    assert "MISSING_REQUIRED_ARTIFACT" in set(missing.health_frame["issue_code"])

    second = build_tiny_pit_admissibility_validator_contract_fixture(output_dir=tmp_path / "second")
    metadata = json.loads(second.artifact_paths["metadata"].read_text(encoding="utf-8"))
    metadata["case_count"] = 11
    second.artifact_paths["metadata"].write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    bad_count = check_tiny_pit_admissibility_validator_contract_fixture_health(
        root=tmp_path / "second",
        output_dir=tmp_path / "health_bad_count",
    )
    assert bad_count.status == "FAIL"
    assert "CASE_COUNT_NOT_12" in set(bad_count.health_frame["issue_code"])

    statuses = pd.read_csv(second.artifact_paths["output_status_contract"], dtype=str).fillna("")
    statuses.loc[len(statuses)] = {
        "status_name": "ACTIVE_REPLAY_INPUT_READY",
        "meaning": "unsafe active-ready status",
        "runtime_status": "PASS",
        "active_replay_input_allowed": "True",
        "labels_allowed": "False",
        "training_allowed": "False",
        "stock_profile_allowed": "False",
        "buy_review_allowed": "False",
        "trading_allowed": "False",
        "notes": "should fail",
    }
    statuses.to_csv(second.artifact_paths["output_status_contract"], index=False)
    forbidden_status = check_tiny_pit_admissibility_validator_contract_fixture_health(
        root=tmp_path / "second",
        output_dir=tmp_path / "health_forbidden_status",
    )
    assert forbidden_status.status == "FAIL"
    assert "FORBIDDEN_FUTURE_STATUS_PRESENT" in set(forbidden_status.health_frame["issue_code"])


def test_status_reports_latest_context_and_forbidden_flags_false(tmp_path: Path) -> None:
    fixture = build_tiny_pit_admissibility_validator_contract_fixture(output_dir=tmp_path)
    status = run_tiny_pit_admissibility_validator_contract_fixture_status(
        root=tmp_path,
        output_dir=tmp_path / "status",
    )

    assert status.latest_fixture_id == fixture.tiny_pit_admissibility_validator_contract_fixture_id
    assert status.status == "PASS"
    assert status.status != TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED
    assert status.workflow_stage == TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED
    assert status.health_status == "PASS"
    assert status.case_count == 12
    assert status.package_section_count == 12
    assert status.gate_group_count == 24
    assert status.timing_rule_count == 10
    assert status.validation_issue_count == 0
    assert status.report_only is True
    assert status.diagnostic_only is True
    assert status.forbidden_future_status_present is False
    assert status.next_action == VIEWS_NEXT_ACTION
    for flag in SAFETY_FALSE_FLAGS:
        assert getattr(status, flag) is False


def test_status_handles_no_artifact_and_invalid_health(tmp_path: Path) -> None:
    empty = run_tiny_pit_admissibility_validator_contract_fixture_status(
        root=tmp_path / "missing",
        output_dir=tmp_path / "status_empty",
    )
    assert empty.status == "NO_INPUT"
    assert empty.workflow_stage == NO_TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE
    assert empty.health_status == "PASS"

    fixture = build_tiny_pit_admissibility_validator_contract_fixture(output_dir=tmp_path / "bad")
    metadata = json.loads(fixture.artifact_paths["metadata"].read_text(encoding="utf-8"))
    metadata["status"] = TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    invalid = run_tiny_pit_admissibility_validator_contract_fixture_status(
        root=tmp_path / "bad",
        output_dir=tmp_path / "status_invalid",
    )
    assert invalid.status == "FAIL"
    assert invalid.workflow_stage == TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_INVALID
    assert invalid.health_status == "FAIL"


def test_cli_view_commands_run_and_remain_report_only(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "tiny_pit_fixture"
    env = {**os.environ, "PYTHONPATH": "src"}

    core = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "tiny-pit-admissibility-validator-contract-fixture",
            "--output-dir",
            str(root),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "status: PASS" in core.stdout

    index = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "tiny-pit-admissibility-validator-contract-fixture-index",
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
    assert "case_count: 12" in index.stdout

    health = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "tiny-pit-admissibility-validator-contract-fixture-health",
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
            "tiny-pit-admissibility-validator-contract-fixture-status",
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
    assert "status: PASS" in status.stdout
    assert f"workflow_stage: {TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED}" in status.stdout
    assert "pit_admissibility_validator_implemented: False" in status.stdout
    assert "real_replay_input_created: False" in status.stdout
    assert "real_forward_labels_created: False" in status.stdout
    assert "model_training_performed: False" in status.stdout
    assert "trading_allowed: False" in status.stdout
    assert "forbidden_future_status_present: False" in status.stdout
    assert VIEWS_NEXT_ACTION in status.stdout
    for forbidden_status in FORBIDDEN_FUTURE_STATUSES:
        assert forbidden_status not in status.stdout
