"""Status summary for report-only metric computation phase 1 artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.metric_computation import METRIC_COMPUTATION_REPORT_CREATED
from quant_replay_system.metric_computation_health import check_metric_computation_health
from quant_replay_system.metric_computation_index import DEFAULT_ROOT, build_metric_computation_index
from quant_replay_system.metric_computation_index import _text, _to_bool, _to_int


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"
NO_METRIC_COMPUTATION_ARTIFACT_FOUND = "NO_METRIC_COMPUTATION_ARTIFACT_FOUND"
METRIC_COMPUTATION_HEALTH_FAILED = "METRIC_COMPUTATION_HEALTH_FAILED"

SUMMARY_COLUMNS = [
    "latest_metric_computation_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "ready_for_metric_computation",
    "metric_computation_executed",
    "metric_computation_report_created",
    "metric_result_rows_created",
    "metric_summary_created",
    "metrics_computed",
    "allowed_metric_set",
    "requested_metric_set",
    "unsupported_metrics_requested",
    "sample_row_count",
    "eligible_sample_count",
    "quarantined_sample_count",
    "label_coverage_numerator",
    "label_coverage_denominator",
    "metric_names_present",
    "result_row_count",
    "summary_row_count",
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
    "blocker_count",
    "warning_count",
    "report_path",
    "safety_statement",
    "next_action",
]


@dataclass(frozen=True)
class MetricComputationStatusResult:
    latest_metric_computation_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    ready_for_metric_computation: bool
    metric_computation_executed: bool
    metric_computation_report_created: bool
    metric_result_rows_created: bool
    metric_summary_created: bool
    metrics_computed: bool
    allowed_metric_set: str
    requested_metric_set: str
    unsupported_metrics_requested: bool
    sample_row_count: int
    eligible_sample_count: int
    quarantined_sample_count: int
    label_coverage_numerator: int
    label_coverage_denominator: int
    metric_names_present: str
    result_row_count: int
    summary_row_count: int
    training_allowed: bool
    weights_trained: bool
    training_result_created: bool
    model_version_created: bool
    thresholds_optimized: bool
    predictions_created: bool
    calibrated_probabilities_created: bool
    feature_importance_created: bool
    stock_profile_allowed: bool
    active_stock_profile_exists: bool
    stock_profile_created: bool
    buy_review_allowed: bool
    real_buy_review_eligible: bool
    approved_for_paper: bool
    strategy_performance_validated: bool
    trading_allowed: bool
    blocker_count: int
    warning_count: int
    report_path: str
    safety_statement: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_metric_computation_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> MetricComputationStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_metric_computation_index(root=root, output_dir=sibling_root / "index")
    health = check_metric_computation_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        frame = index.index_frame.copy()
        frame["_status_priority"] = frame["status"].map(_status_priority)
        latest = frame.sort_values(["created_at", "_status_priority", "metric_computation_run_id"]).iloc[-1].to_dict()
        result = _result_from_latest(latest, health.status, health.error_count, health.warning_count, output_dir, root)
    _write(result)
    return result


def _result_from_latest(
    latest: dict[str, Any],
    health_status: str,
    error_count: int,
    warning_count: int,
    output_dir: str | Path,
    root: str | Path,
) -> MetricComputationStatusResult:
    status = _text(latest.get("status"))
    stage = METRIC_COMPUTATION_HEALTH_FAILED if health_status == "FAIL" else _text(latest.get("workflow_stage")) or status
    summary = {
        "latest_metric_computation_run_id": _text(latest.get("metric_computation_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "ready_for_metric_computation": _to_bool(latest.get("ready_for_metric_computation")),
        "metric_computation_executed": _to_bool(latest.get("metric_computation_executed")),
        "metric_computation_report_created": _to_bool(latest.get("metric_computation_report_created")),
        "metric_result_rows_created": _to_bool(latest.get("metric_result_rows_created")),
        "metric_summary_created": _to_bool(latest.get("metric_summary_created")),
        "metrics_computed": _to_bool(latest.get("metrics_computed")),
        "allowed_metric_set": _text(latest.get("allowed_metric_set")),
        "requested_metric_set": _text(latest.get("requested_metric_set")),
        "unsupported_metrics_requested": _to_bool(latest.get("unsupported_metrics_requested")),
        "sample_row_count": _to_int(latest.get("sample_row_count")),
        "eligible_sample_count": _to_int(latest.get("eligible_sample_count")),
        "quarantined_sample_count": _to_int(latest.get("quarantined_sample_count")),
        "label_coverage_numerator": _to_int(latest.get("label_coverage_numerator")),
        "label_coverage_denominator": _to_int(latest.get("label_coverage_denominator")),
        "metric_names_present": _text(latest.get("metric_names_present")),
        "result_row_count": _to_int(latest.get("result_row_count")),
        "summary_row_count": _to_int(latest.get("summary_row_count")),
        "training_allowed": _to_bool(latest.get("training_allowed")),
        "weights_trained": _to_bool(latest.get("weights_trained")),
        "training_result_created": _to_bool(latest.get("training_result_created")),
        "model_version_created": _to_bool(latest.get("model_version_created")),
        "thresholds_optimized": _to_bool(latest.get("thresholds_optimized")),
        "predictions_created": _to_bool(latest.get("predictions_created")),
        "calibrated_probabilities_created": _to_bool(latest.get("calibrated_probabilities_created")),
        "feature_importance_created": _to_bool(latest.get("feature_importance_created")),
        "stock_profile_allowed": _to_bool(latest.get("stock_profile_allowed")),
        "active_stock_profile_exists": _to_bool(latest.get("active_stock_profile_exists")),
        "stock_profile_created": _to_bool(latest.get("stock_profile_created")),
        "buy_review_allowed": _to_bool(latest.get("buy_review_allowed")),
        "real_buy_review_eligible": _to_bool(latest.get("real_buy_review_eligible")),
        "approved_for_paper": _to_bool(latest.get("approved_for_paper")),
        "strategy_performance_validated": _to_bool(latest.get("strategy_performance_validated")),
        "trading_allowed": _to_bool(latest.get("trading_allowed")),
        "blocker_count": max(_to_int(latest.get("blocker_count")), error_count),
        "warning_count": max(_to_int(latest.get("warning_count")), warning_count),
        "report_path": _text(latest.get("report_path")),
        "safety_statement": _safety_statement(),
        "next_action": _next_action(stage, status),
    }
    return _result(summary, output_dir, root, [])


def _no_artifact_result(
    output_dir: str | Path,
    root: str | Path,
    health_status: str,
    error_count: int,
    warning_count: int,
) -> MetricComputationStatusResult:
    summary = {
        "latest_metric_computation_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_METRIC_COMPUTATION_ARTIFACT_FOUND,
        "ready_for_metric_computation": False,
        "metric_computation_executed": False,
        "metric_computation_report_created": False,
        "metric_result_rows_created": False,
        "metric_summary_created": False,
        "metrics_computed": False,
        "allowed_metric_set": "",
        "requested_metric_set": "",
        "unsupported_metrics_requested": False,
        "sample_row_count": 0,
        "eligible_sample_count": 0,
        "quarantined_sample_count": 0,
        "label_coverage_numerator": 0,
        "label_coverage_denominator": 0,
        "metric_names_present": "",
        "result_row_count": 0,
        "summary_row_count": 0,
        "training_allowed": False,
        "weights_trained": False,
        "training_result_created": False,
        "model_version_created": False,
        "thresholds_optimized": False,
        "predictions_created": False,
        "calibrated_probabilities_created": False,
        "feature_importance_created": False,
        "stock_profile_allowed": False,
        "active_stock_profile_exists": False,
        "stock_profile_created": False,
        "buy_review_allowed": False,
        "real_buy_review_eligible": False,
        "approved_for_paper": False,
        "strategy_performance_validated": False,
        "trading_allowed": False,
        "blocker_count": max(error_count, 1),
        "warning_count": warning_count,
        "report_path": "",
        "safety_statement": _safety_statement(),
        "next_action": "Create or provide report-only metric computation artifacts before checking status.",
    }
    return _result(summary, output_dir, root, [])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> MetricComputationStatusResult:
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "metric_computation_status.csv",
        "status_report": Path(output_dir) / "metric_computation_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    return MetricComputationStatusResult(
        summary_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata={"root": str(root), "report_only": True, "diagnostic_only": True},
        **summary,
    )


def _write(result: MetricComputationStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "latest_metric_computation_run_id": result.latest_metric_computation_run_id,
                "status": result.status,
                "health_status": result.health_status,
                "workflow_stage": result.workflow_stage,
                "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
                **result.audit_metadata,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Metric Computation Status",
                "",
                result.safety_statement,
                "",
                f"- latest_metric_computation_run_id: {result.latest_metric_computation_run_id}",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- metrics_computed: {result.metrics_computed}",
                f"- metric_names_present: {result.metric_names_present}",
                f"- next_action: {result.next_action}",
                "",
                result.summary_frame.to_markdown(index=False),
            ]
        ),
        encoding="utf-8",
    )


def _safety_statement() -> str:
    return (
        "Metric computation phase 1 is report-only historical metric computation only. "
        "METRIC_COMPUTATION_REPORT_CREATED means report-only historical metrics for a bounded sample; "
        "not strategy validation, not training_result, not weights, not model_version, not thresholds, "
        "not predictions/probabilities/feature importance, not stock_profile, not buy-review eligibility, "
        "not paper approval, not performance validation, and not trading."
    )


def _next_action(stage: str, status: str) -> str:
    if stage == METRIC_COMPUTATION_HEALTH_FAILED:
        return "Resolve metric computation health errors before trusting artifact views."
    if status == METRIC_COMPUTATION_REPORT_CREATED:
        return "Review report-only historical metrics; do not treat them as strategy validation."
    return "Review metric computation gates and artifacts before any next workflow."


def _status_priority(status: Any) -> int:
    text = _text(status)
    if text == METRIC_COMPUTATION_REPORT_CREATED:
        return 3
    if text == "READY_FOR_METRIC_COMPUTATION":
        return 2
    if text == "NO_METRIC_COMPUTATION_INPUT":
        return 1
    return 0
