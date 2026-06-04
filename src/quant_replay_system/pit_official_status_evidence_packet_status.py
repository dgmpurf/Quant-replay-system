"""Status view for PIT official status evidence packet artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.pit_official_status_evidence_packet_health import (
    check_pit_official_status_evidence_packet_health,
)
from quant_replay_system.pit_official_status_evidence_packet_index import (
    scan_pit_official_status_evidence_packet_artifacts,
)


NO_STAGE = "NO_PIT_OFFICIAL_STATUS_EVIDENCE_PACKETS"
READY_STAGE = "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_READY_FOR_REVIEW"
BLOCKED_STAGE = "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_BLOCKED"
HEALTH_WARN_STAGE = "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_HEALTH_WARN"
FAILED_STAGE = "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_FAILED"


def run_pit_official_status_evidence_packet_status(
    *,
    root: str | Path = "outputs/reports/pit_official_status_evidence_packet",
    output_dir: str | Path = "outputs/reports/pit_official_status_evidence_packet/status",
) -> dict[str, Any]:
    index = scan_pit_official_status_evidence_packet_artifacts(root)
    health = check_pit_official_status_evidence_packet_health(root=root, output_dir=Path(output_dir) / "_health_probe", index_df=index)
    latest = index.iloc[0].to_dict() if not index.empty else {}
    if index.empty:
        status = "WARN"
        stage = NO_STAGE
        next_action = "Run pit-official-status-evidence-packet to consolidate official/status evidence context."
    elif health["status"] == "FAIL":
        status = "FAIL"
        stage = FAILED_STAGE
        next_action = "Repair PIT official status evidence packet artifacts before using them as research-status context."
    elif health["status"] == "WARN":
        status = "WARN"
        stage = HEALTH_WARN_STAGE
        next_action = "Review PIT official status evidence packet health warnings before evidence review."
    elif _int(latest.get("blocked_count")) > 0:
        status = "WARN"
        stage = BLOCKED_STAGE
        next_action = "Rows remain blocked; acquire official date-specific not-delisted/ST/suspension/survivorship evidence before approval review."
    else:
        status = "PASS"
        stage = READY_STAGE
        next_action = "Review evidence packet manually; no approval or universe export has been applied."
    packet_id = _string(latest.get("packet_id")) or "none"
    output_dir = Path(output_dir)
    artifact_dir = output_dir / packet_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "latest_packet_id": _string(latest.get("packet_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health["status"],
        "row_count": _int(latest.get("row_count")),
        "evidence_packet_row_count": _int(latest.get("evidence_packet_row_count")),
        "strong_official_date_specific_count": _int(latest.get("strong_official_date_specific_count")),
        "supporting_official_symbol_level_count": _int(latest.get("supporting_official_symbol_level_count")),
        "supporting_local_eod_cache_count": _int(latest.get("supporting_local_eod_cache_count")),
        "context_only_count": _int(latest.get("context_only_count")),
        "missing_count": _int(latest.get("missing_count")),
        "checklist_pass_count": _int(latest.get("checklist_pass_count")),
        "blocked_count": _int(latest.get("blocked_count")),
        "eod_low_budget_checklist_pass_count": _int(latest.get("eod_low_budget_checklist_pass_count")),
        "report_path": _string(latest.get("report_path")),
        "next_manual_action": next_action,
    }
    frame = pd.DataFrame(
        [
            {
                "component": "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_STATUS",
                "status": status,
                "latest_artifact_id": summary["latest_packet_id"],
                "report_path": summary["report_path"],
                "row_count": summary["row_count"],
                "blocked_count": summary["blocked_count"],
                "checklist_pass_count": summary["checklist_pass_count"],
                "next_action": next_action,
            }
        ]
    )
    status_csv = artifact_dir / "pit_official_status_evidence_packet_status.csv"
    summary_csv = artifact_dir / "pit_official_status_evidence_packet_status_summary.csv"
    report = artifact_dir / "pit_official_status_evidence_packet_status_report.md"
    metadata = artifact_dir / "metadata.json"
    frame.to_csv(status_csv, index=False)
    pd.DataFrame([summary]).to_csv(summary_csv, index=False)
    metadata.write_text(
        json.dumps(
            {
                "status_id": packet_id,
                **summary,
                "approval_applied": False,
                "pit_review_run": False,
                "universe_exported": False,
                "no_current_candidates_generated": True,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    report.write_text(f"# PIT Official Status Evidence Packet Status\n\nstatus: {status}\nworkflow_stage: {stage}\nnext_manual_action: {next_action}\n", encoding="utf-8")
    return {
        "status": status,
        "workflow_stage": stage,
        "latest_packet_id": summary["latest_packet_id"],
        "health_status": health["status"],
        "row_count": summary["row_count"],
        "evidence_packet_row_count": summary["evidence_packet_row_count"],
        "strong_official_date_specific_count": summary["strong_official_date_specific_count"],
        "supporting_official_symbol_level_count": summary["supporting_official_symbol_level_count"],
        "supporting_local_eod_cache_count": summary["supporting_local_eod_cache_count"],
        "context_only_count": summary["context_only_count"],
        "missing_count": summary["missing_count"],
        "checklist_pass_count": summary["checklist_pass_count"],
        "blocked_count": summary["blocked_count"],
        "eod_low_budget_checklist_pass_count": summary["eod_low_budget_checklist_pass_count"],
        "report_path": summary["report_path"],
        "next_manual_action": next_action,
        "status_frame": frame,
        "summary_frame": pd.DataFrame([summary]),
        "artifact_paths": {"artifact_dir": artifact_dir, "report": report, "metadata": metadata},
    }


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
