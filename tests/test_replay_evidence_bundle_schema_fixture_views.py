from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.replay_evidence_bundle_schema_fixture import (
    FORBIDDEN_METADATA_FALSE_FLAGS,
    REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED,
    REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS,
    build_replay_evidence_bundle_schema_fixture,
)
from quant_replay_system.replay_evidence_bundle_schema_fixture_health import (
    check_replay_evidence_bundle_schema_fixture_health,
)
from quant_replay_system.replay_evidence_bundle_schema_fixture_index import (
    NO_REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE,
    build_replay_evidence_bundle_schema_fixture_index,
)
from quant_replay_system.replay_evidence_bundle_schema_fixture_status import (
    REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_INVALID,
    run_replay_evidence_bundle_schema_fixture_status,
)


def test_index_safe_empty_behavior(tmp_path: Path) -> None:
    result = build_replay_evidence_bundle_schema_fixture_index(root=tmp_path / "missing", output_dir=tmp_path / "index")

    assert result.artifact_count == 0
    assert result.latest_run_id == ""
    assert result.latest_status == "NO_INPUT"
    assert result.latest_workflow_stage == NO_REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE
    assert result.latest_health_status == "PASS"
    assert result.index_frame.empty
    assert result.artifact_paths["index_csv"].exists()


def test_index_ignores_view_dirs_discovers_fixture_and_preserves_numeric_run_id(tmp_path: Path) -> None:
    fixture = build_replay_evidence_bundle_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["replay_evidence_bundle_schema_fixture_id"] = "522962104398"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")
    for name in ["index", "health", "status"]:
        (tmp_path / name).mkdir()

    result = build_replay_evidence_bundle_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")
    row = result.index_frame.loc[0]

    assert result.artifact_count == 1
    assert result.latest_run_id == "522962104398"
    assert isinstance(row["replay_evidence_bundle_schema_fixture_id"], str)
    assert row["replay_evidence_bundle_schema_fixture_id"] == "522962104398"
    assert result.latest_status == "PASS"
    assert result.latest_workflow_stage == REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED
    assert result.latest_health_status == "PASS"
    assert row["expected_artifacts"] == 12
    assert row["bundle_count"] == 10
    assert row["validation_issue_count"] == 0
    assert row["metadata_path"] == str(fixture.artifact_paths["metadata"])
    assert row["schema_fields_path"] == str(fixture.artifact_paths["schema_fields"])
    assert row["fixture_rows_path"] == str(fixture.artifact_paths["fixture_rows"])
    assert row["lineage_matrix_path"] == str(fixture.artifact_paths["lineage_matrix"])
    assert row["replay_evidence_bundle_schema_fixture_created"] is True
    assert row["replay_evidence_bundle_rows_created"] is True
    assert row["report_only"] is True
    assert row["diagnostic_only"] is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert row[flag] is False
    written = pd.read_csv(result.artifact_paths["index_csv"], dtype=str)
    assert written.loc[0, "replay_evidence_bundle_schema_fixture_id"] == "522962104398"


def test_health_passes_for_empty_and_valid_fixture_runs(tmp_path: Path) -> None:
    empty = check_replay_evidence_bundle_schema_fixture_health(root=tmp_path / "missing", output_dir=tmp_path / "empty")
    assert empty.status == "PASS"
    assert empty.checked_artifact_count == 0
    assert empty.issue_count == 0

    build_replay_evidence_bundle_schema_fixture(output_dir=tmp_path)
    result = check_replay_evidence_bundle_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0
    assert result.artifact_paths["health_csv"].exists()


def test_health_fails_when_metadata_unreadable_or_required_artifact_missing(tmp_path: Path) -> None:
    fixture = build_replay_evidence_bundle_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["metadata"].write_text("{not-json", encoding="utf-8")

    result = check_replay_evidence_bundle_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_bad_json")
    assert "METADATA_UNREADABLE" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_replay_evidence_bundle_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["fixture_rows"].unlink()

    result = check_replay_evidence_bundle_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_missing")
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fails_when_status_or_required_columns_are_invalid(tmp_path: Path) -> None:
    fixture = build_replay_evidence_bundle_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["status"] = "MAYBE"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_replay_evidence_bundle_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_status")
    assert "UNKNOWN_STATUS" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_replay_evidence_bundle_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).drop(columns=["available_time_max"])
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_replay_evidence_bundle_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_rows")
    assert "FIXTURE_ROWS_REQUIRED_COLUMNS_MISSING" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_replay_evidence_bundle_schema_fixture(output_dir=tmp_path)
    fields = pd.read_csv(fixture.artifact_paths["schema_fields"], dtype=str)
    fields = fields[fields["field_name"] != "available_time_max"]
    fields.to_csv(fixture.artifact_paths["schema_fields"], index=False)

    result = check_replay_evidence_bundle_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_fields")
    assert "SCHEMA_FIELDS_REQUIRED_FIELDS_MISSING" in _issue_codes(result)


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (lambda rows: rows.iloc[:-1], "BUNDLE_COUNT_NOT_10"),
        (
            lambda rows: rows.assign(
                replay_evidence_bundle_id=rows["replay_evidence_bundle_id"].where(
                    rows.index != 1, rows.loc[0, "replay_evidence_bundle_id"]
                )
            ),
            "REPLAY_EVIDENCE_BUNDLE_ID_NOT_UNIQUE",
        ),
        (
            lambda rows: rows.assign(replay_decision_time=rows["replay_decision_time"].where(rows.index != 0, "")),
            "REPLAY_DECISION_TIME_MISSING",
        ),
        (lambda rows: rows.assign(entity_id=rows["entity_id"].where(rows.index != 0, "")), "ENTITY_CONTEXT_MISSING"),
        (lambda rows: rows.assign(symbol=rows["symbol"].where(rows.index != 0, "")), "ENTITY_CONTEXT_MISSING"),
        (
            lambda rows: rows.assign(instrument_type=rows["instrument_type"].where(rows.index != 0, "")),
            "ENTITY_CONTEXT_MISSING",
        ),
        (
            lambda rows: rows.assign(evidence_item_types=rows["evidence_item_types"].where(rows.index != 0, "")),
            "EVIDENCE_ITEM_REFS_MISSING",
        ),
        (
            lambda rows: rows.assign(source_id_refs=rows["source_id_refs"].where(rows.index != 0, "")),
            "SOURCE_REGISTRY_LINKAGE_MISSING",
        ),
        (
            lambda rows: rows.assign(factor_id_refs=rows["factor_id_refs"].where(rows.index != 0, "")),
            "FACTOR_DEFINITION_LINKAGE_MISSING",
        ),
        (
            lambda rows: rows.assign(company_exposure_id_refs=rows["company_exposure_id_refs"].where(rows.index != 3, "")),
            "COMPANY_EXPOSURE_LINKAGE_MISSING",
        ),
        (
            lambda rows: rows.assign(event_structured_id_refs=rows["event_structured_id_refs"].where(rows.index != 2, "")),
            "EVENT_STRUCTURED_LINKAGE_MISSING",
        ),
        (
            lambda rows: rows.assign(factor_observation_id_refs=rows["factor_observation_id_refs"].where(rows.index != 0, "")),
            "FACTOR_OBSERVATION_LINKAGE_MISSING",
        ),
        (
            lambda rows: rows.assign(available_time_max=rows["available_time_max"].where(rows.index != 0, "2025-01-01T09:30:00")),
            "ADMISSIBLE_AVAILABLE_TIME_AFTER_REPLAY_TIME",
        ),
        (lambda rows: rows.assign(future_label_excluded="False"), "FUTURE_LABELS_NOT_EXCLUDED"),
        (lambda rows: rows.assign(future_revision_excluded="False"), "FUTURE_REVISIONS_NOT_EXCLUDED"),
        (lambda rows: rows.assign(source_hash_coverage=""), "HASH_COVERAGE_MISSING"),
        (lambda rows: rows.assign(revision_id_coverage=""), "REVISION_COVERAGE_MISSING"),
        (lambda rows: rows.assign(parser_version_refs=""), "PARSER_EXTRACTOR_CALCULATION_VERSION_MISSING"),
    ],
)
def test_health_fails_for_material_fixture_contract_mutations(tmp_path: Path, mutation, expected_code: str) -> None:
    fixture = build_replay_evidence_bundle_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).fillna("")
    mutation(rows).to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_replay_evidence_bundle_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("column", "value", "expected_code"),
    [
        ("source_permission_status", "DENIED", "ADMISSIBLE_SOURCE_PERMISSION_NOT_ALLOWED"),
        ("compliance_class", "PRIVATE", "RESTRICTED_PRIVATE_ILLEGAL_NOT_BLOCKED"),
        ("manual_review_status", "READY_TO_TRADE", "MANUAL_REVIEW_STATUS_INVALID"),
        ("quality_status", "READY_TO_TRADE", "QUALITY_STATUS_INVALID"),
        ("compliance_class", "READY_TO_TRADE", "COMPLIANCE_CLASS_INVALID"),
        ("trade_usage", "buy_signal", "TRADE_USAGE_FORBIDDEN"),
        ("candidate_context_ref", "contains access_token test", "SENSITIVE_TEXT_DETECTED"),
    ],
)
def test_health_fails_for_permissions_quality_trade_usage_and_sensitive_values(
    tmp_path: Path, column: str, value: str, expected_code: str
) -> None:
    fixture = build_replay_evidence_bundle_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).fillna("")
    rows.loc[0, column] = value
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_replay_evidence_bundle_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("row_id", "column", "value", "expected_code"),
    [
        (
            "SYNTH_BLOCKED_FUTURE_AVAILABLE_TIME_BUNDLE",
            "admissibility_status",
            "ADMISSIBLE",
            "FUTURE_AVAILABLE_EVIDENCE_NOT_BLOCKED",
        ),
        (
            "SYNTH_BLOCKED_MISSING_HASH_REVISION_BUNDLE",
            "admissibility_status",
            "ADMISSIBLE",
            "MISSING_HASH_REVISION_ROW_NOT_BLOCKED",
        ),
        (
            "SYNTH_OBSERVE_ONLY_INCOMPLETE_CONTEXT_BUNDLE",
            "decision_time_eligible",
            "True",
            "OBSERVE_ONLY_INCOMPLETE_DECISION_ELIGIBLE",
        ),
        (
            "SYNTH_RISK_VETO_ST_DELIST_BUNDLE",
            "risk_veto_flag",
            "False",
            "RISK_VETO_ROW_DOES_NOT_BLOCK_ACTIONABILITY",
        ),
    ],
)
def test_health_fails_for_blocked_and_veto_row_contracts(
    tmp_path: Path, row_id: str, column: str, value: str, expected_code: str
) -> None:
    fixture = build_replay_evidence_bundle_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).fillna("")
    rows.loc[rows["replay_evidence_bundle_id"] == row_id, column] = value
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_replay_evidence_bundle_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize("flag", FORBIDDEN_METADATA_FALSE_FLAGS)
def test_health_fails_when_any_forbidden_metadata_flag_is_true(tmp_path: Path, flag: str) -> None:
    fixture = build_replay_evidence_bundle_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata[flag] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_replay_evidence_bundle_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert "FORBIDDEN_METADATA_FLAG_TRUE" in _issue_codes(result)


@pytest.mark.parametrize(
    ("column", "expected_code"),
    [
        ("replay_decisions_created", "ROW_REPLAY_DECISIONS_CREATED_TRUE"),
        ("forward_labels_created", "ROW_FORWARD_LABELS_CREATED_TRUE"),
        ("future_labels_joined", "ROW_FUTURE_LABELS_JOINED_TRUE"),
        ("signal_score_implemented", "ROW_SIGNAL_SCORE_IMPLEMENTED_TRUE"),
        ("signal_score_input_authorized", "ROW_SIGNAL_SCORE_INPUT_AUTHORIZED_TRUE"),
        ("model_training_allowed", "ROW_MODEL_TRAINING_ALLOWED_TRUE"),
        ("active_weight_allowed", "ROW_ACTIVE_WEIGHT_ALLOWED_TRUE"),
        ("active_threshold_allowed", "ROW_ACTIVE_THRESHOLD_ALLOWED_TRUE"),
        ("stock_profile_validation_allowed", "ROW_STOCK_PROFILE_VALIDATION_ALLOWED_TRUE"),
        ("paper_validation_allowed", "ROW_PAPER_VALIDATION_ALLOWED_TRUE"),
        ("real_buy_review_allowed", "ROW_REAL_BUY_REVIEW_ALLOWED_TRUE"),
        ("buy_review_allowed", "ROW_BUY_REVIEW_ALLOWED_TRUE"),
        ("strategy_performance_validated", "ROW_STRATEGY_PERFORMANCE_VALIDATED_TRUE"),
        ("trading_allowed", "ROW_TRADING_ALLOWED_TRUE"),
        ("data_raw_written", "ROW_DATA_RAW_WRITTEN_TRUE"),
        ("current_candidates_run", "ROW_CURRENT_CANDIDATES_RUN_TRUE"),
        ("snapshot_built", "ROW_SNAPSHOT_BUILT_TRUE"),
        ("signal_semantics_changed", "ROW_SIGNAL_SEMANTICS_CHANGED_TRUE"),
        ("active_stock_profile_created", "ROW_ACTIVE_STOCK_PROFILE_CREATED_TRUE"),
    ],
)
def test_health_fails_when_row_forbidden_flags_are_true(tmp_path: Path, column: str, expected_code: str) -> None:
    fixture = build_replay_evidence_bundle_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).fillna("")
    rows.loc[0, column] = "True"
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_replay_evidence_bundle_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


def test_health_fails_when_artifact_paths_point_to_protected_operational_outputs(tmp_path: Path) -> None:
    fixture = build_replay_evidence_bundle_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["artifact_paths"]["fixture_rows"] = "data/raw/replay_evidence_bundle_fixture_rows.csv"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_replay_evidence_bundle_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert "UNSAFE_ARTIFACT_PATH" in _issue_codes(result)


def test_status_safe_empty_and_latest_fixture_summary(tmp_path: Path) -> None:
    empty = run_replay_evidence_bundle_schema_fixture_status(root=tmp_path / "missing", output_dir=tmp_path / "empty_status")
    assert empty.status == "PASS"
    assert empty.workflow_stage == NO_REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE
    assert empty.health_status == "PASS"
    assert empty.latest_run_id == ""

    fixture = build_replay_evidence_bundle_schema_fixture(output_dir=tmp_path)
    result = run_replay_evidence_bundle_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert result.status == "PASS"
    assert result.workflow_stage == REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED
    assert result.health_status == "PASS"
    assert result.latest_run_id == fixture.replay_evidence_bundle_schema_fixture_id
    assert result.bundle_count == 10
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.replay_evidence_bundle_schema_fixture_created is True
    assert result.replay_evidence_bundle_rows_created is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert getattr(result, flag) is False
    assert "report-only" in result.next_action
    assert "research-status/checkpoint integration" in result.next_action
    assert "real replay evidence bundles" in result.next_action
    assert "trading permission" in result.next_action


def test_status_marks_invalid_fixture_without_granting_downstream_readiness(tmp_path: Path) -> None:
    fixture = build_replay_evidence_bundle_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["replay_decisions_created"] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = run_replay_evidence_bundle_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert result.status == "FAIL"
    assert result.workflow_stage == REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_INVALID
    assert result.replay_decisions_created is True
    assert result.forward_labels_created is False
    assert result.signal_score_implemented is False
    assert result.model_training_performed is False
    assert result.active_weights_created is False
    assert result.active_thresholds_created is False
    assert result.buy_review_allowed is False
    assert result.strategy_performance_validated is False
    assert result.trading_allowed is False


def test_cli_index_health_status_commands_run_successfully(tmp_path: Path) -> None:
    root = tmp_path / "manual_diagnostics" / "replay_evidence_bundle_schema_fixture_v0_1"
    build_replay_evidence_bundle_schema_fixture(output_dir=root)

    env = {**os.environ, "PYTHONPATH": "src"}
    for command in [
        "replay-evidence-bundle-schema-fixture-index",
        "replay-evidence-bundle-schema-fixture-health",
        "replay-evidence-bundle-schema-fixture-status",
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
        assert "replay evidence bundle schema fixture" in completed.stdout.lower()
        assert "trading" in completed.stdout.lower()

    assert not (tmp_path / "docs" / "project_sources").exists()


def test_required_replay_evidence_bundle_fields_are_view_contract_inputs() -> None:
    assert "replay_evidence_bundle_id" in REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS
    assert "replay_decision_time" in REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS
    assert "source_id_refs" in REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS
    assert "factor_observation_id_refs" in REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS
    assert "future_label_excluded" in REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS
    assert "trading_allowed" in REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS


def _metadata(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _issue_codes(result) -> set[str]:
    if result.health_frame.empty:
        return set()
    return set(result.health_frame["issue_code"].astype(str))
