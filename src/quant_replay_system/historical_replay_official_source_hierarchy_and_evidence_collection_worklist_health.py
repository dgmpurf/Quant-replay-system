"""Health view for official source hierarchy worklist artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.historical_replay_official_source_hierarchy_and_evidence_collection_worklist import (
    OUTPUT_FILES,
    SAFETY_FALSE_FIELDS,
)
from quant_replay_system.historical_replay_official_source_hierarchy_and_evidence_collection_worklist_index import (
    DEFAULT_ROOT,
    VIEW_DIR_NAMES,
    build_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_index,
)


STATUS_HEALTH_PASS = "OFFICIAL_SOURCE_HIERARCHY_WORKLIST_HEALTH_PASS_REPORT_ONLY"
STATUS_HEALTH_WARN = "OFFICIAL_SOURCE_HIERARCHY_WORKLIST_HEALTH_WARN_REVIEW_REQUIRED"
STATUS_HEALTH_FAIL = "OFFICIAL_SOURCE_HIERARCHY_WORKLIST_HEALTH_FAIL_UNSAFE"

HEALTH_COLUMNS = ["run_id", "status", "severity", "issue_code", "message", "artifact_path"]
EXPECTED_SYMBOLS = ["000001", "000002", "159915", "300750", "510300", "600000", "600519", "601318", "688981"]
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
    "blocker_missing_source_class",
    "blocker_missing_source_id",
    "blocker_missing_raw_reference",
    "blocker_missing_permission_class",
    "blocker_missing_revision_id",
    "blocker_missing_available_time",
    "blocker_missing_timezone_policy",
    "blocker_missing_quality_status",
    "blocker_missing_limitation_note",
    "blocker_missing_survivorship_rationale",
]


@dataclass(frozen=True)
class HistoricalReplayOfficialSourceHierarchyWorklistHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    rows: list[dict[str, str]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def check_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path | None = None,
) -> HistoricalReplayOfficialSourceHierarchyWorklistHealthResult:
    root_path = Path(root)
    out_dir = Path(output_dir) if output_dir is not None else root_path / "health"
    build_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_index(
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
    result = HistoricalReplayOfficialSourceHierarchyWorklistHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(rows),
        error_count=error_count,
        warning_count=warning_count,
        rows=rows,
        artifact_paths=paths,
        warnings=[] if status == STATUS_HEALTH_PASS else [f"Official source hierarchy worklist health is {status}."],
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
    worklist = _read_csv(paths["worklist"]) if paths["worklist"].exists() else []
    source_classes = _read_csv(paths["source_hierarchy_matrix"]) if paths["source_hierarchy_matrix"].exists() else []
    families = _read_csv(paths["evidence_family_requirement_matrix"]) if paths["evidence_family_requirement_matrix"].exists() else []
    no_hit = _read_csv(paths["no_hit_handoff_matrix"]) if paths["no_hit_handoff_matrix"].exists() else []

    if metadata is not None:
        run_id = _text(metadata.get("run_id") or run_id)
        issues.extend(_metadata_issues(run_id, metadata, worklist, source_classes, families, no_hit, paths["metadata"]))
    if safety is not None:
        issues.extend(_safety_issues(run_id, safety, paths["safety_flags"]))
    if worklist:
        issues.extend(_worklist_issues(run_id, worklist, paths["worklist"]))
    if no_hit:
        issues.extend(_no_hit_issues(run_id, no_hit, paths["no_hit_handoff_matrix"]))
    if paths["report"].exists():
        issues.extend(_public_text_issues(run_id, paths["report"]))
    if worklist and all(_text(row.get("closure_status")) == "blocked" for row in worklist):
        issues.append(_issue(run_id, "WARNING", "ALL_ROWS_REVIEW_REQUIRED", "All rows remain blocked or review-required.", paths["worklist"]))
    return issues


def _metadata_issues(
    run_id: str,
    metadata: dict[str, Any],
    worklist: list[dict[str, str]],
    source_classes: list[dict[str, str]],
    families: list[dict[str, str]],
    no_hit: list[dict[str, str]],
    path: Path,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field in SAFETY_FALSE_FIELDS:
        if _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{field} must remain false.", path))
    if _int(metadata.get("row_count")) != 9:
        issues.append(_issue(run_id, "ERROR", "ROW_COUNT_MISMATCH", "Selected sample row count must be exactly 9.", path))
    if _int(metadata.get("stock_row_count")) != 7 or _int(metadata.get("etf_row_count")) != 2:
        issues.append(_issue(run_id, "ERROR", "INSTRUMENT_COUNT_MISMATCH", "Metadata STOCK/ETF counts must be 7/2.", path))
    if _int(metadata.get("source_class_count")) != 7 or (source_classes and len(source_classes) != 7):
        issues.append(_issue(run_id, "ERROR", "SOURCE_CLASS_COUNT_MISMATCH", "Source class count must be 7.", path))
    if _int(metadata.get("evidence_family_count")) != 9 or (families and len(families) != 9):
        issues.append(_issue(run_id, "ERROR", "EVIDENCE_FAMILY_COUNT_MISMATCH", "Evidence family count must be 9.", path))
    if _int(metadata.get("evidence_collection_worklist_row_count")) != 72 or (worklist and len(worklist) != 72):
        issues.append(_issue(run_id, "ERROR", "WORKLIST_ROW_COUNT_MISMATCH", "Evidence collection worklist rows must be 72.", path))
    if _int(metadata.get("no_hit_handoff_row_count")) != 9 or (no_hit and len(no_hit) != 9):
        issues.append(_issue(run_id, "ERROR", "NO_HIT_COUNT_MISMATCH", "No-hit handoff row count must be 9.", path))
    if _int(metadata.get("blocked_count")) != 72:
        issues.append(_issue(run_id, "ERROR", "BLOCKED_COUNT_MISMATCH", "Blocked count must remain 72.", path))
    if _int(metadata.get("profile_conflict_count")) != 7:
        issues.append(_issue(run_id, "ERROR", "PROFILE_CONFLICT_COUNT_MISMATCH", "Profile conflict count must be 7.", path))
    if _int(metadata.get("survivorship_warning_count")) != 9:
        issues.append(_issue(run_id, "ERROR", "SURVIVORSHIP_COUNT_MISMATCH", "Survivorship warning count must be 9.", path))
    status_text = " ".join(_text(metadata.get(key)) for key in ("runtime_status", "workflow_stage", "health_status"))
    if any(word in status_text for word in FORBIDDEN_READINESS_WORDING):
        issues.append(_issue(run_id, "ERROR", "UNSAFE_READINESS_WORDING", "Metadata contains forbidden readiness wording.", path))
    return issues


def _safety_issues(run_id: str, safety: dict[str, Any], path: Path) -> list[dict[str, str]]:
    return [
        _issue(run_id, "ERROR", "FORBIDDEN_SAFETY_FLAG_TRUE", f"{field} must remain false.", path)
        for field in SAFETY_FALSE_FIELDS
        if _to_bool(safety.get(field))
    ]


def _worklist_issues(run_id: str, rows: list[dict[str, str]], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    symbols = list(dict.fromkeys(_text(row.get("symbol")) for row in rows))
    if symbols != EXPECTED_SYMBOLS:
        issues.append(_issue(run_id, "ERROR", "SYMBOL_SET_MISMATCH", "Selected sample symbol set/order must be exact.", path))
    for symbol in symbols:
        if symbol.isdigit() and len(symbol) < 6:
            issues.append(_issue(run_id, "ERROR", "SYMBOL_LEADING_ZERO_LOST", "Symbol appears to have lost leading zeros.", path))
    for row in rows:
        blockers = set(filter(None, _text(row.get("blocker_reason")).split(";")))
        for field in SAFETY_FALSE_FIELDS:
            if _to_bool(row.get(field)):
                issues.append(_issue(run_id, "ERROR", "FORBIDDEN_ROW_FLAG_TRUE", f"{field} must remain false.", path))
        missing_common = [blocker for blocker in COMMON_BLOCKERS if blocker not in blockers]
        if missing_common:
            issues.append(_issue(run_id, "ERROR", "MISSING_COMMON_BLOCKER", f"Missing common blockers: {';'.join(missing_common)}", path))
        if _text(row.get("instrument_type")) == "STOCK" and _text(row.get("evidence_family")) == "st_no_st_status":
            if "blocker_missing_stock_st_source" not in blockers:
                issues.append(_issue(run_id, "ERROR", "MISSING_STOCK_ST_BLOCKER", "STOCK rows require ST source blocker.", path))
        if _text(row.get("instrument_type")) == "ETF" and _text(row.get("evidence_family")) == "etf_st_not_applicable_policy":
            if "blocker_missing_etf_st_not_applicable_policy" not in blockers:
                issues.append(_issue(run_id, "ERROR", "MISSING_ETF_ST_POLICY_BLOCKER", "ETF rows require ST not-applicable policy blocker.", path))
        if _text(row.get("closure_status")) != "blocked":
            issues.append(_issue(run_id, "ERROR", "UNSAFE_CLOSURE_STATUS", "Default rows must remain blocked.", path))
    return issues


def _no_hit_issues(run_id: str, rows: list[dict[str, str]], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for row in rows:
        if _text(row.get("no_hit_acceptance_status")) != "not_accepted":
            issues.append(_issue(run_id, "ERROR", "NO_HIT_ACCEPTED_UNSAFE", "No-hit context must remain not accepted.", path))
        if _text(row.get("no_hit_review_needed")) != "true":
            issues.append(_issue(run_id, "ERROR", "NO_HIT_REVIEW_NOT_REQUIRED", "No-hit review must remain required.", path))
    return issues


def _public_text_issues(run_id: str, path: Path) -> list[dict[str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    return [
        _issue(run_id, "ERROR", "UNSAFE_READINESS_WORDING", f"Artifact contains {word}.", path)
        for word in FORBIDDEN_READINESS_WORDING
        if word in text
    ]


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
        "run_id": run_id,
        "status": STATUS_HEALTH_FAIL if severity == "ERROR" else STATUS_HEALTH_WARN,
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }


def _paths(output_dir: Path) -> dict[str, Path]:
    return {
        "artifact_dir": output_dir,
        "health_csv": output_dir
        / "historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health.csv",
        "health_md": output_dir
        / "historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health.md",
        "metadata_json": output_dir / "metadata.json",
    }


def _write(result: HistoricalReplayOfficialSourceHierarchyWorklistHealthResult) -> None:
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


def _render_markdown(result: HistoricalReplayOfficialSourceHierarchyWorklistHealthResult) -> str:
    return "\n".join(
        [
            "# Historical Replay Official Source Hierarchy and Evidence Collection Worklist Health",
            "",
            f"- Status: `{result.status}`",
            f"- Checked artifact count: `{result.checked_artifact_count}`",
            f"- Error count: `{result.error_count}`",
            f"- Warning count: `{result.warning_count}`",
            "- Report-only health checks; no official evidence collection, evidence closure, PIT approval, replay, labels, training, model, buy-review, trading, or protected data-write behavior is created.",
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
