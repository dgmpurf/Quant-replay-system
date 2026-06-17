"""Status summary for report-only metric/evaluation phase 1 structural planning artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.metric_evaluation import (
    METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED,
    NO_METRIC_EVALUATION_INPUT,
    READY_FOR_METRIC_EVALUATION_PLANNING_ARTIFACTS,
)
from quant_replay_system.metric_evaluation_health import check_metric_evaluation_health
from quant_replay_system.metric_evaluation_index import DEFAULT_ROOT, build_metric_evaluation_index


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"

NO_METRIC_EVALUATION_ARTIFACT_FOUND = "NO_METRIC_EVALUATION_ARTIFACT_FOUND"
METRIC_EVALUATION_HEALTH_FAILED = "METRIC_EVALUATION_HEALTH_FAILED"

SUMMARY_COLUMNS = [
    "latest_metric_evaluation_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "source_training_evaluation_run_id",
    "source_training_evaluation_status",
    "source_training_evaluation_health_status",
    "source_forward_return_label_run_id",
    "source_replay_decision_freeze_run_id",
    "training_evaluation_dataset_artifacts_created",
    "training_evaluation_sample_row_count",
    "training_evaluation_label_row_count",
    "symbol_count",
    "label_name_set",
    "ready_for_metric_evaluation_planning_artifacts",
    "metric_evaluation_executed",
    "metric_evaluation_planning_artifacts_created",
    "metric_evaluation_input_index_created",
    "metric_definitions_created",
    "sample_scope_created",
    "denominator_rules_created",
    "health_status_plan_created",
    "research_status_plan_created",
    "metric_definition_count",
    "sample_scope_row_count",
    "denominator_rule_count",
    "metrics_computed",
    "metric_result_rows_created",
    "metric_evaluation_results_created",
    "evaluation_execution_completed",
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
class MetricEvaluationStatusResult:
    latest_metric_evaluation_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    source_training_evaluation_run_id: str
    source_training_evaluation_status: str
    source_training_evaluation_health_status: str
    source_forward_return_label_run_id: str
    source_replay_decision_freeze_run_id: str
    training_evaluation_dataset_artifacts_created: bool
    training_evaluation_sample_row_count: int
    training_evaluation_label_row_count: int
    symbol_count: int
    label_name_set: str
    ready_for_metric_evaluation_planning_artifacts: bool
    metric_evaluation_executed: bool
    metric_evaluation_planning_artifacts_created: bool
    metric_evaluation_input_index_created: bool
    metric_definitions_created: bool
    sample_scope_created: bool
    denominator_rules_created: bool
    health_status_plan_created: bool
    research_status_plan_created: bool
    metric_definition_count: int
    sample_scope_row_count: int
    denominator_rule_count: int
    metrics_computed: bool
    metric_result_rows_created: bool
    metric_evaluation_results_created: bool
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
    blocker_count: int
    warning_count: int
    report_path: str
    safety_statement: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_metric_evaluation_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> MetricEvaluationStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_metric_evaluation_index(root=root, output_dir=sibling_root / "index")
    health = check_metric_evaluation_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        latest = index.index_frame.sort_values(["generated_at", "metric_evaluation_run_id"]).iloc[-1].to_dict()
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
) -> MetricEvaluationStatusResult:
    status = _text(latest.get("status"))
    stage = _stage_for_latest(status, _text(latest.get("workflow_stage")), health_status)
    summary = {
        "latest_metric_evaluation_run_id": _text(latest.get("metric_evaluation_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "source_training_evaluation_run_id": _text(latest.get("source_training_evaluation_run_id")),
        "source_training_evaluation_status": _text(latest.get("source_training_evaluation_status")),
        "source_training_evaluation_health_status": _text(latest.get("source_training_evaluation_health_status")),
        "source_forward_return_label_run_id": _text(latest.get("source_forward_return_label_run_id")),
        "source_replay_decision_freeze_run_id": _text(latest.get("source_replay_decision_freeze_run_id")),
        "training_evaluation_dataset_artifacts_created": _to_bool(latest.get("training_evaluation_dataset_artifacts_created")),
        "training_evaluation_sample_row_count": _to_int(latest.get("training_evaluation_sample_row_count")),
        "training_evaluation_label_row_count": _to_int(latest.get("training_evaluation_label_row_count")),
        "symbol_count": _to_int(latest.get("symbol_count")),
        "label_name_set": _text(latest.get("label_name_set")),
        "ready_for_metric_evaluation_planning_artifacts": _to_bool(latest.get("ready_for_metric_evaluation_planning_artifacts")),
        "metric_evaluation_executed": _to_bool(latest.get("metric_evaluation_executed")),
        "metric_evaluation_planning_artifacts_created": _to_bool(latest.get("metric_evaluation_planning_artifacts_created")),
        "metric_evaluation_input_index_created": _to_bool(latest.get("metric_evaluation_input_index_created")),
        "metric_definitions_created": _to_bool(latest.get("metric_definitions_created")),
        "sample_scope_created": _to_bool(latest.get("sample_scope_created")),
        "denominator_rules_created": _to_bool(latest.get("denominator_rules_created")),
        "health_status_plan_created": _to_bool(latest.get("health_status_plan_created")),
        "research_status_plan_created": _to_bool(latest.get("research_status_plan_created")),
        "metric_definition_count": _to_int(latest.get("metric_definition_count")),
        "sample_scope_row_count": _to_int(latest.get("sample_scope_row_count")),
        "denominator_rule_count": _to_int(latest.get("denominator_rule_count")),
        "metrics_computed": _to_bool(latest.get("metrics_computed")),
        "metric_result_rows_created": _to_bool(latest.get("metric_result_rows_created")),
        "metric_evaluation_results_created": _to_bool(latest.get("metric_evaluation_results_created")),
        "evaluation_execution_completed": _to_bool(latest.get("evaluation_execution_completed")),
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
        "next_action": _next_action(stage),
    }
    return _result(summary, output_dir, root, [])


def _no_artifact_result(
    output_dir: str | Path,
    root: str | Path,
    health_status: str,
    error_count: int,
    warning_count: int,
) -> MetricEvaluationStatusResult:
    summary = {
        "latest_metric_evaluation_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_METRIC_EVALUATION_ARTIFACT_FOUND,
        "source_training_evaluation_run_id": "",
        "source_training_evaluation_status": "",
        "source_training_evaluation_health_status": "",
        "source_forward_return_label_run_id": "",
        "source_replay_decision_freeze_run_id": "",
        "training_evaluation_dataset_artifacts_created": False,
        "training_evaluation_sample_row_count": 0,
        "training_evaluation_label_row_count": 0,
        "symbol_count": 0,
        "label_name_set": "",
        "ready_for_metric_evaluation_planning_artifacts": False,
        "metric_evaluation_executed": False,
        "metric_evaluation_planning_artifacts_created": False,
        "metric_evaluation_input_index_created": False,
        "metric_definitions_created": False,
        "sample_scope_created": False,
        "denominator_rules_created": False,
        "health_status_plan_created": False,
        "research_status_plan_created": False,
        "metric_definition_count": 0,
        "sample_scope_row_count": 0,
        "denominator_rule_count": 0,
        "metrics_computed": False,
        "metric_result_rows_created": False,
        "metric_evaluation_results_created": False,
        "evaluation_execution_completed": False,
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
        "blocker_count": error_count,
        "warning_count": warning_count,
        "report_path": "",
        "safety_statement": _safety_statement(),
        "next_action": "Run metric-evaluation only after report-only phase 1 inputs are ready; do not compute metrics, create result rows, train, create model_version, stock_profile, paper approval, or trading outputs.",
    }
    return _result(summary, output_dir, root, [f"No metric/evaluation artifacts found under {root}"])


def _result(summary: dict[str, Any], output_dir: str | Path, root: str | Path, warnings: list[str]) -> MetricEvaluationStatusResult:
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "metric_evaluation_status.csv",
        "status_report": Path(output_dir) / "metric_evaluation_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return MetricEvaluationStatusResult(
        latest_metric_evaluation_run_id=str(summary["latest_metric_evaluation_run_id"]),
        status=str(summary["status"]),
        health_status=str(summary["health_status"]),
        workflow_stage=str(summary["workflow_stage"]),
        source_training_evaluation_run_id=str(summary["source_training_evaluation_run_id"]),
        source_training_evaluation_status=str(summary["source_training_evaluation_status"]),
        source_training_evaluation_health_status=str(summary["source_training_evaluation_health_status"]),
        source_forward_return_label_run_id=str(summary["source_forward_return_label_run_id"]),
        source_replay_decision_freeze_run_id=str(summary["source_replay_decision_freeze_run_id"]),
        training_evaluation_dataset_artifacts_created=bool(summary["training_evaluation_dataset_artifacts_created"]),
        training_evaluation_sample_row_count=int(summary["training_evaluation_sample_row_count"]),
        training_evaluation_label_row_count=int(summary["training_evaluation_label_row_count"]),
        symbol_count=int(summary["symbol_count"]),
        label_name_set=str(summary["label_name_set"]),
        ready_for_metric_evaluation_planning_artifacts=bool(summary["ready_for_metric_evaluation_planning_artifacts"]),
        metric_evaluation_executed=bool(summary["metric_evaluation_executed"]),
        metric_evaluation_planning_artifacts_created=bool(summary["metric_evaluation_planning_artifacts_created"]),
        metric_evaluation_input_index_created=bool(summary["metric_evaluation_input_index_created"]),
        metric_definitions_created=bool(summary["metric_definitions_created"]),
        sample_scope_created=bool(summary["sample_scope_created"]),
        denominator_rules_created=bool(summary["denominator_rules_created"]),
        health_status_plan_created=bool(summary["health_status_plan_created"]),
        research_status_plan_created=bool(summary["research_status_plan_created"]),
        metric_definition_count=int(summary["metric_definition_count"]),
        sample_scope_row_count=int(summary["sample_scope_row_count"]),
        denominator_rule_count=int(summary["denominator_rule_count"]),
        metrics_computed=bool(summary["metrics_computed"]),
        metric_result_rows_created=bool(summary["metric_result_rows_created"]),
        metric_evaluation_results_created=bool(summary["metric_evaluation_results_created"]),
        evaluation_execution_completed=bool(summary["evaluation_execution_completed"]),
        training_allowed=bool(summary["training_allowed"]),
        weights_trained=bool(summary["weights_trained"]),
        training_result_created=bool(summary["training_result_created"]),
        model_version_created=bool(summary["model_version_created"]),
        thresholds_optimized=bool(summary["thresholds_optimized"]),
        predictions_created=bool(summary["predictions_created"]),
        calibrated_probabilities_created=bool(summary["calibrated_probabilities_created"]),
        feature_importance_created=bool(summary["feature_importance_created"]),
        stock_profile_allowed=bool(summary["stock_profile_allowed"]),
        active_stock_profile_exists=bool(summary["active_stock_profile_exists"]),
        stock_profile_created=bool(summary["stock_profile_created"]),
        buy_review_allowed=bool(summary["buy_review_allowed"]),
        real_buy_review_eligible=bool(summary["real_buy_review_eligible"]),
        approved_for_paper=bool(summary["approved_for_paper"]),
        strategy_performance_validated=bool(summary["strategy_performance_validated"]),
        trading_allowed=bool(summary["trading_allowed"]),
        blocker_count=int(summary["blocker_count"]),
        warning_count=int(summary["warning_count"]),
        report_path=str(summary["report_path"]),
        safety_statement=str(summary["safety_statement"]),
        next_action=str(summary["next_action"]),
        summary_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata={"root": str(root), "report_only": True, "diagnostic_only": True},
    )


def _stage_for_latest(status: str, workflow_stage: str, health_status: str) -> str:
    if health_status == "FAIL":
        return METRIC_EVALUATION_HEALTH_FAILED
    if workflow_stage:
        return workflow_stage
    if status == NO_METRIC_EVALUATION_INPUT:
        return "METRIC_EVALUATION_NO_INPUT"
    if status in {READY_FOR_METRIC_EVALUATION_PLANNING_ARTIFACTS, METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED}:
        return status
    return status or NO_METRIC_EVALUATION_ARTIFACT_FOUND


def _next_action(stage: str) -> str:
    if stage == METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED:
        return "Review report-only metric/evaluation structural planning artifacts; computed metrics and result rows require a separate explicit task."
    if stage == READY_FOR_METRIC_EVALUATION_PLANNING_ARTIFACTS:
        return "Review gates and rerun core with explicit allow only if report-only metric/evaluation planning artifacts are intended."
    if stage == "METRIC_EVALUATION_NO_INPUT":
        return "Provide TRAINING_EVALUATION_DATASET_CREATED source artifacts, exact approval, metric definition, scope, leakage, side-effect, and overclaim inputs."
    if stage == METRIC_EVALUATION_HEALTH_FAILED:
        return "Fix health blockers before using metric/evaluation planning context."
    return "Resolve blocker gates; do not compute metrics, create result rows, train weights, create model_version, stock_profile, paper approval, performance validation, or trading outputs."


def _safety_statement() -> str:
    return (
        "metric/evaluation phase 1 is report-only structural planning only. "
        "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED means planning artifacts only; it is not metrics computed, "
        "not metric result rows, not training_result, not weights, not model_version, not thresholds, "
        "not predictions, not calibrated probabilities, not feature importance, not stock_profile, "
        "not buy-review eligibility, not paper approval, not strategy performance validation, and not trading."
    )


def _write(result: MetricEvaluationStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "status_id": f"{result.latest_metric_evaluation_run_id}:{result.workflow_stage}",
                "latest_metric_evaluation_run_id": result.latest_metric_evaluation_run_id,
                "status": result.status,
                "health_status": result.health_status,
                "workflow_stage": result.workflow_stage,
                "warnings": result.warnings,
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
                "# Metric / Evaluation Status",
                "",
                f"- latest_metric_evaluation_run_id: {result.latest_metric_evaluation_run_id}",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- metric_evaluation_planning_artifacts_created: {result.metric_evaluation_planning_artifacts_created}",
                f"- metric_definition_count: {result.metric_definition_count}",
                f"- sample_scope_row_count: {result.sample_scope_row_count}",
                "",
                result.safety_statement,
                "",
                f"Next action: {result.next_action}",
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


def _to_int(value: Any) -> int:
    try:
        if value is None or value == "" or pd.isna(value):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0
