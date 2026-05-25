import json
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
            "Demo workflow validated; no fills were supplied. Proceed to paper-reconcile-fills only if you want "
            "to test fills, or return to data-source strategy."
        ),
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")
    paper_row = result.dashboard_frame.loc[result.dashboard_frame["component"] == "PAPER_WORKFLOW_STATUS"].iloc[0]
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.status == "WARN"
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert "Demo workflow validated" in result.next_manual_action
    assert paper_row["warning_classification"] == "EXPECTED_DEMO_WARNING"
    assert summary["expected_demo_warning_count"] == 1
    assert summary["actionable_warning_count"] == 0


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
    assert result.market_cache_export_plan_downstream_export_id == "export-plan-a"
    assert result.market_cache_export_plan_downstream_snapshot_quality_status == "PASS"
    assert result.linked_snapshot_quality_status == "PASS"
    assert result.active_snapshot_chain == "MARKET_CACHE_EXPORT_POLICY_STATUS"
    assert "current-candidates" in result.next_manual_action
    assert plan_row["warning_classification"] == "EXPECTED_REVIEWABLE_WARNING"
    assert summary["actionable_warning_count"] == 0


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
    assert metadata["market_cache_export_plan_downstream_export_id"] == "export-plan-metadata"
    assert metadata["market_cache_export_plan_downstream_snapshot_quality_status"] == "PASS"
    assert component_statuses["latest_market_cache_export_plan_id"] == "plan-metadata"
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


def _daily_paper(root: Path, *, reviewed_decisions_path: Path | None = None) -> Path:
    folder = root / "paper_trading" / "daily" / f"{DECISION_DATE}_journal-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "paper_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "paper_date": DECISION_DATE,
            "journal_id": "journal-a",
            "created_at": f"{DECISION_DATE}T16:05:00",
            "reviewed_decisions_used": True,
            "reconciliation": {"status": "", "issue_count": 0, "error_count": 0, "warning_count": 0},
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


def _reconciliation(root: Path, *, status: str = "PASS", errors: int = 0, warnings: int = 0) -> Path:
    folder = root / "paper_trading" / "reconciliation" / "recon-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "reconciliation_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "reconciliation_id": "recon-a",
            "created_at": f"{DECISION_DATE}T16:10:00",
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
    status: str = "PASS",
    workflow_stage: str | None = None,
    expected_demo_warning_count: int = 0,
    stale_warning_count: int = 0,
    actionable_warning_count: int = 0,
    blocking_error_count: int = 0,
    next_manual_action: str = "Review completed workflow artifacts.",
) -> Path:
    folder = root / "paper_trading" / "workflow_status" / "paper-workflow-status-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "paper_workflow_status_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    total_warning_count = expected_demo_warning_count + stale_warning_count + actionable_warning_count
    resolved_stage = workflow_stage or ("WORKFLOW_COMPLETE" if status == "PASS" else "WORKFLOW_NEEDS_ATTENTION")
    _write_json(
        folder / "metadata.json",
        {
            "workflow_status_id": "paper-workflow-status-a",
            "created_at": f"{DECISION_DATE}T16:15:00",
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
    created_at: str = f"{DECISION_DATE}T14:30:00",
) -> Path:
    folder = root / "historical_backfill" / "status" / f"status-{backfill_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "historical_backfill_status_report.md"
    status_csv = folder / "historical_backfill_status.csv"
    summary_csv = folder / "historical_backfill_status_summary.csv"
    metadata_path = folder / "metadata.json"
    next_action = "Review WARN tasks and only rerun with --accept-cache-write after manual approval."
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
                "cache_write_occurred": False,
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
            },
            {
                "component": "MARKET_CACHE_EXPORT_POLICY_HEALTH",
                "status": health_status,
                "latest_plan_id": plan_id,
                "warning_count": warning_count,
                "error_count": error_count,
                "issue_count": warning_count + error_count,
            },
            {
                "component": "LATEST_MARKET_CACHE_EXPORT_POLICY_PLAN",
                "status": status,
                "latest_plan_id": plan_id,
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
                "latest_plan_id": plan_id,
                "recommendation_count": 2,
                "recommended_count": 1,
                "recommended_with_warnings_count": 1 if warning_count else 0,
                "no_reliable_source_count": 0,
                "no_cache_rows_count": 0,
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
