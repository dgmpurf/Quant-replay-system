"""Health checks for report-only Global APPROVED_FOR_PAPER approval-review artifacts."""

from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.global_approved_for_paper_approval_review import (
    ARTIFACT_FILES,
    DOWNSTREAM_FALSE_FIELDS,
    FORBIDDEN_ARTIFACT_TOKENS,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_APPROVAL_BLOCKED,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_FORBIDDEN_ARTIFACT_BLOCKED,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_HEALTH_BLOCKED,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_LINEAGE_BLOCKED,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_OVERCLAIM_BLOCKED,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_SIDE_EFFECT_BLOCKED,
    NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_INPUT,
    READY_FOR_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW,
)
from quant_replay_system.global_approved_for_paper_approval_review_index import (
    DEFAULT_ROOT,
    _frame_to_markdown,
    _read_csv,
    _text,
    _to_bool,
    build_global_approved_for_paper_approval_review_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"
HEALTH_COLUMNS = ["global_approved_for_paper_approval_review_id", "severity", "issue_code", "message", "artifact_path"]

ALLOWED_STATUSES = {
    NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_INPUT,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_APPROVAL_BLOCKED,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_FORBIDDEN_ARTIFACT_BLOCKED,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_HEALTH_BLOCKED,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_LINEAGE_BLOCKED,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_OVERCLAIM_BLOCKED,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_SIDE_EFFECT_BLOCKED,
    READY_FOR_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED,
}

ALWAYS_REQUIRED_PATH_CODES = {
    "global_approved_for_paper_approval_review_metadata_path": "MISSING_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_METADATA",
    "global_approved_for_paper_precondition_results_path": "MISSING_GLOBAL_APPROVED_FOR_PAPER_PRECONDITION_RESULTS",
    "global_approved_for_paper_forbidden_output_guard_path": "MISSING_GLOBAL_APPROVED_FOR_PAPER_FORBIDDEN_OUTPUT_GUARD",
    "global_approved_for_paper_overclaim_guard_path": "MISSING_GLOBAL_APPROVED_FOR_PAPER_OVERCLAIM_GUARD",
    "global_approved_for_paper_side_effect_guard_path": "MISSING_GLOBAL_APPROVED_FOR_PAPER_SIDE_EFFECT_GUARD",
    "recommended_next_task_path": "MISSING_RECOMMENDED_NEXT_TASK",
}

CREATED_REQUIRED_PATH_CODES = {
    "global_approved_for_paper_approval_manifest_review_path": "MISSING_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_MANIFEST_REVIEW",
    "global_approved_for_paper_lineage_matrix_path": "MISSING_GLOBAL_APPROVED_FOR_PAPER_LINEAGE_MATRIX",
    "global_approved_for_paper_research_status_preview_path": "MISSING_GLOBAL_APPROVED_FOR_PAPER_RESEARCH_STATUS_PREVIEW",
    "global_approved_for_paper_limitations_path": "MISSING_GLOBAL_APPROVED_FOR_PAPER_LIMITATIONS",
}

LINEAGE_REQUIRED_COLUMNS = {
    "global_approved_for_paper_approval_review_id",
    "source_approved_for_paper_phase1_run_id",
    "source_paper_workflow_phase1_run_id",
    "source_model_workflow_run_id",
    "source_hash",
    "revision_id",
    "available_time",
    "quality_status",
    "report_only",
    "diagnostic_only",
    "research_governed",
}

LIMITATION_TOPICS = {
    "not_global_operational_state": ["not global approved_for_paper as operational state"],
    "no_buy_review": ["no real buy-review eligibility"],
    "no_buy_review_allowed": ["no buy_review_allowed"],
    "no_performance_validation": ["no strategy performance validation"],
    "no_current_candidates": ["no current-candidates"],
    "no_snapshot": ["no snapshot"],
    "no_signal_semantics": ["no signal_semantics mutation", "no signal semantics mutation"],
    "no_active_stock_profile": ["no active stock_profile", "no active stock profile"],
    "no_trading": ["no broker/order/message/api/trading", "no trading"],
}

FORBIDDEN_ARTIFACT_PATTERNS = {f"*{token}*" for token in FORBIDDEN_ARTIFACT_TOKENS}


@dataclass(frozen=True)
class GlobalApprovedForPaperApprovalReviewHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_global_approved_for_paper_approval_review_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> GlobalApprovedForPaperApprovalReviewHealthResult:
    index = build_global_approved_for_paper_approval_review_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(
            _issue(
                "",
                "ERROR",
                "NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_ARTIFACT_FOUND",
                "No Global APPROVED_FOR_PAPER approval-review artifacts found.",
                root,
            )
        )
    else:
        for row in index.index_frame.to_dict("records"):
            issues.extend(_issues_for_row(row))
    frame = _finalize(pd.DataFrame(issues, dtype=object))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "global_approved_for_paper_approval_review_health.csv",
        "health_report": Path(output_dir) / "global_approved_for_paper_approval_review_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = GlobalApprovedForPaperApprovalReviewHealthResult(
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
    run_id = _text(row.get("global_approved_for_paper_approval_review_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []
    _ensure_manual_diagnostics_issues(run_id, artifact_path, issues)
    if status and status not in ALLOWED_STATUSES:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_STATUS", f"Unknown status: {status}", artifact_path))
    for field, code in ALWAYS_REQUIRED_PATH_CODES.items():
        _require_path(run_id, Path(_text(row.get(field))), code, issues)
    _forbidden_artifact_issues(run_id, artifact_path, issues)
    _created_state_issues(row, issues)
    if status == GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED:
        for field, code in CREATED_REQUIRED_PATH_CODES.items():
            _require_path(run_id, Path(_text(row.get(field))), code, issues)
        issues.extend(_approval_manifest_issues(run_id, Path(_text(row.get("global_approved_for_paper_approval_manifest_review_path")))))
        issues.extend(_lineage_issues(run_id, Path(_text(row.get("global_approved_for_paper_lineage_matrix_path")))))
        issues.extend(_limitations_issues(run_id, Path(_text(row.get("global_approved_for_paper_limitations_path")))))
    for field in DOWNSTREAM_FALSE_FIELDS:
        if _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", f"{field.upper()}_UNEXPECTED", f"Unsafe false-expected field is true: {field}", artifact_path))
    if _to_bool(row.get("global_approved_for_paper")):
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "GLOBAL_APPROVED_FOR_PAPER_OPERATIONAL_STATE_UNEXPECTED",
                "Artifact view must not treat report-only approval review as global APPROVED_FOR_PAPER.",
                artifact_path,
            )
        )
    for field in ["report_only", "research_governed", "diagnostic_output"]:
        if not _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", "RESEARCH_GOVERNED_FLAGS_MISSING", f"Missing or false flag: {field}", artifact_path))
    return issues


def _created_state_issues(row: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    run_id = _text(row.get("global_approved_for_paper_approval_review_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    status = _text(row.get("status"))
    created = _to_bool(row.get("global_approved_for_paper_approval_review_report_only_artifacts_created"))
    if status == GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED and not created:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_CREATED_FLAG_FALSE",
                "Report-only artifact-created flag must be true for approved report-only review status.",
                artifact_path,
            )
        )
    if status in {NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_INPUT, READY_FOR_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW} and created:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_CREATED_FLAG_UNEXPECTED",
                "Report-only artifact-created flag must remain false before created status.",
                artifact_path,
            )
        )


def _approval_manifest_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    frame = _read_csv(path)
    if frame.empty:
        return []
    if "exact_approval_text_matched" not in frame.columns or not _to_bool(frame.iloc[0].get("exact_approval_text_matched")):
        return [
            _issue(
                run_id,
                "ERROR",
                "GLOBAL_APPROVED_FOR_PAPER_EXACT_APPROVAL_EVIDENCE_MISSING",
                "Approval manifest review must preserve exact approval evidence.",
                path,
            )
        ]
    return []


def _lineage_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    frame = _read_csv(path)
    if frame.empty:
        return []
    missing = LINEAGE_REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        return [
            _issue(
                run_id,
                "ERROR",
                "GLOBAL_APPROVED_FOR_PAPER_LINEAGE_COLUMNS_MISSING",
                f"Missing lineage columns: {','.join(sorted(missing))}",
                path,
            )
        ]
    row = frame.iloc[0].to_dict()
    missing_values = [field for field in LINEAGE_REQUIRED_COLUMNS if not _text(row.get(field))]
    if missing_values:
        return [
            _issue(
                run_id,
                "ERROR",
                "GLOBAL_APPROVED_FOR_PAPER_LINEAGE_VALUES_MISSING",
                f"Missing lineage values: {','.join(sorted(missing_values))}",
                path,
            )
        ]
    return []


def _limitations_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").lower()
    missing = [topic for topic, alternatives in LIMITATION_TOPICS.items() if not any(alternative in text for alternative in alternatives)]
    if missing:
        return [
            _issue(
                run_id,
                "ERROR",
                "GLOBAL_APPROVED_FOR_PAPER_LIMITATIONS_WORDING_MISSING",
                f"Global APPROVED_FOR_PAPER approval-review limitations missing topics: {','.join(missing)}",
                path,
            )
        ]
    return []


def _forbidden_artifact_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    allowed_names = set(ARTIFACT_FILES.values())
    for child in (artifact_path.iterdir() if artifact_path.exists() else []):
        name = child.name.lower()
        if child.name in allowed_names:
            continue
        if any(fnmatch.fnmatch(name, pattern) for pattern in FORBIDDEN_ARTIFACT_PATTERNS):
            issues.append(
                _issue(
                    run_id,
                    "ERROR",
                    "FORBIDDEN_GLOBAL_APPROVED_FOR_PAPER_DOWNSTREAM_ARTIFACT_PRESENT",
                    f"Forbidden downstream artifact present: {child.name}",
                    child,
                )
            )


def _require_path(run_id: str, path: Path, code: str, issues: list[dict[str, Any]]) -> None:
    if not _text(path) or not path.exists():
        issues.append(_issue(run_id, "ERROR", code, f"Required Global APPROVED_FOR_PAPER approval-review artifact missing: {path}", path))


def _ensure_manual_diagnostics_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    parts = {part.lower() for part in artifact_path.parts}
    if "outputs" not in parts or "reports" not in parts or "manual_diagnostics" not in parts:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "ARTIFACT_PATH_OUTSIDE_MANUAL_DIAGNOSTICS",
                "Global APPROVED_FOR_PAPER approval-review artifacts must remain under outputs/reports/manual_diagnostics.",
                artifact_path,
            )
        )


def _write(result: GlobalApprovedForPaperApprovalReviewHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "health_id": _hash_payload(result.health_frame.to_dict("records")),
                "status": result.status,
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
                "# Global APPROVED_FOR_PAPER Approval Review Health",
                "",
                "Report-only health for Global APPROVED_FOR_PAPER approval-review artifacts. It fails if outputs imply global APPROVED_FOR_PAPER operational state, real buy-review eligibility, buy_review_allowed, strategy performance validation, current-candidates, snapshots, signal_semantics mutation, active stock_profile, promoted/production models, active thresholds, advisory predictions, active probabilities, broker/order/message/API/cache/data side effects, or trading.",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                _frame_to_markdown(result.health_frame) if not result.health_frame.empty else "No issues found.",
            ]
        ),
        encoding="utf-8",
    )


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    for column in HEALTH_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[HEALTH_COLUMNS].copy()


def _issue(run_id: str, severity: str, issue_code: str, message: str, artifact_path: str | Path) -> dict[str, Any]:
    return {
        "global_approved_for_paper_approval_review_id": run_id,
        "severity": severity,
        "issue_code": issue_code,
        "message": message,
        "artifact_path": str(artifact_path),
    }


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]
