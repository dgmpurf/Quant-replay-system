from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.forward_return_label_schema_fixture import (
    FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED,
    FORBIDDEN_METADATA_FALSE_FLAGS,
    REQUIRED_FORWARD_RETURN_LABEL_FIELDS,
    ROW_FALSE_FLAGS,
    build_forward_return_label_schema_fixture,
)
from quant_replay_system.forward_return_label_schema_fixture_health import (
    check_forward_return_label_schema_fixture_health,
)
from quant_replay_system.forward_return_label_schema_fixture_index import (
    NO_FORWARD_RETURN_LABEL_SCHEMA_FIXTURE,
    build_forward_return_label_schema_fixture_index,
)
from quant_replay_system.forward_return_label_schema_fixture_status import (
    FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_INVALID,
    run_forward_return_label_schema_fixture_status,
)


def test_index_safe_empty_behavior(tmp_path: Path) -> None:
    result = build_forward_return_label_schema_fixture_index(root=tmp_path / "missing", output_dir=tmp_path / "index")

    assert result.artifact_count == 0
    assert result.latest_run_id == ""
    assert result.latest_status == "NO_INPUT"
    assert result.latest_workflow_stage == NO_FORWARD_RETURN_LABEL_SCHEMA_FIXTURE
    assert result.latest_health_status == "PASS"
    assert result.index_frame.empty
    assert result.artifact_paths["index_csv"].exists()


def test_index_discovers_fixture_ignores_view_dirs_and_preserves_numeric_run_id(tmp_path: Path) -> None:
    fixture = build_forward_return_label_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["forward_return_label_schema_fixture_id"] = "885637683024"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")
    for name in ["index", "health", "status"]:
        (tmp_path / name).mkdir()

    result = build_forward_return_label_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")
    row = result.index_frame.loc[0]

    assert result.artifact_count == 1
    assert result.latest_run_id == "885637683024"
    assert isinstance(row["forward_return_label_schema_fixture_id"], str)
    assert row["forward_return_label_schema_fixture_id"] == "885637683024"
    assert result.latest_status == "PASS"
    assert result.latest_workflow_stage == FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED
    assert result.latest_health_status == "PASS"
    assert row["expected_artifacts"] == 9
    assert row["label_count"] == 10
    assert row["validation_issue_count"] == 0
    assert row["metadata_path"] == str(fixture.artifact_paths["metadata"])
    assert row["fixture_rows_path"] == str(fixture.artifact_paths["fixture_rows"])
    assert row["field_contract_path"] == str(fixture.artifact_paths["field_contract"])
    assert row["report_only"] is True
    assert row["diagnostic_only"] is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert row[flag] is False
    assert row["future_label_joined_to_decision_input"] is False
    written = pd.read_csv(result.artifact_paths["index_csv"], dtype=str)
    assert written.loc[0, "forward_return_label_schema_fixture_id"] == "885637683024"


def test_health_passes_for_empty_and_valid_fixture_runs(tmp_path: Path) -> None:
    empty = check_forward_return_label_schema_fixture_health(root=tmp_path / "missing", output_dir=tmp_path / "empty")
    assert empty.status == "PASS"
    assert empty.checked_artifact_count == 0
    assert empty.issue_count == 0

    build_forward_return_label_schema_fixture(output_dir=tmp_path)
    result = check_forward_return_label_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0
    assert result.artifact_paths["health_csv"].exists()


def test_health_fails_for_unreadable_metadata_and_missing_required_artifact(tmp_path: Path) -> None:
    fixture = build_forward_return_label_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["metadata"].write_text("{not-json", encoding="utf-8")

    result = check_forward_return_label_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_bad_json")
    assert "METADATA_UNREADABLE" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_forward_return_label_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["fixture_rows"].unlink()

    result = check_forward_return_label_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_missing")
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fails_for_invalid_metadata_and_required_columns(tmp_path: Path) -> None:
    fixture = build_forward_return_label_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["status"] = "FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_forward_return_label_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_status")
    assert "UNKNOWN_STATUS" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_forward_return_label_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).drop(columns=["window_start_date"])
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_forward_return_label_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_rows")
    assert "FIXTURE_ROWS_REQUIRED_COLUMNS_MISSING" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_forward_return_label_schema_fixture(output_dir=tmp_path)
    fields = pd.read_csv(fixture.artifact_paths["field_contract"], dtype=str)
    fields = fields[fields["field_name"] != "window_start_date"]
    fields.to_csv(fixture.artifact_paths["field_contract"], index=False)

    result = check_forward_return_label_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_fields")
    assert "FIELD_CONTRACT_REQUIRED_FIELDS_MISSING" in _issue_codes(result)


@pytest.mark.parametrize(
    ("column", "value", "expected_code"),
    [
        ("real_forward_label_created", "True", "REAL_FORWARD_LABEL_FLAG_TRUE"),
        ("future_label_joined_to_decision_input", "True", "FUTURE_LABEL_JOIN_FLAG_TRUE"),
        ("signal_score_input_authorized", "True", "SIGNAL_SCORE_FLAG_TRUE"),
        ("model_training_input_authorized", "True", "MODEL_TRAINING_FLAG_TRUE"),
        ("stock_profile_input_authorized", "True", "STOCK_PROFILE_FLAG_TRUE"),
        ("paper_validation_created", "True", "PAPER_VALIDATION_FLAG_TRUE"),
        ("buy_review_allowed", "True", "BUY_REVIEW_FLAG_TRUE"),
        ("strategy_performance_validated", "True", "PERFORMANCE_OR_TRADING_FLAG_TRUE"),
        ("trading_allowed", "True", "PERFORMANCE_OR_TRADING_FLAG_TRUE"),
        ("blocker_reason", "contains access_token test", "SENSITIVE_TEXT_DETECTED"),
    ],
)
def test_health_fails_for_forbidden_row_flags_and_secret_like_text(
    tmp_path: Path, column: str, value: str, expected_code: str
) -> None:
    fixture = build_forward_return_label_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).fillna("")
    rows.loc[0, column] = value
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_forward_return_label_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize("flag", FORBIDDEN_METADATA_FALSE_FLAGS)
def test_health_fails_for_forbidden_metadata_flags(tmp_path: Path, flag: str) -> None:
    fixture = build_forward_return_label_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata[flag] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_forward_return_label_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert "FORBIDDEN_METADATA_FLAG_TRUE" in _issue_codes(result)


def test_health_fails_for_material_label_contract_mutations(tmp_path: Path) -> None:
    fixture = build_forward_return_label_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).fillna("")
    rows = rows.iloc[:-1]
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_forward_return_label_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_count")
    assert "LABEL_COUNT_NOT_10" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_forward_return_label_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).fillna("")
    rows.loc[rows["label_status"] == "COMPLETE", "window_start_date"] = "2024-04-02T09:30:00"
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_forward_return_label_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_window")
    assert "COMPLETE_WINDOW_START_NOT_AFTER_DECISION_TIME" in _issue_codes(result)


def test_status_safe_empty_latest_fixture_and_invalid_health(tmp_path: Path) -> None:
    empty = run_forward_return_label_schema_fixture_status(root=tmp_path / "missing", output_dir=tmp_path / "status_empty")

    assert empty.status == "PASS"
    assert empty.workflow_stage == NO_FORWARD_RETURN_LABEL_SCHEMA_FIXTURE
    assert empty.health_status == "PASS"
    assert empty.latest_run_id == ""
    assert empty.report_only is True
    assert empty.diagnostic_only is True
    assert empty.artifact_paths["status_csv"].exists()

    fixture = build_forward_return_label_schema_fixture(output_dir=tmp_path)
    status = run_forward_return_label_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert status.latest_run_id == fixture.forward_return_label_schema_fixture_id
    assert status.status == "PASS"
    assert status.workflow_stage == FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED
    assert status.health_status == "PASS"
    assert status.label_count == 10
    assert status.validation_issue_count == 0
    assert status.report_only is True
    assert status.diagnostic_only is True
    assert status.real_forward_labels_created is False
    assert status.future_labels_joined is False
    assert status.future_label_joined_to_decision_input is False
    assert status.signal_score_input_authorized is False
    assert status.model_training_input_authorized is False
    assert status.buy_review_allowed is False
    assert status.trading_allowed is False
    assert "Forward Return Label Schema Fixture Research-Status and Checkpoint Report-Only v0.1" in status.next_action

    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["status"] = "MAYBE"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")
    invalid = run_forward_return_label_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status_invalid")
    assert invalid.status == "FAIL"
    assert invalid.workflow_stage == FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_INVALID


def test_cli_index_health_status_commands_run_successfully(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "forward_return_label_schema_fixture_v0_1"
    build = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "forward-return-label-schema-fixture",
            "--output-dir",
            str(root),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    assert "status: PASS" in build.stdout

    for command in [
        "forward-return-label-schema-fixture-index",
        "forward-return-label-schema-fixture-health",
        "forward-return-label-schema-fixture-status",
    ]:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "quant_replay_system.cli",
                command,
                "--root",
                str(root),
                "--output-dir",
                str(root / command.rsplit("-", 1)[-1]),
            ],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
        )
        assert "forward label" in completed.stdout.lower() or "forward return label" in completed.stdout.lower()
        assert "trading" in completed.stdout.lower()

    assert not (tmp_path / "docs" / "project_sources").exists()


def _metadata(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _issue_codes(result) -> set[str]:
    if result.health_frame.empty:
        return set()
    return set(result.health_frame["issue_code"].astype(str))
