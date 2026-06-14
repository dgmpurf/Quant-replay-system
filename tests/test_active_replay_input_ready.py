from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from quant_replay_system.active_replay_input_ready import (
    ACTIVE_REPLAY_INPUT_READY_ATTESTATION_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_AUTHORITY_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EVIDENCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_PIT_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_REVIEW_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_SOURCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_TAXONOMY_BLOCKED,
    NO_ACTIVE_REPLAY_INPUT_READY_GOVERNANCE_INPUT,
    READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY,
    ActiveReplayInputReadySettings,
    run_active_replay_input_ready,
)
from quant_replay_system.active_replay_input_ready_health import check_active_replay_input_ready_health
from quant_replay_system.active_replay_input_ready_index import build_active_replay_input_ready_index
from quant_replay_system.active_replay_input_ready_status import (
    ACTIVE_REPLAY_INPUT_READY_HEALTH_FAILED,
    ACTIVE_REPLAY_INPUT_READY_NO_INPUT,
    ACTIVE_REPLAY_INPUT_READY_READY_TO_EMIT,
    run_active_replay_input_ready_status,
)


def test_no_input_writes_report_only_artifacts_with_safe_defaults(tmp_path: Path) -> None:
    result = run_active_replay_input_ready(
        ActiveReplayInputReadySettings(output_dir=_active_ready_output_dir(tmp_path))
    )

    assert result.status == NO_ACTIVE_REPLAY_INPUT_READY_GOVERNANCE_INPUT
    assert result.workflow_stage == NO_ACTIVE_REPLAY_INPUT_READY_GOVERNANCE_INPUT
    assert result.ready_to_emit_active_replay_input_ready is False
    _assert_never_active(result)
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_path.is_relative_to(_active_ready_output_dir(tmp_path))

    for key in _required_artifact_keys():
        assert result.artifact_paths[key].exists()

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == NO_ACTIVE_REPLAY_INPUT_READY_GOVERNANCE_INPUT
    assert metadata["ready_to_emit_active_replay_input_ready"] is False
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_ready_emitted"] is False
    assert metadata["replay_execution_allowed"] is False
    assert metadata["replay_decisions_exist"] is False
    assert metadata["forward_labels_allowed"] is False
    assert metadata["forward_labels_exist"] is False
    assert metadata["training_allowed"] is False
    assert metadata["weights_trained"] is False
    assert metadata["stock_profile_allowed"] is False
    assert metadata["active_stock_profile_exists"] is False
    assert metadata["buy_review_allowed"] is False
    assert metadata["real_buy_review_eligible"] is False
    assert metadata["trading_allowed"] is False
    assert metadata["order_placed"] is False
    assert metadata["broker_api_called"] is False
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert metadata["status"] != "ACTIVE_REPLAY_INPUT_READY"
    assert metadata["workflow_stage"] != "ACTIVE_REPLAY_INPUT_READY"


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("ready_decision_artifact_path", ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED),
        ("ready_decision_health_artifact_path", ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED),
        ("ready_decision_status_artifact_path", ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED),
        ("governance_request_manifest_path", ACTIVE_REPLAY_INPUT_READY_REVIEW_BLOCKED),
        ("final_authority_manifest_path", ACTIVE_REPLAY_INPUT_READY_AUTHORITY_BLOCKED),
        ("final_attestation_manifest_path", ACTIVE_REPLAY_INPUT_READY_ATTESTATION_BLOCKED),
        ("pit_source_evidence_bundle_path", ACTIVE_REPLAY_INPUT_READY_EVIDENCE_BLOCKED),
        ("taxonomy_evidence_bundle_path", ACTIVE_REPLAY_INPUT_READY_TAXONOMY_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(
    tmp_path: Path, setting_name: str, expected_status: str
) -> None:
    settings = replace(_happy_settings(tmp_path), **{setting_name: None})

    result = run_active_replay_input_ready(settings)

    assert result.status == expected_status
    assert result.ready_to_emit_active_replay_input_ready is False
    _assert_never_active(result)


@pytest.mark.parametrize(
    ("path_name", "override", "expected_status"),
    [
        (
            "ready_decision_artifact_path",
            {"status": "NO_ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT"},
            ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED,
        ),
        (
            "ready_decision_health_artifact_path",
            {"health_status": "FAIL"},
            ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED,
        ),
        (
            "ready_decision_status_artifact_path",
            {"status": "READY_DECISION_BLOCKED"},
            ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED,
        ),
        (
            "governance_request_manifest_path",
            {"request_result": "REJECTED"},
            ACTIVE_REPLAY_INPUT_READY_REVIEW_BLOCKED,
        ),
        (
            "final_authority_manifest_path",
            {"authority_result": "REJECTED"},
            ACTIVE_REPLAY_INPUT_READY_AUTHORITY_BLOCKED,
        ),
        (
            "final_attestation_manifest_path",
            {"no_trading_authority_attested": False},
            ACTIVE_REPLAY_INPUT_READY_ATTESTATION_BLOCKED,
        ),
        (
            "pit_source_evidence_bundle_path",
            {"accepted_pit_universe_evidence_attached": False},
            ACTIVE_REPLAY_INPUT_READY_PIT_BLOCKED,
        ),
        (
            "pit_source_evidence_bundle_path",
            {"source_hash_coverage_attached": False},
            ACTIVE_REPLAY_INPUT_READY_SOURCE_BLOCKED,
        ),
        (
            "pit_source_evidence_bundle_path",
            {"factor_observation_coverage_attached": False},
            ACTIVE_REPLAY_INPUT_READY_EVIDENCE_BLOCKED,
        ),
        (
            "taxonomy_evidence_bundle_path",
            {"not_fixed_12_only": False},
            ACTIVE_REPLAY_INPUT_READY_TAXONOMY_BLOCKED,
        ),
        (
            "leakage_side_effect_evidence_bundle_path",
            {"no_future_labels": False},
            ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED,
        ),
        (
            "leakage_side_effect_evidence_bundle_path",
            {"no_data_raw_written": False},
            ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED,
        ),
        (
            "overclaim_evidence_bundle_path",
            {"ready_to_emit_not_active_replay_input_ready": False},
            ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED,
        ),
    ],
)
def test_manifest_gate_failures_block(
    tmp_path: Path, path_name: str, override: dict[str, object], expected_status: str
) -> None:
    settings = _happy_settings(tmp_path)
    path = getattr(settings, path_name)
    _patch_json(path, override)

    result = run_active_replay_input_ready(settings)

    assert result.status == expected_status
    assert result.ready_to_emit_active_replay_input_ready is False
    _assert_never_active(result)


@pytest.mark.parametrize(
    ("unsafe_field", "expected_status"),
    [
        ("active_replay_input_ready", ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("active_replay_input", ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("active_ready_emitted", ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("replay_execution_allowed", ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("replay_decisions_exist", ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED),
        ("forward_labels_allowed", ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("forward_labels_exist", ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED),
        ("training_allowed", ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("weights_trained", ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED),
        ("stock_profile_allowed", ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("active_stock_profile_exists", ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED),
        ("buy_review_allowed", ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("real_buy_review_eligible", ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED),
        ("trading_allowed", ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
        ("order_placed", ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("message_sent", ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("llm_api_called", ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("external_api_called", ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("cache_mutated", ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("data_raw_written", ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("data_processed_written", ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("data_cache_written", ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("broker_api_called", ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED),
        ("approved_for_paper", ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED),
    ],
)
def test_unsafe_ready_decision_flags_block(
    tmp_path: Path, unsafe_field: str, expected_status: str
) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.ready_decision_artifact_path, {unsafe_field: True})

    result = run_active_replay_input_ready(settings)

    assert result.status == expected_status
    assert result.ready_to_emit_active_replay_input_ready is False
    _assert_never_active(result)


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    settings = ActiveReplayInputReadySettings(output_dir=tmp_path / "unsafe")

    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_active_replay_input_ready(settings)


def test_happy_path_reaches_ready_to_emit_without_active_ready_emission(tmp_path: Path) -> None:
    result = run_active_replay_input_ready(_happy_settings(tmp_path))

    assert result.status == READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY
    assert result.workflow_stage == READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY
    assert result.ready_to_emit_active_replay_input_ready is True
    _assert_never_active(result)
    assert result.blocker_count == 0
    assert result.overclaim_guard_pass_count == result.overclaim_guard_total_count
    assert result.status != "ACTIVE_REPLAY_INPUT_READY"

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY
    assert metadata["ready_to_emit_active_replay_input_ready"] is True
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_ready_emitted"] is False
    assert metadata["status"] != "ACTIVE_REPLAY_INPUT_READY"

    candidate = json.loads(result.artifact_paths["ready_candidate"].read_text(encoding="utf-8"))
    assert candidate["status"] == READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY
    assert candidate["ready_to_emit_active_replay_input_ready"] is True
    assert candidate["active_replay_input_ready"] is False
    assert candidate["active_replay_input"] is False
    assert candidate["active_ready_emitted"] is False
    assert candidate["status"] != "ACTIVE_REPLAY_INPUT_READY"

    report = result.artifact_paths["active_ready_report"].read_text(encoding="utf-8")
    assert "not ACTIVE_REPLAY_INPUT_READY" in report
    assert "does not create active replay input" in report
    assert "does not run replay" in report

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_cli_active_replay_input_ready_runs_without_active_ready_emission(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "active-replay-input-ready",
            "--ready-decision-artifact-path",
            str(settings.ready_decision_artifact_path),
            "--ready-decision-health-artifact-path",
            str(settings.ready_decision_health_artifact_path),
            "--ready-decision-status-artifact-path",
            str(settings.ready_decision_status_artifact_path),
            "--governance-audit-path",
            str(settings.governance_audit_path),
            "--governance-request-manifest-path",
            str(settings.governance_request_manifest_path),
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

    assert "active_ready_run_id:" in completed.stdout
    assert f"status: {READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY}" in completed.stdout
    assert "ready_to_emit_active_replay_input_ready: True" in completed.stdout
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


def test_artifact_views_are_registered_without_research_status_checkpoint_or_project_source() -> None:
    help_text = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout

    assert "active-replay-input-ready" in help_text
    assert "active-replay-input-ready-index" in help_text
    assert "active-replay-input-ready-health" in help_text
    assert "active-replay-input-ready-status" in help_text
    assert "latest_active_replay_input_ready_run_id" not in Path(
        "src/quant_replay_system/local_research_dashboard.py"
    ).read_text(encoding="utf-8")
    assert not Path("docs/project_sources").exists()
    assert not Path("docs/release_checkpoint_v1.37.0.md").exists()


def test_index_discovers_no_input_and_ready_to_emit_artifacts(tmp_path: Path) -> None:
    root = _active_ready_output_dir(tmp_path)
    no_input = run_active_replay_input_ready(ActiveReplayInputReadySettings(output_dir=root))
    ready = run_active_replay_input_ready(_happy_settings(tmp_path))

    result = build_active_replay_input_ready_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 2
    assert set(result.index_frame["active_ready_run_id"]) == {
        no_input.active_ready_run_id,
        ready.active_ready_run_id,
    }
    ready_row = result.index_frame[result.index_frame["active_ready_run_id"] == ready.active_ready_run_id].iloc[0]
    assert ready_row["status"] == READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY
    assert ready_row["ready_to_emit_active_replay_input_ready"] is True
    assert ready_row["active_replay_input_ready"] is False
    assert ready_row["active_replay_input"] is False
    assert ready_row["active_ready_emitted"] is False
    assert ready_row["replay_execution_allowed"] is False
    assert ready_row["replay_decisions_exist"] is False
    assert ready_row["forward_labels_allowed"] is False
    assert ready_row["forward_labels_exist"] is False
    assert ready_row["training_allowed"] is False
    assert ready_row["weights_trained"] is False
    assert ready_row["stock_profile_allowed"] is False
    assert ready_row["active_stock_profile_exists"] is False
    assert ready_row["buy_review_allowed"] is False
    assert ready_row["real_buy_review_eligible"] is False
    assert ready_row["trading_allowed"] is False
    assert ready_row["order_placed"] is False
    assert ready_row["broker_api_called"] is False


def test_health_passes_for_valid_no_input_and_ready_to_emit_artifacts(tmp_path: Path) -> None:
    root = _active_ready_output_dir(tmp_path)
    run_active_replay_input_ready(ActiveReplayInputReadySettings(output_dir=root))
    no_input_health = check_active_replay_input_ready_health(root=root, output_dir=root / "health_no_input")
    assert no_input_health.status == "PASS"

    ready_root = _active_ready_output_dir(tmp_path / "ready")
    settings = _happy_settings(tmp_path / "ready")
    run_active_replay_input_ready(settings)
    ready_health = check_active_replay_input_ready_health(root=ready_root, output_dir=ready_root / "health")
    assert ready_health.status == "PASS"


@pytest.mark.parametrize(
    "unsafe_field",
    [
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
def test_health_fails_for_unsafe_flags(tmp_path: Path, unsafe_field: str) -> None:
    root = _active_ready_output_dir(tmp_path)
    result = run_active_replay_input_ready(_happy_settings(tmp_path))
    _patch_json(result.artifact_paths["metadata"], {unsafe_field: True})

    health = check_active_replay_input_ready_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert unsafe_field.upper() in " ".join(health.health_frame["issue_code"].astype(str).tolist())


def test_health_fails_for_active_ready_status_and_overclaim_guard_failure(tmp_path: Path) -> None:
    root = _active_ready_output_dir(tmp_path)
    result = run_active_replay_input_ready(_happy_settings(tmp_path))
    _patch_json(
        result.artifact_paths["metadata"],
        {
            "status": "ACTIVE_REPLAY_INPUT_READY",
            "workflow_stage": "ACTIVE_REPLAY_INPUT_READY",
            "overclaim_guard_pass_count": 1,
            "overclaim_guard_total_count": 2,
        },
    )

    health = check_active_replay_input_ready_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    issue_codes = set(health.health_frame["issue_code"])
    assert "ACTIVE_REPLAY_INPUT_READY_UNEXPECTED" in issue_codes
    assert "OVERCLAIM_GUARD_FAILED" in issue_codes


def test_status_reports_no_input_and_ready_to_emit_with_safety_text(tmp_path: Path) -> None:
    root = _active_ready_output_dir(tmp_path)
    run_active_replay_input_ready(ActiveReplayInputReadySettings(output_dir=root))
    no_input = run_active_replay_input_ready_status(root=root, output_dir=root / "status")
    assert no_input.workflow_stage == ACTIVE_REPLAY_INPUT_READY_NO_INPUT
    assert no_input.ready_to_emit_active_replay_input_ready is False
    assert no_input.active_replay_input_ready is False

    ready_root = _active_ready_output_dir(tmp_path / "ready")
    ready = run_active_replay_input_ready(_happy_settings(tmp_path / "ready"))
    status = run_active_replay_input_ready_status(root=ready_root, output_dir=ready_root / "status")

    assert status.latest_active_ready_run_id == ready.active_ready_run_id
    assert status.workflow_stage == ACTIVE_REPLAY_INPUT_READY_READY_TO_EMIT
    assert status.ready_to_emit_active_replay_input_ready is True
    assert status.active_replay_input_ready is False
    assert status.active_replay_input is False
    text = status.artifact_paths["status_report"].read_text(encoding="utf-8")
    assert "READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY is not ACTIVE_REPLAY_INPUT_READY" in text
    assert "ACTIVE_REPLAY_INPUT_READY is not emitted" in text
    assert "active replay input is not created" in text
    assert "replay is not run" in text
    assert "replay decisions are not created" in text
    assert "labels are not computed" in text
    assert "training is not run" in text
    assert "stock_profile is not created" in text
    assert "buy-review eligibility is not created" in text
    assert "trading is not authorized" in text


def test_status_reports_health_failed_for_unsafe_latest_artifact(tmp_path: Path) -> None:
    root = _active_ready_output_dir(tmp_path)
    result = run_active_replay_input_ready(_happy_settings(tmp_path))
    _patch_json(result.artifact_paths["metadata"], {"active_replay_input_ready": True})

    status = run_active_replay_input_ready_status(root=root, output_dir=root / "status")

    assert status.workflow_stage == ACTIVE_REPLAY_INPUT_READY_HEALTH_FAILED
    assert status.health_status == "FAIL"
    assert status.active_replay_input_ready is False


def test_cli_artifact_view_commands_run(tmp_path: Path) -> None:
    root = _active_ready_output_dir(tmp_path)
    run_active_replay_input_ready(_happy_settings(tmp_path))

    env = {**os.environ, "PYTHONPATH": "src"}
    index = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "active-replay-input-ready-index",
            "--root",
            str(root),
            "--output-dir",
            str(root / "index"),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "artifact_count: 1" in index.stdout

    health = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "active-replay-input-ready-health",
            "--root",
            str(root),
            "--output-dir",
            str(root / "health"),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "status: PASS" in health.stdout

    status = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "active-replay-input-ready-status",
            "--root",
            str(root),
            "--output-dir",
            str(root / "status"),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "workflow_stage: ACTIVE_REPLAY_INPUT_READY_READY_TO_EMIT" in status.stdout
    assert "active_replay_input_ready: False" in status.stdout


def _active_ready_output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "active_replay_input_ready_v0_1"


def _happy_settings(tmp_path: Path) -> ActiveReplayInputReadySettings:
    root = tmp_path / "fixtures"
    root.mkdir(parents=True, exist_ok=True)
    ready_decision = _write_json(root / "ready_decision.json", _ready_decision_payload())
    health = _write_json(root / "ready_decision_health.json", {"health_status": "PASS"})
    status = _write_json(
        root / "ready_decision_status.json",
        {
            "status": "READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION",
            "workflow_stage": "READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION",
            "ready_for_active_replay_input_ready_decision": True,
            "active_replay_input_ready": False,
            "active_replay_input": False,
            "active_ready_emitted": False,
        },
    )
    governance_audit = root / "governance_audit.md"
    governance_audit.write_text("governance audit accepted for report-only fixture", encoding="utf-8")
    return ActiveReplayInputReadySettings(
        ready_decision_artifact_path=ready_decision,
        ready_decision_health_artifact_path=health,
        ready_decision_status_artifact_path=status,
        governance_audit_path=governance_audit,
        governance_request_manifest_path=_write_json(
            root / "governance_request.json",
            {"request_result": "PASS", "report_only": True, "diagnostic_only": True},
        ),
        final_authority_manifest_path=_write_json(
            root / "authority.json",
            {
                "authority_result": "PASS",
                "primary_reviewer": "reviewer_a",
                "second_reviewer": "reviewer_b",
                "authority_scope": "report_only_active_readiness_governance",
            },
        ),
        final_attestation_manifest_path=_write_json(
            root / "attestation.json",
            {
                "primary_reviewer_attested": True,
                "second_reviewer_attested": True,
                "no_active_input_creation_attested": True,
                "no_replay_execution_attested": True,
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
        output_dir=_active_ready_output_dir(tmp_path),
    )


def _ready_decision_payload() -> dict[str, object]:
    return {
        "decision_run_id": "ready123",
        "status": "READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION",
        "workflow_stage": "READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION",
        "ready_for_active_replay_input_ready_decision": True,
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


def _required_artifact_keys() -> list[str]:
    return [
        "metadata",
        "active_ready_report",
        "active_ready_precondition_results",
        "active_ready_authority_results",
        "ready_decision_lineage_results",
        "active_ready_attestation_results",
        "pit_source_evidence_results",
        "taxonomy_evidence_results",
        "leakage_side_effect_guard_results",
        "overclaim_guard_results",
        "ready_candidate",
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
