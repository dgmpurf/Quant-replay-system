import json
import os
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.local_research_dashboard import (
    LocalResearchDashboardResult,
    infer_local_research_next_action,
    infer_local_research_workflow_stage,
    run_local_research_dashboard,
)
from quant_replay_system.historical_replay_input_gate_validator_fixture import (
    build_historical_replay_input_gate_validator_fixture,
)
from quant_replay_system.historical_replay_input_gate_validator import (
    run_historical_replay_input_gate_validator,
)
from quant_replay_system.minimal_replay_input_package_fixture_smoke import (
    MinimalReplayInputPackageFixtureSmokeSettings,
    run_minimal_replay_input_package_fixture_smoke,
)
from quant_replay_system.active_replay_input_promotion import (
    ActiveReplayInputPromotionSettings,
    run_active_replay_input_promotion,
)
from quant_replay_system.active_replay_input_acceptance import (
    ActiveReplayInputAcceptanceSettings,
    run_active_replay_input_acceptance,
)
from quant_replay_system.active_replay_input_active_ready import (
    ActiveReplayInputActiveReadySettings,
    run_active_replay_input_active_ready,
)
from quant_replay_system.active_replay_input_final_review import (
    ActiveReplayInputFinalReviewSettings,
    run_active_replay_input_final_review,
)
from quant_replay_system.active_replay_input_emission import (
    ActiveReplayInputEmissionSettings,
    run_active_replay_input_emission,
)
from quant_replay_system.active_replay_input_ready import (
    ActiveReplayInputReadySettings,
    run_active_replay_input_ready,
)
from quant_replay_system.actual_replay_execute import ACTUAL_REPLAY_EXECUTED, run_actual_replay_execute
from quant_replay_system.forward_return_label import FORWARD_RETURN_LABELS_CREATED, run_forward_return_label
from quant_replay_system.replay_decision_freeze import REPLAY_DECISION_FROZEN, run_replay_decision_freeze
from quant_replay_system.training_evaluation import (
    TRAINING_EVALUATION_DATASET_CREATED,
    run_training_evaluation,
)
from quant_replay_system.pit_evidence_checklist_validator import SUMMARY_COLUMNS, VALIDATION_COLUMNS
from quant_replay_system.replay_substrate_schema_fixture import build_replay_substrate_schema_fixture
from quant_replay_system.reviewer_no_hit_source_coverage_acceptance import (
    build_reviewer_no_hit_source_coverage_acceptance,
)
from quant_replay_system.reviewer_no_hit_acceptance_downstream_impact import (
    build_reviewer_no_hit_acceptance_downstream_impact,
)
from quant_replay_system.universe_profile_policy_audit import build_universe_profile_policy_audit
from test_actual_replay_execute import _happy_settings as _actual_replay_happy_settings
from test_forward_return_label import _happy_settings as _forward_return_label_happy_settings
from test_replay_decision_freeze import _happy_settings as _replay_decision_freeze_happy_settings
from test_training_evaluation import _happy_settings as _training_evaluation_happy_settings


DECISION_DATE = "2024-05-20"
UNIVERSE = "etf_core"


def test_dashboard_handles_no_artifacts(tmp_path: Path) -> None:
    result = run_local_research_dashboard(root=_reports_root(tmp_path), output_dir=tmp_path / "dashboard")

    assert isinstance(result, LocalResearchDashboardResult)
    assert result.workflow_stage == "NO_DATA"
    assert result.status == "WARN"
    assert result.next_manual_action == "Run data-pipeline."


def test_dashboard_detects_data_preparation_workflow_status_artifact(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _data_preparation_status(root)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.data_preparation_status == "PASS"
    assert result.workflow_stage == "DATA_PREPARATION_READY"


def test_dashboard_detects_current_candidate_artifacts(tmp_path: Path) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.current_candidate_status == "READY"
    assert result.latest_decision_date == DECISION_DATE
    assert result.workflow_stage == "CURRENT_CANDIDATES_READY"


def test_dashboard_detects_current_candidate_health_artifacts(tmp_path: Path) -> None:
    root = _workflow_to_current_candidate_health(_reports_root(tmp_path))

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.current_candidate_health_status == "PASS"
    assert result.workflow_stage == "CURRENT_CANDIDATES_HEALTH_READY"


def test_dashboard_includes_current_candidates_backfill_plan_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _current_candidates_backfill_plan_status(root, plan_id="plan-ready")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    plan_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "CURRENT_CANDIDATES_BACKFILL_PLAN_STATUS"
    ].iloc[0]

    assert result.latest_current_candidates_backfill_plan_id == "plan-ready"
    assert result.current_candidates_backfill_plan_status == "PASS"
    assert result.current_candidates_backfill_plan_stage == "CURRENT_CANDIDATES_BACKFILL_PLAN_READY"
    assert result.current_candidates_backfill_plan_health_status == "PASS"
    assert result.current_candidates_backfill_plan_selected_date_count == 8
    assert result.current_candidates_backfill_plan_first_signal_date == "2024-04-02"
    assert result.current_candidates_backfill_plan_last_signal_date == "2024-05-06"
    assert result.current_candidates_backfill_plan_warmup_trading_days == 60
    assert '"forward_10d_available_count": 8' in result.current_candidates_backfill_plan_forward_horizon_summary
    assert result.workflow_stage == "CURRENT_CANDIDATES_BACKFILL_PLAN_READY"
    assert plan_row["warning_classification"] == ""
    assert "before candidate generation" in result.next_manual_action


def test_dashboard_current_candidates_backfill_plan_ready_is_non_blocking(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _current_candidates_backfill_plan_status(root, plan_id="plan-non-blocking")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    plan_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "CURRENT_CANDIDATES_BACKFILL_PLAN_STATUS"
    ].iloc[0]

    assert result.status != "FAIL"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 0
    assert result.summary_frame.iloc[0]["actionable_warning_count"] == 0
    assert plan_row["warning_classification"] == ""


def test_dashboard_failed_current_candidates_backfill_plan_health_is_actionable_when_active(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _current_candidates_backfill_plan_status(
        root,
        plan_id="plan-fail",
        status="FAIL",
        workflow_stage="CURRENT_CANDIDATES_BACKFILL_PLAN_FAILED",
        health_status="FAIL",
        warning_count=0,
        error_count=1,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    plan_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "CURRENT_CANDIDATES_BACKFILL_PLAN_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "CURRENT_CANDIDATES_BACKFILL_PLAN_FAILED"
    assert result.current_candidates_backfill_plan_health_status == "FAIL"
    assert plan_row["warning_classification"] == "BLOCKING_ERROR"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 1
    assert "Repair current-candidates backfill plan artifacts" in result.next_manual_action


def test_dashboard_preserves_later_paper_priority_over_current_candidates_backfill_plan(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _current_candidates_backfill_plan_status(root, plan_id="plan-context", status="WARN")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    plan_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "CURRENT_CANDIDATES_BACKFILL_PLAN_STATUS"
    ].iloc[0]

    assert result.latest_current_candidates_backfill_plan_id == "plan-context"
    assert result.current_candidates_backfill_plan_stage == "CURRENT_CANDIDATES_BACKFILL_PLAN_READY"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert plan_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_exposes_legacy_backfill_plan_context_without_active_override(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _current_candidates_backfill_plan_status(
        root,
        plan_id="plan-active",
        legacy_plan_count=1,
        stale_plan_warning_count=1,
        legacy_missing_warmup_count=1,
        latest_plan_is_warmup_aware=True,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.latest_current_candidates_backfill_plan_id == "plan-active"
    assert result.current_candidates_backfill_plan_status == "PASS"
    assert result.current_candidates_backfill_plan_stage == "CURRENT_CANDIDATES_BACKFILL_PLAN_READY"
    assert result.current_candidates_backfill_plan_health_status == "PASS"
    assert result.current_candidates_backfill_plan_legacy_plan_count == 1
    assert result.current_candidates_backfill_plan_stale_plan_warning_count == 1
    assert result.current_candidates_backfill_plan_active_plan_issue_count == 0
    assert result.current_candidates_backfill_plan_active_plan_error_count == 0
    assert result.current_candidates_backfill_plan_legacy_missing_warmup_count == 1
    assert result.current_candidates_backfill_plan_latest_plan_is_warmup_aware is True
    assert result.workflow_stage == "CURRENT_CANDIDATES_BACKFILL_PLAN_READY"


def test_dashboard_exports_current_candidates_backfill_plan_fields_to_summary_and_metadata(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _current_candidates_backfill_plan_status(root, plan_id="plan-export")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_current_candidates_backfill_plan_id"] == "plan-export"
    assert row["current_candidates_backfill_plan_status"] == "PASS"
    assert row["current_candidates_backfill_plan_stage"] == "CURRENT_CANDIDATES_BACKFILL_PLAN_READY"
    assert row["current_candidates_backfill_plan_health_status"] == "PASS"
    assert row["current_candidates_backfill_plan_selected_date_count"] == "8"
    assert row["current_candidates_backfill_plan_warmup_trading_days"] == "60"
    assert '"forward_5d_available_count": 8' in row["current_candidates_backfill_plan_forward_horizon_summary"]
    assert row["current_candidates_backfill_plan_latest_plan_is_warmup_aware"] == "True"
    assert metadata["latest_current_candidates_backfill_plan_id"] == "plan-export"
    assert metadata["current_candidates_backfill_plan_health_status"] == "PASS"
    assert metadata["current_candidates_backfill_plan_selected_date_count"] == 8
    assert metadata["current_candidates_backfill_plan_latest_plan_is_warmup_aware"] is True
    assert metadata["component_statuses"]["latest_current_candidates_backfill_plan_id"] == "plan-export"


def test_cli_research_status_prints_current_candidates_backfill_plan_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = _reports_root(tmp_path)
    _current_candidates_backfill_plan_status(root, plan_id="plan-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_current_candidates_backfill_plan_id: plan-cli" in output.out
    assert "current_candidates_backfill_plan_status: PASS" in output.out
    assert "current_candidates_backfill_plan_stage: CURRENT_CANDIDATES_BACKFILL_PLAN_READY" in output.out
    assert "current_candidates_backfill_plan_health_status: PASS" in output.out
    assert "current_candidates_backfill_plan_selected_date_count: 8" in output.out
    assert "current_candidates_backfill_plan_latest_plan_is_warmup_aware: True" in output.out


def test_dashboard_includes_current_candidates_backfill_execution_manifest_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _current_candidates_backfill_execution_manifest_status(root, execution_manifest_id="manifest-blocked")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    manifest_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_STATUS"
    ].iloc[0]

    assert result.latest_current_candidates_backfill_execution_manifest_id == "manifest-blocked"
    assert result.current_candidates_backfill_execution_manifest_status == "WARN"
    assert (
        result.current_candidates_backfill_execution_manifest_stage
        == "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_BLOCKED"
    )
    assert result.current_candidates_backfill_execution_manifest_health_status == "PASS"
    assert result.current_candidates_backfill_execution_manifest_plan_id == "plan-a"
    assert result.current_candidates_backfill_execution_manifest_row_count == 8
    assert result.current_candidates_backfill_execution_manifest_ready_count == 0
    assert result.current_candidates_backfill_execution_manifest_blocked_count == 8
    assert result.current_candidates_backfill_execution_manifest_blocked_universe_as_of_count == 8
    assert result.workflow_stage == "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_BLOCKED"
    assert manifest_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert "no current-candidates were run" in result.next_manual_action


def test_dashboard_backfill_execution_manifest_ready_for_review_does_not_imply_execution(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _current_candidates_backfill_execution_manifest_status(
        root,
        execution_manifest_id="manifest-ready",
        status="PASS",
        workflow_stage="CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_READY_FOR_REVIEW",
        ready_count=8,
        blocked_count=0,
        blocked_universe_as_of_count=0,
        warning_count=0,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    manifest_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_READY_FOR_REVIEW"
    assert result.current_candidates_backfill_execution_manifest_ready_count == 8
    assert result.current_candidates_backfill_execution_manifest_blocked_count == 0
    assert manifest_row["warning_classification"] == ""
    assert "separate candidate generation" in result.next_manual_action
    assert result.audit_metadata["local_research_dashboard_only"] is True


def test_dashboard_failed_current_candidates_backfill_execution_manifest_health_is_actionable_when_active(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _current_candidates_backfill_execution_manifest_status(
        root,
        execution_manifest_id="manifest-fail",
        status="FAIL",
        workflow_stage="CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_FAILED",
        health_status="FAIL",
        warning_count=0,
        error_count=1,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    manifest_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_FAILED"
    assert manifest_row["warning_classification"] == "BLOCKING_ERROR"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 1
    assert "Repair execution manifest artifacts" in result.next_manual_action


def test_dashboard_preserves_later_paper_priority_over_backfill_execution_manifest(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _current_candidates_backfill_execution_manifest_status(root, execution_manifest_id="manifest-context")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    manifest_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_STATUS"
    ].iloc[0]

    assert result.latest_current_candidates_backfill_execution_manifest_id == "manifest-context"
    assert result.current_candidates_backfill_execution_manifest_blocked_universe_as_of_count == 8
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert manifest_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_exports_current_candidates_backfill_execution_manifest_fields_to_summary_and_metadata(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _current_candidates_backfill_execution_manifest_status(root, execution_manifest_id="manifest-export")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_current_candidates_backfill_execution_manifest_id"] == "manifest-export"
    assert row["current_candidates_backfill_execution_manifest_status"] == "WARN"
    assert row["current_candidates_backfill_execution_manifest_health_status"] == "PASS"
    assert row["current_candidates_backfill_execution_manifest_plan_id"] == "plan-a"
    assert row["current_candidates_backfill_execution_manifest_row_count"] == "8"
    assert row["current_candidates_backfill_execution_manifest_blocked_universe_as_of_count"] == "8"
    assert metadata["latest_current_candidates_backfill_execution_manifest_id"] == "manifest-export"
    assert metadata["current_candidates_backfill_execution_manifest_plan_id"] == "plan-a"
    assert metadata["current_candidates_backfill_execution_manifest_blocked_universe_as_of_count"] == 8
    assert (
        metadata["component_statuses"]["latest_current_candidates_backfill_execution_manifest_id"]
        == "manifest-export"
    )


def test_cli_research_status_prints_current_candidates_backfill_execution_manifest_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = _reports_root(tmp_path)
    _current_candidates_backfill_execution_manifest_status(root, execution_manifest_id="manifest-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_current_candidates_backfill_execution_manifest_id: manifest-cli" in output.out
    assert "current_candidates_backfill_execution_manifest_status: WARN" in output.out
    assert "current_candidates_backfill_execution_manifest_plan_id: plan-a" in output.out
    assert "current_candidates_backfill_execution_manifest_blocked_universe_as_of_count: 8" in output.out


def test_dashboard_includes_pit_universe_overlay_plan_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_plan_status(root, overlay_plan_id="overlay-needs-review")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    overlay_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_OVERLAY_PLAN_STATUS"
    ].iloc[0]

    assert result.latest_pit_universe_overlay_plan_id == "overlay-needs-review"
    assert result.pit_universe_overlay_plan_status == "WARN"
    assert result.pit_universe_overlay_plan_stage == "PIT_UNIVERSE_OVERLAY_PLAN_NEEDS_REVIEW"
    assert result.pit_universe_overlay_plan_health_status == "PASS"
    assert result.pit_universe_overlay_plan_row_count == 72
    assert result.pit_universe_overlay_plan_signal_date_count == 8
    assert result.pit_universe_overlay_plan_symbol_count == 9
    assert result.pit_universe_overlay_plan_needs_manual_review_count == 72
    assert result.pit_universe_overlay_plan_valid_for_signal_date_count == 0
    assert result.pit_universe_overlay_plan_survivorship_bias_warning_count == 72
    assert result.workflow_stage == "PIT_UNIVERSE_OVERLAY_PLAN_NEEDS_REVIEW"
    assert overlay_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert "manual review" in result.next_manual_action
    assert "not valid" in result.next_manual_action


def test_dashboard_pit_universe_overlay_needs_review_does_not_imply_candidate_generation(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_plan_status(root, overlay_plan_id="overlay-context")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    overlay_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_OVERLAY_PLAN_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "PIT_UNIVERSE_OVERLAY_PLAN_NEEDS_REVIEW"
    assert result.pit_universe_overlay_plan_valid_for_signal_date_count == 0
    assert overlay_row["actionable_warning_count"] == 0
    assert overlay_row["blocking_error_count"] == 0
    assert result.summary_frame.iloc[0]["expected_reviewable_warning_count"] == 1
    assert result.audit_metadata["local_research_dashboard_only"] is True
    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False


def test_dashboard_failed_pit_universe_overlay_plan_health_is_actionable_when_active(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_plan_status(
        root,
        overlay_plan_id="overlay-fail",
        status="FAIL",
        workflow_stage="PIT_UNIVERSE_OVERLAY_PLAN_FAILED",
        health_status="FAIL",
        warning_count=0,
        error_count=1,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    overlay_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_OVERLAY_PLAN_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "PIT_UNIVERSE_OVERLAY_PLAN_FAILED"
    assert overlay_row["warning_classification"] == "BLOCKING_ERROR"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 1
    assert "Repair PIT universe overlay plan artifacts" in result.next_manual_action


def test_dashboard_preserves_later_paper_priority_over_pit_universe_overlay_plan(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_plan_status(root, overlay_plan_id="overlay-paper-context")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    overlay_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_OVERLAY_PLAN_STATUS"
    ].iloc[0]

    assert result.latest_pit_universe_overlay_plan_id == "overlay-paper-context"
    assert result.pit_universe_overlay_plan_needs_manual_review_count == 72
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert overlay_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_exports_pit_universe_overlay_plan_fields_to_summary_and_metadata(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_plan_status(root, overlay_plan_id="overlay-export")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_pit_universe_overlay_plan_id"] == "overlay-export"
    assert row["pit_universe_overlay_plan_status"] == "WARN"
    assert row["pit_universe_overlay_plan_stage"] == "PIT_UNIVERSE_OVERLAY_PLAN_NEEDS_REVIEW"
    assert row["pit_universe_overlay_plan_health_status"] == "PASS"
    assert row["pit_universe_overlay_plan_row_count"] == "72"
    assert row["pit_universe_overlay_plan_needs_manual_review_count"] == "72"
    assert row["pit_universe_overlay_plan_valid_for_signal_date_count"] == "0"
    assert row["pit_universe_overlay_plan_survivorship_bias_warning_count"] == "72"
    assert metadata["latest_pit_universe_overlay_plan_id"] == "overlay-export"
    assert metadata["pit_universe_overlay_plan_needs_manual_review_count"] == 72
    assert metadata["pit_universe_overlay_plan_valid_for_signal_date_count"] == 0
    assert metadata["component_statuses"]["latest_pit_universe_overlay_plan_id"] == "overlay-export"


def test_cli_research_status_prints_pit_universe_overlay_plan_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_plan_status(root, overlay_plan_id="overlay-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_pit_universe_overlay_plan_id: overlay-cli" in output.out
    assert "pit_universe_overlay_plan_status: WARN" in output.out
    assert "pit_universe_overlay_plan_stage: PIT_UNIVERSE_OVERLAY_PLAN_NEEDS_REVIEW" in output.out
    assert "pit_universe_overlay_plan_needs_manual_review_count: 72" in output.out
    assert "pit_universe_overlay_plan_survivorship_bias_warning_count: 72" in output.out


def test_dashboard_includes_pit_universe_overlay_review_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_review_status(root, review_id="review-needs-evidence")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    review_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_OVERLAY_REVIEW_STATUS"
    ].iloc[0]

    assert result.latest_pit_universe_overlay_review_id == "review-needs-evidence"
    assert result.pit_universe_overlay_review_status == "WARN"
    assert result.pit_universe_overlay_review_stage == "PIT_UNIVERSE_OVERLAY_REVIEW_NEEDS_MORE_EVIDENCE"
    assert result.pit_universe_overlay_review_health_status == "PASS"
    assert result.pit_universe_overlay_review_approved_count == 1
    assert result.pit_universe_overlay_review_valid_for_signal_date_count == 1
    assert result.pit_universe_overlay_review_needs_more_evidence_count == 1
    assert result.pit_universe_overlay_review_unresolved_survivorship_warning_count == 1
    assert result.workflow_stage == "PIT_UNIVERSE_OVERLAY_REVIEW_NEEDS_MORE_EVIDENCE"
    assert review_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert "more evidence" in result.next_manual_action


def test_dashboard_pit_universe_overlay_review_approved_rows_do_not_imply_candidate_generation(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_review_status(
        root,
        review_id="review-approved",
        status="PASS",
        workflow_stage="PIT_UNIVERSE_OVERLAY_REVIEW_HAS_APPROVED_ROWS",
        approved_count=1,
        valid_for_signal_date_count=1,
        needs_more_evidence_count=0,
        unresolved_survivorship_warning_count=0,
        warning_count=0,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    review_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_OVERLAY_REVIEW_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "PIT_UNIVERSE_OVERLAY_REVIEW_HAS_APPROVED_ROWS"
    assert result.pit_universe_overlay_review_approved_count == 1
    assert result.pit_universe_overlay_review_valid_for_signal_date_count == 1
    assert review_row["blocking_error_count"] == 0
    assert result.audit_metadata["local_research_dashboard_only"] is True
    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False


def test_dashboard_failed_pit_universe_overlay_review_health_is_actionable_when_active(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_review_status(
        root,
        review_id="review-fail",
        status="FAIL",
        workflow_stage="PIT_UNIVERSE_OVERLAY_REVIEW_FAILED",
        health_status="FAIL",
        warning_count=0,
        error_count=1,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    review_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_OVERLAY_REVIEW_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "PIT_UNIVERSE_OVERLAY_REVIEW_FAILED"
    assert review_row["warning_classification"] == "BLOCKING_ERROR"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 1
    assert "Repair PIT universe overlay review artifacts" in result.next_manual_action


def test_dashboard_preserves_later_paper_priority_over_pit_universe_overlay_review(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_review_status(root, review_id="review-paper-context")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    review_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_OVERLAY_REVIEW_STATUS"
    ].iloc[0]

    assert result.latest_pit_universe_overlay_review_id == "review-paper-context"
    assert result.pit_universe_overlay_review_needs_more_evidence_count == 1
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert review_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_exports_pit_universe_overlay_review_fields_to_summary_and_metadata(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_review_status(root, review_id="review-export")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_pit_universe_overlay_review_id"] == "review-export"
    assert row["pit_universe_overlay_review_status"] == "WARN"
    assert row["pit_universe_overlay_review_stage"] == "PIT_UNIVERSE_OVERLAY_REVIEW_NEEDS_MORE_EVIDENCE"
    assert row["pit_universe_overlay_review_health_status"] == "PASS"
    assert row["pit_universe_overlay_review_approved_count"] == "1"
    assert row["pit_universe_overlay_review_valid_for_signal_date_count"] == "1"
    assert row["pit_universe_overlay_review_needs_more_evidence_count"] == "1"
    assert metadata["latest_pit_universe_overlay_review_id"] == "review-export"
    assert metadata["pit_universe_overlay_review_approved_count"] == 1
    assert metadata["component_statuses"]["latest_pit_universe_overlay_review_id"] == "review-export"


def test_cli_research_status_prints_pit_universe_overlay_review_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_review_status(root, review_id="review-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_pit_universe_overlay_review_id: review-cli" in output.out
    assert "pit_universe_overlay_review_status: WARN" in output.out
    assert "pit_universe_overlay_review_stage: PIT_UNIVERSE_OVERLAY_REVIEW_NEEDS_MORE_EVIDENCE" in output.out
    assert "pit_universe_overlay_review_approved_count: 1" in output.out
    assert "pit_universe_overlay_review_unresolved_survivorship_warning_count: 1" in output.out


def test_dashboard_includes_pit_universe_export_readiness_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_export_readiness_status(root, export_readiness_id="export-blocked")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    readiness_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_EXPORT_READINESS_STATUS"
    ].iloc[0]

    assert result.latest_pit_universe_export_readiness_id == "export-blocked"
    assert result.pit_universe_export_readiness_status == "WARN"
    assert result.pit_universe_export_readiness_stage == "PIT_UNIVERSE_EXPORT_BLOCKED_NO_APPROVED_ROWS"
    assert result.pit_universe_export_readiness_health_status == "PASS"
    assert result.pit_universe_export_readiness_review_id == "review-a"
    assert result.pit_universe_export_readiness_approved_count == 0
    assert result.pit_universe_export_readiness_export_ready_count == 0
    assert result.pit_universe_export_readiness_blocked_count == 72
    assert result.pit_universe_export_readiness_no_approved_rows is True
    assert result.workflow_stage == "PIT_UNIVERSE_EXPORT_BLOCKED_NO_APPROVED_ROWS"
    assert readiness_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert "Approve PIT universe rows" in result.next_manual_action


def test_dashboard_failed_pit_universe_export_readiness_health_is_actionable_when_active(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_export_readiness_status(
        root,
        export_readiness_id="export-fail",
        status="FAIL",
        workflow_stage="PIT_UNIVERSE_EXPORT_READINESS_FAILED",
        health_status="FAIL",
        warning_count=0,
        error_count=1,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    readiness_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_EXPORT_READINESS_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "PIT_UNIVERSE_EXPORT_READINESS_FAILED"
    assert readiness_row["warning_classification"] == "BLOCKING_ERROR"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 1
    assert "Repair PIT universe export-readiness artifacts" in result.next_manual_action


def test_dashboard_preserves_later_paper_priority_over_pit_universe_export_readiness(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_export_readiness_status(root, export_readiness_id="export-paper-context")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    readiness_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_EXPORT_READINESS_STATUS"
    ].iloc[0]

    assert result.latest_pit_universe_export_readiness_id == "export-paper-context"
    assert result.pit_universe_export_readiness_blocked_count == 72
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert readiness_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_exports_pit_universe_export_readiness_fields_to_summary_and_metadata(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_export_readiness_status(root, export_readiness_id="export-summary")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_pit_universe_export_readiness_id"] == "export-summary"
    assert row["pit_universe_export_readiness_status"] == "WARN"
    assert row["pit_universe_export_readiness_stage"] == "PIT_UNIVERSE_EXPORT_BLOCKED_NO_APPROVED_ROWS"
    assert row["pit_universe_export_readiness_health_status"] == "PASS"
    assert row["pit_universe_export_readiness_approved_count"] == "0"
    assert row["pit_universe_export_readiness_blocked_count"] == "72"
    assert metadata["latest_pit_universe_export_readiness_id"] == "export-summary"
    assert metadata["pit_universe_export_readiness_blocked_count"] == 72
    assert metadata["component_statuses"]["latest_pit_universe_export_readiness_id"] == "export-summary"


def test_cli_research_status_prints_pit_universe_export_readiness_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_overlay_export_readiness_status(root, export_readiness_id="export-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_pit_universe_export_readiness_id: export-cli" in output.out
    assert "pit_universe_export_readiness_status: WARN" in output.out
    assert "pit_universe_export_readiness_stage: PIT_UNIVERSE_EXPORT_BLOCKED_NO_APPROVED_ROWS" in output.out
    assert "pit_universe_export_readiness_approved_count: 0" in output.out
    assert "pit_universe_export_readiness_blocked_count: 72" in output.out


def test_dashboard_includes_pit_universe_export_staging_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_export_staging_status(root, staging_id="stage-blocked")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    staging_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_EXPORT_STAGING_STATUS"
    ].iloc[0]

    assert result.latest_pit_universe_export_staging_id == "stage-blocked"
    assert result.pit_universe_export_staging_status == "WARN"
    assert result.pit_universe_export_staging_stage == "PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS"
    assert result.pit_universe_export_staging_health_status == "PASS"
    assert result.pit_universe_export_staging_export_readiness_id == "export-a"
    assert result.pit_universe_export_staging_export_ready_input_count == 0
    assert result.pit_universe_export_staging_staged_row_count == 0
    assert result.pit_universe_export_staging_blocked_count == 72
    assert result.pit_universe_export_staging_no_ready_rows is True
    assert result.workflow_stage == "PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS"
    assert staging_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert "Complete PIT universe review evidence" in result.next_manual_action


def test_dashboard_preserves_later_paper_priority_over_pit_universe_export_staging(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_export_staging_status(root, staging_id="stage-paper-context")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    staging_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_EXPORT_STAGING_STATUS"
    ].iloc[0]

    assert result.latest_pit_universe_export_staging_id == "stage-paper-context"
    assert result.pit_universe_export_staging_blocked_count == 72
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert staging_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_exports_pit_universe_export_staging_fields_to_summary_and_metadata(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_export_staging_status(root, staging_id="stage-summary")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_pit_universe_export_staging_id"] == "stage-summary"
    assert row["pit_universe_export_staging_status"] == "WARN"
    assert row["pit_universe_export_staging_stage"] == "PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS"
    assert row["pit_universe_export_staging_health_status"] == "PASS"
    assert row["pit_universe_export_staging_staged_row_count"] == "0"
    assert row["pit_universe_export_staging_blocked_count"] == "72"
    assert metadata["latest_pit_universe_export_staging_id"] == "stage-summary"
    assert metadata["pit_universe_export_staging_blocked_count"] == 72
    assert metadata["component_statuses"]["latest_pit_universe_export_staging_id"] == "stage-summary"


def test_cli_research_status_prints_pit_universe_export_staging_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_export_staging_status(root, staging_id="stage-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_pit_universe_export_staging_id: stage-cli" in output.out
    assert "pit_universe_export_staging_status: WARN" in output.out
    assert "pit_universe_export_staging_stage: PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS" in output.out
    assert "pit_universe_export_staging_staged_row_count: 0" in output.out
    assert "pit_universe_export_staging_blocked_count: 72" in output.out


def test_dashboard_includes_pit_universe_evidence_helper_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_evidence_completion_helper_status(root, helper_id="helper-needs-review")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    helper_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_STATUS"
    ].iloc[0]

    assert result.latest_pit_universe_evidence_helper_id == "helper-needs-review"
    assert result.pit_universe_evidence_helper_status == "WARN"
    assert result.pit_universe_evidence_helper_stage == "PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_NEEDS_REVIEW"
    assert result.pit_universe_evidence_helper_health_status == "PASS"
    assert result.pit_universe_evidence_helper_review_id == "review-a"
    assert result.pit_universe_evidence_helper_row_count == 72
    assert result.pit_universe_evidence_helper_needs_evidence_count == 72
    assert result.pit_universe_evidence_helper_rows_with_base_hints_count == 72
    assert result.pit_universe_evidence_helper_future_dated_hint_count == 72
    assert result.pit_universe_evidence_helper_authoritative_hint_count == 0
    assert result.workflow_stage == "PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_NEEDS_REVIEW"
    assert helper_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert "Complete PIT universe evidence" in result.next_manual_action


def test_dashboard_failed_pit_universe_evidence_helper_health_is_actionable_when_active(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_evidence_completion_helper_status(
        root,
        helper_id="helper-fail",
        status="FAIL",
        workflow_stage="PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_FAILED",
        health_status="FAIL",
        warning_count=0,
        error_count=1,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    helper_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_FAILED"
    assert helper_row["warning_classification"] == "BLOCKING_ERROR"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 1
    assert "Repair PIT universe evidence completion helper artifacts" in result.next_manual_action


def test_dashboard_preserves_later_paper_priority_over_pit_universe_evidence_helper(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_evidence_completion_helper_status(root, helper_id="helper-paper-context")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    helper_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_STATUS"
    ].iloc[0]

    assert result.latest_pit_universe_evidence_helper_id == "helper-paper-context"
    assert result.pit_universe_evidence_helper_needs_evidence_count == 72
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert helper_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_exports_pit_universe_evidence_helper_fields_to_summary_and_metadata(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_evidence_completion_helper_status(root, helper_id="helper-summary")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_pit_universe_evidence_helper_id"] == "helper-summary"
    assert row["pit_universe_evidence_helper_status"] == "WARN"
    assert row["pit_universe_evidence_helper_stage"] == "PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_NEEDS_REVIEW"
    assert row["pit_universe_evidence_helper_health_status"] == "PASS"
    assert row["pit_universe_evidence_helper_row_count"] == "72"
    assert row["pit_universe_evidence_helper_needs_evidence_count"] == "72"
    assert row["pit_universe_evidence_helper_authoritative_hint_count"] == "0"
    assert metadata["latest_pit_universe_evidence_helper_id"] == "helper-summary"
    assert metadata["pit_universe_evidence_helper_needs_evidence_count"] == 72
    assert metadata["pit_universe_evidence_helper_authoritative_hint_count"] == 0
    assert metadata["component_statuses"]["latest_pit_universe_evidence_helper_id"] == "helper-summary"


def test_cli_research_status_prints_pit_universe_evidence_helper_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_evidence_completion_helper_status(root, helper_id="helper-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_pit_universe_evidence_helper_id: helper-cli" in output.out
    assert "pit_universe_evidence_helper_status: WARN" in output.out
    assert "pit_universe_evidence_helper_stage: PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_NEEDS_REVIEW" in output.out
    assert "pit_universe_evidence_helper_needs_evidence_count: 72" in output.out
    assert "pit_universe_evidence_helper_authoritative_hint_count: 0" in output.out


def test_dashboard_includes_pit_universe_evidence_worklist_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_evidence_review_worklist_status(root, worklist_id="worklist-needs-review")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    worklist_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_STATUS"
    ].iloc[0]

    assert result.latest_pit_universe_evidence_worklist_id == "worklist-needs-review"
    assert result.pit_universe_evidence_worklist_status == "WARN"
    assert result.pit_universe_evidence_worklist_stage == "PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_NEEDS_REVIEW"
    assert result.pit_universe_evidence_worklist_health_status == "PASS"
    assert result.pit_universe_evidence_worklist_review_id == "review-a"
    assert result.pit_universe_evidence_worklist_helper_id == "helper-a"
    assert result.pit_universe_evidence_worklist_row_count == 72
    assert result.pit_universe_evidence_worklist_symbol_count == 9
    assert result.pit_universe_evidence_worklist_signal_date_count == 8
    assert result.pit_universe_evidence_worklist_needs_evidence_count == 72
    assert result.pit_universe_evidence_worklist_future_dated_hint_count == 72
    assert result.workflow_stage == "PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_NEEDS_REVIEW"
    assert worklist_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert "Complete PIT universe evidence" in result.next_manual_action


def test_dashboard_failed_pit_universe_evidence_worklist_health_is_actionable_when_active(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_evidence_review_worklist_status(
        root,
        worklist_id="worklist-fail",
        status="FAIL",
        workflow_stage="PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_FAILED",
        health_status="FAIL",
        warning_count=0,
        error_count=1,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    worklist_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_FAILED"
    assert worklist_row["warning_classification"] == "BLOCKING_ERROR"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 1
    assert "Repair PIT universe evidence review worklist artifacts" in result.next_manual_action


def test_dashboard_preserves_later_paper_priority_over_pit_universe_evidence_worklist(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_evidence_review_worklist_status(root, worklist_id="worklist-paper-context")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    worklist_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_STATUS"
    ].iloc[0]

    assert result.latest_pit_universe_evidence_worklist_id == "worklist-paper-context"
    assert result.pit_universe_evidence_worklist_needs_evidence_count == 72
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert worklist_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_exports_pit_universe_evidence_worklist_fields_to_summary_and_metadata(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_evidence_review_worklist_status(root, worklist_id="worklist-summary")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_pit_universe_evidence_worklist_id"] == "worklist-summary"
    assert row["pit_universe_evidence_worklist_status"] == "WARN"
    assert row["pit_universe_evidence_worklist_stage"] == "PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_NEEDS_REVIEW"
    assert row["pit_universe_evidence_worklist_health_status"] == "PASS"
    assert row["pit_universe_evidence_worklist_row_count"] == "72"
    assert row["pit_universe_evidence_worklist_needs_evidence_count"] == "72"
    assert row["pit_universe_evidence_worklist_future_dated_hint_count"] == "72"
    assert metadata["latest_pit_universe_evidence_worklist_id"] == "worklist-summary"
    assert metadata["pit_universe_evidence_worklist_needs_evidence_count"] == 72
    assert metadata["pit_universe_evidence_worklist_future_dated_hint_count"] == 72
    assert metadata["component_statuses"]["latest_pit_universe_evidence_worklist_id"] == "worklist-summary"


def test_cli_research_status_prints_pit_universe_evidence_worklist_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_evidence_review_worklist_status(root, worklist_id="worklist-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_pit_universe_evidence_worklist_id: worklist-cli" in output.out
    assert "pit_universe_evidence_worklist_status: WARN" in output.out
    assert "pit_universe_evidence_worklist_stage: PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_NEEDS_REVIEW" in output.out
    assert "pit_universe_evidence_worklist_needs_evidence_count: 72" in output.out
    assert "pit_universe_evidence_worklist_future_dated_hint_count: 72" in output.out


def test_dashboard_includes_pit_universe_evidence_update_ingestion_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_evidence_update_ingestion_status(root, ingestion_id="ingest-no-ready")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_STATUS"
    ].iloc[0]

    assert result.latest_pit_universe_evidence_update_ingestion_id == "ingest-no-ready"
    assert result.pit_universe_evidence_update_ingestion_status == "WARN"
    assert (
        result.pit_universe_evidence_update_ingestion_stage
        == "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_NO_READY_UPDATES"
    )
    assert result.pit_universe_evidence_update_ingestion_health_status == "PASS"
    assert result.pit_universe_evidence_update_ingestion_row_count == 72
    assert result.pit_universe_evidence_update_ingestion_ready_for_review_update_count == 0
    assert result.pit_universe_evidence_update_ingestion_blocked_count == 72
    assert result.workflow_stage == "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_NO_READY_UPDATES"
    assert row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"


def test_dashboard_preserves_later_paper_priority_over_pit_universe_evidence_update_ingestion(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_evidence_update_ingestion_status(root, ingestion_id="ingest-paper-context")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_STATUS"
    ].iloc[0]

    assert result.latest_pit_universe_evidence_update_ingestion_id == "ingest-paper-context"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert row["warning_classification"] == "STALE_ARTIFACT_WARNING"


def test_dashboard_exports_pit_universe_evidence_update_ingestion_fields_to_summary_and_metadata(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_evidence_update_ingestion_status(root, ingestion_id="ingest-summary")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_pit_universe_evidence_update_ingestion_id"] == "ingest-summary"
    assert row["pit_universe_evidence_update_ingestion_status"] == "WARN"
    assert (
        row["pit_universe_evidence_update_ingestion_stage"]
        == "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_NO_READY_UPDATES"
    )
    assert row["pit_universe_evidence_update_ingestion_ready_for_review_update_count"] == "0"
    assert row["pit_universe_evidence_update_ingestion_blocked_count"] == "72"
    assert metadata["latest_pit_universe_evidence_update_ingestion_id"] == "ingest-summary"
    assert metadata["pit_universe_evidence_update_ingestion_blocked_count"] == 72


def test_cli_research_status_prints_pit_universe_evidence_update_ingestion_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = _reports_root(tmp_path)
    _pit_universe_evidence_update_ingestion_status(root, ingestion_id="ingest-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_pit_universe_evidence_update_ingestion_id: ingest-cli" in output.out
    assert "pit_universe_evidence_update_ingestion_status: WARN" in output.out
    assert (
        "pit_universe_evidence_update_ingestion_stage: "
        "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_NO_READY_UPDATES"
    ) in output.out
    assert "pit_universe_evidence_update_ingestion_ready_for_review_update_count: 0" in output.out
    assert "pit_universe_evidence_update_ingestion_blocked_count: 72" in output.out


def test_dashboard_includes_pit_evidence_checklist_validator_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_evidence_checklist_validator_artifact(root, validator_id="validator-blocked")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_EVIDENCE_CHECKLIST_VALIDATOR_STATUS"
    ].iloc[0]

    assert result.latest_pit_evidence_checklist_validator_id == "validator-blocked"
    assert result.pit_evidence_checklist_validator_status == "WARN"
    assert result.pit_evidence_checklist_validator_stage == "PIT_EVIDENCE_CHECKLIST_VALIDATION_BLOCKED"
    assert result.pit_evidence_checklist_validator_health_status == "PASS"
    assert result.pit_evidence_checklist_validator_row_count == 16
    assert result.pit_evidence_checklist_validator_checklist_pass_count == 0
    assert result.pit_evidence_checklist_validator_blocked_count == 16
    assert result.pit_evidence_checklist_validator_stock_core_blocked_count == 8
    assert result.pit_evidence_checklist_validator_etf_core_blocked_count == 8
    assert result.workflow_stage == "PIT_EVIDENCE_CHECKLIST_VALIDATION_BLOCKED"
    assert row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"


def test_dashboard_preserves_later_paper_priority_over_pit_evidence_checklist_validator(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_evidence_checklist_validator_artifact(root, validator_id="validator-paper-context")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_EVIDENCE_CHECKLIST_VALIDATOR_STATUS"
    ].iloc[0]

    assert result.latest_pit_evidence_checklist_validator_id == "validator-paper-context"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_exports_pit_evidence_checklist_validator_fields_to_summary_and_metadata(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_evidence_checklist_validator_artifact(root, validator_id="validator-summary")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_pit_evidence_checklist_validator_id"] == "validator-summary"
    assert row["pit_evidence_checklist_validator_status"] == "WARN"
    assert row["pit_evidence_checklist_validator_stage"] == "PIT_EVIDENCE_CHECKLIST_VALIDATION_BLOCKED"
    assert row["pit_evidence_checklist_validator_health_status"] == "PASS"
    assert row["pit_evidence_checklist_validator_row_count"] == "16"
    assert row["pit_evidence_checklist_validator_checklist_pass_count"] == "0"
    assert row["pit_evidence_checklist_validator_blocked_count"] == "16"
    assert row["pit_evidence_checklist_validator_stock_core_blocked_count"] == "8"
    assert row["pit_evidence_checklist_validator_etf_core_blocked_count"] == "8"
    assert metadata["latest_pit_evidence_checklist_validator_id"] == "validator-summary"
    assert metadata["pit_evidence_checklist_validator_blocked_count"] == 16
    assert metadata["component_statuses"]["latest_pit_evidence_checklist_validator_id"] == "validator-summary"


def test_cli_research_status_prints_pit_evidence_checklist_validator_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = _reports_root(tmp_path)
    _pit_evidence_checklist_validator_artifact(root, validator_id="validator-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_pit_evidence_checklist_validator_id: validator-cli" in output.out
    assert "pit_evidence_checklist_validator_status: WARN" in output.out
    assert "pit_evidence_checklist_validator_stage: PIT_EVIDENCE_CHECKLIST_VALIDATION_BLOCKED" in output.out
    assert "pit_evidence_checklist_validator_health_status: PASS" in output.out
    assert "pit_evidence_checklist_validator_blocked_count: 16" in output.out


def test_dashboard_includes_pit_evidence_policy_profile_comparison_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_evidence_policy_profile_comparison_artifact(root, comparison_id="comparison-blocked")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_STATUS"
    ].iloc[0]

    assert result.latest_pit_evidence_policy_profile_comparison_id == "comparison-blocked"
    assert result.pit_evidence_policy_profile_comparison_status == "WARN"
    assert (
        result.pit_evidence_policy_profile_comparison_stage
        == "PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_ALL_BLOCKED"
    )
    assert result.pit_evidence_policy_profile_comparison_health_status == "PASS"
    assert result.pit_evidence_policy_profile_comparison_profile_name == "EOD_POST_CLOSE_LOW_BUDGET_PIT"
    assert result.pit_evidence_policy_profile_comparison_row_count == 16
    assert result.pit_evidence_policy_profile_comparison_strict_pass_count == 0
    assert result.pit_evidence_policy_profile_comparison_eod_low_budget_pass_count == 0
    assert result.pit_evidence_policy_profile_comparison_reviewed_no_hit_support_pass_count == 0
    assert result.pit_evidence_policy_profile_comparison_no_hit_context_supported_count == 0
    assert result.pit_evidence_policy_profile_comparison_reviewer_acceptance_required_count == 0
    assert result.pit_evidence_policy_profile_comparison_relaxed_blocker_count == 16
    assert result.pit_evidence_policy_profile_comparison_remaining_blocked_count == 16
    assert result.workflow_stage == "PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_ALL_BLOCKED"
    assert row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"


def test_dashboard_preserves_later_paper_priority_over_pit_evidence_policy_profile_comparison(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_evidence_policy_profile_comparison_artifact(root, comparison_id="comparison-paper-context")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_STATUS"
    ].iloc[0]

    assert result.latest_pit_evidence_policy_profile_comparison_id == "comparison-paper-context"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert row["warning_classification"] == "STALE_ARTIFACT_WARNING"


def test_cli_research_status_prints_pit_evidence_policy_profile_comparison_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = _reports_root(tmp_path)
    _pit_evidence_policy_profile_comparison_artifact(root, comparison_id="comparison-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_pit_evidence_policy_profile_comparison_id: comparison-cli" in output.out
    assert "pit_evidence_policy_profile_comparison_status: WARN" in output.out
    assert (
        "pit_evidence_policy_profile_comparison_stage: "
        "PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_ALL_BLOCKED"
    ) in output.out
    assert "pit_evidence_policy_profile_comparison_eod_low_budget_pass_count: 0" in output.out
    assert "pit_evidence_policy_profile_comparison_reviewed_no_hit_support_pass_count: 0" in output.out


def test_dashboard_includes_pit_official_status_evidence_packet_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_official_status_evidence_packet_artifact(root, packet_id="packet-blocked")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_STATUS"
    ].iloc[0]

    assert result.latest_pit_official_status_evidence_packet_id == "packet-blocked"
    assert result.pit_official_status_evidence_packet_status == "WARN"
    assert result.pit_official_status_evidence_packet_stage == "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_BLOCKED"
    assert result.pit_official_status_evidence_packet_health_status == "PASS"
    assert result.pit_official_status_evidence_packet_row_count == 16
    assert result.pit_official_status_evidence_packet_blocked_count == 16
    assert result.pit_official_status_evidence_packet_supporting_local_eod_cache_count == 16
    assert result.workflow_stage == "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_BLOCKED"
    assert row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"


def test_dashboard_preserves_later_paper_priority_over_pit_official_status_evidence_packet(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_official_status_evidence_packet_artifact(root, packet_id="packet-paper-context")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_STATUS"
    ].iloc[0]

    assert result.latest_pit_official_status_evidence_packet_id == "packet-paper-context"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert row["warning_classification"] == "STALE_ARTIFACT_WARNING"


def test_cli_research_status_prints_pit_official_status_evidence_packet_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = _reports_root(tmp_path)
    _pit_official_status_evidence_packet_artifact(root, packet_id="packet-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_pit_official_status_evidence_packet_id: packet-cli" in output.out
    assert "pit_official_status_evidence_packet_status: WARN" in output.out
    assert "pit_official_status_evidence_packet_stage: PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_BLOCKED" in output.out
    assert "pit_official_status_evidence_packet_blocked_count: 16" in output.out


def test_dashboard_includes_pit_official_status_evidence_packet_enrichment_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_official_status_evidence_packet_enrichment_artifact(root, enrichment_id="enrich-blocked")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_ENRICHMENT_STATUS"
    ].iloc[0]

    assert result.latest_pit_official_status_evidence_packet_enrichment_id == "enrich-blocked"
    assert result.pit_official_status_evidence_packet_enrichment_status == "WARN"
    assert (
        result.pit_official_status_evidence_packet_enrichment_stage
        == "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_ENRICHMENT_BLOCKED"
    )
    assert result.pit_official_status_evidence_packet_enrichment_health_status == "PASS"
    assert result.pit_official_status_evidence_packet_enrichment_source_packet_id == "packet-a"
    assert result.pit_official_status_evidence_packet_enrichment_policy_comparison_id == "comparison-a"
    assert result.pit_official_status_evidence_packet_enrichment_row_count == 16
    assert result.pit_official_status_evidence_packet_enrichment_strong_official_date_specific_quotation_count == 16
    assert result.pit_official_status_evidence_packet_enrichment_reviewed_no_hit_context_supported_count == 16
    assert result.pit_official_status_evidence_packet_enrichment_reviewer_acceptance_required_count == 16
    assert result.pit_official_status_evidence_packet_enrichment_checklist_pass_count == 0
    assert result.pit_official_status_evidence_packet_enrichment_remaining_blocked_count == 16
    assert row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"


def test_dashboard_preserves_later_paper_priority_over_pit_official_status_evidence_packet_enrichment(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _pit_official_status_evidence_packet_enrichment_artifact(root, enrichment_id="enrich-paper-context")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_ENRICHMENT_STATUS"
    ].iloc[0]

    assert result.latest_pit_official_status_evidence_packet_enrichment_id == "enrich-paper-context"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert row["warning_classification"] == "STALE_ARTIFACT_WARNING"


def test_cli_research_status_prints_pit_official_status_evidence_packet_enrichment_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = _reports_root(tmp_path)
    _pit_official_status_evidence_packet_enrichment_artifact(root, enrichment_id="enrich-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_pit_official_status_evidence_packet_enrichment_id: enrich-cli" in output.out
    assert "pit_official_status_evidence_packet_enrichment_status: WARN" in output.out
    assert (
        "pit_official_status_evidence_packet_enrichment_stage: "
        "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_ENRICHMENT_BLOCKED"
    ) in output.out
    assert "pit_official_status_evidence_packet_enrichment_remaining_blocked_count: 16" in output.out


def test_dashboard_includes_reviewer_no_hit_downstream_impact_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    impact_dir = _reviewer_no_hit_downstream_impact_artifact(root)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "REVIEWER_NO_HIT_ACCEPTANCE_DOWNSTREAM_IMPACT_STATUS"
    ].iloc[0]
    summary = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert result.latest_reviewer_no_hit_acceptance_downstream_impact_id == impact_dir.name
    assert result.reviewer_no_hit_downstream_impact_status == "WARN"
    assert (
        result.reviewer_no_hit_downstream_impact_stage
        == "REVIEWER_NO_HIT_ACCEPTANCE_DOWNSTREAM_IMPACT_NO_ACCEPTED_CONTEXT"
    )
    assert result.reviewer_no_hit_downstream_impact_health_status == "PASS"
    assert result.reviewer_no_hit_downstream_impact_accepted_no_hit_context_count == 0
    assert result.reviewer_no_hit_downstream_impact_checklist_pass_count == 0
    assert result.reviewer_no_hit_downstream_impact_remaining_blocked_count == 2
    assert not result.reviewer_no_hit_downstream_impact_approval_applied
    assert result.workflow_stage == "REVIEWER_NO_HIT_ACCEPTANCE_DOWNSTREAM_IMPACT_NO_ACCEPTED_CONTEXT"
    assert row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert summary.loc[0, "latest_reviewer_no_hit_acceptance_downstream_impact_id"] == impact_dir.name
    assert metadata["reviewer_no_hit_downstream_impact_checklist_pass_count"] == 0


def test_dashboard_preserves_later_paper_priority_over_reviewer_no_hit_downstream_impact(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _reviewer_no_hit_downstream_impact_artifact(root)
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "REVIEWER_NO_HIT_ACCEPTANCE_DOWNSTREAM_IMPACT_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.latest_reviewer_no_hit_acceptance_downstream_impact_id
    assert row["warning_classification"] == "STALE_ARTIFACT_WARNING"


def test_cli_research_status_prints_reviewer_no_hit_downstream_impact_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = _reports_root(tmp_path)
    impact_dir = _reviewer_no_hit_downstream_impact_artifact(root)

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert (
        "latest_reviewer_no_hit_acceptance_downstream_impact_id: "
        f"{impact_dir.name}"
    ) in output.out
    assert "reviewer_no_hit_downstream_impact_status: WARN" in output.out
    assert (
        "reviewer_no_hit_downstream_impact_stage: "
        "REVIEWER_NO_HIT_ACCEPTANCE_DOWNSTREAM_IMPACT_NO_ACCEPTED_CONTEXT"
    ) in output.out
    assert "reviewer_no_hit_downstream_impact_approval_applied: False" in output.out


def test_research_status_includes_replay_substrate_schema_fixture_context(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    fixture = build_replay_substrate_schema_fixture(
        output_dir=root / "manual_diagnostics" / "replay_substrate_schema_fixture_v0_1"
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "REPLAY_SUBSTRATE_SCHEMA_FIXTURE_STATUS"
    ].iloc[0]
    summary = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert result.latest_replay_substrate_schema_fixture_id == fixture.fixture_id
    assert result.replay_substrate_schema_fixture_status == "PASS"
    assert result.replay_substrate_schema_fixture_stage == "REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY"
    assert result.replay_substrate_schema_fixture_health_status == "PASS"
    assert result.replay_substrate_schema_fixture_entity_count == 14
    assert result.replay_substrate_schema_fixture_validation_issue_count == 0
    assert result.replay_substrate_schema_fixture_overclaim_guard_status == "PASS"
    assert result.replay_substrate_schema_fixture_overclaim_guard_pass_count == 8
    assert result.replay_substrate_schema_fixture_overclaim_guard_total_count == 8
    assert result.replay_substrate_schema_fixture_active_replay_input is False
    assert result.replay_substrate_schema_fixture_forward_labels_exist is False
    assert result.replay_substrate_schema_fixture_weights_trained is False
    assert result.replay_substrate_schema_fixture_active_stock_profile_exists is False
    assert result.replay_substrate_schema_fixture_real_buy_review_eligible is False
    assert result.replay_substrate_schema_fixture_report_only is True
    assert result.replay_substrate_schema_fixture_diagnostic_only is True
    assert result.replay_substrate_schema_fixture_no_live_trading is True
    assert result.replay_substrate_schema_fixture_no_broker_api is True
    assert result.replay_substrate_schema_fixture_no_order_placement is True
    assert result.workflow_stage == "REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY"
    assert row["status"] == "PASS"
    assert row["blocking_error_count"] == 0
    assert summary.loc[0, "latest_replay_substrate_schema_fixture_id"] == fixture.fixture_id
    assert summary.loc[0, "replay_substrate_schema_fixture_overclaim_guard_pass_count"] == "8"
    assert summary.loc[0, "replay_substrate_schema_fixture_overclaim_guard_total_count"] == "8"
    assert summary.loc[0, "replay_substrate_schema_fixture_active_replay_input"] == "False"
    assert metadata["replay_substrate_schema_fixture_status"] == "PASS"
    assert metadata["replay_substrate_schema_fixture_overclaim_guard_pass_count"] == 8
    assert metadata["replay_substrate_schema_fixture_overclaim_guard_total_count"] == 8
    assert metadata["replay_substrate_schema_fixture_active_replay_input"] is False
    assert metadata["replay_substrate_schema_fixture_forward_labels_exist"] is False
    assert metadata["replay_substrate_schema_fixture_weights_trained"] is False
    assert metadata["replay_substrate_schema_fixture_active_stock_profile_exists"] is False
    assert metadata["replay_substrate_schema_fixture_real_buy_review_eligible"] is False
    assert metadata["replay_substrate_schema_fixture_report_only"] is True
    assert metadata["replay_substrate_schema_fixture_diagnostic_only"] is True
    assert metadata["replay_substrate_schema_fixture_no_live_trading"] is True
    assert metadata["replay_substrate_schema_fixture_no_broker_api"] is True
    assert metadata["replay_substrate_schema_fixture_no_order_placement"] is True


def test_research_status_preserves_paper_priority_over_replay_substrate_schema_fixture(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    build_replay_substrate_schema_fixture(
        output_dir=root / "manual_diagnostics" / "replay_substrate_schema_fixture_v0_1"
    )
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "REPLAY_SUBSTRATE_SCHEMA_FIXTURE_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.replay_substrate_schema_fixture_status == "PASS"
    assert row["status"] == "PASS"


def test_research_status_reports_failed_replay_substrate_fixture_as_context_blocker(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    fixture = build_replay_substrate_schema_fixture(
        output_dir=root / "manual_diagnostics" / "replay_substrate_schema_fixture_v0_1"
    )
    fixture.artifact_paths["report"].unlink()

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "REPLAY_SUBSTRATE_SCHEMA_FIXTURE_STATUS"
    ].iloc[0]

    assert result.replay_substrate_schema_fixture_status == "FAIL"
    assert result.replay_substrate_schema_fixture_stage == "REPLAY_SUBSTRATE_SCHEMA_FIXTURE_FAILED"
    assert result.workflow_stage == "REPLAY_SUBSTRATE_SCHEMA_FIXTURE_FAILED"
    assert row["blocking_error_count"] >= 1
    assert result.replay_substrate_schema_fixture_active_replay_input is False
    assert result.replay_substrate_schema_fixture_forward_labels_exist is False
    assert result.replay_substrate_schema_fixture_weights_trained is False
    assert result.replay_substrate_schema_fixture_active_stock_profile_exists is False
    assert result.replay_substrate_schema_fixture_real_buy_review_eligible is False


def test_cli_research_status_prints_replay_substrate_schema_fixture_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = _reports_root(tmp_path)
    fixture = build_replay_substrate_schema_fixture(
        output_dir=root / "manual_diagnostics" / "replay_substrate_schema_fixture_v0_1"
    )

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert f"latest_replay_substrate_schema_fixture_id: {fixture.fixture_id}" in output.out
    assert "replay_substrate_schema_fixture_status: PASS" in output.out
    assert "replay_substrate_schema_fixture_stage: REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY" in output.out
    assert "replay_substrate_schema_fixture_overclaim_guard_pass_count: 8" in output.out
    assert "replay_substrate_schema_fixture_overclaim_guard_total_count: 8" in output.out
    assert "replay_substrate_schema_fixture_active_replay_input: False" in output.out
    assert "replay_substrate_schema_fixture_forward_labels_exist: False" in output.out
    assert "replay_substrate_schema_fixture_weights_trained: False" in output.out
    assert "replay_substrate_schema_fixture_active_stock_profile_exists: False" in output.out
    assert "replay_substrate_schema_fixture_real_buy_review_eligible: False" in output.out
    assert "replay_substrate_schema_fixture_report_only: True" in output.out
    assert "replay_substrate_schema_fixture_diagnostic_only: True" in output.out
    assert "replay_substrate_schema_fixture_no_live_trading: True" in output.out
    assert "replay_substrate_schema_fixture_no_broker_api: True" in output.out
    assert "replay_substrate_schema_fixture_no_order_placement: True" in output.out


def test_research_status_includes_input_gate_validator_fixture_context(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    fixture = build_historical_replay_input_gate_validator_fixture(
        output_dir=root / "manual_diagnostics" / "historical_replay_input_gate_validator_fixture_v0_1"
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "INPUT_GATE_VALIDATOR_FIXTURE_STATUS"
    ].iloc[0]
    summary = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert result.latest_input_gate_validator_fixture_run_id == fixture.fixture_run_id
    assert result.input_gate_validator_fixture_status == "PASS"
    assert result.input_gate_validator_fixture_stage == "INPUT_GATE_VALIDATOR_FIXTURE_READY"
    assert result.input_gate_validator_fixture_health_status == "PASS"
    assert result.input_gate_validator_fixture_case_count == 68
    assert result.input_gate_validator_fixture_blocked_case_count == 67
    assert result.input_gate_validator_fixture_pass_candidate_case_count == 1
    assert result.input_gate_validator_fixture_active_ready_case_count == 0
    assert result.input_gate_validator_fixture_validation_issue_count == 0
    assert result.input_gate_validator_fixture_overclaim_guard_pass_count == 14
    assert result.input_gate_validator_fixture_overclaim_guard_total_count == 14
    assert result.input_gate_validator_fixture_active_replay_input is False
    assert result.input_gate_validator_fixture_forward_labels_exist is False
    assert result.input_gate_validator_fixture_weights_trained is False
    assert result.input_gate_validator_fixture_active_stock_profile_exists is False
    assert result.input_gate_validator_fixture_real_buy_review_eligible is False
    assert result.input_gate_validator_fixture_validator_implemented is False
    assert result.input_gate_validator_fixture_report_only is True
    assert result.input_gate_validator_fixture_diagnostic_only is True
    assert result.input_gate_validator_fixture_no_live_trading is True
    assert result.input_gate_validator_fixture_no_broker_api is True
    assert result.input_gate_validator_fixture_no_order_placement is True
    assert result.input_gate_validator_fixture_no_message_sent is True
    assert result.input_gate_validator_fixture_llm_api_called is False
    assert result.input_gate_validator_fixture_external_api_called is False
    assert result.input_gate_validator_fixture_cache_mutated is False
    assert result.input_gate_validator_fixture_current_candidates_run is False
    assert result.input_gate_validator_fixture_snapshot_built is False
    assert result.input_gate_validator_fixture_signal_semantics_changed is False
    assert result.workflow_stage == "INPUT_GATE_VALIDATOR_FIXTURE_READY"
    assert result.workflow_stage not in {
        "ACTIVE_REPLAY_INPUT_READY",
        "REAL_REPLAY_READY",
        "FORWARD_LABEL_READY",
        "TRAINING_READY",
        "STOCK_PROFILE_READY",
        "REAL_BUY_REVIEW_READY",
    }
    assert row["status"] == "PASS"
    assert row["blocking_error_count"] == 0
    assert summary.loc[0, "latest_input_gate_validator_fixture_run_id"] == fixture.fixture_run_id
    assert summary.loc[0, "input_gate_validator_fixture_case_count"] == "68"
    assert summary.loc[0, "input_gate_validator_fixture_active_replay_input"] == "False"
    assert metadata["input_gate_validator_fixture_status"] == "PASS"
    assert metadata["input_gate_validator_fixture_overclaim_guard_pass_count"] == 14
    assert metadata["input_gate_validator_fixture_active_replay_input"] is False
    assert metadata["input_gate_validator_fixture_forward_labels_exist"] is False
    assert metadata["input_gate_validator_fixture_weights_trained"] is False
    assert metadata["input_gate_validator_fixture_active_stock_profile_exists"] is False
    assert metadata["input_gate_validator_fixture_real_buy_review_eligible"] is False
    assert metadata["input_gate_validator_fixture_validator_implemented"] is False
    assert metadata["input_gate_validator_fixture_report_only"] is True
    assert metadata["input_gate_validator_fixture_diagnostic_only"] is True
    assert metadata["input_gate_validator_fixture_no_live_trading"] is True
    assert metadata["input_gate_validator_fixture_no_broker_api"] is True
    assert metadata["input_gate_validator_fixture_no_order_placement"] is True
    assert metadata["input_gate_validator_fixture_no_message_sent"] is True
    assert metadata["input_gate_validator_fixture_llm_api_called"] is False
    assert metadata["input_gate_validator_fixture_external_api_called"] is False
    assert metadata["input_gate_validator_fixture_cache_mutated"] is False
    assert metadata["input_gate_validator_fixture_current_candidates_run"] is False
    assert metadata["input_gate_validator_fixture_snapshot_built"] is False
    assert metadata["input_gate_validator_fixture_signal_semantics_changed"] is False


def test_research_status_preserves_paper_priority_over_input_gate_validator_fixture(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    build_historical_replay_input_gate_validator_fixture(
        output_dir=root / "manual_diagnostics" / "historical_replay_input_gate_validator_fixture_v0_1"
    )
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "INPUT_GATE_VALIDATOR_FIXTURE_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.input_gate_validator_fixture_status == "PASS"
    assert result.input_gate_validator_fixture_active_replay_input is False
    assert result.input_gate_validator_fixture_validator_implemented is False
    assert row["status"] == "PASS"


def test_research_status_preserves_replay_substrate_priority_over_input_gate_validator_fixture(
    tmp_path: Path,
) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    build_replay_substrate_schema_fixture(
        output_dir=root / "manual_diagnostics" / "replay_substrate_schema_fixture_v0_1"
    )
    build_historical_replay_input_gate_validator_fixture(
        output_dir=root / "manual_diagnostics" / "historical_replay_input_gate_validator_fixture_v0_1"
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY"
    assert result.input_gate_validator_fixture_status == "PASS"
    assert result.input_gate_validator_fixture_active_replay_input is False
    assert result.replay_substrate_schema_fixture_status == "PASS"


def test_cli_research_status_prints_input_gate_validator_fixture_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    fixture = build_historical_replay_input_gate_validator_fixture(
        output_dir=root / "manual_diagnostics" / "historical_replay_input_gate_validator_fixture_v0_1"
    )

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert f"latest_input_gate_validator_fixture_run_id: {fixture.fixture_run_id}" in output.out
    assert "input_gate_validator_fixture_status: PASS" in output.out
    assert "input_gate_validator_fixture_stage: INPUT_GATE_VALIDATOR_FIXTURE_READY" in output.out
    assert "input_gate_validator_fixture_case_count: 68" in output.out
    assert "input_gate_validator_fixture_blocked_case_count: 67" in output.out
    assert "input_gate_validator_fixture_pass_candidate_case_count: 1" in output.out
    assert "input_gate_validator_fixture_active_ready_case_count: 0" in output.out
    assert "input_gate_validator_fixture_validation_issue_count: 0" in output.out
    assert "input_gate_validator_fixture_overclaim_guard_pass_count: 14" in output.out
    assert "input_gate_validator_fixture_overclaim_guard_total_count: 14" in output.out
    assert "input_gate_validator_fixture_active_replay_input: False" in output.out
    assert "input_gate_validator_fixture_forward_labels_exist: False" in output.out
    assert "input_gate_validator_fixture_weights_trained: False" in output.out
    assert "input_gate_validator_fixture_active_stock_profile_exists: False" in output.out
    assert "input_gate_validator_fixture_real_buy_review_eligible: False" in output.out
    assert "input_gate_validator_fixture_validator_implemented: False" in output.out
    assert "input_gate_validator_fixture_report_only: True" in output.out
    assert "input_gate_validator_fixture_diagnostic_only: True" in output.out
    assert "input_gate_validator_fixture_no_live_trading: True" in output.out
    assert "input_gate_validator_fixture_no_broker_api: True" in output.out
    assert "input_gate_validator_fixture_no_order_placement: True" in output.out
    assert "input_gate_validator_fixture_no_message_sent: True" in output.out
    assert "input_gate_validator_fixture_llm_api_called: False" in output.out
    assert "input_gate_validator_fixture_external_api_called: False" in output.out
    assert "input_gate_validator_fixture_cache_mutated: False" in output.out
    assert "input_gate_validator_fixture_current_candidates_run: False" in output.out
    assert "input_gate_validator_fixture_snapshot_built: False" in output.out
    assert "input_gate_validator_fixture_signal_semantics_changed: False" in output.out


def test_research_status_includes_historical_replay_input_gate_validator_context(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    validator = run_historical_replay_input_gate_validator(
        output_dir=root / "manual_diagnostics" / "historical_replay_input_gate_validator_v0_1"
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "HISTORICAL_REPLAY_INPUT_GATE_VALIDATOR_STATUS"
    ].iloc[0]
    summary = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert result.latest_historical_replay_input_gate_validator_run_id == validator.validator_run_id
    assert result.historical_replay_input_gate_validator_status == "NO_INPUT"
    assert result.historical_replay_input_gate_validator_stage == "INPUT_GATE_VALIDATOR_NO_INPUT"
    assert result.historical_replay_input_gate_validator_health_status == "PASS"
    assert result.historical_replay_input_gate_validator_pass_candidate is False
    assert result.historical_replay_input_gate_validator_active_replay_input_ready is False
    assert result.historical_replay_input_gate_validator_active_replay_input is False
    assert result.historical_replay_input_gate_validator_forward_labels_exist is False
    assert result.historical_replay_input_gate_validator_weights_trained is False
    assert result.historical_replay_input_gate_validator_active_stock_profile_exists is False
    assert result.historical_replay_input_gate_validator_real_buy_review_eligible is False
    assert result.historical_replay_input_gate_validator_report_only is True
    assert result.historical_replay_input_gate_validator_diagnostic_only is True
    assert result.historical_replay_input_gate_validator_no_live_trading is True
    assert result.historical_replay_input_gate_validator_no_broker_api is True
    assert result.historical_replay_input_gate_validator_no_order_placement is True
    assert result.historical_replay_input_gate_validator_no_message_sent is True
    assert result.historical_replay_input_gate_validator_llm_api_called is False
    assert result.historical_replay_input_gate_validator_external_api_called is False
    assert result.historical_replay_input_gate_validator_cache_mutated is False
    assert result.historical_replay_input_gate_validator_current_candidates_run is False
    assert result.historical_replay_input_gate_validator_snapshot_built is False
    assert result.historical_replay_input_gate_validator_signal_semantics_changed is False
    assert result.workflow_stage == "INPUT_GATE_VALIDATOR_NO_INPUT"
    assert result.workflow_stage != "ACTIVE_REPLAY_INPUT_READY"
    assert row["status"] == "NO_INPUT"
    assert row["blocking_error_count"] == 0
    assert summary.loc[0, "latest_historical_replay_input_gate_validator_run_id"] == validator.validator_run_id
    assert summary.loc[0, "historical_replay_input_gate_validator_active_replay_input"] == "False"
    assert metadata["historical_replay_input_gate_validator_status"] == "NO_INPUT"
    assert metadata["historical_replay_input_gate_validator_active_replay_input_ready"] is False
    assert metadata["historical_replay_input_gate_validator_active_replay_input"] is False
    assert metadata["historical_replay_input_gate_validator_forward_labels_exist"] is False
    assert metadata["historical_replay_input_gate_validator_weights_trained"] is False
    assert metadata["historical_replay_input_gate_validator_active_stock_profile_exists"] is False
    assert metadata["historical_replay_input_gate_validator_real_buy_review_eligible"] is False


def test_research_status_preserves_paper_priority_over_historical_replay_input_gate_validator(
    tmp_path: Path,
) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    run_historical_replay_input_gate_validator(
        output_dir=root / "manual_diagnostics" / "historical_replay_input_gate_validator_v0_1"
    )
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "HISTORICAL_REPLAY_INPUT_GATE_VALIDATOR_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.historical_replay_input_gate_validator_status == "NO_INPUT"
    assert result.historical_replay_input_gate_validator_active_replay_input_ready is False
    assert result.historical_replay_input_gate_validator_active_replay_input is False
    assert row["status"] == "NO_INPUT"


def test_cli_research_status_prints_historical_replay_input_gate_validator_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    validator = run_historical_replay_input_gate_validator(
        output_dir=root / "manual_diagnostics" / "historical_replay_input_gate_validator_v0_1"
    )

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert (
        f"latest_historical_replay_input_gate_validator_run_id: {validator.validator_run_id}"
        in output.out
    )
    assert "historical_replay_input_gate_validator_status: NO_INPUT" in output.out
    assert "historical_replay_input_gate_validator_stage: INPUT_GATE_VALIDATOR_NO_INPUT" in output.out
    assert "historical_replay_input_gate_validator_health_status: PASS" in output.out
    assert "historical_replay_input_gate_validator_pass_candidate: False" in output.out
    assert "historical_replay_input_gate_validator_active_replay_input_ready: False" in output.out
    assert "historical_replay_input_gate_validator_active_replay_input: False" in output.out
    assert "historical_replay_input_gate_validator_forward_labels_exist: False" in output.out
    assert "historical_replay_input_gate_validator_weights_trained: False" in output.out
    assert "historical_replay_input_gate_validator_active_stock_profile_exists: False" in output.out
    assert "historical_replay_input_gate_validator_real_buy_review_eligible: False" in output.out
    assert "historical_replay_input_gate_validator_report_only: True" in output.out
    assert "historical_replay_input_gate_validator_diagnostic_only: True" in output.out
    assert "historical_replay_input_gate_validator_no_live_trading: True" in output.out
    assert "historical_replay_input_gate_validator_no_broker_api: True" in output.out
    assert "historical_replay_input_gate_validator_no_order_placement: True" in output.out
    assert "historical_replay_input_gate_validator_no_message_sent: True" in output.out
    assert "historical_replay_input_gate_validator_llm_api_called: False" in output.out
    assert "historical_replay_input_gate_validator_external_api_called: False" in output.out
    assert "historical_replay_input_gate_validator_cache_mutated: False" in output.out
    assert "historical_replay_input_gate_validator_current_candidates_run: False" in output.out
    assert "historical_replay_input_gate_validator_snapshot_built: False" in output.out
    assert "historical_replay_input_gate_validator_signal_semantics_changed: False" in output.out


def test_research_status_includes_minimal_replay_input_package_fixture_smoke_context(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    smoke = run_minimal_replay_input_package_fixture_smoke(
        MinimalReplayInputPackageFixtureSmokeSettings(
            output_dir=root / "manual_diagnostics" / "minimal_replay_input_package_fixture_smoke_v0_1",
            validator_output_dir=root / "manual_diagnostics" / "historical_replay_input_gate_validator_v0_1",
        )
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "MINIMAL_REPLAY_INPUT_PACKAGE_FIXTURE_SMOKE_STATUS"
    ].iloc[0]

    assert result.minimal_replay_input_package_fixture_smoke_implemented is True
    assert result.minimal_replay_input_package_fixture_smoke_views_implemented is True
    assert result.latest_smoke_run_id == smoke.smoke_run_id
    assert result.latest_smoke_status == "REPLAY_INPUT_GATE_PASS_CANDIDATE"
    assert result.latest_smoke_health_status == "PASS"
    assert result.latest_smoke_workflow_stage == "SMOKE_PASS_CANDIDATE_READY"
    assert result.latest_smoke_validator_run_id == smoke.validator_run_id
    assert result.latest_smoke_validator_status == "REPLAY_INPUT_GATE_PASS_CANDIDATE"
    assert result.smoke_pass_candidate is True
    assert result.smoke_active_replay_input_ready is False
    assert result.smoke_active_replay_input is False
    assert result.smoke_forward_labels_exist is False
    assert result.smoke_weights_trained is False
    assert result.smoke_active_stock_profile_exists is False
    assert result.smoke_real_buy_review_eligible is False
    assert result.smoke_approval_applied is False
    assert result.smoke_order_placed is False
    assert result.smoke_llm_api_called is False
    assert result.smoke_external_api_called is False
    assert result.smoke_cache_mutated is False
    assert result.smoke_current_candidates_run is False
    assert result.smoke_snapshot_built is False
    assert result.smoke_signal_semantics_changed is False
    assert result.smoke_report_only is True
    assert result.smoke_diagnostic_only is True
    assert result.smoke_no_live_trading is True
    assert result.smoke_no_broker_api is True
    assert result.smoke_no_order_placement is True
    assert result.smoke_no_message_sent is True
    assert result.workflow_stage == "SMOKE_PASS_CANDIDATE_READY"
    assert result.workflow_stage != "ACTIVE_REPLAY_INPUT_READY"
    assert row["status"] == "REPLAY_INPUT_GATE_PASS_CANDIDATE"

    summary = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str)
    metadata = json.loads(Path(result.artifact_paths["metadata"]).read_text(encoding="utf-8"))
    assert summary.loc[0, "latest_smoke_run_id"] == smoke.smoke_run_id
    assert summary.loc[0, "smoke_active_replay_input_ready"] == "False"
    assert metadata["latest_smoke_workflow_stage"] == "SMOKE_PASS_CANDIDATE_READY"
    assert metadata["smoke_active_replay_input_ready"] is False
    assert metadata["smoke_active_replay_input"] is False


def test_research_status_preserves_paper_priority_over_minimal_replay_smoke(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    run_minimal_replay_input_package_fixture_smoke(
        MinimalReplayInputPackageFixtureSmokeSettings(
            output_dir=root / "manual_diagnostics" / "minimal_replay_input_package_fixture_smoke_v0_1",
            validator_output_dir=root / "manual_diagnostics" / "historical_replay_input_gate_validator_v0_1",
        )
    )
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.latest_smoke_workflow_stage == "SMOKE_PASS_CANDIDATE_READY"
    assert result.smoke_pass_candidate is True
    assert result.smoke_active_replay_input_ready is False
    assert result.smoke_active_replay_input is False


def test_research_status_includes_active_replay_input_promotion_context(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    promotion = _active_replay_input_promotion_ready(root)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "ACTIVE_REPLAY_INPUT_PROMOTION_STATUS"
    ].iloc[0]

    assert result.active_replay_input_promotion_implemented is True
    assert result.active_replay_input_promotion_views_implemented is True
    assert result.latest_active_replay_input_promotion_run_id == promotion.promotion_run_id
    assert result.latest_active_replay_input_promotion_status == "PROMOTION_READY_FOR_HUMAN_REVIEW"
    assert result.latest_active_replay_input_promotion_health_status == "PASS"
    assert result.latest_active_replay_input_promotion_workflow_stage == "PROMOTION_READY_FOR_HUMAN_REVIEW"
    assert result.active_replay_input_promotion_ready_for_human_review is True
    assert result.active_replay_input_promotion_active_replay_input_ready is False
    assert result.active_replay_input_promotion_active_replay_input is False
    assert result.active_replay_input_promotion_active_ready_emitted is False
    assert result.active_replay_input_promotion_forward_labels_exist is False
    assert result.active_replay_input_promotion_weights_trained is False
    assert result.active_replay_input_promotion_active_stock_profile_exists is False
    assert result.active_replay_input_promotion_real_buy_review_eligible is False
    assert result.active_replay_input_promotion_approval_applied is False
    assert result.active_replay_input_promotion_order_placed is False
    assert result.active_replay_input_promotion_llm_api_called is False
    assert result.active_replay_input_promotion_external_api_called is False
    assert result.active_replay_input_promotion_cache_mutated is False
    assert result.active_replay_input_promotion_current_candidates_run is False
    assert result.active_replay_input_promotion_snapshot_built is False
    assert result.active_replay_input_promotion_signal_semantics_changed is False
    assert result.active_replay_input_promotion_report_only is True
    assert result.active_replay_input_promotion_diagnostic_only is True
    assert result.active_replay_input_promotion_no_live_trading is True
    assert result.active_replay_input_promotion_no_broker_api is True
    assert result.active_replay_input_promotion_no_order_placement is True
    assert result.active_replay_input_promotion_no_message_sent is True
    assert result.workflow_stage == "PROMOTION_READY_FOR_HUMAN_REVIEW"
    assert result.workflow_stage != "ACTIVE_REPLAY_INPUT_READY"
    assert row["status"] == "PROMOTION_READY_FOR_HUMAN_REVIEW"

    summary = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str)
    metadata = json.loads(Path(result.artifact_paths["metadata"]).read_text(encoding="utf-8"))
    assert summary.loc[0, "latest_active_replay_input_promotion_run_id"] == promotion.promotion_run_id
    assert summary.loc[0, "active_replay_input_promotion_active_replay_input_ready"] == "False"
    assert metadata["latest_active_replay_input_promotion_workflow_stage"] == "PROMOTION_READY_FOR_HUMAN_REVIEW"
    assert metadata["active_replay_input_promotion_active_replay_input_ready"] is False
    assert metadata["active_replay_input_promotion_active_replay_input"] is False


def test_research_status_preserves_paper_priority_over_active_replay_input_promotion(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    _active_replay_input_promotion_ready(root)
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.latest_active_replay_input_promotion_workflow_stage == "PROMOTION_READY_FOR_HUMAN_REVIEW"
    assert result.active_replay_input_promotion_ready_for_human_review is True
    assert result.active_replay_input_promotion_active_replay_input_ready is False
    assert result.active_replay_input_promotion_active_replay_input is False


def test_cli_research_status_prints_active_replay_input_promotion_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    promotion = _active_replay_input_promotion_ready(root)

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert f"latest_active_replay_input_promotion_run_id: {promotion.promotion_run_id}" in output.out
    assert "latest_active_replay_input_promotion_status: PROMOTION_READY_FOR_HUMAN_REVIEW" in output.out
    assert "latest_active_replay_input_promotion_health_status: PASS" in output.out
    assert "latest_active_replay_input_promotion_workflow_stage: PROMOTION_READY_FOR_HUMAN_REVIEW" in output.out
    assert "active_replay_input_promotion_ready_for_human_review: True" in output.out
    assert "active_replay_input_promotion_active_replay_input_ready: False" in output.out
    assert "active_replay_input_promotion_active_replay_input: False" in output.out
    assert "active_replay_input_promotion_active_ready_emitted: False" in output.out
    assert "active_replay_input_promotion_forward_labels_exist: False" in output.out
    assert "active_replay_input_promotion_weights_trained: False" in output.out
    assert "active_replay_input_promotion_active_stock_profile_exists: False" in output.out
    assert "active_replay_input_promotion_real_buy_review_eligible: False" in output.out
    assert "active_replay_input_promotion_approval_applied: False" in output.out
    assert "active_replay_input_promotion_order_placed: False" in output.out
    assert "active_replay_input_promotion_llm_api_called: False" in output.out
    assert "active_replay_input_promotion_external_api_called: False" in output.out
    assert "active_replay_input_promotion_cache_mutated: False" in output.out
    assert "active_replay_input_promotion_current_candidates_run: False" in output.out
    assert "active_replay_input_promotion_snapshot_built: False" in output.out
    assert "active_replay_input_promotion_signal_semantics_changed: False" in output.out
    assert "active_replay_input_promotion_report_only: True" in output.out
    assert "active_replay_input_promotion_diagnostic_only: True" in output.out
    assert "active_replay_input_promotion_no_live_trading: True" in output.out
    assert "active_replay_input_promotion_no_broker_api: True" in output.out
    assert "active_replay_input_promotion_no_order_placement: True" in output.out
    assert "active_replay_input_promotion_no_message_sent: True" in output.out
    assert "ACTIVE_REPLAY_INPUT_READY" not in output.out


def test_research_status_includes_active_replay_input_acceptance_context(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    acceptance = _active_replay_input_acceptance_ready(root)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "ACTIVE_REPLAY_INPUT_ACCEPTANCE_STATUS"
    ].iloc[0]

    assert result.active_replay_input_acceptance_implemented is True
    assert result.active_replay_input_acceptance_views_implemented is True
    assert result.latest_active_replay_input_acceptance_run_id == acceptance.acceptance_run_id
    assert result.latest_active_replay_input_acceptance_status == "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW"
    assert result.latest_active_replay_input_acceptance_health_status == "PASS"
    assert result.latest_active_replay_input_acceptance_workflow_stage == "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW"
    assert result.active_replay_input_acceptance_ready_for_active_ready_review is True
    assert result.active_replay_input_acceptance_active_replay_input_ready is False
    assert result.active_replay_input_acceptance_active_replay_input is False
    assert result.active_replay_input_acceptance_active_ready_emitted is False
    assert result.active_replay_input_acceptance_forward_labels_exist is False
    assert result.active_replay_input_acceptance_weights_trained is False
    assert result.active_replay_input_acceptance_active_stock_profile_exists is False
    assert result.active_replay_input_acceptance_real_buy_review_eligible is False
    assert result.active_replay_input_acceptance_approval_applied is False
    assert result.active_replay_input_acceptance_order_placed is False
    assert result.active_replay_input_acceptance_llm_api_called is False
    assert result.active_replay_input_acceptance_external_api_called is False
    assert result.active_replay_input_acceptance_cache_mutated is False
    assert result.active_replay_input_acceptance_current_candidates_run is False
    assert result.active_replay_input_acceptance_snapshot_built is False
    assert result.active_replay_input_acceptance_signal_semantics_changed is False
    assert result.active_replay_input_acceptance_report_only is True
    assert result.active_replay_input_acceptance_diagnostic_only is True
    assert result.active_replay_input_acceptance_no_live_trading is True
    assert result.active_replay_input_acceptance_no_broker_api is True
    assert result.active_replay_input_acceptance_no_order_placement is True
    assert result.active_replay_input_acceptance_no_message_sent is True
    assert result.workflow_stage == "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW"
    assert result.workflow_stage != "ACTIVE_REPLAY_INPUT_READY"
    assert row["status"] == "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW"

    summary = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str)
    metadata = json.loads(Path(result.artifact_paths["metadata"]).read_text(encoding="utf-8"))
    assert summary.loc[0, "latest_active_replay_input_acceptance_run_id"] == acceptance.acceptance_run_id
    assert summary.loc[0, "active_replay_input_acceptance_active_replay_input_ready"] == "False"
    assert metadata["latest_active_replay_input_acceptance_workflow_stage"] == (
        "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW"
    )
    assert metadata["active_replay_input_acceptance_active_replay_input_ready"] is False
    assert metadata["active_replay_input_acceptance_active_replay_input"] is False
    assert metadata["active_replay_input_acceptance_active_ready_emitted"] is False


def test_research_status_preserves_paper_priority_over_active_replay_input_acceptance(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    _active_replay_input_acceptance_ready(root)
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.latest_active_replay_input_acceptance_workflow_stage == (
        "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW"
    )
    assert result.active_replay_input_acceptance_ready_for_active_ready_review is True
    assert result.active_replay_input_acceptance_active_replay_input_ready is False
    assert result.active_replay_input_acceptance_active_replay_input is False
    assert result.active_replay_input_acceptance_active_ready_emitted is False


def test_cli_research_status_prints_active_replay_input_acceptance_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    acceptance = _active_replay_input_acceptance_ready(root)

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert f"latest_active_replay_input_acceptance_run_id: {acceptance.acceptance_run_id}" in output.out
    assert "latest_active_replay_input_acceptance_status: ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW" in output.out
    assert "latest_active_replay_input_acceptance_health_status: PASS" in output.out
    assert (
        "latest_active_replay_input_acceptance_workflow_stage: ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW"
        in output.out
    )
    assert "active_replay_input_acceptance_ready_for_active_ready_review: True" in output.out
    assert "active_replay_input_acceptance_active_replay_input_ready: False" in output.out
    assert "active_replay_input_acceptance_active_replay_input: False" in output.out
    assert "active_replay_input_acceptance_active_ready_emitted: False" in output.out
    assert "active_replay_input_acceptance_forward_labels_exist: False" in output.out
    assert "active_replay_input_acceptance_weights_trained: False" in output.out
    assert "active_replay_input_acceptance_active_stock_profile_exists: False" in output.out
    assert "active_replay_input_acceptance_real_buy_review_eligible: False" in output.out
    assert "active_replay_input_acceptance_approval_applied: False" in output.out
    assert "active_replay_input_acceptance_order_placed: False" in output.out
    assert "active_replay_input_acceptance_llm_api_called: False" in output.out
    assert "active_replay_input_acceptance_external_api_called: False" in output.out
    assert "active_replay_input_acceptance_cache_mutated: False" in output.out
    assert "active_replay_input_acceptance_current_candidates_run: False" in output.out
    assert "active_replay_input_acceptance_snapshot_built: False" in output.out
    assert "active_replay_input_acceptance_signal_semantics_changed: False" in output.out
    assert "active_replay_input_acceptance_report_only: True" in output.out
    assert "active_replay_input_acceptance_diagnostic_only: True" in output.out
    assert "active_replay_input_acceptance_no_live_trading: True" in output.out
    assert "active_replay_input_acceptance_no_broker_api: True" in output.out
    assert "active_replay_input_acceptance_no_order_placement: True" in output.out
    assert "active_replay_input_acceptance_no_message_sent: True" in output.out
    assert "ACTIVE_REPLAY_INPUT_READY" not in output.out


def test_active_replay_input_acceptance_checkpoint_docs_and_project_source_policy() -> None:
    doc = Path("docs/active_replay_input_acceptance.md")
    checkpoint = Path("docs/release_checkpoint_v1.32.0.md")
    source_note = Path("SOURCE_UPDATE_NOTES_v1_32_0.md")

    for path in [doc, checkpoint, source_note]:
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "active-replay-input-acceptance" in text
        assert "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW" in text
        assert "ACTIVE_REPLAY_INPUT_READY" in text
        assert "does not create active replay input" in text
        assert "does not run replay" in text
        assert "does not compute forward labels" in text
        assert "does not train weights" in text
        assert "does not create active stock profiles" in text
        assert "does not create real buy-review eligibility" in text

    assert "PAPER_WORKFLOW_READY" in checkpoint.read_text(encoding="utf-8")
    source_text = source_note.read_text(encoding="utf-8")
    assert "docs/project_sources" in source_text
    assert "intentionally absent from Git" in source_text
    assert not Path("docs/project_sources").exists()


def test_research_status_includes_active_replay_input_active_ready_context(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    active_ready = _active_replay_input_active_ready_ready(root)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "ACTIVE_REPLAY_INPUT_ACTIVE_READY_STATUS"
    ].iloc[0]

    assert result.active_replay_input_active_ready_implemented is True
    assert result.active_replay_input_active_ready_views_implemented is True
    assert result.latest_active_replay_input_active_ready_run_id == active_ready.active_ready_run_id
    assert result.latest_active_replay_input_active_ready_status == "ACTIVE_READY_READY_FOR_FINAL_REVIEW"
    assert result.latest_active_replay_input_active_ready_health_status == "PASS"
    assert result.latest_active_replay_input_active_ready_workflow_stage == "ACTIVE_READY_READY_FOR_FINAL_REVIEW"
    assert result.ready_for_final_review is True
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.active_ready_emitted is False
    assert result.forward_labels_exist is False
    assert result.weights_trained is False
    assert result.active_stock_profile_exists is False
    assert result.real_buy_review_eligible is False
    assert result.approval_applied is False
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
    assert result.signal_semantics_changed is False
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.no_live_trading is True
    assert result.no_broker_api is True
    assert result.no_order_placement is True
    assert result.no_message_sent is True
    assert result.workflow_stage == "ACTIVE_READY_READY_FOR_FINAL_REVIEW"
    assert result.workflow_stage != "ACTIVE_REPLAY_INPUT_READY"
    assert row["status"] == "ACTIVE_READY_READY_FOR_FINAL_REVIEW"

    summary = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str)
    metadata = json.loads(Path(result.artifact_paths["metadata"]).read_text(encoding="utf-8"))
    assert summary.loc[0, "latest_active_replay_input_active_ready_run_id"] == active_ready.active_ready_run_id
    assert summary.loc[0, "active_replay_input_ready"] == "False"
    assert metadata["latest_active_replay_input_active_ready_workflow_stage"] == (
        "ACTIVE_READY_READY_FOR_FINAL_REVIEW"
    )
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_ready_emitted"] is False


def test_research_status_preserves_paper_priority_over_active_replay_input_active_ready(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    _active_replay_input_active_ready_ready(root)
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.latest_active_replay_input_active_ready_workflow_stage == "ACTIVE_READY_READY_FOR_FINAL_REVIEW"
    assert result.ready_for_final_review is True
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.active_ready_emitted is False


def test_cli_research_status_prints_active_replay_input_active_ready_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    active_ready = _active_replay_input_active_ready_ready(root)

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert f"latest_active_replay_input_active_ready_run_id: {active_ready.active_ready_run_id}" in output.out
    assert "latest_active_replay_input_active_ready_status: ACTIVE_READY_READY_FOR_FINAL_REVIEW" in output.out
    assert "latest_active_replay_input_active_ready_health_status: PASS" in output.out
    assert (
        "latest_active_replay_input_active_ready_workflow_stage: ACTIVE_READY_READY_FOR_FINAL_REVIEW"
        in output.out
    )
    assert "ready_for_final_review: True" in output.out
    assert "active_replay_input_ready: False" in output.out
    assert "active_replay_input: False" in output.out
    assert "active_ready_emitted: False" in output.out
    assert "forward_labels_exist: False" in output.out
    assert "weights_trained: False" in output.out
    assert "active_stock_profile_exists: False" in output.out
    assert "real_buy_review_eligible: False" in output.out
    assert "approval_applied: False" in output.out
    assert "order_placed: False" in output.out
    assert "message_sent: False" in output.out
    assert "llm_api_called: False" in output.out
    assert "external_api_called: False" in output.out
    assert "cache_mutated: False" in output.out
    assert "data_raw_written: False" in output.out
    assert "data_processed_written: False" in output.out
    assert "data_cache_written: False" in output.out
    assert "current_candidates_run: False" in output.out
    assert "snapshot_built: False" in output.out
    assert "signal_semantics_changed: False" in output.out


def test_active_replay_input_active_ready_checkpoint_docs_and_project_source_policy() -> None:
    doc = Path("docs/active_replay_input_active_ready.md")
    checkpoint = Path("docs/release_checkpoint_v1.33.0.md")
    source_note = Path("SOURCE_UPDATE_NOTES_v1_33_0.md")

    for path in [doc, checkpoint, source_note]:
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "active-replay-input-active-ready" in text
        assert "ACTIVE_READY_READY_FOR_FINAL_REVIEW" in text
        assert "ACTIVE_REPLAY_INPUT_READY" in text
        assert "does not create active replay input" in text
        assert "does not run replay" in text
        assert "does not compute forward labels" in text
        assert "does not train weights" in text
        assert "does not create active stock profiles" in text
        assert "does not create real buy-review eligibility" in text
        assert "does not authorize trading" in text

    assert "PAPER_WORKFLOW_READY" in checkpoint.read_text(encoding="utf-8")
    source_text = source_note.read_text(encoding="utf-8")
    assert "docs/project_sources" in source_text
    assert "intentionally absent from Git" in source_text
    assert not Path("docs/project_sources").exists()


def test_research_status_includes_active_replay_input_final_review_context(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    final_review = _active_replay_input_final_review_ready(root)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "ACTIVE_REPLAY_INPUT_FINAL_REVIEW_STATUS"
    ].iloc[0]

    assert result.active_replay_input_final_review_implemented is True
    assert result.active_replay_input_final_review_views_implemented is True
    assert result.latest_active_replay_input_final_review_run_id == final_review.final_review_run_id
    assert result.latest_active_replay_input_final_review_status == "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW"
    assert result.latest_active_replay_input_final_review_health_status == "PASS"
    assert result.latest_active_replay_input_final_review_workflow_stage == (
        "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW"
    )
    assert result.ready_for_emission_review is True
    assert result.active_replay_input_final_review_active_replay_input_ready is False
    assert result.active_replay_input_final_review_active_replay_input is False
    assert result.active_replay_input_final_review_active_ready_emitted is False
    assert result.active_replay_input_final_review_forward_labels_exist is False
    assert result.active_replay_input_final_review_weights_trained is False
    assert result.active_replay_input_final_review_active_stock_profile_exists is False
    assert result.active_replay_input_final_review_real_buy_review_eligible is False
    assert result.active_replay_input_final_review_approval_applied is False
    assert result.active_replay_input_final_review_order_placed is False
    assert result.active_replay_input_final_review_message_sent is False
    assert result.active_replay_input_final_review_llm_api_called is False
    assert result.active_replay_input_final_review_external_api_called is False
    assert result.active_replay_input_final_review_cache_mutated is False
    assert result.active_replay_input_final_review_data_raw_written is False
    assert result.active_replay_input_final_review_data_processed_written is False
    assert result.active_replay_input_final_review_data_cache_written is False
    assert result.active_replay_input_final_review_current_candidates_run is False
    assert result.active_replay_input_final_review_snapshot_built is False
    assert result.active_replay_input_final_review_signal_semantics_changed is False
    assert result.active_replay_input_final_review_report_only is True
    assert result.active_replay_input_final_review_diagnostic_only is True
    assert result.active_replay_input_final_review_no_live_trading is True
    assert result.active_replay_input_final_review_no_broker_api is True
    assert result.active_replay_input_final_review_no_order_placement is True
    assert result.active_replay_input_final_review_no_message_sent is True
    assert result.workflow_stage == "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW"
    assert result.workflow_stage != "ACTIVE_REPLAY_INPUT_READY"
    assert row["status"] == "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW"

    summary = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str)
    metadata = json.loads(Path(result.artifact_paths["metadata"]).read_text(encoding="utf-8"))
    assert summary.loc[0, "latest_active_replay_input_final_review_run_id"] == (
        final_review.final_review_run_id
    )
    assert summary.loc[0, "active_replay_input_final_review_active_replay_input_ready"] == "False"
    assert metadata["latest_active_replay_input_final_review_workflow_stage"] == (
        "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW"
    )
    assert metadata["ready_for_emission_review"] is True
    assert metadata["active_replay_input_final_review_active_replay_input_ready"] is False
    assert metadata["active_replay_input_final_review_active_replay_input"] is False
    assert metadata["active_replay_input_final_review_active_ready_emitted"] is False


def test_research_status_preserves_paper_priority_over_active_replay_input_final_review(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    _active_replay_input_final_review_ready(root)
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.latest_active_replay_input_final_review_workflow_stage == (
        "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW"
    )
    assert result.ready_for_emission_review is True
    assert result.active_replay_input_final_review_active_replay_input_ready is False
    assert result.active_replay_input_final_review_active_replay_input is False
    assert result.active_replay_input_final_review_active_ready_emitted is False


def test_cli_research_status_prints_active_replay_input_final_review_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    final_review = _active_replay_input_final_review_ready(root)

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert f"latest_active_replay_input_final_review_run_id: {final_review.final_review_run_id}" in output.out
    assert "latest_active_replay_input_final_review_status: FINAL_REVIEW_READY_FOR_EMISSION_REVIEW" in output.out
    assert "latest_active_replay_input_final_review_health_status: PASS" in output.out
    assert (
        "latest_active_replay_input_final_review_workflow_stage: FINAL_REVIEW_READY_FOR_EMISSION_REVIEW"
        in output.out
    )
    assert "ready_for_emission_review: True" in output.out
    assert "active_replay_input_final_review_active_replay_input_ready: False" in output.out
    assert "active_replay_input_final_review_active_replay_input: False" in output.out
    assert "active_replay_input_final_review_active_ready_emitted: False" in output.out
    assert "active_replay_input_final_review_forward_labels_exist: False" in output.out
    assert "active_replay_input_final_review_weights_trained: False" in output.out
    assert "active_replay_input_final_review_active_stock_profile_exists: False" in output.out
    assert "active_replay_input_final_review_real_buy_review_eligible: False" in output.out
    assert "active_replay_input_final_review_approval_applied: False" in output.out
    assert "active_replay_input_final_review_order_placed: False" in output.out
    assert "active_replay_input_final_review_message_sent: False" in output.out
    assert "active_replay_input_final_review_llm_api_called: False" in output.out
    assert "active_replay_input_final_review_external_api_called: False" in output.out
    assert "active_replay_input_final_review_cache_mutated: False" in output.out
    assert "active_replay_input_final_review_data_raw_written: False" in output.out
    assert "active_replay_input_final_review_data_processed_written: False" in output.out
    assert "active_replay_input_final_review_data_cache_written: False" in output.out
    assert "active_replay_input_final_review_current_candidates_run: False" in output.out
    assert "active_replay_input_final_review_snapshot_built: False" in output.out
    assert "active_replay_input_final_review_signal_semantics_changed: False" in output.out


def test_active_replay_input_final_review_checkpoint_docs_and_project_source_policy() -> None:
    doc = Path("docs/active_replay_input_final_review.md")
    checkpoint = Path("docs/release_checkpoint_v1.34.0.md")
    source_note = Path("SOURCE_UPDATE_NOTES_v1_34_0.md")

    for path in [doc, checkpoint, source_note]:
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "active-replay-input-final-review" in text
        assert "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW" in text
        assert "ACTIVE_REPLAY_INPUT_READY" in text
        assert "does not create active replay input" in text
        assert "does not run replay" in text
        assert "does not compute forward labels" in text
        assert "does not train weights" in text
        assert "does not create active stock profiles" in text
        assert "does not create real buy-review eligibility" in text
        assert "does not authorize trading" in text

    assert "PAPER_WORKFLOW_READY" in checkpoint.read_text(encoding="utf-8")
    source_text = source_note.read_text(encoding="utf-8")
    assert "docs/project_sources" in source_text
    assert "intentionally absent from Git" in source_text
    assert not Path("docs/project_sources").exists()


def test_research_status_includes_active_replay_input_emission_context(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    emission = _active_replay_input_emission_ready(root)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "ACTIVE_REPLAY_INPUT_EMISSION_STATUS"
    ].iloc[0]

    assert result.active_replay_input_emission_implemented is True
    assert result.active_replay_input_emission_views_implemented is True
    assert result.latest_active_replay_input_emission_run_id == emission.emission_run_id
    assert result.latest_active_replay_input_emission_status == "EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW"
    assert result.latest_active_replay_input_emission_health_status == "PASS"
    assert result.latest_active_replay_input_emission_workflow_stage == (
        "EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW"
    )
    assert result.ready_for_active_replay_input_ready_review is True
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
    assert result.weights_trained is False
    assert result.active_stock_profile_exists is False
    assert result.real_buy_review_eligible is False
    assert result.approval_applied is False
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
    assert result.signal_semantics_changed is False
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.no_live_trading is True
    assert result.no_broker_api is True
    assert result.no_order_placement is True
    assert result.no_message_sent is True
    assert result.workflow_stage == "EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW"
    assert result.workflow_stage != "ACTIVE_REPLAY_INPUT_READY"
    assert row["status"] == "EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW"

    summary = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str)
    metadata = json.loads(Path(result.artifact_paths["metadata"]).read_text(encoding="utf-8"))
    assert summary.loc[0, "latest_active_replay_input_emission_run_id"] == emission.emission_run_id
    assert summary.loc[0, "active_replay_input_ready"] == "False"
    assert summary.loc[0, "active_replay_input"] == "False"
    assert summary.loc[0, "active_ready_emitted"] == "False"
    assert metadata["latest_active_replay_input_emission_workflow_stage"] == (
        "EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW"
    )
    assert metadata["ready_for_active_replay_input_ready_review"] is True
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_ready_emitted"] is False


def test_research_status_preserves_paper_priority_over_active_replay_input_emission(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    _active_replay_input_emission_ready(root)
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.latest_active_replay_input_emission_workflow_stage == (
        "EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW"
    )
    assert result.ready_for_active_replay_input_ready_review is True
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.active_ready_emitted is False


def test_cli_research_status_prints_active_replay_input_emission_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    emission = _active_replay_input_emission_ready(root)

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert f"latest_active_replay_input_emission_run_id: {emission.emission_run_id}" in output.out
    assert "latest_active_replay_input_emission_status: EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW" in output.out
    assert "latest_active_replay_input_emission_health_status: PASS" in output.out
    assert (
        "latest_active_replay_input_emission_workflow_stage: "
        "EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW"
    ) in output.out
    assert "ready_for_active_replay_input_ready_review: True" in output.out
    assert "active_replay_input_ready: False" in output.out
    assert "active_replay_input: False" in output.out
    assert "active_ready_emitted: False" in output.out
    assert "replay_execution_allowed: False" in output.out
    assert "forward_labels_allowed: False" in output.out
    assert "training_allowed: False" in output.out
    assert "stock_profile_allowed: False" in output.out
    assert "buy_review_allowed: False" in output.out
    assert "trading_allowed: False" in output.out


def test_active_replay_input_emission_checkpoint_docs_and_project_source_policy() -> None:
    doc = Path("docs/active_replay_input_emission.md")
    checkpoint = Path("docs/release_checkpoint_v1.35.0.md")
    source_note = Path("SOURCE_UPDATE_NOTES_v1_35_0.md")

    for path in [doc, checkpoint, source_note]:
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "active-replay-input-emission" in text
        assert "EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW" in text
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
    assert "PAPER_WORKFLOW_READY" in checkpoint_text
    assert "96fae2783877" in checkpoint_text
    source_text = source_note.read_text(encoding="utf-8")
    assert "docs/project_sources" in source_text
    assert "intentionally absent from Git" in source_text
    assert "after tag v1.35.0" in source_text
    assert not Path("docs/project_sources").exists()


def test_research_status_includes_active_replay_input_ready_context(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    active_ready = _active_replay_input_ready_ready(root)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "ACTIVE_REPLAY_INPUT_READY_STATUS"
    ].iloc[0]

    assert result.active_replay_input_ready_workflow_implemented is True
    assert result.active_replay_input_ready_views_implemented is True
    assert result.latest_active_replay_input_ready_run_id == active_ready.active_ready_run_id
    assert result.latest_active_replay_input_ready_status == "READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY"
    assert result.latest_active_replay_input_ready_health_status == "PASS"
    assert result.latest_active_replay_input_ready_workflow_stage == (
        "ACTIVE_REPLAY_INPUT_READY_READY_TO_EMIT"
    )
    assert result.ready_to_emit_active_replay_input_ready is True
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
    assert result.message_sent is False
    assert result.llm_api_called is False
    assert result.external_api_called is False
    assert result.cache_mutated is False
    assert result.data_raw_written is False
    assert result.data_processed_written is False
    assert result.data_cache_written is False
    assert result.current_candidates_run is False
    assert result.snapshot_built is False
    assert result.signal_semantics_changed is False
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.no_live_trading is True
    assert result.no_broker_api is True
    assert result.no_order_placement is True
    assert result.no_message_sent is True
    assert result.workflow_stage == "ACTIVE_REPLAY_INPUT_READY_READY_TO_EMIT"
    assert result.workflow_stage != "ACTIVE_REPLAY_INPUT_READY"
    assert row["status"] == "READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY"

    summary = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str)
    metadata = json.loads(Path(result.artifact_paths["metadata"]).read_text(encoding="utf-8"))
    assert summary.loc[0, "latest_active_replay_input_ready_run_id"] == (
        active_ready.active_ready_run_id
    )
    assert summary.loc[0, "ready_to_emit_active_replay_input_ready"] == "True"
    assert summary.loc[0, "active_replay_input_ready"] == "False"
    assert summary.loc[0, "active_replay_input"] == "False"
    assert summary.loc[0, "active_ready_emitted"] == "False"
    assert metadata["latest_active_replay_input_ready_workflow_stage"] == (
        "ACTIVE_REPLAY_INPUT_READY_READY_TO_EMIT"
    )
    assert metadata["ready_to_emit_active_replay_input_ready"] is True
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_ready_emitted"] is False


def test_research_status_preserves_paper_priority_over_active_replay_input_ready(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    _active_replay_input_ready_ready(root)
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.latest_active_replay_input_ready_workflow_stage == (
        "ACTIVE_REPLAY_INPUT_READY_READY_TO_EMIT"
    )
    assert result.ready_to_emit_active_replay_input_ready is True
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.active_ready_emitted is False


def test_cli_research_status_prints_active_replay_input_ready_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = tmp_path / "outputs" / "reports"
    root.mkdir(parents=True, exist_ok=True)
    active_ready = _active_replay_input_ready_ready(root)

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert f"latest_active_replay_input_ready_run_id: {active_ready.active_ready_run_id}" in output.out
    assert "latest_active_replay_input_ready_status: READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY" in output.out
    assert "latest_active_replay_input_ready_health_status: PASS" in output.out
    assert (
        "latest_active_replay_input_ready_workflow_stage: ACTIVE_REPLAY_INPUT_READY_READY_TO_EMIT"
        in output.out
    )
    assert "ready_to_emit_active_replay_input_ready: True" in output.out
    assert "active_replay_input_ready: False" in output.out
    assert "active_replay_input: False" in output.out
    assert "active_ready_emitted: False" in output.out
    assert "replay_execution_allowed: False" in output.out
    assert "replay_decisions_exist: False" in output.out
    assert "forward_labels_allowed: False" in output.out
    assert "forward_labels_exist: False" in output.out
    assert "training_allowed: False" in output.out
    assert "weights_trained: False" in output.out
    assert "stock_profile_allowed: False" in output.out
    assert "active_stock_profile_exists: False" in output.out
    assert "buy_review_allowed: False" in output.out
    assert "real_buy_review_eligible: False" in output.out
    assert "trading_allowed: False" in output.out


def test_active_replay_input_ready_checkpoint_docs_and_project_source_policy() -> None:
    doc = Path("docs/active_replay_input_ready.md")
    checkpoint = Path("docs/release_checkpoint_v1.37.0.md")
    source_note = Path("SOURCE_UPDATE_NOTES_v1_37_0.md")

    for path in [doc, checkpoint, source_note]:
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "active-replay-input-ready" in text
        assert "READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY" in text
        assert "ACTIVE_REPLAY_INPUT_READY" in text
        assert "does not emit ACTIVE_REPLAY_INPUT_READY" in text
        assert "does not create active replay input" in text
        assert "does not run replay" in text
        assert "does not create replay decisions" in text
        assert "does not compute forward labels" in text
        assert "does not train weights" in text
        assert "does not create active stock profiles" in text
        assert "does not create real buy-review eligibility" in text
        assert "does not authorize trading" in text

    checkpoint_text = checkpoint.read_text(encoding="utf-8")
    assert "PAPER_WORKFLOW_READY" in checkpoint_text
    assert "ac0d55bd52b2" in checkpoint_text
    source_text = source_note.read_text(encoding="utf-8")
    assert "docs/project_sources" in source_text
    assert "intentionally absent from Git" in source_text
    assert "after tag v1.37.0" in source_text
    assert not Path("docs/project_sources").exists()


def test_dashboard_includes_universe_profile_policy_audit_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _universe_profile_policy_audit(root)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "UNIVERSE_PROFILE_POLICY_AUDIT_STATUS"
    ].iloc[0]

    assert result.latest_universe_profile_policy_audit_id
    assert result.universe_profile_policy_audit_status == "WARN"
    assert result.universe_profile_policy_audit_stage == "UNIVERSE_PROFILE_POLICY_AMBIGUOUS_MIXED_UNIVERSE"
    assert result.universe_profile_policy_audit_health_status == "WARN"
    assert result.universe_profile_policy_row_count == 2
    assert result.universe_profile_policy_stock_row_count == 1
    assert result.universe_profile_policy_etf_row_count == 1
    assert result.universe_profile_policy_ambiguous_policy_count == 2
    assert result.workflow_stage == "UNIVERSE_PROFILE_POLICY_AMBIGUOUS_MIXED_UNIVERSE"
    assert row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"


def test_dashboard_preserves_later_paper_priority_over_universe_profile_policy_audit(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _universe_profile_policy_audit(root)
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "UNIVERSE_PROFILE_POLICY_AUDIT_STATUS"
    ].iloc[0]

    assert result.universe_profile_policy_audit_status == "WARN"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert row["warning_classification"] == "STALE_ARTIFACT_WARNING"


def test_dashboard_exports_universe_profile_policy_audit_fields_to_summary_and_metadata(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _universe_profile_policy_audit(root)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["universe_profile_policy_audit_status"] == "WARN"
    assert row["universe_profile_policy_audit_stage"] == "UNIVERSE_PROFILE_POLICY_AMBIGUOUS_MIXED_UNIVERSE"
    assert row["universe_profile_policy_stock_row_count"] == "1"
    assert row["universe_profile_policy_etf_row_count"] == "1"
    assert row["universe_profile_policy_ambiguous_policy_count"] == "2"
    assert metadata["universe_profile_policy_ambiguous_policy_count"] == 2
    assert metadata["universe_profile_policy_stock_row_count"] == 1


def test_cli_research_status_prints_universe_profile_policy_audit_fields(
    tmp_path: Path,
    capsys,
) -> None:
    root = _reports_root(tmp_path)
    _universe_profile_policy_audit(root)

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "universe_profile_policy_audit_status: WARN" in output.out
    assert "universe_profile_policy_audit_stage: UNIVERSE_PROFILE_POLICY_AMBIGUOUS_MIXED_UNIVERSE" in output.out
    assert "universe_profile_policy_stock_row_count: 1" in output.out
    assert "universe_profile_policy_etf_row_count: 1" in output.out
    assert "universe_profile_policy_ambiguous_policy_count: 2" in output.out


def test_dashboard_detects_current_to_paper_handoff_artifacts(tmp_path: Path) -> None:
    root = _workflow_to_paper_handoff(_reports_root(tmp_path))

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.current_to_paper_status == "READY"
    assert result.workflow_stage == "PAPER_HANDOFF_READY"


def test_dashboard_detects_current_to_paper_review_artifacts(tmp_path: Path) -> None:
    root = _workflow_to_review_template(_reports_root(tmp_path))

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.current_to_paper_review_status == "READY"
    assert result.workflow_stage == "REVIEW_TEMPLATE_READY"


def test_dashboard_detects_paper_workflow_status_artifacts(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _paper_workflow_status(root, status="PASS")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.paper_workflow_status == "PASS"
    assert result.workflow_stage == "LOCAL_RESEARCH_WORKFLOW_COMPLETE"


def test_dashboard_infers_next_action_when_no_data_exists(tmp_path: Path) -> None:
    result = run_local_research_dashboard(root=_reports_root(tmp_path), output_dir=tmp_path / "dashboard")

    assert result.next_manual_action == "Run data-pipeline."


def test_dashboard_infers_next_action_after_data_preparation(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _data_preparation_status(root)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.next_manual_action == "Run current-candidates."


def test_dashboard_infers_next_action_after_current_candidates(tmp_path: Path) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.next_manual_action == "Run current-candidates-index."
    assert infer_local_research_workflow_stage(result.dashboard_frame) == "CURRENT_CANDIDATES_READY"
    assert infer_local_research_next_action(result.dashboard_frame) == "Run current-candidates-index."


def test_dashboard_infers_next_action_after_paper_handoff(tmp_path: Path) -> None:
    root = _workflow_to_paper_handoff(_reports_root(tmp_path))

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.next_manual_action == "Run current-to-paper-review."


def test_dashboard_infers_next_action_when_review_template_needs_editing(tmp_path: Path) -> None:
    root = _workflow_to_review_template(_reports_root(tmp_path))

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.next_manual_action == "Manually edit review_updates_template.csv."


def test_dashboard_marks_needs_attention_when_health_or_reconciliation_fails(tmp_path: Path) -> None:
    root = _workflow_to_daily(_reports_root(tmp_path))
    _reconciliation(root, status="FAIL", errors=1)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "LOCAL_RESEARCH_NEEDS_ATTENTION"
    assert result.status == "FAIL"
    assert result.next_manual_action == "Review warnings/errors."


def test_dashboard_writes_markdown_report(tmp_path: Path) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.artifact_paths["local_research_dashboard"].exists()
    content = result.artifact_paths["local_research_dashboard"].read_text(encoding="utf-8")
    assert "# Unified Local Research Workflow Dashboard" in content


def test_dashboard_writes_dashboard_csv_readable_by_pandas(tmp_path: Path) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_dashboard_csv"])

    assert "workflow_area" in exported.columns
    assert "CURRENT_CANDIDATES" in set(exported["component"])


def test_dashboard_writes_summary_csv_readable_by_pandas(tmp_path: Path) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"])

    assert exported.iloc[0]["workflow_stage"] == "CURRENT_CANDIDATES_READY"


def test_dashboard_summary_csv_exports_market_update_handoff_fields(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_update_handoff_artifact(
        root,
        handoff_id="handoff-export",
        status="WARN",
        pipeline_id="pipeline-export",
        snapshot_quality_status="PASS",
        current_candidate_run_id="candidate-export",
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    row = exported.iloc[0].to_dict()

    assert row["latest_market_update_handoff_id"] == "handoff-export"
    assert row["market_update_handoff_status"] == "WARN"
    assert row["market_update_handoff_stage"] == "CURRENT_CANDIDATES_READY_FOR_PAPER_SMOKE_TEST"
    assert "current-candidates artifact" in row["market_update_handoff_next_action"]
    assert row["market_update_handoff_pipeline_id"] == "pipeline-export"
    assert row["market_update_handoff_snapshot_quality_status"] == "PASS"
    assert row["market_update_handoff_current_candidate_run_id"] == "candidate-export"


def test_dashboard_writes_metadata_json(tmp_path: Path) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["dashboard_id"] == result.dashboard_id
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False
    assert metadata["network_api_calls_used_in_tests"] is False


def test_dashboard_metadata_exports_market_update_handoff_fields_and_preserves_paper_priority(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _market_update_handoff_artifact(
        root,
        handoff_id="handoff-context",
        status="WARN",
        pipeline_id="pipeline-context",
        snapshot_quality_status="PASS",
        current_candidate_run_id="candidate-context",
    )
    _paper_workflow_status(root, status="PASS")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    component_statuses = metadata["component_statuses"]

    assert metadata["workflow_stage"] == "LOCAL_RESEARCH_WORKFLOW_COMPLETE"
    assert metadata["next_manual_action"] == "Review completed local research workflow artifacts."
    assert metadata["latest_market_update_handoff_id"] == "handoff-context"
    assert metadata["market_update_handoff_status"] == "WARN"
    assert metadata["market_update_handoff_stage"] == "CURRENT_CANDIDATES_READY_FOR_PAPER_SMOKE_TEST"
    assert "current-candidates artifact" in metadata["market_update_handoff_next_action"]
    assert metadata["market_update_handoff_pipeline_id"] == "pipeline-context"
    assert metadata["market_update_handoff_snapshot_quality_status"] == "PASS"
    assert metadata["market_update_handoff_current_candidate_run_id"] == "candidate-context"
    assert component_statuses["latest_market_update_handoff_id"] == "handoff-context"
    assert component_statuses["market_update_handoff_pipeline_id"] == "pipeline-context"


def test_research_status_includes_actual_replay_execution_context_and_safety_fields(
    tmp_path: Path,
) -> None:
    executed = run_actual_replay_execute(
        replace(_actual_replay_happy_settings(tmp_path), allow_actual_replay_execution=True)
    )
    root = tmp_path / "outputs" / "reports"

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "ACTUAL_REPLAY_EXECUTE_STATUS"
    ].iloc[0]
    summary = result.summary_frame.iloc[0].to_dict()
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert row["status"] == ACTUAL_REPLAY_EXECUTED
    assert row["workflow_area"] == "ACTUAL_REPLAY_EXECUTE"
    assert result.actual_replay_execution_workflow_implemented is True
    assert result.actual_replay_execution_views_implemented is True
    assert result.latest_actual_replay_execution_run_id == executed.actual_replay_execution_run_id
    assert result.latest_actual_replay_execution_status == ACTUAL_REPLAY_EXECUTED
    assert result.latest_actual_replay_execution_health_status == "PASS"
    assert result.latest_actual_replay_execution_workflow_stage == ACTUAL_REPLAY_EXECUTED
    assert result.actual_replay_execution_artifact_path.endswith(executed.actual_replay_execution_run_id)
    assert result.actual_replay_source_active_input_creation_run_id == "293deb5f459a"
    assert result.actual_replay_source_real_replay_precheck_run_id == "0657ae658ab8"
    assert result.ready_for_actual_replay_execution is True
    assert result.actual_replay_executed is True
    assert result.actual_replay_replay_execution_started is True
    assert result.actual_replay_replay_execution_completed is True
    assert result.actual_replay_replay_decisions_created is False
    assert result.actual_replay_replay_decisions_exist is False
    assert result.actual_replay_replay_decision_artifact_path == ""
    assert result.actual_replay_forward_labels_allowed is False
    assert result.actual_replay_forward_labels_exist is False
    assert result.actual_replay_training_allowed is False
    assert result.actual_replay_weights_trained is False
    assert result.actual_replay_stock_profile_allowed is False
    assert result.actual_replay_active_stock_profile_exists is False
    assert result.actual_replay_buy_review_allowed is False
    assert result.actual_replay_real_buy_review_eligible is False
    assert result.actual_replay_trading_allowed is False
    assert result.actual_replay_order_placed is False
    assert result.actual_replay_broker_api_called is False
    assert result.actual_replay_message_sent is False
    assert result.actual_replay_llm_api_called is False
    assert result.actual_replay_external_api_called is False
    assert result.actual_replay_cache_mutated is False
    assert result.actual_replay_data_raw_written is False
    assert result.actual_replay_data_processed_written is False
    assert result.actual_replay_data_cache_written is False
    assert result.actual_replay_current_candidates_run is False
    assert result.actual_replay_snapshot_built is False
    assert result.actual_replay_signal_semantics_changed is False
    assert result.actual_replay_report_only is True
    assert result.actual_replay_diagnostic_only is True
    assert result.actual_replay_no_live_trading is True
    assert result.actual_replay_no_broker_api is True
    assert result.actual_replay_no_order_placement is True
    assert result.actual_replay_no_message_sent is True
    assert str(summary["actual_replay_replay_decisions_created"]) == "False"
    assert metadata["actual_replay_replay_decisions_created"] is False
    assert metadata["actual_replay_trading_allowed"] is False


def test_research_status_preserves_paper_priority_with_actual_replay_execution(
    tmp_path: Path,
) -> None:
    root = _workflow_to_daily(tmp_path / "outputs" / "reports")
    root.mkdir(parents=True, exist_ok=True)
    _reconciliation(root, status="PASS")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        stale_warning_count=0,
        actionable_warning_count=0,
        blocking_error_count=0,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )
    run_actual_replay_execute(
        replace(
            _actual_replay_happy_settings(tmp_path),
            output_dir=root / "manual_diagnostics" / "actual_replay_execute_v0_1",
            allow_actual_replay_execution=True,
        )
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    actual_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "ACTUAL_REPLAY_EXECUTE_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert actual_row["warning_classification"] == ""
    assert result.latest_actual_replay_execution_status == ACTUAL_REPLAY_EXECUTED
    assert result.actual_replay_replay_decisions_created is False
    assert result.actual_replay_forward_labels_allowed is False
    assert result.actual_replay_training_allowed is False
    assert result.actual_replay_stock_profile_allowed is False
    assert result.actual_replay_buy_review_allowed is False
    assert result.actual_replay_trading_allowed is False


def test_cli_research_status_prints_actual_replay_execution_fields(tmp_path: Path, capsys) -> None:
    run_actual_replay_execute(
        replace(_actual_replay_happy_settings(tmp_path), allow_actual_replay_execution=True)
    )
    root = tmp_path / "outputs" / "reports"

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "actual_replay_execution_workflow_implemented: True" in output.out
    assert f"latest_actual_replay_execution_status: {ACTUAL_REPLAY_EXECUTED}" in output.out
    assert "actual_replay_executed: True" in output.out
    assert "actual_replay_replay_decisions_created: False" in output.out
    assert "actual_replay_forward_labels_allowed: False" in output.out
    assert "actual_replay_training_allowed: False" in output.out
    assert "actual_replay_stock_profile_allowed: False" in output.out
    assert "actual_replay_buy_review_allowed: False" in output.out
    assert "actual_replay_trading_allowed: False" in output.out


def test_research_status_includes_replay_decision_freeze_context_and_safety_fields(
    tmp_path: Path,
) -> None:
    frozen = run_replay_decision_freeze(
        replace(_replay_decision_freeze_happy_settings(tmp_path), allow_replay_decision_freeze=True)
    )
    root = tmp_path / "outputs" / "reports"

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "REPLAY_DECISION_FREEZE_STATUS"
    ].iloc[0]
    summary = result.summary_frame.iloc[0].to_dict()
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert row["status"] == REPLAY_DECISION_FROZEN
    assert row["workflow_area"] == "REPLAY_DECISION_FREEZE"
    assert result.replay_decision_freeze_workflow_implemented is True
    assert result.replay_decision_freeze_views_implemented is True
    assert result.latest_replay_decision_freeze_run_id == frozen.replay_decision_freeze_run_id
    assert result.latest_replay_decision_freeze_status == REPLAY_DECISION_FROZEN
    assert result.latest_replay_decision_freeze_health_status == "PASS"
    assert result.latest_replay_decision_freeze_workflow_stage == REPLAY_DECISION_FROZEN
    assert result.replay_decision_freeze_artifact_path.endswith(frozen.replay_decision_freeze_run_id)
    assert result.source_actual_replay_execution_run_id == "ad8dfa413ded"
    assert result.replay_decision_freeze_source_active_input_creation_run_id == "293deb5f459a"
    assert result.replay_decision_freeze_source_real_replay_precheck_run_id == "0657ae658ab8"
    assert result.replay_decision_freeze_actual_replay_execution_status == ACTUAL_REPLAY_EXECUTED
    assert result.replay_decision_freeze_actual_replay_execution_health_status == "PASS"
    assert result.replay_decision_freeze_actual_replay_executed is True
    assert result.ready_for_replay_decision_freeze is True
    assert result.replay_decision_freeze_executed is True
    assert result.replay_decision_frozen is True
    assert result.replay_decision_artifacts_created is True
    assert result.replay_decision_freeze_replay_decisions_created is True
    assert result.replay_decision_freeze_replay_decisions_exist is True
    assert result.replay_decision_freeze_replay_decision_artifact_path.endswith("replay_decision_rows.csv")
    assert result.replay_decision_freeze_decision_row_count == 1
    assert result.replay_decision_freeze_decision_label_set == "WATCH"
    assert result.replay_decision_freeze_forward_labels_allowed is False
    assert result.replay_decision_freeze_forward_labels_exist is False
    assert result.replay_decision_freeze_forward_return_labels_created is False
    assert result.replay_decision_freeze_training_allowed is False
    assert result.replay_decision_freeze_weights_trained is False
    assert result.replay_decision_freeze_training_result_created is False
    assert result.replay_decision_freeze_stock_profile_allowed is False
    assert result.replay_decision_freeze_active_stock_profile_exists is False
    assert result.replay_decision_freeze_stock_profile_created is False
    assert result.replay_decision_freeze_buy_review_allowed is False
    assert result.replay_decision_freeze_real_buy_review_eligible is False
    assert result.replay_decision_freeze_approved_for_paper is False
    assert result.replay_decision_freeze_strategy_performance_validated is False
    assert result.replay_decision_freeze_trading_allowed is False
    assert result.replay_decision_freeze_order_placed is False
    assert result.replay_decision_freeze_broker_api_called is False
    assert result.replay_decision_freeze_message_sent is False
    assert result.replay_decision_freeze_llm_api_called is False
    assert result.replay_decision_freeze_external_api_called is False
    assert result.replay_decision_freeze_cache_mutated is False
    assert result.replay_decision_freeze_data_raw_written is False
    assert result.replay_decision_freeze_data_processed_written is False
    assert result.replay_decision_freeze_data_cache_written is False
    assert result.replay_decision_freeze_current_candidates_run is False
    assert result.replay_decision_freeze_snapshot_built is False
    assert result.replay_decision_freeze_signal_semantics_changed is False
    assert result.replay_decision_freeze_report_only is True
    assert result.replay_decision_freeze_diagnostic_only is True
    assert result.replay_decision_freeze_no_live_trading is True
    assert result.replay_decision_freeze_no_broker_api is True
    assert result.replay_decision_freeze_no_order_placement is True
    assert result.replay_decision_freeze_no_message_sent is True
    assert str(summary["replay_decision_freeze_forward_labels_allowed"]) == "False"
    assert metadata["replay_decision_freeze_forward_labels_allowed"] is False
    assert metadata["replay_decision_freeze_strategy_performance_validated"] is False
    assert metadata["replay_decision_freeze_trading_allowed"] is False


def test_research_status_preserves_paper_priority_with_replay_decision_freeze(
    tmp_path: Path,
) -> None:
    root = _workflow_to_daily(tmp_path / "outputs" / "reports")
    root.mkdir(parents=True, exist_ok=True)
    _reconciliation(root, status="PASS")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        stale_warning_count=0,
        actionable_warning_count=0,
        blocking_error_count=0,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )
    run_replay_decision_freeze(
        replace(
            _replay_decision_freeze_happy_settings(tmp_path),
            output_dir=root / "manual_diagnostics" / "replay_decision_freeze_v0_1",
            allow_replay_decision_freeze=True,
        )
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    freeze_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "REPLAY_DECISION_FREEZE_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert freeze_row["warning_classification"] == ""
    assert result.latest_replay_decision_freeze_status == REPLAY_DECISION_FROZEN
    assert result.replay_decision_freeze_replay_decisions_created is True
    assert result.replay_decision_freeze_forward_labels_allowed is False
    assert result.replay_decision_freeze_forward_labels_exist is False
    assert result.replay_decision_freeze_forward_return_labels_created is False
    assert result.replay_decision_freeze_training_allowed is False
    assert result.replay_decision_freeze_stock_profile_allowed is False
    assert result.replay_decision_freeze_buy_review_allowed is False
    assert result.replay_decision_freeze_approved_for_paper is False
    assert result.replay_decision_freeze_strategy_performance_validated is False
    assert result.replay_decision_freeze_trading_allowed is False


def test_cli_research_status_prints_replay_decision_freeze_fields(tmp_path: Path, capsys) -> None:
    run_replay_decision_freeze(
        replace(_replay_decision_freeze_happy_settings(tmp_path), allow_replay_decision_freeze=True)
    )
    root = tmp_path / "outputs" / "reports"

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "replay_decision_freeze_workflow_implemented: True" in output.out
    assert f"latest_replay_decision_freeze_status: {REPLAY_DECISION_FROZEN}" in output.out
    assert "replay_decision_frozen: True" in output.out
    assert "replay_decision_freeze_replay_decisions_created: True" in output.out
    assert "replay_decision_freeze_forward_labels_allowed: False" in output.out
    assert "replay_decision_freeze_forward_return_labels_created: False" in output.out
    assert "replay_decision_freeze_training_allowed: False" in output.out
    assert "replay_decision_freeze_stock_profile_allowed: False" in output.out
    assert "replay_decision_freeze_buy_review_allowed: False" in output.out
    assert "replay_decision_freeze_approved_for_paper: False" in output.out
    assert "replay_decision_freeze_strategy_performance_validated: False" in output.out
    assert "replay_decision_freeze_trading_allowed: False" in output.out


def test_research_status_includes_forward_return_label_context_and_safety_fields(
    tmp_path: Path,
) -> None:
    labeled = run_forward_return_label(
        replace(_forward_return_label_happy_settings(tmp_path), allow_forward_return_label=True)
    )
    root = tmp_path / "outputs" / "reports"

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "FORWARD_RETURN_LABEL_STATUS"
    ].iloc[0]
    summary = result.summary_frame.iloc[0].to_dict()
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert row["status"] == FORWARD_RETURN_LABELS_CREATED
    assert row["workflow_area"] == "FORWARD_RETURN_LABEL"
    assert result.forward_return_label_workflow_implemented is True
    assert result.forward_return_label_views_implemented is True
    assert result.latest_forward_return_label_run_id == labeled.forward_return_label_run_id
    assert result.latest_forward_return_label_status == FORWARD_RETURN_LABELS_CREATED
    assert result.latest_forward_return_label_health_status == "PASS"
    assert result.latest_forward_return_label_workflow_stage == FORWARD_RETURN_LABELS_CREATED
    assert result.forward_return_label_artifact_path.endswith(labeled.forward_return_label_run_id)
    assert result.source_replay_decision_freeze_run_id == "freeze_abc123"
    assert result.source_replay_decision_freeze_artifact_path.endswith("forward_return_label_fixture_v0_1")
    assert result.replay_decision_freeze_status == REPLAY_DECISION_FROZEN
    assert result.replay_decision_freeze_health_status == "PASS"
    assert result.forward_return_label_replay_decision_frozen is True
    assert result.forward_return_label_replay_decisions_exist is True
    assert result.ready_for_forward_return_label is True
    assert result.forward_return_label_executed is True
    assert result.forward_return_label_artifacts_created is True
    assert result.forward_return_label_forward_labels_allowed is True
    assert result.forward_return_label_forward_labels_exist is True
    assert result.forward_return_label_forward_return_labels_created is True
    assert result.forward_return_label_label_row_count == 5
    assert "forward_return_5d" in result.forward_return_label_label_name_set
    assert result.forward_return_label_symbol_count == 1
    assert result.forward_return_label_replay_decision_count == 1
    assert result.forward_return_label_training_allowed is False
    assert result.forward_return_label_weights_trained is False
    assert result.forward_return_label_training_result_created is False
    assert result.forward_return_label_stock_profile_allowed is False
    assert result.forward_return_label_active_stock_profile_exists is False
    assert result.forward_return_label_stock_profile_created is False
    assert result.forward_return_label_buy_review_allowed is False
    assert result.forward_return_label_real_buy_review_eligible is False
    assert result.forward_return_label_approved_for_paper is False
    assert result.forward_return_label_strategy_performance_validated is False
    assert result.forward_return_label_trading_allowed is False
    assert result.forward_return_label_order_placed is False
    assert result.forward_return_label_broker_api_called is False
    assert result.forward_return_label_message_sent is False
    assert result.forward_return_label_llm_api_called is False
    assert result.forward_return_label_external_api_called is False
    assert result.forward_return_label_cache_mutated is False
    assert result.forward_return_label_data_raw_written is False
    assert result.forward_return_label_data_processed_written is False
    assert result.forward_return_label_data_cache_written is False
    assert result.forward_return_label_current_candidates_run is False
    assert result.forward_return_label_snapshot_built is False
    assert result.forward_return_label_signal_semantics_changed is False
    assert result.forward_return_label_report_only is True
    assert result.forward_return_label_diagnostic_only is True
    assert result.forward_return_label_no_live_trading is True
    assert result.forward_return_label_no_broker_api is True
    assert result.forward_return_label_no_order_placement is True
    assert result.forward_return_label_no_message_sent is True
    assert str(summary["forward_return_label_label_row_count"]) == "5"
    assert metadata["forward_return_label_label_row_count"] == 5
    assert metadata["forward_return_label_training_allowed"] is False
    assert metadata["forward_return_label_stock_profile_created"] is False
    assert metadata["forward_return_label_real_buy_review_eligible"] is False
    assert metadata["forward_return_label_strategy_performance_validated"] is False
    assert metadata["forward_return_label_trading_allowed"] is False


def test_research_status_preserves_paper_priority_with_forward_return_label(tmp_path: Path) -> None:
    run_forward_return_label(
        replace(_forward_return_label_happy_settings(tmp_path), allow_forward_return_label=True)
    )
    root = _workflow_to_daily(tmp_path / "outputs" / "reports")
    _reconciliation(root, status="PASS")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="PAPER_WORKFLOW_READY",
        expected_demo_warning_count=1,
        next_manual_action="Paper workflow remains later priority; forward labels are research context only.",
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.latest_forward_return_label_status == FORWARD_RETURN_LABELS_CREATED
    assert result.forward_return_label_forward_return_labels_created is True
    assert result.forward_return_label_training_allowed is False
    assert result.forward_return_label_stock_profile_allowed is False
    assert result.forward_return_label_buy_review_allowed is False
    assert result.forward_return_label_trading_allowed is False


def test_cli_research_status_prints_forward_return_label_fields(tmp_path: Path, capsys) -> None:
    run_forward_return_label(
        replace(_forward_return_label_happy_settings(tmp_path), allow_forward_return_label=True)
    )
    root = tmp_path / "outputs" / "reports"

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "forward_return_label_workflow_implemented: True" in output.out
    assert f"latest_forward_return_label_status: {FORWARD_RETURN_LABELS_CREATED}" in output.out
    assert "source_replay_decision_freeze_run_id: freeze_abc123" in output.out
    assert "ready_for_forward_return_label: True" in output.out
    assert "forward_return_label_forward_return_labels_created: True" in output.out
    assert "forward_return_label_label_row_count: 5" in output.out
    assert "forward_return_label_training_allowed: False" in output.out
    assert "forward_return_label_stock_profile_allowed: False" in output.out
    assert "forward_return_label_buy_review_allowed: False" in output.out
    assert "forward_return_label_approved_for_paper: False" in output.out
    assert "forward_return_label_strategy_performance_validated: False" in output.out
    assert "forward_return_label_trading_allowed: False" in output.out


def test_research_status_includes_training_evaluation_context_and_safety_fields(
    tmp_path: Path,
) -> None:
    training = run_training_evaluation(
        replace(_training_evaluation_happy_settings(tmp_path), allow_training_evaluation_dataset=True)
    )
    root = tmp_path / "outputs" / "reports"

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "TRAINING_EVALUATION_STATUS"
    ].iloc[0]
    summary = result.summary_frame.iloc[0].to_dict()
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert row["status"] == TRAINING_EVALUATION_DATASET_CREATED
    assert row["workflow_area"] == "TRAINING_EVALUATION"
    assert result.training_evaluation_workflow_implemented is True
    assert result.training_evaluation_views_implemented is True
    assert result.latest_training_evaluation_run_id == training.training_evaluation_run_id
    assert result.latest_training_evaluation_status == TRAINING_EVALUATION_DATASET_CREATED
    assert result.latest_training_evaluation_health_status == "PASS"
    assert result.latest_training_evaluation_workflow_stage == TRAINING_EVALUATION_DATASET_CREATED
    assert result.training_evaluation_artifact_path.endswith(training.training_evaluation_run_id)
    assert result.source_forward_return_label_run_id == "label_abc123"
    assert result.source_forward_return_label_status == FORWARD_RETURN_LABELS_CREATED
    assert result.source_forward_return_label_health_status == "PASS"
    assert result.source_replay_decision_freeze_run_id == "freeze_abc123"
    assert result.training_evaluation_forward_labels_exist is True
    assert result.training_evaluation_forward_return_labels_created is True
    assert result.training_evaluation_label_row_count == 1
    assert result.training_evaluation_replay_decision_count == 1
    assert result.training_evaluation_symbol_count == 1
    assert "forward_return_5d" in result.training_evaluation_label_name_set
    assert result.ready_for_training_evaluation_dataset is True
    assert result.training_evaluation_executed is True
    assert result.training_evaluation_dataset_artifacts_created is True
    assert result.training_evaluation_bounded_sample_rows_created is True
    assert result.training_evaluation_label_coverage_report_created is True
    assert result.training_evaluation_split_plan_created is True
    assert result.training_evaluation_feature_plan_created is True
    assert result.training_evaluation_label_plan_created is True
    assert result.training_evaluation_dataset_sample_row_count == 1
    assert result.training_evaluation_metrics_computed is False
    assert result.training_evaluation_training_allowed is False
    assert result.training_evaluation_weights_trained is False
    assert result.training_evaluation_training_result_created is False
    assert result.training_evaluation_model_version_created is False
    assert result.training_evaluation_thresholds_optimized is False
    assert result.training_evaluation_predictions_created is False
    assert result.training_evaluation_calibrated_probabilities_created is False
    assert result.training_evaluation_feature_importance_created is False
    assert result.training_evaluation_stock_profile_allowed is False
    assert result.training_evaluation_active_stock_profile_exists is False
    assert result.training_evaluation_stock_profile_created is False
    assert result.training_evaluation_buy_review_allowed is False
    assert result.training_evaluation_real_buy_review_eligible is False
    assert result.training_evaluation_approved_for_paper is False
    assert result.training_evaluation_strategy_performance_validated is False
    assert result.training_evaluation_trading_allowed is False
    assert result.training_evaluation_order_placed is False
    assert result.training_evaluation_broker_api_called is False
    assert result.training_evaluation_message_sent is False
    assert result.training_evaluation_llm_api_called is False
    assert result.training_evaluation_external_api_called is False
    assert result.training_evaluation_cache_mutated is False
    assert result.training_evaluation_data_raw_written is False
    assert result.training_evaluation_data_processed_written is False
    assert result.training_evaluation_data_cache_written is False
    assert result.training_evaluation_current_candidates_run is False
    assert result.training_evaluation_snapshot_built is False
    assert result.training_evaluation_signal_semantics_changed is False
    assert result.training_evaluation_report_only is True
    assert result.training_evaluation_diagnostic_only is True
    assert result.training_evaluation_no_live_trading is True
    assert result.training_evaluation_no_broker_api is True
    assert result.training_evaluation_no_order_placement is True
    assert result.training_evaluation_no_message_sent is True
    assert str(summary["training_evaluation_dataset_sample_row_count"]) == "1"
    assert metadata["training_evaluation_dataset_sample_row_count"] == 1
    assert metadata["training_evaluation_metrics_computed"] is False
    assert metadata["training_evaluation_training_result_created"] is False
    assert metadata["training_evaluation_model_version_created"] is False
    assert metadata["training_evaluation_stock_profile_created"] is False
    assert metadata["training_evaluation_strategy_performance_validated"] is False
    assert metadata["training_evaluation_trading_allowed"] is False


def test_research_status_preserves_paper_priority_with_training_evaluation(tmp_path: Path) -> None:
    run_training_evaluation(
        replace(_training_evaluation_happy_settings(tmp_path), allow_training_evaluation_dataset=True)
    )
    root = _workflow_to_daily(tmp_path / "outputs" / "reports")
    _reconciliation(root, status="PASS")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="PAPER_WORKFLOW_READY",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Paper workflow remains later priority; training/evaluation phase 1 "
            "is report-only dataset/planning context."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.latest_training_evaluation_status == TRAINING_EVALUATION_DATASET_CREATED
    assert result.training_evaluation_dataset_artifacts_created is True
    assert result.training_evaluation_metrics_computed is False
    assert result.training_evaluation_training_allowed is False
    assert result.training_evaluation_training_result_created is False
    assert result.training_evaluation_stock_profile_allowed is False
    assert result.training_evaluation_buy_review_allowed is False
    assert result.training_evaluation_trading_allowed is False


def test_cli_research_status_prints_training_evaluation_fields(tmp_path: Path, capsys) -> None:
    run_training_evaluation(
        replace(_training_evaluation_happy_settings(tmp_path), allow_training_evaluation_dataset=True)
    )
    root = tmp_path / "outputs" / "reports"

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "training_evaluation_workflow_implemented: True" in output.out
    assert f"latest_training_evaluation_status: {TRAINING_EVALUATION_DATASET_CREATED}" in output.out
    assert "source_forward_return_label_run_id: label_abc123" in output.out
    assert "ready_for_training_evaluation_dataset: True" in output.out
    assert "training_evaluation_dataset_artifacts_created: True" in output.out
    assert "training_evaluation_label_row_count: 1" in output.out
    assert "training_evaluation_metrics_computed: False" in output.out
    assert "training_evaluation_training_allowed: False" in output.out
    assert "training_evaluation_training_result_created: False" in output.out
    assert "training_evaluation_model_version_created: False" in output.out
    assert "training_evaluation_stock_profile_allowed: False" in output.out
    assert "training_evaluation_buy_review_allowed: False" in output.out
    assert "training_evaluation_approved_for_paper: False" in output.out
    assert "training_evaluation_strategy_performance_validated: False" in output.out
    assert "training_evaluation_trading_allowed: False" in output.out


def test_cli_research_status_works(tmp_path: Path, capsys) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "Research status:" in output.out
    assert "Report path:" in output.out


def test_cli_prints_next_manual_action(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "next_manual_action: Run data-pipeline." in output.out


def test_cli_prints_no_live_trading_statement(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "No live trading or broker API was invoked." in output.out


def test_dashboard_output_is_deterministic(tmp_path: Path) -> None:
    root = _workflow_complete(_reports_root(tmp_path))

    first = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    second = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert first.dashboard_id == second.dashboard_id
    assert first.dashboard_frame.to_dict("records") == second.dashboard_frame.to_dict("records")
    assert first.summary_frame.to_dict("records") == second.summary_frame.to_dict("records")


def test_dashboard_no_live_trading_or_broker_integration_is_invoked(tmp_path: Path) -> None:
    root = _workflow_complete(_reports_root(tmp_path))

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["local_research_dashboard_only"] is True
    assert not any("broker" in module_name.lower() for module_name in sys.modules)


def test_dashboard_no_real_network_api_calls_are_used(tmp_path: Path) -> None:
    root = _workflow_complete(_reports_root(tmp_path))

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.status == "PASS"
    assert result.audit_metadata["network_api_calls_used_in_tests"] is False


def test_dashboard_prefers_active_review_chain_over_stale_warn_artifacts(tmp_path: Path) -> None:
    root = _workflow_to_review_template(_reports_root(tmp_path))
    _review_template_health(root, health_id="health-stale", status="WARN", warnings=1)
    _paper_review(
        root,
        review_id="review-stale",
        template_health={
            "template_health_check_id": "health-stale",
            "template_health_status": "WARN",
            "template_health_report_path": str(
                root / "paper_trading" / "review_template_health" / "health-stale" / "review_template_health_report.md"
            ),
            "template_health_issue_count": 1,
            "template_health_error_count": 0,
            "template_health_warning_count": 1,
        },
        warnings=["stale review warning"],
    )
    _review_template_health(root, health_id="health-active", status="PASS")
    active_review = _paper_review(
        root,
        review_id="review-active",
        template_health={
            "template_health_check_id": "health-active",
            "template_health_status": "PASS",
            "template_health_report_path": str(
                root / "paper_trading" / "review_template_health" / "health-active" / "review_template_health_report.md"
            ),
            "template_health_issue_count": 0,
            "template_health_error_count": 0,
            "template_health_warning_count": 0,
        },
    )
    _daily_paper(root, reviewed_decisions_path=active_review / "reviewed_decisions.csv")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    by_component = {row["component"]: row for row in result.dashboard_frame.to_dict("records")}

    assert by_component["PAPER_REVIEW"]["latest_artifact_id"] == "review-active"
    assert by_component["REVIEW_TEMPLATE_HEALTH"]["latest_artifact_id"] == "health-active"
    assert result.paper_review_status == "READY"
    assert "stale_warning_count" in by_component["REVIEW_TEMPLATE_HEALTH"]["notes"]
    assert result.workflow_stage != "LOCAL_RESEARCH_NEEDS_ATTENTION"
    assert int(result.summary_frame.iloc[0]["stale_warning_count"]) > 0


def test_dashboard_prefers_active_reconciliation_over_unlinked_diagnostic_failure(tmp_path: Path) -> None:
    root = _workflow_to_review_template(_reports_root(tmp_path))
    _review_template_health(root, health_id="health-active", status="PASS")
    active_review = _paper_review(
        root,
        review_id="review-active",
        template_health={
            "template_health_check_id": "health-active",
            "template_health_status": "PASS",
            "template_health_report_path": str(
                root / "paper_trading" / "review_template_health" / "health-active" / "review_template_health_report.md"
            ),
            "template_health_issue_count": 0,
            "template_health_error_count": 0,
            "template_health_warning_count": 0,
        },
    )
    active_reconciliation = _reconciliation(root, reconciliation_id="recon-active", status="PASS")
    _reconciliation(
        root,
        reconciliation_id="recon-diagnostic",
        status="FAIL",
        errors=1,
        created_at=f"{DECISION_DATE}T16:20:00",
    )
    _daily_paper(
        root,
        reviewed_decisions_path=active_review / "reviewed_decisions.csv",
        reconciliation_report_path=active_reconciliation / "reconciliation_report.md",
        reconciliation_status="PASS",
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    by_component = {row["component"]: row for row in result.dashboard_frame.to_dict("records")}

    assert by_component["RECONCILIATION"]["latest_artifact_id"] == "recon-active"
    assert by_component["RECONCILIATION"]["status"] == "PASS"
    assert result.reconciliation_status == "PASS"
    assert result.status != "FAIL"
    assert result.workflow_stage != "LOCAL_RESEARCH_NEEDS_ATTENTION"


def test_dashboard_inherits_expected_demo_warning_actionability_from_paper_workflow_status(tmp_path: Path) -> None:
    root = _workflow_to_daily(_reports_root(tmp_path))
    _reconciliation(root, status="PASS")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WORKFLOW_NEEDS_ATTENTION",
        expected_demo_warning_count=1,
        stale_warning_count=0,
        actionable_warning_count=0,
        blocking_error_count=0,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    paper_row = result.dashboard_frame.loc[result.dashboard_frame["component"] == "PAPER_WORKFLOW_STATUS"].iloc[0]
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.status == "WARN"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action
    assert paper_row["warning_classification"] == "EXPECTED_DEMO_WARNING"
    assert summary["expected_demo_warning_count"] == 1
    assert summary["actionable_warning_count"] == 0


def test_dashboard_prefers_newer_paper_workflow_status_artifact_when_created_at_is_deterministic(
    tmp_path: Path,
) -> None:
    root = _workflow_to_daily(_reports_root(tmp_path))
    _reconciliation(root, status="PASS")
    stale = _paper_workflow_status(
        root,
        workflow_status_id="workflow-status-stale",
        status="FAIL",
        workflow_stage="WORKFLOW_NEEDS_ATTENTION",
        blocking_error_count=1,
        next_manual_action="Review warnings/errors in workflow status and health reports.",
        created_at="1970-01-01T00:00:00+00:00",
    )
    latest = _paper_workflow_status(
        root,
        workflow_status_id="workflow-status-latest",
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
        created_at="1970-01-01T00:00:00+00:00",
    )
    os.utime(stale / "metadata.json", (100, 100))
    os.utime(latest / "metadata.json", (200, 200))

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    paper_row = result.dashboard_frame.loc[result.dashboard_frame["component"] == "PAPER_WORKFLOW_STATUS"].iloc[0]

    assert paper_row["latest_artifact_id"] == "workflow-status-latest"
    assert result.paper_workflow_status == "WARN"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_classifies_prior_current_candidate_health_warning_as_stale(tmp_path: Path) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))
    _current_candidate_health_with_issues(
        root,
        status="WARN",
        issues=[
            {
                "artifact_type": "CURRENT_CANDIDATES",
                "run_id": "old-dry-run",
                "path_field": "candidates_path",
                "path_value": str(root / "current_candidates" / "old" / "candidates.csv"),
                "severity": "WARN",
                "issue_code": "CSV_EMPTY",
                "issue_message": "candidates.csv has no rows.",
                "suggested_action": "Confirm no candidates passed filters.",
            }
        ],
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    health_row = result.dashboard_frame.loc[result.dashboard_frame["component"] == "CURRENT_CANDIDATE_HEALTH"].iloc[0]
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.workflow_stage == "CURRENT_CANDIDATES_HEALTH_READY"
    assert result.next_manual_action == "Run current-to-paper."
    assert health_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert summary["stale_warning_count"] == 1
    assert summary["actionable_warning_count"] == 0


def test_dashboard_includes_market_update_handoff_status_when_no_paper_workflow_exists(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_update_handoff_status(root, status="WARN", warning_count=1)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    handoff_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "MARKET_UPDATE_HANDOFF_STATUS"
    ].iloc[0]
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.workflow_stage == "CURRENT_CANDIDATES_READY_FOR_PAPER_SMOKE_TEST"
    assert result.market_update_handoff_status == "WARN"
    assert result.latest_market_update_handoff_id == "handoff-a"
    assert result.market_update_handoff_stage == "CURRENT_CANDIDATES_READY_FOR_PAPER_SMOKE_TEST"
    assert result.market_update_handoff_current_candidate_run_id == "candidate-a"
    assert "current-to-paper" in result.next_manual_action
    assert handoff_row["warning_classification"] == "EXPECTED_DEMO_WARNING"
    assert summary["market_update_handoff_pipeline_id"] == "pipeline-a"
    assert summary["market_update_handoff_snapshot_quality_status"] == "PASS"
    assert summary["actionable_warning_count"] == 0


def test_dashboard_includes_historical_backfill_status_when_no_later_workflow_exists(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _historical_backfill_status(root, status="WARN", warning_count=1)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    backfill_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "HISTORICAL_BACKFILL_STATUS"
    ].iloc[0]
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.workflow_stage == "BACKFILL_WARNINGS_NEED_REVIEW"
    assert result.status == "WARN"
    assert result.latest_historical_backfill_id == "backfill-a"
    assert result.historical_backfill_status == "WARN"
    assert result.historical_backfill_stage == "BACKFILL_WARNINGS_NEED_REVIEW"
    assert result.historical_backfill_task_count == 6
    assert result.historical_backfill_pass_count == 3
    assert result.historical_backfill_warn_count == 3
    assert result.historical_backfill_fail_count == 0
    assert result.historical_backfill_skipped_count == 0
    assert result.historical_backfill_cache_write_occurred is False
    assert "Review WARN tasks" in result.next_manual_action
    assert backfill_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert summary["expected_reviewable_warning_count"] == 1
    assert summary["actionable_warning_count"] == 0


def test_dashboard_preserves_paper_priority_with_historical_backfill_context(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _historical_backfill_status(root, status="WARN", warning_count=1)
    _paper_workflow_status(root, status="PASS")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    backfill_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "HISTORICAL_BACKFILL_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "LOCAL_RESEARCH_WORKFLOW_COMPLETE"
    assert result.paper_workflow_status == "PASS"
    assert result.latest_historical_backfill_id == "backfill-a"
    assert result.historical_backfill_status == "WARN"
    assert backfill_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Review completed" in result.next_manual_action


def test_dashboard_marks_active_failed_historical_backfill_as_actionable(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _historical_backfill_status(
        root,
        status="FAIL",
        workflow_stage="BACKFILL_FAILED",
        health_status="FAIL",
        error_count=1,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    backfill_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "HISTORICAL_BACKFILL_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "BACKFILL_FAILED"
    assert result.latest_historical_backfill_id == "backfill-a"
    assert backfill_row["warning_classification"] == "BLOCKING_ERROR"
    assert "failed backfill" in result.next_manual_action


def test_dashboard_treats_partial_backfill_rejections_as_reviewable(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _historical_backfill_status(
        root,
        status="WARN",
        workflow_stage="BACKFILL_PARTIAL_WITH_REJECTIONS",
        health_status="PASS",
        warning_count=1,
        cache_write_occurred=True,
        accepted_task_count=8,
        rejected_task_count=2,
        preflight_rejected_count=2,
        comparison_failed_count=2,
        cache_write_partial=True,
        rejected_symbols="300750,688981",
        rejected_sources="BAOSTOCK_OPTIONAL",
        rejected_issue_categories="BLOCKED_PREFLIGHT_REJECT,COMPARISON_FAIL",
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    backfill_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "HISTORICAL_BACKFILL_STATUS"
    ].iloc[0]

    assert result.status == "WARN"
    assert result.workflow_stage == "BACKFILL_PARTIAL_WITH_REJECTIONS"
    assert result.historical_backfill_cache_write_partial is True
    assert result.historical_backfill_accepted_task_count == 8
    assert result.historical_backfill_rejected_task_count == 2
    assert result.historical_backfill_preflight_rejected_count == 2
    assert result.historical_backfill_comparison_failed_count == 2
    assert result.historical_backfill_rejected_symbols == "300750,688981"
    assert backfill_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert "Review rejected rows" in result.next_manual_action


def test_dashboard_preserves_paper_priority_with_partial_backfill_context(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _historical_backfill_status(
        root,
        status="WARN",
        workflow_stage="BACKFILL_PARTIAL_WITH_REJECTIONS",
        health_status="PASS",
        warning_count=1,
        cache_write_occurred=True,
        accepted_task_count=8,
        rejected_task_count=2,
        preflight_rejected_count=2,
        comparison_failed_count=2,
        cache_write_partial=True,
        rejected_symbols="300750,688981",
        rejected_sources="BAOSTOCK_OPTIONAL",
        rejected_issue_categories="BLOCKED_PREFLIGHT_REJECT,COMPARISON_FAIL",
    )
    _paper_workflow_status(root, status="PASS")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    backfill_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "HISTORICAL_BACKFILL_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "LOCAL_RESEARCH_WORKFLOW_COMPLETE"
    assert result.historical_backfill_stage == "BACKFILL_PARTIAL_WITH_REJECTIONS"
    assert result.historical_backfill_rejected_task_count == 2
    assert backfill_row["warning_classification"] == "STALE_ARTIFACT_WARNING"


def test_dashboard_summary_csv_exports_historical_backfill_fields(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _historical_backfill_status(root, backfill_id="backfill-export", status="WARN", warning_count=1)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    row = exported.iloc[0].to_dict()

    assert row["latest_historical_backfill_id"] == "backfill-export"
    assert row["historical_backfill_status"] == "WARN"
    assert row["historical_backfill_stage"] == "BACKFILL_WARNINGS_NEED_REVIEW"
    assert "Review WARN tasks" in row["historical_backfill_next_action"]
    assert row["historical_backfill_task_count"] == "6"
    assert row["historical_backfill_pass_count"] == "3"
    assert row["historical_backfill_warn_count"] == "3"
    assert row["historical_backfill_fail_count"] == "0"
    assert row["historical_backfill_skipped_count"] == "0"
    assert row["historical_backfill_cache_write_occurred"] == "False"
    assert row["historical_backfill_rejected_task_count"] == "0"
    assert row["historical_backfill_cache_write_partial"] == "False"
    assert row["historical_backfill_report_path"]


def test_dashboard_metadata_exports_historical_backfill_fields(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _historical_backfill_status(root, backfill_id="backfill-metadata", status="WARN", warning_count=1)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    component_statuses = metadata["component_statuses"]

    assert metadata["latest_historical_backfill_id"] == "backfill-metadata"
    assert metadata["historical_backfill_status"] == "WARN"
    assert metadata["historical_backfill_stage"] == "BACKFILL_WARNINGS_NEED_REVIEW"
    assert "Review WARN tasks" in metadata["historical_backfill_next_action"]
    assert metadata["historical_backfill_task_count"] == 6
    assert metadata["historical_backfill_warn_count"] == 3
    assert metadata["historical_backfill_cache_write_occurred"] is False
    assert metadata["historical_backfill_rejected_task_count"] == 0
    assert metadata["historical_backfill_cache_write_partial"] is False
    assert component_statuses["latest_historical_backfill_id"] == "backfill-metadata"
    assert component_statuses["expected_reviewable_warning_count"] == 1


def test_dashboard_includes_market_cache_export_status_when_no_later_workflow_exists(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_status(root, export_id="export-a", status="PASS")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    export_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "MARKET_CACHE_EXPORT_STATUS"
    ].iloc[0]
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.workflow_stage == "SNAPSHOT_READY_FROM_EXPORT"
    assert result.market_cache_export_status == "PASS"
    assert result.latest_market_cache_export_id == "export-a"
    assert result.market_cache_export_stage == "SNAPSHOT_READY_FROM_EXPORT"
    assert result.market_cache_export_pipeline_id == "pipeline-export-a"
    assert result.market_cache_export_data_pipeline_status == "PASS"
    assert result.market_cache_export_data_quality_status == "PASS"
    assert result.market_cache_export_snapshot_quality_status == "PASS"
    assert result.linked_snapshot_quality_status == "PASS"
    assert result.active_snapshot_chain == "MARKET_CACHE_EXPORT_STATUS"
    assert result.market_cache_export_snapshot_manifest_path.endswith("snapshot_manifest.json")
    assert "current-candidates" in result.next_manual_action
    assert export_row["warning_classification"] == ""
    assert summary["market_cache_export_report_path"]


def test_dashboard_preserves_current_candidate_priority_with_market_cache_export_context(tmp_path: Path) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))
    _market_cache_export_status(root, export_id="export-context", status="PASS")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "CURRENT_CANDIDATES_READY"
    assert result.current_candidate_status == "READY"
    assert result.latest_market_cache_export_id == "export-context"
    assert result.market_cache_export_status == "PASS"
    assert result.market_cache_export_snapshot_quality_status == "PASS"


def test_dashboard_preserves_paper_priority_with_market_cache_export_context(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_status(root, export_id="export-paper-context", status="FAIL", error_count=1)
    _paper_workflow_status(root, status="PASS")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    export_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "MARKET_CACHE_EXPORT_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "LOCAL_RESEARCH_WORKFLOW_COMPLETE"
    assert result.status == "WARN"
    assert result.paper_workflow_status == "PASS"
    assert result.latest_market_cache_export_id == "export-paper-context"
    assert export_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Review completed" in result.next_manual_action


def test_dashboard_uses_latest_market_cache_export_when_older_export_failed(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_status(
        root,
        export_id="export-old",
        status="FAIL",
        workflow_stage="CACHE_EXPORT_FAILED",
        health_status="FAIL",
        error_count=1,
        created_at=f"{DECISION_DATE}T14:00:00",
    )
    _market_cache_export_status(
        root,
        export_id="export-new",
        status="PASS",
        created_at=f"{DECISION_DATE}T15:00:00",
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    export_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "MARKET_CACHE_EXPORT_STATUS"
    ].iloc[0]
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.workflow_stage == "SNAPSHOT_READY_FROM_EXPORT"
    assert result.latest_market_cache_export_id == "export-new"
    assert result.market_cache_export_status == "PASS"
    assert export_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "stale_error_count=" in export_row["notes"]
    assert summary["stale_warning_count"] > 0
    assert summary["blocking_error_count"] == 0


def test_dashboard_active_export_snapshot_pass_not_overridden_by_stale_snapshot_warn(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_status(root, export_id="export-pass", status="PASS", snapshot_quality_status="PASS")
    _snapshot_quality(root, status="WARN")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    snapshot_row = result.dashboard_frame.loc[result.dashboard_frame["component"] == "SNAPSHOT_QUALITY"].iloc[0]
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.workflow_stage == "SNAPSHOT_READY_FROM_EXPORT"
    assert result.next_manual_action == "Run current-candidates with the reviewed cache export snapshot manifest."
    assert result.linked_snapshot_quality_status == "PASS"
    assert result.active_snapshot_chain == "MARKET_CACHE_EXPORT_STATUS"
    assert result.active_snapshot_warning_count == 0
    assert result.active_snapshot_error_count == 0
    assert result.unrelated_snapshot_warning_count > 0
    assert snapshot_row["warning_classification"] == "LINKED_SNAPSHOT_PASS;UNRELATED_SNAPSHOT_WARNING"
    assert summary["actionable_warning_count"] == 0
    assert summary["blocking_error_count"] == 0


def test_dashboard_active_export_snapshot_warn_remains_actionable(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_status(root, export_id="export-warn", status="PASS", snapshot_quality_status="WARN")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    snapshot_row = result.dashboard_frame.loc[result.dashboard_frame["component"] == "SNAPSHOT_QUALITY"].iloc[0]

    assert result.workflow_stage == "LOCAL_RESEARCH_NEEDS_ATTENTION"
    assert result.linked_snapshot_quality_status == "WARN"
    assert result.active_snapshot_chain == "MARKET_CACHE_EXPORT_STATUS"
    assert result.active_snapshot_warning_count == 1
    assert result.active_snapshot_error_count == 0
    assert snapshot_row["warning_classification"] == "ACTIVE_SNAPSHOT_WARNING"
    assert result.next_manual_action == "Review warnings/errors."


def test_dashboard_active_export_snapshot_fail_is_blocking(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_status(root, export_id="export-fail-snapshot", status="PASS", snapshot_quality_status="FAIL")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    snapshot_row = result.dashboard_frame.loc[result.dashboard_frame["component"] == "SNAPSHOT_QUALITY"].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "LOCAL_RESEARCH_NEEDS_ATTENTION"
    assert result.linked_snapshot_quality_status == "FAIL"
    assert result.active_snapshot_error_count == 1
    assert snapshot_row["warning_classification"] == "ACTIVE_SNAPSHOT_ERROR"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 1


def test_dashboard_standalone_snapshot_warn_remains_actionable_without_active_chain(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _snapshot_quality(root, status="WARN")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    snapshot_row = result.dashboard_frame.loc[result.dashboard_frame["component"] == "SNAPSHOT_QUALITY"].iloc[0]

    assert result.workflow_stage == "LOCAL_RESEARCH_NEEDS_ATTENTION"
    assert result.linked_snapshot_quality_status == "WARN"
    assert result.active_snapshot_chain == "SNAPSHOT_QUALITY"
    assert result.active_snapshot_warning_count == 1
    assert snapshot_row["warning_classification"] == "ACTIVE_SNAPSHOT_WARNING"


def test_dashboard_paper_priority_treats_unlinked_snapshot_warn_as_context(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _paper_workflow_status(root, status="PASS")
    _snapshot_quality(root, status="WARN")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    snapshot_row = result.dashboard_frame.loc[result.dashboard_frame["component"] == "SNAPSHOT_QUALITY"].iloc[0]

    assert result.workflow_stage == "LOCAL_RESEARCH_WORKFLOW_COMPLETE"
    assert result.paper_workflow_status == "PASS"
    assert result.active_snapshot_chain == "PAPER_WORKFLOW_STATUS"
    assert result.unrelated_snapshot_warning_count > 0
    assert snapshot_row["warning_classification"] == "MISSING_LINKED_SNAPSHOT;UNRELATED_SNAPSHOT_WARNING"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 0


def test_dashboard_marks_active_failed_market_cache_export_as_actionable(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_status(
        root,
        export_id="export-fail",
        status="FAIL",
        workflow_stage="CACHE_EXPORT_FAILED",
        health_status="FAIL",
        error_count=1,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    export_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "MARKET_CACHE_EXPORT_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "CACHE_EXPORT_FAILED"
    assert result.latest_market_cache_export_id == "export-fail"
    assert export_row["warning_classification"] == "BLOCKING_ERROR"
    assert "market-cache-export-health errors" in result.next_manual_action


def test_dashboard_summary_csv_exports_market_cache_export_fields(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_status(root, export_id="export-summary", status="PASS")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    row = exported.iloc[0].to_dict()

    assert row["latest_market_cache_export_id"] == "export-summary"
    assert row["market_cache_export_status"] == "PASS"
    assert row["market_cache_export_stage"] == "SNAPSHOT_READY_FROM_EXPORT"
    assert "current-candidates" in row["market_cache_export_next_action"]
    assert row["market_cache_export_pipeline_id"] == "pipeline-export-summary"
    assert row["market_cache_export_data_pipeline_status"] == "PASS"
    assert row["market_cache_export_data_quality_status"] == "PASS"
    assert row["market_cache_export_snapshot_quality_status"] == "PASS"
    assert row["market_cache_export_snapshot_manifest_path"].endswith("snapshot_manifest.json")
    assert row["market_cache_export_report_path"]
    assert row["linked_snapshot_quality_status"] == "PASS"
    assert row["active_snapshot_chain"] == "MARKET_CACHE_EXPORT_STATUS"
    assert row["active_snapshot_warning_count"] == "0"
    assert row["active_snapshot_error_count"] == "0"
    assert row["stale_snapshot_warning_count"] == "0"
    assert row["unrelated_snapshot_warning_count"] == "0"


def test_dashboard_includes_market_cache_export_plan_status_when_no_later_workflow_exists(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_policy_status(root, plan_id="plan-a", status="WARN", warning_count=1)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    plan_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "MARKET_CACHE_EXPORT_POLICY_STATUS"
    ].iloc[0]
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.workflow_stage == "SNAPSHOT_READY_FROM_POLICY_PLAN"
    assert result.status == "WARN"
    assert result.latest_market_cache_export_plan_id == "plan-a"
    assert result.market_cache_export_plan_status == "WARN"
    assert result.market_cache_export_plan_stage == "SNAPSHOT_READY_FROM_POLICY_PLAN"
    assert result.market_cache_export_plan_recommendation_count == 2
    assert result.market_cache_export_plan_recommended_count == 1
    assert result.market_cache_export_plan_warning_count == 1
    assert result.market_cache_export_plan_comparison_pass_count == 1
    assert result.market_cache_export_plan_comparison_unavailable_count == 1
    assert result.market_cache_export_plan_comparison_fail_count == 0
    assert result.market_cache_export_plan_comparison_supported_recommendation_count == 1
    assert result.market_cache_export_plan_comparison_unsupported_recommendation_count == 1
    assert result.market_cache_export_plan_downstream_export_id == "export-plan-a"
    assert result.market_cache_export_plan_downstream_snapshot_quality_status == "PASS"
    assert result.linked_snapshot_quality_status == "PASS"
    assert result.active_snapshot_chain == "MARKET_CACHE_EXPORT_POLICY_STATUS"
    assert "current-candidates" in result.next_manual_action
    assert plan_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert summary["actionable_warning_count"] == 0


def test_dashboard_marks_active_policy_plan_stock_comparison_fail_as_actionable(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_policy_status(
        root,
        plan_id="plan-comparison-fail",
        status="WARN",
        workflow_stage="POLICY_PLAN_COMPARISON_WARNINGS_NEED_REVIEW",
        warning_count=1,
        comparison_pass_count=0,
        comparison_fail_count=1,
        comparison_unavailable_count=0,
        comparison_supported_recommendation_count=1,
        comparison_unsupported_recommendation_count=0,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    plan_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "MARKET_CACHE_EXPORT_POLICY_STATUS"
    ].iloc[0]
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.workflow_stage == "LOCAL_RESEARCH_NEEDS_ATTENTION"
    assert result.latest_market_cache_export_plan_id == "plan-comparison-fail"
    assert result.market_cache_export_plan_comparison_fail_count == 1
    assert plan_row["warning_classification"] == "ACTIONABLE_WARNING"
    assert summary["actionable_warning_count"] > 0


def test_dashboard_preserves_market_cache_export_priority_with_policy_plan_context(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_policy_status(root, plan_id="plan-context", status="FAIL", error_count=1)
    _market_cache_export_status(root, export_id="export-context", status="PASS")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    plan_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "MARKET_CACHE_EXPORT_POLICY_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "SNAPSHOT_READY_FROM_EXPORT"
    assert result.market_cache_export_status == "PASS"
    assert result.latest_market_cache_export_plan_id == "plan-context"
    assert result.market_cache_export_plan_comparison_pass_count == 1
    assert result.market_cache_export_plan_comparison_unavailable_count == 1
    assert plan_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 0


def test_dashboard_preserves_paper_priority_with_market_cache_export_plan_context(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_policy_status(root, plan_id="plan-paper-context", status="WARN", warning_count=1)
    _paper_workflow_status(root, status="PASS")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "LOCAL_RESEARCH_WORKFLOW_COMPLETE"
    assert result.paper_workflow_status == "PASS"
    assert result.latest_market_cache_export_plan_id == "plan-paper-context"
    assert result.market_cache_export_plan_status == "WARN"
    assert result.market_cache_export_plan_comparison_pass_count == 1
    assert result.market_cache_export_plan_comparison_unavailable_count == 1
    assert result.summary_frame.iloc[0]["stale_warning_count"] > 0
    assert "Review completed" in result.next_manual_action


def test_dashboard_marks_active_failed_market_cache_export_plan_as_actionable(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_policy_status(
        root,
        plan_id="plan-fail",
        status="FAIL",
        workflow_stage="POLICY_PLAN_FAILED",
        health_status="FAIL",
        warning_count=0,
        error_count=1,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    plan_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "MARKET_CACHE_EXPORT_POLICY_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "POLICY_PLAN_FAILED"
    assert result.latest_market_cache_export_plan_id == "plan-fail"
    assert plan_row["warning_classification"] == "BLOCKING_ERROR"
    assert "market-cache-export-plan-health errors" in result.next_manual_action


def test_dashboard_uses_latest_market_cache_export_plan_when_older_plan_failed(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_policy_status(
        root,
        plan_id="plan-old",
        status="FAIL",
        workflow_stage="POLICY_PLAN_FAILED",
        health_status="FAIL",
        error_count=1,
        created_at=f"{DECISION_DATE}T14:00:00",
    )
    _market_cache_export_policy_status(
        root,
        plan_id="plan-new",
        status="WARN",
        workflow_stage="SNAPSHOT_READY_FROM_POLICY_PLAN",
        warning_count=1,
        created_at=f"{DECISION_DATE}T15:00:00",
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    plan_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "MARKET_CACHE_EXPORT_POLICY_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "SNAPSHOT_READY_FROM_POLICY_PLAN"
    assert result.latest_market_cache_export_plan_id == "plan-new"
    assert result.market_cache_export_plan_status == "WARN"
    assert plan_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert "stale_error_count=" in plan_row["notes"]
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 0


def test_dashboard_summary_csv_exports_market_cache_export_plan_fields(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_policy_status(root, plan_id="plan-summary", status="WARN", warning_count=1)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    row = exported.iloc[0].to_dict()

    assert row["latest_market_cache_export_plan_id"] == "plan-summary"
    assert row["market_cache_export_plan_status"] == "WARN"
    assert row["market_cache_export_plan_stage"] == "SNAPSHOT_READY_FROM_POLICY_PLAN"
    assert row["market_cache_export_plan_recommendation_count"] == "2"
    assert row["market_cache_export_plan_recommended_count"] == "1"
    assert row["market_cache_export_plan_warning_count"] == "1"
    assert row["market_cache_export_plan_comparison_pass_count"] == "1"
    assert row["market_cache_export_plan_comparison_warn_count"] == "0"
    assert row["market_cache_export_plan_comparison_fail_count"] == "0"
    assert row["market_cache_export_plan_comparison_unavailable_count"] == "1"
    assert row["market_cache_export_plan_comparison_required_but_missing_count"] == "0"
    assert row["market_cache_export_plan_comparison_supported_recommendation_count"] == "1"
    assert row["market_cache_export_plan_comparison_unsupported_recommendation_count"] == "1"
    assert row["market_cache_export_plan_generated_manifest_path"].endswith(
        "market_cache_export_recommended_plan-summary.csv"
    )
    assert row["market_cache_export_plan_downstream_export_id"] == "export-plan-summary"
    assert row["market_cache_export_plan_downstream_snapshot_quality_status"] == "PASS"


def test_dashboard_metadata_exports_market_cache_export_plan_fields(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_policy_status(root, plan_id="plan-metadata", status="WARN", warning_count=1)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    component_statuses = metadata["component_statuses"]

    assert metadata["latest_market_cache_export_plan_id"] == "plan-metadata"
    assert metadata["market_cache_export_plan_status"] == "WARN"
    assert metadata["market_cache_export_plan_stage"] == "SNAPSHOT_READY_FROM_POLICY_PLAN"
    assert metadata["market_cache_export_plan_recommendation_count"] == 2
    assert metadata["market_cache_export_plan_recommended_count"] == 1
    assert metadata["market_cache_export_plan_warning_count"] == 1
    assert metadata["market_cache_export_plan_comparison_pass_count"] == 1
    assert metadata["market_cache_export_plan_comparison_warn_count"] == 0
    assert metadata["market_cache_export_plan_comparison_fail_count"] == 0
    assert metadata["market_cache_export_plan_comparison_unavailable_count"] == 1
    assert metadata["market_cache_export_plan_comparison_required_but_missing_count"] == 0
    assert metadata["market_cache_export_plan_comparison_supported_recommendation_count"] == 1
    assert metadata["market_cache_export_plan_comparison_unsupported_recommendation_count"] == 1
    assert metadata["market_cache_export_plan_downstream_export_id"] == "export-plan-metadata"
    assert metadata["market_cache_export_plan_downstream_snapshot_quality_status"] == "PASS"
    assert component_statuses["latest_market_cache_export_plan_id"] == "plan-metadata"
    assert component_statuses["market_cache_export_plan_comparison_pass_count"] == 1
    assert component_statuses["market_cache_export_plan_comparison_unavailable_count"] == 1
    assert component_statuses["market_cache_export_plan_generated_manifest_path"].endswith(
        "market_cache_export_recommended_plan-metadata.csv"
    )


def test_dashboard_metadata_exports_market_cache_export_fields(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_status(root, export_id="export-metadata", status="PASS")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    component_statuses = metadata["component_statuses"]

    assert metadata["latest_market_cache_export_id"] == "export-metadata"
    assert metadata["market_cache_export_status"] == "PASS"
    assert metadata["market_cache_export_stage"] == "SNAPSHOT_READY_FROM_EXPORT"
    assert "current-candidates" in metadata["market_cache_export_next_action"]
    assert metadata["market_cache_export_pipeline_id"] == "pipeline-export-metadata"
    assert metadata["market_cache_export_data_pipeline_status"] == "PASS"
    assert metadata["market_cache_export_data_quality_status"] == "PASS"
    assert metadata["market_cache_export_snapshot_quality_status"] == "PASS"
    assert metadata["market_cache_export_snapshot_manifest_path"].endswith("snapshot_manifest.json")
    assert metadata["linked_snapshot_quality_status"] == "PASS"
    assert metadata["active_snapshot_chain"] == "MARKET_CACHE_EXPORT_STATUS"
    assert metadata["active_snapshot_warning_count"] == 0
    assert metadata["active_snapshot_error_count"] == 0
    assert metadata["stale_snapshot_warning_count"] == 0
    assert metadata["unrelated_snapshot_warning_count"] == 0
    assert component_statuses["latest_market_cache_export_id"] == "export-metadata"
    assert component_statuses["market_cache_export_pipeline_id"] == "pipeline-export-metadata"


def test_cli_research_status_prints_market_cache_export_fields(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_status(root, export_id="export-cli", status="PASS")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_market_cache_export_id: export-cli" in output.out
    assert "market_cache_export_status: PASS" in output.out
    assert "market_cache_export_stage: SNAPSHOT_READY_FROM_EXPORT" in output.out
    assert "market_cache_export_pipeline_id: pipeline-export-cli" in output.out
    assert "market_cache_export_snapshot_quality_status: PASS" in output.out
    assert "active_snapshot_chain: MARKET_CACHE_EXPORT_STATUS" in output.out
    assert "linked_snapshot_quality_status: PASS" in output.out


def test_cli_research_status_prints_market_cache_export_plan_fields(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)
    _market_cache_export_policy_status(root, plan_id="plan-cli", status="WARN", warning_count=1)

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_market_cache_export_plan_id: plan-cli" in output.out
    assert "market_cache_export_plan_status: WARN" in output.out
    assert "market_cache_export_plan_stage: SNAPSHOT_READY_FROM_POLICY_PLAN" in output.out
    assert "market_cache_export_plan_comparison_pass_count: 1" in output.out
    assert "market_cache_export_plan_comparison_unavailable_count: 1" in output.out
    assert "market_cache_export_plan_downstream_export_id: export-plan-cli" in output.out
    assert "market_cache_export_plan_downstream_snapshot_quality_status: PASS" in output.out


def test_cli_research_status_prints_historical_backfill_fields(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)
    _historical_backfill_status(root, backfill_id="backfill-cli", status="WARN", warning_count=1)

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_historical_backfill_id: backfill-cli" in output.out
    assert "historical_backfill_status: WARN" in output.out
    assert "historical_backfill_stage: BACKFILL_WARNINGS_NEED_REVIEW" in output.out
    assert "historical_backfill_rejected_task_count: 0" in output.out


def test_dashboard_does_not_regress_from_paper_workflow_to_market_update_handoff(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_update_handoff_status(
        root,
        status="FAIL",
        workflow_stage="HANDOFF_ARTIFACTS_NEED_REPAIR",
        health_status="FAIL",
        warning_count=0,
        error_count=1,
    )
    _paper_workflow_status(root, status="PASS")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    handoff_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "MARKET_UPDATE_HANDOFF_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "LOCAL_RESEARCH_WORKFLOW_COMPLETE"
    assert result.status == "WARN"
    assert result.paper_workflow_status == "PASS"
    assert handoff_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Review completed" in result.next_manual_action


def test_dashboard_marks_active_broken_market_update_handoff_as_blocking(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _market_update_handoff_status(
        root,
        status="FAIL",
        workflow_stage="HANDOFF_ARTIFACTS_NEED_REPAIR",
        health_status="FAIL",
        error_count=1,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    handoff_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "MARKET_UPDATE_HANDOFF_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "LOCAL_RESEARCH_NEEDS_ATTENTION"
    assert result.status == "FAIL"
    assert result.next_manual_action == "Review warnings/errors."
    assert handoff_row["warning_classification"] == "BLOCKING_ERROR"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 1


def test_cli_research_status_prints_market_update_handoff_fields(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)
    _market_update_handoff_status(root, status="WARN", warning_count=1)

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_market_update_handoff_id: handoff-a" in output.out
    assert "market_update_handoff_status: WARN" in output.out
    assert "market_update_handoff_stage: CURRENT_CANDIDATES_READY_FOR_PAPER_SMOKE_TEST" in output.out
    assert "market_update_handoff_current_candidate_run_id: candidate-a" in output.out


def test_dashboard_includes_advisory_profile_calibration_status_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _advisory_profile_calibration_status(root, calibration_id="calibration-reviewed")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    calibration_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "ADVISORY_PROFILE_CALIBRATION_STATUS"
    ].iloc[0]

    assert result.latest_advisory_profile_calibration_run_id == "calibration-reviewed"
    assert result.advisory_profile_calibration_status == "WARN"
    assert result.advisory_profile_calibration_stage == "ADVISORY_PROFILE_CALIBRATION_READY_FOR_REVIEW"
    assert result.advisory_profile_calibration_health_status == "PASS"
    assert result.advisory_profile_calibration_profile == "balanced"
    assert result.advisory_profile_calibration_review_buy_candidate_count == 1
    assert result.advisory_profile_calibration_watch_count == 2
    assert result.advisory_profile_calibration_no_action_count == 1
    assert result.advisory_profile_calibration_blocked_count == 2
    assert result.advisory_profile_calibration_issue_count == 2
    assert result.workflow_stage == "ADVISORY_PROFILE_CALIBRATION_READY_FOR_REVIEW"
    assert calibration_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert "REVIEW_BUY_CANDIDATE is not an order" in result.next_manual_action


def test_dashboard_advisory_profile_calibration_demo_is_visible_but_not_blocking(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _advisory_profile_calibration_status(
        root,
        calibration_id="calibration-demo",
        workflow_stage="DEMO_ADVISORY_PROFILE_CALIBRATION_VALIDATED",
        profile="balanced",
        row_count=9,
        review_buy_candidate_count=0,
        watch_count=0,
        no_action_count=0,
        blocked_count=0,
        demo_only_count=9,
        issue_count=0,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    calibration_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "ADVISORY_PROFILE_CALIBRATION_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "DEMO_ADVISORY_PROFILE_CALIBRATION_VALIDATED"
    assert result.advisory_profile_calibration_demo_only_count == 9
    assert result.advisory_profile_calibration_review_buy_candidate_count == 0
    assert calibration_row["warning_classification"] == "EXPECTED_DEMO_WARNING"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 0
    assert "DEMO_ONLY labels" in result.next_manual_action


def test_dashboard_failed_advisory_profile_calibration_health_is_actionable_when_active(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _advisory_profile_calibration_status(
        root,
        calibration_id="calibration-fail",
        status="FAIL",
        workflow_stage="ADVISORY_PROFILE_CALIBRATION_FAILED",
        health_status="FAIL",
        warning_count=0,
        error_count=1,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    calibration_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "ADVISORY_PROFILE_CALIBRATION_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "ADVISORY_PROFILE_CALIBRATION_FAILED"
    assert calibration_row["warning_classification"] == "BLOCKING_ERROR"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 1
    assert "Repair advisory profile calibration artifacts" in result.next_manual_action


def test_dashboard_preserves_later_paper_priority_over_advisory_profile_calibration(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _advisory_profile_calibration_status(root, calibration_id="calibration-reviewed")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    calibration_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "ADVISORY_PROFILE_CALIBRATION_STATUS"
    ].iloc[0]

    assert result.latest_advisory_profile_calibration_run_id == "calibration-reviewed"
    assert result.advisory_profile_calibration_stage == "ADVISORY_PROFILE_CALIBRATION_READY_FOR_REVIEW"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert calibration_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_exports_advisory_profile_calibration_fields_to_summary_and_metadata(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _advisory_profile_calibration_status(root, calibration_id="calibration-export")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_advisory_profile_calibration_run_id"] == "calibration-export"
    assert row["advisory_profile_calibration_status"] == "WARN"
    assert row["advisory_profile_calibration_stage"] == "ADVISORY_PROFILE_CALIBRATION_READY_FOR_REVIEW"
    assert row["advisory_profile_calibration_health_status"] == "PASS"
    assert row["advisory_profile_calibration_review_buy_candidate_count"] == "1"
    assert row["advisory_profile_calibration_watch_count"] == "2"
    assert row["advisory_profile_calibration_blocked_count"] == "2"
    assert row["advisory_profile_calibration_profile"] == "balanced"
    assert metadata["latest_advisory_profile_calibration_run_id"] == "calibration-export"
    assert metadata["advisory_profile_calibration_health_status"] == "PASS"
    assert metadata["advisory_profile_calibration_review_buy_candidate_count"] == 1
    assert metadata["component_statuses"]["latest_advisory_profile_calibration_run_id"] == "calibration-export"


def test_cli_research_status_prints_advisory_profile_calibration_fields(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)
    _advisory_profile_calibration_status(root, calibration_id="calibration-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_advisory_profile_calibration_run_id: calibration-cli" in output.out
    assert "advisory_profile_calibration_status: WARN" in output.out
    assert "advisory_profile_calibration_stage: ADVISORY_PROFILE_CALIBRATION_READY_FOR_REVIEW" in output.out
    assert "advisory_profile_calibration_health_status: PASS" in output.out
    assert "advisory_profile_calibration_review_buy_candidate_count: 1" in output.out


def test_dashboard_includes_calibration_to_signal_semantics_status_when_no_later_workflow_exists(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _calibration_to_signal_semantics_status(root, proposal_id="proposal-reviewed")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    proposal_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "CALIBRATION_TO_SIGNAL_SEMANTICS_STATUS"
    ].iloc[0]

    assert result.latest_calibration_to_signal_semantics_proposal_run_id == "proposal-reviewed"
    assert result.calibration_to_signal_semantics_status == "WARN"
    assert result.calibration_to_signal_semantics_stage == "CALIBRATION_TO_SEMANTICS_NEEDS_MORE_EVIDENCE"
    assert result.calibration_to_signal_semantics_health_status == "PASS"
    assert result.calibration_to_signal_semantics_defaults_changed is False
    assert "KEEP_CURRENT_DEFAULTS" in result.calibration_to_signal_semantics_proposal_categories
    assert "DO_NOT_EXPAND_BUY_REVIEW_YET" in result.calibration_to_signal_semantics_proposal_categories
    assert result.calibration_to_signal_semantics_calibration_run_count == 10
    assert result.calibration_to_signal_semantics_observed_review_buy_candidate_count == 7
    assert result.calibration_to_signal_semantics_observed_watch_count == 8
    assert result.calibration_to_signal_semantics_observed_blocked_count == 24
    assert result.workflow_stage == "CALIBRATION_TO_SEMANTICS_NEEDS_MORE_EVIDENCE"
    assert proposal_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert "Keep current defaults" in result.next_manual_action
    assert "do not expand BUY review yet" in result.next_manual_action


def test_dashboard_calibration_to_signal_semantics_defaults_changed_is_actionable(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _calibration_to_signal_semantics_status(
        root,
        proposal_id="proposal-defaults-changed",
        status="FAIL",
        workflow_stage="CALIBRATION_TO_SEMANTICS_FAILED",
        health_status="FAIL",
        defaults_changed=True,
        warning_count=0,
        error_count=1,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    proposal_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "CALIBRATION_TO_SIGNAL_SEMANTICS_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "CALIBRATION_TO_SEMANTICS_FAILED"
    assert result.calibration_to_signal_semantics_defaults_changed is True
    assert proposal_row["warning_classification"] == "BLOCKING_ERROR"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 1


def test_dashboard_failed_calibration_to_signal_semantics_health_is_actionable_when_active(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _calibration_to_signal_semantics_status(
        root,
        proposal_id="proposal-health-fail",
        status="FAIL",
        workflow_stage="CALIBRATION_TO_SEMANTICS_FAILED",
        health_status="FAIL",
        warning_count=0,
        error_count=1,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    proposal_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "CALIBRATION_TO_SIGNAL_SEMANTICS_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "CALIBRATION_TO_SEMANTICS_FAILED"
    assert result.calibration_to_signal_semantics_health_status == "FAIL"
    assert proposal_row["warning_classification"] == "BLOCKING_ERROR"
    assert "Repair calibration-to-semantics proposal artifacts" in result.next_manual_action


def test_dashboard_preserves_later_paper_priority_over_calibration_to_signal_semantics(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _calibration_to_signal_semantics_status(root, proposal_id="proposal-reviewed")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    proposal_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "CALIBRATION_TO_SIGNAL_SEMANTICS_STATUS"
    ].iloc[0]

    assert result.latest_calibration_to_signal_semantics_proposal_run_id == "proposal-reviewed"
    assert result.calibration_to_signal_semantics_stage == "CALIBRATION_TO_SEMANTICS_NEEDS_MORE_EVIDENCE"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert proposal_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_exports_calibration_to_signal_semantics_fields_to_summary_and_metadata(
    tmp_path: Path,
) -> None:
    root = _reports_root(tmp_path)
    _calibration_to_signal_semantics_status(root, proposal_id="proposal-export")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_calibration_to_signal_semantics_proposal_run_id"] == "proposal-export"
    assert row["calibration_to_signal_semantics_status"] == "WARN"
    assert row["calibration_to_signal_semantics_stage"] == "CALIBRATION_TO_SEMANTICS_NEEDS_MORE_EVIDENCE"
    assert row["calibration_to_signal_semantics_health_status"] == "PASS"
    assert row["calibration_to_signal_semantics_defaults_changed"] == "False"
    assert "REQUIRE_MORE_EVIDENCE" in row["calibration_to_signal_semantics_proposal_categories"]
    assert row["calibration_to_signal_semantics_calibration_run_count"] == "10"
    assert row["calibration_to_signal_semantics_observed_review_buy_candidate_count"] == "7"
    assert metadata["latest_calibration_to_signal_semantics_proposal_run_id"] == "proposal-export"
    assert metadata["calibration_to_signal_semantics_defaults_changed"] is False
    assert metadata["calibration_to_signal_semantics_observed_blocked_count"] == 24
    assert (
        metadata["component_statuses"]["latest_calibration_to_signal_semantics_proposal_run_id"]
        == "proposal-export"
    )


def test_cli_research_status_prints_calibration_to_signal_semantics_fields(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)
    _calibration_to_signal_semantics_status(root, proposal_id="proposal-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_calibration_to_signal_semantics_proposal_run_id: proposal-cli" in output.out
    assert "calibration_to_signal_semantics_status: WARN" in output.out
    assert (
        "calibration_to_signal_semantics_stage: CALIBRATION_TO_SEMANTICS_NEEDS_MORE_EVIDENCE"
        in output.out
    )
    assert "calibration_to_signal_semantics_defaults_changed: False" in output.out
    assert "calibration_to_signal_semantics_observed_review_buy_candidate_count: 7" in output.out


def test_dashboard_includes_signal_semantics_status_when_no_later_workflow_exists(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _signal_semantics_status(root, semantics_id="semantics-reviewed")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    semantics_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "SIGNAL_SEMANTICS_STATUS"
    ].iloc[0]

    assert result.latest_signal_semantics_run_id == "semantics-reviewed"
    assert result.signal_semantics_status == "WARN"
    assert result.signal_semantics_stage == "SIGNAL_SEMANTICS_READY_FOR_REVIEW"
    assert result.signal_semantics_health_status == "PASS"
    assert result.signal_semantics_review_buy_candidate_count == 1
    assert result.signal_semantics_watch_count == 1
    assert result.signal_semantics_blocked_count == 2
    assert result.signal_semantics_issue_count == 2
    assert result.signal_semantics_profile == "reviewed_local_v0"
    assert result.workflow_stage == "SIGNAL_SEMANTICS_READY_FOR_REVIEW"
    assert semantics_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert "REVIEW_BUY_CANDIDATE is not an order" in result.next_manual_action
    assert "auto-order remains disabled" in result.next_manual_action


def test_dashboard_signal_semantics_demo_is_visible_but_not_blocking(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _signal_semantics_status(
        root,
        semantics_id="semantics-demo",
        workflow_stage="DEMO_SIGNAL_SEMANTICS_VALIDATED",
        profile="demo",
        row_count=9,
        demo_only_count=9,
        review_buy_candidate_count=0,
        review_sell_candidate_count=0,
        watch_count=0,
        blocked_count=0,
        issue_count=0,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    semantics_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "SIGNAL_SEMANTICS_STATUS"
    ].iloc[0]

    assert result.workflow_stage == "DEMO_SIGNAL_SEMANTICS_VALIDATED"
    assert result.signal_semantics_demo_only_count == 9
    assert result.signal_semantics_review_buy_candidate_count == 0
    assert result.signal_semantics_review_sell_candidate_count == 0
    assert semantics_row["warning_classification"] == "EXPECTED_DEMO_WARNING"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 0
    assert "DEMO_ONLY labels" in result.next_manual_action


def test_dashboard_failed_signal_semantics_health_is_actionable_when_active(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _signal_semantics_status(
        root,
        semantics_id="semantics-fail",
        status="FAIL",
        workflow_stage="SIGNAL_SEMANTICS_FAILED",
        health_status="FAIL",
        warning_count=0,
        error_count=1,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    semantics_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "SIGNAL_SEMANTICS_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "SIGNAL_SEMANTICS_FAILED"
    assert semantics_row["warning_classification"] == "BLOCKING_ERROR"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 1
    assert "Repair signal semantics artifacts" in result.next_manual_action


def test_dashboard_demo_signal_semantics_buy_sell_leakage_is_actionable(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _signal_semantics_status(
        root,
        semantics_id="semantics-unsafe-demo",
        status="FAIL",
        workflow_stage="SIGNAL_SEMANTICS_FAILED",
        health_status="FAIL",
        profile="demo",
        row_count=2,
        demo_only_count=1,
        review_buy_candidate_count=1,
        review_sell_candidate_count=0,
        warning_count=0,
        error_count=1,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.status == "FAIL"
    assert result.workflow_stage == "SIGNAL_SEMANTICS_FAILED"
    assert result.signal_semantics_profile == "demo"
    assert result.signal_semantics_review_buy_candidate_count == 1
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 1


def test_dashboard_preserves_later_paper_priority_over_signal_semantics_review_labels(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _signal_semantics_status(root, semantics_id="semantics-reviewed")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    semantics_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "SIGNAL_SEMANTICS_STATUS"
    ].iloc[0]

    assert result.latest_signal_semantics_run_id == "semantics-reviewed"
    assert result.signal_semantics_stage == "SIGNAL_SEMANTICS_READY_FOR_REVIEW"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert semantics_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_exports_signal_semantics_fields_to_summary_and_metadata(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _signal_semantics_status(root, semantics_id="semantics-export")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_signal_semantics_run_id"] == "semantics-export"
    assert row["signal_semantics_status"] == "WARN"
    assert row["signal_semantics_stage"] == "SIGNAL_SEMANTICS_READY_FOR_REVIEW"
    assert row["signal_semantics_health_status"] == "PASS"
    assert row["signal_semantics_review_buy_candidate_count"] == "1"
    assert row["signal_semantics_watch_count"] == "1"
    assert row["signal_semantics_blocked_count"] == "2"
    assert row["signal_semantics_profile"] == "reviewed_local_v0"
    assert metadata["latest_signal_semantics_run_id"] == "semantics-export"
    assert metadata["signal_semantics_health_status"] == "PASS"
    assert metadata["signal_semantics_review_buy_candidate_count"] == 1
    assert metadata["component_statuses"]["latest_signal_semantics_run_id"] == "semantics-export"


def test_cli_research_status_prints_signal_semantics_fields(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)
    _signal_semantics_status(root, semantics_id="semantics-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_signal_semantics_run_id: semantics-cli" in output.out
    assert "signal_semantics_status: WARN" in output.out
    assert "signal_semantics_stage: SIGNAL_SEMANTICS_READY_FOR_REVIEW" in output.out
    assert "signal_semantics_health_status: PASS" in output.out
    assert "signal_semantics_review_buy_candidate_count: 1" in output.out


def test_dashboard_includes_signal_advisory_status_when_no_later_workflow_exists(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _signal_advisory_status(root)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.latest_signal_run_id == "signal-a"
    assert result.signal_advisory_status == "WARN"
    assert result.signal_advisory_stage == "DEMO_SIGNAL_ADVISORY_VALIDATED"
    assert result.signal_health_status == "PASS"
    assert result.signal_count == 9
    assert result.demo_signal_count == 9
    assert result.workflow_stage == "DEMO_SIGNAL_ADVISORY_VALIDATED"
    assert "DEMO_ONLY" in result.advisory_action_counts
    assert "Review local alert preview" in result.next_manual_action


def test_dashboard_signal_demo_is_visible_but_not_blocking(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _signal_advisory_status(root, status="WARN", workflow_stage="DEMO_SIGNAL_ADVISORY_VALIDATED", warning_count=1)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    signal_row = result.dashboard_frame.loc[result.dashboard_frame["component"] == "SIGNAL_ADVISORY_STATUS"].iloc[0]

    assert signal_row["warning_classification"] == "EXPECTED_DEMO_WARNING"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 0
    assert "REVIEW_BUY_CANDIDATE\": 0" in result.advisory_action_counts
    assert "REVIEW_SELL_CANDIDATE\": 0" in result.advisory_action_counts


def test_dashboard_preserves_later_paper_priority_over_signal_advisory_demo(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _signal_advisory_status(root, status="WARN", warning_count=1)
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.latest_signal_run_id == "signal-a"
    assert result.signal_advisory_stage == "DEMO_SIGNAL_ADVISORY_VALIDATED"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_failed_signal_health_is_actionable_when_active(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _signal_advisory_status(
        root,
        status="FAIL",
        workflow_stage="SIGNAL_ADVISORY_FAILED",
        health_status="FAIL",
        error_count=1,
        warning_count=0,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    signal_row = result.dashboard_frame.loc[result.dashboard_frame["component"] == "SIGNAL_ADVISORY_STATUS"].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "SIGNAL_ADVISORY_FAILED"
    assert signal_row["warning_classification"] == "BLOCKING_ERROR"
    assert "Repair signal advisory artifacts" in result.next_manual_action


def test_dashboard_exports_signal_advisory_fields_to_summary_and_metadata(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _signal_advisory_status(root, signal_id="signal-export")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_signal_run_id"] == "signal-export"
    assert row["signal_advisory_status"] == "WARN"
    assert row["signal_advisory_stage"] == "DEMO_SIGNAL_ADVISORY_VALIDATED"
    assert row["signal_health_status"] == "PASS"
    assert row["signal_count"] == "9"
    assert row["demo_signal_count"] == "9"
    assert row["source_candidate_run_id"] == "candidate-a"
    assert row["selection_profile"] == "demo"
    assert row["demo_mode"] == "True"
    assert row["not_strategy_recommendation"] == "True"
    assert metadata["latest_signal_run_id"] == "signal-export"
    assert metadata["signal_health_status"] == "PASS"
    assert metadata["demo_mode"] is True
    assert metadata["component_statuses"]["latest_signal_run_id"] == "signal-export"


def test_cli_research_status_prints_signal_advisory_fields(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)
    _signal_advisory_status(root, signal_id="signal-cli")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_signal_run_id: signal-cli" in output.out
    assert "signal_advisory_status: WARN" in output.out
    assert "signal_advisory_stage: DEMO_SIGNAL_ADVISORY_VALIDATED" in output.out
    assert "signal_health_status: PASS" in output.out
    assert "demo_mode: True" in output.out


def test_dashboard_includes_single_symbol_advisory_status_when_no_later_workflow_exists(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _single_symbol_advisory_status(root, advisory_id="single-000001", symbol="000001")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.latest_single_symbol_advisory_run_id == "single-000001"
    assert result.latest_single_symbol_advisory_symbol == "000001"
    assert result.single_symbol_advisory_status == "WARN"
    assert result.single_symbol_advisory_stage == "DEMO_SINGLE_SYMBOL_ADVISORY_VALIDATED"
    assert result.single_symbol_advisory_action == "DEMO_ONLY"
    assert result.single_symbol_advisory_health_status == "PASS"
    assert result.single_symbol_advisory_demo_mode is True
    assert result.single_symbol_advisory_not_strategy_recommendation is True
    assert result.workflow_stage == "DEMO_SINGLE_SYMBOL_ADVISORY_VALIDATED"
    assert "Review local single-symbol advisory preview" in result.next_manual_action


def test_dashboard_single_symbol_not_found_is_visible_but_not_blocking(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _single_symbol_advisory_status(
        root,
        advisory_id="single-missing",
        symbol="999999",
        status="WARN",
        workflow_stage="SINGLE_SYMBOL_ADVISORY_NOT_FOUND",
        latest_status="NOT_FOUND",
        advisory_action="NO_ACTION",
        final_score="",
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    advisory_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "SINGLE_SYMBOL_ADVISORY_STATUS"
    ].iloc[0]

    assert result.latest_single_symbol_advisory_symbol == "999999"
    assert result.single_symbol_advisory_action == "NO_ACTION"
    assert result.workflow_stage == "SINGLE_SYMBOL_ADVISORY_NOT_FOUND"
    assert result.status == "WARN"
    assert advisory_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 0
    assert "no recommendation was invented" in result.next_manual_action


def test_dashboard_failed_single_symbol_health_is_actionable_when_active(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _single_symbol_advisory_status(
        root,
        advisory_id="single-fail",
        status="FAIL",
        workflow_stage="SINGLE_SYMBOL_ADVISORY_FAILED",
        health_status="FAIL",
        error_count=1,
        warning_count=0,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    advisory_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "SINGLE_SYMBOL_ADVISORY_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "SINGLE_SYMBOL_ADVISORY_FAILED"
    assert advisory_row["warning_classification"] == "BLOCKING_ERROR"
    assert "Repair single-symbol advisory artifacts" in result.next_manual_action


def test_dashboard_preserves_later_paper_priority_over_single_symbol_not_found(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _single_symbol_advisory_status(
        root,
        advisory_id="single-missing",
        symbol="999999",
        workflow_stage="SINGLE_SYMBOL_ADVISORY_NOT_FOUND",
        latest_status="NOT_FOUND",
        advisory_action="NO_ACTION",
    )
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    advisory_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "SINGLE_SYMBOL_ADVISORY_STATUS"
    ].iloc[0]

    assert result.latest_single_symbol_advisory_symbol == "999999"
    assert result.single_symbol_advisory_stage == "SINGLE_SYMBOL_ADVISORY_NOT_FOUND"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert advisory_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_exports_single_symbol_advisory_fields_to_summary_and_metadata(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _single_symbol_advisory_status(root, advisory_id="single-export", symbol="000001")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_single_symbol_advisory_run_id"] == "single-export"
    assert row["latest_single_symbol_advisory_symbol"] == "000001"
    assert row["single_symbol_advisory_status"] == "WARN"
    assert row["single_symbol_advisory_stage"] == "DEMO_SINGLE_SYMBOL_ADVISORY_VALIDATED"
    assert row["single_symbol_advisory_action"] == "DEMO_ONLY"
    assert row["single_symbol_advisory_health_status"] == "PASS"
    assert row["single_symbol_advisory_demo_mode"] == "True"
    assert row["single_symbol_advisory_not_strategy_recommendation"] == "True"
    assert metadata["latest_single_symbol_advisory_run_id"] == "single-export"
    assert metadata["latest_single_symbol_advisory_symbol"] == "000001"
    assert metadata["single_symbol_advisory_health_status"] == "PASS"
    assert metadata["single_symbol_advisory_demo_mode"] is True
    assert metadata["component_statuses"]["latest_single_symbol_advisory_symbol"] == "000001"


def test_cli_research_status_prints_single_symbol_advisory_fields(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)
    _single_symbol_advisory_status(root, advisory_id="single-cli", symbol="000001")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_single_symbol_advisory_run_id: single-cli" in output.out
    assert "latest_single_symbol_advisory_symbol: 000001" in output.out
    assert "single_symbol_advisory_status: WARN" in output.out
    assert "single_symbol_advisory_stage: DEMO_SINGLE_SYMBOL_ADVISORY_VALIDATED" in output.out
    assert "single_symbol_advisory_health_status: PASS" in output.out


def test_dashboard_includes_single_symbol_answer_status_when_no_later_workflow_exists(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _single_symbol_advisory_answer_status(root, answer_id="answer-000001", symbol="000001")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.latest_single_symbol_advisory_answer_run_id == "answer-000001"
    assert result.latest_single_symbol_advisory_answer_symbol == "000001"
    assert result.single_symbol_advisory_answer_status == "WARN"
    assert result.single_symbol_advisory_answer_stage == "DEMO_SINGLE_SYMBOL_ADVISORY_ANSWER_VALIDATED"
    assert result.single_symbol_advisory_answer_action == "DEMO_ONLY"
    assert result.single_symbol_advisory_answer_health_status == "PASS"
    assert result.single_symbol_advisory_answer_question == "should I buy?"
    assert result.single_symbol_advisory_answer_style == "concise"
    assert result.single_symbol_advisory_answer_demo_mode is True
    assert result.single_symbol_advisory_answer_not_strategy_recommendation is True
    assert result.workflow_stage == "DEMO_SINGLE_SYMBOL_ADVISORY_ANSWER_VALIDATED"
    assert "Review local question-style answer" in result.next_manual_action


def test_dashboard_single_symbol_answer_not_found_is_visible_but_not_blocking(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _single_symbol_advisory_answer_status(
        root,
        answer_id="answer-missing",
        symbol="999999",
        status="WARN",
        workflow_stage="SINGLE_SYMBOL_ADVISORY_ANSWER_NOT_FOUND",
        latest_status="NOT_FOUND",
        advisory_action="NO_ACTION",
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    answer_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "SINGLE_SYMBOL_ADVISORY_ANSWER_STATUS"
    ].iloc[0]

    assert result.latest_single_symbol_advisory_answer_symbol == "999999"
    assert result.single_symbol_advisory_answer_action == "NO_ACTION"
    assert result.workflow_stage == "SINGLE_SYMBOL_ADVISORY_ANSWER_NOT_FOUND"
    assert result.status == "WARN"
    assert answer_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 0
    assert "no recommendation was invented" in result.next_manual_action


def test_dashboard_failed_single_symbol_answer_health_is_actionable_when_active(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _single_symbol_advisory_answer_status(
        root,
        answer_id="answer-fail",
        status="FAIL",
        workflow_stage="SINGLE_SYMBOL_ADVISORY_ANSWER_FAILED",
        health_status="FAIL",
        error_count=1,
        warning_count=0,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    answer_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "SINGLE_SYMBOL_ADVISORY_ANSWER_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "SINGLE_SYMBOL_ADVISORY_ANSWER_FAILED"
    assert answer_row["warning_classification"] == "BLOCKING_ERROR"
    assert "Repair question-style answer artifacts" in result.next_manual_action


def test_dashboard_computed_answer_llm_api_called_is_actionable(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _single_symbol_answer_artifact(root, answer_id="answer-llm", symbol="000001", metadata_updates={"llm_api_called": True})

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    answer_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "SINGLE_SYMBOL_ADVISORY_ANSWER_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "SINGLE_SYMBOL_ADVISORY_ANSWER_FAILED"
    assert result.latest_single_symbol_advisory_answer_symbol == "000001"
    assert answer_row["warning_classification"] == "BLOCKING_ERROR"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 1


def test_dashboard_preserves_later_paper_priority_over_single_symbol_answer_not_found(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _single_symbol_advisory_answer_status(
        root,
        answer_id="answer-missing",
        symbol="999999",
        workflow_stage="SINGLE_SYMBOL_ADVISORY_ANSWER_NOT_FOUND",
        latest_status="NOT_FOUND",
        advisory_action="NO_ACTION",
    )
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    answer_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "SINGLE_SYMBOL_ADVISORY_ANSWER_STATUS"
    ].iloc[0]

    assert result.latest_single_symbol_advisory_answer_symbol == "999999"
    assert result.single_symbol_advisory_answer_stage == "SINGLE_SYMBOL_ADVISORY_ANSWER_NOT_FOUND"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert answer_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_exports_single_symbol_answer_fields_to_summary_and_metadata(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _single_symbol_advisory_answer_status(root, answer_id="answer-export", symbol="000001")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_single_symbol_advisory_answer_run_id"] == "answer-export"
    assert row["latest_single_symbol_advisory_answer_symbol"] == "000001"
    assert row["single_symbol_advisory_answer_status"] == "WARN"
    assert row["single_symbol_advisory_answer_stage"] == "DEMO_SINGLE_SYMBOL_ADVISORY_ANSWER_VALIDATED"
    assert row["single_symbol_advisory_answer_action"] == "DEMO_ONLY"
    assert row["single_symbol_advisory_answer_health_status"] == "PASS"
    assert row["single_symbol_advisory_answer_question"] == "should I buy?"
    assert row["single_symbol_advisory_answer_style"] == "concise"
    assert row["single_symbol_advisory_answer_demo_mode"] == "True"
    assert row["single_symbol_advisory_answer_not_strategy_recommendation"] == "True"
    assert metadata["latest_single_symbol_advisory_answer_run_id"] == "answer-export"
    assert metadata["latest_single_symbol_advisory_answer_symbol"] == "000001"
    assert metadata["single_symbol_advisory_answer_health_status"] == "PASS"
    assert metadata["single_symbol_advisory_answer_demo_mode"] is True
    assert metadata["component_statuses"]["latest_single_symbol_advisory_answer_symbol"] == "000001"


def test_cli_research_status_prints_single_symbol_answer_fields(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)
    _single_symbol_advisory_answer_status(root, answer_id="answer-cli", symbol="000001")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_single_symbol_advisory_answer_run_id: answer-cli" in output.out
    assert "latest_single_symbol_advisory_answer_symbol: 000001" in output.out
    assert "single_symbol_advisory_answer_status: WARN" in output.out
    assert "single_symbol_advisory_answer_stage: DEMO_SINGLE_SYMBOL_ADVISORY_ANSWER_VALIDATED" in output.out
    assert "single_symbol_advisory_answer_health_status: PASS" in output.out


def test_dashboard_includes_advisory_conversation_status_when_no_later_workflow_exists(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _advisory_conversation_status(root, conversation_id="conv-000001", parsed_symbol="000001")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.latest_advisory_conversation_run_id == "conv-000001"
    assert result.advisory_conversation_original_question == "000001 now can buy?"
    assert result.advisory_conversation_parsed_symbol == "000001"
    assert result.advisory_conversation_parsed_intent == "BUY_REVIEW"
    assert result.advisory_conversation_status == "WARN"
    assert result.advisory_conversation_stage == "DEMO_ADVISORY_CONVERSATION_VALIDATED"
    assert result.advisory_conversation_action == "DEMO_ONLY"
    assert result.advisory_conversation_health_status == "PASS"
    assert result.advisory_conversation_parser_type == "deterministic_rule_based"
    assert result.advisory_conversation_llm_api_called is False
    assert result.advisory_conversation_no_message_sent is True
    assert result.workflow_stage == "DEMO_ADVISORY_CONVERSATION_VALIDATED"
    assert "Review local conversational advisory answer" in result.next_manual_action


def test_dashboard_advisory_conversation_parse_failed_visible_but_not_blocking(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _advisory_conversation_status(
        root,
        conversation_id="conv-parse-failed",
        question="can I buy this?",
        parsed_symbol="",
        status="WARN",
        workflow_stage="ADVISORY_CONVERSATION_PARSE_FAILED",
        latest_status="PARSE_FAILED",
        advisory_action="NO_ACTION",
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    conversation_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "ADVISORY_CONVERSATION_STATUS"
    ].iloc[0]

    assert result.advisory_conversation_parsed_symbol == ""
    assert result.advisory_conversation_action == "NO_ACTION"
    assert result.workflow_stage == "ADVISORY_CONVERSATION_PARSE_FAILED"
    assert result.status == "WARN"
    assert conversation_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 0
    assert "no symbol or recommendation was invented" in result.next_manual_action


def test_dashboard_advisory_conversation_not_found_visible_but_not_blocking(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _advisory_conversation_status(
        root,
        conversation_id="conv-not-found",
        parsed_symbol="999999",
        status="WARN",
        workflow_stage="ADVISORY_CONVERSATION_NOT_FOUND",
        latest_status="NOT_FOUND",
        advisory_action="NO_ACTION",
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    conversation_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "ADVISORY_CONVERSATION_STATUS"
    ].iloc[0]

    assert result.advisory_conversation_parsed_symbol == "999999"
    assert result.advisory_conversation_action == "NO_ACTION"
    assert result.workflow_stage == "ADVISORY_CONVERSATION_NOT_FOUND"
    assert conversation_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert "no recommendation was invented" in result.next_manual_action


def test_dashboard_failed_advisory_conversation_health_is_actionable_when_active(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _advisory_conversation_status(
        root,
        conversation_id="conv-fail",
        status="FAIL",
        workflow_stage="ADVISORY_CONVERSATION_FAILED",
        health_status="FAIL",
        llm_api_called=True,
        error_count=1,
        warning_count=0,
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    conversation_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "ADVISORY_CONVERSATION_STATUS"
    ].iloc[0]

    assert result.status == "FAIL"
    assert result.workflow_stage == "ADVISORY_CONVERSATION_FAILED"
    assert result.advisory_conversation_llm_api_called is True
    assert conversation_row["warning_classification"] == "BLOCKING_ERROR"
    assert result.summary_frame.iloc[0]["blocking_error_count"] == 1


def test_dashboard_preserves_later_paper_priority_over_advisory_conversation_parse_failed(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _advisory_conversation_status(
        root,
        conversation_id="conv-parse-failed",
        question="can I buy this?",
        parsed_symbol="",
        workflow_stage="ADVISORY_CONVERSATION_PARSE_FAILED",
        latest_status="PARSE_FAILED",
        advisory_action="NO_ACTION",
    )
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    conversation_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "ADVISORY_CONVERSATION_STATUS"
    ].iloc[0]

    assert result.advisory_conversation_stage == "ADVISORY_CONVERSATION_PARSE_FAILED"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert conversation_row["warning_classification"] == "STALE_ARTIFACT_WARNING"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action


def test_dashboard_exports_advisory_conversation_fields_to_summary_and_metadata(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _advisory_conversation_status(root, conversation_id="conv-export", parsed_symbol="000001")

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    row = exported.iloc[0].to_dict()

    assert row["latest_advisory_conversation_run_id"] == "conv-export"
    assert row["advisory_conversation_original_question"] == "000001 now can buy?"
    assert row["advisory_conversation_parsed_symbol"] == "000001"
    assert row["advisory_conversation_parsed_intent"] == "BUY_REVIEW"
    assert row["advisory_conversation_status"] == "WARN"
    assert row["advisory_conversation_stage"] == "DEMO_ADVISORY_CONVERSATION_VALIDATED"
    assert row["advisory_conversation_action"] == "DEMO_ONLY"
    assert row["advisory_conversation_health_status"] == "PASS"
    assert row["advisory_conversation_llm_api_called"] == "False"
    assert row["advisory_conversation_no_message_sent"] == "True"
    assert metadata["latest_advisory_conversation_run_id"] == "conv-export"
    assert metadata["advisory_conversation_parsed_symbol"] == "000001"
    assert metadata["advisory_conversation_health_status"] == "PASS"
    assert metadata["advisory_conversation_llm_api_called"] is False
    assert metadata["component_statuses"]["advisory_conversation_parsed_symbol"] == "000001"


def test_cli_research_status_prints_advisory_conversation_fields(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)
    _advisory_conversation_status(root, conversation_id="conv-cli", parsed_symbol="000001")

    code = cli.main(["research-status", "--root", str(root), "--output-dir", str(tmp_path / "dashboard")])
    output = capsys.readouterr()

    assert code == 0
    assert "latest_advisory_conversation_run_id: conv-cli" in output.out
    assert "advisory_conversation_parsed_symbol: 000001" in output.out
    assert "advisory_conversation_status: WARN" in output.out
    assert "advisory_conversation_stage: DEMO_ADVISORY_CONVERSATION_VALIDATED" in output.out
    assert "advisory_conversation_llm_api_called: False" in output.out
    assert "advisory_conversation_no_message_sent: True" in output.out


def _reports_root(tmp_path: Path) -> Path:
    root = tmp_path / "reports"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _active_replay_input_promotion_ready(root: Path):
    input_root = root / "manual_diagnostics" / "active_replay_input_promotion_test_inputs"
    validator = _active_replay_input_promotion_validator_artifact(input_root / "validator")
    smoke = _active_replay_input_promotion_smoke_artifact(input_root / "smoke", validator)
    request = _active_replay_input_promotion_request_manifest(input_root / "promotion_request.json", validator, smoke)
    review = _active_replay_input_promotion_review_manifest(input_root / "human_review.json")
    return run_active_replay_input_promotion(
        ActiveReplayInputPromotionSettings(
            output_dir=root / "manual_diagnostics" / "active_replay_input_promotion_v0_1",
            validator_artifact=validator,
            smoke_artifact=smoke,
            promotion_request_manifest=request,
            human_review_manifest=review,
        )
    )


def _active_replay_input_promotion_validator_artifact(path: Path) -> Path:
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
    (path / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _active_replay_input_promotion_smoke_artifact(path: Path, validator_path: Path) -> Path:
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
    (path / "smoke_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _active_replay_input_promotion_request_manifest(path: Path, validator_artifact: Path, smoke_artifact: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
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
    path.write_text(json.dumps(request, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _active_replay_input_promotion_review_manifest(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
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
    path.write_text(json.dumps(review, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _active_replay_input_acceptance_ready(root: Path):
    input_root = root / "manual_diagnostics" / "active_replay_input_acceptance_test_inputs"
    promotion = _active_replay_input_promotion_ready(root)
    promotion_artifact = promotion.artifact_path
    request = _active_replay_input_acceptance_request_manifest(
        input_root / "acceptance_request.json",
        promotion_artifact,
    )
    authority = _active_replay_input_acceptance_authority_manifest(input_root / "authority.json")
    attestation = _active_replay_input_acceptance_attestation_manifest(input_root / "attestation.json")
    second_review = _active_replay_input_acceptance_second_review_manifest(input_root / "second_review.json")
    red_team = _active_replay_input_acceptance_red_team_manifest(input_root / "red_team.json")
    promotion_health = _write_json(input_root / "promotion_health.json", {"health_status": "PASS"})
    promotion_status = _write_json(
        input_root / "promotion_status.json",
        {"status": "PROMOTION_READY_FOR_HUMAN_REVIEW", "ready_for_human_review": True},
    )
    return run_active_replay_input_acceptance(
        ActiveReplayInputAcceptanceSettings(
            output_dir=root / "manual_diagnostics" / "active_replay_input_acceptance_v0_1",
            promotion_artifact=promotion_artifact,
            promotion_health_artifact=promotion_health,
            promotion_status_artifact=promotion_status,
            acceptance_request_manifest=request,
            reviewer_authority_manifest=authority,
            manual_attestation_manifest=attestation,
            second_review_manifest=second_review,
            red_team_review_manifest=red_team,
        )
    )


def _active_replay_input_active_ready_ready(root: Path):
    input_root = root / "manual_diagnostics" / "active_replay_input_active_ready_test_inputs"
    acceptance = _active_replay_input_acceptance_ready(root)
    acceptance_artifact = acceptance.artifact_path
    acceptance_health = _write_json(input_root / "acceptance_health.json", {"health_status": "PASS"})
    acceptance_status = _write_json(
        input_root / "acceptance_status.json",
        {
            "status": "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW",
            "ready_for_active_ready_review": True,
            "active_replay_input_ready": False,
            "active_replay_input": False,
            "active_ready_emitted": False,
        },
    )
    return run_active_replay_input_active_ready(
        ActiveReplayInputActiveReadySettings(
            output_dir=root / "manual_diagnostics" / "active_replay_input_active_ready_v0_1",
            acceptance_artifact=acceptance_artifact,
            acceptance_health_artifact=acceptance_health,
            acceptance_status_artifact=acceptance_status,
            active_ready_request_manifest=_active_ready_request_manifest(
                input_root / "active_ready_request.json",
                acceptance_artifact,
            ),
            active_ready_authority_manifest=_active_ready_authority_manifest(input_root / "authority.json"),
            pit_coverage_manifest=_active_ready_pit_coverage_manifest(input_root / "pit_coverage.json"),
            source_coverage_manifest=_active_ready_source_coverage_manifest(input_root / "source_coverage.json"),
            evidence_coverage_manifest=_active_ready_evidence_coverage_manifest(input_root / "evidence_coverage.json"),
            taxonomy_compliance_manifest=_active_ready_taxonomy_manifest(input_root / "taxonomy.json"),
            leakage_review_manifest=_active_ready_leakage_manifest(input_root / "leakage.json"),
            side_effect_review_manifest=_active_ready_side_effect_manifest(input_root / "side_effect.json"),
            overclaim_review_manifest=_active_ready_overclaim_manifest(input_root / "overclaim.json"),
        )
    )


def _active_ready_request_manifest(path: Path, acceptance_artifact: Path) -> Path:
    return _write_json(
        path,
        {
            "active_ready_request_id": "active_ready_request_001",
            "requested_by": "fixture_reviewer",
            "requested_at": "2024-04-02T18:00:00+08:00",
            "request_reason": "fixture final-review-only active-ready governance",
            "acceptance_artifact_ref": str(acceptance_artifact),
            "requested_status": "ACTIVE_READY_READY_FOR_FINAL_REVIEW",
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
        },
    )


def _active_ready_authority_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
            "active_ready_authority_id": "authority_001",
            "primary_approver": "primary_fixture_reviewer",
            "second_approver": "second_fixture_reviewer",
            "pit_reviewer": "pit_fixture_reviewer",
            "source_reviewer": "source_fixture_reviewer",
            "evidence_reviewer": "evidence_fixture_reviewer",
            "risk_compliance_reviewer": "risk_fixture_reviewer",
            "strategy_owner": "strategy_fixture_owner",
            "authority_scope": "review-only final-review-ready active-ready governance",
            "authority_result": "ACCEPTED_FOR_REVIEW_ONLY",
            "report_only": True,
            "diagnostic_only": True,
        },
    )


def _active_ready_pit_coverage_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
            "pit_coverage_id": "pit_001",
            "available_time_coverage_complete": True,
            "universe_coverage_complete": True,
            "suspension_st_delist_coverage_complete": True,
            "corporate_action_policy_reviewed": True,
            "pit_result": "PASS",
            "report_only": True,
            "diagnostic_only": True,
        },
    )


def _active_ready_source_coverage_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
            "source_coverage_id": "source_001",
            "source_id_coverage_complete": True,
            "source_hash_coverage_complete": True,
            "revision_id_coverage_complete": True,
            "permission_class_coverage_complete": True,
            "quality_status_coverage_complete": True,
            "source_result": "PASS",
            "report_only": True,
            "diagnostic_only": True,
        },
    )


def _active_ready_evidence_coverage_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
            "evidence_coverage_id": "evidence_001",
            "raw_evidence_refs_complete": True,
            "replay_evidence_bundle_complete": True,
            "factor_definition_coverage_complete": True,
            "factor_observation_coverage_complete": True,
            "event_structured_coverage_complete": True,
            "company_exposure_coverage_complete": True,
            "evidence_result": "PASS",
            "report_only": True,
            "diagnostic_only": True,
        },
    )


def _active_ready_taxonomy_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
            "taxonomy_compliance_id": "taxonomy_001",
            "uses_8_layer_taxonomy": True,
            "not_fixed_12_only": True,
            "factor_layer_metadata_complete": True,
            "trade_usage_metadata_complete": True,
            "compliance_metadata_complete": True,
            "taxonomy_result": "PASS",
            "report_only": True,
            "diagnostic_only": True,
        },
    )


def _active_ready_leakage_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
            "leakage_review_id": "leakage_001",
            "no_future_labels": True,
            "no_forward_returns": True,
            "no_training_outputs": True,
            "no_model_weights": True,
            "no_stock_profile_artifacts": True,
            "no_buy_review_eligibility": True,
            "leakage_result": "PASS",
            "report_only": True,
            "diagnostic_only": True,
        },
    )


def _active_ready_side_effect_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
            "side_effect_review_id": "side_effect_001",
            "no_approval_applied": True,
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
            "no_signal_semantics_changed": True,
            "side_effect_result": "PASS",
            "report_only": True,
            "diagnostic_only": True,
        },
    )


def _active_ready_overclaim_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
            "overclaim_review_id": "overclaim_001",
            "pass_candidate_not_active_ready": True,
            "smoke_not_active_ready": True,
            "promotion_not_active_ready": True,
            "acceptance_not_active_ready": True,
            "final_review_not_active_ready": True,
            "active_ready_not_replay": True,
            "active_ready_not_labels": True,
            "active_ready_not_training": True,
            "active_ready_not_stock_profile": True,
            "active_ready_not_buy_review": True,
            "active_ready_not_trading": True,
            "active_ready_not_performance_validation": True,
            "overclaim_result": "PASS",
            "report_only": True,
            "diagnostic_only": True,
        },
    )


def _active_replay_input_final_review_ready(root: Path):
    input_root = root / "manual_diagnostics" / "active_replay_input_final_review_test_inputs"
    active_ready = _active_replay_input_active_ready_ready(root)
    active_ready_artifact = active_ready.artifact_path
    active_ready_health = _write_json(input_root / "active_ready_health.json", {"health_status": "PASS"})
    active_ready_status = _write_json(
        input_root / "active_ready_status.json",
        {
            "status": "ACTIVE_READY_READY_FOR_FINAL_REVIEW",
            "health_status": "PASS",
            "workflow_stage": "ACTIVE_READY_READY_FOR_FINAL_REVIEW",
            "ready_for_final_review": True,
            "active_replay_input_ready": False,
            "active_replay_input": False,
            "active_ready_emitted": False,
        },
    )
    return run_active_replay_input_final_review(
        ActiveReplayInputFinalReviewSettings(
            output_dir=root / "manual_diagnostics" / "active_replay_input_final_review_v0_1",
            active_ready_artifact=active_ready_artifact,
            active_ready_health_artifact=active_ready_health,
            active_ready_status_artifact=active_ready_status,
            final_review_package_manifest=_final_review_package_manifest(
                input_root / "final_review_package.json",
                active_ready_artifact,
            ),
            final_review_authority_manifest=_final_review_authority_manifest(input_root / "authority.json"),
            final_review_attestation_manifest=_final_review_attestation_manifest(input_root / "attestation.json"),
            pit_source_evidence_attachment_bundle=_final_review_pit_source_bundle(input_root / "pit_source.json"),
            taxonomy_attachment_bundle=_final_review_taxonomy_bundle(input_root / "taxonomy.json"),
            leakage_side_effect_evidence_bundle=_final_review_leakage_side_effect_bundle(
                input_root / "leakage_side_effect.json"
            ),
            overclaim_evidence_bundle=_final_review_overclaim_bundle(input_root / "overclaim.json"),
            emission_request_manifest=_final_review_emission_request_manifest(input_root / "emission.json"),
        )
    )


def _active_replay_input_emission_ready(root: Path):
    input_root = root / "manual_diagnostics" / "active_replay_input_emission_test_inputs"
    final_review = _active_replay_input_final_review_ready(root)
    final_review_artifact = final_review.artifact_path
    final_review_health = _write_json(input_root / "final_review_health.json", {"health_status": "PASS"})
    final_review_status = _write_json(
        input_root / "final_review_status.json",
        {
            "status": "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW",
            "workflow_stage": "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW",
            "ready_for_emission_review": True,
            "active_replay_input_ready": False,
            "active_replay_input": False,
            "active_ready_emitted": False,
        },
    )
    return run_active_replay_input_emission(
        ActiveReplayInputEmissionSettings(
            output_dir=root / "manual_diagnostics" / "active_replay_input_emission_v0_1",
            final_review_artifact_path=final_review_artifact,
            final_review_health_artifact_path=final_review_health,
            final_review_status_artifact_path=final_review_status,
            emission_request_manifest_path=_emission_request_manifest(input_root / "emission_request.json"),
            emission_authority_manifest_path=_emission_authority_manifest(input_root / "authority.json"),
            emission_attestation_manifest_path=_emission_attestation_manifest(input_root / "attestation.json"),
            pit_source_evidence_bundle_path=_emission_pit_source_evidence(input_root / "pit_source.json"),
            taxonomy_evidence_bundle_path=_emission_taxonomy_bundle(input_root / "taxonomy.json"),
            leakage_side_effect_evidence_bundle_path=_emission_leakage_side_effect_bundle(
                input_root / "leakage_side_effect.json"
            ),
            overclaim_evidence_bundle_path=_emission_overclaim_bundle(input_root / "overclaim.json"),
        )
    )


def _active_replay_input_ready_ready(root: Path):
    input_root = root / "manual_diagnostics" / "active_replay_input_ready_test_inputs"
    ready_decision = _write_json(input_root / "ready_decision.json", _active_replay_input_ready_decision_payload())
    ready_decision_health = _write_json(input_root / "ready_decision_health.json", {"health_status": "PASS"})
    ready_decision_status = _write_json(
        input_root / "ready_decision_status.json",
        {
            "status": "READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION",
            "workflow_stage": "READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION",
            "ready_for_active_replay_input_ready_decision": True,
            "active_replay_input_ready": False,
            "active_replay_input": False,
            "active_ready_emitted": False,
            "replay_execution_allowed": False,
            "replay_decisions_exist": False,
        },
    )
    governance_audit = input_root / "governance_audit.md"
    governance_audit.write_text("Report-only governance audit accepted for fixture.", encoding="utf-8")
    return run_active_replay_input_ready(
        ActiveReplayInputReadySettings(
            output_dir=root / "manual_diagnostics" / "active_replay_input_ready_v0_1",
            ready_decision_artifact_path=ready_decision,
            ready_decision_health_artifact_path=ready_decision_health,
            ready_decision_status_artifact_path=ready_decision_status,
            governance_audit_path=governance_audit,
            governance_request_manifest_path=_active_replay_input_ready_request_manifest(
                input_root / "governance_request.json"
            ),
            final_authority_manifest_path=_active_replay_input_ready_authority_manifest(
                input_root / "authority.json"
            ),
            final_attestation_manifest_path=_active_replay_input_ready_attestation_manifest(
                input_root / "attestation.json"
            ),
            pit_source_evidence_bundle_path=_active_replay_input_ready_pit_source_bundle(
                input_root / "pit_source.json"
            ),
            taxonomy_evidence_bundle_path=_active_replay_input_ready_taxonomy_bundle(
                input_root / "taxonomy.json"
            ),
            leakage_side_effect_evidence_bundle_path=_active_replay_input_ready_leakage_bundle(
                input_root / "leakage_side_effect.json"
            ),
            overclaim_evidence_bundle_path=_active_replay_input_ready_overclaim_bundle(
                input_root / "overclaim.json"
            ),
        )
    )


def _active_replay_input_ready_decision_payload() -> dict[str, object]:
    return {
        "decision_run_id": "ready_decision_fixture",
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
        "broker_api_called": False,
        "message_sent": False,
        "llm_api_called": False,
        "external_api_called": False,
        "cache_mutated": False,
        "data_raw_written": False,
        "data_processed_written": False,
        "data_cache_written": False,
        "current_candidates_run": False,
        "snapshot_built": False,
        "approved_for_paper": False,
        "report_only": True,
        "diagnostic_only": True,
    }


def _active_replay_input_ready_request_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
            "request_result": "PASS",
            "requested_status": "READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY",
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
        },
    )


def _active_replay_input_ready_authority_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
            "authority_result": "PASS",
            "primary_reviewer": "primary_fixture_reviewer",
            "second_reviewer": "second_fixture_reviewer",
            "authority_scope": "report-only ACTIVE_REPLAY_INPUT_READY governance",
            "report_only": True,
            "diagnostic_only": True,
        },
    )


def _active_replay_input_ready_attestation_manifest(path: Path) -> Path:
    return _write_json(
        path,
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
    )


def _active_replay_input_ready_pit_source_bundle(path: Path) -> Path:
    return _write_json(
        path,
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
    )


def _active_replay_input_ready_taxonomy_bundle(path: Path) -> Path:
    return _write_json(
        path,
        {
            "uses_8_layer_taxonomy": True,
            "not_fixed_12_only": True,
            "factor_layer_metadata_attached": True,
            "trade_usage_metadata_attached": True,
            "compliance_metadata_attached": True,
            "report_only": True,
            "diagnostic_only": True,
        },
    )


def _active_replay_input_ready_leakage_bundle(path: Path) -> Path:
    return _write_json(
        path,
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
    )


def _active_replay_input_ready_overclaim_bundle(path: Path) -> Path:
    return _write_json(
        path,
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
    )


def _emission_request_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
            "emission_request_id": "emission_request_001",
            "requested_status": "EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW",
            "requested_by": "fixture_reviewer",
            "requested_at": "2024-04-02T20:00:00+08:00",
            "request_reason": "fixture report-only active replay input emission review",
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
        },
    )


def _emission_authority_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
            "emission_authority_id": "emission_authority_001",
            "primary_reviewer": "primary_fixture_reviewer",
            "second_reviewer": "second_fixture_reviewer",
            "pit_source_reviewer": "pit_fixture_reviewer",
            "evidence_taxonomy_reviewer": "evidence_fixture_reviewer",
            "risk_compliance_reviewer": "risk_fixture_reviewer",
            "system_operator": "operator_fixture",
            "strategy_owner": "strategy_fixture_owner",
            "authority_scope": "report-only active replay input emission review",
            "authority_result": "ACCEPTED_FOR_REVIEW_ONLY",
            "report_only": True,
            "diagnostic_only": True,
        },
    )


def _emission_attestation_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
            "attestation_id": "emission_attestation_001",
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
        },
    )


def _emission_pit_source_evidence(path: Path) -> Path:
    return _write_json(
        path,
        {
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
        },
    )


def _emission_taxonomy_bundle(path: Path) -> Path:
    return _write_json(
        path,
        {
            "uses_8_layer_taxonomy": True,
            "not_fixed_12_only": True,
            "factor_layer_metadata_attached": True,
            "trade_usage_metadata_attached": True,
            "compliance_metadata_attached": True,
            "taxonomy_result": "PASS",
            "report_only": True,
            "diagnostic_only": True,
        },
    )


def _emission_leakage_side_effect_bundle(path: Path) -> Path:
    return _write_json(
        path,
        {
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
        },
    )


def _emission_overclaim_bundle(path: Path) -> Path:
    return _write_json(
        path,
        {
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
        },
    )


def _final_review_package_manifest(path: Path, active_ready_artifact: Path) -> Path:
    return _write_json(
        path,
        {
            "final_review_package_id": "final_review_package_001",
            "requested_by": "fixture_reviewer",
            "requested_at": "2024-04-02T19:00:00+08:00",
            "package_reason": "fixture final review emission-readiness context",
            "active_ready_artifact_ref": str(active_ready_artifact),
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
        },
    )


def _final_review_authority_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
            "final_review_authority_id": "final_authority_001",
            "primary_reviewer": "primary_fixture_reviewer",
            "second_reviewer": "second_fixture_reviewer",
            "pit_source_reviewer": "pit_fixture_reviewer",
            "evidence_taxonomy_reviewer": "evidence_fixture_reviewer",
            "risk_compliance_reviewer": "risk_fixture_reviewer",
            "system_operator": "operator_fixture",
            "strategy_owner": "strategy_fixture_owner",
            "authority_scope": "report-only final-review emission-readiness context",
            "authority_result": "ACCEPTED_FOR_REVIEW_ONLY",
            "report_only": True,
            "diagnostic_only": True,
        },
    )


def _final_review_attestation_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
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
        },
    )


def _final_review_pit_source_bundle(path: Path) -> Path:
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
    return _write_json(path, payload)


def _final_review_taxonomy_bundle(path: Path) -> Path:
    return _write_json(
        path,
        {
            "uses_8_layer_taxonomy": True,
            "not_fixed_12_only": True,
            "factor_layer_metadata_attached": True,
            "trade_usage_metadata_attached": True,
            "compliance_metadata_attached": True,
            "taxonomy_result": "PASS",
            "report_only": True,
            "diagnostic_only": True,
        },
    )


def _final_review_leakage_side_effect_bundle(path: Path) -> Path:
    return _write_json(
        path,
        {
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
        },
    )


def _final_review_overclaim_bundle(path: Path) -> Path:
    return _write_json(
        path,
        {
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
        },
    )


def _final_review_emission_request_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
            "requested_status": "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW",
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
        },
    )


def _active_replay_input_acceptance_request_manifest(path: Path, promotion_artifact: Path) -> Path:
    return _write_json(
        path,
        {
            "acceptance_request_id": "acceptance_request_001",
            "requested_by": "fixture_reviewer",
            "requested_at": "2024-04-02T17:00:00+08:00",
            "request_reason": "fixture report-only acceptance",
            "promotion_artifact_ref": str(promotion_artifact),
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
        },
    )


def _active_replay_input_acceptance_authority_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
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
        },
    )


def _active_replay_input_acceptance_attestation_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
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
        },
    )


def _active_replay_input_acceptance_second_review_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
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
        },
    )


def _active_replay_input_acceptance_red_team_manifest(path: Path) -> Path:
    return _write_json(
        path,
        {
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
        },
    )


def _workflow_to_current_candidates(root: Path) -> Path:
    _data_preparation_status(root)
    _snapshot_quality(root)
    _current_candidate(root)
    return root


def _workflow_to_current_candidate_health(root: Path) -> Path:
    _workflow_to_current_candidates(root)
    _current_candidate_health(root, status="PASS")
    return root


def _workflow_to_paper_handoff(root: Path) -> Path:
    _workflow_to_current_candidate_health(root)
    _current_to_paper_handoff(root)
    return root


def _workflow_to_review_template(root: Path) -> Path:
    _workflow_to_paper_handoff(root)
    _review_template(root)
    return root


def _workflow_to_review(root: Path) -> Path:
    _workflow_to_review_template(root)
    _review_template_health(root, status="PASS")
    _paper_review(root)
    return root


def _workflow_to_daily(root: Path) -> Path:
    _workflow_to_review(root)
    _daily_paper(root)
    return root


def _workflow_complete(root: Path) -> Path:
    _workflow_to_daily(root)
    _reconciliation(root, status="PASS")
    _paper_workflow_status(root, status="PASS")
    return root


def _data_preparation_status(root: Path) -> Path:
    folder = root / "data_preparation" / "workflow_status" / "data-prep-status-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "data_preparation_workflow_status_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "workflow_status_id": "data-prep-status-a",
            "created_at": f"{DECISION_DATE}T09:00:00",
            "status": "PASS",
            "workflow_stage": "DATA_PREP_WORKFLOW_COMPLETE",
            "latest_decision_date": DECISION_DATE,
            "latest_pipeline_id": "pipeline-a",
            "latest_snapshot_id": "snapshot-a",
            "next_manual_action": "Proceed to current-to-paper.",
            "output_files": {"data_preparation_workflow_status_report": str(report)},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _snapshot_quality(root: Path, *, status: str = "PASS") -> Path:
    folder = root / "snapshot_quality" / "snapshot-a_gate-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "snapshot_quality_gate_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "snapshot_id": "snapshot-a",
            "quality_gate_id": "gate-a",
            "created_at": f"{DECISION_DATE}T09:10:00",
            "status": status,
            "warning_count": 1 if status == "WARN" else 0,
            "error_count": 1 if status == "FAIL" else 0,
            "output_files": {"snapshot_quality_gate_report": str(report)},
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _current_candidate(root: Path, *, run_id: str = "run-a") -> Path:
    folder = root / "current_candidates" / f"{DECISION_DATE}_{UNIVERSE}_{run_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "current_candidates_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "run_id": run_id,
            "decision_date": DECISION_DATE,
            "universe_name": UNIVERSE,
            "created_at": f"{DECISION_DATE}T15:30:00",
            "row_counts": {"factor_dataset": 2, "scored_dataset": 2, "candidates": 1},
            "output_files": {
                "current_candidates_report": str(report),
                "candidates": str(folder / "candidates.csv"),
                "factor_dataset": str(folder / "factor_dataset.csv"),
                "scored_dataset": str(folder / "scored_dataset.csv"),
            },
            "snapshot_quality": {"status": "PASS", "report_path": str(root / "snapshot_quality" / "snapshot-a_gate-a" / "snapshot_quality_gate_report.md")},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _current_candidate_health(root: Path, *, status: str = "PASS", errors: int = 0, warnings: int = 0) -> Path:
    folder = root / "current_candidates" / "health" / "cch-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "current_candidate_artifact_health_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "health_check_id": "cch-a",
            "created_at": f"{DECISION_DATE}T15:40:00",
            "status": status,
            "issue_count": errors + warnings,
            "error_count": errors,
            "warning_count": warnings,
            "output_files": {"current_candidate_artifact_health_report": str(report)},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _current_candidate_health_with_issues(
    root: Path,
    *,
    status: str,
    issues: list[dict],
) -> Path:
    folder = root / "current_candidates" / "health" / "cch-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "current_candidate_artifact_health_report.md"
    issues_path = folder / "current_candidate_artifact_health_issues.csv"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    pd.DataFrame(issues).to_csv(issues_path, index=False)
    error_count = sum(1 for issue in issues if issue.get("severity") == "ERROR")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "WARN")
    _write_json(
        folder / "metadata.json",
        {
            "health_check_id": "cch-a",
            "created_at": f"{DECISION_DATE}T15:40:00",
            "status": status,
            "issue_count": len(issues),
            "error_count": error_count,
            "warning_count": warning_count,
            "output_files": {
                "current_candidate_artifact_health_report": str(report),
                "current_candidate_artifact_health_issues": str(issues_path),
            },
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _current_to_paper_handoff(root: Path) -> Path:
    folder = root / "current_to_paper_handoff" / "handoff-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "handoff_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "handoff_metadata.json",
        {
            "handoff_id": "handoff-a",
            "created_at": f"{DECISION_DATE}T15:45:00",
            "selected_decision_date": DECISION_DATE,
            "selected_universe_name": UNIVERSE,
            "selected_run_id": "run-a",
            "paper_journal_id": "journal-a",
            "output_files": {"handoff_report": str(report)},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _review_template(root: Path) -> Path:
    folder = root / "current_to_paper_review_handoff" / "review-template-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "review_handoff_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "review_handoff_id": "review-template-a",
            "created_at": f"{DECISION_DATE}T15:50:00",
            "decision_count": 1,
            "output_files": {
                "review_handoff_report": str(report),
                "review_updates_template": str(folder / "review_updates_template.csv"),
            },
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _review_template_health(
    root: Path,
    *,
    health_id: str = "template-health-a",
    status: str = "PASS",
    errors: int = 0,
    warnings: int = 0,
) -> Path:
    folder = root / "paper_trading" / "review_template_health" / health_id
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "review_template_health_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "health_check_id": health_id,
            "created_at": f"{DECISION_DATE}T15:55:00",
            "status": status,
            "issue_count": errors + warnings,
            "error_count": errors,
            "warning_count": warnings,
            "output_files": {"review_template_health_report": str(report)},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _paper_review(
    root: Path,
    *,
    review_id: str = "review-a",
    template_health: dict | None = None,
    warnings: list[str] | None = None,
) -> Path:
    folder = root / "paper_trading" / "reviews" / review_id
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "paper_review_report.md"
    reviewed = folder / "reviewed_decisions.csv"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    pd.DataFrame(
        [
            {
                "decision_id": "d1",
                "symbol": "510300",
                "manual_review_status": "WATCH_ONLY",
            }
        ]
    ).to_csv(reviewed, index=False)
    metadata = {
        "review_id": review_id,
        "created_at": f"{DECISION_DATE}T16:00:00",
        "output_files": {
            "paper_review_report": str(report),
            "reviewed_decisions": str(reviewed),
        },
        "warnings": warnings or [],
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
    }
    if template_health is not None:
        metadata["template_health"] = template_health
    _write_json(folder / "metadata.json", metadata)
    return folder


def _daily_paper(
    root: Path,
    *,
    reviewed_decisions_path: Path | None = None,
    reconciliation_report_path: Path | None = None,
    reconciliation_status: str = "",
    reconciliation_issue_count: int = 0,
    reconciliation_error_count: int = 0,
    reconciliation_warning_count: int = 0,
) -> Path:
    folder = root / "paper_trading" / "daily" / f"{DECISION_DATE}_journal-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "paper_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    reconciliation = {
        "status": reconciliation_status,
        "issue_count": reconciliation_issue_count,
        "error_count": reconciliation_error_count,
        "warning_count": reconciliation_warning_count,
    }
    if reconciliation_report_path is not None:
        reconciliation["report_path"] = str(reconciliation_report_path)
    _write_json(
        folder / "metadata.json",
        {
            "paper_date": DECISION_DATE,
            "journal_id": "journal-a",
            "created_at": f"{DECISION_DATE}T16:05:00",
            "reviewed_decisions_used": True,
            "reconciliation": reconciliation,
            "output_files": {"paper_report": str(report), "decisions": str(folder / "decisions.csv")},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "paper_trading_only": True,
        },
    )
    if reviewed_decisions_path is not None:
        metadata_path = folder / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["reviewed_decisions_path"] = str(reviewed_decisions_path)
        metadata["output_files"]["reviewed_decisions"] = str(reviewed_decisions_path)
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return folder


def _reconciliation(
    root: Path,
    *,
    reconciliation_id: str = "recon-a",
    status: str = "PASS",
    errors: int = 0,
    warnings: int = 0,
    created_at: str | None = None,
) -> Path:
    folder = root / "paper_trading" / "reconciliation" / reconciliation_id
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "reconciliation_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "reconciliation_id": reconciliation_id,
            "created_at": created_at or f"{DECISION_DATE}T16:10:00",
            "status": status,
            "issue_count": errors + warnings,
            "error_count": errors,
            "warning_count": warnings,
            "output_files": {"reconciliation_report": str(report)},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "paper_trading_only": True,
        },
    )
    return folder


def _paper_workflow_status(
    root: Path,
    *,
    workflow_status_id: str = "paper-workflow-status-a",
    status: str = "PASS",
    workflow_stage: str | None = None,
    expected_demo_warning_count: int = 0,
    stale_warning_count: int = 0,
    actionable_warning_count: int = 0,
    blocking_error_count: int = 0,
    next_manual_action: str = "Review completed workflow artifacts.",
    created_at: str | None = None,
) -> Path:
    folder = root / "paper_trading" / "workflow_status" / workflow_status_id
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "paper_workflow_status_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    total_warning_count = expected_demo_warning_count + stale_warning_count + actionable_warning_count
    resolved_stage = workflow_stage or ("WORKFLOW_COMPLETE" if status == "PASS" else "WORKFLOW_NEEDS_ATTENTION")
    _write_json(
        folder / "metadata.json",
        {
            "workflow_status_id": workflow_status_id,
            "created_at": created_at or f"{DECISION_DATE}T16:15:00",
            "status": status,
            "workflow_stage": resolved_stage,
            "latest_decision_date": DECISION_DATE,
            "next_manual_action": next_manual_action,
            "total_warning_count": total_warning_count,
            "expected_demo_warning_count": expected_demo_warning_count,
            "stale_warning_count": stale_warning_count,
            "actionable_warning_count": actionable_warning_count,
            "blocking_error_count": blocking_error_count,
            "component_statuses": {
                "total_warning_count": total_warning_count,
                "expected_demo_warning_count": expected_demo_warning_count,
                "stale_warning_count": stale_warning_count,
                "actionable_warning_count": actionable_warning_count,
                "blocking_error_count": blocking_error_count,
            },
            "output_files": {"paper_workflow_status_report": str(report)},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _historical_backfill_status(
    root: Path,
    *,
    status: str = "WARN",
    workflow_stage: str = "BACKFILL_WARNINGS_NEED_REVIEW",
    backfill_id: str = "backfill-a",
    health_status: str = "WARN",
    warning_count: int = 0,
    error_count: int = 0,
    cache_write_occurred: bool = False,
    accepted_task_count: int = 0,
    rejected_task_count: int = 0,
    preflight_rejected_count: int = 0,
    comparison_failed_count: int = 0,
    cache_write_partial: bool = False,
    rejected_symbols: str = "",
    rejected_sources: str = "",
    rejected_issue_categories: str = "",
    created_at: str = f"{DECISION_DATE}T14:30:00",
) -> Path:
    folder = root / "historical_backfill" / "status" / f"status-{backfill_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "historical_backfill_status_report.md"
    status_csv = folder / "historical_backfill_status.csv"
    summary_csv = folder / "historical_backfill_status_summary.csv"
    metadata_path = folder / "metadata.json"
    next_action = (
        "Review rejected rows; accepted rows were cache-written. Use reviewed export/snapshot path if downstream validation passed."
        if workflow_stage == "BACKFILL_PARTIAL_WITH_REJECTIONS"
        else "Review WARN tasks and only rerun with --accept-cache-write after manual approval."
    )
    report.write_text("No live trading or broker API was invoked.", encoding="utf-8")
    pd.DataFrame(
        [
            {
                "component": "HISTORICAL_BACKFILL_INDEX",
                "status": "PASS",
                "latest_backfill_id": backfill_id,
                "warning_count": 0,
                "error_count": 0,
                "issue_count": 0,
            },
            {
                "component": "HISTORICAL_BACKFILL_HEALTH",
                "status": health_status,
                "latest_backfill_id": backfill_id,
                "warning_count": warning_count,
                "error_count": error_count,
                "issue_count": warning_count + error_count,
            },
            {
                "component": "LATEST_HISTORICAL_BACKFILL",
                "status": status,
                "latest_backfill_id": backfill_id,
                "warning_count": warning_count,
                "error_count": error_count,
                "issue_count": warning_count + error_count,
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "status": status,
                "workflow_stage": workflow_stage,
                "latest_backfill_id": backfill_id,
                "task_count": 6,
                "pass_count": 3,
                "warn_count": 3 if status == "WARN" else 0,
                "fail_count": 1 if status == "FAIL" else 0,
                "skipped_count": 0,
                "cache_write_occurred": cache_write_occurred,
                "accepted_task_count": accepted_task_count,
                "rejected_task_count": rejected_task_count,
                "preflight_rejected_count": preflight_rejected_count,
                "comparison_failed_count": comparison_failed_count,
                "cache_write_partial": cache_write_partial,
                "rejected_symbols": rejected_symbols,
                "rejected_sources": rejected_sources,
                "rejected_issue_categories": rejected_issue_categories,
                "health_status": health_status,
                "issue_count": warning_count + error_count,
                "warning_count": warning_count,
                "error_count": error_count,
                "next_manual_action": next_action,
                "report_path": str(root / "historical_backfill" / backfill_id / "historical_backfill_report.md"),
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{backfill_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_backfill_id": backfill_id,
            "next_manual_action": next_action,
            "accepted_task_count": accepted_task_count,
            "rejected_task_count": rejected_task_count,
            "preflight_rejected_count": preflight_rejected_count,
            "comparison_failed_count": comparison_failed_count,
            "cache_write_partial": cache_write_partial,
            "rejected_symbols": rejected_symbols,
            "rejected_sources": rejected_sources,
            "rejected_issue_categories": rejected_issue_categories,
            "warnings": ["Expected dry-run WARN tasks need review."] if warning_count else [],
            "output_files": {
                "historical_backfill_status_report": str(report),
                "historical_backfill_status_csv": str(status_csv),
                "historical_backfill_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _market_cache_export_status(
    root: Path,
    *,
    export_id: str = "export-a",
    status: str = "PASS",
    workflow_stage: str = "SNAPSHOT_READY_FROM_EXPORT",
    health_status: str = "PASS",
    snapshot_quality_status: str = "PASS",
    warning_count: int = 0,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:00:00",
) -> Path:
    folder = root / "market_cache_export" / "status" / f"status-{export_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "market_cache_export_status_report.md"
    status_csv = folder / "market_cache_export_status.csv"
    summary_csv = folder / "market_cache_export_status_summary.csv"
    metadata_path = folder / "metadata.json"
    snapshot_manifest = root / "market_cache_export" / export_id / "snapshot_manifest.json"
    export_report = root / "market_cache_export" / export_id / "market_cache_export_report.md"
    next_action = "Use the snapshot manifest for current-candidates or link this export into research-status."
    report.write_text("No live trading or broker API was invoked.", encoding="utf-8")
    pd.DataFrame(
        [
            {
                "component": "MARKET_CACHE_EXPORT_INDEX",
                "status": "PASS",
                "latest_export_id": export_id,
                "warning_count": 0,
                "error_count": 0,
                "issue_count": 0,
            },
            {
                "component": "MARKET_CACHE_EXPORT_HEALTH",
                "status": health_status,
                "latest_export_id": export_id,
                "warning_count": warning_count,
                "error_count": error_count,
                "issue_count": warning_count + error_count,
            },
            {
                "component": "LATEST_MARKET_CACHE_EXPORT",
                "status": status,
                "latest_export_id": export_id,
                "warning_count": warning_count,
                "error_count": error_count,
                "issue_count": warning_count + error_count,
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "status": status,
                "workflow_stage": workflow_stage,
                "latest_export_id": export_id,
                "exported_row_count": 93,
                "duplicate_key_count": 0,
                "generated_pipeline_manifest_path": str(
                    root / "market_cache_export" / export_id / "market_cache_export_manifest.json"
                ),
                "pipeline_id": f"pipeline-{export_id}",
                "data_pipeline_status": "PASS",
                "data_quality_status": "PASS",
                "snapshot_quality_status": snapshot_quality_status,
                "snapshot_manifest_path": str(snapshot_manifest),
                "health_status": health_status,
                "issue_count": warning_count + error_count,
                "warning_count": warning_count,
                "error_count": error_count,
                "next_manual_action": next_action,
                "report_path": str(export_report),
                "no_live_trading": True,
                "no_broker_api": True,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{export_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_export_id": export_id,
            "next_manual_action": next_action,
            "warnings": ["Reviewed cache export needs attention."] if warning_count else [],
            "output_files": {
                "market_cache_export_status_report": str(report),
                "market_cache_export_status_csv": str(status_csv),
                "market_cache_export_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _market_cache_export_policy_status(
    root: Path,
    *,
    plan_id: str = "plan-a",
    status: str = "WARN",
    workflow_stage: str = "SNAPSHOT_READY_FROM_POLICY_PLAN",
    health_status: str = "WARN",
    warning_count: int = 0,
    error_count: int = 0,
    comparison_pass_count: int = 1,
    comparison_warn_count: int = 0,
    comparison_fail_count: int = 0,
    comparison_unavailable_count: int = 1,
    comparison_required_but_missing_count: int = 0,
    comparison_supported_recommendation_count: int = 1,
    comparison_unsupported_recommendation_count: int = 1,
    created_at: str = f"{DECISION_DATE}T14:50:00",
) -> Path:
    folder = root / "market_cache_export_policy" / "status" / f"status-{plan_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "market_cache_export_policy_status_report.md"
    status_csv = folder / "market_cache_export_policy_status.csv"
    summary_csv = folder / "market_cache_export_policy_status_summary.csv"
    metadata_path = folder / "metadata.json"
    generated_manifest = root / "market_cache_export_policy" / "_manifests" / f"market_cache_export_recommended_{plan_id}.csv"
    downstream_export_id = f"export-{plan_id}"
    next_action = "Review policy warnings, then use the linked snapshot/export outputs for downstream research if appropriate."
    report.write_text("No live trading or broker API was invoked.", encoding="utf-8")
    generated_manifest.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "symbol": "000001",
                "start_date": "2024-01-02",
                "end_date": "2024-01-05",
                "source": "AKSHARE_OPTIONAL",
                "upstream_source": "TENCENT",
                "enabled": "true",
            }
        ]
    ).to_csv(generated_manifest, index=False)
    pd.DataFrame(
        [
            {
                "component": "MARKET_CACHE_EXPORT_POLICY_INDEX",
                "status": "PASS",
                "latest_plan_id": plan_id,
                "warning_count": 0,
                "error_count": 0,
                "issue_count": 0,
                "comparison_pass_count": comparison_pass_count,
                "comparison_warn_count": comparison_warn_count,
                "comparison_fail_count": comparison_fail_count,
                "comparison_unavailable_count": comparison_unavailable_count,
                "comparison_supported_recommendation_count": comparison_supported_recommendation_count,
                "comparison_unsupported_recommendation_count": comparison_unsupported_recommendation_count,
            },
            {
                "component": "MARKET_CACHE_EXPORT_POLICY_HEALTH",
                "status": health_status,
                "latest_plan_id": plan_id,
                "warning_count": warning_count,
                "error_count": error_count,
                "issue_count": warning_count + error_count,
                "comparison_pass_count": comparison_pass_count,
                "comparison_warn_count": comparison_warn_count,
                "comparison_fail_count": comparison_fail_count,
                "comparison_unavailable_count": comparison_unavailable_count,
                "comparison_supported_recommendation_count": comparison_supported_recommendation_count,
                "comparison_unsupported_recommendation_count": comparison_unsupported_recommendation_count,
            },
            {
                "component": "LATEST_MARKET_CACHE_EXPORT_POLICY_PLAN",
                "status": status,
                "latest_plan_id": plan_id,
                "warning_count": warning_count,
                "error_count": error_count,
                "issue_count": warning_count + error_count,
                "comparison_pass_count": comparison_pass_count,
                "comparison_warn_count": comparison_warn_count,
                "comparison_fail_count": comparison_fail_count,
                "comparison_unavailable_count": comparison_unavailable_count,
                "comparison_supported_recommendation_count": comparison_supported_recommendation_count,
                "comparison_unsupported_recommendation_count": comparison_unsupported_recommendation_count,
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "status": status,
                "workflow_stage": workflow_stage,
                "latest_plan_id": plan_id,
                "recommendation_count": 2,
                "recommended_count": 1,
                "recommended_with_warnings_count": 1 if warning_count else 0,
                "no_reliable_source_count": 0,
                "no_cache_rows_count": 0,
                "comparison_pass_count": comparison_pass_count,
                "comparison_warn_count": comparison_warn_count,
                "comparison_fail_count": comparison_fail_count,
                "comparison_unavailable_count": comparison_unavailable_count,
                "comparison_required_but_missing_count": comparison_required_but_missing_count,
                "comparison_supported_recommendation_count": comparison_supported_recommendation_count,
                "comparison_unsupported_recommendation_count": comparison_unsupported_recommendation_count,
                "generated_reviewed_manifest_path": str(generated_manifest),
                "downstream_export_id": downstream_export_id,
                "downstream_export_status": "PASS",
                "downstream_pipeline_id": f"pipeline-{plan_id}",
                "downstream_snapshot_quality_status": "PASS",
                "health_status": health_status,
                "issue_count": warning_count + error_count,
                "warning_count": warning_count,
                "error_count": error_count,
                "next_manual_action": next_action,
                "report_path": str(root / "market_cache_export_policy" / plan_id / "market_cache_export_policy_report.md"),
                "no_live_trading": True,
                "no_broker_api": True,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{plan_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_plan_id": plan_id,
            "next_manual_action": next_action,
            "warnings": ["PROVISIONAL recommendation needs review."] if warning_count else [],
            "output_files": {
                "market_cache_export_policy_status_report": str(report),
                "market_cache_export_policy_status_csv": str(status_csv),
                "market_cache_export_policy_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _calibration_to_signal_semantics_status(
    root: Path,
    *,
    proposal_id: str = "proposal-a",
    status: str = "WARN",
    workflow_stage: str = "CALIBRATION_TO_SEMANTICS_NEEDS_MORE_EVIDENCE",
    health_status: str = "PASS",
    proposal_categories: str = (
        "KEEP_CURRENT_DEFAULTS;CONSIDER_WATCH_EXPANSION;DO_NOT_EXPAND_BUY_REVIEW_YET;"
        "REQUIRE_MORE_EVIDENCE;NEED_MULTI_DATE_VALIDATION;NEED_MORE_SYMBOLS;"
        "NEED_BACKTEST_OR_PAPER_EVIDENCE"
    ),
    defaults_changed: bool = False,
    calibration_run_count: int = 10,
    observed_review_buy_candidate_count: int = 7,
    observed_watch_count: int = 8,
    observed_blocked_count: int = 24,
    warning_count: int = 1,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:40:30",
) -> Path:
    folder = root / "calibration_to_signal_semantics" / "status" / f"status-{proposal_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "calibration_to_signal_semantics_status_report.md"
    status_csv = folder / "calibration_to_signal_semantics_status.csv"
    summary_csv = folder / "calibration_to_signal_semantics_status_summary.csv"
    metadata_path = folder / "metadata.json"
    proposal_report = (
        root / "calibration_to_signal_semantics" / proposal_id / "calibration_to_signal_semantics_report.md"
    )
    next_action = (
        "Keep current defaults; consider WATCH expansion only after more evidence; do not expand BUY review yet."
        if workflow_stage == "CALIBRATION_TO_SEMANTICS_NEEDS_MORE_EVIDENCE"
        else "Repair calibration-to-semantics proposal artifacts before dashboard integration."
        if status == "FAIL"
        else "Review proposal manually; do not change signal_semantics defaults without explicit implementation work."
    )
    report.write_text(
        "No live trading, broker API, order placement, message delivery, LLM API, or external API was invoked.",
        encoding="utf-8",
    )
    proposal_report.parent.mkdir(parents=True, exist_ok=True)
    proposal_report.write_text(
        "Proposal context only. REVIEW_BUY_CANDIDATE remains human-review-only, not an order.",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "component": "CALIBRATION_TO_SIGNAL_SEMANTICS_PROPOSAL",
                "status": "READY" if status != "FAIL" else "FAIL",
                "latest_artifact_id": proposal_id,
                "row_count": calibration_run_count,
                "warning_count": 0,
                "error_count": 0,
                "issue_count": 0,
            },
            {
                "component": "CALIBRATION_TO_SIGNAL_SEMANTICS_HEALTH",
                "status": health_status,
                "latest_artifact_id": "proposal-health-a",
                "row_count": calibration_run_count,
                "warning_count": 0 if health_status == "PASS" else warning_count,
                "error_count": error_count,
                "issue_count": error_count + (0 if health_status == "PASS" else warning_count),
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "workflow_stage": workflow_stage,
                "status": status,
                "latest_proposal_run_id": proposal_id,
                "latest_status": "READY" if status != "FAIL" else "FAIL",
                "health_status": health_status,
                "proposal_categories": proposal_categories,
                "defaults_changed": defaults_changed,
                "calibration_run_count": calibration_run_count,
                "observed_review_buy_candidate_count": observed_review_buy_candidate_count,
                "observed_watch_count": observed_watch_count,
                "observed_blocked_count": observed_blocked_count,
                "report_path": str(proposal_report),
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{proposal_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_proposal_run_id": proposal_id,
            "health_status": health_status,
            "proposal_categories": proposal_categories.split(";"),
            "defaults_changed": defaults_changed,
            "next_manual_action": next_action,
            "warnings": ["Proposal says more evidence is needed."] if warning_count else [],
            "output_files": {
                "calibration_to_signal_semantics_status_report": str(report),
                "calibration_to_signal_semantics_status_csv": str(status_csv),
                "calibration_to_signal_semantics_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "external_api_called": False,
            "llm_api_called": False,
            "config_mutated": False,
            "auto_order_allowed": False,
        },
    )
    return folder


def _current_candidates_backfill_plan_status(
    root: Path,
    *,
    plan_id: str = "plan-a",
    status: str = "PASS",
    workflow_stage: str = "CURRENT_CANDIDATES_BACKFILL_PLAN_READY",
    health_status: str = "PASS",
    selected_date_count: int = 8,
    first_signal_date: str = "2024-04-02",
    last_signal_date: str = "2024-05-06",
    warmup_trading_days: int = 60,
    warmup_feasible_count: int = 8,
    forward_1d_available_count: int = 8,
    forward_3d_available_count: int = 8,
    forward_5d_available_count: int = 8,
    forward_10d_available_count: int = 8,
    legacy_plan_count: int = 0,
    stale_plan_warning_count: int = 0,
    active_plan_issue_count: int = 0,
    active_plan_error_count: int = 0,
    legacy_missing_warmup_count: int = 0,
    latest_plan_is_warmup_aware: bool = True,
    warning_count: int = 0,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:39:30",
) -> Path:
    folder = root / "current_candidates_backfill_plan" / "status" / f"status-{plan_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "current_candidates_backfill_plan_status_report.md"
    status_csv = folder / "current_candidates_backfill_plan_status.csv"
    summary_csv = folder / "current_candidates_backfill_plan_status_summary.csv"
    metadata_path = folder / "metadata.json"
    plan_report = (
        root / "current_candidates_backfill_plan" / plan_id / "current_candidates_backfill_plan_report.md"
    )
    next_action = (
        "Repair current-candidates backfill plan artifacts before any backfill execution."
        if status == "FAIL"
        else "Review the backfill plan, source policy, warmup coverage, and forward horizons before candidate generation."
    )
    report.write_text(
        "Plan-only status. No current-candidates generation, live trading, broker API, order placement, message delivery, or network/API call was invoked.",
        encoding="utf-8",
    )
    plan_report.parent.mkdir(parents=True, exist_ok=True)
    plan_report.write_text("Plan-only artifact. It does not generate candidates or forward labels.", encoding="utf-8")
    pd.DataFrame(
        [
            {
                "component": "CURRENT_CANDIDATES_BACKFILL_PLAN",
                "status": "READY" if status != "FAIL" else "FAIL",
                "latest_artifact_id": plan_id,
                "selected_date_count": selected_date_count,
                "warning_count": 0,
                "error_count": 0,
                "issue_count": 0,
            },
            {
                "component": "CURRENT_CANDIDATES_BACKFILL_PLAN_HEALTH",
                "status": health_status,
                "latest_artifact_id": "backfill-plan-health-a",
                "selected_date_count": selected_date_count,
                "warning_count": warning_count,
                "error_count": error_count,
                "issue_count": warning_count + error_count,
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "latest_plan_id": plan_id,
                "status": status,
                "workflow_stage": workflow_stage,
                "health_status": health_status,
                "selected_date_count": selected_date_count,
                "first_signal_date": first_signal_date,
                "last_signal_date": last_signal_date,
                "warmup_trading_days": warmup_trading_days,
                "warmup_feasible_count": warmup_feasible_count,
                "forward_1d_available_count": forward_1d_available_count,
                "forward_3d_available_count": forward_3d_available_count,
                "forward_5d_available_count": forward_5d_available_count,
                "forward_10d_available_count": forward_10d_available_count,
                "legacy_plan_count": legacy_plan_count,
                "stale_plan_warning_count": stale_plan_warning_count,
                "active_plan_issue_count": active_plan_issue_count,
                "active_plan_error_count": active_plan_error_count,
                "legacy_missing_warmup_count": legacy_missing_warmup_count,
                "latest_plan_is_warmup_aware": latest_plan_is_warmup_aware,
                "report_path": str(plan_report),
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{plan_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_plan_id": plan_id,
            "health_status": health_status,
            "selected_date_count": selected_date_count,
            "next_manual_action": next_action,
            "warnings": ["Backfill plan health warnings are present."] if warning_count else [],
            "output_files": {
                "current_candidates_backfill_plan_status_report": str(report),
                "current_candidates_backfill_plan_status_csv": str(status_csv),
                "current_candidates_backfill_plan_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "current_candidates_executed": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "order_placement_enabled": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "network_api_called": False,
        },
    )
    return folder


def _current_candidates_backfill_execution_manifest_status(
    root: Path,
    *,
    execution_manifest_id: str = "manifest-a",
    plan_id: str = "plan-a",
    status: str = "WARN",
    workflow_stage: str = "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_BLOCKED",
    health_status: str = "PASS",
    row_count: int = 8,
    ready_count: int = 0,
    blocked_count: int = 8,
    blocked_missing_snapshot_count: int = 0,
    blocked_snapshot_quality_count: int = 0,
    blocked_universe_as_of_count: int = 8,
    blocked_plan_infeasible_count: int = 0,
    reviewed_execution_required_count: int = 8,
    warning_count: int = 1,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:39:45",
) -> Path:
    folder = root / "current_candidates_backfill_execution_manifest" / "status" / f"status-{execution_manifest_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "current_candidates_backfill_execution_manifest_status_report.md"
    status_csv = folder / "current_candidates_backfill_execution_manifest_status.csv"
    summary_csv = folder / "current_candidates_backfill_execution_manifest_status_summary.csv"
    metadata_path = folder / "metadata.json"
    manifest_report = (
        root
        / "current_candidates_backfill_execution_manifest"
        / execution_manifest_id
        / "current_candidates_backfill_execution_manifest_report.md"
    )
    next_action = (
        "Repair execution manifest artifacts before reviewed candidate generation."
        if status == "FAIL"
        else "Review READY_FOR_REVIEW signal dates manually before any separate candidate generation step."
        if workflow_stage == "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_READY_FOR_REVIEW"
        else "Resolve blocked signal-date inputs before candidate generation; no current-candidates were run."
    )
    report.write_text(
        "Manifest-only status. No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, or network/API call was invoked.",
        encoding="utf-8",
    )
    manifest_report.parent.mkdir(parents=True, exist_ok=True)
    manifest_report.write_text(
        "Execution readiness manifest only. It does not generate candidates, build snapshots, or compute forward labels.",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "component": "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST",
                "status": "WARN" if blocked_count else ("READY" if status != "FAIL" else "FAIL"),
                "latest_artifact_id": execution_manifest_id,
                "row_count": row_count,
                "ready_count": ready_count,
                "blocked_count": blocked_count,
                "warning_count": warning_count if status != "PASS" else 0,
                "error_count": 0,
                "issue_count": warning_count if status != "PASS" else 0,
            },
            {
                "component": "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_HEALTH",
                "status": health_status,
                "latest_artifact_id": "execution-manifest-health-a",
                "row_count": row_count,
                "ready_count": ready_count,
                "blocked_count": blocked_count,
                "warning_count": 0 if health_status == "PASS" else warning_count,
                "error_count": error_count,
                "issue_count": error_count + (0 if health_status == "PASS" else warning_count),
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "latest_execution_manifest_id": execution_manifest_id,
                "plan_id": plan_id,
                "status": status,
                "workflow_stage": workflow_stage,
                "health_status": health_status,
                "row_count": row_count,
                "ready_count": ready_count,
                "blocked_count": blocked_count,
                "blocked_missing_snapshot_count": blocked_missing_snapshot_count,
                "blocked_snapshot_quality_count": blocked_snapshot_quality_count,
                "blocked_universe_as_of_count": blocked_universe_as_of_count,
                "blocked_plan_infeasible_count": blocked_plan_infeasible_count,
                "reviewed_execution_required_count": reviewed_execution_required_count,
                "report_path": str(manifest_report),
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{execution_manifest_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_execution_manifest_id": execution_manifest_id,
            "plan_id": plan_id,
            "health_status": health_status,
            "row_count": row_count,
            "ready_count": ready_count,
            "blocked_count": blocked_count,
            "next_manual_action": next_action,
            "warnings": ["Latest execution manifest has blocked signal-date rows."] if warning_count else [],
            "output_files": {
                "current_candidates_backfill_execution_manifest_status_report": str(report),
                "current_candidates_backfill_execution_manifest_status_csv": str(status_csv),
                "current_candidates_backfill_execution_manifest_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "order_placement_enabled": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "network_api_called": False,
            "execution_manifest_artifacts_only": True,
        },
    )
    return folder


def _pit_universe_overlay_plan_status(
    root: Path,
    *,
    overlay_plan_id: str = "overlay-a",
    status: str = "WARN",
    workflow_stage: str = "PIT_UNIVERSE_OVERLAY_PLAN_NEEDS_REVIEW",
    health_status: str = "PASS",
    row_count: int = 72,
    signal_date_count: int = 8,
    symbol_count: int = 9,
    needs_manual_review_count: int = 72,
    valid_for_signal_date_count: int = 0,
    survivorship_bias_warning_count: int = 72,
    warning_count: int = 1,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:49:45",
) -> Path:
    folder = root / "point_in_time_universe_overlay_plan" / "status" / f"status-{overlay_plan_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "point_in_time_universe_overlay_plan_status_report.md"
    status_csv = folder / "point_in_time_universe_overlay_plan_status.csv"
    summary_csv = folder / "point_in_time_universe_overlay_plan_status_summary.csv"
    metadata_path = folder / "metadata.json"
    overlay_report = (
        root
        / "point_in_time_universe_overlay_plan"
        / overlay_plan_id
        / "point_in_time_universe_overlay_plan_report.md"
    )
    next_action = (
        "Repair PIT universe overlay plan artifacts before manual PIT universe review."
        if status == "FAIL"
        else "Review PIT-valid overlay rows before any separate snapshot preparation step."
        if workflow_stage == "PIT_UNIVERSE_OVERLAY_PLAN_READY_FOR_REVIEW"
        else "Complete manual review for point-in-time universe rows; generated rows are not valid for execution yet."
    )
    report.write_text(
        "Plan-only PIT universe overlay status. No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM API, or external API was invoked.",
        encoding="utf-8",
    )
    overlay_report.parent.mkdir(parents=True, exist_ok=True)
    overlay_report.write_text(
        "PIT universe overlay plan only. NEEDS_MANUAL_REVIEW rows are not valid point-in-time universe rows yet.",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "component": "PIT_UNIVERSE_OVERLAY_PLAN",
                "status": "NEEDS_REVIEW" if needs_manual_review_count else ("READY" if status != "FAIL" else "FAIL"),
                "latest_artifact_id": overlay_plan_id,
                "row_count": row_count,
                "needs_manual_review_count": needs_manual_review_count,
                "valid_for_signal_date_count": valid_for_signal_date_count,
                "survivorship_bias_warning_count": survivorship_bias_warning_count,
                "warning_count": warning_count if status != "PASS" else 0,
                "error_count": 0,
                "issue_count": warning_count if status != "PASS" else 0,
            },
            {
                "component": "PIT_UNIVERSE_OVERLAY_PLAN_HEALTH",
                "status": health_status,
                "latest_artifact_id": "pit-overlay-health-a",
                "row_count": row_count,
                "needs_manual_review_count": needs_manual_review_count,
                "valid_for_signal_date_count": valid_for_signal_date_count,
                "survivorship_bias_warning_count": survivorship_bias_warning_count,
                "warning_count": 0 if health_status == "PASS" else warning_count,
                "error_count": error_count,
                "issue_count": error_count + (0 if health_status == "PASS" else warning_count),
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "latest_overlay_plan_id": overlay_plan_id,
                "status": status,
                "workflow_stage": workflow_stage,
                "health_status": health_status,
                "row_count": row_count,
                "signal_date_count": signal_date_count,
                "symbol_count": symbol_count,
                "needs_manual_review_count": needs_manual_review_count,
                "valid_for_signal_date_count": valid_for_signal_date_count,
                "survivorship_bias_warning_count": survivorship_bias_warning_count,
                "report_path": str(overlay_report),
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{overlay_plan_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_overlay_plan_id": overlay_plan_id,
            "health_status": health_status,
            "row_count": row_count,
            "needs_manual_review_count": needs_manual_review_count,
            "valid_for_signal_date_count": valid_for_signal_date_count,
            "next_manual_action": next_action,
            "warnings": ["Latest PIT universe overlay plan still requires manual review."] if warning_count else [],
            "output_files": {
                "point_in_time_universe_overlay_plan_status_report": str(report),
                "point_in_time_universe_overlay_plan_status_csv": str(status_csv),
                "point_in_time_universe_overlay_plan_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "order_placement_enabled": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "network_api_called": False,
            "llm_api_called": False,
            "pit_universe_overlay_plan_artifacts_only": True,
        },
    )
    return folder


def _pit_universe_overlay_review_status(
    root: Path,
    *,
    review_id: str = "review-a",
    status: str = "WARN",
    workflow_stage: str = "PIT_UNIVERSE_OVERLAY_REVIEW_NEEDS_MORE_EVIDENCE",
    health_status: str = "PASS",
    approved_count: int = 1,
    valid_for_signal_date_count: int = 1,
    needs_more_evidence_count: int = 1,
    unresolved_survivorship_warning_count: int = 1,
    warning_count: int = 1,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:52:45",
) -> Path:
    folder = root / "point_in_time_universe_overlay_review" / "status" / f"status-{review_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "pit_universe_overlay_review_status_report.md"
    status_csv = folder / "pit_universe_overlay_review_status.csv"
    summary_csv = folder / "pit_universe_overlay_review_status_summary.csv"
    metadata_path = folder / "metadata.json"
    review_report = (
        root
        / "point_in_time_universe_overlay_review"
        / review_id
        / "pit_universe_overlay_review_report.md"
    )
    next_action = (
        "Repair PIT universe overlay review artifacts before snapshot preparation planning."
        if status == "FAIL"
        else "Review approved PIT universe rows before separate snapshot preparation planning."
        if workflow_stage
        in {
            "PIT_UNIVERSE_OVERLAY_REVIEW_HAS_APPROVED_ROWS",
            "PIT_UNIVERSE_OVERLAY_REVIEW_ALL_APPROVED",
        }
        else "Resolve PIT universe overlay rows that need more evidence before snapshot preparation planning."
    )
    report.write_text(
        "Review-only PIT universe overlay status. No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM API, or external API was invoked.",
        encoding="utf-8",
    )
    review_report.parent.mkdir(parents=True, exist_ok=True)
    review_report.write_text(
        "Reviewed PIT universe overlay evidence only. Approved rows do not imply candidate generation.",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "component": "PIT_UNIVERSE_OVERLAY_REVIEW",
                "status": "NEEDS_MORE_EVIDENCE"
                if needs_more_evidence_count
                else ("HAS_APPROVED_ROWS" if approved_count else "WARN"),
                "latest_artifact_id": review_id,
                "approved_count": approved_count,
                "valid_for_signal_date_count": valid_for_signal_date_count,
                "needs_more_evidence_count": needs_more_evidence_count,
                "unresolved_survivorship_warning_count": unresolved_survivorship_warning_count,
                "warning_count": warning_count if status != "PASS" else 0,
                "error_count": 0,
                "issue_count": warning_count if status != "PASS" else 0,
            },
            {
                "component": "PIT_UNIVERSE_OVERLAY_REVIEW_HEALTH",
                "status": health_status,
                "latest_artifact_id": "pit-overlay-review-health-a",
                "approved_count": approved_count,
                "valid_for_signal_date_count": valid_for_signal_date_count,
                "needs_more_evidence_count": needs_more_evidence_count,
                "unresolved_survivorship_warning_count": unresolved_survivorship_warning_count,
                "warning_count": 0 if health_status == "PASS" else warning_count,
                "error_count": error_count,
                "issue_count": error_count + (0 if health_status == "PASS" else warning_count),
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "latest_review_id": review_id,
                "status": status,
                "workflow_stage": workflow_stage,
                "health_status": health_status,
                "approved_count": approved_count,
                "valid_for_signal_date_count": valid_for_signal_date_count,
                "needs_more_evidence_count": needs_more_evidence_count,
                "unresolved_survivorship_warning_count": unresolved_survivorship_warning_count,
                "report_path": str(review_report),
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{review_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_review_id": review_id,
            "health_status": health_status,
            "approved_count": approved_count,
            "valid_for_signal_date_count": valid_for_signal_date_count,
            "needs_more_evidence_count": needs_more_evidence_count,
            "unresolved_survivorship_warning_count": unresolved_survivorship_warning_count,
            "next_manual_action": next_action,
            "warnings": ["Latest PIT universe overlay review still needs more evidence."] if warning_count else [],
            "output_files": {
                "pit_universe_overlay_review_status_report": str(report),
                "pit_universe_overlay_review_status_csv": str(status_csv),
                "pit_universe_overlay_review_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "order_placement_enabled": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "network_api_called": False,
            "llm_api_called": False,
            "pit_universe_overlay_review_artifacts_only": True,
        },
    )
    return folder


def _pit_universe_overlay_export_readiness_status(
    root: Path,
    *,
    export_readiness_id: str = "export-a",
    review_id: str = "review-a",
    status: str = "WARN",
    workflow_stage: str = "PIT_UNIVERSE_EXPORT_BLOCKED_NO_APPROVED_ROWS",
    health_status: str = "PASS",
    approved_count: int = 0,
    export_ready_count: int = 0,
    blocked_count: int = 72,
    no_approved_rows: bool = True,
    missing_required_columns_count: int = 72,
    unresolved_survivorship_warning_count: int = 72,
    warning_count: int = 1,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:53:45",
) -> Path:
    folder = root / "point_in_time_universe_overlay_export_readiness" / "status" / f"status-{export_readiness_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "pit_universe_overlay_export_readiness_status_report.md"
    status_csv = folder / "pit_universe_overlay_export_readiness_status.csv"
    summary_csv = folder / "pit_universe_overlay_export_readiness_status_summary.csv"
    metadata_path = folder / "metadata.json"
    readiness_report = (
        root
        / "point_in_time_universe_overlay_export_readiness"
        / export_readiness_id
        / "pit_universe_overlay_export_readiness_report.md"
    )
    next_action = (
        "Repair PIT universe overlay export-readiness artifacts before any universe export planning."
        if status == "FAIL"
        else "Review export-ready PIT universe rows before a separate explicit universe export workflow."
        if workflow_stage == "PIT_UNIVERSE_EXPORT_READY_FOR_DRY_RUN"
        else "Approve PIT universe rows with evidence before export readiness can proceed."
        if workflow_stage == "PIT_UNIVERSE_EXPORT_BLOCKED_NO_APPROVED_ROWS"
        else "Resolve PIT universe review evidence and required universe columns before export readiness can proceed."
    )
    report.write_text(
        "Export-readiness status only. No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked.",
        encoding="utf-8",
    )
    readiness_report.parent.mkdir(parents=True, exist_ok=True)
    readiness_report.write_text(
        "PIT universe overlay export readiness only. No usable universe export occurred.",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "component": "PIT_UNIVERSE_EXPORT_READINESS",
                "status": "BLOCKED_NO_APPROVED_ROWS" if no_approved_rows else "READY_FOR_DRY_RUN",
                "latest_artifact_id": export_readiness_id,
                "review_id": review_id,
                "approved_count": approved_count,
                "export_ready_count": export_ready_count,
                "blocked_count": blocked_count,
                "no_approved_rows": no_approved_rows,
                "missing_required_columns_count": missing_required_columns_count,
                "unresolved_survivorship_warning_count": unresolved_survivorship_warning_count,
                "warning_count": warning_count if status != "PASS" else 0,
                "error_count": 0,
                "issue_count": warning_count if status != "PASS" else 0,
            },
            {
                "component": "PIT_UNIVERSE_EXPORT_READINESS_HEALTH",
                "status": health_status,
                "latest_artifact_id": "pit-export-readiness-health-a",
                "review_id": review_id,
                "approved_count": approved_count,
                "export_ready_count": export_ready_count,
                "blocked_count": blocked_count,
                "no_approved_rows": no_approved_rows,
                "missing_required_columns_count": missing_required_columns_count,
                "unresolved_survivorship_warning_count": unresolved_survivorship_warning_count,
                "warning_count": 0 if health_status == "PASS" else warning_count,
                "error_count": error_count,
                "issue_count": error_count + (0 if health_status == "PASS" else warning_count),
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "latest_export_readiness_id": export_readiness_id,
                "status": status,
                "workflow_stage": workflow_stage,
                "health_status": health_status,
                "review_id": review_id,
                "approved_count": approved_count,
                "export_ready_count": export_ready_count,
                "blocked_count": blocked_count,
                "no_approved_rows": no_approved_rows,
                "missing_required_columns_count": missing_required_columns_count,
                "unresolved_survivorship_warning_count": unresolved_survivorship_warning_count,
                "report_path": str(readiness_report),
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{export_readiness_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_export_readiness_id": export_readiness_id,
            "health_status": health_status,
            "review_id": review_id,
            "approved_count": approved_count,
            "export_ready_count": export_ready_count,
            "blocked_count": blocked_count,
            "no_approved_rows": no_approved_rows,
            "missing_required_columns_count": missing_required_columns_count,
            "unresolved_survivorship_warning_count": unresolved_survivorship_warning_count,
            "next_manual_action": next_action,
            "warnings": ["Latest PIT universe overlay export readiness is blocked."] if warning_count else [],
            "output_files": {
                "pit_universe_overlay_export_readiness_status_report": str(report),
                "pit_universe_overlay_export_readiness_status_csv": str(status_csv),
                "pit_universe_overlay_export_readiness_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "universe_exported": False,
            "would_write_data_raw": False,
            "would_write_data_processed": False,
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "order_placement_enabled": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "network_api_called": False,
            "llm_api_called": False,
            "pit_universe_overlay_export_readiness_artifacts_only": True,
        },
    )
    return folder


def _pit_universe_export_staging_status(
    root: Path,
    *,
    staging_id: str = "stage-a",
    export_readiness_id: str = "export-a",
    review_id: str = "review-a",
    status: str = "WARN",
    workflow_stage: str = "PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS",
    health_status: str = "PASS",
    export_ready_input_count: int = 0,
    staged_row_count: int = 0,
    blocked_count: int = 72,
    source_is_diagnostic: bool = False,
    no_ready_rows: bool = True,
    warning_count: int = 1,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:54:10",
) -> Path:
    folder = root / "point_in_time_universe_export_staging" / "status" / f"status-{staging_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "pit_universe_export_staging_status_report.md"
    status_csv = folder / "pit_universe_export_staging_status.csv"
    summary_csv = folder / "pit_universe_export_staging_status_summary.csv"
    metadata_path = folder / "metadata.json"
    staging_report = (
        root
        / "point_in_time_universe_export_staging"
        / staging_id
        / "pit_universe_export_staging_report.md"
    )
    next_action = (
        "Repair PIT universe export staging artifacts before any accepted export planning."
        if status == "FAIL"
        else "Review staged PIT universe previews before any separate accepted export workflow."
        if workflow_stage == "PIT_UNIVERSE_EXPORT_STAGING_READY_FOR_REVIEW"
        else "Use only active non-diagnostic export-readiness artifacts for staging."
        if workflow_stage == "PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_DIAGNOSTIC_SOURCE"
        else "Complete PIT universe review evidence before staging can create previews."
    )
    report.write_text(
        "PIT universe export staging status only. No data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, network/API, LLM/API, or cache mutation was invoked.",
        encoding="utf-8",
    )
    staging_report.parent.mkdir(parents=True, exist_ok=True)
    staging_report.write_text("PIT universe export staging preview only.", encoding="utf-8")
    pd.DataFrame(
        [
            {
                "component": "PIT_UNIVERSE_EXPORT_STAGING",
                "status": "BLOCKED_NO_READY_ROWS" if no_ready_rows else "READY_FOR_REVIEW",
                "latest_artifact_id": staging_id,
                "export_readiness_id": export_readiness_id,
                "review_id": review_id,
                "export_ready_input_count": export_ready_input_count,
                "staged_row_count": staged_row_count,
                "blocked_count": blocked_count,
                "source_is_diagnostic": source_is_diagnostic,
                "no_ready_rows": no_ready_rows,
                "warning_count": warning_count if status != "PASS" else 0,
                "error_count": 0,
                "issue_count": warning_count if status != "PASS" else 0,
            },
            {
                "component": "PIT_UNIVERSE_EXPORT_STAGING_HEALTH",
                "status": health_status,
                "latest_artifact_id": "pit-export-staging-health-a",
                "warning_count": 0 if health_status == "PASS" else warning_count,
                "error_count": error_count,
                "issue_count": error_count + (0 if health_status == "PASS" else warning_count),
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "latest_staging_id": staging_id,
                "status": status,
                "workflow_stage": workflow_stage,
                "health_status": health_status,
                "export_readiness_id": export_readiness_id,
                "review_id": review_id,
                "export_ready_input_count": export_ready_input_count,
                "staged_row_count": staged_row_count,
                "blocked_count": blocked_count,
                "source_is_diagnostic": source_is_diagnostic,
                "no_ready_rows": no_ready_rows,
                "report_path": str(staging_report),
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{staging_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_staging_id": staging_id,
            "health_status": health_status,
            "export_readiness_id": export_readiness_id,
            "review_id": review_id,
            "export_ready_input_count": export_ready_input_count,
            "staged_row_count": staged_row_count,
            "blocked_count": blocked_count,
            "source_is_diagnostic": source_is_diagnostic,
            "no_ready_rows": no_ready_rows,
            "next_manual_action": next_action,
            "warnings": ["Latest PIT universe export staging is blocked."] if warning_count else [],
            "output_files": {
                "pit_universe_export_staging_status_report": str(report),
                "pit_universe_export_staging_status_csv": str(status_csv),
                "pit_universe_export_staging_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "would_write_data_raw": False,
            "would_write_data_processed": False,
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "order_placement_enabled": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "network_api_called": False,
            "llm_api_called": False,
            "pit_universe_export_staging_artifacts_only": True,
        },
    )
    return folder


def _pit_universe_evidence_completion_helper_status(
    root: Path,
    *,
    helper_id: str = "helper-a",
    review_id: str = "review-a",
    status: str = "WARN",
    workflow_stage: str = "PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_NEEDS_REVIEW",
    health_status: str = "PASS",
    row_count: int = 72,
    needs_evidence_count: int = 72,
    rows_with_base_hints_count: int = 72,
    future_dated_hint_count: int = 72,
    authoritative_hint_count: int = 0,
    warning_count: int = 1,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:54:45",
) -> Path:
    folder = (
        root
        / "point_in_time_universe_evidence_completion_helper"
        / "status"
        / f"status-{helper_id}"
    )
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "pit_universe_evidence_completion_helper_status_report.md"
    status_csv = folder / "pit_universe_evidence_completion_helper_status.csv"
    summary_csv = folder / "pit_universe_evidence_completion_helper_status_summary.csv"
    metadata_path = folder / "metadata.json"
    helper_report = (
        root
        / "point_in_time_universe_evidence_completion_helper"
        / helper_id
        / "pit_universe_evidence_gap_report.md"
    )
    next_action = (
        "Repair PIT universe evidence completion helper artifacts before using completion templates."
        if status == "FAIL"
        else "Review PIT universe evidence completion helper health warnings before using completion templates."
        if workflow_stage == "PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_HEALTH_WARN"
        else "Complete PIT universe evidence fields manually; helper hints are non-authoritative and do not approve rows."
    )
    report.write_text(
        "Evidence completion helper status only. No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked.",
        encoding="utf-8",
    )
    helper_report.parent.mkdir(parents=True, exist_ok=True)
    helper_report.write_text(
        "PIT universe evidence completion helper only. No approvals or usable universe export occurred.",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "component": "PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER",
                "status": "NEEDS_REVIEW",
                "latest_artifact_id": helper_id,
                "review_id": review_id,
                "row_count": row_count,
                "needs_evidence_count": needs_evidence_count,
                "rows_with_base_hints_count": rows_with_base_hints_count,
                "future_dated_hint_count": future_dated_hint_count,
                "authoritative_hint_count": authoritative_hint_count,
                "warning_count": warning_count if status != "PASS" else 0,
                "error_count": 0,
                "issue_count": warning_count if status != "PASS" else 0,
            },
            {
                "component": "PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_HEALTH",
                "status": health_status,
                "latest_artifact_id": "pit-evidence-helper-health-a",
                "review_id": review_id,
                "row_count": row_count,
                "needs_evidence_count": needs_evidence_count,
                "rows_with_base_hints_count": rows_with_base_hints_count,
                "future_dated_hint_count": future_dated_hint_count,
                "authoritative_hint_count": authoritative_hint_count,
                "warning_count": 0 if health_status == "PASS" else warning_count,
                "error_count": error_count,
                "issue_count": error_count + (0 if health_status == "PASS" else warning_count),
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "latest_helper_id": helper_id,
                "status": status,
                "workflow_stage": workflow_stage,
                "health_status": health_status,
                "review_id": review_id,
                "row_count": row_count,
                "needs_evidence_count": needs_evidence_count,
                "rows_with_base_hints_count": rows_with_base_hints_count,
                "future_dated_hint_count": future_dated_hint_count,
                "authoritative_hint_count": authoritative_hint_count,
                "report_path": str(helper_report),
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{helper_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_helper_id": helper_id,
            "health_status": health_status,
            "review_id": review_id,
            "row_count": row_count,
            "needs_evidence_count": needs_evidence_count,
            "rows_with_base_hints_count": rows_with_base_hints_count,
            "future_dated_hint_count": future_dated_hint_count,
            "authoritative_hint_count": authoritative_hint_count,
            "next_manual_action": next_action,
            "warnings": ["Latest PIT universe evidence helper rows still need evidence."] if warning_count else [],
            "output_files": {
                "pit_universe_evidence_completion_helper_status_report": str(report),
                "pit_universe_evidence_completion_helper_status_csv": str(status_csv),
                "pit_universe_evidence_completion_helper_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "universe_exported": False,
            "would_write_data_raw": False,
            "would_write_data_processed": False,
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "order_placement_enabled": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "network_api_called": False,
            "llm_api_called": False,
            "pit_universe_evidence_completion_helper_artifacts_only": True,
        },
    )
    return folder


def _pit_universe_evidence_review_worklist_status(
    root: Path,
    *,
    worklist_id: str = "worklist-a",
    review_id: str = "review-a",
    helper_id: str = "helper-a",
    status: str = "WARN",
    workflow_stage: str = "PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_NEEDS_REVIEW",
    health_status: str = "PASS",
    row_count: int = 72,
    symbol_count: int = 9,
    signal_date_count: int = 8,
    needs_evidence_count: int = 72,
    future_dated_hint_count: int = 72,
    authoritative_hint_count: int = 0,
    warning_count: int = 1,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:55:00",
) -> Path:
    folder = root / "point_in_time_universe_evidence_review_worklist" / "status" / f"status-{worklist_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "pit_universe_evidence_review_worklist_status_report.md"
    status_csv = folder / "pit_universe_evidence_review_worklist_status.csv"
    summary_csv = folder / "pit_universe_evidence_review_worklist_status_summary.csv"
    metadata_path = folder / "metadata.json"
    worklist_report = (
        root
        / "point_in_time_universe_evidence_review_worklist"
        / worklist_id
        / "pit_universe_evidence_review_worklist_report.md"
    )
    next_action = (
        "Repair PIT universe evidence review worklist artifacts before using reviewer templates."
        if status == "FAIL"
        else "Review PIT universe evidence review worklist health warnings before using reviewer templates."
        if workflow_stage == "PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_HEALTH_WARN"
        else "Complete PIT universe evidence fields manually; worklist hints are non-authoritative and do not approve rows."
    )
    report.write_text(
        "Evidence review worklist status only. No approval, universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked.",
        encoding="utf-8",
    )
    worklist_report.parent.mkdir(parents=True, exist_ok=True)
    worklist_report.write_text(
        "PIT universe evidence review worklist only. No approvals or usable universe export occurred.",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "component": "PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST",
                "status": "NEEDS_REVIEW",
                "latest_artifact_id": worklist_id,
                "review_id": review_id,
                "helper_id": helper_id,
                "row_count": row_count,
                "symbol_count": symbol_count,
                "signal_date_count": signal_date_count,
                "needs_evidence_count": needs_evidence_count,
                "future_dated_hint_count": future_dated_hint_count,
                "authoritative_hint_count": authoritative_hint_count,
                "warning_count": warning_count if status != "PASS" else 0,
                "error_count": 0,
                "issue_count": warning_count if status != "PASS" else 0,
            },
            {
                "component": "PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_HEALTH",
                "status": health_status,
                "latest_artifact_id": "pit-evidence-worklist-health-a",
                "review_id": review_id,
                "helper_id": helper_id,
                "row_count": row_count,
                "symbol_count": symbol_count,
                "signal_date_count": signal_date_count,
                "needs_evidence_count": needs_evidence_count,
                "future_dated_hint_count": future_dated_hint_count,
                "authoritative_hint_count": authoritative_hint_count,
                "warning_count": 0 if health_status == "PASS" else warning_count,
                "error_count": error_count,
                "issue_count": error_count + (0 if health_status == "PASS" else warning_count),
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "latest_worklist_id": worklist_id,
                "status": status,
                "workflow_stage": workflow_stage,
                "health_status": health_status,
                "review_id": review_id,
                "helper_id": helper_id,
                "row_count": row_count,
                "symbol_count": symbol_count,
                "signal_date_count": signal_date_count,
                "needs_evidence_count": needs_evidence_count,
                "future_dated_hint_count": future_dated_hint_count,
                "authoritative_hint_count": authoritative_hint_count,
                "report_path": str(worklist_report),
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{worklist_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_worklist_id": worklist_id,
            "health_status": health_status,
            "review_id": review_id,
            "helper_id": helper_id,
            "row_count": row_count,
            "symbol_count": symbol_count,
            "signal_date_count": signal_date_count,
            "needs_evidence_count": needs_evidence_count,
            "future_dated_hint_count": future_dated_hint_count,
            "authoritative_hint_count": authoritative_hint_count,
            "next_manual_action": next_action,
            "warnings": ["Latest PIT universe evidence review worklist rows still need evidence."]
            if warning_count
            else [],
            "output_files": {
                "pit_universe_evidence_review_worklist_status_report": str(report),
                "pit_universe_evidence_review_worklist_status_csv": str(status_csv),
                "pit_universe_evidence_review_worklist_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "approved_rows_created": False,
            "universe_exported": False,
            "would_write_data_raw": False,
            "would_write_data_processed": False,
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "order_placement_enabled": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "network_api_called": False,
            "llm_api_called": False,
            "pit_universe_evidence_review_worklist_artifacts_only": True,
        },
    )
    return folder


def _pit_universe_evidence_update_ingestion_status(
    root: Path,
    *,
    ingestion_id: str = "ingest-a",
    status: str = "WARN",
    workflow_stage: str = "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_NO_READY_UPDATES",
    health_status: str = "PASS",
    row_count: int = 72,
    ready_for_review_update_count: int = 0,
    blocked_count: int = 72,
    approval_requested_count: int = 0,
    approved_ready_count: int = 0,
    duplicate_identity_count: int = 0,
    suggested_copy_risk_count: int = 0,
    warning_count: int = 1,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T16:05:00",
) -> Path:
    folder = root / "point_in_time_universe_evidence_update_ingestion" / "status" / f"status-{ingestion_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "pit_universe_evidence_update_ingestion_status_report.md"
    status_csv = folder / "pit_universe_evidence_update_ingestion_status.csv"
    summary_csv = folder / "pit_universe_evidence_update_ingestion_status_summary.csv"
    metadata_path = folder / "metadata.json"
    ingestion_report = (
        root
        / "point_in_time_universe_evidence_update_ingestion"
        / ingestion_id
        / "pit_universe_evidence_update_ingestion_report.md"
    )
    review_updates = (
        root
        / "point_in_time_universe_evidence_update_ingestion"
        / ingestion_id
        / "pit_universe_review_updates.csv"
    )
    ingestion_report.parent.mkdir(parents=True, exist_ok=True)
    ingestion_report.write_text("PIT universe evidence update ingestion report only.", encoding="utf-8")
    review_updates.write_text("signal_date,symbol,universe_name,review_status\n", encoding="utf-8")
    next_action = (
        "Repair PIT universe evidence update ingestion artifacts before using clean review updates."
        if status == "FAIL"
        else "Reviewer has not completed usable PIT universe evidence update rows yet."
        if ready_for_review_update_count == 0
        else "Review clean review_updates artifact manually before a separate pit-universe-overlay-review run."
    )
    report.write_text(
        "Evidence update ingestion status only. No approval applied, universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked.",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "component": "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION",
                "status": "WARN" if ready_for_review_update_count == 0 else "READY",
                "latest_artifact_id": ingestion_id,
                "row_count": row_count,
                "ready_for_review_update_count": ready_for_review_update_count,
                "blocked_count": blocked_count,
                "approval_requested_count": approval_requested_count,
                "approved_ready_count": approved_ready_count,
                "duplicate_identity_count": duplicate_identity_count,
                "suggested_copy_risk_count": suggested_copy_risk_count,
                "warning_count": warning_count if status != "PASS" else 0,
                "error_count": 0,
                "issue_count": warning_count if status != "PASS" else 0,
            },
            {
                "component": "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_HEALTH",
                "status": health_status,
                "latest_artifact_id": "pit-evidence-update-ingestion-health-a",
                "warning_count": 0 if health_status == "PASS" else warning_count,
                "error_count": error_count,
                "issue_count": error_count + (0 if health_status == "PASS" else warning_count),
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "latest_ingestion_id": ingestion_id,
                "status": status,
                "workflow_stage": workflow_stage,
                "health_status": health_status,
                "row_count": row_count,
                "ready_for_review_update_count": ready_for_review_update_count,
                "blocked_count": blocked_count,
                "approval_requested_count": approval_requested_count,
                "approved_ready_count": approved_ready_count,
                "duplicate_identity_count": duplicate_identity_count,
                "suggested_copy_risk_count": suggested_copy_risk_count,
                "report_path": str(ingestion_report),
                "review_updates_path": str(review_updates),
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{ingestion_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_ingestion_id": ingestion_id,
            "health_status": health_status,
            "row_count": row_count,
            "ready_for_review_update_count": ready_for_review_update_count,
            "blocked_count": blocked_count,
            "approval_requested_count": approval_requested_count,
            "approved_ready_count": approved_ready_count,
            "duplicate_identity_count": duplicate_identity_count,
            "suggested_copy_risk_count": suggested_copy_risk_count,
            "next_manual_action": next_action,
            "output_files": {
                "pit_universe_evidence_update_ingestion_status_report": str(report),
                "pit_universe_evidence_update_ingestion_status_csv": str(status_csv),
                "pit_universe_evidence_update_ingestion_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "approval_applied": False,
            "universe_exported": False,
            "would_write_data_raw": False,
            "would_write_data_processed": False,
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "order_placement_enabled": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "network_api_called": False,
            "llm_api_called": False,
            "pit_universe_evidence_update_ingestion_artifacts_only": True,
        },
    )
    return folder


def _pit_evidence_checklist_validator_artifact(
    root: Path,
    *,
    validator_id: str = "validator-a",
    status: str = "WARN",
    row_count: int = 16,
    checklist_pass_count: int = 0,
    blocked_count: int = 16,
    stock_core_blocked_count: int = 8,
    etf_core_blocked_count: int = 8,
) -> Path:
    folder = root / "pit_evidence_checklist_validator" / validator_id
    folder.mkdir(parents=True, exist_ok=True)
    validation_csv = folder / "pit_evidence_checklist_validation.csv"
    summary_csv = folder / "pit_evidence_checklist_validation_summary.csv"
    missing_csv = folder / "missing_evidence_matrix.csv"
    preview_csv = folder / "approval_candidate_preview.csv"
    report = folder / "report.md"
    metadata = folder / "metadata.json"
    pd.DataFrame(
        [
            {
                "validator_id": validator_id,
                "signal_date": "2024-04-02",
                "symbol": "000001",
                "universe_name": "stock_core",
                "profile": "stock_core",
                "review_status": "NEEDS_MORE_EVIDENCE",
                "checklist_status": "CHECKLIST_BLOCKED_MISSING_EVIDENCE",
                "checklist_pass": False,
                "blocked": True,
                "blocker_reason": "missing evidence",
                "missing_required_fields": "is_active_evidence",
                "unacceptable_source_fields": "",
                "pit_timing_blocker": True,
                "survivorship_blocker": True,
                "stock_st_blocker": True,
                "no_approval_applied": True,
                "no_universe_export": True,
                "no_data_raw_write": True,
                "no_data_processed_write": True,
                "no_current_candidates_generated": True,
                "no_snapshot_built": True,
                "no_forward_labels": True,
                "no_live_trading": True,
                "no_broker_api": True,
                "no_order_placement": True,
                "no_message_sent": True,
                "checklist_validation_only": True,
            }
        ],
        columns=VALIDATION_COLUMNS,
    ).to_csv(validation_csv, index=False)
    pd.DataFrame(
        [
            {
                "validator_id": validator_id,
                "status": status,
                "row_count": row_count,
                "checklist_pass_count": checklist_pass_count,
                "blocked_count": blocked_count,
                "stock_core_blocked_count": stock_core_blocked_count,
                "etf_core_blocked_count": etf_core_blocked_count,
                "missing_evidence_count": blocked_count,
                "unacceptable_source_count": 0,
                "pit_timing_blocked_count": blocked_count,
                "survivorship_blocked_count": blocked_count,
                "stock_st_blocked_count": stock_core_blocked_count,
            }
        ],
        columns=SUMMARY_COLUMNS,
    ).to_csv(summary_csv, index=False)
    pd.DataFrame(
        [
            {
                "validator_id": validator_id,
                "signal_date": "2024-04-02",
                "symbol": "000001",
                "universe_name": "stock_core",
                "field_name": "is_active_evidence",
                "issue_code": "MISSING_REQUIRED_EVIDENCE",
                "issue_message": "is_active_evidence is required.",
                "acceptable_sources": "official",
                "notes": "",
            }
        ]
    ).to_csv(missing_csv, index=False)
    pd.DataFrame().to_csv(preview_csv, index=False)
    report.write_text("No approval applied. No universe export. No current-candidates were run.", encoding="utf-8")
    _write_json(
        metadata,
        {
            "validator_id": validator_id,
            "created_at": "2026-06-04T10:00:00+08:00",
            "status": status,
            "row_count": row_count,
            "checklist_pass_count": checklist_pass_count,
            "blocked_count": blocked_count,
            "stock_core_blocked_count": stock_core_blocked_count,
            "etf_core_blocked_count": etf_core_blocked_count,
            "output_files": {
                "validation_csv": str(validation_csv),
                "summary_csv": str(summary_csv),
                "missing_evidence_matrix": str(missing_csv),
                "approval_candidate_preview": str(preview_csv),
                "report": str(report),
                "metadata": str(metadata),
            },
            "no_approval_applied": True,
            "no_universe_export": True,
            "no_data_raw_write": True,
            "no_data_processed_write": True,
            "no_current_candidates_generated": True,
            "no_snapshot_built": True,
            "no_forward_labels": True,
            "no_live_trading": True,
            "no_broker_api": True,
            "no_order_placement": True,
            "no_message_sent": True,
            "checklist_validation_only": True,
            "would_write_data_raw": False,
            "would_write_data_processed": False,
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "order_placement_enabled": False,
            "message_sent": False,
        },
    )
    return folder


def _pit_evidence_policy_profile_comparison_artifact(
    root: Path,
    *,
    comparison_id: str = "comparison-a",
    status: str = "WARN",
    row_count: int = 16,
    strict_pass_count: int = 0,
    eod_low_budget_pass_count: int = 0,
    reviewed_no_hit_support_pass_count: int = 0,
    no_hit_context_supported_count: int = 0,
    reviewer_acceptance_required_count: int = 0,
    relaxed_blocker_count: int = 16,
    remaining_blocked_count: int = 16,
    created_at: str = "2026-06-04T16:10:00+08:00",
) -> Path:
    folder = root / "pit_evidence_policy_profile_comparison" / comparison_id
    folder.mkdir(parents=True, exist_ok=True)
    comparison_csv = folder / "pit_evidence_policy_profile_comparison.csv"
    summary_csv = folder / "pit_evidence_policy_profile_summary.csv"
    relaxed_csv = folder / "relaxed_blocker_matrix.csv"
    remaining_csv = folder / "remaining_blocker_matrix.csv"
    snapshot_csv = folder / "eod_post_close_policy_profile_snapshot.csv"
    report = folder / "report.md"
    metadata = folder / "metadata.json"
    pd.DataFrame(
        [
            {
                "comparison_id": comparison_id,
                "symbol": "000001",
                "signal_date": "2024-04-02",
                "recommended_future_universe": "stock_core",
                "profile_name": "EOD_POST_CLOSE_LOW_BUDGET_PIT",
                "strict_status": "CHECKLIST_BLOCKED_PIT_TIMING",
                "eod_low_budget_status": "EOD_LOW_BUDGET_BLOCKED",
                "strict_blockers": "PIT timing blocked; survivorship unresolved",
                "relaxed_blockers": "PIT_TIMING_BLOCKED",
                "remaining_blockers": "survivorship unresolved",
                "available_time": "2024-04-02 15:30:00",
                "decision_time": "2024-04-02 16:00:00",
                "available_time_within_decision_time": True,
                "same_day_market_cache_used_as_support": True,
                "active_context_supported_by_cache": True,
                "suspension_context_supported_by_cache": True,
                "not_delisted_still_required": True,
                "st_no_st_still_required": True,
                "survivorship_still_required": True,
                "checklist_pass_under_strict": False,
                "checklist_pass_under_eod_low_budget": False,
                "checklist_pass_under_reviewed_no_hit_support": False,
                "no_hit_context_supported": False,
                "reviewer_acceptance_required": False,
                "approval_candidate_preview_only": False,
                "should_apply_approval": False,
                "no_pit_review_run": True,
                "no_export_readiness_run": True,
                "no_staging_run": True,
                "no_universe_export": True,
                "no_data_raw_write": True,
                "no_data_processed_write": True,
                "no_current_candidates_generated": True,
                "comparison_only": True,
            }
        ]
    ).to_csv(comparison_csv, index=False)
    pd.DataFrame(
        [
            {
                "comparison_id": comparison_id,
                "status": status,
                "reference_profile_name": "STRICT_PIT",
                "profile_name": "EOD_POST_CLOSE_LOW_BUDGET_PIT",
                "profile_is_opt_in": True,
                "strict_default_unchanged": True,
                "row_count": row_count,
                "strict_checklist_pass_count": strict_pass_count,
                "eod_low_budget_checklist_pass_count": eod_low_budget_pass_count,
                "reviewed_no_hit_support_pass_count": reviewed_no_hit_support_pass_count,
                "no_hit_context_supported_count": no_hit_context_supported_count,
                "reviewer_acceptance_required_count": reviewer_acceptance_required_count,
                "relaxed_blocker_count": relaxed_blocker_count,
                "remaining_blocked_count": remaining_blocked_count,
                "approval_candidate_preview_count": eod_low_budget_pass_count,
            }
        ]
    ).to_csv(summary_csv, index=False)
    pd.DataFrame([{"comparison_id": comparison_id, "symbol": "000001", "signal_date": "2024-04-02", "blocker": "PIT_TIMING_BLOCKED"}]).to_csv(relaxed_csv, index=False)
    pd.DataFrame([{"comparison_id": comparison_id, "symbol": "000001", "signal_date": "2024-04-02", "blocker": "survivorship unresolved"}]).to_csv(remaining_csv, index=False)
    pd.DataFrame([{"field_name": "available_time", "rule": "available_time <= decision_time"}]).to_csv(snapshot_csv, index=False)
    report.write_text("No approval applied. Comparison only.", encoding="utf-8")
    _write_json(
        metadata,
        {
            "comparison_id": comparison_id,
            "created_at": created_at,
            "status": status,
            "reference_profile_name": "STRICT_PIT",
            "profile_name": "EOD_POST_CLOSE_LOW_BUDGET_PIT",
            "profile_is_opt_in": True,
            "strict_default_unchanged": True,
            "row_count": row_count,
            "strict_checklist_pass_count": strict_pass_count,
            "eod_low_budget_checklist_pass_count": eod_low_budget_pass_count,
            "reviewed_no_hit_support_pass_count": reviewed_no_hit_support_pass_count,
            "no_hit_context_supported_count": no_hit_context_supported_count,
            "reviewer_acceptance_required_count": reviewer_acceptance_required_count,
            "relaxed_blocker_count": relaxed_blocker_count,
            "remaining_blocked_count": remaining_blocked_count,
            "approval_applied": False,
            "pit_review_run": False,
            "export_readiness_run": False,
            "export_staging_run": False,
            "universe_exported": False,
            "active_worklist_mutated": False,
            "no_data_raw_write": True,
            "no_data_processed_write": True,
            "no_current_candidates_generated": True,
            "comparison_only": True,
            "output_files": {
                "comparison_csv": str(comparison_csv),
                "summary_csv": str(summary_csv),
                "relaxed_blocker_matrix": str(relaxed_csv),
                "remaining_blocker_matrix": str(remaining_csv),
                "policy_snapshot": str(snapshot_csv),
                "report": str(report),
                "metadata": str(metadata),
            },
        },
    )
    return folder


def _pit_official_status_evidence_packet_artifact(
    root: Path,
    *,
    packet_id: str = "packet-a",
    status: str = "WARN",
    row_count: int = 16,
    evidence_packet_row_count: int = 64,
    strong_official_date_specific_count: int = 0,
    supporting_official_symbol_level_count: int = 16,
    supporting_local_eod_cache_count: int = 16,
    context_only_count: int = 0,
    missing_count: int = 32,
    checklist_pass_count: int = 0,
    blocked_count: int = 16,
    eod_low_budget_checklist_pass_count: int = 0,
    created_at: str = "2026-06-05T09:10:00+08:00",
) -> Path:
    folder = root / "pit_official_status_evidence_packet" / packet_id
    folder.mkdir(parents=True, exist_ok=True)
    packet_csv = folder / "pit_official_status_evidence_packet.csv"
    source_csv = folder / "source_coverage_summary.csv"
    per_date_csv = folder / "per_symbol_date_status_evidence.csv"
    matrix_csv = folder / "evidence_strength_matrix.csv"
    draft_csv = folder / "updated_draft_completed_updates.csv"
    report = folder / "report.md"
    metadata = folder / "metadata.json"
    pd.DataFrame(
        [
            {
                "packet_id": packet_id,
                "signal_date": "2024-04-02",
                "symbol": "000001",
                "universe_name": "stock_core",
                "evidence_field": "not_delisted",
                "evidence_strength": "MISSING",
                "source_name": "",
                "source_url_or_path": "",
                "source_type": "",
                "accessed_at": "",
                "pit_suitability": "MISSING",
                "fields_supported": "",
                "field_status": "missing",
                "blocker_status": "missing not-delisted/ST/survivorship evidence",
                "evidence_reference": "",
                "context_only_or_approval_candidate": "missing",
                "approval_candidate_preview_only": False,
                "should_apply_approval": False,
                "no_approval_applied": True,
                "no_pit_review_run": True,
                "no_export_readiness_run": True,
                "no_staging_run": True,
                "no_universe_export": True,
                "no_data_raw_write": True,
                "no_data_processed_write": True,
                "no_current_candidates_generated": True,
                "no_snapshot_built": True,
                "no_forward_labels": True,
                "no_live_trading": True,
                "no_broker_api": True,
                "no_order_placement": True,
                "no_message_sent": True,
                "packet_only": True,
            }
        ]
    ).to_csv(packet_csv, index=False)
    pd.DataFrame(
        [
            {
                "packet_id": packet_id,
                "source_name": "local_market_cache",
                "source_url_or_path": "data/cache/market/daily_bars.csv",
                "source_type": "local_market_cache",
                "access_status": "readable",
                "parseable": True,
                "symbols_observed": "000001,159915",
                "dates_observed": "2024-04",
                "pit_suitability": "EOD_SUPPORT_ONLY",
                "strong_official_date_specific_count": 0,
                "supporting_official_symbol_level_count": 0,
                "supporting_local_eod_cache_count": supporting_local_eod_cache_count,
                "context_only_count": 0,
                "missing_count": 0,
            }
        ]
    ).to_csv(source_csv, index=False)
    pd.DataFrame(
        [
            {
                "packet_id": packet_id,
                "signal_date": "2024-04-02",
                "symbol": "000001",
                "universe_name": "stock_core",
                "strong_official_date_specific_count": 0,
                "supporting_official_symbol_level_count": 1,
                "supporting_local_eod_cache_count": 1,
                "context_only_count": 0,
                "missing_count": 2,
                "checklist_pass": False,
                "blocked": True,
                "blocker_reason": "missing not-delisted/ST/survivorship evidence",
                "review_status": "NEEDS_MORE_EVIDENCE",
                "include_flag": False,
                "survivorship_bias_resolved": False,
            }
        ]
    ).to_csv(per_date_csv, index=False)
    pd.DataFrame(
        [
            {
                "packet_id": packet_id,
                "symbol": "000001",
                "universe_name": "stock_core",
                "evidence_field": "not_delisted",
                "evidence_strength": "MISSING",
                "row_count": 1,
            }
        ]
    ).to_csv(matrix_csv, index=False)
    pd.DataFrame(
        [
            {
                "signal_date": "2024-04-02",
                "symbol": "000001",
                "universe_name": "stock_core",
                "review_status": "NEEDS_MORE_EVIDENCE",
                "include_flag": False,
                "reviewer": "",
                "reviewed_at": "",
                "review_reason": "packet fixture remains blocked",
                "evidence_source": "local_market_cache_context",
                "evidence_path": "data/cache/market/daily_bars.csv",
                "evidence_reference": "local_market_cache:000001:2024-04-02",
                "listed_date": "",
                "delisted_date": "",
                "is_active": "",
                "is_st": "",
                "is_suspended": "",
                "listed_date_evidence": "",
                "delisted_date_evidence": "",
                "is_active_evidence": "",
                "survivorship_bias_resolved": False,
                "as_of_date": "",
                "name": "",
                "instrument_type": "STOCK",
                "exchange": "SZSE",
                "industry": "",
                "min_lot": "",
                "t_plus_rule": "",
                "available_time": "",
                "revision_id": "",
                "source": "",
            }
        ]
    ).to_csv(draft_csv, index=False)
    report.write_text("No approval applied. Packet only.", encoding="utf-8")
    _write_json(
        metadata,
        {
            "packet_id": packet_id,
            "created_at": created_at,
            "status": status,
            "row_count": row_count,
            "evidence_packet_row_count": evidence_packet_row_count,
            "strong_official_date_specific_count": strong_official_date_specific_count,
            "supporting_official_symbol_level_count": supporting_official_symbol_level_count,
            "supporting_local_eod_cache_count": supporting_local_eod_cache_count,
            "context_only_count": context_only_count,
            "missing_count": missing_count,
            "checklist_pass_count": checklist_pass_count,
            "blocked_count": blocked_count,
            "eod_low_budget_checklist_pass_count": eod_low_budget_checklist_pass_count,
            "approval_applied": False,
            "pit_review_run": False,
            "export_readiness_run": False,
            "export_staging_run": False,
            "universe_exported": False,
            "active_worklist_mutated": False,
            "no_data_raw_write": True,
            "no_data_processed_write": True,
            "no_current_candidates_generated": True,
            "no_snapshot_built": True,
            "no_forward_labels": True,
            "cache_mutated": False,
            "packet_only": True,
            "output_files": {
                "packet_csv": str(packet_csv),
                "source_coverage_summary": str(source_csv),
                "per_symbol_date_status_evidence": str(per_date_csv),
                "evidence_strength_matrix": str(matrix_csv),
                "updated_draft_completed_updates": str(draft_csv),
                "report": str(report),
                "metadata": str(metadata),
            },
        },
    )
    return folder


def _pit_official_status_evidence_packet_enrichment_artifact(
    root: Path,
    *,
    enrichment_id: str = "enrich-a",
    status: str = "WARN",
    source_packet_id: str = "packet-a",
    policy_comparison_id: str = "comparison-a",
    row_count: int = 16,
    strong_official_date_specific_quotation_count: int = 16,
    reviewed_no_hit_context_supported_count: int = 16,
    reviewer_acceptance_required_count: int = 16,
    checklist_pass_count: int = 0,
    remaining_blocked_count: int = 16,
    created_at: str = "2026-06-05T09:20:00+08:00",
) -> Path:
    folder = root / "pit_official_status_evidence_packet_enrichment" / enrichment_id
    folder.mkdir(parents=True, exist_ok=True)
    enriched_csv = folder / "pit_official_status_evidence_packet_enrichment.csv"
    summary_csv = folder / "pit_official_status_evidence_packet_enrichment_summary.csv"
    blockers_csv = folder / "remaining_enrichment_blockers.csv"
    report = folder / "report.md"
    metadata = folder / "metadata.json"
    pd.DataFrame(
        [
            {
                "enrichment_id": enrichment_id,
                "source_packet_id": source_packet_id,
                "policy_comparison_id": policy_comparison_id,
                "signal_date": "2024-04-02",
                "symbol": "000001",
                "universe_name": "stock_core",
                "strong_official_date_specific_quotation": True,
                "quotation_source_url": "https://www.szse.cn/api/report/ShowReport?symbol=000001",
                "quotation_fields_observed": "symbol,date,close,volume",
                "reviewed_no_hit_context_supported": True,
                "reviewer_acceptance_required": True,
                "prior_official_symbol_level_context": True,
                "local_eod_cache_context": True,
                "missing_evidence_categories": "reviewer_no_hit_acceptance; survivorship_bias_resolution",
                "remaining_blocked": True,
                "checklist_pass": False,
                "no_approval_applied": True,
                "no_universe_export": True,
                "no_current_candidates_generated": True,
            }
        ]
    ).to_csv(enriched_csv, index=False)
    pd.DataFrame(
        [
            {
                "enrichment_id": enrichment_id,
                "status": status,
                "source_packet_id": source_packet_id,
                "policy_comparison_id": policy_comparison_id,
                "row_count": row_count,
                "strong_official_date_specific_quotation_count": (
                    strong_official_date_specific_quotation_count
                ),
                "reviewed_no_hit_context_supported_count": reviewed_no_hit_context_supported_count,
                "reviewer_acceptance_required_count": reviewer_acceptance_required_count,
                "prior_official_symbol_level_context_count": 16,
                "local_eod_cache_context_count": 16,
                "checklist_pass_count": checklist_pass_count,
                "remaining_blocked_count": remaining_blocked_count,
            }
        ]
    ).to_csv(summary_csv, index=False)
    pd.DataFrame(
        [
            {
                "enrichment_id": enrichment_id,
                "signal_date": "2024-04-02",
                "symbol": "000001",
                "blocker": "reviewer_no_hit_acceptance",
            }
        ]
    ).to_csv(blockers_csv, index=False)
    report.write_text("No approval applied. Enrichment only.", encoding="utf-8")
    _write_json(
        metadata,
        {
            "enrichment_id": enrichment_id,
            "created_at": created_at,
            "status": status,
            "source_packet_id": source_packet_id,
            "policy_comparison_id": policy_comparison_id,
            "row_count": row_count,
            "strong_official_date_specific_quotation_count": (
                strong_official_date_specific_quotation_count
            ),
            "reviewed_no_hit_context_supported_count": reviewed_no_hit_context_supported_count,
            "reviewer_acceptance_required_count": reviewer_acceptance_required_count,
            "prior_official_symbol_level_context_count": 16,
            "local_eod_cache_context_count": 16,
            "checklist_pass_count": checklist_pass_count,
            "remaining_blocked_count": remaining_blocked_count,
            "approval_applied": False,
            "pit_review_run": False,
            "export_readiness_run": False,
            "export_staging_run": False,
            "universe_exported": False,
            "active_worklist_mutated": False,
            "no_data_raw_write": True,
            "no_data_processed_write": True,
            "no_current_candidates_generated": True,
            "no_snapshot_built": True,
            "no_forward_labels": True,
            "cache_mutated": False,
            "enrichment_only": True,
            "output_files": {
                "enriched_csv": str(enriched_csv),
                "summary_csv": str(summary_csv),
                "blocker_matrix": str(blockers_csv),
                "report": str(report),
                "metadata": str(metadata),
            },
        },
    )
    return folder


def _universe_profile_policy_audit(root: Path) -> Path:
    worklist = root / "manual_diagnostics" / "policy_audit_test_worklist.csv"
    worklist.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "worklist_id": "worklist001",
                "review_id": "review001",
                "signal_date": "2024-04-02",
                "symbol": "000001",
                "universe_name": "etf_core",
                "suggested_instrument_type": "STOCK",
                "current_review_status": "NEEDS_MANUAL_REVIEW",
                "no_live_trading": True,
                "no_broker_api": True,
                "no_order_placement": True,
                "no_message_sent": True,
                "worklist_only": True,
            },
            {
                "worklist_id": "worklist001",
                "review_id": "review001",
                "signal_date": "2024-04-02",
                "symbol": "510300",
                "universe_name": "etf_core",
                "suggested_instrument_type": "ETF",
                "current_review_status": "NEEDS_MANUAL_REVIEW",
                "no_live_trading": True,
                "no_broker_api": True,
                "no_order_placement": True,
                "no_message_sent": True,
                "worklist_only": True,
            },
        ]
    ).to_csv(worklist, index=False)
    result = build_universe_profile_policy_audit(
        worklist=worklist,
        output_dir=root / "universe_profile_policy_audit",
    )
    return Path(result.artifact_paths["artifact_dir"])


def _signal_semantics_status(
    root: Path,
    *,
    semantics_id: str = "semantics-a",
    status: str = "WARN",
    workflow_stage: str = "SIGNAL_SEMANTICS_READY_FOR_REVIEW",
    health_status: str = "PASS",
    row_count: int = 4,
    demo_only_count: int = 0,
    watch_count: int = 1,
    review_buy_candidate_count: int = 1,
    review_sell_candidate_count: int = 0,
    hold_review_count: int = 0,
    no_action_count: int = 0,
    blocked_count: int = 2,
    issue_count: int = 2,
    profile: str = "reviewed_local_v0",
    input_path: str = "outputs/reports/manual_diagnostics/signal_semantics_synthetic_reviewed_fixture.csv",
    warning_count: int = 1,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:41:00",
) -> Path:
    folder = root / "signal_semantics" / "status" / f"status-{semantics_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "signal_semantics_status_report.md"
    status_csv = folder / "signal_semantics_status.csv"
    summary_csv = folder / "signal_semantics_status_summary.csv"
    metadata_path = folder / "metadata.json"
    semantics_report = root / "signal_semantics" / semantics_id / "signal_semantics_report.md"
    next_action = (
        "Demo signal semantics validated; do not treat DEMO_ONLY labels as strategy recommendations."
        if workflow_stage == "DEMO_SIGNAL_SEMANTICS_VALIDATED"
        else "Repair signal semantics artifacts before using advisory labels."
        if status == "FAIL"
        else "Review signal semantics labels manually; REVIEW_BUY_CANDIDATE is not an order and auto-order remains disabled."
    )
    report.write_text(
        "No live trading, broker API, order placement, or message delivery was invoked.",
        encoding="utf-8",
    )
    semantics_report.parent.mkdir(parents=True, exist_ok=True)
    semantics_report.write_text(
        "Signal semantics labels are advisory human-review labels, not orders.",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "component": "SIGNAL_SEMANTICS",
                "status": "READY" if status != "FAIL" else "FAIL",
                "latest_artifact_id": semantics_id,
                "row_count": row_count,
                "warning_count": 0,
                "error_count": 0,
                "issue_count": issue_count,
            },
            {
                "component": "SIGNAL_SEMANTICS_HEALTH",
                "status": health_status,
                "latest_artifact_id": "semantics-health-a",
                "row_count": row_count,
                "warning_count": 0 if health_status == "PASS" else warning_count,
                "error_count": error_count,
                "issue_count": error_count + (0 if health_status == "PASS" else warning_count),
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "workflow_stage": workflow_stage,
                "status": status,
                "latest_semantics_run_id": semantics_id,
                "latest_status": "READY" if status != "FAIL" else "FAIL",
                "health_status": health_status,
                "row_count": row_count,
                "demo_only_count": demo_only_count,
                "watch_count": watch_count,
                "review_buy_candidate_count": review_buy_candidate_count,
                "review_sell_candidate_count": review_sell_candidate_count,
                "hold_review_count": hold_review_count,
                "no_action_count": no_action_count,
                "blocked_count": blocked_count,
                "issue_count": issue_count,
                "profile": profile,
                "input_path": input_path,
                "input_type": "candidates",
                "report_path": str(semantics_report),
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{semantics_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_semantics_run_id": semantics_id,
            "health_status": health_status,
            "row_count": row_count,
            "next_manual_action": next_action,
            "warnings": ["Latest signal semantics artifact is review-only."] if warning_count else [],
            "output_files": {
                "signal_semantics_status_report": str(report),
                "signal_semantics_status_csv": str(status_csv),
                "signal_semantics_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "auto_order_allowed": False,
        },
    )
    return folder


def _advisory_profile_calibration_status(
    root: Path,
    *,
    calibration_id: str = "calibration-a",
    status: str = "WARN",
    workflow_stage: str = "ADVISORY_PROFILE_CALIBRATION_READY_FOR_REVIEW",
    health_status: str = "PASS",
    row_count: int = 6,
    review_buy_candidate_count: int = 1,
    watch_count: int = 2,
    no_action_count: int = 1,
    blocked_count: int = 2,
    demo_only_count: int = 0,
    issue_count: int = 2,
    profile: str = "balanced",
    input_path: str = "outputs/reports/manual_diagnostics/advisory_profile_calibration_synthetic_fixture.csv",
    warning_count: int = 1,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:40:00",
) -> Path:
    folder = root / "advisory_profile_calibration" / "status" / f"status-{calibration_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "advisory_profile_calibration_status_report.md"
    status_csv = folder / "advisory_profile_calibration_status.csv"
    summary_csv = folder / "advisory_profile_calibration_status_summary.csv"
    metadata_path = folder / "metadata.json"
    calibration_report = root / "advisory_profile_calibration" / calibration_id / "advisory_profile_calibration_report.md"
    next_action = (
        "Demo advisory profile calibration validated; do not treat DEMO_ONLY labels as strategy recommendations."
        if workflow_stage == "DEMO_ADVISORY_PROFILE_CALIBRATION_VALIDATED"
        else "Repair advisory profile calibration artifacts before using threshold analysis."
        if status == "FAIL"
        else "Review calibration labels manually; REVIEW_BUY_CANDIDATE is not an order and auto-order remains disabled."
    )
    report.write_text(
        "No live trading, broker API, order placement, or message delivery was invoked.",
        encoding="utf-8",
    )
    calibration_report.parent.mkdir(parents=True, exist_ok=True)
    calibration_report.write_text(
        "Calibration labels are threshold-analysis labels, not orders.",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "component": "ADVISORY_PROFILE_CALIBRATION",
                "status": "READY" if status != "FAIL" else "FAIL",
                "latest_artifact_id": calibration_id,
                "row_count": row_count,
                "warning_count": 0,
                "error_count": 0,
                "issue_count": issue_count,
            },
            {
                "component": "ADVISORY_PROFILE_CALIBRATION_HEALTH",
                "status": health_status,
                "latest_artifact_id": "calibration-health-a",
                "row_count": row_count,
                "warning_count": 0 if health_status == "PASS" else warning_count,
                "error_count": error_count,
                "issue_count": error_count + (0 if health_status == "PASS" else warning_count),
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "workflow_stage": workflow_stage,
                "status": status,
                "latest_calibration_run_id": calibration_id,
                "latest_status": "READY" if status != "FAIL" else "FAIL",
                "health_status": health_status,
                "row_count": row_count,
                "review_buy_candidate_count": review_buy_candidate_count,
                "watch_count": watch_count,
                "no_action_count": no_action_count,
                "blocked_count": blocked_count,
                "demo_only_count": demo_only_count,
                "issue_count": issue_count,
                "profile": profile,
                "input_path": input_path,
                "input_type": "candidates",
                "report_path": str(calibration_report),
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{calibration_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_calibration_run_id": calibration_id,
            "health_status": health_status,
            "row_count": row_count,
            "next_manual_action": next_action,
            "warnings": ["Latest advisory profile calibration artifact is review-only."] if warning_count else [],
            "output_files": {
                "advisory_profile_calibration_status_report": str(report),
                "advisory_profile_calibration_status_csv": str(status_csv),
                "advisory_profile_calibration_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "auto_order_allowed": False,
        },
    )
    return folder


def _signal_advisory_status(
    root: Path,
    *,
    signal_id: str = "signal-a",
    status: str = "WARN",
    workflow_stage: str = "DEMO_SIGNAL_ADVISORY_VALIDATED",
    health_status: str = "PASS",
    warning_count: int = 1,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:42:00",
) -> Path:
    folder = root / "signals" / "status" / f"status-{signal_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "signal_advisory_status_report.md"
    status_csv = folder / "signal_advisory_status.csv"
    summary_csv = folder / "signal_advisory_status_summary.csv"
    metadata_path = folder / "metadata.json"
    alert_preview = root / "signals" / signal_id / "signal_alert_preview.md"
    signal_report = root / "signals" / signal_id / "signal_advisory_report.md"
    next_action = (
        "Review local alert preview; do not treat DEMO_ONLY signals as strategy recommendations."
        if workflow_stage == "DEMO_SIGNAL_ADVISORY_VALIDATED"
        else "Repair signal advisory artifacts before using alert previews."
        if status == "FAIL"
        else "Review local alert preview and require manual confirmation before any human action."
    )
    report.write_text("No live trading, broker API, order placement, or message delivery was invoked.", encoding="utf-8")
    alert_preview.parent.mkdir(parents=True, exist_ok=True)
    alert_preview.write_text("Manual confirmation required. No auto-order.", encoding="utf-8")
    signal_report.write_text("Signals are advisory artifacts, not orders.", encoding="utf-8")
    pd.DataFrame(
        [
            {
                "component": "SIGNAL_ADVISORY",
                "status": "READY",
                "latest_artifact_id": signal_id,
                "signal_count": 9,
                "warning_count": 0,
                "error_count": 0,
                "issue_count": 0,
            },
            {
                "component": "SIGNAL_ADVISORY_HEALTH",
                "status": health_status,
                "latest_artifact_id": "signal-health-a",
                "signal_count": 9,
                "warning_count": 0 if health_status == "PASS" else warning_count,
                "error_count": error_count,
                "issue_count": error_count + (0 if health_status == "PASS" else warning_count),
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "workflow_stage": workflow_stage,
                "status": status,
                "latest_signal_run_id": signal_id,
                "latest_status": "READY",
                "health_status": health_status,
                "signal_count": 9,
                "demo_signal_count": 9,
                "watch_count": 0,
                "review_buy_candidate_count": 0,
                "review_sell_candidate_count": 0,
                "blocked_count": 0,
                "source_candidate_run_id": "candidate-a",
                "selection_profile": "demo",
                "demo_mode": True,
                "not_strategy_recommendation": True,
                "alert_preview_path": str(alert_preview),
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{signal_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_signal_run_id": signal_id,
            "health_status": health_status,
            "signal_count": 9,
            "next_manual_action": next_action,
            "warnings": ["Latest signal advisory artifact is DEMO_ONLY."] if warning_count else [],
            "output_files": {
                "signal_advisory_status_report": str(report),
                "signal_advisory_status_csv": str(status_csv),
                "signal_advisory_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "message_delivery_enabled": False,
            "message_sent": False,
        },
    )
    return folder


def _single_symbol_advisory_status(
    root: Path,
    *,
    advisory_id: str = "single-a",
    symbol: str = "000001",
    status: str = "WARN",
    workflow_stage: str = "DEMO_SINGLE_SYMBOL_ADVISORY_VALIDATED",
    latest_status: str = "READY",
    advisory_action: str = "DEMO_ONLY",
    health_status: str = "PASS",
    final_score: str = "55.6",
    warning_count: int = 1,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:43:00",
) -> Path:
    folder = root / "single_symbol_advisory" / "status" / f"status-{advisory_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "single_symbol_advisory_status_report.md"
    status_csv = folder / "single_symbol_advisory_status.csv"
    summary_csv = folder / "single_symbol_advisory_status_summary.csv"
    metadata_path = folder / "metadata.json"
    alert_preview = root / "single_symbol_advisory" / advisory_id / "alert_preview.md"
    advisory_report = root / "single_symbol_advisory" / advisory_id / "single_symbol_advisory_report.md"
    next_action = (
        "Review local single-symbol alert preview; do not treat DEMO_ONLY output as a strategy recommendation."
        if workflow_stage == "DEMO_SINGLE_SYMBOL_ADVISORY_VALIDATED"
        else "Symbol was not found in the provided local artifact; provide a relevant candidates/scored/signals artifact before reviewing."
        if workflow_stage == "SINGLE_SYMBOL_ADVISORY_NOT_FOUND"
        else "Repair single-symbol advisory artifacts before using this review."
        if status == "FAIL"
        else "Review local single-symbol advisory report; manual confirmation remains required."
    )
    report.write_text("No live trading, broker API, order placement, or message delivery was invoked.", encoding="utf-8")
    alert_preview.parent.mkdir(parents=True, exist_ok=True)
    alert_preview.write_text("Manual confirmation required. No auto-order.", encoding="utf-8")
    advisory_report.write_text("Single-symbol advisory is not an order.", encoding="utf-8")
    pd.DataFrame(
        [
            {
                "component": "SINGLE_SYMBOL_ADVISORY",
                "status": latest_status,
                "latest_artifact_id": advisory_id,
                "symbol": symbol,
                "warning_count": 0,
                "error_count": 0,
                "issue_count": 0,
            },
            {
                "component": "SINGLE_SYMBOL_ADVISORY_HEALTH",
                "status": health_status,
                "latest_artifact_id": "single-health-a",
                "symbol": symbol,
                "warning_count": 0 if health_status == "PASS" else warning_count,
                "error_count": error_count,
                "issue_count": error_count + (0 if health_status == "PASS" else warning_count),
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "workflow_stage": workflow_stage,
                "status": status,
                "latest_advisory_run_id": advisory_id,
                "latest_symbol": symbol,
                "latest_status": latest_status,
                "latest_advisory_action": advisory_action,
                "health_status": health_status,
                "final_score": final_score,
                "demo_mode": True,
                "not_strategy_recommendation": True,
                "alert_preview_path": str(alert_preview),
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{advisory_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_advisory_run_id": advisory_id,
            "latest_symbol": symbol,
            "latest_advisory_action": advisory_action,
            "health_status": health_status,
            "next_manual_action": next_action,
            "warnings": ["Latest single-symbol advisory artifact is review-only."] if warning_count else [],
            "output_files": {
                "single_symbol_advisory_status_report": str(report),
                "single_symbol_advisory_status_csv": str(status_csv),
                "single_symbol_advisory_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "message_delivery_enabled": False,
            "message_sent": False,
        },
    )
    return folder


def _single_symbol_advisory_answer_status(
    root: Path,
    *,
    answer_id: str = "answer-a",
    advisory_id: str = "single-a",
    symbol: str = "000001",
    status: str = "WARN",
    workflow_stage: str = "DEMO_SINGLE_SYMBOL_ADVISORY_ANSWER_VALIDATED",
    latest_status: str = "READY",
    advisory_action: str = "DEMO_ONLY",
    health_status: str = "PASS",
    question: str = "should I buy?",
    answer_style: str = "concise",
    warning_count: int = 1,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:44:00",
) -> Path:
    folder = root / "single_symbol_advisory_answer" / "status" / f"status-{answer_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "single_symbol_advisory_answer_status_report.md"
    status_csv = folder / "single_symbol_advisory_answer_status.csv"
    summary_csv = folder / "single_symbol_advisory_answer_status_summary.csv"
    metadata_path = folder / "metadata.json"
    answer_markdown = root / "single_symbol_advisory_answer" / answer_id / "single_symbol_advisory_answer.md"
    next_action = (
        "Review local question-style answer; do not treat DEMO_ONLY output as a strategy recommendation."
        if workflow_stage == "DEMO_SINGLE_SYMBOL_ADVISORY_ANSWER_VALIDATED"
        else "Symbol was not found in the provided local artifact; no recommendation was invented."
        if workflow_stage == "SINGLE_SYMBOL_ADVISORY_ANSWER_NOT_FOUND"
        else "Repair question-style answer artifacts before using this response."
        if status == "FAIL"
        else "Review local question-style answer; manual confirmation remains required."
    )
    report.write_text("No live trading, broker API, order placement, LLM API, or message delivery was invoked.", encoding="utf-8")
    answer_markdown.parent.mkdir(parents=True, exist_ok=True)
    answer_markdown.write_text(
        "Manual confirmation required. No auto-order. No LLM/API call. No message sent.",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "component": "SINGLE_SYMBOL_ADVISORY_ANSWER",
                "status": latest_status,
                "latest_artifact_id": answer_id,
                "symbol": symbol,
                "warning_count": 0,
                "error_count": 0,
                "issue_count": 0,
            },
            {
                "component": "SINGLE_SYMBOL_ADVISORY_ANSWER_HEALTH",
                "status": health_status,
                "latest_artifact_id": "answer-health-a",
                "symbol": symbol,
                "warning_count": 0 if health_status == "PASS" else warning_count,
                "error_count": error_count,
                "issue_count": error_count + (0 if health_status == "PASS" else warning_count),
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "workflow_stage": workflow_stage,
                "status": status,
                "latest_answer_run_id": answer_id,
                "latest_advisory_run_id": advisory_id,
                "latest_symbol": symbol,
                "latest_status": latest_status,
                "latest_advisory_action": advisory_action,
                "latest_question": question,
                "answer_style": answer_style,
                "health_status": health_status,
                "demo_mode": True,
                "not_strategy_recommendation": True,
                "answer_markdown_path": str(answer_markdown),
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{answer_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_answer_run_id": answer_id,
            "latest_advisory_run_id": advisory_id,
            "latest_symbol": symbol,
            "latest_advisory_action": advisory_action,
            "health_status": health_status,
            "next_manual_action": next_action,
            "warnings": ["Latest question-style answer is review-only."] if warning_count else [],
            "output_files": {
                "single_symbol_advisory_answer_status_report": str(report),
                "single_symbol_advisory_answer_status_csv": str(status_csv),
                "single_symbol_advisory_answer_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "llm_api_called": False,
        },
    )
    return folder


def _advisory_conversation_status(
    root: Path,
    *,
    conversation_id: str = "conv-a",
    question: str = "000001 now can buy?",
    parsed_symbol: str = "000001",
    parsed_intent: str = "BUY_REVIEW",
    status: str = "WARN",
    workflow_stage: str = "DEMO_ADVISORY_CONVERSATION_VALIDATED",
    latest_status: str = "READY",
    advisory_action: str = "DEMO_ONLY",
    health_status: str = "PASS",
    parser_type: str = "deterministic_rule_based",
    llm_api_called: bool = False,
    no_message_sent: bool = True,
    no_live_trading: bool = True,
    no_broker_api: bool = True,
    auto_order_allowed: bool = False,
    warning_count: int = 1,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:46:00",
) -> Path:
    folder = root / "advisory_conversation" / "status" / f"status-{conversation_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "advisory_conversation_status_report.md"
    status_csv = folder / "advisory_conversation_status.csv"
    summary_csv = folder / "advisory_conversation_status_summary.csv"
    metadata_path = folder / "metadata.json"
    linked_answer = root / "single_symbol_advisory_answer" / f"answer-{conversation_id}" / "single_symbol_advisory_answer.md"
    linked_answer.parent.mkdir(parents=True, exist_ok=True)
    linked_answer.write_text(
        "Manual confirmation required. No auto-order. No LLM/API call. No message sent.",
        encoding="utf-8",
    )
    next_action = (
        "Review local conversational advisory answer; do not treat DEMO_ONLY output as a strategy recommendation."
        if workflow_stage == "DEMO_ADVISORY_CONVERSATION_VALIDATED"
        else "Provide a six-digit local symbol in the question; no symbol or recommendation was invented."
        if workflow_stage == "ADVISORY_CONVERSATION_PARSE_FAILED"
        else "Parsed symbol was not found in the provided local artifact; no recommendation was invented."
        if workflow_stage == "ADVISORY_CONVERSATION_NOT_FOUND"
        else "Repair advisory conversation artifacts before using local conversational answers."
        if status == "FAIL"
        else "Review local conversational advisory answer; manual confirmation remains required."
    )
    report.write_text(
        "No live trading, broker API, order placement, LLM/API call, external API call, or message delivery was invoked.",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "component": "ADVISORY_CONVERSATION",
                "status": latest_status,
                "latest_artifact_id": conversation_id,
                "symbol": parsed_symbol,
                "warning_count": 0,
                "error_count": 0,
                "issue_count": 0,
            },
            {
                "component": "ADVISORY_CONVERSATION_HEALTH",
                "status": health_status,
                "latest_artifact_id": "conversation-health-a",
                "symbol": parsed_symbol,
                "warning_count": 0 if health_status == "PASS" else warning_count,
                "error_count": error_count,
                "issue_count": error_count + (0 if health_status == "PASS" else warning_count),
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "workflow_stage": workflow_stage,
                "status": status,
                "latest_conversation_run_id": conversation_id,
                "latest_original_question": question,
                "latest_parsed_symbol": parsed_symbol,
                "latest_parsed_intent": parsed_intent,
                "latest_advisory_action": advisory_action,
                "parser_type": parser_type,
                "health_status": health_status,
                "llm_api_called": llm_api_called,
                "no_message_sent": no_message_sent,
                "no_live_trading": no_live_trading,
                "no_broker_api": no_broker_api,
                "auto_order_allowed": auto_order_allowed,
                "linked_answer_markdown_path": str(linked_answer),
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{conversation_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_conversation_run_id": conversation_id,
            "latest_original_question": question,
            "latest_parsed_symbol": parsed_symbol,
            "latest_parsed_intent": parsed_intent,
            "latest_advisory_action": advisory_action,
            "health_status": health_status,
            "next_manual_action": next_action,
            "warnings": ["Latest advisory conversation artifact is review-only."] if warning_count else [],
            "output_files": {
                "advisory_conversation_status_report": str(report),
                "advisory_conversation_status_csv": str(status_csv),
                "advisory_conversation_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "llm_api_called": llm_api_called,
        },
    )
    return folder


def _single_symbol_answer_artifact(
    root: Path,
    *,
    answer_id: str,
    advisory_id: str = "single-a",
    symbol: str = "000001",
    metadata_updates: dict | None = None,
) -> Path:
    folder = root / "single_symbol_advisory_answer" / answer_id
    folder.mkdir(parents=True, exist_ok=True)
    answer_md = folder / "single_symbol_advisory_answer.md"
    answer_json = folder / "single_symbol_advisory_answer.json"
    metadata_path = folder / "metadata.json"
    body = (
        "Demo-only review for workflow validation; not a real trading recommendation.\n"
        "Manual confirmation required. No auto-order. No message sent. No LLM/API call."
    )
    answer_md.write_text(body, encoding="utf-8")
    payload = {
        "answer_run_id": answer_id,
        "advisory_run_id": advisory_id,
        "symbol": symbol,
        "status": "READY",
        "advisory_action": "DEMO_ONLY",
        **_semantics_provenance("DEMO_ONLY"),
        "question": "should I buy?",
        "answer_style": "concise",
        "short_answer": "Demo-only review for workflow validation; not a real trading recommendation.",
        "answer_body": body,
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "audit_metadata": {
            "demo_mode": True,
            "not_strategy_recommendation": True,
            "llm_api_called": False,
            **_semantics_provenance("DEMO_ONLY"),
        },
        "advisory_record": {
            "symbol": symbol,
            "status": "READY",
            "advisory_action": "DEMO_ONLY",
            **_semantics_provenance("DEMO_ONLY"),
            "demo_mode": True,
            "not_strategy_recommendation": True,
            "requires_manual_confirmation": True,
            "auto_order_allowed": False,
            "no_live_trading": True,
            "no_broker_api": True,
            "no_message_sent": True,
        },
    }
    answer_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    metadata = {
        "answer_run_id": answer_id,
        "created_at": f"{DECISION_DATE}T15:44:00",
        "advisory_run_id": advisory_id,
        "symbol": symbol,
        "status": "READY",
        "advisory_action": "DEMO_ONLY",
        **_semantics_provenance("DEMO_ONLY"),
        "question": "should I buy?",
        "answer_style": "concise",
        "short_answer": "Demo-only review for workflow validation; not a real trading recommendation.",
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "message_delivery_enabled": False,
        "message_sent": False,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "approved_for_paper_applied": False,
        "llm_api_called": False,
        "external_api_called": False,
        "demo_mode": True,
        "not_strategy_recommendation": True,
        "output_files": {
            "single_symbol_advisory_answer": str(answer_md),
            "single_symbol_advisory_answer_json": str(answer_json),
            "metadata": str(metadata_path),
        },
    }
    metadata.update(metadata_updates or {})
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return folder


def _semantics_provenance(action: str) -> dict:
    return {
        "semantics_policy_source": "signal_semantics",
        "semantics_policy_version": "v0.1",
        "semantics_classifier": "classify_signal_semantics_action",
        "semantics_settings_profile": "demo",
        "semantics_action": action,
        "semantics_reason": "Dashboard fixture classified by shared signal semantics.",
        "semantics_manual_confirmation_required": True,
        "semantics_auto_order_allowed": False,
        "semantics_no_live_trading": True,
        "semantics_no_broker_api": True,
    }


def _market_update_handoff_status(
    root: Path,
    *,
    status: str = "WARN",
    workflow_stage: str = "CURRENT_CANDIDATES_READY_FOR_PAPER_SMOKE_TEST",
    handoff_id: str = "handoff-a",
    health_status: str = "PASS",
    warning_count: int = 0,
    error_count: int = 0,
    created_at: str = f"{DECISION_DATE}T15:35:00",
) -> Path:
    folder = root / "market_update_handoff" / "status" / f"status-{handoff_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "market_update_handoff_status_report.md"
    status_csv = folder / "market_update_handoff_status.csv"
    summary_csv = folder / "market_update_handoff_status_summary.csv"
    metadata_path = folder / "metadata.json"
    next_action = "Run current-to-paper on the latest current-candidates artifact, then continue paper review smoke testing."
    report.write_text("No live trading or broker API was invoked.", encoding="utf-8")
    pd.DataFrame(
        [
            {
                "component": "MARKET_UPDATE_HANDOFF_INDEX",
                "status": "PASS",
                "latest_handoff_id": handoff_id,
                "warning_count": 0,
                "error_count": 0,
                "issue_count": 0,
            },
            {
                "component": "MARKET_UPDATE_HANDOFF_HEALTH",
                "status": health_status,
                "latest_handoff_id": handoff_id,
                "warning_count": 0,
                "error_count": error_count,
                "issue_count": error_count,
            },
            {
                "component": "LATEST_MARKET_UPDATE_HANDOFF",
                "status": status,
                "latest_handoff_id": handoff_id,
                "warning_count": warning_count,
                "error_count": 0,
                "issue_count": 0,
            },
        ]
    ).to_csv(status_csv, index=False)
    pd.DataFrame(
        [
            {
                "status": status,
                "workflow_stage": workflow_stage,
                "latest_handoff_id": handoff_id,
                "pipeline_id": "pipeline-a",
                "snapshot_quality_status": "PASS",
                "current_candidate_run_id": "candidate-a",
                "candidate_count": 2,
                "health_status": health_status,
                "issue_count": error_count,
                "warning_count": 0,
                "error_count": error_count,
                "next_manual_action": next_action,
            }
        ]
    ).to_csv(summary_csv, index=False)
    _write_json(
        metadata_path,
        {
            "status_id": f"status-{handoff_id}",
            "created_at": created_at,
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_handoff_id": handoff_id,
            "next_manual_action": next_action,
            "warnings": ["Provisional WARN_ACCEPT rows were included."] if warning_count else [],
            "output_files": {
                "market_update_handoff_status_report": str(report),
                "market_update_handoff_status_csv": str(status_csv),
                "market_update_handoff_status_summary": str(summary_csv),
                "metadata": str(metadata_path),
            },
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _market_update_handoff_artifact(
    root: Path,
    *,
    handoff_id: str = "handoff-a",
    status: str = "PASS",
    pipeline_id: str = "pipeline-a",
    snapshot_quality_status: str = "PASS",
    current_candidate_run_id: str = "candidate-a",
    candidate_count: int = 2,
    created_at: str = f"{DECISION_DATE}T15:35:00",
) -> Path:
    artifact_dir = root / "market_update_handoff" / handoff_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    linked_dir = root / "market_update_handoff" / "_linked" / handoff_id
    linked_dir.mkdir(parents=True, exist_ok=True)
    no_live = "No live trading or broker API was invoked."

    batch_market_csv = linked_dir / "market_raw_data.csv"
    pd.DataFrame(
        [
            {
                "symbol": "510300",
                "trade_date": DECISION_DATE,
                "open": 1.0,
                "high": 1.1,
                "low": 0.9,
                "close": 1.0,
                "volume": 1000,
                "amount": 1000,
                "available_time": f"{DECISION_DATE} 15:30:00",
                "source": "AKSHARE_OPTIONAL",
            }
        ]
    ).to_csv(batch_market_csv, index=False)
    pipeline_manifest = linked_dir / "market_update_handoff_manifest.json"
    pipeline_manifest.write_text(
        json.dumps(
            {
                "datasets": [
                    {"dataset_type": "market", "source": "LOCAL_CSV", "input_path": str(batch_market_csv)}
                ]
            }
        ),
        encoding="utf-8",
    )
    pipeline_report = linked_dir / "data_pipeline_report.md"
    snapshot_manifest = linked_dir / "snapshot_manifest.json"
    snapshot_report = linked_dir / "snapshot_quality_gate_report.md"
    current_report = linked_dir / "current_candidates_report.md"
    current_metadata = linked_dir / "current_candidate_metadata.json"
    factor_dataset = linked_dir / "factor_dataset.csv"
    scored_dataset = linked_dir / "scored_dataset.csv"
    candidates = linked_dir / "candidates.csv"
    pipeline_report.write_text(no_live, encoding="utf-8")
    snapshot_manifest.write_text("{}", encoding="utf-8")
    snapshot_report.write_text(no_live, encoding="utf-8")
    current_report.write_text(no_live, encoding="utf-8")
    current_metadata.write_text(json.dumps({"run_id": current_candidate_run_id}), encoding="utf-8")
    pd.DataFrame([{"symbol": "510300"}] * candidate_count).to_csv(factor_dataset, index=False)
    pd.DataFrame([{"symbol": "510300", "final_score": 50.0}] * candidate_count).to_csv(scored_dataset, index=False)
    pd.DataFrame([{"symbol": "510300"}] * candidate_count).to_csv(candidates, index=False)

    handoff_report = artifact_dir / "market_update_handoff_report.md"
    handoff_rows = artifact_dir / "market_update_handoff_rows.csv"
    manifest_artifact = artifact_dir / "generated_pipeline_manifest.json"
    handoff_report.write_text(no_live, encoding="utf-8")
    pd.DataFrame(
        [
            {
                "symbol": "510300",
                "included": True,
                "handoff_status": "INCLUDED_WARN_ACCEPT" if status == "WARN" else "INCLUDED_ACCEPT",
                "raw_data_path": str(batch_market_csv),
            }
        ]
    ).to_csv(handoff_rows, index=False)
    manifest_artifact.write_text(pipeline_manifest.read_text(encoding="utf-8"), encoding="utf-8")

    _write_json(
        artifact_dir / "metadata.json",
        {
            "handoff_id": handoff_id,
            "status": status,
            "created_at": created_at,
            "summary": [{"included_row_count": 1}],
            "batch_market_csv_path": str(batch_market_csv),
            "generated_pipeline_manifest_path": str(pipeline_manifest),
            "pipeline_id": pipeline_id,
            "pipeline_status": "PASS",
            "data_pipeline_report_path": str(pipeline_report),
            "snapshot_manifest_path": str(snapshot_manifest),
            "snapshot_quality_status": snapshot_quality_status,
            "snapshot_quality_report_path": str(snapshot_report),
            "current_candidate_run_id": current_candidate_run_id,
            "current_candidate_artifact_paths": {
                "current_candidates_report": str(current_report),
                "metadata": str(current_metadata),
                "factor_dataset": str(factor_dataset),
                "scored_dataset": str(scored_dataset),
                "candidates": str(candidates),
            },
            "factor_dataset_shape": [candidate_count, 1],
            "scored_dataset_shape": [candidate_count, 2],
            "candidates_shape": [candidate_count, 1],
            "candidate_count": candidate_count,
            "warnings": ["Provisional WARN_ACCEPT rows were included."] if status == "WARN" else [],
            "artifact_paths": {
                "market_update_handoff_report": str(handoff_report),
                "market_update_handoff_rows": str(handoff_rows),
                "generated_pipeline_manifest": str(manifest_artifact),
                "metadata": str(artifact_dir / "metadata.json"),
            },
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "no_live_trading": True,
            "no_broker_api": True,
            "no_live_trading_statement": no_live,
        },
    )
    return artifact_dir


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def test_research_status_includes_reviewer_no_hit_acceptance_when_active(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _reviewer_no_hit_acceptance_artifact(root)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.reviewer_no_hit_acceptance_status == "WARN"
    assert result.reviewer_no_hit_acceptance_stage == "REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTANCE_NEEDS_REVIEW"
    assert result.reviewer_no_hit_acceptance_row_count == 8
    assert result.reviewer_no_hit_acceptance_reviewer_acceptance_required_count == 8
    assert result.reviewer_no_hit_acceptance_checklist_pass_count == 0
    assert result.workflow_stage == "REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTANCE_NEEDS_REVIEW"


def test_research_status_preserves_later_paper_priority_with_reviewer_no_hit_acceptance(tmp_path: Path) -> None:
    root = _workflow_to_daily(_reports_root(tmp_path))
    _reviewer_no_hit_acceptance_artifact(root)
    _reconciliation(root, status="PASS")
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action=(
            "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
            "only if testing fills, or return to data-source / strategy research."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.reviewer_no_hit_acceptance_stage == "REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTANCE_NEEDS_REVIEW"
    row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTANCE_STATUS"
    ].iloc[0]
    assert row["stale_warning_count"] >= 1
    assert row["actionable_warning_count"] == 0


def test_research_status_metadata_exports_reviewer_no_hit_acceptance_fields(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _reviewer_no_hit_acceptance_artifact(root)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    summary = pd.read_csv(result.artifact_paths["local_research_summary"], keep_default_na=False)
    metadata = json.loads(Path(result.artifact_paths["metadata"]).read_text(encoding="utf-8"))

    assert summary.loc[0, "latest_reviewer_no_hit_acceptance_id"]
    assert summary.loc[0, "reviewer_no_hit_acceptance_row_count"] == 8
    assert metadata["reviewer_no_hit_acceptance_status"] == "WARN"
    assert metadata["reviewer_no_hit_acceptance_checklist_pass_count"] == 0


def _reviewer_no_hit_acceptance_artifact(root: Path) -> Path:
    enrichment = root / "_fixtures" / "enrichment-a"
    enrichment.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {"signal_date": "2024-04-02", "symbol": "000001", "universe_name": "stock_core"},
            {"signal_date": "2024-04-02", "symbol": "159915", "universe_name": "etf_core"},
        ]
    ).to_csv(enrichment / "pit_official_status_evidence_packet_enrichment.csv", index=False)
    _write_json(
        enrichment / "metadata.json",
        {
            "enrichment_id": "enrichment-a",
            "source_packet_id": "packet-a",
            "policy_comparison_id": "comparison-a",
            "created_at": "2026-06-05T00:00:00Z",
        },
    )
    audit = root / "_fixtures" / "audit"
    audit.mkdir(parents=True, exist_ok=True)
    for name in [
        "source_coverage_acceptance_rules.csv",
        "query_window_rules.csv",
        "survivorship_rationale_template.csv",
        "blocker_after_acceptance_matrix.csv",
    ]:
        pd.DataFrame([{"rule": "review_required"}]).to_csv(audit / name, index=False)
    comparison = root / "_fixtures" / "comparison-a"
    comparison.mkdir(parents=True, exist_ok=True)
    _write_json(comparison / "metadata.json", {"comparison_id": "comparison-a"})
    result = build_reviewer_no_hit_source_coverage_acceptance(
        enrichment=enrichment,
        audit=audit,
        policy_comparison=comparison,
        output_dir=root / "reviewer_no_hit_source_coverage_acceptance",
    )
    return result.artifact_paths["artifact_dir"]


def _reviewer_no_hit_downstream_impact_artifact(root: Path) -> Path:
    acceptance = _reviewer_no_hit_acceptance_artifact(root)
    validator = root / "_fixtures" / "validator-a"
    validator.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "signal_date": "2024-04-02",
                "symbol": "000001",
                "universe_name": "stock_core",
                "checklist_pass": False,
                "blocker_reason": "remaining PIT evidence required",
            },
            {
                "signal_date": "2024-04-02",
                "symbol": "159915",
                "universe_name": "etf_core",
                "checklist_pass": False,
                "blocker_reason": "remaining PIT evidence required",
            },
        ]
    ).to_csv(validator / "pit_evidence_checklist_validation.csv", index=False)
    _write_json(validator / "metadata.json", {"validator_id": "validator-a"})
    policy = root / "_fixtures" / "comparison-a"
    policy.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "signal_date": "2024-04-02",
                "symbol": "000001",
                "recommended_future_universe": "stock_core",
            },
            {
                "signal_date": "2024-04-02",
                "symbol": "159915",
                "recommended_future_universe": "etf_core",
            },
        ]
    ).to_csv(policy / "pit_evidence_policy_profile_comparison.csv", index=False)
    _write_json(policy / "metadata.json", {"comparison_id": "comparison-a"})
    result = build_reviewer_no_hit_acceptance_downstream_impact(
        acceptance=acceptance,
        enrichment=root / "_fixtures" / "enrichment-a",
        validator=validator,
        policy_comparison=policy,
        output_dir=root / "reviewer_no_hit_acceptance_downstream_impact",
    )
    return result.artifact_paths["artifact_dir"]
