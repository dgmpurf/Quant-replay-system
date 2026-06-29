"""Health view for synthetic Tiny PIT admissibility validator artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_admissibility_validator import (
    ARTIFACT_FILENAMES,
    SAFETY_FALSE_FLAGS,
    TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED,
    tiny_pit_admissibility_validator_statuses,
)
from quant_replay_system.tiny_pit_admissibility_validator_index import VIEW_DIR_NAMES


HEALTH_COLUMNS = ["validator_run_id", "status", "severity", "issue_code", "message", "artifact_path"]
HEALTH_STATUSES = {"PASS", "WARN", "FAIL"}


@dataclass(frozen=True)
class TinyPitAdmissibilityValidatorHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]


def check_tiny_pit_admissibility_validator_health(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/tiny_pit_admissibility_validator_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/tiny_pit_admissibility_validator_v0_1/health",
) -> TinyPitAdmissibilityValidatorHealthResult:
    candidate_dirs = _candidate_dirs(Path(root))
    issues: list[dict[str, Any]] = []
    for artifact_dir in candidate_dirs:
        issues.extend(_issues_for_artifact_dir(artifact_dir))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = _paths(output_dir)
    result = TinyPitAdmissibilityValidatorHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=[] if Path(root).exists() else [f"Tiny PIT validator root does not exist: {root}"],
    )
    _write(result)
    return result


def _issues_for_artifact_dir(artifact_dir: Path) -> list[dict[str, Any]]:
    validator_run_id = artifact_dir.name
    issues: list[dict[str, Any]] = []
    paths = {key: artifact_dir / filename for key, filename in ARTIFACT_FILENAMES.items()}
    for path in paths.values():
        if not path.exists():
            issues.append(_issue(validator_run_id, "ERROR", "MISSING_REQUIRED_ARTIFACT", f"Missing {path.name}.", path))
    metadata: dict[str, Any] | None = None
    if paths["metadata"].exists():
        try:
            metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(_issue(validator_run_id, "ERROR", "METADATA_UNREADABLE", f"Metadata unreadable: {exc}", paths["metadata"]))
    if metadata is not None:
        validator_run_id = str(metadata.get("validator_run_id") or validator_run_id)
        issues.extend(_metadata_issues(validator_run_id, metadata, paths["metadata"]))
    if paths["safety_flags"].exists():
        issues.extend(_safety_flag_issues(validator_run_id, paths["safety_flags"]))
    for text_path in [paths["metadata"], paths["report"], paths["output_status_contract"], paths["safety_flags"]]:
        if text_path.exists():
            issues.extend(_text_issues(validator_run_id, text_path))
    return issues


def _metadata_issues(validator_run_id: str, metadata: dict[str, Any], path: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    required_fields = {
        "validator_run_id",
        "created_at",
        "workflow_stage",
        "status",
        "case_count",
        "pass_candidate_count",
        "warning_count",
        "blocker_count",
        "report_only",
        "diagnostic_only",
        "synthetic_only",
        "artifact_path",
        "report_path",
    }
    missing = sorted(field for field in required_fields if field not in metadata)
    if missing:
        issues.append(_issue(validator_run_id, "ERROR", "MISSING_METADATA_FIELD", f"Missing: {','.join(missing)}", path))
    status = _text(metadata.get("status"))
    if status not in HEALTH_STATUSES:
        issues.append(_issue(validator_run_id, "ERROR", "INVALID_STATUS", f"Invalid status: {status}", path))
    if _text(metadata.get("workflow_stage")) != TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED:
        issues.append(_issue(validator_run_id, "ERROR", "WORKFLOW_STAGE_INVALID", "workflow_stage is invalid.", path))
    for flag in ["report_only", "diagnostic_only", "synthetic_only"]:
        if not _to_bool(metadata.get(flag)):
            issues.append(_issue(validator_run_id, "ERROR", "REQUIRED_REPORT_FLAG_FALSE", f"{flag} is not true.", path))
    for flag in SAFETY_FALSE_FLAGS:
        if _to_bool(metadata.get(flag)):
            issues.append(_issue(validator_run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{flag} is true.", path))
    return issues


def _safety_flag_issues(validator_run_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        flags = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [_issue(validator_run_id, "ERROR", "SAFETY_FLAGS_UNREADABLE", f"safety_flags unreadable: {exc}", path)]
    issues = []
    for flag in SAFETY_FALSE_FLAGS:
        if _to_bool(flags.get(flag)):
            issues.append(_issue(validator_run_id, "ERROR", "FORBIDDEN_SAFETY_FLAG_TRUE", f"{flag} is true.", path))
    return issues


def _text_issues(validator_run_id: str, path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    issues: list[dict[str, Any]] = []
    if "ACTIVE_REPLAY_INPUT_READY" in text:
        issues.append(_issue(validator_run_id, "ERROR", "FORBIDDEN_ACTIVE_READY_TEXT", "ACTIVE_REPLAY_INPUT_READY appears.", path))
    if re.search(r"(trading_allowed|buy_review_allowed|strategy_performance_validated)\s*[:=,]\s*true", text, re.I):
        issues.append(_issue(validator_run_id, "ERROR", "FORBIDDEN_TRUE_TEXT", "Forbidden true wording appears.", path))
    return issues


def _candidate_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and path.name not in VIEW_DIR_NAMES and not path.name.startswith("_") and (path / "metadata.json").exists()
    )


def _write(result: TinyPitAdmissibilityValidatorHealthResult) -> None:
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
        "synthetic_only": True,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
    }
    result.artifact_paths["metadata"].write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    for column in HEALTH_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame.loc[:, HEALTH_COLUMNS]


def _issue(validator_run_id: str, severity: str, issue_code: str, message: str, artifact_path: Path) -> dict[str, Any]:
    return {
        "validator_run_id": validator_run_id,
        "status": "FAIL" if severity == "ERROR" else "WARN",
        "severity": severity,
        "issue_code": issue_code,
        "message": message,
        "artifact_path": str(artifact_path),
    }


def _paths(output_dir: str | Path) -> dict[str, Path]:
    artifact_dir = Path(output_dir)
    return {
        "artifact_dir": artifact_dir,
        "health_csv": artifact_dir / "tiny_pit_admissibility_validator_health.csv",
        "metadata": artifact_dir / "metadata.json",
    }


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}
