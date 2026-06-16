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
from quant_replay_system.actual_replay_execute import (
    ACTUAL_REPLAY_EXECUTED,
    ACTUAL_REPLAY_EXECUTION_ATTESTATION_BLOCKED,
    ACTUAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED,
    ACTUAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED,
    ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED,
    ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED,
    ACTUAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED,
    ACTUAL_REPLAY_EXECUTION_PIT_BLOCKED,
    ACTUAL_REPLAY_EXECUTION_REVIEW_BLOCKED,
    ACTUAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED,
    ACTUAL_REPLAY_EXECUTION_SOURCE_BLOCKED,
    ACTUAL_REPLAY_EXECUTION_TAXONOMY_BLOCKED,
    NO_ACTUAL_REPLAY_EXECUTION_INPUT,
    READY_FOR_ACTUAL_REPLAY_EXECUTION,
    ActualReplayExecuteSettings,
    run_actual_replay_execute,
)
from quant_replay_system.actual_replay_execute_health import check_actual_replay_execute_health
from quant_replay_system.actual_replay_execute_index import build_actual_replay_execute_index
from quant_replay_system.actual_replay_execute_status import (
    ACTUAL_REPLAY_EXECUTION_HEALTH_FAILED,
    ACTUAL_REPLAY_EXECUTION_NO_INPUT_ARTIFACT,
    run_actual_replay_execute_status,
)


EXACT_APPROVAL = (
    "I explicitly authorize implementation of actual replay execution core only, "
    "report-only, no replay_decision creation, no forward labels, no training, "
    "no stock_profile, no buy-review, no trading."
)


def test_no_input_writes_required_artifacts_with_safe_defaults(tmp_path: Path) -> None:
    result = run_actual_replay_execute(ActualReplayExecuteSettings(output_dir=_output_dir(tmp_path)))

    assert result.status == NO_ACTUAL_REPLAY_EXECUTION_INPUT
    assert result.workflow_stage == "ACTUAL_REPLAY_EXECUTION_NO_INPUT"
    assert result.ready_for_actual_replay_execution is False
    _assert_not_executed_or_downstream(result)
    assert result.report_only is True
    assert result.diagnostic_only is True

    for key in _required_artifact_keys():
        assert result.artifact_paths[key].exists()

    metadata = _read_json(result.artifact_paths["metadata"])
    safety = _read_json(result.artifact_paths["safety_flags"])
    assert metadata["execution_status"] == NO_ACTUAL_REPLAY_EXECUTION_INPUT
    assert metadata["ready_for_actual_replay_execution"] is False
    assert metadata["actual_replay_executed"] is False
    for field in _downstream_false_fields():
        assert metadata[field] is False
        assert safety[field] is False


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("active_replay_input_artifact_path", ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("active_input_health_artifact_path", ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("active_input_status_artifact_path", ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("real_replay_precheck_artifact_path", ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("real_replay_precheck_health_artifact_path", ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("real_replay_precheck_status_artifact_path", ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("actual_replay_execution_plan_path", ACTUAL_REPLAY_EXECUTION_REVIEW_BLOCKED),
        ("approval_manifest_path", ACTUAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED),
        ("actual_replay_execution_request_manifest_path", ACTUAL_REPLAY_EXECUTION_REVIEW_BLOCKED),
        ("actual_replay_execution_authority_manifest_path", ACTUAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED),
        ("second_reviewer_attestation_manifest_path", ACTUAL_REPLAY_EXECUTION_ATTESTATION_BLOCKED),
        ("pit_source_evidence_bundle_path", ACTUAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED),
        ("taxonomy_evidence_bundle_path", ACTUAL_REPLAY_EXECUTION_TAXONOMY_BLOCKED),
        ("factor_event_company_evidence_bundle_path", ACTUAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED),
        ("source_hash_revision_available_time_evidence_path", ACTUAL_REPLAY_EXECUTION_SOURCE_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", ACTUAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED),
        ("actual_replay_execution_candidate_manifest_path", ACTUAL_REPLAY_EXECUTION_REVIEW_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(
    tmp_path: Path,
    setting_name: str,
    expected_status: str,
) -> None:
    result = run_actual_replay_execute(replace(_happy_settings(tmp_path), **{setting_name: None}))

    assert result.status == expected_status
    assert result.ready_for_actual_replay_execution is False
    _assert_not_executed_or_downstream(result)


@pytest.mark.parametrize(
    ("path_name", "override", "expected_status"),
    [
        ("approval_manifest_path", {"approval_text": ""}, ACTUAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED),
        ("approval_manifest_path", {"approval_text": "continue"}, ACTUAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED),
        ("approval_manifest_path", {"approval_text": "I authorize replay_decision creation."}, ACTUAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED),
        ("approval_manifest_path", {"approval_text": "I authorize labels and training."}, ACTUAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED),
        ("approval_manifest_path", {"approval_text": "I authorize trading."}, ACTUAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED),
        ("active_replay_input_artifact_path", {"input_status": "READY_FOR_ACTIVE_REPLAY_INPUT_CREATION"}, ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("active_replay_input_artifact_path", {"active_replay_input_created": False}, ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("active_replay_input_artifact_path", {"active_replay_input": False}, ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("active_input_health_artifact_path", {"health_status": "FAIL"}, ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("real_replay_precheck_artifact_path", {"execution_status": "NO_REAL_REPLAY_EXECUTION_INPUT"}, ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("real_replay_precheck_artifact_path", {"ready_for_real_replay_execution_review": False}, ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("real_replay_precheck_health_artifact_path", {"health_status": "FAIL"}, ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("actual_replay_execution_request_manifest_path", {"actual_replay_execution_core_requested": False}, ACTUAL_REPLAY_EXECUTION_REVIEW_BLOCKED),
        ("actual_replay_execution_authority_manifest_path", {"authority_result": "REJECTED"}, ACTUAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED),
        ("second_reviewer_attestation_manifest_path", {"second_reviewer_attested": False}, ACTUAL_REPLAY_EXECUTION_ATTESTATION_BLOCKED),
        ("pit_source_evidence_bundle_path", {"accepted_pit_universe_evidence_attached": False}, ACTUAL_REPLAY_EXECUTION_PIT_BLOCKED),
        ("pit_source_evidence_bundle_path", {"source_registry_evidence_attached": False}, ACTUAL_REPLAY_EXECUTION_SOURCE_BLOCKED),
        ("taxonomy_evidence_bundle_path", {"not_fixed_12_only": False}, ACTUAL_REPLAY_EXECUTION_TAXONOMY_BLOCKED),
        ("factor_event_company_evidence_bundle_path", {"factor_observation_attached": False}, ACTUAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED),
        ("source_hash_revision_available_time_evidence_path", {"revision_id_coverage_attached": False}, ACTUAL_REPLAY_EXECUTION_SOURCE_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", {"no_future_labels": False}, ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", {"no_data_raw_written": False}, ACTUAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("overclaim_evidence_bundle_path", {"actual_replay_execution_not_replay_decision": False}, ACTUAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED),
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

    result = run_actual_replay_execute(settings)

    assert result.status == expected_status
    assert result.ready_for_actual_replay_execution is False
    _assert_not_executed_or_downstream(result)


@pytest.mark.parametrize(
    ("unsafe_field", "expected_status"),
    [
        ("future_labels_exist", ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("forward_labels_allowed", ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("forward_labels_exist", ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("forward_returns_exist", ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("replay_decisions_created", ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("replay_decisions_exist", ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("training_allowed", ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("weights_trained", ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("stock_profile_allowed", ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("active_stock_profile_exists", ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("buy_review_allowed", ACTUAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED),
        ("real_buy_review_eligible", ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("trading_allowed", ACTUAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED),
        ("order_placed", ACTUAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("broker_api_called", ACTUAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("message_sent", ACTUAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("llm_api_called", ACTUAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("external_api_called", ACTUAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("cache_mutated", ACTUAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("data_raw_written", ACTUAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("data_processed_written", ACTUAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("data_cache_written", ACTUAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
    ],
)
def test_unsafe_input_flags_block(tmp_path: Path, unsafe_field: str, expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.active_replay_input_artifact_path, {unsafe_field: True})

    result = run_actual_replay_execute(settings)

    assert result.status == expected_status
    assert result.ready_for_actual_replay_execution is False
    _assert_not_executed_or_downstream(result)


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_actual_replay_execute(ActualReplayExecuteSettings(output_dir=tmp_path / "unsafe"))


def test_happy_path_without_allow_reaches_ready_but_does_not_execute(tmp_path: Path) -> None:
    result = run_actual_replay_execute(_happy_settings(tmp_path))

    assert result.status == READY_FOR_ACTUAL_REPLAY_EXECUTION
    assert result.workflow_stage == READY_FOR_ACTUAL_REPLAY_EXECUTION
    assert result.ready_for_actual_replay_execution is True
    _assert_not_executed_or_downstream(result)


def test_happy_path_with_explicit_allow_executes_report_only_artifacts(tmp_path: Path) -> None:
    result = run_actual_replay_execute(replace(_happy_settings(tmp_path), allow_actual_replay_execution=True))

    assert result.status == ACTUAL_REPLAY_EXECUTED
    assert result.workflow_stage == ACTUAL_REPLAY_EXECUTED
    assert result.ready_for_actual_replay_execution is True
    assert result.actual_replay_executed is True
    assert result.replay_execution_started is True
    assert result.replay_execution_completed is True
    _assert_downstream_blocked_after_execution(result)

    metadata = _read_json(result.artifact_paths["metadata"])
    input_snapshot = _read_json(result.artifact_paths["input_snapshot"])
    safety = _read_json(result.artifact_paths["safety_flags"])
    observation = pd.read_csv(result.artifact_paths["observation_snapshot"])
    evidence = pd.read_csv(result.artifact_paths["evidence_bundle_index"])
    report = result.artifact_paths["report"].read_text(encoding="utf-8")

    assert metadata["execution_status"] == ACTUAL_REPLAY_EXECUTED
    assert input_snapshot["explicit_approval_validation_result"] == "PASS"
    assert input_snapshot["approval_text"] == EXACT_APPROVAL
    assert len(observation) >= 1
    assert not any("forward" in column.lower() or "label" in column.lower() for column in observation.columns)
    assert not any("decision" in column.lower() for column in observation.columns)
    for column in ["available_time", "source_hash", "revision_id", "taxonomy_coverage", "pit_status"]:
        assert column in evidence.columns
    for field in _downstream_false_fields():
        if field not in {"replay_execution_started", "replay_execution_completed", "actual_replay_executed"}:
            assert safety[field] is False
    for phrase in [
        "not replay_decision",
        "not forward labels",
        "not training",
        "not stock_profile",
        "not buy-review",
        "not trading",
    ]:
        assert phrase in report


def test_cli_actual_replay_execute_runs_no_input(tmp_path: Path, capsys) -> None:
    code = cli.main(["actual-replay-execute", "--output-dir", str(_output_dir(tmp_path))])
    output = capsys.readouterr()

    assert code == 0
    assert "status: NO_ACTUAL_REPLAY_EXECUTION_INPUT" in output.out
    assert "workflow_stage: ACTUAL_REPLAY_EXECUTION_NO_INPUT" in output.out
    assert "ready_for_actual_replay_execution: False" in output.out
    assert "actual_replay_executed: False" in output.out
    assert "replay_decisions_created: False" in output.out
    assert "trading_allowed: False" in output.out


def test_cli_happy_path_without_allow_reaches_ready_but_does_not_execute(tmp_path: Path) -> None:
    completed = _run_cli_with_settings(_happy_settings(tmp_path), allow=False)

    assert f"status: {READY_FOR_ACTUAL_REPLAY_EXECUTION}" in completed.stdout
    assert "ready_for_actual_replay_execution: True" in completed.stdout
    assert "actual_replay_executed: False" in completed.stdout
    assert "replay_execution_started: False" in completed.stdout


def test_cli_happy_path_with_allow_executes_report_only(tmp_path: Path) -> None:
    completed = _run_cli_with_settings(_happy_settings(tmp_path), allow=True)

    assert f"status: {ACTUAL_REPLAY_EXECUTED}" in completed.stdout
    assert "ready_for_actual_replay_execution: True" in completed.stdout
    assert "actual_replay_executed: True" in completed.stdout
    assert "replay_execution_started: True" in completed.stdout
    assert "replay_execution_completed: True" in completed.stdout
    assert "replay_decisions_created: False" in completed.stdout
    assert "forward_labels_allowed: False" in completed.stdout
    assert "weights_trained: False" in completed.stdout
    assert "trading_allowed: False" in completed.stdout


def test_actual_replay_execute_index_discovers_all_report_only_artifact_states(tmp_path: Path) -> None:
    no_input = run_actual_replay_execute(ActualReplayExecuteSettings(output_dir=_output_dir(tmp_path)))
    ready = run_actual_replay_execute(_happy_settings(tmp_path))
    executed = run_actual_replay_execute(
        replace(_happy_settings(tmp_path), allow_actual_replay_execution=True)
    )

    index = build_actual_replay_execute_index(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "index")

    assert index.artifact_count == 3
    rows = {row["status"]: row for row in index.index_frame.to_dict("records")}
    assert rows[NO_ACTUAL_REPLAY_EXECUTION_INPUT]["actual_replay_execution_run_id"] == no_input.actual_replay_execution_run_id
    assert rows[READY_FOR_ACTUAL_REPLAY_EXECUTION]["actual_replay_execution_run_id"] == ready.actual_replay_execution_run_id
    executed_row = rows[ACTUAL_REPLAY_EXECUTED]
    assert executed_row["actual_replay_execution_run_id"] == executed.actual_replay_execution_run_id
    assert executed_row["source_active_input_creation_run_id"] == "293deb5f459a"
    assert executed_row["source_real_replay_precheck_run_id"] == "0657ae658ab8"
    assert executed_row["actual_replay_executed"] is True
    assert executed_row["replay_execution_started"] is True
    assert executed_row["replay_execution_completed"] is True
    assert executed_row["replay_decisions_created"] is False
    assert executed_row["replay_decisions_exist"] is False
    assert executed_row["replay_decision_artifact_path"] == ""
    assert executed_row["forward_labels_allowed"] is False
    assert executed_row["weights_trained"] is False
    assert executed_row["trading_allowed"] is False
    assert executed_row["report_only"] is True
    assert executed_row["diagnostic_only"] is True


@pytest.mark.parametrize(
    "settings",
    [
        lambda tmp_path: ActualReplayExecuteSettings(output_dir=_output_dir(tmp_path)),
        lambda tmp_path: _happy_settings(tmp_path),
        lambda tmp_path: replace(_happy_settings(tmp_path), allow_actual_replay_execution=True),
    ],
)
def test_actual_replay_execute_health_passes_valid_report_only_states(tmp_path: Path, settings) -> None:
    run_actual_replay_execute(settings(tmp_path))

    health = check_actual_replay_execute_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "PASS"
    assert health.checked_artifact_count == 1
    assert health.error_count == 0


@pytest.mark.parametrize(
    "unsafe_field",
    [
        "replay_decisions_created",
        "replay_decisions_exist",
        "forward_labels_allowed",
        "forward_labels_exist",
        "training_allowed",
        "weights_trained",
        "stock_profile_allowed",
        "active_stock_profile_exists",
        "buy_review_allowed",
        "real_buy_review_eligible",
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
    ],
)
def test_actual_replay_execute_health_fails_unsafe_flags(tmp_path: Path, unsafe_field: str) -> None:
    result = run_actual_replay_execute(replace(_happy_settings(tmp_path), allow_actual_replay_execution=True))
    _patch_json(result.artifact_paths["metadata"], {unsafe_field: True})
    _patch_json(result.artifact_paths["safety_flags"], {unsafe_field: True})

    health = check_actual_replay_execute_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert health.error_count >= 1
    assert any(unsafe_field.upper() in str(code) for code in health.health_frame["issue_code"].tolist())


def test_actual_replay_execute_health_fails_replay_decision_artifact_path(tmp_path: Path) -> None:
    result = run_actual_replay_execute(replace(_happy_settings(tmp_path), allow_actual_replay_execution=True))
    _patch_json(result.artifact_paths["metadata"], {"replay_decision_artifact_path": "replay_decisions.csv"})

    health = check_actual_replay_execute_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert "REPLAY_DECISION_ARTIFACT_PATH_UNEXPECTED" in set(health.health_frame["issue_code"])


@pytest.mark.parametrize("column_name", ["forward_5d_return", "training_label", "replay_decision"])
def test_actual_replay_execute_health_fails_observation_label_or_decision_columns(
    tmp_path: Path, column_name: str
) -> None:
    result = run_actual_replay_execute(replace(_happy_settings(tmp_path), allow_actual_replay_execution=True))
    frame = pd.read_csv(result.artifact_paths["observation_snapshot"])
    frame[column_name] = 0
    frame.to_csv(result.artifact_paths["observation_snapshot"], index=False)

    health = check_actual_replay_execute_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert any("OBSERVATION" in code for code in health.health_frame["issue_code"].tolist())


@pytest.mark.parametrize("column_name", ["available_time", "source_hash", "revision_id", "taxonomy_coverage", "pit_status"])
def test_actual_replay_execute_health_fails_missing_evidence_required_columns(
    tmp_path: Path, column_name: str
) -> None:
    result = run_actual_replay_execute(replace(_happy_settings(tmp_path), allow_actual_replay_execution=True))
    frame = pd.read_csv(result.artifact_paths["evidence_bundle_index"]).drop(columns=[column_name])
    frame.to_csv(result.artifact_paths["evidence_bundle_index"], index=False)

    health = check_actual_replay_execute_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert "EVIDENCE_INDEX_REQUIRED_COLUMNS_MISSING" in set(health.health_frame["issue_code"])


def test_actual_replay_execute_status_reports_no_input_ready_and_executed_states(tmp_path: Path) -> None:
    no_input_root = _output_dir(tmp_path) / "no_input"
    ready_root = _output_dir(tmp_path) / "ready"
    executed_root = _output_dir(tmp_path) / "executed"
    run_actual_replay_execute(ActualReplayExecuteSettings(output_dir=no_input_root))
    run_actual_replay_execute(replace(_happy_settings(tmp_path), output_dir=ready_root))
    run_actual_replay_execute(
        replace(_happy_settings(tmp_path), output_dir=executed_root, allow_actual_replay_execution=True)
    )

    no_input_status = run_actual_replay_execute_status(root=no_input_root, output_dir=no_input_root / "status")
    ready_status = run_actual_replay_execute_status(root=ready_root, output_dir=ready_root / "status")
    executed_status = run_actual_replay_execute_status(root=executed_root, output_dir=executed_root / "status")

    assert no_input_status.workflow_stage == ACTUAL_REPLAY_EXECUTION_NO_INPUT_ARTIFACT
    assert ready_status.workflow_stage == READY_FOR_ACTUAL_REPLAY_EXECUTION
    assert ready_status.ready_for_actual_replay_execution is True
    assert executed_status.workflow_stage == ACTUAL_REPLAY_EXECUTED
    assert executed_status.actual_replay_executed is True
    assert executed_status.replay_decisions_created is False
    assert executed_status.forward_labels_allowed is False
    assert executed_status.weights_trained is False
    assert executed_status.active_stock_profile_exists is False
    assert executed_status.real_buy_review_eligible is False
    assert executed_status.trading_allowed is False
    for phrase in [
        "report-only",
        "execution artifacts only",
        "does not create replay decisions",
        "does not compute forward labels",
        "does not train weights",
        "does not create stock_profile",
        "does not create buy-review eligibility",
        "does not authorize trading",
    ]:
        assert phrase in executed_status.safety_statement


def test_actual_replay_execute_status_reports_health_failure(tmp_path: Path) -> None:
    result = run_actual_replay_execute(replace(_happy_settings(tmp_path), allow_actual_replay_execution=True))
    _patch_json(result.artifact_paths["metadata"], {"trading_allowed": True})

    status = run_actual_replay_execute_status(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "status")

    assert status.workflow_stage == ACTUAL_REPLAY_EXECUTION_HEALTH_FAILED
    assert status.health_status == "FAIL"


def test_cli_actual_replay_execute_artifact_views_run(tmp_path: Path, capsys) -> None:
    run_actual_replay_execute(replace(_happy_settings(tmp_path), allow_actual_replay_execution=True))

    index_code = cli.main(
        ["actual-replay-execute-index", "--root", str(_output_dir(tmp_path)), "--output-dir", str(_output_dir(tmp_path) / "index")]
    )
    index_output = capsys.readouterr().out
    health_code = cli.main(
        ["actual-replay-execute-health", "--root", str(_output_dir(tmp_path)), "--output-dir", str(_output_dir(tmp_path) / "health")]
    )
    health_output = capsys.readouterr().out
    status_code = cli.main(
        ["actual-replay-execute-status", "--root", str(_output_dir(tmp_path)), "--output-dir", str(_output_dir(tmp_path) / "status")]
    )
    status_output = capsys.readouterr().out

    assert index_code == 0
    assert "artifact_count: 1" in index_output
    assert health_code == 0
    assert "status: PASS" in health_output
    assert "checked_artifact_count: 1" in health_output
    assert status_code == 0
    assert f"workflow_stage: {ACTUAL_REPLAY_EXECUTED}" in status_output
    assert "actual_replay_executed: True" in status_output
    assert "replay_decisions_created: False" in status_output
    assert "trading_allowed: False" in status_output
    assert "execution artifacts only" in status_output


def test_research_status_checkpoint_docs_added_without_project_source_pack() -> None:
    parser = cli.build_parser()
    command_names = {action.dest for action in parser._subparsers._group_actions[0]._choices_actions}
    assert "actual-replay-execute" in command_names
    assert "actual-replay-execute-index" in command_names
    assert "actual-replay-execute-health" in command_names
    assert "actual-replay-execute-status" in command_names
    doc = Path("docs/actual_replay_execute.md")
    checkpoint = Path("docs/release_checkpoint_v1.42.0.md")
    source_note = Path("SOURCE_UPDATE_NOTES_v1_42_0.md")
    for path in [doc, checkpoint, source_note]:
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "actual-replay-execute" in text
        assert "ACTUAL_REPLAY_EXECUTED" in text
        assert "report-only" in text
        assert "execution artifacts only" in text
        assert "not replay_decision" in text
        assert "no forward labels" in text
        assert "no training" in text
        assert "no active stock_profile" in text
        assert "no real buy-review eligibility" in text
        assert "no trading" in text
    assert "PAPER_WORKFLOW_READY" in checkpoint.read_text(encoding="utf-8")
    source_text = source_note.read_text(encoding="utf-8")
    assert "docs/project_sources" in source_text
    assert "intentionally absent from Git" in source_text
    assert "after tag v1.42.0" in source_text
    assert "Replay Decision Freeze Planning Report-Only v0.1" in source_text
    assert not Path("docs/project_sources").exists()


def _assert_not_executed_or_downstream(result) -> None:
    assert result.actual_replay_executed is False
    assert result.replay_execution_started is False
    assert result.replay_execution_completed is False
    _assert_downstream_blocked_after_execution(result)


def _assert_downstream_blocked_after_execution(result) -> None:
    assert result.replay_decisions_created is False
    assert result.replay_decisions_exist is False
    assert result.replay_decision_artifact_path == ""
    assert result.forward_labels_allowed is False
    assert result.forward_labels_exist is False
    assert result.training_allowed is False
    assert result.weights_trained is False
    assert result.stock_profile_allowed is False
    assert result.active_stock_profile_exists is False
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


def _required_artifact_keys() -> list[str]:
    return [
        "metadata",
        "report",
        "input_snapshot",
        "observation_snapshot",
        "evidence_bundle_index",
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


def _downstream_false_fields() -> list[str]:
    return [
        "actual_replay_executed",
        "replay_execution_started",
        "replay_execution_completed",
        "replay_decisions_created",
        "replay_decisions_exist",
        "forward_labels_allowed",
        "forward_labels_exist",
        "training_allowed",
        "weights_trained",
        "stock_profile_allowed",
        "active_stock_profile_exists",
        "buy_review_allowed",
        "real_buy_review_eligible",
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
    ]


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "actual_replay_execute_v0_1"


def _fixture_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "actual_replay_execute_fixture_v0_1"


def _happy_settings(tmp_path: Path) -> ActualReplayExecuteSettings:
    root = _fixture_root(tmp_path)
    root.mkdir(parents=True, exist_ok=True)
    active_input = _write_json(root / "active_replay_input.json", _active_input_payload())
    active_health = _write_json(root / "active_input_health.json", {"health_status": "PASS"})
    active_status = _write_json(root / "active_input_status.json", {"status": "ACTIVE_REPLAY_INPUT_CREATED"})
    precheck = _write_json(root / "real_replay_precheck.json", _precheck_payload(active_input))
    precheck_health = _write_json(root / "real_replay_precheck_health.json", {"health_status": "PASS"})
    precheck_status = _write_json(root / "real_replay_precheck_status.json", {"status": "READY_FOR_REAL_REPLAY_EXECUTION_REVIEW"})
    plan = root / "actual_replay_execution_plan.md"
    plan.write_text("# Actual replay execution core report-only plan\n", encoding="utf-8")
    approval = _write_json(root / "approval.json", {"approval_text": EXACT_APPROVAL})
    request = _write_json(root / "request.json", {"actual_replay_execution_core_requested": True, "report_only": True})
    authority = _write_json(root / "authority.json", {"authority_result": "ACCEPTED_FOR_ACTUAL_REPLAY_EXECUTION_CORE_ONLY"})
    attestation = _write_json(root / "attestation.json", _attestation_payload())
    pit_source = _write_json(root / "pit_source_evidence.json", _pit_source_payload())
    taxonomy = _write_json(root / "taxonomy.json", _taxonomy_payload())
    factor_event_company = _write_json(root / "factor_event_company.json", _factor_event_company_payload())
    source_hash = _write_json(root / "source_hash.json", _source_hash_payload())
    leakage = _write_json(root / "leakage.json", _leakage_payload())
    overclaim = _write_json(root / "overclaim.json", _overclaim_payload())
    candidate = _write_json(root / "candidate.json", _candidate_payload(active_input, precheck))
    return ActualReplayExecuteSettings(
        active_replay_input_artifact_path=active_input,
        active_input_health_artifact_path=active_health,
        active_input_status_artifact_path=active_status,
        real_replay_precheck_artifact_path=precheck,
        real_replay_precheck_health_artifact_path=precheck_health,
        real_replay_precheck_status_artifact_path=precheck_status,
        actual_replay_execution_plan_path=plan,
        approval_manifest_path=approval,
        actual_replay_execution_request_manifest_path=request,
        actual_replay_execution_authority_manifest_path=authority,
        second_reviewer_attestation_manifest_path=attestation,
        pit_source_evidence_bundle_path=pit_source,
        taxonomy_evidence_bundle_path=taxonomy,
        factor_event_company_evidence_bundle_path=factor_event_company,
        source_hash_revision_available_time_evidence_path=source_hash,
        leakage_side_effect_evidence_bundle_path=leakage,
        overclaim_evidence_bundle_path=overclaim,
        actual_replay_execution_candidate_manifest_path=candidate,
        output_dir=_output_dir(tmp_path),
    )


def _active_input_payload() -> dict[str, object]:
    payload = {
        "active_input_creation_run_id": "293deb5f459a",
        "input_status": "ACTIVE_REPLAY_INPUT_CREATED",
        "active_replay_input_created": True,
        "active_replay_input": True,
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
    }
    payload.update({field: False for field in _downstream_false_fields()})
    return payload


def _precheck_payload(active_input_path: Path) -> dict[str, object]:
    return {
        "real_replay_execution_run_id": "0657ae658ab8",
        "execution_status": "READY_FOR_REAL_REPLAY_EXECUTION_REVIEW",
        "ready_for_real_replay_execution_review": True,
        "source_active_input_creation_run_id": "293deb5f459a",
        "source_active_replay_input_artifact_path": str(active_input_path),
        "replay_execution_started": False,
        "replay_execution_completed": False,
        "real_replay_executed": False,
        "replay_decisions_created": False,
        "replay_decisions_exist": False,
        "forward_labels_allowed": False,
        "forward_labels_exist": False,
        "training_allowed": False,
        "weights_trained": False,
        "stock_profile_allowed": False,
        "active_stock_profile_exists": False,
        "buy_review_allowed": False,
        "real_buy_review_eligible": False,
        "trading_allowed": False,
    }


def _attestation_payload() -> dict[str, object]:
    return {
        "second_reviewer_attested": True,
        "actual_replay_execution_core_attested": True,
        "report_only_attested": True,
        "no_replay_decision_creation_attested": True,
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
        "no_replay_decisions": True,
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
    payload.update({field: False for field in _downstream_false_fields()})
    payload.update({"forward_returns_exist": False, "approved_for_paper": False})
    return payload


def _overclaim_payload() -> dict[str, object]:
    return {
        "actual_replay_execution_not_replay_decision": True,
        "actual_replay_execution_not_label_permission": True,
        "actual_replay_execution_not_training_permission": True,
        "actual_replay_execution_not_stock_profile_permission": True,
        "actual_replay_execution_not_buy_review_eligibility": True,
        "actual_replay_execution_not_paper_approval": True,
        "actual_replay_execution_not_performance_validation": True,
        "actual_replay_execution_not_trading_authorization": True,
        "buy_review_allowed": False,
        "trading_allowed": False,
        "approved_for_paper": False,
    }


def _candidate_payload(active_input_path: Path, precheck_path: Path) -> dict[str, object]:
    payload = {
        "source_active_replay_input_artifact_path": str(active_input_path),
        "source_active_input_creation_run_id": "293deb5f459a",
        "source_real_replay_precheck_artifact_path": str(precheck_path),
        "source_real_replay_precheck_run_id": "0657ae658ab8",
        "deterministic_only": True,
        "future_labels_excluded": True,
        "replay_decision_artifact_path": "",
    }
    payload.update({field: False for field in _downstream_false_fields()})
    return payload


def _run_cli_with_settings(settings: ActualReplayExecuteSettings, *, allow: bool) -> subprocess.CompletedProcess[str]:
    args = [
        sys.executable,
        "-m",
        "quant_replay_system.cli",
        "actual-replay-execute",
        "--active-replay-input-artifact-path",
        str(settings.active_replay_input_artifact_path),
        "--active-input-health-artifact-path",
        str(settings.active_input_health_artifact_path),
        "--active-input-status-artifact-path",
        str(settings.active_input_status_artifact_path),
        "--real-replay-precheck-artifact-path",
        str(settings.real_replay_precheck_artifact_path),
        "--real-replay-precheck-health-artifact-path",
        str(settings.real_replay_precheck_health_artifact_path),
        "--real-replay-precheck-status-artifact-path",
        str(settings.real_replay_precheck_status_artifact_path),
        "--actual-replay-execution-plan-path",
        str(settings.actual_replay_execution_plan_path),
        "--approval-manifest-path",
        str(settings.approval_manifest_path),
        "--actual-replay-execution-request-manifest-path",
        str(settings.actual_replay_execution_request_manifest_path),
        "--actual-replay-execution-authority-manifest-path",
        str(settings.actual_replay_execution_authority_manifest_path),
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
        "--actual-replay-execution-candidate-manifest-path",
        str(settings.actual_replay_execution_candidate_manifest_path),
        "--output-dir",
        str(settings.output_dir),
    ]
    if allow:
        args.append("--allow-actual-replay-execution")
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
