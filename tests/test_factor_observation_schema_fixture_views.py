from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.factor_observation_schema_fixture import (
    FACTOR_OBSERVATION_SCHEMA_FIXTURE_CREATED,
    FORBIDDEN_METADATA_FALSE_FLAGS,
    REQUIRED_FACTOR_OBSERVATION_FIELDS,
    build_factor_observation_schema_fixture,
)
from quant_replay_system.factor_observation_schema_fixture_health import (
    check_factor_observation_schema_fixture_health,
)
from quant_replay_system.factor_observation_schema_fixture_index import (
    NO_FACTOR_OBSERVATION_SCHEMA_FIXTURE,
    build_factor_observation_schema_fixture_index,
)
from quant_replay_system.factor_observation_schema_fixture_status import (
    FACTOR_OBSERVATION_SCHEMA_FIXTURE_INVALID,
    run_factor_observation_schema_fixture_status,
)


def test_index_safe_empty_behavior(tmp_path: Path) -> None:
    result = build_factor_observation_schema_fixture_index(root=tmp_path / "missing", output_dir=tmp_path / "index")

    assert result.artifact_count == 0
    assert result.latest_run_id == ""
    assert result.latest_status == "NO_INPUT"
    assert result.latest_workflow_stage == NO_FACTOR_OBSERVATION_SCHEMA_FIXTURE
    assert result.latest_health_status == "PASS"
    assert result.index_frame.empty
    assert result.artifact_paths["index_csv"].exists()


def test_index_ignores_view_dirs_discovers_fixture_and_preserves_numeric_run_id(tmp_path: Path) -> None:
    fixture = build_factor_observation_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["factor_observation_schema_fixture_id"] = "522962104398"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")
    for name in ["index", "health", "status"]:
        (tmp_path / name).mkdir()

    result = build_factor_observation_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")
    row = result.index_frame.loc[0]

    assert result.artifact_count == 1
    assert result.latest_run_id == "522962104398"
    assert isinstance(row["factor_observation_schema_fixture_id"], str)
    assert row["factor_observation_schema_fixture_id"] == "522962104398"
    assert result.latest_status == "PASS"
    assert result.latest_workflow_stage == FACTOR_OBSERVATION_SCHEMA_FIXTURE_CREATED
    assert result.latest_health_status == "PASS"
    assert row["expected_artifacts"] == 11
    assert row["observation_count"] == 10
    assert row["validation_issue_count"] == 0
    assert row["metadata_path"] == str(fixture.artifact_paths["metadata"])
    assert row["schema_fields_path"] == str(fixture.artifact_paths["schema_fields"])
    assert row["fixture_rows_path"] == str(fixture.artifact_paths["fixture_rows"])
    assert row["source_quality_matrix_path"] == str(fixture.artifact_paths["source_quality_matrix"])
    assert row["factor_event_exposure_lineage_matrix_path"] == str(
        fixture.artifact_paths["factor_event_exposure_lineage_matrix"]
    )
    assert row["factor_observation_schema_fixture_created"] is True
    assert row["factor_observation_rows_created"] is True
    assert row["report_only"] is True
    assert row["diagnostic_only"] is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert row[flag] is False
    written = pd.read_csv(result.artifact_paths["index_csv"], dtype=str)
    assert written.loc[0, "factor_observation_schema_fixture_id"] == "522962104398"


def test_health_passes_for_empty_and_valid_fixture_runs(tmp_path: Path) -> None:
    empty = check_factor_observation_schema_fixture_health(root=tmp_path / "missing", output_dir=tmp_path / "empty")
    assert empty.status == "PASS"
    assert empty.checked_artifact_count == 0
    assert empty.issue_count == 0

    build_factor_observation_schema_fixture(output_dir=tmp_path)
    result = check_factor_observation_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0
    assert result.artifact_paths["health_csv"].exists()


def test_health_fails_when_metadata_unreadable_or_required_artifact_missing(tmp_path: Path) -> None:
    fixture = build_factor_observation_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["metadata"].write_text("{not-json", encoding="utf-8")

    result = check_factor_observation_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_bad_json")
    assert "METADATA_UNREADABLE" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_factor_observation_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["fixture_rows"].unlink()

    result = check_factor_observation_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_missing")
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fails_when_status_or_required_columns_are_invalid(tmp_path: Path) -> None:
    fixture = build_factor_observation_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["status"] = "MAYBE"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_factor_observation_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_status")
    assert "UNKNOWN_STATUS" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_factor_observation_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).drop(columns=["available_time"])
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_factor_observation_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_rows")
    assert "FIXTURE_ROWS_REQUIRED_COLUMNS_MISSING" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_factor_observation_schema_fixture(output_dir=tmp_path)
    fields = pd.read_csv(fixture.artifact_paths["schema_fields"], dtype=str)
    fields = fields[fields["field_name"] != "available_time"]
    fields.to_csv(fixture.artifact_paths["schema_fields"], index=False)

    result = check_factor_observation_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_fields")
    assert "SCHEMA_FIELDS_REQUIRED_FIELDS_MISSING" in _issue_codes(result)


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (lambda rows: rows.iloc[:-1], "OBSERVATION_COUNT_NOT_10"),
        (
            lambda rows: rows.assign(
                factor_observation_id=rows["factor_observation_id"].where(
                    rows.index != 1, rows.loc[0, "factor_observation_id"]
                )
            ),
            "FACTOR_OBSERVATION_ID_NOT_UNIQUE",
        ),
        (lambda rows: rows.assign(factor_id=rows["factor_id"].where(rows.index != 0, "")), "FACTOR_ID_MISSING"),
        (
            lambda rows: rows.assign(
                factor_definition_version=rows["factor_definition_version"].where(rows.index != 0, "")
            ),
            "FACTOR_DEFINITION_VERSION_MISSING",
        ),
        (
            lambda rows: rows.assign(taxonomy_layer_id=rows["taxonomy_layer_id"].where(rows.index != 0, "")),
            "TAXONOMY_LAYER_ID_MISSING",
        ),
        (
            lambda rows: rows.assign(observation_date=rows["observation_date"].where(rows.index != 0, "")),
            "OBSERVATION_DATE_MISSING",
        ),
        (
            lambda rows: rows.assign(available_time=rows["available_time"].where(rows.index != 0, "")),
            "AVAILABLE_TIME_MISSING",
        ),
        (
            lambda rows: rows.assign(as_of_date=rows["as_of_date"].where(rows.index != 0, "2024-03-01")),
            "AVAILABLE_TIME_AFTER_AS_OF_DATE",
        ),
        (
            lambda rows: rows.assign(period_end=rows["period_end"].where(rows.index != 0, "2025-01-01")),
            "PERIOD_END_AFTER_AVAILABLE_TIME",
        ),
        (
            lambda rows: rows.assign(stale_after=rows["stale_after"].where(rows.index != 0, "2024-03-01T00:00:00")),
            "STALE_AFTER_BEFORE_AVAILABLE_TIME",
        ),
    ],
)
def test_health_fails_for_identity_timing_and_required_material_fields(
    tmp_path: Path, mutation, expected_code: str
) -> None:
    fixture = build_factor_observation_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).fillna("")
    mutation(rows).to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_factor_observation_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("column", "value", "expected_code"),
    [
        ("source_id", "", "SOURCE_ID_MISSING"),
        ("dataset_id", "", "DOCUMENT_OR_DATASET_MISSING_FOR_EVIDENCE_BACKED"),
        ("source_hash", "", "HASHES_MISSING"),
        ("revision_id", "", "REVISION_ID_MISSING"),
        ("parser_version", "", "PARSER_EXTRACTOR_CALCULATION_VERSION_MISSING"),
        ("extractor_version", "", "PARSER_EXTRACTOR_CALCULATION_VERSION_MISSING"),
        ("calculation_version", "", "PARSER_EXTRACTOR_CALCULATION_VERSION_MISSING"),
        ("factor_observation_type", "BUY_SIGNAL", "FACTOR_OBSERVATION_TYPE_INVALID"),
        ("instrument_type", "BROKER_ACCOUNT", "INSTRUMENT_TYPE_INVALID"),
        ("value_dtype", "PROBABILITY", "VALUE_DTYPE_INVALID"),
        ("direction_rule_type", "BUY_SIGNAL", "DIRECTION_RULE_TYPE_INVALID"),
        ("direction_for_entity", "BUY", "DIRECTION_FOR_ENTITY_INVALID"),
        ("quality_status", "READY_TO_TRADE", "QUALITY_STATUS_INVALID"),
        ("manual_review_status", "READY_TO_TRADE", "MANUAL_REVIEW_STATUS_INVALID"),
        ("trade_usage", "paper_trade", "TRADE_USAGE_INVALID"),
        ("raw_value", "", "OBSERVED_ROW_VALUE_MISSING"),
        ("observation_confidence", "1.2", "CONFIDENCE_OUT_OF_BOUNDS"),
        ("evidence_confidence", "-0.2", "CONFIDENCE_OUT_OF_BOUNDS"),
        ("calculation_confidence", "bad", "CONFIDENCE_OUT_OF_BOUNDS"),
        ("validation_notes", "confidence is return probability", "CONFIDENCE_TREATED_AS_RETURN_PROBABILITY"),
        ("factor_name", "contains access_token test", "SENSITIVE_TEXT_DETECTED"),
        ("trade_usage", "buy_signal", "TRADE_USAGE_FORBIDDEN"),
    ],
)
def test_health_fails_for_lineage_enums_confidence_and_sensitive_values(
    tmp_path: Path, column: str, value: str, expected_code: str
) -> None:
    fixture = build_factor_observation_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).fillna("")
    rows.loc[0, column] = value
    if expected_code == "DOCUMENT_OR_DATASET_MISSING_FOR_EVIDENCE_BACKED":
        rows.loc[0, "document_id"] = ""
    if expected_code == "HASHES_MISSING":
        rows.loc[0, ["content_hash", "metadata_hash"]] = ""
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_factor_observation_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (
            lambda rows: rows.assign(
                raw_value=rows["raw_value"].where(
                    rows["factor_observation_id"] != "SYNTH_BLOCKED_UNVERIFIED_EVENT_OBSERVATION", "1.0"
                )
            ),
            "BLOCKED_ROW_HAS_ACTIVE_VALUE",
        ),
        (
            lambda rows: rows.assign(
                direction_rule_detail=rows["direction_rule_detail"].where(
                    rows["direction_rule_type"].isin(["DIRECT", "UNKNOWN", "RISK_VETO_ONLY"]), ""
                )
            ),
            "MIXED_OR_CONDITIONAL_DIRECTION_DETAIL_MISSING",
        ),
        (
            lambda rows: rows.assign(
                company_exposure_id_refs=rows["company_exposure_id_refs"].where(
                    rows["factor_observation_id"] != "SYNTH_IRON_ORE_COST_PRESSURE_CONTEXT", ""
                )
            ),
            "COMMODITY_EXPOSURE_DIRECTION_CONTEXT_MISSING",
        ),
        (
            lambda rows: rows.assign(
                production_event_ingestion_created=rows["production_event_ingestion_created"].where(
                    rows["factor_observation_id"] != "SYNTH_POLICY_CAPACITY_RESTRICTION_EVENT_CONTEXT", "True"
                )
            ),
            "EVENT_DERIVED_ROW_CLAIMS_PRODUCTION_EVENT_INGESTION",
        ),
        (
            lambda rows: rows.assign(
                production_company_exposure_mapping_created=rows["production_company_exposure_mapping_created"].where(
                    rows["factor_observation_id"] != "SYNTH_EXPORT_TRADE_POLICY_EXPOSURE_CONTEXT", "True"
                )
            ),
            "EXPOSURE_DERIVED_ROW_CLAIMS_PRODUCTION_MAPPING",
        ),
        (
            lambda rows: rows.assign(
                direction_rule_detail=rows["direction_rule_detail"].where(
                    rows["factor_observation_id"] != "SYNTH_ST_DELIST_RISK_VETO_OBSERVATION",
                    "creates positive alpha and buy permission",
                )
            ),
            "RISK_VETO_IMPLIES_POSITIVE_ALPHA_OR_BUY",
        ),
        (
            lambda rows: rows.assign(
                trade_usage=rows["trade_usage"].where(
                    rows["factor_observation_id"] != "SYNTH_BLOCKED_UNVERIFIED_EVENT_OBSERVATION", "research_context"
                )
            ),
            "BLOCKED_ROW_NOT_NO_TRADE",
        ),
        (
            lambda rows: rows.assign(
                pit_valid=rows["pit_valid"].where(
                    rows["factor_observation_id"] != "SYNTH_BLOCKED_UNVERIFIED_EVENT_OBSERVATION", "True"
                )
            ),
            "BLOCKED_ROW_PIT_OR_DECISION_ELIGIBLE",
        ),
    ],
)
def test_health_fails_for_special_direction_event_exposure_risk_and_blocked_contracts(
    tmp_path: Path, mutation, expected_code: str
) -> None:
    fixture = build_factor_observation_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).fillna("")
    mutation(rows).to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_factor_observation_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("column", "value", "expected_code"),
    [
        ("normalization_status", "ACTIVE", "TRANSFORMATION_STATUS_ACTIVE"),
        ("winsorization_status", "APPLIED", "TRANSFORMATION_STATUS_ACTIVE"),
        ("direction_adjustment_status", "ACTIVE", "TRANSFORMATION_STATUS_ACTIVE"),
        ("normalized_value", "1.0", "TRANSFORMATION_VALUE_ACTIVE"),
        ("winsorized_value", "1.0", "TRANSFORMATION_VALUE_ACTIVE"),
        ("direction_adjusted_value", "1.0", "TRANSFORMATION_VALUE_ACTIVE"),
        ("report_only", "False", "ROW_REPORT_ONLY_NOT_TRUE"),
        ("diagnostic_only", "False", "ROW_DIAGNOSTIC_ONLY_NOT_TRUE"),
        ("is_live_signal", "True", "ROW_IS_LIVE_SIGNAL_TRUE"),
        ("is_alpha_claim", "True", "ROW_IS_ALPHA_CLAIM_TRUE"),
        ("signal_score_implemented", "True", "ROW_SIGNAL_SCORE_IMPLEMENTED_TRUE"),
        ("signal_score_input_authorized", "True", "ROW_SIGNAL_SCORE_INPUT_AUTHORIZED_TRUE"),
        ("model_training_allowed", "True", "ROW_MODEL_TRAINING_ALLOWED_TRUE"),
        ("active_weight_allowed", "True", "ROW_ACTIVE_WEIGHT_ALLOWED_TRUE"),
        ("active_threshold_allowed", "True", "ROW_ACTIVE_THRESHOLD_ALLOWED_TRUE"),
        ("stock_profile_validation_allowed", "True", "ROW_STOCK_PROFILE_VALIDATION_ALLOWED_TRUE"),
        ("paper_validation_allowed", "True", "ROW_PAPER_VALIDATION_ALLOWED_TRUE"),
        ("real_buy_review_allowed", "True", "ROW_REAL_BUY_REVIEW_ALLOWED_TRUE"),
        ("buy_review_allowed", "True", "ROW_BUY_REVIEW_ALLOWED_TRUE"),
        ("strategy_performance_validated", "True", "ROW_STRATEGY_PERFORMANCE_VALIDATED_TRUE"),
        ("trading_allowed", "True", "ROW_TRADING_ALLOWED_TRUE"),
    ],
)
def test_health_fails_when_row_transform_or_safety_flags_are_invalid(
    tmp_path: Path, column: str, value: str, expected_code: str
) -> None:
    fixture = build_factor_observation_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).fillna("")
    rows.loc[0, column] = value
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_factor_observation_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize("flag", FORBIDDEN_METADATA_FALSE_FLAGS)
def test_health_fails_when_any_forbidden_metadata_flag_is_true(tmp_path: Path, flag: str) -> None:
    fixture = build_factor_observation_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata[flag] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_factor_observation_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert "FORBIDDEN_METADATA_FLAG_TRUE" in _issue_codes(result)


def test_health_fails_when_artifact_paths_point_to_protected_operational_outputs(tmp_path: Path) -> None:
    fixture = build_factor_observation_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["artifact_paths"]["fixture_rows"] = "data/raw/factor_observation_fixture_rows.csv"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_factor_observation_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert "UNSAFE_ARTIFACT_PATH" in _issue_codes(result)


def test_status_safe_empty_and_latest_fixture_summary(tmp_path: Path) -> None:
    empty = run_factor_observation_schema_fixture_status(root=tmp_path / "missing", output_dir=tmp_path / "empty_status")
    assert empty.status == "PASS"
    assert empty.workflow_stage == NO_FACTOR_OBSERVATION_SCHEMA_FIXTURE
    assert empty.health_status == "PASS"
    assert empty.latest_run_id == ""

    fixture = build_factor_observation_schema_fixture(output_dir=tmp_path)
    result = run_factor_observation_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert result.status == "PASS"
    assert result.workflow_stage == FACTOR_OBSERVATION_SCHEMA_FIXTURE_CREATED
    assert result.health_status == "PASS"
    assert result.latest_run_id == fixture.factor_observation_schema_fixture_id
    assert result.observation_count == 10
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.factor_observation_schema_fixture_created is True
    assert result.factor_observation_rows_created is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert getattr(result, flag) is False
    assert "report-only" in result.next_action
    assert "research-status/checkpoint integration" not in result.next_action
    assert "post-checkpoint governance audit" in result.next_action
    assert "real factor observations" in result.next_action
    assert "production factor registry" in result.next_action
    assert "trading workflow" in result.next_action


def test_status_marks_invalid_fixture_without_granting_downstream_readiness(tmp_path: Path) -> None:
    fixture = build_factor_observation_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["production_factor_observations_created"] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = run_factor_observation_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert result.status == "FAIL"
    assert result.workflow_stage == FACTOR_OBSERVATION_SCHEMA_FIXTURE_INVALID
    assert result.production_factor_observations_created is True
    assert result.signal_score_implemented is False
    assert result.signal_score_input_authorized is False
    assert result.model_training_performed is False
    assert result.active_weights_created is False
    assert result.active_thresholds_created is False
    assert result.buy_review_allowed is False
    assert result.strategy_performance_validated is False
    assert result.trading_allowed is False


def test_cli_index_health_status_commands_run_successfully(tmp_path: Path) -> None:
    root = tmp_path / "manual_diagnostics" / "factor_observation_schema_fixture_v0_1"
    build_factor_observation_schema_fixture(output_dir=root)

    env = {**os.environ, "PYTHONPATH": "src"}
    for command in [
        "factor-observation-schema-fixture-index",
        "factor-observation-schema-fixture-health",
        "factor-observation-schema-fixture-status",
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
        assert "factor observation schema fixture" in completed.stdout.lower()
        assert "trading" in completed.stdout.lower()

    assert not (tmp_path / "docs" / "project_sources").exists()


def test_required_factor_observation_fields_are_view_contract_inputs() -> None:
    assert "factor_observation_id" in REQUIRED_FACTOR_OBSERVATION_FIELDS
    assert "factor_id" in REQUIRED_FACTOR_OBSERVATION_FIELDS
    assert "factor_definition_version" in REQUIRED_FACTOR_OBSERVATION_FIELDS
    assert "available_time" in REQUIRED_FACTOR_OBSERVATION_FIELDS
    assert "signal_score_input_authorized" in REQUIRED_FACTOR_OBSERVATION_FIELDS
    assert "trading_allowed" in REQUIRED_FACTOR_OBSERVATION_FIELDS


def _metadata(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _issue_codes(result) -> set[str]:
    if result.health_frame.empty:
        return set()
    return set(result.health_frame["issue_code"].astype(str))
