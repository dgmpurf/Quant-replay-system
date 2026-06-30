"""Health checks for manifest-only Tiny PIT real reviewed LOCAL_CSV preflight artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype import (
    ARTIFACT_FILENAMES,
    CSV_READ_LEVEL_NONE,
    FORBIDDEN_STATUS_WORDING,
    REQUIRED_FALSE_FLAGS,
    WORKFLOW_STAGE,
    real_reviewed_local_csv_package_candidate_real_preflight_prototype_statuses,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_index import (
    DEFAULT_ROOT,
    VIEW_DIR_NAMES,
)


HEALTH_COLUMNS = ["run_id", "status", "severity", "issue_code", "message", "artifact_path"]
REQUIRED_METADATA_FIELDS = {
    "run_id",
    "fixture_id",
    "fixture_version",
    "workflow_name",
    "workflow_stage",
    "runtime_status",
    "status",
    "health_status",
    "created_at",
    "report_only",
    "diagnostic_only",
    "csv_read_level",
    "manifest_read",
    "references_followed",
    "local_file_hash_computed",
    "external_source_validated",
    "pit_admissibility_validated",
    "artifact_path",
    "report_path",
}


@dataclass(frozen=True)
class TinyPitRealReviewedLocalCsvPackageCandidateRealPreflightPrototypeHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]


def check_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/health",
) -> TinyPitRealReviewedLocalCsvPackageCandidateRealPreflightPrototypeHealthResult:
    root_path = Path(root)
    candidate_dirs = _candidate_dirs(root_path)
    issues: list[dict[str, str]] = []
    for artifact_dir in candidate_dirs:
        issues.extend(_issues_for_artifact_dir(artifact_dir))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = _paths(output_dir)
    result = TinyPitRealReviewedLocalCsvPackageCandidateRealPreflightPrototypeHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=[] if root_path.exists() else [f"Tiny PIT manifest-only preflight root does not exist: {root}"],
    )
    _write(result)
    return result


def _issues_for_artifact_dir(artifact_dir: Path) -> list[dict[str, str]]:
    run_id = artifact_dir.name
    issues: list[dict[str, str]] = []
    paths = {key: artifact_dir / filename for key, filename in ARTIFACT_FILENAMES.items()}
    for path in paths.values():
        if not path.exists():
            issues.append(_issue(run_id, "ERROR", "MISSING_REQUIRED_ARTIFACT", f"Missing {path.name}.", path))
    metadata: dict[str, Any] | None = None
    if paths["metadata"].exists():
        try:
            metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(_issue(run_id, "ERROR", "METADATA_UNREADABLE", f"Metadata unreadable: {exc}", paths["metadata"]))
    if metadata is not None:
        run_id = str(metadata.get("run_id") or metadata.get("fixture_id") or run_id)
        issues.extend(_metadata_issues(run_id, metadata, paths["metadata"]))
    if paths["forbidden_downstream_flags"].exists():
        issues.extend(_safety_flag_issues(run_id, paths["forbidden_downstream_flags"]))
    for text_path in [paths["metadata"], paths["report"], paths["forbidden_downstream_flags"]]:
        if text_path.exists():
            issues.extend(_text_issues(run_id, text_path))
    return issues


def _metadata_issues(run_id: str, metadata: dict[str, Any], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    missing = sorted(field for field in REQUIRED_METADATA_FIELDS if field not in metadata)
    if missing:
        issues.append(_issue(run_id, "ERROR", "MISSING_METADATA_FIELD", f"Missing: {','.join(missing)}", path))
    runtime_status = _text(metadata.get("runtime_status") or metadata.get("status"))
    if runtime_status not in real_reviewed_local_csv_package_candidate_real_preflight_prototype_statuses():
        issues.append(_issue(run_id, "ERROR", "INVALID_RUNTIME_STATUS", f"Invalid runtime_status: {runtime_status}", path))
    if _text(metadata.get("workflow_stage")) != WORKFLOW_STAGE:
        issues.append(_issue(run_id, "ERROR", "WORKFLOW_STAGE_INVALID", "workflow_stage is invalid.", path))
    for flag in ["report_only", "diagnostic_only"]:
        if not _to_bool(metadata.get(flag)):
            issues.append(_issue(run_id, "ERROR", "REQUIRED_REPORT_FLAG_FALSE", f"{flag} is not true.", path))
    if _text(metadata.get("csv_read_level")) != CSV_READ_LEVEL_NONE:
        issues.append(_issue(run_id, "ERROR", "CSV_READ_LEVEL_UNSAFE", "csv_read_level must be CSV_READ_NONE.", path))
    for flag in ["references_followed", "local_file_hash_computed", "external_source_validated", "pit_admissibility_validated"]:
        if _to_bool(metadata.get(flag)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{flag} is true.", path))
    for flag in REQUIRED_FALSE_FLAGS:
        if _to_bool(metadata.get(flag)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{flag} is true.", path))
    return issues


def _safety_flag_issues(run_id: str, path: Path) -> list[dict[str, str]]:
    try:
        flags = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [_issue(run_id, "ERROR", "SAFETY_FLAGS_UNREADABLE", f"forbidden_downstream_flags unreadable: {exc}", path)]
    issues: list[dict[str, str]] = []
    for flag in REQUIRED_FALSE_FLAGS:
        if flag not in flags:
            issues.append(_issue(run_id, "ERROR", "MISSING_SAFETY_FLAG", f"{flag} is missing.", path))
        elif _to_bool(flags.get(flag)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_SAFETY_FLAG_TRUE", f"{flag} is true.", path))
    return issues


def _text_issues(run_id: str, path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    issues: list[dict[str, str]] = []
    for forbidden in FORBIDDEN_STATUS_WORDING:
        pattern = rf"(?<![A-Z0-9_]){re.escape(forbidden)}(?![A-Z0-9_])"
        if re.search(pattern, text) and f"not {forbidden}" not in text:
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_STATUS_WORDING", f"Forbidden wording appears: {forbidden}", path))
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
        and (path / "metadata.json").exists()
    )


def _write(result: TinyPitRealReviewedLocalCsvPackageCandidateRealPreflightPrototypeHealthResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(result.artifact_paths["health_csv"], index=False)
    metadata = {
        "health_status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "report_only": True,
        "diagnostic_only": True,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
    }
    result.artifact_paths["metadata"].write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _issue(run_id: str, severity: str, issue_code: str, message: str, path: Path) -> dict[str, str]:
    return {
        "run_id": run_id,
        "status": "FAIL" if severity == "ERROR" else "WARN",
        "severity": severity,
        "issue_code": issue_code,
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


def _paths(output_dir: str | Path) -> dict[str, Path]:
    artifact_dir = Path(output_dir)
    return {
        "artifact_dir": artifact_dir,
        "health_csv": artifact_dir / "tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_health.csv",
        "metadata": artifact_dir / "metadata.json",
    }


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)

