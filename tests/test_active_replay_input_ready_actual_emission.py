from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from quant_replay_system.active_replay_input_ready_actual_emission import (
    ACTIVE_REPLAY_INPUT_READY,
    ACTUAL_ACTIVE_REPLAY_INPUT_READY_ATTESTATION_BLOCKED,
    ACTUAL_ACTIVE_REPLAY_INPUT_READY_AUTHORITY_BLOCKED,
    ACTUAL_ACTIVE_REPLAY_INPUT_READY_EVIDENCE_BLOCKED,
    ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED,
    ACTUAL_ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED,
    ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED,
    ACTUAL_ACTIVE_REPLAY_INPUT_READY_PIT_BLOCKED,
    ACTUAL_ACTIVE_REPLAY_INPUT_READY_REVIEW_BLOCKED,
    ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED,
    ACTUAL_ACTIVE_REPLAY_INPUT_READY_SOURCE_BLOCKED,
    ACTUAL_ACTIVE_REPLAY_INPUT_READY_TAXONOMY_BLOCKED,
    NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT,
    READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION,
    ActualActiveReplayInputReadyEmissionSettings,
    run_actual_active_replay_input_ready_emission,
)


def test_no_input_writes_required_artifacts_with_safe_defaults(tmp_path: Path) -> None:
    result = run_actual_active_replay_input_ready_emission(
        ActualActiveReplayInputReadyEmissionSettings(output_dir=_output_dir(tmp_path))
    )

    assert result.status == NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT
    assert result.workflow_stage == NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT
    assert result.active_replay_input_ready_marker_emitted is False
    _assert_operational_flags_false(result)
    assert result.report_only is True
    assert result.diagnostic_only is True

    for key in _required_artifact_keys():
        assert result.artifact_paths[key].exists()

    metadata = _read_json(result.artifact_paths["metadata"])
    assert metadata["status"] == NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT
    assert metadata["active_replay_input_ready_marker_emitted"] is False
    assert metadata["active_replay_input_ready"] is False
    for field in _always_false_operational_fields():
        assert metadata[field] is False

    marker = _read_json(result.artifact_paths["marker"])
    assert marker["marker_status"] == NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT
    assert marker["active_replay_input_ready_marker_emitted"] is False
    assert marker["active_replay_input_ready"] is False


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("emission_decision_artifact_path", ACTUAL_ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED),
        ("emission_decision_health_artifact_path", ACTUAL_ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED),
        ("emission_decision_status_artifact_path", ACTUAL_ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED),
        ("actual_emission_plan_path", ACTUAL_ACTIVE_REPLAY_INPUT_READY_REVIEW_BLOCKED),
        ("actual_emission_request_manifest_path", ACTUAL_ACTIVE_REPLAY_INPUT_READY_REVIEW_BLOCKED),
        ("final_authority_manifest_path", ACTUAL_ACTIVE_REPLAY_INPUT_READY_AUTHORITY_BLOCKED),
        ("second_reviewer_attestation_manifest_path", ACTUAL_ACTIVE_REPLAY_INPUT_READY_ATTESTATION_BLOCKED),
        ("pit_source_evidence_bundle_path", ACTUAL_ACTIVE_REPLAY_INPUT_READY_EVIDENCE_BLOCKED),
        ("taxonomy_evidence_bundle_path", ACTUAL_ACTIVE_REPLAY_INPUT_READY_TAXONOMY_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(
    tmp_path: Path, setting_name: str, expected_status: str
) -> None:
    settings = replace(_happy_settings(tmp_path), **{setting_name: None})

    result = run_actual_active_replay_input_ready_emission(settings)

    assert result.status == expected_status
    assert result.active_replay_input_ready_marker_emitted is False
    _assert_operational_flags_false(result)


@pytest.mark.parametrize(
    ("path_name", "override", "expected_status"),
    [
        (
            "emission_decision_artifact_path",
            {"status": "NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT"},
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED,
        ),
        (
            "emission_decision_health_artifact_path",
            {"health_status": "FAIL"},
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED,
        ),
        (
            "emission_decision_artifact_path",
            {"ready_for_active_replay_input_ready_emission_decision": False},
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED,
        ),
        (
            "actual_emission_request_manifest_path",
            {"explicit_actual_active_replay_input_ready_emission_request": False},
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_REVIEW_BLOCKED,
        ),
        (
            "final_authority_manifest_path",
            {"authority_result": "REJECTED"},
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_AUTHORITY_BLOCKED,
        ),
        (
            "second_reviewer_attestation_manifest_path",
            {"second_reviewer_attested": False},
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_ATTESTATION_BLOCKED,
        ),
        (
            "pit_source_evidence_bundle_path",
            {"accepted_pit_universe_evidence_attached": False},
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_PIT_BLOCKED,
        ),
        (
            "pit_source_evidence_bundle_path",
            {"source_hash_coverage_attached": False},
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_SOURCE_BLOCKED,
        ),
        (
            "pit_source_evidence_bundle_path",
            {"factor_observation_coverage_attached": False},
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_EVIDENCE_BLOCKED,
        ),
        (
            "taxonomy_evidence_bundle_path",
            {"not_fixed_12_only": False},
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_TAXONOMY_BLOCKED,
        ),
        (
            "leakage_side_effect_evidence_bundle_path",
            {"no_future_labels": False},
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED,
        ),
        (
            "leakage_side_effect_evidence_bundle_path",
            {"no_data_raw_written": False},
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED,
        ),
        (
            "overclaim_evidence_bundle_path",
            {"marker_only_not_active_input": False},
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED,
        ),
    ],
)
def test_manifest_gate_failures_block(
    tmp_path: Path, path_name: str, override: dict[str, object], expected_status: str
) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(getattr(settings, path_name), override)

    result = run_actual_active_replay_input_ready_emission(settings)

    assert result.status == expected_status
    assert result.active_replay_input_ready_marker_emitted is False
    _assert_operational_flags_false(result)


@pytest.mark.parametrize(
    ("unsafe_field", "expected_status"),
    [
        ("active_replay_input_ready", ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("active_replay_input", ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("active_ready_emitted", ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("replay_execution_allowed", ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("replay_decisions_exist", ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED),
        ("forward_labels_allowed", ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("forward_labels_exist", ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED),
        ("forward_returns_exist", ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED),
        ("training_allowed", ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("training_outputs_exist", ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED),
        ("model_weights_exist", ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED),
        ("weights_trained", ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED),
        ("stock_profile_allowed", ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("stock_profile_artifacts_exist", ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED),
        ("active_stock_profile_exists", ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED),
        ("buy_review_allowed", ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("real_buy_review_eligible", ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED),
        ("trading_allowed", ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("order_placed", ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("message_sent", ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("llm_api_called", ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("external_api_called", ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("cache_mutated", ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("data_raw_written", ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("data_processed_written", ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("data_cache_written", ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("broker_api_called", ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("current_candidates_run", ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("snapshot_built", ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("approved_for_paper", ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
    ],
)
def test_unsafe_input_flags_block(tmp_path: Path, unsafe_field: str, expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.emission_decision_artifact_path, {unsafe_field: True})

    result = run_actual_active_replay_input_ready_emission(settings)

    assert result.status == expected_status
    assert result.active_replay_input_ready_marker_emitted is False
    _assert_operational_flags_false(result)


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_actual_active_replay_input_ready_emission(
            ActualActiveReplayInputReadyEmissionSettings(output_dir=tmp_path / "unsafe")
        )


def test_happy_path_without_allow_flag_reaches_ready_but_does_not_emit_marker(tmp_path: Path) -> None:
    result = run_actual_active_replay_input_ready_emission(_happy_settings(tmp_path))

    assert result.status == READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION
    assert result.workflow_stage == READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION
    assert result.active_replay_input_ready_marker_emitted is False
    assert result.active_replay_input_ready is False
    assert result.active_ready_emitted is False
    _assert_operational_flags_false(result)

    marker = _read_json(result.artifact_paths["marker"])
    assert marker["marker_status"] == READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION
    assert marker["active_replay_input_ready_marker_emitted"] is False
    assert marker["active_replay_input_ready"] is False


def test_happy_path_with_explicit_allow_flag_emits_marker_only(tmp_path: Path) -> None:
    result = run_actual_active_replay_input_ready_emission(
        replace(_happy_settings(tmp_path), allow_active_replay_input_ready_marker_emission=True)
    )

    assert result.status == ACTIVE_REPLAY_INPUT_READY
    assert result.workflow_stage == ACTIVE_REPLAY_INPUT_READY
    assert result.active_replay_input_ready_marker_emitted is True
    assert result.active_replay_input_ready is True
    assert result.active_ready_emitted is True
    _assert_operational_flags_false(result, marker_allowed=True)

    marker = _read_json(result.artifact_paths["marker"])
    assert marker["marker_status"] == ACTIVE_REPLAY_INPUT_READY
    assert marker["active_replay_input_ready_marker_emitted"] is True
    assert marker["active_replay_input_ready"] is True
    assert marker["active_ready_emitted"] is True
    assert marker["active_replay_input"] is False
    assert marker["replay_execution_allowed"] is False
    assert marker["replay_decisions_exist"] is False
    assert marker["forward_labels_allowed"] is False
    assert marker["forward_labels_exist"] is False
    assert marker["training_allowed"] is False
    assert marker["weights_trained"] is False
    assert marker["stock_profile_allowed"] is False
    assert marker["active_stock_profile_exists"] is False
    assert marker["buy_review_allowed"] is False
    assert marker["real_buy_review_eligible"] is False
    assert marker["trading_allowed"] is False

    report = result.artifact_paths["report"].read_text(encoding="utf-8")
    assert "marker-only" in report
    assert "not active replay input" in report
    assert "does not run replay" in report
    assert "does not authorize trading" in report

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_cli_actual_emission_no_input_runs(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "active-replay-input-ready-actual-emission",
            "--output-dir",
            str(_output_dir(tmp_path)),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert f"status: {NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT}" in completed.stdout
    assert "active_replay_input_ready_marker_emitted: False" in completed.stdout
    assert "active_replay_input_ready: False" in completed.stdout
    assert "active_replay_input: False" in completed.stdout


def test_cli_happy_path_requires_explicit_allow_to_emit_marker(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    base_args = _cli_happy_args(settings)

    no_allow = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", *base_args],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    assert f"status: {READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION}" in no_allow.stdout
    assert "active_replay_input_ready_marker_emitted: False" in no_allow.stdout
    assert "status: ACTIVE_REPLAY_INPUT_READY\n" not in no_allow.stdout

    allow = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            *base_args,
            "--allow-active-replay-input-ready-marker-emission",
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    assert f"status: {ACTIVE_REPLAY_INPUT_READY}" in allow.stdout
    assert "active_replay_input_ready_marker_emitted: True" in allow.stdout
    assert "active_replay_input_ready: True" in allow.stdout
    assert "active_replay_input: False" in allow.stdout
    assert "replay_execution_allowed: False" in allow.stdout
    assert "replay_decisions_exist: False" in allow.stdout
    assert "forward_labels_allowed: False" in allow.stdout
    assert "forward_labels_exist: False" in allow.stdout
    assert "training_allowed: False" in allow.stdout
    assert "weights_trained: False" in allow.stdout
    assert "stock_profile_allowed: False" in allow.stdout
    assert "active_stock_profile_exists: False" in allow.stdout
    assert "buy_review_allowed: False" in allow.stdout
    assert "real_buy_review_eligible: False" in allow.stdout
    assert "trading_allowed: False" in allow.stdout


def test_only_core_cli_command_is_added_and_no_docs_or_research_status_integration() -> None:
    help_text = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout

    assert "active-replay-input-ready-actual-emission" in help_text
    assert "active-replay-input-ready-actual-emission-index" not in help_text
    assert "active-replay-input-ready-actual-emission-health" not in help_text
    assert "active-replay-input-ready-actual-emission-status" not in help_text

    dashboard_text = Path("src/quant_replay_system/local_research_dashboard.py").read_text(encoding="utf-8")
    assert "active_replay_input_ready_actual_emission" not in dashboard_text
    assert not Path("docs/release_checkpoint_v1.39.0.md").exists()
    assert not Path("docs/project_sources").exists()


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "active_replay_input_ready_actual_emission_v0_1"


def _happy_settings(tmp_path: Path) -> ActualActiveReplayInputReadyEmissionSettings:
    root = tmp_path / "fixtures"
    root.mkdir(parents=True, exist_ok=True)
    plan = root / "actual_emission_plan.md"
    plan.write_text("actual marker-only emission plan accepted for fixture", encoding="utf-8")
    return ActualActiveReplayInputReadyEmissionSettings(
        emission_decision_artifact_path=_write_json(root / "emission_decision.json", _emission_decision_payload()),
        emission_decision_health_artifact_path=_write_json(root / "emission_decision_health.json", {"health_status": "PASS"}),
        emission_decision_status_artifact_path=_write_json(
            root / "emission_decision_status.json",
            {
                "status": "READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION",
                "workflow_stage": "ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION_READY",
                "ready_for_active_replay_input_ready_emission_decision": True,
                "active_replay_input_ready": False,
                "active_replay_input": False,
                "active_ready_emitted": False,
            },
        ),
        actual_emission_plan_path=plan,
        actual_emission_request_manifest_path=_write_json(
            root / "actual_emission_request.json",
            {
                "request_result": "PASS",
                "explicit_actual_active_replay_input_ready_emission_request": True,
                "requested_marker_status": "ACTIVE_REPLAY_INPUT_READY",
                "marker_only": True,
                "report_only": True,
                "diagnostic_only": True,
            },
        ),
        final_authority_manifest_path=_write_json(
            root / "final_authority.json",
            {
                "authority_result": "PASS",
                "primary_reviewer": "reviewer_a",
                "second_reviewer": "reviewer_b",
                "authorized_by": "reviewer_a",
                "authorized_at": "2026-06-14T00:00:00Z",
                "authority_scope": "actual_active_replay_input_ready_marker_only",
                "authority_reason": "marker-only ACTIVE_REPLAY_INPUT_READY emission; no active input or replay",
            },
        ),
        second_reviewer_attestation_manifest_path=_write_json(
            root / "second_reviewer_attestation.json",
            {
                "second_reviewer_attested": True,
                "marker_only_attested": True,
                "no_active_input_creation_attested": True,
                "no_replay_execution_attested": True,
                "no_replay_decision_creation_attested": True,
                "no_forward_label_attested": True,
                "no_training_attested": True,
                "no_stock_profile_attested": True,
                "no_buy_review_attested": True,
                "no_trading_authority_attested": True,
                "no_performance_claim_attested": True,
                "report_only": True,
                "diagnostic_only": True,
            },
        ),
        pit_source_evidence_bundle_path=_write_json(
            root / "pit_source.json",
            {
                "accepted_pit_universe_evidence_attached": True,
                "source_id_coverage_attached": True,
                "source_hash_coverage_attached": True,
                "revision_id_coverage_attached": True,
                "permission_class_coverage_attached": True,
                "factor_observation_coverage_attached": True,
                "raw_evidence_refs_attached": True,
                "report_only": True,
                "diagnostic_only": True,
            },
        ),
        taxonomy_evidence_bundle_path=_write_json(
            root / "taxonomy.json",
            {
                "uses_8_layer_taxonomy": True,
                "not_fixed_12_only": True,
                "factor_layer_metadata_attached": True,
                "trade_usage_metadata_attached": True,
                "compliance_metadata_attached": True,
                "report_only": True,
                "diagnostic_only": True,
            },
        ),
        leakage_side_effect_evidence_bundle_path=_write_json(
            root / "leakage_side_effect.json",
            {
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
                "report_only": True,
                "diagnostic_only": True,
            },
        ),
        overclaim_evidence_bundle_path=_write_json(
            root / "overclaim.json",
            {
                "marker_only_not_active_input": True,
                "marker_only_not_replay_permission": True,
                "marker_only_not_replay_decision": True,
                "marker_only_not_labels": True,
                "marker_only_not_training": True,
                "marker_only_not_stock_profile": True,
                "marker_only_not_buy_review": True,
                "marker_only_not_trading": True,
                "marker_only_not_performance_validation": True,
                "marker_only_not_paper_approval": True,
                "report_only": True,
                "diagnostic_only": True,
            },
        ),
        active_replay_input_ready_marker_candidate_manifest_path=_write_json(
            root / "marker_candidate.json",
            {
                "candidate_status": "ACTIVE_REPLAY_INPUT_READY",
                "marker_only": True,
                "active_replay_input_ready": False,
                "active_replay_input": False,
                "active_ready_emitted": False,
                "report_only": True,
                "diagnostic_only": True,
            },
        ),
        output_dir=_output_dir(tmp_path),
    )


def _emission_decision_payload() -> dict[str, object]:
    return {
        "active_ready_emission_run_id": "emission_decision123",
        "status": "READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION",
        "workflow_stage": "READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION",
        "ready_for_active_replay_input_ready_emission_decision": True,
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "active_ready_emitted": False,
        "replay_execution_allowed": False,
        "replay_decisions_exist": False,
        "forward_labels_allowed": False,
        "forward_labels_exist": False,
        "forward_returns_exist": False,
        "training_allowed": False,
        "training_outputs_exist": False,
        "model_weights_exist": False,
        "weights_trained": False,
        "stock_profile_allowed": False,
        "stock_profile_artifacts_exist": False,
        "active_stock_profile_exists": False,
        "buy_review_allowed": False,
        "real_buy_review_eligible": False,
        "trading_allowed": False,
        "order_placed": False,
        "message_sent": False,
        "llm_api_called": False,
        "external_api_called": False,
        "cache_mutated": False,
        "data_raw_written": False,
        "data_processed_written": False,
        "data_cache_written": False,
        "broker_api_called": False,
        "current_candidates_run": False,
        "snapshot_built": False,
        "approved_for_paper": False,
        "report_only": True,
        "diagnostic_only": True,
    }


def _assert_operational_flags_false(result: object, marker_allowed: bool = False) -> None:
    if not marker_allowed:
        assert result.active_replay_input_ready is False
        assert result.active_ready_emitted is False
    assert result.active_replay_input is False
    assert result.replay_execution_allowed is False
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


def _always_false_operational_fields() -> list[str]:
    return [
        "active_replay_input",
        "replay_execution_allowed",
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
        "marker",
        "recommended_next_task",
    ]


def _cli_happy_args(settings: ActualActiveReplayInputReadyEmissionSettings) -> list[str]:
    return [
        "active-replay-input-ready-actual-emission",
        "--emission-decision-artifact-path",
        str(settings.emission_decision_artifact_path),
        "--emission-decision-health-artifact-path",
        str(settings.emission_decision_health_artifact_path),
        "--emission-decision-status-artifact-path",
        str(settings.emission_decision_status_artifact_path),
        "--actual-emission-plan-path",
        str(settings.actual_emission_plan_path),
        "--actual-emission-request-manifest-path",
        str(settings.actual_emission_request_manifest_path),
        "--final-authority-manifest-path",
        str(settings.final_authority_manifest_path),
        "--second-reviewer-attestation-manifest-path",
        str(settings.second_reviewer_attestation_manifest_path),
        "--pit-source-evidence-bundle-path",
        str(settings.pit_source_evidence_bundle_path),
        "--taxonomy-evidence-bundle-path",
        str(settings.taxonomy_evidence_bundle_path),
        "--leakage-side-effect-evidence-bundle-path",
        str(settings.leakage_side_effect_evidence_bundle_path),
        "--overclaim-evidence-bundle-path",
        str(settings.overclaim_evidence_bundle_path),
        "--active-replay-input-ready-marker-candidate-manifest-path",
        str(settings.active_replay_input_ready_marker_candidate_manifest_path),
        "--output-dir",
        str(settings.output_dir),
    ]


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _patch_json(path: Path, override: dict[str, object]) -> None:
    payload = _read_json(path)
    payload.update(override)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
