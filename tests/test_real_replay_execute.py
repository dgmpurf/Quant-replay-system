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
from quant_replay_system.local_research_dashboard import run_local_research_dashboard
from quant_replay_system.real_replay_execute_health import check_real_replay_execute_health
from quant_replay_system.real_replay_execute_index import build_real_replay_execute_index
from quant_replay_system.real_replay_execute_status import run_real_replay_execute_status
from quant_replay_system.real_replay_execute import (
    NO_REAL_REPLAY_EXECUTION_INPUT,
    READY_FOR_REAL_REPLAY_EXECUTION_REVIEW,
    REAL_REPLAY_EXECUTION_ATTESTATION_BLOCKED,
    REAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED,
    REAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED,
    REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED,
    REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED,
    REAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED,
    REAL_REPLAY_EXECUTION_PIT_BLOCKED,
    REAL_REPLAY_EXECUTION_REVIEW_BLOCKED,
    REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED,
    REAL_REPLAY_EXECUTION_SOURCE_BLOCKED,
    REAL_REPLAY_EXECUTION_TAXONOMY_BLOCKED,
    RealReplayExecuteSettings,
    run_real_replay_execute,
)


def test_no_input_writes_required_artifacts_with_safe_defaults(tmp_path: Path) -> None:
    result = run_real_replay_execute(RealReplayExecuteSettings(output_dir=_output_dir(tmp_path)))

    assert result.status == NO_REAL_REPLAY_EXECUTION_INPUT
    assert result.workflow_stage == "REAL_REPLAY_EXECUTION_NO_INPUT"
    assert result.ready_for_real_replay_execution_review is False
    _assert_never_executed_or_downstream(result)
    assert result.report_only is True
    assert result.diagnostic_only is True

    for key in _required_artifact_keys():
        assert result.artifact_paths[key].exists()

    metadata = _read_json(result.artifact_paths["metadata"])
    precheck = _read_json(result.artifact_paths["precheck"])
    assert metadata["status"] == NO_REAL_REPLAY_EXECUTION_INPUT
    assert metadata["ready_for_real_replay_execution_review"] is False
    assert precheck["execution_status"] == NO_REAL_REPLAY_EXECUTION_INPUT
    assert precheck["ready_for_real_replay_execution_review"] is False
    assert precheck["replay_execution_started"] is False
    assert precheck["replay_execution_completed"] is False
    assert precheck["real_replay_executed"] is False
    assert precheck["replay_decisions_created"] is False
    assert precheck["replay_decisions_exist"] is False
    assert precheck["future_labels_excluded"] is True
    assert precheck["deterministic_only"] is True
    for field in _downstream_false_fields():
        assert metadata[field] is False
        assert precheck[field] is False


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("active_replay_input_artifact_path", REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("active_input_health_artifact_path", REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("active_input_status_artifact_path", REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("real_replay_execution_plan_path", REAL_REPLAY_EXECUTION_REVIEW_BLOCKED),
        ("replay_execution_request_manifest_path", REAL_REPLAY_EXECUTION_REVIEW_BLOCKED),
        ("replay_execution_authority_manifest_path", REAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED),
        ("second_reviewer_attestation_manifest_path", REAL_REPLAY_EXECUTION_ATTESTATION_BLOCKED),
        ("pit_source_evidence_bundle_path", REAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED),
        ("taxonomy_evidence_bundle_path", REAL_REPLAY_EXECUTION_TAXONOMY_BLOCKED),
        ("factor_event_company_evidence_bundle_path", REAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED),
        ("source_hash_revision_available_time_evidence_path", REAL_REPLAY_EXECUTION_SOURCE_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", REAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED),
        ("replay_execution_candidate_manifest_path", REAL_REPLAY_EXECUTION_REVIEW_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(
    tmp_path: Path,
    setting_name: str,
    expected_status: str,
) -> None:
    result = run_real_replay_execute(replace(_happy_settings(tmp_path), **{setting_name: None}))

    assert result.status == expected_status
    assert result.ready_for_real_replay_execution_review is False
    _assert_never_executed_or_downstream(result)


@pytest.mark.parametrize(
    ("path_name", "override", "expected_status"),
    [
        ("active_replay_input_artifact_path", {"input_status": "READY_FOR_ACTIVE_REPLAY_INPUT_CREATION"}, REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("active_replay_input_artifact_path", {"active_replay_input_created": False}, REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("active_replay_input_artifact_path", {"active_replay_input": False}, REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("active_input_health_artifact_path", {"health_status": "FAIL"}, REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("active_input_status_artifact_path", {"status": "ACTIVE_REPLAY_INPUT_CREATE_NO_INPUT"}, REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED),
        ("replay_execution_request_manifest_path", {"explicit_real_replay_execution_review_request": False}, REAL_REPLAY_EXECUTION_REVIEW_BLOCKED),
        ("replay_execution_authority_manifest_path", {"authority_result": "REJECTED"}, REAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED),
        ("second_reviewer_attestation_manifest_path", {"second_reviewer_attested": False}, REAL_REPLAY_EXECUTION_ATTESTATION_BLOCKED),
        ("pit_source_evidence_bundle_path", {"accepted_pit_universe_evidence_attached": False}, REAL_REPLAY_EXECUTION_PIT_BLOCKED),
        ("pit_source_evidence_bundle_path", {"source_registry_evidence_attached": False}, REAL_REPLAY_EXECUTION_SOURCE_BLOCKED),
        ("pit_source_evidence_bundle_path", {"raw_document_store_attached": False}, REAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED),
        ("taxonomy_evidence_bundle_path", {"not_fixed_12_only": False}, REAL_REPLAY_EXECUTION_TAXONOMY_BLOCKED),
        ("factor_event_company_evidence_bundle_path", {"factor_observation_attached": False}, REAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED),
        ("source_hash_revision_available_time_evidence_path", {"revision_id_coverage_attached": False}, REAL_REPLAY_EXECUTION_SOURCE_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", {"no_future_labels": False}, REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", {"no_data_raw_written": False}, REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("overclaim_evidence_bundle_path", {"replay_precheck_not_replay_execution": False}, REAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED),
        ("replay_execution_candidate_manifest_path", {"deterministic_only": False}, REAL_REPLAY_EXECUTION_REVIEW_BLOCKED),
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

    result = run_real_replay_execute(settings)

    assert result.status == expected_status
    assert result.ready_for_real_replay_execution_review is False
    _assert_never_executed_or_downstream(result)


@pytest.mark.parametrize(
    ("unsafe_field", "expected_status"),
    [
        ("future_labels_exist", REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("forward_labels_allowed", REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("forward_labels_exist", REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("forward_returns_exist", REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("replay_decisions_created", REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("replay_decisions_exist", REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("training_allowed", REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("training_outputs_exist", REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("model_weights_exist", REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("weights_trained", REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("stock_profile_allowed", REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("stock_profile_artifacts_exist", REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("active_stock_profile_exists", REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("buy_review_allowed", REAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED),
        ("real_buy_review_eligible", REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED),
        ("trading_allowed", REAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED),
        ("approved_for_paper", REAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED),
        ("order_placed", REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("broker_api_called", REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("message_sent", REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("llm_api_called", REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("external_api_called", REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("cache_mutated", REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("data_raw_written", REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("data_processed_written", REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
        ("data_cache_written", REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED),
    ],
)
def test_unsafe_input_flags_block(tmp_path: Path, unsafe_field: str, expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.active_replay_input_artifact_path, {unsafe_field: True})

    result = run_real_replay_execute(settings)

    assert result.status == expected_status
    assert result.ready_for_real_replay_execution_review is False
    _assert_never_executed_or_downstream(result)


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_real_replay_execute(RealReplayExecuteSettings(output_dir=tmp_path / "unsafe"))


def test_happy_path_reaches_pre_execution_review_ready_without_running_replay(tmp_path: Path) -> None:
    result = run_real_replay_execute(_happy_settings(tmp_path))

    assert result.status == READY_FOR_REAL_REPLAY_EXECUTION_REVIEW
    assert result.workflow_stage == READY_FOR_REAL_REPLAY_EXECUTION_REVIEW
    assert result.ready_for_real_replay_execution_review is True
    _assert_never_executed_or_downstream(result)

    precheck = _read_json(result.artifact_paths["precheck"])
    assert precheck["execution_status"] == READY_FOR_REAL_REPLAY_EXECUTION_REVIEW
    assert precheck["source_active_input_creation_run_id"] == "293deb5f459a"
    assert precheck["active_replay_input_created"] is True
    assert precheck["active_replay_input"] is True
    assert precheck["replay_as_of_date"] == "2024-04-02"
    assert precheck["replay_calendar"] == "XSHG_XSHE_EOD"
    assert precheck["source_hash_coverage"] == "COMPLETE"
    assert precheck["revision_id_coverage"] == "COMPLETE"
    assert precheck["available_time_policy"] == "ALL_AVAILABLE_TIME_LTE_REPLAY_DECISION_TIME"
    assert precheck["taxonomy_coverage"] == "8_LAYER_TAXONOMY_COVERED"
    assert precheck["future_labels_excluded"] is True
    assert precheck["deterministic_only"] is True
    assert precheck["replay_decision_artifact_path"] == ""
    for field in _downstream_false_fields():
        assert precheck[field] is False

    report = result.artifact_paths["report"].read_text(encoding="utf-8")
    for phrase in [
        "not replay execution",
        "not replay decisions",
        "not forward labels",
        "not training",
        "not stock_profile",
        "not buy-review",
        "not trading",
    ]:
        assert phrase in report


def test_cli_real_replay_execute_runs_no_input(tmp_path: Path, capsys) -> None:
    code = cli.main(
        [
            "real-replay-execute",
            "--output-dir",
            str(_output_dir(tmp_path)),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "status: NO_REAL_REPLAY_EXECUTION_INPUT" in output.out
    assert "workflow_stage: REAL_REPLAY_EXECUTION_NO_INPUT" in output.out
    assert "ready_for_real_replay_execution_review: False" in output.out
    assert "replay_execution_started: False" in output.out
    assert "real_replay_executed: False" in output.out
    assert "replay_decisions_created: False" in output.out
    assert "trading_allowed: False" in output.out


def test_cli_real_replay_execute_happy_path_reaches_review_ready_without_replay(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    args = [
        sys.executable,
        "-m",
        "quant_replay_system.cli",
        "real-replay-execute",
        "--active-replay-input-artifact-path",
        str(settings.active_replay_input_artifact_path),
        "--active-input-health-artifact-path",
        str(settings.active_input_health_artifact_path),
        "--active-input-status-artifact-path",
        str(settings.active_input_status_artifact_path),
        "--real-replay-execution-plan-path",
        str(settings.real_replay_execution_plan_path),
        "--replay-execution-request-manifest-path",
        str(settings.replay_execution_request_manifest_path),
        "--replay-execution-authority-manifest-path",
        str(settings.replay_execution_authority_manifest_path),
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
        "--replay-execution-candidate-manifest-path",
        str(settings.replay_execution_candidate_manifest_path),
        "--output-dir",
        str(_output_dir(tmp_path)),
    ]

    completed = subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert f"status: {READY_FOR_REAL_REPLAY_EXECUTION_REVIEW}" in completed.stdout
    assert "ready_for_real_replay_execution_review: True" in completed.stdout
    assert "replay_execution_started: False" in completed.stdout
    assert "replay_execution_completed: False" in completed.stdout
    assert "real_replay_executed: False" in completed.stdout
    assert "replay_decisions_created: False" in completed.stdout
    assert "replay_decisions_exist: False" in completed.stdout
    assert "forward_labels_allowed: False" in completed.stdout
    assert "weights_trained: False" in completed.stdout
    assert "active_stock_profile_exists: False" in completed.stdout
    assert "real_buy_review_eligible: False" in completed.stdout
    assert "trading_allowed: False" in completed.stdout


def test_index_discovers_no_input_artifact_and_precheck_fields(tmp_path: Path) -> None:
    run_real_replay_execute(RealReplayExecuteSettings(output_dir=_output_dir(tmp_path)))

    index = build_real_replay_execute_index(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "index")

    assert index.artifact_count == 1
    row = index.index_frame.iloc[0].to_dict()
    assert row["status"] == NO_REAL_REPLAY_EXECUTION_INPUT
    assert row["workflow_stage"] == "REAL_REPLAY_EXECUTION_NO_INPUT"
    assert row["ready_for_real_replay_execution_review"] is False
    assert row["active_replay_input_created"] is False
    assert row["active_replay_input"] is False
    assert row["future_labels_excluded"] is True
    assert row["deterministic_only"] is True
    assert row["replay_decision_artifact_path"] == ""
    assert row["report_only"] is True
    assert row["diagnostic_only"] is True
    for field in _downstream_false_fields() + ["signal_semantics_changed"]:
        assert row[field] is False


def test_index_discovers_happy_path_review_ready_artifact(tmp_path: Path) -> None:
    result = run_real_replay_execute(_happy_settings(tmp_path))

    index = build_real_replay_execute_index(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "index")

    assert index.artifact_count == 1
    row = index.index_frame.iloc[0].to_dict()
    assert row["real_replay_execution_run_id"] == result.real_replay_execution_run_id
    assert row["status"] == READY_FOR_REAL_REPLAY_EXECUTION_REVIEW
    assert row["workflow_stage"] == READY_FOR_REAL_REPLAY_EXECUTION_REVIEW
    assert row["ready_for_real_replay_execution_review"] is True
    assert row["source_active_input_creation_run_id"] == "293deb5f459a"
    assert row["active_replay_input_created"] is True
    assert row["active_replay_input"] is True
    assert row["replay_as_of_date"] == "2024-04-02"
    assert row["replay_calendar"] == "XSHG_XSHE_EOD"
    assert row["source_hash_coverage"] == "COMPLETE"
    assert row["revision_id_coverage"] == "COMPLETE"
    assert row["available_time_policy"] == "ALL_AVAILABLE_TIME_LTE_REPLAY_DECISION_TIME"
    assert row["taxonomy_coverage"] == "8_LAYER_TAXONOMY_COVERED"
    for field in _downstream_false_fields() + ["signal_semantics_changed"]:
        assert row[field] is False


def test_health_passes_valid_no_input_artifact(tmp_path: Path) -> None:
    run_real_replay_execute(RealReplayExecuteSettings(output_dir=_output_dir(tmp_path)))

    health = check_real_replay_execute_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "PASS"
    assert health.checked_artifact_count == 1
    assert health.error_count == 0


def test_health_passes_valid_review_ready_artifact(tmp_path: Path) -> None:
    run_real_replay_execute(_happy_settings(tmp_path))

    health = check_real_replay_execute_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "PASS"
    assert health.checked_artifact_count == 1
    assert health.error_count == 0


@pytest.mark.parametrize(
    "unsafe_field",
    [
        "replay_execution_started",
        "replay_execution_completed",
        "real_replay_executed",
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
def test_health_fails_if_unsafe_flags_are_true(tmp_path: Path, unsafe_field: str) -> None:
    result = run_real_replay_execute(_happy_settings(tmp_path))
    _patch_json(result.artifact_paths["metadata"], {unsafe_field: True})
    _patch_json(result.artifact_paths["precheck"], {unsafe_field: True})

    health = check_real_replay_execute_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert health.error_count >= 1
    assert unsafe_field.upper() in "\n".join(health.health_frame["issue_code"].tolist())


def test_health_fails_if_status_is_real_replay_executed(tmp_path: Path) -> None:
    result = run_real_replay_execute(_happy_settings(tmp_path))
    _patch_json(result.artifact_paths["metadata"], {"status": "REAL_REPLAY_EXECUTED"})
    _patch_json(result.artifact_paths["precheck"], {"execution_status": "REAL_REPLAY_EXECUTED"})

    health = check_real_replay_execute_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert "REAL_REPLAY_EXECUTED_UNAUTHORIZED" in health.health_frame["issue_code"].tolist()


def test_health_fails_if_overclaim_guards_fail(tmp_path: Path) -> None:
    result = run_real_replay_execute(_happy_settings(tmp_path))
    frame = pd.read_csv(result.artifact_paths["overclaim_guard_results"])
    frame.loc[0, "passed"] = False
    frame.loc[0, "status"] = REAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED
    frame.to_csv(result.artifact_paths["overclaim_guard_results"], index=False)

    health = check_real_replay_execute_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert "OVERCLAIM_GUARD_FAILED" in health.health_frame["issue_code"].tolist()


def test_status_reports_no_input_state_with_safety_wording(tmp_path: Path) -> None:
    result = run_real_replay_execute(RealReplayExecuteSettings(output_dir=_output_dir(tmp_path)))

    status = run_real_replay_execute_status(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "status")

    assert status.latest_real_replay_execution_run_id == result.real_replay_execution_run_id
    assert status.status == NO_REAL_REPLAY_EXECUTION_INPUT
    assert status.health_status == "PASS"
    assert status.workflow_stage == "REAL_REPLAY_EXECUTION_NO_INPUT"
    assert status.ready_for_real_replay_execution_review is False
    assert status.replay_execution_started is False
    assert status.real_replay_executed is False
    assert status.trading_allowed is False
    _assert_status_safety_text(status.safety_statement)


def test_status_reports_review_ready_state_with_safety_wording(tmp_path: Path) -> None:
    result = run_real_replay_execute(_happy_settings(tmp_path))

    status = run_real_replay_execute_status(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "status")

    assert status.latest_real_replay_execution_run_id == result.real_replay_execution_run_id
    assert status.status == READY_FOR_REAL_REPLAY_EXECUTION_REVIEW
    assert status.health_status == "PASS"
    assert status.workflow_stage == READY_FOR_REAL_REPLAY_EXECUTION_REVIEW
    assert status.ready_for_real_replay_execution_review is True
    assert status.source_active_input_creation_run_id == "293deb5f459a"
    assert status.active_replay_input_created is True
    assert status.active_replay_input is True
    assert status.replay_execution_started is False
    assert status.replay_execution_completed is False
    assert status.real_replay_executed is False
    assert status.replay_decisions_created is False
    assert status.replay_decisions_exist is False
    assert status.forward_labels_allowed is False
    assert status.training_allowed is False
    assert status.weights_trained is False
    assert status.stock_profile_allowed is False
    assert status.real_buy_review_eligible is False
    assert status.trading_allowed is False
    _assert_status_safety_text(status.safety_statement)


def test_cli_real_replay_execute_artifact_views_run(tmp_path: Path, capsys) -> None:
    run_real_replay_execute(RealReplayExecuteSettings(output_dir=_output_dir(tmp_path)))

    assert cli.main(["real-replay-execute-index", "--root", str(_output_dir(tmp_path)), "--output-dir", str(_output_dir(tmp_path) / "index")]) == 0
    index_output = capsys.readouterr().out
    assert "artifact_count: 1" in index_output

    assert cli.main(["real-replay-execute-health", "--root", str(_output_dir(tmp_path)), "--output-dir", str(_output_dir(tmp_path) / "health")]) == 0
    health_output = capsys.readouterr().out
    assert "status: PASS" in health_output

    assert cli.main(["real-replay-execute-status", "--root", str(_output_dir(tmp_path)), "--output-dir", str(_output_dir(tmp_path) / "status")]) == 0
    status_output = capsys.readouterr().out
    assert "status: NO_REAL_REPLAY_EXECUTION_INPUT" in status_output
    assert "workflow_stage: REAL_REPLAY_EXECUTION_NO_INPUT" in status_output
    assert "does not run replay" in status_output


def test_research_status_includes_real_replay_execution_no_input_fields(tmp_path: Path, capsys) -> None:
    root = tmp_path / "outputs" / "reports"
    created = run_real_replay_execute(
        RealReplayExecuteSettings(output_dir=root / "manual_diagnostics" / "real_replay_execute_v0_1")
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    summary = pd.read_csv(result.artifact_paths["local_research_summary"], keep_default_na=False)
    metadata = _read_json(result.artifact_paths["metadata"])
    row = summary.iloc[0].to_dict()

    assert result.real_replay_execution_workflow_implemented is True
    assert result.real_replay_execution_views_implemented is True
    assert result.latest_real_replay_execution_run_id == created.real_replay_execution_run_id
    assert result.latest_real_replay_execution_status == NO_REAL_REPLAY_EXECUTION_INPUT
    assert result.latest_real_replay_execution_health_status == "PASS"
    assert result.latest_real_replay_execution_workflow_stage == "REAL_REPLAY_EXECUTION_NO_INPUT"
    assert result.ready_for_real_replay_execution_review is False
    assert result.replay_execution_started is False
    assert result.real_replay_executed is False
    assert result.replay_decisions_created is False
    assert result.forward_labels_allowed is False
    assert result.weights_trained is False
    assert result.active_stock_profile_exists is False
    assert result.real_buy_review_eligible is False
    assert result.trading_allowed is False
    assert result.no_live_trading is True
    assert result.no_broker_api is True
    assert result.no_order_placement is True
    assert result.no_message_sent is True
    assert row["latest_real_replay_execution_run_id"] == created.real_replay_execution_run_id
    assert row["latest_real_replay_execution_status"] == NO_REAL_REPLAY_EXECUTION_INPUT
    assert row["ready_for_real_replay_execution_review"] is False
    assert row["replay_execution_started"] is False
    assert row["real_replay_executed"] is False
    assert row["replay_decisions_created"] is False
    assert metadata["latest_real_replay_execution_run_id"] == created.real_replay_execution_run_id
    assert metadata["latest_real_replay_execution_status"] == NO_REAL_REPLAY_EXECUTION_INPUT
    assert metadata["ready_for_real_replay_execution_review"] is False
    assert metadata["component_statuses"]["latest_real_replay_execution_run_id"] == (
        created.real_replay_execution_run_id
    )

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard_cli")])
    output = capsys.readouterr()

    assert code == 0
    assert f"latest_real_replay_execution_run_id: {created.real_replay_execution_run_id}" in output.out
    assert f"latest_real_replay_execution_status: {NO_REAL_REPLAY_EXECUTION_INPUT}" in output.out
    assert "ready_for_real_replay_execution_review: False" in output.out
    assert "replay_execution_started: False" in output.out
    assert "real_replay_executed: False" in output.out
    assert "replay_decisions_created: False" in output.out
    assert "trading_allowed: False" in output.out


def test_research_status_preserves_paper_priority_over_real_replay_review_ready(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    created = run_real_replay_execute(
        replace(_happy_settings(tmp_path), output_dir=root / "manual_diagnostics" / "real_replay_execute_v0_1")
    )
    _paper_workflow_status(root)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.latest_real_replay_execution_run_id == created.real_replay_execution_run_id
    assert result.latest_real_replay_execution_status == READY_FOR_REAL_REPLAY_EXECUTION_REVIEW
    assert result.latest_real_replay_execution_health_status == "PASS"
    assert result.latest_real_replay_execution_workflow_stage == READY_FOR_REAL_REPLAY_EXECUTION_REVIEW
    assert result.ready_for_real_replay_execution_review is True
    assert result.source_active_input_creation_run_id == "293deb5f459a"
    assert result.active_replay_input is True
    assert result.replay_as_of_date == "2024-04-02"
    assert result.source_active_replay_input_artifact_path.endswith("active_replay_input.json")
    assert result.symbol_universe_ref.endswith("symbol_universe.json")
    assert result.raw_document_store_ref.endswith("raw_documents.json")
    assert result.factor_definition_ref.endswith("factor_definitions.json")
    assert result.factor_observation_ref.endswith("factor_observations.json")
    assert result.event_structured_ref.endswith("events.json")
    assert result.company_exposure_ref.endswith("exposures.json")
    assert result.evidence_bundle_ref.endswith("evidence_bundle.json")
    assert result.source_hash_coverage == "COMPLETE"
    assert result.revision_id_coverage == "COMPLETE"
    assert result.available_time_policy == "ALL_AVAILABLE_TIME_LTE_REPLAY_DECISION_TIME"
    assert result.taxonomy_coverage == "8_LAYER_TAXONOMY_COVERED"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.replay_execution_started is False
    assert result.real_replay_executed is False
    assert result.replay_decisions_created is False
    assert result.forward_labels_allowed is False
    assert result.weights_trained is False
    assert result.active_stock_profile_exists is False
    assert result.real_buy_review_eligible is False
    assert result.trading_allowed is False


def test_real_replay_execute_docs_checkpoint_and_source_note_are_report_only() -> None:
    workflow_doc = Path("docs/real_replay_execute.md")
    dashboard_doc = Path("docs/local_research_dashboard.md")
    readme = Path("README.md")
    checkpoint = Path("docs/release_checkpoint_v1.41.0.md")
    source_note = Path("SOURCE_UPDATE_NOTES_v1_41_0.md")

    for path in [workflow_doc, dashboard_doc, readme, checkpoint, source_note]:
        text = path.read_text(encoding="utf-8")
        assert "real replay execution" in text.lower()
        assert "pre-execution review" in text.lower()
        assert "does not run replay" in text
        assert "does not create replay decisions" in text
        assert "does not compute forward labels" in text
        assert "does not train weights" in text
        assert "does not create active stock profiles" in text
        assert "does not create real buy-review eligibility" in text
        assert "does not authorize trading" in text

    source_text = source_note.read_text(encoding="utf-8")
    assert "docs/project_sources/ is intentionally absent from Git" in source_text
    assert "ChatGPT Project Source is maintained separately" in source_text
    assert "Real Replay Execution Artifact Views Report-Only v0.1" in source_text
    assert not Path("docs/project_sources").exists()


def _assert_never_executed_or_downstream(result) -> None:
    assert result.replay_execution_started is False
    assert result.replay_execution_completed is False
    assert result.real_replay_executed is False
    assert result.replay_execution_allowed is False
    assert result.replay_decisions_created is False
    assert result.replay_decisions_exist is False
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


def _assert_status_safety_text(text: str) -> None:
    for phrase in [
        "report-only",
        "diagnostic-only",
        "pre-execution review-ready only",
        "does not run replay",
        "does not create replay decisions",
        "does not compute labels",
        "does not train weights",
        "does not create stock_profile",
        "does not create buy-review eligibility",
        "does not authorize trading",
    ]:
        assert phrase in text


def _required_artifact_keys() -> list[str]:
    return [
        "metadata",
        "report",
        "precondition_results",
        "authority_results",
        "lineage_results",
        "attestation_results",
        "pit_source_evidence_results",
        "taxonomy_evidence_results",
        "leakage_side_effect_guard_results",
        "overclaim_guard_results",
        "precheck",
        "recommended_next_task",
    ]


def _downstream_false_fields() -> list[str]:
    return [
        "replay_execution_started",
        "replay_execution_completed",
        "real_replay_executed",
        "replay_execution_allowed",
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
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "real_replay_execute_v0_1"


def _fixture_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "real_replay_execute_fixture_v0_1"


def _paper_workflow_status(root: Path) -> Path:
    folder = root / "paper_trading" / "workflow_status" / "paper-workflow-status-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "paper_workflow_status_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "workflow_status_id": "paper-workflow-status-a",
            "created_at": "2024-05-20T16:15:00",
            "status": "WARN",
            "workflow_stage": "WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
            "latest_decision_date": "2024-05-20",
            "next_manual_action": "Demo WATCH_ONLY paper workflow validated; no fills were supplied.",
            "total_warning_count": 1,
            "expected_demo_warning_count": 1,
            "stale_warning_count": 0,
            "actionable_warning_count": 0,
            "blocking_error_count": 0,
            "component_statuses": {
                "total_warning_count": 1,
                "expected_demo_warning_count": 1,
                "stale_warning_count": 0,
                "actionable_warning_count": 0,
                "blocking_error_count": 0,
            },
            "output_files": {"paper_workflow_status_report": str(report)},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _happy_settings(tmp_path: Path) -> RealReplayExecuteSettings:
    root = _fixture_root(tmp_path)
    root.mkdir(parents=True, exist_ok=True)
    active_input = _write_json(root / "active_replay_input.json", _active_input_payload())
    health = _write_json(root / "active_input_health.json", {"health_status": "PASS"})
    status = _write_json(
        root / "active_input_status.json",
        {
            "status": "ACTIVE_REPLAY_INPUT_CREATED",
            "active_replay_input_created": True,
            "active_replay_input": True,
        },
    )
    plan = root / "real_replay_execution_plan.md"
    plan.write_text("# Report-only real replay execution precheck plan\n", encoding="utf-8")
    request = _write_json(root / "replay_execution_request.json", _request_payload())
    authority = _write_json(root / "replay_execution_authority.json", _authority_payload())
    attestation = _write_json(root / "second_reviewer_attestation.json", _attestation_payload())
    pit_source = _write_json(root / "pit_source_evidence.json", _pit_source_payload())
    taxonomy = _write_json(root / "taxonomy_evidence.json", _taxonomy_payload())
    factor_event_company = _write_json(
        root / "factor_event_company_evidence.json",
        _factor_event_company_payload(),
    )
    source_hash = _write_json(root / "source_hash_revision_available_time.json", _source_hash_payload())
    leakage = _write_json(root / "leakage_side_effect.json", _leakage_payload())
    overclaim = _write_json(root / "overclaim.json", _overclaim_payload())
    candidate = _write_json(root / "replay_execution_candidate.json", _candidate_payload(active_input))
    return RealReplayExecuteSettings(
        active_replay_input_artifact_path=active_input,
        active_input_health_artifact_path=health,
        active_input_status_artifact_path=status,
        real_replay_execution_plan_path=plan,
        replay_execution_request_manifest_path=request,
        replay_execution_authority_manifest_path=authority,
        second_reviewer_attestation_manifest_path=attestation,
        pit_source_evidence_bundle_path=pit_source,
        taxonomy_evidence_bundle_path=taxonomy,
        factor_event_company_evidence_bundle_path=factor_event_company,
        source_hash_revision_available_time_evidence_path=source_hash,
        leakage_side_effect_evidence_bundle_path=leakage,
        overclaim_evidence_bundle_path=overclaim,
        replay_execution_candidate_manifest_path=candidate,
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
        "symbol_universe_ref": "outputs/reports/manual_diagnostics/example/symbol_universe.json",
        "pit_universe_ref": "outputs/reports/manual_diagnostics/example/pit_universe.json",
        "source_registry_ref": "outputs/reports/manual_diagnostics/example/source_registry.json",
        "raw_document_store_ref": "outputs/reports/manual_diagnostics/example/raw_documents.json",
        "factor_definition_ref": "outputs/reports/manual_diagnostics/example/factor_definitions.json",
        "factor_observation_ref": "outputs/reports/manual_diagnostics/example/factor_observations.json",
        "event_structured_ref": "outputs/reports/manual_diagnostics/example/events.json",
        "company_exposure_ref": "outputs/reports/manual_diagnostics/example/exposures.json",
        "evidence_bundle_ref": "outputs/reports/manual_diagnostics/example/evidence_bundle.json",
        "source_hash_coverage": "COMPLETE",
        "revision_id_coverage": "COMPLETE",
        "available_time_policy": "ALL_AVAILABLE_TIME_LTE_REPLAY_DECISION_TIME",
        "taxonomy_coverage": "8_LAYER_TAXONOMY_COVERED",
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update({field: False for field in _downstream_false_fields()})
    return payload


def _request_payload() -> dict[str, object]:
    return {
        "explicit_real_replay_execution_review_request": True,
        "actual_replay_execution_authorized": False,
        "replay_decision_creation_authorized": False,
        "report_only": True,
        "diagnostic_only": True,
    }


def _authority_payload() -> dict[str, object]:
    return {
        "authority_result": "ACCEPTED_FOR_PRE_EXECUTION_REVIEW_ONLY",
        "primary_reviewer": "reviewer_a",
        "second_reviewer": "reviewer_b",
        "authorized_by": "reviewer_a",
        "authorized_at": "2026-06-15T00:00:00Z",
        "authority_scope": "PRE_EXECUTION_REVIEW_ONLY",
        "authority_reason": "Validate readiness without running replay.",
        "can_authorize_actual_replay_execution": False,
    }


def _attestation_payload() -> dict[str, object]:
    return {
        "second_reviewer_attested": True,
        "real_replay_pre_execution_review_attested": True,
        "report_only_attested": True,
        "no_actual_replay_execution_attested": True,
        "no_replay_decision_creation_attested": True,
        "no_forward_label_attested": True,
        "no_training_attested": True,
        "no_stock_profile_attested": True,
        "no_buy_review_attested": True,
        "no_trading_authority_attested": True,
        "no_performance_claim_attested": True,
        "report_only": True,
        "diagnostic_only": True,
    }


def _pit_source_payload() -> dict[str, object]:
    return {
        "accepted_pit_universe_evidence_attached": True,
        "source_registry_evidence_attached": True,
        "raw_document_store_attached": True,
        "evidence_bundle_attached": True,
        "report_only": True,
        "diagnostic_only": True,
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
        "report_only": True,
        "diagnostic_only": True,
    }


def _factor_event_company_payload() -> dict[str, object]:
    return {
        "factor_definition_attached": True,
        "factor_observation_attached": True,
        "event_structured_attached": True,
        "company_exposure_attached": True,
        "all_available_time_lte_replay_decision_time": True,
        "report_only": True,
        "diagnostic_only": True,
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
        "no_replay_execution": True,
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
    payload.update(
        {
            "future_labels_exist": False,
            "forward_returns_exist": False,
            "training_outputs_exist": False,
            "model_weights_exist": False,
            "stock_profile_artifacts_exist": False,
            "approved_for_paper": False,
        }
    )
    return payload


def _overclaim_payload() -> dict[str, object]:
    return {
        "replay_precheck_not_replay_execution": True,
        "replay_precheck_not_replay_decision_permission": True,
        "replay_precheck_not_label_permission": True,
        "replay_precheck_not_training_permission": True,
        "replay_precheck_not_stock_profile_permission": True,
        "replay_precheck_not_buy_review_eligibility": True,
        "replay_precheck_not_paper_approval": True,
        "replay_precheck_not_performance_validation": True,
        "replay_precheck_not_trading_authorization": True,
        "active_input_not_replay_execution": True,
        "report_only": True,
        "diagnostic_only": True,
        "buy_review_allowed": False,
        "trading_allowed": False,
        "approved_for_paper": False,
    }


def _candidate_payload(active_input_path: Path) -> dict[str, object]:
    payload = {
        "source_active_replay_input_artifact_path": str(active_input_path),
        "source_active_input_creation_run_id": "293deb5f459a",
        "deterministic_only": True,
        "future_labels_excluded": True,
        "replay_decision_artifact_path": "",
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update({field: False for field in _downstream_false_fields()})
    return payload


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
