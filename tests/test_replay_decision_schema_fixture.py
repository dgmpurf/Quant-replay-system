from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system.replay_decision_schema_fixture import (
    ALLOWED_DECISION_ACTIONABILITY,
    ALLOWED_DECISION_LABELS,
    ALLOWED_FREEZE_STATUS,
    ALLOWED_TRADE_USAGE,
    FORBIDDEN_METADATA_FALSE_FLAGS,
    FORBIDDEN_TRADE_USAGE,
    REPLAY_DECISION_SCHEMA_FIXTURE_CREATED,
    REQUIRED_REPLAY_DECISION_FIELDS,
    ROW_FALSE_FLAGS,
    build_replay_decision_schema_fixture,
)


EXPECTED_ARTIFACTS = {
    "replay_decision_schema_fixture_metadata.json",
    "replay_decision_schema_fields.csv",
    "replay_decision_fixture_rows.csv",
    "replay_decision_evidence_bundle_matrix.csv",
    "replay_decision_pit_admissibility_matrix.csv",
    "replay_decision_freeze_matrix.csv",
    "replay_decision_label_exclusion_matrix.csv",
    "replay_decision_quality_compliance_matrix.csv",
    "replay_decision_risk_veto_matrix.csv",
    "replay_decision_forbidden_output_guard_matrix.csv",
    "replay_decision_validation_summary.csv",
    "replay_decision_limitations.md",
    "recommended_next_task.md",
}


def _build(tmp_path: Path):
    return build_replay_decision_schema_fixture(
        output_dir=tmp_path
        / "outputs"
        / "reports"
        / "manual_diagnostics"
        / "replay_decision_schema_fixture_v0_1"
    )


def _rows(result) -> pd.DataFrame:
    return pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str).fillna("")


def _metadata(result) -> dict:
    return json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))


def test_replay_decision_schema_fixture_writes_required_artifacts(tmp_path: Path) -> None:
    result = _build(tmp_path)

    assert result.status == "PASS"
    assert result.workflow_stage == REPLAY_DECISION_SCHEMA_FIXTURE_CREATED
    assert result.status != REPLAY_DECISION_SCHEMA_FIXTURE_CREATED
    assert result.decision_count == 10
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_paths["artifact_dir"].is_relative_to(
        tmp_path / "outputs" / "reports" / "manual_diagnostics" / "replay_decision_schema_fixture_v0_1"
    )
    assert {path.name for path in result.artifact_paths["artifact_dir"].iterdir()} == EXPECTED_ARTIFACTS
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()


def test_metadata_status_stage_and_forbidden_flags_are_safe(tmp_path: Path) -> None:
    metadata = _metadata(_build(tmp_path))

    assert metadata["replay_decision_schema_fixture_created"] is True
    assert metadata["replay_decision_rows_created"] is True
    assert metadata["status"] == "PASS"
    assert metadata["workflow_stage"] == REPLAY_DECISION_SCHEMA_FIXTURE_CREATED
    assert metadata["status"] != REPLAY_DECISION_SCHEMA_FIXTURE_CREATED
    assert metadata["decision_count"] == 10
    assert metadata["validation_issue_count"] == 0
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert metadata[flag] is False


def test_schema_fields_and_fixture_rows_include_required_fields(tmp_path: Path) -> None:
    result = _build(tmp_path)
    fields = pd.read_csv(result.artifact_paths["schema_fields"], dtype=str)
    rows = _rows(result)

    assert set(REQUIRED_REPLAY_DECISION_FIELDS).issubset(set(fields["field_name"]))
    assert set(REQUIRED_REPLAY_DECISION_FIELDS).issubset(set(rows.columns))
    assert len(rows) == 10
    assert rows["replay_decision_id"].is_unique
    for column in [
        "replay_decision_time",
        "replay_as_of_date",
        "entity_id",
        "symbol",
        "instrument_type",
        "decision_key",
        "replay_decision_version",
        "schema_version",
    ]:
        assert rows[column].str.len().gt(0).all()


def test_required_synthetic_cases_are_present(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path))

    assert set(rows["replay_decision_id"]) == {
        "SYNTH_WATCH_COMPLETE_EVIDENCE_DECISION",
        "SYNTH_REVIEW_BUY_CANDIDATE_REPORT_ONLY_DECISION",
        "SYNTH_REVIEW_SELL_CANDIDATE_REPORT_ONLY_DECISION",
        "SYNTH_HOLD_REVIEW_DECISION",
        "SYNTH_NO_ACTION_WEAK_EVIDENCE_DECISION",
        "SYNTH_BLOCKED_RISK_VETO_ST_DELIST_DECISION",
        "SYNTH_BLOCKED_FUTURE_AVAILABLE_EVIDENCE_DECISION",
        "SYNTH_BLOCKED_MISSING_REPLAY_EVIDENCE_BUNDLE_DECISION",
        "SYNTH_BLOCKED_RESTRICTED_OR_PRIVATE_SOURCE_DECISION",
        "SYNTH_OBSERVE_ONLY_INCOMPLETE_REVIEW_DECISION",
    }


def test_decision_labels_are_review_only_and_trade_usage_is_safe(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path)).set_index("replay_decision_id")

    assert set(rows["decision_label"]) <= ALLOWED_DECISION_LABELS
    assert set(rows["decision_actionability"]) <= ALLOWED_DECISION_ACTIONABILITY
    assert set(rows["freeze_status"]) <= ALLOWED_FREEZE_STATUS
    assert set(rows["trade_usage"]) <= ALLOWED_TRADE_USAGE
    assert not set(rows["trade_usage"]) & FORBIDDEN_TRADE_USAGE

    buy = rows.loc["SYNTH_REVIEW_BUY_CANDIDATE_REPORT_ONLY_DECISION"]
    assert buy["decision_label"] == "REVIEW_BUY_CANDIDATE"
    assert buy["decision_actionability"] == "review_only"
    assert buy["trade_usage"] == "review_only"
    assert buy["buy_review_allowed"] == "False"
    assert "not a buy instruction" in buy["decision_rationale_summary"]

    sell = rows.loc["SYNTH_REVIEW_SELL_CANDIDATE_REPORT_ONLY_DECISION"]
    assert sell["decision_label"] == "REVIEW_SELL_CANDIDATE"
    assert sell["decision_actionability"] == "review_only"
    assert sell["trade_usage"] == "review_only"
    assert sell["trading_allowed"] == "False"
    assert "not a sell instruction" in sell["decision_rationale_summary"]


def test_evidence_bundle_lineage_and_pit_eligibility(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path)).set_index("replay_decision_id")

    eligible = rows[rows["decision_time_eligible"] == "True"]
    assert eligible["replay_evidence_bundle_id"].str.len().gt(0).all()
    assert (eligible["replay_evidence_bundle_status"] == "PASS").all()
    assert (eligible["replay_evidence_bundle_health_status"] == "PASS").all()
    assert (eligible["replay_evidence_bundle_workflow_stage"] == "REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED").all()
    assert eligible.apply(
        lambda row: pd.Timestamp(row["available_time_max"]) <= pd.Timestamp(row["replay_decision_time"]),
        axis=1,
    ).all()
    assert (eligible["all_inputs_available_lte_decision_time"] == "True").all()
    assert (eligible["pit_valid"] == "True").all()

    future = rows.loc["SYNTH_BLOCKED_FUTURE_AVAILABLE_EVIDENCE_DECISION"]
    assert future["decision_label"] == "BLOCKED"
    assert future["pit_valid"] == "False"
    assert future["decision_time_eligible"] == "False"
    assert future["all_inputs_available_lte_decision_time"] == "False"
    assert pd.Timestamp(future["available_time_max"]) > pd.Timestamp(future["replay_decision_time"])

    missing = rows.loc["SYNTH_BLOCKED_MISSING_REPLAY_EVIDENCE_BUNDLE_DECISION"]
    assert missing["replay_evidence_bundle_id"] == ""
    assert missing["decision_time_eligible"] == "False"
    assert missing["risk_veto_type"] == "MISSING_EVIDENCE_BUNDLE"


def test_label_output_and_downstream_leakage_exclusions(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path))

    true_exclusion_columns = [
        "future_label_excluded",
        "future_outcome_excluded",
        "future_return_excluded",
        "future_revision_excluded",
        "metrics_excluded",
        "training_output_excluded",
        "model_output_excluded",
        "stock_profile_output_excluded",
        "paper_approval_excluded",
        "buy_review_output_excluded",
    ]
    for column in true_exclusion_columns:
        assert (rows[column] == "True").all()

    false_output_columns = [
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
    ]
    for column in false_output_columns:
        assert (rows[column] == "False").all()


def test_risk_veto_restricted_and_observe_only_rows_block_actionability(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path)).set_index("replay_decision_id")

    risk = rows.loc["SYNTH_BLOCKED_RISK_VETO_ST_DELIST_DECISION"]
    assert risk["decision_label"] == "BLOCKED"
    assert risk["risk_veto_flag"] == "True"
    assert risk["risk_veto_type"] == "ST_OR_DELIST_RISK"
    assert risk["decision_actionability"] == "blocked"
    assert risk["trade_usage"] in {"no_trade", "risk_filter"}
    assert risk["decision_time_eligible"] == "False"

    restricted = rows.loc["SYNTH_BLOCKED_RESTRICTED_OR_PRIVATE_SOURCE_DECISION"]
    assert restricted["decision_label"] == "BLOCKED"
    assert restricted["compliance_class"] in {"RESTRICTED", "PRIVATE", "ILLEGAL"}
    assert restricted["trade_usage"] == "no_trade"
    assert restricted["decision_time_eligible"] == "False"
    assert int(restricted["restricted_source_count"]) + int(restricted["private_source_count"]) > 0

    observe = rows.loc["SYNTH_OBSERVE_ONLY_INCOMPLETE_REVIEW_DECISION"]
    assert observe["decision_actionability"] == "observe_only"
    assert observe["manual_review_status"] == "REVIEW_REQUIRED"
    assert observe["freeze_status"] == "NOT_FROZEN_DIAGNOSTIC_ONLY"
    assert observe["decision_time_eligible"] == "False"


def test_freeze_hashes_and_mutation_guards(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path))

    frozen = rows[rows["freeze_status"] == "FROZEN_SYNTHETIC_FIXTURE"]
    assert not frozen.empty
    assert (frozen["mutation_allowed"] == "False").all()
    for column in ["decision_hash", "evidence_snapshot_hash", "source_revision_snapshot_hash", "revision_id"]:
        assert frozen[column].str.len().gt(0).all()

    not_frozen = rows[rows["freeze_status"] != "FROZEN_SYNTHETIC_FIXTURE"]
    assert (not_frozen["mutation_allowed"] == "False").all()


def test_matrix_artifacts_and_validation_summary_are_safe(tmp_path: Path) -> None:
    result = _build(tmp_path)
    validation = pd.read_csv(result.artifact_paths["validation_summary"], dtype=str).fillna("")
    guard = pd.read_csv(result.artifact_paths["forbidden_output_guard_matrix"], dtype=str).fillna("")
    pit = pd.read_csv(result.artifact_paths["pit_admissibility_matrix"], dtype=str).fillna("")
    freeze = pd.read_csv(result.artifact_paths["freeze_matrix"], dtype=str).fillna("")
    label = pd.read_csv(result.artifact_paths["label_exclusion_matrix"], dtype=str).fillna("")

    assert (validation["passed"] == "True").all()
    assert (guard["observed_value"] == "False").all()
    assert (guard["passed"] == "True").all()
    assert len(pit) == 10
    assert len(freeze) == 10
    assert len(label) == 10


def test_rows_metadata_limitations_next_task_and_secret_scan(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result)
    metadata = _metadata(result)
    limitations = result.artifact_paths["limitations"].read_text(encoding="utf-8")
    next_task = result.artifact_paths["recommended_next_task"].read_text(encoding="utf-8")
    all_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in result.artifact_paths["artifact_dir"].iterdir()
        if path.suffix in {".json", ".csv", ".md"}
    )

    for flag in ROW_FALSE_FLAGS:
        assert (rows[flag] == "False").all()
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert metadata[flag] is False
    assert "No real replay decisions" in limitations
    assert "No forward labels" in limitations
    assert "No future labels joined" in limitations
    assert "No signal_score" in limitations
    assert "No model training" in limitations
    assert "No buy-review" in limitations
    assert "No trading" in limitations
    assert "Replay Decision Schema Fixture Views Report-Only v0.1" in next_task
    assert not re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", all_text.lower())


def test_cli_command_runs_and_replay_decision_view_commands_are_registered(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "replay_decision_schema_fixture_v0_1"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "replay-decision-schema-fixture",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "replay_decision_schema_fixture_id:" in completed.stdout
    assert "status: PASS" in completed.stdout
    assert f"workflow_stage: {REPLAY_DECISION_SCHEMA_FIXTURE_CREATED}" in completed.stdout
    assert "decision_count: 10" in completed.stdout
    assert "validation_issue_count: 0" in completed.stdout
    assert "report_only: True" in completed.stdout
    assert "diagnostic_only: True" in completed.stdout
    assert "No real replay decisions" in completed.stdout

    artifact_dirs = [path for path in output_dir.iterdir() if path.is_dir()]
    assert len(artifact_dirs) == 1
    assert (artifact_dirs[0] / "replay_decision_fixture_rows.csv").exists()

    help_output = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout
    assert "replay-decision-schema-fixture" in help_output
    assert "replay-decision-schema-fixture-index" in help_output
    assert "replay-decision-schema-fixture-health" in help_output
    assert "replay-decision-schema-fixture-status" in help_output
