from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system.factor_definition_schema_fixture import (
    CANONICAL_TAXONOMY_LAYERS,
    MOJIBAKE_LAYER_NAME_FRAGMENTS,
    REQUIRED_FACTOR_DEFINITION_FIELDS,
    build_factor_definition_schema_fixture,
)


EXPECTED_ARTIFACTS = {
    "factor_definition_schema_fixture_metadata.json",
    "factor_definition_schema_fields.csv",
    "factor_definition_fixture_rows.csv",
    "factor_definition_taxonomy_layer_matrix.csv",
    "factor_definition_usage_boundary_matrix.csv",
    "factor_definition_validation_summary.csv",
    "factor_definition_limitations.md",
    "recommended_next_task.md",
}

FORBIDDEN_FALSE_METADATA_FLAGS = [
    "signal_score_formula_active",
    "signal_score_implemented",
    "live_signals_created",
    "signal_semantics_changed",
    "factor_observations_created",
    "event_ingestion_created",
    "company_exposure_created",
    "replay_evidence_bundle_created",
    "model_training_performed",
    "active_weights_created",
    "active_thresholds_created",
    "stock_profile_validation_created",
    "paper_validation_created",
    "real_buy_review_eligible",
    "buy_review_allowed",
    "strategy_performance_validated",
    "trading_allowed",
    "live_trading_enabled",
    "broker_api_called",
    "external_api_called",
    "llm_api_called",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
    "active_stock_profile_created",
    "operational_global_approved_for_paper_granted",
]


def _build(tmp_path: Path):
    return build_factor_definition_schema_fixture(
        output_dir=tmp_path / "outputs" / "reports" / "manual_diagnostics" / "factor_definition_schema_fixture_v0_1"
    )


def test_factor_definition_schema_fixture_writes_expected_artifacts(tmp_path: Path) -> None:
    result = _build(tmp_path)

    assert result.status == "PASS"
    assert result.workflow_stage == "FACTOR_DEFINITION_SCHEMA_FIXTURE_CREATED"
    assert result.factor_count == 8
    assert result.taxonomy_layer_count == 8
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_paths["artifact_dir"].is_relative_to(
        tmp_path / "outputs" / "reports" / "manual_diagnostics" / "factor_definition_schema_fixture_v0_1"
    )
    assert {path.name for path in result.artifact_paths["artifact_dir"].iterdir()} == EXPECTED_ARTIFACTS
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()


def test_metadata_keeps_report_only_counts_and_forbidden_flags_false(tmp_path: Path) -> None:
    result = _build(tmp_path)

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["factor_definition_schema_fixture_created"] is True
    assert metadata["status"] == "PASS"
    assert metadata["workflow_stage"] == "FACTOR_DEFINITION_SCHEMA_FIXTURE_CREATED"
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert metadata["factor_definition_rows_created"] is True
    assert metadata["factor_count"] == 8
    assert metadata["taxonomy_layer_count"] == 8
    assert metadata["taxonomy_primary_classification"] is True
    assert metadata["legacy_12_factor_tags_checklist_only"] is True
    for flag in FORBIDDEN_FALSE_METADATA_FLAGS:
        assert metadata[flag] is False


def test_schema_fields_and_fixture_rows_include_required_fields(tmp_path: Path) -> None:
    result = _build(tmp_path)

    fields = pd.read_csv(result.artifact_paths["schema_fields"], dtype=str)
    rows = pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str)

    assert set(REQUIRED_FACTOR_DEFINITION_FIELDS).issubset(set(fields["field_name"]))
    assert set(REQUIRED_FACTOR_DEFINITION_FIELDS).issubset(set(rows.columns))
    assert len(rows) == 8
    assert rows["factor_id"].map(type).eq(str).all()
    assert rows["factor_id"].str.len().gt(0).all()
    assert rows["factor_version"].str.len().gt(0).all()


def test_fixture_rows_cover_canonical_taxonomy_layers_with_exact_names(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str)

    assert rows["taxonomy_layer_id"].tolist() == list(CANONICAL_TAXONOMY_LAYERS)
    assert rows["taxonomy_layer_id"].is_unique
    for layer_id, layer_name in CANONICAL_TAXONOMY_LAYERS.items():
        actual = rows.loc[rows["taxonomy_layer_id"] == layer_id, "taxonomy_layer_name"].iloc[0]
        assert actual == layer_name

    layer_text = " ".join(rows["taxonomy_layer_name"].fillna("").astype(str))
    for fragment in MOJIBAKE_LAYER_NAME_FRAGMENTS:
        assert fragment not in layer_text


def test_legacy_tags_are_checklist_only_and_taxonomy_is_primary(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str).fillna("")
    matrix = pd.read_csv(result.artifact_paths["taxonomy_layer_matrix"], dtype=str)
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert rows["legacy_12_factor_tags"].str.len().gt(0).all()
    assert metadata["taxonomy_primary_classification"] is True
    assert metadata["legacy_12_factor_tags_checklist_only"] is True
    assert (matrix["taxonomy_primary"] == "True").all()
    assert (matrix["legacy_12_factor_tags_primary"] == "False").all()


def test_fixture_rows_require_source_registry_and_raw_document_store(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str)

    assert (rows["source_registry_required"] == "True").all()
    assert (rows["raw_document_store_required"] == "True").all()
    assert rows["available_time_policy"].str.len().gt(0).all()
    assert rows["revision_policy"].str.len().gt(0).all()
    assert rows["compliance_class"].str.len().gt(0).all()


def test_fixture_rows_are_diagnostic_only_and_never_live_or_alpha(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str)

    assert (rows["report_only"] == "True").all()
    assert (rows["diagnostic_only"] == "True").all()
    assert (rows["is_live_signal"] == "False").all()
    assert (rows["is_alpha_claim"] == "False").all()
    assert (rows["signal_score_component_allowed"] == "False").all()
    assert (rows["model_training_allowed"] == "False").all()
    assert (rows["active_weight_allowed"] == "False").all()
    assert (rows["active_threshold_allowed"] == "False").all()
    assert (rows["real_buy_review_allowed"] == "False").all()
    assert (rows["trading_allowed"] == "False").all()
    assert set(rows["validation_status"]) <= {"DIAGNOSTIC_ONLY", "REVIEW_REQUIRED"}


def test_trade_usage_direction_and_risk_veto_boundaries(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str).set_index("factor_id")
    allowed_trade_usage = {
        "research_feature",
        "event_context",
        "market_confirmation",
        "risk_filter",
        "observe_only",
        "no_trade",
        "diagnostic_only",
    }
    forbidden_trade_usage = {"buy_signal", "sell_signal", "real_buy_review", "trading_signal"}

    assert set(rows["trade_usage"]) <= allowed_trade_usage
    assert not set(rows["trade_usage"]) & forbidden_trade_usage
    mixed = rows[rows["expected_direction"].isin(["MIXED_BY_EXPOSURE", "MIXED_BY_REGIME"])]
    assert mixed["direction_rule_detail"].str.len().gt(0).all()

    risk_veto = rows.loc["L8_ST_STATUS_RISK_VETO_SAMPLE"]
    assert risk_veto["factor_kind"] == "RISK_VETO"
    assert risk_veto["expected_direction"] == "RISK_VETO_ONLY"
    assert risk_veto["trade_usage"] == "risk_filter"
    assert "cannot create positive alpha or buy permission" in risk_veto["direction_rule_detail"]


def test_disclosure_sentiment_and_volume_rows_do_not_imply_buy_sell(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str).set_index("factor_id")

    l5 = rows.loc["L5_VOLUME_CONFIRMATION_SAMPLE"]
    l6 = rows.loc["L6_ANNOUNCEMENT_EVENT_SAMPLE"]
    assert l5["trade_usage"] == "market_confirmation"
    assert l5["expected_direction"] == "NEUTRAL"
    assert "cannot be interpreted as buy/sell" in l5["direction_rule_detail"]
    assert l6["factor_kind"] == "TEXT_DERIVED_EVENT"
    assert l6["trade_usage"] == "event_context"
    assert "do not directly create buy/sell signals" in l6["direction_rule_detail"]


def test_validation_usage_matrix_and_artifacts_do_not_activate_signal_score(tmp_path: Path) -> None:
    result = _build(tmp_path)
    usage = pd.read_csv(result.artifact_paths["usage_boundary_matrix"], dtype=str)
    validation = pd.read_csv(result.artifact_paths["validation_summary"], dtype=str)

    assert (usage["signal_score_component_allowed"] == "False").all()
    assert (usage["model_training_allowed"] == "False").all()
    assert (usage["active_weight_allowed"] == "False").all()
    assert (usage["active_threshold_allowed"] == "False").all()
    assert (usage["real_buy_review_allowed"] == "False").all()
    assert (usage["trading_allowed"] == "False").all()
    assert (validation["passed"] == "True").all()

    artifact_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in result.artifact_paths["artifact_dir"].iterdir()
        if path.suffix in {".json", ".csv", ".md"}
    ).lower()
    assert "signal_score_formula_active,true" not in artifact_text
    assert "signal_score_implemented,true" not in artifact_text
    assert "buy_signal" not in artifact_text
    assert "sell_signal" not in artifact_text
    assert "trading_signal" not in artifact_text


def test_recommended_next_task_views_commands_and_project_source_boundary(tmp_path: Path) -> None:
    result = _build(tmp_path)
    next_task = result.artifact_paths["recommended_next_task"].read_text(encoding="utf-8")

    assert "Factor Definition Schema Fixture Views Report-Only v0.1" in next_task
    assert "research-status" not in next_task.lower()
    assert not (tmp_path / "docs" / "project_sources").exists()

    help_output = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout
    assert "factor-definition-schema-fixture" in help_output
    assert "factor-definition-schema-fixture-index" in help_output
    assert "factor-definition-schema-fixture-health" in help_output
    assert "factor-definition-schema-fixture-status" in help_output
    assert "factor-definition-schema-fixture-research-status" not in help_output


def test_cli_command_runs_successfully(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "factor_definition_schema_fixture_v0_1"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "factor-definition-schema-fixture",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "factor_definition_schema_fixture_id:" in completed.stdout
    assert "status: PASS" in completed.stdout
    assert "workflow_stage: FACTOR_DEFINITION_SCHEMA_FIXTURE_CREATED" in completed.stdout
    assert "factor_count: 8" in completed.stdout
    assert "taxonomy_layer_count: 8" in completed.stdout
    assert "report_only: True" in completed.stdout
    assert "diagnostic_only: True" in completed.stdout
    assert "No factor observations, event ingestion, company exposure" in completed.stdout

    artifact_dirs = [path for path in output_dir.iterdir() if path.is_dir()]
    assert len(artifact_dirs) == 1
    assert (artifact_dirs[0] / "factor_definition_fixture_rows.csv").exists()
