"""Health checks for report-only Operational Global APPROVED_FOR_PAPER planning artifacts."""

from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.operational_global_approved_for_paper import (
    ARTIFACT_FILES,
    BLOCKED_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER,
    INVALID_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT,
    NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT,
    OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED,
    READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW,
)
from quant_replay_system.operational_global_approved_for_paper_index import (
    CORE_FALSE_FIELDS,
    DEFAULT_ROOT,
    DOWNSTREAM_FALSE_FIELDS,
    _frame_to_markdown,
    _read_json,
    _text,
    _to_bool,
    build_operational_global_approved_for_paper_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"

HEALTH_COLUMNS = ["operational_global_approved_for_paper_id", "severity", "issue_code", "message", "artifact_path"]

ALLOWED_STATUSES = {
    NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT,
    READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW,
    OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED,
    BLOCKED_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER,
    INVALID_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT,
}

ALWAYS_REQUIRED_ARTIFACT_KEYS = {
    "operational_global_approved_for_paper_metadata": "MISSING_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_METADATA",
    "operational_global_approved_for_paper_health_gate_results": "MISSING_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_HEALTH_GATE_RESULTS",
    "operational_global_approved_for_paper_forbidden_output_guard": "MISSING_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_FORBIDDEN_OUTPUT_GUARD",
    "operational_global_approved_for_paper_side_effect_guard": "MISSING_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_SIDE_EFFECT_GUARD",
    "operational_global_approved_for_paper_overclaim_guard": "MISSING_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_OVERCLAIM_GUARD",
    "recommended_next_task": "MISSING_RECOMMENDED_NEXT_TASK",
}

CREATED_REQUIRED_ARTIFACT_KEYS = {
    "operational_global_approved_for_paper_manifest_review": "MISSING_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_MANIFEST_REVIEW",
    "operational_global_approved_for_paper_lineage_matrix": "MISSING_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_LINEAGE_MATRIX",
    "operational_global_approved_for_paper_limitations": "MISSING_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_LIMITATIONS",
    "operational_global_approved_for_paper_revocation_plan": "MISSING_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVOCATION_PLAN",
}

FORBIDDEN_ARTIFACT_PATTERNS = {
    "*current_candidates*",
    "*current-candidates*",
    "*snapshot*",
    "*signal_semantics*",
    "*signal-semantics*",
    "*broker*",
    "*order*",
    "*trading*",
    "*data/raw*",
    "*data/processed*",
    "*data/cache*",
}


@dataclass(frozen=True)
class OperationalGlobalApprovedForPaperHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_operational_global_approved_for_paper_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> OperationalGlobalApprovedForPaperHealthResult:
    index = build_operational_global_approved_for_paper_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if not index.index_frame.empty:
        for row in index.index_frame.to_dict("records"):
            issues.extend(_issues_for_row(row))
    frame = _finalize(pd.DataFrame(issues, dtype=object))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "operational_global_approved_for_paper_health.csv",
        "health_report": Path(output_dir) / "operational_global_approved_for_paper_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = OperationalGlobalApprovedForPaperHealthResult(
        status=status,
        checked_artifact_count=len(index.index_frame),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=index.warnings,
        audit_metadata={"root": str(root), "checked_artifact_count": len(index.index_frame), "report_only": True, "diagnostic_only": True},
    )
    _write(result)
    return result


def _issues_for_row(row: dict[str, Any]) -> list[dict[str, Any]]:
    run_id = _text(row.get("operational_global_approved_for_paper_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []

    metadata_path = Path(_text(row.get("operational_global_approved_for_paper_metadata_path")))
    if metadata_path.exists() and not _read_json(metadata_path):
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "UNREADABLE_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_METADATA",
                "Metadata exists but cannot be parsed.",
                metadata_path,
            )
        )

    if status and status not in ALLOWED_STATUSES:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "UNKNOWN_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_STATUS",
                f"Unknown status: {status}",
                artifact_path,
            )
        )

    for key, code in ALWAYS_REQUIRED_ARTIFACT_KEYS.items():
        _require_path(run_id, Path(_text(row.get(f"{key}_path"))), code, issues)

    if status == OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED:
        for key, code in CREATED_REQUIRED_ARTIFACT_KEYS.items():
            _require_path(run_id, Path(_text(row.get(f"{key}_path"))), code, issues)

    for field in [*CORE_FALSE_FIELDS, *DOWNSTREAM_FALSE_FIELDS]:
        if _to_bool(row.get(field)):
            issues.append(
                _issue(
                    run_id,
                    "ERROR",
                    f"{field.upper()}_UNEXPECTED",
                    f"Unsafe false-expected field is true: {field}",
                    artifact_path,
                )
            )

    if not _to_bool(row.get("report_only")) or not _to_bool(row.get("research_governed")) or not _to_bool(row.get("diagnostic_output")):
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "RESEARCH_GOVERNED_FLAGS_MISSING",
                "report_only, research_governed, and diagnostic_output must remain true.",
                artifact_path,
            )
        )

    issues.extend(_forbidden_artifact_path_issues(run_id, artifact_path, row))
    return issues


def _require_path(run_id: str, path: Path, code: str, issues: list[dict[str, Any]]) -> None:
    if not _text(path) or not path.exists():
        issues.append(_issue(run_id, "ERROR", code, f"Required artifact missing: {path}", path))


def _forbidden_artifact_path_issues(run_id: str, artifact_path: Path, row: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    values = [str(value).replace("\\", "/").lower() for key, value in row.items() if key.endswith("_path") or key == "artifact_path"]
    metadata_path = Path(_text(row.get("operational_global_approved_for_paper_metadata_path")))
    metadata = _read_json(metadata_path) if metadata_path.exists() else {}
    artifact_paths = metadata.get("artifact_paths")
    if isinstance(artifact_paths, dict):
        values.extend(str(value).replace("\\", "/").lower() for value in artifact_paths.values())
    for value in values:
        if _is_allowed_self_artifact(value):
            continue
        if any(fnmatch.fnmatch(value, pattern) for pattern in FORBIDDEN_ARTIFACT_PATTERNS):
            issues.append(
                _issue(
                    run_id,
                    "ERROR",
                    "FORBIDDEN_OPERATIONAL_ARTIFACT_PATH",
                    f"Forbidden operational artifact path observed: {value}",
                    artifact_path,
                )
            )
            break
    return issues


def _is_allowed_self_artifact(value: str) -> bool:
    return "outputs/reports/manual_diagnostics/operational_global_approved_for_paper_v0_1" in value


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    for column in HEALTH_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[HEALTH_COLUMNS].copy()


def _write(result: OperationalGlobalApprovedForPaperHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "status": result.status,
                "checked_artifact_count": result.checked_artifact_count,
                "issue_count": result.issue_count,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "warnings": result.warnings,
                "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
                **result.audit_metadata,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Operational Global APPROVED_FOR_PAPER Health",
                "",
                "This health view is report-only and does not grant operational global APPROVED_FOR_PAPER.",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                f"- error_count: {result.error_count}",
                "",
                _frame_to_markdown(result.health_frame) if not result.health_frame.empty else "No health issues found.",
            ]
        ),
        encoding="utf-8",
    )


def _issue(run_id: str, severity: str, code: str, message: str, path: Path) -> dict[str, Any]:
    return {
        "operational_global_approved_for_paper_id": run_id,
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }
