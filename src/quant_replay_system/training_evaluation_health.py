"""Health checks for report-only training/evaluation phase 1 artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.training_evaluation import (
    NO_TRAINING_EVALUATION_INPUT,
    READY_FOR_TRAINING_EVALUATION_DATASET,
    TRAINING_EVALUATION_APPROVAL_BLOCKED,
    TRAINING_EVALUATION_DATASET_BOUNDARY_BLOCKED,
    TRAINING_EVALUATION_DATASET_CREATED,
    TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED,
    TRAINING_EVALUATION_FORWARD_LABEL_BLOCKED,
    TRAINING_EVALUATION_FROZEN_DECISION_BLOCKED,
    TRAINING_EVALUATION_LABEL_PLAN_BLOCKED,
    TRAINING_EVALUATION_LEAKAGE_BLOCKED,
    TRAINING_EVALUATION_LINEAGE_BLOCKED,
    TRAINING_EVALUATION_METRIC_BLOCKED,
    TRAINING_EVALUATION_OVERCLAIM_BLOCKED,
    TRAINING_EVALUATION_REVIEW_BLOCKED,
    TRAINING_EVALUATION_SIDE_EFFECT_BLOCKED,
    TRAINING_EVALUATION_SPLIT_BLOCKED,
)
from quant_replay_system.training_evaluation_index import DEFAULT_ROOT, build_training_evaluation_index


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"
HEALTH_COLUMNS = ["training_evaluation_run_id", "severity", "issue_code", "message", "artifact_path"]

ALLOWED_STATUSES = {
    NO_TRAINING_EVALUATION_INPUT,
    TRAINING_EVALUATION_APPROVAL_BLOCKED,
    TRAINING_EVALUATION_LINEAGE_BLOCKED,
    TRAINING_EVALUATION_FORWARD_LABEL_BLOCKED,
    TRAINING_EVALUATION_FROZEN_DECISION_BLOCKED,
    TRAINING_EVALUATION_DATASET_BOUNDARY_BLOCKED,
    TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED,
    TRAINING_EVALUATION_SPLIT_BLOCKED,
    TRAINING_EVALUATION_LABEL_PLAN_BLOCKED,
    TRAINING_EVALUATION_METRIC_BLOCKED,
    TRAINING_EVALUATION_LEAKAGE_BLOCKED,
    TRAINING_EVALUATION_SIDE_EFFECT_BLOCKED,
    TRAINING_EVALUATION_OVERCLAIM_BLOCKED,
    TRAINING_EVALUATION_REVIEW_BLOCKED,
    READY_FOR_TRAINING_EVALUATION_DATASET,
    TRAINING_EVALUATION_DATASET_CREATED,
}
SAMPLE_REQUIRED_COLUMNS = {
    "replay_decision_id",
    "replay_decision_freeze_run_id",
    "forward_return_label_run_id",
    "symbol",
    "label_name",
    "label_horizon_trading_days",
    "label_start_date",
    "label_end_date",
    "label_value",
    "label_source_field",
    "split_role",
}
FORBIDDEN_OUTPUT_COLUMNS = {
    "hit_rate",
    "average_return",
    "median_return",
    "benchmark_relative_performance",
    "industry_relative_performance",
    "ic",
    "sharpe",
    "profit_loss_ratio",
    "model_weight",
    "model_version",
    "threshold_optimized",
    "prediction",
    "calibrated_probability",
    "feature_importance",
    "stock_profile_status",
    "stock_profile_validated",
    "real_buy_review_eligible",
    "approved_for_paper",
    "strategy_performance_validated",
    "order_id",
    "broker_order_id",
    "trade_id",
}
UNSAFE_FALSE_FIELDS = [
    "metrics_computed",
    "training_allowed",
    "weights_trained",
    "training_result_created",
    "model_version_created",
    "thresholds_optimized",
    "predictions_created",
    "calibrated_probabilities_created",
    "feature_importance_created",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "stock_profile_created",
    "buy_review_allowed",
    "real_buy_review_eligible",
    "approved_for_paper",
    "strategy_performance_validated",
    "trading_allowed",
    "order_placed",
    "broker_api_called",
    "message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
]


@dataclass(frozen=True)
class TrainingEvaluationHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_training_evaluation_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> TrainingEvaluationHealthResult:
    index = build_training_evaluation_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_TRAINING_EVALUATION_ARTIFACT_FOUND", "No training/evaluation artifacts found.", root))
    else:
        for row in index.index_frame.to_dict("records"):
            issues.extend(_issues_for_row(row))
    frame = _finalize(pd.DataFrame(issues, dtype=object))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "training_evaluation_health.csv",
        "health_report": Path(output_dir) / "training_evaluation_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = TrainingEvaluationHealthResult(
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
    run_id = _text(row.get("training_evaluation_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []

    _ensure_manual_diagnostics_issues(run_id, artifact_path, issues)
    for path, code in [
        (Path(_text(row.get("metadata_path"))), "MISSING_METADATA"),
        (Path(_text(row.get("report_path"))), "MISSING_REPORT"),
        (Path(_text(row.get("safety_flags_path"))), "MISSING_SAFETY_FLAGS"),
    ]:
        if not _text(path) or not path.exists():
            issues.append(_issue(run_id, "ERROR", code, f"Required training/evaluation artifact missing: {path}", path))

    if status not in ALLOWED_STATUSES:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_TRAINING_EVALUATION_STATUS", f"Unknown status: {status}", artifact_path))

    if _to_bool(row.get("training_evaluation_dataset_artifacts_created")) and status != TRAINING_EVALUATION_DATASET_CREATED:
        issues.append(_issue(run_id, "ERROR", "DATASET_CREATED_WITHOUT_CREATED_STATUS", "Dataset artifacts flag can be true only with TRAINING_EVALUATION_DATASET_CREATED.", artifact_path))

    sample_path = Path(_text(row.get("sample_rows_path")))
    dataset_index_path = Path(_text(row.get("dataset_index_path")))
    label_coverage_path = Path(_text(row.get("label_coverage_report_path")))
    sample_rows = _read_csv(sample_path) if sample_path.exists() else pd.DataFrame()
    if status == TRAINING_EVALUATION_DATASET_CREATED:
        for path, code in [
            (dataset_index_path, "DATASET_CREATED_WITHOUT_DATASET_INDEX"),
            (sample_path, "DATASET_CREATED_WITHOUT_SAMPLE_ROWS"),
            (label_coverage_path, "DATASET_CREATED_WITHOUT_LABEL_COVERAGE_REPORT"),
        ]:
            if not path.exists():
                issues.append(_issue(run_id, "ERROR", code, f"TRAINING_EVALUATION_DATASET_CREATED requires artifact: {path}", path))
        if sample_path.exists() and sample_rows.empty:
            issues.append(_issue(run_id, "ERROR", "DATASET_CREATED_WITH_EMPTY_SAMPLE_ROWS", "TRAINING_EVALUATION_DATASET_CREATED requires bounded sample rows.", sample_path))

    if sample_path.exists() and not sample_rows.empty:
        issues.extend(_sample_row_issues(run_id, sample_path, sample_rows))

    for field in UNSAFE_FALSE_FIELDS:
        if _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", f"{field.upper()}_UNEXPECTED", f"Unsafe false-expected field is true: {field}", artifact_path))
    for field in ["report_only", "diagnostic_only"]:
        if not _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", "UNSAFE_REPORT_ONLY_FLAGS", f"Missing or false flag: {field}", artifact_path))
    return issues


def _sample_row_issues(run_id: str, path: Path, frame: pd.DataFrame) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    missing = sorted(SAMPLE_REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        issues.append(_issue(run_id, "ERROR", "SAMPLE_ROWS_REQUIRED_COLUMNS_MISSING", f"Sample rows missing required columns: {','.join(missing)}", path))
    lower_columns = {column.lower() for column in frame.columns}
    matched = sorted(lower_columns & FORBIDDEN_OUTPUT_COLUMNS)
    if matched:
        issues.append(_issue(run_id, "ERROR", "SAMPLE_ROWS_FORBIDDEN_COLUMNS", f"Forbidden columns in sample rows: {','.join(matched)}", path))
    return issues


def _ensure_manual_diagnostics_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    parts = {part.lower() for part in artifact_path.parts}
    if "outputs" not in parts or "reports" not in parts or "manual_diagnostics" not in parts:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "ARTIFACT_PATH_OUTSIDE_MANUAL_DIAGNOSTICS",
                "Training/evaluation artifacts must remain under outputs/reports/manual_diagnostics.",
                artifact_path,
            )
        )


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, dtype={"symbol": "string"})
    except Exception:
        return pd.DataFrame()


def _issue(run_id: str, severity: str, code: str, message: str, path: str | Path) -> dict[str, Any]:
    return {
        "training_evaluation_run_id": run_id,
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    for column in HEALTH_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[HEALTH_COLUMNS]


def _write(result: TrainingEvaluationHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "health_id": _hash_payload(result.health_frame.to_dict("records")),
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
                "# Training / Evaluation Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                "Health keeps training/evaluation phase 1 report-only dataset/planning-only and fails if artifacts imply metrics, training_result, weights, model_version, thresholds, predictions, probabilities, feature importance, stock_profile, buy-review, paper approval, performance validation, broker/order/message/API/cache/data side effects, snapshots, current-candidates, signal semantics mutation, or trading.",
                "",
                result.health_frame.to_markdown(index=False) if not result.health_frame.empty else "No health issues found.",
            ]
        ),
        encoding="utf-8",
    )


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]
