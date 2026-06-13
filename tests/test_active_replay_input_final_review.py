from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from quant_replay_system.active_replay_input_final_review import (
    FINAL_REVIEW_READY_FOR_EMISSION_REVIEW,
    NO_FINAL_REVIEW_PACKAGE,
    ActiveReplayInputFinalReviewSettings,
    run_active_replay_input_final_review,
)


def test_no_input_returns_no_final_review_package_and_writes_required_artifacts(tmp_path: Path) -> None:
    result = run_active_replay_input_final_review(
        ActiveReplayInputFinalReviewSettings(output_dir=_final_review_output_dir(tmp_path))
    )

    assert result.status == NO_FINAL_REVIEW_PACKAGE
    assert result.ready_for_emission_review is False
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.active_ready_emitted is False
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_path.is_relative_to(_final_review_output_dir(tmp_path))

    for key in _required_artifact_keys():
        assert result.artifact_paths[key].exists()

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == NO_FINAL_REVIEW_PACKAGE
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_ready_emitted"] is False
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert "ACTIVE_REPLAY_INPUT_READY" not in json.dumps(metadata)


def test_missing_active_ready_lineage_blocks_when_package_is_present(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    settings = ActiveReplayInputFinalReviewSettings(
        output_dir=settings.output_dir,
        active_ready_artifact=tmp_path / "missing_active_ready",
        active_ready_health_artifact=settings.active_ready_health_artifact,
        active_ready_status_artifact=settings.active_ready_status_artifact,
        final_review_package_manifest=settings.final_review_package_manifest,
        final_review_authority_manifest=settings.final_review_authority_manifest,
        final_review_attestation_manifest=settings.final_review_attestation_manifest,
        pit_source_evidence_attachment_bundle=settings.pit_source_evidence_attachment_bundle,
        taxonomy_attachment_bundle=settings.taxonomy_attachment_bundle,
        leakage_side_effect_evidence_bundle=settings.leakage_side_effect_evidence_bundle,
        overclaim_evidence_bundle=settings.overclaim_evidence_bundle,
        emission_request_manifest=settings.emission_request_manifest,
    )

    result = run_active_replay_input_final_review(settings)

    assert result.status == "FINAL_REVIEW_LINEAGE_BLOCKED"
    assert result.ready_for_emission_review is False
    assert result.active_replay_input_ready is False


@pytest.mark.parametrize(
    ("field", "value", "expected_status"),
    [
        ("status", "ACTIVE_READY_PIT_BLOCKED", "FINAL_REVIEW_LINEAGE_BLOCKED"),
        ("health_status", "FAIL", "FINAL_REVIEW_LINEAGE_BLOCKED"),
        ("active_replay_input_ready", True, "FINAL_REVIEW_OVERCLAIM_BLOCKED"),
        ("active_replay_input", True, "FINAL_REVIEW_OVERCLAIM_BLOCKED"),
        ("active_ready_emitted", True, "FINAL_REVIEW_OVERCLAIM_BLOCKED"),
        ("forward_labels_exist", True, "FINAL_REVIEW_LEAKAGE_BLOCKED"),
        ("weights_trained", True, "FINAL_REVIEW_LEAKAGE_BLOCKED"),
        ("active_stock_profile_exists", True, "FINAL_REVIEW_LEAKAGE_BLOCKED"),
        ("real_buy_review_eligible", True, "FINAL_REVIEW_OVERCLAIM_BLOCKED"),
    ],
)
def test_active_ready_metadata_blocks_non_final_review_or_unsafe_state(
    tmp_path: Path, field: str, value: object, expected_status: str
) -> None:
    settings = _happy_settings(tmp_path, active_ready_override={field: value})

    result = run_active_replay_input_final_review(settings)

    assert result.status == expected_status
    assert result.ready_for_emission_review is False
    assert result.active_replay_input_ready is False
    assert "ACTIVE_REPLAY_INPUT_READY" not in result.status


@pytest.mark.parametrize(
    ("manifest_name", "override", "expected_status"),
    [
        (
            "final_review_package_manifest",
            {"active_replay_input_ready": True},
            "FINAL_REVIEW_OVERCLAIM_BLOCKED",
        ),
        (
            "final_review_authority_manifest",
            {"authority_result": "REJECTED"},
            "FINAL_REVIEW_AUTHORITY_BLOCKED",
        ),
        (
            "final_review_attestation_manifest",
            {"no_replay_execution_attested": False},
            "FINAL_REVIEW_ATTESTATION_BLOCKED",
        ),
        (
            "pit_source_evidence_attachment_bundle",
            {"source_hash_coverage_attached": False},
            "FINAL_REVIEW_SOURCE_BLOCKED",
        ),
        (
            "taxonomy_attachment_bundle",
            {"not_fixed_12_only": False},
            "FINAL_REVIEW_TAXONOMY_BLOCKED",
        ),
        (
            "leakage_side_effect_evidence_bundle",
            {"no_future_labels": False},
            "FINAL_REVIEW_LEAKAGE_BLOCKED",
        ),
        (
            "leakage_side_effect_evidence_bundle",
            {"no_data_raw_written": False},
            "FINAL_REVIEW_SIDE_EFFECT_BLOCKED",
        ),
        (
            "overclaim_evidence_bundle",
            {"final_review_ready_not_active_input_ready": False},
            "FINAL_REVIEW_OVERCLAIM_BLOCKED",
        ),
        (
            "emission_request_manifest",
            {"allow_active_replay_input_ready_emission": True},
            "FINAL_REVIEW_REVIEW_BLOCKED",
        ),
    ],
)
def test_manifest_gate_failures_block_by_gate_group(
    tmp_path: Path, manifest_name: str, override: dict[str, object], expected_status: str
) -> None:
    settings = _happy_settings(tmp_path)
    replacement = _manifest_writer(manifest_name)(tmp_path / f"{manifest_name}.json", override)
    settings = _replace_setting(settings, manifest_name, replacement)

    result = run_active_replay_input_final_review(settings)

    assert result.status == expected_status
    assert result.ready_for_emission_review is False
    assert result.active_replay_input_ready is False


def test_happy_path_returns_ready_for_emission_review_only(tmp_path: Path) -> None:
    result = run_active_replay_input_final_review(_happy_settings(tmp_path))

    assert result.status == FINAL_REVIEW_READY_FOR_EMISSION_REVIEW
    assert result.workflow_stage == FINAL_REVIEW_READY_FOR_EMISSION_REVIEW
    assert result.ready_for_emission_review is True
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.active_ready_emitted is False
    assert result.forward_labels_exist is False
    assert result.weights_trained is False
    assert result.active_stock_profile_exists is False
    assert result.real_buy_review_eligible is False
    assert result.approval_applied is False
    assert result.overclaim_guard_pass_count == result.overclaim_guard_total_count
    assert "ACTIVE_REPLAY_INPUT_READY" not in result.status

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == FINAL_REVIEW_READY_FOR_EMISSION_REVIEW
    assert metadata["ready_for_emission_review"] is True
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_ready_emitted"] is False
    assert "ACTIVE_REPLAY_INPUT_READY" not in json.dumps(metadata)

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_cli_command_runs_without_active_replay_input_ready_claim(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "active-replay-input-final-review",
            "--active-ready-artifact",
            str(settings.active_ready_artifact),
            "--active-ready-health-artifact",
            str(settings.active_ready_health_artifact),
            "--active-ready-status-artifact",
            str(settings.active_ready_status_artifact),
            "--final-review-package-manifest",
            str(settings.final_review_package_manifest),
            "--final-review-authority-manifest",
            str(settings.final_review_authority_manifest),
            "--final-review-attestation-manifest",
            str(settings.final_review_attestation_manifest),
            "--pit-source-evidence-attachment-bundle",
            str(settings.pit_source_evidence_attachment_bundle),
            "--taxonomy-attachment-bundle",
            str(settings.taxonomy_attachment_bundle),
            "--leakage-side-effect-evidence-bundle",
            str(settings.leakage_side_effect_evidence_bundle),
            "--overclaim-evidence-bundle",
            str(settings.overclaim_evidence_bundle),
            "--emission-request-manifest",
            str(settings.emission_request_manifest),
            "--output-dir",
            str(_final_review_output_dir(tmp_path)),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "final_review_run_id:" in completed.stdout
    assert f"status: {FINAL_REVIEW_READY_FOR_EMISSION_REVIEW}" in completed.stdout
    assert "ready_for_emission_review: True" in completed.stdout
    assert "active_replay_input_ready: False" in completed.stdout
    assert "active_replay_input: False" in completed.stdout
    assert "active_ready_emitted: False" in completed.stdout
    assert "ACTIVE_REPLAY_INPUT_READY" not in completed.stdout

    help_text = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout
    assert "active-replay-input-final-review" in help_text
    assert "active-replay-input-final-review-index" not in help_text
    assert "active-replay-input-final-review-health" not in help_text
    assert "active-replay-input-final-review-status" not in help_text
    assert not Path("docs/project_sources").exists()


def _final_review_output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "active_replay_input_final_review_v0_1"


def _required_artifact_keys() -> list[str]:
    return [
        "metadata",
        "final_review_report",
        "final_review_package_manifest_results",
        "active_ready_lineage_results",
        "final_reviewer_authority_results",
        "final_reviewer_attestation_results",
        "pit_source_evidence_attachment_results",
        "taxonomy_attachment_results",
        "leakage_side_effect_evidence_results",
        "overclaim_guard_results",
        "emission_readiness_results",
        "recommended_next_task",
    ]


def _happy_settings(
    tmp_path: Path,
    *,
    active_ready_override: dict[str, object] | None = None,
) -> ActiveReplayInputFinalReviewSettings:
    active_ready = _write_active_ready_artifact(tmp_path / "active_ready", active_ready_override)
    return ActiveReplayInputFinalReviewSettings(
        output_dir=_final_review_output_dir(tmp_path),
        active_ready_artifact=active_ready,
        active_ready_health_artifact=_write_json(tmp_path / "active_ready_health.json", {"health_status": "PASS"}),
        active_ready_status_artifact=_write_json(
            tmp_path / "active_ready_status.json",
            {
                "status": "ACTIVE_READY_READY_FOR_FINAL_REVIEW",
                "health_status": "PASS",
                "workflow_stage": "ACTIVE_READY_READY_FOR_FINAL_REVIEW",
                "ready_for_final_review": True,
                "active_replay_input_ready": False,
                "active_replay_input": False,
                "active_ready_emitted": False,
            },
        ),
        final_review_package_manifest=_write_package(tmp_path / "final_review_package.json"),
        final_review_authority_manifest=_write_authority(tmp_path / "final_review_authority.json"),
        final_review_attestation_manifest=_write_attestation(tmp_path / "final_review_attestation.json"),
        pit_source_evidence_attachment_bundle=_write_pit_source_bundle(tmp_path / "pit_source_bundle.json"),
        taxonomy_attachment_bundle=_write_taxonomy(tmp_path / "taxonomy.json"),
        leakage_side_effect_evidence_bundle=_write_leakage_side_effect(tmp_path / "leakage_side_effect.json"),
        overclaim_evidence_bundle=_write_overclaim(tmp_path / "overclaim.json"),
        emission_request_manifest=_write_emission_request(tmp_path / "emission_request.json"),
    )


def _replace_setting(
    settings: ActiveReplayInputFinalReviewSettings,
    name: str,
    path: Path,
) -> ActiveReplayInputFinalReviewSettings:
    values = settings.__dict__ | {name: path}
    return ActiveReplayInputFinalReviewSettings(**values)


def _write_active_ready_artifact(path: Path, overrides: dict[str, object] | None = None) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    payload = {
        "active_ready_run_id": "active-ready-ready",
        "status": "ACTIVE_READY_READY_FOR_FINAL_REVIEW",
        "workflow_stage": "ACTIVE_READY_READY_FOR_FINAL_REVIEW",
        "health_status": "PASS",
        "ready_for_final_review": True,
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "active_ready_emitted": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
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
        "signal_semantics_changed": False,
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update(overrides or {})
    _write_json(path / "active_ready_metadata.json", payload)
    return path


def _write_package(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "final_review_package_id": "pkg-1",
        "requested_by": "reviewer",
        "requested_at": "2026-06-13T00:00:00Z",
        "package_reason": "review final package",
        "active_ready_artifact_ref": "active-ready-ready",
        "requested_status": "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW",
        "report_only": True,
        "diagnostic_only": True,
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "active_ready_emitted": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
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
        "signal_semantics_changed": False,
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_authority(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "final_review_authority_id": "auth-1",
        "primary_reviewer": "primary",
        "second_reviewer": "second",
        "pit_source_reviewer": "pit",
        "evidence_taxonomy_reviewer": "taxonomy",
        "risk_compliance_reviewer": "risk",
        "system_operator": "operator",
        "strategy_owner": "owner",
        "authority_scope": "review-only final-review evidence package",
        "authority_result": "PASS",
        "report_only": True,
        "diagnostic_only": True,
        "notes": "no trading authority",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_attestation(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "final_review_attestation_id": "attest-1",
        "primary_reviewer_attested": True,
        "second_reviewer_attested": True,
        "pit_source_reviewer_attested": True,
        "evidence_taxonomy_reviewer_attested": True,
        "risk_compliance_reviewer_attested": True,
        "no_trading_authority_attested": True,
        "no_performance_claim_attested": True,
        "no_replay_execution_attested": True,
        "attestation_result": "PASS",
        "report_only": True,
        "diagnostic_only": True,
        "notes": "review only",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_pit_source_bundle(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "pit_source_evidence_bundle_id": "pit-source-1",
        "pit_universe_evidence_attached": True,
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
        "notes": "attached",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_taxonomy(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "taxonomy_attachment_id": "taxonomy-1",
        "uses_8_layer_taxonomy": True,
        "not_fixed_12_only": True,
        "factor_layer_metadata_attached": True,
        "trade_usage_metadata_attached": True,
        "compliance_metadata_attached": True,
        "taxonomy_result": "PASS",
        "report_only": True,
        "diagnostic_only": True,
        "notes": "8-layer",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_leakage_side_effect(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "leakage_side_effect_evidence_id": "leakage-1",
        "no_future_labels": True,
        "no_forward_returns": True,
        "no_training_outputs": True,
        "no_model_weights": True,
        "no_stock_profile_artifacts": True,
        "no_buy_review_eligibility": True,
        "no_approved_for_paper": True,
        "no_order_placed": True,
        "no_message_sent": True,
        "no_broker_api_called": True,
        "no_llm_api_called": True,
        "no_external_api_called": True,
        "no_cache_mutated": True,
        "no_data_raw_written": True,
        "no_data_processed_written": True,
        "no_data_cache_written": True,
        "no_current_candidates_run": True,
        "no_snapshot_built": True,
        "no_signal_semantics_changed": True,
        "leakage_side_effect_result": "PASS",
        "report_only": True,
        "diagnostic_only": True,
        "notes": "negative evidence",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_overclaim(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "overclaim_evidence_id": "overclaim-1",
        "pass_candidate_not_active_ready": True,
        "smoke_not_active_ready": True,
        "promotion_not_active_ready": True,
        "acceptance_not_active_ready": True,
        "active_ready_final_review_not_active_ready": True,
        "final_review_ready_not_active_input_ready": True,
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
        "notes": "guards",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_emission_request(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "emission_request_id": "emission-1",
        "requested_status": "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW",
        "requested_by": "reviewer",
        "request_reason": "first implementation stops at emission review",
        "report_only": True,
        "diagnostic_only": True,
        "allow_active_replay_input_ready_emission": False,
        "allow_active_replay_input_creation": False,
        "allow_replay_execution": False,
        "allow_forward_labels": False,
        "allow_training": False,
        "allow_stock_profile": False,
        "allow_buy_review": False,
        "allow_trading": False,
        "notes": "no emission",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _manifest_writer(name: str):
    return {
        "final_review_package_manifest": _write_package,
        "final_review_authority_manifest": _write_authority,
        "final_review_attestation_manifest": _write_attestation,
        "pit_source_evidence_attachment_bundle": _write_pit_source_bundle,
        "taxonomy_attachment_bundle": _write_taxonomy,
        "leakage_side_effect_evidence_bundle": _write_leakage_side_effect,
        "overclaim_evidence_bundle": _write_overclaim,
        "emission_request_manifest": _write_emission_request,
    }[name]


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path
