"""Unified local-only research workflow dashboard."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import LocalResearchDashboardSettings, Settings, load_settings


LOCAL_RESEARCH_DASHBOARD_LIMITATIONS = [
    "Scans local artifact metadata only.",
    "Does not regenerate data preparation, current-candidate, or paper-trading artifacts.",
    "Does not apply reviews, reconcile fills, place orders, call brokers, or fetch network data.",
    "Stage inference is conservative when artifacts are missing or metadata is incomplete.",
]

DASHBOARD_COLUMNS = [
    "workflow_area",
    "component",
    "status",
    "stage",
    "latest_artifact_id",
    "decision_date",
    "universe_name",
    "report_path",
    "metadata_path",
    "issue_count",
    "warning_count",
    "error_count",
    "next_action",
    "notes",
]

SUMMARY_COLUMNS = [
    "workflow_stage",
    "status",
    "latest_decision_date",
    "universe_name",
    "data_preparation_status",
    "snapshot_quality_status",
    "current_candidate_status",
    "current_candidate_health_status",
    "current_to_paper_status",
    "current_to_paper_review_status",
    "paper_review_status",
    "paper_daily_status",
    "reconciliation_status",
    "paper_workflow_status",
    "next_manual_action",
]

COMPONENTS = [
    "DATA_PREPARATION_WORKFLOW",
    "SNAPSHOT_QUALITY",
    "CURRENT_CANDIDATES",
    "CURRENT_CANDIDATE_HEALTH",
    "CURRENT_TO_PAPER_HANDOFF",
    "CURRENT_TO_PAPER_REVIEW_HANDOFF",
    "REVIEW_TEMPLATE_HEALTH",
    "PAPER_REVIEW",
    "DAILY_PAPER",
    "RECONCILIATION",
    "PAPER_WORKFLOW_STATUS",
]

WORKFLOW_AREAS = {
    "DATA_PREPARATION_WORKFLOW": "DATA_PREPARATION",
    "SNAPSHOT_QUALITY": "DATA_PREPARATION",
    "CURRENT_CANDIDATES": "CURRENT_CANDIDATES",
    "CURRENT_CANDIDATE_HEALTH": "CURRENT_CANDIDATES",
    "CURRENT_TO_PAPER_HANDOFF": "PAPER_TRADING",
    "CURRENT_TO_PAPER_REVIEW_HANDOFF": "PAPER_TRADING",
    "REVIEW_TEMPLATE_HEALTH": "PAPER_TRADING",
    "PAPER_REVIEW": "PAPER_TRADING",
    "DAILY_PAPER": "PAPER_TRADING",
    "RECONCILIATION": "PAPER_TRADING",
    "PAPER_WORKFLOW_STATUS": "PAPER_TRADING",
}


@dataclass(frozen=True)
class LocalResearchDashboardArtifactPaths:
    artifact_dir: Path
    local_research_dashboard: Path
    local_research_dashboard_csv: Path
    local_research_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "local_research_dashboard": self.local_research_dashboard,
            "local_research_dashboard_csv": self.local_research_dashboard_csv,
            "local_research_summary": self.local_research_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class LocalResearchDashboardResult:
    dashboard_id: str
    status: str
    latest_decision_date: str
    universe_name: str
    data_preparation_status: str
    snapshot_quality_status: str
    current_candidate_status: str
    current_candidate_health_status: str
    current_to_paper_status: str
    current_to_paper_review_status: str
    paper_review_status: str
    paper_daily_status: str
    reconciliation_status: str
    paper_workflow_status: str
    next_manual_action: str
    workflow_stage: str
    dashboard_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_local_research_dashboard(
    *,
    root: str | Path | None = None,
    data_preparation_root: str | Path | None = None,
    current_candidates_root: str | Path | None = None,
    paper_trading_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    decision_date: str | pd.Timestamp | None = None,
    universe_name: str | None = None,
    config: Settings | LocalResearchDashboardSettings | dict[str, Any] | str | Path | None = None,
) -> LocalResearchDashboardResult:
    """Scan local research workflow artifacts and write a unified status dashboard."""

    project_settings, dashboard_settings = _resolve_settings(config)
    if dashboard_settings.enable_live_trading or dashboard_settings.enable_broker_api:
        raise ValueError("Local research dashboard cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else dashboard_settings.root_dir
    effective_data_prep_root = (
        Path(data_preparation_root)
        if data_preparation_root is not None
        else dashboard_settings.data_preparation_root
    )
    effective_current_root = (
        Path(current_candidates_root)
        if current_candidates_root is not None
        else dashboard_settings.current_candidates_root
    )
    effective_paper_root = Path(paper_trading_root) if paper_trading_root is not None else dashboard_settings.paper_trading_root
    effective_output_dir = Path(output_dir) if output_dir is not None else dashboard_settings.output_dir
    if root is not None:
        if data_preparation_root is None:
            effective_data_prep_root = effective_root / "data_preparation"
        if current_candidates_root is None:
            effective_current_root = effective_root / "current_candidates"
        if paper_trading_root is None:
            effective_paper_root = effective_root / "paper_trading"

    scan = scan_local_research_workflow_artifacts(
        root=effective_root,
        data_preparation_root=effective_data_prep_root,
        current_candidates_root=effective_current_root,
        paper_trading_root=effective_paper_root,
        decision_date=decision_date,
        universe_name=universe_name,
    )
    dashboard_frame = build_local_research_dashboard_frame(
        scan,
        decision_date=decision_date,
        universe_name=universe_name,
    )
    workflow_stage = infer_local_research_workflow_stage(dashboard_frame)
    next_manual_action = infer_local_research_next_action(dashboard_frame, workflow_stage=workflow_stage)
    summary_frame = summarize_local_research_status(
        dashboard_frame,
        workflow_stage=workflow_stage,
        next_manual_action=next_manual_action,
    )
    summary = summary_frame.iloc[0].to_dict()
    dashboard_id = generate_local_research_dashboard_id(
        dashboard_frame,
        decision_date=decision_date,
        config_version=dashboard_settings.config_version,
    )
    paths = resolve_local_research_dashboard_paths(effective_output_dir, dashboard_id)
    warnings = _dashboard_warnings(dashboard_frame, workflow_stage)
    audit_metadata = {
        "dashboard_id": dashboard_id,
        "root_dir": effective_root,
        "data_preparation_root": effective_data_prep_root,
        "current_candidates_root": effective_current_root,
        "paper_trading_root": effective_paper_root,
        "decision_date_filter": _date_string(decision_date),
        "universe_name_filter": _string_or_empty(universe_name),
        "workflow_stage": workflow_stage,
        "strict": dashboard_settings.strict,
        "config_version": dashboard_settings.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "network_api_calls_used_in_tests": False,
        "local_research_dashboard_only": True,
    }
    result = LocalResearchDashboardResult(
        dashboard_id=dashboard_id,
        status=str(summary.get("status", "WARN")),
        latest_decision_date=str(summary.get("latest_decision_date", "")),
        universe_name=str(summary.get("universe_name", "")),
        data_preparation_status=str(summary.get("data_preparation_status", "MISSING")),
        snapshot_quality_status=str(summary.get("snapshot_quality_status", "MISSING")),
        current_candidate_status=str(summary.get("current_candidate_status", "MISSING")),
        current_candidate_health_status=str(summary.get("current_candidate_health_status", "MISSING")),
        current_to_paper_status=str(summary.get("current_to_paper_status", "MISSING")),
        current_to_paper_review_status=str(summary.get("current_to_paper_review_status", "MISSING")),
        paper_review_status=str(summary.get("paper_review_status", "MISSING")),
        paper_daily_status=str(summary.get("paper_daily_status", "MISSING")),
        reconciliation_status=str(summary.get("reconciliation_status", "MISSING")),
        paper_workflow_status=str(summary.get("paper_workflow_status", "MISSING")),
        next_manual_action=next_manual_action,
        workflow_stage=workflow_stage,
        dashboard_frame=dashboard_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=LOCAL_RESEARCH_DASHBOARD_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if dashboard_settings.write_artifacts:
        write_local_research_dashboard_artifacts(result)
    _ = project_settings
    return result


def scan_local_research_workflow_artifacts(
    *,
    root: str | Path,
    data_preparation_root: str | Path,
    current_candidates_root: str | Path,
    paper_trading_root: str | Path,
    decision_date: str | pd.Timestamp | None = None,
    universe_name: str | None = None,
) -> pd.DataFrame:
    """Scan local metadata files for the unified research workflow."""

    root_path = Path(root)
    data_prep_root = Path(data_preparation_root)
    current_root = Path(current_candidates_root)
    paper_root = Path(paper_trading_root)
    requested_date = _date_string(decision_date)
    requested_universe = _string_or_empty(universe_name)
    records: list[dict[str, Any]] = []

    records.extend(_scan_data_preparation_workflow_status(data_prep_root, requested_date, requested_universe))
    records.extend(_scan_snapshot_quality(root_path / "snapshot_quality", requested_date))
    records.extend(_scan_current_candidates(current_root, requested_date, requested_universe))
    records.extend(_scan_current_candidate_health(current_root / "health"))
    records.extend(_scan_current_to_paper_handoff(root_path / "current_to_paper_handoff", requested_date, requested_universe))
    records.extend(_scan_current_to_paper_review_handoff(root_path / "current_to_paper_review_handoff"))
    records.extend(_scan_review_template_health(paper_root / "review_template_health"))
    records.extend(_scan_paper_reviews(paper_root / "reviews"))
    records.extend(_scan_daily_paper(paper_root / "daily", requested_date))
    records.extend(_scan_reconciliation(paper_root / "reconciliation"))
    records.extend(_scan_paper_workflow_status(paper_root / "workflow_status", requested_date))
    return _finalize_scan_frame(pd.DataFrame(records))


def build_local_research_dashboard_frame(
    scan_frame: pd.DataFrame,
    *,
    decision_date: str | pd.Timestamp | None = None,
    universe_name: str | None = None,
) -> pd.DataFrame:
    """Build one dashboard row per local research workflow component."""

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
            rows.append(_missing_dashboard_row(component))
            continue
        latest = active_chain.get(component, _latest_record(component_rows)).copy()
        latest = _annotate_stale_component_warnings(latest, component_rows)
        latest["next_action"] = _component_next_action(component, latest.get("status", ""))
        rows.append(latest)
    _ = decision_date, universe_name
    return _finalize_dashboard_frame(pd.DataFrame(rows))


def _active_reviewed_paper_chain(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Resolve the active reviewed paper chain from the selected daily artifact."""

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
            chain["REVIEW_TEMPLATE_HEALTH_MISSING"] = _missing_dashboard_row(
                "REVIEW_TEMPLATE_HEALTH",
                notes="No template health artifact linked to active reviewed decisions.",
            )
    else:
        chain["PAPER_REVIEW_MISSING"] = _missing_dashboard_row(
            "PAPER_REVIEW",
            notes="No paper review artifact linked to active reviewed decisions.",
        )
        chain["REVIEW_TEMPLATE_HEALTH_MISSING"] = _missing_dashboard_row(
            "REVIEW_TEMPLATE_HEALTH",
            notes="No linked paper review artifact was available for template health selection.",
        )
    return chain


def _active_daily_record(frame: pd.DataFrame) -> dict[str, Any] | None:
    daily_rows = frame.loc[frame["component"] == "DAILY_PAPER"]
    if daily_rows.empty:
        return None
    reviewed_rows = daily_rows.loc[daily_rows["status"] == "REVIEWED_READY"]
    if not reviewed_rows.empty:
        return _latest_record(reviewed_rows)
    return _latest_record(daily_rows)


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
            workflow_area="PAPER_TRADING",
            component="REVIEW_TEMPLATE_HEALTH",
            status=status,
            stage="REVIEW_TEMPLATE_HEALTH_READY",
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
    stale_warning_count = 0
    stale_error_count = 0
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
    if not stale_warning_count and not stale_error_count:
        return selected
    annotated = selected.copy()
    notes = _string_or_empty(annotated.get("notes"))
    stale_note = f"stale_warning_count={stale_warning_count}; stale_error_count={stale_error_count}"
    annotated["notes"] = f"{notes}; {stale_note}" if notes else stale_note
    return annotated


def infer_local_research_workflow_stage(dashboard_frame: pd.DataFrame) -> str:
    """Infer the current unified research workflow stage."""

    statuses = _status_by_component(dashboard_frame)
    if _has_attention_status(dashboard_frame):
        return "LOCAL_RESEARCH_NEEDS_ATTENTION"
    if statuses["PAPER_WORKFLOW_STATUS"] == "PASS":
        return "LOCAL_RESEARCH_WORKFLOW_COMPLETE"
    if statuses["PAPER_WORKFLOW_STATUS"] in {"READY", "REVIEWED_READY"}:
        return "PAPER_WORKFLOW_READY"
    if all(status == "MISSING" for status in statuses.values()):
        return "NO_DATA"
    if statuses["CURRENT_CANDIDATES"] == "MISSING":
        if statuses["SNAPSHOT_QUALITY"] != "MISSING":
            return "SNAPSHOT_READY"
        return "DATA_PREPARATION_READY"
    if statuses["CURRENT_CANDIDATE_HEALTH"] == "MISSING":
        return "CURRENT_CANDIDATES_READY"
    if statuses["CURRENT_TO_PAPER_HANDOFF"] == "MISSING":
        return "CURRENT_CANDIDATES_HEALTH_READY"
    if statuses["CURRENT_TO_PAPER_REVIEW_HANDOFF"] == "MISSING":
        return "PAPER_HANDOFF_READY"
    if statuses["REVIEW_TEMPLATE_HEALTH"] == "MISSING":
        return "REVIEW_TEMPLATE_READY"
    if statuses["PAPER_REVIEW"] == "MISSING":
        return "REVIEW_TEMPLATE_HEALTH_READY"
    if statuses["DAILY_PAPER"] == "MISSING":
        return "REVIEW_APPLIED"
    if statuses["RECONCILIATION"] == "MISSING":
        return "PAPER_DAILY_READY"
    if statuses["PAPER_WORKFLOW_STATUS"] == "MISSING":
        return "RECONCILIATION_READY"
    return "LOCAL_RESEARCH_NEEDS_ATTENTION"


def infer_local_research_next_action(
    dashboard_frame: pd.DataFrame,
    *,
    workflow_stage: str | None = None,
) -> str:
    """Infer the next manual action for the unified research workflow."""

    stage = workflow_stage or infer_local_research_workflow_stage(dashboard_frame)
    actions = {
        "NO_DATA": "Run data-pipeline.",
        "DATA_PREPARATION_READY": "Run current-candidates.",
        "SNAPSHOT_READY": "Run current-candidates.",
        "CURRENT_CANDIDATES_READY": "Run current-candidates-index.",
        "CURRENT_CANDIDATES_HEALTH_READY": "Run current-to-paper.",
        "PAPER_HANDOFF_READY": "Run current-to-paper-review.",
        "REVIEW_TEMPLATE_READY": "Manually edit review_updates_template.csv.",
        "REVIEW_TEMPLATE_HEALTH_READY": "Run paper-review-decisions --health-check.",
        "REVIEW_APPLIED": "Run paper-daily --reviewed-decisions.",
        "PAPER_DAILY_READY": "Enter manual fills CSV.",
        "RECONCILIATION_READY": "Run paper-workflow-status.",
        "PAPER_WORKFLOW_READY": "Review paper workflow status report.",
        "LOCAL_RESEARCH_WORKFLOW_COMPLETE": "Review completed local research workflow artifacts.",
        "LOCAL_RESEARCH_NEEDS_ATTENTION": "Review warnings/errors.",
    }
    return actions.get(stage, "Review local research workflow artifacts.")


def summarize_local_research_status(
    dashboard_frame: pd.DataFrame,
    *,
    workflow_stage: str,
    next_manual_action: str,
) -> pd.DataFrame:
    """Summarize the unified dashboard into one row."""

    frame = _finalize_dashboard_frame(dashboard_frame)
    by_component = {row["component"]: row for row in frame.to_dict("records")}
    active = frame.loc[frame["status"] != "MISSING"] if not frame.empty else pd.DataFrame()
    active_statuses = [str(row.get("status", "")).upper() for row in active.to_dict("records")]
    all_statuses = [str(row.get("status", "")).upper() for row in frame.to_dict("records")]
    missing_count = all_statuses.count("MISSING")
    error_count = int(pd.to_numeric(frame["error_count"], errors="coerce").fillna(0).sum()) if not frame.empty else 0
    warning_count = int(pd.to_numeric(frame["warning_count"], errors="coerce").fillna(0).sum()) if not frame.empty else 0
    status = (
        "FAIL"
        if "FAIL" in active_statuses or error_count
        else "WARN"
        if "WARN" in active_statuses or missing_count or warning_count
        else "PASS"
    )
    row = {
        "workflow_stage": workflow_stage,
        "status": status,
        "latest_decision_date": _latest_decision_date(frame),
        "universe_name": _latest_universe_name(frame),
        "data_preparation_status": _component_status(by_component, "DATA_PREPARATION_WORKFLOW"),
        "snapshot_quality_status": _component_status(by_component, "SNAPSHOT_QUALITY"),
        "current_candidate_status": _component_status(by_component, "CURRENT_CANDIDATES"),
        "current_candidate_health_status": _component_status(by_component, "CURRENT_CANDIDATE_HEALTH"),
        "current_to_paper_status": _component_status(by_component, "CURRENT_TO_PAPER_HANDOFF"),
        "current_to_paper_review_status": _component_status(by_component, "CURRENT_TO_PAPER_REVIEW_HANDOFF"),
        "paper_review_status": _component_status(by_component, "PAPER_REVIEW"),
        "paper_daily_status": _component_status(by_component, "DAILY_PAPER"),
        "reconciliation_status": _component_status(by_component, "RECONCILIATION"),
        "paper_workflow_status": _component_status(by_component, "PAPER_WORKFLOW_STATUS"),
        "next_manual_action": next_manual_action,
    }
    return pd.DataFrame([row], columns=SUMMARY_COLUMNS)


def resolve_local_research_dashboard_paths(
    output_dir: str | Path,
    dashboard_id: str,
) -> LocalResearchDashboardArtifactPaths:
    """Resolve deterministic dashboard artifact paths."""

    artifact_dir = Path(output_dir) / dashboard_id
    return LocalResearchDashboardArtifactPaths(
        artifact_dir=artifact_dir,
        local_research_dashboard=artifact_dir / "local_research_dashboard.md",
        local_research_dashboard_csv=artifact_dir / "local_research_dashboard.csv",
        local_research_summary=artifact_dir / "local_research_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_local_research_dashboard_artifacts(result: LocalResearchDashboardResult) -> dict[str, Path]:
    """Write dashboard markdown, CSVs, and metadata."""

    paths = LocalResearchDashboardArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.dashboard_frame, paths.local_research_dashboard_csv)
    _export_dataframe(result.summary_frame, paths.local_research_summary)
    metadata = build_local_research_dashboard_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.local_research_dashboard.write_text(render_local_research_dashboard_report(result, metadata), encoding="utf-8")
    return paths.as_dict()


def build_local_research_dashboard_metadata(
    result: LocalResearchDashboardResult,
    paths: LocalResearchDashboardArtifactPaths,
) -> dict[str, Any]:
    """Build metadata for dashboard artifacts."""

    return {
        "dashboard_id": result.dashboard_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_decision_date": result.latest_decision_date,
        "universe_name": result.universe_name,
        "next_manual_action": result.next_manual_action,
        "component_statuses": result.summary_frame.to_dict("records")[0] if not result.summary_frame.empty else {},
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "network_api_calls_used_in_tests": False,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_local_research_dashboard_report(
    result: LocalResearchDashboardResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render the unified local research workflow dashboard report."""

    _ = metadata
    lines = [
        f"# Unified Local Research Workflow Dashboard: {result.dashboard_id}",
        "",
        "No broker or live trading integration was invoked. This dashboard scans local research artifacts only.",
        "",
        "## Workflow Summary",
        "",
        _markdown_table(
            result.summary_frame,
            [
                "workflow_stage",
                "status",
                "latest_decision_date",
                "universe_name",
                "next_manual_action",
            ],
        ),
        "",
        "## Component Status",
        "",
        _markdown_table(
            result.dashboard_frame,
            [
                "workflow_area",
                "component",
                "status",
                "stage",
                "latest_artifact_id",
                "decision_date",
                "universe_name",
                "issue_count",
                "warning_count",
                "error_count",
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


def generate_local_research_dashboard_id(
    dashboard_frame: pd.DataFrame,
    *,
    decision_date: str | pd.Timestamp | None,
    config_version: str,
) -> str:
    """Generate deterministic dashboard id."""

    frame = _finalize_dashboard_frame(dashboard_frame)
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


def _scan_data_preparation_workflow_status(root: Path, decision_date: str, universe_name: str) -> list[dict[str, Any]]:
    scan_root = root if root.name == "workflow_status" else root / "workflow_status"
    records = []
    for metadata_path in _metadata_paths(scan_root, "metadata.json"):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None or not metadata.get("workflow_status_id"):
            continue
        metadata_date = _date_string(metadata.get("latest_decision_date"))
        metadata_universe = _string_or_empty(metadata.get("universe_name")) or _string_or_empty(
            metadata.get("audit_metadata", {}).get("universe_name_filter") if isinstance(metadata.get("audit_metadata"), dict) else ""
        )
        if decision_date and metadata_date and metadata_date != decision_date:
            continue
        if universe_name and metadata_universe and metadata_universe != universe_name:
            continue
        output_files = _output_files(metadata)
        records.append(
            _record(
                workflow_area="DATA_PREPARATION",
                component="DATA_PREPARATION_WORKFLOW",
                status=_string_or_empty(metadata.get("status")) or "READY",
                stage=_string_or_empty(metadata.get("workflow_stage")),
                latest_artifact_id=_string_or_empty(metadata.get("workflow_status_id")) or metadata_path.parent.name,
                decision_date=metadata_date,
                universe_name=metadata_universe,
                report_path=output_files.get("data_preparation_workflow_status_report", metadata_path.parent / "data_preparation_workflow_status_report.md"),
                metadata_path=metadata_path,
                warning_count=len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else 0,
                notes=f"next_manual_action={_string_or_empty(metadata.get('next_manual_action'))}",
                created_at=metadata.get("created_at"),
            )
        )
    return records


def _scan_snapshot_quality(root: Path, decision_date: str) -> list[dict[str, Any]]:
    records = []
    for metadata_path in _metadata_paths(root, "metadata.json"):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None or not metadata.get("quality_gate_id"):
            continue
        output_files = _output_files(metadata)
        records.append(
            _record(
                workflow_area="DATA_PREPARATION",
                component="SNAPSHOT_QUALITY",
                status=_string_or_empty(metadata.get("status")) or "READY",
                stage="SNAPSHOT_READY",
                latest_artifact_id=_string_or_empty(metadata.get("quality_gate_id")) or metadata_path.parent.name,
                decision_date=decision_date,
                report_path=output_files.get("snapshot_quality_gate_report", metadata_path.parent / "snapshot_quality_gate_report.md"),
                metadata_path=metadata_path,
                issue_count=_int_or_zero(metadata.get("issue_count")),
                warning_count=_int_or_zero(metadata.get("warning_count")),
                error_count=_int_or_zero(metadata.get("error_count")),
                notes=f"snapshot_id={_string_or_empty(metadata.get('snapshot_id'))}",
                created_at=metadata.get("created_at"),
            )
        )
    return records


def _scan_current_candidates(root: Path, decision_date: str, universe_name: str) -> list[dict[str, Any]]:
    records = []
    for metadata_path in _metadata_paths(root, "metadata.json", excluded_parts={"index", "health"}):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None or not metadata.get("run_id"):
            continue
        metadata_date = _date_string(metadata.get("decision_date"))
        metadata_universe = _string_or_empty(metadata.get("universe_name"))
        if decision_date and metadata_date != decision_date:
            continue
        if universe_name and metadata_universe != universe_name:
            continue
        output_files = _output_files(metadata)
        row_counts = metadata.get("row_counts") if isinstance(metadata.get("row_counts"), dict) else {}
        snapshot_quality = metadata.get("snapshot_quality") if isinstance(metadata.get("snapshot_quality"), dict) else {}
        records.append(
            _record(
                workflow_area="CURRENT_CANDIDATES",
                component="CURRENT_CANDIDATES",
                status="READY",
                stage="CURRENT_CANDIDATES_READY",
                latest_artifact_id=_string_or_empty(metadata.get("run_id")) or metadata_path.parent.name,
                decision_date=metadata_date,
                universe_name=metadata_universe,
                report_path=output_files.get("current_candidates_report", metadata_path.parent / "current_candidates_report.md"),
                metadata_path=metadata_path,
                warning_count=len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else 0,
                notes=(
                    f"candidate_count={_string_or_empty(row_counts.get('candidates'))}; "
                    f"snapshot_quality_status={_string_or_empty(snapshot_quality.get('status'))}"
                ),
                created_at=metadata.get("created_at"),
            )
        )
    return records


def _scan_current_candidate_health(root: Path) -> list[dict[str, Any]]:
    return _health_records(
        root,
        workflow_area="CURRENT_CANDIDATES",
        component="CURRENT_CANDIDATE_HEALTH",
        id_key="health_check_id",
        report_key="current_candidate_artifact_health_report",
        default_report="current_candidate_artifact_health_report.md",
        stage="CURRENT_CANDIDATES_HEALTH_READY",
    )


def _scan_current_to_paper_handoff(root: Path, decision_date: str, universe_name: str) -> list[dict[str, Any]]:
    records = []
    for metadata_path in _metadata_paths(root, "handoff_metadata.json"):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None or not metadata.get("handoff_id"):
            continue
        metadata_date = _date_string(metadata.get("selected_decision_date"))
        metadata_universe = _string_or_empty(metadata.get("selected_universe_name"))
        if decision_date and metadata_date != decision_date:
            continue
        if universe_name and metadata_universe != universe_name:
            continue
        output_files = _output_files(metadata)
        records.append(
            _record(
                workflow_area="PAPER_TRADING",
                component="CURRENT_TO_PAPER_HANDOFF",
                status="READY",
                stage="PAPER_HANDOFF_READY",
                latest_artifact_id=_string_or_empty(metadata.get("handoff_id")) or metadata_path.parent.name,
                decision_date=metadata_date,
                universe_name=metadata_universe,
                report_path=output_files.get("handoff_report", metadata_path.parent / "handoff_report.md"),
                metadata_path=metadata_path,
                warning_count=len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else 0,
                notes=f"selected_run_id={_string_or_empty(metadata.get('selected_run_id'))}",
                created_at=metadata.get("created_at"),
            )
        )
    return records


def _scan_current_to_paper_review_handoff(root: Path) -> list[dict[str, Any]]:
    records = []
    for metadata_path in _metadata_paths(root, "metadata.json"):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None or not metadata.get("review_handoff_id"):
            continue
        output_files = _output_files(metadata)
        records.append(
            _record(
                workflow_area="PAPER_TRADING",
                component="CURRENT_TO_PAPER_REVIEW_HANDOFF",
                status="READY",
                stage="REVIEW_TEMPLATE_READY",
                latest_artifact_id=_string_or_empty(metadata.get("review_handoff_id")) or metadata_path.parent.name,
                report_path=output_files.get("review_handoff_report", metadata.get("report_path", metadata_path.parent / "review_handoff_report.md")),
                metadata_path=metadata_path,
                warning_count=len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else 0,
                notes=f"decision_count={_string_or_empty(metadata.get('decision_count'))}",
                created_at=metadata.get("created_at"),
            )
        )
    return records


def _scan_review_template_health(root: Path) -> list[dict[str, Any]]:
    return _health_records(
        root,
        workflow_area="PAPER_TRADING",
        component="REVIEW_TEMPLATE_HEALTH",
        id_key="health_check_id",
        report_key="review_template_health_report",
        default_report="review_template_health_report.md",
        stage="REVIEW_TEMPLATE_HEALTH_READY",
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
                workflow_area="PAPER_TRADING",
                component="PAPER_REVIEW",
                status="READY",
                stage="REVIEW_APPLIED",
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
        records.append(
            _record(
                workflow_area="PAPER_TRADING",
                component="DAILY_PAPER",
                status="REVIEWED_READY" if metadata.get("reviewed_decisions_used") is True else "READY",
                stage="PAPER_DAILY_READY",
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
        workflow_area="PAPER_TRADING",
        component="RECONCILIATION",
        id_key="reconciliation_id",
        report_key="reconciliation_report",
        default_report="reconciliation_report.md",
        stage="RECONCILIATION_READY",
    )


def _scan_paper_workflow_status(root: Path, decision_date: str) -> list[dict[str, Any]]:
    records = []
    for metadata_path in _metadata_paths(root, "metadata.json"):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None or not metadata.get("workflow_status_id"):
            continue
        metadata_date = _date_string(metadata.get("latest_decision_date"))
        if decision_date and metadata_date and metadata_date != decision_date:
            continue
        output_files = _output_files(metadata)
        records.append(
            _record(
                workflow_area="PAPER_TRADING",
                component="PAPER_WORKFLOW_STATUS",
                status=_string_or_empty(metadata.get("status")) or "READY",
                stage=_string_or_empty(metadata.get("workflow_stage")) or "PAPER_WORKFLOW_READY",
                latest_artifact_id=_string_or_empty(metadata.get("workflow_status_id")) or metadata_path.parent.name,
                decision_date=metadata_date,
                report_path=output_files.get("paper_workflow_status_report", metadata_path.parent / "paper_workflow_status_report.md"),
                metadata_path=metadata_path,
                warning_count=len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else 0,
                notes=f"next_manual_action={_string_or_empty(metadata.get('next_manual_action'))}",
                created_at=metadata.get("created_at"),
            )
        )
    return records


def _health_records(
    root: Path,
    *,
    workflow_area: str,
    component: str,
    id_key: str,
    report_key: str,
    default_report: str,
    stage: str,
) -> list[dict[str, Any]]:
    records = []
    for metadata_path in _metadata_paths(root, "metadata.json"):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None or not metadata.get(id_key):
            continue
        output_files = _output_files(metadata)
        records.append(
            _record(
                workflow_area=workflow_area,
                component=component,
                status=_string_or_empty(metadata.get("status")) or "READY",
                stage=stage,
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
        "workflow_area": "",
        "component": "",
        "status": "",
        "stage": "",
        "latest_artifact_id": "",
        "decision_date": "",
        "universe_name": "",
        "report_path": "",
        "metadata_path": "",
        "issue_count": 0,
        "warning_count": 0,
        "error_count": 0,
        "next_action": "",
        "notes": "",
        "created_at": "",
    }
    row.update(values)
    component = _string_or_empty(row.get("component"))
    row["workflow_area"] = _string_or_empty(row.get("workflow_area")) or WORKFLOW_AREAS.get(component, "")
    row["status"] = _string_or_empty(row["status"]).upper()
    row["decision_date"] = _date_string(row.get("decision_date"))
    row["report_path"] = _string_or_empty(row.get("report_path"))
    row["metadata_path"] = _string_or_empty(row.get("metadata_path"))
    row["latest_artifact_id"] = _string_or_empty(row.get("latest_artifact_id"))
    row["issue_count"] = _int_or_zero(row.get("issue_count"))
    row["warning_count"] = _int_or_zero(row.get("warning_count"))
    row["error_count"] = _int_or_zero(row.get("error_count"))
    return row


def _missing_dashboard_row(component: str, *, notes: str = "No matching local artifact metadata found.") -> dict[str, Any]:
    return _record(
        workflow_area=WORKFLOW_AREAS.get(component, ""),
        component=component,
        status="MISSING",
        next_action=_component_next_action(component, "MISSING"),
        notes=notes,
    )


def _component_next_action(component: str, status: str) -> str:
    if status == "FAIL":
        return "Review warnings/errors."
    if component == "DATA_PREPARATION_WORKFLOW":
        return "Run data-prep-status." if status == "MISSING" else "Run current-candidates."
    if component == "SNAPSHOT_QUALITY":
        return "Run snapshot-quality." if status == "MISSING" else "Run current-candidates."
    if component == "CURRENT_CANDIDATES":
        return "Run current-candidates." if status == "MISSING" else "Run current-candidates-index."
    if component == "CURRENT_CANDIDATE_HEALTH":
        return "Run current-candidates-health." if status == "MISSING" else "Run current-to-paper."
    if component == "CURRENT_TO_PAPER_HANDOFF":
        return "Run current-to-paper." if status == "MISSING" else "Run current-to-paper-review."
    if component == "CURRENT_TO_PAPER_REVIEW_HANDOFF":
        return "Run current-to-paper-review." if status == "MISSING" else "Manually edit review_updates_template.csv."
    if component == "REVIEW_TEMPLATE_HEALTH":
        return "Run paper-review-template-health." if status == "MISSING" else "Run paper-review-decisions --health-check."
    if component == "PAPER_REVIEW":
        return "Run paper-review-decisions --health-check." if status == "MISSING" else "Run paper-daily --reviewed-decisions."
    if component == "DAILY_PAPER":
        return "Run paper-daily --reviewed-decisions." if status == "MISSING" else "Enter manual fills CSV."
    if component == "RECONCILIATION":
        return "Run paper-reconcile-fills." if status == "MISSING" else "Run paper-workflow-status."
    if component == "PAPER_WORKFLOW_STATUS":
        return "Run paper-workflow-status." if status == "MISSING" else "Review completed local research workflow artifacts."
    return ""


def _status_by_component(dashboard_frame: pd.DataFrame) -> dict[str, str]:
    frame = _finalize_dashboard_frame(dashboard_frame)
    values = {row["component"]: row["status"] for row in frame.to_dict("records")}
    for component in COMPONENTS:
        values.setdefault(component, "MISSING")
    return values


def _has_attention_status(dashboard_frame: pd.DataFrame) -> bool:
    frame = _finalize_dashboard_frame(dashboard_frame)
    if frame.empty:
        return False
    active = frame.loc[frame["status"] != "MISSING"]
    if active.empty:
        return False
    statuses = set(active["status"].astype(str).str.upper())
    if statuses.intersection({"FAIL", "WARN"}):
        return True
    error_count = int(pd.to_numeric(active["error_count"], errors="coerce").fillna(0).sum())
    return error_count > 0


def _component_status(by_component: dict[str, dict[str, Any]], component: str) -> str:
    row = by_component.get(component, {})
    return _string_or_empty(row.get("status")) or "MISSING"


def _latest_decision_date(frame: pd.DataFrame) -> str:
    dates = sorted(_date_string(value) for value in frame.get("decision_date", pd.Series(dtype="object")).tolist() if _date_string(value))
    return dates[-1] if dates else ""


def _latest_universe_name(frame: pd.DataFrame) -> str:
    values = sorted(_string_or_empty(value) for value in frame.get("universe_name", pd.Series(dtype="object")).tolist() if _string_or_empty(value))
    return values[-1] if values else ""


def _dashboard_warnings(dashboard_frame: pd.DataFrame, workflow_stage: str) -> list[str]:
    warnings = []
    if workflow_stage != "LOCAL_RESEARCH_WORKFLOW_COMPLETE":
        warnings.append(f"Workflow stage is {workflow_stage}; manual action is still needed.")
    failing = dashboard_frame.loc[dashboard_frame["status"] == "FAIL"] if not dashboard_frame.empty else pd.DataFrame()
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
    return _load_json_or_none(Path(path_text)) or {}


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
    columns = DASHBOARD_COLUMNS + ["created_at"]
    for column in columns:
        if column not in scan.columns:
            scan[column] = ""
    if scan.empty:
        return scan[columns]
    return scan[columns].sort_values(["workflow_area", "component", "decision_date", "created_at", "latest_artifact_id"], na_position="last").reset_index(drop=True)


def _finalize_dashboard_frame(frame: pd.DataFrame) -> pd.DataFrame:
    dashboard = frame.copy(deep=True)
    for column in DASHBOARD_COLUMNS:
        if column not in dashboard.columns:
            dashboard[column] = ""
    if dashboard.empty:
        return dashboard[DASHBOARD_COLUMNS]
    return dashboard[DASHBOARD_COLUMNS].sort_values(["component"], key=lambda series: series.map(_component_order)).reset_index(drop=True)


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
    config: Settings | LocalResearchDashboardSettings | dict[str, Any] | str | Path | None,
) -> tuple[Settings, LocalResearchDashboardSettings]:
    if config is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.local_research_dashboard
    if isinstance(config, Settings):
        return config, config.local_research_dashboard
    if isinstance(config, (str, Path)):
        project = load_settings(Path(config))
        return project, project.local_research_dashboard
    project = load_settings(Path("config/default.yaml"))
    if isinstance(config, LocalResearchDashboardSettings):
        return project, config
    if isinstance(config, dict):
        payload = dict(project.local_research_dashboard.model_dump())
        for key, value in config.items():
            if key == "local_research_dashboard" and isinstance(value, dict):
                payload.update(value)
            elif key in payload:
                payload[key] = value
        return project, LocalResearchDashboardSettings(**payload)
    raise TypeError("config must be Settings, LocalResearchDashboardSettings, dict, path, or None")


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
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
