from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system.reviewed_local_csv_replay_prototype_input_contract_fixture import (
    REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED,
    SAFETY_FALSE_FLAGS,
    build_reviewed_local_csv_replay_prototype_input_contract_fixture,
)
from quant_replay_system.reviewed_local_csv_replay_prototype_input_contract_fixture_health import (
    check_reviewed_local_csv_replay_prototype_input_contract_fixture_health,
)
from quant_replay_system.reviewed_local_csv_replay_prototype_input_contract_fixture_index import (
    NO_REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE,
    build_reviewed_local_csv_replay_prototype_input_contract_fixture_index,
)
from quant_replay_system.reviewed_local_csv_replay_prototype_input_contract_fixture_status import (
    REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_INVALID,
    run_reviewed_local_csv_replay_prototype_input_contract_fixture_status,
)


def test_index_discovers_latest_artifact_and_preserves_contract_summary(tmp_path: Path) -> None:
    fixture = build_reviewed_local_csv_replay_prototype_input_contract_fixture(output_dir=tmp_path)
    metadata = json.loads(fixture.artifact_paths["metadata"].read_text(encoding="utf-8"))
    metadata["reviewed_local_csv_replay_prototype_input_contract_fixture_id"] = "885637683024"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    result = build_reviewed_local_csv_replay_prototype_input_contract_fixture_index(
        root=tmp_path,
        output_dir=tmp_path / "index",
    )
    row = result.index_frame.iloc[0].to_dict()
    written = pd.read_csv(result.artifact_paths["index_csv"], dtype=str).fillna("")

    assert result.artifact_count == 1
    assert result.latest_run_id == "885637683024"
    assert result.latest_status == "PASS"
    assert result.latest_workflow_stage == REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED
    assert result.latest_health_status == "PASS"
    assert row["contract_count"] == 12
    assert row["validation_issue_count"] == 0
    assert isinstance(row["reviewed_local_csv_replay_prototype_input_contract_fixture_id"], str)
    assert written.loc[0, "reviewed_local_csv_replay_prototype_input_contract_fixture_id"] == "885637683024"


def test_index_empty_root_reports_no_input_stage(tmp_path: Path) -> None:
    result = build_reviewed_local_csv_replay_prototype_input_contract_fixture_index(
        root=tmp_path / "missing",
        output_dir=tmp_path / "index",
    )

    assert result.artifact_count == 0
    assert result.latest_status == "NO_INPUT"
    assert result.latest_workflow_stage == NO_REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE
    assert result.latest_health_status == "PASS"


def test_health_passes_for_valid_artifact_and_fails_for_forbidden_flag(tmp_path: Path) -> None:
    fixture = build_reviewed_local_csv_replay_prototype_input_contract_fixture(output_dir=tmp_path)
    healthy = check_reviewed_local_csv_replay_prototype_input_contract_fixture_health(
        root=tmp_path,
        output_dir=tmp_path / "health",
    )

    assert healthy.status == "PASS"
    assert healthy.checked_artifact_count == 1
    assert healthy.issue_count == 0

    metadata = json.loads(fixture.artifact_paths["metadata"].read_text(encoding="utf-8"))
    metadata["buy_review_allowed"] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    unhealthy = check_reviewed_local_csv_replay_prototype_input_contract_fixture_health(
        root=tmp_path,
        output_dir=tmp_path / "health_bad",
    )
    assert unhealthy.status == "FAIL"
    assert "FORBIDDEN_METADATA_FLAG_TRUE" in set(unhealthy.health_frame["issue_code"])


def test_health_fails_for_missing_required_artifact_or_bad_contract_count(tmp_path: Path) -> None:
    fixture = build_reviewed_local_csv_replay_prototype_input_contract_fixture(output_dir=tmp_path)
    fixture.artifact_paths["pit_rule_matrix"].unlink()

    missing = check_reviewed_local_csv_replay_prototype_input_contract_fixture_health(
        root=tmp_path,
        output_dir=tmp_path / "health_missing",
    )
    assert missing.status == "FAIL"
    assert "MISSING_REQUIRED_ARTIFACT" in set(missing.health_frame["issue_code"])

    build_reviewed_local_csv_replay_prototype_input_contract_fixture(output_dir=tmp_path / "second")
    second_dir = next(path for path in (tmp_path / "second").iterdir() if path.is_dir())
    metadata_path = second_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["contract_count"] = 11
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    bad_count = check_reviewed_local_csv_replay_prototype_input_contract_fixture_health(
        root=tmp_path / "second",
        output_dir=tmp_path / "health_bad_count",
    )
    assert bad_count.status == "FAIL"
    assert "CONTRACT_COUNT_NOT_12" in set(bad_count.health_frame["issue_code"])


def test_status_reports_latest_context_and_forbidden_flags_false(tmp_path: Path) -> None:
    fixture = build_reviewed_local_csv_replay_prototype_input_contract_fixture(output_dir=tmp_path)
    status = run_reviewed_local_csv_replay_prototype_input_contract_fixture_status(
        root=tmp_path,
        output_dir=tmp_path / "status",
    )

    assert status.latest_run_id == fixture.reviewed_local_csv_replay_prototype_input_contract_fixture_id
    assert status.status == "PASS"
    assert status.workflow_stage == REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED
    assert status.health_status == "PASS"
    assert status.contract_count == 12
    assert status.validation_issue_count == 0
    assert status.report_only is True
    assert status.diagnostic_only is True
    for flag in SAFETY_FALSE_FLAGS:
        assert getattr(status, flag) is False
    assert (
        "Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture Research-Status and Checkpoint Report-Only v0.1"
        in status.next_action
    )


def test_status_handles_no_artifact_and_invalid_health(tmp_path: Path) -> None:
    empty = run_reviewed_local_csv_replay_prototype_input_contract_fixture_status(
        root=tmp_path / "missing",
        output_dir=tmp_path / "status_empty",
    )
    assert empty.status == "NO_INPUT"
    assert empty.workflow_stage == NO_REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE
    assert empty.health_status == "PASS"

    fixture = build_reviewed_local_csv_replay_prototype_input_contract_fixture(output_dir=tmp_path / "bad")
    metadata = json.loads(fixture.artifact_paths["metadata"].read_text(encoding="utf-8"))
    metadata["status"] = REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    invalid = run_reviewed_local_csv_replay_prototype_input_contract_fixture_status(
        root=tmp_path / "bad",
        output_dir=tmp_path / "status_invalid",
    )
    assert invalid.status == "FAIL"
    assert invalid.workflow_stage == REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_INVALID
    assert invalid.health_status == "FAIL"


def test_cli_view_commands_run_and_remain_report_only(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "reviewed_local_csv_fixture"
    env = {**os.environ, "PYTHONPATH": "src"}

    core = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "reviewed-local-csv-replay-prototype-input-contract-fixture",
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
            "reviewed-local-csv-replay-prototype-input-contract-fixture-index",
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
    assert "contract_count: 12" in index.stdout

    health = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "reviewed-local-csv-replay-prototype-input-contract-fixture-health",
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
            "reviewed-local-csv-replay-prototype-input-contract-fixture-status",
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
    assert f"workflow_stage: {REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED}" in status.stdout
    assert "buy_review_allowed: False" in status.stdout
    assert "trading_allowed: False" in status.stdout
    assert "Research-Status and Checkpoint Report-Only v0.1" in status.stdout

