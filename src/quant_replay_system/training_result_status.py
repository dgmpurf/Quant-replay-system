"""Status summary for report-only actual training_result phase 1 artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.training_result import (
    DOWNSTREAM_FALSE_FIELDS,
    NO_TRAINING_RESULT_INPUT,
    READY_FOR_TRAINING_RESULT,
    TRAINING_RESULT_CREATED,
)
from quant_replay_system.training_result_health import check_training_result_health
from quant_replay_system.training_result_index import DEFAULT_ROOT, build_training_result_index
from quant_replay_system.training_result_index import _text, _to_bool, _to_int


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"
NO_TRAINING_RESULT_ARTIFACT_FOUND = "NO_TRAINING_RESULT_ARTIFACT_FOUND"
TRAINING_RESULT_HEALTH_FAILED = "TRAINING_RESULT_HEALTH_FAILED"

SUMMARY_COLUMNS = [
    "latest_training_result_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "ready_for_training_result",
    "training_result_executed",
    "training_result_created",
    "training_result_row_count",
    "eligible_training_result_row_count",
    "quarantined_training_result_row_count",
    "metric_evidence_names_present",
    "metric_evidence_reference_count",
    "limitations_created",
    "overfit_warnings_created",
    "input_index_row_count",
    "metric_evidence_reference_row_count",
    "lineage_matrix_row_count",
    "overfit_warning_row_count",
    *DOWNSTREAM_FALSE_FIELDS,
    "blocker_count",
    "warning_count",
    "report_path",
    "safety_statement",
    "next_action",
]


@dataclass(frozen=True)
class TrainingResultStatusResult:
    latest_training_result_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    ready_for_training_result: bool
    training_result_executed: bool
    training_result_created: bool
    training_result_row_count: int
    eligible_training_result_row_count: int
    quarantined_training_result_row_count: int
    metric_evidence_names_present: str
    metric_evidence_reference_count: int
    limitations_created: bool
    overfit_warnings_created: bool
    input_index_row_count: int
    metric_evidence_reference_row_count: int
    lineage_matrix_row_count: int
    overfit_warning_row_count: int
    weights_trained: bool
    model_version_created: bool
    parameter_version_created: bool
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


def run_training_result_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> TrainingResultStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_training_result_index(root=root, output_dir=sibling_root / "index")
    health = check_training_result_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        frame = index.index_frame.copy()
        frame["_status_priority"] = frame["status"].map(_status_priority)
        latest = frame.sort_values(["created_at", "_status_priority", "training_result_run_id"]).iloc[-1].to_dict()
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
) -> TrainingResultStatusResult:
    status = _text(latest.get("status"))
    stage = TRAINING_RESULT_HEALTH_FAILED if health_status == "FAIL" else _text(latest.get("workflow_stage")) or status
    summary = {
        "latest_training_result_run_id": _text(latest.get("training_result_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "ready_for_training_result": _to_bool(latest.get("ready_for_training_result")),
        "training_result_executed": _to_bool(latest.get("training_result_executed")),
        "training_result_created": _to_bool(latest.get("training_result_created")),
        "training_result_row_count": _to_int(latest.get("training_result_row_count")),
        "eligible_training_result_row_count": _to_int(latest.get("eligible_training_result_row_count")),
        "quarantined_training_result_row_count": _to_int(latest.get("quarantined_training_result_row_count")),
        "metric_evidence_names_present": _text(latest.get("metric_evidence_names_present")),
        "metric_evidence_reference_count": _to_int(latest.get("metric_evidence_reference_count")),
        "limitations_created": _to_bool(latest.get("limitations_created")),
        "overfit_warnings_created": _to_bool(latest.get("overfit_warnings_created")),
        "input_index_row_count": _to_int(latest.get("input_index_row_count")),
        "metric_evidence_reference_row_count": _to_int(latest.get("metric_evidence_reference_row_count")),
        "lineage_matrix_row_count": _to_int(latest.get("lineage_matrix_row_count")),
        "overfit_warning_row_count": _to_int(latest.get("overfit_warning_row_count")),
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
) -> TrainingResultStatusResult:
    summary = {
        "latest_training_result_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_TRAINING_RESULT_ARTIFACT_FOUND,
        "ready_for_training_result": False,
        "training_result_executed": False,
        "training_result_created": False,
        "training_result_row_count": 0,
        "eligible_training_result_row_count": 0,
        "quarantined_training_result_row_count": 0,
        "metric_evidence_names_present": "",
        "metric_evidence_reference_count": 0,
        "limitations_created": False,
        "overfit_warnings_created": False,
        "input_index_row_count": 0,
        "metric_evidence_reference_row_count": 0,
        "lineage_matrix_row_count": 0,
        "overfit_warning_row_count": 0,
        **{field: False for field in DOWNSTREAM_FALSE_FIELDS},
        "blocker_count": max(error_count, 1),
        "warning_count": warning_count,
        "report_path": "",
        "safety_statement": _safety_statement(""),
        "next_action": "Create or provide report-only actual training_result artifacts before checking status.",
    }
    return _result(summary, output_dir, root, [])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> TrainingResultStatusResult:
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "training_result_status.csv",
        "status_report": Path(output_dir) / "training_result_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    return TrainingResultStatusResult(
        summary_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata={"root": str(root), "report_only": True, "diagnostic_only": True},
        **summary,
    )


def _write(result: TrainingResultStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "latest_training_result_run_id": result.latest_training_result_run_id,
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
                "# Actual Training Result Status",
                "",
                result.safety_statement,
                "",
                f"- latest_training_result_run_id: {result.latest_training_result_run_id}",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- training_result_created: {result.training_result_created}",
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
        "TRAINING_RESULT_CREATED means report-only actual training_result artifacts only. "
        if status == TRAINING_RESULT_CREATED
        else ""
    )
    return (
        "Actual training_result phase 1 is report-only artifact creation only. "
        f"{created_clause}"
        "It does not train weights, does not create model_version, does not create parameter_version, "
        "does not optimize thresholds, does not create predictions/probabilities/feature importance, "
        "does not create stock_profile, does not create buy-review eligibility, does not apply paper approval, "
        "does not claim strategy performance validation, and does not authorize trading. "
        "In short: not weights, not model_version, not parameter_version, not thresholds, "
        "not predictions/probabilities/feature importance, not stock_profile, not buy-review, "
        "not paper approval, not performance validation, and not trading."
    )


def _next_action(stage: str, status: str) -> str:
    if stage == TRAINING_RESULT_HEALTH_FAILED:
        return "Resolve actual training_result health errors before trusting artifact views."
    if status == TRAINING_RESULT_CREATED:
        return "Review report-only actual training_result artifact views before research-status integration."
    if status == READY_FOR_TRAINING_RESULT:
        return "Rerun with explicit allow only if report-only actual training_result artifacts should be created."
    if status == NO_TRAINING_RESULT_INPUT:
        return "Provide exact approval and complete upstream report-only lineage before actual training_result creation."
    return "Review actual training_result gates and artifacts before any next workflow."


def _status_priority(status: Any) -> int:
    text = _text(status)
    if text == TRAINING_RESULT_CREATED:
        return 3
    if text == READY_FOR_TRAINING_RESULT:
        return 2
    if text == NO_TRAINING_RESULT_INPUT:
        return 1
    return 0
