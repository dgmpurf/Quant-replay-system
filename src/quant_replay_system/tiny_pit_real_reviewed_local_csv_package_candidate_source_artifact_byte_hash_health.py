"""Health view for Tiny PIT source artifact byte-hash report-only artifacts."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash import (
    ARTIFACT_FILENAMES,
    REQUIRED_FALSE_FLAGS,
    STATUS_MATCHED,
    STATUS_MISMATCHED,
    STATUS_NO_INPUT,
    STATUS_WARN_REVISION_OR_AVAILABLE_TIME_METADATA_MISSING,
    STATUS_WARN_SOURCE_HASH_METADATA_MISSING,
    WORKFLOW_STAGE,
    source_artifact_byte_hash_statuses,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash_index import (
    DEFAULT_ROOT,
    build_source_artifact_byte_hash_index,
)


HEALTH_COLUMNS = ["run_id", "status", "severity", "issue_code", "message", "artifact_path"]
HASH_PATTERN = re.compile(r"\b[0-9a-fA-F]{64}\b")
FORBIDDEN_LIVE_WORDING = [
    "SOURCE_RELIABILITY_VALIDATED",
    "SOURCE_HASH_VALIDATED",
    "PIT_ADMISSIBLE_PACKAGE",
    "PACKAGE_APPROVED",
    "PACKAGE_ADMISSIBLE",
    "READY_FOR_REPLAY",
    "ACTIVE_REPLAY_INPUT_READY",
    "BUY_REVIEW_READY",
    "TRADING_READY",
    "PERFORMANCE_VALIDATED",
]
FORBIDDEN_TRUE_FIELDS = [
    "source_content_read",
    "source_content_semantically_read",
    "target_csv_opened",
    "csv_header_read",
    "csv_values_read",
    "csv_full_content_read",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "available_time_compared_to_decision_time",
    "pit_admissibility_validated",
    "source_reliability_scored",
    "reviewer_authority_validated",
    "local_file_hash_recomputed",
    "expected_hash_reverified",
    *REQUIRED_FALSE_FLAGS,
]


@dataclass(frozen=True)
class SourceArtifactByteHashHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    rows: list[dict[str, str]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def check_source_artifact_byte_hash_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/health",
) -> SourceArtifactByteHashHealthResult:
    root_path = Path(root)
    index = build_source_artifact_byte_hash_index(root=root_path, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, str]] = []
    if not root_path.exists():
        issues.append(_issue("", "WARNING", "ARTIFACT_ROOT_MISSING", "Artifact root is missing.", root_path))
    else:
        for artifact_dir in _candidate_dirs(root_path):
            issues.extend(_issues_for_artifact_dir(artifact_dir))
    rows = [_finalize_row(row) for row in issues]
    error_count = sum(1 for row in rows if row["severity"] == "ERROR")
    warning_count = sum(1 for row in rows if row["severity"] == "WARNING")
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = _paths(output_dir)
    result = SourceArtifactByteHashHealthResult(
        status=status,
        checked_artifact_count=index.artifact_count,
        issue_count=len(rows),
        error_count=error_count,
        warning_count=warning_count,
        rows=rows,
        artifact_paths=paths,
        warnings=[] if status == "PASS" else [f"Source artifact byte-hash health is {status}."],
    )
    _write(result)
    return result


def _candidate_dirs(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir()
        and path.name not in {"index", "health", "status"}
        and not path.name.startswith("_")
        and (path / ARTIFACT_FILENAMES["metadata"]).exists()
    )


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
            with _open_path(paths["metadata"], "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                metadata = loaded
            else:
                issues.append(_issue(run_id, "ERROR", "METADATA_SCHEMA_INVALID", "Metadata JSON must be an object.", paths["metadata"]))
        except (OSError, json.JSONDecodeError):
            issues.append(_issue(run_id, "ERROR", "METADATA_UNREADABLE", "Metadata JSON is unreadable.", paths["metadata"]))
    if metadata is not None:
        run_id = str(metadata.get("run_id") or run_id)
        issues.extend(_metadata_issues(run_id, metadata, paths["metadata"]))
    for key, path in paths.items():
        if key != "metadata" and path.exists():
            issues.extend(_public_text_issues(run_id, path))
    for folder in ("index", "status"):
        view_dir = artifact_dir.parent / folder
        if view_dir.exists():
            for path in sorted(view_dir.iterdir()):
                if path.is_file():
                    issues.extend(_public_text_issues(run_id, path))
    return issues


def _metadata_issues(run_id: str, metadata: dict[str, Any], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    runtime_status = str(metadata.get("runtime_status") or metadata.get("status") or "")
    health_status = str(metadata.get("health_status") or "")
    if runtime_status not in source_artifact_byte_hash_statuses():
        issues.append(_issue(run_id, "ERROR", "INVALID_RUNTIME_STATUS", "runtime_status is invalid.", path))
    if str(metadata.get("workflow_stage") or "") != WORKFLOW_STAGE:
        issues.append(_issue(run_id, "ERROR", "WORKFLOW_STAGE_INVALID", "workflow_stage is invalid.", path))
    for field in ("runtime_status", "workflow_stage", "recommended_next_task"):
        if _has_forbidden_wording(str(metadata.get(field) or "")):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_LIVE_WORDING", "Live status field contains unsafe wording.", path))
    for field in ("report_only", "diagnostic_only"):
        if not _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "REQUIRED_REPORT_FLAG_FALSE", f"{field} must be true.", path))
    for field in FORBIDDEN_TRUE_FIELDS:
        if _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", "Forbidden metadata flag is true.", path))
    if runtime_status == STATUS_MATCHED and health_status != "PASS":
        issues.append(_issue(run_id, "ERROR", "MATCHED_HEALTH_INVALID", "Matched context must keep PASS health.", path))
    if runtime_status in {
        STATUS_MISMATCHED,
        STATUS_WARN_SOURCE_HASH_METADATA_MISSING,
        STATUS_WARN_REVISION_OR_AVAILABLE_TIME_METADATA_MISSING,
    }:
        if health_status != "WARN":
            issues.append(_issue(run_id, "ERROR", "WARNING_HEALTH_INVALID", "Warning context must keep WARN health.", path))
        if runtime_status == STATUS_MISMATCHED:
            issues.append(_issue(run_id, "WARNING", "BYTE_IDENTITY_MISMATCH_ACTIONABLE", "Byte identity mismatch is actionable report-only context.", path))
        if runtime_status == STATUS_WARN_SOURCE_HASH_METADATA_MISSING:
            issues.append(_issue(run_id, "WARNING", "DECLARED_SOURCE_HASH_MISSING", "Declared source hash is missing.", path))
    if runtime_status == STATUS_NO_INPUT and health_status != "PASS":
        issues.append(_issue(run_id, "ERROR", "NO_INPUT_HEALTH_INVALID", "No-input context must keep PASS health.", path))
    if health_status == "FAIL":
        issues.append(_issue(run_id, "ERROR", "CORE_HEALTH_FAILED", "Core artifact health is FAIL.", path))
    full_hash = str(metadata.get("computed_source_hash_full") or "")
    if full_hash:
        for public_path in _public_paths(path.parent):
            issues.extend(_public_text_issues(run_id, public_path, full_hashes=[full_hash]))
    return issues


def _public_paths(artifact_dir: Path) -> list[Path]:
    return [
        artifact_dir / ARTIFACT_FILENAMES["report"],
        artifact_dir / ARTIFACT_FILENAMES["summary"],
        artifact_dir / ARTIFACT_FILENAMES["issues"],
        artifact_dir / ARTIFACT_FILENAMES["limitations"],
        artifact_dir / ARTIFACT_FILENAMES["forbidden_downstream_flags"],
    ]


def _public_text_issues(run_id: str, path: Path, full_hashes: list[str] | None = None) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    try:
        with _open_path(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        return issues
    if HASH_PATTERN.search(text) or any(full_hash and full_hash in text for full_hash in (full_hashes or [])):
        issues.append(_issue(run_id, "ERROR", "FULL_HASH_DISCLOSURE_LEAK", "Public artifact exposes a full hash.", path))
    if "SOURCE_CONTENT_SENTINEL" in text:
        issues.append(_issue(run_id, "ERROR", "SOURCE_CONTENT_DISCLOSURE_LEAK", "Public artifact exposes source content marker.", path))
    if any(marker in text for marker in ("TARGET_CSV_SENTINEL", "CSV_HEADER_SENTINEL", "CSV_ROW_SENTINEL")):
        issues.append(_issue(run_id, "ERROR", "TARGET_CSV_DISCLOSURE_LEAK", "Public artifact exposes target CSV marker.", path))
    if any(marker in text for marker in ("SECRET_SENTINEL", "/private/", "private/source")):
        issues.append(_issue(run_id, "ERROR", "PRIVATE_OR_SECRET_DISCLOSURE_LEAK", "Public artifact exposes a private path or secret marker.", path))
    if _has_forbidden_wording(text):
        issues.append(_issue(run_id, "ERROR", "FORBIDDEN_LIVE_WORDING", "Public artifact contains unsafe live wording.", path))
    return issues


def _has_forbidden_wording(value: str) -> bool:
    return any(phrase in value for phrase in FORBIDDEN_LIVE_WORDING)


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
        "health_csv": root / "source_artifact_byte_hash_health.csv",
        "health_md": root / "source_artifact_byte_hash_health.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: SourceArtifactByteHashHealthResult) -> None:
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


def _health_markdown(result: SourceArtifactByteHashHealthResult) -> str:
    lines = [
        "# Source Artifact Byte-Hash Health",
        "",
        f"- Status: `{result.status}`",
        f"- Checked artifact count: `{result.checked_artifact_count}`",
        f"- Error count: `{result.error_count}`",
        f"- Warning count: `{result.warning_count}`",
        "- Health checks do not expose full hashes, private paths, source content, CSV content, replay readiness, buy-review, or trading readiness.",
        "",
    ]
    return "\n".join(lines)


def _write_rows(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _open_path(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _open_path(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _open_path(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def _open_path(path: Path, *args: Any, **kwargs: Any) -> Any:
    return getattr(path, "open")(*args, **kwargs)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)
