"""Health view for official status evidence packet closure worklist artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.historical_replay_official_status_evidence_packet_closure_worklist import (
    OUTPUT_FILES,
    SAFETY_FALSE_FIELDS,
)
from quant_replay_system.historical_replay_official_status_evidence_packet_closure_worklist_index import (
    DEFAULT_ROOT,
    VIEW_DIR_NAMES,
    build_historical_replay_official_status_evidence_packet_closure_worklist_index,
)


STATUS_HEALTH_PASS = "OFFICIAL_STATUS_EVIDENCE_PACKET_CLOSURE_WORKLIST_HEALTH_PASS_REPORT_ONLY"
STATUS_HEALTH_WARN = "OFFICIAL_STATUS_EVIDENCE_PACKET_CLOSURE_WORKLIST_HEALTH_WARN_REVIEW_REQUIRED"
STATUS_HEALTH_FAIL = "OFFICIAL_STATUS_EVIDENCE_PACKET_CLOSURE_WORKLIST_HEALTH_FAIL_UNSAFE"

HEALTH_COLUMNS = ["packet_worklist_run_id", "status", "severity", "issue_code", "message", "artifact_path"]
EXPECTED_SYMBOLS = ["000001", "000002", "159915", "300750", "510300", "600000", "600519", "601318", "688981"]
EXPECTED_STOCK_SYMBOLS = {"000001", "000002", "300750", "600000", "600519", "601318", "688981"}
EXPECTED_ETF_SYMBOLS = {"159915", "510300"}
FORBIDDEN_READINESS_WORDING = [
    "PIT_ADMISSIBLE",
    "PIT_APPROVED",
    "READY_FOR_REPLAY",
    "ACTIVE_REPLAY_INPUT_READY",
    "BUY_REVIEW_READY",
    "TRADING_READY",
    "APPROVED_FOR_PAPER",
    "PERFORMANCE_VALIDATED",
]
COMMON_BLOCKERS = [
    "blocker_missing_listed_status_evidence",
    "blocker_missing_delisted_status_evidence",
    "blocker_missing_suspension_or_trading_status",
    "blocker_missing_universe_membership_evidence",
    "blocker_universe_asof_after_signal",
    "blocker_missing_survivorship_rationale",
    "blocker_missing_source_id",
    "blocker_missing_raw_reference",
    "blocker_missing_permission_class",
    "blocker_missing_revision_id",
    "blocker_missing_available_time",
]
REVIEW_STATUSES = {"blocked", "needs_manual_review"}


@dataclass(frozen=True)
class HistoricalReplayOfficialStatusEvidencePacketClosureWorklistHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    rows: list[dict[str, str]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def check_historical_replay_official_status_evidence_packet_closure_worklist_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path | None = None,
) -> HistoricalReplayOfficialStatusEvidencePacketClosureWorklistHealthResult:
    root_path = Path(root)
    out_dir = Path(output_dir) if output_dir is not None else root_path / "health"
    build_historical_replay_official_status_evidence_packet_closure_worklist_index(
        root=root_path, output_dir=out_dir.parent / "index"
    )

    issues: list[dict[str, str]] = []
    candidate_dirs = _candidate_dirs(root_path)
    if not root_path.exists():
        issues.append(_issue("", "WARNING", "ARTIFACT_ROOT_MISSING", "Artifact root is missing.", root_path))
    for artifact_dir in candidate_dirs:
        issues.extend(_issues_for_artifact_dir(artifact_dir))

    rows = [{column: row.get(column, "") for column in HEALTH_COLUMNS} for row in issues]
    error_count = sum(row["severity"] == "ERROR" for row in rows)
    warning_count = sum(row["severity"] == "WARNING" for row in rows)
    status = STATUS_HEALTH_FAIL if error_count else STATUS_HEALTH_WARN if warning_count else STATUS_HEALTH_PASS
    paths = _paths(out_dir)
    result = HistoricalReplayOfficialStatusEvidencePacketClosureWorklistHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(rows),
        error_count=error_count,
        warning_count=warning_count,
        rows=rows,
        artifact_paths=paths,
        warnings=[] if status == STATUS_HEALTH_PASS else [f"Official status worklist health is {status}."],
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
    paths = {key: artifact_dir / filename for key, filename in OUTPUT_FILES.items()}
    issues: list[dict[str, str]] = []
    for key, path in paths.items():
        if not path.exists():
            issues.append(_issue(run_id, "ERROR", "MISSING_REQUIRED_ARTIFACT", f"Missing required {key}.", path))

    metadata = _read_json(paths["metadata"])
    safety = _read_json(paths["safety_flags"])
    rows = _read_csv(paths["worklist"]) if paths["worklist"].exists() else []
    if metadata is not None:
        run_id = _text(metadata.get("packet_worklist_run_id") or run_id)
        issues.extend(_metadata_issues(run_id, metadata, rows, paths["metadata"]))
    if safety is not None:
        issues.extend(_safety_issues(run_id, safety, paths["safety_flags"]))
    if rows:
        issues.extend(_worklist_issues(run_id, rows, paths["worklist"]))
    if paths["report"].exists():
        issues.extend(_public_text_issues(run_id, paths["report"]))
    if rows and all(_text(row.get("closure_status")) in REVIEW_STATUSES for row in rows):
        issues.append(_issue(run_id, "WARNING", "ALL_ROWS_REVIEW_REQUIRED", "All rows remain blocked or review-required.", paths["worklist"]))
    return issues


def _metadata_issues(run_id: str, metadata: dict[str, Any], rows: list[dict[str, str]], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field in SAFETY_FALSE_FIELDS:
        if _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{field} must remain false.", path))
    if _int(metadata.get("row_count")) != 9 or (rows and len(rows) != 9):
        issues.append(_issue(run_id, "ERROR", "ROW_COUNT_MISMATCH", "Selected sample row count must be exactly 9.", path))
    stock_count = sum(_text(row.get("instrument_type")) == "STOCK" for row in rows)
    etf_count = sum(_text(row.get("instrument_type")) == "ETF" for row in rows)
    if _int(metadata.get("stock_row_count")) != 7 or _int(metadata.get("etf_row_count")) != 2:
        issues.append(_issue(run_id, "ERROR", "INSTRUMENT_COUNT_MISMATCH", "Metadata STOCK/ETF counts must be 7/2.", path))
    if rows and (stock_count != 7 or etf_count != 2):
        issues.append(_issue(run_id, "ERROR", "INSTRUMENT_COUNT_MISMATCH", "Worklist STOCK/ETF counts must be 7/2.", path))
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
    symbols = [_text(row.get("symbol")) for row in rows]
    if symbols != EXPECTED_SYMBOLS:
        issues.append(_issue(run_id, "ERROR", "SYMBOL_SET_MISMATCH", "Selected sample symbol set/order must be exact.", path))
    for symbol in symbols:
        if symbol.isdigit() and len(symbol) < 6:
            issues.append(_issue(run_id, "ERROR", "SYMBOL_LEADING_ZERO_LOST", "Symbol appears to have lost leading zeros.", path))
    for row in rows:
        symbol = _text(row.get("symbol"))
        blockers = set(filter(None, _text(row.get("blocker_reason")).split(";")))
        for field in SAFETY_FALSE_FIELDS:
            if _to_bool(row.get(field)):
                issues.append(_issue(run_id, "ERROR", "FORBIDDEN_ROW_FLAG_TRUE", f"{field} must remain false.", path))
        if symbol in EXPECTED_STOCK_SYMBOLS and _text(row.get("profile_conflict_flag")).lower() != "true":
            issues.append(_issue(run_id, "ERROR", "STOCK_PROFILE_CONFLICT_NOT_FLAGGED", "STOCK rows under etf_core must remain profile-conflict context.", path))
        if symbol in EXPECTED_ETF_SYMBOLS and _text(row.get("profile_conflict_flag")).lower() == "true":
            issues.append(_issue(run_id, "ERROR", "ETF_PROFILE_CONFLICT_FLAGGED", "ETF rows must not be marked as profile conflicts.", path))
        if symbol in EXPECTED_STOCK_SYMBOLS and "blocker_missing_st_status_evidence" not in blockers:
            issues.append(_issue(run_id, "ERROR", "MISSING_STOCK_ST_BLOCKER", "STOCK rows require missing ST evidence blocker.", path))
        if symbol in EXPECTED_ETF_SYMBOLS and "blocker_missing_st_not_applicable_policy" not in blockers:
            issues.append(_issue(run_id, "ERROR", "MISSING_ETF_ST_POLICY_BLOCKER", "ETF rows require ST not-applicable policy blocker.", path))
        missing_common = [blocker for blocker in COMMON_BLOCKERS if blocker not in blockers]
        if missing_common:
            issues.append(_issue(run_id, "ERROR", "MISSING_COMMON_BLOCKER", f"Missing common blockers: {';'.join(missing_common)}", path))
        if _text(row.get("closure_status")) not in REVIEW_STATUSES:
            issues.append(_issue(run_id, "ERROR", "UNSAFE_CLOSURE_STATUS", "Default rows must remain blocked or needs-review.", path))
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
        "packet_worklist_run_id": run_id,
        "status": STATUS_HEALTH_FAIL if severity == "ERROR" else STATUS_HEALTH_WARN,
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }


def _paths(output_dir: Path) -> dict[str, Path]:
    return {
        "artifact_dir": output_dir,
        "health_csv": output_dir / "historical_replay_official_status_evidence_packet_closure_worklist_health.csv",
        "health_md": output_dir / "historical_replay_official_status_evidence_packet_closure_worklist_health.md",
        "metadata_json": output_dir / "metadata.json",
    }


def _write(result: HistoricalReplayOfficialStatusEvidencePacketClosureWorklistHealthResult) -> None:
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


def _render_markdown(result: HistoricalReplayOfficialStatusEvidencePacketClosureWorklistHealthResult) -> str:
    return "\n".join(
        [
            "# Historical Replay Official Status Evidence Packet Closure Worklist Health",
            "",
            f"- Status: `{result.status}`",
            f"- Checked artifact count: `{result.checked_artifact_count}`",
            f"- Error count: `{result.error_count}`",
            f"- Warning count: `{result.warning_count}`",
            "- Report-only health checks; no official evidence closure, PIT approval, replay, labels, training, model, buy-review, trading, or protected data-write behavior is created.",
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
    return str(value).replace("\n", " ")


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
