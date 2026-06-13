from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from quant_replay_system.active_replay_input_emission import (
    EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW,
    NO_EMISSION_INPUT,
    ActiveReplayInputEmissionSettings,
    run_active_replay_input_emission,
)


def test_no_input_produces_no_emission_input_and_writes_required_artifacts(tmp_path: Path) -> None:
    result = run_active_replay_input_emission(
        ActiveReplayInputEmissionSettings(output_dir=_emission_output_dir(tmp_path))
    )

    assert result.status == NO_EMISSION_INPUT
    assert result.workflow_stage == NO_EMISSION_INPUT
    assert result.ready_for_active_replay_input_ready_review is False
    _assert_non_active_flags(result)
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_path.is_relative_to(_emission_output_dir(tmp_path))

    for key in _required_artifact_keys():
        assert result.artifact_paths[key].exists()

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == NO_EMISSION_INPUT
    assert metadata["ready_for_active_replay_input_ready_review"] is False
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_ready_emitted"] is False
    assert "ACTIVE_REPLAY_INPUT_READY" not in json.dumps(metadata)


def test_missing_final_review_lineage_blocks_when_emission_input_exists(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    settings = ActiveReplayInputEmissionSettings(
        output_dir=settings.output_dir,
        final_review_artifact_path=tmp_path / "missing_final_review",
        final_review_health_artifact_path=settings.final_review_health_artifact_path,
        final_review_status_artifact_path=settings.final_review_status_artifact_path,
        emission_request_manifest_path=settings.emission_request_manifest_path,
        emission_authority_manifest_path=settings.emission_authority_manifest_path,
        emission_attestation_manifest_path=settings.emission_attestation_manifest_path,
        pit_source_evidence_bundle_path=settings.pit_source_evidence_bundle_path,
        taxonomy_evidence_bundle_path=settings.taxonomy_evidence_bundle_path,
        leakage_side_effect_evidence_bundle_path=settings.leakage_side_effect_evidence_bundle_path,
        overclaim_evidence_bundle_path=settings.overclaim_evidence_bundle_path,
    )

    result = run_active_replay_input_emission(settings)

    assert result.status == "EMISSION_LINEAGE_BLOCKED"
    assert result.ready_for_active_replay_input_ready_review is False
    _assert_non_active_flags(result)


@pytest.mark.parametrize(
    ("metadata_override", "expected_status"),
    [
        ({"status": "FINAL_REVIEW_REVIEW_BLOCKED"}, "EMISSION_LINEAGE_BLOCKED"),
        ({"active_replay_input_ready": True}, "EMISSION_OVERCLAIM_BLOCKED"),
        ({"active_replay_input": True}, "EMISSION_OVERCLAIM_BLOCKED"),
        ({"active_ready_emitted": True}, "EMISSION_OVERCLAIM_BLOCKED"),
        ({"forward_labels_exist": True}, "EMISSION_LEAKAGE_BLOCKED"),
        ({"forward_returns_exist": True}, "EMISSION_LEAKAGE_BLOCKED"),
        ({"training_outputs_exist": True}, "EMISSION_LEAKAGE_BLOCKED"),
        ({"model_weights_exist": True}, "EMISSION_LEAKAGE_BLOCKED"),
        ({"weights_trained": True}, "EMISSION_LEAKAGE_BLOCKED"),
        ({"stock_profile_artifacts_exist": True}, "EMISSION_LEAKAGE_BLOCKED"),
        ({"active_stock_profile_exists": True}, "EMISSION_LEAKAGE_BLOCKED"),
        ({"real_buy_review_eligible": True}, "EMISSION_LEAKAGE_BLOCKED"),
        ({"approved_for_paper": True}, "EMISSION_OVERCLAIM_BLOCKED"),
        ({"order_placed": True}, "EMISSION_SIDE_EFFECT_BLOCKED"),
        ({"message_sent": True}, "EMISSION_SIDE_EFFECT_BLOCKED"),
        ({"llm_api_called": True}, "EMISSION_SIDE_EFFECT_BLOCKED"),
        ({"external_api_called": True}, "EMISSION_SIDE_EFFECT_BLOCKED"),
        ({"cache_mutated": True}, "EMISSION_SIDE_EFFECT_BLOCKED"),
        ({"data_raw_written": True}, "EMISSION_SIDE_EFFECT_BLOCKED"),
        ({"data_processed_written": True}, "EMISSION_SIDE_EFFECT_BLOCKED"),
        ({"data_cache_written": True}, "EMISSION_SIDE_EFFECT_BLOCKED"),
        ({"current_candidates_run": True}, "EMISSION_SIDE_EFFECT_BLOCKED"),
        ({"snapshot_built": True}, "EMISSION_SIDE_EFFECT_BLOCKED"),
        ({"replay_execution_allowed": True}, "EMISSION_OVERCLAIM_BLOCKED"),
    ],
)
def test_final_review_metadata_blocks_non_ready_or_unsafe_state(
    tmp_path: Path, metadata_override: dict[str, object], expected_status: str
) -> None:
    final_review = _write_final_review_artifact(tmp_path / "final_review", metadata_override)
    settings = _happy_settings(tmp_path, final_review_artifact_path=final_review)

    result = run_active_replay_input_emission(settings)

    assert result.status == expected_status
    assert result.ready_for_active_replay_input_ready_review is False
    _assert_non_active_flags(result)
    assert result.status != "ACTIVE_REPLAY_INPUT_READY"


def test_final_review_health_not_pass_blocks(tmp_path: Path) -> None:
    settings = _happy_settings(
        tmp_path,
        final_review_health_artifact_path=_write_json(tmp_path / "final_review_health.json", {"health_status": "FAIL"}),
    )

    result = run_active_replay_input_emission(settings)

    assert result.status == "EMISSION_LINEAGE_BLOCKED"
    assert result.ready_for_active_replay_input_ready_review is False


@pytest.mark.parametrize("setting_name", ["final_review_health_artifact_path", "final_review_status_artifact_path"])
def test_missing_final_review_health_or_status_artifact_blocks(tmp_path: Path, setting_name: str) -> None:
    settings = _replace_setting(_happy_settings(tmp_path), setting_name, None)

    result = run_active_replay_input_emission(settings)

    assert result.status == "EMISSION_LINEAGE_BLOCKED"
    assert result.ready_for_active_replay_input_ready_review is False
    _assert_non_active_flags(result)


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("emission_authority_manifest_path", "EMISSION_AUTHORITY_BLOCKED"),
        ("emission_attestation_manifest_path", "EMISSION_ATTESTATION_BLOCKED"),
        ("pit_source_evidence_bundle_path", "EMISSION_EVIDENCE_BLOCKED"),
        ("taxonomy_evidence_bundle_path", "EMISSION_TAXONOMY_BLOCKED"),
        ("leakage_side_effect_evidence_bundle_path", "EMISSION_LEAKAGE_BLOCKED"),
        ("overclaim_evidence_bundle_path", "EMISSION_OVERCLAIM_BLOCKED"),
    ],
)
def test_missing_required_manifests_block_by_gate(tmp_path: Path, setting_name: str, expected_status: str) -> None:
    settings = _replace_setting(_happy_settings(tmp_path), setting_name, None)

    result = run_active_replay_input_emission(settings)

    assert result.status == expected_status
    assert result.ready_for_active_replay_input_ready_review is False
    _assert_non_active_flags(result)


@pytest.mark.parametrize(
    ("setting_name", "writer", "override", "expected_status"),
    [
        ("pit_source_evidence_bundle_path", "_write_pit_source_evidence", {"source_hash_coverage_attached": False}, "EMISSION_SOURCE_BLOCKED"),
        ("pit_source_evidence_bundle_path", "_write_pit_source_evidence", {"factor_observation_coverage_attached": False}, "EMISSION_EVIDENCE_BLOCKED"),
        ("taxonomy_evidence_bundle_path", "_write_taxonomy", {"not_fixed_12_only": False}, "EMISSION_TAXONOMY_BLOCKED"),
        ("leakage_side_effect_evidence_bundle_path", "_write_leakage_side_effect", {"no_future_labels": False}, "EMISSION_LEAKAGE_BLOCKED"),
        ("leakage_side_effect_evidence_bundle_path", "_write_leakage_side_effect", {"no_data_raw_written": False}, "EMISSION_SIDE_EFFECT_BLOCKED"),
        ("overclaim_evidence_bundle_path", "_write_overclaim", {"final_review_ready_not_active_input_ready": False}, "EMISSION_OVERCLAIM_BLOCKED"),
    ],
)
def test_manifest_gate_failures_block(
    tmp_path: Path, setting_name: str, writer: str, override: dict[str, object], expected_status: str
) -> None:
    replacement = globals()[writer](tmp_path / f"{setting_name}.json", override)
    settings = _replace_setting(_happy_settings(tmp_path), setting_name, replacement)

    result = run_active_replay_input_emission(settings)

    assert result.status == expected_status
    assert result.ready_for_active_replay_input_ready_review is False
    _assert_non_active_flags(result)


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    settings = ActiveReplayInputEmissionSettings(output_dir=tmp_path / "unsafe")

    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_active_replay_input_emission(settings)


def test_happy_path_reaches_review_ready_only(tmp_path: Path) -> None:
    result = run_active_replay_input_emission(_happy_settings(tmp_path))

    assert result.status == EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW
    assert result.workflow_stage == EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW
    assert result.ready_for_active_replay_input_ready_review is True
    _assert_non_active_flags(result)
    assert result.blocker_count == 0
    assert result.overclaim_guard_pass_count == result.overclaim_guard_total_count
    assert result.status != "ACTIVE_REPLAY_INPUT_READY"

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW
    assert metadata["ready_for_active_replay_input_ready_review"] is True
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_ready_emitted"] is False
    assert metadata["status"] != "ACTIVE_REPLAY_INPUT_READY"

    candidate = json.loads(
        result.artifact_paths["active_replay_input_ready_review_candidate"].read_text(encoding="utf-8")
    )
    assert candidate["ready_for_active_replay_input_ready_review"] is True
    assert candidate["active_replay_input_ready"] is False
    assert candidate["active_replay_input"] is False
    assert candidate["active_ready_emitted"] is False
    assert candidate["status"] != "ACTIVE_REPLAY_INPUT_READY"

    report = result.artifact_paths["emission_report"].read_text(encoding="utf-8")
    assert "not ACTIVE_REPLAY_INPUT_READY" in report
    assert "not active input readiness" in report
    assert "does not run replay" in report

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_cli_active_replay_input_emission_runs_without_active_ready_claim(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "active-replay-input-emission",
            "--final-review-artifact-path",
            str(settings.final_review_artifact_path),
            "--final-review-health-artifact-path",
            str(settings.final_review_health_artifact_path),
            "--final-review-status-artifact-path",
            str(settings.final_review_status_artifact_path),
            "--emission-request-manifest-path",
            str(settings.emission_request_manifest_path),
            "--emission-authority-manifest-path",
            str(settings.emission_authority_manifest_path),
            "--emission-attestation-manifest-path",
            str(settings.emission_attestation_manifest_path),
            "--pit-source-evidence-bundle-path",
            str(settings.pit_source_evidence_bundle_path),
            "--taxonomy-evidence-bundle-path",
            str(settings.taxonomy_evidence_bundle_path),
            "--leakage-side-effect-evidence-bundle-path",
            str(settings.leakage_side_effect_evidence_bundle_path),
            "--overclaim-evidence-bundle-path",
            str(settings.overclaim_evidence_bundle_path),
            "--output-dir",
            str(settings.output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "emission_run_id:" in completed.stdout
    assert f"status: {EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW}" in completed.stdout
    assert "ready_for_active_replay_input_ready_review: True" in completed.stdout
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


def test_no_index_health_status_research_status_checkpoint_or_project_source_added(tmp_path: Path) -> None:
    help_text = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout

    assert "active-replay-input-emission" in help_text
    assert "active-replay-input-emission-index" not in help_text
    assert "active-replay-input-emission-health" not in help_text
    assert "active-replay-input-emission-status" not in help_text

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "research-status",
            "--root",
            str(tmp_path / "outputs" / "reports"),
            "--output-dir",
            str(tmp_path / "dashboard"),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    assert "active_replay_input_emission" not in completed.stdout
    assert not Path("docs/project_sources").exists()
    assert not Path("docs/release_checkpoint_v1.35.0.md").exists()


def _assert_non_active_flags(result) -> None:
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
        "emission_report",
        "emission_precondition_results",
        "emission_authority_results",
        "final_review_lineage_results",
        "emission_attestation_results",
        "pit_source_evidence_results",
        "taxonomy_evidence_results",
        "leakage_side_effect_guard_results",
        "overclaim_guard_results",
        "active_replay_input_ready_review_candidate",
        "recommended_next_task",
    ]


def _emission_output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "active_replay_input_emission_v0_1"


def _happy_settings(tmp_path: Path, **overrides: Path | None) -> ActiveReplayInputEmissionSettings:
    def default_path(name: str, writer):
        return overrides[name] if name in overrides else writer()

    values = {
        "output_dir": _emission_output_dir(tmp_path),
        "final_review_artifact_path": default_path(
            "final_review_artifact_path", lambda: _write_final_review_artifact(tmp_path / "final_review")
        ),
        "final_review_health_artifact_path": default_path(
            "final_review_health_artifact_path",
            lambda: _write_json(tmp_path / "final_review_health.json", {"health_status": "PASS"}),
        ),
        "final_review_status_artifact_path": default_path(
            "final_review_status_artifact_path",
            lambda: _write_json(
                tmp_path / "final_review_status.json",
                {
                    "status": "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW",
                    "workflow_stage": "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW",
                    "ready_for_emission_review": True,
                    "active_replay_input_ready": False,
                    "active_replay_input": False,
                    "active_ready_emitted": False,
                },
            ),
        ),
        "emission_request_manifest_path": default_path(
            "emission_request_manifest_path", lambda: _write_emission_request(tmp_path / "emission_request.json")
        ),
        "emission_authority_manifest_path": default_path(
            "emission_authority_manifest_path", lambda: _write_authority(tmp_path / "authority.json")
        ),
        "emission_attestation_manifest_path": default_path(
            "emission_attestation_manifest_path", lambda: _write_attestation(tmp_path / "attestation.json")
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
    }
    values.update(overrides)
    return ActiveReplayInputEmissionSettings(**values)


def _replace_setting(
    settings: ActiveReplayInputEmissionSettings, field_name: str, value: Path | None
) -> ActiveReplayInputEmissionSettings:
    values = settings.__dict__.copy()
    values[field_name] = value
    return ActiveReplayInputEmissionSettings(**values)


def _write_final_review_artifact(path: Path, overrides: dict[str, object] | None = None) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    payload = {
        "final_review_run_id": "final_review_001",
        "status": "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW",
        "workflow_stage": "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW",
        "ready_for_emission_review": True,
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
    (path / "final_review_metadata.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_emission_request(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "emission_request_id": "emission_request_001",
        "requested_status": "EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW",
        "requested_by": "fixture_reviewer",
        "requested_at": "2024-04-02T18:00:00+08:00",
        "request_reason": "fixture review-only emission precondition check",
        "allow_active_replay_input_ready_emission": False,
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
        "emission_authority_id": "authority_001",
        "primary_reviewer": "primary_fixture_reviewer",
        "second_reviewer": "second_fixture_reviewer",
        "pit_source_reviewer": "pit_fixture_reviewer",
        "evidence_taxonomy_reviewer": "evidence_fixture_reviewer",
        "risk_compliance_reviewer": "risk_fixture_reviewer",
        "system_operator": "operator_fixture",
        "strategy_owner": "owner_fixture",
        "authority_scope": "review-only active-ready emission review",
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


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path
