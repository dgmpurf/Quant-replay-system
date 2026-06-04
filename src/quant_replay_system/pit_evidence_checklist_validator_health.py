"""Health checks for PIT evidence checklist validator artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.pit_evidence_checklist_validator import VALIDATION_COLUMNS, SUMMARY_COLUMNS
from quant_replay_system.pit_evidence_checklist_validator_index import scan_pit_evidence_checklist_validator_artifacts


def check_pit_evidence_checklist_validator_health(
    *,
    root: str | Path = "outputs/reports/pit_evidence_checklist_validator",
    output_dir: str | Path = "outputs/reports/pit_evidence_checklist_validator/health",
    index_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    index = index_df.copy() if index_df is not None else scan_pit_evidence_checklist_validator_artifacts(root)
    issues: list[dict[str, Any]] = []
    for row in index.to_dict("records"):
        validator_id = _string(row.get("validator_id"))
        for path_field, required in [
            ("metadata_path", None),
            ("report_path", None),
            ("validation_csv_path", VALIDATION_COLUMNS),
            ("summary_csv_path", SUMMARY_COLUMNS),
            ("missing_evidence_matrix_path", None),
            ("approval_candidate_preview_path", None),
        ]:
            path = Path(_string(row.get(path_field)))
            if not path.exists():
                issues.append(_issue(validator_id, path_field, path, "ERROR", f"MISSING_{path_field.upper()}", f"{path_field} is missing."))
                continue
            if required:
                try:
                    frame = pd.read_csv(path, keep_default_na=False)
                except Exception as exc:
                    issues.append(_issue(validator_id, path_field, path, "ERROR", f"UNREADABLE_{path_field.upper()}", str(exc)))
                    continue
                missing = [column for column in required if column not in frame.columns]
                if missing:
                    issues.append(_issue(validator_id, path_field, path, "ERROR", "MISSING_REQUIRED_COLUMNS", ", ".join(missing)))
        for field, code in [
            ("no_approval_applied", "APPROVAL_APPLIED_DETECTED"),
            ("no_universe_export", "UNIVERSE_EXPORT_DETECTED"),
            ("no_data_raw_write", "DATA_RAW_WRITE_DETECTED"),
            ("no_data_processed_write", "DATA_PROCESSED_WRITE_DETECTED"),
            ("no_current_candidates_generated", "CURRENT_CANDIDATES_GENERATED"),
            ("no_snapshot_built", "SNAPSHOT_BUILT"),
            ("no_forward_labels", "FORWARD_LABELS_COMPUTED"),
            ("no_live_trading", "LIVE_TRADING_DETECTED"),
            ("no_broker_api", "BROKER_DETECTED"),
            ("no_order_placement", "ORDER_PLACEMENT_DETECTED"),
            ("no_message_sent", "MESSAGE_DELIVERY_DETECTED"),
            ("checklist_validation_only", "VALIDATION_ONLY_FLAG_MISSING"),
        ]:
            if not _bool(row.get(field)):
                issues.append(_issue(validator_id, "metadata_path", row.get("metadata_path"), "ERROR", code, f"{field} must remain true."))
    issue_frame = pd.DataFrame(issues, columns=["validator_id", "path_field", "path_value", "severity", "issue_code", "issue_message"])
    error_count = int((issue_frame["severity"] == "ERROR").sum()) if not issue_frame.empty else 0
    warning_count = int((issue_frame["severity"] == "WARN").sum()) if not issue_frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    output_dir = Path(output_dir)
    health_id = f"health_{abs(hash(tuple(index.get('validator_id', [])))):x}"[:16]
    artifact_dir = output_dir / health_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    issues_path = artifact_dir / "pit_evidence_checklist_validator_health_issues.csv"
    summary_path = artifact_dir / "pit_evidence_checklist_validator_health_summary.csv"
    report_path = artifact_dir / "pit_evidence_checklist_validator_health_report.md"
    metadata_path = artifact_dir / "metadata.json"
    summary = pd.DataFrame([{"status": status, "checked_artifact_count": len(index), "issue_count": len(issue_frame), "error_count": error_count, "warning_count": warning_count}])
    issue_frame.to_csv(issues_path, index=False)
    summary.to_csv(summary_path, index=False)
    metadata = {"health_check_id": health_id, "status": status, "checked_artifact_count": len(index), "issue_count": len(issue_frame), "error_count": error_count, "warning_count": warning_count, "output_files": {"issues": str(issues_path), "summary": str(summary_path), "report": str(report_path), "metadata": str(metadata_path)}, "approval_applied": False, "universe_exported": False}
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(f"# PIT Evidence Checklist Validator Health\n\nstatus: {status}\nissue_count: {len(issue_frame)}\n", encoding="utf-8")
    return {"status": status, "checked_artifact_count": len(index), "issue_count": len(issue_frame), "error_count": error_count, "warning_count": warning_count, "health_frame": issue_frame, "summary_frame": summary, "artifact_paths": {"artifact_dir": artifact_dir, "report": report_path, "metadata": metadata_path}, "health_check_id": health_id}


def _issue(validator_id: str, path_field: str, path_value: Any, severity: str, issue_code: str, message: str) -> dict[str, Any]:
    return {"validator_id": validator_id, "path_field": path_field, "path_value": str(path_value), "severity": severity, "issue_code": issue_code, "issue_message": message}


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
