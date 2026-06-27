from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system.replay_evidence_bundle_schema_fixture import (
    ADMISSIBILITY_STATUSES,
    ALLOWED_TRADE_USAGE,
    BUNDLE_COMPLETENESS_STATUSES,
    BUNDLE_STATUSES,
    COMPLIANCE_CLASSES,
    EVIDENCE_ITEM_TYPES,
    FORBIDDEN_METADATA_FALSE_FLAGS,
    FORBIDDEN_TRADE_USAGE,
    MANUAL_REVIEW_STATUSES,
    QUALITY_STATUSES,
    REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED,
    REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS,
    RISK_VETO_TYPES,
    build_replay_evidence_bundle_schema_fixture,
)


EXPECTED_ARTIFACTS = {
    "replay_evidence_bundle_schema_fixture_metadata.json",
    "replay_evidence_bundle_schema_fields.csv",
    "replay_evidence_bundle_fixture_rows.csv",
    "replay_evidence_bundle_item_matrix.csv",
    "replay_evidence_bundle_pit_admissibility_matrix.csv",
    "replay_evidence_bundle_lineage_matrix.csv",
    "replay_evidence_bundle_quality_compliance_matrix.csv",
    "replay_evidence_bundle_risk_veto_matrix.csv",
    "replay_evidence_bundle_forbidden_output_guard_matrix.csv",
    "replay_evidence_bundle_validation_summary.csv",
    "replay_evidence_bundle_limitations.md",
    "recommended_next_task.md",
}


def _build(tmp_path: Path):
    return build_replay_evidence_bundle_schema_fixture(
        output_dir=tmp_path
        / "outputs"
        / "reports"
        / "manual_diagnostics"
        / "replay_evidence_bundle_schema_fixture_v0_1"
    )


def _rows(result) -> pd.DataFrame:
    return pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str).fillna("")


def _metadata(result) -> dict:
    return json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))


def test_replay_evidence_bundle_schema_fixture_writes_required_artifacts(tmp_path: Path) -> None:
    result = _build(tmp_path)

    assert result.status == "PASS"
    assert result.workflow_stage == REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED
    assert result.status != REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED
    assert result.bundle_count == 10
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_paths["artifact_dir"].is_relative_to(
        tmp_path / "outputs" / "reports" / "manual_diagnostics" / "replay_evidence_bundle_schema_fixture_v0_1"
    )
    assert {path.name for path in result.artifact_paths["artifact_dir"].iterdir()} == EXPECTED_ARTIFACTS
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()


def test_metadata_status_stage_and_forbidden_flags_are_safe(tmp_path: Path) -> None:
    metadata = _metadata(_build(tmp_path))

    assert metadata["replay_evidence_bundle_schema_fixture_created"] is True
    assert metadata["replay_evidence_bundle_rows_created"] is True
    assert metadata["status"] == "PASS"
    assert metadata["workflow_stage"] == REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED
    assert metadata["status"] != REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED
    assert metadata["bundle_count"] == 10
    assert metadata["validation_issue_count"] == 0
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert metadata[flag] is False


def test_schema_fields_and_rows_include_required_fields(tmp_path: Path) -> None:
    result = _build(tmp_path)
    fields = pd.read_csv(result.artifact_paths["schema_fields"], dtype=str)
    rows = _rows(result)

    assert set(REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS).issubset(set(fields["field_name"]))
    assert set(REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS).issubset(set(rows.columns))
    assert len(rows) == 10
    assert rows["replay_evidence_bundle_id"].is_unique
    for column in [
        "replay_decision_time",
        "replay_as_of_date",
        "entity_id",
        "symbol",
        "instrument_type",
        "bundle_key",
        "bundle_version",
        "schema_version",
    ]:
        assert rows[column].str.len().gt(0).all()


def test_required_synthetic_cases_are_present(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path))

    assert set(rows["replay_evidence_bundle_id"]) == {
        "SYNTH_COMPLETE_PRICE_VOLUME_FACTOR_BUNDLE",
        "SYNTH_FUNDAMENTAL_AVAILABLE_AFTER_PERIOD_END_BUNDLE",
        "SYNTH_EVENT_POLICY_CONTEXT_BUNDLE",
        "SYNTH_COMPANY_EXPOSURE_DIRECTION_CONTEXT_BUNDLE",
        "SYNTH_COMMODITY_COST_SPREAD_BUNDLE",
        "SYNTH_RISK_VETO_ST_DELIST_BUNDLE",
        "SYNTH_BLOCKED_FUTURE_AVAILABLE_TIME_BUNDLE",
        "SYNTH_BLOCKED_MISSING_HASH_REVISION_BUNDLE",
        "SYNTH_BLOCKED_RESTRICTED_OR_PRIVATE_SOURCE_BUNDLE",
        "SYNTH_OBSERVE_ONLY_INCOMPLETE_CONTEXT_BUNDLE",
    }


def test_rows_use_valid_enums_and_non_actionable_trade_usage(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path))

    assert set(rows["bundle_status"]) <= BUNDLE_STATUSES
    assert set(rows["bundle_completeness_status"]) <= BUNDLE_COMPLETENESS_STATUSES
    assert set(rows["admissibility_status"]) <= ADMISSIBILITY_STATUSES
    assert set(rows["quality_status"]) <= QUALITY_STATUSES
    assert set(rows["manual_review_status"]) <= MANUAL_REVIEW_STATUSES
    assert set(rows["compliance_class"]) <= COMPLIANCE_CLASSES
    assert set(rows["risk_veto_type"]) <= RISK_VETO_TYPES
    assert set(rows["trade_usage"]) <= ALLOWED_TRADE_USAGE
    assert not set(rows["trade_usage"]) & FORBIDDEN_TRADE_USAGE


def test_item_matrix_covers_required_evidence_types(tmp_path: Path) -> None:
    result = _build(tmp_path)
    matrix = pd.read_csv(result.artifact_paths["item_matrix"], dtype=str).fillna("")

    assert set(matrix["evidence_item_type"]) == EVIDENCE_ITEM_TYPES
    assert (matrix["row_count"].astype(int) > 0).all()
    assert (matrix["report_only"] == "True").all()
    assert (matrix["diagnostic_only"] == "True").all()


def test_lineage_references_are_present_where_required(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path))

    assert rows["source_id_refs"].str.len().gt(0).all()
    assert rows["source_registry_run_id"].str.len().gt(0).all()
    assert rows["raw_document_store_run_id"].str.len().gt(0).all()
    assert rows["factor_definition_run_id"].str.len().gt(0).all()
    assert rows["factor_observation_run_id"].str.len().gt(0).all()
    required_raw = rows[rows["raw_document_or_dataset_required"] == "True"]
    assert required_raw.apply(
        lambda row: int(row["raw_document_ref_count"]) + int(row["raw_dataset_ref_count"]) > 0,
        axis=1,
    ).all()
    factor_rows = rows[rows["factor_observation_count"].astype(int) > 0]
    assert factor_rows["factor_id_refs"].str.len().gt(0).all()
    assert factor_rows["factor_definition_version_refs"].str.len().gt(0).all()
    exposure_rows = rows[rows["exposure_context_count"].astype(int) > 0]
    assert exposure_rows["company_exposure_id_refs"].str.len().gt(0).all()
    event_rows = rows[rows["event_count"].astype(int) > 0]
    assert event_rows["event_structured_id_refs"].str.len().gt(0).all()


def test_pit_admissibility_and_future_leakage_guards(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path)).set_index("replay_evidence_bundle_id")

    admissible = rows[rows["admissibility_status"] == "ADMISSIBLE"]
    assert admissible.apply(
        lambda row: pd.Timestamp(row["available_time_max"]) <= pd.Timestamp(row["replay_decision_time"]),
        axis=1,
    ).all()
    assert (admissible["all_available_time_lte_replay_time"] == "True").all()
    assert (rows["future_label_excluded"] == "True").all()
    assert (rows["future_revision_excluded"] == "True").all()
    assert (rows["future_labels_joined"] == "False").all()

    future_blocked = rows.loc["SYNTH_BLOCKED_FUTURE_AVAILABLE_TIME_BUNDLE"]
    assert future_blocked["admissibility_status"] == "BLOCKED_FUTURE_AVAILABLE_TIME"
    assert future_blocked["pit_valid"] == "False"
    assert future_blocked["decision_time_eligible"] == "False"
    assert pd.Timestamp(future_blocked["available_time_max"]) > pd.Timestamp(future_blocked["replay_decision_time"])

    fundamental = rows.loc["SYNTH_FUNDAMENTAL_AVAILABLE_AFTER_PERIOD_END_BUNDLE"]
    assert pd.Timestamp(fundamental["period_end"]) < pd.Timestamp(fundamental["source_publish_time"])
    assert pd.Timestamp(fundamental["source_publish_time"]) < pd.Timestamp(fundamental["available_time_max"])
    assert pd.Timestamp(fundamental["available_time_max"]) <= pd.Timestamp(fundamental["replay_decision_time"])


def test_hash_revision_version_and_source_permission_guards(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path)).set_index("replay_evidence_bundle_id")

    complete = rows[rows["admissibility_status"].isin(["ADMISSIBLE", "OBSERVE_ONLY"])]
    for column in [
        "source_hash_coverage",
        "content_hash_coverage",
        "metadata_hash_coverage",
        "revision_id_coverage",
        "parser_version_refs",
        "extractor_version_refs",
        "calculation_version_refs",
    ]:
        assert complete[column].str.len().gt(0).all()

    missing = rows.loc["SYNTH_BLOCKED_MISSING_HASH_REVISION_BUNDLE"]
    assert missing["admissibility_status"] in {"BLOCKED_MISSING_HASH", "BLOCKED_MISSING_REVISION"}
    assert missing["decision_time_eligible"] == "False"
    assert int(missing["revision_gap_count"]) > 0

    restricted = rows.loc["SYNTH_BLOCKED_RESTRICTED_OR_PRIVATE_SOURCE_BUNDLE"]
    assert restricted["admissibility_status"] == "BLOCKED_PRIVATE_RESTRICTED_ILLEGAL"
    assert restricted["source_permission_status"] == "BLOCKED"
    assert restricted["trade_usage"] == "no_trade"
    assert int(restricted["restricted_source_count"]) + int(restricted["private_source_count"]) > 0


def test_risk_veto_and_observe_only_rows_block_actionability(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path)).set_index("replay_evidence_bundle_id")

    risk = rows.loc["SYNTH_RISK_VETO_ST_DELIST_BUNDLE"]
    assert risk["risk_veto_flag"] == "True"
    assert risk["risk_veto_type"] == "ST_OR_DELIST_RISK"
    assert risk["decision_time_eligible"] == "False"
    assert risk["pit_valid"] == "False"
    assert risk["trade_usage"] in {"no_trade", "risk_filter"}
    assert "no positive alpha" in risk["hard_veto_reason"]

    observe = rows.loc["SYNTH_OBSERVE_ONLY_INCOMPLETE_CONTEXT_BUNDLE"]
    assert observe["bundle_completeness_status"] == "PARTIAL_CONTEXT_ONLY"
    assert observe["admissibility_status"] == "OBSERVE_ONLY"
    assert observe["decision_time_eligible"] == "False"
    assert observe["trade_usage"] == "observe_only"


def test_forbidden_output_flags_are_false_in_rows_metadata_and_guard_matrix(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result)
    metadata = _metadata(result)
    guard = pd.read_csv(result.artifact_paths["forbidden_output_guard_matrix"], dtype=str).fillna("")

    row_false_flags = [
        "real_replay_evidence_bundle_created",
        "replay_decisions_created",
        "forward_labels_created",
        "future_labels_joined",
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
        "live_trading_enabled",
        "broker_api_called",
        "external_api_called",
        "llm_api_called",
        "data_raw_written",
        "data_processed_written",
        "data_cache_written",
        "current_candidates_run",
        "snapshot_built",
        "signal_semantics_changed",
        "active_stock_profile_created",
    ]
    for flag in row_false_flags:
        assert (rows[flag] == "False").all()
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert metadata[flag] is False
    assert (guard["observed_value"] == "False").all()
    assert (guard["passed"] == "True").all()


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
    assert "Replay Evidence Bundle Schema Fixture Views Report-Only v0.1" in next_task
    assert "No real replay evidence bundles" in limitations
    assert "No replay decisions" in limitations
    assert "No forward labels" in limitations
    assert "No signal_score" in limitations
    assert "No model training" in limitations
    assert "No buy-review" in limitations
    assert "No trading" in limitations
    assert not re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", all_text.lower())


def test_cli_command_runs_and_only_core_command_is_registered(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "replay_evidence_bundle_schema_fixture_v0_1"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "replay-evidence-bundle-schema-fixture",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "replay_evidence_bundle_schema_fixture_id:" in completed.stdout
    assert "status: PASS" in completed.stdout
    assert f"workflow_stage: {REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED}" in completed.stdout
    assert "bundle_count: 10" in completed.stdout
    assert "validation_issue_count: 0" in completed.stdout
    assert "report_only: True" in completed.stdout
    assert "diagnostic_only: True" in completed.stdout
    assert "No real replay evidence bundles" in completed.stdout

    artifact_dirs = [path for path in output_dir.iterdir() if path.is_dir()]
    assert len(artifact_dirs) == 1
    assert (artifact_dirs[0] / "replay_evidence_bundle_fixture_rows.csv").exists()

    help_output = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout
    assert "replay-evidence-bundle-schema-fixture" in help_output
    assert "replay-evidence-bundle-schema-fixture-index" in help_output
    assert "replay-evidence-bundle-schema-fixture-health" in help_output
    assert "replay-evidence-bundle-schema-fixture-status" in help_output
