import json
import os
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.local_research_dashboard import (
    LocalResearchDashboardResult,
    infer_local_research_next_action,
    infer_local_research_workflow_stage,
    run_local_research_dashboard,
)
from quant_replay_system.universe_profile_policy_audit import build_universe_profile_policy_audit


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


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
