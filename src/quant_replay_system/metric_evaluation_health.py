"""Health checks for report-only metric/evaluation phase 1 structural planning artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.metric_evaluation import (
    FORBIDDEN_FALSE_FIELDS,
    METRIC_EVALUATION_APPROVAL_BLOCKED,
    METRIC_EVALUATION_COMPUTATION_BLOCKED,
    METRIC_EVALUATION_DATASET_HEALTH_BLOCKED,
    METRIC_EVALUATION_DATASET_INPUT_BLOCKED,
    METRIC_EVALUATION_DEFINITION_BLOCKED,
    METRIC_EVALUATION_LEAKAGE_BLOCKED,
    METRIC_EVALUATION_LINEAGE_BLOCKED,
    METRIC_EVALUATION_OVERCLAIM_BLOCKED,
    METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED,
    METRIC_EVALUATION_RESULT_ROWS_BLOCKED,
    METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED,
    METRIC_EVALUATION_SIDE_EFFECT_BLOCKED,
    NO_METRIC_EVALUATION_INPUT,
    READY_FOR_METRIC_EVALUATION_PLANNING_ARTIFACTS,
)
from quant_replay_system.metric_evaluation_index import DEFAULT_ROOT, build_metric_evaluation_index


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"
HEALTH_COLUMNS = ["metric_evaluation_run_id", "severity", "issue_code", "message", "artifact_path"]

ALLOWED_STATUSES = {
    NO_METRIC_EVALUATION_INPUT,
    METRIC_EVALUATION_APPROVAL_BLOCKED,
    METRIC_EVALUATION_DATASET_INPUT_BLOCKED,
    METRIC_EVALUATION_DATASET_HEALTH_BLOCKED,
    METRIC_EVALUATION_LINEAGE_BLOCKED,
    METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED,
    METRIC_EVALUATION_DEFINITION_BLOCKED,
    METRIC_EVALUATION_COMPUTATION_BLOCKED,
    METRIC_EVALUATION_RESULT_ROWS_BLOCKED,
    METRIC_EVALUATION_LEAKAGE_BLOCKED,
    METRIC_EVALUATION_SIDE_EFFECT_BLOCKED,
    METRIC_EVALUATION_OVERCLAIM_BLOCKED,
    READY_FOR_METRIC_EVALUATION_PLANNING_ARTIFACTS,
    METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED,
}

CREATED_REQUIRED_ARTIFACTS = {
    "input_index_path": "PLANNING_CREATED_WITHOUT_INPUT_INDEX",
    "metric_definitions_path": "PLANNING_CREATED_WITHOUT_METRIC_DEFINITIONS",
    "sample_scope_path": "PLANNING_CREATED_WITHOUT_SAMPLE_SCOPE",
    "denominator_rules_path": "PLANNING_CREATED_WITHOUT_DENOMINATOR_RULES",
    "health_status_plan_path": "PLANNING_CREATED_WITHOUT_HEALTH_STATUS_PLAN",
    "research_status_plan_path": "PLANNING_CREATED_WITHOUT_RESEARCH_STATUS_PLAN",
}

METRIC_DEFINITION_REQUIRED_COLUMNS = {
    "metric_name",
    "definition_plain_language",
    "computation_allowed_in_current_phase",
    "result_rows_allowed_in_current_phase",
    "requires_future_exact_approval",
    "report_only",
    "diagnostic_only",
}

FORBIDDEN_OUTPUT_COLUMNS = {
    "computed_value",
    "metric_value",
    "hit_rate_value",
    "average_return_value",
    "median_return_value",
    "benchmark_relative_performance",
    "industry_relative_performance",
    "ic_value",
    "sharpe_value",
    "profit_loss_ratio_value",
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

UNSAFE_FALSE_FIELDS = ["approval_applied", "clean_review_updates_created", *FORBIDDEN_FALSE_FIELDS]


@dataclass(frozen=True)
class MetricEvaluationHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_metric_evaluation_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> MetricEvaluationHealthResult:
    index = build_metric_evaluation_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_METRIC_EVALUATION_ARTIFACT_FOUND", "No metric/evaluation artifacts found.", root))
    else:
        for row in index.index_frame.to_dict("records"):
            issues.extend(_issues_for_row(row))
    frame = _finalize(pd.DataFrame(issues, dtype=object))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "metric_evaluation_health.csv",
        "health_report": Path(output_dir) / "metric_evaluation_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = MetricEvaluationHealthResult(
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
    run_id = _text(row.get("metric_evaluation_run_id"))
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
            issues.append(_issue(run_id, "ERROR", code, f"Required metric/evaluation artifact missing: {path}", path))

    if status not in ALLOWED_STATUSES:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_METRIC_EVALUATION_STATUS", f"Unknown status: {status}", artifact_path))

    created = _to_bool(row.get("metric_evaluation_planning_artifacts_created"))
    if created and status != METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "PLANNING_ARTIFACTS_CREATED_WITHOUT_CREATED_STATUS",
                "Planning artifacts flag can be true only with METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED.",
                artifact_path,
            )
        )

    if status == METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED:
        for field, code in CREATED_REQUIRED_ARTIFACTS.items():
            path = Path(_text(row.get(field)))
            if not path.exists():
                issues.append(_issue(run_id, "ERROR", code, f"Created metric/evaluation planning artifact missing: {path}", path))

    issues.extend(_csv_artifact_issues(run_id, artifact_path, row, created))

    if (artifact_path / "metric_evaluation_result_rows.csv").exists():
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "METRIC_RESULT_ROWS_ARTIFACT_UNEXPECTED",
                "metric_evaluation_result_rows.csv must not exist in report-only phase 1.",
                artifact_path / "metric_evaluation_result_rows.csv",
            )
        )
    for name in ["review_updates.csv", "clean_review_updates.csv", "metric_evaluation_results.csv"]:
        if (artifact_path / name).exists():
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_OUTPUT_ARTIFACT_UNEXPECTED", f"Forbidden output exists: {name}", artifact_path / name))

    for field in UNSAFE_FALSE_FIELDS:
        if _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", f"{field.upper()}_UNEXPECTED", f"Unsafe false-expected field is true: {field}", artifact_path))
    for field in ["report_only", "diagnostic_only"]:
        if not _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", "UNSAFE_REPORT_ONLY_FLAGS", f"Missing or false flag: {field}", artifact_path))
    return issues


def _csv_artifact_issues(run_id: str, artifact_path: Path, row: dict[str, Any], created: bool) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for field in [
        "input_index_path",
        "metric_definitions_path",
        "sample_scope_path",
        "denominator_rules_path",
        "health_status_plan_path",
    ]:
        path = Path(_text(row.get(field)))
        if not path.exists():
            continue
        frame = _read_csv(path)
        lower_columns = {column.lower() for column in frame.columns}
        matched = sorted(lower_columns & FORBIDDEN_OUTPUT_COLUMNS)
        if matched:
            issues.append(_issue(run_id, "ERROR", "CSV_FORBIDDEN_OUTPUT_COLUMNS", f"Forbidden computed/output columns in {path.name}: {','.join(matched)}", path))
        if "symbol" in frame.columns:
            bad_symbols = frame["symbol"].dropna().astype(str).str.strip().loc[lambda values: values.ne("") & values.str.fullmatch(r"\d{1,5}")]
            if not bad_symbols.empty:
                issues.append(_issue(run_id, "ERROR", "LEADING_ZERO_SYMBOL_NOT_PRESERVED", f"Symbol values lost leading zeros in {path.name}.", path))
    metric_definitions_path = Path(_text(row.get("metric_definitions_path")))
    if created and metric_definitions_path.exists():
        definitions = _read_csv(metric_definitions_path)
        missing = sorted(METRIC_DEFINITION_REQUIRED_COLUMNS - set(definitions.columns))
        if missing:
            issues.append(_issue(run_id, "ERROR", "METRIC_DEFINITION_REQUIRED_COLUMNS_MISSING", f"Metric definitions missing required columns: {','.join(missing)}", metric_definitions_path))
        if not definitions.empty:
            for column, expected in [
                ("computation_allowed_in_current_phase", False),
                ("result_rows_allowed_in_current_phase", False),
                ("requires_future_exact_approval", True),
            ]:
                if column in definitions.columns and not definitions[column].map(_to_bool).eq(expected).all():
                    issues.append(_issue(run_id, "ERROR", "METRIC_DEFINITION_PHASE_FLAGS_INVALID", f"Invalid phase flag in {column}.", metric_definitions_path))
    return issues


def _ensure_manual_diagnostics_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    parts = {part.lower() for part in artifact_path.parts}
    if "outputs" not in parts or "reports" not in parts or "manual_diagnostics" not in parts:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "ARTIFACT_PATH_OUTSIDE_MANUAL_DIAGNOSTICS",
                "Metric/evaluation artifacts must remain under outputs/reports/manual_diagnostics.",
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
        "metric_evaluation_run_id": run_id,
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


def _write(result: MetricEvaluationHealthResult) -> None:
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
                "# Metric / Evaluation Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                "Health keeps metric/evaluation phase 1 report-only and fails if artifacts imply computed metrics, metric result rows, training_result, weights, model_version, thresholds, predictions, probabilities, feature importance, stock_profile, buy-review, paper approval, performance validation, broker/order/message/API/cache/data side effects, snapshots, current-candidates, signal semantics mutation, or trading.",
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
