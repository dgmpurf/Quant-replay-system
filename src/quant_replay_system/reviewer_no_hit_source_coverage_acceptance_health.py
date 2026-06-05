"""Health checks for reviewer no-hit source coverage acceptance artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.reviewer_no_hit_source_coverage_acceptance import (
    ACCEPTANCE_COLUMNS,
    SUMMARY_COLUMNS,
    TEMPLATE_COLUMNS,
)
from quant_replay_system.reviewer_no_hit_source_coverage_acceptance_index import (
    scan_reviewer_no_hit_source_coverage_acceptance_artifacts,
)


def check_reviewer_no_hit_source_coverage_acceptance_health(
    *,
    root: str | Path = "outputs/reports/reviewer_no_hit_source_coverage_acceptance",
    output_dir: str | Path = "outputs/reports/reviewer_no_hit_source_coverage_acceptance/health",
    index_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    index = index_df.copy() if index_df is not None else scan_reviewer_no_hit_source_coverage_acceptance_artifacts(root)
    issues: list[dict[str, Any]] = []
    for row in index.to_dict("records"):
        acceptance_id = _string(row.get("acceptance_id"))
        for field, required in [
            ("metadata_path", None),
            ("report_path", None),
            ("acceptance_csv_path", ACCEPTANCE_COLUMNS),
            ("template_csv_path", TEMPLATE_COLUMNS),
            ("summary_csv_path", SUMMARY_COLUMNS),
        ]:
            path = Path(_string(row.get(field)))
            if not path.exists():
                issues.append(_issue(acceptance_id, field, path, "ERROR", f"MISSING_{field.upper()}", f"{field} is missing."))
                continue
            if required:
                try:
                    frame = pd.read_csv(path, keep_default_na=False)
                except Exception as exc:
                    issues.append(_issue(acceptance_id, field, path, "ERROR", f"UNREADABLE_{field.upper()}", str(exc)))
                    continue
                missing = [column for column in required if column not in frame.columns]
                if missing:
                    issues.append(_issue(acceptance_id, field, path, "ERROR", "MISSING_REQUIRED_COLUMNS", ", ".join(missing)))
                if field == "acceptance_csv_path":
                    if "checklist_pass_candidate" in frame.columns and frame["checklist_pass_candidate"].map(_bool).any():
                        issues.append(_issue(acceptance_id, field, path, "ERROR", "CHECKLIST_PASS_CREATED", "acceptance must not create checklist-pass rows."))
                    if frame.astype(str).apply(lambda series: series.str.contains("APPROVED_FOR_PIT_UNIVERSE", na=False)).any().any():
                        issues.append(_issue(acceptance_id, field, path, "ERROR", "APPROVED_FOR_PIT_UNIVERSE_DETECTED", "acceptance must not create approval rows."))
                    accepted = frame.loc[frame.get("acceptance_status", pd.Series(dtype=str)).astype(str).str.upper() == "ACCEPTED_AS_SUPPORTING_CONTEXT"]
                    if not accepted.empty:
                        missing_reviewer = accepted[
                            accepted[["accepted_by", "accepted_at", "acceptance_reason", "evidence_reference"]]
                            .astype(str)
                            .apply(lambda series: series.str.strip() == "")
                            .any(axis=1)
                        ]
                        if not missing_reviewer.empty:
                            issues.append(_issue(acceptance_id, field, path, "ERROR", "ACCEPTED_ROW_MISSING_REVIEWER_FIELDS", "accepted rows require reviewer/evidence fields."))
                        survivorship = accepted.loc[accepted["exception_type"].astype(str) == "SURVIVORSHIP_RATIONALE"]
                        if not survivorship.empty and (survivorship["survivorship_rationale"].astype(str).str.strip() == "").any():
                            issues.append(_issue(acceptance_id, field, path, "ERROR", "SURVIVORSHIP_ACCEPTANCE_MISSING_RATIONALE", "survivorship acceptance requires rationale."))
        checks = [
            ("approval_applied", False, "APPROVAL_APPLIED_DETECTED"),
            ("pit_review_run", False, "PIT_REVIEW_RUN_DETECTED"),
            ("export_readiness_run", False, "EXPORT_READINESS_RUN_DETECTED"),
            ("export_staging_run", False, "STAGING_RUN_DETECTED"),
            ("universe_exported", False, "UNIVERSE_EXPORT_DETECTED"),
            ("active_worklist_mutated", False, "ACTIVE_ARTIFACT_MUTATION_DETECTED"),
            ("no_clean_review_updates_created", True, "CLEAN_REVIEW_UPDATES_CREATED"),
            ("no_data_raw_write", True, "DATA_RAW_WRITE_DETECTED"),
            ("no_data_processed_write", True, "DATA_PROCESSED_WRITE_DETECTED"),
            ("no_current_candidates_generated", True, "CURRENT_CANDIDATES_GENERATED"),
            ("no_snapshot_built", True, "SNAPSHOT_BUILT_DETECTED"),
            ("no_forward_labels", True, "FORWARD_LABELS_DETECTED"),
            ("cache_mutated", False, "CACHE_MUTATION_DETECTED"),
            ("acceptance_only", True, "ACCEPTANCE_ONLY_FLAG_MISSING"),
        ]
        for field, expected, code in checks:
            if _bool(row.get(field)) != expected:
                issues.append(_issue(acceptance_id, "metadata_path", row.get("metadata_path"), "ERROR", code, f"{field} expected {expected}."))
    issue_frame = pd.DataFrame(issues, columns=["acceptance_id", "path_field", "path_value", "severity", "issue_code", "issue_message"])
    error_count = int((issue_frame["severity"] == "ERROR").sum()) if not issue_frame.empty else 0
    warning_count = int((issue_frame["severity"] == "WARN").sum()) if not issue_frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    output_dir = Path(output_dir)
    health_id = f"health_{abs(hash(tuple(index.get('acceptance_id', [])))):x}"[:16]
    artifact_dir = output_dir / health_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    issues_path = artifact_dir / "reviewer_no_hit_source_coverage_acceptance_health_issues.csv"
    summary_path = artifact_dir / "reviewer_no_hit_source_coverage_acceptance_health_summary.csv"
    report = artifact_dir / "reviewer_no_hit_source_coverage_acceptance_health_report.md"
    metadata = artifact_dir / "metadata.json"
    summary = pd.DataFrame([{"status": status, "checked_artifact_count": len(index), "issue_count": len(issue_frame), "error_count": error_count, "warning_count": warning_count}])
    issue_frame.to_csv(issues_path, index=False)
    summary.to_csv(summary_path, index=False)
    metadata.write_text(json.dumps({"health_check_id": health_id, "status": status, "issue_count": len(issue_frame), "error_count": error_count, "warning_count": warning_count}, indent=2, sort_keys=True), encoding="utf-8")
    report.write_text(f"# Reviewer No-Hit Source Coverage Acceptance Health\n\nstatus: {status}\nissue_count: {len(issue_frame)}\n", encoding="utf-8")
    return {"status": status, "checked_artifact_count": len(index), "issue_count": len(issue_frame), "error_count": error_count, "warning_count": warning_count, "health_frame": issue_frame, "summary_frame": summary, "artifact_paths": {"artifact_dir": artifact_dir, "report": report, "metadata": metadata}, "health_check_id": health_id}


def _issue(acceptance_id: str, path_field: str, path_value: Any, severity: str, issue_code: str, message: str) -> dict[str, Any]:
    return {"acceptance_id": acceptance_id, "path_field": path_field, "path_value": str(path_value), "severity": severity, "issue_code": issue_code, "issue_message": message}


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
