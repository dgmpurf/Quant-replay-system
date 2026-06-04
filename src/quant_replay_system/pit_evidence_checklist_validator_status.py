"""Status view for PIT evidence checklist validator artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.pit_evidence_checklist_validator_health import check_pit_evidence_checklist_validator_health
from quant_replay_system.pit_evidence_checklist_validator_index import scan_pit_evidence_checklist_validator_artifacts


NO_STAGE = "NO_PIT_EVIDENCE_CHECKLIST_VALIDATION"
BLOCKED_STAGE = "PIT_EVIDENCE_CHECKLIST_VALIDATION_BLOCKED"
PASS_STAGE = "PIT_EVIDENCE_CHECKLIST_VALIDATION_HAS_APPROVAL_CANDIDATES"
HEALTH_WARN_STAGE = "PIT_EVIDENCE_CHECKLIST_VALIDATION_HEALTH_WARN"
FAILED_STAGE = "PIT_EVIDENCE_CHECKLIST_VALIDATION_FAILED"


def run_pit_evidence_checklist_validator_status(
    *,
    root: str | Path = "outputs/reports/pit_evidence_checklist_validator",
    output_dir: str | Path = "outputs/reports/pit_evidence_checklist_validator/status",
) -> dict[str, Any]:
    index = scan_pit_evidence_checklist_validator_artifacts(root)
    health = check_pit_evidence_checklist_validator_health(root=root, output_dir=Path(output_dir) / "_health_probe", index_df=index)
    latest = index.iloc[0].to_dict() if not index.empty else {}
    if index.empty:
        status = "WARN"
        stage = NO_STAGE
        next_action = "Run pit-evidence-checklist-validator against completed or draft PIT evidence updates."
    elif health["status"] == "FAIL":
        status = "FAIL"
        stage = FAILED_STAGE
        next_action = "Repair PIT evidence checklist validator artifacts before using them as evidence-gate context."
    elif health["status"] == "WARN":
        status = "WARN"
        stage = HEALTH_WARN_STAGE
        next_action = "Review checklist validator health warnings."
    elif _int(latest.get("checklist_pass_count")) > 0:
        status = "PASS"
        stage = PASS_STAGE
        next_action = "Review approval candidate preview manually; no PIT approval has been applied."
    else:
        status = "WARN"
        stage = BLOCKED_STAGE
        next_action = "Close missing active/not-delisted, PIT timing, ST/no-ST, and survivorship evidence before approval candidates."
    status_id = _string(latest.get("validator_id")) or "none"
    output_dir = Path(output_dir)
    artifact_dir = output_dir / status_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "latest_validator_id": _string(latest.get("validator_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health["status"],
        "row_count": _int(latest.get("row_count")),
        "checklist_pass_count": _int(latest.get("checklist_pass_count")),
        "blocked_count": _int(latest.get("blocked_count")),
        "stock_core_blocked_count": _int(latest.get("stock_core_blocked_count")),
        "etf_core_blocked_count": _int(latest.get("etf_core_blocked_count")),
        "report_path": _string(latest.get("report_path")),
        "next_manual_action": next_action,
    }
    frame = pd.DataFrame(
        [
            {
                "component": "PIT_EVIDENCE_CHECKLIST_VALIDATOR",
                "status": status,
                "latest_artifact_id": summary["latest_validator_id"],
                "report_path": summary["report_path"],
                "row_count": summary["row_count"],
                "checklist_pass_count": summary["checklist_pass_count"],
                "blocked_count": summary["blocked_count"],
                "next_action": next_action,
            }
        ]
    )
    status_csv = artifact_dir / "pit_evidence_checklist_validator_status.csv"
    summary_csv = artifact_dir / "pit_evidence_checklist_validator_status_summary.csv"
    report = artifact_dir / "pit_evidence_checklist_validator_status_report.md"
    metadata = artifact_dir / "metadata.json"
    frame.to_csv(status_csv, index=False)
    pd.DataFrame([summary]).to_csv(summary_csv, index=False)
    metadata.write_text(json.dumps({"status_id": status_id, **summary, "output_files": {"status_csv": str(status_csv), "summary_csv": str(summary_csv), "report": str(report), "metadata": str(metadata)}, "approval_applied": False, "universe_exported": False}, indent=2, sort_keys=True), encoding="utf-8")
    report.write_text(f"# PIT Evidence Checklist Validator Status\n\nstatus: {status}\nworkflow_stage: {stage}\nnext_manual_action: {next_action}\n", encoding="utf-8")
    return {"status": status, "workflow_stage": stage, "latest_validator_id": summary["latest_validator_id"], "health_status": health["status"], "row_count": summary["row_count"], "checklist_pass_count": summary["checklist_pass_count"], "blocked_count": summary["blocked_count"], "stock_core_blocked_count": summary["stock_core_blocked_count"], "etf_core_blocked_count": summary["etf_core_blocked_count"], "report_path": summary["report_path"], "next_manual_action": next_action, "status_frame": frame, "summary_frame": pd.DataFrame([summary]), "artifact_paths": {"artifact_dir": artifact_dir, "report": report, "metadata": metadata}}


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
