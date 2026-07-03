"""Health view for Source Hash / Revision ID / Available-Time artifacts."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time import (
    ARTIFACT_FILENAMES,
    AVAILABLE_TIME_METADATA_PRESENT_ONLY,
    AVAILABLE_TIME_VALIDATION_NONE,
    HASH_ALGORITHM,
    PIT_ADMISSIBILITY_NONE,
    REQUIRED_FALSE_FLAGS,
    REVISION_ID_METADATA_PRESENT_ONLY,
    REVISION_ID_VALIDATION_NONE,
    SOURCE_HASH_METADATA_PRESENT_ONLY,
    SOURCE_HASH_VALIDATION_NONE,
    STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
    STATUS_BLOCKED_BY_MALFORMED_AVAILABLE_TIME,
    STATUS_BLOCKED_BY_MALFORMED_SOURCE_HASH,
    STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
    STATUS_BLOCKED_BY_MISSING_REVISION_ID,
    STATUS_BLOCKED_BY_PATH_GUARD,
    STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA,
    STATUS_BLOCKED_BY_UNSUPPORTED_HASH_ALGORITHM,
    STATUS_METADATA_PRESENT,
    STATUS_NO_INPUT,
    STATUS_WARN_TIMEZONE_ASSUMPTION_REQUIRED,
    WORKFLOW_STAGE,
    source_hash_revision_available_time_statuses,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time_index import (
    DEFAULT_ROOT,
    VIEW_DIR_NAMES,
    build_source_hash_revision_available_time_index,
)


HEALTH_COLUMNS = ["run_id", "status", "severity", "issue_code", "message", "artifact_path"]
FORBIDDEN_STATUS_WORDING = [
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
    "source_hash_recomputed",
    "source_artifact_opened",
    "source_content_read",
    "local_file_hash_recomputed",
    "expected_hash_reverified",
    "target_csv_opened",
    "real_csv_consumed",
    "available_time_compared_to_decision_time",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "source_reliability_scored",
    "reviewer_authority_validated",
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
    "reviewer_approval",
]
BLOCKED_STATUS_CODES = {
    STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG: "MISSING_ALLOW_FLAG",
    STATUS_BLOCKED_BY_PATH_GUARD: "PATH_GUARD_BLOCKED",
    STATUS_BLOCKED_BY_UNSUPPORTED_HASH_ALGORITHM: "UNSUPPORTED_HASH_ALGORITHM",
    STATUS_BLOCKED_BY_MALFORMED_SOURCE_HASH: "MALFORMED_SOURCE_HASH",
    STATUS_BLOCKED_BY_MISSING_REVISION_ID: "MISSING_REVISION_ID",
    STATUS_BLOCKED_BY_MALFORMED_AVAILABLE_TIME: "MALFORMED_AVAILABLE_TIME",
    STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM: "FORBIDDEN_DOWNSTREAM_FLAG_TRUE",
    STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA: "UNSAFE_REFERENCE_METADATA",
}


@dataclass(frozen=True)
class SourceHashRevisionAvailableTimeHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    rows: list[dict[str, str]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def check_source_hash_revision_available_time_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/health",
) -> SourceHashRevisionAvailableTimeHealthResult:
    root_path = Path(root)
    index_output = Path(output_dir).parent / "index"
    index = build_source_hash_revision_available_time_index(root=root_path, output_dir=index_output)
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
    result = SourceHashRevisionAvailableTimeHealthResult(
        status=status,
        checked_artifact_count=index.artifact_count,
        issue_count=len(rows),
        error_count=error_count,
        warning_count=warning_count,
        rows=rows,
        artifact_paths=paths,
        warnings=[] if status == "PASS" else [f"Source hash revision available-time health is {status}."],
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
    if runtime_status not in source_hash_revision_available_time_statuses():
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
        expected_levels = {
            "source_hash_validation_level": SOURCE_HASH_VALIDATION_NONE,
            "revision_id_validation_level": REVISION_ID_VALIDATION_NONE,
            "available_time_validation_level": AVAILABLE_TIME_VALIDATION_NONE,
            "pit_admissibility_level": PIT_ADMISSIBILITY_NONE,
        }
        for field, expected in expected_levels.items():
            if str(metadata.get(field) or "") != expected:
                issues.append(_issue(run_id, "ERROR", "NO_INPUT_LEVEL_INVALID", f"{field} is invalid.", path))
    elif runtime_status in {STATUS_METADATA_PRESENT, STATUS_WARN_TIMEZONE_ASSUMPTION_REQUIRED}:
        expected_levels = {
            "source_hash_validation_level": SOURCE_HASH_METADATA_PRESENT_ONLY,
            "revision_id_validation_level": REVISION_ID_METADATA_PRESENT_ONLY,
            "available_time_validation_level": AVAILABLE_TIME_METADATA_PRESENT_ONLY,
            "pit_admissibility_level": PIT_ADMISSIBILITY_NONE,
        }
        for field, expected in expected_levels.items():
            if str(metadata.get(field) or "") != expected:
                issues.append(_issue(run_id, "ERROR", "METADATA_PRESENT_LEVEL_INVALID", f"{field} is invalid.", path))
        if str(metadata.get("source_hash_algorithm") or "") != HASH_ALGORITHM:
            issues.append(_issue(run_id, "ERROR", "UNSUPPORTED_HASH_ALGORITHM", "Source hash algorithm unsupported.", path))
        if len(str(metadata.get("source_hash_preview") or "")) > 16:
            issues.append(_issue(run_id, "ERROR", "FULL_SOURCE_HASH_DISCLOSURE_LEAK", "Source hash preview is too long.", path))
        if not _to_bool(metadata.get("revision_id_value_recorded")):
            issues.append(_issue(run_id, "ERROR", "MISSING_REVISION_ID", "Revision id value not recorded.", path))
        if not _to_bool(metadata.get("available_time_parseable")):
            issues.append(_issue(run_id, "ERROR", "MALFORMED_AVAILABLE_TIME", "Available-time not parseable.", path))
        if runtime_status == STATUS_WARN_TIMEZONE_ASSUMPTION_REQUIRED:
            if health_status != "WARN":
                issues.append(_issue(run_id, "ERROR", "TIMEZONE_WARNING_POLICY_INVALID", "Timezone warning must keep WARN health.", path))
            else:
                issues.append(_issue(run_id, "WARNING", "TIMEZONE_ASSUMPTION_REVIEW_REQUIRED", "Available-time timezone assumption requires review.", path))
    elif runtime_status in BLOCKED_STATUS_CODES:
        issues.append(_issue(run_id, "ERROR", BLOCKED_STATUS_CODES[runtime_status], "Core artifact is blocked.", path))
    elif health_status == "FAIL":
        issues.append(_issue(run_id, "ERROR", "CORE_ARTIFACT_HEALTH_FAIL", "Core artifact health is FAIL.", path))
    for field in sorted(set(FORBIDDEN_TRUE_FIELDS)):
        if _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{field} is true.", path))
    return issues


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
        issues.append(_issue(run_id, "ERROR", "FULL_SOURCE_HASH_DISCLOSURE_LEAK", "Full source hash appears outside allowed metadata policy.", path))
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
        "health_csv": root / "source_hash_revision_available_time_health.csv",
        "health_md": root / "source_hash_revision_available_time_health.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: SourceHashRevisionAvailableTimeHealthResult) -> None:
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


def _health_markdown(result: SourceHashRevisionAvailableTimeHealthResult) -> str:
    lines = [
        "# Source Hash Revision Available-Time Health",
        "",
        f"- Status: `{result.status}`",
        f"- Checked artifacts: `{result.checked_artifact_count}`",
        f"- Errors: `{result.error_count}`",
        f"- Warnings: `{result.warning_count}`",
        "- Health checks generated artifacts only and does not re-open source references, recompute hashes, or compare available_time to decision time.",
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
