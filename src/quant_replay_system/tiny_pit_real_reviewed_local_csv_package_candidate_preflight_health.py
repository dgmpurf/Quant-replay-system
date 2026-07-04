"""Health view for Tiny PIT reviewed LOCAL_CSV preflight artifacts."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_preflight import (
    ARTIFACT_FILENAMES,
    NEGATIVE_FALSE_FIELDS,
    STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
    STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
    STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
    STATUS_BLOCKED_BY_MISSING_REQUIRED_METADATA,
    STATUS_BLOCKED_BY_PATH_GUARD,
    STATUS_BLOCKED_BY_PERMISSION,
    STATUS_BLOCKED_BY_REVIEWER_QUALITY_LIMITATION,
    STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA,
    STATUS_BLOCKED_BY_UNSUPPORTED_VALIDATION_CLAIM,
    STATUS_HEALTH_FAILED,
    STATUS_METADATA_CONTEXT_REPORT_ONLY,
    STATUS_NO_INPUT,
    STATUS_WARN_MISSING_OPTIONAL_EVIDENCE,
    STATUS_WARN_NO_AVAILABLE_TIME_PIT_GATE,
    STATUS_WARN_UNVALIDATED_SOURCE_HASH,
    WORKFLOW_STAGE,
    preflight_statuses,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_preflight_index import (
    DEFAULT_ROOT,
    VIEW_DIR_NAMES,
    build_real_reviewed_local_csv_package_candidate_preflight_index,
)


HEALTH_COLUMNS = ["run_id", "status", "severity", "issue_code", "message", "artifact_path"]
FORBIDDEN_LIVE_WORDING = [
    "REAL_PACKAGE_CANDIDATE_CREATED",
    "PACKAGE_APPROVED",
    "PACKAGE_ADMISSIBLE",
    "PIT_ADMISSIBLE_PACKAGE",
    "READY_FOR_REPLAY",
    "REPLAY_INPUT_READY",
    "ACTIVE_REPLAY_INPUT_READY",
    "APPROVED_FOR_ACTIVE_INPUT",
    "BUY_REVIEW_READY",
    "TRADING_READY",
    "PERFORMANCE_VALIDATED",
]
BLOCKED_STATUS_CODES = {
    STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG: "MISSING_ALLOW_FLAG",
    STATUS_BLOCKED_BY_MANIFEST_SCHEMA: "MANIFEST_SCHEMA_BLOCKED",
    STATUS_BLOCKED_BY_PATH_GUARD: "PATH_GUARD_BLOCKED",
    STATUS_BLOCKED_BY_MISSING_REQUIRED_METADATA: "MISSING_REQUIRED_EVIDENCE",
    STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA: "UNSAFE_REFERENCE_METADATA",
    STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM: "FORBIDDEN_DOWNSTREAM",
    STATUS_BLOCKED_BY_REVIEWER_QUALITY_LIMITATION: "REVIEWER_QUALITY_BLOCKER",
    STATUS_BLOCKED_BY_PERMISSION: "FORBIDDEN_PERMISSION",
    STATUS_BLOCKED_BY_UNSUPPORTED_VALIDATION_CLAIM: "UNSUPPORTED_VALIDATION_CLAIM",
    STATUS_HEALTH_FAILED: "CORE_HEALTH_FAILED",
}
WARN_STATUS_CODES = {
    STATUS_WARN_MISSING_OPTIONAL_EVIDENCE: "MISSING_OPTIONAL_EVIDENCE",
    STATUS_WARN_UNVALIDATED_SOURCE_HASH: "UNVALIDATED_FUTURE_CAPABILITY_WARNING",
    STATUS_WARN_NO_AVAILABLE_TIME_PIT_GATE: "UNVALIDATED_FUTURE_CAPABILITY_WARNING",
}
CONTENT_LEAK_MARKERS = [
    "SOURCE_CONTENT_SHOULD_NOT_APPEAR",
    "TARGET_CSV_SHOULD_NOT_APPEAR",
    "HEADER_VALUE_SHOULD_NOT_APPEAR",
    "ROW_VALUE_SHOULD_NOT_APPEAR",
    "source_content_sample",
    "target_csv_sample",
    "header_value_sample",
    "row_value_sample",
]
PRIVATE_LEAK_MARKERS = [".env", "private/source.csv", "secret", "token", "credential"]
REVIEWER_LEAK_MARKERS = ["private-reviewer-identity"]
FULL_HASH_PATTERN = re.compile(r"\b[0-9a-fA-F]{64}\b")


@dataclass(frozen=True)
class RealReviewedLocalCsvPreflightHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    rows: list[dict[str, str]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def check_real_reviewed_local_csv_package_candidate_preflight_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/health",
) -> RealReviewedLocalCsvPreflightHealthResult:
    root_path = Path(root)
    index_output = Path(output_dir).parent / "index"
    index = build_real_reviewed_local_csv_package_candidate_preflight_index(
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
    result = RealReviewedLocalCsvPreflightHealthResult(
        status=status,
        checked_artifact_count=index.artifact_count,
        issue_count=len(rows),
        error_count=error_count,
        warning_count=warning_count,
        rows=rows,
        artifact_paths=paths,
        warnings=[] if status == "PASS" else [f"Preflight artifact health is {status}."],
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
            loaded = json.loads(paths["metadata"].read_text(encoding="utf-8"))
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
    if paths["evidence_reference_matrix"].exists():
        issues.extend(_matrix_issues(run_id, paths["evidence_reference_matrix"]))
    for path in paths.values():
        if path.exists():
            issues.extend(_text_issues(run_id, path))
    return issues


def _metadata_issues(run_id: str, metadata: dict[str, Any], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    runtime_status = str(metadata.get("runtime_status") or metadata.get("status") or "")
    health_status = str(metadata.get("health_status") or "")
    if runtime_status not in preflight_statuses():
        issues.append(_issue(run_id, "ERROR", "INVALID_RUNTIME_STATUS", "runtime_status is invalid.", path))
    if str(metadata.get("workflow_stage") or "") != WORKFLOW_STAGE:
        issues.append(_issue(run_id, "ERROR", "WORKFLOW_STAGE_INVALID", "workflow_stage is invalid.", path))
    for field in ("runtime_status", "workflow_stage", "recommended_next_task"):
        if _has_forbidden_wording(str(metadata.get(field) or "")):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_LIVE_WORDING", "Live status wording is unsafe.", path))
    for field in ("report_only", "diagnostic_only"):
        if not _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "REQUIRED_REPORT_FLAG_FALSE", f"{field} must be true.", path))
    for field in NEGATIVE_FALSE_FIELDS:
        if _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{field} is true.", path))
    if runtime_status == STATUS_METADATA_CONTEXT_REPORT_ONLY:
        if _to_int(metadata.get("required_reference_present_count")) < _to_int(metadata.get("required_reference_count")):
            issues.append(_issue(run_id, "ERROR", "MISSING_REQUIRED_EVIDENCE", "Required evidence is missing.", path))
        if _to_int(metadata.get("promotion_blocker_count")):
            issues.append(_issue(run_id, "ERROR", "PROMOTION_BLOCKER_PRESENT", "Promotion blocker count is positive.", path))
        if health_status != "PASS":
            issues.append(_issue(run_id, "ERROR", "METADATA_CONTEXT_HEALTH_INVALID", "Metadata context should be PASS.", path))
    elif runtime_status == STATUS_NO_INPUT:
        if health_status != "PASS":
            issues.append(_issue(run_id, "ERROR", "NO_INPUT_HEALTH_INVALID", "No-input artifact should be PASS.", path))
    elif runtime_status in WARN_STATUS_CODES:
        issues.append(_issue(run_id, "WARNING", WARN_STATUS_CODES[runtime_status], "Core artifact is warning context.", path))
    elif runtime_status in BLOCKED_STATUS_CODES:
        issues.append(_issue(run_id, "ERROR", BLOCKED_STATUS_CODES[runtime_status], "Core artifact is blocked.", path))
    elif health_status == "FAIL":
        issues.append(_issue(run_id, "ERROR", "CORE_ARTIFACT_HEALTH_FAIL", "Core artifact health is FAIL.", path))
    if _to_int(metadata.get("missing_required_reference_count")):
        issues.append(_issue(run_id, "ERROR", "MISSING_REQUIRED_EVIDENCE", "Required evidence is missing.", path))
    if (
        runtime_status != STATUS_WARN_MISSING_OPTIONAL_EVIDENCE
        and _to_int(metadata.get("missing_optional_reference_count"))
    ):
        issues.append(_issue(run_id, "WARNING", "MISSING_OPTIONAL_EVIDENCE", "Optional evidence is missing.", path))
    return issues


def _safety_flag_issues(run_id: str, path: Path) -> list[dict[str, str]]:
    try:
        flags = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [_issue(run_id, "ERROR", "SAFETY_FLAGS_UNREADABLE", "Safety flags JSON is unreadable.", path)]
    if not isinstance(flags, dict):
        return [_issue(run_id, "ERROR", "SAFETY_FLAGS_UNREADABLE", "Safety flags JSON is not an object.", path)]
    issues: list[dict[str, str]] = []
    for flag in NEGATIVE_FALSE_FIELDS:
        if flag not in flags:
            issues.append(_issue(run_id, "ERROR", "MISSING_SAFETY_FLAG", f"{flag} is missing.", path))
        elif _to_bool(flags.get(flag)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_SAFETY_FLAG_TRUE", f"{flag} is true.", path))
    return issues


def _matrix_issues(run_id: str, path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError:
        return [_issue(run_id, "ERROR", "MATRIX_UNREADABLE", "Evidence matrix is unreadable.", path)]
    for row in rows:
        decision = str(row.get("reference_decision") or "")
        reference_name = str(row.get("reference_name") or "")
        runtime_status = str(row.get("reference_runtime_status") or "")
        if _has_forbidden_wording(runtime_status):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_LIVE_WORDING", "Reference status wording is unsafe.", path))
        if reference_name == "expected_hash_verification_metadata" and decision == "WARN":
            issues.append(_issue(run_id, "WARNING", "EXPECTED_HASH_REFERENCE_WARN", "Expected-hash reference is warning context.", path))
        if decision == "UNSUPPORTED_VALIDATION_CLAIM":
            issues.append(_issue(run_id, "ERROR", "UNSUPPORTED_VALIDATION_CLAIM", "Reference claims unsupported validation.", path))
        elif decision == "FORBIDDEN_DOWNSTREAM":
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_DOWNSTREAM", "Reference has forbidden downstream flag.", path))
        elif decision == "REVIEWER_QUALITY_LIMITATION_BLOCK":
            issues.append(_issue(run_id, "ERROR", "REVIEWER_QUALITY_BLOCKER", "Reviewer quality limitation blocker.", path))
        elif decision == "PERMISSION_BLOCK":
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_PERMISSION", "Forbidden permission context.", path))
        elif decision in {"UNSAFE_REFERENCE_METADATA", "PATH_GUARD_BLOCK", "BLOCK"}:
            issues.append(_issue(run_id, "ERROR", "UNSAFE_REFERENCE_METADATA", "Reference metadata is blocked.", path))
    return issues


def _text_issues(run_id: str, path: Path) -> list[dict[str, str]]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    issues: list[dict[str, str]] = []
    if FULL_HASH_PATTERN.search(text):
        issues.append(_issue(run_id, "ERROR", "FULL_HASH_DISCLOSURE_LEAK", "Full hash-like value appears in artifact.", path))
    if any(marker in text for marker in REVIEWER_LEAK_MARKERS):
        issues.append(_issue(run_id, "ERROR", "REVIEWER_ID_DISCLOSURE_LEAK", "Reviewer identity disclosure marker appears in artifact.", path))
    if any(marker.lower() in text.lower() for marker in PRIVATE_LEAK_MARKERS):
        issues.append(_issue(run_id, "ERROR", "PRIVATE_PATH_DISCLOSURE_LEAK", "Private path or secret marker appears in artifact.", path))
    if any(marker in text for marker in CONTENT_LEAK_MARKERS):
        issues.append(_issue(run_id, "ERROR", "SOURCE_OR_CSV_CONTENT_LEAK", "Source or CSV content marker appears in artifact.", path))
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


def _paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {
        "artifact_dir": root,
        "health_csv": root / "real_reviewed_local_csv_package_candidate_preflight_health.csv",
        "health_md": root / "real_reviewed_local_csv_package_candidate_preflight_health.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: RealReviewedLocalCsvPreflightHealthResult) -> None:
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


def _health_markdown(result: RealReviewedLocalCsvPreflightHealthResult) -> str:
    lines = [
        "# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Health",
        "",
        f"- status: {result.status}",
        f"- checked_artifact_count: {result.checked_artifact_count}",
        "- scope: generated preflight artifacts only",
        "- source/reference/CSV content: not read",
        "",
    ]
    for row in result.rows:
        lines.append(f"- {row['severity']} {row['issue_code']}: {row['message']}")
    return "\n".join(lines)


def _write_rows(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows([{column: row.get(column, "") for column in columns} for row in rows])


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def _has_forbidden_wording(text: str) -> bool:
    return any(phrase in text for phrase in FORBIDDEN_LIVE_WORDING)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
