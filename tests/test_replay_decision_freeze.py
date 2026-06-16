from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.actual_replay_execute import ACTUAL_REPLAY_EXECUTED
from quant_replay_system.replay_decision_freeze import (
    NO_REPLAY_DECISION_FREEZE_INPUT,
    READY_FOR_REPLAY_DECISION_FREEZE,
    REPLAY_DECISION_FREEZE_ATTESTATION_BLOCKED,
    REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED,
    REPLAY_DECISION_FREEZE_EVIDENCE_BLOCKED,
    REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED,
    REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED,
    REPLAY_DECISION_FREEZE_OVERCLAIM_BLOCKED,
    REPLAY_DECISION_FREEZE_PIT_BLOCKED,
    REPLAY_DECISION_FREEZE_REVIEW_BLOCKED,
    REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED,
    REPLAY_DECISION_FREEZE_SOURCE_BLOCKED,
    REPLAY_DECISION_FREEZE_TAXONOMY_BLOCKED,
    REPLAY_DECISION_FROZEN,
    ReplayDecisionFreezeSettings,
    run_replay_decision_freeze,
)
from quant_replay_system.replay_decision_freeze_health import check_replay_decision_freeze_health
from quant_replay_system.replay_decision_freeze_index import build_replay_decision_freeze_index
from quant_replay_system.replay_decision_freeze_status import (
    REPLAY_DECISION_FREEZE_NO_INPUT_ARTIFACT,
    run_replay_decision_freeze_status,
)


EXACT_APPROVAL = (
    "I explicitly authorize implementation of replay decision freeze core only, "
    "report-only, no forward labels, no training, no stock_profile, no buy-review, no trading."
)

ALLOWED_LABELS = {
    "WATCH",
    "REVIEW_BUY_CANDIDATE",
    "REVIEW_SELL_CANDIDATE",
    "HOLD_REVIEW",
    "NO_ACTION",
    "BLOCKED",
}
FORBIDDEN_DECISION_COLUMNS = {
    "future_close",
    "future_price",
    "forward_return",
    "forward_return_label",
    "benchmark_relative_return",
    "industry_relative_return",
    "max_drawdown",
    "max_runup",
    "hit_miss",
    "false_positive",
    "false_negative",
    "training_score",
    "model_weight",
    "stock_profile_status",
    "real_buy_review_eligible",
    "approved_for_paper",
    "order_id",
    "broker_order_id",
    "trade_id",
}


def test_no_input_writes_required_artifacts_with_safe_defaults(tmp_path: Path) -> None:
    result = run_replay_decision_freeze(ReplayDecisionFreezeSettings(output_dir=_output_dir(tmp_path)))

    assert result.status == NO_REPLAY_DECISION_FREEZE_INPUT
    assert result.workflow_stage == "REPLAY_DECISION_FREEZE_NO_INPUT"
    assert result.ready_for_replay_decision_freeze is False
    assert result.replay_decision_freeze_executed is False
    assert result.replay_decision_frozen is False
    assert result.replay_decision_artifacts_created is False
    _assert_downstream_flags_false(result)
    assert result.report_only is True
    assert result.diagnostic_only is True
    for key in _required_artifact_keys():
        assert result.artifact_paths[key].exists()
    metadata = _read_json(result.artifact_paths["metadata"])
    safety = _read_json(result.artifact_paths["safety_flags"])
    assert metadata["execution_status"] == NO_REPLAY_DECISION_FREEZE_INPUT
    assert metadata["ready_for_replay_decision_freeze"] is False
    for field in _downstream_false_fields():
        assert metadata[field] is False
        assert safety[field] is False


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("actual_replay_execution_artifact_path", REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED),
        ("actual_replay_execution_health_artifact_path", REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED),
        ("actual_replay_execution_status_artifact_path", REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED),
        ("replay_decision_freeze_plan_path", REPLAY_DECISION_FREEZE_REVIEW_BLOCKED),
        ("approval_manifest_path", REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED),
        ("replay_decision_freeze_request_manifest_path", REPLAY_DECISION_FREEZE_REVIEW_BLOCKED),
        ("replay_decision_freeze_authority_manifest_path", REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED),
        ("second_reviewer_attestation_manifest_path", REPLAY_DECISION_FREEZE_ATTESTATION_BLOCKED),
        ("pit_source_evidence_bundle_path", REPLAY_DECISION_FREEZE_EVIDENCE_BLOCKED),
        ("taxonomy_evidence_bundle_path", REPLAY_DECISION_FREEZE_TAXONOMY_BLOCKED),
        ("factor_event_company_evidence_bundle_path", REPLAY_DECISION_FREEZE_EVIDENCE_BLOCKED),
        ("source_hash_revision_available_time_evidence_path", REPLAY_DECISION_FREEZE_SOURCE_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", REPLAY_DECISION_FREEZE_OVERCLAIM_BLOCKED),
        ("replay_decision_candidate_manifest_path", REPLAY_DECISION_FREEZE_REVIEW_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(tmp_path: Path, setting_name: str, expected_status: str) -> None:
    result = run_replay_decision_freeze(replace(_happy_settings(tmp_path), **{setting_name: None}))

    assert result.status == expected_status
    assert result.ready_for_replay_decision_freeze is False
    assert result.replay_decision_frozen is False
    assert result.replay_decisions_created is False


@pytest.mark.parametrize(
    ("path_name", "override", "expected_status"),
    [
        ("approval_manifest_path", {"approval_text": ""}, REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED),
        ("approval_manifest_path", {"approval_text": "continue"}, REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED),
        ("approval_manifest_path", {"approval_text": "freeze decisions"}, REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED),
        ("approval_manifest_path", {"approval_text": "make replay decisions"}, REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED),
        ("approval_manifest_path", {"approval_text": "go ahead"}, REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED),
        ("approval_manifest_path", {"approval_text": "Implement replay decision freeze and forward labels."}, REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED),
        ("approval_manifest_path", {"approval_text": "Implement replay decision freeze and training."}, REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED),
        ("approval_manifest_path", {"approval_text": "Implement replay decision freeze and stock_profile."}, REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED),
        ("approval_manifest_path", {"approval_text": "Implement replay decision freeze and buy-review."}, REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED),
        ("approval_manifest_path", {"approval_text": "Implement replay decision freeze and trading."}, REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED),
        ("actual_replay_execution_artifact_path", {"execution_status": "READY_FOR_ACTUAL_REPLAY_EXECUTION"}, REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED),
        ("actual_replay_execution_health_artifact_path", {"health_status": "FAIL"}, REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED),
        ("actual_replay_execution_artifact_path", {"actual_replay_executed": False}, REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED),
        ("actual_replay_execution_artifact_path", {"replay_execution_started": False}, REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED),
        ("actual_replay_execution_artifact_path", {"replay_execution_completed": False}, REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED),
        ("actual_replay_execution_artifact_path", {"source_active_input_creation_run_id": ""}, REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED),
        ("actual_replay_execution_artifact_path", {"source_real_replay_precheck_run_id": ""}, REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED),
        ("replay_decision_freeze_request_manifest_path", {"replay_decision_freeze_core_requested": False}, REPLAY_DECISION_FREEZE_REVIEW_BLOCKED),
        ("replay_decision_freeze_authority_manifest_path", {"authority_result": "REJECTED"}, REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED),
        ("second_reviewer_attestation_manifest_path", {"second_reviewer_attested": False}, REPLAY_DECISION_FREEZE_ATTESTATION_BLOCKED),
        ("pit_source_evidence_bundle_path", {"accepted_pit_universe_evidence_attached": False}, REPLAY_DECISION_FREEZE_PIT_BLOCKED),
        ("pit_source_evidence_bundle_path", {"source_registry_evidence_attached": False}, REPLAY_DECISION_FREEZE_SOURCE_BLOCKED),
        ("taxonomy_evidence_bundle_path", {"uses_8_layer_taxonomy": False}, REPLAY_DECISION_FREEZE_TAXONOMY_BLOCKED),
        ("factor_event_company_evidence_bundle_path", {"event_structured_attached": False}, REPLAY_DECISION_FREEZE_EVIDENCE_BLOCKED),
        ("source_hash_revision_available_time_evidence_path", {"available_time_policy_attached": False}, REPLAY_DECISION_FREEZE_SOURCE_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", {"no_future_labels": False}, REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", {"no_broker_api_called": False}, REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED),
        ("overclaim_evidence_bundle_path", {"replay_decision_not_forward_label_permission": False}, REPLAY_DECISION_FREEZE_OVERCLAIM_BLOCKED),
    ],
)
def test_manifest_gate_failures_block(
    tmp_path: Path,
    path_name: str,
    override: dict[str, object],
    expected_status: str,
) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(getattr(settings, path_name), override)

    result = run_replay_decision_freeze(settings)

    assert result.status == expected_status
    assert result.ready_for_replay_decision_freeze is False
    assert result.replay_decision_frozen is False
    assert result.replay_decisions_created is False


@pytest.mark.parametrize(
    ("unsafe_field", "expected_status"),
    [
        ("forward_labels_allowed", REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED),
        ("forward_labels_exist", REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED),
        ("forward_return_labels_created", REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED),
        ("forward_returns_exist", REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED),
        ("training_allowed", REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED),
        ("weights_trained", REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED),
        ("training_result_created", REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED),
        ("stock_profile_allowed", REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED),
        ("active_stock_profile_exists", REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED),
        ("stock_profile_created", REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED),
        ("buy_review_allowed", REPLAY_DECISION_FREEZE_OVERCLAIM_BLOCKED),
        ("real_buy_review_eligible", REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED),
        ("approved_for_paper", REPLAY_DECISION_FREEZE_OVERCLAIM_BLOCKED),
        ("trading_allowed", REPLAY_DECISION_FREEZE_OVERCLAIM_BLOCKED),
        ("order_placed", REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED),
        ("broker_api_called", REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED),
        ("message_sent", REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED),
        ("llm_api_called", REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED),
        ("external_api_called", REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED),
        ("cache_mutated", REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED),
        ("data_raw_written", REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED),
        ("data_processed_written", REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED),
        ("data_cache_written", REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED),
        ("current_candidates_run", REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED),
        ("snapshot_built", REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED),
    ],
)
def test_unsafe_input_flags_block(tmp_path: Path, unsafe_field: str, expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.actual_replay_execution_artifact_path, {unsafe_field: True})

    result = run_replay_decision_freeze(settings)

    assert result.status == expected_status
    assert result.replay_decision_frozen is False
    assert result.replay_decisions_created is False


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_replay_decision_freeze(ReplayDecisionFreezeSettings(output_dir=tmp_path / "unsafe"))


def test_happy_path_without_allow_reaches_ready_but_does_not_freeze(tmp_path: Path) -> None:
    result = run_replay_decision_freeze(_happy_settings(tmp_path))

    assert result.status == READY_FOR_REPLAY_DECISION_FREEZE
    assert result.workflow_stage == READY_FOR_REPLAY_DECISION_FREEZE
    assert result.ready_for_replay_decision_freeze is True
    assert result.replay_decision_freeze_executed is False
    assert result.replay_decision_frozen is False
    assert result.replay_decision_artifacts_created is False
    assert result.replay_decisions_created is False
    assert result.replay_decisions_exist is False
    assert result.replay_decision_artifact_path == ""
    _assert_downstream_flags_false(result)


def test_happy_path_with_explicit_allow_freezes_replay_decision_artifacts_only(tmp_path: Path) -> None:
    result = run_replay_decision_freeze(replace(_happy_settings(tmp_path), allow_replay_decision_freeze=True))

    assert result.status == REPLAY_DECISION_FROZEN
    assert result.workflow_stage == REPLAY_DECISION_FROZEN
    assert result.ready_for_replay_decision_freeze is True
    assert result.replay_decision_freeze_executed is True
    assert result.replay_decision_frozen is True
    assert result.replay_decision_artifacts_created is True
    assert result.replay_decisions_created is True
    assert result.replay_decisions_exist is True
    assert result.replay_decision_artifact_path.endswith("replay_decision_rows.csv")
    _assert_downstream_flags_false(result)

    metadata = _read_json(result.artifact_paths["metadata"])
    rows = pd.read_csv(result.artifact_paths["replay_decision_rows"])
    evidence = pd.read_csv(result.artifact_paths["replay_decision_evidence_index"])
    safety = _read_json(result.artifact_paths["safety_flags"])
    report = result.artifact_paths["report"].read_text(encoding="utf-8")

    assert metadata["execution_status"] == REPLAY_DECISION_FROZEN
    assert metadata["source_actual_replay_execution_run_id"] == "ad8dfa413ded"
    assert metadata["actual_replay_execution_status"] == ACTUAL_REPLAY_EXECUTED
    assert metadata["actual_replay_execution_health_status"] == "PASS"
    assert metadata["replay_decisions_created"] is True
    assert set(rows["decision_label"]).issubset(ALLOWED_LABELS)
    assert FORBIDDEN_DECISION_COLUMNS.isdisjoint(set(rows.columns))
    assert rows["actual_replay_execution_run_id"].iloc[0] == "ad8dfa413ded"
    assert rows["source_active_input_creation_run_id"].iloc[0] == "293deb5f459a"
    assert rows["source_real_replay_precheck_run_id"].iloc[0] == "0657ae658ab8"
    for column in [
        "replay_decision_id",
        "evidence_bundle_id",
        "available_time_max",
        "source_hash_coverage",
        "revision_id_coverage",
        "taxonomy_coverage",
        "report_only",
        "diagnostic_only",
    ]:
        assert column in rows.columns
    for column in [
        "replay_decision_id",
        "evidence_bundle_id",
        "source_id",
        "source_hash",
        "revision_id",
        "available_time",
        "taxonomy_layer",
        "factor_ids",
        "event_ids",
        "pit_valid",
        "quality_status",
        "permission_class",
    ]:
        assert column in evidence.columns
    for field in _safety_false_fields():
        assert safety[field] is False
    for phrase in [
        "not forward-label",
        "not training",
        "not stock_profile",
        "not buy-review",
        "not trading",
    ]:
        assert phrase in report


def test_cli_replay_decision_freeze_runs_no_input(tmp_path: Path, capsys) -> None:
    code = cli.main(["replay-decision-freeze", "--output-dir", str(_output_dir(tmp_path))])
    output = capsys.readouterr()

    assert code == 0
    assert "status: NO_REPLAY_DECISION_FREEZE_INPUT" in output.out
    assert "workflow_stage: REPLAY_DECISION_FREEZE_NO_INPUT" in output.out
    assert "ready_for_replay_decision_freeze: False" in output.out
    assert "replay_decision_frozen: False" in output.out
    assert "replay_decisions_created: False" in output.out
    assert "forward_labels_allowed: False" in output.out
    assert "training_allowed: False" in output.out
    assert "trading_allowed: False" in output.out


def test_cli_happy_path_without_allow_reaches_ready_but_does_not_freeze(tmp_path: Path) -> None:
    completed = _run_cli_with_settings(_happy_settings(tmp_path), allow=False)

    assert f"status: {READY_FOR_REPLAY_DECISION_FREEZE}" in completed.stdout
    assert "ready_for_replay_decision_freeze: True" in completed.stdout
    assert "replay_decision_frozen: False" in completed.stdout
    assert "replay_decisions_created: False" in completed.stdout


def test_cli_happy_path_with_allow_freezes_report_only_decisions(tmp_path: Path) -> None:
    completed = _run_cli_with_settings(_happy_settings(tmp_path), allow=True)

    assert f"status: {REPLAY_DECISION_FROZEN}" in completed.stdout
    assert "ready_for_replay_decision_freeze: True" in completed.stdout
    assert "replay_decision_frozen: True" in completed.stdout
    assert "replay_decisions_created: True" in completed.stdout
    assert "forward_labels_allowed: False" in completed.stdout
    assert "forward_return_labels_created: False" in completed.stdout
    assert "training_result_created: False" in completed.stdout
    assert "stock_profile_created: False" in completed.stdout
    assert "real_buy_review_eligible: False" in completed.stdout
    assert "trading_allowed: False" in completed.stdout


def test_artifact_view_commands_and_checkpoint_docs_exist_without_project_source_pack() -> None:
    parser = cli.build_parser()
    command_names = {action.dest for action in parser._subparsers._group_actions[0]._choices_actions}
    assert "replay-decision-freeze" in command_names
    assert "replay-decision-freeze-index" in command_names
    assert "replay-decision-freeze-health" in command_names
    assert "replay-decision-freeze-status" in command_names
    assert Path("docs/replay_decision_freeze.md").exists()
    assert Path("docs/release_checkpoint_v1.43.0.md").exists()
    assert Path("SOURCE_UPDATE_NOTES_v1_43_0.md").exists()
    assert not Path("docs/project_sources").exists()


@pytest.mark.parametrize(
    ("allow", "expected_status", "expected_rows"),
    [
        (False, READY_FOR_REPLAY_DECISION_FREEZE, 0),
        (True, REPLAY_DECISION_FROZEN, 1),
    ],
)
def test_index_discovers_ready_and_frozen_artifacts(
    tmp_path: Path,
    allow: bool,
    expected_status: str,
    expected_rows: int,
) -> None:
    run_replay_decision_freeze(replace(_happy_settings(tmp_path), allow_replay_decision_freeze=allow))

    result = build_replay_decision_freeze_index(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0].to_dict()
    assert row["status"] == expected_status
    assert row["source_actual_replay_execution_run_id"] == "ad8dfa413ded"
    assert row["source_active_input_creation_run_id"] == "293deb5f459a"
    assert row["source_real_replay_precheck_run_id"] == "0657ae658ab8"
    assert row["actual_replay_execution_status"] == ACTUAL_REPLAY_EXECUTED
    assert row["actual_replay_execution_health_status"] == "PASS"
    assert row["actual_replay_executed"] is True
    assert row["ready_for_replay_decision_freeze"] is True
    assert row["replay_decision_frozen"] is allow
    assert row["replay_decisions_created"] is allow
    assert row["replay_decisions_exist"] is allow
    assert row["decision_row_count"] == expected_rows
    assert row["decision_label_set"] == ("WATCH" if allow else "")
    assert row["forward_labels_allowed"] is False
    assert row["forward_labels_exist"] is False
    assert row["forward_return_labels_created"] is False
    assert row["training_allowed"] is False
    assert row["weights_trained"] is False
    assert row["training_result_created"] is False
    assert row["stock_profile_allowed"] is False
    assert row["active_stock_profile_exists"] is False
    assert row["stock_profile_created"] is False
    assert row["buy_review_allowed"] is False
    assert row["real_buy_review_eligible"] is False
    assert row["approved_for_paper"] is False
    assert row["trading_allowed"] is False
    assert row["order_placed"] is False
    assert row["broker_api_called"] is False
    assert row["message_sent"] is False
    assert row["llm_api_called"] is False
    assert row["external_api_called"] is False
    assert row["cache_mutated"] is False
    assert row["data_raw_written"] is False
    assert row["data_processed_written"] is False
    assert row["data_cache_written"] is False
    assert row["current_candidates_run"] is False
    assert row["snapshot_built"] is False
    assert row["signal_semantics_changed"] is False
    assert row["report_only"] is True
    assert row["diagnostic_only"] is True
    assert Path(str(row["metadata_path"])).exists()
    assert Path(str(row["replay_decision_rows_path"])).exists()
    assert Path(str(row["replay_decision_evidence_index_path"])).exists()
    assert Path(str(row["safety_flags_path"])).exists()


def test_index_discovers_no_input_artifact(tmp_path: Path) -> None:
    run_replay_decision_freeze(ReplayDecisionFreezeSettings(output_dir=_output_dir(tmp_path)))

    result = build_replay_decision_freeze_index(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0].to_dict()
    assert row["status"] == NO_REPLAY_DECISION_FREEZE_INPUT
    assert row["workflow_stage"] == "REPLAY_DECISION_FREEZE_NO_INPUT"
    assert row["decision_row_count"] == 0
    assert row["replay_decision_frozen"] is False
    assert row["replay_decisions_created"] is False
    assert row["forward_labels_allowed"] is False
    assert row["training_allowed"] is False
    assert row["trading_allowed"] is False


@pytest.mark.parametrize(
    ("settings",),
    [
        (ReplayDecisionFreezeSettings,),
    ],
)
def test_health_passes_valid_no_input_artifact(tmp_path: Path, settings) -> None:
    run_replay_decision_freeze(settings(output_dir=_output_dir(tmp_path)))

    result = check_replay_decision_freeze_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert result.status == "PASS"
    assert result.error_count == 0


@pytest.mark.parametrize("allow", [False, True])
def test_health_passes_valid_ready_and_frozen_artifacts(tmp_path: Path, allow: bool) -> None:
    run_replay_decision_freeze(replace(_happy_settings(tmp_path), allow_replay_decision_freeze=allow))

    result = check_replay_decision_freeze_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert result.status == "PASS"
    assert result.error_count == 0


@pytest.mark.parametrize(
    ("mutator", "issue_code"),
    [
        (lambda artifact: (artifact / "replay_decision_rows.csv").unlink(), "FROZEN_STATUS_WITHOUT_ROWS"),
        (lambda artifact: pd.DataFrame([{"decision_label": "WATCH"}]).to_csv(artifact / "replay_decision_rows.csv", index=False), "ROWS_EXIST_WITHOUT_FROZEN_STATUS"),
        (lambda artifact: _append_decision_column(artifact, "future_close", 10.0), "REPLAY_DECISION_ROWS_FORBIDDEN_COLUMNS"),
        (lambda artifact: _append_decision_column(artifact, "forward_return", 0.1), "REPLAY_DECISION_ROWS_FORBIDDEN_COLUMNS"),
        (lambda artifact: _append_decision_column(artifact, "training_score", 0.8), "REPLAY_DECISION_ROWS_FORBIDDEN_COLUMNS"),
        (lambda artifact: _append_decision_column(artifact, "stock_profile_status", "active"), "REPLAY_DECISION_ROWS_FORBIDDEN_COLUMNS"),
        (lambda artifact: _append_decision_column(artifact, "real_buy_review_eligible", True), "REPLAY_DECISION_ROWS_FORBIDDEN_COLUMNS"),
        (lambda artifact: _append_decision_column(artifact, "approved_for_paper", True), "REPLAY_DECISION_ROWS_FORBIDDEN_COLUMNS"),
        (lambda artifact: _append_decision_column(artifact, "broker_order_id", "B1"), "REPLAY_DECISION_ROWS_FORBIDDEN_COLUMNS"),
        (lambda artifact: _set_decision_label(artifact, "BUY_NOW"), "REPLAY_DECISION_LABEL_OUTSIDE_REVIEW_ONLY_SET"),
        (lambda artifact: _drop_evidence_column(artifact, "available_time"), "EVIDENCE_INDEX_REQUIRED_COLUMNS_MISSING"),
        (lambda artifact: _drop_evidence_column(artifact, "source_hash"), "EVIDENCE_INDEX_REQUIRED_COLUMNS_MISSING"),
        (lambda artifact: _drop_evidence_column(artifact, "revision_id"), "EVIDENCE_INDEX_REQUIRED_COLUMNS_MISSING"),
        (lambda artifact: _drop_evidence_column(artifact, "taxonomy_layer"), "EVIDENCE_INDEX_REQUIRED_COLUMNS_MISSING"),
        (lambda artifact: _drop_evidence_column(artifact, "pit_valid"), "EVIDENCE_INDEX_REQUIRED_COLUMNS_MISSING"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"forward_labels_allowed": True}), "FORWARD_LABELS_ALLOWED_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"forward_labels_exist": True}), "FORWARD_LABELS_EXIST_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"forward_return_labels_created": True}), "FORWARD_RETURN_LABELS_CREATED_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"training_allowed": True}), "TRAINING_ALLOWED_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"weights_trained": True}), "WEIGHTS_TRAINED_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"training_result_created": True}), "TRAINING_RESULT_CREATED_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"stock_profile_allowed": True}), "STOCK_PROFILE_ALLOWED_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"active_stock_profile_exists": True}), "ACTIVE_STOCK_PROFILE_EXISTS_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"stock_profile_created": True}), "STOCK_PROFILE_CREATED_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"buy_review_allowed": True}), "BUY_REVIEW_ALLOWED_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"real_buy_review_eligible": True}), "REAL_BUY_REVIEW_ELIGIBLE_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"approved_for_paper": True}), "APPROVED_FOR_PAPER_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"trading_allowed": True}), "TRADING_ALLOWED_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"order_placed": True}), "ORDER_PLACED_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"broker_api_called": True}), "BROKER_API_CALLED_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"message_sent": True}), "MESSAGE_SENT_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"llm_api_called": True}), "LLM_API_CALLED_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"external_api_called": True}), "EXTERNAL_API_CALLED_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"cache_mutated": True}), "CACHE_MUTATED_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"data_raw_written": True}), "DATA_RAW_WRITTEN_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"data_processed_written": True}), "DATA_PROCESSED_WRITTEN_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"data_cache_written": True}), "DATA_CACHE_WRITTEN_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"current_candidates_run": True}), "CURRENT_CANDIDATES_RUN_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"snapshot_built": True}), "SNAPSHOT_BUILT_UNEXPECTED"),
        (lambda artifact: _patch_json(artifact / "replay_decision_safety_flags.json", {"signal_semantics_changed": True}), "SIGNAL_SEMANTICS_CHANGED_UNEXPECTED"),
    ],
)
def test_health_fails_for_unsafe_or_malformed_artifacts(tmp_path: Path, mutator, issue_code: str) -> None:
    result = run_replay_decision_freeze(replace(_happy_settings(tmp_path), allow_replay_decision_freeze=True))
    if issue_code == "ROWS_EXIST_WITHOUT_FROZEN_STATUS":
        result = run_replay_decision_freeze(_happy_settings(tmp_path))
    mutator(result.artifact_path)

    health = check_replay_decision_freeze_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert issue_code in set(health.health_frame["issue_code"])


def test_health_fails_for_artifact_path_outside_manual_diagnostics(tmp_path: Path) -> None:
    result = run_replay_decision_freeze(
        replace(_happy_settings(tmp_path), allow_replay_decision_freeze=True, output_dir=_output_dir(tmp_path))
    )
    _patch_json(result.artifact_paths["metadata"], {"artifact_path": str(tmp_path / "unsafe")})

    health = check_replay_decision_freeze_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert "ARTIFACT_PATH_OUTSIDE_MANUAL_DIAGNOSTICS" in set(health.health_frame["issue_code"])


@pytest.mark.parametrize(
    ("status_builder", "expected_stage"),
    [
        (lambda tmp_path: run_replay_decision_freeze(ReplayDecisionFreezeSettings(output_dir=_output_dir(tmp_path))), REPLAY_DECISION_FREEZE_NO_INPUT_ARTIFACT),
        (lambda tmp_path: run_replay_decision_freeze(_happy_settings(tmp_path)), READY_FOR_REPLAY_DECISION_FREEZE),
        (lambda tmp_path: run_replay_decision_freeze(replace(_happy_settings(tmp_path), allow_replay_decision_freeze=True)), REPLAY_DECISION_FROZEN),
    ],
)
def test_status_reports_no_input_ready_and_frozen_report_only_states(tmp_path: Path, status_builder, expected_stage: str) -> None:
    built = status_builder(tmp_path)

    result = run_replay_decision_freeze_status(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "status")

    assert result.latest_replay_decision_freeze_run_id == built.replay_decision_freeze_run_id
    assert result.health_status == "PASS"
    assert result.workflow_stage == expected_stage
    assert result.forward_labels_allowed is False
    assert result.forward_labels_exist is False
    assert result.forward_return_labels_created is False
    assert result.training_allowed is False
    assert result.weights_trained is False
    assert result.training_result_created is False
    assert result.stock_profile_allowed is False
    assert result.active_stock_profile_exists is False
    assert result.stock_profile_created is False
    assert result.buy_review_allowed is False
    assert result.real_buy_review_eligible is False
    assert result.approved_for_paper is False
    assert result.trading_allowed is False
    text = result.artifact_paths["status_report"].read_text(encoding="utf-8")
    for phrase in [
        "report-only",
        "frozen decision-time review rows only",
        "does not compute forward labels",
        "does not train weights",
        "does not create stock_profile",
        "does not create buy-review eligibility",
        "does not apply paper approval",
        "does not authorize trading",
    ]:
        assert phrase in text


def test_cli_artifact_view_commands_run(tmp_path: Path) -> None:
    run_replay_decision_freeze(replace(_happy_settings(tmp_path), allow_replay_decision_freeze=True))
    root = _output_dir(tmp_path)

    for command in ["replay-decision-freeze-index", "replay-decision-freeze-health", "replay-decision-freeze-status"]:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "quant_replay_system.cli",
                command,
                "--root",
                str(root),
                "--output-dir",
                str(root / command),
            ],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
        )
        assert completed.returncode == 0
        assert "replay decision freeze" in completed.stdout.lower()


def test_replay_decision_freeze_docs_checkpoint_and_source_note_exist_with_safety_wording() -> None:
    doc = Path("docs/replay_decision_freeze.md")
    checkpoint = Path("docs/release_checkpoint_v1.43.0.md")
    source_note = Path("SOURCE_UPDATE_NOTES_v1_43_0.md")

    for path in [doc, checkpoint, source_note]:
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        for phrase in [
            "report-only",
            "frozen decision-time review rows",
            "does not compute forward labels",
            "does not train weights",
            "does not create training_result",
            "does not create active stock_profile",
            "does not create real buy-review eligibility",
            "does not apply paper approval",
            "does not validate strategy performance",
            "does not authorize trading",
        ]:
            assert phrase in text

    source_text = source_note.read_text(encoding="utf-8")
    assert "docs/project_sources/ is intentionally absent from Git" in source_text
    assert "Forward Return Label Planning Report-Only v0.1" in source_text
    assert "not immediate training" in source_text
    assert not Path("docs/project_sources").exists()


def _required_artifact_keys() -> list[str]:
    return [
        "metadata",
        "report",
        "replay_decision_rows",
        "replay_decision_evidence_index",
        "safety_flags",
        "precondition_results",
        "authority_results",
        "lineage_results",
        "attestation_results",
        "pit_source_evidence_results",
        "taxonomy_evidence_results",
        "leakage_side_effect_guard_results",
        "overclaim_guard_results",
        "recommended_next_task",
    ]


def _assert_downstream_flags_false(result) -> None:
    assert result.forward_labels_allowed is False
    assert result.forward_labels_exist is False
    assert result.forward_return_labels_created is False
    assert result.training_allowed is False
    assert result.weights_trained is False
    assert result.training_result_created is False
    assert result.stock_profile_allowed is False
    assert result.active_stock_profile_exists is False
    assert result.stock_profile_created is False
    assert result.buy_review_allowed is False
    assert result.real_buy_review_eligible is False
    assert result.trading_allowed is False
    assert result.order_placed is False
    assert result.broker_api_called is False
    assert result.message_sent is False
    assert result.llm_api_called is False
    assert result.external_api_called is False
    assert result.cache_mutated is False
    assert result.data_raw_written is False
    assert result.data_processed_written is False
    assert result.data_cache_written is False
    assert result.current_candidates_run is False
    assert result.snapshot_built is False


def _downstream_false_fields() -> list[str]:
    return [
        "replay_decision_freeze_executed",
        "replay_decision_frozen",
        "replay_decision_artifacts_created",
        "replay_decisions_created",
        "replay_decisions_exist",
        *_safety_false_fields(),
    ]


def _safety_false_fields() -> list[str]:
    return [
        "forward_labels_allowed",
        "forward_labels_exist",
        "forward_return_labels_created",
        "training_allowed",
        "weights_trained",
        "training_result_created",
        "stock_profile_allowed",
        "active_stock_profile_exists",
        "stock_profile_created",
        "buy_review_allowed",
        "real_buy_review_eligible",
        "approved_for_paper",
        "trading_allowed",
        "order_placed",
        "broker_api_called",
        "message_sent",
        "llm_api_called",
        "external_api_called",
        "cache_mutated",
        "data_raw_written",
        "data_processed_written",
        "data_cache_written",
        "current_candidates_run",
        "snapshot_built",
        "signal_semantics_changed",
    ]


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "replay_decision_freeze_v0_1"


def _fixture_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "replay_decision_freeze_fixture_v0_1"


def _happy_settings(tmp_path: Path) -> ReplayDecisionFreezeSettings:
    root = _fixture_root(tmp_path)
    root.mkdir(parents=True, exist_ok=True)
    actual = _write_json(root / "actual_replay_execution.json", _actual_replay_payload())
    actual_health = _write_json(root / "actual_replay_health.json", {"health_status": "PASS"})
    actual_status = _write_json(root / "actual_replay_status.json", {"status": ACTUAL_REPLAY_EXECUTED})
    plan = root / "replay_decision_freeze_plan.md"
    plan.write_text("# Replay decision freeze core report-only plan\n", encoding="utf-8")
    approval = _write_json(root / "approval.json", {"approval_text": EXACT_APPROVAL})
    request = _write_json(root / "request.json", {"replay_decision_freeze_core_requested": True, "report_only": True})
    authority = _write_json(root / "authority.json", {"authority_result": "ACCEPTED_FOR_REPLAY_DECISION_FREEZE_CORE_ONLY"})
    attestation = _write_json(root / "attestation.json", _attestation_payload())
    pit_source = _write_json(root / "pit_source_evidence.json", _pit_source_payload())
    taxonomy = _write_json(root / "taxonomy.json", _taxonomy_payload())
    factor_event_company = _write_json(root / "factor_event_company.json", _factor_event_company_payload())
    source_hash = _write_json(root / "source_hash.json", _source_hash_payload())
    leakage = _write_json(root / "leakage.json", _leakage_payload())
    overclaim = _write_json(root / "overclaim.json", _overclaim_payload())
    candidate = _write_json(root / "candidate.json", _candidate_payload())
    return ReplayDecisionFreezeSettings(
        actual_replay_execution_artifact_path=actual,
        actual_replay_execution_health_artifact_path=actual_health,
        actual_replay_execution_status_artifact_path=actual_status,
        replay_decision_freeze_plan_path=plan,
        approval_manifest_path=approval,
        replay_decision_freeze_request_manifest_path=request,
        replay_decision_freeze_authority_manifest_path=authority,
        second_reviewer_attestation_manifest_path=attestation,
        pit_source_evidence_bundle_path=pit_source,
        taxonomy_evidence_bundle_path=taxonomy,
        factor_event_company_evidence_bundle_path=factor_event_company,
        source_hash_revision_available_time_evidence_path=source_hash,
        leakage_side_effect_evidence_bundle_path=leakage,
        overclaim_evidence_bundle_path=overclaim,
        replay_decision_candidate_manifest_path=candidate,
        output_dir=_output_dir(tmp_path),
    )


def _actual_replay_payload() -> dict[str, object]:
    payload = {
        "actual_replay_execution_run_id": "ad8dfa413ded",
        "execution_status": ACTUAL_REPLAY_EXECUTED,
        "workflow_stage": ACTUAL_REPLAY_EXECUTED,
        "source_active_input_creation_run_id": "293deb5f459a",
        "source_real_replay_precheck_run_id": "0657ae658ab8",
        "actual_replay_executed": True,
        "replay_execution_started": True,
        "replay_execution_completed": True,
        "replay_as_of_date": "2024-04-02",
        "replay_calendar": "XSHG_XSHE_EOD",
        "symbol_universe_ref": "symbol_universe.json",
        "pit_universe_ref": "pit_universe.json",
        "source_registry_ref": "source_registry.json",
        "raw_document_store_ref": "raw_documents.json",
        "factor_definition_ref": "factor_definitions.json",
        "factor_observation_ref": "factor_observations.json",
        "event_structured_ref": "events.json",
        "company_exposure_ref": "exposures.json",
        "evidence_bundle_ref": "evidence_bundle.json",
        "source_hash_coverage": "COMPLETE",
        "revision_id_coverage": "COMPLETE",
        "available_time_policy": "ALL_AVAILABLE_TIME_LTE_REPLAY_DECISION_TIME",
        "taxonomy_coverage": "8_LAYER_TAXONOMY_COVERED",
        "future_labels_excluded": True,
        "deterministic_only": True,
    }
    payload.update({field: False for field in _safety_false_fields()})
    payload.update({"forward_returns_exist": False})
    return payload


def _attestation_payload() -> dict[str, object]:
    return {
        "second_reviewer_attested": True,
        "replay_decision_freeze_core_attested": True,
        "report_only_attested": True,
        "no_forward_label_attested": True,
        "no_training_attested": True,
        "no_stock_profile_attested": True,
        "no_buy_review_attested": True,
        "no_trading_authority_attested": True,
        "no_performance_claim_attested": True,
    }


def _pit_source_payload() -> dict[str, object]:
    return {
        "accepted_pit_universe_evidence_attached": True,
        "source_registry_evidence_attached": True,
        "raw_document_store_attached": True,
        "evidence_bundle_attached": True,
    }


def _taxonomy_payload() -> dict[str, object]:
    return {
        "uses_8_layer_taxonomy": True,
        "not_fixed_12_only": True,
        "factor_definition_attached": True,
        "factor_observation_attached": True,
        "event_structured_attached": True,
        "company_exposure_attached": True,
        "factor_layer_metadata_attached": True,
    }


def _factor_event_company_payload() -> dict[str, object]:
    return {
        "factor_definition_attached": True,
        "factor_observation_attached": True,
        "event_structured_attached": True,
        "company_exposure_attached": True,
        "all_available_time_lte_replay_decision_time": True,
    }


def _source_hash_payload() -> dict[str, object]:
    return {
        "source_hash_coverage_attached": True,
        "revision_id_coverage_attached": True,
        "available_time_policy_attached": True,
        "available_time_policy": "ALL_AVAILABLE_TIME_LTE_REPLAY_DECISION_TIME",
    }


def _leakage_payload() -> dict[str, object]:
    payload = {
        "no_future_labels": True,
        "no_forward_returns": True,
        "no_training_outputs": True,
        "no_model_weights": True,
        "no_stock_profile_artifacts": True,
        "no_buy_review_eligibility": True,
        "no_approved_for_paper": True,
        "no_broker_api_called": True,
        "no_order_placed": True,
        "no_message_sent": True,
        "no_llm_api_called": True,
        "no_external_api_called": True,
        "no_cache_mutated": True,
        "no_data_raw_written": True,
        "no_data_processed_written": True,
        "no_data_cache_written": True,
        "no_current_candidates_run": True,
        "no_snapshot_built": True,
    }
    payload.update({field: False for field in _safety_false_fields()})
    payload.update({"forward_returns_exist": False})
    return payload


def _overclaim_payload() -> dict[str, object]:
    return {
        "replay_decision_not_forward_label_permission": True,
        "replay_decision_not_training_permission": True,
        "replay_decision_not_stock_profile_permission": True,
        "replay_decision_not_buy_review_eligibility": True,
        "replay_decision_not_paper_approval": True,
        "replay_decision_not_performance_validation": True,
        "replay_decision_not_trading_authorization": True,
        "buy_review_allowed": False,
        "trading_allowed": False,
        "approved_for_paper": False,
    }


def _candidate_payload() -> dict[str, object]:
    payload = {
        "deterministic_only": True,
        "future_labels_excluded": True,
        "decision_label": "WATCH",
        "decision_reason_code": "DETERMINISTIC_REPLAY_CONTEXT",
        "symbol": "000001",
        "instrument_type": "STOCK",
        "evidence_bundle_id": "evidence_000001_20240402",
        "factor_layer_support": "VALUATION;MOMENTUM;EVENT",
        "factor_ids": "factor_momentum_20d;factor_quality_signal",
        "event_ids": "event_none",
        "source_ids": "source_szse_1815;source_cninfo",
        "available_time_max": "2024-04-02T15:30:00+08:00",
        "risk_vetoes": "",
        "confidence": 0.5,
    }
    payload.update({field: False for field in _safety_false_fields()})
    payload.update({"forward_returns_exist": False})
    return payload


def _run_cli_with_settings(settings: ReplayDecisionFreezeSettings, *, allow: bool) -> subprocess.CompletedProcess[str]:
    args = [
        sys.executable,
        "-m",
        "quant_replay_system.cli",
        "replay-decision-freeze",
        "--actual-replay-execution-artifact-path",
        str(settings.actual_replay_execution_artifact_path),
        "--actual-replay-execution-health-artifact-path",
        str(settings.actual_replay_execution_health_artifact_path),
        "--actual-replay-execution-status-artifact-path",
        str(settings.actual_replay_execution_status_artifact_path),
        "--replay-decision-freeze-plan-path",
        str(settings.replay_decision_freeze_plan_path),
        "--approval-manifest-path",
        str(settings.approval_manifest_path),
        "--replay-decision-freeze-request-manifest-path",
        str(settings.replay_decision_freeze_request_manifest_path),
        "--replay-decision-freeze-authority-manifest-path",
        str(settings.replay_decision_freeze_authority_manifest_path),
        "--second-reviewer-attestation-manifest-path",
        str(settings.second_reviewer_attestation_manifest_path),
        "--pit-source-evidence-bundle-path",
        str(settings.pit_source_evidence_bundle_path),
        "--taxonomy-evidence-bundle-path",
        str(settings.taxonomy_evidence_bundle_path),
        "--factor-event-company-evidence-bundle-path",
        str(settings.factor_event_company_evidence_bundle_path),
        "--source-hash-revision-available-time-evidence-path",
        str(settings.source_hash_revision_available_time_evidence_path),
        "--leakage-side-effect-evidence-bundle-path",
        str(settings.leakage_side_effect_evidence_bundle_path),
        "--overclaim-evidence-bundle-path",
        str(settings.overclaim_evidence_bundle_path),
        "--replay-decision-candidate-manifest-path",
        str(settings.replay_decision_candidate_manifest_path),
        "--output-dir",
        str(settings.output_dir),
    ]
    if allow:
        args.append("--allow-replay-decision-freeze")
    return subprocess.run(args, check=True, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": "src"})


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _patch_json(path: Path | None, patch: dict[str, object]) -> None:
    assert path is not None
    payload = _read_json(path)
    payload.update(patch)
    _write_json(path, payload)


def _append_decision_column(artifact_path: Path, column: str, value: object) -> None:
    frame = pd.read_csv(artifact_path / "replay_decision_rows.csv")
    frame[column] = value
    frame.to_csv(artifact_path / "replay_decision_rows.csv", index=False)


def _set_decision_label(artifact_path: Path, label: str) -> None:
    frame = pd.read_csv(artifact_path / "replay_decision_rows.csv")
    frame["decision_label"] = label
    frame.to_csv(artifact_path / "replay_decision_rows.csv", index=False)


def _drop_evidence_column(artifact_path: Path, column: str) -> None:
    frame = pd.read_csv(artifact_path / "replay_decision_evidence_index.csv")
    frame = frame.drop(columns=[column])
    frame.to_csv(artifact_path / "replay_decision_evidence_index.csv", index=False)
