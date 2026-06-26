from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.company_exposure_schema_fixture import (
    FORBIDDEN_METADATA_FALSE_FLAGS,
    REQUIRED_COMPANY_EXPOSURE_FIELDS,
    build_company_exposure_schema_fixture,
)
from quant_replay_system.company_exposure_schema_fixture_health import check_company_exposure_schema_fixture_health
from quant_replay_system.company_exposure_schema_fixture_index import build_company_exposure_schema_fixture_index
from quant_replay_system.company_exposure_schema_fixture_status import (
    COMPANY_EXPOSURE_SCHEMA_FIXTURE_CREATED,
    COMPANY_EXPOSURE_SCHEMA_FIXTURE_INVALID,
    NO_COMPANY_EXPOSURE_SCHEMA_FIXTURE,
    run_company_exposure_schema_fixture_status,
)


def test_index_safe_empty_behavior(tmp_path: Path) -> None:
    result = build_company_exposure_schema_fixture_index(root=tmp_path / "missing", output_dir=tmp_path / "index")

    assert result.artifact_count == 0
    assert result.latest_run_id == ""
    assert result.latest_status == "NO_INPUT"
    assert result.latest_workflow_stage == NO_COMPANY_EXPOSURE_SCHEMA_FIXTURE
    assert result.latest_health_status == "PASS"
    assert result.index_frame.empty
    assert result.artifact_paths["index_csv"].exists()


def test_index_ignores_view_directories_and_discovers_valid_fixture(tmp_path: Path) -> None:
    fixture = build_company_exposure_schema_fixture(output_dir=tmp_path)
    for name in ["index", "health", "status"]:
        (tmp_path / name).mkdir()

    result = build_company_exposure_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    assert result.latest_run_id == fixture.company_exposure_schema_fixture_id
    assert result.latest_status == "PASS"
    assert result.latest_workflow_stage == COMPANY_EXPOSURE_SCHEMA_FIXTURE_CREATED
    assert result.latest_health_status == "PASS"
    assert result.index_frame.loc[0, "company_exposure_schema_fixture_id"] == fixture.company_exposure_schema_fixture_id


def test_index_preserves_numeric_looking_run_ids_as_strings(tmp_path: Path) -> None:
    fixture = build_company_exposure_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["company_exposure_schema_fixture_id"] = "522962104398"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = build_company_exposure_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")

    assert result.latest_run_id == "522962104398"
    assert isinstance(result.index_frame.loc[0, "company_exposure_schema_fixture_id"], str)
    written = pd.read_csv(result.artifact_paths["index_csv"], dtype=str)
    assert written.loc[0, "company_exposure_schema_fixture_id"] == "522962104398"


def test_index_exposes_expected_artifact_paths_counts_and_flags(tmp_path: Path) -> None:
    fixture = build_company_exposure_schema_fixture(output_dir=tmp_path)

    result = build_company_exposure_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")
    row = result.index_frame.loc[0]

    assert row["metadata_path"] == str(fixture.artifact_paths["metadata"])
    assert row["schema_fields_path"] == str(fixture.artifact_paths["schema_fields"])
    assert row["fixture_rows_path"] == str(fixture.artifact_paths["fixture_rows"])
    assert row["type_matrix_path"] == str(fixture.artifact_paths["type_matrix"])
    assert row["direction_matrix_path"] == str(fixture.artifact_paths["direction_matrix"])
    assert row["pit_lineage_matrix_path"] == str(fixture.artifact_paths["pit_lineage_matrix"])
    assert row["validation_summary_path"] == str(fixture.artifact_paths["validation_summary"])
    assert row["limitations_path"] == str(fixture.artifact_paths["limitations"])
    assert row["recommended_next_task_path"] == str(fixture.artifact_paths["recommended_next_task"])
    assert row["expected_artifacts"] == 9
    assert row["exposure_count"] == 10
    assert row["validation_issue_count"] == 0
    assert row["company_exposure_schema_fixture_created"] is True
    assert row["company_exposure_rows_created"] is True
    assert row["report_only"] is True
    assert row["diagnostic_only"] is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert row[flag] is False


def test_health_passes_for_empty_and_valid_fixture_runs(tmp_path: Path) -> None:
    empty = check_company_exposure_schema_fixture_health(root=tmp_path / "missing", output_dir=tmp_path / "empty_health")
    assert empty.status == "PASS"
    assert empty.checked_artifact_count == 0
    assert empty.issue_count == 0

    build_company_exposure_schema_fixture(output_dir=tmp_path)
    result = check_company_exposure_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0
    assert result.artifact_paths["health_csv"].exists()


def test_health_fails_when_metadata_unreadable_or_required_artifact_missing(tmp_path: Path) -> None:
    fixture = build_company_exposure_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["metadata"].write_text("{not-json", encoding="utf-8")

    result = check_company_exposure_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_bad_json")
    assert "METADATA_UNREADABLE" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_company_exposure_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["fixture_rows"].unlink()

    result = check_company_exposure_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_missing")
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fails_when_status_or_required_columns_are_invalid(tmp_path: Path) -> None:
    fixture = build_company_exposure_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["status"] = "MAYBE"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_company_exposure_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_status")
    assert "UNKNOWN_STATUS" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_company_exposure_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).drop(columns=["available_time"])
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_company_exposure_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_rows")
    assert "FIXTURE_ROWS_REQUIRED_COLUMNS_MISSING" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_company_exposure_schema_fixture(output_dir=tmp_path)
    fields = pd.read_csv(fixture.artifact_paths["schema_fields"], dtype=str)
    fields = fields[fields["field_name"] != "available_time"]
    fields.to_csv(fixture.artifact_paths["schema_fields"], index=False)

    result = check_company_exposure_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_fields")
    assert "SCHEMA_FIELDS_REQUIRED_FIELDS_MISSING" in _issue_codes(result)


def test_health_fails_when_exposure_count_or_identity_contract_is_invalid(tmp_path: Path) -> None:
    cases = [
        (lambda rows: rows.iloc[:-1], "EXPOSURE_COUNT_NOT_10"),
        (
            lambda rows: rows.assign(
                company_exposure_id=rows["company_exposure_id"].where(rows.index != 1, rows.loc[0, "company_exposure_id"])
            ),
            "COMPANY_EXPOSURE_ID_NOT_UNIQUE",
        ),
        (lambda rows: rows.assign(company_exposure_version=rows["company_exposure_version"].where(rows.index != 0, "")), "COMPANY_EXPOSURE_VERSION_MISSING"),
        (lambda rows: rows.assign(symbol=rows["symbol"].where(rows.index != 0, "1")), "ENTITY_ID_OR_SYMBOL_NOT_STRING_PRESERVED"),
    ]
    for index, (mutation, expected_code) in enumerate(cases):
        root = tmp_path / f"identity_{index}"
        fixture = build_company_exposure_schema_fixture(output_dir=root)
        rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str)
        mutation(rows).to_csv(fixture.artifact_paths["fixture_rows"], index=False)

        result = check_company_exposure_schema_fixture_health(root=root, output_dir=root / "health")

        assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("column", "value", "expected_code"),
    [
        ("instrument_type", "ACCOUNT", "INSTRUMENT_TYPE_INVALID"),
        ("exposure_type", "ALPHA", "EXPOSURE_TYPE_INVALID"),
        ("exposure_measure_type", "RETURN_PROBABILITY", "EXPOSURE_MEASURE_TYPE_INVALID"),
        ("exposure_strength_bucket", "BUY", "EXPOSURE_STRENGTH_BUCKET_INVALID"),
        ("mapping_method", "PRIVATE_API_DERIVED", "MAPPING_METHOD_INVALID"),
        ("evidence_specificity", "BROKER_PRIVATE", "EVIDENCE_SPECIFICITY_INVALID"),
        ("direction_rule_type", "BUY_SIGNAL", "DIRECTION_RULE_TYPE_INVALID"),
        ("direction_for_factor_increase", "BUY", "DIRECTION_FOR_FACTOR_INCREASE_INVALID"),
    ],
)
def test_health_fails_when_enum_fields_are_invalid(tmp_path: Path, column: str, value: str, expected_code: str) -> None:
    fixture = build_company_exposure_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str)
    rows.loc[0, column] = value
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_company_exposure_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (
            lambda rows: rows.assign(
                direction_rule_detail=rows["direction_rule_detail"].where(
                    rows["direction_for_factor_increase"] != "CONDITIONAL", ""
                )
            ),
            "MIXED_OR_CONDITIONAL_DIRECTION_DETAIL_MISSING",
        ),
        (
            lambda rows: rows.assign(
                direction_for_factor_increase=rows["direction_for_factor_increase"].where(
                    rows["company_exposure_id"] != "SYNTH_STEEL_IRON_ORE_COST_BUYER", "POSITIVE"
                )
            ),
            "IRON_ORE_OPPOSITE_DIRECTION_BROKEN",
        ),
        (
            lambda rows: rows.assign(
                direction_rule_detail=rows["direction_rule_detail"].where(
                    rows["company_exposure_id"] != "SYNTH_ST_STATUS_RISK_VETO_EXPOSURE",
                    "creates positive alpha and buy permission",
                )
            ),
            "RISK_VETO_IMPLIES_POSITIVE_ALPHA_OR_BUY",
        ),
        (
            lambda rows: rows.assign(
                trade_usage=rows["trade_usage"].where(
                    rows["company_exposure_id"] != "SYNTH_BLOCKED_PRIVATE_SUPPLIER_RELATIONSHIP", "research_context"
                )
            ),
            "BLOCKED_ROW_NOT_NO_TRADE",
        ),
        (
            lambda rows: rows.assign(
                pit_valid=rows["pit_valid"].where(
                    rows["company_exposure_id"] != "SYNTH_BLOCKED_PRIVATE_SUPPLIER_RELATIONSHIP", "True"
                )
            ),
            "BLOCKED_ROW_PIT_OR_DECISION_ELIGIBLE",
        ),
        (
            lambda rows: rows.assign(
                direction_rule_detail=rows["direction_rule_detail"].where(
                    rows["company_exposure_id"] != "SYNTH_ETF_INDEX_HOLDING_EXPOSURE",
                    "claims real/current holdings ingestion",
                )
            ),
            "ETF_ROW_CLAIMS_REAL_CURRENT_HOLDINGS",
        ),
    ],
)
def test_health_fails_when_direction_and_special_case_contracts_are_invalid(
    tmp_path: Path, mutation, expected_code: str
) -> None:
    fixture = build_company_exposure_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str)
    mutation(rows).to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_company_exposure_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("column", "value", "expected_code"),
    [
        ("source_id", "", "SOURCE_ID_MISSING"),
        ("document_version_id", "", "DOCUMENT_VERSION_ID_MISSING_FOR_EVIDENCE_BACKED"),
        ("source_hash", "", "HASH_OR_CONTENT_HASH_MISSING"),
        ("revision_id", "", "REVISION_ID_MISSING"),
        ("mapping_version", "", "MAPPING_VERSION_MISSING"),
        ("available_time", "", "AVAILABLE_TIME_MISSING"),
        ("quality_status", "BAD", "QUALITY_STATUS_INVALID_OR_MISSING"),
        ("manual_review_status", "BAD", "MANUAL_REVIEW_STATUS_INVALID_OR_MISSING"),
        ("mapping_confidence", "1.2", "MAPPING_CONFIDENCE_OUT_OF_BOUNDS"),
        ("direction_rule_detail", "mapping confidence is return probability", "MAPPING_CONFIDENCE_TREATED_AS_RETURN_PROBABILITY"),
        ("proxy_reason", "", "PROXY_REASON_MISSING"),
        ("trade_usage", "buy_signal", "TRADE_USAGE_FORBIDDEN"),
        ("entity_name", "contains secret-like text", "SENSITIVE_TEXT_DETECTED"),
    ],
)
def test_health_fails_when_required_values_are_invalid(
    tmp_path: Path, column: str, value: str, expected_code: str
) -> None:
    fixture = build_company_exposure_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str)
    mask = rows["is_proxy"].eq("True") if column == "proxy_reason" else rows.index == 0
    rows.loc[mask, column] = value
    if expected_code == "HASH_OR_CONTENT_HASH_MISSING":
        rows.loc[mask, "content_hash"] = ""
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_company_exposure_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


def test_health_fails_when_time_ordering_is_invalid(tmp_path: Path) -> None:
    cases = [
        ("effective_to", "2023-01-01", "EFFECTIVE_TIME_ORDER_INVALID"),
        ("as_of_date", "2024-03-01", "AVAILABLE_TIME_AFTER_AS_OF_DATE"),
        ("stale_after", "2024-03-01T00:00:00", "STALE_AFTER_BEFORE_AVAILABLE_TIME"),
    ]
    for index, (column, value, expected_code) in enumerate(cases):
        root = tmp_path / f"time_{index}"
        fixture = build_company_exposure_schema_fixture(output_dir=root)
        rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str)
        rows.loc[0, column] = value
        rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

        result = check_company_exposure_schema_fixture_health(root=root, output_dir=root / "health")

        assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("column", "value", "expected_code"),
    [
        ("report_only", "False", "ROW_REPORT_ONLY_NOT_TRUE"),
        ("diagnostic_only", "False", "ROW_DIAGNOSTIC_ONLY_NOT_TRUE"),
        ("is_live_signal", "True", "ROW_IS_LIVE_SIGNAL_TRUE"),
        ("is_alpha_claim", "True", "ROW_IS_ALPHA_CLAIM_TRUE"),
        ("model_training_allowed", "True", "ROW_MODEL_TRAINING_ALLOWED_TRUE"),
        ("active_weight_allowed", "True", "ROW_ACTIVE_WEIGHT_ALLOWED_TRUE"),
        ("active_threshold_allowed", "True", "ROW_ACTIVE_THRESHOLD_ALLOWED_TRUE"),
        ("stock_profile_validation_allowed", "True", "ROW_STOCK_PROFILE_VALIDATION_ALLOWED_TRUE"),
        ("real_buy_review_allowed", "True", "ROW_REAL_BUY_REVIEW_ALLOWED_TRUE"),
        ("trading_allowed", "True", "ROW_TRADING_ALLOWED_TRUE"),
    ],
)
def test_health_fails_when_row_safety_flags_are_invalid(
    tmp_path: Path, column: str, value: str, expected_code: str
) -> None:
    fixture = build_company_exposure_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str)
    rows.loc[0, column] = value
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_company_exposure_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize("flag", FORBIDDEN_METADATA_FALSE_FLAGS)
def test_health_fails_when_any_forbidden_metadata_flag_is_true(tmp_path: Path, flag: str) -> None:
    fixture = build_company_exposure_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata[flag] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_company_exposure_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert "FORBIDDEN_METADATA_FLAG_TRUE" in _issue_codes(result)


def test_health_fails_when_artifact_paths_point_to_protected_operational_outputs(tmp_path: Path) -> None:
    fixture = build_company_exposure_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["artifact_paths"]["fixture_rows"] = "data/raw/company_exposure_fixture_rows.csv"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_company_exposure_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert "UNSAFE_ARTIFACT_PATH" in _issue_codes(result)


def test_status_safe_empty_behavior_and_latest_fixture_summary(tmp_path: Path) -> None:
    empty = run_company_exposure_schema_fixture_status(root=tmp_path / "missing", output_dir=tmp_path / "empty_status")
    assert empty.status == "PASS"
    assert empty.workflow_stage == NO_COMPANY_EXPOSURE_SCHEMA_FIXTURE
    assert empty.health_status == "PASS"
    assert empty.latest_run_id == ""

    fixture = build_company_exposure_schema_fixture(output_dir=tmp_path)
    result = run_company_exposure_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert result.status == "PASS"
    assert result.workflow_stage == COMPANY_EXPOSURE_SCHEMA_FIXTURE_CREATED
    assert result.health_status == "PASS"
    assert result.latest_run_id == fixture.company_exposure_schema_fixture_id
    assert result.exposure_count == 10
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.company_exposure_schema_fixture_created is True
    assert result.company_exposure_rows_created is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert getattr(result, flag) is False
    assert "Company Exposure Schema Fixture Views are report-only" in result.next_action
    assert "research-status/checkpoint integration only after the views remain stable" in result.next_action
    assert "trading permission" in result.next_action


def test_status_marks_invalid_fixture_without_granting_downstream_readiness(tmp_path: Path) -> None:
    fixture = build_company_exposure_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["factor_observations_created"] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = run_company_exposure_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert result.status == "FAIL"
    assert result.workflow_stage == COMPANY_EXPOSURE_SCHEMA_FIXTURE_INVALID
    assert result.factor_observations_created is True
    assert result.signal_score_implemented is False
    assert result.model_training_performed is False
    assert result.active_weights_created is False
    assert result.active_thresholds_created is False
    assert result.buy_review_allowed is False
    assert result.strategy_performance_validated is False
    assert result.trading_allowed is False


def test_cli_index_health_status_commands_run_successfully(tmp_path: Path) -> None:
    root = tmp_path / "manual_diagnostics" / "company_exposure_schema_fixture_v0_1"
    build_company_exposure_schema_fixture(output_dir=root)

    env = {**os.environ, "PYTHONPATH": "src"}
    for command in [
        "company-exposure-schema-fixture-index",
        "company-exposure-schema-fixture-health",
        "company-exposure-schema-fixture-status",
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
        assert "company exposure schema fixture" in completed.stdout.lower()
        assert "trading" in completed.stdout.lower()

    assert not (tmp_path / "docs" / "project_sources").exists()


def test_required_company_exposure_fields_are_view_contract_inputs() -> None:
    assert "company_exposure_id" in REQUIRED_COMPANY_EXPOSURE_FIELDS
    assert "direction_for_factor_increase" in REQUIRED_COMPANY_EXPOSURE_FIELDS
    assert "mapping_confidence" in REQUIRED_COMPANY_EXPOSURE_FIELDS
    assert "trading_allowed" in REQUIRED_COMPANY_EXPOSURE_FIELDS


def _metadata(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _issue_codes(result) -> set[str]:
    if result.health_frame.empty:
        return set()
    return set(result.health_frame["issue_code"].astype(str))
