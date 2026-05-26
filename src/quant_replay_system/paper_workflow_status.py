"""Local-only paper trading workflow status dashboard."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_replay_system.config import PaperWorkflowStatusSettings, Settings, load_settings


PAPER_WORKFLOW_STATUS_LIMITATIONS = [
    "Scans local artifact metadata only.",
    "Does not regenerate missing artifacts or rerun workflow steps.",
    "Does not apply reviews, reconcile fills, place orders, or call broker APIs.",
    "Stage inference is conservative when artifacts are missing or metadata is incomplete.",
]

STATUS_COLUMNS = [
    "component",
    "status",
    "latest_artifact_id",
    "decision_date",
    "report_path",
    "metadata_path",
    "issue_count",
    "warning_count",
    "error_count",
    "total_warning_count",
    "expected_demo_warning_count",
    "stale_warning_count",
    "actionable_warning_count",
    "blocking_error_count",
    "diagnostic_reconciliation_failure_count",
    "active_reconciliation_error_count",
    "warning_classification",
    "next_action",
    "notes",
]

SUMMARY_COLUMNS = [
    "workflow_stage",
    "status",
    "latest_decision_date",
    "current_candidate_status",
    "handoff_status",
    "review_template_status",
    "review_template_health_status",
    "review_status",
    "daily_paper_status",
    "reconciliation_status",
    "artifact_index_status",
    "artifact_health_status",
    "total_warning_count",
    "expected_demo_warning_count",
    "expected_no_fills_warning_count",
    "stale_warning_count",
    "actionable_warning_count",
    "actionable_paper_warning_count",
    "blocking_error_count",
    "diagnostic_reconciliation_failure_count",
    "active_reconciliation_error_count",
    "watch_only_count",
    "approved_count",
    "open_position_count",
    "closed_trade_count",
    "paper_demo_validated",
    "next_manual_action",
]

EXPECTED_DEMO_WARNING = "EXPECTED_DEMO_WARNING"
STALE_ARTIFACT_WARNING = "STALE_ARTIFACT_WARNING"
ACTIONABLE_WARNING = "ACTIONABLE_WARNING"
BLOCKING_ERROR = "BLOCKING_ERROR"
WATCH_ONLY_DEMO_STAGE = "WATCH_ONLY_DEMO_VALIDATED_NO_FILLS"

DEMO_WORKFLOW_NEXT_ACTION = (
    "Demo WATCH_ONLY paper workflow validated; no fills were supplied. Proceed to fill reconciliation "
    "only if testing fills, or return to data-source / strategy research."
)

STALE_ONLY_NEXT_ACTION = (
    "Active workflow chain is not blocked; stale warning artifacts remain indexed for audit."
)

COMPONENTS = [
    "CURRENT_CANDIDATES",
    "CURRENT_CANDIDATE_INDEX",
    "CURRENT_CANDIDATE_HEALTH",
    "CURRENT_TO_PAPER_HANDOFF",
    "REVIEW_TEMPLATE",
    "REVIEW_TEMPLATE_HEALTH",
    "PAPER_REVIEW",
    "DAILY_PAPER",
    "RECONCILIATION",
    "PAPER_ARTIFACT_INDEX",
    "PAPER_ARTIFACT_HEALTH",
]


@dataclass(frozen=True)
class PaperWorkflowStatusArtifactPaths:
    artifact_dir: Path
    paper_workflow_status_report: Path
    paper_workflow_status_csv: Path
    paper_workflow_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "paper_workflow_status_report": self.paper_workflow_status_report,
            "paper_workflow_status_csv": self.paper_workflow_status_csv,
            "paper_workflow_summary": self.paper_workflow_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PaperWorkflowStatusResult:
    workflow_status_id: str
    status: str
    latest_decision_date: str
    current_candidate_status: str
    handoff_status: str
    review_template_status: str
    review_template_health_status: str
    review_status: str
    daily_paper_status: str
    reconciliation_status: str
    artifact_index_status: str
    artifact_health_status: str
    next_manual_action: str
    workflow_stage: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_paper_workflow_status(
    *,
    root: str | Path | None = None,
    current_candidates_root: str | Path | None = None,
    paper_trading_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    decision_date: str | pd.Timestamp | None = None,
    universe_name: str | None = None,
    config: Settings | PaperWorkflowStatusSettings | dict[str, Any] | str | Path | None = None,
) -> PaperWorkflowStatusResult:
    """Scan local paper workflow artifacts and write a status dashboard."""

    project_settings, workflow_settings = _resolve_settings(config)
    if workflow_settings.enable_live_trading or workflow_settings.enable_broker_api:
        raise ValueError("Paper workflow status dashboard cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else workflow_settings.root_dir
    effective_current_root = (
        Path(current_candidates_root)
        if current_candidates_root is not None
        else workflow_settings.current_candidates_root
    )
    effective_paper_root = Path(paper_trading_root) if paper_trading_root is not None else workflow_settings.paper_trading_root
    effective_output_dir = Path(output_dir) if output_dir is not None else workflow_settings.output_dir
    if root is not None and current_candidates_root is None:
        effective_current_root = effective_root / "current_candidates"
    if root is not None and paper_trading_root is None:
        effective_paper_root = effective_root / "paper_trading"

    scan = scan_paper_workflow_artifacts(
        root=effective_root,
        current_candidates_root=effective_current_root,
        paper_trading_root=effective_paper_root,
        decision_date=decision_date,
        universe_name=universe_name,
    )
    status_frame = build_paper_workflow_status_frame(
        scan,
        decision_date=decision_date,
        universe_name=universe_name,
    )
    workflow_stage = infer_paper_workflow_stage(status_frame)
    next_manual_action = infer_next_manual_action(status_frame, workflow_stage=workflow_stage)
    summary_frame = summarize_paper_workflow_status(
        status_frame,
        workflow_stage=workflow_stage,
        next_manual_action=next_manual_action,
    )
    summary = summary_frame.iloc[0].to_dict()
    workflow_status_id = generate_paper_workflow_status_id(
        status_frame,
        decision_date=decision_date,
        config_version=workflow_settings.config_version,
    )
    paths = resolve_paper_workflow_status_paths(effective_output_dir, workflow_status_id)
    warnings = _dashboard_warnings(status_frame, workflow_stage)
    audit_metadata = {
        "workflow_status_id": workflow_status_id,
        "root_dir": effective_root,
        "current_candidates_root": effective_current_root,
        "paper_trading_root": effective_paper_root,
        "decision_date_filter": _date_string(decision_date),
        "universe_name_filter": _string_or_empty(universe_name),
        "workflow_stage": workflow_stage,
        "strict": workflow_settings.strict,
        "config_version": workflow_settings.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
    }
    result = PaperWorkflowStatusResult(
        workflow_status_id=workflow_status_id,
        status=str(summary.get("status", "WARN")),
        latest_decision_date=str(summary.get("latest_decision_date", "")),
        current_candidate_status=str(summary.get("current_candidate_status", "MISSING")),
        handoff_status=str(summary.get("handoff_status", "MISSING")),
        review_template_status=str(summary.get("review_template_status", "MISSING")),
        review_template_health_status=str(summary.get("review_template_health_status", "MISSING")),
        review_status=str(summary.get("review_status", "MISSING")),
        daily_paper_status=str(summary.get("daily_paper_status", "MISSING")),
        reconciliation_status=str(summary.get("reconciliation_status", "MISSING")),
        artifact_index_status=str(summary.get("artifact_index_status", "MISSING")),
        artifact_health_status=str(summary.get("artifact_health_status", "MISSING")),
        next_manual_action=next_manual_action,
        workflow_stage=workflow_stage,
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=PAPER_WORKFLOW_STATUS_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if workflow_settings.write_artifacts:
        write_paper_workflow_status_artifacts(result)
    _ = project_settings
    return result


def scan_paper_workflow_artifacts(
    *,
    root: str | Path,
    current_candidates_root: str | Path,
    paper_trading_root: str | Path,
    decision_date: str | pd.Timestamp | None = None,
    universe_name: str | None = None,
) -> pd.DataFrame:
    """Scan local metadata files for paper workflow components."""

    root_path = Path(root)
    current_root = Path(current_candidates_root)
    paper_root = Path(paper_trading_root)
    requested_date = _date_string(decision_date)
    requested_universe = _string_or_empty(universe_name)
    records: list[dict[str, Any]] = []

    records.extend(_scan_current_candidates(current_root, requested_date, requested_universe))
    records.extend(_scan_current_candidate_index(current_root))
    records.extend(_scan_current_candidate_health(current_root))
    records.extend(_scan_current_to_paper_handoff(root_path / "current_to_paper_handoff", requested_date, requested_universe))
    records.extend(_scan_review_template_handoff(root_path / "current_to_paper_review_handoff"))
    records.extend(_scan_review_template_health(paper_root / "review_template_health"))
    records.extend(_scan_paper_reviews(paper_root / "reviews"))
    records.extend(_scan_daily_paper(paper_root / "daily", requested_date))
    records.extend(_scan_reconciliation(paper_root / "reconciliation"))
    records.extend(_scan_paper_artifact_index(paper_root))
    records.extend(_scan_paper_artifact_health(paper_root))
    return _finalize_scan_frame(pd.DataFrame(records))


def build_paper_workflow_status_frame(
    scan_frame: pd.DataFrame,
    *,
    decision_date: str | pd.Timestamp | None = None,
    universe_name: str | None = None,
) -> pd.DataFrame:
    """Build one status row per workflow component."""

    frame = _finalize_scan_frame(scan_frame)
    active_chain = _active_reviewed_paper_chain(frame)
    rows: list[dict[str, Any]] = []
    for component in COMPONENTS:
        component_rows = frame.loc[frame["component"] == component]
        linked_missing = _linked_missing_component(component, active_chain)
        if linked_missing is not None:
            rows.append(linked_missing)
            continue
        if component_rows.empty:
            rows.append(_missing_status_row(component))
            continue
        latest = active_chain.get(component, _latest_record(component_rows)).copy()
        latest = _annotate_stale_component_warnings(latest, component_rows)
        latest["next_action"] = _component_next_action(component, latest.get("status", ""))
        rows.append(latest)
    _ = decision_date, universe_name
    status_frame = _finalize_status_frame(pd.DataFrame(rows))
    return _classify_paper_workflow_actionability(status_frame)


def _active_reviewed_paper_chain(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Resolve the active paper-review chain from the selected daily paper artifact."""

    chain: dict[str, dict[str, Any]] = {}
    daily = _active_daily_record(frame)
    if daily is None:
        return chain
    chain["DAILY_PAPER"] = daily
    if daily.get("status") != "REVIEWED_READY":
        return chain
    daily_metadata = _metadata_for_row(daily)
    if not _daily_reviewed_decisions_path(daily_metadata):
        return chain

    review = _review_record_linked_to_daily(frame, daily)
    if review is not None:
        chain["PAPER_REVIEW"] = review
        template_health = _template_health_record_linked_to_review(frame, review)
        if template_health is not None:
            chain["REVIEW_TEMPLATE_HEALTH"] = template_health
        else:
            chain["REVIEW_TEMPLATE_HEALTH_MISSING"] = _missing_status_row(
                "REVIEW_TEMPLATE_HEALTH",
                notes="No template health artifact linked to active reviewed decisions.",
            )
    else:
        chain["PAPER_REVIEW_MISSING"] = _missing_status_row(
            "PAPER_REVIEW",
            notes="No paper review artifact linked to active reviewed decisions.",
        )
        chain["REVIEW_TEMPLATE_HEALTH_MISSING"] = _missing_status_row(
            "REVIEW_TEMPLATE_HEALTH",
            notes="No linked paper review artifact was available for template health selection.",
        )
    reconciliation = _reconciliation_record_linked_to_daily(frame, daily)
    if reconciliation is not None:
        chain["RECONCILIATION"] = reconciliation
    return chain


def _active_daily_record(frame: pd.DataFrame) -> dict[str, Any] | None:
    daily_rows = frame.loc[frame["component"] == "DAILY_PAPER"]
    if daily_rows.empty:
        return None
    reviewed_rows = daily_rows.loc[daily_rows["status"] == "REVIEWED_READY"]
    if not reviewed_rows.empty:
        return _latest_daily_record(reviewed_rows)
    return _latest_daily_record(daily_rows)


def _latest_daily_record(frame: pd.DataFrame) -> dict[str, Any]:
    sortable = frame.copy(deep=True)
    sortable["_sort_date"] = sortable["decision_date"].map(lambda value: _date_string(value))
    sortable["_sort_created"] = sortable["created_at"].map(_string_or_empty)
    sortable["_sort_decision_count"] = sortable["metadata_path"].map(
        lambda value: _int_or_zero(_metadata_for_row({"metadata_path": value}).get("decision_count"))
    )
    sortable = sortable.sort_values(
        ["_sort_date", "_sort_created", "_sort_decision_count", "latest_artifact_id", "metadata_path"],
        na_position="last",
    )
    return sortable.iloc[-1].drop(
        labels=["_sort_date", "_sort_created", "_sort_decision_count"],
        errors="ignore",
    ).to_dict()


def _review_record_linked_to_daily(frame: pd.DataFrame, daily: dict[str, Any]) -> dict[str, Any] | None:
    daily_metadata = _metadata_for_row(daily)
    reviewed_path = _daily_reviewed_decisions_path(daily_metadata)
    review_id = _artifact_id_from_path(reviewed_path)
    review_rows = frame.loc[frame["component"] == "PAPER_REVIEW"]
    if review_rows.empty:
        return None

    matches = []
    for row in review_rows.to_dict("records"):
        review_metadata = _metadata_for_row(row)
        review_output = _output_files(review_metadata).get("reviewed_decisions") or review_metadata.get(
            "reviewed_decisions_path"
        )
        metadata_review_id = _string_or_empty(review_metadata.get("review_id")) or _artifact_id_from_path(
            row.get("metadata_path")
        )
        if (reviewed_path and _paths_match(review_output, reviewed_path)) or (
            review_id and metadata_review_id == review_id
        ):
            matches.append(row)
    if matches:
        return _latest_record(pd.DataFrame(matches))
    return None


def _template_health_record_linked_to_review(frame: pd.DataFrame, review: dict[str, Any]) -> dict[str, Any] | None:
    review_metadata = _metadata_for_row(review)
    template_health = review_metadata.get("template_health") if isinstance(review_metadata.get("template_health"), dict) else {}
    health_id = _string_or_empty(template_health.get("template_health_check_id"))
    health_report = _string_or_empty(template_health.get("template_health_report_path"))
    health_rows = frame.loc[frame["component"] == "REVIEW_TEMPLATE_HEALTH"]

    matches = []
    for row in health_rows.to_dict("records"):
        if (health_id and _string_or_empty(row.get("latest_artifact_id")) == health_id) or (
            health_report and _paths_match(row.get("report_path"), health_report)
        ):
            matches.append(row)
    if matches:
        return _latest_record(pd.DataFrame(matches))

    status = _string_or_empty(template_health.get("template_health_status"))
    if status:
        return _record(
            component="REVIEW_TEMPLATE_HEALTH",
            status=status,
            latest_artifact_id=health_id or _artifact_id_from_path(health_report),
            report_path=health_report,
            metadata_path="",
            issue_count=_int_or_zero(template_health.get("template_health_issue_count")),
            warning_count=_int_or_zero(template_health.get("template_health_warning_count")),
            error_count=_int_or_zero(template_health.get("template_health_error_count")),
            notes="linked_from_active_paper_review_metadata",
            created_at=review.get("created_at"),
        )
    return None


def _reconciliation_record_linked_to_daily(frame: pd.DataFrame, daily: dict[str, Any]) -> dict[str, Any] | None:
    daily_metadata = _metadata_for_row(daily)
    reconciliation = daily_metadata.get("reconciliation") if isinstance(daily_metadata.get("reconciliation"), dict) else {}
    report_path = _string_or_empty(reconciliation.get("report_path"))
    reconciliation_id = _string_or_empty(reconciliation.get("reconciliation_id")) or _artifact_id_from_path(report_path)
    reconciliation_rows = frame.loc[frame["component"] == "RECONCILIATION"]

    matches = []
    for row in reconciliation_rows.to_dict("records"):
        row_metadata = _metadata_for_row(row)
        row_output = _output_files(row_metadata).get("reconciliation_report")
        row_id = (
            _string_or_empty(row_metadata.get("reconciliation_id"))
            or _string_or_empty(row.get("latest_artifact_id"))
            or _artifact_id_from_path(row.get("metadata_path"))
        )
        if (report_path and (_paths_match(row.get("report_path"), report_path) or _paths_match(row_output, report_path))) or (
            reconciliation_id and row_id == reconciliation_id
        ):
            matches.append(row)
    if matches:
        return _latest_record(pd.DataFrame(matches))

    status = _string_or_empty(reconciliation.get("status"))
    if status:
        return _record(
            component="RECONCILIATION",
            status=status,
            latest_artifact_id=reconciliation_id,
            report_path=report_path,
            metadata_path="",
            issue_count=_int_or_zero(reconciliation.get("issue_count")),
            warning_count=_int_or_zero(reconciliation.get("warning_count")),
            error_count=_int_or_zero(reconciliation.get("error_count")),
            notes="linked_from_active_daily_metadata",
            created_at=daily.get("created_at"),
        )
    return None


def _linked_missing_component(component: str, active_chain: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    if component == "PAPER_REVIEW" and "PAPER_REVIEW_MISSING" in active_chain:
        return active_chain["PAPER_REVIEW_MISSING"]
    if component == "REVIEW_TEMPLATE_HEALTH" and "REVIEW_TEMPLATE_HEALTH_MISSING" in active_chain:
        return active_chain["REVIEW_TEMPLATE_HEALTH_MISSING"]
    return None


def _annotate_stale_component_warnings(selected: dict[str, Any], component_rows: pd.DataFrame) -> dict[str, Any]:
    if component_rows.empty:
        return selected
    selected_path = _string_or_empty(selected.get("metadata_path"))
    selected_id = _string_or_empty(selected.get("latest_artifact_id"))
    selected_component = _string_or_empty(selected.get("component"))
    stale_warning_count = 0
    stale_error_count = 0
    diagnostic_reconciliation_failure_count = 0
    for row in component_rows.to_dict("records"):
        same_path = selected_path and _string_or_empty(row.get("metadata_path")) == selected_path
        same_id = selected_id and _string_or_empty(row.get("latest_artifact_id")) == selected_id
        if same_path or same_id:
            continue
        stale_warning_count += _int_or_zero(row.get("warning_count"))
        stale_error_count += _int_or_zero(row.get("error_count"))
        if _string_or_empty(row.get("status")) == "WARN":
            stale_warning_count += 1
        if _string_or_empty(row.get("status")) == "FAIL":
            stale_error_count += 1
            if selected_component == "RECONCILIATION":
                diagnostic_reconciliation_failure_count += 1
    if not stale_warning_count and not stale_error_count:
        annotated = selected.copy()
    else:
        annotated = selected.copy()
        notes = _string_or_empty(annotated.get("notes"))
        stale_note = f"stale_warning_count={stale_warning_count}; stale_error_count={stale_error_count}"
        annotated["notes"] = f"{notes}; {stale_note}" if notes else stale_note
    if selected_component == "RECONCILIATION":
        annotated["diagnostic_reconciliation_failure_count"] = diagnostic_reconciliation_failure_count
        annotated["active_reconciliation_error_count"] = (
            max(_int_or_zero(annotated.get("error_count")), 1)
            if _string_or_empty(annotated.get("status")) == "FAIL"
            else 0
        )
    return annotated


def _classify_paper_workflow_actionability(status_frame: pd.DataFrame) -> pd.DataFrame:
    frame = _finalize_status_frame(status_frame)
    if frame.empty:
        return frame
    context = _paper_warning_context(frame)
    records = []
    for row in frame.to_dict("records"):
        classified = dict(row)
        counts = _component_warning_actionability(classified, context)
        classified.update(counts)
        classified["warning_classification"] = _classification_label(counts)
        records.append(classified)
    return _finalize_status_frame(pd.DataFrame(records))


def _paper_warning_context(frame: pd.DataFrame) -> dict[str, Any]:
    by_component = {row["component"]: row for row in frame.to_dict("records")}
    daily = by_component.get("DAILY_PAPER", {})
    current = by_component.get("CURRENT_CANDIDATES", {})
    review = by_component.get("PAPER_REVIEW", {})
    reconciliation = by_component.get("RECONCILIATION", {})
    daily_metadata = _metadata_for_row(daily)
    active_ids = {
        ("DAILY", _string_or_empty(daily.get("latest_artifact_id"))),
        ("REVIEW", _string_or_empty(review.get("latest_artifact_id"))),
        ("RECONCILIATION", _string_or_empty(reconciliation.get("latest_artifact_id"))),
    }
    return {
        "active_daily_id": _string_or_empty(daily.get("latest_artifact_id")),
        "active_current_run_id": _string_or_empty(current.get("latest_artifact_id")),
        "active_paper_artifact_ids": {item for item in active_ids if item[1]},
        "watch_only_no_fills_demo": _is_watch_only_no_fills_daily(daily_metadata),
    }


def _component_warning_actionability(row: dict[str, Any], context: dict[str, Any]) -> dict[str, int]:
    component = _string_or_empty(row.get("component"))
    warning_count = _int_or_zero(row.get("warning_count"))
    error_count = _int_or_zero(row.get("error_count"))
    stale_warning_count = _parse_note_count(row.get("notes"), "stale_warning_count")
    blocking_error_count = error_count
    if _string_or_empty(row.get("status")) == "FAIL":
        blocking_error_count = max(blocking_error_count, 1)
    if _string_or_empty(row.get("status")) == "MISSING" and "linked to active" in _string_or_empty(row.get("notes")):
        blocking_error_count = max(blocking_error_count, 1)

    if component == "PAPER_ARTIFACT_HEALTH":
        issue_counts = _paper_artifact_health_issue_actionability(row, context)
        if issue_counts is not None:
            return issue_counts | {
                "total_warning_count": issue_counts["expected_demo_warning_count"]
                + issue_counts["stale_warning_count"]
                + issue_counts["actionable_warning_count"],
            }
        metadata_counts = _metadata_actionability_counts(row)
        if metadata_counts is not None:
            return metadata_counts

    if component == "CURRENT_CANDIDATE_HEALTH":
        issue_counts = _current_candidate_health_issue_actionability(row, context)
        if issue_counts is not None:
            return issue_counts | {
                "total_warning_count": issue_counts["expected_demo_warning_count"]
                + issue_counts["stale_warning_count"]
                + issue_counts["actionable_warning_count"],
            }
        metadata_counts = _metadata_actionability_counts(row)
        if metadata_counts is not None:
            return metadata_counts

    if component == "DAILY_PAPER":
        daily_counts = _daily_paper_safety_actionability(row)
        warning_count += daily_counts["warning_count"]
        blocking_error_count += daily_counts["blocking_error_count"]

    expected_demo_warning_count = _expected_demo_warning_count(row, context, warning_count)
    actionable_warning_count = max(warning_count - expected_demo_warning_count, 0)
    if _string_or_empty(row.get("status")) == "WARN" and warning_count == 0 and stale_warning_count == 0:
        actionable_warning_count = max(actionable_warning_count, 1)
    return {
        "total_warning_count": warning_count + stale_warning_count,
        "expected_demo_warning_count": expected_demo_warning_count,
        "stale_warning_count": stale_warning_count,
        "actionable_warning_count": actionable_warning_count,
        "blocking_error_count": blocking_error_count,
    }


def _expected_demo_warning_count(row: dict[str, Any], context: dict[str, Any], warning_count: int) -> int:
    component = _string_or_empty(row.get("component"))
    if warning_count <= 0:
        return 0
    if component == "CURRENT_CANDIDATES" and _current_candidate_is_demo(row):
        return warning_count
    if component == "CURRENT_TO_PAPER_HANDOFF" and _handoff_targets_active_watch_only_demo(row, context):
        return warning_count
    if component == "CURRENT_TO_PAPER_HANDOFF" and context.get("watch_only_no_fills_demo"):
        return _expected_demo_handoff_warning_count(row, warning_count)
    if component == "DAILY_PAPER" and context.get("watch_only_no_fills_demo"):
        return warning_count
    return 0


def _current_candidate_is_demo(row: dict[str, Any]) -> bool:
    metadata = _metadata_for_row(row)
    audit = metadata.get("audit_metadata") if isinstance(metadata.get("audit_metadata"), dict) else {}
    return (
        metadata.get("demo_mode") is True
        or audit.get("demo_mode") is True
        or _string_or_empty(metadata.get("selection_profile")).lower() == "demo"
        or _string_or_empty(audit.get("selection_profile")).lower() == "demo"
    )


def _handoff_targets_active_watch_only_demo(row: dict[str, Any], context: dict[str, Any]) -> bool:
    if not context.get("watch_only_no_fills_demo"):
        return False
    active_daily_id = _string_or_empty(context.get("active_daily_id"))
    if not active_daily_id:
        return False
    metadata = _metadata_for_row(row)
    audit = metadata.get("audit_metadata") if isinstance(metadata.get("audit_metadata"), dict) else {}
    paper_journal_id = _string_or_empty(metadata.get("paper_journal_id")) or _string_or_empty(audit.get("paper_journal_id"))
    return paper_journal_id == active_daily_id


def _expected_demo_handoff_warning_count(row: dict[str, Any], warning_count: int) -> int:
    metadata = _metadata_for_row(row)
    warnings = metadata.get("warnings") if isinstance(metadata.get("warnings"), list) else []
    if not warnings:
        return 0
    expected_count = sum(1 for warning in warnings if _is_expected_demo_handoff_warning(warning))
    if expected_count != len(warnings):
        return 0
    return min(warning_count, expected_count) if warning_count else expected_count


def _is_expected_demo_handoff_warning(value: Any) -> bool:
    text = _string_or_empty(value).lower()
    if not text:
        return False
    expected_fragments = [
        "health check skipped for direct candidates_path handoff",
        "no fills_path provided",
        "no fills supplied for reconciliation",
        "pending manual review",
        "no manual paper fills loaded",
    ]
    return any(fragment in text for fragment in expected_fragments)


def _daily_paper_safety_actionability(row: dict[str, Any]) -> dict[str, int]:
    metadata = _metadata_for_row(row)
    if not metadata:
        return {"warning_count": 0, "blocking_error_count": 0}
    details = _watch_only_demo_details(metadata)
    warning_count = 0
    blocking_error_count = 0
    if details["live_trading_enabled"] or details["broker_api_invoked"]:
        blocking_error_count += 1
    if (
        details["approved_count"] > 0
        and details["fill_count"] == 0
        and details["open_position_count"] == 0
        and details["closed_trade_count"] == 0
    ):
        warning_count += 1
    return {"warning_count": warning_count, "blocking_error_count": blocking_error_count}


def _paper_artifact_health_issue_actionability(row: dict[str, Any], context: dict[str, Any]) -> dict[str, int] | None:
    issues = _load_issue_frame_from_metadata(row, "artifact_health_issues")
    if issues is None:
        return None
    counts = _empty_actionability_counts()
    active_ids = context.get("active_paper_artifact_ids", set())
    active_daily_id = _string_or_empty(context.get("active_daily_id"))
    for issue in issues.to_dict("records"):
        severity = _string_or_empty(issue.get("severity")).upper()
        if severity == "ERROR":
            counts["blocking_error_count"] += 1
            continue
        if severity != "WARN":
            continue
        artifact_type = _string_or_empty(issue.get("artifact_type")).upper()
        artifact_id = _string_or_empty(issue.get("artifact_id"))
        actionability = _string_or_empty(issue.get("actionability")).upper()
        if actionability == EXPECTED_DEMO_WARNING:
            counts["expected_demo_warning_count"] += 1
        elif actionability == STALE_ARTIFACT_WARNING:
            counts["stale_warning_count"] += 1
        elif _is_expected_demo_fills_issue(issue, active_daily_id, bool(context.get("watch_only_no_fills_demo"))):
            counts["expected_demo_warning_count"] += 1
        elif active_ids and (artifact_type, artifact_id) not in active_ids:
            counts["stale_warning_count"] += 1
        else:
            counts["actionable_warning_count"] += 1
    return counts


def _current_candidate_health_issue_actionability(row: dict[str, Any], context: dict[str, Any]) -> dict[str, int] | None:
    issues = _load_issue_frame_from_metadata(row, "current_candidate_artifact_health_issues")
    if issues is None:
        return None
    counts = _empty_actionability_counts()
    active_run_id = _string_or_empty(context.get("active_current_run_id"))
    for issue in issues.to_dict("records"):
        severity = _string_or_empty(issue.get("severity")).upper()
        if severity == "ERROR":
            counts["blocking_error_count"] += 1
            continue
        if severity != "WARN":
            continue
        run_id = _string_or_empty(issue.get("run_id"))
        actionability = _string_or_empty(issue.get("actionability")).upper()
        if actionability == STALE_ARTIFACT_WARNING:
            counts["stale_warning_count"] += 1
        elif active_run_id and run_id and run_id != active_run_id:
            counts["stale_warning_count"] += 1
        else:
            counts["actionable_warning_count"] += 1
    return counts


def _load_issue_frame_from_metadata(row: dict[str, Any], output_key: str) -> pd.DataFrame | None:
    metadata = _metadata_for_row(row)
    output_files = _output_files(metadata)
    issue_path = _string_or_empty(output_files.get(output_key))
    if not issue_path:
        return None
    path = Path(issue_path)
    if not path.exists():
        return None
    try:
        return pd.read_csv(path, dtype=str).fillna("")
    except Exception:
        return None


def _metadata_actionability_counts(row: dict[str, Any]) -> dict[str, int] | None:
    metadata = _metadata_for_row(row)
    if not metadata:
        return None
    if not any(key in metadata for key in _actionability_count_keys()):
        return None
    return {
        "total_warning_count": _int_or_zero(metadata.get("total_warning_count")),
        "expected_demo_warning_count": _int_or_zero(metadata.get("expected_demo_warning_count")),
        "stale_warning_count": _int_or_zero(metadata.get("stale_warning_count")),
        "actionable_warning_count": _int_or_zero(metadata.get("actionable_warning_count")),
        "blocking_error_count": _int_or_zero(metadata.get("blocking_error_count")),
    }


def _is_expected_demo_fills_issue(issue: dict[str, Any], active_daily_id: str, is_demo: bool) -> bool:
    return (
        is_demo
        and _string_or_empty(issue.get("artifact_type")).upper() == "DAILY"
        and _string_or_empty(issue.get("artifact_id")) == active_daily_id
        and _string_or_empty(issue.get("path_field")) == "fills_path"
        and _string_or_empty(issue.get("issue_code")) == "CSV_EMPTY"
    )


def _is_watch_only_no_fills_daily(metadata: dict[str, Any]) -> bool:
    return bool(_watch_only_demo_details(metadata)["watch_only_no_fills_candidate"])


def _watch_only_demo_details(metadata: dict[str, Any]) -> dict[str, Any]:
    details = {
        "reviewed_decisions_used": metadata.get("reviewed_decisions_used") is True,
        "decision_count": _int_or_zero(metadata.get("decision_count")),
        "fill_count": _int_or_zero(metadata.get("fill_count")),
        "open_position_count": _int_or_zero(metadata.get("open_position_count")),
        "closed_trade_count": _int_or_zero(metadata.get("closed_trade_count")),
        "watch_only_count": 0,
        "pending_count": 0,
        "approved_count": 0,
        "rejected_count": 0,
        "expected_no_fills_warning_count": 0,
        "unexpected_daily_warning_count": 0,
        "live_trading_enabled": metadata.get("live_trading_enabled") is True,
        "broker_api_invoked": metadata.get("broker_api_invoked") is True,
        "approved_text_present": False,
        "actions_no_trade_compatible": False,
        "watch_only_no_fills_candidate": False,
        "paper_demo_validated": False,
    }
    warnings = metadata.get("warnings") if isinstance(metadata.get("warnings"), list) else []
    details["expected_no_fills_warning_count"] = sum(1 for warning in warnings if _is_expected_no_fills_warning(warning))
    details["unexpected_daily_warning_count"] = max(len(warnings) - details["expected_no_fills_warning_count"], 0)
    reviewed_path = _daily_reviewed_decisions_path(metadata)
    if not reviewed_path:
        return details
    path = Path(reviewed_path)
    if not path.exists():
        return details
    try:
        frame = pd.read_csv(path, dtype=str).fillna("")
    except Exception:
        return details
    if frame.empty or "manual_review_status" not in frame.columns:
        return details
    status_counts = {
        str(key).strip().upper(): _int_or_zero(value)
        for key, value in frame["manual_review_status"].value_counts().to_dict().items()
    }
    details["watch_only_count"] = status_counts.get("WATCH_ONLY", 0)
    details["pending_count"] = status_counts.get("PENDING_REVIEW", 0)
    details["approved_count"] = status_counts.get("APPROVED_FOR_PAPER", 0)
    details["rejected_count"] = status_counts.get("REJECTED", 0)
    details["approved_text_present"] = bool(
        frame.astype(str).apply(lambda series: series.str.contains("APPROVED_FOR_PAPER", na=False)).any().any()
    )
    details["actions_no_trade_compatible"] = _frame_actions_no_trade_compatible(frame)
    details["watch_only_no_fills_candidate"] = (
        details["reviewed_decisions_used"]
        and details["fill_count"] == 0
        and details["open_position_count"] == 0
        and details["closed_trade_count"] == 0
        and details["watch_only_count"] > 0
        and details["approved_count"] == 0
        and not details["approved_text_present"]
    )
    details["paper_demo_validated"] = (
        details["watch_only_no_fills_candidate"]
        and details["pending_count"] == 0
        and details["rejected_count"] == 0
        and details["actions_no_trade_compatible"]
        and details["unexpected_daily_warning_count"] == 0
        and not details["live_trading_enabled"]
        and not details["broker_api_invoked"]
    )
    return details


def _frame_actions_no_trade_compatible(frame: pd.DataFrame) -> bool:
    action_columns = [column for column in ["action", "score_action"] if column in frame.columns]
    if not action_columns:
        return False
    allowed = {"SKIP", "NO_TRADE", "WATCH_ONLY"}
    for column in action_columns:
        values = {_string_or_empty(value).upper() for value in frame[column].tolist() if _string_or_empty(value)}
        if values and not values.issubset(allowed):
            return False
    return True


def _is_expected_no_fills_warning(value: Any) -> bool:
    text = _string_or_empty(value).lower()
    if not text:
        return False
    expected_fragments = [
        "no fills_path provided",
        "no fills supplied for reconciliation",
        "no manual paper fills loaded",
    ]
    return any(fragment in text for fragment in expected_fragments)


def _empty_actionability_counts() -> dict[str, int]:
    return {
        "expected_demo_warning_count": 0,
        "stale_warning_count": 0,
        "actionable_warning_count": 0,
        "blocking_error_count": 0,
    }


def _classification_label(counts: dict[str, int]) -> str:
    labels = []
    if counts.get("blocking_error_count", 0):
        labels.append(BLOCKING_ERROR)
    if counts.get("actionable_warning_count", 0):
        labels.append(ACTIONABLE_WARNING)
    if counts.get("expected_demo_warning_count", 0):
        labels.append(EXPECTED_DEMO_WARNING)
    if counts.get("stale_warning_count", 0):
        labels.append(STALE_ARTIFACT_WARNING)
    return ";".join(labels)


def _parse_note_count(notes: Any, key: str) -> int:
    text = _string_or_empty(notes)
    if not text:
        return 0
    prefix = f"{key}="
    for part in text.replace(",", ";").split(";"):
        item = part.strip()
        if item.startswith(prefix):
            return _int_or_zero(item[len(prefix) :])
    return 0


def _warning_actionability_totals(status_frame: pd.DataFrame) -> dict[str, int]:
    frame = _finalize_status_frame(status_frame)
    totals = {
        "total_warning_count": 0,
        "expected_demo_warning_count": 0,
        "stale_warning_count": 0,
        "actionable_warning_count": 0,
        "blocking_error_count": 0,
    }
    if frame.empty:
        return totals
    for key in totals:
        if key in frame.columns:
            totals[key] = int(pd.to_numeric(frame[key], errors="coerce").fillna(0).sum())
    return totals


def _actionability_count_keys() -> list[str]:
    return [
        "total_warning_count",
        "expected_demo_warning_count",
        "stale_warning_count",
        "actionable_warning_count",
        "blocking_error_count",
    ]


def _watch_only_demo_details_from_status_frame(status_frame: pd.DataFrame) -> dict[str, Any]:
    frame = _finalize_status_frame(status_frame)
    rows = frame.loc[frame["component"] == "DAILY_PAPER"]
    if rows.empty:
        return _watch_only_demo_details({})
    return _watch_only_demo_details(_metadata_for_row(rows.iloc[0].to_dict()))


def infer_paper_workflow_stage(status_frame: pd.DataFrame) -> str:
    """Infer the current workflow stage from component status rows."""

    statuses = _status_by_component(status_frame)
    if statuses["CURRENT_CANDIDATE_HEALTH"] == "FAIL" or statuses["PAPER_ARTIFACT_HEALTH"] == "FAIL":
        return "WORKFLOW_NEEDS_ATTENTION"
    if statuses["REVIEW_TEMPLATE_HEALTH"] == "FAIL":
        return "REVIEW_TEMPLATE_HEALTH_FAIL"
    if statuses["REVIEW_TEMPLATE_HEALTH"] == "WARN":
        return "REVIEW_TEMPLATE_HEALTH_WARN"
    if statuses["CURRENT_CANDIDATES"] == "MISSING":
        return "NO_CURRENT_CANDIDATES"
    if statuses["CURRENT_TO_PAPER_HANDOFF"] == "MISSING":
        return "CURRENT_CANDIDATES_READY"
    if statuses["REVIEW_TEMPLATE"] == "MISSING":
        return "HANDOFF_READY"
    if statuses["PAPER_REVIEW"] == "MISSING":
        return "REVIEW_TEMPLATE_READY"
    if statuses["DAILY_PAPER"] == "MISSING":
        return "REVIEW_READY"
    if statuses["RECONCILIATION"] == "MISSING":
        return "DAILY_PAPER_READY"
    if statuses["RECONCILIATION"] in {"FAIL", "WARN"}:
        return "WORKFLOW_NEEDS_ATTENTION"
    if statuses["PAPER_ARTIFACT_INDEX"] == "MISSING" or statuses["PAPER_ARTIFACT_HEALTH"] == "MISSING":
        return "RECONCILIATION_READY"
    actionability = _warning_actionability_totals(status_frame)
    if actionability["blocking_error_count"] > 0 or actionability["actionable_warning_count"] > 0:
        return "WORKFLOW_NEEDS_ATTENTION"
    demo_details = _watch_only_demo_details_from_status_frame(status_frame)
    if (
        demo_details["paper_demo_validated"]
        and actionability["blocking_error_count"] == 0
        and actionability["actionable_warning_count"] == 0
    ):
        return WATCH_ONLY_DEMO_STAGE
    if statuses["PAPER_ARTIFACT_HEALTH"] == "PASS":
        return "WORKFLOW_COMPLETE"
    return "WORKFLOW_NEEDS_ATTENTION"


def infer_next_manual_action(status_frame: pd.DataFrame, *, workflow_stage: str | None = None) -> str:
    """Infer the next manual action from the workflow stage."""

    stage = workflow_stage or infer_paper_workflow_stage(status_frame)
    if stage == "WORKFLOW_NEEDS_ATTENTION":
        totals = _warning_actionability_totals(status_frame)
        if totals["blocking_error_count"] == 0 and totals["actionable_warning_count"] == 0:
            if totals["expected_demo_warning_count"] > 0:
                return DEMO_WORKFLOW_NEXT_ACTION
            if totals["stale_warning_count"] > 0:
                return STALE_ONLY_NEXT_ACTION
    actions = {
        "NO_CURRENT_CANDIDATES": "Run current-candidates.",
        "CURRENT_CANDIDATES_READY": "Run current-to-paper.",
        "HANDOFF_READY": "Run current-to-paper-review.",
        "REVIEW_TEMPLATE_READY": "Manually edit review_updates_template.csv, then run paper-review-decisions --health-check.",
        "REVIEW_TEMPLATE_HEALTH_WARN": "Review template health warnings before applying paper-review-decisions.",
        "REVIEW_TEMPLATE_HEALTH_FAIL": "Fix review template health errors before applying paper-review-decisions.",
        "REVIEW_READY": "Run paper-daily --reviewed-decisions.",
        "DAILY_PAPER_READY": "Enter manual fills CSV or run paper-reconcile-fills.",
        "RECONCILIATION_READY": "Run paper-index and paper-health-check.",
        WATCH_ONLY_DEMO_STAGE: DEMO_WORKFLOW_NEXT_ACTION,
        "WORKFLOW_COMPLETE": "Review completed workflow artifacts.",
        "WORKFLOW_NEEDS_ATTENTION": "Review warnings/errors in workflow status and health reports.",
    }
    return actions.get(stage, "Review workflow artifacts.")


def summarize_paper_workflow_status(
    status_frame: pd.DataFrame,
    *,
    workflow_stage: str,
    next_manual_action: str,
) -> pd.DataFrame:
    """Summarize the workflow status into one dashboard row."""

    frame = _finalize_status_frame(status_frame)
    by_component = {row["component"]: row for row in frame.to_dict("records")}
    explicit_statuses = [str(row.get("status", "")).upper() for row in frame.to_dict("records")]
    missing_count = explicit_statuses.count("MISSING")
    error_count = int(pd.to_numeric(frame["error_count"], errors="coerce").fillna(0).sum()) if not frame.empty else 0
    warning_count = int(pd.to_numeric(frame["warning_count"], errors="coerce").fillna(0).sum()) if not frame.empty else 0
    actionability = _warning_actionability_totals(frame)
    demo_details = _watch_only_demo_details_from_status_frame(frame)
    status = (
        "FAIL"
        if "FAIL" in explicit_statuses or error_count or actionability["blocking_error_count"] > 0
        else "WARN"
        if (
            "WARN" in explicit_statuses
            or missing_count
            or warning_count
            or actionability["actionable_warning_count"] > 0
            or actionability["expected_demo_warning_count"] > 0
            or actionability["stale_warning_count"] > 0
        )
        else "PASS"
    )
    artifact_index_status = _combined_component_status(
        by_component,
        ["CURRENT_CANDIDATE_INDEX", "PAPER_ARTIFACT_INDEX"],
        missing_value="MISSING",
    )
    artifact_health_status = _combined_component_status(
        by_component,
        ["CURRENT_CANDIDATE_HEALTH", "PAPER_ARTIFACT_HEALTH"],
        missing_value="MISSING",
    )
    reconciliation = by_component.get("RECONCILIATION", {})
    row = {
        "workflow_stage": workflow_stage,
        "status": status,
        "latest_decision_date": _latest_decision_date(frame),
        "current_candidate_status": _component_status(by_component, "CURRENT_CANDIDATES"),
        "handoff_status": _component_status(by_component, "CURRENT_TO_PAPER_HANDOFF"),
        "review_template_status": _component_status(by_component, "REVIEW_TEMPLATE"),
        "review_template_health_status": _component_status(by_component, "REVIEW_TEMPLATE_HEALTH"),
        "review_status": _component_status(by_component, "PAPER_REVIEW"),
        "daily_paper_status": _component_status(by_component, "DAILY_PAPER"),
        "reconciliation_status": _component_status(by_component, "RECONCILIATION"),
        "artifact_index_status": artifact_index_status,
        "artifact_health_status": artifact_health_status,
        "total_warning_count": actionability["total_warning_count"],
        "expected_demo_warning_count": actionability["expected_demo_warning_count"],
        "expected_no_fills_warning_count": demo_details["expected_no_fills_warning_count"],
        "stale_warning_count": actionability["stale_warning_count"],
        "actionable_warning_count": actionability["actionable_warning_count"],
        "actionable_paper_warning_count": actionability["actionable_warning_count"],
        "blocking_error_count": actionability["blocking_error_count"],
        "diagnostic_reconciliation_failure_count": _int_or_zero(
            reconciliation.get("diagnostic_reconciliation_failure_count")
        ),
        "active_reconciliation_error_count": _int_or_zero(
            reconciliation.get("active_reconciliation_error_count")
        ),
        "watch_only_count": demo_details["watch_only_count"],
        "approved_count": demo_details["approved_count"],
        "open_position_count": demo_details["open_position_count"],
        "closed_trade_count": demo_details["closed_trade_count"],
        "paper_demo_validated": demo_details["paper_demo_validated"],
        "next_manual_action": next_manual_action,
    }
    return pd.DataFrame([row], columns=SUMMARY_COLUMNS)


def resolve_paper_workflow_status_paths(
    output_dir: str | Path,
    workflow_status_id: str,
) -> PaperWorkflowStatusArtifactPaths:
    """Resolve deterministic workflow status artifact paths."""

    artifact_dir = Path(output_dir) / workflow_status_id
    return PaperWorkflowStatusArtifactPaths(
        artifact_dir=artifact_dir,
        paper_workflow_status_report=artifact_dir / "paper_workflow_status_report.md",
        paper_workflow_status_csv=artifact_dir / "paper_workflow_status.csv",
        paper_workflow_summary=artifact_dir / "paper_workflow_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_paper_workflow_status_artifacts(result: PaperWorkflowStatusResult) -> dict[str, Path]:
    """Write workflow status report, CSVs, and metadata."""

    paths = PaperWorkflowStatusArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.status_frame, paths.paper_workflow_status_csv)
    _export_dataframe(result.summary_frame, paths.paper_workflow_summary)
    metadata = build_paper_workflow_status_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.paper_workflow_status_report.write_text(render_paper_workflow_status_report(result, metadata), encoding="utf-8")
    return paths.as_dict()


def build_paper_workflow_status_metadata(
    result: PaperWorkflowStatusResult,
    paths: PaperWorkflowStatusArtifactPaths,
) -> dict[str, Any]:
    """Build metadata for workflow status artifacts."""

    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    return {
        "workflow_status_id": result.workflow_status_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_decision_date": result.latest_decision_date,
        "next_manual_action": result.next_manual_action,
        "total_warning_count": _int_or_zero(summary.get("total_warning_count")),
        "expected_demo_warning_count": _int_or_zero(summary.get("expected_demo_warning_count")),
        "expected_no_fills_warning_count": _int_or_zero(summary.get("expected_no_fills_warning_count")),
        "stale_warning_count": _int_or_zero(summary.get("stale_warning_count")),
        "actionable_warning_count": _int_or_zero(summary.get("actionable_warning_count")),
        "actionable_paper_warning_count": _int_or_zero(summary.get("actionable_paper_warning_count")),
        "blocking_error_count": _int_or_zero(summary.get("blocking_error_count")),
        "diagnostic_reconciliation_failure_count": _int_or_zero(
            summary.get("diagnostic_reconciliation_failure_count")
        ),
        "active_reconciliation_error_count": _int_or_zero(summary.get("active_reconciliation_error_count")),
        "watch_only_count": _int_or_zero(summary.get("watch_only_count")),
        "approved_count": _int_or_zero(summary.get("approved_count")),
        "open_position_count": _int_or_zero(summary.get("open_position_count")),
        "closed_trade_count": _int_or_zero(summary.get("closed_trade_count")),
        "paper_demo_validated": bool(summary.get("paper_demo_validated", False)),
        "component_statuses": result.summary_frame.to_dict("records")[0] if not result.summary_frame.empty else {},
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_paper_workflow_status_report(
    result: PaperWorkflowStatusResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render markdown workflow status dashboard."""

    _ = metadata
    lines = [
        f"# Paper Trading Workflow Status: {result.workflow_status_id}",
        "",
        "No broker or live trading integration was invoked. This dashboard scans local workflow artifacts only.",
        "",
        "## Workflow Summary",
        "",
        _markdown_table(
            result.summary_frame,
            [
                "workflow_stage",
                "status",
                "latest_decision_date",
                "total_warning_count",
                "expected_demo_warning_count",
                "expected_no_fills_warning_count",
                "stale_warning_count",
                "actionable_warning_count",
                "blocking_error_count",
                "diagnostic_reconciliation_failure_count",
                "active_reconciliation_error_count",
                "watch_only_count",
                "approved_count",
                "open_position_count",
                "closed_trade_count",
                "paper_demo_validated",
                "next_manual_action",
            ],
        ),
        "",
        "## Component Status",
        "",
        _markdown_table(
            result.status_frame,
            [
                "component",
                "status",
                "latest_artifact_id",
                "decision_date",
                "issue_count",
                "warning_count",
                "error_count",
                "total_warning_count",
                "expected_demo_warning_count",
                "stale_warning_count",
                "actionable_warning_count",
                "blocking_error_count",
                "diagnostic_reconciliation_failure_count",
                "active_reconciliation_error_count",
                "warning_classification",
                "next_action",
                "report_path",
            ],
            max_rows=100,
        ),
        "",
        "## Next Manual Action",
        "",
        f"- {result.next_manual_action}",
        "",
        "## Warnings",
        "",
        _warnings_section(result.warnings),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in result.known_limitations),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def generate_paper_workflow_status_id(
    status_frame: pd.DataFrame,
    *,
    decision_date: str | pd.Timestamp | None,
    config_version: str,
) -> str:
    """Generate deterministic workflow status id."""

    frame = _finalize_status_frame(status_frame)
    payload = {
        "decision_date": _date_string(decision_date),
        "artifacts": [
            {
                "component": row["component"],
                "artifact_id": row["latest_artifact_id"],
                "status": row["status"],
            }
            for row in frame.to_dict("records")
        ],
        "config_version": config_version,
    }
    return _hash_payload(payload, length=12)


def _scan_current_candidates(root: Path, decision_date: str, universe_name: str) -> list[dict[str, Any]]:
    records = []
    for metadata_path in _metadata_paths(root, "metadata.json", excluded_parts={"index", "health"}):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None:
            continue
        metadata_date = _date_string(metadata.get("decision_date"))
        metadata_universe = _string_or_empty(metadata.get("universe_name"))
        if decision_date and metadata_date != decision_date:
            continue
        if universe_name and metadata_universe != universe_name:
            continue
        output_files = _output_files(metadata)
        row_counts = metadata.get("row_counts") if isinstance(metadata.get("row_counts"), dict) else {}
        records.append(
            _record(
                component="CURRENT_CANDIDATES",
                status="READY",
                latest_artifact_id=_string_or_empty(metadata.get("run_id")) or metadata_path.parent.name,
                decision_date=metadata_date,
                universe_name=metadata_universe,
                report_path=output_files.get("current_candidates_report", metadata_path.parent / "current_candidates_report.md"),
                metadata_path=metadata_path,
                issue_count=0,
                warning_count=len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else 0,
                error_count=0,
                notes=f"candidate_count={_string_or_empty(row_counts.get('candidates'))}",
                created_at=metadata.get("created_at"),
            )
        )
    return records


def _scan_current_candidate_index(root: Path) -> list[dict[str, Any]]:
    return _single_metadata_record(
        root / "index" / "metadata.json",
        component="CURRENT_CANDIDATE_INDEX",
        id_key="index_id",
        default_id="current-candidate-index",
        report_key="current_candidate_artifact_index",
        default_report="current_candidate_artifact_index.md",
        status="READY",
    )


def _scan_current_candidate_health(root: Path) -> list[dict[str, Any]]:
    return _health_records(
        root / "health",
        component="CURRENT_CANDIDATE_HEALTH",
        id_key="health_check_id",
        report_key="current_candidate_artifact_health_report",
        default_report="current_candidate_artifact_health_report.md",
    )


def _scan_current_to_paper_handoff(root: Path, decision_date: str, universe_name: str) -> list[dict[str, Any]]:
    records = []
    for metadata_path in _metadata_paths(root, "handoff_metadata.json"):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None:
            continue
        metadata_date = _date_string(metadata.get("selected_decision_date"))
        metadata_universe = _string_or_empty(metadata.get("selected_universe_name"))
        if decision_date and metadata_date and metadata_date != decision_date:
            continue
        if universe_name and metadata_universe and metadata_universe != universe_name:
            continue
        output_files = _output_files(metadata)
        records.append(
            _record(
                component="CURRENT_TO_PAPER_HANDOFF",
                status="READY",
                latest_artifact_id=_string_or_empty(metadata.get("handoff_id")) or metadata_path.parent.name,
                decision_date=metadata_date,
                universe_name=metadata_universe,
                report_path=output_files.get("handoff_report", metadata_path.parent / "handoff_report.md"),
                metadata_path=metadata_path,
                issue_count=0,
                warning_count=len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else 0,
                error_count=0,
                notes=f"paper_journal_id={_string_or_empty(metadata.get('paper_journal_id'))}",
                created_at=metadata.get("created_at"),
            )
        )
    return records


def _scan_review_template_handoff(root: Path) -> list[dict[str, Any]]:
    records = []
    for metadata_path in _metadata_paths(root, "metadata.json"):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None or not metadata.get("review_handoff_id"):
            continue
        output_files = _output_files(metadata)
        records.append(
            _record(
                component="REVIEW_TEMPLATE",
                status="READY",
                latest_artifact_id=_string_or_empty(metadata.get("review_handoff_id")) or metadata_path.parent.name,
                report_path=output_files.get("review_handoff_report", metadata.get("report_path", "")),
                metadata_path=metadata_path,
                issue_count=0,
                warning_count=len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else 0,
                error_count=0,
                notes=f"decision_count={_string_or_empty(metadata.get('decision_count'))}",
                created_at=metadata.get("created_at") or metadata.get("audit_metadata", {}).get("review_time", ""),
            )
        )
    return records


def _scan_review_template_health(root: Path) -> list[dict[str, Any]]:
    return _health_records(
        root,
        component="REVIEW_TEMPLATE_HEALTH",
        id_key="health_check_id",
        report_key="review_template_health_report",
        default_report="review_template_health_report.md",
    )


def _scan_paper_reviews(root: Path) -> list[dict[str, Any]]:
    records = []
    for metadata_path in _metadata_paths(root, "metadata.json"):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None or not metadata.get("review_id"):
            continue
        output_files = _output_files(metadata)
        template_health = metadata.get("template_health") if isinstance(metadata.get("template_health"), dict) else {}
        records.append(
            _record(
                component="PAPER_REVIEW",
                status="READY",
                latest_artifact_id=_string_or_empty(metadata.get("review_id")) or metadata_path.parent.name,
                report_path=output_files.get("paper_review_report", metadata_path.parent / "paper_review_report.md"),
                metadata_path=metadata_path,
                issue_count=_int_or_zero(template_health.get("template_health_issue_count")),
                warning_count=len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else 0,
                error_count=_int_or_zero(template_health.get("template_health_error_count")),
                notes=f"template_health_status={_string_or_empty(template_health.get('template_health_status'))}",
                created_at=metadata.get("created_at"),
            )
        )
    return records


def _scan_daily_paper(root: Path, decision_date: str) -> list[dict[str, Any]]:
    records = []
    for metadata_path in _metadata_paths(root, "metadata.json"):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None or not metadata.get("journal_id"):
            continue
        metadata_date = _date_string(metadata.get("paper_date"))
        if decision_date and metadata_date != decision_date:
            continue
        output_files = _output_files(metadata)
        reconciliation = metadata.get("reconciliation") if isinstance(metadata.get("reconciliation"), dict) else {}
        status = "READY"
        if metadata.get("reviewed_decisions_used") is True:
            status = "REVIEWED_READY"
        records.append(
            _record(
                component="DAILY_PAPER",
                status=status,
                latest_artifact_id=_string_or_empty(metadata.get("journal_id")) or metadata_path.parent.name,
                decision_date=metadata_date,
                report_path=output_files.get("paper_report", metadata_path.parent / "paper_report.md"),
                metadata_path=metadata_path,
                issue_count=_int_or_zero(reconciliation.get("issue_count")),
                warning_count=_int_or_zero(reconciliation.get("warning_count")),
                error_count=_int_or_zero(reconciliation.get("error_count")),
                notes=f"reviewed_decisions_used={metadata.get('reviewed_decisions_used')}",
                created_at=metadata.get("created_at"),
            )
        )
    return records


def _scan_reconciliation(root: Path) -> list[dict[str, Any]]:
    return _health_records(
        root,
        component="RECONCILIATION",
        id_key="reconciliation_id",
        report_key="reconciliation_report",
        default_report="reconciliation_report.md",
    )


def _scan_paper_artifact_index(root: Path) -> list[dict[str, Any]]:
    return _single_metadata_record(
        root / "index" / "metadata.json",
        component="PAPER_ARTIFACT_INDEX",
        id_key="index_id",
        default_id="paper-artifact-index",
        report_key="paper_artifact_index",
        default_report="paper_artifact_index.md",
        status="READY",
    )


def _scan_paper_artifact_health(root: Path) -> list[dict[str, Any]]:
    return _health_records(
        root / "health",
        component="PAPER_ARTIFACT_HEALTH",
        id_key="health_check_id",
        report_key="artifact_health_report",
        default_report="artifact_health_report.md",
    )


def _single_metadata_record(
    metadata_path: Path,
    *,
    component: str,
    id_key: str,
    default_id: str,
    report_key: str,
    default_report: str,
    status: str,
) -> list[dict[str, Any]]:
    metadata = _load_json_or_none(metadata_path)
    if metadata is None:
        return []
    output_files = _output_files(metadata)
    return [
        _record(
            component=component,
            status=status,
            latest_artifact_id=_string_or_empty(metadata.get(id_key)) or default_id,
            report_path=output_files.get(report_key, metadata_path.parent / default_report),
            metadata_path=metadata_path,
            issue_count=_int_or_zero(metadata.get("issue_count")),
            warning_count=len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else _int_or_zero(metadata.get("warning_count")),
            error_count=_int_or_zero(metadata.get("error_count")),
            notes=f"artifact_count={_string_or_empty(metadata.get('artifact_count'))}",
            created_at=metadata.get("created_at"),
        )
    ]


def _health_records(
    root: Path,
    *,
    component: str,
    id_key: str,
    report_key: str,
    default_report: str,
) -> list[dict[str, Any]]:
    records = []
    for metadata_path in _metadata_paths(root, "metadata.json"):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None or not metadata.get(id_key):
            continue
        output_files = _output_files(metadata)
        records.append(
            _record(
                component=component,
                status=_string_or_empty(metadata.get("status")) or "READY",
                latest_artifact_id=_string_or_empty(metadata.get(id_key)) or metadata_path.parent.name,
                report_path=output_files.get(report_key, metadata_path.parent / default_report),
                metadata_path=metadata_path,
                issue_count=_int_or_zero(metadata.get("issue_count")),
                warning_count=_int_or_zero(metadata.get("warning_count")),
                error_count=_int_or_zero(metadata.get("error_count")),
                notes="",
                created_at=metadata.get("created_at"),
            )
        )
    return records


def _record(**values: Any) -> dict[str, Any]:
    row = {
        "component": "",
        "status": "",
        "latest_artifact_id": "",
        "decision_date": "",
        "universe_name": "",
        "report_path": "",
        "metadata_path": "",
        "issue_count": 0,
        "warning_count": 0,
        "error_count": 0,
        "total_warning_count": 0,
        "expected_demo_warning_count": 0,
        "stale_warning_count": 0,
        "actionable_warning_count": 0,
        "blocking_error_count": 0,
        "diagnostic_reconciliation_failure_count": 0,
        "active_reconciliation_error_count": 0,
        "warning_classification": "",
        "next_action": "",
        "notes": "",
        "created_at": "",
    }
    row.update(values)
    row["status"] = _string_or_empty(row["status"]).upper()
    row["decision_date"] = _date_string(row.get("decision_date"))
    row["report_path"] = _string_or_empty(row.get("report_path"))
    row["metadata_path"] = _string_or_empty(row.get("metadata_path"))
    row["latest_artifact_id"] = _string_or_empty(row.get("latest_artifact_id"))
    row["issue_count"] = _int_or_zero(row.get("issue_count"))
    row["warning_count"] = _int_or_zero(row.get("warning_count"))
    row["error_count"] = _int_or_zero(row.get("error_count"))
    row["total_warning_count"] = _int_or_zero(row.get("total_warning_count"))
    row["expected_demo_warning_count"] = _int_or_zero(row.get("expected_demo_warning_count"))
    row["stale_warning_count"] = _int_or_zero(row.get("stale_warning_count"))
    row["actionable_warning_count"] = _int_or_zero(row.get("actionable_warning_count"))
    row["blocking_error_count"] = _int_or_zero(row.get("blocking_error_count"))
    row["diagnostic_reconciliation_failure_count"] = _int_or_zero(row.get("diagnostic_reconciliation_failure_count"))
    row["active_reconciliation_error_count"] = _int_or_zero(row.get("active_reconciliation_error_count"))
    row["warning_classification"] = _string_or_empty(row.get("warning_classification"))
    return row


def _missing_status_row(component: str, *, notes: str = "No matching local artifact metadata found.") -> dict[str, Any]:
    return _record(
        component=component,
        status="MISSING",
        next_action=_component_next_action(component, "MISSING"),
        notes=notes,
    )


def _component_next_action(component: str, status: str) -> str:
    if status == "FAIL":
        return "Review warnings/errors."
    if component == "CURRENT_CANDIDATES":
        return "Run current-candidates." if status == "MISSING" else "Run current-to-paper."
    if component == "CURRENT_TO_PAPER_HANDOFF":
        return "Run current-to-paper." if status == "MISSING" else "Run current-to-paper-review."
    if component == "REVIEW_TEMPLATE":
        return "Run current-to-paper-review." if status == "MISSING" else "Manually edit review_updates_template.csv."
    if component == "REVIEW_TEMPLATE_HEALTH":
        return "Run paper-review-template-health or paper-review-decisions --health-check." if status == "MISSING" else "Run paper-review-decisions --health-check."
    if component == "PAPER_REVIEW":
        return "Run paper-review-decisions --health-check." if status == "MISSING" else "Run paper-daily --reviewed-decisions."
    if component == "DAILY_PAPER":
        return "Run paper-daily --reviewed-decisions." if status == "MISSING" else "Enter fills or run paper-reconcile-fills."
    if component == "RECONCILIATION":
        return "Run paper-reconcile-fills." if status == "MISSING" else "Run paper-index and paper-health-check."
    if component in {"PAPER_ARTIFACT_INDEX", "CURRENT_CANDIDATE_INDEX"}:
        return "Run artifact index command." if status == "MISSING" else "Run artifact health check."
    if component in {"PAPER_ARTIFACT_HEALTH", "CURRENT_CANDIDATE_HEALTH"}:
        return "Run artifact health check." if status == "MISSING" else "Review health result."
    return ""


def _status_by_component(status_frame: pd.DataFrame) -> dict[str, str]:
    frame = _finalize_status_frame(status_frame)
    values = {row["component"]: row["status"] for row in frame.to_dict("records")}
    for component in COMPONENTS:
        values.setdefault(component, "MISSING")
    return values


def _combined_component_status(by_component: dict[str, dict[str, Any]], components: list[str], *, missing_value: str) -> str:
    statuses = [_component_status(by_component, component) for component in components]
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    if any(status in {"PASS", "READY"} for status in statuses):
        if any(status == "MISSING" for status in statuses):
            return "WARN"
        return "PASS" if all(status == "PASS" for status in statuses) else "READY"
    return missing_value


def _component_status(by_component: dict[str, dict[str, Any]], component: str) -> str:
    row = by_component.get(component, {})
    return _string_or_empty(row.get("status")) or "MISSING"


def _latest_decision_date(frame: pd.DataFrame) -> str:
    dates = sorted(_date_string(value) for value in frame.get("decision_date", pd.Series(dtype="object")).tolist() if _date_string(value))
    return dates[-1] if dates else ""


def _dashboard_warnings(status_frame: pd.DataFrame, workflow_stage: str) -> list[str]:
    warnings = []
    totals = _warning_actionability_totals(status_frame)
    if (
        workflow_stage == "WORKFLOW_NEEDS_ATTENTION"
        and totals["blocking_error_count"] == 0
        and totals["actionable_warning_count"] == 0
        and (totals["expected_demo_warning_count"] > 0 or totals["stale_warning_count"] > 0)
    ):
        warnings.append(
            "Only expected demo or stale artifact warnings were classified for the active workflow chain."
        )
    elif workflow_stage == WATCH_ONLY_DEMO_STAGE:
        warnings.append("WATCH_ONLY no-fills demo workflow was validated; no fills were supplied.")
    elif workflow_stage != "WORKFLOW_COMPLETE":
        warnings.append(f"Workflow stage is {workflow_stage}; manual action is still needed.")
    failing = status_frame.loc[status_frame["status"] == "FAIL"] if not status_frame.empty else pd.DataFrame()
    for row in failing.to_dict("records"):
        warnings.append(f"{row['component']} status is FAIL.")
    return warnings


def _metadata_paths(root: Path, filename: str, excluded_parts: set[str] | None = None) -> list[Path]:
    if not root.exists():
        return []
    excluded = excluded_parts or set()
    paths = []
    for path in root.rglob(filename):
        relative_parts = set(path.relative_to(root).parts[:-1])
        if relative_parts.intersection(excluded):
            continue
        paths.append(path)
    return sorted(paths)


def _load_json_or_none(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _output_files(metadata: dict[str, Any]) -> dict[str, Any]:
    output_files = metadata.get("output_files")
    return output_files if isinstance(output_files, dict) else {}


def _metadata_for_row(row: dict[str, Any]) -> dict[str, Any]:
    path_text = _string_or_empty(row.get("metadata_path"))
    if not path_text:
        return {}
    path = Path(path_text)
    return _load_json_or_none(path) or {}


def _daily_reviewed_decisions_path(metadata: dict[str, Any]) -> str:
    output_files = _output_files(metadata)
    return _string_or_empty(metadata.get("reviewed_decisions_path")) or _string_or_empty(
        output_files.get("reviewed_decisions")
    )


def _artifact_id_from_path(value: Any) -> str:
    text = _string_or_empty(value)
    if not text:
        return ""
    path = Path(text)
    if path.name == "metadata.json":
        return path.parent.name
    if path.name:
        return path.parent.name
    return ""


def _paths_match(left: Any, right: Any) -> bool:
    left_keys = _path_keys(left)
    right_keys = _path_keys(right)
    return bool(left_keys and right_keys and left_keys.intersection(right_keys))


def _path_keys(value: Any) -> set[str]:
    text = _string_or_empty(value)
    if not text:
        return set()
    normalized = text.replace("\\", "/").lower()
    keys = {normalized}
    try:
        keys.add(str(Path(text).resolve(strict=False)).replace("\\", "/").lower())
    except (OSError, RuntimeError):
        pass
    return keys


def _latest_record(frame: pd.DataFrame) -> dict[str, Any]:
    sortable = frame.copy(deep=True)
    sortable["_sort_date"] = sortable["decision_date"].map(lambda value: _date_string(value))
    sortable["_sort_created"] = sortable["created_at"].map(_string_or_empty)
    sortable = sortable.sort_values(
        ["_sort_date", "_sort_created", "latest_artifact_id", "metadata_path"],
        na_position="last",
    )
    return sortable.iloc[-1].drop(labels=["_sort_date", "_sort_created"], errors="ignore").to_dict()


def _finalize_scan_frame(frame: pd.DataFrame) -> pd.DataFrame:
    scan = frame.copy(deep=True)
    columns = STATUS_COLUMNS + ["universe_name", "created_at"]
    for column in columns:
        if column not in scan.columns:
            scan[column] = ""
    if scan.empty:
        return scan[columns]
    return scan[columns].sort_values(["component", "decision_date", "created_at", "latest_artifact_id"], na_position="last").reset_index(drop=True)


def _finalize_status_frame(frame: pd.DataFrame) -> pd.DataFrame:
    status = frame.copy(deep=True)
    for column in STATUS_COLUMNS:
        if column not in status.columns:
            status[column] = ""
    if status.empty:
        return status[STATUS_COLUMNS]
    return status[STATUS_COLUMNS].sort_values(["component"], key=lambda series: series.map(_component_order)).reset_index(drop=True)


def _component_order(component: Any) -> int:
    text = _string_or_empty(component)
    return COMPONENTS.index(text) if text in COMPONENTS else len(COMPONENTS)


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    export = _sanitize_dataframe_for_export(frame)
    path.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(path, index=False)


def _sanitize_dataframe_for_export(frame: pd.DataFrame) -> pd.DataFrame:
    export = frame.copy(deep=True)
    for column in export.columns:
        if pd.api.types.is_datetime64_any_dtype(export[column]):
            export[column] = export[column].dt.strftime("%Y-%m-%d %H:%M:%S")
        elif export[column].dtype == "object":
            export[column] = export[column].map(_cell_to_export_value)
    return export


def _cell_to_export_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True)
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return value


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 50) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "_No rows._"
    table = frame[available].head(max_rows).copy()
    rows = [
        "| " + " | ".join(available) + " |",
        "| " + " | ".join("---" for _ in available) + " |",
    ]
    for record in table.to_dict("records"):
        rows.append("| " + " | ".join(_format_markdown_value(record[column]) for column in available) + " |")
    return "\n".join(rows)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)


def _format_markdown_value(value: Any) -> str:
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        return f"{value:.6f}"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True).replace("|", "\\|")
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).replace("|", "\\|").replace("\n", " ")


def _resolve_settings(
    config: Settings | PaperWorkflowStatusSettings | dict[str, Any] | str | Path | None,
) -> tuple[Settings, PaperWorkflowStatusSettings]:
    if config is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.paper_workflow_status
    if isinstance(config, Settings):
        return config, config.paper_workflow_status
    if isinstance(config, (str, Path)):
        project = load_settings(Path(config))
        return project, project.paper_workflow_status
    project = load_settings(Path("config/default.yaml"))
    if isinstance(config, PaperWorkflowStatusSettings):
        return project, config
    if isinstance(config, dict):
        payload = dict(project.paper_workflow_status.model_dump())
        for key, value in config.items():
            if key == "paper_workflow_status" and isinstance(value, dict):
                payload.update(value)
            elif key in payload:
                payload[key] = value
        return project, PaperWorkflowStatusSettings(**payload)
    raise TypeError("config must be Settings, PaperWorkflowStatusSettings, dict, path, or None")


def _date_string(value: Any) -> str:
    if not _present(value):
        return ""
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        return ""
    return str(timestamp.date())


def _int_or_zero(value: Any) -> int:
    if not _present(value):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _present(value: Any) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    return str(value).strip() != ""


def _string_or_empty(value: Any) -> str:
    return str(value).strip() if _present(value) else ""


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if np.isnan(value):
            return None
        return float(value)
    if isinstance(value, float) and np.isnan(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
