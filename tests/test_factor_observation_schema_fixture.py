from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system.factor_observation_schema_fixture import (
    ALLOWED_TRADE_USAGE,
    DIRECTION_ADJUSTMENT_STATUSES,
    DIRECTION_FOR_ENTITY,
    DIRECTION_RULE_TYPES,
    FACTOR_OBSERVATION_SCHEMA_FIXTURE_CREATED,
    FACTOR_OBSERVATION_TYPES,
    FORBIDDEN_METADATA_FALSE_FLAGS,
    FORBIDDEN_TRADE_USAGE,
    FREQUENCIES,
    INSTRUMENT_TYPES,
    MANUAL_REVIEW_STATUSES,
    NORMALIZATION_STATUSES,
    OBSERVATION_STATUSES,
    QUALITY_STATUSES,
    REQUIRED_FACTOR_OBSERVATION_FIELDS,
    SOURCE_TIERS,
    TRANSFORM_STATUSES,
    VALUE_DTYPES,
    WINSORIZATION_STATUSES,
    build_factor_observation_schema_fixture,
)


EXPECTED_ARTIFACTS = {
    "factor_observation_schema_fixture_metadata.json",
    "factor_observation_schema_fields.csv",
    "factor_observation_fixture_rows.csv",
    "factor_observation_type_matrix.csv",
    "factor_observation_value_semantics_matrix.csv",
    "factor_observation_pit_lineage_matrix.csv",
    "factor_observation_source_quality_matrix.csv",
    "factor_observation_factor_event_exposure_lineage_matrix.csv",
    "factor_observation_validation_summary.csv",
    "factor_observation_limitations.md",
    "recommended_next_task.md",
}


def _build(tmp_path: Path):
    return build_factor_observation_schema_fixture(
        output_dir=tmp_path
        / "outputs"
        / "reports"
        / "manual_diagnostics"
        / "factor_observation_schema_fixture_v0_1"
    )


def _rows(result) -> pd.DataFrame:
    return pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str).fillna("")


def _metadata(result) -> dict:
    return json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))


def test_factor_observation_schema_fixture_writes_required_artifacts(tmp_path: Path) -> None:
    result = _build(tmp_path)

    assert result.status == "PASS"
    assert result.workflow_stage == FACTOR_OBSERVATION_SCHEMA_FIXTURE_CREATED
    assert result.status != FACTOR_OBSERVATION_SCHEMA_FIXTURE_CREATED
    assert result.observation_count == 10
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_paths["artifact_dir"].is_relative_to(
        tmp_path / "outputs" / "reports" / "manual_diagnostics" / "factor_observation_schema_fixture_v0_1"
    )
    assert {path.name for path in result.artifact_paths["artifact_dir"].iterdir()} == EXPECTED_ARTIFACTS
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()


def test_metadata_uses_pass_status_created_stage_and_forbidden_flags_false(tmp_path: Path) -> None:
    result = _build(tmp_path)
    metadata = _metadata(result)

    assert metadata["factor_observation_schema_fixture_created"] is True
    assert metadata["factor_observation_rows_created"] is True
    assert metadata["status"] == "PASS"
    assert metadata["workflow_stage"] == FACTOR_OBSERVATION_SCHEMA_FIXTURE_CREATED
    assert metadata["status"] != FACTOR_OBSERVATION_SCHEMA_FIXTURE_CREATED
    assert metadata["observation_count"] == 10
    assert metadata["validation_issue_count"] == 0
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert metadata[flag] is False


def test_schema_fields_and_rows_include_required_fields(tmp_path: Path) -> None:
    result = _build(tmp_path)
    fields = pd.read_csv(result.artifact_paths["schema_fields"], dtype=str)
    rows = _rows(result)

    assert set(REQUIRED_FACTOR_OBSERVATION_FIELDS).issubset(set(fields["field_name"]))
    assert set(REQUIRED_FACTOR_OBSERVATION_FIELDS).issubset(set(rows.columns))
    assert len(rows) == 10
    assert rows["factor_observation_id"].is_unique
    assert rows["observation_version"].str.len().gt(0).all()
    assert rows["observation_key"].str.len().gt(0).all()
    assert rows["factor_id"].str.len().gt(0).all()
    assert rows["factor_definition_version"].str.len().gt(0).all()
    assert rows["taxonomy_layer_id"].str.len().gt(0).all()


def test_fixture_rows_use_valid_enums_and_non_actionable_trade_usage(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path))

    assert set(rows["factor_observation_type"]) <= FACTOR_OBSERVATION_TYPES
    assert set(rows["instrument_type"]) <= INSTRUMENT_TYPES
    assert set(rows["value_dtype"]) <= VALUE_DTYPES
    assert set(rows["frequency"]) <= FREQUENCIES
    assert set(rows["source_tier"]) <= SOURCE_TIERS
    assert set(rows["direction_rule_type"]) <= DIRECTION_RULE_TYPES
    assert set(rows["direction_for_entity"]) <= DIRECTION_FOR_ENTITY
    assert set(rows["transform_status"]) <= TRANSFORM_STATUSES
    assert set(rows["normalization_status"]) <= NORMALIZATION_STATUSES
    assert set(rows["winsorization_status"]) <= WINSORIZATION_STATUSES
    assert set(rows["direction_adjustment_status"]) <= DIRECTION_ADJUSTMENT_STATUSES
    assert set(rows["quality_status"]) <= QUALITY_STATUSES
    assert set(rows["manual_review_status"]) <= MANUAL_REVIEW_STATUSES
    assert set(rows["observation_status"]) <= OBSERVATION_STATUSES
    assert set(rows["trade_usage"]) <= ALLOWED_TRADE_USAGE
    assert not set(rows["trade_usage"]) & FORBIDDEN_TRADE_USAGE


def test_timing_pit_and_evidence_lineage_are_complete_and_ordered(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path))

    for column in [
        "observation_date",
        "available_time",
        "as_of_date",
        "revision_id",
        "source_id",
        "source_hash",
        "content_hash",
        "metadata_hash",
        "parser_version",
        "extractor_version",
        "calculation_version",
    ]:
        assert rows[column].str.len().gt(0).all()

    assert rows.apply(lambda row: pd.Timestamp(row["available_time"]) <= pd.Timestamp(row["as_of_date"]), axis=1).all()
    assert rows.apply(lambda row: pd.Timestamp(row["available_time"]) <= pd.Timestamp(row["stale_after"]), axis=1).all()
    period_rows = rows[rows["period_end"].str.len() > 0]
    assert period_rows.apply(lambda row: pd.Timestamp(row["period_end"]) <= pd.Timestamp(row["available_time"]), axis=1).all()
    assert len(rows[rows["observation_date"] != rows["available_time"].str[:10]]) >= 6
    assert len(period_rows[period_rows["period_end"] != period_rows["available_time"].str[:10]]) >= 2
    evidence_backed = rows[rows["source_tier"] != "SYNTHETIC_FIXTURE"]
    assert evidence_backed.apply(lambda row: bool(row["document_id"]) or bool(row["dataset_id"]), axis=1).all()


def test_value_semantics_keep_transformations_inactive(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path))

    observed = rows[rows["observation_status"] == "OBSERVED"]
    assert observed.apply(
        lambda row: bool(row["raw_value"]) or bool(row["categorical_value"]) or bool(row["boolean_value"]),
        axis=1,
    ).all()
    assert not rows["normalization_status"].isin({"ACTIVE", "APPLIED"}).any()
    assert not rows["winsorization_status"].isin({"ACTIVE", "APPLIED"}).any()
    assert not rows["direction_adjustment_status"].isin({"ACTIVE", "APPLIED"}).any()
    assert set(rows["normalized_value"]) <= {"", "not_applied"}
    assert set(rows["winsorized_value"]) <= {"", "not_applied"}
    assert set(rows["direction_adjusted_value"]) <= {"", "not_applied"}


def test_direction_event_and_exposure_context_boundaries(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path)).set_index("factor_observation_id")

    commodity = rows.loc["SYNTH_IRON_ORE_COST_PRESSURE_CONTEXT"]
    assert commodity["direction_rule_type"] == "MIXED_BY_EXPOSURE"
    assert commodity["direction_for_entity"] == "MIXED"
    assert "steel buyer" in commodity["direction_rule_detail"]
    assert "resource producer" in commodity["direction_rule_detail"]
    assert commodity["company_exposure_id_refs"]

    event_row = rows.loc["SYNTH_POLICY_CAPACITY_RESTRICTION_EVENT_CONTEXT"]
    assert event_row["event_structured_id_refs"]
    assert event_row["production_event_ingestion_created"] == "False"
    assert event_row["trade_usage"] in {"event_context", "factor_context", "research_context"}

    exposure_row = rows.loc["SYNTH_EXPORT_TRADE_POLICY_EXPOSURE_CONTEXT"]
    assert exposure_row["direction_rule_type"] == "CONDITIONAL"
    assert exposure_row["company_exposure_id_refs"]
    assert exposure_row["production_company_exposure_mapping_created"] == "False"

    conditional = rows[
        rows["direction_rule_type"].isin(["CONDITIONAL", "MIXED_BY_EXPOSURE", "MIXED_BY_REGIME"])
        | rows["direction_for_entity"].isin(["CONDITIONAL", "MIXED"])
    ]
    assert conditional["direction_rule_detail"].str.len().gt(0).all()


def test_risk_veto_and_blocked_rows_fail_closed(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path)).set_index("factor_observation_id")

    risk = rows.loc["SYNTH_ST_DELIST_RISK_VETO_OBSERVATION"]
    assert risk["factor_observation_type"] == "RISK_STATUS"
    assert risk["direction_rule_type"] == "RISK_VETO_ONLY"
    assert risk["direction_for_entity"] == "RISK_VETO_ONLY"
    assert risk["risk_veto_flag"] == "True"
    assert risk["trade_usage"] in {"risk_filter", "no_trade"}
    assert risk["is_alpha_claim"] == "False"
    assert "no positive alpha" in risk["direction_rule_detail"]

    blocked = rows.loc["SYNTH_BLOCKED_UNVERIFIED_EVENT_OBSERVATION"]
    assert blocked["observation_status"] == "BLOCKED"
    assert blocked["quality_status"] == "BLOCKED"
    assert blocked["manual_review_status"] == "BLOCKED"
    assert blocked["value_dtype"] == "BLOCKED"
    assert blocked["raw_value"] == ""
    assert blocked["trade_usage"] == "no_trade"
    assert blocked["pit_valid"] == "False"
    assert blocked["decision_time_eligible"] == "False"


def test_confidence_fields_are_bounded_and_not_return_probabilities(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result)
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in result.artifact_paths["artifact_dir"].iterdir()
        if path.suffix in {".json", ".csv", ".md"}
    ).lower()

    for column in ["observation_confidence", "evidence_confidence", "calculation_confidence"]:
        assert rows[column].astype(float).between(0, 1).all()
    assert "not return probability" in text
    assert "not a signal score" in text
    assert "not a model weight" in text


def test_rows_and_metadata_remain_report_only_and_non_production(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result)
    metadata = _metadata(result)

    for flag in ["report_only", "diagnostic_only"]:
        assert (rows[flag] == "True").all()
    for flag in [
        "is_live_signal",
        "is_alpha_claim",
        "signal_score_implemented",
        "signal_score_input_authorized",
        "model_training_allowed",
        "active_weight_allowed",
        "active_threshold_allowed",
        "stock_profile_validation_allowed",
        "paper_validation_allowed",
        "real_buy_review_allowed",
        "buy_review_allowed",
        "strategy_performance_validated",
        "trading_allowed",
    ]:
        assert (rows[flag] == "False").all()

    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert metadata[flag] is False


def test_validation_summary_limitations_next_task_and_secret_scan(tmp_path: Path) -> None:
    result = _build(tmp_path)
    validation = pd.read_csv(result.artifact_paths["validation_summary"], dtype=str)
    next_task = result.artifact_paths["recommended_next_task"].read_text(encoding="utf-8")
    limitations = result.artifact_paths["limitations"].read_text(encoding="utf-8")
    all_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in result.artifact_paths["artifact_dir"].iterdir()
        if path.suffix in {".json", ".csv", ".md"}
    )

    assert (validation["passed"] == "True").all()
    assert "Factor Observation Schema Fixture Views Report-Only v0.1" in next_task
    assert "research-status" not in next_task.lower()
    assert "No real factor observations" in limitations
    assert "No production factor registry" in limitations
    assert "No normalization, winsorization, or direction-adjustment runtime" in limitations
    assert "No replay evidence bundles" in limitations
    assert "No signal_score" in limitations
    assert "No model training" in limitations
    assert "No buy-review" in limitations
    assert "No trading" in limitations
    assert not re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", all_text.lower())
    assert not (tmp_path / "docs" / "project_sources").exists()


def test_cli_command_runs_and_view_commands_are_registered(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "factor_observation_schema_fixture_v0_1"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "factor-observation-schema-fixture",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "factor_observation_schema_fixture_id:" in completed.stdout
    assert "status: PASS" in completed.stdout
    assert f"workflow_stage: {FACTOR_OBSERVATION_SCHEMA_FIXTURE_CREATED}" in completed.stdout
    assert "observation_count: 10" in completed.stdout
    assert "validation_issue_count: 0" in completed.stdout
    assert "report_only: True" in completed.stdout
    assert "diagnostic_only: True" in completed.stdout
    assert "No real factor observations" in completed.stdout

    artifact_dirs = [path for path in output_dir.iterdir() if path.is_dir()]
    assert len(artifact_dirs) == 1
    assert (artifact_dirs[0] / "factor_observation_fixture_rows.csv").exists()

    help_output = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout
    assert "factor-observation-schema-fixture" in help_output
    assert "factor-observation-schema-fixture-index" in help_output
    assert "factor-observation-schema-fixture-health" in help_output
    assert "factor-observation-schema-fixture-status" in help_output
