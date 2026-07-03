"""Health view for Reviewer Authority / Quality / Limitation artifacts."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_reviewer_authority_quality_limitation import (
    ARTIFACT_FILENAMES,
    PACKAGE_PROMOTION_NONE,
    PERMISSION_CLASS_METADATA_PRESENT_ONLY,
    PERMISSION_REVIEW_NONE,
    QUALITY_METADATA_PRESENT_ONLY,
    QUALITY_STATUS_NONE,
    REQUIRED_FALSE_FLAGS,
    REVIEWER_AUTHORITY_NONE,
    REVIEWER_METADATA_PRESENT_ONLY,
    LIMITATION_METADATA_PRESENT_ONLY,
    LIMITATION_REVIEW_NONE,
    STATUS_BLOCKED_BY_BLOCKING_LIMITATION,
    STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
    STATUS_BLOCKED_BY_FORBIDDEN_PERMISSION,
    STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
    STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
    STATUS_BLOCKED_BY_MISSING_QUALITY_STATUS,
    STATUS_BLOCKED_BY_MISSING_REVIEWER_METADATA,
    STATUS_BLOCKED_BY_PATH_GUARD,
    STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA,
    STATUS_BLOCKED_BY_UNSUPPORTED_REVIEWER_ROLE,
    STATUS_METADATA_PRESENT,
    STATUS_NO_INPUT,
    STATUS_WARN_LIMITATIONS,
    WORKFLOW_STAGE,
    reviewer_authority_quality_limitation_statuses,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_reviewer_authority_quality_limitation_index import (
    DEFAULT_ROOT,
    VIEW_DIR_NAMES,
    build_reviewer_authority_quality_limitation_index,
)


HEALTH_COLUMNS = ["run_id", "status", "severity", "issue_code", "message", "artifact_path"]
FORBIDDEN_STATUS_WORDING = [
    "REVIEWER_APPROVED_PACKAGE",
    "PACKAGE_APPROVED",
    "PACKAGE_ADMISSIBLE",
    "PIT_ADMISSIBLE_PACKAGE",
    "READY_FOR_REPLAY",
    "REPLAY_INPUT_READY",
    "ACTIVE_REPLAY_INPUT_READY",
    "APPROVED_FOR_ACTIVE_INPUT",
    "TRADING_READY",
    "BUY_REVIEW_READY",
    "PERFORMANCE_VALIDATED",
]
FORBIDDEN_TRUE_FIELDS = [
    "reviewer_authority_validated",
    "quality_status_validated",
    "permission_class_validated",
    "limitations_overridden_by_reviewer",
    "limitations_overridden_by_quality",
    "source_reliability_scored",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    *REQUIRED_FALSE_FLAGS,
]
DISCLOSURE_MARKERS = [
    "SOURCE_CONTENT_SENTINEL",
    "TARGET_CSV_SENTINEL",
    "ROW_VALUE_SENTINEL",
    "source_content_sample",
    "target_csv_sample",
    "row_value_sample",
    "source_reliability_score_value",
    "private/source",
    "private\\source",
]
BLOCKED_STATUS_CODES = {
    STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG: "MISSING_ALLOW_FLAG",
    STATUS_BLOCKED_BY_MANIFEST_SCHEMA: "MANIFEST_SCHEMA_BLOCKED",
    STATUS_BLOCKED_BY_PATH_GUARD: "PATH_GUARD_BLOCKED",
    STATUS_BLOCKED_BY_MISSING_REVIEWER_METADATA: "MISSING_REVIEWER_METADATA",
    STATUS_BLOCKED_BY_UNSUPPORTED_REVIEWER_ROLE: "UNSUPPORTED_REVIEWER_ROLE",
    STATUS_BLOCKED_BY_MISSING_QUALITY_STATUS: "MISSING_QUALITY_STATUS",
    STATUS_BLOCKED_BY_BLOCKING_LIMITATION: "BLOCKING_LIMITATION_PRESENT",
    STATUS_BLOCKED_BY_FORBIDDEN_PERMISSION: "FORBIDDEN_PERMISSION_CLASS",
    STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM: "FORBIDDEN_DOWNSTREAM_FLAG_TRUE",
    STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA: "UNSAFE_REFERENCE_METADATA",
}


@dataclass(frozen=True)
class ReviewerAuthorityQualityLimitationHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    rows: list[dict[str, str]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def check_reviewer_authority_quality_limitation_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/health",
) -> ReviewerAuthorityQualityLimitationHealthResult:
    root_path = Path(root)
    index_output = Path(output_dir).parent / "index"
    index = build_reviewer_authority_quality_limitation_index(
        root=root_path,
        output_dir=index_output,
    )
    issues: list[dict[str, str]] = []
    if not root_path.exists():
        issues.append(_issue("", "WARNING", "ARTIFACT_ROOT_MISSING", "Artifact root is missing.", root_path))
    for artifact_dir in _candidate_dirs(root_path):
        issues.extend(_issues_for_artifact_dir(artifact_dir))
    rows = [_finalize_row(row) for row in issues]
    error_count = sum(1 for row in rows if row["severity"] == "ERROR")
    warning_count = sum(1 for row in rows if row["severity"] == "WARNING")
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = _paths(output_dir)
    result = ReviewerAuthorityQualityLimitationHealthResult(
        status=status,
        checked_artifact_count=index.artifact_count,
        issue_count=len(rows),
        error_count=error_count,
        warning_count=warning_count,
        rows=rows,
        artifact_paths=paths,
        warnings=[] if status == "PASS" else [f"Reviewer quality limitation health is {status}."],
    )
    _write(result)
    return result


def _issues_for_artifact_dir(artifact_dir: Path) -> list[dict[str, str]]:
    run_id = artifact_dir.name
    issues: list[dict[str, str]] = []
    paths = {key: artifact_dir / filename for key, filename in ARTIFACT_FILENAMES.items()}
    for path in paths.values():
        if not path.exists():
            issues.append(_issue(run_id, "ERROR", "MISSING_REQUIRED_ARTIFACT", "Required artifact is missing.", path))
    metadata: dict[str, Any] | None = None
    if paths["metadata"].exists():
        try:
            with paths["metadata"].open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                metadata = loaded
            else:
                issues.append(_issue(run_id, "ERROR", "METADATA_UNREADABLE", "Metadata JSON is not an object.", paths["metadata"]))
        except (OSError, json.JSONDecodeError):
            issues.append(_issue(run_id, "ERROR", "METADATA_UNREADABLE", "Metadata JSON is unreadable.", paths["metadata"]))
    if metadata is not None:
        run_id = str(metadata.get("run_id") or run_id)
        issues.extend(_metadata_issues(run_id, metadata, paths["metadata"]))
    if paths["forbidden_downstream_flags"].exists():
        issues.extend(_safety_flag_issues(run_id, paths["forbidden_downstream_flags"]))
    for key, path in paths.items():
        if key != "metadata" and path.exists():
            issues.extend(_text_issues(run_id, path))
    sibling_root = artifact_dir.parent
    for folder in ("index", "status"):
        view_dir = sibling_root / folder
        if view_dir.exists():
            for path in sorted(view_dir.iterdir()):
                if path.is_file():
                    issues.extend(_text_issues(run_id, path))
    return issues


def _metadata_issues(run_id: str, metadata: dict[str, Any], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    runtime_status = str(metadata.get("runtime_status") or metadata.get("status") or "")
    health_status = str(metadata.get("health_status") or "")
    if runtime_status not in reviewer_authority_quality_limitation_statuses():
        issues.append(_issue(run_id, "ERROR", "INVALID_RUNTIME_STATUS", "runtime_status is invalid.", path))
    if str(metadata.get("workflow_stage") or "") != WORKFLOW_STAGE:
        issues.append(_issue(run_id, "ERROR", "WORKFLOW_STAGE_INVALID", "workflow_stage is invalid.", path))
    for field in ("runtime_status", "workflow_stage", "recommended_next_task"):
        if _has_forbidden_wording(str(metadata.get(field) or "")):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_STATUS_WORDING", "Live status field contains unsafe wording.", path))
    for field in ("report_only", "diagnostic_only"):
        if not _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "REQUIRED_REPORT_FLAG_FALSE", f"{field} must be true.", path))
    if runtime_status == STATUS_NO_INPUT:
        _check_expected_levels(
            issues,
            run_id,
            path,
            metadata,
            {
                "reviewer_authority_level": REVIEWER_AUTHORITY_NONE,
                "quality_status_level": QUALITY_STATUS_NONE,
                "limitation_review_level": LIMITATION_REVIEW_NONE,
                "permission_review_level": PERMISSION_REVIEW_NONE,
                "package_promotion_level": PACKAGE_PROMOTION_NONE,
            },
            "NO_INPUT_LEVEL_INVALID",
        )
    elif runtime_status in {STATUS_METADATA_PRESENT, STATUS_WARN_LIMITATIONS}:
        _check_expected_levels(
            issues,
            run_id,
            path,
            metadata,
            {
                "reviewer_authority_level": REVIEWER_METADATA_PRESENT_ONLY,
                "quality_status_level": QUALITY_METADATA_PRESENT_ONLY,
                "limitation_review_level": LIMITATION_METADATA_PRESENT_ONLY,
                "permission_review_level": PERMISSION_CLASS_METADATA_PRESENT_ONLY,
                "package_promotion_level": PACKAGE_PROMOTION_NONE,
            },
            "METADATA_PRESENT_LEVEL_INVALID",
        )
        if not _to_bool(metadata.get("reviewer_role_supported")):
            issues.append(_issue(run_id, "ERROR", "UNSUPPORTED_REVIEWER_ROLE", "Reviewer role unsupported.", path))
        if not _to_bool(metadata.get("quality_status_declared")):
            issues.append(_issue(run_id, "ERROR", "MISSING_QUALITY_STATUS", "Quality status not declared.", path))
        severity = str(metadata.get("limitation_severity_max") or "")
        if severity == "WARN":
            if health_status != "WARN":
                issues.append(_issue(run_id, "ERROR", "LIMITATION_WARNING_POLICY_INVALID", "WARN limitation must keep WARN health.", path))
            else:
                issues.append(_issue(run_id, "WARNING", "LIMITATION_REVIEW_REQUIRED", "Limitation warning requires review.", path))
        if severity == "BLOCKER":
            issues.append(_issue(run_id, "ERROR", "BLOCKING_LIMITATION_PRESENT", "BLOCKER limitation present.", path))
        if str(metadata.get("permission_class") or "") in {"restricted", "private", "illegal_or_do_not_use", "unknown"}:
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_PERMISSION_CLASS", "Permission class blocks future promotion.", path))
    elif runtime_status in BLOCKED_STATUS_CODES:
        severity = "ERROR"
        issues.append(_issue(run_id, severity, BLOCKED_STATUS_CODES[runtime_status], "Core artifact is blocked.", path))
    elif health_status == "FAIL":
        issues.append(_issue(run_id, "ERROR", "CORE_ARTIFACT_HEALTH_FAIL", "Core artifact health is FAIL.", path))
    for field in sorted(set(FORBIDDEN_TRUE_FIELDS)):
        if _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{field} is true.", path))
    return issues


def _check_expected_levels(
    issues: list[dict[str, str]],
    run_id: str,
    path: Path,
    metadata: dict[str, Any],
    expected: dict[str, str],
    code: str,
) -> None:
    for field, value in expected.items():
        if str(metadata.get(field) or "") != value:
            issues.append(_issue(run_id, "ERROR", code, f"{field} is invalid.", path))


def _safety_flag_issues(run_id: str, path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            flags = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return [_issue(run_id, "ERROR", "SAFETY_FLAGS_UNREADABLE", "Safety flags JSON is unreadable.", path)]
    if not isinstance(flags, dict):
        return [_issue(run_id, "ERROR", "SAFETY_FLAGS_UNREADABLE", "Safety flags JSON is not an object.", path)]
    issues: list[dict[str, str]] = []
    for flag in REQUIRED_FALSE_FLAGS:
        if flag not in flags:
            issues.append(_issue(run_id, "ERROR", "MISSING_SAFETY_FLAG", f"{flag} is missing.", path))
        elif _to_bool(flags.get(flag)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_SAFETY_FLAG_TRUE", f"{flag} is true.", path))
    return issues


def _text_issues(run_id: str, path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            text = handle.read()
    except OSError:
        return []
    issues: list[dict[str, str]] = []
    if _contains_full_hash(text):
        issues.append(_issue(run_id, "ERROR", "FULL_HASH_DISCLOSURE_LEAK", "Full hash appears outside allowed metadata policy.", path))
    if _has_private_reviewer_identity(text):
        issues.append(_issue(run_id, "ERROR", "PRIVATE_REVIEWER_ID_LEAK", "Private reviewer identity appears outside disclosure policy.", path))
    if _has_disclosure_marker(text):
        issues.append(_issue(run_id, "ERROR", "ARTIFACT_DISCLOSURE_LEAK", "Artifact contains forbidden disclosure marker.", path))
    if _has_forbidden_wording(text):
        issues.append(_issue(run_id, "ERROR", "FORBIDDEN_STATUS_WORDING", "Artifact contains unsafe positive wording.", path))
    return issues


def _candidate_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir()
        and path.name not in VIEW_DIR_NAMES
        and not path.name.startswith("_")
        and (path / ARTIFACT_FILENAMES["metadata"]).exists()
    )


def _issue(run_id: str, severity: str, code: str, message: str, path: Path) -> dict[str, str]:
    return {
        "run_id": run_id,
        "status": "FAIL" if severity == "ERROR" else "WARN",
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }


def _finalize_row(row: dict[str, str]) -> dict[str, str]:
    return {column: row.get(column, "") for column in HEALTH_COLUMNS}


def _paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {
        "artifact_dir": root,
        "health_csv": root / "reviewer_quality_limitation_health.csv",
        "health_md": root / "reviewer_quality_limitation_health.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: ReviewerAuthorityQualityLimitationHealthResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_rows(result.artifact_paths["health_csv"], HEALTH_COLUMNS, result.rows)
    _write_text(result.artifact_paths["health_md"], _health_markdown(result))
    _write_json(
        result.artifact_paths["metadata_json"],
        {
            "status": result.status,
            "checked_artifact_count": result.checked_artifact_count,
            "issue_count": result.issue_count,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "warnings": result.warnings,
        },
    )


def _health_markdown(result: ReviewerAuthorityQualityLimitationHealthResult) -> str:
    lines = [
        "# Reviewer Authority Quality Limitation Health",
        "",
        f"- Status: `{result.status}`",
        f"- Checked artifacts: `{result.checked_artifact_count}`",
        f"- Errors: `{result.error_count}`",
        f"- Warnings: `{result.warning_count}`",
        "- Health checks generated artifacts only and does not re-open reviewer metadata, validate authority, promote quality, or create package/replay/trading readiness.",
        "",
        "| Severity | Issue code | Message |",
        "|---|---|---|",
    ]
    for row in result.rows:
        lines.append(f"| {row['severity']} | {row['issue_code']} | {row['message']} |")
    return "\n".join(lines) + "\n"


def _write_rows(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(text)


def _contains_full_hash(text: str) -> bool:
    return re.search(r"\b[0-9a-fA-F]{64}\b", text) is not None


def _has_private_reviewer_identity(text: str) -> bool:
    return "private-reviewer-identity" in text


def _has_disclosure_marker(text: str) -> bool:
    return any(marker in text for marker in DISCLOSURE_MARKERS)


def _has_forbidden_wording(text: str) -> bool:
    return any(phrase in text for phrase in FORBIDDEN_STATUS_WORDING)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)
