"""Status summary for report-only training/evaluation phase 1 artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.training_evaluation import (
    NO_TRAINING_EVALUATION_INPUT,
    READY_FOR_TRAINING_EVALUATION_DATASET,
    TRAINING_EVALUATION_DATASET_CREATED,
)
from quant_replay_system.training_evaluation_health import check_training_evaluation_health
from quant_replay_system.training_evaluation_index import DEFAULT_ROOT, build_training_evaluation_index


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"

NO_TRAINING_EVALUATION_ARTIFACT_FOUND = "NO_TRAINING_EVALUATION_ARTIFACT_FOUND"
TRAINING_EVALUATION_HEALTH_FAILED = "TRAINING_EVALUATION_HEALTH_FAILED"

SUMMARY_COLUMNS = [
    "latest_training_evaluation_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "source_forward_return_label_run_id",
    "source_forward_return_label_status",
    "source_forward_return_label_health_status",
    "source_replay_decision_freeze_run_id",
    "ready_for_training_evaluation_dataset",
    "training_evaluation_executed",
    "training_evaluation_dataset_artifacts_created",
    "bounded_sample_rows_created",
    "label_coverage_report_created",
    "split_plan_created",
    "feature_plan_created",
    "label_plan_created",
    "dataset_sample_row_count",
    "label_row_count",
    "symbol_count",
    "label_name_set",
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
    "blocker_count",
    "warning_count",
    "report_path",
    "safety_statement",
    "next_action",
]


@dataclass(frozen=True)
class TrainingEvaluationStatusResult:
    latest_training_evaluation_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    ready_for_training_evaluation_dataset: bool
    training_evaluation_executed: bool
    training_evaluation_dataset_artifacts_created: bool
    bounded_sample_rows_created: bool
    label_coverage_report_created: bool
    split_plan_created: bool
    feature_plan_created: bool
    label_plan_created: bool
    dataset_sample_row_count: int
    label_row_count: int
    symbol_count: int
    label_name_set: str
    metrics_computed: bool
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


def run_training_evaluation_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> TrainingEvaluationStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_training_evaluation_index(root=root, output_dir=sibling_root / "index")
    health = check_training_evaluation_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        latest = index.index_frame.sort_values(["generated_at", "training_evaluation_run_id"]).iloc[-1].to_dict()
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
) -> TrainingEvaluationStatusResult:
    status = _text(latest.get("status"))
    stage = _stage_for_latest(status, _text(latest.get("workflow_stage")), health_status)
    summary = {
        "latest_training_evaluation_run_id": _text(latest.get("training_evaluation_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "source_forward_return_label_run_id": _text(latest.get("source_forward_return_label_run_id")),
        "source_forward_return_label_status": _text(latest.get("source_forward_return_label_status")),
        "source_forward_return_label_health_status": _text(
            latest.get("source_forward_return_label_health_status")
        ),
        "source_replay_decision_freeze_run_id": _text(latest.get("source_replay_decision_freeze_run_id")),
        "ready_for_training_evaluation_dataset": _to_bool(latest.get("ready_for_training_evaluation_dataset")),
        "training_evaluation_executed": _to_bool(latest.get("training_evaluation_executed")),
        "training_evaluation_dataset_artifacts_created": _to_bool(latest.get("training_evaluation_dataset_artifacts_created")),
        "bounded_sample_rows_created": _to_bool(latest.get("bounded_sample_rows_created")),
        "label_coverage_report_created": _to_bool(latest.get("label_coverage_report_created")),
        "split_plan_created": _to_bool(latest.get("split_plan_created")),
        "feature_plan_created": _to_bool(latest.get("feature_plan_created")),
        "label_plan_created": _to_bool(latest.get("label_plan_created")),
        "dataset_sample_row_count": _to_int(latest.get("dataset_sample_row_count")),
        "label_row_count": _to_int(latest.get("label_row_count")),
        "symbol_count": _to_int(latest.get("symbol_count")),
        "label_name_set": _text(latest.get("label_name_set")),
        "metrics_computed": _to_bool(latest.get("metrics_computed")),
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
) -> TrainingEvaluationStatusResult:
    summary = {
        "latest_training_evaluation_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_TRAINING_EVALUATION_ARTIFACT_FOUND,
        "source_forward_return_label_run_id": "",
        "source_forward_return_label_status": "",
        "source_forward_return_label_health_status": "",
        "source_replay_decision_freeze_run_id": "",
        "ready_for_training_evaluation_dataset": False,
        "training_evaluation_executed": False,
        "training_evaluation_dataset_artifacts_created": False,
        "bounded_sample_rows_created": False,
        "label_coverage_report_created": False,
        "split_plan_created": False,
        "feature_plan_created": False,
        "label_plan_created": False,
        "dataset_sample_row_count": 0,
        "label_row_count": 0,
        "symbol_count": 0,
        "label_name_set": "",
        "metrics_computed": False,
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
        "next_action": "Run training-evaluation only after report-only phase 1 inputs are ready; do not compute metrics, train, create model_version, stock_profile, buy-review, paper approval, or trading outputs.",
    }
    return _result(summary, output_dir, root, [f"No training/evaluation artifacts found under {root}"])


def _result(summary: dict[str, Any], output_dir: str | Path, root: str | Path, warnings: list[str]) -> TrainingEvaluationStatusResult:
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "training_evaluation_status.csv",
        "status_report": Path(output_dir) / "training_evaluation_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return TrainingEvaluationStatusResult(
        latest_training_evaluation_run_id=str(summary["latest_training_evaluation_run_id"]),
        status=str(summary["status"]),
        health_status=str(summary["health_status"]),
        workflow_stage=str(summary["workflow_stage"]),
        ready_for_training_evaluation_dataset=bool(summary["ready_for_training_evaluation_dataset"]),
        training_evaluation_executed=bool(summary["training_evaluation_executed"]),
        training_evaluation_dataset_artifacts_created=bool(summary["training_evaluation_dataset_artifacts_created"]),
        bounded_sample_rows_created=bool(summary["bounded_sample_rows_created"]),
        label_coverage_report_created=bool(summary["label_coverage_report_created"]),
        split_plan_created=bool(summary["split_plan_created"]),
        feature_plan_created=bool(summary["feature_plan_created"]),
        label_plan_created=bool(summary["label_plan_created"]),
        dataset_sample_row_count=int(summary["dataset_sample_row_count"]),
        label_row_count=int(summary["label_row_count"]),
        symbol_count=int(summary["symbol_count"]),
        label_name_set=str(summary["label_name_set"]),
        metrics_computed=bool(summary["metrics_computed"]),
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
        return TRAINING_EVALUATION_HEALTH_FAILED
    if workflow_stage:
        return workflow_stage
    if status == NO_TRAINING_EVALUATION_INPUT:
        return "TRAINING_EVALUATION_NO_INPUT"
    if status in {READY_FOR_TRAINING_EVALUATION_DATASET, TRAINING_EVALUATION_DATASET_CREATED}:
        return status
    return status or NO_TRAINING_EVALUATION_ARTIFACT_FOUND


def _next_action(stage: str) -> str:
    if stage == TRAINING_EVALUATION_DATASET_CREATED:
        return "Review report-only dataset/planning artifacts; metrics, training_result, weights, and model_version require a separate explicit task."
    if stage == READY_FOR_TRAINING_EVALUATION_DATASET:
        return "Review gates and rerun core with explicit allow only if report-only dataset/planning artifacts are intended."
    if stage == "TRAINING_EVALUATION_NO_INPUT":
        return "Provide frozen replay decision, forward label, governance, approval, leakage, and overclaim inputs."
    if stage == TRAINING_EVALUATION_HEALTH_FAILED:
        return "Fix health blockers before using training/evaluation dataset planning context."
    return "Resolve blocker gates; do not compute metrics, train weights, create stock_profile, buy-review, paper approval, or trading outputs."


def _safety_statement() -> str:
    return (
        "training/evaluation phase 1 is report-only dataset/planning-only. "
        "TRAINING_EVALUATION_DATASET_CREATED means dataset/planning artifacts only; it does not compute metrics, "
        "does not create training_result, does not train weights, does not create model_version, does not optimize thresholds, "
        "does not create predictions, does not create stock_profile, does not create buy-review eligibility, "
        "does not apply paper approval, does not claim strategy performance validation, and does not authorize trading."
    )


def _write(result: TrainingEvaluationStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "status_id": f"{result.latest_training_evaluation_run_id}:{result.workflow_stage}",
                "latest_training_evaluation_run_id": result.latest_training_evaluation_run_id,
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
                "# Training / Evaluation Status",
                "",
                f"- latest_training_evaluation_run_id: {result.latest_training_evaluation_run_id}",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- training_evaluation_dataset_artifacts_created: {result.training_evaluation_dataset_artifacts_created}",
                f"- dataset_sample_row_count: {result.dataset_sample_row_count}",
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
