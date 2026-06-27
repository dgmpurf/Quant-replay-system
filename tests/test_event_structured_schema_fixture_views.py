from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.event_structured_schema_fixture import (
    FORBIDDEN_METADATA_FALSE_FLAGS,
    REQUIRED_EVENT_STRUCTURED_FIELDS,
    build_event_structured_schema_fixture,
)
from quant_replay_system.event_structured_schema_fixture_health import check_event_structured_schema_fixture_health
from quant_replay_system.event_structured_schema_fixture_index import (
    EVENT_STRUCTURED_SCHEMA_FIXTURE_CREATED,
    NO_EVENT_STRUCTURED_SCHEMA_FIXTURE,
    build_event_structured_schema_fixture_index,
)
from quant_replay_system.event_structured_schema_fixture_status import (
    EVENT_STRUCTURED_SCHEMA_FIXTURE_INVALID,
    run_event_structured_schema_fixture_status,
)


def test_index_safe_empty_behavior(tmp_path: Path) -> None:
    result = build_event_structured_schema_fixture_index(root=tmp_path / "missing", output_dir=tmp_path / "index")

    assert result.artifact_count == 0
    assert result.latest_run_id == ""
    assert result.latest_status == "NO_INPUT"
    assert result.latest_workflow_stage == NO_EVENT_STRUCTURED_SCHEMA_FIXTURE
    assert result.latest_health_status == "PASS"
    assert result.index_frame.empty
    assert result.artifact_paths["index_csv"].exists()


def test_index_ignores_view_directories_discovers_fixture_and_preserves_run_id(tmp_path: Path) -> None:
    fixture = build_event_structured_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["event_structured_schema_fixture_id"] = "522962104398"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")
    for name in ["index", "health", "status"]:
        (tmp_path / name).mkdir()

    result = build_event_structured_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")
    row = result.index_frame.loc[0]

    assert result.artifact_count == 1
    assert result.latest_run_id == "522962104398"
    assert isinstance(row["event_structured_schema_fixture_id"], str)
    assert row["event_structured_schema_fixture_id"] == "522962104398"
    assert result.latest_status == "PASS"
    assert result.latest_workflow_stage == EVENT_STRUCTURED_SCHEMA_FIXTURE_CREATED
    assert result.latest_health_status == "PASS"
    assert row["expected_artifacts"] == 10
    assert row["event_count"] == 10
    assert row["validation_issue_count"] == 0
    assert row["metadata_path"] == str(fixture.artifact_paths["metadata"])
    assert row["schema_fields_path"] == str(fixture.artifact_paths["schema_fields"])
    assert row["fixture_rows_path"] == str(fixture.artifact_paths["fixture_rows"])
    assert row["source_quality_matrix_path"] == str(fixture.artifact_paths["source_quality_matrix"])
    assert row["event_structured_schema_fixture_created"] is True
    assert row["event_structured_rows_created"] is True
    assert row["report_only"] is True
    assert row["diagnostic_only"] is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert row[flag] is False
    written = pd.read_csv(result.artifact_paths["index_csv"], dtype=str)
    assert written.loc[0, "event_structured_schema_fixture_id"] == "522962104398"


def test_health_passes_for_empty_and_valid_fixture_runs(tmp_path: Path) -> None:
    empty = check_event_structured_schema_fixture_health(root=tmp_path / "missing", output_dir=tmp_path / "empty_health")
    assert empty.status == "PASS"
    assert empty.checked_artifact_count == 0
    assert empty.issue_count == 0

    build_event_structured_schema_fixture(output_dir=tmp_path)
    result = check_event_structured_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0
    assert result.artifact_paths["health_csv"].exists()


def test_health_fails_when_metadata_unreadable_or_required_artifact_missing(tmp_path: Path) -> None:
    fixture = build_event_structured_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["metadata"].write_text("{not-json", encoding="utf-8")

    result = check_event_structured_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_bad_json")
    assert "METADATA_UNREADABLE" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_event_structured_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["fixture_rows"].unlink()

    result = check_event_structured_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_missing")
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fails_when_status_or_required_columns_are_invalid(tmp_path: Path) -> None:
    fixture = build_event_structured_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["status"] = "MAYBE"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_event_structured_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_status")
    assert "UNKNOWN_STATUS" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_event_structured_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).drop(columns=["available_time"])
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_event_structured_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_rows")
    assert "FIXTURE_ROWS_REQUIRED_COLUMNS_MISSING" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_event_structured_schema_fixture(output_dir=tmp_path)
    fields = pd.read_csv(fixture.artifact_paths["schema_fields"], dtype=str)
    fields = fields[fields["field_name"] != "available_time"]
    fields.to_csv(fixture.artifact_paths["schema_fields"], index=False)

    result = check_event_structured_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_fields")
    assert "SCHEMA_FIELDS_REQUIRED_FIELDS_MISSING" in _issue_codes(result)


def test_health_fails_when_count_identity_or_timing_contract_is_invalid(tmp_path: Path) -> None:
    cases = [
        (lambda rows: rows.iloc[:-1], "EVENT_COUNT_NOT_10"),
        (
            lambda rows: rows.assign(
                event_structured_id=rows["event_structured_id"].where(rows.index != 1, rows.loc[0, "event_structured_id"])
            ),
            "EVENT_STRUCTURED_ID_NOT_UNIQUE",
        ),
        (lambda rows: rows.assign(event_version=rows["event_version"].where(rows.index != 0, "")), "EVENT_VERSION_MISSING"),
        (lambda rows: rows.assign(publish_time=rows["event_time"], available_time=rows["event_time"]), "TIMING_SEPARATION_INSUFFICIENT"),
        (lambda rows: rows.assign(available_time=rows["available_time"].where(rows.index != 0, "")), "AVAILABLE_TIME_MISSING"),
        (lambda rows: rows.assign(as_of_date=rows["as_of_date"].where(rows.index != 0, "2024-03-01")), "AVAILABLE_TIME_AFTER_AS_OF_DATE"),
        (lambda rows: rows.assign(stale_after=rows["stale_after"].where(rows.index != 0, "2024-03-01T00:00:00")), "STALE_AFTER_BEFORE_AVAILABLE_TIME"),
    ]
    for index, (mutation, expected_code) in enumerate(cases):
        root = tmp_path / f"identity_{index}"
        fixture = build_event_structured_schema_fixture(output_dir=root)
        rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str)
        mutation(rows).to_csv(fixture.artifact_paths["fixture_rows"], index=False)

        result = check_event_structured_schema_fixture_health(root=root, output_dir=root / "health")

        assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("column", "value", "expected_code"),
    [
        ("source_id", "", "SOURCE_ID_MISSING"),
        ("document_id", "", "DOCUMENT_ID_MISSING_FOR_EVIDENCE_BACKED"),
        ("document_version_id", "", "DOCUMENT_VERSION_ID_MISSING_FOR_EVIDENCE_BACKED"),
        ("source_hash", "", "HASH_OR_CONTENT_HASH_MISSING"),
        ("revision_id", "", "REVISION_ID_MISSING"),
        ("parser_version", "", "PARSER_VERSION_MISSING"),
        ("extractor_version", "", "EXTRACTOR_VERSION_MISSING"),
        ("event_type", "BUY_SIGNAL", "EVENT_TYPE_INVALID"),
        ("event_scope", "TRADING", "EVENT_SCOPE_INVALID"),
        ("source_tier", "PRIVATE_API", "SOURCE_TIER_INVALID"),
        ("direction_rule_type", "BUY_SIGNAL", "DIRECTION_RULE_TYPE_INVALID"),
        ("direction_for_affected_entity", "BUY", "DIRECTION_FOR_AFFECTED_ENTITY_INVALID"),
        ("event_status", "READY_TO_TRADE", "EVENT_STATUS_INVALID"),
        ("quality_status", "READY_TO_TRADE", "QUALITY_STATUS_INVALID"),
        ("manual_review_status", "READY_TO_TRADE", "MANUAL_REVIEW_STATUS_INVALID"),
        ("extraction_confidence", "1.2", "EXTRACTION_CONFIDENCE_OUT_OF_BOUNDS"),
        ("event_confidence", "-0.2", "EVENT_CONFIDENCE_OUT_OF_BOUNDS"),
        ("validation_notes", "confidence is return probability", "CONFIDENCE_TREATED_AS_RETURN_PROBABILITY"),
        ("event_name", "contains access_token test", "SENSITIVE_TEXT_DETECTED"),
        ("trade_usage", "buy_signal", "TRADE_USAGE_FORBIDDEN"),
    ],
)
def test_health_fails_when_required_values_enums_confidence_or_secret_values_are_invalid(
    tmp_path: Path, column: str, value: str, expected_code: str
) -> None:
    fixture = build_event_structured_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str)
    rows.loc[0, column] = value
    if expected_code == "HASH_OR_CONTENT_HASH_MISSING":
        rows.loc[0, "content_hash"] = ""
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_event_structured_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (
            lambda rows: rows.assign(
                direction_rule_detail=rows["direction_rule_detail"].where(
                    rows["direction_rule_type"] != "CONDITIONAL", ""
                )
            ),
            "MIXED_OR_CONDITIONAL_DIRECTION_DETAIL_MISSING",
        ),
        (
            lambda rows: rows.assign(
                company_exposure_id_refs=rows["company_exposure_id_refs"].where(
                    rows["event_structured_id"] != "SYNTH_IRON_ORE_PRICE_SHOCK_PUBLIC", ""
                )
            ),
            "COMMODITY_POLICY_DIRECTION_CONTEXT_MISSING",
        ),
        (
            lambda rows: rows.assign(
                direction_rule_detail=rows["direction_rule_detail"].where(
                    rows["event_structured_id"] != "SYNTH_ST_DELIST_RISK_VETO_EVENT",
                    "creates positive alpha and buy permission",
                )
            ),
            "RISK_VETO_IMPLIES_POSITIVE_ALPHA_OR_BUY",
        ),
        (
            lambda rows: rows.assign(
                trade_usage=rows["trade_usage"].where(
                    rows["event_structured_id"] != "SYNTH_BLOCKED_UNVERIFIED_RUMOR_EVENT", "research_context"
                )
            ),
            "BLOCKED_RUMOR_NOT_NO_TRADE",
        ),
        (
            lambda rows: rows.assign(
                pit_valid=rows["pit_valid"].where(
                    rows["event_structured_id"] != "SYNTH_BLOCKED_UNVERIFIED_RUMOR_EVENT", "True"
                )
            ),
            "BLOCKED_RUMOR_PIT_OR_DECISION_ELIGIBLE",
        ),
        (
            lambda rows: rows.assign(
                validation_notes=rows["validation_notes"].where(
                    rows["event_structured_id"] != "SYNTH_INDEX_REBALANCE_CONTEXT",
                    "claims real/current holdings ingestion",
                )
            ),
            "ETF_INDEX_ROW_CLAIMS_REAL_CURRENT_HOLDINGS",
        ),
    ],
)
def test_health_fails_when_special_direction_blocked_or_etf_contracts_are_invalid(
    tmp_path: Path, mutation, expected_code: str
) -> None:
    fixture = build_event_structured_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str)
    mutation(rows).to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_event_structured_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("column", "value", "expected_code"),
    [
        ("report_only", "False", "ROW_REPORT_ONLY_NOT_TRUE"),
        ("diagnostic_only", "False", "ROW_DIAGNOSTIC_ONLY_NOT_TRUE"),
        ("is_live_signal", "True", "ROW_IS_LIVE_SIGNAL_TRUE"),
        ("is_alpha_claim", "True", "ROW_IS_ALPHA_CLAIM_TRUE"),
        ("signal_score_implemented", "True", "ROW_SIGNAL_SCORE_IMPLEMENTED_TRUE"),
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
    fixture = build_event_structured_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str)
    rows.loc[0, column] = value
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_event_structured_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize("flag", FORBIDDEN_METADATA_FALSE_FLAGS)
def test_health_fails_when_any_forbidden_metadata_flag_is_true(tmp_path: Path, flag: str) -> None:
    fixture = build_event_structured_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata[flag] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_event_structured_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert "FORBIDDEN_METADATA_FLAG_TRUE" in _issue_codes(result)


def test_health_fails_when_artifact_paths_point_to_protected_operational_outputs(tmp_path: Path) -> None:
    fixture = build_event_structured_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["artifact_paths"]["fixture_rows"] = "data/raw/event_structured_fixture_rows.csv"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_event_structured_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert "UNSAFE_ARTIFACT_PATH" in _issue_codes(result)


def test_status_safe_empty_and_latest_fixture_summary(tmp_path: Path) -> None:
    empty = run_event_structured_schema_fixture_status(root=tmp_path / "missing", output_dir=tmp_path / "empty_status")
    assert empty.status == "PASS"
    assert empty.workflow_stage == NO_EVENT_STRUCTURED_SCHEMA_FIXTURE
    assert empty.health_status == "PASS"
    assert empty.latest_run_id == ""

    fixture = build_event_structured_schema_fixture(output_dir=tmp_path)
    result = run_event_structured_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert result.status == "PASS"
    assert result.workflow_stage == EVENT_STRUCTURED_SCHEMA_FIXTURE_CREATED
    assert result.health_status == "PASS"
    assert result.latest_run_id == fixture.event_structured_schema_fixture_id
    assert result.event_count == 10
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.event_structured_schema_fixture_created is True
    assert result.event_structured_rows_created is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert getattr(result, flag) is False
    assert "report-only" in result.next_action
    assert "post-checkpoint governance audit" in result.next_action
    assert "research-status/checkpoint context is available" in result.next_action
    assert "production event ingestion" in result.next_action
    assert "trading workflow" in result.next_action


def test_status_marks_invalid_fixture_without_granting_downstream_readiness(tmp_path: Path) -> None:
    fixture = build_event_structured_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["factor_observations_created"] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = run_event_structured_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert result.status == "FAIL"
    assert result.workflow_stage == EVENT_STRUCTURED_SCHEMA_FIXTURE_INVALID
    assert result.factor_observations_created is True
    assert result.signal_score_implemented is False
    assert result.model_training_performed is False
    assert result.active_weights_created is False
    assert result.active_thresholds_created is False
    assert result.buy_review_allowed is False
    assert result.strategy_performance_validated is False
    assert result.trading_allowed is False


def test_cli_index_health_status_commands_run_successfully(tmp_path: Path) -> None:
    root = tmp_path / "manual_diagnostics" / "event_structured_schema_fixture_v0_1"
    build_event_structured_schema_fixture(output_dir=root)

    env = {**os.environ, "PYTHONPATH": "src"}
    for command in [
        "event-structured-schema-fixture-index",
        "event-structured-schema-fixture-health",
        "event-structured-schema-fixture-status",
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
        assert "event structured schema fixture" in completed.stdout.lower()
        assert "trading" in completed.stdout.lower()

    assert not (tmp_path / "docs" / "project_sources").exists()


def test_required_event_structured_fields_are_view_contract_inputs() -> None:
    assert "event_structured_id" in REQUIRED_EVENT_STRUCTURED_FIELDS
    assert "event_time" in REQUIRED_EVENT_STRUCTURED_FIELDS
    assert "publish_time" in REQUIRED_EVENT_STRUCTURED_FIELDS
    assert "available_time" in REQUIRED_EVENT_STRUCTURED_FIELDS
    assert "direction_for_affected_entity" in REQUIRED_EVENT_STRUCTURED_FIELDS
    assert "trading_allowed" in REQUIRED_EVENT_STRUCTURED_FIELDS


def _metadata(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _issue_codes(result) -> set[str]:
    if result.health_frame.empty:
        return set()
    return set(result.health_frame["issue_code"].astype(str))
