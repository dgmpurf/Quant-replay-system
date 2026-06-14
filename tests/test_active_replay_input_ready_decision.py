from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from quant_replay_system.active_replay_input_ready_decision import (
    NO_ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT,
    READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION,
    ActiveReplayInputReadyDecisionSettings,
    run_active_replay_input_ready_decision,
)


def test_no_input_writes_report_only_artifacts_without_active_ready_claim(tmp_path: Path) -> None:
    result = run_active_replay_input_ready_decision(
        ActiveReplayInputReadyDecisionSettings(output_dir=_decision_output_dir(tmp_path))
    )

    assert result.status == NO_ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT
    assert result.workflow_stage == NO_ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT
    assert result.ready_for_active_replay_input_ready_decision is False
    _assert_never_active(result)
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_path.is_relative_to(_decision_output_dir(tmp_path))

    for key in _required_artifact_keys():
        assert result.artifact_paths[key].exists()

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == NO_ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT
    assert metadata["ready_for_active_replay_input_ready_decision"] is False
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_ready_emitted"] is False
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert "ACTIVE_REPLAY_INPUT_READY" not in {metadata["status"], metadata["workflow_stage"]}


@pytest.mark.parametrize(
    ("override", "expected_status"),
    [
        ({"status": "EMISSION_LINEAGE_BLOCKED"}, "ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED"),
        ({"active_replay_input_ready": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED"),
        ({"active_replay_input": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED"),
        ({"active_ready_emitted": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED"),
        ({"forward_labels_exist": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED"),
        ({"forward_returns_exist": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED"),
        ({"weights_trained": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED"),
        ({"active_stock_profile_exists": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED"),
        ({"real_buy_review_eligible": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED"),
        ({"order_placed": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED"),
        ({"message_sent": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED"),
        ({"llm_api_called": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED"),
        ({"external_api_called": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED"),
        ({"cache_mutated": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED"),
        ({"data_raw_written": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED"),
        ({"data_processed_written": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED"),
        ({"data_cache_written": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED"),
        ({"current_candidates_run": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED"),
        ({"snapshot_built": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED"),
        ({"replay_execution_allowed": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED"),
        ({"training_allowed": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED"),
        ({"buy_review_allowed": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED"),
        ({"trading_allowed": True}, "ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED"),
    ],
)
def test_emission_metadata_blocks_unsafe_state(
    tmp_path: Path, override: dict[str, object], expected_status: str
) -> None:
    emission_artifact = _write_emission_artifact(tmp_path / "emission", override)
    settings = _happy_settings(tmp_path, emission_artifact_path=emission_artifact)

    result = run_active_replay_input_ready_decision(settings)

    assert result.status == expected_status
    assert result.ready_for_active_replay_input_ready_decision is False
    _assert_never_active(result)
    assert result.status != "ACTIVE_REPLAY_INPUT_READY"


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("emission_artifact_path", "ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED"),
        ("emission_health_artifact_path", "ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED"),
        ("emission_status_artifact_path", "ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED"),
        ("emission_acceptance_audit_path", "ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED"),
        ("decision_request_manifest_path", "ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED"),
        ("decision_authority_manifest_path", "ACTIVE_REPLAY_INPUT_READY_DECISION_AUTHORITY_BLOCKED"),
        ("decision_attestation_manifest_path", "ACTIVE_REPLAY_INPUT_READY_DECISION_ATTESTATION_BLOCKED"),
        ("pit_source_evidence_bundle_path", "ACTIVE_REPLAY_INPUT_READY_DECISION_EVIDENCE_BLOCKED"),
        ("taxonomy_evidence_bundle_path", "ACTIVE_REPLAY_INPUT_READY_DECISION_TAXONOMY_BLOCKED"),
        ("leakage_side_effect_evidence_bundle_path", "ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED"),
        ("overclaim_evidence_bundle_path", "ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED"),
        (
            "active_replay_input_ready_candidate_manifest_path",
            "ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED",
        ),
    ],
)
def test_missing_required_manifests_block_by_gate(
    tmp_path: Path, setting_name: str, expected_status: str
) -> None:
    settings = _replace_setting(_happy_settings(tmp_path), setting_name, None)

    result = run_active_replay_input_ready_decision(settings)

    assert result.status == expected_status
    assert result.ready_for_active_replay_input_ready_decision is False
    _assert_never_active(result)


@pytest.mark.parametrize(
    ("setting_name", "writer", "override", "expected_status"),
    [
        (
            "decision_authority_manifest_path",
            "_write_authority",
            {"authority_result": "REJECTED"},
            "ACTIVE_REPLAY_INPUT_READY_DECISION_AUTHORITY_BLOCKED",
        ),
        (
            "decision_attestation_manifest_path",
            "_write_attestation",
            {"no_replay_execution_attested": False},
            "ACTIVE_REPLAY_INPUT_READY_DECISION_ATTESTATION_BLOCKED",
        ),
        (
            "pit_source_evidence_bundle_path",
            "_write_pit_source_evidence",
            {"accepted_pit_universe_evidence_attached": False},
            "ACTIVE_REPLAY_INPUT_READY_DECISION_PIT_BLOCKED",
        ),
        (
            "pit_source_evidence_bundle_path",
            "_write_pit_source_evidence",
            {"source_hash_coverage_attached": False},
            "ACTIVE_REPLAY_INPUT_READY_DECISION_SOURCE_BLOCKED",
        ),
        (
            "pit_source_evidence_bundle_path",
            "_write_pit_source_evidence",
            {"factor_observation_coverage_attached": False},
            "ACTIVE_REPLAY_INPUT_READY_DECISION_EVIDENCE_BLOCKED",
        ),
        (
            "taxonomy_evidence_bundle_path",
            "_write_taxonomy",
            {"not_fixed_12_only": False},
            "ACTIVE_REPLAY_INPUT_READY_DECISION_TAXONOMY_BLOCKED",
        ),
        (
            "leakage_side_effect_evidence_bundle_path",
            "_write_leakage_side_effect",
            {"no_future_labels": False},
            "ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED",
        ),
        (
            "leakage_side_effect_evidence_bundle_path",
            "_write_leakage_side_effect",
            {"no_data_raw_written": False},
            "ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED",
        ),
        (
            "overclaim_evidence_bundle_path",
            "_write_overclaim",
            {"emission_ready_review_not_active_input_ready": False},
            "ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED",
        ),
        (
            "active_replay_input_ready_candidate_manifest_path",
            "_write_candidate_manifest",
            {"candidate_status": "ACTIVE_REPLAY_INPUT_READY"},
            "ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED",
        ),
    ],
)
def test_manifest_gate_failures_block(
    tmp_path: Path,
    setting_name: str,
    writer: str,
    override: dict[str, object],
    expected_status: str,
) -> None:
    replacement = globals()[writer](tmp_path / f"{setting_name}.json", override)
    settings = _replace_setting(_happy_settings(tmp_path), setting_name, replacement)

    result = run_active_replay_input_ready_decision(settings)

    assert result.status == expected_status
    assert result.ready_for_active_replay_input_ready_decision is False
    _assert_never_active(result)


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    settings = ActiveReplayInputReadyDecisionSettings(output_dir=tmp_path / "unsafe")

    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_active_replay_input_ready_decision(settings)


def test_happy_path_reaches_ready_decision_only(tmp_path: Path) -> None:
    result = run_active_replay_input_ready_decision(_happy_settings(tmp_path))

    assert result.status == READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION
    assert result.workflow_stage == READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION
    assert result.ready_for_active_replay_input_ready_decision is True
    _assert_never_active(result)
    assert result.blocker_count == 0
    assert result.overclaim_guard_pass_count == result.overclaim_guard_total_count
    assert result.status != "ACTIVE_REPLAY_INPUT_READY"

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION
    assert metadata["ready_for_active_replay_input_ready_decision"] is True
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_ready_emitted"] is False
    assert metadata["status"] != "ACTIVE_REPLAY_INPUT_READY"

    candidate = json.loads(result.artifact_paths["ready_candidate"].read_text(encoding="utf-8"))
    assert candidate["ready_for_active_replay_input_ready_decision"] is True
    assert candidate["active_replay_input_ready"] is False
    assert candidate["active_replay_input"] is False
    assert candidate["active_ready_emitted"] is False
    assert candidate["status"] != "ACTIVE_REPLAY_INPUT_READY"

    report = result.artifact_paths["decision_report"].read_text(encoding="utf-8")
    assert "not ACTIVE_REPLAY_INPUT_READY" in report
    assert "does not run replay" in report
    assert "does not create active replay input" in report

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_cli_active_replay_input_ready_decision_runs_without_active_ready_claim(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "active-replay-input-ready-decision",
            "--emission-artifact-path",
            str(settings.emission_artifact_path),
            "--emission-health-artifact-path",
            str(settings.emission_health_artifact_path),
            "--emission-status-artifact-path",
            str(settings.emission_status_artifact_path),
            "--emission-acceptance-audit-path",
            str(settings.emission_acceptance_audit_path),
            "--decision-request-manifest-path",
            str(settings.decision_request_manifest_path),
            "--decision-authority-manifest-path",
            str(settings.decision_authority_manifest_path),
            "--decision-attestation-manifest-path",
            str(settings.decision_attestation_manifest_path),
            "--pit-source-evidence-bundle-path",
            str(settings.pit_source_evidence_bundle_path),
            "--taxonomy-evidence-bundle-path",
            str(settings.taxonomy_evidence_bundle_path),
            "--leakage-side-effect-evidence-bundle-path",
            str(settings.leakage_side_effect_evidence_bundle_path),
            "--overclaim-evidence-bundle-path",
            str(settings.overclaim_evidence_bundle_path),
            "--active-replay-input-ready-candidate-manifest-path",
            str(settings.active_replay_input_ready_candidate_manifest_path),
            "--output-dir",
            str(settings.output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "decision_run_id:" in completed.stdout
    assert f"status: {READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION}" in completed.stdout
    assert "ready_for_active_replay_input_ready_decision: True" in completed.stdout
    assert "active_replay_input_ready: False" in completed.stdout
    assert "active_replay_input: False" in completed.stdout
    assert "active_ready_emitted: False" in completed.stdout
    assert "replay_execution_allowed: False" in completed.stdout
    assert "forward_labels_allowed: False" in completed.stdout
    assert "training_allowed: False" in completed.stdout
    assert "stock_profile_allowed: False" in completed.stdout
    assert "buy_review_allowed: False" in completed.stdout
    assert "trading_allowed: False" in completed.stdout
    assert "status: ACTIVE_REPLAY_INPUT_READY\n" not in completed.stdout
    assert "workflow_stage: ACTIVE_REPLAY_INPUT_READY\n" not in completed.stdout


def test_cli_scope_does_not_add_views_research_status_or_checkpoint() -> None:
    help_text = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout

    assert "active-replay-input-ready-decision" in help_text
    assert "active-replay-input-ready-decision-index" not in help_text
    assert "active-replay-input-ready-decision-health" not in help_text
    assert "active-replay-input-ready-decision-status" not in help_text

    completed = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "research-status"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    assert "active_replay_input_ready_decision" not in completed.stdout
    assert not Path("docs/release_checkpoint_v1.36.0.md").exists()
    assert not Path("docs/project_sources").exists()


def _assert_never_active(result) -> None:
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.active_ready_emitted is False
    assert result.replay_execution_allowed is False
    assert result.forward_labels_allowed is False
    assert result.training_allowed is False
    assert result.stock_profile_allowed is False
    assert result.buy_review_allowed is False
    assert result.trading_allowed is False
    assert result.forward_labels_exist is False
    assert result.forward_returns_exist is False
    assert result.training_outputs_exist is False
    assert result.model_weights_exist is False
    assert result.active_stock_profile_exists is False
    assert result.real_buy_review_eligible is False
    assert result.approved_for_paper is False
    assert result.order_placed is False
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
        "decision_report",
        "decision_precondition_results",
        "decision_authority_results",
        "emission_lineage_results",
        "decision_attestation_results",
        "pit_source_evidence_results",
        "taxonomy_evidence_results",
        "leakage_side_effect_guard_results",
        "overclaim_guard_results",
        "ready_candidate",
        "recommended_next_task",
    ]


def _decision_output_dir(tmp_path: Path) -> Path:
    return (
        tmp_path
        / "outputs"
        / "reports"
        / "manual_diagnostics"
        / "active_replay_input_ready_decision_v0_1"
    )


def _happy_settings(tmp_path: Path, **overrides: Path | None) -> ActiveReplayInputReadyDecisionSettings:
    def default_path(name: str, writer):
        return overrides[name] if name in overrides else writer()

    values = {
        "output_dir": _decision_output_dir(tmp_path),
        "emission_artifact_path": default_path(
            "emission_artifact_path", lambda: _write_emission_artifact(tmp_path / "emission")
        ),
        "emission_health_artifact_path": default_path(
            "emission_health_artifact_path",
            lambda: _write_json(tmp_path / "emission_health.json", {"health_status": "PASS"}),
        ),
        "emission_status_artifact_path": default_path(
            "emission_status_artifact_path",
            lambda: _write_json(
                tmp_path / "emission_status.json",
                {
                    "status": "EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW",
                    "workflow_stage": "EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW",
                    "ready_for_active_replay_input_ready_review": True,
                    "active_replay_input_ready": False,
                    "active_replay_input": False,
                    "active_ready_emitted": False,
                },
            ),
        ),
        "emission_acceptance_audit_path": default_path(
            "emission_acceptance_audit_path",
            lambda: _write_json(
                tmp_path / "emission_acceptance_audit.json",
                {
                    "audit_id": "emission_acceptance_audit_001",
                    "audit_result": "PASS",
                    "emission_ready_for_decision_review": True,
                    "report_only": True,
                    "diagnostic_only": True,
                },
            ),
        ),
        "decision_request_manifest_path": default_path(
            "decision_request_manifest_path", lambda: _write_decision_request(tmp_path / "decision_request.json")
        ),
        "decision_authority_manifest_path": default_path(
            "decision_authority_manifest_path", lambda: _write_authority(tmp_path / "authority.json")
        ),
        "decision_attestation_manifest_path": default_path(
            "decision_attestation_manifest_path", lambda: _write_attestation(tmp_path / "attestation.json")
        ),
        "pit_source_evidence_bundle_path": default_path(
            "pit_source_evidence_bundle_path", lambda: _write_pit_source_evidence(tmp_path / "pit_source.json")
        ),
        "taxonomy_evidence_bundle_path": default_path(
            "taxonomy_evidence_bundle_path", lambda: _write_taxonomy(tmp_path / "taxonomy.json")
        ),
        "leakage_side_effect_evidence_bundle_path": default_path(
            "leakage_side_effect_evidence_bundle_path",
            lambda: _write_leakage_side_effect(tmp_path / "leakage_side_effect.json"),
        ),
        "overclaim_evidence_bundle_path": default_path(
            "overclaim_evidence_bundle_path", lambda: _write_overclaim(tmp_path / "overclaim.json")
        ),
        "active_replay_input_ready_candidate_manifest_path": default_path(
            "active_replay_input_ready_candidate_manifest_path",
            lambda: _write_candidate_manifest(tmp_path / "ready_candidate_manifest.json"),
        ),
    }
    values.update(overrides)
    return ActiveReplayInputReadyDecisionSettings(**values)


def _replace_setting(
    settings: ActiveReplayInputReadyDecisionSettings, field_name: str, value: Path | None
) -> ActiveReplayInputReadyDecisionSettings:
    values = settings.__dict__.copy()
    values[field_name] = value
    return ActiveReplayInputReadyDecisionSettings(**values)


def _write_emission_artifact(path: Path, overrides: dict[str, object] | None = None) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    payload = {
        "emission_run_id": "emission_001",
        "status": "EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW",
        "workflow_stage": "EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW",
        "ready_for_active_replay_input_ready_review": True,
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "active_ready_emitted": False,
        "forward_labels_exist": False,
        "forward_returns_exist": False,
        "training_outputs_exist": False,
        "model_weights_exist": False,
        "weights_trained": False,
        "stock_profile_artifacts_exist": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
        "approved_for_paper": False,
        "approval_applied": False,
        "order_placed": False,
        "message_sent": False,
        "llm_api_called": False,
        "external_api_called": False,
        "cache_mutated": False,
        "data_raw_written": False,
        "data_processed_written": False,
        "data_cache_written": False,
        "current_candidates_run": False,
        "snapshot_built": False,
        "replay_execution_allowed": False,
        "forward_labels_allowed": False,
        "training_allowed": False,
        "stock_profile_allowed": False,
        "buy_review_allowed": False,
        "trading_allowed": False,
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update(overrides or {})
    (path / "emission_metadata.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_decision_request(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "decision_request_id": "decision_request_001",
        "requested_status": READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION,
        "requested_by": "fixture_reviewer",
        "requested_at": "2024-04-02T19:00:00+08:00",
        "request_reason": "fixture report-only ready decision precondition check",
        "allow_active_replay_input_ready": False,
        "allow_active_replay_input_creation": False,
        "allow_replay_execution": False,
        "allow_forward_labels": False,
        "allow_training": False,
        "allow_stock_profile": False,
        "allow_buy_review": False,
        "allow_trading": False,
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_authority(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "decision_authority_id": "authority_001",
        "primary_reviewer": "primary_fixture_reviewer",
        "second_reviewer": "second_fixture_reviewer",
        "pit_source_reviewer": "pit_fixture_reviewer",
        "evidence_taxonomy_reviewer": "evidence_fixture_reviewer",
        "risk_compliance_reviewer": "risk_fixture_reviewer",
        "system_operator": "operator_fixture",
        "strategy_owner": "owner_fixture",
        "authority_scope": "report-only active-ready decision review",
        "authority_result": "ACCEPTED_FOR_REVIEW_ONLY",
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_attestation(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "attestation_id": "attestation_001",
        "primary_reviewer_attested": True,
        "second_reviewer_attested": True,
        "pit_source_reviewer_attested": True,
        "evidence_taxonomy_reviewer_attested": True,
        "risk_compliance_reviewer_attested": True,
        "no_active_ready_emission_attested": True,
        "no_trading_authority_attested": True,
        "no_performance_claim_attested": True,
        "no_replay_execution_attested": True,
        "attestation_result": "PASS",
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_pit_source_evidence(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "accepted_pit_universe_evidence_attached": True,
        "available_time_coverage_attached": True,
        "source_id_coverage_attached": True,
        "source_hash_coverage_attached": True,
        "revision_id_coverage_attached": True,
        "permission_class_coverage_attached": True,
        "quality_status_coverage_attached": True,
        "raw_evidence_refs_attached": True,
        "replay_evidence_bundle_ref_attached": True,
        "factor_definition_coverage_attached": True,
        "factor_observation_coverage_attached": True,
        "event_structured_coverage_attached": True,
        "company_exposure_coverage_attached": True,
        "attachment_result": "PASS",
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_taxonomy(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "uses_8_layer_taxonomy": True,
        "not_fixed_12_only": True,
        "factor_layer_metadata_attached": True,
        "trade_usage_metadata_attached": True,
        "compliance_metadata_attached": True,
        "taxonomy_result": "PASS",
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_leakage_side_effect(path: Path, overrides: dict[str, object] | None = None) -> Path:
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
        "leakage_side_effect_result": "PASS",
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_overclaim(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "pass_candidate_not_active_ready": True,
        "smoke_not_active_ready": True,
        "promotion_not_active_ready": True,
        "acceptance_not_active_ready": True,
        "active_ready_final_review_not_active_ready": True,
        "final_review_ready_not_active_input_ready": True,
        "emission_ready_review_not_active_input_ready": True,
        "ready_decision_not_active_replay_input_ready": True,
        "active_input_ready_not_replay": True,
        "active_input_ready_not_labels": True,
        "active_input_ready_not_training": True,
        "active_input_ready_not_stock_profile": True,
        "active_input_ready_not_buy_review": True,
        "active_input_ready_not_trading": True,
        "active_input_ready_not_performance_validation": True,
        "overclaim_result": "PASS",
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_candidate_manifest(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "candidate_id": "ready_candidate_001",
        "candidate_status": READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION,
        "ready_for_active_replay_input_ready_decision": True,
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "active_ready_emitted": False,
        "replay_execution_allowed": False,
        "forward_labels_allowed": False,
        "training_allowed": False,
        "stock_profile_allowed": False,
        "buy_review_allowed": False,
        "trading_allowed": False,
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path
