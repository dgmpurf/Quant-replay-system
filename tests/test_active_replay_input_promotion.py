from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.active_replay_input_promotion import (
    PROMOTION_READY_FOR_HUMAN_REVIEW,
    ActiveReplayInputPromotionSettings,
    run_active_replay_input_promotion,
)


def test_no_input_returns_no_promotion_input_and_writes_required_artifacts(tmp_path: Path) -> None:
    result = run_active_replay_input_promotion(
        ActiveReplayInputPromotionSettings(output_dir=_promotion_output_dir(tmp_path))
    )

    assert result.status == "NO_PROMOTION_INPUT"
    assert result.ready_for_human_review is False
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_path.is_relative_to(_promotion_output_dir(tmp_path))

    for key in [
        "metadata",
        "promotion_report",
        "promotion_precondition_results",
        "human_review_gate_results",
        "artifact_lineage_results",
        "pit_coverage_results",
        "source_permission_results",
        "leakage_guard_results",
        "side_effect_guard_results",
        "overclaim_guard_report",
        "recommended_next_task",
    ]:
        assert result.artifact_paths[key].exists()

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == "NO_PROMOTION_INPUT"
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_ready_emitted"] is False
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True


def test_missing_validator_lineage_blocks(tmp_path: Path) -> None:
    result = run_active_replay_input_promotion(
        ActiveReplayInputPromotionSettings(
            output_dir=_promotion_output_dir(tmp_path),
            validator_artifact=tmp_path / "missing_validator",
        )
    )

    assert result.status == "PROMOTION_LINEAGE_BLOCKED"
    assert result.ready_for_human_review is False
    assert result.active_replay_input_ready is False


@pytest.mark.parametrize(
    ("field", "value", "expected_status"),
    [
        ("status", "NO_INPUT", "PROMOTION_LINEAGE_BLOCKED"),
        ("pass_candidate", False, "PROMOTION_LINEAGE_BLOCKED"),
        ("active_replay_input_ready", True, "PROMOTION_LEAKAGE_BLOCKED"),
        ("active_replay_input", True, "PROMOTION_SIDE_EFFECT_BLOCKED"),
        ("forward_labels_exist", True, "PROMOTION_LEAKAGE_BLOCKED"),
        ("weights_trained", True, "PROMOTION_LEAKAGE_BLOCKED"),
        ("active_stock_profile_exists", True, "PROMOTION_LEAKAGE_BLOCKED"),
        ("real_buy_review_eligible", True, "PROMOTION_LEAKAGE_BLOCKED"),
    ],
)
def test_validator_unsafe_or_non_pass_candidate_metadata_blocks(
    tmp_path: Path, field: str, value: object, expected_status: str
) -> None:
    validator = _write_validator_artifact(tmp_path / "validator", {field: value})
    smoke = _write_smoke_artifact(tmp_path / "smoke", validator)
    request = _write_promotion_request(tmp_path / "promotion_request.json", validator, smoke)
    review = _write_human_review(tmp_path / "human_review.json")

    result = run_active_replay_input_promotion(
        ActiveReplayInputPromotionSettings(
            output_dir=_promotion_output_dir(tmp_path),
            validator_artifact=validator,
            smoke_artifact=smoke,
            promotion_request_manifest=request,
            human_review_manifest=review,
        )
    )

    assert result.status == expected_status
    assert result.ready_for_human_review is False
    assert result.active_replay_input_ready is False
    assert "ACTIVE_REPLAY_INPUT_READY" not in result.status


def test_smoke_stage_or_validator_linkage_mismatch_blocks(tmp_path: Path) -> None:
    validator = _write_validator_artifact(tmp_path / "validator")
    smoke = _write_smoke_artifact(tmp_path / "smoke", validator, {"validator_run_id": "wrong"})
    request = _write_promotion_request(tmp_path / "promotion_request.json", validator, smoke)
    review = _write_human_review(tmp_path / "human_review.json")

    result = run_active_replay_input_promotion(
        ActiveReplayInputPromotionSettings(
            output_dir=_promotion_output_dir(tmp_path),
            validator_artifact=validator,
            smoke_artifact=smoke,
            promotion_request_manifest=request,
            human_review_manifest=review,
        )
    )

    assert result.status == "PROMOTION_LINEAGE_BLOCKED"
    assert result.ready_for_human_review is False


def test_missing_promotion_request_or_human_review_blocks(tmp_path: Path) -> None:
    validator = _write_validator_artifact(tmp_path / "validator")
    smoke = _write_smoke_artifact(tmp_path / "smoke", validator)

    result = run_active_replay_input_promotion(
        ActiveReplayInputPromotionSettings(
            output_dir=_promotion_output_dir(tmp_path),
            validator_artifact=validator,
            smoke_artifact=smoke,
        )
    )

    assert result.status == "PROMOTION_REVIEW_BLOCKED"
    assert result.ready_for_human_review is False
    assert result.blocker_count >= 2


def test_human_review_false_gate_blocks(tmp_path: Path) -> None:
    validator = _write_validator_artifact(tmp_path / "validator")
    smoke = _write_smoke_artifact(tmp_path / "smoke", validator)
    request = _write_promotion_request(tmp_path / "promotion_request.json", validator, smoke)
    review = _write_human_review(tmp_path / "human_review.json", {"source_permission_reviewed": False})

    result = run_active_replay_input_promotion(
        ActiveReplayInputPromotionSettings(
            output_dir=_promotion_output_dir(tmp_path),
            validator_artifact=validator,
            smoke_artifact=smoke,
            promotion_request_manifest=request,
            human_review_manifest=review,
        )
    )

    assert result.status == "PROMOTION_REVIEW_BLOCKED"
    human_gates = pd.read_csv(result.artifact_paths["human_review_gate_results"], dtype=str)
    assert "source_permission_reviewed" in set(human_gates["gate_name"])
    assert "False" in set(human_gates["passed"])


def test_unsafe_promotion_request_side_effect_flag_blocks(tmp_path: Path) -> None:
    validator = _write_validator_artifact(tmp_path / "validator")
    smoke = _write_smoke_artifact(tmp_path / "smoke", validator)
    request = _write_promotion_request(tmp_path / "promotion_request.json", validator, smoke, {"cache_mutated": True})
    review = _write_human_review(tmp_path / "human_review.json")

    result = run_active_replay_input_promotion(
        ActiveReplayInputPromotionSettings(
            output_dir=_promotion_output_dir(tmp_path),
            validator_artifact=validator,
            smoke_artifact=smoke,
            promotion_request_manifest=request,
            human_review_manifest=review,
        )
    )

    assert result.status == "PROMOTION_SIDE_EFFECT_BLOCKED"
    assert result.cache_mutated is False
    assert result.ready_for_human_review is False


def test_happy_path_returns_ready_for_human_review_only(tmp_path: Path) -> None:
    validator = _write_validator_artifact(tmp_path / "validator")
    smoke = _write_smoke_artifact(tmp_path / "smoke", validator)
    request = _write_promotion_request(tmp_path / "promotion_request.json", validator, smoke)
    review = _write_human_review(tmp_path / "human_review.json")

    result = run_active_replay_input_promotion(
        ActiveReplayInputPromotionSettings(
            output_dir=_promotion_output_dir(tmp_path),
            validator_artifact=validator,
            smoke_artifact=smoke,
            promotion_request_manifest=request,
            human_review_manifest=review,
        )
    )

    assert result.status == PROMOTION_READY_FOR_HUMAN_REVIEW
    assert result.ready_for_human_review is True
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.forward_labels_exist is False
    assert result.weights_trained is False
    assert result.active_stock_profile_exists is False
    assert result.real_buy_review_eligible is False
    assert result.approval_applied is False
    assert result.active_ready_emitted is False
    assert result.overclaim_guard_pass_count == result.overclaim_guard_total_count

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == PROMOTION_READY_FOR_HUMAN_REVIEW
    assert metadata["ready_for_human_review"] is True
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_ready_emitted"] is False
    assert "ACTIVE_REPLAY_INPUT_READY" not in json.dumps(metadata)

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_cli_command_runs_and_no_view_commands_are_added(tmp_path: Path) -> None:
    validator = _write_validator_artifact(tmp_path / "validator")
    smoke = _write_smoke_artifact(tmp_path / "smoke", validator)
    request = _write_promotion_request(tmp_path / "promotion_request.json", validator, smoke)
    review = _write_human_review(tmp_path / "human_review.json")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "active-replay-input-promotion",
            "--validator-artifact",
            str(validator),
            "--smoke-artifact",
            str(smoke),
            "--promotion-request-manifest",
            str(request),
            "--human-review-manifest",
            str(review),
            "--output-dir",
            str(_promotion_output_dir(tmp_path)),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "promotion_run_id:" in completed.stdout
    assert "status: PROMOTION_READY_FOR_HUMAN_REVIEW" in completed.stdout
    assert "active_replay_input_ready: False" in completed.stdout
    assert "active_replay_input: False" in completed.stdout
    assert "ACTIVE_REPLAY_INPUT_READY" not in completed.stdout

    help_text = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout
    assert "active-replay-input-promotion" in help_text
    assert "active-replay-input-promotion-index" not in help_text
    assert "active-replay-input-promotion-health" not in help_text
    assert "active-replay-input-promotion-status" not in help_text
    assert not Path("docs/project_sources").exists()


def _promotion_output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "active_replay_input_promotion_v0_1"


def _write_validator_artifact(path: Path, overrides: dict[str, object] | None = None) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    metadata = {
        "validator_run_id": "validator_001",
        "status": "REPLAY_INPUT_GATE_PASS_CANDIDATE",
        "workflow_stage": "REPLAY_INPUT_GATE_PASS_CANDIDATE",
        "input_package_path": str(path.parent / "input_package"),
        "pass_candidate": True,
        "active_replay_input_ready": False,
        "active_replay_input": False,
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
        "artifact_path": str(path),
    }
    metadata.update(overrides or {})
    (path / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_smoke_artifact(path: Path, validator_path: Path, overrides: dict[str, object] | None = None) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    validator_metadata = json.loads((validator_path / "metadata.json").read_text(encoding="utf-8"))
    metadata = {
        "smoke_run_id": "smoke_001",
        "validator_run_id": validator_metadata["validator_run_id"],
        "validator_artifact_path": str(validator_path),
        "validator_status": "REPLAY_INPUT_GATE_PASS_CANDIDATE",
        "validation_status": "PASS",
        "workflow_stage": "SMOKE_PASS_CANDIDATE_READY",
        "smoke_stage": "SMOKE_PASS_CANDIDATE_READY",
        "pass_candidate": True,
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
        "report_only": True,
        "diagnostic_only": True,
        "artifact_path": str(path),
    }
    metadata.update(overrides or {})
    (path / "smoke_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_promotion_request(
    path: Path,
    validator_artifact: Path,
    smoke_artifact: Path,
    overrides: dict[str, object] | None = None,
) -> Path:
    request = {
        "promotion_request_id": "promotion_request_001",
        "requested_by": "fixture_reviewer",
        "requested_at": "2024-04-02T16:10:00+08:00",
        "request_reason": "fixture report-only promotion review",
        "validator_artifact_ref": str(validator_artifact),
        "smoke_artifact_ref": str(smoke_artifact),
        "input_package_ref": str(validator_artifact.parent / "input_package"),
        "requested_status": "PROMOTION_READY_FOR_HUMAN_REVIEW",
        "report_only": True,
        "diagnostic_only": True,
        "active_replay_input_ready": False,
        "active_replay_input": False,
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
    request.update(overrides or {})
    path.write_text(json.dumps(request, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_human_review(path: Path, overrides: dict[str, object] | None = None) -> Path:
    review = {
        "human_review_id": "human_review_001",
        "reviewer": "fixture_reviewer",
        "reviewed_at": "2024-04-02T16:20:00+08:00",
        "review_scope": "report-only active replay input promotion readiness",
        "pit_universe_reviewed": True,
        "source_permission_reviewed": True,
        "raw_evidence_reviewed": True,
        "factor_definition_reviewed": True,
        "factor_observation_reviewed": True,
        "event_structured_reviewed": True,
        "company_exposure_reviewed": True,
        "leakage_reviewed": True,
        "side_effect_reviewed": True,
        "promotion_decision_reviewed": True,
        "review_result": "READY_FOR_HUMAN_REVIEW",
        "report_only": True,
        "diagnostic_only": True,
        "notes": "fixture only",
    }
    review.update(overrides or {})
    path.write_text(json.dumps(review, indent=2, sort_keys=True), encoding="utf-8")
    return path
