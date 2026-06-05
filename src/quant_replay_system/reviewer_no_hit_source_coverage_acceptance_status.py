"""Status view for reviewer no-hit source coverage acceptance artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.reviewer_no_hit_source_coverage_acceptance_health import (
    check_reviewer_no_hit_source_coverage_acceptance_health,
)
from quant_replay_system.reviewer_no_hit_source_coverage_acceptance_index import (
    scan_reviewer_no_hit_source_coverage_acceptance_artifacts,
)


NO_STAGE = "NO_REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTANCE"
NEEDS_REVIEW_STAGE = "REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTANCE_NEEDS_REVIEW"
ACCEPTED_STAGE = "REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTED_AS_SUPPORTING_CONTEXT"
HEALTH_WARN_STAGE = "REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTANCE_HEALTH_WARN"
FAILED_STAGE = "REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTANCE_FAILED"


def run_reviewer_no_hit_source_coverage_acceptance_status(
    *,
    root: str | Path = "outputs/reports/reviewer_no_hit_source_coverage_acceptance",
    output_dir: str | Path = "outputs/reports/reviewer_no_hit_source_coverage_acceptance/status",
) -> dict[str, Any]:
    index = scan_reviewer_no_hit_source_coverage_acceptance_artifacts(root)
    health = check_reviewer_no_hit_source_coverage_acceptance_health(root=root, output_dir=Path(output_dir) / "_health_probe", index_df=index)
    latest = index.iloc[0].to_dict() if not index.empty else {}
    if index.empty:
        status = "WARN"
        stage = NO_STAGE
        next_action = "Run reviewer-no-hit-source-coverage-acceptance to create reviewer acceptance templates."
    elif health["status"] == "FAIL":
        status = "FAIL"
        stage = FAILED_STAGE
        next_action = "Repair reviewer no-hit acceptance artifacts before using them as research-status context."
    elif health["status"] == "WARN":
        status = "WARN"
        stage = HEALTH_WARN_STAGE
        next_action = "Review reviewer no-hit acceptance health warnings."
    elif _int(latest.get("accepted_count")) > 0:
        status = "WARN" if _int(latest.get("remaining_blocked_count")) > 0 else "PASS"
        stage = ACCEPTED_STAGE
        next_action = "Accepted no-hit source coverage is supporting context only; run checklist validation later with complete PIT metadata."
    else:
        status = "WARN"
        stage = NEEDS_REVIEW_STAGE
        next_action = "Complete reviewer acceptance fields for no-hit source coverage, query windows, and survivorship rationale."
    acceptance_id = _string(latest.get("acceptance_id")) or "none"
    output_dir = Path(output_dir)
    artifact_dir = output_dir / acceptance_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "latest_acceptance_id": _string(latest.get("acceptance_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health["status"],
        "enrichment_id": _string(latest.get("enrichment_id")),
        "source_packet_id": _string(latest.get("source_packet_id")),
        "policy_comparison_id": _string(latest.get("policy_comparison_id")),
        "row_count": _int(latest.get("row_count")),
        "accepted_count": _int(latest.get("accepted_count")),
        "rejected_count": _int(latest.get("rejected_count")),
        "needs_more_evidence_count": _int(latest.get("needs_more_evidence_count")),
        "needs_review_count": _int(latest.get("needs_review_count")),
        "reviewer_acceptance_required_count": _int(latest.get("reviewer_acceptance_required_count")),
        "accepted_supporting_context_count": _int(latest.get("accepted_supporting_context_count")),
        "survivorship_rationale_required_count": _int(latest.get("survivorship_rationale_required_count")),
        "checklist_pass_count": _int(latest.get("checklist_pass_count")),
        "remaining_blocked_count": _int(latest.get("remaining_blocked_count")),
        "report_path": _string(latest.get("report_path")),
        "next_manual_action": next_action,
    }
    frame = pd.DataFrame(
        [
            {
                "component": "REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTANCE_STATUS",
                "status": status,
                "latest_artifact_id": summary["latest_acceptance_id"],
                "report_path": summary["report_path"],
                "row_count": summary["row_count"],
                "accepted_count": summary["accepted_count"],
                "remaining_blocked_count": summary["remaining_blocked_count"],
                "checklist_pass_count": summary["checklist_pass_count"],
                "next_action": next_action,
            }
        ]
    )
    status_csv = artifact_dir / "reviewer_no_hit_source_coverage_acceptance_status.csv"
    summary_csv = artifact_dir / "reviewer_no_hit_source_coverage_acceptance_status_summary.csv"
    report = artifact_dir / "reviewer_no_hit_source_coverage_acceptance_status_report.md"
    metadata = artifact_dir / "metadata.json"
    frame.to_csv(status_csv, index=False)
    pd.DataFrame([summary]).to_csv(summary_csv, index=False)
    metadata.write_text(json.dumps({"status_id": acceptance_id, **summary, "approval_applied": False, "universe_exported": False, "no_current_candidates_generated": True}, indent=2, sort_keys=True), encoding="utf-8")
    report.write_text(f"# Reviewer No-Hit Source Coverage Acceptance Status\n\nstatus: {status}\nworkflow_stage: {stage}\nnext_manual_action: {next_action}\n", encoding="utf-8")
    return {"status": status, "workflow_stage": stage, "latest_acceptance_id": summary["latest_acceptance_id"], "health_status": health["status"], "enrichment_id": summary["enrichment_id"], "source_packet_id": summary["source_packet_id"], "policy_comparison_id": summary["policy_comparison_id"], "row_count": summary["row_count"], "accepted_count": summary["accepted_count"], "rejected_count": summary["rejected_count"], "needs_more_evidence_count": summary["needs_more_evidence_count"], "needs_review_count": summary["needs_review_count"], "reviewer_acceptance_required_count": summary["reviewer_acceptance_required_count"], "accepted_supporting_context_count": summary["accepted_supporting_context_count"], "survivorship_rationale_required_count": summary["survivorship_rationale_required_count"], "checklist_pass_count": summary["checklist_pass_count"], "remaining_blocked_count": summary["remaining_blocked_count"], "report_path": summary["report_path"], "next_manual_action": next_action, "status_frame": frame, "summary_frame": pd.DataFrame([summary]), "artifact_paths": {"artifact_dir": artifact_dir, "report": report, "metadata": metadata}}


def _int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _string(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()
