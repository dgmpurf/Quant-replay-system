from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from quant_replay_system.active_replay_input_ready_emission import (
    ACTIVE_REPLAY_INPUT_READY_EMISSION_ATTESTATION_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_AUTHORITY_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_EVIDENCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_LINEAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_PIT_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_REVIEW_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_SOURCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_TAXONOMY_BLOCKED,
    NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT,
    READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION,
    ActiveReplayInputReadyEmissionSettings,
    run_active_replay_input_ready_emission,
)
from quant_replay_system.active_replay_input_ready_emission_health import (
    check_active_replay_input_ready_emission_health,
)
from quant_replay_system.active_replay_input_ready_emission_index import (
    build_active_replay_input_ready_emission_index,
)
from quant_replay_system.active_replay_input_ready_emission_status import (
    ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION_NO_INPUT,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION_READY,
    run_active_replay_input_ready_emission_status,
)


def test_no_input_writes_report_only_artifacts_with_safe_defaults(tmp_path: Path) -> None:
    result = run_active_replay_input_ready_emission(
        ActiveReplayInputReadyEmissionSettings(output_dir=_output_dir(tmp_path))
    )

    assert result.status == NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT
    assert result.workflow_stage == NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT
    assert result.ready_for_active_replay_input_ready_emission_decision is False
    _assert_never_active(result)
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_path.is_relative_to(_output_dir(tmp_path))

    for key in _required_artifact_keys():
        assert result.artifact_paths[key].exists()

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT
    assert metadata["ready_for_active_replay_input_ready_emission_decision"] is False
    assert metadata["status"] != "ACTIVE_REPLAY_INPUT_READY"
    assert metadata["workflow_stage"] != "ACTIVE_REPLAY_INPUT_READY"
    for field in _always_false_fields():
        assert metadata[field] is False
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("ready_to_emit_artifact_path", ACTIVE_REPLAY_INPUT_READY_EMISSION_LINEAGE_BLOCKED),
        ("active_ready_health_artifact_path", ACTIVE_REPLAY_INPUT_READY_EMISSION_LINEAGE_BLOCKED),
        ("active_ready_status_artifact_path", ACTIVE_REPLAY_INPUT_READY_EMISSION_LINEAGE_BLOCKED),
        ("final_emission_governance_plan_path", ACTIVE_REPLAY_INPUT_READY_EMISSION_REVIEW_BLOCKED),
        ("final_emission_request_manifest_path", ACTIVE_REPLAY_INPUT_READY_EMISSION_REVIEW_BLOCKED),
        ("final_authority_manifest_path", ACTIVE_REPLAY_INPUT_READY_EMISSION_AUTHORITY_BLOCKED),
        ("final_attestation_manifest_path", ACTIVE_REPLAY_INPUT_READY_EMISSION_ATTESTATION_BLOCKED),
        ("pit_source_evidence_bundle_path", ACTIVE_REPLAY_INPUT_READY_EMISSION_EVIDENCE_BLOCKED),
        ("taxonomy_evidence_bundle_path", ACTIVE_REPLAY_INPUT_READY_EMISSION_TAXONOMY_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(
    tmp_path: Path, setting_name: str, expected_status: str
) -> None:
    settings = replace(_happy_settings(tmp_path), **{setting_name: None})

    result = run_active_replay_input_ready_emission(settings)

    assert result.status == expected_status
    assert result.ready_for_active_replay_input_ready_emission_decision is False
    _assert_never_active(result)


@pytest.mark.parametrize(
    ("path_name", "override", "expected_status"),
    [
        (
            "ready_to_emit_artifact_path",
            {"status": "NO_ACTIVE_REPLAY_INPUT_READY_GOVERNANCE_INPUT"},
            ACTIVE_REPLAY_INPUT_READY_EMISSION_LINEAGE_BLOCKED,
        ),
        (
            "active_ready_health_artifact_path",
            {"health_status": "FAIL"},
            ACTIVE_REPLAY_INPUT_READY_EMISSION_LINEAGE_BLOCKED,
        ),
        (
            "ready_to_emit_artifact_path",
            {"ready_to_emit_active_replay_input_ready": False},
            ACTIVE_REPLAY_INPUT_READY_EMISSION_LINEAGE_BLOCKED,
        ),
        (
            "final_emission_request_manifest_path",
            {"request_result": "REJECTED"},
            ACTIVE_REPLAY_INPUT_READY_EMISSION_REVIEW_BLOCKED,
        ),
        (
            "final_authority_manifest_path",
            {"authority_result": "REJECTED"},
            ACTIVE_REPLAY_INPUT_READY_EMISSION_AUTHORITY_BLOCKED,
        ),
        (
            "final_attestation_manifest_path",
            {"second_reviewer_attested": False},
            ACTIVE_REPLAY_INPUT_READY_EMISSION_ATTESTATION_BLOCKED,
        ),
        (
            "pit_source_evidence_bundle_path",
            {"accepted_pit_universe_evidence_attached": False},
            ACTIVE_REPLAY_INPUT_READY_EMISSION_PIT_BLOCKED,
        ),
        (
            "pit_source_evidence_bundle_path",
            {"source_hash_coverage_attached": False},
            ACTIVE_REPLAY_INPUT_READY_EMISSION_SOURCE_BLOCKED,
        ),
        (
            "pit_source_evidence_bundle_path",
            {"factor_observation_coverage_attached": False},
            ACTIVE_REPLAY_INPUT_READY_EMISSION_EVIDENCE_BLOCKED,
        ),
        (
            "taxonomy_evidence_bundle_path",
            {"not_fixed_12_only": False},
            ACTIVE_REPLAY_INPUT_READY_EMISSION_TAXONOMY_BLOCKED,
        ),
        (
            "leakage_side_effect_evidence_bundle_path",
            {"no_future_labels": False},
            ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED,
        ),
        (
            "leakage_side_effect_evidence_bundle_path",
            {"no_data_raw_written": False},
            ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED,
        ),
        (
            "overclaim_evidence_bundle_path",
            {"ready_to_emit_not_active_replay_input_ready": False},
            ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED,
        ),
    ],
)
def test_manifest_gate_failures_block(
    tmp_path: Path, path_name: str, override: dict[str, object], expected_status: str
) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(getattr(settings, path_name), override)

    result = run_active_replay_input_ready_emission(settings)

    assert result.status == expected_status
    assert result.ready_for_active_replay_input_ready_emission_decision is False
    _assert_never_active(result)


@pytest.mark.parametrize(
    ("unsafe_field", "expected_status"),
    [
        ("active_replay_input_ready", ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED),
        ("active_replay_input", ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED),
        ("active_ready_emitted", ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED),
        ("replay_execution_allowed", ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED),
        ("replay_decisions_exist", ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED),
        ("forward_labels_allowed", ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED),
        ("forward_labels_exist", ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED),
        ("forward_returns_exist", ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED),
        ("training_allowed", ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED),
        ("training_outputs_exist", ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED),
        ("model_weights_exist", ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED),
        ("weights_trained", ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED),
        ("stock_profile_allowed", ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED),
        ("stock_profile_artifacts_exist", ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED),
        ("active_stock_profile_exists", ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED),
        ("buy_review_allowed", ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED),
        ("real_buy_review_eligible", ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED),
        ("trading_allowed", ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED),
        ("order_placed", ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED),
        ("message_sent", ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED),
        ("llm_api_called", ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED),
        ("external_api_called", ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED),
        ("cache_mutated", ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED),
        ("data_raw_written", ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED),
        ("data_processed_written", ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED),
        ("data_cache_written", ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED),
        ("broker_api_called", ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED),
        ("current_candidates_run", ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED),
        ("snapshot_built", ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED),
        ("approved_for_paper", ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED),
    ],
)
def test_unsafe_input_flags_block(tmp_path: Path, unsafe_field: str, expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.ready_to_emit_artifact_path, {unsafe_field: True})

    result = run_active_replay_input_ready_emission(settings)

    assert result.status == expected_status
    assert result.ready_for_active_replay_input_ready_emission_decision is False
    _assert_never_active(result)


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    settings = ActiveReplayInputReadyEmissionSettings(output_dir=tmp_path / "unsafe")

    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_active_replay_input_ready_emission(settings)


def test_happy_path_reaches_emission_decision_ready_without_active_ready_emission(
    tmp_path: Path,
) -> None:
    result = run_active_replay_input_ready_emission(_happy_settings(tmp_path))

    assert result.status == READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION
    assert result.workflow_stage == READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION
    assert result.ready_for_active_replay_input_ready_emission_decision is True
    _assert_never_active(result)
    assert result.blocker_count == 0
    assert result.status != "ACTIVE_REPLAY_INPUT_READY"

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION
    assert metadata["ready_for_active_replay_input_ready_emission_decision"] is True
    assert metadata["status"] != "ACTIVE_REPLAY_INPUT_READY"
    for field in _always_false_fields():
        assert metadata[field] is False

    candidate = json.loads(result.artifact_paths["emission_candidate"].read_text(encoding="utf-8"))
    assert candidate["status"] == READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION
    assert candidate["ready_for_active_replay_input_ready_emission_decision"] is True
    assert candidate["active_replay_input_ready"] is False
    assert candidate["active_replay_input"] is False
    assert candidate["active_ready_emitted"] is False
    assert candidate["status"] != "ACTIVE_REPLAY_INPUT_READY"

    report = result.artifact_paths["emission_report"].read_text(encoding="utf-8")
    assert "READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION is not ACTIVE_REPLAY_INPUT_READY" in report
    assert "does not create active replay input" in report
    assert "does not run replay" in report
    assert "does not create replay decisions" in report

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_cli_active_replay_input_ready_emission_runs(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "active-replay-input-ready-emission",
            "--ready-to-emit-artifact-path",
            str(settings.ready_to_emit_artifact_path),
            "--active-ready-health-artifact-path",
            str(settings.active_ready_health_artifact_path),
            "--active-ready-status-artifact-path",
            str(settings.active_ready_status_artifact_path),
            "--final-emission-governance-plan-path",
            str(settings.final_emission_governance_plan_path),
            "--final-emission-request-manifest-path",
            str(settings.final_emission_request_manifest_path),
            "--final-authority-manifest-path",
            str(settings.final_authority_manifest_path),
            "--final-attestation-manifest-path",
            str(settings.final_attestation_manifest_path),
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

    assert "active_ready_emission_run_id:" in completed.stdout
    assert f"status: {READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION}" in completed.stdout
    assert "ready_for_active_replay_input_ready_emission_decision: True" in completed.stdout
    assert "active_replay_input_ready: False" in completed.stdout
    assert "active_replay_input: False" in completed.stdout
    assert "active_ready_emitted: False" in completed.stdout
    assert "replay_execution_allowed: False" in completed.stdout
    assert "replay_decisions_exist: False" in completed.stdout
    assert "forward_labels_allowed: False" in completed.stdout
    assert "forward_labels_exist: False" in completed.stdout
    assert "training_allowed: False" in completed.stdout
    assert "weights_trained: False" in completed.stdout
    assert "stock_profile_allowed: False" in completed.stdout
    assert "active_stock_profile_exists: False" in completed.stdout
    assert "buy_review_allowed: False" in completed.stdout
    assert "real_buy_review_eligible: False" in completed.stdout
    assert "trading_allowed: False" in completed.stdout
    assert "status: ACTIVE_REPLAY_INPUT_READY\n" not in completed.stdout
    assert "workflow_stage: ACTIVE_REPLAY_INPUT_READY\n" not in completed.stdout


def test_artifact_view_cli_commands_are_registered_without_research_status_or_checkpoint() -> None:
    help_text = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout

    assert "active-replay-input-ready-emission" in help_text
    assert "active-replay-input-ready-emission-index" in help_text
    assert "active-replay-input-ready-emission-health" in help_text
    assert "active-replay-input-ready-emission-status" in help_text
    assert "active_replay_input_ready_emission" not in Path(
        "src/quant_replay_system/local_research_dashboard.py"
    ).read_text(encoding="utf-8")
    assert not Path("docs/active_replay_input_ready_emission.md").exists()
    assert not Path("docs/release_checkpoint_v1.38.0.md").exists()
    assert not Path("SOURCE_UPDATE_NOTES_v1_38_0.md").exists()
    assert not Path("docs/project_sources").exists()


def test_index_discovers_no_input_artifact(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    no_input = run_active_replay_input_ready_emission(
        ActiveReplayInputReadyEmissionSettings(output_dir=root)
    )

    result = build_active_replay_input_ready_emission_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["active_ready_emission_run_id"] == no_input.active_ready_emission_run_id
    assert row["status"] == NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT
    assert row["ready_for_active_replay_input_ready_emission_decision"] is False
    assert row["active_replay_input_ready"] is False
    assert row["active_replay_input"] is False
    assert row["active_ready_emitted"] is False
    assert row["replay_execution_allowed"] is False
    assert row["replay_decisions_exist"] is False
    assert row["forward_labels_allowed"] is False
    assert row["forward_labels_exist"] is False
    assert row["training_allowed"] is False
    assert row["weights_trained"] is False
    assert row["stock_profile_allowed"] is False
    assert row["active_stock_profile_exists"] is False
    assert row["buy_review_allowed"] is False
    assert row["real_buy_review_eligible"] is False
    assert row["trading_allowed"] is False
    assert row["report_only"] is True
    assert row["diagnostic_only"] is True
    assert result.artifact_paths["index_csv"].exists()


def test_index_discovers_happy_path_artifact(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    ready = run_active_replay_input_ready_emission(_happy_settings(tmp_path))

    result = build_active_replay_input_ready_emission_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["active_ready_emission_run_id"] == ready.active_ready_emission_run_id
    assert row["status"] == READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION
    assert row["workflow_stage"] == READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION
    assert row["ready_for_active_replay_input_ready_emission_decision"] is True
    assert row["active_replay_input_ready"] is False
    assert row["active_replay_input"] is False
    assert row["active_ready_emitted"] is False
    assert row["replay_execution_allowed"] is False
    assert row["replay_decisions_exist"] is False
    assert row["forward_labels_allowed"] is False
    assert row["forward_labels_exist"] is False
    assert row["training_allowed"] is False
    assert row["weights_trained"] is False
    assert row["stock_profile_allowed"] is False
    assert row["active_stock_profile_exists"] is False
    assert row["buy_review_allowed"] is False
    assert row["real_buy_review_eligible"] is False
    assert row["trading_allowed"] is False
    assert row["overclaim_guard_pass_count"] == row["overclaim_guard_total_count"]
    assert row["blocker_count"] == 0


def test_health_passes_for_valid_no_input_artifact(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    run_active_replay_input_ready_emission(ActiveReplayInputReadyEmissionSettings(output_dir=root))

    result = check_active_replay_input_ready_emission_health(root=root, output_dir=root / "health")

    assert result.status == "PASS"
    assert result.error_count == 0
    assert result.checked_artifact_count == 1


def test_health_passes_for_valid_emission_decision_ready_artifact(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    run_active_replay_input_ready_emission(_happy_settings(tmp_path))

    result = check_active_replay_input_ready_emission_health(root=root, output_dir=root / "health")

    assert result.status == "PASS"
    assert result.error_count == 0
    assert result.checked_artifact_count == 1


@pytest.mark.parametrize(
    ("metadata_field", "metadata_value", "issue_code"),
    [
        ("status", "ACTIVE_REPLAY_INPUT_READY", "ACTIVE_REPLAY_INPUT_READY_UNEXPECTED"),
        ("active_replay_input_ready", True, "ACTIVE_REPLAY_INPUT_READY_FLAG_UNEXPECTED"),
        ("active_replay_input", True, "ACTIVE_REPLAY_INPUT_UNEXPECTED"),
        ("active_ready_emitted", True, "ACTIVE_READY_EMITTED_UNEXPECTED"),
        ("replay_execution_allowed", True, "REPLAY_EXECUTION_ALLOWED_UNEXPECTED"),
        ("replay_decisions_exist", True, "REPLAY_DECISIONS_EXIST_UNEXPECTED"),
        ("forward_labels_allowed", True, "FORWARD_LABELS_ALLOWED_UNEXPECTED"),
        ("forward_labels_exist", True, "FORWARD_LABELS_EXIST_UNEXPECTED"),
        ("training_allowed", True, "TRAINING_ALLOWED_UNEXPECTED"),
        ("weights_trained", True, "WEIGHTS_TRAINED_UNEXPECTED"),
        ("stock_profile_allowed", True, "STOCK_PROFILE_ALLOWED_UNEXPECTED"),
        ("active_stock_profile_exists", True, "ACTIVE_STOCK_PROFILE_EXISTS_UNEXPECTED"),
        ("buy_review_allowed", True, "BUY_REVIEW_ALLOWED_UNEXPECTED"),
        ("real_buy_review_eligible", True, "REAL_BUY_REVIEW_ELIGIBLE_UNEXPECTED"),
        ("trading_allowed", True, "TRADING_ALLOWED_UNEXPECTED"),
        ("order_placed", True, "ORDER_PLACED_UNEXPECTED"),
        ("broker_api_called", True, "BROKER_API_CALLED_UNEXPECTED"),
        ("message_sent", True, "MESSAGE_SENT_UNEXPECTED"),
        ("llm_api_called", True, "LLM_API_CALLED_UNEXPECTED"),
        ("external_api_called", True, "EXTERNAL_API_CALLED_UNEXPECTED"),
        ("cache_mutated", True, "CACHE_MUTATED_UNEXPECTED"),
        ("data_raw_written", True, "DATA_RAW_WRITTEN_UNEXPECTED"),
        ("data_processed_written", True, "DATA_PROCESSED_WRITTEN_UNEXPECTED"),
        ("data_cache_written", True, "DATA_CACHE_WRITTEN_UNEXPECTED"),
        ("current_candidates_run", True, "CURRENT_CANDIDATES_RUN_UNEXPECTED"),
        ("snapshot_built", True, "SNAPSHOT_BUILT_UNEXPECTED"),
        ("signal_semantics_changed", True, "SIGNAL_SEMANTICS_CHANGED_UNEXPECTED"),
        ("overclaim_guard_pass_count", 0, "OVERCLAIM_GUARD_FAILED"),
    ],
)
def test_health_fails_for_unsafe_or_overclaim_metadata(
    tmp_path: Path, metadata_field: str, metadata_value: object, issue_code: str
) -> None:
    root = _output_dir(tmp_path)
    result = run_active_replay_input_ready_emission(_happy_settings(tmp_path))
    _patch_json(result.artifact_paths["metadata"], {metadata_field: metadata_value})

    health = check_active_replay_input_ready_emission_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert issue_code in set(health.health_frame["issue_code"])


def test_health_fails_when_decision_ready_flag_is_true_for_non_ready_status(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    result = run_active_replay_input_ready_emission(
        ActiveReplayInputReadyEmissionSettings(output_dir=root)
    )
    _patch_json(
        result.artifact_paths["metadata"],
        {"ready_for_active_replay_input_ready_emission_decision": True},
    )

    health = check_active_replay_input_ready_emission_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION_INCONSISTENT" in set(
        health.health_frame["issue_code"]
    )


def test_health_fails_for_output_path_outside_manual_diagnostics(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    result = run_active_replay_input_ready_emission(
        ActiveReplayInputReadyEmissionSettings(output_dir=root)
    )
    _patch_json(result.artifact_paths["metadata"], {"artifact_path": str(tmp_path / "unsafe")})

    health = check_active_replay_input_ready_emission_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "UNSAFE_OUTPUT_PATH" in set(health.health_frame["issue_code"])


def test_status_reports_correct_no_input_state(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    no_input = run_active_replay_input_ready_emission(
        ActiveReplayInputReadyEmissionSettings(output_dir=root)
    )

    status = run_active_replay_input_ready_emission_status(root=root, output_dir=root / "status")

    assert status.latest_active_ready_emission_run_id == no_input.active_ready_emission_run_id
    assert status.status == NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT
    assert status.health_status == "PASS"
    assert status.workflow_stage == ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION_NO_INPUT
    assert status.ready_for_active_replay_input_ready_emission_decision is False
    assert status.active_replay_input_ready is False
    assert status.active_replay_input is False
    assert status.active_ready_emitted is False
    assert status.replay_execution_allowed is False
    assert status.replay_decisions_exist is False
    assert status.forward_labels_exist is False
    assert status.weights_trained is False
    assert status.active_stock_profile_exists is False
    assert status.real_buy_review_eligible is False


def test_status_reports_correct_emission_decision_ready_state_with_safety_wording(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    ready = run_active_replay_input_ready_emission(_happy_settings(tmp_path))

    status = run_active_replay_input_ready_emission_status(root=root, output_dir=root / "status")

    assert status.latest_active_ready_emission_run_id == ready.active_ready_emission_run_id
    assert status.status == READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION
    assert status.health_status == "PASS"
    assert status.workflow_stage == ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION_READY
    assert status.ready_for_active_replay_input_ready_emission_decision is True
    assert status.active_replay_input_ready is False
    assert status.active_replay_input is False
    assert status.active_ready_emitted is False
    assert status.replay_execution_allowed is False
    assert status.replay_decisions_exist is False
    assert status.forward_labels_allowed is False
    assert status.forward_labels_exist is False
    assert status.training_allowed is False
    assert status.weights_trained is False
    assert status.stock_profile_allowed is False
    assert status.active_stock_profile_exists is False
    assert status.buy_review_allowed is False
    assert status.real_buy_review_eligible is False
    assert status.trading_allowed is False
    assert "report-only" in status.safety_statement
    assert "READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION is not ACTIVE_REPLAY_INPUT_READY" in (
        status.safety_statement
    )
    assert "ACTIVE_REPLAY_INPUT_READY is not emitted" in status.safety_statement
    assert "active replay input is not created" in status.safety_statement
    assert "replay is not run" in status.safety_statement
    assert "replay decisions are not created" in status.safety_statement
    assert "labels are not computed" in status.safety_statement
    assert "training is not run" in status.safety_statement
    assert "stock_profile is not created" in status.safety_statement
    assert "buy-review eligibility is not created" in status.safety_statement
    assert "trading is not authorized" in status.safety_statement
    assert "ACTIVE_REPLAY_INPUT_READY\n" not in status.summary_frame.to_csv(index=False)


def test_cli_artifact_view_commands_run_without_active_ready_claim(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    run_active_replay_input_ready_emission(_happy_settings(tmp_path))

    for command in [
        "active-replay-input-ready-emission-index",
        "active-replay-input-ready-emission-health",
        "active-replay-input-ready-emission-status",
    ]:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "quant_replay_system.cli",
                command,
                "--root",
                str(root),
                "--output-dir",
                str(root / command.rsplit("-", 1)[-1]),
            ],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
        )

        assert "ACTIVE_REPLAY_INPUT_READY emission" in completed.stdout
        assert "active replay input" in completed.stdout
        assert "status: ACTIVE_REPLAY_INPUT_READY\n" not in completed.stdout
        assert "workflow_stage: ACTIVE_REPLAY_INPUT_READY\n" not in completed.stdout


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "active_replay_input_ready_emission_v0_1"


def _happy_settings(tmp_path: Path) -> ActiveReplayInputReadyEmissionSettings:
    root = tmp_path / "fixtures"
    root.mkdir(parents=True, exist_ok=True)
    governance_plan = root / "final_emission_governance_plan.md"
    governance_plan.write_text("final emission governance plan accepted for report-only fixture", encoding="utf-8")
    return ActiveReplayInputReadyEmissionSettings(
        ready_to_emit_artifact_path=_write_json(root / "ready_to_emit.json", _ready_to_emit_payload()),
        active_ready_health_artifact_path=_write_json(root / "active_ready_health.json", {"health_status": "PASS"}),
        active_ready_status_artifact_path=_write_json(
            root / "active_ready_status.json",
            {
                "status": "READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY",
                "workflow_stage": "ACTIVE_REPLAY_INPUT_READY_READY_TO_EMIT",
                "ready_to_emit_active_replay_input_ready": True,
                "active_replay_input_ready": False,
                "active_replay_input": False,
                "active_ready_emitted": False,
            },
        ),
        final_emission_governance_plan_path=governance_plan,
        final_emission_request_manifest_path=_write_json(
            root / "final_emission_request.json",
            {
                "request_result": "PASS",
                "explicit_final_emission_request": True,
                "explicit_actual_emission_allowed": False,
                "report_only": True,
                "diagnostic_only": True,
            },
        ),
        final_authority_manifest_path=_write_json(
            root / "authority.json",
            {
                "authority_result": "PASS",
                "primary_reviewer": "reviewer_a",
                "second_reviewer": "reviewer_b",
                "authority_scope": "report_only_emission_decision",
            },
        ),
        final_attestation_manifest_path=_write_json(
            root / "attestation.json",
            {
                "primary_reviewer_attested": True,
                "second_reviewer_attested": True,
                "no_active_ready_emission_attested": True,
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
            root / "leakage.json",
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
                "pass_candidate_not_active_ready": True,
                "smoke_not_active_ready": True,
                "promotion_not_active_ready": True,
                "acceptance_not_active_ready": True,
                "active_ready_final_review_not_active_ready": True,
                "final_review_ready_not_active_input_ready": True,
                "emission_ready_review_not_active_input_ready": True,
                "ready_decision_not_active_replay_input_ready": True,
                "ready_to_emit_not_active_replay_input_ready": True,
                "emission_decision_ready_not_active_replay_input_ready": True,
                "active_input_ready_not_replay": True,
                "active_input_ready_not_labels": True,
                "active_input_ready_not_training": True,
                "active_input_ready_not_stock_profile": True,
                "active_input_ready_not_buy_review": True,
                "active_input_ready_not_trading": True,
                "active_input_ready_not_performance_validation": True,
                "report_only": True,
                "diagnostic_only": True,
            },
        ),
        output_dir=_output_dir(tmp_path),
    )


def _ready_to_emit_payload() -> dict[str, object]:
    return {
        "active_ready_run_id": "ready_emit123",
        "status": "READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY",
        "workflow_stage": "READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY",
        "ready_to_emit_active_replay_input_ready": True,
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


def _assert_never_active(result: object) -> None:
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.active_ready_emitted is False
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
    assert result.status != "ACTIVE_REPLAY_INPUT_READY"
    assert result.workflow_stage != "ACTIVE_REPLAY_INPUT_READY"


def _always_false_fields() -> list[str]:
    return [
        "active_replay_input_ready",
        "active_replay_input",
        "active_ready_emitted",
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
    ]


def _required_artifact_keys() -> list[str]:
    return [
        "metadata",
        "emission_report",
        "final_emission_precondition_results",
        "final_emission_authority_results",
        "ready_to_emit_lineage_results",
        "final_emission_attestation_results",
        "pit_source_evidence_results",
        "taxonomy_evidence_results",
        "leakage_side_effect_guard_results",
        "overclaim_guard_results",
        "emission_candidate",
        "recommended_next_task",
    ]


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _patch_json(path: Path, override: dict[str, object]) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(override)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
