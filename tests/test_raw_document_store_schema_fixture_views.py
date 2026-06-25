from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.raw_document_store_schema_fixture import (
    FORBIDDEN_METADATA_FALSE_FLAGS,
    REQUIRED_RAW_DOCUMENT_STORE_FIELDS,
    build_raw_document_store_schema_fixture,
)
from quant_replay_system.raw_document_store_schema_fixture_health import check_raw_document_store_schema_fixture_health
from quant_replay_system.raw_document_store_schema_fixture_index import build_raw_document_store_schema_fixture_index
from quant_replay_system.raw_document_store_schema_fixture_status import (
    NO_RAW_DOCUMENT_STORE_SCHEMA_FIXTURE,
    RAW_DOCUMENT_STORE_SCHEMA_FIXTURE_CREATED,
    RAW_DOCUMENT_STORE_SCHEMA_FIXTURE_INVALID,
    run_raw_document_store_schema_fixture_status,
)


def test_index_safe_empty_behavior(tmp_path: Path) -> None:
    result = build_raw_document_store_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")

    assert result.artifact_count == 0
    assert result.latest_run_id == ""
    assert result.latest_status == "NO_INPUT"
    assert result.latest_workflow_stage == NO_RAW_DOCUMENT_STORE_SCHEMA_FIXTURE
    assert result.latest_health_status == "PASS"
    assert result.index_frame.empty
    assert result.artifact_paths["index_csv"].exists()


def test_index_ignores_view_directories_and_discovers_valid_fixture(tmp_path: Path) -> None:
    fixture = build_raw_document_store_schema_fixture(output_dir=tmp_path)
    for name in ["index", "health", "status"]:
        (tmp_path / name).mkdir()

    result = build_raw_document_store_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    assert result.latest_run_id == fixture.raw_document_store_schema_fixture_id
    assert result.latest_status == "PASS"
    assert result.latest_workflow_stage == RAW_DOCUMENT_STORE_SCHEMA_FIXTURE_CREATED
    assert result.latest_health_status == "PASS"
    assert result.index_frame.loc[0, "raw_document_store_schema_fixture_id"] == fixture.raw_document_store_schema_fixture_id


def test_index_preserves_numeric_looking_run_ids_as_strings(tmp_path: Path) -> None:
    fixture = build_raw_document_store_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["raw_document_store_schema_fixture_id"] = "522962104398"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = build_raw_document_store_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")

    assert result.latest_run_id == "522962104398"
    assert isinstance(result.index_frame.loc[0, "raw_document_store_schema_fixture_id"], str)
    written = pd.read_csv(result.artifact_paths["index_csv"], dtype=str)
    assert written.loc[0, "raw_document_store_schema_fixture_id"] == "522962104398"


def test_index_exposes_expected_artifact_paths_and_forbidden_flags(tmp_path: Path) -> None:
    fixture = build_raw_document_store_schema_fixture(output_dir=tmp_path)

    result = build_raw_document_store_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")
    row = result.index_frame.loc[0]

    assert row["metadata_path"] == str(fixture.artifact_paths["metadata"])
    assert row["schema_fields_path"] == str(fixture.artifact_paths["schema_fields"])
    assert row["fixture_rows_path"] == str(fixture.artifact_paths["fixture_rows"])
    assert row["permission_matrix_path"] == str(fixture.artifact_paths["permission_matrix"])
    assert row["storage_policy_matrix_path"] == str(fixture.artifact_paths["storage_policy_matrix"])
    assert row["pit_timing_matrix_path"] == str(fixture.artifact_paths["pit_timing_matrix"])
    assert row["validation_summary_path"] == str(fixture.artifact_paths["validation_summary"])
    assert row["limitations_path"] == str(fixture.artifact_paths["limitations"])
    assert row["recommended_next_task_path"] == str(fixture.artifact_paths["recommended_next_task"])
    assert row["document_count"] == 7
    assert row["validation_issue_count"] == 0
    assert row["report_only"] is True
    assert row["diagnostic_only"] is True
    assert row["production_raw_document_store_created"] is False
    assert row["real_source_permission_created"] is False
    assert row["real_data_fetched"] is False
    assert row["raw_document_ingestion_created"] is False
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert row[flag] is False


def test_health_passes_for_empty_and_valid_fixture_runs(tmp_path: Path) -> None:
    empty = check_raw_document_store_schema_fixture_health(root=tmp_path / "missing", output_dir=tmp_path / "empty_health")
    assert empty.status == "PASS"
    assert empty.checked_artifact_count == 0
    assert empty.issue_count == 0

    build_raw_document_store_schema_fixture(output_dir=tmp_path)
    result = check_raw_document_store_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0
    assert result.artifact_paths["health_csv"].exists()


def test_health_fails_when_metadata_unreadable_or_required_artifact_missing(tmp_path: Path) -> None:
    fixture = build_raw_document_store_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["metadata"].write_text("{not-json", encoding="utf-8")

    result = check_raw_document_store_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_bad_json")
    assert "METADATA_UNREADABLE" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_raw_document_store_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["fixture_rows"].unlink()

    result = check_raw_document_store_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_missing")
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fails_when_status_or_required_columns_are_invalid(tmp_path: Path) -> None:
    fixture = build_raw_document_store_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["status"] = "MAYBE"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_raw_document_store_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_status")
    assert "UNKNOWN_STATUS" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_raw_document_store_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).drop(columns=["available_time"])
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_raw_document_store_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_rows")
    assert "FIXTURE_ROWS_REQUIRED_COLUMNS_MISSING" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_raw_document_store_schema_fixture(output_dir=tmp_path)
    fields = pd.read_csv(fixture.artifact_paths["schema_fields"], dtype=str)
    fields = fields[fields["field_name"] != "available_time"]
    fields.to_csv(fixture.artifact_paths["schema_fields"], index=False)

    result = check_raw_document_store_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_fields")
    assert "SCHEMA_FIELDS_REQUIRED_FIELDS_MISSING" in _issue_codes(result)


@pytest.mark.parametrize(
    ("column", "value", "expected_code"),
    [
        ("report_only", "False", "ROW_REPORT_ONLY_NOT_TRUE"),
        ("diagnostic_only", "False", "ROW_DIAGNOSTIC_ONLY_NOT_TRUE"),
        ("review_reason", "contains secret-like text", "SENSITIVE_TEXT_DETECTED"),
        ("document_id", "", "DOCUMENT_ID_MISSING"),
        ("document_version_id", "", "DOCUMENT_VERSION_ID_MISSING"),
        ("source_id", "", "SOURCE_ID_MISSING"),
        ("available_time", "", "AVAILABLE_TIME_MISSING"),
        ("source_hash", "", "HASH_OR_CONTENT_HASH_MISSING"),
        ("revision_id", "", "REVISION_ID_MISSING"),
        ("permission_class", "", "PERMISSION_CLASS_MISSING"),
        ("storage_policy", "", "STORAGE_POLICY_MISSING"),
        ("manual_review_status", "", "MANUAL_REVIEW_STATUS_MISSING"),
        ("quality_status", "", "QUALITY_STATUS_MISSING"),
        ("pit_valid", "MAYBE", "PIT_VALID_NOT_EXPLICIT"),
    ],
)
def test_health_fails_when_fixture_row_required_values_are_invalid(
    tmp_path: Path, column: str, value: str, expected_code: str
) -> None:
    fixture = build_raw_document_store_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str)
    mask = rows["document_id"] == "LOCAL_CSV_REVIEWED_DATASET_SAMPLE"
    rows.loc[mask, column] = value
    if expected_code == "HASH_OR_CONTENT_HASH_MISSING":
        rows.loc[mask, "content_hash"] = ""
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_raw_document_store_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


def test_health_fails_when_timing_and_permission_matrix_are_unsafe(tmp_path: Path) -> None:
    cases = [
        ("published_at", "2024-04-02T00:00:00", "PUBLISHED_AFTER_AVAILABLE_TIME"),
        ("period_end", "2024-04-02T00:00:00", "PERIOD_END_AFTER_AVAILABLE_TIME"),
    ]
    for index, (column, value, expected_code) in enumerate(cases):
        root = tmp_path / f"timing_{index}"
        fixture = build_raw_document_store_schema_fixture(output_dir=root)
        rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str)
        rows.loc[rows["document_id"] == "LOCAL_CSV_REVIEWED_DATASET_SAMPLE", column] = value
        rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

        result = check_raw_document_store_schema_fixture_health(root=root, output_dir=root / "health")

        assert expected_code in _issue_codes(result)

    root = tmp_path / "permission"
    fixture = build_raw_document_store_schema_fixture(output_dir=root)
    matrix = pd.read_csv(fixture.artifact_paths["permission_matrix"], dtype=str)
    matrix.loc[matrix["document_id"] == "LOCAL_CSV_REVIEWED_DATASET_SAMPLE", "source_id_implies_permission"] = "True"
    matrix.to_csv(fixture.artifact_paths["permission_matrix"], index=False)

    result = check_raw_document_store_schema_fixture_health(root=root, output_dir=root / "health")

    assert "SOURCE_ID_IMPLIES_PERMISSION" in _issue_codes(result)


def test_health_fails_when_blocked_or_copyrighted_rows_are_unsafe(tmp_path: Path) -> None:
    fixture = build_raw_document_store_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str)
    rows.loc[rows["document_id"] == "BLOCKED_PRIVATE_RUMOR_SAMPLE", "decision_time_eligible"] = "True"
    rows.loc[rows["document_id"] == "COPYRIGHTED_NEWS_REFERENCE_ONLY_SAMPLE", "raw_content_stored"] = "True"
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_raw_document_store_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert _issue_codes(result) >= {
        "BLOCKED_PRIVATE_RUMOR_DECISION_TIME_ELIGIBLE",
        "COPYRIGHTED_NEWS_RAW_CONTENT_STORED",
    }


@pytest.mark.parametrize("flag", FORBIDDEN_METADATA_FALSE_FLAGS)
def test_health_fails_when_any_forbidden_metadata_flag_is_true(tmp_path: Path, flag: str) -> None:
    fixture = build_raw_document_store_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata[flag] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_raw_document_store_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert "FORBIDDEN_METADATA_FLAG_TRUE" in _issue_codes(result)


def test_health_fails_when_artifact_paths_point_to_protected_operational_outputs(tmp_path: Path) -> None:
    fixture = build_raw_document_store_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["artifact_paths"]["fixture_rows"] = "data/raw/raw_document_store_fixture_rows.csv"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_raw_document_store_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert "UNSAFE_ARTIFACT_PATH" in _issue_codes(result)


def test_status_safe_empty_behavior_and_latest_fixture_summary(tmp_path: Path) -> None:
    empty = run_raw_document_store_schema_fixture_status(root=tmp_path / "missing", output_dir=tmp_path / "empty_status")
    assert empty.status == "PASS"
    assert empty.workflow_stage == NO_RAW_DOCUMENT_STORE_SCHEMA_FIXTURE
    assert empty.health_status == "PASS"
    assert empty.latest_run_id == ""

    fixture = build_raw_document_store_schema_fixture(output_dir=tmp_path)
    result = run_raw_document_store_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert result.status == "PASS"
    assert result.workflow_stage == RAW_DOCUMENT_STORE_SCHEMA_FIXTURE_CREATED
    assert result.health_status == "PASS"
    assert result.latest_run_id == fixture.raw_document_store_schema_fixture_id
    assert result.document_count == 7
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.raw_document_store_schema_fixture_created is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert getattr(result, flag) is False
    assert "Raw Document Store Schema Fixture Views are report-only" in result.next_action
    assert "research-status/checkpoint integration" in result.next_action
    assert "production raw documents" in result.next_action
    assert "trading permission" in result.next_action


def test_status_marks_invalid_fixture_without_granting_downstream_readiness(tmp_path: Path) -> None:
    fixture = build_raw_document_store_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["raw_document_ingestion_created"] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = run_raw_document_store_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert result.status == "FAIL"
    assert result.workflow_stage == RAW_DOCUMENT_STORE_SCHEMA_FIXTURE_INVALID
    assert result.raw_document_ingestion_created is True
    assert result.production_raw_document_store_created is False
    assert result.real_source_permission_created is False
    assert result.buy_review_allowed is False
    assert result.strategy_performance_validated is False
    assert result.trading_allowed is False


def test_cli_index_health_status_commands_run_successfully(tmp_path: Path) -> None:
    root = tmp_path / "manual_diagnostics" / "raw_document_store_schema_fixture_v0_1"
    build_raw_document_store_schema_fixture(output_dir=root)

    env = {**os.environ, "PYTHONPATH": "src"}
    for command in [
        "raw-document-store-schema-fixture-index",
        "raw-document-store-schema-fixture-health",
        "raw-document-store-schema-fixture-status",
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
            env=env,
        )

        assert "raw document store schema fixture" in completed.stdout.lower()
        assert "trading" in completed.stdout.lower()

    assert not (tmp_path / "docs" / "project_sources").exists()


def _metadata(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _issue_codes(result: object) -> set[str]:
    return set(result.health_frame["issue_code"].astype(str))
