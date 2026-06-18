"""Health checks for report-only metric extension phase 1 artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.metric_extension import (
    ALLOWED_EXTENSION_METRIC_SET,
    FORBIDDEN_FALSE_FIELDS,
    METRIC_EXTENSION_APPROVAL_BLOCKED,
    METRIC_EXTENSION_BENCHMARK_MAPPING_BLOCKED,
    METRIC_EXTENSION_DENOMINATOR_BLOCKED,
    METRIC_EXTENSION_FORWARD_LABEL_INPUT_BLOCKED,
    METRIC_EXTENSION_HEALTH_BLOCKED,
    METRIC_EXTENSION_INDUSTRY_MAPPING_BLOCKED,
    METRIC_EXTENSION_LEAKAGE_BLOCKED,
    METRIC_EXTENSION_LINEAGE_BLOCKED,
    METRIC_EXTENSION_METRIC_COMPUTATION_INPUT_BLOCKED,
    METRIC_EXTENSION_METRIC_EVALUATION_INPUT_BLOCKED,
    METRIC_EXTENSION_OVERCLAIM_BLOCKED,
    METRIC_EXTENSION_REPLAY_FREEZE_INPUT_BLOCKED,
    METRIC_EXTENSION_REPORT_CREATED,
    METRIC_EXTENSION_RESULT_ROW_BLOCKED,
    METRIC_EXTENSION_RETURN_FIELD_BLOCKED,
    METRIC_EXTENSION_SAMPLE_SCOPE_BLOCKED,
    METRIC_EXTENSION_SIDE_EFFECT_BLOCKED,
    METRIC_EXTENSION_TRAINING_EVALUATION_INPUT_BLOCKED,
    METRIC_EXTENSION_UNSUPPORTED_METRIC_BLOCKED,
    NO_METRIC_EXTENSION_INPUT,
    READY_FOR_METRIC_EXTENSION,
)
from quant_replay_system.metric_extension_index import DEFAULT_ROOT, build_metric_extension_index
from quant_replay_system.metric_extension_index import _read_csv, _text, _to_bool


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"
HEALTH_COLUMNS = ["metric_extension_run_id", "severity", "issue_code", "message", "artifact_path"]

ALLOWED_STATUSES = {
    NO_METRIC_EXTENSION_INPUT,
    METRIC_EXTENSION_APPROVAL_BLOCKED,
    METRIC_EXTENSION_METRIC_COMPUTATION_INPUT_BLOCKED,
    METRIC_EXTENSION_METRIC_EVALUATION_INPUT_BLOCKED,
    METRIC_EXTENSION_TRAINING_EVALUATION_INPUT_BLOCKED,
    METRIC_EXTENSION_FORWARD_LABEL_INPUT_BLOCKED,
    METRIC_EXTENSION_REPLAY_FREEZE_INPUT_BLOCKED,
    METRIC_EXTENSION_HEALTH_BLOCKED,
    METRIC_EXTENSION_LINEAGE_BLOCKED,
    METRIC_EXTENSION_BENCHMARK_MAPPING_BLOCKED,
    METRIC_EXTENSION_INDUSTRY_MAPPING_BLOCKED,
    METRIC_EXTENSION_RETURN_FIELD_BLOCKED,
    METRIC_EXTENSION_DENOMINATOR_BLOCKED,
    METRIC_EXTENSION_SAMPLE_SCOPE_BLOCKED,
    METRIC_EXTENSION_UNSUPPORTED_METRIC_BLOCKED,
    METRIC_EXTENSION_RESULT_ROW_BLOCKED,
    METRIC_EXTENSION_LEAKAGE_BLOCKED,
    METRIC_EXTENSION_SIDE_EFFECT_BLOCKED,
    METRIC_EXTENSION_OVERCLAIM_BLOCKED,
    READY_FOR_METRIC_EXTENSION,
    METRIC_EXTENSION_REPORT_CREATED,
}

PATH_METRIC_NAMES = {"max_drawdown", "max_runup"}
ANALYTIC_METRIC_NAMES = {
    "information_coefficient",
    "ic",
    "rank_information_coefficient",
    "rank_ic",
    "sharpe_like_metric",
    "confidence_interval",
    "out_of_sample_metric",
    "regime_robustness",
}
COST_TRADING_METRIC_NAMES = {"false_positive_cost", "false_negative_opportunity_cost", "turnover", "slippage_sensitivity"}
FORBIDDEN_RESULT_ROW_COLUMNS = {
    "training_result",
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
POSITIVE_OVERCLAIM_PHRASES = [
    "strategy validation passed",
    "validates profitability",
    "validated profitability",
    "profitable strategy",
    "grants trading permission",
    "trading permission",
    "stock-profile readiness",
    "buy-review readiness",
    "paper approval granted",
    "performance validation passed",
    "strategy performance validated",
]


@dataclass(frozen=True)
class MetricExtensionHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_metric_extension_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> MetricExtensionHealthResult:
    index = build_metric_extension_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_METRIC_EXTENSION_ARTIFACT_FOUND", "No metric extension artifacts found.", root))
    else:
        for row in index.index_frame.to_dict("records"):
            issues.extend(_issues_for_row(row))
    frame = _finalize(pd.DataFrame(issues, dtype=object))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "metric_extension_health.csv",
        "health_report": Path(output_dir) / "metric_extension_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = MetricExtensionHealthResult(
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
    run_id = _text(row.get("metric_extension_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []
    _ensure_manual_diagnostics_issues(run_id, artifact_path, issues)
    for path, code in [
        (Path(_text(row.get("metadata_path"))), "MISSING_METADATA"),
        (Path(_text(row.get("report_path"))), "MISSING_REPORT"),
        (Path(_text(row.get("safety_flags_path"))), "MISSING_SAFETY_FLAGS"),
        (Path(_text(row.get("result_rows_path"))), "MISSING_RESULT_ROWS"),
        (Path(_text(row.get("summary_path"))), "MISSING_SUMMARY"),
    ]:
        if not _text(path) or not path.exists():
            issues.append(_issue(run_id, "ERROR", code, f"Required metric extension artifact missing: {path}", path))
    if status not in ALLOWED_STATUSES:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_METRIC_EXTENSION_STATUS", f"Unknown status: {status}", artifact_path))

    result_rows_path = Path(_text(row.get("result_rows_path")))
    summary_path = Path(_text(row.get("summary_path")))
    result_rows = _read_csv(result_rows_path)
    summary_rows = _read_csv(summary_path)
    result_row_count = len(result_rows)
    summary_row_count = len(summary_rows)

    if status != METRIC_EXTENSION_REPORT_CREATED and result_row_count > 0:
        issues.append(_issue(run_id, "ERROR", "RESULT_ROWS_WITHOUT_REPORT_CREATED_STATUS", "Result rows can exist only with METRIC_EXTENSION_REPORT_CREATED.", result_rows_path))
    if status == METRIC_EXTENSION_REPORT_CREATED:
        if result_row_count == 0:
            issues.append(_issue(run_id, "ERROR", "REPORT_CREATED_WITHOUT_RESULT_ROWS", "METRIC_EXTENSION_REPORT_CREATED requires result rows.", result_rows_path))
        if summary_row_count == 0:
            issues.append(_issue(run_id, "ERROR", "REPORT_CREATED_WITHOUT_SUMMARY", "METRIC_EXTENSION_REPORT_CREATED requires summary rows.", summary_path))
        if not _to_bool(row.get("extended_metrics_computed")):
            issues.append(_issue(run_id, "ERROR", "REPORT_CREATED_EXTENDED_METRICS_COMPUTED_FALSE", "extended_metrics_computed must be true for report-created status.", artifact_path))
        if not _to_bool(row.get("extended_metric_result_rows_created")):
            issues.append(_issue(run_id, "ERROR", "REPORT_CREATED_RESULT_ROWS_FLAG_FALSE", "extended_metric_result_rows_created must be true for report-created status.", artifact_path))
        if not _to_bool(row.get("extended_metric_summary_created")):
            issues.append(_issue(run_id, "ERROR", "REPORT_CREATED_SUMMARY_FLAG_FALSE", "extended_metric_summary_created must be true for report-created status.", artifact_path))

    allowed_set = {item.strip() for item in _text(row.get("allowed_extension_metric_set")).split(",") if item.strip()}
    if not allowed_set or allowed_set - set(ALLOWED_EXTENSION_METRIC_SET):
        issues.append(_issue(run_id, "ERROR", "ALLOWED_EXTENSION_METRIC_SET_UNSUPPORTED", "Allowed extension metric set contains unsupported metrics.", artifact_path))

    issues.extend(_result_row_issues(run_id, result_rows_path, result_rows))
    issues.extend(_report_wording_issues(run_id, Path(_text(row.get("report_path")))))
    for field in FORBIDDEN_FALSE_FIELDS:
        if _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", f"{field.upper()}_UNEXPECTED", f"Unsafe false-expected field is true: {field}", artifact_path))
    for field in ["report_only", "diagnostic_only"]:
        if not _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", "REPORT_ONLY_FLAGS_MISSING", f"Missing or false flag: {field}", artifact_path))
    return issues


def _result_row_issues(run_id: str, result_rows_path: Path, rows: pd.DataFrame) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if rows.empty:
        return issues
    columns = {column.lower() for column in rows.columns}
    forbidden = sorted(columns & FORBIDDEN_RESULT_ROW_COLUMNS)
    if forbidden:
        issues.append(_issue(run_id, "ERROR", "RESULT_ROW_FORBIDDEN_COLUMNS", f"Forbidden result-row columns: {','.join(forbidden)}", result_rows_path))
    if "metric_name" not in rows.columns:
        issues.append(_issue(run_id, "ERROR", "RESULT_ROW_METRIC_NAME_MISSING", "Result rows require metric_name.", result_rows_path))
        return issues
    metric_names = set(rows["metric_name"].dropna().astype(str))
    allowed = set(ALLOWED_EXTENSION_METRIC_SET)
    unsupported = sorted(metric_names - allowed - PATH_METRIC_NAMES - ANALYTIC_METRIC_NAMES - COST_TRADING_METRIC_NAMES)
    if unsupported:
        issues.append(_issue(run_id, "ERROR", "RESULT_ROW_UNSUPPORTED_METRIC_NAMES", f"Unsupported metric names: {','.join(unsupported)}", result_rows_path))
    path_metrics = sorted(metric_names & PATH_METRIC_NAMES)
    if path_metrics:
        issues.append(_issue(run_id, "ERROR", "RESULT_ROW_PATH_METRIC_NAMES", f"Path metric names are not allowed: {','.join(path_metrics)}", result_rows_path))
    analytic_metrics = sorted(metric_names & ANALYTIC_METRIC_NAMES)
    if analytic_metrics:
        issues.append(_issue(run_id, "ERROR", "RESULT_ROW_ANALYTIC_METRIC_NAMES", f"Analytic/IC/Sharpe/confidence/OOS/regime metrics are not allowed: {','.join(analytic_metrics)}", result_rows_path))
    cost_metrics = sorted(metric_names & COST_TRADING_METRIC_NAMES)
    if cost_metrics:
        issues.append(_issue(run_id, "ERROR", "RESULT_ROW_COST_TRADING_METRIC_NAMES", f"Cost/turnover/slippage metrics are not allowed: {','.join(cost_metrics)}", result_rows_path))
    for column in [
        "source_metric_computation_run_id",
        "source_metric_evaluation_planning_run_id",
        "source_training_evaluation_run_id",
        "source_forward_return_label_run_id",
        "source_replay_decision_freeze_run_id",
    ]:
        if column not in rows.columns or rows[column].fillna("").astype(str).str.strip().eq("").any():
            issues.append(_issue(run_id, "ERROR", "RESULT_ROW_LINEAGE_MISSING", f"Missing lineage column/value: {column}", result_rows_path))
    if _comparator_missing(rows, "benchmark_relative_return", "benchmark_id") or _comparator_missing(rows, "industry_relative_return", "industry_id"):
        issues.append(_issue(run_id, "ERROR", "RESULT_ROW_BENCHMARK_INDUSTRY_ID_MISSING", "Missing benchmark_id or industry_id for the matching relative-return metric.", result_rows_path))
    for column in ["metric_value", "numerator_count", "denominator_count"]:
        if column not in rows.columns or pd.to_numeric(rows[column], errors="coerce").isna().any():
            issues.append(_issue(run_id, "ERROR", "RESULT_ROW_NUMERATOR_DENOMINATOR_MISSING", f"Missing numeric field: {column}", result_rows_path))
    for column in ["report_only", "diagnostic_only"]:
        if column not in rows.columns or not rows[column].map(_to_bool).all():
            issues.append(_issue(run_id, "ERROR", "RESULT_ROW_REPORT_FLAGS_MISSING", f"Missing or false result-row flag: {column}", result_rows_path))
    return issues


def _comparator_missing(rows: pd.DataFrame, metric_name: str, column: str) -> bool:
    if column not in rows.columns:
        return True
    subset = rows[rows["metric_name"].astype(str) == metric_name]
    if subset.empty:
        return False
    return subset[column].fillna("").astype(str).str.strip().eq("").any()


def _report_wording_issues(run_id: str, report_path: Path) -> list[dict[str, Any]]:
    if not report_path.exists():
        return []
    text = report_path.read_text(encoding="utf-8").lower()
    for phrase in POSITIVE_OVERCLAIM_PHRASES:
        if phrase in text:
            return [_issue(run_id, "ERROR", "REPORT_OVERCLAIM_WORDING", f"Report contains overclaim phrase: {phrase}", report_path)]
    return []


def _ensure_manual_diagnostics_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    parts = {part.lower() for part in artifact_path.parts}
    if "outputs" not in parts or "reports" not in parts or "manual_diagnostics" not in parts:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "ARTIFACT_PATH_OUTSIDE_MANUAL_DIAGNOSTICS",
                "Metric extension artifacts must remain under outputs/reports/manual_diagnostics.",
                artifact_path,
            )
        )


def _write(result: MetricExtensionHealthResult) -> None:
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
                "# Metric Extension Health",
                "",
                "Report-only health for metric extension phase 1 artifacts. It fails if benchmark/industry relative rows become advanced/path/cost metrics, training_result, weights, model_version, thresholds, predictions, calibrated probabilities, feature importance, stock_profile, buy-review, paper approval, performance validation, broker/order/message/API/cache/data side effects, snapshots, current-candidates, signal semantics mutation, or trading.",
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
        "metric_extension_run_id": run_id,
        "severity": severity,
        "issue_code": issue_code,
        "message": message,
        "artifact_path": str(artifact_path),
    }


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]
