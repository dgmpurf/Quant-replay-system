"""Health checks for first-batch reviewer evidence completion plan artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns
from quant_replay_system.first_batch_reviewer_evidence_completion_plan import PLAN_COLUMNS
from quant_replay_system.first_batch_reviewer_evidence_completion_plan_index import (
    build_first_batch_reviewer_evidence_completion_plan_index,
)


HEALTH_COLUMNS = ["plan_id", "status", "severity", "issue_code", "message", "artifact_path"]


@dataclass(frozen=True)
class FirstBatchReviewerEvidenceCompletionPlanHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_first_batch_reviewer_evidence_completion_plan_health(
    *,
    root: str | Path = "outputs/reports/first_batch_reviewer_evidence_completion_plan",
    output_dir: str | Path = "outputs/reports/first_batch_reviewer_evidence_completion_plan/health",
) -> FirstBatchReviewerEvidenceCompletionPlanHealthResult:
    index = build_first_batch_reviewer_evidence_completion_plan_index(root=root)
    issues: list[dict[str, Any]] = []
    for row in index.index_frame.to_dict("records"):
        issues.extend(_issues_for_row(row))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    artifact_dir = Path(output_dir) / _hash_payload({"root": str(root), "issues": frame.to_dict("records")})
    paths = {
        "artifact_dir": artifact_dir,
        "health_csv": artifact_dir / "first_batch_reviewer_evidence_completion_plan_health.csv",
        "health_report": artifact_dir / "first_batch_reviewer_evidence_completion_plan_health_report.md",
        "metadata": artifact_dir / "metadata.json",
    }
    result = FirstBatchReviewerEvidenceCompletionPlanHealthResult(
        status=status,
        checked_artifact_count=len(index.index_frame),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=[],
        audit_metadata=_safe_audit_metadata(root, len(index.index_frame)),
    )
    _write(result)
    return result


def _issues_for_row(row: dict[str, Any]) -> list[dict[str, Any]]:
    plan_id = _text(row.get("plan_id"))
    metadata_path = Path(_text(row.get("metadata_path")))
    plan_csv_path = Path(_text(row.get("plan_csv_path")))
    report_path = Path(_text(row.get("report_path")))
    template_path = Path(_text(row.get("reviewer_completion_template_path")))
    issues: list[dict[str, Any]] = []
    for path, code in [
        (metadata_path, "MISSING_METADATA"),
        (plan_csv_path, "MISSING_PLAN_CSV"),
        (report_path, "MISSING_REPORT"),
        (template_path, "MISSING_REVIEWER_COMPLETION_TEMPLATE"),
    ]:
        if not _text(path) or not path.exists():
            issues.append(_issue(plan_id, "ERROR", code, f"Required artifact missing: {path}", path))
    if plan_csv_path.exists():
        frame = read_csv_preserve_symbol_columns(plan_csv_path, keep_default_na=False)
        missing = sorted(set(PLAN_COLUMNS) - set(frame.columns))
        if missing:
            issues.append(_issue(plan_id, "ERROR", "MISSING_REQUIRED_COLUMNS", ", ".join(missing), plan_csv_path))
        if "review_status" in frame and frame["review_status"].astype(str).isin(["APPROVED_FOR_PIT_UNIVERSE", "REJECTED"]).any():
            issues.append(_issue(plan_id, "ERROR", "APPROVAL_OR_REJECTION_DETECTED", "Completion planning rows must remain non-approved and non-rejected.", plan_csv_path))
        if "include_flag" in frame and frame["include_flag"].map(_to_bool).any():
            issues.append(_issue(plan_id, "ERROR", "INCLUDE_FLAG_TRUE_DETECTED", "Completion planning rows must keep include_flag=false.", plan_csv_path))
        if "valid_for_signal_date" in frame and frame["valid_for_signal_date"].map(_to_bool).any():
            issues.append(_issue(plan_id, "ERROR", "VALID_FOR_SIGNAL_DATE_DETECTED", "Completion planning rows must keep valid_for_signal_date=false.", plan_csv_path))
        if "approved_for_pit_universe_candidate" in frame and frame["approved_for_pit_universe_candidate"].map(_to_bool).any():
            issues.append(_issue(plan_id, "ERROR", "APPROVED_CANDIDATE_DETECTED", "Completion planning must not create approval candidates.", plan_csv_path))
    for field, code in {
        "clean_review_updates_created": "CLEAN_REVIEW_UPDATES_DETECTED",
        "approval_applied": "APPROVAL_APPLIED_DETECTED",
        "pit_review_run": "PIT_REVIEW_RUN_DETECTED",
        "export_readiness_run": "EXPORT_READINESS_RUN_DETECTED",
        "export_staging_run": "EXPORT_STAGING_RUN_DETECTED",
        "universe_exported": "UNIVERSE_EXPORT_DETECTED",
    }.items():
        if _to_bool(row.get(field)):
            issues.append(_issue(plan_id, "ERROR", code, f"Unsafe flag {field} is true.", metadata_path))
    for field, code in {
        "no_data_raw_write": "DATA_RAW_WRITE_DETECTED",
        "no_data_processed_write": "DATA_PROCESSED_WRITE_DETECTED",
        "no_current_candidates_generated": "CURRENT_CANDIDATES_GENERATED",
        "no_snapshot_built": "SNAPSHOT_BUILT",
        "no_forward_labels": "FORWARD_LABELS_COMPUTED",
        "completion_planning_only": "COMPLETION_PLANNING_ONLY_FLAG_MISSING",
    }.items():
        if not _to_bool(row.get(field)):
            issues.append(_issue(plan_id, "ERROR", code, f"Required safety flag {field} is not true.", metadata_path))
    if metadata_path.exists():
        artifact_dir = metadata_path.parent
        if (artifact_dir / "review_updates.csv").exists():
            issues.append(_issue(plan_id, "ERROR", "CLEAN_REVIEW_UPDATES_FILE_DETECTED", "review_updates.csv must not be created by this workflow.", artifact_dir / "review_updates.csv"))
    return issues


def _write(result: FirstBatchReviewerEvidenceCompletionPlanHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# First-Batch Reviewer Evidence Completion Plan Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                result.health_frame.to_markdown(index=False) if not result.health_frame.empty else "No issues.",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "health_id": paths["artifact_dir"].name,
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")


def _issue(plan_id: str, severity: str, code: str, message: str, path: Path) -> dict[str, Any]:
    return {
        "plan_id": plan_id,
        "status": "FAIL" if severity == "ERROR" else "WARN",
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    for column in HEALTH_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame.loc[:, HEALTH_COLUMNS]


def _safe_audit_metadata(root: str | Path, checked_count: int) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "checked_artifact_count": checked_count,
        "approval_applied": False,
        "clean_review_updates_created": False,
        "pit_review_run": False,
        "export_readiness_run": False,
        "export_staging_run": False,
        "universe_exported": False,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "current_candidates_executed": False,
        "snapshot_manifest_built": False,
        "forward_returns_computed": False,
        "cache_mutated": False,
    }


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value
