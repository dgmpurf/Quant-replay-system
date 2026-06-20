"""Health checks for report-only model weight/versioning artifacts."""

from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.model_weight_versioning import (
    DOWNSTREAM_FALSE_FIELDS,
    MODEL_WEIGHT_VERSIONING_INPUT_FOUND,
    MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED,
    NO_MODEL_WEIGHT_VERSIONING_INPUT,
    READY_FOR_MODEL_WEIGHT_VERSIONING,
)
from quant_replay_system.model_weight_versioning_index import DEFAULT_ROOT, build_model_weight_versioning_index
from quant_replay_system.model_weight_versioning_index import _read_csv, _read_json, _text, _to_bool, _to_int


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"
HEALTH_COLUMNS = ["model_workflow_run_id", "severity", "issue_code", "message", "artifact_path"]

ALLOWED_STATUSES = {
    NO_MODEL_WEIGHT_VERSIONING_INPUT,
    MODEL_WEIGHT_VERSIONING_INPUT_FOUND,
    READY_FOR_MODEL_WEIGHT_VERSIONING,
    MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED,
    "MODEL_WEIGHT_VERSIONING_APPROVAL_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_INPUT_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_PLANNING_INPUT_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_METRIC_EXTENSION_INPUT_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_METRIC_COMPUTATION_INPUT_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_METRIC_EVALUATION_INPUT_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_TRAINING_EVALUATION_INPUT_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_FORWARD_LABEL_INPUT_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_REPLAY_FREEZE_INPUT_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_LINEAGE_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_ROWS_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_METRIC_EVIDENCE_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_LIMITATIONS_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_OVERFIT_WARNING_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_REPORT_ONLY_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_FORBIDDEN_ARTIFACT_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_LEAKAGE_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_SIDE_EFFECT_BLOCKED",
    "MODEL_WEIGHT_VERSIONING_OVERCLAIM_BLOCKED",
}

ALWAYS_REQUIRED_PATH_CODES = {
    "metadata_path": "MISSING_METADATA",
    "report_path": "MISSING_REPORT",
    "model_safety_flags_path": "MISSING_MODEL_SAFETY_FLAGS",
    "model_precondition_results_path": "MISSING_MODEL_PRECONDITION_RESULTS",
    "model_approval_results_path": "MISSING_MODEL_APPROVAL_RESULTS",
    "model_input_lineage_results_path": "MISSING_MODEL_INPUT_LINEAGE_RESULTS",
    "model_training_result_input_results_path": "MISSING_MODEL_TRAINING_RESULT_INPUT_RESULTS",
    "model_metric_evidence_results_path": "MISSING_MODEL_METRIC_EVIDENCE_RESULTS",
    "model_leakage_guard_results_path": "MISSING_MODEL_LEAKAGE_GUARD_RESULTS",
    "model_side_effect_guard_results_path": "MISSING_MODEL_SIDE_EFFECT_GUARD_RESULTS",
    "model_overclaim_guard_results_path": "MISSING_MODEL_OVERCLAIM_GUARD_RESULTS",
}

CREATED_REQUIRED_PATH_CODES = {
    "metadata_path": "MISSING_METADATA",
    "model_weights_reference_path": "MISSING_MODEL_WEIGHTS_REFERENCE",
    "model_version_metadata_path": "MISSING_MODEL_VERSION_METADATA",
    "parameter_version_metadata_path": "MISSING_PARAMETER_VERSION_METADATA",
    "threshold_plan_path": "MISSING_THRESHOLD_PLAN",
    "prediction_rows_path": "MISSING_PREDICTION_ROWS",
    "probability_calibration_report_path": "MISSING_PROBABILITY_CALIBRATION_REPORT",
    "feature_importance_report_path": "MISSING_FEATURE_IMPORTANCE_REPORT",
    "model_input_index_path": "MISSING_MODEL_INPUT_INDEX",
    "model_lineage_matrix_path": "MISSING_MODEL_LINEAGE_MATRIX",
    "model_limitations_path": "MISSING_MODEL_LIMITATIONS",
    "model_overfit_warnings_path": "MISSING_MODEL_OVERFIT_WARNINGS",
    "model_safety_flags_path": "MISSING_MODEL_SAFETY_FLAGS",
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
    "report-only research artifacts",
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
    "active_stock_profile*",
    "stock_profile*",
    "buy_review*",
    "paper_approval*",
    "approved_for_paper*",
    "performance_validation*",
    "strategy_performance*",
    "broker*",
    "order*",
    "trade*",
    "message*",
    "active_model_pointer*",
    "promoted_model_pointer*",
    "production_model_pointer*",
    "scheduler*",
    "cron*",
    "current_candidates*",
    "snapshot*",
}

POSITIVE_OVERCLAIM_PHRASES = [
    "stock-profile readiness",
    "buy-review readiness",
    "paper approval granted",
    "approved for paper",
    "strategy performance validated",
    "performance validation passed",
    "production readiness",
    "real-trading readiness",
    "trading permission",
    "profitability proof",
]


@dataclass(frozen=True)
class ModelWeightVersioningHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_model_weight_versioning_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ModelWeightVersioningHealthResult:
    index = build_model_weight_versioning_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_MODEL_WEIGHT_VERSIONING_ARTIFACT_FOUND", "No model weight versioning artifacts found.", root))
    else:
        for row in index.index_frame.to_dict("records"):
            issues.extend(_issues_for_row(row))
    frame = _finalize(pd.DataFrame(issues, dtype=object))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "model_weight_versioning_health.csv",
        "health_report": Path(output_dir) / "model_weight_versioning_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ModelWeightVersioningHealthResult(
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
    run_id = _text(row.get("model_workflow_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []
    _ensure_manual_diagnostics_issues(run_id, artifact_path, issues)
    if status not in ALLOWED_STATUSES:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_MODEL_WEIGHT_VERSIONING_STATUS", f"Unknown status: {status}", artifact_path))
    for field, code in ALWAYS_REQUIRED_PATH_CODES.items():
        _require_path(run_id, Path(_text(row.get(field))), code, issues)
    _forbidden_artifact_issues(run_id, artifact_path, issues)
    _created_state_issues(row, issues)
    if status == MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED:
        for field, code in CREATED_REQUIRED_PATH_CODES.items():
            _require_path(run_id, Path(_text(row.get(field))), code, issues)
        issues.extend(_model_weights_reference_issues(run_id, Path(_text(row.get("model_weights_reference_path")))))
        issues.extend(_model_version_issues(run_id, Path(_text(row.get("model_version_metadata_path")))))
        issues.extend(_parameter_version_issues(run_id, Path(_text(row.get("parameter_version_metadata_path")))))
        issues.extend(_threshold_plan_issues(run_id, Path(_text(row.get("threshold_plan_path")))))
        issues.extend(_prediction_rows_issues(run_id, Path(_text(row.get("prediction_rows_path")))))
        issues.extend(_probability_calibration_issues(run_id, Path(_text(row.get("probability_calibration_report_path")))))
        issues.extend(_feature_importance_issues(run_id, Path(_text(row.get("feature_importance_report_path")))))
        issues.extend(_metric_evidence_issues(run_id, row))
        issues.extend(_input_index_issues(run_id, Path(_text(row.get("model_input_index_path")))))
        issues.extend(_lineage_issues(run_id, Path(_text(row.get("model_lineage_matrix_path")))))
        issues.extend(_limitations_issues(run_id, Path(_text(row.get("model_limitations_path")))))
        issues.extend(_overfit_warning_issues(run_id, Path(_text(row.get("model_overfit_warnings_path")))))
    issues.extend(_report_wording_issues(run_id, Path(_text(row.get("report_path")))))
    for field in DOWNSTREAM_FALSE_FIELDS:
        if _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", f"{field.upper()}_UNEXPECTED", f"Unsafe false-expected field is true: {field}", artifact_path))
    for field in ["report_only", "diagnostic_only"]:
        if not _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", "REPORT_ONLY_FLAGS_MISSING", f"Missing or false flag: {field}", artifact_path))
    return issues


def _created_state_issues(row: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    run_id = _text(row.get("model_workflow_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    metadata = _read_json(Path(_text(row.get("metadata_path"))))
    safety = _read_json(Path(_text(row.get("model_safety_flags_path"))))
    status = _text(row.get("status"))
    row_created = _to_bool(row.get("model_weight_versioning_research_artifacts_created"))
    metadata_created = _to_bool(metadata.get("model_weight_versioning_research_artifacts_created"))
    safety_created = _to_bool(safety.get("model_weight_versioning_research_artifacts_created"))
    if status == MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED and not (row_created and metadata_created and safety_created):
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "MODEL_RESEARCH_ARTIFACTS_CREATED_FLAG_FALSE",
                "model_weight_versioning_research_artifacts_created must be true for created status.",
                artifact_path,
            )
        )
    if status in {NO_MODEL_WEIGHT_VERSIONING_INPUT, READY_FOR_MODEL_WEIGHT_VERSIONING} and (row_created or metadata_created or safety_created):
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "MODEL_RESEARCH_ARTIFACTS_CREATED_UNEXPECTED",
                "model_weight_versioning_research_artifacts_created must remain false before created status.",
                artifact_path,
            )
        )


def _model_weights_reference_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    if not payload:
        return []
    text = json.dumps(payload, sort_keys=True).lower()
    reference_type = _text(payload.get("reference_type")).lower()
    forbidden = _text(payload.get("forbidden_interpretation")).lower()
    if "report_only_reference" not in reference_type or any(token in reference_type for token in ["executable", "binary", "estimator", "trading"]):
        return [_issue(run_id, "ERROR", "MODEL_WEIGHTS_REFERENCE_EXECUTABLE", "Model weights reference must be report-only, not executable.", path)]
    if "executable trading model" not in forbidden or "stock_profile allowed" in text or "trading permission allowed" in text:
        return [_issue(run_id, "ERROR", "MODEL_WEIGHTS_REFERENCE_EXECUTABLE", "Model weights reference must forbid executable model, stock_profile, paper/performance and trading interpretations.", path)]
    return []


def _model_version_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    issues = []
    for field, code in [
        ("active_model", "MODEL_VERSION_ACTIVE_UNEXPECTED"),
        ("promoted_model", "MODEL_VERSION_PROMOTED_UNEXPECTED"),
        ("production_model", "MODEL_VERSION_PRODUCTION_UNEXPECTED"),
    ]:
        if _to_bool(payload.get(field)):
            issues.append(_issue(run_id, "ERROR", code, f"model_version_metadata has {field}=true.", path))
    return issues


def _parameter_version_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    if _to_bool(payload.get("active_parameters")):
        return [_issue(run_id, "ERROR", "PARAMETER_VERSION_ACTIVE_UNEXPECTED", "parameter_version_metadata has active_parameters=true.", path)]
    return []


def _threshold_plan_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty:
        return []
    text = _frame_text(rows)
    unsafe = _strip_safe_negations(text)
    if "signal_semantics changed" in unsafe or "active thresholds" in unsafe or "buy/sell candidates" in unsafe:
        return [_issue(run_id, "ERROR", "THRESHOLD_PLAN_ACTIVE_UNEXPECTED", "Threshold plan implies signal semantics changes or active thresholds.", path)]
    return []


def _prediction_rows_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty:
        return []
    text = _strip_safe_negations(_frame_text(rows))
    if "advisory signals" in text or "current-candidates" in text or "trading permission" in text:
        return [_issue(run_id, "ERROR", "PREDICTION_ROWS_ADVISORY_UNEXPECTED", "Prediction rows imply advisory/current-candidates/trading semantics.", path)]
    return []


def _probability_calibration_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = _strip_safe_negations(path.read_text(encoding="utf-8").lower())
    if "active probabilities" in text or "buy/sell candidates" in text:
        return [_issue(run_id, "ERROR", "PROBABILITY_CALIBRATION_ACTIVE_UNEXPECTED", "Probability calibration report implies active probabilities.", path)]
    return []


def _feature_importance_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty:
        return []
    text = _strip_safe_negations(_frame_text(rows))
    if "active stock_profile explanation" in text or "buy-review explanation" in text or "trading signal" in text:
        return [_issue(run_id, "ERROR", "FEATURE_IMPORTANCE_ACTIVE_PROFILE_UNEXPECTED", "Feature importance implies active stock_profile or buy-review explanation.", path)]
    return []


def _metric_evidence_issues(run_id: str, row: dict[str, Any]) -> list[dict[str, Any]]:
    metric_names = {name.strip() for name in _text(row.get("metric_evidence_names_present")).split(",") if name.strip()}
    missing = sorted(REQUIRED_METRIC_EVIDENCE - metric_names)
    issues: list[dict[str, Any]] = []
    if missing:
        issues.append(_issue(run_id, "ERROR", "METRIC_EVIDENCE_REQUIRED_METRIC_MISSING", f"Missing metric evidence: {','.join(missing)}", row.get("metadata_path", "")))
    if _contains_positive_overclaim(",".join(metric_names)):
        issues.append(_issue(run_id, "ERROR", "METRIC_EVIDENCE_OVERCLAIM", "Metric evidence is interpreted as strategy validation or profitability proof.", row.get("metadata_path", "")))
    return issues


def _input_index_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty:
        return []
    missing = INPUT_INDEX_REQUIRED_COLUMNS - set(rows.columns)
    if missing:
        return [_issue(run_id, "ERROR", "MODEL_INPUT_INDEX_LINEAGE_MISSING", f"Model input index missing columns: {','.join(sorted(missing))}", path)]
    if rows["source_run_id"].fillna("").astype(str).str.strip().eq("").any():
        return [_issue(run_id, "ERROR", "MODEL_INPUT_INDEX_LINEAGE_MISSING", "Model input index has blank source_run_id.", path)]
    return []


def _lineage_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty or "lineage_item" not in rows.columns:
        return []
    observed_items = set(rows["lineage_item"].dropna().astype(str))
    missing_source = sorted(LINEAGE_SOURCE_RUN_ITEMS - observed_items)
    if missing_source:
        return [_issue(run_id, "ERROR", "MODEL_LINEAGE_SOURCE_RUN_ID_MISSING", f"Model lineage missing source run IDs: {','.join(missing_source)}", path)]
    missing_coverage = sorted(LINEAGE_COVERAGE_ITEMS - observed_items)
    if missing_coverage:
        return [_issue(run_id, "ERROR", "MODEL_LINEAGE_COVERAGE_MISSING", f"Model lineage missing coverage fields: {','.join(missing_coverage)}", path)]
    if "source_value" in rows.columns and rows.loc[rows["lineage_item"].isin(LINEAGE_SOURCE_RUN_ITEMS | LINEAGE_COVERAGE_ITEMS), "source_value"].fillna("").astype(str).str.strip().eq("").any():
        return [_issue(run_id, "ERROR", "MODEL_LINEAGE_COVERAGE_MISSING", "Model lineage has blank source or coverage values.", path)]
    return []


def _limitations_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").lower()
    missing = [phrase for phrase in LIMITATION_PHRASES if phrase not in text]
    if missing:
        return [_issue(run_id, "ERROR", "MODEL_LIMITATIONS_WORDING_MISSING", f"Model limitations missing phrases: {','.join(missing)}", path)]
    return []


def _overfit_warning_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty or "risk_item" not in rows.columns:
        return []
    missing = REQUIRED_OVERFIT_WARNINGS - set(rows["risk_item"].dropna().astype(str))
    if missing:
        return [_issue(run_id, "ERROR", "MODEL_OVERFIT_WARNING_MISSING", f"Model overfit warnings missing: {','.join(sorted(missing))}", path)]
    return []


def _report_wording_issues(run_id: str, report_path: Path) -> list[dict[str, Any]]:
    if not report_path.exists():
        return []
    text = report_path.read_text(encoding="utf-8").lower()
    if _contains_positive_overclaim(text):
        return [_issue(run_id, "ERROR", "REPORT_OVERCLAIM_WORDING", "Report contains stock-profile, buy-review, paper/performance, production or trading overclaim wording.", report_path)]
    return []


def _contains_positive_overclaim(text: str) -> bool:
    normalized = _strip_safe_negations(text.lower())
    return any(phrase in normalized for phrase in POSITIVE_OVERCLAIM_PHRASES)


def _strip_safe_negations(text: str) -> str:
    normalized = text.lower()
    for safe_phrase in [
        "not active stock_profile",
        "not stock_profile",
        "no stock_profile",
        "not buy-review",
        "no buy-review",
        "not paper approval",
        "no paper approval",
        "not performance validation",
        "no performance validation",
        "not strategy performance validation",
        "not trading",
        "no trading",
        "not executable trading model",
        "not active/promoted/production model",
        "no signal_semantics change",
        "no active thresholds",
        "not advisory signals",
        "not current-candidates",
        "not trading permission",
        "not buy-review explanation",
        "not trading signal",
        "no active probabilities",
        "no buy/sell candidates",
    ]:
        normalized = normalized.replace(safe_phrase, "")
    return normalized


def _frame_text(frame: pd.DataFrame) -> str:
    return " ".join(frame.astype(str).fillna("").agg(" ".join, axis=1).str.lower())


def _forbidden_artifact_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    for child in (artifact_path.iterdir() if artifact_path.exists() else []):
        name = child.name.lower()
        if any(fnmatch.fnmatch(name, pattern) for pattern in FORBIDDEN_ARTIFACT_PATTERNS):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_ARTIFACT_PRESENT", f"Forbidden active/downstream artifact present: {child.name}", child))


def _require_path(run_id: str, path: Path, code: str, issues: list[dict[str, Any]]) -> None:
    if not _text(path) or not path.exists():
        issues.append(_issue(run_id, "ERROR", code, f"Required model weight versioning artifact missing: {path}", path))


def _ensure_manual_diagnostics_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    parts = {part.lower() for part in artifact_path.parts}
    if "outputs" not in parts or "reports" not in parts or "manual_diagnostics" not in parts:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "ARTIFACT_PATH_OUTSIDE_MANUAL_DIAGNOSTICS",
                "Model weight versioning artifacts must remain under outputs/reports/manual_diagnostics.",
                artifact_path,
            )
        )


def _write(result: ModelWeightVersioningHealthResult) -> None:
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
                "# Model Weight Versioning Health",
                "",
                "Report-only health for model weights/versioning/threshold/prediction phase 1 artifacts. It fails if outputs imply executable trading models, active/promoted/production models, active thresholds, advisory predictions, stock_profile, buy-review, paper approval, performance validation, broker/order/message/API/cache/data side effects, current-candidates, snapshots, signal semantics mutation, or trading.",
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
        "model_workflow_run_id": run_id,
        "severity": severity,
        "issue_code": issue_code,
        "message": message,
        "artifact_path": str(artifact_path),
    }


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]
