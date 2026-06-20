"""Health checks for research-governed active model phase 1 report-only artifacts."""

from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.active_model import (
    ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED,
    DOWNSTREAM_FALSE_FIELDS,
    NO_ACTIVE_MODEL_INPUT,
    READY_FOR_ACTIVE_MODEL,
)
from quant_replay_system.active_model_index import DEFAULT_ROOT, build_active_model_index
from quant_replay_system.active_model_index import _read_csv, _read_json, _text, _to_bool, _to_int


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"
HEALTH_COLUMNS = ["active_model_run_id", "severity", "issue_code", "message", "artifact_path"]

ALLOWED_STATUSES = {
    NO_ACTIVE_MODEL_INPUT,
    "ACTIVE_MODEL_INPUT_FOUND",
    "ACTIVE_MODEL_APPROVAL_BLOCKED",
    "ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED",
    "ACTIVE_MODEL_TRAINING_RESULT_INPUT_BLOCKED",
    "ACTIVE_MODEL_TRAINING_RESULT_PLANNING_INPUT_BLOCKED",
    "ACTIVE_MODEL_METRIC_EXTENSION_INPUT_BLOCKED",
    "ACTIVE_MODEL_METRIC_COMPUTATION_INPUT_BLOCKED",
    "ACTIVE_MODEL_METRIC_EVALUATION_INPUT_BLOCKED",
    "ACTIVE_MODEL_TRAINING_EVALUATION_INPUT_BLOCKED",
    "ACTIVE_MODEL_FORWARD_LABEL_INPUT_BLOCKED",
    "ACTIVE_MODEL_REPLAY_FREEZE_INPUT_BLOCKED",
    "ACTIVE_MODEL_HEALTH_BLOCKED",
    "ACTIVE_MODEL_LINEAGE_BLOCKED",
    "ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED",
    "ACTIVE_MODEL_TRAINING_RESULT_ROWS_BLOCKED",
    "ACTIVE_MODEL_METRIC_EVIDENCE_BLOCKED",
    "ACTIVE_MODEL_LIMITATIONS_BLOCKED",
    "ACTIVE_MODEL_OVERFIT_WARNING_BLOCKED",
    "ACTIVE_MODEL_SAFETY_FLAG_BLOCKED",
    "ACTIVE_MODEL_FORBIDDEN_ARTIFACT_BLOCKED",
    "ACTIVE_MODEL_LEAKAGE_BLOCKED",
    "ACTIVE_MODEL_SIDE_EFFECT_BLOCKED",
    "ACTIVE_MODEL_OVERCLAIM_BLOCKED",
    READY_FOR_ACTIVE_MODEL,
    ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED,
}

ALWAYS_REQUIRED_PATH_CODES = {
    "metadata_path": "MISSING_ACTIVE_MODEL_METADATA",
    "report_path": "MISSING_ACTIVE_MODEL_REPORT",
    "active_model_safety_flags_path": "MISSING_ACTIVE_MODEL_SAFETY_FLAGS",
    "active_model_precondition_results_path": "MISSING_ACTIVE_MODEL_PRECONDITION_RESULTS",
    "active_model_approval_results_path": "MISSING_ACTIVE_MODEL_APPROVAL_RESULTS",
    "active_model_input_lineage_results_path": "MISSING_ACTIVE_MODEL_INPUT_LINEAGE_RESULTS",
    "active_model_model_weight_versioning_input_results_path": "MISSING_ACTIVE_MODEL_WEIGHT_VERSIONING_INPUT_RESULTS",
    "active_model_metric_evidence_results_path": "MISSING_ACTIVE_MODEL_METRIC_EVIDENCE_RESULTS",
    "active_model_leakage_guard_results_path": "MISSING_ACTIVE_MODEL_LEAKAGE_GUARD_RESULTS",
    "active_model_side_effect_guard_results_path": "MISSING_ACTIVE_MODEL_SIDE_EFFECT_GUARD_RESULTS",
    "active_model_overclaim_guard_results_path": "MISSING_ACTIVE_MODEL_OVERCLAIM_GUARD_RESULTS",
    "recommended_next_task_path": "MISSING_RECOMMENDED_NEXT_TASK",
}

CREATED_REQUIRED_PATH_CODES = {
    "metadata_path": "MISSING_ACTIVE_MODEL_METADATA",
    "active_model_pointer_path": "MISSING_ACTIVE_MODEL_POINTER",
    "active_model_registry_entry_path": "MISSING_ACTIVE_MODEL_REGISTRY_ENTRY",
    "active_parameter_pointer_path": "MISSING_ACTIVE_PARAMETER_POINTER",
    "active_model_activation_status_path": "MISSING_ACTIVE_MODEL_ACTIVATION_STATUS",
    "active_model_rollback_plan_path": "MISSING_ACTIVE_MODEL_ROLLBACK_PLAN",
    "active_model_input_index_path": "MISSING_ACTIVE_MODEL_INPUT_INDEX",
    "active_model_lineage_matrix_path": "MISSING_ACTIVE_MODEL_LINEAGE_MATRIX",
    "active_model_limitations_path": "MISSING_ACTIVE_MODEL_LIMITATIONS",
    "active_model_overfit_warnings_path": "MISSING_ACTIVE_MODEL_OVERFIT_WARNINGS",
    "active_model_safety_flags_path": "MISSING_ACTIVE_MODEL_SAFETY_FLAGS",
}

REQUIRED_METRIC_EVIDENCE = {
    "sample_count",
    "label_coverage",
    "average_return",
    "median_return",
    "hit_rate",
    "benchmark_relative_return",
    "industry_relative_return",
}
INPUT_INDEX_REQUIRED_COLUMNS = {"source_run_id", "health_status"}
LINEAGE_SOURCE_RUN_ITEMS = {
    "model_workflow_run_id",
    "training_result_run_id",
    "training_result_planning_run_id",
    "metric_extension_run_id",
    "metric_computation_run_id",
    "metric_evaluation_run_id",
    "training_evaluation_run_id",
    "forward_return_label_run_id",
    "replay_decision_freeze_run_id",
}
LINEAGE_COVERAGE_ITEMS = {"source_hash", "revision_id", "available_time", "quality_status"}

LIMITATION_PHRASES = [
    "no promoted model",
    "no production model",
    "no active thresholds",
    "no advisory predictions",
    "no active probabilities",
    "no stock_profile",
    "no buy-review",
    "no paper approval",
    "no performance validation",
    "no trading",
]

REQUIRED_OVERFIT_WARNINGS = {
    "small sample",
    "class imbalance",
    "single-stock overfit",
    "metric selection bias",
    "lookahead leakage",
}

FORBIDDEN_ARTIFACT_PATTERNS = {
    "promoted_model*",
    "production_model*",
    "active_threshold*",
    "advisory_prediction*",
    "active_probability*",
    "stock_profile*",
    "active_stock_profile*",
    "buy_review*",
    "paper_approval*",
    "approved_for_paper*",
    "performance_validation*",
    "strategy_performance*",
    "broker*",
    "order*",
    "trade*",
    "message*",
    "current_candidates*",
    "snapshot*",
    "signal_semantics*",
    "scheduler*",
    "cron*",
    "serving*",
}

POSITIVE_OVERCLAIM_PHRASES = [
    "promoted model created",
    "production model created",
    "active threshold",
    "active thresholds",
    "advisory prediction",
    "advisory predictions",
    "active probabilities",
    "active probability",
    "stock_profile readiness",
    "buy-review readiness",
    "paper approval granted",
    "approved for paper",
    "strategy performance validated",
    "performance validation passed",
    "production readiness",
    "real-trading readiness",
    "trading permission granted",
    "broker/order/trading path exists",
    "production serving exists",
    "current-candidates integration enabled",
    "snapshot integration enabled",
    "signal_semantics mutation",
    "profitability proof",
]


@dataclass(frozen=True)
class ActiveModelHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_active_model_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ActiveModelHealthResult:
    index = build_active_model_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_ACTIVE_MODEL_ARTIFACT_FOUND", "No active model artifacts found.", root))
    else:
        for row in index.index_frame.to_dict("records"):
            issues.extend(_issues_for_row(row))
    frame = _finalize(pd.DataFrame(issues, dtype=object))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "active_model_health.csv",
        "health_report": Path(output_dir) / "active_model_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ActiveModelHealthResult(
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
    run_id = _text(row.get("active_model_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []
    _ensure_manual_diagnostics_issues(run_id, artifact_path, issues)
    if status and status not in ALLOWED_STATUSES:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_ACTIVE_MODEL_STATUS", f"Unknown status: {status}", artifact_path))
    for field, code in ALWAYS_REQUIRED_PATH_CODES.items():
        _require_path(run_id, Path(_text(row.get(field))), code, issues)
    _forbidden_artifact_issues(run_id, artifact_path, issues)
    _created_state_issues(row, issues)
    if status == ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED:
        for field, code in CREATED_REQUIRED_PATH_CODES.items():
            _require_path(run_id, Path(_text(row.get(field))), code, issues)
        issues.extend(_active_model_pointer_issues(run_id, Path(_text(row.get("active_model_pointer_path")))))
        issues.extend(_active_model_registry_issues(run_id, Path(_text(row.get("active_model_registry_entry_path")))))
        issues.extend(_active_parameter_pointer_issues(run_id, Path(_text(row.get("active_parameter_pointer_path")))))
        issues.extend(_activation_status_issues(run_id, Path(_text(row.get("active_model_activation_status_path")))))
        issues.extend(_rollback_plan_issues(run_id, Path(_text(row.get("active_model_rollback_plan_path")))))
        issues.extend(_metric_evidence_issues(run_id, row))
        issues.extend(_input_index_issues(run_id, Path(_text(row.get("active_model_input_index_path")))))
        issues.extend(_lineage_issues(run_id, Path(_text(row.get("active_model_lineage_matrix_path")))))
        issues.extend(_limitations_issues(run_id, Path(_text(row.get("active_model_limitations_path")))))
        issues.extend(_overfit_warning_issues(run_id, Path(_text(row.get("active_model_overfit_warnings_path")))))
    issues.extend(_report_wording_issues(run_id, Path(_text(row.get("report_path")))))
    for field in DOWNSTREAM_FALSE_FIELDS:
        if _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", f"{field.upper()}_UNEXPECTED", f"Unsafe false-expected field is true: {field}", artifact_path))
    for field in ["research_governed", "diagnostic_output"]:
        if not _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", "RESEARCH_GOVERNED_FLAGS_MISSING", f"Missing or false flag: {field}", artifact_path))
    return issues


def _created_state_issues(row: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    run_id = _text(row.get("active_model_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    metadata = _read_json(Path(_text(row.get("metadata_path"))))
    safety = _read_json(Path(_text(row.get("active_model_safety_flags_path"))))
    status = _text(row.get("status"))
    row_created = _to_bool(row.get("active_model_artifacts_created"))
    metadata_created = _to_bool(metadata.get("active_model_artifacts_created"))
    safety_created = _to_bool(safety.get("active_model_artifacts_created"))
    if status == ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED and not (row_created and metadata_created and safety_created):
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "ACTIVE_MODEL_ARTIFACTS_CREATED_FLAG_FALSE",
                "active_model_artifacts_created must be true for created status.",
                artifact_path,
            )
        )
    if status in {NO_ACTIVE_MODEL_INPUT, READY_FOR_ACTIVE_MODEL} and (row_created or metadata_created or safety_created):
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "ACTIVE_MODEL_ARTIFACTS_CREATED_UNEXPECTED",
                "active_model_artifacts_created must remain false before created status.",
                artifact_path,
            )
        )


def _active_model_pointer_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    if not payload:
        return []
    checks = [
        ("promoted_model", "ACTIVE_MODEL_POINTER_PROMOTED_UNEXPECTED", "active_model_pointer claims promoted model."),
        ("production_model", "ACTIVE_MODEL_POINTER_PRODUCTION_UNEXPECTED", "active_model_pointer claims production model."),
        ("serving_enabled", "ACTIVE_MODEL_POINTER_SERVING_UNEXPECTED", "active_model_pointer has serving_enabled=true."),
        ("current_candidates_integration", "ACTIVE_MODEL_POINTER_CURRENT_CANDIDATES_UNEXPECTED", "active_model_pointer has current-candidates integration."),
        ("snapshot_integration", "ACTIVE_MODEL_POINTER_SNAPSHOT_UNEXPECTED", "active_model_pointer has snapshot integration."),
        ("signal_semantics_mutated", "ACTIVE_MODEL_POINTER_SIGNAL_SEMANTICS_UNEXPECTED", "active_model_pointer mutates signal_semantics."),
        ("trading_allowed", "ACTIVE_MODEL_POINTER_TRADING_UNEXPECTED", "active_model_pointer permits trading."),
        ("broker_api_allowed", "ACTIVE_MODEL_POINTER_TRADING_UNEXPECTED", "active_model_pointer permits broker API."),
        ("order_allowed", "ACTIVE_MODEL_POINTER_TRADING_UNEXPECTED", "active_model_pointer permits orders."),
        ("message_allowed", "ACTIVE_MODEL_POINTER_TRADING_UNEXPECTED", "active_model_pointer permits messages."),
    ]
    issues = [_issue(run_id, "ERROR", code, message, path) for field, code, message in checks if _to_bool(payload.get(field))]
    text = _strip_safe_negations(json.dumps(payload, sort_keys=True).lower())
    if any(phrase in text for phrase in POSITIVE_OVERCLAIM_PHRASES):
        issues.append(_issue(run_id, "ERROR", "ACTIVE_MODEL_POINTER_OVERCLAIM", "active_model_pointer contains active/promoted/production/profile/paper/performance/trading overclaim.", path))
    return issues


def _active_model_registry_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    checks = [
        ("promoted_model", "ACTIVE_MODEL_REGISTRY_PROMOTED_UNEXPECTED"),
        ("production_model", "ACTIVE_MODEL_REGISTRY_PRODUCTION_UNEXPECTED"),
        ("serving_enabled", "ACTIVE_MODEL_REGISTRY_SERVING_UNEXPECTED"),
        ("trading_enabled", "ACTIVE_MODEL_REGISTRY_TRADING_UNEXPECTED"),
        ("scheduler_enabled", "ACTIVE_MODEL_REGISTRY_SERVING_UNEXPECTED"),
    ]
    return [_issue(run_id, "ERROR", code, f"active_model_registry_entry has {field}=true.", path) for field, code in checks if _to_bool(payload.get(field))]


def _active_parameter_pointer_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    issues = []
    for field in ["active_thresholds_created", "signal_semantics_mutated", "advisory_predictions_created", "active_probabilities_created"]:
        if _to_bool(payload.get(field)):
            code = "ACTIVE_PARAMETER_POINTER_THRESHOLD_UNEXPECTED" if field == "active_thresholds_created" else f"ACTIVE_PARAMETER_POINTER_{field.upper()}_UNEXPECTED"
            issues.append(_issue(run_id, "ERROR", code, f"active_parameter_pointer has {field}=true.", path))
    return issues


def _activation_status_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    return [
        _issue(run_id, "ERROR", f"{field.upper()}_UNEXPECTED", f"active_model_activation_status has {field}=true.", path)
        for field in DOWNSTREAM_FALSE_FIELDS
        if _to_bool(payload.get(field))
    ]


def _rollback_plan_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = _strip_safe_negations(path.read_text(encoding="utf-8").lower())
    if "production serving exists" in text or "broker/order/trading path exists" in text:
        return [_issue(run_id, "ERROR", "ACTIVE_MODEL_ROLLBACK_OVERCLAIM", "Rollback plan claims production serving or broker/order/trading path.", path)]
    return []


def _metric_evidence_issues(run_id: str, row: dict[str, Any]) -> list[dict[str, Any]]:
    metric_names_text = _text(row.get("metric_evidence_names_present"))
    metric_names = {name.strip() for name in metric_names_text.split(",") if name.strip()}
    missing = sorted(REQUIRED_METRIC_EVIDENCE - metric_names)
    issues: list[dict[str, Any]] = []
    if missing:
        issues.append(_issue(run_id, "ERROR", "ACTIVE_MODEL_METRIC_EVIDENCE_MISSING", f"Missing metric evidence: {','.join(missing)}", row.get("metadata_path", "")))
    if _contains_positive_overclaim(metric_names_text):
        issues.append(_issue(run_id, "ERROR", "ACTIVE_MODEL_METRIC_EVIDENCE_OVERCLAIM", "Metric evidence is interpreted as strategy validation or profitability proof.", row.get("metadata_path", "")))
    return issues


def _input_index_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty:
        return []
    missing = INPUT_INDEX_REQUIRED_COLUMNS - set(rows.columns)
    if missing:
        return [_issue(run_id, "ERROR", "ACTIVE_MODEL_INPUT_INDEX_LINEAGE_MISSING", f"Active model input index missing columns: {','.join(sorted(missing))}", path)]
    if rows["source_run_id"].fillna("").astype(str).str.strip().eq("").any():
        return [_issue(run_id, "ERROR", "ACTIVE_MODEL_INPUT_INDEX_LINEAGE_MISSING", "Active model input index has blank source_run_id.", path)]
    if rows["health_status"].fillna("").astype(str).str.strip().eq("").any():
        return [_issue(run_id, "ERROR", "ACTIVE_MODEL_INPUT_INDEX_HEALTH_MISSING", "Active model input index has blank health_status.", path)]
    return []


def _lineage_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty or "lineage_item" not in rows.columns:
        return []
    observed_items = set(rows["lineage_item"].dropna().astype(str))
    missing_source = sorted(LINEAGE_SOURCE_RUN_ITEMS - observed_items)
    if missing_source:
        return [_issue(run_id, "ERROR", "ACTIVE_MODEL_LINEAGE_SOURCE_RUN_ID_MISSING", f"Active model lineage missing source run IDs: {','.join(missing_source)}", path)]
    missing_coverage = sorted(LINEAGE_COVERAGE_ITEMS - observed_items)
    if missing_coverage:
        return [_issue(run_id, "ERROR", "ACTIVE_MODEL_LINEAGE_COVERAGE_MISSING", f"Active model lineage missing coverage fields: {','.join(missing_coverage)}", path)]
    required = LINEAGE_SOURCE_RUN_ITEMS | LINEAGE_COVERAGE_ITEMS
    if "source_value" in rows.columns and rows.loc[rows["lineage_item"].isin(required), "source_value"].fillna("").astype(str).str.strip().eq("").any():
        return [_issue(run_id, "ERROR", "ACTIVE_MODEL_LINEAGE_COVERAGE_MISSING", "Active model lineage has blank source or coverage values.", path)]
    return []


def _limitations_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").lower()
    missing = [phrase for phrase in LIMITATION_PHRASES if phrase not in text]
    if missing:
        return [_issue(run_id, "ERROR", "ACTIVE_MODEL_LIMITATIONS_WORDING_MISSING", f"Active model limitations missing phrases: {','.join(missing)}", path)]
    return []


def _overfit_warning_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty or "risk_item" not in rows.columns:
        return []
    missing = REQUIRED_OVERFIT_WARNINGS - set(rows["risk_item"].dropna().astype(str))
    if missing:
        return [_issue(run_id, "ERROR", "ACTIVE_MODEL_OVERFIT_WARNING_MISSING", f"Active model overfit warnings missing: {','.join(sorted(missing))}", path)]
    return []


def _report_wording_issues(run_id: str, report_path: Path) -> list[dict[str, Any]]:
    if not report_path.exists():
        return []
    text = report_path.read_text(encoding="utf-8").lower()
    if _contains_positive_overclaim(text):
        return [_issue(run_id, "ERROR", "ACTIVE_MODEL_REPORT_OVERCLAIM", "Active model report contains production/profile/paper/performance/trading overclaim wording.", report_path)]
    return []


def _contains_positive_overclaim(text: str) -> bool:
    normalized = _strip_safe_negations(text.lower())
    return any(phrase in normalized for phrase in POSITIVE_OVERCLAIM_PHRASES)


def _strip_safe_negations(text: str) -> str:
    normalized = text.lower()
    for safe_phrase in [
        "not a promoted model",
        "not promoted model",
        "no promoted model",
        "not a production model",
        "not production model",
        "no production model",
        "no production serving exists",
        "not active thresholds",
        "no active thresholds",
        "not advisory predictions",
        "no advisory predictions",
        "no active probabilities",
        "not stock_profile",
        "no stock_profile",
        "not buy-review",
        "no buy-review",
        "not paper approval",
        "no paper approval",
        "not strategy performance validation",
        "no performance validation",
        "not trading permission",
        "no trading permission",
        "not trading",
        "no trading",
        "no broker/order/trading path exists",
        "not current-candidates",
        "no current-candidates",
        "not snapshots",
        "no snapshots",
        "not signal semantics mutation",
        "no signal_semantics mutation",
        "no signal semantics mutation",
    ]:
        normalized = normalized.replace(safe_phrase, "")
    return normalized


def _forbidden_artifact_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    for child in (artifact_path.iterdir() if artifact_path.exists() else []):
        name = child.name.lower()
        if any(fnmatch.fnmatch(name, pattern) for pattern in FORBIDDEN_ARTIFACT_PATTERNS):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_ACTIVE_MODEL_ARTIFACT_PRESENT", f"Forbidden active/downstream artifact present: {child.name}", child))


def _require_path(run_id: str, path: Path, code: str, issues: list[dict[str, Any]]) -> None:
    if not _text(path) or not path.exists():
        issues.append(_issue(run_id, "ERROR", code, f"Required active model artifact missing: {path}", path))


def _ensure_manual_diagnostics_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    parts = {part.lower() for part in artifact_path.parts}
    if "outputs" not in parts or "reports" not in parts or "manual_diagnostics" not in parts:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "ARTIFACT_PATH_OUTSIDE_MANUAL_DIAGNOSTICS",
                "Active model artifacts must remain under outputs/reports/manual_diagnostics.",
                artifact_path,
            )
        )


def _write(result: ActiveModelHealthResult) -> None:
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
                "# Active Model Health",
                "",
                "Report-only health for research-governed Active Model Phase 1 artifacts. It fails if outputs imply promoted or production models, active thresholds, advisory predictions, active probabilities, stock_profile, buy-review, paper approval, performance validation, broker/order/message/API/cache/data side effects, current-candidates, snapshots, signal semantics mutation, or trading.",
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
        "active_model_run_id": run_id,
        "severity": severity,
        "issue_code": issue_code,
        "message": message,
        "artifact_path": str(artifact_path),
    }


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]
