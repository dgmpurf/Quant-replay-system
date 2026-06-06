"""Health checks for reviewer material evidence fill guidance artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns
from quant_replay_system.reviewer_material_evidence_fill_guidance import GUIDANCE_COLUMNS, SAFE_TEMPLATE_COLUMNS
from quant_replay_system.reviewer_material_evidence_fill_guidance_index import (
    build_reviewer_material_evidence_fill_guidance_index,
)


HEALTH_COLUMNS = ["guidance_id", "status", "severity", "issue_code", "message", "artifact_path"]

REQUIRED_ARTIFACT_FILES = {
    "guidance_csv_path": "MISSING_GUIDANCE_CSV",
    "safe_template_path": "MISSING_SAFE_TEMPLATE",
    "report_path": "MISSING_REPORT",
}

REQUIRED_SIDE_FILES = [
    ("recommended_fill_order.csv", "MISSING_RECOMMENDED_FILL_ORDER"),
    ("symbol_level_fill_guidance.csv", "MISSING_SYMBOL_LEVEL_GUIDANCE"),
    ("date_specific_fill_guidance.csv", "MISSING_DATE_SPECIFIC_GUIDANCE"),
    ("no_hit_acceptance_fill_guidance.csv", "MISSING_NO_HIT_GUIDANCE"),
    ("survivorship_rationale_fill_guidance.csv", "MISSING_SURVIVORSHIP_GUIDANCE"),
    ("metadata_fill_guidance.csv", "MISSING_METADATA_GUIDANCE"),
    ("reviewer_risk_controls.csv", "MISSING_REVIEWER_RISK_CONTROLS"),
    ("source_lineage_summary.csv", "MISSING_SOURCE_LINEAGE_SUMMARY"),
]


@dataclass(frozen=True)
class ReviewerMaterialEvidenceFillGuidanceHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_reviewer_material_evidence_fill_guidance_health(
    *,
    root: str | Path = "outputs/reports/reviewer_material_evidence_fill_guidance",
    output_dir: str | Path = "outputs/reports/reviewer_material_evidence_fill_guidance/health",
) -> ReviewerMaterialEvidenceFillGuidanceHealthResult:
    index = build_reviewer_material_evidence_fill_guidance_index(root=root)
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
        "health_csv": artifact_dir / "reviewer_material_evidence_fill_guidance_health.csv",
        "health_report": artifact_dir / "reviewer_material_evidence_fill_guidance_health_report.md",
        "metadata": artifact_dir / "metadata.json",
    }
    result = ReviewerMaterialEvidenceFillGuidanceHealthResult(
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
    guidance_id = _text(row.get("guidance_id"))
    metadata_path = Path(_text(row.get("metadata_path")))
    guidance_csv_path = Path(_text(row.get("guidance_csv_path")))
    safe_template_path = Path(_text(row.get("safe_template_path")))
    issues: list[dict[str, Any]] = []
    for column, code in REQUIRED_ARTIFACT_FILES.items():
        path = Path(_text(row.get(column)))
        if not _text(path) or not path.exists():
            issues.append(_issue(guidance_id, "ERROR", code, f"Required artifact missing: {path}", path))
    if metadata_path.exists():
        artifact_dir = metadata_path.parent
        for filename, code in REQUIRED_SIDE_FILES:
            path = artifact_dir / filename
            if not path.exists():
                issues.append(_issue(guidance_id, "ERROR", code, f"Required artifact missing: {path}", path))
        fill_order_path = artifact_dir / "recommended_fill_order.csv"
        if fill_order_path.exists():
            fill_order = read_csv_preserve_symbol_columns(fill_order_path, keep_default_na=False)
            first_group = _text(fill_order.iloc[0].get("fill_group")) if not fill_order.empty else ""
            if first_group != "SAFETY_BASELINE":
                issues.append(
                    _issue(
                        guidance_id,
                        "ERROR",
                        "SAFETY_BASELINE_NOT_FIRST",
                        "Fill order must start with SAFETY_BASELINE.",
                        fill_order_path,
                    )
                )
        for filename in ["review_updates.csv", "clean_review_updates.csv"]:
            path = artifact_dir / filename
            if path.exists():
                issues.append(
                    _issue(
                        guidance_id,
                        "ERROR",
                        "CLEAN_REVIEW_UPDATES_FILE_DETECTED",
                        f"{filename} must not be created by this workflow.",
                        path,
                    )
                )
    if guidance_csv_path.exists():
        frame = read_csv_preserve_symbol_columns(guidance_csv_path, keep_default_na=False)
        missing = sorted(set(GUIDANCE_COLUMNS) - set(frame.columns))
        if missing:
            issues.append(_issue(guidance_id, "ERROR", "MISSING_REQUIRED_COLUMNS", ", ".join(missing), guidance_csv_path))
        if len(frame) != 16:
            issues.append(_issue(guidance_id, "ERROR", "UNEXPECTED_ROW_COUNT", f"Expected 16 rows, found {len(frame)}.", guidance_csv_path))
        issues.extend(_unsafe_frame_issues(guidance_id, frame, guidance_csv_path))
        if "symbol" in frame and "000001" not in set(frame["symbol"].astype(str)):
            issues.append(
                _issue(
                    guidance_id,
                    "ERROR",
                    "LEADING_ZERO_SYMBOL_NOT_PRESERVED",
                    "Leading-zero symbol 000001 was not preserved.",
                    guidance_csv_path,
                )
            )
    if safe_template_path.exists():
        template = read_csv_preserve_symbol_columns(safe_template_path, keep_default_na=False)
        missing = sorted(set(SAFE_TEMPLATE_COLUMNS) - set(template.columns))
        if missing:
            issues.append(_issue(guidance_id, "ERROR", "MISSING_SAFE_TEMPLATE_COLUMNS", ", ".join(missing), safe_template_path))
        issues.extend(_unsafe_frame_issues(guidance_id, template, safe_template_path))
    if _to_int(row.get("row_count")) != 16:
        issues.append(_issue(guidance_id, "ERROR", "UNEXPECTED_METADATA_ROW_COUNT", "Metadata row_count must be 16.", metadata_path))
    for field, code in {
        "clean_review_updates_created": "CLEAN_REVIEW_UPDATES_DETECTED",
        "approval_applied": "APPROVAL_APPLIED_DETECTED",
        "pit_review_run": "PIT_REVIEW_RUN_DETECTED",
        "export_readiness_run": "EXPORT_READINESS_RUN_DETECTED",
        "export_staging_run": "EXPORT_STAGING_RUN_DETECTED",
        "universe_exported": "UNIVERSE_EXPORT_DETECTED",
    }.items():
        if _to_bool(row.get(field)):
            issues.append(_issue(guidance_id, "ERROR", code, f"Unsafe flag {field} is true.", metadata_path))
    for field, code in {
        "no_data_raw_write": "DATA_RAW_WRITE_DETECTED",
        "no_data_processed_write": "DATA_PROCESSED_WRITE_DETECTED",
        "no_current_candidates_generated": "CURRENT_CANDIDATES_GENERATED",
        "no_snapshot_built": "SNAPSHOT_BUILT",
        "no_forward_labels": "FORWARD_LABELS_COMPUTED",
        "guidance_only": "GUIDANCE_ONLY_FLAG_MISSING",
    }.items():
        if not _to_bool(row.get(field)):
            issues.append(_issue(guidance_id, "ERROR", code, f"Required safety flag {field} is not true.", metadata_path))
    if _to_int(row.get("checklist_pass_candidate_count")):
        issues.append(
            _issue(
                guidance_id,
                "ERROR",
                "CHECKLIST_PASS_CANDIDATE_DETECTED",
                "Reviewer fill guidance must not change strict checklist behavior.",
                metadata_path,
            )
        )
    return issues


def _unsafe_frame_issues(guidance_id: str, frame: pd.DataFrame, path: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    text = path.read_text(encoding="utf-8")
    if "APPROVED_FOR_PIT_UNIVERSE" in text:
        issues.append(
            _issue(
                guidance_id,
                "ERROR",
                "APPROVED_FOR_PIT_UNIVERSE_DETECTED",
                "Guidance artifacts must not contain approval status text.",
                path,
            )
        )
    for column, code in {
        "include_flag": "INCLUDE_FLAG_TRUE_DETECTED",
        "valid_for_signal_date": "VALID_FOR_SIGNAL_DATE_TRUE_DETECTED",
        "checklist_pass_candidate": "CHECKLIST_PASS_CANDIDATE_DETECTED",
        "approval_applied": "APPROVAL_APPLIED_DETECTED",
        "clean_review_updates_created": "CLEAN_REVIEW_UPDATES_DETECTED",
    }.items():
        if column in frame and frame[column].map(_to_bool).any():
            issues.append(_issue(guidance_id, "ERROR", code, f"Unsafe column {column} contains true.", path))
    return issues


def _write(result: ReviewerMaterialEvidenceFillGuidanceHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Reviewer Material Evidence Fill Guidance Health",
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


def _issue(guidance_id: str, severity: str, code: str, message: str, path: Path) -> dict[str, Any]:
    return {
        "guidance_id": guidance_id,
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


def _to_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


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
