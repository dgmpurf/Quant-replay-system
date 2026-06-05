"""Status view for reviewer no-hit acceptance downstream impact artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.reviewer_no_hit_acceptance_downstream_impact_health import (
    check_reviewer_no_hit_acceptance_downstream_impact_health,
)
from quant_replay_system.reviewer_no_hit_acceptance_downstream_impact_index import (
    scan_reviewer_no_hit_acceptance_downstream_impact_artifacts,
)


NO_STAGE = "NO_REVIEWER_NO_HIT_ACCEPTANCE_DOWNSTREAM_IMPACT"
NO_ACCEPTED_STAGE = "REVIEWER_NO_HIT_ACCEPTANCE_DOWNSTREAM_IMPACT_NO_ACCEPTED_CONTEXT"
SUPPORTING_STAGE = "REVIEWER_NO_HIT_ACCEPTANCE_DOWNSTREAM_IMPACT_SUPPORTING_CONTEXT_ONLY"
FAILED_STAGE = "REVIEWER_NO_HIT_ACCEPTANCE_DOWNSTREAM_IMPACT_FAILED"


def run_reviewer_no_hit_acceptance_downstream_impact_status(
    *,
    root: str | Path = "outputs/reports/reviewer_no_hit_acceptance_downstream_impact",
    output_dir: str | Path = "outputs/reports/reviewer_no_hit_acceptance_downstream_impact/status",
) -> dict[str, Any]:
    index = scan_reviewer_no_hit_acceptance_downstream_impact_artifacts(root)
    health = check_reviewer_no_hit_acceptance_downstream_impact_health(
        root=root,
        output_dir=Path(output_dir) / "_health_probe",
        index_df=index,
    )
    latest = index.iloc[0].to_dict() if not index.empty else {}
    if index.empty:
        status = "WARN"
        stage = NO_STAGE
        next_action = "Run reviewer-no-hit-acceptance-downstream-impact after reviewer acceptance artifacts exist."
    elif health["status"] == "FAIL":
        status = "FAIL"
        stage = FAILED_STAGE
        next_action = "Repair downstream impact artifacts before using them as research-status context."
    elif _int(latest.get("accepted_no_hit_context_count")) > 0:
        status = "WARN" if _int(latest.get("remaining_blocked_count")) > 0 else "PASS"
        stage = SUPPORTING_STAGE
        next_action = "Accepted no-hit context is linked as supporting context only; continue PIT evidence completion before approval."
    else:
        status = "WARN"
        stage = NO_ACCEPTED_STAGE
        next_action = "Complete reviewer no-hit acceptance before downstream accepted-context impact can be shown."
    impact_id = _string(latest.get("impact_id")) or "none"
    output_dir = Path(output_dir)
    artifact_dir = output_dir / impact_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "latest_impact_id": _string(latest.get("impact_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health["status"],
        "acceptance_id": _string(latest.get("acceptance_id")),
        "enrichment_id": _string(latest.get("enrichment_id")),
        "source_packet_id": _string(latest.get("source_packet_id")),
        "reviewed_no_hit_policy_comparison_id": _string(latest.get("reviewed_no_hit_policy_comparison_id")),
        "validator_id": _string(latest.get("validator_id")),
        "row_count": _int(latest.get("row_count")),
        "accepted_no_hit_context_count": _int(latest.get("accepted_no_hit_context_count")),
        "packet_context_gap_reduced_count": _int(latest.get("packet_context_gap_reduced_count")),
        "checklist_pass_count": _int(latest.get("checklist_pass_count")),
        "remaining_blocked_count": _int(latest.get("remaining_blocked_count")),
        "approval_applied": _bool(latest.get("approval_applied")),
        "report_path": _string(latest.get("report_path")),
        "next_manual_action": next_action,
    }
    frame = pd.DataFrame(
        [
            {
                "component": "REVIEWER_NO_HIT_ACCEPTANCE_DOWNSTREAM_IMPACT_STATUS",
                "status": status,
                "latest_artifact_id": summary["latest_impact_id"],
                "report_path": summary["report_path"],
                "row_count": summary["row_count"],
                "accepted_no_hit_context_count": summary["accepted_no_hit_context_count"],
                "remaining_blocked_count": summary["remaining_blocked_count"],
                "checklist_pass_count": summary["checklist_pass_count"],
                "next_action": next_action,
            }
        ]
    )
    status_csv = artifact_dir / "reviewer_no_hit_acceptance_downstream_impact_status.csv"
    summary_csv = artifact_dir / "reviewer_no_hit_acceptance_downstream_impact_status_summary.csv"
    report = artifact_dir / "reviewer_no_hit_acceptance_downstream_impact_status_report.md"
    metadata = artifact_dir / "metadata.json"
    frame.to_csv(status_csv, index=False)
    pd.DataFrame([summary]).to_csv(summary_csv, index=False)
    metadata.write_text(json.dumps({"status_id": impact_id, **summary, "universe_exported": False, "no_current_candidates_generated": True}, indent=2, sort_keys=True), encoding="utf-8")
    report.write_text(f"# Reviewer No-Hit Acceptance Downstream Impact Status\n\nstatus: {status}\nworkflow_stage: {stage}\nnext_manual_action: {next_action}\n", encoding="utf-8")
    return {"status": status, "workflow_stage": stage, "latest_impact_id": summary["latest_impact_id"], "health_status": health["status"], "acceptance_id": summary["acceptance_id"], "enrichment_id": summary["enrichment_id"], "source_packet_id": summary["source_packet_id"], "reviewed_no_hit_policy_comparison_id": summary["reviewed_no_hit_policy_comparison_id"], "validator_id": summary["validator_id"], "row_count": summary["row_count"], "accepted_no_hit_context_count": summary["accepted_no_hit_context_count"], "packet_context_gap_reduced_count": summary["packet_context_gap_reduced_count"], "checklist_pass_count": summary["checklist_pass_count"], "remaining_blocked_count": summary["remaining_blocked_count"], "approval_applied": summary["approval_applied"], "report_path": summary["report_path"], "next_manual_action": next_action, "status_frame": frame, "summary_frame": pd.DataFrame([summary]), "artifact_paths": {"artifact_dir": artifact_dir, "report": report, "metadata": metadata}}


def _int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _string(value).lower() in {"1", "true", "yes", "y"}


def _string(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()
