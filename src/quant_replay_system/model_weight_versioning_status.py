"""Status summary for report-only model weight/versioning artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.model_weight_versioning import (
    DOWNSTREAM_FALSE_FIELDS,
    MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED,
    NO_MODEL_WEIGHT_VERSIONING_INPUT,
    READY_FOR_MODEL_WEIGHT_VERSIONING,
)
from quant_replay_system.model_weight_versioning_health import check_model_weight_versioning_health
from quant_replay_system.model_weight_versioning_index import DEFAULT_ROOT, build_model_weight_versioning_index
from quant_replay_system.model_weight_versioning_index import _text, _to_bool, _to_int


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"
NO_MODEL_WEIGHT_VERSIONING_ARTIFACT_FOUND = "NO_MODEL_WEIGHT_VERSIONING_ARTIFACT_FOUND"
MODEL_WEIGHT_VERSIONING_HEALTH_FAILED = "MODEL_WEIGHT_VERSIONING_HEALTH_FAILED"

SUMMARY_COLUMNS = [
    "latest_model_workflow_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "ready_for_model_weight_versioning",
    "model_weight_versioning_executed",
    "model_weight_versioning_research_artifacts_created",
    "training_result_row_count",
    "eligible_training_result_row_count",
    "quarantined_training_result_row_count",
    "metric_evidence_names_present",
    "metric_evidence_reference_count",
    "model_weights_reference_created",
    "model_version_metadata_created",
    "parameter_version_metadata_created",
    "threshold_plan_created",
    "prediction_rows_created",
    "probability_calibration_report_created",
    "feature_importance_report_created",
    *DOWNSTREAM_FALSE_FIELDS,
    "blocker_count",
    "warning_count",
    "report_path",
    "safety_statement",
    "next_action",
]


@dataclass(frozen=True)
class ModelWeightVersioningStatusResult:
    latest_model_workflow_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    ready_for_model_weight_versioning: bool
    model_weight_versioning_executed: bool
    model_weight_versioning_research_artifacts_created: bool
    training_result_row_count: int
    eligible_training_result_row_count: int
    quarantined_training_result_row_count: int
    metric_evidence_names_present: str
    metric_evidence_reference_count: int
    model_weights_reference_created: bool
    model_version_metadata_created: bool
    parameter_version_metadata_created: bool
    threshold_plan_created: bool
    prediction_rows_created: bool
    probability_calibration_report_created: bool
    feature_importance_report_created: bool
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


def run_model_weight_versioning_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ModelWeightVersioningStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_model_weight_versioning_index(root=root, output_dir=sibling_root / "index")
    health = check_model_weight_versioning_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        frame = index.index_frame.copy()
        frame["_status_priority"] = frame["status"].map(_status_priority)
        latest = frame.sort_values(["created_at", "_status_priority", "model_workflow_run_id"]).iloc[-1].to_dict()
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
) -> ModelWeightVersioningStatusResult:
    status = _text(latest.get("status"))
    stage = MODEL_WEIGHT_VERSIONING_HEALTH_FAILED if health_status == "FAIL" else _text(latest.get("workflow_stage")) or status
    summary = {
        "latest_model_workflow_run_id": _text(latest.get("model_workflow_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "ready_for_model_weight_versioning": _to_bool(latest.get("ready_for_model_weight_versioning")),
        "model_weight_versioning_executed": _to_bool(latest.get("model_weight_versioning_executed")),
        "model_weight_versioning_research_artifacts_created": _to_bool(latest.get("model_weight_versioning_research_artifacts_created")),
        "training_result_row_count": _to_int(latest.get("training_result_row_count")),
        "eligible_training_result_row_count": _to_int(latest.get("eligible_training_result_row_count")),
        "quarantined_training_result_row_count": _to_int(latest.get("quarantined_training_result_row_count")),
        "metric_evidence_names_present": _text(latest.get("metric_evidence_names_present")),
        "metric_evidence_reference_count": _to_int(latest.get("metric_evidence_reference_count")),
        "model_weights_reference_created": _to_bool(latest.get("model_weights_reference_created")),
        "model_version_metadata_created": _to_bool(latest.get("model_version_metadata_created")),
        "parameter_version_metadata_created": _to_bool(latest.get("parameter_version_metadata_created")),
        "threshold_plan_created": _to_bool(latest.get("threshold_plan_created")),
        "prediction_rows_created": _to_bool(latest.get("prediction_rows_created")),
        "probability_calibration_report_created": _to_bool(latest.get("probability_calibration_report_created")),
        "feature_importance_report_created": _to_bool(latest.get("feature_importance_report_created")),
        **{field: _to_bool(latest.get(field)) for field in DOWNSTREAM_FALSE_FIELDS},
        "blocker_count": max(_to_int(latest.get("blocker_count")), error_count),
        "warning_count": max(_to_int(latest.get("warning_count")), warning_count),
        "report_path": _text(latest.get("report_path")),
        "safety_statement": _safety_statement(status),
        "next_action": _next_action(stage, status),
    }
    return _result(summary, output_dir, root, [])


def _no_artifact_result(
    output_dir: str | Path,
    root: str | Path,
    health_status: str,
    error_count: int,
    warning_count: int,
) -> ModelWeightVersioningStatusResult:
    summary = {
        "latest_model_workflow_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_MODEL_WEIGHT_VERSIONING_ARTIFACT_FOUND,
        "ready_for_model_weight_versioning": False,
        "model_weight_versioning_executed": False,
        "model_weight_versioning_research_artifacts_created": False,
        "training_result_row_count": 0,
        "eligible_training_result_row_count": 0,
        "quarantined_training_result_row_count": 0,
        "metric_evidence_names_present": "",
        "metric_evidence_reference_count": 0,
        "model_weights_reference_created": False,
        "model_version_metadata_created": False,
        "parameter_version_metadata_created": False,
        "threshold_plan_created": False,
        "prediction_rows_created": False,
        "probability_calibration_report_created": False,
        "feature_importance_report_created": False,
        **{field: False for field in DOWNSTREAM_FALSE_FIELDS},
        "blocker_count": max(error_count, 1),
        "warning_count": warning_count,
        "report_path": "",
        "safety_statement": _safety_statement(""),
        "next_action": "Create or provide report-only model weight versioning artifacts before checking status.",
    }
    return _result(summary, output_dir, root, [])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> ModelWeightVersioningStatusResult:
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "model_weight_versioning_status.csv",
        "status_report": Path(output_dir) / "model_weight_versioning_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    return ModelWeightVersioningStatusResult(
        summary_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata={"root": str(root), "report_only": True, "diagnostic_only": True},
        **summary,
    )


def _write(result: ModelWeightVersioningStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "latest_model_workflow_run_id": result.latest_model_workflow_run_id,
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
                "# Model Weight Versioning Status",
                "",
                result.safety_statement,
                "",
                f"- latest_model_workflow_run_id: {result.latest_model_workflow_run_id}",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- model_weight_versioning_research_artifacts_created: {result.model_weight_versioning_research_artifacts_created}",
                f"- training_result_row_count: {result.training_result_row_count}",
                f"- metric_evidence_names_present: {result.metric_evidence_names_present}",
                f"- next_action: {result.next_action}",
                "",
                result.summary_frame.to_markdown(index=False),
            ]
        ),
        encoding="utf-8",
    )


def _safety_statement(status: str) -> str:
    created_clause = (
        "MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED means report-only research artifacts. "
        if status == MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED
        else ""
    )
    return (
        "Model weight versioning phase 1 is report-only research artifact creation only. "
        f"{created_clause}"
        "It is not active stock_profile, does not create active stock_profile, does not create buy-review eligibility, "
        "is not buy-review, does not apply paper approval, is not paper approval, "
        "does not claim strategy performance validation, is not performance validation, "
        "does not authorize trading, and is not trading. "
        "The model weights reference is not executable trading model. "
        "The model_version metadata is not active/promoted/production model. "
        "The threshold plan is not active signal semantics. "
        "Prediction rows are not advisory signals."
    )


def _next_action(stage: str, status: str) -> str:
    if stage == MODEL_WEIGHT_VERSIONING_HEALTH_FAILED:
        return "Resolve model weight versioning health errors before trusting artifact views."
    if status == MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED:
        return "Review report-only model weight versioning artifact views before research-status integration."
    if status == READY_FOR_MODEL_WEIGHT_VERSIONING:
        return "Rerun with explicit allow only if report-only model research artifacts should be created."
    if status == NO_MODEL_WEIGHT_VERSIONING_INPUT:
        return "Provide exact approval and complete upstream TRAINING_RESULT_CREATED lineage before model weight versioning."
    return "Review model weight versioning gates and artifacts before any next workflow."


def _status_priority(status: Any) -> int:
    text = _text(status)
    if text == MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED:
        return 3
    if text == READY_FOR_MODEL_WEIGHT_VERSIONING:
        return 2
    if text == NO_MODEL_WEIGHT_VERSIONING_INPUT:
        return 1
    return 0
