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
from quant_replay_system.active_replay_input_ready_decision_health import (
    check_active_replay_input_ready_decision_health,
)
from quant_replay_system.active_replay_input_ready_decision_index import (
    build_active_replay_input_ready_decision_index,
)
from quant_replay_system.active_replay_input_ready_decision_status import (
    NO_READY_DECISION_ARTIFACT_FOUND,
    READY_DECISION_BLOCKED,
    READY_DECISION_HEALTH_FAILED,
    READY_DECISION_NO_INPUT,
    run_active_replay_input_ready_decision_status,
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


def test_artifact_view_cli_commands_are_registered_with_research_status_checkpoint_docs() -> None:
    help_text = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout

    assert "active-replay-input-ready-decision" in help_text
    assert "active-replay-input-ready-decision-index" in help_text
    assert "active-replay-input-ready-decision-health" in help_text
    assert "active-replay-input-ready-decision-status" in help_text

    assert Path("docs/active_replay_input_ready_decision.md").exists()
    assert Path("docs/release_checkpoint_v1.36.0.md").exists()
    assert Path("SOURCE_UPDATE_NOTES_v1_36_0.md").exists()
    assert not Path("docs/project_sources").exists()


def test_index_discovers_no_input_and_ready_decision_artifacts(tmp_path: Path) -> None:
    root = _decision_output_dir(tmp_path)
    no_input = run_active_replay_input_ready_decision(ActiveReplayInputReadyDecisionSettings(output_dir=root))
    ready = run_active_replay_input_ready_decision(_happy_settings(tmp_path))

    result = build_active_replay_input_ready_decision_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 2
    assert set(result.index_frame["decision_run_id"]) == {no_input.decision_run_id, ready.decision_run_id}
    ready_row = result.index_frame[result.index_frame["decision_run_id"] == ready.decision_run_id].iloc[0]
    assert ready_row["status"] == READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION
    assert ready_row["ready_for_active_replay_input_ready_decision"] is True
    assert ready_row["active_replay_input_ready"] is False
    assert ready_row["active_replay_input"] is False
    assert ready_row["active_ready_emitted"] is False
    assert ready_row["replay_execution_allowed"] is False
    assert ready_row["forward_labels_allowed"] is False
    assert ready_row["training_allowed"] is False
    assert ready_row["stock_profile_allowed"] is False
    assert ready_row["buy_review_allowed"] is False
    assert ready_row["trading_allowed"] is False
    assert ready_row["replay_decisions_exist"] is False
    assert ready_row["forward_labels_exist"] is False
    assert ready_row["weights_trained"] is False
    assert ready_row["active_stock_profile_exists"] is False
    assert ready_row["real_buy_review_eligible"] is False
    assert ready_row["report_only"] is True
    assert ready_row["diagnostic_only"] is True
    assert ready_row["precondition_gate_count"] == ready.precondition_count
    assert ready_row["overclaim_guard_pass_count"] == ready_row["overclaim_guard_total_count"]
    assert result.artifact_paths["index_csv"].exists()


def test_health_passes_for_valid_no_input_and_ready_decision_artifacts(tmp_path: Path) -> None:
    root = _decision_output_dir(tmp_path)
    run_active_replay_input_ready_decision(ActiveReplayInputReadyDecisionSettings(output_dir=root))
    no_input_health = check_active_replay_input_ready_decision_health(root=root, output_dir=root / "health_no_input")
    assert no_input_health.status == "PASS"
    assert no_input_health.error_count == 0

    run_active_replay_input_ready_decision(_happy_settings(tmp_path))
    ready_health = check_active_replay_input_ready_decision_health(root=root, output_dir=root / "health_ready")
    assert ready_health.status == "PASS"
    assert ready_health.error_count == 0


@pytest.mark.parametrize(
    ("metadata_field", "metadata_value", "issue_code"),
    [
        ("status", "ACTIVE_REPLAY_INPUT_READY", "ACTIVE_REPLAY_INPUT_READY_UNEXPECTED"),
        (
            "ready_for_active_replay_input_ready_decision",
            True,
            "READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION_INCONSISTENT",
        ),
        ("active_replay_input_ready", True, "ACTIVE_REPLAY_INPUT_READY_FLAG_UNEXPECTED"),
        ("active_replay_input", True, "ACTIVE_REPLAY_INPUT_UNEXPECTED"),
        ("active_ready_emitted", True, "ACTIVE_READY_EMITTED_UNEXPECTED"),
        ("replay_execution_allowed", True, "REPLAY_EXECUTION_ALLOWED_UNEXPECTED"),
        ("forward_labels_allowed", True, "FORWARD_LABELS_ALLOWED_UNEXPECTED"),
        ("training_allowed", True, "TRAINING_ALLOWED_UNEXPECTED"),
        ("stock_profile_allowed", True, "STOCK_PROFILE_ALLOWED_UNEXPECTED"),
        ("buy_review_allowed", True, "BUY_REVIEW_ALLOWED_UNEXPECTED"),
        ("trading_allowed", True, "TRADING_ALLOWED_UNEXPECTED"),
        ("replay_decisions_exist", True, "REPLAY_DECISIONS_EXIST_UNEXPECTED"),
        ("forward_labels_exist", True, "FORWARD_LABELS_EXIST_UNEXPECTED"),
        ("weights_trained", True, "WEIGHTS_TRAINED_UNEXPECTED"),
        ("active_stock_profile_exists", True, "ACTIVE_STOCK_PROFILE_EXISTS_UNEXPECTED"),
        ("real_buy_review_eligible", True, "REAL_BUY_REVIEW_ELIGIBLE_UNEXPECTED"),
        ("approval_applied", True, "APPROVAL_APPLIED_UNEXPECTED"),
        ("order_placed", True, "ORDER_PLACED_UNEXPECTED"),
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
        ("report_only", False, "UNSAFE_REPORT_ONLY_FLAGS"),
        ("no_live_trading", False, "UNSAFE_TRADING_FLAGS"),
    ],
)
def test_health_fails_for_unsafe_ready_decision_metadata(
    tmp_path: Path, metadata_field: str, metadata_value: object, issue_code: str
) -> None:
    root = _decision_output_dir(tmp_path)
    ready = run_active_replay_input_ready_decision(_happy_settings(tmp_path))
    updates = {metadata_field: metadata_value}
    if metadata_field == "ready_for_active_replay_input_ready_decision":
        updates["status"] = "ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED"
    _mutate_json(ready.artifact_paths["metadata"], updates)

    result = check_active_replay_input_ready_decision_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert issue_code in set(result.health_frame["issue_code"])


def test_health_fails_when_overclaim_guards_fail(tmp_path: Path) -> None:
    root = _decision_output_dir(tmp_path)
    ready = run_active_replay_input_ready_decision(_happy_settings(tmp_path))
    _mutate_json(ready.artifact_paths["metadata"], {"overclaim_guard_pass_count": 1})

    result = check_active_replay_input_ready_decision_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert "OVERCLAIM_GUARD_FAILED" in set(result.health_frame["issue_code"])


def test_status_reports_ready_decision_without_active_ready_claim(tmp_path: Path) -> None:
    root = _decision_output_dir(tmp_path)
    ready = run_active_replay_input_ready_decision(_happy_settings(tmp_path))

    result = run_active_replay_input_ready_decision_status(root=root, output_dir=root / "status")

    assert result.latest_decision_run_id == ready.decision_run_id
    assert result.status == READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION
    assert result.health_status == "PASS"
    assert result.workflow_stage == READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION
    assert result.ready_for_active_replay_input_ready_decision is True
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.active_ready_emitted is False
    assert "report-only" in result.safety_statement
    assert "not ACTIVE_REPLAY_INPUT_READY" in result.safety_statement
    assert "does not emit ACTIVE_REPLAY_INPUT_READY" in result.safety_statement
    assert "does not create active replay input" in result.safety_statement
    assert "does not run replay" in result.safety_statement
    assert "does not compute forward labels" in result.safety_statement
    assert "does not train weights" in result.safety_statement
    assert "does not create active stock profiles" in result.safety_statement
    assert "does not create real buy-review eligibility" in result.safety_statement
    assert "does not authorize trading" in result.safety_statement


def test_status_reports_no_input_blocked_and_health_failed_stages(tmp_path: Path) -> None:
    root = _decision_output_dir(tmp_path)
    no_input = run_active_replay_input_ready_decision(ActiveReplayInputReadyDecisionSettings(output_dir=root))
    no_input_status = run_active_replay_input_ready_decision_status(root=root, output_dir=root / "status_no_input")
    assert no_input_status.latest_decision_run_id == no_input.decision_run_id
    assert no_input_status.workflow_stage == READY_DECISION_NO_INPUT

    blocked_settings = _replace_setting(_happy_settings(tmp_path), "decision_authority_manifest_path", None)
    blocked = run_active_replay_input_ready_decision(blocked_settings)
    blocked_status = run_active_replay_input_ready_decision_status(root=root, output_dir=root / "status_blocked")
    assert blocked_status.latest_decision_run_id == blocked.decision_run_id
    assert blocked_status.workflow_stage == READY_DECISION_BLOCKED

    _mutate_json(blocked.artifact_paths["metadata"], {"active_replay_input": True})
    failed_status = run_active_replay_input_ready_decision_status(root=root, output_dir=root / "status_failed")
    assert failed_status.workflow_stage == READY_DECISION_HEALTH_FAILED
    assert failed_status.health_status == "FAIL"

    missing_status = run_active_replay_input_ready_decision_status(
        root=root / "missing", output_dir=root / "status_missing"
    )
    assert missing_status.workflow_stage == NO_READY_DECISION_ARTIFACT_FOUND


def test_artifact_view_cli_commands_and_research_status_remain_report_only(tmp_path: Path) -> None:
    root = _decision_output_dir(tmp_path)
    ready = run_active_replay_input_ready_decision(_happy_settings(tmp_path))

    commands = [
        ("active-replay-input-ready-decision-index", "artifact_count: 1"),
        ("active-replay-input-ready-decision-health", "status: PASS"),
        (
            "active-replay-input-ready-decision-status",
            f"workflow_stage: {READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION}",
        ),
    ]
    for command, expected_text in commands:
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
        assert expected_text in completed.stdout
        assert "No active input ready emission" in completed.stdout
        assert "status: ACTIVE_REPLAY_INPUT_READY\n" not in completed.stdout

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
    assert f"latest_active_replay_input_ready_decision_run_id: {ready.decision_run_id}" in completed.stdout
    assert (
        f"latest_active_replay_input_ready_decision_status: {READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION}"
    ) in completed.stdout
    assert "latest_active_replay_input_ready_decision_health_status: PASS" in completed.stdout
    assert (
        f"latest_active_replay_input_ready_decision_workflow_stage: {READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION}"
    ) in completed.stdout
    assert "active_replay_input_ready_decision_implemented: True" in completed.stdout
    assert "active_replay_input_ready_decision_views_implemented: True" in completed.stdout
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
    assert "replay_decisions_exist: False" in completed.stdout
    assert "forward_labels_exist: False" in completed.stdout
    assert "weights_trained: False" in completed.stdout
    assert "active_stock_profile_exists: False" in completed.stdout
    assert "real_buy_review_eligible: False" in completed.stdout
    assert "status: ACTIVE_REPLAY_INPUT_READY\n" not in completed.stdout
    assert "workflow_stage: ACTIVE_REPLAY_INPUT_READY\n" not in completed.stdout
    assert not Path("docs/project_sources").exists()
    assert Path("docs/release_checkpoint_v1.36.0.md").exists()


def test_research_status_preserves_paper_priority_over_ready_decision(tmp_path: Path) -> None:
    run_active_replay_input_ready_decision(_happy_settings(tmp_path))
    paper_artifact = tmp_path / "outputs" / "reports" / "paper_trading" / "workflow_status" / "paper-ready"
    paper_artifact.mkdir(parents=True, exist_ok=True)
    report = paper_artifact / "paper_workflow_status_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    (paper_artifact / "metadata.json").write_text(
        json.dumps(
            {
                "workflow_status_id": "paper-ready",
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
            indent=2,
        ),
        encoding="utf-8",
    )

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

    assert "workflow_stage: PAPER_WORKFLOW_READY" in completed.stdout
    assert f"latest_active_replay_input_ready_decision_status: {READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION}" in completed.stdout
    assert "ready_for_active_replay_input_ready_decision: True" in completed.stdout
    assert "active_replay_input_ready: False" in completed.stdout
    assert "active_replay_input: False" in completed.stdout
    assert "active_ready_emitted: False" in completed.stdout
    assert "workflow_stage: ACTIVE_REPLAY_INPUT_READY\n" not in completed.stdout


def test_ready_decision_docs_checkpoint_and_source_note_state_safety_boundary() -> None:
    doc = Path("docs/active_replay_input_ready_decision.md")
    checkpoint = Path("docs/release_checkpoint_v1.36.0.md")
    source_note = Path("SOURCE_UPDATE_NOTES_v1_36_0.md")

    for path in [doc, checkpoint, source_note]:
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "active-replay-input-ready-decision" in text
        assert READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION in text
        assert "ACTIVE_REPLAY_INPUT_READY" in text
        assert "does not emit ACTIVE_REPLAY_INPUT_READY" in text
        assert "does not create active replay input" in text
        assert "does not run replay" in text
        assert "does not compute forward labels" in text
        assert "does not train weights" in text
        assert "does not create active stock profiles" in text
        assert "does not create real buy-review eligibility" in text
        assert "does not authorize trading" in text

    checkpoint_text = checkpoint.read_text(encoding="utf-8")
    assert "v1.36.0" in checkpoint_text
    assert "PAPER_WORKFLOW_READY" in checkpoint_text
    assert "0e6af6622f83" in checkpoint_text
    source_text = source_note.read_text(encoding="utf-8")
    assert "docs/project_sources" in source_text
    assert "intentionally absent from Git" in source_text
    assert "after tag v1.36.0" in source_text
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


def _mutate_json(path: Path, updates: dict[str, object]) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
