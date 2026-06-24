from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system.source_registry_schema_fixture import (
    FORBIDDEN_SIDE_EFFECT_FLAGS,
    REQUIRED_SOURCE_REGISTRY_FIELDS,
    build_source_registry_schema_fixture,
)
from quant_replay_system.source_registry_schema_fixture_health import check_source_registry_schema_fixture_health
from quant_replay_system.source_registry_schema_fixture_index import build_source_registry_schema_fixture_index
from quant_replay_system.source_registry_schema_fixture_status import (
    NO_SOURCE_REGISTRY_SCHEMA_FIXTURE,
    SOURCE_REGISTRY_SCHEMA_FIXTURE_CREATED,
    SOURCE_REGISTRY_SCHEMA_FIXTURE_INVALID,
    run_source_registry_schema_fixture_status,
)


def test_index_safe_empty_behavior(tmp_path: Path) -> None:
    result = build_source_registry_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")

    assert result.artifact_count == 0
    assert result.latest_run_id == ""
    assert result.latest_status == "NO_INPUT"
    assert result.latest_workflow_stage == NO_SOURCE_REGISTRY_SCHEMA_FIXTURE
    assert result.latest_health_status == "PASS"
    assert result.index_frame.empty
    assert result.artifact_paths["index_csv"].exists()


def test_index_ignores_view_directories_and_discovers_valid_fixture(tmp_path: Path) -> None:
    fixture = build_source_registry_schema_fixture(output_dir=tmp_path)
    for name in ["index", "health", "status"]:
        (tmp_path / name).mkdir()

    result = build_source_registry_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    assert result.latest_run_id == fixture.source_registry_schema_fixture_id
    assert result.latest_status == "PASS"
    assert result.latest_workflow_stage == SOURCE_REGISTRY_SCHEMA_FIXTURE_CREATED
    assert result.latest_health_status == "PASS"
    assert result.index_frame.loc[0, "source_registry_schema_fixture_id"] == fixture.source_registry_schema_fixture_id


def test_index_preserves_numeric_looking_run_ids_as_strings(tmp_path: Path) -> None:
    fixture = build_source_registry_schema_fixture(output_dir=tmp_path)
    metadata_path = fixture.artifact_paths["metadata"]
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["source_registry_schema_fixture_id"] = "522962104398"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    result = build_source_registry_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")

    assert result.latest_run_id == "522962104398"
    assert isinstance(result.index_frame.loc[0, "source_registry_schema_fixture_id"], str)
    written = pd.read_csv(result.artifact_paths["index_csv"], dtype=str)
    assert written.loc[0, "source_registry_schema_fixture_id"] == "522962104398"


def test_index_exposes_expected_artifact_paths_and_flags(tmp_path: Path) -> None:
    fixture = build_source_registry_schema_fixture(output_dir=tmp_path)

    result = build_source_registry_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")
    row = result.index_frame.loc[0]

    assert row["metadata_path"] == str(fixture.artifact_paths["metadata"])
    assert row["schema_fields_path"] == str(fixture.artifact_paths["schema_fields"])
    assert row["fixture_rows_path"] == str(fixture.artifact_paths["fixture_rows"])
    assert row["permission_matrix_path"] == str(fixture.artifact_paths["permission_matrix"])
    assert row["replay_suitability_matrix_path"] == str(fixture.artifact_paths["replay_suitability_matrix"])
    assert row["validation_summary_path"] == str(fixture.artifact_paths["validation_summary"])
    assert row["limitations_path"] == str(fixture.artifact_paths["limitations"])
    assert row["recommended_next_task_path"] == str(fixture.artifact_paths["recommended_next_task"])
    assert row["source_count"] == 5
    assert row["validation_issue_count"] == 0
    assert row["report_only"] is True
    assert row["diagnostic_only"] is True
    for flag in FORBIDDEN_SIDE_EFFECT_FLAGS:
        assert row[flag] is False


def test_health_passes_for_empty_and_valid_fixture_runs(tmp_path: Path) -> None:
    empty = check_source_registry_schema_fixture_health(root=tmp_path / "missing", output_dir=tmp_path / "empty_health")
    assert empty.status == "PASS"
    assert empty.checked_artifact_count == 0
    assert empty.issue_count == 0

    build_source_registry_schema_fixture(output_dir=tmp_path)
    result = check_source_registry_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0
    assert result.artifact_paths["health_csv"].exists()


def test_health_fails_when_metadata_unreadable_or_required_artifact_missing(tmp_path: Path) -> None:
    fixture = build_source_registry_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["metadata"].write_text("{not-json", encoding="utf-8")

    result = check_source_registry_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_bad_json")
    assert _issue_codes(result) >= {"METADATA_UNREADABLE"}

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_source_registry_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["fixture_rows"].unlink()

    result = check_source_registry_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_missing")
    assert _issue_codes(result) >= {"MISSING_REQUIRED_ARTIFACT"}


def test_health_fails_when_status_or_required_columns_are_invalid(tmp_path: Path) -> None:
    fixture = build_source_registry_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["status"] = "MAYBE"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_source_registry_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_status")
    assert _issue_codes(result) >= {"UNKNOWN_STATUS"}

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_source_registry_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).drop(columns=["source_type"])
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_source_registry_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_rows")
    assert _issue_codes(result) >= {"FIXTURE_ROWS_REQUIRED_COLUMNS_MISSING"}

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_source_registry_schema_fixture(output_dir=tmp_path)
    fields = pd.read_csv(fixture.artifact_paths["schema_fields"], dtype=str)
    fields = fields[fields["field_name"] != "source_type"]
    fields.to_csv(fixture.artifact_paths["schema_fields"], index=False)

    result = check_source_registry_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_fields")
    assert _issue_codes(result) >= {"SCHEMA_FIELDS_REQUIRED_FIELDS_MISSING"}


def test_health_fails_when_fixture_row_safety_policy_is_broken(tmp_path: Path) -> None:
    cases = [
        ("report_only", "False", "ROW_REPORT_ONLY_NOT_TRUE"),
        ("diagnostic_only", "False", "ROW_DIAGNOSTIC_ONLY_NOT_TRUE"),
        ("review_reason", "contains token-like text", "SENSITIVE_TEXT_DETECTED"),
        ("replay_suitability", "REPLAY_READY_AFTER_REVIEW", "BLOCKED_SOURCE_REPLAY_READY"),
        ("project_role", "PRIMARY_LOCAL_FALLBACK", "PAID_VENDOR_CURRENT_DEPENDENCY"),
        ("reliability_status", "VERIFIED", "PUBLIC_WRAPPER_AUTO_VERIFIED"),
        ("manual_review_required", "False", "LOCAL_CSV_MANUAL_REVIEW_MISSING"),
    ]
    for index, (column, value, expected_code) in enumerate(cases):
        root = tmp_path / f"case_{index}"
        fixture = build_source_registry_schema_fixture(output_dir=root)
        rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str)
        if expected_code == "BLOCKED_SOURCE_REPLAY_READY":
            mask = rows["source_id"] == "BLOCKED_PRIVATE_UNVERIFIED_SAMPLE"
        elif expected_code == "PAID_VENDOR_CURRENT_DEPENDENCY":
            mask = rows["source_id"] == "PAID_VENDOR_FUTURE_BACKUP_SAMPLE"
        elif expected_code == "PUBLIC_WRAPPER_AUTO_VERIFIED":
            mask = rows["source_id"] == "PUBLIC_WRAPPER_OPTIONAL_SAMPLE"
        elif expected_code == "LOCAL_CSV_MANUAL_REVIEW_MISSING":
            mask = rows["source_id"] == "LOCAL_CSV_REVIEWED_SAMPLE"
        else:
            mask = rows["source_id"] == "LOCAL_CSV_REVIEWED_SAMPLE"
        rows.loc[mask, column] = value
        rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

        result = check_source_registry_schema_fixture_health(root=root, output_dir=root / "health")

        assert expected_code in _issue_codes(result)


def test_health_fails_when_replay_matrix_marks_sources_as_unsafe_current_or_canonical(tmp_path: Path) -> None:
    fixture = build_source_registry_schema_fixture(output_dir=tmp_path)
    matrix = pd.read_csv(fixture.artifact_paths["replay_suitability_matrix"], dtype=str)
    matrix.loc[matrix["source_id"] == "PAID_VENDOR_FUTURE_BACKUP_SAMPLE", "current_dependency_allowed"] = "True"
    matrix.loc[matrix["source_id"] == "PUBLIC_WRAPPER_OPTIONAL_SAMPLE", "canonical_permission_source"] = "True"
    matrix.to_csv(fixture.artifact_paths["replay_suitability_matrix"], index=False)

    result = check_source_registry_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert _issue_codes(result) >= {"PAID_VENDOR_CURRENT_DEPENDENCY", "PUBLIC_WRAPPER_CANONICAL_PERMISSION"}


def test_health_fails_when_forbidden_metadata_flags_are_true(tmp_path: Path) -> None:
    flag_groups = [
        ["live_trading_enabled"],
        ["broker_api_called", "external_api_called", "llm_api_called"],
        ["data_raw_written", "data_processed_written", "data_cache_written"],
        ["current_candidates_run", "snapshot_built", "signal_semantics_changed"],
        ["buy_review_allowed", "real_buy_review_eligible"],
        ["strategy_performance_validated", "trading_allowed"],
    ]
    for index, flags in enumerate(flag_groups):
        root = tmp_path / f"flags_{index}"
        fixture = build_source_registry_schema_fixture(output_dir=root)
        metadata = _metadata(fixture.artifact_paths["metadata"])
        for flag in flags:
            metadata[flag] = True
        fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

        result = check_source_registry_schema_fixture_health(root=root, output_dir=root / "health")

        assert "FORBIDDEN_SIDE_EFFECT_FLAG_TRUE" in _issue_codes(result)


def test_health_fails_when_artifact_paths_point_to_protected_operational_outputs(tmp_path: Path) -> None:
    fixture = build_source_registry_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["artifact_paths"]["fixture_rows"] = "data/raw/source_registry_fixture_rows.csv"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_source_registry_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert "UNSAFE_ARTIFACT_PATH" in _issue_codes(result)


def test_status_safe_empty_behavior_and_latest_fixture_summary(tmp_path: Path) -> None:
    empty = run_source_registry_schema_fixture_status(root=tmp_path / "missing", output_dir=tmp_path / "empty_status")
    assert empty.status == "PASS"
    assert empty.workflow_stage == NO_SOURCE_REGISTRY_SCHEMA_FIXTURE
    assert empty.health_status == "PASS"
    assert empty.latest_run_id == ""

    fixture = build_source_registry_schema_fixture(output_dir=tmp_path)
    result = run_source_registry_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert result.status == "PASS"
    assert result.workflow_stage == SOURCE_REGISTRY_SCHEMA_FIXTURE_CREATED
    assert result.health_status == "PASS"
    assert result.latest_run_id == fixture.source_registry_schema_fixture_id
    assert result.source_count == 5
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.source_registry_schema_fixture_created is True
    for flag in FORBIDDEN_SIDE_EFFECT_FLAGS:
        assert getattr(result, flag) is False
    assert "Add source-registry schema fixture research-status integration next" not in result.next_action
    assert "post-checkpoint governance audit" in result.next_action
    assert "report-only schema-fixture governance" in result.next_action
    assert "real source registry" in result.next_action
    assert "trading workflow" in result.next_action


def test_status_marks_invalid_fixture_without_granting_permission(tmp_path: Path) -> None:
    fixture = build_source_registry_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["live_trading_enabled"] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = run_source_registry_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert result.status == "FAIL"
    assert result.workflow_stage == SOURCE_REGISTRY_SCHEMA_FIXTURE_INVALID
    assert result.live_trading_enabled is True
    assert result.trading_allowed is False
    assert result.real_buy_review_eligible is False


def test_cli_index_health_status_commands_run_successfully(tmp_path: Path) -> None:
    root = tmp_path / "manual_diagnostics" / "source_registry_schema_fixture_v0_1"
    build_source_registry_schema_fixture(output_dir=root)

    env = {**os.environ, "PYTHONPATH": "src"}
    for command in [
        "source-registry-schema-fixture-index",
        "source-registry-schema-fixture-health",
        "source-registry-schema-fixture-status",
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

        assert "source registry schema fixture" in completed.stdout.lower()

    assert not (tmp_path / "docs" / "project_sources").exists()


def _metadata(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _issue_codes(result: object) -> set[str]:
    return set(result.health_frame["issue_code"].astype(str))
