"""Health checks for report-only training result planning phase 1 artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.training_result_planning import (
    DOWNSTREAM_FALSE_FIELDS,
    FORBIDDEN_ARTIFACT_NAMES,
    NO_TRAINING_RESULT_PLANNING_INPUT,
    READY_FOR_TRAINING_RESULT_PLANNING,
    TRAINING_RESULT_PLANNING_APPROVAL_BLOCKED,
    TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED,
    TRAINING_RESULT_PLANNING_DENOMINATOR_BLOCKED,
    TRAINING_RESULT_PLANNING_FORBIDDEN_ARTIFACT_BLOCKED,
    TRAINING_RESULT_PLANNING_FORWARD_LABEL_INPUT_BLOCKED,
    TRAINING_RESULT_PLANNING_HEALTH_BLOCKED,
    TRAINING_RESULT_PLANNING_LEAKAGE_BLOCKED,
    TRAINING_RESULT_PLANNING_LINEAGE_BLOCKED,
    TRAINING_RESULT_PLANNING_METRIC_COMPUTATION_INPUT_BLOCKED,
    TRAINING_RESULT_PLANNING_METRIC_EVALUATION_INPUT_BLOCKED,
    TRAINING_RESULT_PLANNING_METRIC_EVIDENCE_BLOCKED,
    TRAINING_RESULT_PLANNING_METRIC_EXTENSION_INPUT_BLOCKED,
    TRAINING_RESULT_PLANNING_OVERCLAIM_BLOCKED,
    TRAINING_RESULT_PLANNING_REPLAY_FREEZE_INPUT_BLOCKED,
    TRAINING_RESULT_PLANNING_REPORT_ONLY_BLOCKED,
    TRAINING_RESULT_PLANNING_SAMPLE_SCOPE_BLOCKED,
    TRAINING_RESULT_PLANNING_SIDE_EFFECT_BLOCKED,
    TRAINING_RESULT_PLANNING_TRAINING_EVALUATION_INPUT_BLOCKED,
)
from quant_replay_system.training_result_planning_index import DEFAULT_ROOT, build_training_result_planning_index
from quant_replay_system.training_result_planning_index import _read_csv, _text, _to_bool


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"
HEALTH_COLUMNS = ["training_result_planning_run_id", "severity", "issue_code", "message", "artifact_path"]

ALLOWED_STATUSES = {
    NO_TRAINING_RESULT_PLANNING_INPUT,
    TRAINING_RESULT_PLANNING_APPROVAL_BLOCKED,
    TRAINING_RESULT_PLANNING_METRIC_EXTENSION_INPUT_BLOCKED,
    TRAINING_RESULT_PLANNING_METRIC_COMPUTATION_INPUT_BLOCKED,
    TRAINING_RESULT_PLANNING_METRIC_EVALUATION_INPUT_BLOCKED,
    TRAINING_RESULT_PLANNING_TRAINING_EVALUATION_INPUT_BLOCKED,
    TRAINING_RESULT_PLANNING_FORWARD_LABEL_INPUT_BLOCKED,
    TRAINING_RESULT_PLANNING_REPLAY_FREEZE_INPUT_BLOCKED,
    TRAINING_RESULT_PLANNING_HEALTH_BLOCKED,
    TRAINING_RESULT_PLANNING_LINEAGE_BLOCKED,
    TRAINING_RESULT_PLANNING_METRIC_EVIDENCE_BLOCKED,
    TRAINING_RESULT_PLANNING_DENOMINATOR_BLOCKED,
    TRAINING_RESULT_PLANNING_SAMPLE_SCOPE_BLOCKED,
    TRAINING_RESULT_PLANNING_REPORT_ONLY_BLOCKED,
    TRAINING_RESULT_PLANNING_FORBIDDEN_ARTIFACT_BLOCKED,
    TRAINING_RESULT_PLANNING_LEAKAGE_BLOCKED,
    TRAINING_RESULT_PLANNING_SIDE_EFFECT_BLOCKED,
    TRAINING_RESULT_PLANNING_OVERCLAIM_BLOCKED,
    READY_FOR_TRAINING_RESULT_PLANNING,
    TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED,
}

SUBSTANTIVE_PATH_FIELDS = [
    "input_index_path",
    "metric_evidence_index_path",
    "lineage_matrix_path",
    "model_scope_path",
    "limitations_path",
    "overfit_warnings_path",
    "health_plan_path",
    "status_plan_path",
]

CREATED_REQUIRED_PATH_CODES = {
    "metadata_path": "MISSING_METADATA",
    "report_path": "MISSING_REPORT",
    "input_index_path": "MISSING_INPUT_INDEX",
    "metric_evidence_index_path": "MISSING_METRIC_EVIDENCE_INDEX",
    "lineage_matrix_path": "MISSING_LINEAGE_MATRIX",
    "model_scope_path": "MISSING_MODEL_SCOPE",
    "limitations_path": "MISSING_LIMITATIONS",
    "overfit_warnings_path": "MISSING_OVERFIT_WARNINGS",
    "health_plan_path": "MISSING_HEALTH_PLAN",
    "status_plan_path": "MISSING_STATUS_PLAN",
    "safety_flags_path": "MISSING_SAFETY_FLAGS",
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

LINEAGE_REQUIRED_COLUMNS = {
    "metric_extension_run_id",
    "metric_computation_run_id",
    "metric_evaluation_run_id",
    "training_evaluation_run_id",
    "forward_return_label_run_id",
    "replay_decision_freeze_run_id",
    "source_hash",
    "revision_id",
    "available_time",
    "quality_status",
}

FORBIDDEN_SCOPE_ITEMS = {
    "model_weights",
    "model_version",
    "parameter_version",
    "thresholds",
    "predictions",
    "calibrated_probabilities",
    "feature_importance",
}

LIMITATION_PHRASES = [
    "report-only planning artifacts",
    "not actual training_result",
    "not weights",
    "not model_version",
    "not parameter_version",
    "not thresholds",
    "not predictions/probabilities/feature importance",
    "not stock_profile",
    "not buy-review",
    "not paper approval",
    "not performance validation",
    "not trading",
]

REQUIRED_OVERFIT_WARNINGS = {
    "small sample",
    "class imbalance",
    "single-stock overfit",
    "metric selection bias",
    "lookahead leakage",
}

REQUIRED_HEALTH_GATES = {"upstream health PASS", "lineage complete", "report-only flags"}
REQUIRED_STATUS_FALSE_FIELDS = {
    "training_result_created",
    "weights_trained",
    "model_version_created",
    "parameter_version_created",
    "thresholds_optimized",
    "predictions_created",
    "stock_profile_created",
    "approved_for_paper",
    "strategy_performance_validated",
    "trading_allowed",
}

OVERCLAIM_PHRASES = [
    "actual training_result",
    "strategy validation passed",
    "strategy performance validated",
    "validates profitability",
    "trading permission",
    "stock-profile readiness",
    "buy-review readiness",
    "paper approval granted",
]


@dataclass(frozen=True)
class TrainingResultPlanningHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_training_result_planning_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> TrainingResultPlanningHealthResult:
    index = build_training_result_planning_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_TRAINING_RESULT_PLANNING_ARTIFACT_FOUND", "No training result planning artifacts found.", root))
    else:
        for row in index.index_frame.to_dict("records"):
            issues.extend(_issues_for_row(row))
    frame = _finalize(pd.DataFrame(issues, dtype=object))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "training_result_planning_health.csv",
        "health_report": Path(output_dir) / "training_result_planning_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = TrainingResultPlanningHealthResult(
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
    run_id = _text(row.get("training_result_planning_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []
    _ensure_manual_diagnostics_issues(run_id, artifact_path, issues)
    if status not in ALLOWED_STATUSES:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_TRAINING_RESULT_PLANNING_STATUS", f"Unknown status: {status}", artifact_path))
    _require_path(run_id, Path(_text(row.get("metadata_path"))), "MISSING_METADATA", issues)
    _require_path(run_id, Path(_text(row.get("report_path"))), "MISSING_REPORT", issues)
    _require_path(run_id, Path(_text(row.get("safety_flags_path"))), "MISSING_SAFETY_FLAGS", issues)
    _forbidden_artifact_issues(run_id, artifact_path, issues)

    substantive_exists = any(Path(_text(row.get(field))).exists() for field in SUBSTANTIVE_PATH_FIELDS)
    if status != TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED and substantive_exists:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "SUBSTANTIVE_PLANNING_ARTIFACT_WITHOUT_CREATED_STATUS",
                "Substantive planning artifacts can exist only with TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED.",
                artifact_path,
            )
        )
    if status == TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED:
        for field, code in CREATED_REQUIRED_PATH_CODES.items():
            _require_path(run_id, Path(_text(row.get(field))), code, issues)
        _created_flag_issues(run_id, artifact_path, row, issues)
        issues.extend(_metric_evidence_issues(run_id, Path(_text(row.get("metric_evidence_index_path")))))
        issues.extend(_input_index_issues(run_id, Path(_text(row.get("input_index_path")))))
        issues.extend(_lineage_issues(run_id, Path(_text(row.get("lineage_matrix_path")))))
        issues.extend(_model_scope_issues(run_id, Path(_text(row.get("model_scope_path")))))
        issues.extend(_limitations_issues(run_id, Path(_text(row.get("limitations_path")))))
        issues.extend(_overfit_warning_issues(run_id, Path(_text(row.get("overfit_warnings_path")))))
        issues.extend(_health_plan_issues(run_id, Path(_text(row.get("health_plan_path")))))
        issues.extend(_status_plan_issues(run_id, Path(_text(row.get("status_plan_path")))))
    issues.extend(_report_wording_issues(run_id, Path(_text(row.get("report_path")))))
    for field in DOWNSTREAM_FALSE_FIELDS:
        if _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", f"{field.upper()}_UNEXPECTED", f"Unsafe false-expected field is true: {field}", artifact_path))
    for field in ["report_only", "diagnostic_only"]:
        if not _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", "REPORT_ONLY_FLAGS_MISSING", f"Missing or false flag: {field}", artifact_path))
    return issues


def _created_flag_issues(run_id: str, artifact_path: Path, row: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    expected = {
        "training_result_planning_artifacts_created": "ARTIFACTS_CREATED_FLAG_FALSE",
        "model_scope_rows_created": "MODEL_SCOPE_FLAG_FALSE",
        "limitations_created": "LIMITATIONS_FLAG_FALSE",
        "overfit_warnings_created": "OVERFIT_WARNINGS_FLAG_FALSE",
        "health_plan_created": "HEALTH_PLAN_FLAG_FALSE",
        "status_plan_created": "STATUS_PLAN_FLAG_FALSE",
    }
    for field, code in expected.items():
        if not _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", code, f"{field} must be true for artifacts-created status.", artifact_path))


def _metric_evidence_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty:
        return []
    issues: list[dict[str, Any]] = []
    columns = set(rows.columns)
    if "metric_name" not in columns:
        issues.append(_issue(run_id, "ERROR", "METRIC_EVIDENCE_REQUIRED_METRIC_MISSING", "metric evidence requires metric_name.", path))
        return issues
    missing = sorted(REQUIRED_METRIC_EVIDENCE - set(rows["metric_name"].dropna().astype(str)))
    if missing:
        issues.append(_issue(run_id, "ERROR", "METRIC_EVIDENCE_REQUIRED_METRIC_MISSING", f"Missing metric evidence: {','.join(missing)}", path))
    if "forbidden_interpretation" not in columns or not ({"accepted_interpretation", "permitted_interpretation"} & columns):
        issues.append(_issue(run_id, "ERROR", "METRIC_EVIDENCE_INTERPRETATION_MISSING", "Metric evidence requires permitted/accepted and forbidden interpretations.", path))
    text = " ".join(rows.astype(str).fillna("").agg(" ".join, axis=1).str.lower())
    for phrase in OVERCLAIM_PHRASES:
        if phrase in text:
            issues.append(_issue(run_id, "ERROR", "METRIC_EVIDENCE_OVERCLAIM", f"Metric evidence contains overclaim wording: {phrase}", path))
            break
    return issues


def _input_index_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty:
        return []
    missing = {"source_run_id", "source_health_status"} - set(rows.columns)
    if missing:
        return [_issue(run_id, "ERROR", "INPUT_INDEX_LINEAGE_MISSING", f"Input index missing columns: {','.join(sorted(missing))}", path)]
    if rows["source_run_id"].fillna("").astype(str).str.strip().eq("").any():
        return [_issue(run_id, "ERROR", "INPUT_INDEX_LINEAGE_MISSING", "Input index has blank source_run_id.", path)]
    return []


def _lineage_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty:
        return []
    missing = LINEAGE_REQUIRED_COLUMNS - set(rows.columns)
    if missing:
        return [_issue(run_id, "ERROR", "LINEAGE_COVERAGE_MISSING", f"Lineage matrix missing columns: {','.join(sorted(missing))}", path)]
    for column in LINEAGE_REQUIRED_COLUMNS:
        if rows[column].fillna("").astype(str).str.strip().eq("").any():
            return [_issue(run_id, "ERROR", "LINEAGE_COVERAGE_MISSING", f"Lineage matrix has blank values in {column}.", path)]
    return []


def _model_scope_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty or "scope_item" not in rows.columns or "allowed_in_phase_1" not in rows.columns:
        return []
    forbidden = rows[rows["scope_item"].astype(str).isin(FORBIDDEN_SCOPE_ITEMS)]
    if forbidden["allowed_in_phase_1"].map(_to_bool).any():
        return [_issue(run_id, "ERROR", "MODEL_SCOPE_FORBIDDEN_ALLOWED", "Model scope allows forbidden training/model outputs.", path)]
    return []


def _limitations_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").lower()
    missing = [phrase for phrase in LIMITATION_PHRASES if phrase not in text]
    if missing:
        return [_issue(run_id, "ERROR", "LIMITATIONS_WORDING_MISSING", f"Limitations missing phrases: {','.join(missing)}", path)]
    return []


def _overfit_warning_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty or "risk_item" not in rows.columns:
        return []
    missing = REQUIRED_OVERFIT_WARNINGS - set(rows["risk_item"].dropna().astype(str))
    if missing:
        return [_issue(run_id, "ERROR", "OVERFIT_WARNING_MISSING", f"Overfit warnings missing: {','.join(sorted(missing))}", path)]
    return []


def _health_plan_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty or "future_gate" not in rows.columns:
        return []
    missing = REQUIRED_HEALTH_GATES - set(rows["future_gate"].dropna().astype(str))
    if missing:
        return [_issue(run_id, "ERROR", "HEALTH_PLAN_GATE_MISSING", f"Health plan missing gates: {','.join(sorted(missing))}", path)]
    return []


def _status_plan_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty or "status_field" not in rows.columns or "expected_value" not in rows.columns:
        return []
    for field in REQUIRED_STATUS_FALSE_FIELDS:
        subset = rows[rows["status_field"].astype(str) == field]
        if subset.empty or subset["expected_value"].map(_to_bool).any():
            return [_issue(run_id, "ERROR", "STATUS_PLAN_FALSE_FIELD_ALLOWED", f"Status plan does not keep {field} false.", path)]
    return []


def _report_wording_issues(run_id: str, report_path: Path) -> list[dict[str, Any]]:
    if not report_path.exists():
        return []
    text = report_path.read_text(encoding="utf-8").lower()
    positive_phrases = [phrase for phrase in OVERCLAIM_PHRASES if phrase != "actual training_result"]
    for phrase in positive_phrases:
        if phrase in text:
            return [_issue(run_id, "ERROR", "REPORT_OVERCLAIM_WORDING", f"Report contains overclaim phrase: {phrase}", report_path)]
    return []


def _forbidden_artifact_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    for child in (artifact_path.iterdir() if artifact_path.exists() else []):
        name = child.name.lower()
        if name in FORBIDDEN_ARTIFACT_NAMES or any(token in name for token in ["model_weight", "threshold_set", "prediction", "probabilit", "feature_importance", "stock_profile", "buy_review", "paper_approval", "broker_order", "trade_id"]):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_ARTIFACT_PRESENT", f"Forbidden actual training/model/trading artifact present: {child.name}", child))


def _require_path(run_id: str, path: Path, code: str, issues: list[dict[str, Any]]) -> None:
    if not _text(path) or not path.exists():
        issues.append(_issue(run_id, "ERROR", code, f"Required training result planning artifact missing: {path}", path))


def _ensure_manual_diagnostics_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    parts = {part.lower() for part in artifact_path.parts}
    if "outputs" not in parts or "reports" not in parts or "manual_diagnostics" not in parts:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "ARTIFACT_PATH_OUTSIDE_MANUAL_DIAGNOSTICS",
                "Training result planning artifacts must remain under outputs/reports/manual_diagnostics.",
                artifact_path,
            )
        )


def _write(result: TrainingResultPlanningHealthResult) -> None:
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
                "# Training Result Planning Health",
                "",
                "Report-only health for training result planning phase 1 artifacts. It fails if planning outputs become actual training_result, weights, model_version, parameter_version, thresholds, predictions, calibrated probabilities, feature importance, stock_profile, buy-review, paper approval, performance validation, broker/order/message/API/cache/data side effects, current-candidates, snapshots, signal semantics mutation, or trading.",
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
        "training_result_planning_run_id": run_id,
        "severity": severity,
        "issue_code": issue_code,
        "message": message,
        "artifact_path": str(artifact_path),
    }


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]
