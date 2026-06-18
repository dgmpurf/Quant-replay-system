"""Status summary for report-only metric extension phase 1 artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.metric_extension import FORBIDDEN_FALSE_FIELDS, METRIC_EXTENSION_REPORT_CREATED
from quant_replay_system.metric_extension_health import check_metric_extension_health
from quant_replay_system.metric_extension_index import DEFAULT_ROOT, build_metric_extension_index
from quant_replay_system.metric_extension_index import _text, _to_bool, _to_int


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"
NO_METRIC_EXTENSION_ARTIFACT_FOUND = "NO_METRIC_EXTENSION_ARTIFACT_FOUND"
METRIC_EXTENSION_HEALTH_FAILED = "METRIC_EXTENSION_HEALTH_FAILED"

SUMMARY_COLUMNS = [
    "latest_metric_extension_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "ready_for_metric_extension",
    "metric_extension_executed",
    "metric_extension_report_created",
    "extended_metric_result_rows_created",
    "extended_metric_summary_created",
    "extended_metrics_computed",
    "allowed_extension_metric_set",
    "requested_extension_metric_set",
    "unsupported_metrics_requested",
    "sample_row_count",
    "eligible_sample_count",
    "quarantined_sample_count",
    "benchmark_mapping_row_count",
    "industry_mapping_row_count",
    "benchmark_denominator_count",
    "industry_denominator_count",
    "benchmark_relative_return_created",
    "industry_relative_return_created",
    "metric_names_present",
    "result_row_count",
    "summary_row_count",
    *FORBIDDEN_FALSE_FIELDS,
    "blocker_count",
    "warning_count",
    "report_path",
    "safety_statement",
    "next_action",
]


@dataclass(frozen=True)
class MetricExtensionStatusResult:
    latest_metric_extension_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    ready_for_metric_extension: bool
    metric_extension_executed: bool
    metric_extension_report_created: bool
    extended_metric_result_rows_created: bool
    extended_metric_summary_created: bool
    extended_metrics_computed: bool
    allowed_extension_metric_set: str
    requested_extension_metric_set: str
    unsupported_metrics_requested: bool
    sample_row_count: int
    eligible_sample_count: int
    quarantined_sample_count: int
    benchmark_mapping_row_count: int
    industry_mapping_row_count: int
    benchmark_denominator_count: int
    industry_denominator_count: int
    benchmark_relative_return_created: bool
    industry_relative_return_created: bool
    metric_names_present: str
    result_row_count: int
    summary_row_count: int
    evaluation_execution_completed: bool
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
    order_placed: bool
    broker_api_called: bool
    message_sent: bool
    llm_api_called: bool
    external_api_called: bool
    cache_mutated: bool
    data_raw_written: bool
    data_processed_written: bool
    data_cache_written: bool
    current_candidates_run: bool
    snapshot_built: bool
    signal_semantics_changed: bool
    blocker_count: int
    warning_count: int
    report_path: str
    safety_statement: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_metric_extension_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> MetricExtensionStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_metric_extension_index(root=root, output_dir=sibling_root / "index")
    health = check_metric_extension_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        frame = index.index_frame.copy()
        frame["_status_priority"] = frame["status"].map(_status_priority)
        latest = frame.sort_values(["created_at", "_status_priority", "metric_extension_run_id"]).iloc[-1].to_dict()
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
) -> MetricExtensionStatusResult:
    status = _text(latest.get("status"))
    stage = METRIC_EXTENSION_HEALTH_FAILED if health_status == "FAIL" else _text(latest.get("workflow_stage")) or status
    summary = {
        "latest_metric_extension_run_id": _text(latest.get("metric_extension_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "ready_for_metric_extension": _to_bool(latest.get("ready_for_metric_extension")),
        "metric_extension_executed": _to_bool(latest.get("metric_extension_executed")),
        "metric_extension_report_created": _to_bool(latest.get("metric_extension_report_created")),
        "extended_metric_result_rows_created": _to_bool(latest.get("extended_metric_result_rows_created")),
        "extended_metric_summary_created": _to_bool(latest.get("extended_metric_summary_created")),
        "extended_metrics_computed": _to_bool(latest.get("extended_metrics_computed")),
        "allowed_extension_metric_set": _text(latest.get("allowed_extension_metric_set")),
        "requested_extension_metric_set": _text(latest.get("requested_extension_metric_set")),
        "unsupported_metrics_requested": _to_bool(latest.get("unsupported_metrics_requested")),
        "sample_row_count": _to_int(latest.get("sample_row_count")),
        "eligible_sample_count": _to_int(latest.get("eligible_sample_count")),
        "quarantined_sample_count": _to_int(latest.get("quarantined_sample_count")),
        "benchmark_mapping_row_count": _to_int(latest.get("benchmark_mapping_row_count")),
        "industry_mapping_row_count": _to_int(latest.get("industry_mapping_row_count")),
        "benchmark_denominator_count": _to_int(latest.get("benchmark_denominator_count")),
        "industry_denominator_count": _to_int(latest.get("industry_denominator_count")),
        "benchmark_relative_return_created": _to_bool(latest.get("benchmark_relative_return_created")),
        "industry_relative_return_created": _to_bool(latest.get("industry_relative_return_created")),
        "metric_names_present": _text(latest.get("metric_names_present")),
        "result_row_count": _to_int(latest.get("result_row_count")),
        "summary_row_count": _to_int(latest.get("summary_row_count")),
        **{field: _to_bool(latest.get(field)) for field in FORBIDDEN_FALSE_FIELDS},
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
) -> MetricExtensionStatusResult:
    summary = {
        "latest_metric_extension_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_METRIC_EXTENSION_ARTIFACT_FOUND,
        "ready_for_metric_extension": False,
        "metric_extension_executed": False,
        "metric_extension_report_created": False,
        "extended_metric_result_rows_created": False,
        "extended_metric_summary_created": False,
        "extended_metrics_computed": False,
        "allowed_extension_metric_set": "",
        "requested_extension_metric_set": "",
        "unsupported_metrics_requested": False,
        "sample_row_count": 0,
        "eligible_sample_count": 0,
        "quarantined_sample_count": 0,
        "benchmark_mapping_row_count": 0,
        "industry_mapping_row_count": 0,
        "benchmark_denominator_count": 0,
        "industry_denominator_count": 0,
        "benchmark_relative_return_created": False,
        "industry_relative_return_created": False,
        "metric_names_present": "",
        "result_row_count": 0,
        "summary_row_count": 0,
        **{field: False for field in FORBIDDEN_FALSE_FIELDS},
        "blocker_count": max(error_count, 1),
        "warning_count": warning_count,
        "report_path": "",
        "safety_statement": _safety_statement(),
        "next_action": "Create or provide report-only metric extension artifacts before checking status.",
    }
    return _result(summary, output_dir, root, [])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> MetricExtensionStatusResult:
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "metric_extension_status.csv",
        "status_report": Path(output_dir) / "metric_extension_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    return MetricExtensionStatusResult(
        summary_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata={"root": str(root), "report_only": True, "diagnostic_only": True},
        **summary,
    )


def _write(result: MetricExtensionStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "latest_metric_extension_run_id": result.latest_metric_extension_run_id,
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
                "# Metric Extension Status",
                "",
                result.safety_statement,
                "",
                f"- latest_metric_extension_run_id: {result.latest_metric_extension_run_id}",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- extended_metrics_computed: {result.extended_metrics_computed}",
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
        "Metric extension phase 1 is report-only benchmark/industry relative metric computation only. "
        "METRIC_EXTENSION_REPORT_CREATED means report-only benchmark/industry relative metrics for a bounded sample; "
        "not strategy validation, not training_result, not weights, not model_version, not thresholds, "
        "not predictions/probabilities/feature importance, not stock_profile, not buy-review eligibility, "
        "not paper approval, not performance validation, and not trading."
    )


def _next_action(stage: str, status: str) -> str:
    if stage == METRIC_EXTENSION_HEALTH_FAILED:
        return "Resolve metric extension health errors before trusting artifact views."
    if status == METRIC_EXTENSION_REPORT_CREATED:
        return "Review report-only benchmark/industry relative metrics; do not treat them as strategy validation."
    return "Review metric extension gates and artifacts before any next workflow."


def _status_priority(status: Any) -> int:
    text = _text(status)
    if text == METRIC_EXTENSION_REPORT_CREATED:
        return 3
    if text == "READY_FOR_METRIC_EXTENSION":
        return 2
    if text == "NO_METRIC_EXTENSION_INPUT":
        return 1
    return 0
