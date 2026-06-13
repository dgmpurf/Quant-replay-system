from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.active_replay_input_acceptance import (
    ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW,
    NO_ACCEPTANCE_INPUT,
    ActiveReplayInputAcceptanceSettings,
    run_active_replay_input_acceptance,
)


def test_no_input_returns_no_acceptance_input_and_writes_required_artifacts(tmp_path: Path) -> None:
    result = run_active_replay_input_acceptance(
        ActiveReplayInputAcceptanceSettings(output_dir=_acceptance_output_dir(tmp_path))
    )

    assert result.status == NO_ACCEPTANCE_INPUT
    assert result.ready_for_active_ready_review is False
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.active_ready_emitted is False
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_path.is_relative_to(_acceptance_output_dir(tmp_path))

    for key in [
        "metadata",
        "acceptance_report",
        "acceptance_precondition_results",
        "reviewer_authority_results",
        "manual_attestation_results",
        "second_review_results",
        "red_team_review_results",
        "lineage_acceptance_results",
        "pit_acceptance_results",
        "source_acceptance_results",
        "leakage_acceptance_results",
        "side_effect_acceptance_results",
        "overclaim_guard_report",
        "recommended_next_task",
    ]:
        assert result.artifact_paths[key].exists()

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == NO_ACCEPTANCE_INPUT
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_ready_emitted"] is False
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert "ACTIVE_REPLAY_INPUT_READY" not in json.dumps(metadata)


def test_missing_promotion_lineage_blocks(tmp_path: Path) -> None:
    result = run_active_replay_input_acceptance(
        ActiveReplayInputAcceptanceSettings(
            output_dir=_acceptance_output_dir(tmp_path),
            promotion_artifact=tmp_path / "missing_promotion",
        )
    )

    assert result.status == "ACCEPTANCE_LINEAGE_BLOCKED"
    assert result.ready_for_active_ready_review is False
    assert result.active_replay_input_ready is False


@pytest.mark.parametrize(
    ("field", "value", "expected_status"),
    [
        ("status", "NO_PROMOTION_INPUT", "ACCEPTANCE_LINEAGE_BLOCKED"),
        ("ready_for_human_review", False, "ACCEPTANCE_LINEAGE_BLOCKED"),
        ("active_replay_input_ready", True, "ACCEPTANCE_LEAKAGE_BLOCKED"),
        ("active_replay_input", True, "ACCEPTANCE_SIDE_EFFECT_BLOCKED"),
        ("active_ready_emitted", True, "ACCEPTANCE_LEAKAGE_BLOCKED"),
        ("forward_labels_exist", True, "ACCEPTANCE_LEAKAGE_BLOCKED"),
        ("weights_trained", True, "ACCEPTANCE_LEAKAGE_BLOCKED"),
        ("active_stock_profile_exists", True, "ACCEPTANCE_LEAKAGE_BLOCKED"),
        ("real_buy_review_eligible", True, "ACCEPTANCE_LEAKAGE_BLOCKED"),
    ],
)
def test_promotion_metadata_blocks_unsafe_or_non_ready_state(
    tmp_path: Path, field: str, value: object, expected_status: str
) -> None:
    promotion = _write_promotion_artifact(tmp_path / "promotion", {field: value})
    settings = _happy_settings(tmp_path, promotion)

    result = run_active_replay_input_acceptance(settings)

    assert result.status == expected_status
    assert result.ready_for_active_ready_review is False
    assert result.active_ready_emitted is False


def test_promotion_health_not_pass_blocks_when_health_artifact_is_provided(tmp_path: Path) -> None:
    promotion = _write_promotion_artifact(tmp_path / "promotion")
    health = _write_json(tmp_path / "promotion_health.json", {"health_status": "FAIL"})
    settings = _happy_settings(tmp_path, promotion, promotion_health_artifact=health)

    result = run_active_replay_input_acceptance(settings)

    assert result.status == "ACCEPTANCE_LINEAGE_BLOCKED"
    assert result.ready_for_active_ready_review is False


def test_missing_acceptance_request_blocks(tmp_path: Path) -> None:
    promotion = _write_promotion_artifact(tmp_path / "promotion")
    settings = _happy_settings(tmp_path, promotion, acceptance_request_manifest=None)

    result = run_active_replay_input_acceptance(settings)

    assert result.status == "ACCEPTANCE_REVIEW_BLOCKED"
    assert result.ready_for_active_ready_review is False


def test_unsafe_acceptance_request_side_effect_blocks(tmp_path: Path) -> None:
    promotion = _write_promotion_artifact(tmp_path / "promotion")
    request = _write_acceptance_request(tmp_path / "acceptance_request.json", promotion, {"cache_mutated": True})
    settings = _happy_settings(tmp_path, promotion, acceptance_request_manifest=request)

    result = run_active_replay_input_acceptance(settings)

    assert result.status == "ACCEPTANCE_SIDE_EFFECT_BLOCKED"
    assert result.cache_mutated is False
    assert result.ready_for_active_ready_review is False


def test_reviewer_authority_not_accepted_blocks(tmp_path: Path) -> None:
    promotion = _write_promotion_artifact(tmp_path / "promotion")
    authority = _write_reviewer_authority(tmp_path / "authority.json", {"authority_result": "REJECTED"})
    settings = _happy_settings(tmp_path, promotion, reviewer_authority_manifest=authority)

    result = run_active_replay_input_acceptance(settings)

    assert result.status == "ACCEPTANCE_AUTHORITY_BLOCKED"
    assert result.ready_for_active_ready_review is False


def test_manual_attestation_false_blocks(tmp_path: Path) -> None:
    promotion = _write_promotion_artifact(tmp_path / "promotion")
    attestation = _write_manual_attestation(tmp_path / "attestation.json", {"source_permission_attested": False})
    settings = _happy_settings(tmp_path, promotion, manual_attestation_manifest=attestation)

    result = run_active_replay_input_acceptance(settings)

    assert result.status == "ACCEPTANCE_ATTESTATION_BLOCKED"
    gates = pd.read_csv(result.artifact_paths["manual_attestation_results"], dtype=str)
    assert "source_permission_attested" in set(gates["gate_name"])
    assert "False" in set(gates["passed"])


def test_missing_second_review_and_red_team_block(tmp_path: Path) -> None:
    promotion = _write_promotion_artifact(tmp_path / "promotion")
    missing_second = _happy_settings(tmp_path, promotion, second_review_manifest=None)
    missing_red_team = _happy_settings(tmp_path, promotion, red_team_review_manifest=None)

    second_result = run_active_replay_input_acceptance(missing_second)
    red_team_result = run_active_replay_input_acceptance(missing_red_team)

    assert second_result.status == "ACCEPTANCE_SECOND_REVIEW_BLOCKED"
    assert red_team_result.status == "ACCEPTANCE_RED_TEAM_BLOCKED"


def test_happy_path_returns_ready_for_active_ready_review_only(tmp_path: Path) -> None:
    promotion = _write_promotion_artifact(tmp_path / "promotion")

    result = run_active_replay_input_acceptance(_happy_settings(tmp_path, promotion))

    assert result.status == ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW
    assert result.ready_for_active_ready_review is True
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
    assert metadata["status"] == ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW
    assert metadata["ready_for_active_ready_review"] is True
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_ready_emitted"] is False
    assert "ACTIVE_REPLAY_INPUT_READY" not in json.dumps(metadata)

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_cli_command_runs_without_active_ready_claim(tmp_path: Path) -> None:
    promotion = _write_promotion_artifact(tmp_path / "promotion")
    settings = _happy_settings(tmp_path, promotion)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "active-replay-input-acceptance",
            "--promotion-artifact",
            str(settings.promotion_artifact),
            "--promotion-health-artifact",
            str(settings.promotion_health_artifact),
            "--promotion-status-artifact",
            str(settings.promotion_status_artifact),
            "--acceptance-request-manifest",
            str(settings.acceptance_request_manifest),
            "--reviewer-authority-manifest",
            str(settings.reviewer_authority_manifest),
            "--manual-attestation-manifest",
            str(settings.manual_attestation_manifest),
            "--second-review-manifest",
            str(settings.second_review_manifest),
            "--red-team-review-manifest",
            str(settings.red_team_review_manifest),
            "--output-dir",
            str(_acceptance_output_dir(tmp_path)),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "acceptance_run_id:" in completed.stdout
    assert f"status: {ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW}" in completed.stdout
    assert "ready_for_active_ready_review: True" in completed.stdout
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
    assert "active-replay-input-acceptance" in help_text
    assert "active-replay-input-acceptance-index" not in help_text
    assert "active-replay-input-acceptance-health" not in help_text
    assert "active-replay-input-acceptance-status" not in help_text
    assert not Path("docs/project_sources").exists()


def _acceptance_output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "active_replay_input_acceptance_v0_1"


def _happy_settings(
    tmp_path: Path,
    promotion: Path,
    **overrides: Path | None,
) -> ActiveReplayInputAcceptanceSettings:
    def default_path(name: str, writer):
        return overrides[name] if name in overrides else writer()

    values = {
        "output_dir": _acceptance_output_dir(tmp_path),
        "promotion_artifact": promotion,
        "promotion_health_artifact": default_path(
            "promotion_health_artifact",
            lambda: _write_json(tmp_path / "promotion_health.json", {"health_status": "PASS"}),
        ),
        "promotion_status_artifact": default_path(
            "promotion_status_artifact",
            lambda: _write_json(
                tmp_path / "promotion_status.json",
                {"status": "PROMOTION_READY_FOR_HUMAN_REVIEW", "ready_for_human_review": True},
            ),
        ),
        "acceptance_request_manifest": default_path(
            "acceptance_request_manifest",
            lambda: _write_acceptance_request(tmp_path / "acceptance_request.json", promotion),
        ),
        "reviewer_authority_manifest": default_path(
            "reviewer_authority_manifest",
            lambda: _write_reviewer_authority(tmp_path / "authority.json"),
        ),
        "manual_attestation_manifest": default_path(
            "manual_attestation_manifest",
            lambda: _write_manual_attestation(tmp_path / "attestation.json"),
        ),
        "second_review_manifest": default_path(
            "second_review_manifest",
            lambda: _write_second_review(tmp_path / "second_review.json"),
        ),
        "red_team_review_manifest": default_path(
            "red_team_review_manifest",
            lambda: _write_red_team_review(tmp_path / "red_team.json"),
        ),
    }
    values.update(overrides)
    return ActiveReplayInputAcceptanceSettings(**values)


def _write_promotion_artifact(path: Path, overrides: dict[str, object] | None = None) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    metadata = {
        "promotion_run_id": "promotion_001",
        "status": "PROMOTION_READY_FOR_HUMAN_REVIEW",
        "workflow_stage": "PROMOTION_READY_FOR_HUMAN_REVIEW",
        "ready_for_human_review": True,
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "active_ready_emitted": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
        "approval_applied": False,
        "order_placed": False,
        "llm_api_called": False,
        "external_api_called": False,
        "cache_mutated": False,
        "current_candidates_run": False,
        "snapshot_built": False,
        "signal_semantics_changed": False,
        "report_only": True,
        "diagnostic_only": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "artifact_path": str(path),
    }
    metadata.update(overrides or {})
    (path / "promotion_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_acceptance_request(
    path: Path, promotion: Path, overrides: dict[str, object] | None = None
) -> Path:
    payload = {
        "acceptance_request_id": "acceptance_request_001",
        "requested_by": "fixture_reviewer",
        "requested_at": "2024-04-02T17:00:00+08:00",
        "request_reason": "fixture report-only acceptance",
        "promotion_artifact_ref": str(promotion),
        "requested_status": "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW",
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
        "llm_api_called": False,
        "external_api_called": False,
        "cache_mutated": False,
        "current_candidates_run": False,
        "snapshot_built": False,
        "signal_semantics_changed": False,
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_reviewer_authority(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "reviewer_authority_id": "authority_001",
        "primary_reviewer": "primary_fixture_reviewer",
        "primary_reviewer_role": "research_governance_reviewer",
        "second_reviewer": "second_fixture_reviewer",
        "red_team_reviewer": "red_team_fixture_reviewer",
        "data_source_reviewer": "source_fixture_reviewer",
        "strategy_owner": "strategy_fixture_owner",
        "authority_scope": "review-only acceptance for active-ready review",
        "authority_result": "ACCEPTED_FOR_REVIEW_ONLY",
        "report_only": True,
        "diagnostic_only": True,
        "notes": "fixture only",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_manual_attestation(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "pit_validity_attested": True,
        "source_permission_attested": True,
        "source_hash_revision_attested": True,
        "no_future_labels_attested": True,
        "no_training_leakage_attested": True,
        "no_stock_profile_leakage_attested": True,
        "no_buy_review_eligibility_attested": True,
        "no_active_ready_attested": True,
        "no_side_effects_attested": True,
        "no_trading_authorization_attested": True,
        "report_only": True,
        "diagnostic_only": True,
        "attestation_result": "ACCEPTED_FOR_REVIEW_ONLY",
        "notes": "fixture only",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_second_review(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "second_review_id": "second_review_001",
        "reviewer": "second_fixture_reviewer",
        "reviewed_at": "2024-04-02T17:10:00+08:00",
        "pit_reviewed": True,
        "source_reviewed": True,
        "evidence_reviewed": True,
        "leakage_reviewed": True,
        "side_effect_reviewed": True,
        "overclaim_wording_reviewed": True,
        "review_result": "ACCEPTED_FOR_REVIEW_ONLY",
        "report_only": True,
        "diagnostic_only": True,
        "notes": "fixture only",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_red_team_review(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "red_team_review_id": "red_team_001",
        "reviewer": "red_team_fixture_reviewer",
        "reviewed_at": "2024-04-02T17:20:00+08:00",
        "attempted_to_find_future_leakage": True,
        "attempted_to_find_permission_gap": True,
        "attempted_to_find_overclaim": True,
        "attempted_to_find_side_effect_risk": True,
        "red_team_result": "ACCEPTED_FOR_REVIEW_ONLY",
        "report_only": True,
        "diagnostic_only": True,
        "notes": "fixture only",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path
