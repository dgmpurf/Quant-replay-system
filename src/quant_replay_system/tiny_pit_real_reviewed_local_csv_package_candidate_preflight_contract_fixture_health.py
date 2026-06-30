"""Health view for Tiny PIT real reviewed LOCAL_CSV preflight fixture artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture import (
    ARTIFACT_FILENAMES,
    FORBIDDEN_STATUS_WORDING,
    SAFETY_FALSE_FLAGS,
    TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_CONTRACT_FIXTURE_CREATED_REPORT_ONLY,
    real_reviewed_local_csv_package_candidate_preflight_statuses,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_index import (
    DEFAULT_ROOT,
    VIEW_DIR_NAMES,
)


HEALTH_COLUMNS = ["fixture_id", "status", "severity", "issue_code", "message", "artifact_path"]
REQUIRED_METADATA_FIELDS = {
    "fixture_id",
    "fixture_version",
    "workflow_name",
    "workflow_stage",
    "status",
    "health_status",
    "created_at",
    "case_count",
    "pass_count",
    "warn_count",
    "fail_count",
    "blocker_count",
    "warning_count",
    "report_only",
    "diagnostic_only",
    "synthetic_only",
    "artifact_path",
    "report_path",
    "recommended_next_task",
}


@dataclass(frozen=True)
class TinyPitRealReviewedLocalCsvPackageCandidatePreflightContractFixtureHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]


def check_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/health",
) -> TinyPitRealReviewedLocalCsvPackageCandidatePreflightContractFixtureHealthResult:
    root_path = Path(root)
    candidate_dirs = _candidate_dirs(root_path)
    issues: list[dict[str, Any]] = []
    for artifact_dir in candidate_dirs:
        issues.extend(_issues_for_artifact_dir(artifact_dir))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = _paths(output_dir)
    result = TinyPitRealReviewedLocalCsvPackageCandidatePreflightContractFixtureHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=[] if root_path.exists() else [f"Tiny PIT real reviewed LOCAL_CSV preflight root does not exist: {root}"],
    )
    _write(result)
    return result


def _issues_for_artifact_dir(artifact_dir: Path) -> list[dict[str, Any]]:
    fixture_id = artifact_dir.name
    issues: list[dict[str, Any]] = []
    paths = {key: artifact_dir / filename for key, filename in ARTIFACT_FILENAMES.items()}
    for path in paths.values():
        if not path.exists():
            issues.append(_issue(fixture_id, "ERROR", "MISSING_REQUIRED_ARTIFACT", f"Missing {path.name}.", path))
    metadata: dict[str, Any] | None = None
    if paths["metadata"].exists():
        try:
            metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(_issue(fixture_id, "ERROR", "METADATA_UNREADABLE", f"Metadata unreadable: {exc}", paths["metadata"]))
    if metadata is not None:
        fixture_id = str(metadata.get("fixture_id") or fixture_id)
        issues.extend(_metadata_issues(fixture_id, metadata, paths["metadata"]))
    if paths["forbidden_downstream_flags"].exists():
        issues.extend(_safety_flag_issues(fixture_id, paths["forbidden_downstream_flags"]))
    else:
        issues.append(
            _issue(
                fixture_id,
                "ERROR",
                "MISSING_FORBIDDEN_DOWNSTREAM_FLAGS",
                "forbidden_downstream_flags.json is missing.",
                paths["forbidden_downstream_flags"],
            )
        )
    for text_path in [paths["metadata"], paths["report"], paths["forbidden_downstream_flags"]]:
        if text_path.exists():
            issues.extend(_text_issues(fixture_id, text_path))
    return issues


def _metadata_issues(fixture_id: str, metadata: dict[str, Any], path: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    missing = sorted(field for field in REQUIRED_METADATA_FIELDS if field not in metadata)
    if missing:
        issues.append(_issue(fixture_id, "ERROR", "MISSING_METADATA_FIELD", f"Missing: {','.join(missing)}", path))
    status = _text(metadata.get("status"))
    if status not in real_reviewed_local_csv_package_candidate_preflight_statuses():
        issues.append(_issue(fixture_id, "ERROR", "INVALID_STATUS", f"Invalid status: {status}", path))
    if (
        _text(metadata.get("workflow_stage"))
        != TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_CONTRACT_FIXTURE_CREATED_REPORT_ONLY
    ):
        issues.append(_issue(fixture_id, "ERROR", "WORKFLOW_STAGE_INVALID", "workflow_stage is invalid.", path))
    for flag in ["report_only", "diagnostic_only", "synthetic_only"]:
        if not _to_bool(metadata.get(flag)):
            issues.append(_issue(fixture_id, "ERROR", "REQUIRED_REPORT_FLAG_FALSE", f"{flag} is not true.", path))
    for flag in SAFETY_FALSE_FLAGS:
        if _to_bool(metadata.get(flag)):
            issues.append(_issue(fixture_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{flag} is true.", path))
    return issues


def _safety_flag_issues(fixture_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        flags = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [_issue(fixture_id, "ERROR", "SAFETY_FLAGS_UNREADABLE", f"forbidden_downstream_flags unreadable: {exc}", path)]
    issues: list[dict[str, Any]] = []
    for flag in SAFETY_FALSE_FLAGS:
        if flag not in flags:
            issues.append(_issue(fixture_id, "ERROR", "MISSING_SAFETY_FLAG", f"{flag} is missing.", path))
        elif _to_bool(flags.get(flag)):
            issues.append(_issue(fixture_id, "ERROR", "FORBIDDEN_SAFETY_FLAG_TRUE", f"{flag} is true.", path))
    return issues


def _text_issues(fixture_id: str, path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    issues: list[dict[str, Any]] = []
    for forbidden in FORBIDDEN_STATUS_WORDING:
        pattern = rf"(?<![A-Z0-9_]){re.escape(forbidden)}(?![A-Z0-9_])"
        if re.search(pattern, text) and f"not {forbidden}" not in text:
            issues.append(
                _issue(
                    fixture_id,
                    "ERROR",
                    "FORBIDDEN_STATUS_WORDING",
                    f"Forbidden status wording appears: {forbidden}",
                    path,
                )
            )
    lowered = text.lower()
    for unsafe in [
        'real_csv_required": true',
        'real_csv_consumed": true',
        'real_reviewed_csv_package_created": true',
        'real_package_candidate_created": true',
        'active_reviewed_input_candidate_created": true',
        'real_replay_input_created": true',
        'active_replay_input": true',
        'active_replay_input_ready_emitted": true',
        'replay_execution_allowed": true',
        'trading_allowed": true',
        'buy_review_allowed": true',
        'data_raw_written": true',
        'data_processed_written": true',
        'data_cache_written": true',
    ]:
        if unsafe in lowered:
            issues.append(_issue(fixture_id, "ERROR", "FORBIDDEN_TRUE_TEXT", f"Forbidden true text appears: {unsafe}", path))
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


def _write(result: TinyPitRealReviewedLocalCsvPackageCandidatePreflightContractFixtureHealthResult) -> None:
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


def _issue(fixture_id: str, severity: str, issue_code: str, message: str, path: Path) -> dict[str, str]:
    return {
        "fixture_id": fixture_id,
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
        "health_csv": artifact_dir
        / "tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_health.csv",
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
