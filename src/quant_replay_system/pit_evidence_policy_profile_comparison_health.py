"""Health checks for PIT evidence policy profile comparison artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.pit_evidence_policy_profile_comparison import COMPARISON_COLUMNS, SUMMARY_COLUMNS
from quant_replay_system.pit_evidence_policy_profile_comparison_index import (
    scan_pit_evidence_policy_profile_comparison_artifacts,
)


def check_pit_evidence_policy_profile_comparison_health(
    *,
    root: str | Path = "outputs/reports/pit_evidence_policy_profile_comparison",
    output_dir: str | Path = "outputs/reports/pit_evidence_policy_profile_comparison/health",
    index_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    index = index_df.copy() if index_df is not None else scan_pit_evidence_policy_profile_comparison_artifacts(root)
    issues: list[dict[str, Any]] = []
    for row in index.to_dict("records"):
        comparison_id = _string(row.get("comparison_id"))
        for field, required_columns in [
            ("metadata_path", None),
            ("report_path", None),
            ("comparison_csv_path", COMPARISON_COLUMNS),
            ("summary_csv_path", SUMMARY_COLUMNS),
        ]:
            path = Path(_string(row.get(field)))
            if not path.exists():
                issues.append(_issue(comparison_id, field, path, "ERROR", f"MISSING_{field.upper()}", f"{field} is missing."))
                continue
            if required_columns:
                try:
                    frame = pd.read_csv(path, keep_default_na=False)
                except Exception as exc:
                    issues.append(_issue(comparison_id, field, path, "ERROR", f"UNREADABLE_{field.upper()}", str(exc)))
                    continue
                missing = [column for column in required_columns if column not in frame.columns]
                if missing:
                    issues.append(_issue(comparison_id, field, path, "ERROR", "MISSING_REQUIRED_COLUMNS", ", ".join(missing)))
                if field == "comparison_csv_path" and "should_apply_approval" in frame.columns and frame["should_apply_approval"].map(_bool).any():
                    issues.append(_issue(comparison_id, field, path, "ERROR", "APPROVAL_UPDATE_CREATED", "comparison must not request approval."))
        checks = [
            ("profile_is_opt_in", True, "PROFILE_NOT_OPT_IN"),
            ("strict_default_unchanged", True, "STRICT_DEFAULT_MODIFIED"),
            ("approval_applied", False, "APPROVAL_APPLIED_DETECTED"),
            ("pit_review_run", False, "PIT_REVIEW_RUN_DETECTED"),
            ("export_readiness_run", False, "EXPORT_READINESS_RUN_DETECTED"),
            ("export_staging_run", False, "STAGING_RUN_DETECTED"),
            ("universe_exported", False, "UNIVERSE_EXPORT_DETECTED"),
            ("active_worklist_mutated", False, "ACTIVE_ARTIFACT_MUTATION_DETECTED"),
            ("no_data_raw_write", True, "DATA_RAW_WRITE_DETECTED"),
            ("no_data_processed_write", True, "DATA_PROCESSED_WRITE_DETECTED"),
            ("no_current_candidates_generated", True, "CURRENT_CANDIDATES_GENERATED"),
            ("comparison_only", True, "COMPARISON_ONLY_FLAG_MISSING"),
        ]
        for field, expected, code in checks:
            value = _bool(row.get(field))
            if value != expected:
                issues.append(_issue(comparison_id, "metadata_path", row.get("metadata_path"), "ERROR", code, f"{field} expected {expected}."))
    issue_frame = pd.DataFrame(issues, columns=["comparison_id", "path_field", "path_value", "severity", "issue_code", "issue_message"])
    error_count = int((issue_frame["severity"] == "ERROR").sum()) if not issue_frame.empty else 0
    warning_count = int((issue_frame["severity"] == "WARN").sum()) if not issue_frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    output_dir = Path(output_dir)
    health_id = f"health_{abs(hash(tuple(index.get('comparison_id', [])))):x}"[:16]
    artifact_dir = output_dir / health_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    issues_path = artifact_dir / "pit_evidence_policy_profile_comparison_health_issues.csv"
    summary_path = artifact_dir / "pit_evidence_policy_profile_comparison_health_summary.csv"
    report = artifact_dir / "pit_evidence_policy_profile_comparison_health_report.md"
    metadata = artifact_dir / "metadata.json"
    summary = pd.DataFrame([{"status": status, "checked_artifact_count": len(index), "issue_count": len(issue_frame), "error_count": error_count, "warning_count": warning_count}])
    issue_frame.to_csv(issues_path, index=False)
    summary.to_csv(summary_path, index=False)
    metadata.write_text(json.dumps({"health_check_id": health_id, "status": status, "issue_count": len(issue_frame), "error_count": error_count, "warning_count": warning_count}, indent=2, sort_keys=True), encoding="utf-8")
    report.write_text(f"# PIT Evidence Policy Profile Comparison Health\n\nstatus: {status}\nissue_count: {len(issue_frame)}\n", encoding="utf-8")
    return {"status": status, "checked_artifact_count": len(index), "issue_count": len(issue_frame), "error_count": error_count, "warning_count": warning_count, "health_frame": issue_frame, "summary_frame": summary, "artifact_paths": {"artifact_dir": artifact_dir, "report": report, "metadata": metadata}, "health_check_id": health_id}


def _issue(comparison_id: str, path_field: str, path_value: Any, severity: str, issue_code: str, message: str) -> dict[str, Any]:
    return {"comparison_id": comparison_id, "path_field": path_field, "path_value": str(path_value), "severity": severity, "issue_code": issue_code, "issue_message": message}


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
