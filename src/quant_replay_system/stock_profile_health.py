"""Health checks for report-only stock profile phase 1 artifacts."""

from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.stock_profile import (
    ARTIFACT_FILES,
    DOWNSTREAM_FALSE_FIELDS,
    FACTOR_LAYERS,
    NO_STOCK_PROFILE_INPUT,
    READY_FOR_STOCK_PROFILE_PHASE1,
    REQUIRED_METRICS,
    REQUIRED_OVERFIT_WARNINGS,
    STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED,
    SUBSTANTIVE_ARTIFACT_KEYS,
)
from quant_replay_system.stock_profile_index import DEFAULT_ROOT, build_stock_profile_index
from quant_replay_system.stock_profile_index import _read_csv, _read_json, _text, _to_bool


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"
HEALTH_COLUMNS = ["stock_profile_run_id", "severity", "issue_code", "message", "artifact_path"]

ALLOWED_STATUSES = {
    NO_STOCK_PROFILE_INPUT,
    "STOCK_PROFILE_INPUT_FOUND",
    "STOCK_PROFILE_APPROVAL_BLOCKED",
    "STOCK_PROFILE_ACTIVE_MODEL_INPUT_BLOCKED",
    "STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED",
    "STOCK_PROFILE_TRAINING_RESULT_INPUT_BLOCKED",
    "STOCK_PROFILE_TRAINING_RESULT_PLANNING_INPUT_BLOCKED",
    "STOCK_PROFILE_METRIC_EXTENSION_INPUT_BLOCKED",
    "STOCK_PROFILE_METRIC_COMPUTATION_INPUT_BLOCKED",
    "STOCK_PROFILE_METRIC_EVALUATION_INPUT_BLOCKED",
    "STOCK_PROFILE_TRAINING_EVALUATION_INPUT_BLOCKED",
    "STOCK_PROFILE_FORWARD_LABEL_INPUT_BLOCKED",
    "STOCK_PROFILE_REPLAY_FREEZE_INPUT_BLOCKED",
    "STOCK_PROFILE_HEALTH_BLOCKED",
    "STOCK_PROFILE_LINEAGE_BLOCKED",
    "STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED",
    "STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED",
    "STOCK_PROFILE_TRAINING_RESULT_ROWS_BLOCKED",
    "STOCK_PROFILE_METRIC_EVIDENCE_BLOCKED",
    "STOCK_PROFILE_LIMITATIONS_BLOCKED",
    "STOCK_PROFILE_OVERFIT_WARNING_BLOCKED",
    "STOCK_PROFILE_SAFETY_FLAG_BLOCKED",
    "STOCK_PROFILE_FORBIDDEN_ARTIFACT_BLOCKED",
    "STOCK_PROFILE_LEAKAGE_BLOCKED",
    "STOCK_PROFILE_SIDE_EFFECT_BLOCKED",
    "STOCK_PROFILE_OVERCLAIM_BLOCKED",
    READY_FOR_STOCK_PROFILE_PHASE1,
    STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED,
}

ALWAYS_REQUIRED_PATH_CODES = {
    "stock_profile_metadata_path": "MISSING_STOCK_PROFILE_METADATA",
    "stock_profile_safety_flags_path": "MISSING_STOCK_PROFILE_SAFETY_FLAGS",
    "stock_profile_precondition_results_path": "MISSING_STOCK_PROFILE_PRECONDITION_RESULTS",
    "stock_profile_approval_results_path": "MISSING_STOCK_PROFILE_APPROVAL_RESULTS",
    "stock_profile_upstream_lineage_results_path": "MISSING_STOCK_PROFILE_UPSTREAM_LINEAGE_RESULTS",
    "stock_profile_active_model_input_results_path": "MISSING_STOCK_PROFILE_ACTIVE_MODEL_INPUT_RESULTS",
    "stock_profile_model_weight_versioning_input_results_path": "MISSING_STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_RESULTS",
    "stock_profile_training_result_input_results_path": "MISSING_STOCK_PROFILE_TRAINING_RESULT_INPUT_RESULTS",
    "stock_profile_metric_evidence_results_path": "MISSING_STOCK_PROFILE_METRIC_EVIDENCE_RESULTS",
    "stock_profile_leakage_guard_results_path": "MISSING_STOCK_PROFILE_LEAKAGE_GUARD_RESULTS",
    "stock_profile_side_effect_guard_results_path": "MISSING_STOCK_PROFILE_SIDE_EFFECT_GUARD_RESULTS",
    "stock_profile_overclaim_guard_results_path": "MISSING_STOCK_PROFILE_OVERCLAIM_GUARD_RESULTS",
    "recommended_next_task_path": "MISSING_RECOMMENDED_NEXT_TASK",
}

CREATED_REQUIRED_PATH_CODES = {
    "stock_profile_metadata_path": "MISSING_STOCK_PROFILE_METADATA",
    "stock_profile_input_index_path": "MISSING_STOCK_PROFILE_INPUT_INDEX",
    "stock_profile_lineage_matrix_path": "MISSING_STOCK_PROFILE_LINEAGE_MATRIX",
    "stock_profile_factor_coverage_summary_path": "MISSING_STOCK_PROFILE_FACTOR_COVERAGE_SUMMARY",
    "stock_profile_symbol_coverage_path": "MISSING_STOCK_PROFILE_SYMBOL_COVERAGE",
    "stock_profile_market_regime_coverage_path": "MISSING_STOCK_PROFILE_MARKET_REGIME_COVERAGE",
    "stock_profile_metric_summary_path": "MISSING_STOCK_PROFILE_METRIC_SUMMARY",
    "stock_profile_limitations_path": "MISSING_STOCK_PROFILE_LIMITATIONS",
    "stock_profile_overfit_warnings_path": "MISSING_STOCK_PROFILE_OVERFIT_WARNINGS",
    "stock_profile_safety_flags_path": "MISSING_STOCK_PROFILE_SAFETY_FLAGS",
}

LINEAGE_FIELDS = [
    "source_active_model_run_id",
    "source_active_model_status",
    "source_active_model_health_status",
    "source_model_workflow_run_id",
    "source_model_weight_versioning_status",
    "source_model_weight_versioning_health_status",
    "source_training_result_run_id",
    "source_training_result_status",
    "source_training_result_health_status",
    "source_training_result_planning_run_id",
    "source_training_result_planning_status",
    "source_training_result_planning_health_status",
    "source_metric_extension_run_id",
    "source_metric_extension_status",
    "source_metric_extension_health_status",
    "source_metric_computation_run_id",
    "source_metric_computation_status",
    "source_metric_computation_health_status",
    "source_metric_evaluation_planning_run_id",
    "source_metric_evaluation_status",
    "source_metric_evaluation_health_status",
    "source_training_evaluation_run_id",
    "source_training_evaluation_status",
    "source_training_evaluation_health_status",
    "source_forward_return_label_run_id",
    "source_forward_return_label_status",
    "source_forward_return_label_health_status",
    "source_replay_decision_freeze_run_id",
    "source_replay_decision_freeze_status",
    "source_replay_decision_freeze_health_status",
]

LIMITATION_TOPICS = {
    "no_buy_review": ["no real buy-review", "no buy-review"],
    "no_paper_approval": ["no paper approval"],
    "no_performance_validation": ["no strategy performance validation", "no performance validation"],
    "no_current_candidates": ["no current-candidates"],
    "no_snapshot": ["no snapshot"],
    "no_signal_semantics": ["no signal_semantics mutation", "no signal semantics mutation"],
    "no_trading": ["no broker/order/message/api/trading", "no trading"],
    "no_promoted_model": ["no promoted model"],
    "no_production_model": ["no production model"],
    "no_active_thresholds": ["no active thresholds"],
    "no_advisory_predictions": ["no advisory predictions"],
    "no_active_probabilities": ["no active probabilities"],
}

FORBIDDEN_ARTIFACT_PATTERNS = {
    "buy_review*",
    "paper_approval*",
    "approved_for_paper*",
    "performance_validation*",
    "strategy_performance*",
    "current_candidates*",
    "snapshot*",
    "signal_semantics*",
    "broker*",
    "order*",
    "trade*",
    "message*",
    "promoted_model*",
    "production_model*",
    "active_threshold*",
    "advisory_prediction*",
    "active_probability*",
    "scheduler*",
    "cron*",
    "serving*",
}


@dataclass(frozen=True)
class StockProfileHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_stock_profile_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> StockProfileHealthResult:
    index = build_stock_profile_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_STOCK_PROFILE_ARTIFACT_FOUND", "No stock profile artifacts found.", root))
    else:
        for row in index.index_frame.to_dict("records"):
            issues.extend(_issues_for_row(row))
    frame = _finalize(pd.DataFrame(issues, dtype=object))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "stock_profile_health.csv",
        "health_report": Path(output_dir) / "stock_profile_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = StockProfileHealthResult(
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
    run_id = _text(row.get("stock_profile_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []
    _ensure_manual_diagnostics_issues(run_id, artifact_path, issues)
    if status and status not in ALLOWED_STATUSES:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_STOCK_PROFILE_STATUS", f"Unknown status: {status}", artifact_path))
    for field, code in ALWAYS_REQUIRED_PATH_CODES.items():
        _require_path(run_id, Path(_text(row.get(field))), code, issues)
    _forbidden_artifact_issues(run_id, artifact_path, issues)
    _created_state_issues(row, issues)
    if status in {READY_FOR_STOCK_PROFILE_PHASE1, STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED}:
        _lineage_metadata_issues(row, issues)
    if status == STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED:
        for field, code in CREATED_REQUIRED_PATH_CODES.items():
            _require_path(run_id, Path(_text(row.get(field))), code, issues)
        issues.extend(_input_index_issues(run_id, Path(_text(row.get("stock_profile_input_index_path")))))
        issues.extend(_lineage_matrix_issues(run_id, Path(_text(row.get("stock_profile_lineage_matrix_path")))))
        issues.extend(_factor_coverage_issues(run_id, Path(_text(row.get("stock_profile_factor_coverage_summary_path")))))
        issues.extend(_metric_summary_issues(run_id, Path(_text(row.get("stock_profile_metric_summary_path")))))
        issues.extend(_limitations_issues(run_id, Path(_text(row.get("stock_profile_limitations_path")))))
        issues.extend(_overfit_warning_issues(run_id, Path(_text(row.get("stock_profile_overfit_warnings_path")))))
    for field in DOWNSTREAM_FALSE_FIELDS:
        if _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", f"{field.upper()}_UNEXPECTED", f"Unsafe false-expected field is true: {field}", artifact_path))
    for field in ["report_only", "research_governed", "diagnostic_output"]:
        if not _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", "RESEARCH_GOVERNED_FLAGS_MISSING", f"Missing or false flag: {field}", artifact_path))
    return issues


def _created_state_issues(row: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    run_id = _text(row.get("stock_profile_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    metadata = _read_json(Path(_text(row.get("stock_profile_metadata_path"))))
    safety = _read_json(Path(_text(row.get("stock_profile_safety_flags_path"))))
    status = _text(row.get("status"))
    row_created = _to_bool(row.get("stock_profile_phase1_report_only_artifacts_created"))
    metadata_created = _to_bool(metadata.get("stock_profile_phase1_report_only_artifacts_created"))
    safety_created = _to_bool(safety.get("stock_profile_phase1_report_only_artifacts_created"))
    if status == STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED and not (row_created and metadata_created and safety_created):
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "STOCK_PROFILE_REPORT_ONLY_ARTIFACTS_CREATED_FLAG_FALSE",
                "stock_profile_phase1_report_only_artifacts_created must be true for created status.",
                artifact_path,
            )
        )
    if status in {NO_STOCK_PROFILE_INPUT, READY_FOR_STOCK_PROFILE_PHASE1} and (row_created or metadata_created or safety_created):
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "STOCK_PROFILE_REPORT_ONLY_ARTIFACTS_CREATED_UNEXPECTED",
                "stock_profile_phase1_report_only_artifacts_created must remain false before created status.",
                artifact_path,
            )
        )
    if status in {NO_STOCK_PROFILE_INPUT, READY_FOR_STOCK_PROFILE_PHASE1}:
        for key in SUBSTANTIVE_ARTIFACT_KEYS:
            path = artifact_path / ARTIFACT_FILES[key]
            if path.exists() or _to_bool(row.get(f"{key}_created")):
                issues.append(_issue(run_id, "ERROR", "STOCK_PROFILE_SUBSTANTIVE_ARTIFACT_UNEXPECTED", f"Substantive stock profile artifact exists before created status: {path}", path))


def _lineage_metadata_issues(row: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    run_id = _text(row.get("stock_profile_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    missing = [field for field in LINEAGE_FIELDS if not _text(row.get(field))]
    if missing:
        issues.append(_issue(run_id, "ERROR", "STOCK_PROFILE_SOURCE_LINEAGE_MISSING", f"Missing source lineage fields: {','.join(missing)}", artifact_path))
    if _text(row.get("source_active_model_status")) == "NO_ACTIVE_MODEL_INPUT":
        issues.append(_issue(run_id, "ERROR", "STOCK_PROFILE_ACTIVE_MODEL_NO_INPUT_TREATED_AS_INPUT", "Active-model no-input status cannot be treated as substantive stock profile input.", artifact_path))
    for field in [
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
    ]:
        if _text(row.get(field)) != "PASS":
            issues.append(_issue(run_id, "ERROR", "STOCK_PROFILE_SOURCE_HEALTH_MISSING_OR_NOT_PASS", f"Source health is missing or not PASS: {field}", artifact_path))


def _input_index_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty:
        return []
    missing = {"source_run_id", "health_status"} - set(rows.columns)
    if missing:
        return [_issue(run_id, "ERROR", "STOCK_PROFILE_INPUT_INDEX_LINEAGE_MISSING", f"Stock profile input index missing columns: {','.join(sorted(missing))}", path)]
    if rows["source_run_id"].fillna("").astype(str).str.strip().eq("").any():
        return [_issue(run_id, "ERROR", "STOCK_PROFILE_INPUT_INDEX_LINEAGE_MISSING", "Stock profile input index has blank source_run_id.", path)]
    if rows["health_status"].fillna("").astype(str).str.strip().eq("").any():
        return [_issue(run_id, "ERROR", "STOCK_PROFILE_INPUT_INDEX_HEALTH_MISSING", "Stock profile input index has blank health_status.", path)]
    return []


def _lineage_matrix_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty or "lineage_item" not in rows.columns:
        return [_issue(run_id, "ERROR", "STOCK_PROFILE_LINEAGE_MATRIX_MISSING", "Stock profile lineage matrix missing lineage_item.", path)]
    required = {
        "active_model_run_id",
        "model_workflow_run_id",
        "model_weight_reference_id",
        "model_version_id",
        "parameter_version_id",
        "training_result_run_id",
        "training_result_row_id",
        "metric_extension_run_id",
        "metric_computation_run_id",
        "metric_evaluation_run_id",
        "forward_return_label_run_id",
        "replay_decision_freeze_run_id",
        "source_hash",
        "revision_id",
        "available_time",
        "quality_status",
    }
    missing = required - set(rows["lineage_item"].dropna().astype(str))
    if missing:
        return [_issue(run_id, "ERROR", "STOCK_PROFILE_LINEAGE_MATRIX_SOURCE_MISSING", f"Stock profile lineage missing items: {','.join(sorted(missing))}", path)]
    if "source_value" in rows.columns and rows.loc[rows["lineage_item"].isin(required), "source_value"].fillna("").astype(str).str.strip().eq("").any():
        return [_issue(run_id, "ERROR", "STOCK_PROFILE_LINEAGE_MATRIX_SOURCE_MISSING", "Stock profile lineage has blank source values.", path)]
    return []


def _factor_coverage_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    issues: list[dict[str, Any]] = []
    observed = set(rows.get("factor_layer", pd.Series(dtype=str)).dropna().astype(str))
    if set(FACTOR_LAYERS) - observed:
        issues.append(_issue(run_id, "ERROR", "STOCK_PROFILE_FACTOR_LAYER_TAXONOMY_INCOMPLETE", "Factor coverage must include the 8-layer taxonomy skeleton.", path))
    joined = " ".join(rows.get("notes", pd.Series(dtype=str)).fillna("").astype(str)).lower()
    if "not fixed 12-factor final coverage" not in joined:
        issues.append(_issue(run_id, "ERROR", "STOCK_PROFILE_FACTOR_COVERAGE_FIXED_12_OVERCLAIM", "Factor coverage must not treat fixed 12 factors as exhaustive.", path))
    return issues


def _metric_summary_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty:
        return []
    issues: list[dict[str, Any]] = []
    names = set(rows.get("metric_name", pd.Series(dtype=str)).dropna().astype(str))
    extra = names - set(REQUIRED_METRICS)
    if extra:
        issues.append(_issue(run_id, "ERROR", "STOCK_PROFILE_METRIC_SUMMARY_UNAPPROVED_METRIC", f"Metric summary contains unapproved metrics: {','.join(sorted(extra))}", path))
    text = " ".join(rows.astype(str).fillna("").agg(" ".join, axis=1)).lower()
    if _contains_positive_overclaim(text):
        issues.append(_issue(run_id, "ERROR", "STOCK_PROFILE_METRIC_SUMMARY_OVERCLAIM", "Metric summary claims profitability proof or strategy performance validation.", path))
    return issues


def _limitations_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").lower()
    missing = [
        topic
        for topic, alternatives in LIMITATION_TOPICS.items()
        if not any(alternative in text for alternative in alternatives)
    ]
    if missing:
        return [_issue(run_id, "ERROR", "STOCK_PROFILE_LIMITATIONS_WORDING_MISSING", f"Stock profile limitations missing topics: {','.join(missing)}", path)]
    return []


def _overfit_warning_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty or "risk_item" not in rows.columns:
        return []
    missing = set(REQUIRED_OVERFIT_WARNINGS) - set(rows["risk_item"].dropna().astype(str))
    if missing:
        return [_issue(run_id, "ERROR", "STOCK_PROFILE_OVERFIT_WARNING_MISSING", f"Stock profile overfit warnings missing: {','.join(sorted(missing))}", path)]
    return []


def _contains_positive_overclaim(text: str) -> bool:
    normalized = _strip_safe_negations(text.lower())
    return any(
        phrase in normalized
        for phrase in [
            "profitability proof",
            "strategy performance validation",
            "strategy performance validated",
            "performance validation passed",
            "real buy-review eligibility",
            "paper approval granted",
            "trading permission",
            "production readiness",
        ]
    )


def _strip_safe_negations(text: str) -> str:
    normalized = text.lower()
    for safe_phrase in [
        "not profitability proof",
        "not a profitability proof",
        "not strategy validation",
        "not strategy performance validation",
        "no strategy performance validation",
        "not performance validation",
        "no performance validation",
        "no real buy-review eligibility",
        "not real buy-review eligibility",
        "no paper approval",
        "not paper approval",
        "no trading",
        "not trading",
        "not trading permission",
        "no trading permission",
    ]:
        normalized = normalized.replace(safe_phrase, "")
    return normalized


def _forbidden_artifact_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    for child in (artifact_path.iterdir() if artifact_path.exists() else []):
        name = child.name.lower()
        if any(fnmatch.fnmatch(name, pattern) for pattern in FORBIDDEN_ARTIFACT_PATTERNS):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_STOCK_PROFILE_DOWNSTREAM_ARTIFACT_PRESENT", f"Forbidden downstream artifact present: {child.name}", child))


def _require_path(run_id: str, path: Path, code: str, issues: list[dict[str, Any]]) -> None:
    if not _text(path) or not path.exists():
        issues.append(_issue(run_id, "ERROR", code, f"Required stock profile artifact missing: {path}", path))


def _ensure_manual_diagnostics_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    parts = {part.lower() for part in artifact_path.parts}
    if "outputs" not in parts or "reports" not in parts or "manual_diagnostics" not in parts:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "ARTIFACT_PATH_OUTSIDE_MANUAL_DIAGNOSTICS",
                "Stock profile artifacts must remain under outputs/reports/manual_diagnostics.",
                artifact_path,
            )
        )


def _write(result: StockProfileHealthResult) -> None:
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
                "# Stock Profile Health",
                "",
                "Report-only health for Stock Profile Phase 1 artifacts. It fails if outputs imply active stock_profile, real buy-review eligibility, paper approval, strategy performance validation, current-candidates, snapshots, signal_semantics mutation, promoted/production models, active thresholds, advisory predictions, active probabilities, broker/order/message/API/cache/data side effects, or trading.",
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
        "stock_profile_run_id": run_id,
        "severity": severity,
        "issue_code": issue_code,
        "message": message,
        "artifact_path": str(artifact_path),
    }


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]
