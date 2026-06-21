"""Health checks for report-only APPROVED_FOR_PAPER Phase 1 artifacts."""

from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.approved_for_paper_phase1 import (
    ARTIFACT_FILES,
    DOWNSTREAM_FALSE_FIELDS,
    FORBIDDEN_ARTIFACT_TOKENS,
    NO_APPROVED_FOR_PAPER_PHASE1_INPUT,
    READY_FOR_APPROVED_FOR_PAPER_PHASE1,
    APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED,
    REQUIRED_OVERFIT_WARNINGS,
    SUBSTANTIVE_ARTIFACT_KEYS,
)
from quant_replay_system.approved_for_paper_phase1_index import (
    DEFAULT_ROOT,
    SOURCE_FIELDS,
    _read_csv,
    _read_json,
    _text,
    _to_bool,
    build_approved_for_paper_phase1_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"
HEALTH_COLUMNS = ["approved_for_paper_run_id", "severity", "issue_code", "message", "artifact_path"]

ALLOWED_STATUSES = {
    NO_APPROVED_FOR_PAPER_PHASE1_INPUT,
    "APPROVED_FOR_PAPER_PHASE1_APPROVAL_BLOCKED",
    "APPROVED_FOR_PAPER_PHASE1_FORBIDDEN_ARTIFACT_BLOCKED",
    "APPROVED_FOR_PAPER_PHASE1_HEALTH_BLOCKED",
    "APPROVED_FOR_PAPER_PHASE1_LEAKAGE_BLOCKED",
    "APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED",
    "APPROVED_FOR_PAPER_PHASE1_METRIC_EVIDENCE_BLOCKED",
    "APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED",
    "APPROVED_FOR_PAPER_PHASE1_OVERFIT_WARNING_BLOCKED",
    "APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_ARTIFACT_BLOCKED",
    "APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_INPUT_BLOCKED",
    "APPROVED_FOR_PAPER_PHASE1_SAFETY_FLAG_BLOCKED",
    "APPROVED_FOR_PAPER_PHASE1_SIDE_EFFECT_BLOCKED",
    "APPROVED_FOR_PAPER_PHASE1_STOCK_PROFILE_INPUT_BLOCKED",
    "APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_INPUT_BLOCKED",
    "APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_PLANNING_INPUT_BLOCKED",
    "APPROVED_FOR_PAPER_PHASE1_TRAINING_EVALUATION_INPUT_BLOCKED",
    READY_FOR_APPROVED_FOR_PAPER_PHASE1,
    APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED,
}

ALWAYS_REQUIRED_PATH_CODES = {
    "approved_for_paper_metadata_path": "MISSING_APPROVED_FOR_PAPER_METADATA",
    "approved_for_paper_safety_flags_path": "MISSING_APPROVED_FOR_PAPER_SAFETY_FLAGS",
    "approved_for_paper_precondition_results_path": "MISSING_APPROVED_FOR_PAPER_PRECONDITION_RESULTS",
    "approved_for_paper_approval_results_path": "MISSING_APPROVED_FOR_PAPER_APPROVAL_RESULTS",
    "approved_for_paper_upstream_lineage_results_path": "MISSING_APPROVED_FOR_PAPER_UPSTREAM_LINEAGE_RESULTS",
    "approved_for_paper_paper_workflow_input_results_path": "MISSING_APPROVED_FOR_PAPER_PAPER_WORKFLOW_INPUT_RESULTS",
    "approved_for_paper_leakage_guard_results_path": "MISSING_APPROVED_FOR_PAPER_LEAKAGE_GUARD_RESULTS",
    "approved_for_paper_side_effect_guard_results_path": "MISSING_APPROVED_FOR_PAPER_SIDE_EFFECT_GUARD_RESULTS",
    "approved_for_paper_overclaim_guard_results_path": "MISSING_APPROVED_FOR_PAPER_OVERCLAIM_GUARD_RESULTS",
    "recommended_next_task_path": "MISSING_RECOMMENDED_NEXT_TASK",
}

CREATED_REQUIRED_PATH_CODES = {
    "approved_for_paper_metadata_path": "MISSING_APPROVED_FOR_PAPER_METADATA",
    "approved_for_paper_input_index_path": "MISSING_APPROVED_FOR_PAPER_INPUT_INDEX",
    "approved_for_paper_lineage_matrix_path": "MISSING_APPROVED_FOR_PAPER_LINEAGE_MATRIX",
    "approved_for_paper_review_context_path": "MISSING_APPROVED_FOR_PAPER_REVIEW_CONTEXT",
    "approved_for_paper_decision_draft_path": "MISSING_APPROVED_FOR_PAPER_DECISION_DRAFT",
    "approved_for_paper_limitations_path": "MISSING_APPROVED_FOR_PAPER_LIMITATIONS",
    "approved_for_paper_overfit_warnings_path": "MISSING_APPROVED_FOR_PAPER_OVERFIT_WARNINGS",
    "approved_for_paper_safety_flags_path": "MISSING_APPROVED_FOR_PAPER_SAFETY_FLAGS",
}

LINEAGE_FIELDS = [
    *SOURCE_FIELDS,
    "model_weight_reference_id",
    "model_version_id",
    "parameter_version_id",
]

HEALTH_FIELDS = [
    "source_paper_workflow_phase1_health_status",
    "source_stock_profile_health_status",
    "source_active_model_health_status",
    "source_model_weight_versioning_health_status",
    "source_training_result_health_status",
    "source_training_result_planning_health_status",
    "source_metric_extension_health_status",
    "source_metric_computation_health_status",
    "source_metric_evaluation_health_status",
    "source_training_evaluation_health_status",
    "source_forward_return_label_health_status",
    "source_replay_decision_freeze_health_status",
]

LIMITATION_TOPICS = {
    "no_buy_review": ["no real buy-review"],
    "no_performance_validation": ["no strategy performance validation"],
    "no_current_candidates": ["no current-candidates"],
    "no_snapshot": ["no snapshot"],
    "no_signal_semantics": ["no signal_semantics mutation", "no signal semantics mutation"],
    "no_active_stock_profile": ["no active stock_profile", "no active stock profile"],
    "no_trading": ["no broker/order/message/api/trading", "no trading"],
    "no_promoted_model": ["no promoted model"],
    "no_production_model": ["no production model"],
    "no_active_thresholds": ["no active thresholds"],
    "no_advisory_predictions": ["no advisory predictions"],
    "no_active_probabilities": ["no active probabilities"],
}

REQUIRED_WARNING_SUBSET = {
    "small sample",
    "class imbalance",
    "single-stock overfit",
    "approved-for-paper overfit",
    "lookahead leakage",
}

FORBIDDEN_ARTIFACT_PATTERNS = {
    f"*{token}*" for token in FORBIDDEN_ARTIFACT_TOKENS
}


@dataclass(frozen=True)
class ApprovedForPaperPhase1HealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_approved_for_paper_phase1_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ApprovedForPaperPhase1HealthResult:
    index = build_approved_for_paper_phase1_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_APPROVED_FOR_PAPER_PHASE1_ARTIFACT_FOUND", "No APPROVED_FOR_PAPER phase 1 artifacts found.", root))
    else:
        for row in index.index_frame.to_dict("records"):
            issues.extend(_issues_for_row(row))
    frame = _finalize(pd.DataFrame(issues, dtype=object))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "approved_for_paper_phase1_health.csv",
        "health_report": Path(output_dir) / "approved_for_paper_phase1_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ApprovedForPaperPhase1HealthResult(
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
    run_id = _text(row.get("approved_for_paper_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []
    _ensure_manual_diagnostics_issues(run_id, artifact_path, issues)
    if status and status not in ALLOWED_STATUSES:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_APPROVED_FOR_PAPER_PHASE1_STATUS", f"Unknown status: {status}", artifact_path))
    for field, code in ALWAYS_REQUIRED_PATH_CODES.items():
        _require_path(run_id, Path(_text(row.get(field))), code, issues)
    _forbidden_artifact_issues(run_id, artifact_path, issues)
    _created_state_issues(row, issues)
    if status in {READY_FOR_APPROVED_FOR_PAPER_PHASE1, APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED}:
        _lineage_metadata_issues(row, issues)
    if status == APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED:
        for field, code in CREATED_REQUIRED_PATH_CODES.items():
            _require_path(run_id, Path(_text(row.get(field))), code, issues)
        issues.extend(_review_context_issues(run_id, Path(_text(row.get("approved_for_paper_review_context_path")))))
        issues.extend(_decision_draft_issues(run_id, Path(_text(row.get("approved_for_paper_decision_draft_path")))))
        issues.extend(_limitations_issues(run_id, Path(_text(row.get("approved_for_paper_limitations_path")))))
        issues.extend(_overfit_warning_issues(run_id, Path(_text(row.get("approved_for_paper_overfit_warnings_path")))))
    for field in DOWNSTREAM_FALSE_FIELDS:
        if _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", f"{field.upper()}_UNEXPECTED", f"Unsafe false-expected field is true: {field}", artifact_path))
    for field in ["report_only", "research_governed", "diagnostic_output"]:
        if not _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", "RESEARCH_GOVERNED_FLAGS_MISSING", f"Missing or false flag: {field}", artifact_path))
    return issues


def _created_state_issues(row: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    run_id = _text(row.get("approved_for_paper_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    metadata = _read_json(Path(_text(row.get("approved_for_paper_metadata_path"))))
    safety = _read_json(Path(_text(row.get("approved_for_paper_safety_flags_path"))))
    status = _text(row.get("status"))
    row_created = _to_bool(row.get("approved_for_paper_phase1_report_only_artifacts_created"))
    metadata_created = _to_bool(metadata.get("approved_for_paper_phase1_report_only_artifacts_created"))
    safety_created = _to_bool(safety.get("approved_for_paper_phase1_report_only_artifacts_created"))
    if status == APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED and not (row_created and metadata_created and safety_created):
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "APPROVED_FOR_PAPER_REPORT_ONLY_ARTIFACTS_CREATED_FLAG_FALSE",
                "approved_for_paper_phase1_report_only_artifacts_created must be true for created status.",
                artifact_path,
            )
        )
    if status in {NO_APPROVED_FOR_PAPER_PHASE1_INPUT, READY_FOR_APPROVED_FOR_PAPER_PHASE1} and (
        row_created or metadata_created or safety_created
    ):
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "APPROVED_FOR_PAPER_REPORT_ONLY_ARTIFACTS_CREATED_UNEXPECTED",
                "approved_for_paper_phase1_report_only_artifacts_created must remain false before created status.",
                artifact_path,
            )
        )
    if status in {NO_APPROVED_FOR_PAPER_PHASE1_INPUT, READY_FOR_APPROVED_FOR_PAPER_PHASE1}:
        for key in SUBSTANTIVE_ARTIFACT_KEYS:
            path = artifact_path / ARTIFACT_FILES[key]
            if path.exists() or _to_bool(row.get(f"{key}_created")):
                issues.append(
                    _issue(
                        run_id,
                        "ERROR",
                        "APPROVED_FOR_PAPER_SUBSTANTIVE_ARTIFACT_UNEXPECTED",
                        f"Substantive APPROVED_FOR_PAPER phase 1 artifact exists before created status: {path}",
                        path,
                    )
                )


def _lineage_metadata_issues(row: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    run_id = _text(row.get("approved_for_paper_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    missing = [field for field in LINEAGE_FIELDS if not _text(row.get(field))]
    if missing:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "APPROVED_FOR_PAPER_SOURCE_LINEAGE_MISSING",
                f"Missing source lineage fields: {','.join(missing)}",
                artifact_path,
            )
        )
    for field in HEALTH_FIELDS:
        if _text(row.get(field)) != "PASS":
            issues.append(
                _issue(
                    run_id,
                    "ERROR",
                    "APPROVED_FOR_PAPER_SOURCE_HEALTH_MISSING_OR_NOT_PASS",
                    f"Source health is missing or not PASS: {field}",
                    artifact_path,
                )
            )


def _review_context_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    if _contains_forbidden_instruction(_frame_text(_read_csv(path))):
        return [
            _issue(
                run_id,
                "ERROR",
                "APPROVED_FOR_PAPER_REVIEW_CONTEXT_FORBIDDEN_INSTRUCTION",
                "Review context contains buy/order/trade language.",
                path,
            )
        ]
    return []


def _decision_draft_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    frame = _read_csv(path)
    if frame.empty:
        return []
    allowed = {"APPROVED_FOR_PAPER_PHASE1", "PAPER_APPROVAL_REVIEW_DRAFT", "PAPER_BLOCKED_REVIEW", "NEEDS_HUMAN_REVIEW"}
    labels = set(frame.get("draft_label", pd.Series(dtype=str)).dropna().astype(str))
    if labels - allowed:
        return [
            _issue(
                run_id,
                "ERROR",
                "APPROVED_FOR_PAPER_DECISION_DRAFT_FORBIDDEN_LABEL",
                f"Forbidden decision draft labels: {','.join(sorted(labels - allowed))}",
                path,
            )
        ]
    text = _frame_text(frame).upper()
    if any(token in text for token in ["REAL_BUY_REVIEW_CANDIDATE", "BUY", "SELL", "ORDER", "TRADE"]):
        return [
            _issue(
                run_id,
                "ERROR",
                "APPROVED_FOR_PAPER_DECISION_DRAFT_FORBIDDEN_LABEL",
                "Decision draft contains forbidden buy/sell/order/trade language.",
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
                "APPROVED_FOR_PAPER_LIMITATIONS_WORDING_MISSING",
                f"APPROVED_FOR_PAPER limitations missing topics: {','.join(missing)}",
                path,
            )
        ]
    return []


def _overfit_warning_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    frame = _read_csv(path)
    if frame.empty or "warning_item" not in frame.columns:
        return []
    observed = set(frame["warning_item"].dropna().astype(str))
    missing = REQUIRED_WARNING_SUBSET - observed
    if missing:
        return [
            _issue(
                run_id,
                "ERROR",
                "APPROVED_FOR_PAPER_OVERFIT_WARNING_MISSING",
                f"APPROVED_FOR_PAPER overfit warnings missing: {','.join(sorted(missing))}",
                path,
            )
        ]
    expected_missing = set(REQUIRED_OVERFIT_WARNINGS) - observed
    if expected_missing:
        return [
            _issue(
                run_id,
                "ERROR",
                "APPROVED_FOR_PAPER_OVERFIT_WARNING_MISSING",
                f"APPROVED_FOR_PAPER overfit warnings missing: {','.join(sorted(expected_missing))}",
                path,
            )
        ]
    return []


def _contains_forbidden_instruction(text: str) -> bool:
    upper = text.upper()
    return any(token in upper for token in ["REAL_BUY_REVIEW_CANDIDATE", "BUY", "SELL", "ORDER", "TRADE"])


def _frame_text(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""
    return " ".join(frame.fillna("").astype(str).to_numpy().ravel())


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
                    "FORBIDDEN_APPROVED_FOR_PAPER_DOWNSTREAM_ARTIFACT_PRESENT",
                    f"Forbidden downstream artifact present: {child.name}",
                    child,
                )
            )


def _require_path(run_id: str, path: Path, code: str, issues: list[dict[str, Any]]) -> None:
    if not _text(path) or not path.exists():
        issues.append(_issue(run_id, "ERROR", code, f"Required APPROVED_FOR_PAPER phase 1 artifact missing: {path}", path))


def _ensure_manual_diagnostics_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    parts = {part.lower() for part in artifact_path.parts}
    if "outputs" not in parts or "reports" not in parts or "manual_diagnostics" not in parts:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "ARTIFACT_PATH_OUTSIDE_MANUAL_DIAGNOSTICS",
                "APPROVED_FOR_PAPER Phase 1 artifacts must remain under outputs/reports/manual_diagnostics.",
                artifact_path,
            )
        )


def _write(result: ApprovedForPaperPhase1HealthResult) -> None:
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
                "# APPROVED_FOR_PAPER Phase 1 Health",
                "",
                "Report-only health for APPROVED_FOR_PAPER Phase 1 artifacts. It fails if outputs imply real buy-review eligibility, strategy performance validation, current-candidates, snapshots, signal_semantics mutation, active stock_profile, promoted/production models, active thresholds, advisory predictions, active probabilities, broker/order/message/API/cache/data side effects, or trading.",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                result.health_frame.to_markdown(index=False) if not result.health_frame.empty else "No issues found.",
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
        "approved_for_paper_run_id": run_id,
        "severity": severity,
        "issue_code": issue_code,
        "message": message,
        "artifact_path": str(artifact_path),
    }


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]
