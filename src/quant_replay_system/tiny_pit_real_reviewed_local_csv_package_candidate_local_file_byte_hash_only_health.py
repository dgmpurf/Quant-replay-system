"""Health view for Local File Byte-Hash-Only artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only import (
    ARTIFACT_FILENAMES,
    CSV_READ_NONE,
    HASH_ALGORITHM,
    LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
    REQUIRED_FALSE_FLAGS,
    WORKFLOW_STAGE,
    local_file_byte_hash_only_statuses,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only_index import (
    DEFAULT_ROOT,
    VIEW_DIR_NAMES,
    build_local_file_byte_hash_only_index,
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
    "csv_header_read",
    "csv_row_count_computed",
    "csv_values_read",
    "csv_full_content_read",
    "real_csv_consumed",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "source_reliability_scored",
    "reviewer_authority_validated",
    *REQUIRED_FALSE_FLAGS,
]


@dataclass(frozen=True)
class LocalFileByteHashOnlyHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]


def check_local_file_byte_hash_only_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/health",
) -> LocalFileByteHashOnlyHealthResult:
    root_path = Path(root)
    index_output = Path(output_dir).parent / "index"
    index = build_local_file_byte_hash_only_index(root=root_path, output_dir=index_output)
    issues: list[dict[str, str]] = []
    if not root_path.exists():
        issues.append(_issue("", "WARNING", "ARTIFACT_ROOT_MISSING", "Artifact root does not exist.", root_path))
    for artifact_dir in _candidate_dirs(root_path):
        issues.extend(_issues_for_artifact_dir(artifact_dir))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = _paths(output_dir)
    result = LocalFileByteHashOnlyHealthResult(
        status=status,
        checked_artifact_count=index.artifact_count,
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=[] if status == "PASS" else [f"Local file byte-hash-only health is {status}."],
    )
    _write(result)
    return result


def _issues_for_artifact_dir(artifact_dir: Path) -> list[dict[str, str]]:
    run_id = artifact_dir.name
    issues: list[dict[str, str]] = []
    paths = {key: artifact_dir / filename for key, filename in ARTIFACT_FILENAMES.items()}
    for path in paths.values():
        if not path.exists():
            issues.append(_issue(run_id, "ERROR", "MISSING_REQUIRED_ARTIFACT", f"Missing required artifact: {path.name}", path))
    metadata: dict[str, Any] | None = None
    if paths["metadata"].exists():
        try:
            metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            issues.append(_issue(run_id, "ERROR", "METADATA_UNREADABLE", "Metadata JSON is unreadable.", paths["metadata"]))
    if metadata is not None:
        run_id = str(metadata.get("run_id") or run_id)
        issues.extend(_metadata_issues(run_id, metadata, paths["metadata"]))
        issues.extend(_full_hash_leak_issues(run_id, metadata, paths))
    if paths["forbidden_downstream_flags"].exists():
        issues.extend(_safety_flag_issues(run_id, paths["forbidden_downstream_flags"]))
    for key, path in paths.items():
        if key != "metadata" and path.exists():
            issues.extend(_text_issues(run_id, path))
    return issues


def _metadata_issues(run_id: str, metadata: dict[str, Any], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    runtime_status = str(metadata.get("runtime_status") or metadata.get("status") or "")
    if runtime_status not in local_file_byte_hash_only_statuses():
        issues.append(_issue(run_id, "ERROR", "INVALID_RUNTIME_STATUS", "runtime_status is invalid or unsafe.", path))
    if str(metadata.get("workflow_stage") or "") != WORKFLOW_STAGE:
        issues.append(_issue(run_id, "ERROR", "WORKFLOW_STAGE_INVALID", "workflow_stage is invalid.", path))
    for field in ("runtime_status", "workflow_stage", "recommended_next_task"):
        if _has_forbidden_wording(str(metadata.get(field) or "")):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_STATUS_WORDING", f"{field} contains unsafe positive wording.", path))
    for flag in ["report_only", "diagnostic_only"]:
        if not _to_bool(metadata.get(flag)):
            issues.append(_issue(run_id, "ERROR", "REQUIRED_REPORT_FLAG_FALSE", f"{flag} is not true.", path))
    computed = _to_bool(metadata.get("local_file_byte_hash_computed"))
    algorithm = str(metadata.get("local_file_byte_hash_algorithm") or "")
    if algorithm and algorithm != HASH_ALGORITHM:
        issues.append(_issue(run_id, "ERROR", "UNSUPPORTED_HASH_ALGORITHM", "Hash algorithm is unsupported.", path))
    if computed:
        if algorithm != HASH_ALGORITHM:
            issues.append(_issue(run_id, "ERROR", "HASH_COMPUTED_WITH_UNSUPPORTED_ALGORITHM", "Computed hash must use SHA-256.", path))
        if str(metadata.get("local_file_hash_level") or "") != LOCAL_FILE_BYTE_HASH_SHA256_ONLY:
            issues.append(_issue(run_id, "ERROR", "HASH_LEVEL_INVALID", "Computed hash level is invalid.", path))
        if str(metadata.get("csv_read_level") or "") != CSV_READ_NONE:
            issues.append(_issue(run_id, "ERROR", "CSV_READ_LEVEL_INVALID", "Computed hash artifacts must keep CSV_READ_NONE.", path))
        if not str(metadata.get("local_file_byte_hash_preview") or ""):
            issues.append(_issue(run_id, "ERROR", "HASH_PREVIEW_MISSING", "Computed hash preview is missing.", path))
    for field in sorted(set(FORBIDDEN_TRUE_FIELDS)):
        if _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{field} is true.", path))
    return issues


def _full_hash_leak_issues(run_id: str, metadata: dict[str, Any], paths: dict[str, Path]) -> list[dict[str, str]]:
    full_hash = str(metadata.get("local_file_byte_hash_value") or "")
    if not _looks_like_sha256(full_hash):
        return []
    issues: list[dict[str, str]] = []
    for key in ("report", "summary", "issues", "forbidden_downstream_flags"):
        path = paths[key]
        if path.exists() and full_hash in path.read_text(encoding="utf-8", errors="ignore"):
            issues.append(_issue(run_id, "ERROR", "FULL_HASH_DISCLOSURE_LEAK", "Full hash appears outside metadata.", path))
    index_dir = paths["metadata"].parent.parent / "index"
    for path in [index_dir / "local_file_byte_hash_only_index.csv", index_dir / "local_file_byte_hash_only_index.md", index_dir / "metadata.json"]:
        if path.exists() and full_hash in path.read_text(encoding="utf-8", errors="ignore"):
            issues.append(_issue(run_id, "ERROR", "FULL_HASH_DISCLOSURE_LEAK", "Full hash appears in index output.", path))
    return issues


def _safety_flag_issues(run_id: str, path: Path) -> list[dict[str, str]]:
    try:
        flags = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [_issue(run_id, "ERROR", "SAFETY_FLAGS_UNREADABLE", "Safety flags JSON is unreadable.", path)]
    issues: list[dict[str, str]] = []
    for flag in REQUIRED_FALSE_FLAGS:
        if flag not in flags:
            issues.append(_issue(run_id, "ERROR", "MISSING_SAFETY_FLAG", f"{flag} is missing.", path))
        elif _to_bool(flags.get(flag)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_SAFETY_FLAG_TRUE", f"{flag} is true.", path))
    return issues


def _text_issues(run_id: str, path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not _has_forbidden_wording(text):
        return []
    return [_issue(run_id, "ERROR", "FORBIDDEN_STATUS_WORDING", "Artifact contains unsafe positive wording.", path)]


def _has_forbidden_wording(text: str) -> bool:
    for forbidden in FORBIDDEN_STATUS_WORDING:
        pattern = rf"(?<![A-Z0-9_]){re.escape(forbidden)}(?![A-Z0-9_])"
        if re.search(pattern, text):
            return True
    return False


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


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    for column in HEALTH_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.Series(dtype="object")
    return frame[HEALTH_COLUMNS]


def _paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {
        "artifact_dir": root,
        "health_csv": root / "local_file_byte_hash_only_health.csv",
        "health_md": root / "local_file_byte_hash_only_health.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: LocalFileByteHashOnlyHealthResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(result.artifact_paths["health_csv"], index=False)
    result.artifact_paths["health_md"].write_text(_health_markdown(result), encoding="utf-8")
    metadata = {
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
    }
    result.artifact_paths["metadata_json"].write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _health_markdown(result: LocalFileByteHashOnlyHealthResult) -> str:
    lines = [
        "# Local File Byte-Hash-Only Health",
        "",
        f"- Status: `{result.status}`",
        f"- Checked artifact count: `{result.checked_artifact_count}`",
        f"- Error count: `{result.error_count}`",
        f"- Warning count: `{result.warning_count}`",
        "",
    ]
    if not result.health_frame.empty:
        lines.extend(["| Run id | Severity | Issue code |", "|---|---|---|"])
        for row in result.health_frame.to_dict("records"):
            lines.append(f"| `{row['run_id']}` | `{row['severity']}` | `{row['issue_code']}` |")
    return "\n".join(lines) + "\n"


def _looks_like_sha256(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{64}", value))


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)
