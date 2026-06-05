"""Status view for PIT official status evidence packet enrichment artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.pit_official_status_evidence_packet_enrichment_health import (
    check_pit_official_status_evidence_packet_enrichment_health,
)
from quant_replay_system.pit_official_status_evidence_packet_enrichment_index import (
    scan_pit_official_status_evidence_packet_enrichment_artifacts,
)


NO_STAGE = "NO_PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_ENRICHMENT"
READY_STAGE = "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_ENRICHMENT_READY_FOR_REVIEW"
BLOCKED_STAGE = "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_ENRICHMENT_BLOCKED"
HEALTH_WARN_STAGE = "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_ENRICHMENT_HEALTH_WARN"
FAILED_STAGE = "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_ENRICHMENT_FAILED"


def run_pit_official_status_evidence_packet_enrichment_status(
    *,
    root: str | Path = "outputs/reports/pit_official_status_evidence_packet_enrichment",
    output_dir: str | Path = "outputs/reports/pit_official_status_evidence_packet_enrichment/status",
) -> dict[str, Any]:
    index = scan_pit_official_status_evidence_packet_enrichment_artifacts(root)
    health = check_pit_official_status_evidence_packet_enrichment_health(root=root, output_dir=Path(output_dir) / "_health_probe", index_df=index)
    latest = index.iloc[0].to_dict() if not index.empty else {}
    if index.empty:
        status = "WARN"
        stage = NO_STAGE
        next_action = "Run pit-official-status-evidence-packet-enrichment to merge quotation and reviewed no-hit context."
    elif health["status"] == "FAIL":
        status = "FAIL"
        stage = FAILED_STAGE
        next_action = "Repair enrichment artifacts before using them as research-status context."
    elif health["status"] == "WARN":
        status = "WARN"
        stage = HEALTH_WARN_STAGE
        next_action = "Review enrichment health warnings before evidence review."
    elif _int(latest.get("remaining_blocked_count")) > 0:
        status = "WARN"
        stage = BLOCKED_STAGE
        next_action = "Rows remain blocked; reviewed no-hit support still needs manual acceptance, complete metadata, and survivorship rationale."
    else:
        status = "PASS"
        stage = READY_STAGE
        next_action = "Review enriched evidence manually; no approval or universe export has been applied."
    enrichment_id = _string(latest.get("enrichment_id")) or "none"
    output_dir = Path(output_dir)
    artifact_dir = output_dir / enrichment_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "latest_enrichment_id": _string(latest.get("enrichment_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health["status"],
        "source_packet_id": _string(latest.get("source_packet_id")),
        "policy_comparison_id": _string(latest.get("policy_comparison_id")),
        "row_count": _int(latest.get("row_count")),
        "strong_official_date_specific_quotation_count": _int(latest.get("strong_official_date_specific_quotation_count")),
        "reviewed_no_hit_context_supported_count": _int(latest.get("reviewed_no_hit_context_supported_count")),
        "reviewer_acceptance_required_count": _int(latest.get("reviewer_acceptance_required_count")),
        "prior_official_symbol_level_context_count": _int(latest.get("prior_official_symbol_level_context_count")),
        "local_eod_cache_context_count": _int(latest.get("local_eod_cache_context_count")),
        "checklist_pass_count": _int(latest.get("checklist_pass_count")),
        "remaining_blocked_count": _int(latest.get("remaining_blocked_count")),
        "report_path": _string(latest.get("report_path")),
        "next_manual_action": next_action,
    }
    frame = pd.DataFrame(
        [
            {
                "component": "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_ENRICHMENT_STATUS",
                "status": status,
                "latest_artifact_id": summary["latest_enrichment_id"],
                "report_path": summary["report_path"],
                "row_count": summary["row_count"],
                "remaining_blocked_count": summary["remaining_blocked_count"],
                "checklist_pass_count": summary["checklist_pass_count"],
                "next_action": next_action,
            }
        ]
    )
    status_csv = artifact_dir / "pit_official_status_evidence_packet_enrichment_status.csv"
    summary_csv = artifact_dir / "pit_official_status_evidence_packet_enrichment_status_summary.csv"
    report = artifact_dir / "pit_official_status_evidence_packet_enrichment_status_report.md"
    metadata = artifact_dir / "metadata.json"
    frame.to_csv(status_csv, index=False)
    pd.DataFrame([summary]).to_csv(summary_csv, index=False)
    metadata.write_text(json.dumps({"status_id": enrichment_id, **summary, "approval_applied": False, "universe_exported": False, "no_current_candidates_generated": True}, indent=2, sort_keys=True), encoding="utf-8")
    report.write_text(f"# PIT Official Status Evidence Packet Enrichment Status\n\nstatus: {status}\nworkflow_stage: {stage}\nnext_manual_action: {next_action}\n", encoding="utf-8")
    return {"status": status, "workflow_stage": stage, "latest_enrichment_id": summary["latest_enrichment_id"], "health_status": health["status"], "source_packet_id": summary["source_packet_id"], "policy_comparison_id": summary["policy_comparison_id"], "row_count": summary["row_count"], "strong_official_date_specific_quotation_count": summary["strong_official_date_specific_quotation_count"], "reviewed_no_hit_context_supported_count": summary["reviewed_no_hit_context_supported_count"], "reviewer_acceptance_required_count": summary["reviewer_acceptance_required_count"], "prior_official_symbol_level_context_count": summary["prior_official_symbol_level_context_count"], "local_eod_cache_context_count": summary["local_eod_cache_context_count"], "checklist_pass_count": summary["checklist_pass_count"], "remaining_blocked_count": summary["remaining_blocked_count"], "report_path": summary["report_path"], "next_manual_action": next_action, "status_frame": frame, "summary_frame": pd.DataFrame([summary]), "artifact_paths": {"artifact_dir": artifact_dir, "report": report, "metadata": metadata}}


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
