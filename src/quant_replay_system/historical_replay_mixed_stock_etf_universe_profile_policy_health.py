"""Health view for mixed STOCK/ETF universe profile policy artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.historical_replay_mixed_stock_etf_universe_profile_policy import (
    BLOCKER_VOCABULARY,
    OUTPUT_FILES,
    SAFETY_FALSE_FIELDS,
    STATUS_VOCABULARY,
)
from quant_replay_system.historical_replay_mixed_stock_etf_universe_profile_policy_index import (
    DEFAULT_ROOT,
    VIEW_DIR_NAMES,
    build_historical_replay_mixed_stock_etf_universe_profile_policy_index,
)


STATUS_HEALTH_PASS = "MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_HEALTH_PASS_REPORT_ONLY"
STATUS_HEALTH_FAIL = "MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_HEALTH_FAIL_UNSAFE"
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
ROW_FALSE_FIELDS = [
    "profile_policy_no_hit_override_allowed",
    "profile_policy_pit_approval_allowed",
    "profile_policy_replay_readiness_allowed",
    "profile_policy_buy_review_allowed",
    "profile_policy_trading_allowed",
    "no_hit_context_can_resolve_profile_conflict",
    "legacy_universe_label_is_universe_proof",
    "recommended_profile_is_stock_profile_validation",
    "same_day_quote_is_official_status_proof",
    "forward_return_used_in_decision_context",
    "universe_membership_approved",
    "official_status_evidence_accepted",
    "profile_conflict_resolved",
    "stock_profile_validated",
    "pit_admissibility_approved",
    "active_replay_input",
    "replay_execution_allowed",
    "buy_review_allowed",
    "trading_allowed",
]


@dataclass(frozen=True)
class HistoricalReplayMixedStockEtfUniverseProfilePolicyHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    rows: list[dict[str, str]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def check_historical_replay_mixed_stock_etf_universe_profile_policy_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path | None = None,
) -> HistoricalReplayMixedStockEtfUniverseProfilePolicyHealthResult:
    root_path = Path(root)
    out_dir = Path(output_dir) if output_dir is not None else root_path / "health"
    build_historical_replay_mixed_stock_etf_universe_profile_policy_index(
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
    status = STATUS_HEALTH_FAIL if error_count else STATUS_HEALTH_PASS
    paths = _paths(out_dir)
    result = HistoricalReplayMixedStockEtfUniverseProfilePolicyHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(rows),
        error_count=error_count,
        warning_count=warning_count,
        rows=rows,
        artifact_paths=paths,
        warnings=[] if status == STATUS_HEALTH_PASS else [f"Mixed profile policy fixture health is {status}."],
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
    rows = _read_csv(paths["policy_rows"]) if paths["policy_rows"].exists() else []
    if metadata is not None:
        run_id = _text(metadata.get("run_id") or run_id)
        issues.extend(_metadata_issues(run_id, metadata, rows, paths["metadata"]))
    if safety is not None:
        issues.extend(_safety_issues(run_id, safety, paths["safety_flags"]))
    issues.extend(_row_issues(run_id, rows, paths["policy_rows"]))
    issues.extend(_vocabulary_issues(run_id, paths["status_vocabulary"], paths["blocker_vocabulary"]))
    if paths["report"].exists():
        issues.extend(_public_text_issues(run_id, paths["report"]))
    return issues


def _metadata_issues(
    run_id: str,
    metadata: dict[str, Any],
    rows: list[dict[str, str]],
    path: Path,
) -> list[dict[str, str]]:
    checks = [
        ("row_count", 9, "ROW_COUNT_MISMATCH"),
        ("stock_row_count", 7, "INSTRUMENT_COUNT_MISMATCH"),
        ("etf_row_count", 2, "INSTRUMENT_COUNT_MISMATCH"),
        ("profile_conflict_count", 7, "PROFILE_CONFLICT_COUNT_MISMATCH"),
        ("profile_aligned_context_count", 2, "PROFILE_ALIGNED_COUNT_MISMATCH"),
        ("unresolved_profile_conflict_count", 7, "UNRESOLVED_PROFILE_CONFLICT_COUNT_MISMATCH"),
        ("profile_policy_accepted_count", 0, "PROFILE_POLICY_ACCEPTED_COUNT_MISMATCH"),
        ("no_hit_row_count", 9, "NO_HIT_ROW_COUNT_MISMATCH"),
        ("not_accepted_count", 9, "NOT_ACCEPTED_COUNT_MISMATCH"),
        ("accepted_context_count", 0, "ACCEPTED_CONTEXT_COUNT_MISMATCH"),
        ("universe_membership_approved_count", 0, "UNIVERSE_MEMBERSHIP_APPROVED_COUNT_MISMATCH"),
        ("official_status_evidence_accepted_count", 0, "OFFICIAL_STATUS_EVIDENCE_ACCEPTED_COUNT_MISMATCH"),
        ("row_with_blocker_count", 9, "ROW_WITH_BLOCKER_COUNT_MISMATCH"),
        ("survivorship_warning_count", 9, "SURVIVORSHIP_WARNING_COUNT_MISMATCH"),
        ("safety_true_count", 0, "SAFETY_TRUE_COUNT_MISMATCH"),
    ]
    issues = [
        _issue(run_id, "ERROR", code, f"{field} must be {expected}.", path)
        for field, expected, code in checks
        if _int(metadata.get(field)) != expected
    ]
    if rows and len(rows) != 9:
        issues.append(_issue(run_id, "ERROR", "ROW_COUNT_MISMATCH", "Policy row count must be 9.", path))
    for field in SAFETY_FALSE_FIELDS:
        if _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{field} must remain false.", path))
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


def _row_issues(run_id: str, rows: list[dict[str, str]], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    symbols = [_text(row.get("selected_symbol")) for row in rows]
    if rows and symbols != EXPECTED_SYMBOLS:
        issues.append(_issue(run_id, "ERROR", "SYMBOL_SET_MISMATCH", "Selected sample symbol set/order must be exact.", path))
    for row in rows:
        symbol = _text(row.get("selected_symbol"))
        instrument_type = _text(row.get("instrument_type"))
        if symbol.isdigit() and len(symbol) < 6:
            issues.append(_issue(run_id, "ERROR", "SYMBOL_LEADING_ZERO_LOST", "Symbol appears to have lost leading zeros.", path))
        if not _text(row.get("blocker_reason")):
            issues.append(_issue(run_id, "ERROR", "PROFILE_POLICY_BLOCKERS_MISSING", "Rows must keep profile-policy blocker reasons visible.", path))
        if instrument_type == "STOCK" and (
            _text(row.get("profile_conflict")) != "true"
            or _text(row.get("profile_policy_status")) != "unresolved_profile_conflict"
        ):
            issues.append(_issue(run_id, "ERROR", "PROFILE_CONFLICT_VISIBILITY_MISMATCH", "STOCK rows must keep unresolved profile conflict visible.", path))
        if instrument_type == "ETF" and (
            _text(row.get("profile_conflict")) != "false"
            or _text(row.get("profile_policy_status")) != "profile_aligned_context_only_not_universe_proof"
        ):
            issues.append(_issue(run_id, "ERROR", "PROFILE_ALIGNED_CONTEXT_MISMATCH", "ETF rows must remain aligned context only.", path))
        if _text(row.get("profile_policy_status")) == "accepted_for_policy_context_only_not_pit_approved":
            issues.append(_issue(run_id, "ERROR", "PROFILE_POLICY_ACCEPTED_UNSAFE", "Current selected rows must not be accepted.", path))
        for field in ROW_FALSE_FIELDS:
            if _to_bool(row.get(field)):
                issues.append(_issue(run_id, "ERROR", "FORBIDDEN_ROW_FLAG_TRUE", f"{field} must remain false.", path))
    return issues


def _vocabulary_issues(run_id: str, status_path: Path, blocker_path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    statuses = {row.get("status", "") for row in _read_csv(status_path)}
    blockers = {row.get("blocker", "") for row in _read_csv(blocker_path)}
    if statuses and statuses != set(STATUS_VOCABULARY):
        issues.append(_issue(run_id, "ERROR", "STATUS_VOCABULARY_MISMATCH", "Status vocabulary must match contract.", status_path))
    if blockers and blockers != set(BLOCKER_VOCABULARY):
        issues.append(_issue(run_id, "ERROR", "BLOCKER_VOCABULARY_MISMATCH", "Blocker vocabulary must match contract.", blocker_path))
    for path in [status_path, blocker_path]:
        for row in _read_csv(path):
            text = " ".join(str(value) for value in row.values())
            if any(word in text for word in FORBIDDEN_READINESS_WORDING):
                issues.append(_issue(run_id, "ERROR", "UNSAFE_READINESS_WORDING", f"Vocabulary contains forbidden readiness wording.", path))
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


def _paths(output_dir: Path) -> dict[str, Path]:
    return {
        "artifact_dir": output_dir,
        "health_csv": output_dir / "historical_replay_mixed_stock_etf_universe_profile_policy_health.csv",
        "health_md": output_dir / "historical_replay_mixed_stock_etf_universe_profile_policy_health.md",
        "metadata_json": output_dir / "metadata.json",
    }


def _write(result: HistoricalReplayMixedStockEtfUniverseProfilePolicyHealthResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    with result.artifact_paths["health_csv"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEALTH_COLUMNS)
        writer.writeheader()
        writer.writerows(result.rows)
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


def _render_markdown(result: HistoricalReplayMixedStockEtfUniverseProfilePolicyHealthResult) -> str:
    return "\n".join(
        [
            "# Historical Replay Mixed STOCK/ETF Universe Profile Policy Health",
            "",
            f"- Status: `{result.status}`",
            f"- Checked artifact count: `{result.checked_artifact_count}`",
            f"- Issue count: `{result.issue_count}`",
            "- Report-only health; no profile conflict resolution, universe membership approval, stock_profile validation, evidence acceptance, PIT approval, replay, buy-review, trading, or protected data-write behavior is authorized.",
            "",
        ]
    )


def _issue(run_id: str, severity: str, code: str, message: str, path: Path) -> dict[str, str]:
    return {
        "run_id": run_id,
        "status": STATUS_HEALTH_FAIL if severity == "ERROR" else STATUS_HEALTH_PASS,
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }


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


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)
