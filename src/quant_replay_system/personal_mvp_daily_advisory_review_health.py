"""Health view for Personal MVP daily advisory review report-only artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.personal_mvp_daily_advisory_review import (
    OUTPUT_FILES,
    REQUIRED_FALSE_SAFETY_FIELDS,
    REQUIRED_TRUE_SAFETY_FIELDS,
)
from quant_replay_system.personal_mvp_daily_advisory_review_index import (
    DEFAULT_ROOT,
    build_personal_mvp_daily_advisory_review_index,
)


HEALTH_COLUMNS = ["daily_review_run_id", "status", "severity", "issue_code", "message", "artifact_path"]
SAFE_WARN_STATUSES = {
    "DAILY_ADVISORY_REVIEW_NO_LOCAL_CONTEXT",
    "DAILY_ADVISORY_REVIEW_STALE_CONTEXT_REVIEW_REQUIRED",
    "DAILY_ADVISORY_REVIEW_BLOCKED_CONTEXT_REVIEW_REQUIRED",
}
FORBIDDEN_ACTION_WORDING = ["buy now", "sell now", "place order", "submit order"]
FORBIDDEN_STATUS_WORDING = [
    "BUY_REVIEW_READY",
    "TRADING_READY",
    "READY_FOR_REPLAY",
    "ACTIVE_REPLAY_INPUT_READY",
    "APPROVED_FOR_PAPER",
    "PACKAGE_APPROVED",
    "PERFORMANCE_VALIDATED",
]


@dataclass(frozen=True)
class PersonalMvpDailyAdvisoryReviewHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    rows: list[dict[str, str]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def check_personal_mvp_daily_advisory_review_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path | None = None,
) -> PersonalMvpDailyAdvisoryReviewHealthResult:
    root_path = Path(root)
    out_dir = Path(output_dir) if output_dir is not None else root_path / "health"
    index = build_personal_mvp_daily_advisory_review_index(root=root_path, output_dir=out_dir.parent / "index")
    issues: list[dict[str, str]] = []
    if not root_path.exists():
        issues.append(_issue("", "WARNING", "ARTIFACT_ROOT_MISSING", "Artifact root is missing.", root_path))
    for row in index.rows:
        issues.extend(_issues_for_index_row(row))
    finalized = [_finalize_row(row) for row in issues]
    error_count = sum(1 for row in finalized if row["severity"] == "ERROR")
    warning_count = sum(1 for row in finalized if row["severity"] == "WARNING")
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = _paths(out_dir)
    result = PersonalMvpDailyAdvisoryReviewHealthResult(
        status=status,
        checked_artifact_count=index.artifact_count,
        issue_count=len(finalized),
        error_count=error_count,
        warning_count=warning_count,
        rows=finalized,
        artifact_paths=paths,
        warnings=[] if status == "PASS" else [f"Personal MVP daily advisory review health is {status}."],
    )
    _write(result)
    return result


def _issues_for_index_row(row: dict[str, Any]) -> list[dict[str, str]]:
    run_id = _text(row.get("daily_review_run_id"))
    artifact_dir = Path(_text(row.get("artifact_path")))
    issues: list[dict[str, str]] = []
    paths = {key: artifact_dir / filename for key, filename in OUTPUT_FILES.items()}
    for key, path in paths.items():
        if not path.exists():
            issues.append(_issue(run_id, "ERROR", "MISSING_REQUIRED_ARTIFACT", f"Missing required {key}.", path))
    metadata = _read_json(paths["metadata"])
    safety = _read_json(paths["safety_flags"])
    if metadata is not None:
        issues.extend(_metadata_issues(run_id, metadata, paths["metadata"]))
    if safety is not None:
        issues.extend(_safety_issues(run_id, safety, paths["safety_flags"]))
    if paths["daily_advisory_review_rows"].exists():
        issues.extend(_row_csv_issues(run_id, paths["daily_advisory_review_rows"]))
    for key in ("daily_advisory_review_report", "daily_advisory_review_summary", "single_symbol_drilldown_index", "manual_review_checklist"):
        path = paths[key]
        if path.exists():
            issues.extend(_public_text_issues(run_id, path))
    return issues


def _metadata_issues(run_id: str, metadata: dict[str, Any], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    status = _text(metadata.get("status"))
    health_status = _text(metadata.get("health_status"))
    for field in REQUIRED_TRUE_SAFETY_FIELDS:
        if not _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "REQUIRED_METADATA_FLAG_FALSE", f"{field} must be true.", path))
    for field in REQUIRED_FALSE_SAFETY_FIELDS:
        if _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{field} must be false.", path))
    if any(word in status for word in FORBIDDEN_STATUS_WORDING):
        issues.append(_issue(run_id, "ERROR", "UNSAFE_STATUS_WORDING", "Status contains forbidden readiness wording.", path))
    if health_status == "FAIL":
        issues.append(_issue(run_id, "ERROR", "CORE_HEALTH_FAILED", "Core artifact health_status is FAIL.", path))
    if health_status == "WARN" or status in SAFE_WARN_STATUSES:
        issues.append(_issue(run_id, "WARNING", "REVIEW_CONTEXT_WARNING", "Artifact requires manual review context.", path))
    return issues


def _safety_issues(run_id: str, safety: dict[str, Any], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field in REQUIRED_TRUE_SAFETY_FIELDS:
        if not _to_bool(safety.get(field)):
            issues.append(_issue(run_id, "ERROR", "REQUIRED_SAFETY_FLAG_FALSE", f"{field} must be true.", path))
    for field in REQUIRED_FALSE_SAFETY_FIELDS:
        if _to_bool(safety.get(field)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_SAFETY_FLAG_TRUE", f"{field} must be false.", path))
    return issues


def _row_csv_issues(run_id: str, path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError:
        return issues
    for row in rows:
        symbol = _text(row.get("symbol"))
        if symbol and symbol.isdigit() and len(symbol) < 6:
            issues.append(_issue(run_id, "ERROR", "SYMBOL_LEADING_ZERO_LOST", "Symbol appears to have lost leading zeros.", path))
        for field in ("auto_order_allowed",):
            if _to_bool(row.get(field)):
                issues.append(_issue(run_id, "ERROR", "UNSAFE_ROW_FLAG_TRUE", f"{field} must be false.", path))
    return issues


def _public_text_issues(run_id: str, path: Path) -> list[dict[str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    lowered = text.lower()
    issues: list[dict[str, str]] = []
    if any(phrase in lowered for phrase in FORBIDDEN_ACTION_WORDING):
        issues.append(_issue(run_id, "ERROR", "UNSAFE_ACTION_WORDING", "Artifact contains command-like action wording.", path))
    if any(word in text for word in FORBIDDEN_STATUS_WORDING):
        issues.append(_issue(run_id, "ERROR", "UNSAFE_STATUS_WORDING", "Artifact contains forbidden readiness wording.", path))
    return issues


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _issue(run_id: str, severity: str, code: str, message: str, path: Path) -> dict[str, str]:
    return {
        "daily_review_run_id": run_id,
        "status": "FAIL" if severity == "ERROR" else "WARN",
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }


def _paths(output_dir: Path) -> dict[str, Path]:
    return {
        "artifact_dir": output_dir,
        "health_csv": output_dir / "personal_mvp_daily_advisory_review_health.csv",
        "health_md": output_dir / "personal_mvp_daily_advisory_review_health.md",
        "metadata_json": output_dir / "metadata.json",
    }


def _write(result: PersonalMvpDailyAdvisoryReviewHealthResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_rows(result.artifact_paths["health_csv"], HEALTH_COLUMNS, result.rows)
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


def _render_markdown(result: PersonalMvpDailyAdvisoryReviewHealthResult) -> str:
    return "\n".join(
        [
            "# Personal MVP Daily Advisory Review Health",
            "",
            f"- Status: `{result.status}`",
            f"- Checked artifact count: `{result.checked_artifact_count}`",
            f"- Error count: `{result.error_count}`",
            f"- Warning count: `{result.warning_count}`",
            "- Health checks are report-only and do not create buy-review, trading, broker, order, message, replay, labels, training, model, stock_profile, or protected data-write behavior.",
            "",
        ]
    )


def _write_rows(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _finalize_row(row: dict[str, str]) -> dict[str, str]:
    return {column: row.get(column, "") for column in HEALTH_COLUMNS}


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
