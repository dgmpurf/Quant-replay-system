import json
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.paper_workflow_status import (
    PaperWorkflowStatusResult,
    infer_next_manual_action,
    infer_paper_workflow_stage,
    run_paper_workflow_status,
)


DECISION_DATE = "2024-05-20"
UNIVERSE = "etf_core"


def test_status_dashboard_handles_no_artifacts(tmp_path: Path) -> None:
    result = run_paper_workflow_status(root=_reports_root(tmp_path), output_dir=tmp_path / "status")

    assert isinstance(result, PaperWorkflowStatusResult)
    assert result.workflow_stage == "NO_CURRENT_CANDIDATES"
    assert result.status == "WARN"
    assert result.next_manual_action == "Run current-candidates."


def test_dashboard_detects_current_candidates_artifact(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _current_candidate(root)

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.current_candidate_status == "READY"
    assert result.workflow_stage == "CURRENT_CANDIDATES_READY"


def test_dashboard_detects_current_to_paper_handoff_artifact(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _current_candidate(root)
    _current_to_paper_handoff(root)

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.handoff_status == "READY"
    assert result.workflow_stage == "HANDOFF_READY"


def test_dashboard_detects_review_template_artifact(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _current_candidate(root)
    _current_to_paper_handoff(root)
    _review_template(root)

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.review_template_status == "READY"
    assert result.workflow_stage == "REVIEW_TEMPLATE_READY"


def test_dashboard_detects_review_template_health_pass(tmp_path: Path) -> None:
    root = _workflow_to_review_template(root := _reports_root(tmp_path))
    _review_template_health(root, status="PASS")

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.review_template_health_status == "PASS"
    assert result.workflow_stage == "REVIEW_TEMPLATE_READY"


def test_dashboard_detects_review_template_health_fail(tmp_path: Path) -> None:
    root = _workflow_to_review_template(_reports_root(tmp_path))
    _review_template_health(root, status="FAIL", errors=1)

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.review_template_health_status == "FAIL"
    assert result.workflow_stage == "REVIEW_TEMPLATE_HEALTH_FAIL"
    assert result.status == "FAIL"


def test_dashboard_detects_reviewed_decisions_artifact(tmp_path: Path) -> None:
    root = _workflow_to_review_template(_reports_root(tmp_path))
    _review_template_health(root, status="PASS")
    _paper_review(root)

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.review_status == "READY"
    assert result.workflow_stage == "REVIEW_READY"


def test_dashboard_detects_daily_paper_report_artifact(tmp_path: Path) -> None:
    root = _workflow_to_review(root := _reports_root(tmp_path))
    _daily_paper(root)

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.daily_paper_status == "REVIEWED_READY"
    assert result.workflow_stage == "DAILY_PAPER_READY"


def test_dashboard_detects_reconciliation_artifact(tmp_path: Path) -> None:
    root = _workflow_to_daily(_reports_root(tmp_path))
    _reconciliation(root, status="PASS")

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.reconciliation_status == "PASS"
    assert result.workflow_stage == "RECONCILIATION_READY"


def test_dashboard_infers_next_manual_action_for_major_stages(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    no_artifacts = run_paper_workflow_status(root=root, output_dir=tmp_path / "s0")
    _current_candidate(root)
    current_ready = run_paper_workflow_status(root=root, output_dir=tmp_path / "s1")
    _current_to_paper_handoff(root)
    handoff_ready = run_paper_workflow_status(root=root, output_dir=tmp_path / "s2")

    assert no_artifacts.next_manual_action == "Run current-candidates."
    assert current_ready.next_manual_action == "Run current-to-paper."
    assert handoff_ready.next_manual_action == "Run current-to-paper-review."
    assert infer_paper_workflow_stage(handoff_ready.status_frame) == "HANDOFF_READY"
    assert infer_next_manual_action(handoff_ready.status_frame) == "Run current-to-paper-review."


def test_dashboard_writes_markdown_report(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _current_candidate(root)

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.artifact_paths["paper_workflow_status_report"].exists()
    content = result.artifact_paths["paper_workflow_status_report"].read_text(encoding="utf-8")
    assert "# Paper Trading Workflow Status" in content


def test_dashboard_writes_status_csv_readable_by_pandas(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _current_candidate(root)

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")
    exported = pd.read_csv(result.artifact_paths["paper_workflow_status_csv"])

    assert "component" in exported.columns
    assert "CURRENT_CANDIDATES" in set(exported["component"])


def test_dashboard_writes_summary_csv_readable_by_pandas(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _current_candidate(root)

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")
    exported = pd.read_csv(result.artifact_paths["paper_workflow_summary"])

    assert exported.iloc[0]["workflow_stage"] == "CURRENT_CANDIDATES_READY"


def test_dashboard_writes_metadata_json(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _current_candidate(root)

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["workflow_status_id"] == result.workflow_status_id
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_cli_paper_workflow_status_works(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)
    _current_candidate(root)

    code = cli.main(["paper-workflow-status", "--root", str(root), "--output-dir", str(tmp_path / "status")])
    output = capsys.readouterr()

    assert code == 0
    assert "Workflow status:" in output.out
    assert "Report path:" in output.out


def test_cli_prints_next_manual_action(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)

    code = cli.main(["paper-workflow-status", "--root", str(root), "--output-dir", str(tmp_path / "status")])
    output = capsys.readouterr()

    assert code == 0
    assert "next_manual_action: Run current-candidates." in output.out


def test_cli_prints_no_live_trading_statement(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)

    code = cli.main(["paper-workflow-status", "--root", str(root), "--output-dir", str(tmp_path / "status")])
    output = capsys.readouterr()

    assert code == 0
    assert "No live trading or broker API was invoked." in output.out


def test_dashboard_output_is_deterministic(tmp_path: Path) -> None:
    root = _workflow_complete(_reports_root(tmp_path))

    first = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")
    second = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")

    assert first.workflow_status_id == second.workflow_status_id
    assert first.status_frame.to_dict("records") == second.status_frame.to_dict("records")
    assert first.summary_frame.to_dict("records") == second.summary_frame.to_dict("records")


def test_dashboard_no_live_trading_or_broker_integration_is_invoked(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _current_candidate(root)

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["paper_trading_only"] is True
    assert not any("broker" in module_name.lower() for module_name in sys.modules)


def test_dashboard_no_network_api_calls_are_used(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _workflow_complete(root)

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.status in {"PASS", "WARN"}
    assert result.audit_metadata["broker_api_invoked"] is False


def test_dashboard_complete_workflow_is_pass(tmp_path: Path) -> None:
    root = _workflow_complete(_reports_root(tmp_path))

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.workflow_stage == "WORKFLOW_COMPLETE"
    assert result.status == "PASS"
    assert result.artifact_health_status == "PASS"


def test_dashboard_prefers_review_artifacts_linked_from_latest_daily_reviewed_decisions_path(tmp_path: Path) -> None:
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

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")
    by_component = {row["component"]: row for row in result.status_frame.to_dict("records")}

    assert by_component["PAPER_REVIEW"]["latest_artifact_id"] == "review-active"
    assert by_component["REVIEW_TEMPLATE_HEALTH"]["latest_artifact_id"] == "health-active"
    assert result.review_template_health_status == "PASS"
    assert result.workflow_stage != "REVIEW_TEMPLATE_HEALTH_WARN"
    assert "stale_warning_count" in by_component["REVIEW_TEMPLATE_HEALTH"]["notes"]
    assert int(result.summary_frame.iloc[0]["stale_warning_count"]) > 0


def test_dashboard_prefers_larger_reviewed_daily_when_created_at_ties(tmp_path: Path) -> None:
    root = _workflow_to_review_template(_reports_root(tmp_path))
    _review_template_health(root, health_id="health-small", status="PASS")
    small_review = _paper_review(
        root,
        review_id="review-small",
        template_health={
            "template_health_check_id": "health-small",
            "template_health_status": "PASS",
            "template_health_report_path": str(
                root / "paper_trading" / "review_template_health" / "health-small" / "review_template_health_report.md"
            ),
            "template_health_issue_count": 0,
            "template_health_error_count": 0,
            "template_health_warning_count": 0,
        },
    )
    _review_template_health(root, health_id="health-large", status="PASS")
    large_review = _paper_review(
        root,
        review_id="review-large",
        template_health={
            "template_health_check_id": "health-large",
            "template_health_status": "PASS",
            "template_health_report_path": str(
                root / "paper_trading" / "review_template_health" / "health-large" / "review_template_health_report.md"
            ),
            "template_health_issue_count": 0,
            "template_health_error_count": 0,
            "template_health_warning_count": 0,
        },
    )
    _daily_paper(
        root,
        journal_id="journal-small",
        reviewed_decisions_path=small_review / "reviewed_decisions.csv",
        decision_count=1,
    )
    _daily_paper(
        root,
        journal_id="journal-large",
        reviewed_decisions_path=large_review / "reviewed_decisions.csv",
        decision_count=9,
    )

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")
    by_component = {row["component"]: row for row in result.status_frame.to_dict("records")}

    assert by_component["DAILY_PAPER"]["latest_artifact_id"] == "journal-large"
    assert by_component["PAPER_REVIEW"]["latest_artifact_id"] == "review-large"


def test_dashboard_active_linked_review_health_warn_drives_stage(tmp_path: Path) -> None:
    root = _workflow_to_review_template(_reports_root(tmp_path))
    _review_template_health(root, health_id="health-stale-pass", status="PASS")
    _review_template_health(root, health_id="health-active-warn", status="WARN", warnings=1)
    active_review = _paper_review(
        root,
        review_id="review-active",
        template_health={
            "template_health_check_id": "health-active-warn",
            "template_health_status": "WARN",
            "template_health_report_path": str(
                root / "paper_trading" / "review_template_health" / "health-active-warn" / "review_template_health_report.md"
            ),
            "template_health_issue_count": 1,
            "template_health_error_count": 0,
            "template_health_warning_count": 1,
        },
    )
    _daily_paper(root, reviewed_decisions_path=active_review / "reviewed_decisions.csv")

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.review_template_health_status == "WARN"
    assert result.workflow_stage == "REVIEW_TEMPLATE_HEALTH_WARN"
    assert int(result.summary_frame.iloc[0]["actionable_warning_count"]) > 0


def test_dashboard_reports_missing_health_when_active_link_has_no_template_health(tmp_path: Path) -> None:
    root = _workflow_to_review_template(_reports_root(tmp_path))
    _review_template_health(root, health_id="unrelated-health", status="PASS")
    active_review = _paper_review(root, review_id="review-active")
    _daily_paper(root, reviewed_decisions_path=active_review / "reviewed_decisions.csv")

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")
    by_component = {row["component"]: row for row in result.status_frame.to_dict("records")}

    assert by_component["PAPER_REVIEW"]["latest_artifact_id"] == "review-active"
    assert by_component["REVIEW_TEMPLATE_HEALTH"]["status"] == "MISSING"
    assert "No template health artifact linked" in by_component["REVIEW_TEMPLATE_HEALTH"]["notes"]
    assert int(result.summary_frame.iloc[0]["blocking_error_count"]) > 0


def test_dashboard_expected_demo_empty_fills_warning_changes_next_action(tmp_path: Path) -> None:
    root = _workflow_to_review_template(_reports_root(tmp_path))
    _review_template_health(root, status="PASS")
    active_review = _paper_review(
        root,
        template_health={
            "template_health_check_id": "template-health-a",
            "template_health_status": "PASS",
            "template_health_report_path": str(
                root / "paper_trading" / "review_template_health" / "template-health-a" / "review_template_health_report.md"
            ),
            "template_health_issue_count": 0,
            "template_health_error_count": 0,
            "template_health_warning_count": 0,
        },
    )
    _daily_paper(root, reviewed_decisions_path=active_review / "reviewed_decisions.csv")
    _reconciliation(root, status="PASS")
    _paper_artifact_index(root)
    _paper_artifact_health_with_issues(
        root,
        status="WARN",
        issues=[
            {
                "artifact_type": "DAILY",
                "artifact_id": "journal-a",
                "path_field": "fills_path",
                "path_value": str(root / "paper_trading" / "daily" / f"{DECISION_DATE}_journal-a" / "fills.csv"),
                "severity": "WARN",
                "issue_code": "CSV_EMPTY",
                "issue_message": "Required CSV artifact has no rows.",
                "suggested_action": "Confirm whether an empty artifact is expected.",
            }
        ],
    )

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")
    by_component = {row["component"]: row for row in result.status_frame.to_dict("records")}
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.status == "WARN"
    assert result.next_manual_action != "Review warnings/errors in workflow status and health reports."
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action
    assert by_component["PAPER_ARTIFACT_HEALTH"]["warning_classification"] == "EXPECTED_DEMO_WARNING"
    assert summary["expected_demo_warning_count"] == 1
    assert summary["actionable_warning_count"] == 0
    assert summary["blocking_error_count"] == 0


def test_dashboard_watch_only_no_fills_demo_has_specific_stage(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _current_candidate(root)
    _current_candidate_index(root)
    _current_candidate_health(root, status="PASS")
    _current_to_paper_handoff(
        root,
        warnings=[
            "Health check skipped for direct candidates_path handoff.",
            "No fills_path provided; continuing with empty paper fills.",
            "Reconciliation: No fills supplied for reconciliation.",
            "1 decision(s) pending manual review.",
            "No manual paper fills loaded.",
        ],
    )
    _review_template(root)
    _review_template_health(root, health_id="template-health-a", status="PASS")
    active_review = _paper_review(
        root,
        template_health={
            "template_health_check_id": "template-health-a",
            "template_health_status": "PASS",
            "template_health_report_path": str(
                root / "paper_trading" / "review_template_health" / "template-health-a" / "review_template_health_report.md"
            ),
            "template_health_issue_count": 0,
            "template_health_error_count": 0,
            "template_health_warning_count": 0,
        },
    )
    _daily_paper(
        root,
        reviewed_decisions_path=active_review / "reviewed_decisions.csv",
        decision_count=1,
        fill_count=0,
        open_position_count=0,
        closed_trade_count=0,
        manual_review_status_summary={"WATCH_ONLY": 1},
        warnings=[
            "No fills_path provided; continuing with empty paper fills.",
            "Reconciliation: No fills supplied for reconciliation.",
            "No manual paper fills loaded.",
        ],
    )
    _reconciliation(root, status="PASS")
    _paper_artifact_index(root)
    _paper_artifact_health_with_issues(
        root,
        status="WARN",
        issues=[
            {
                "artifact_type": "DAILY",
                "artifact_id": "journal-a",
                "path_field": "fills_path",
                "path_value": str(root / "paper_trading" / "daily" / f"{DECISION_DATE}_journal-a" / "fills.csv"),
                "severity": "WARN",
                "issue_code": "CSV_EMPTY",
                "issue_message": "Required CSV artifact has no rows.",
                "suggested_action": "Confirm whether an empty artifact is expected.",
            }
        ],
    )

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")
    summary = result.summary_frame.iloc[0].to_dict()
    by_component = {row["component"]: row for row in result.status_frame.to_dict("records")}

    assert result.status == "WARN"
    assert result.workflow_stage == "WATCH_ONLY_DEMO_VALIDATED_NO_FILLS"
    assert "Demo WATCH_ONLY paper workflow validated" in result.next_manual_action
    assert summary["watch_only_count"] == 1
    assert summary["approved_count"] == 0
    assert summary["open_position_count"] == 0
    assert summary["closed_trade_count"] == 0
    assert summary["paper_demo_validated"] is True
    assert summary["expected_no_fills_warning_count"] == 3
    assert summary["actionable_warning_count"] == 0
    assert summary["blocking_error_count"] == 0
    assert by_component["CURRENT_TO_PAPER_HANDOFF"]["warning_classification"] == "EXPECTED_DEMO_WARNING"


def test_dashboard_approved_for_paper_prevents_watch_only_demo_stage(tmp_path: Path) -> None:
    root = _workflow_to_review_template(_reports_root(tmp_path))
    _review_template_health(root, health_id="template-health-a", status="PASS")
    active_review = _paper_review(
        root,
        manual_review_status="APPROVED_FOR_PAPER",
        template_health={
            "template_health_check_id": "template-health-a",
            "template_health_status": "PASS",
            "template_health_report_path": str(
                root / "paper_trading" / "review_template_health" / "template-health-a" / "review_template_health_report.md"
            ),
            "template_health_issue_count": 0,
            "template_health_error_count": 0,
            "template_health_warning_count": 0,
        },
    )
    _daily_paper(
        root,
        reviewed_decisions_path=active_review / "reviewed_decisions.csv",
        decision_count=1,
        fill_count=0,
        open_position_count=0,
        closed_trade_count=0,
        manual_review_status_summary={"APPROVED_FOR_PAPER": 1},
    )
    _reconciliation(root, status="PASS")
    _paper_artifact_index(root)
    _paper_artifact_health(root, status="PASS")

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.workflow_stage == "WORKFLOW_NEEDS_ATTENTION"
    assert result.next_manual_action == "Review warnings/errors in workflow status and health reports."
    assert summary["paper_demo_validated"] is False
    assert summary["approved_count"] == 1
    assert summary["actionable_warning_count"] > 0


def test_dashboard_unexpected_open_positions_prevent_watch_only_demo_stage(tmp_path: Path) -> None:
    root = _workflow_to_review_template(_reports_root(tmp_path))
    _review_template_health(root, health_id="template-health-a", status="PASS")
    active_review = _paper_review(
        root,
        template_health={
            "template_health_check_id": "template-health-a",
            "template_health_status": "PASS",
            "template_health_report_path": str(
                root / "paper_trading" / "review_template_health" / "template-health-a" / "review_template_health_report.md"
            ),
            "template_health_issue_count": 0,
            "template_health_error_count": 0,
            "template_health_warning_count": 0,
        },
    )
    _daily_paper(
        root,
        reviewed_decisions_path=active_review / "reviewed_decisions.csv",
        decision_count=1,
        fill_count=0,
        open_position_count=1,
        closed_trade_count=0,
        manual_review_status_summary={"WATCH_ONLY": 1},
    )
    _reconciliation(root, status="PASS")
    _paper_artifact_index(root)
    _paper_artifact_health(root, status="PASS")

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.workflow_stage != "WATCH_ONLY_DEMO_VALIDATED_NO_FILLS"
    assert summary["paper_demo_validated"] is False
    assert summary["open_position_count"] == 1


def test_dashboard_unreadable_active_artifact_remains_blocking_error(tmp_path: Path) -> None:
    root = _workflow_to_daily(_reports_root(tmp_path))
    _reconciliation(root, status="PASS")
    _paper_artifact_index(root)
    _paper_artifact_health(root, status="FAIL")

    result = run_paper_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.workflow_stage == "WORKFLOW_NEEDS_ATTENTION"
    assert result.next_manual_action == "Review warnings/errors in workflow status and health reports."
    assert int(result.summary_frame.iloc[0]["blocking_error_count"]) > 0


def _reports_root(tmp_path: Path) -> Path:
    root = tmp_path / "reports"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _workflow_to_review_template(root: Path) -> Path:
    _current_candidate(root)
    _current_candidate_index(root)
    _current_candidate_health(root, status="PASS")
    _current_to_paper_handoff(root)
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
    _paper_artifact_index(root)
    _paper_artifact_health(root, status="PASS")
    return root


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
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _current_candidate_index(root: Path) -> Path:
    folder = root / "current_candidates" / "index"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "current_candidate_artifact_index.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "index_id": "cci-a",
            "created_at": f"{DECISION_DATE}T16:00:00",
            "artifact_count": 1,
            "output_files": {"current_candidate_artifact_index": str(report)},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _current_candidate_health(root: Path, *, status: str = "PASS") -> Path:
    folder = root / "current_candidates" / "health" / "cch-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "current_candidate_artifact_health_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "health_check_id": "cch-a",
            "created_at": f"{DECISION_DATE}T16:01:00",
            "status": status,
            "issue_count": 0 if status == "PASS" else 1,
            "error_count": 1 if status == "FAIL" else 0,
            "warning_count": 1 if status == "WARN" else 0,
            "output_files": {"current_candidate_artifact_health_report": str(report)},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _current_to_paper_handoff(root: Path, *, warnings: list[str] | None = None) -> Path:
    folder = root / "current_to_paper_handoff" / "handoff-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "handoff_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "handoff_metadata.json",
        {
            "handoff_id": "handoff-a",
            "created_at": f"{DECISION_DATE}T16:05:00",
            "selected_decision_date": DECISION_DATE,
            "selected_universe_name": UNIVERSE,
            "selected_run_id": "run-a",
            "paper_journal_id": "journal-a",
            "output_files": {"handoff_report": str(report)},
            "warnings": warnings or [],
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
            "created_at": f"{DECISION_DATE}T16:10:00",
            "decision_count": 1,
            "output_files": {"review_handoff_report": str(report), "review_updates_template": str(folder / "review_updates_template.csv")},
            "warnings": [],
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
            "created_at": f"{DECISION_DATE}T16:15:00",
            "status": status,
            "issue_count": errors + warnings,
            "error_count": errors,
            "warning_count": warnings,
            "output_files": {"review_template_health_report": str(report)},
            "warnings": [],
        },
    )
    return folder


def _paper_review(
    root: Path,
    *,
    review_id: str = "review-a",
    template_health: dict | None = None,
    warnings: list[str] | None = None,
    manual_review_status: str = "WATCH_ONLY",
    action: str = "SKIP",
) -> Path:
    folder = root / "paper_trading" / "reviews" / review_id
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "paper_review_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    reviewed = folder / "reviewed_decisions.csv"
    pd.DataFrame(
        [
            {
                "decision_id": "d1",
                "symbol": "510300",
                "action": action,
                "manual_review_status": manual_review_status,
            }
        ]
    ).to_csv(reviewed, index=False)
    metadata = {
        "review_id": review_id,
        "created_at": f"{DECISION_DATE}T16:20:00",
        "output_files": {"paper_review_report": str(report), "reviewed_decisions": str(reviewed)},
        "warnings": warnings or [],
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
    }
    if template_health is not None:
        metadata["template_health"] = template_health
    _write_json(
        folder / "metadata.json",
        metadata,
    )
    return folder


def _daily_paper(
    root: Path,
    *,
    journal_id: str = "journal-a",
    reviewed_decisions_path: Path | None = None,
    decision_count: int | None = None,
    fill_count: int | None = None,
    open_position_count: int | None = None,
    closed_trade_count: int | None = None,
    manual_review_status_summary: dict[str, int] | None = None,
    warnings: list[str] | None = None,
) -> Path:
    folder = root / "paper_trading" / "daily" / f"{DECISION_DATE}_{journal_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "paper_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    metadata = {
            "paper_date": DECISION_DATE,
            "journal_id": journal_id,
            "created_at": f"{DECISION_DATE}T16:30:00",
            "reviewed_decisions_used": True,
            "reconciliation": {"status": "", "issue_count": 0, "error_count": 0, "warning_count": 0},
            "output_files": {"paper_report": str(report), "decisions": str(folder / "decisions.csv")},
            "warnings": warnings or [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "paper_trading_only": True,
        }
    if decision_count is not None:
        metadata["decision_count"] = decision_count
    if fill_count is not None:
        metadata["fill_count"] = fill_count
    if open_position_count is not None:
        metadata["open_position_count"] = open_position_count
    if closed_trade_count is not None:
        metadata["closed_trade_count"] = closed_trade_count
    if manual_review_status_summary is not None:
        metadata["manual_review_status_summary"] = manual_review_status_summary
    _write_json(folder / "metadata.json", metadata)
    if reviewed_decisions_path is not None:
        metadata_path = folder / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["reviewed_decisions_path"] = str(reviewed_decisions_path)
        metadata["output_files"]["reviewed_decisions"] = str(reviewed_decisions_path)
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return folder


def _reconciliation(root: Path, *, status: str = "PASS") -> Path:
    folder = root / "paper_trading" / "reconciliation" / "recon-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "reconciliation_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "reconciliation_id": "recon-a",
            "created_at": f"{DECISION_DATE}T16:35:00",
            "status": status,
            "issue_count": 0 if status == "PASS" else 1,
            "error_count": 1 if status == "FAIL" else 0,
            "warning_count": 1 if status == "WARN" else 0,
            "output_files": {"reconciliation_report": str(report)},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "paper_trading_only": True,
        },
    )
    return folder


def _paper_artifact_index(root: Path) -> Path:
    folder = root / "paper_trading" / "index"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "paper_artifact_index.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "index_id": "paper-index-a",
            "created_at": f"{DECISION_DATE}T16:40:00",
            "artifact_count": 3,
            "output_files": {"paper_artifact_index": str(report)},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "paper_trading_only": True,
        },
    )
    return folder


def _paper_artifact_health(root: Path, *, status: str = "PASS") -> Path:
    folder = root / "paper_trading" / "health" / "paper-health-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "artifact_health_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "health_check_id": "paper-health-a",
            "created_at": f"{DECISION_DATE}T16:41:00",
            "status": status,
            "issue_count": 0 if status == "PASS" else 1,
            "error_count": 1 if status == "FAIL" else 0,
            "warning_count": 1 if status == "WARN" else 0,
            "output_files": {"artifact_health_report": str(report)},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "paper_trading_only": True,
        },
    )
    return folder


def _paper_artifact_health_with_issues(
    root: Path,
    *,
    status: str,
    issues: list[dict],
) -> Path:
    folder = root / "paper_trading" / "health" / "paper-health-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "artifact_health_report.md"
    issues_path = folder / "artifact_health_issues.csv"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    pd.DataFrame(issues).to_csv(issues_path, index=False)
    error_count = sum(1 for issue in issues if issue.get("severity") == "ERROR")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "WARN")
    _write_json(
        folder / "metadata.json",
        {
            "health_check_id": "paper-health-a",
            "created_at": f"{DECISION_DATE}T16:41:00",
            "status": status,
            "issue_count": len(issues),
            "error_count": error_count,
            "warning_count": warning_count,
            "output_files": {
                "artifact_health_report": str(report),
                "artifact_health_issues": str(issues_path),
            },
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "paper_trading_only": True,
        },
    )
    return folder


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
