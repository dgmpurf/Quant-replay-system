"""Status view for PIT evidence policy profile comparison artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.pit_evidence_policy_profile_comparison_health import (
    check_pit_evidence_policy_profile_comparison_health,
)
from quant_replay_system.pit_evidence_policy_profile_comparison_index import (
    scan_pit_evidence_policy_profile_comparison_artifacts,
)


NO_STAGE = "NO_PIT_EVIDENCE_POLICY_PROFILE_COMPARISONS"
READY_STAGE = "PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_READY"
ALL_BLOCKED_STAGE = "PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_ALL_BLOCKED"
PREVIEW_STAGE = "PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_HAS_CANDIDATE_PREVIEWS"
FAILED_STAGE = "PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_FAILED"


def run_pit_evidence_policy_profile_comparison_status(
    *,
    root: str | Path = "outputs/reports/pit_evidence_policy_profile_comparison",
    output_dir: str | Path = "outputs/reports/pit_evidence_policy_profile_comparison/status",
) -> dict[str, Any]:
    index = scan_pit_evidence_policy_profile_comparison_artifacts(root)
    health = check_pit_evidence_policy_profile_comparison_health(root=root, output_dir=Path(output_dir) / "_health_probe", index_df=index)
    latest = index.iloc[0].to_dict() if not index.empty else {}
    if index.empty:
        status = "WARN"
        stage = NO_STAGE
        next_action = "Run pit-evidence-policy-profile-comparison to compare strict and EOD post-close evidence policy assumptions."
    elif health["status"] == "FAIL":
        status = "FAIL"
        stage = FAILED_STAGE
        next_action = "Repair policy profile comparison artifacts before using them as research-status context."
    elif _int(latest.get("eod_low_budget_checklist_pass_count")) > 0:
        status = "PASS"
        stage = PREVIEW_STAGE
        next_action = "Review EOD low-budget approval-candidate previews manually; no approval has been applied."
    elif _int(latest.get("remaining_blocked_count")) > 0:
        status = "WARN"
        stage = ALL_BLOCKED_STAGE
        next_action = "Rows remain blocked under EOD low-budget policy; close non-relaxed PIT evidence gaps before approval review."
    else:
        status = "PASS"
        stage = READY_STAGE
        next_action = "Review comparison results manually; this status is policy context only."
    comparison_id = _string(latest.get("comparison_id")) or "none"
    output_dir = Path(output_dir)
    artifact_dir = output_dir / comparison_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "latest_comparison_id": _string(latest.get("comparison_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health["status"],
        "profile_name": _string(latest.get("profile_name")),
        "row_count": _int(latest.get("row_count")),
        "strict_checklist_pass_count": _int(latest.get("strict_checklist_pass_count")),
        "eod_low_budget_checklist_pass_count": _int(latest.get("eod_low_budget_checklist_pass_count")),
        "relaxed_blocker_count": _int(latest.get("relaxed_blocker_count")),
        "remaining_blocked_count": _int(latest.get("remaining_blocked_count")),
        "report_path": _string(latest.get("report_path")),
        "next_manual_action": next_action,
    }
    frame = pd.DataFrame(
        [
            {
                "component": "PIT_EVIDENCE_POLICY_PROFILE_COMPARISON",
                "status": status,
                "latest_artifact_id": summary["latest_comparison_id"],
                "report_path": summary["report_path"],
                "row_count": summary["row_count"],
                "strict_checklist_pass_count": summary["strict_checklist_pass_count"],
                "eod_low_budget_checklist_pass_count": summary["eod_low_budget_checklist_pass_count"],
                "remaining_blocked_count": summary["remaining_blocked_count"],
                "next_action": next_action,
            }
        ]
    )
    status_csv = artifact_dir / "pit_evidence_policy_profile_comparison_status.csv"
    summary_csv = artifact_dir / "pit_evidence_policy_profile_comparison_status_summary.csv"
    report = artifact_dir / "pit_evidence_policy_profile_comparison_status_report.md"
    metadata = artifact_dir / "metadata.json"
    frame.to_csv(status_csv, index=False)
    pd.DataFrame([summary]).to_csv(summary_csv, index=False)
    metadata.write_text(json.dumps({"status_id": comparison_id, **summary, "approval_applied": False, "universe_exported": False}, indent=2, sort_keys=True), encoding="utf-8")
    report.write_text(f"# PIT Evidence Policy Profile Comparison Status\n\nstatus: {status}\nworkflow_stage: {stage}\nnext_manual_action: {next_action}\n", encoding="utf-8")
    return {"status": status, "workflow_stage": stage, "latest_comparison_id": summary["latest_comparison_id"], "health_status": health["status"], "profile_name": summary["profile_name"], "row_count": summary["row_count"], "strict_checklist_pass_count": summary["strict_checklist_pass_count"], "eod_low_budget_checklist_pass_count": summary["eod_low_budget_checklist_pass_count"], "relaxed_blocker_count": summary["relaxed_blocker_count"], "remaining_blocked_count": summary["remaining_blocked_count"], "report_path": summary["report_path"], "next_manual_action": next_action, "status_frame": frame, "summary_frame": pd.DataFrame([summary]), "artifact_paths": {"artifact_dir": artifact_dir, "report": report, "metadata": metadata}}


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
