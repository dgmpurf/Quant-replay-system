from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.factor_definition_schema_fixture import (
    CANONICAL_TAXONOMY_LAYERS,
    FORBIDDEN_METADATA_FALSE_FLAGS,
    REQUIRED_FACTOR_DEFINITION_FIELDS,
    build_factor_definition_schema_fixture,
)
from quant_replay_system.factor_definition_schema_fixture_health import check_factor_definition_schema_fixture_health
from quant_replay_system.factor_definition_schema_fixture_index import build_factor_definition_schema_fixture_index
from quant_replay_system.factor_definition_schema_fixture_status import (
    FACTOR_DEFINITION_SCHEMA_FIXTURE_CREATED,
    FACTOR_DEFINITION_SCHEMA_FIXTURE_INVALID,
    NO_FACTOR_DEFINITION_SCHEMA_FIXTURE,
    run_factor_definition_schema_fixture_status,
)


def test_index_safe_empty_behavior(tmp_path: Path) -> None:
    result = build_factor_definition_schema_fixture_index(root=tmp_path / "missing", output_dir=tmp_path / "index")

    assert result.artifact_count == 0
    assert result.latest_run_id == ""
    assert result.latest_status == "NO_INPUT"
    assert result.latest_workflow_stage == NO_FACTOR_DEFINITION_SCHEMA_FIXTURE
    assert result.latest_health_status == "PASS"
    assert result.index_frame.empty
    assert result.artifact_paths["index_csv"].exists()


def test_index_ignores_view_directories_and_discovers_valid_fixture(tmp_path: Path) -> None:
    fixture = build_factor_definition_schema_fixture(output_dir=tmp_path)
    for name in ["index", "health", "status"]:
        (tmp_path / name).mkdir()

    result = build_factor_definition_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    assert result.latest_run_id == fixture.factor_definition_schema_fixture_id
    assert result.latest_status == "PASS"
    assert result.latest_workflow_stage == FACTOR_DEFINITION_SCHEMA_FIXTURE_CREATED
    assert result.latest_health_status == "PASS"
    assert result.index_frame.loc[0, "factor_definition_schema_fixture_id"] == fixture.factor_definition_schema_fixture_id


def test_index_preserves_numeric_looking_run_ids_as_strings(tmp_path: Path) -> None:
    fixture = build_factor_definition_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["factor_definition_schema_fixture_id"] = "522962104398"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = build_factor_definition_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")

    assert result.latest_run_id == "522962104398"
    assert isinstance(result.index_frame.loc[0, "factor_definition_schema_fixture_id"], str)
    written = pd.read_csv(result.artifact_paths["index_csv"], dtype=str)
    assert written.loc[0, "factor_definition_schema_fixture_id"] == "522962104398"


def test_index_exposes_expected_artifact_paths_counts_and_flags(tmp_path: Path) -> None:
    fixture = build_factor_definition_schema_fixture(output_dir=tmp_path)

    result = build_factor_definition_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")
    row = result.index_frame.loc[0]

    assert row["metadata_path"] == str(fixture.artifact_paths["metadata"])
    assert row["schema_fields_path"] == str(fixture.artifact_paths["schema_fields"])
    assert row["fixture_rows_path"] == str(fixture.artifact_paths["fixture_rows"])
    assert row["taxonomy_layer_matrix_path"] == str(fixture.artifact_paths["taxonomy_layer_matrix"])
    assert row["usage_boundary_matrix_path"] == str(fixture.artifact_paths["usage_boundary_matrix"])
    assert row["validation_summary_path"] == str(fixture.artifact_paths["validation_summary"])
    assert row["limitations_path"] == str(fixture.artifact_paths["limitations"])
    assert row["recommended_next_task_path"] == str(fixture.artifact_paths["recommended_next_task"])
    assert row["factor_count"] == 8
    assert row["taxonomy_layer_count"] == 8
    assert row["validation_issue_count"] == 0
    assert row["factor_definition_schema_fixture_created"] is True
    assert row["factor_definition_rows_created"] is True
    assert row["taxonomy_primary_classification"] is True
    assert row["legacy_12_factor_tags_checklist_only"] is True
    assert row["report_only"] is True
    assert row["diagnostic_only"] is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert row[flag] is False


def test_health_passes_for_empty_and_valid_fixture_runs(tmp_path: Path) -> None:
    empty = check_factor_definition_schema_fixture_health(root=tmp_path / "missing", output_dir=tmp_path / "empty_health")
    assert empty.status == "PASS"
    assert empty.checked_artifact_count == 0
    assert empty.issue_count == 0

    build_factor_definition_schema_fixture(output_dir=tmp_path)
    result = check_factor_definition_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0
    assert result.artifact_paths["health_csv"].exists()


def test_health_fails_when_metadata_unreadable_or_required_artifact_missing(tmp_path: Path) -> None:
    fixture = build_factor_definition_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["metadata"].write_text("{not-json", encoding="utf-8")

    result = check_factor_definition_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_bad_json")
    assert "METADATA_UNREADABLE" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_factor_definition_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["fixture_rows"].unlink()

    result = check_factor_definition_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_missing")
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fails_when_status_or_required_columns_are_invalid(tmp_path: Path) -> None:
    fixture = build_factor_definition_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["status"] = "MAYBE"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_factor_definition_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_status")
    assert "UNKNOWN_STATUS" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_factor_definition_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).drop(columns=["available_time_policy"])
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_factor_definition_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_rows")
    assert "FIXTURE_ROWS_REQUIRED_COLUMNS_MISSING" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_factor_definition_schema_fixture(output_dir=tmp_path)
    fields = pd.read_csv(fixture.artifact_paths["schema_fields"], dtype=str)
    fields = fields[fields["field_name"] != "available_time_policy"]
    fields.to_csv(fixture.artifact_paths["schema_fields"], index=False)

    result = check_factor_definition_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_fields")
    assert "SCHEMA_FIELDS_REQUIRED_FIELDS_MISSING" in _issue_codes(result)


@pytest.mark.parametrize(
    ("metadata_key", "value", "expected_code"),
    [
        ("factor_count", 7, "FACTOR_COUNT_NOT_8"),
        ("taxonomy_layer_count", 7, "TAXONOMY_LAYER_COUNT_NOT_8"),
        ("taxonomy_primary_classification", False, "TAXONOMY_NOT_PRIMARY"),
        ("legacy_12_factor_tags_checklist_only", False, "LEGACY_TAGS_TREATED_AS_PRIMARY"),
    ],
)
def test_health_fails_when_metadata_contract_is_invalid(
    tmp_path: Path, metadata_key: str, value: object, expected_code: str
) -> None:
    fixture = build_factor_definition_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata[metadata_key] = value
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_factor_definition_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (lambda rows: rows.iloc[:-1], "FACTOR_ROW_COUNT_NOT_8"),
        (
            lambda rows: rows.assign(
                taxonomy_layer_id=rows["taxonomy_layer_id"].where(
                    rows.index != 0, "L2_INDUSTRY_SUPPLY_DEMAND_VALUE_CHAIN_PRICES"
                )
            ),
            "CANONICAL_LAYER_IDS_NOT_ONCE",
        ),
        (
            lambda rows: rows.assign(
                taxonomy_layer_name=rows["taxonomy_layer_name"].where(rows.index != 0, "wrong layer name")
            ),
            "CANONICAL_LAYER_NAME_MISMATCH",
        ),
        (
            lambda rows: rows.assign(
                taxonomy_layer_name=rows["taxonomy_layer_name"].where(rows.index != 0, "缂佸繗鎯€")
            ),
            "MOJIBAKE_LAYER_NAME_DETECTED",
        ),
        (
            lambda rows: rows.assign(factor_kind=rows["factor_kind"].where(rows.index != 0, "ACTION_SIGNAL")),
            "FACTOR_KIND_INVALID",
        ),
        (
            lambda rows: rows.assign(entity_scope=rows["entity_scope"].where(rows.index != 0, "ACCOUNT")),
            "ENTITY_SCOPE_INVALID",
        ),
        (
            lambda rows: rows.assign(trade_usage=rows["trade_usage"].where(rows.index != 0, "buy_signal")),
            "TRADE_USAGE_FORBIDDEN",
        ),
        (
            lambda rows: rows.assign(expected_direction=rows["expected_direction"].where(rows.index != 0, "BUY")),
            "EXPECTED_DIRECTION_INVALID",
        ),
        (
            lambda rows: rows.assign(
                direction_rule_detail=rows["direction_rule_detail"].where(
                    rows["expected_direction"] != "MIXED_BY_EXPOSURE", ""
                )
            ),
            "MIXED_DIRECTION_DETAIL_MISSING",
        ),
        (
            lambda rows: rows.assign(
                expected_direction=rows["expected_direction"].where(
                    rows["factor_id"] != "L8_ST_STATUS_RISK_VETO_SAMPLE", "POSITIVE"
                )
            ),
            "RISK_VETO_POSITIVE_DIRECTION",
        ),
        (
            lambda rows: rows.assign(
                trade_usage=rows["trade_usage"].where(
                    rows["factor_id"] != "L8_ST_STATUS_RISK_VETO_SAMPLE", "research_feature"
                )
            ),
            "RISK_VETO_USAGE_INVALID",
        ),
        (
            lambda rows: rows.assign(
                direction_rule_detail=rows["direction_rule_detail"].where(
                    rows["factor_id"] != "L6_ANNOUNCEMENT_EVENT_SAMPLE", "direct buy signal"
                )
            ),
            "L6_DIRECT_BUY_SELL_IMPLIED",
        ),
    ],
)
def test_health_fails_when_taxonomy_or_usage_rows_are_invalid(tmp_path: Path, mutation, expected_code: str) -> None:
    fixture = build_factor_definition_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str)
    rows = mutation(rows)
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_factor_definition_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("column", "value", "expected_code"),
    [
        ("source_registry_required", "False", "SOURCE_REGISTRY_REQUIRED_NOT_TRUE"),
        ("raw_document_store_required", "False", "RAW_DOCUMENT_STORE_REQUIRED_NOT_TRUE"),
        ("available_time_policy", "", "AVAILABLE_TIME_POLICY_MISSING"),
        ("revision_policy", "", "REVISION_POLICY_MISSING"),
        ("compliance_class", "", "COMPLIANCE_CLASS_MISSING"),
        ("report_only", "False", "ROW_REPORT_ONLY_NOT_TRUE"),
        ("diagnostic_only", "False", "ROW_DIAGNOSTIC_ONLY_NOT_TRUE"),
        ("is_live_signal", "True", "ROW_IS_LIVE_SIGNAL_TRUE"),
        ("is_alpha_claim", "True", "ROW_IS_ALPHA_CLAIM_TRUE"),
        ("model_training_allowed", "True", "ROW_MODEL_TRAINING_ALLOWED_TRUE"),
        ("active_weight_allowed", "True", "ROW_ACTIVE_WEIGHT_ALLOWED_TRUE"),
        ("active_threshold_allowed", "True", "ROW_ACTIVE_THRESHOLD_ALLOWED_TRUE"),
        ("real_buy_review_allowed", "True", "ROW_REAL_BUY_REVIEW_ALLOWED_TRUE"),
        ("trading_allowed", "True", "ROW_TRADING_ALLOWED_TRUE"),
        ("factor_name", "contains secret-like text", "SENSITIVE_TEXT_DETECTED"),
    ],
)
def test_health_fails_when_row_safety_values_are_invalid(
    tmp_path: Path, column: str, value: str, expected_code: str
) -> None:
    fixture = build_factor_definition_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str)
    rows.loc[0, column] = value
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_factor_definition_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize("flag", FORBIDDEN_METADATA_FALSE_FLAGS)
def test_health_fails_when_any_forbidden_metadata_flag_is_true(tmp_path: Path, flag: str) -> None:
    fixture = build_factor_definition_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata[flag] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_factor_definition_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert "FORBIDDEN_METADATA_FLAG_TRUE" in _issue_codes(result)


def test_health_fails_when_artifact_paths_point_to_protected_operational_outputs(tmp_path: Path) -> None:
    fixture = build_factor_definition_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["artifact_paths"]["fixture_rows"] = "data/raw/factor_definition_fixture_rows.csv"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_factor_definition_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert "UNSAFE_ARTIFACT_PATH" in _issue_codes(result)


def test_status_safe_empty_behavior_and_latest_fixture_summary(tmp_path: Path) -> None:
    empty = run_factor_definition_schema_fixture_status(root=tmp_path / "missing", output_dir=tmp_path / "empty_status")
    assert empty.status == "PASS"
    assert empty.workflow_stage == NO_FACTOR_DEFINITION_SCHEMA_FIXTURE
    assert empty.health_status == "PASS"
    assert empty.latest_run_id == ""

    fixture = build_factor_definition_schema_fixture(output_dir=tmp_path)
    result = run_factor_definition_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert result.status == "PASS"
    assert result.workflow_stage == FACTOR_DEFINITION_SCHEMA_FIXTURE_CREATED
    assert result.health_status == "PASS"
    assert result.latest_run_id == fixture.factor_definition_schema_fixture_id
    assert result.factor_count == 8
    assert result.taxonomy_layer_count == 8
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.factor_definition_schema_fixture_created is True
    assert result.factor_definition_rows_created is True
    assert result.taxonomy_primary_classification is True
    assert result.legacy_12_factor_tags_checklist_only is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert getattr(result, flag) is False
    assert "Factor Definition Schema Fixture Views are report-only" in result.next_action
    assert "research-status/checkpoint integration only after" in result.next_action
    assert "live signals" in result.next_action
    assert "trading permission" in result.next_action


def test_status_marks_invalid_fixture_without_granting_downstream_readiness(tmp_path: Path) -> None:
    fixture = build_factor_definition_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["factor_observations_created"] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = run_factor_definition_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert result.status == "FAIL"
    assert result.workflow_stage == FACTOR_DEFINITION_SCHEMA_FIXTURE_INVALID
    assert result.factor_observations_created is True
    assert result.signal_score_implemented is False
    assert result.model_training_performed is False
    assert result.active_weights_created is False
    assert result.active_thresholds_created is False
    assert result.buy_review_allowed is False
    assert result.strategy_performance_validated is False
    assert result.trading_allowed is False


def test_cli_index_health_status_commands_run_successfully(tmp_path: Path) -> None:
    root = tmp_path / "manual_diagnostics" / "factor_definition_schema_fixture_v0_1"
    build_factor_definition_schema_fixture(output_dir=root)

    env = {**os.environ, "PYTHONPATH": "src"}
    for command in [
        "factor-definition-schema-fixture-index",
        "factor-definition-schema-fixture-health",
        "factor-definition-schema-fixture-status",
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
        assert "factor definition schema fixture" in completed.stdout.lower()
        assert "trading" in completed.stdout.lower()

    assert not (tmp_path / "docs" / "project_sources").exists()


def test_canonical_layer_mapping_remains_the_expected_contract() -> None:
    assert list(CANONICAL_TAXONOMY_LAYERS) == [
        "L1_OPERATIONS_COMPANY_EVENTS",
        "L2_INDUSTRY_SUPPLY_DEMAND_VALUE_CHAIN_PRICES",
        "L3_MACRO_LIQUIDITY_POLICY_GLOBAL",
        "L4_CAPITAL_MARKET_INSTITUTIONS_SUPPLY_DEMAND",
        "L5_TRADING_BEHAVIOR_MICROSTRUCTURE",
        "L6_INFORMATION_DISCLOSURE_SENTIMENT_TRANSMISSION",
        "L7_EXPECTATIONS_VALUATION_PRICING_DEVIATION",
        "L8_RISK_EVENTS_COMPLIANCE_BOUNDARY",
    ]


def _metadata(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _issue_codes(result) -> set[str]:
    if result.health_frame.empty:
        return set()
    return set(result.health_frame["issue_code"].astype(str))
