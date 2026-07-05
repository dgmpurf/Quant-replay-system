"""Health view for historical replay PIT evidence closure worklist artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from quant_replay_system.historical_replay_pit_evidence_closure_worklist import OUTPUT_FILES, SAFETY_FALSE_FIELDS
from quant_replay_system.historical_replay_pit_evidence_closure_worklist_index import (
    DEFAULT_ROOT,
    VIEW_DIR_NAMES,
    build_historical_replay_pit_evidence_closure_worklist_index,
)


STATUS_HEALTH_PASS = "PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_PASS_REPORT_ONLY"
STATUS_HEALTH_WARN = "PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_WARN_REVIEW_REQUIRED"
STATUS_HEALTH_FAIL = "PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_FAIL_UNSAFE"

HEALTH_COLUMNS = ["worklist_run_id", "status", "severity", "issue_code", "message", "artifact_path"]
FORBIDDEN_READINESS_WORDING = [
    "PIT_ADMISSIBLE",
    "PIT_APPROVED",
    "ACTIVE_REPLAY_INPUT_READY",
    "READY_FOR_REPLAY",
    "REPLAY_READY",
    "BUY_REVIEW_READY",
    "TRADING_READY",
    "APPROVED_FOR_PAPER",
    "PERFORMANCE_VALIDATED",
]
REVIEW_STATUSES = {"blocked", "needs_manual_review", "missing_evidence", "context_only", "no_hit_review_needed"}
CRITICAL_FIELDS = ["source_id", "permission_class", "available_time", "survivorship_rationale", "reviewer_id"]


@dataclass(frozen=True)
class HistoricalReplayPitEvidenceClosureWorklistHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    rows: list[dict[str, str]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def check_historical_replay_pit_evidence_closure_worklist_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path | None = None,
) -> HistoricalReplayPitEvidenceClosureWorklistHealthResult:
    root_path = Path(root)
    out_dir = Path(output_dir) if output_dir is not None else root_path / "health"
    build_historical_replay_pit_evidence_closure_worklist_index(root=root_path, output_dir=out_dir.parent / "index")
    issues: list[dict[str, str]] = []
    candidate_dirs = _candidate_dirs(root_path)
    if not root_path.exists():
        issues.append(_issue("", "WARNING", "ARTIFACT_ROOT_MISSING", "Artifact root is missing.", root_path))
    for artifact_dir in candidate_dirs:
        issues.extend(_issues_for_artifact_dir(artifact_dir))
    finalized = [{column: row.get(column, "") for column in HEALTH_COLUMNS} for row in issues]
    error_count = sum(row["severity"] == "ERROR" for row in finalized)
    warning_count = sum(row["severity"] == "WARNING" for row in finalized)
    status = STATUS_HEALTH_FAIL if error_count else STATUS_HEALTH_WARN if warning_count else STATUS_HEALTH_PASS
    paths = _paths(out_dir)
    result = HistoricalReplayPitEvidenceClosureWorklistHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(finalized),
        error_count=error_count,
        warning_count=warning_count,
        rows=finalized,
        artifact_paths=paths,
        warnings=[] if status == STATUS_HEALTH_PASS else [f"Historical replay PIT evidence closure worklist health is {status}."],
    )
    _write(result)
    return result


def _candidate_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    candidates: set[Path] = set()
    for filename in OUTPUT_FILES.values():
        for path in root.rglob(filename):
            artifact_dir = path.parent
            try:
                relative_parts = artifact_dir.relative_to(root).parts
            except ValueError:
                continue
            if any(part in VIEW_DIR_NAMES or part.startswith("_") for part in relative_parts):
                continue
            candidates.add(artifact_dir)
    return sorted(candidates)


def _issues_for_artifact_dir(artifact_dir: Path) -> list[dict[str, str]]:
    run_id = artifact_dir.name
    issues: list[dict[str, str]] = []
    paths = {key: artifact_dir / filename for key, filename in OUTPUT_FILES.items()}
    for key, path in paths.items():
        if not path.exists():
            issues.append(_issue(run_id, "ERROR", "MISSING_REQUIRED_ARTIFACT", f"Missing required {key}.", path))
    metadata = _read_json(paths["metadata"])
    safety = _read_json(paths["safety_flags"])
    worklist_rows = _read_csv(paths["worklist"]) if paths["worklist"].exists() else []
    if metadata is not None:
        run_id = _text(metadata.get("worklist_run_id") or run_id)
        issues.extend(_metadata_issues(run_id, metadata, paths["metadata"]))
    if safety is not None:
        issues.extend(_safety_issues(run_id, safety, paths["safety_flags"]))
    if worklist_rows:
        issues.extend(_worklist_issues(run_id, worklist_rows, paths["worklist"]))
    if paths["report"].exists():
        issues.extend(_public_text_issues(run_id, paths["report"]))
    if metadata is not None and not worklist_rows and _text(metadata.get("status")).endswith("WARN_NO_CONTEXT"):
        issues.append(_issue(run_id, "WARNING", "NO_CONTEXT_REVIEW_REQUIRED", "Safe no-context worklist requires review.", artifact_dir))
    if worklist_rows and all(_text(row.get("closure_status")) in REVIEW_STATUSES for row in worklist_rows):
        issues.append(_issue(run_id, "WARNING", "REVIEW_REQUIRED_ROWS", "All rows remain blocked or review-required.", paths["worklist"]))
    return issues


def _metadata_issues(run_id: str, metadata: dict[str, Any], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field in SAFETY_FALSE_FIELDS:
        if _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{field} must remain false.", path))
    if _to_bool(metadata.get("pit_admissibility_approved")) and int(metadata.get("closure_ready_not_pit_approved_count", 0) or 0) > 0:
        issues.append(_issue(run_id, "ERROR", "CLOSURE_READY_BECAME_PIT_APPROVED", "closure_ready_not_pit_approved cannot become PIT approval.", path))
    status = _text(metadata.get("status"))
    if any(word in status for word in FORBIDDEN_READINESS_WORDING):
        issues.append(_issue(run_id, "ERROR", "UNSAFE_READINESS_WORDING", "Metadata status contains forbidden readiness wording.", path))
    return issues


def _safety_issues(run_id: str, safety: dict[str, Any], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field in SAFETY_FALSE_FIELDS:
        if _to_bool(safety.get(field)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_SAFETY_FLAG_TRUE", f"{field} must remain false.", path))
    return issues


def _worklist_issues(run_id: str, rows: list[dict[str, str]], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for row in rows:
        symbol = _text(row.get("symbol"))
        closure_status = _text(row.get("closure_status"))
        blocker_status = _text(row.get("blocker_status"))
        if symbol.isdigit() and len(symbol) < 6:
            issues.append(_issue(run_id, "ERROR", "SYMBOL_LEADING_ZERO_LOST", "Symbol appears to have lost leading zeros.", path))
        for field in SAFETY_FALSE_FIELDS:
            if _to_bool(row.get(field)):
                issues.append(_issue(run_id, "ERROR", "FORBIDDEN_ROW_FLAG_TRUE", f"{field} must remain false.", path))
        for field in CRITICAL_FIELDS:
            if _is_missing(row.get(field)) and closure_status not in REVIEW_STATUSES:
                issues.append(_issue(run_id, "ERROR", "ROW_MISSING_FIELD_NOT_BLOCKED", f"{field} is missing but row is not blocked/review-required.", path))
        if _after_decision(row) and closure_status != "blocked":
            issues.append(_issue(run_id, "ERROR", "ROW_AFTER_DECISION_NOT_BLOCKED", "available_time after signal date must block row.", path))
        if (
            _text(row.get("universe_name")) == "etf_core"
            and _text(row.get("instrument_type")) == "STOCK"
            and _text(row.get("profile_conflict_flag")).lower() != "true"
        ):
            issues.append(_issue(run_id, "ERROR", "MIXED_PROFILE_CONFLICT_NOT_FLAGGED", "STOCK row under etf_core must remain profile conflict.", path))
        if closure_status == "closure_ready_not_pit_approved" and "pit" in blocker_status.lower():
            issues.append(_issue(run_id, "ERROR", "CLOSURE_READY_HAS_PIT_BLOCKER", "closure-ready context still carries PIT blocker.", path))
    return issues


def _public_text_issues(run_id: str, path: Path) -> list[dict[str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    issues = []
    for word in FORBIDDEN_READINESS_WORDING:
        if word in text:
            issues.append(_issue(run_id, "ERROR", "UNSAFE_READINESS_WORDING", f"Artifact contains {word}.", path))
    return issues


def _after_decision(row: dict[str, str]) -> bool:
    if _text(row.get("timing_relation_to_decision")) == "after_decision":
        return True
    signal_date = _text(row.get("signal_date"))
    available_time = _text(row.get("available_time"))
    if not signal_date or _is_missing(available_time):
        return False
    try:
        return datetime.fromisoformat(available_time.replace("Z", "+00:00")).date() > date.fromisoformat(signal_date)
    except ValueError:
        return False


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except OSError:
        return []


def _issue(run_id: str, severity: str, code: str, message: str, path: Path) -> dict[str, str]:
    return {
        "worklist_run_id": run_id,
        "status": STATUS_HEALTH_FAIL if severity == "ERROR" else STATUS_HEALTH_WARN,
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }


def _paths(output_dir: Path) -> dict[str, Path]:
    return {
        "artifact_dir": output_dir,
        "health_csv": output_dir / "historical_replay_pit_evidence_closure_worklist_health.csv",
        "health_md": output_dir / "historical_replay_pit_evidence_closure_worklist_health.md",
        "metadata_json": output_dir / "metadata.json",
    }


def _write(result: HistoricalReplayPitEvidenceClosureWorklistHealthResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_csv(result.artifact_paths["health_csv"], HEALTH_COLUMNS, result.rows)
    result.artifact_paths["health_md"].write_text(_render_markdown(result), encoding="utf-8")
    result.artifact_paths["metadata_json"].write_text(
        json.dumps(
            {
                "status": result.status,
                "checked_artifact_count": result.checked_artifact_count,
                "issue_count": result.issue_count,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "warnings": result.warnings,
                "report_only": True,
                "diagnostic_only": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _render_markdown(result: HistoricalReplayPitEvidenceClosureWorklistHealthResult) -> str:
    return "\n".join(
        [
            "# Historical Replay PIT Evidence Closure Worklist Health",
            "",
            f"- Status: `{result.status}`",
            f"- Checked artifact count: `{result.checked_artifact_count}`",
            f"- Error count: `{result.error_count}`",
            f"- Warning count: `{result.warning_count}`",
            "- Report-only health checks; no PIT evidence closure, replay, labels, training, model, buy-review, trading, or protected data-write behavior is created.",
            "",
        ]
    )


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ")[:240]


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _is_missing(value: Any) -> bool:
    return _text(value).strip().lower() in {"", "missing", "none", "nan"}
