"""Report-only training result planning phase 1 workflow."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_TRAINING_RESULT_PLANNING_INPUT = "NO_TRAINING_RESULT_PLANNING_INPUT"
TRAINING_RESULT_PLANNING_INPUT_FOUND = "TRAINING_RESULT_PLANNING_INPUT_FOUND"
TRAINING_RESULT_PLANNING_APPROVAL_BLOCKED = "TRAINING_RESULT_PLANNING_APPROVAL_BLOCKED"
TRAINING_RESULT_PLANNING_METRIC_EXTENSION_INPUT_BLOCKED = "TRAINING_RESULT_PLANNING_METRIC_EXTENSION_INPUT_BLOCKED"
TRAINING_RESULT_PLANNING_METRIC_COMPUTATION_INPUT_BLOCKED = "TRAINING_RESULT_PLANNING_METRIC_COMPUTATION_INPUT_BLOCKED"
TRAINING_RESULT_PLANNING_METRIC_EVALUATION_INPUT_BLOCKED = "TRAINING_RESULT_PLANNING_METRIC_EVALUATION_INPUT_BLOCKED"
TRAINING_RESULT_PLANNING_TRAINING_EVALUATION_INPUT_BLOCKED = "TRAINING_RESULT_PLANNING_TRAINING_EVALUATION_INPUT_BLOCKED"
TRAINING_RESULT_PLANNING_FORWARD_LABEL_INPUT_BLOCKED = "TRAINING_RESULT_PLANNING_FORWARD_LABEL_INPUT_BLOCKED"
TRAINING_RESULT_PLANNING_REPLAY_FREEZE_INPUT_BLOCKED = "TRAINING_RESULT_PLANNING_REPLAY_FREEZE_INPUT_BLOCKED"
TRAINING_RESULT_PLANNING_HEALTH_BLOCKED = "TRAINING_RESULT_PLANNING_HEALTH_BLOCKED"
TRAINING_RESULT_PLANNING_LINEAGE_BLOCKED = "TRAINING_RESULT_PLANNING_LINEAGE_BLOCKED"
TRAINING_RESULT_PLANNING_METRIC_EVIDENCE_BLOCKED = "TRAINING_RESULT_PLANNING_METRIC_EVIDENCE_BLOCKED"
TRAINING_RESULT_PLANNING_DENOMINATOR_BLOCKED = "TRAINING_RESULT_PLANNING_DENOMINATOR_BLOCKED"
TRAINING_RESULT_PLANNING_SAMPLE_SCOPE_BLOCKED = "TRAINING_RESULT_PLANNING_SAMPLE_SCOPE_BLOCKED"
TRAINING_RESULT_PLANNING_REPORT_ONLY_BLOCKED = "TRAINING_RESULT_PLANNING_REPORT_ONLY_BLOCKED"
TRAINING_RESULT_PLANNING_FORBIDDEN_ARTIFACT_BLOCKED = "TRAINING_RESULT_PLANNING_FORBIDDEN_ARTIFACT_BLOCKED"
TRAINING_RESULT_PLANNING_LEAKAGE_BLOCKED = "TRAINING_RESULT_PLANNING_LEAKAGE_BLOCKED"
TRAINING_RESULT_PLANNING_SIDE_EFFECT_BLOCKED = "TRAINING_RESULT_PLANNING_SIDE_EFFECT_BLOCKED"
TRAINING_RESULT_PLANNING_OVERCLAIM_BLOCKED = "TRAINING_RESULT_PLANNING_OVERCLAIM_BLOCKED"
READY_FOR_TRAINING_RESULT_PLANNING = "READY_FOR_TRAINING_RESULT_PLANNING"
TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED = "TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED"

EXACT_TRAINING_RESULT_PLANNING_APPROVAL_TEXT = (
    "I explicitly authorize Training Result Planning Implementation phase 1 only, and only as "
    "report-only planning artifacts. It may create training_result planning metadata, input index, "
    "metric evidence index, lineage matrix, model scope plan, limitations, overfit warnings, health "
    "plan, status plan, recommended_next_task, and similar report-only planning artifacts only when "
    "immutable METRIC_EXTENSION_REPORT_CREATED, METRIC_COMPUTATION_REPORT_CREATED, "
    "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED, TRAINING_EVALUATION_DATASET_CREATED, "
    "FORWARD_RETURN_LABELS_CREATED, and REPLAY_DECISION_FROZEN artifacts have complete lineage and "
    "PASS health. This phase must not create actual training_result, train weights, create "
    "model_version, create parameter_version, optimize thresholds, create predictions, create "
    "calibrated probabilities, create feature importance, create stock_profile, generate buy-review "
    "eligibility, apply paper approval, claim strategy performance validation, integrate "
    "broker/order/message, or trade. If any upstream lineage, health, available_time, source_hash, "
    "revision_id, quality_status, report_only/diagnostic_only, denominator/sample scope, or metric "
    "evidence is missing, it must fail closed and create no planning artifacts."
)

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/training_result_planning_v0_1")

ARTIFACT_FILES = {
    "metadata": "training_result_planning_metadata.json",
    "report": "training_result_planning_report.md",
    "input_index": "training_result_planning_input_index.csv",
    "metric_evidence_index": "training_result_planning_metric_evidence_index.csv",
    "lineage_matrix": "training_result_planning_lineage_matrix.csv",
    "model_scope": "training_result_planning_model_scope.csv",
    "limitations": "training_result_planning_limitations.md",
    "overfit_warnings": "training_result_planning_overfit_warnings.csv",
    "health_plan": "training_result_planning_health_plan.csv",
    "status_plan": "training_result_planning_status_plan.csv",
    "safety_flags": "training_result_planning_safety_flags.json",
    "precondition_results": "training_result_planning_precondition_results.csv",
    "approval_results": "training_result_planning_approval_results.csv",
    "input_lineage_results": "training_result_planning_input_lineage_results.csv",
    "metric_evidence_results": "training_result_planning_metric_evidence_results.csv",
    "leakage_guard_results": "training_result_planning_leakage_guard_results.csv",
    "side_effect_guard_results": "training_result_planning_side_effect_guard_results.csv",
    "overclaim_guard_results": "training_result_planning_overclaim_guard_results.csv",
    "recommended_next_task": "recommended_next_task.md",
}

FORBIDDEN_ARTIFACT_NAMES = {
    "training_result_metadata.json",
    "training_result_rows.csv",
    "training_result_status.json",
    "model_weights.json",
    "model_weights.csv",
    "model_version.json",
    "parameter_version.json",
    "thresholds.csv",
    "threshold_set.csv",
    "predictions.csv",
    "probabilities.csv",
    "feature_importance.csv",
    "calibration_report.md",
    "validation_report.md",
    "performance_validation_report.md",
    "stock_profile.csv",
    "stock_profile.json",
    "buy_review.csv",
    "paper_approval.json",
    "broker_orders.csv",
}

DOWNSTREAM_FALSE_FIELDS = [
    "training_result_created",
    "weights_trained",
    "model_version_created",
    "parameter_version_created",
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
OVERCLAIM_REQUEST_FIELDS = {
    "actual_training_result_requested",
    "training_result_requested",
    "weights_requested",
    "model_version_requested",
    "parameter_version_requested",
    "thresholds_requested",
    "predictions_requested",
    "calibrated_probabilities_requested",
    "feature_importance_requested",
    "stock_profile_requested",
    "buy_review_requested",
    "paper_approval_requested",
    "performance_validation_requested",
}
SIDE_EFFECT_REQUEST_FIELDS = {"trading_requested", "broker_api_called", "order_placed", "message_sent"}
REQUIRED_OVERCLAIM_TRUE = {
    "training_result_planning_not_actual_training_result",
    "training_result_planning_not_weights",
    "training_result_planning_not_model_version",
    "training_result_planning_not_parameter_version",
    "training_result_planning_not_thresholds",
    "training_result_planning_not_predictions",
    "training_result_planning_not_probabilities",
    "training_result_planning_not_feature_importance",
    "training_result_planning_not_stock_profile",
    "training_result_planning_not_buy_review",
    "training_result_planning_not_paper_approval",
    "training_result_planning_not_performance_validation",
    "training_result_planning_not_trading",
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
LINEAGE_COLUMNS = {
    "metric_extension_run_id",
    "metric_computation_run_id",
    "metric_evaluation_run_id",
    "training_evaluation_run_id",
    "forward_return_label_run_id",
    "replay_decision_freeze_run_id",
    "replay_decision_id",
    "forward_return_label_id",
    "symbol",
    "replay_as_of_date",
    "split_role",
    "label_name",
    "horizon_trading_days",
    "metric_name",
    "metric_value",
    "source_hash",
    "revision_id",
    "available_time",
    "quality_status",
}


@dataclass(frozen=True)
class TrainingResultPlanningSettings:
    approval_manifest_path: Path | None = None
    training_result_planning_request_manifest_path: Path | None = None
    metric_extension_metadata_path: Path | None = None
    metric_extension_result_rows_path: Path | None = None
    metric_extension_summary_path: Path | None = None
    metric_extension_safety_flags_path: Path | None = None
    metric_extension_status_artifact_path: Path | None = None
    metric_extension_health_artifact_path: Path | None = None
    metric_computation_metadata_path: Path | None = None
    metric_computation_result_rows_path: Path | None = None
    metric_computation_summary_path: Path | None = None
    metric_computation_safety_flags_path: Path | None = None
    metric_computation_status_artifact_path: Path | None = None
    metric_computation_health_artifact_path: Path | None = None
    metric_evaluation_metadata_path: Path | None = None
    metric_evaluation_input_index_path: Path | None = None
    metric_evaluation_sample_scope_path: Path | None = None
    metric_evaluation_denominator_rules_path: Path | None = None
    metric_evaluation_safety_flags_path: Path | None = None
    metric_evaluation_status_artifact_path: Path | None = None
    metric_evaluation_health_artifact_path: Path | None = None
    training_evaluation_metadata_path: Path | None = None
    training_evaluation_sample_rows_path: Path | None = None
    training_evaluation_safety_flags_path: Path | None = None
    training_evaluation_status_artifact_path: Path | None = None
    training_evaluation_health_artifact_path: Path | None = None
    forward_return_label_metadata_path: Path | None = None
    forward_return_label_rows_path: Path | None = None
    forward_return_label_status_artifact_path: Path | None = None
    forward_return_label_health_artifact_path: Path | None = None
    replay_decision_freeze_metadata_path: Path | None = None
    replay_decision_freeze_rows_path: Path | None = None
    replay_decision_freeze_status_artifact_path: Path | None = None
    replay_decision_freeze_health_artifact_path: Path | None = None
    leakage_evidence_bundle_path: Path | None = None
    overclaim_evidence_bundle_path: Path | None = None
    side_effect_evidence_bundle_path: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    allow_training_result_planning: bool = False
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class TrainingResultPlanningGateResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str = ""
    observed_value: str = ""


TrainingResultPlanningApprovalResult = TrainingResultPlanningGateResult
TrainingResultPlanningInputLineageResult = TrainingResultPlanningGateResult
TrainingResultPlanningMetricEvidenceResult = TrainingResultPlanningGateResult
TrainingResultPlanningModelScopeResult = TrainingResultPlanningGateResult
TrainingResultPlanningLimitationsResult = TrainingResultPlanningGateResult
TrainingResultPlanningOverfitWarningResult = TrainingResultPlanningGateResult
TrainingResultPlanningHealthPlanResult = TrainingResultPlanningGateResult
TrainingResultPlanningStatusPlanResult = TrainingResultPlanningGateResult
TrainingResultPlanningLeakageGuardResult = TrainingResultPlanningGateResult
TrainingResultPlanningSideEffectGuardResult = TrainingResultPlanningGateResult
TrainingResultPlanningOverclaimResult = TrainingResultPlanningGateResult


@dataclass(frozen=True)
class TrainingResultPlanningResult:
    training_result_planning_run_id: str
    status: str
    workflow_stage: str
    ready_for_training_result_planning: bool
    training_result_planning_executed: bool
    training_result_planning_artifacts_created: bool
    artifact_path: str
    source_metric_extension_run_id: str = ""
    source_metric_extension_status: str = ""
    source_metric_extension_health_status: str = ""
    source_metric_computation_run_id: str = ""
    source_metric_computation_status: str = ""
    source_metric_computation_health_status: str = ""
    source_metric_evaluation_planning_run_id: str = ""
    source_metric_evaluation_status: str = ""
    source_metric_evaluation_health_status: str = ""
    source_training_evaluation_run_id: str = ""
    source_training_evaluation_status: str = ""
    source_training_evaluation_health_status: str = ""
    source_forward_return_label_run_id: str = ""
    source_forward_return_label_status: str = ""
    source_forward_return_label_health_status: str = ""
    source_replay_decision_freeze_run_id: str = ""
    source_replay_decision_freeze_status: str = ""
    source_replay_decision_freeze_health_status: str = ""
    metric_evidence_names_present: str = ""
    metric_evidence_row_count: int = 0
    planning_input_row_count: int = 0
    eligible_planning_input_count: int = 0
    quarantined_planning_input_count: int = 0
    model_scope_rows_created: bool = False
    limitations_created: bool = False
    overfit_warnings_created: bool = False
    health_plan_created: bool = False
    status_plan_created: bool = False
    blocker_count: int = 0
    warning_count: int = 0
    next_action: str = ""
    safety_statement: str = (
        "Training result planning phase 1 is report-only: no actual training_result, no weights, "
        "no model_version, no parameter_version, no thresholds, no predictions, no calibrated "
        "probabilities, no feature importance, no stock_profile, no buy-review, no paper approval, "
        "no strategy performance validation, no broker/order/message/API/cache/data side effects, "
        "no current-candidates, no snapshots, no forward labels, and no trading."
    )
    report_only: bool = True
    diagnostic_only: bool = True
    artifact_paths: dict[str, Path] = field(default_factory=dict)
    gate_results: list[TrainingResultPlanningGateResult] = field(default_factory=list)
    training_result_created: bool = False
    weights_trained: bool = False
    model_version_created: bool = False
    parameter_version_created: bool = False
    thresholds_optimized: bool = False
    predictions_created: bool = False
    calibrated_probabilities_created: bool = False
    feature_importance_created: bool = False
    stock_profile_allowed: bool = False
    active_stock_profile_exists: bool = False
    stock_profile_created: bool = False
    buy_review_allowed: bool = False
    real_buy_review_eligible: bool = False
    approved_for_paper: bool = False
    strategy_performance_validated: bool = False
    trading_allowed: bool = False
    order_placed: bool = False
    broker_api_called: bool = False
    message_sent: bool = False
    llm_api_called: bool = False
    external_api_called: bool = False
    cache_mutated: bool = False
    data_raw_written: bool = False
    data_processed_written: bool = False
    data_cache_written: bool = False
    current_candidates_run: bool = False
    snapshot_built: bool = False
    signal_semantics_changed: bool = False


def run_training_result_planning(
    settings: TrainingResultPlanningSettings | None = None,
) -> TrainingResultPlanningResult:
    settings = settings or TrainingResultPlanningSettings()
    output_root = Path(settings.output_dir)
    _assert_manual_diagnostics_output(output_root)
    run_id = _stable_id(settings)
    artifact_dir = output_root / run_id
    artifact_paths = {"artifact_dir": artifact_dir} | {
        key: artifact_dir / filename for key, filename in ARTIFACT_FILES.items()
    }
    state = _evaluate(settings)
    created = state["status"] == TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED
    ready = state["status"] in {READY_FOR_TRAINING_RESULT_PLANNING, TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED}
    metric_extension_meta = state.get("metric_extension_metadata", {})
    metric_computation_meta = state.get("metric_computation_metadata", {})
    metric_evaluation_meta = state.get("metric_evaluation_metadata", {})
    training_evaluation_meta = state.get("training_evaluation_metadata", {})
    forward_label_meta = state.get("forward_label_metadata", {})
    replay_freeze_meta = state.get("replay_freeze_metadata", {})
    result = TrainingResultPlanningResult(
        training_result_planning_run_id=run_id,
        status=state["status"],
        workflow_stage=(
            "TRAINING_RESULT_PLANNING_NO_INPUT"
            if state["status"] == NO_TRAINING_RESULT_PLANNING_INPUT
            else state["status"]
        ),
        ready_for_training_result_planning=ready,
        training_result_planning_executed=created,
        training_result_planning_artifacts_created=created,
        artifact_path=str(artifact_dir),
        source_metric_extension_run_id=str(metric_extension_meta.get("metric_extension_run_id", "")),
        source_metric_extension_status=str(metric_extension_meta.get("status", metric_extension_meta.get("execution_status", ""))),
        source_metric_extension_health_status=_status_value(settings.metric_extension_health_artifact_path),
        source_metric_computation_run_id=str(metric_computation_meta.get("metric_computation_run_id", "")),
        source_metric_computation_status=str(metric_computation_meta.get("status", metric_computation_meta.get("execution_status", ""))),
        source_metric_computation_health_status=_status_value(settings.metric_computation_health_artifact_path),
        source_metric_evaluation_planning_run_id=str(metric_evaluation_meta.get("metric_evaluation_run_id", "")),
        source_metric_evaluation_status=str(metric_evaluation_meta.get("status", metric_evaluation_meta.get("execution_status", ""))),
        source_metric_evaluation_health_status=_status_value(settings.metric_evaluation_health_artifact_path),
        source_training_evaluation_run_id=str(training_evaluation_meta.get("training_evaluation_run_id", "")),
        source_training_evaluation_status=str(training_evaluation_meta.get("status", training_evaluation_meta.get("execution_status", ""))),
        source_training_evaluation_health_status=_status_value(settings.training_evaluation_health_artifact_path),
        source_forward_return_label_run_id=str(forward_label_meta.get("forward_return_label_run_id", "")),
        source_forward_return_label_status=str(forward_label_meta.get("status", forward_label_meta.get("execution_status", ""))),
        source_forward_return_label_health_status=_status_value(settings.forward_return_label_health_artifact_path),
        source_replay_decision_freeze_run_id=str(replay_freeze_meta.get("replay_decision_freeze_run_id", "")),
        source_replay_decision_freeze_status=str(replay_freeze_meta.get("status", replay_freeze_meta.get("execution_status", ""))),
        source_replay_decision_freeze_health_status=_status_value(settings.replay_decision_freeze_health_artifact_path),
        metric_evidence_names_present=",".join(state.get("metric_evidence_names", [])),
        metric_evidence_row_count=len(state.get("metric_evidence_index", [])),
        planning_input_row_count=len(state.get("lineage_rows", [])),
        eligible_planning_input_count=len(state.get("lineage_rows", [])),
        quarantined_planning_input_count=state.get("quarantined_planning_input_count", 0),
        model_scope_rows_created=created,
        limitations_created=created,
        overfit_warnings_created=created,
        health_plan_created=created,
        status_plan_created=created,
        blocker_count=0 if ready else 0 if state["status"] == NO_TRAINING_RESULT_PLANNING_INPUT else 1,
        warning_count=len(_overfit_warnings()) if created else 0,
        next_action=_next_action(state["status"]),
        artifact_paths=artifact_paths,
        gate_results=state.get("gate_results", []),
    )
    if settings.write_artifacts:
        write_training_result_planning_artifacts(result, state)
    return result


def write_training_result_planning_artifacts(
    result: TrainingResultPlanningResult,
    state: dict[str, Any] | None = None,
) -> None:
    state = state or {}
    artifact_dir = result.artifact_paths["artifact_dir"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    result.artifact_paths["metadata"].write_text(json.dumps(_metadata(result), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["safety_flags"].write_text(json.dumps(_safety_flags(result), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(_recommended_next_task(result), encoding="utf-8")
    for key, group in [
        ("precondition_results", "precondition"),
        ("approval_results", "approval"),
        ("input_lineage_results", "input_lineage"),
        ("metric_evidence_results", "metric_evidence"),
        ("leakage_guard_results", "leakage_guard"),
        ("side_effect_guard_results", "side_effect_guard"),
        ("overclaim_guard_results", "overclaim_guard"),
    ]:
        _write_csv(result.artifact_paths[key], _gate_frame(state.get("gate_results", []), group))
    if result.training_result_planning_artifacts_created:
        _write_csv(result.artifact_paths["input_index"], _input_index(result))
        _write_csv(result.artifact_paths["metric_evidence_index"], pd.DataFrame(state.get("metric_evidence_index", [])))
        _write_csv(result.artifact_paths["lineage_matrix"], pd.DataFrame(state.get("lineage_rows", [])))
        _write_csv(result.artifact_paths["model_scope"], _model_scope())
        result.artifact_paths["limitations"].write_text(_limitations(), encoding="utf-8")
        _write_csv(result.artifact_paths["overfit_warnings"], pd.DataFrame(_overfit_warnings()))
        _write_csv(result.artifact_paths["health_plan"], _health_plan())
        _write_csv(result.artifact_paths["status_plan"], _status_plan())


def _evaluate(settings: TrainingResultPlanningSettings) -> dict[str, Any]:
    state: dict[str, Any] = {"status": NO_TRAINING_RESULT_PLANNING_INPUT, "gate_results": []}
    if _is_no_input(settings):
        return state
    approval = _load_json(settings.approval_manifest_path)
    if str(approval.get("approval_text", "")) != EXACT_TRAINING_RESULT_PLANNING_APPROVAL_TEXT:
        return _blocked(TRAINING_RESULT_PLANNING_APPROVAL_BLOCKED, "approval", "exact_approval", "exact approval missing")
    request = _load_json(settings.training_result_planning_request_manifest_path)
    if _any_truthy(request, OVERCLAIM_REQUEST_FIELDS):
        return _blocked(TRAINING_RESULT_PLANNING_OVERCLAIM_BLOCKED, "overclaim_guard", "request_scope", "request asks for forbidden downstream artifact")
    if _any_truthy(request, SIDE_EFFECT_REQUEST_FIELDS):
        return _blocked(TRAINING_RESULT_PLANNING_SIDE_EFFECT_BLOCKED, "side_effect_guard", "request_side_effect", "request asks for side effects")
    missing = _first_missing_required_path(settings)
    if missing:
        return _blocked(missing[1], "precondition", missing[0], "required input missing")
    if _forbidden_artifact_exists(settings):
        return _blocked(TRAINING_RESULT_PLANNING_FORBIDDEN_ARTIFACT_BLOCKED, "precondition", "forbidden_artifact", "actual training/model artifact exists in input folders")

    metas = {
        "metric_extension_metadata": _load_json(settings.metric_extension_metadata_path),
        "metric_computation_metadata": _load_json(settings.metric_computation_metadata_path),
        "metric_evaluation_metadata": _load_json(settings.metric_evaluation_metadata_path),
        "training_evaluation_metadata": _load_json(settings.training_evaluation_metadata_path),
        "forward_label_metadata": _load_json(settings.forward_return_label_metadata_path),
        "replay_freeze_metadata": _load_json(settings.replay_decision_freeze_metadata_path),
    }
    expected_statuses = [
        ("metric_extension_metadata", settings.metric_extension_status_artifact_path, "METRIC_EXTENSION_REPORT_CREATED", TRAINING_RESULT_PLANNING_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_computation_metadata", settings.metric_computation_status_artifact_path, "METRIC_COMPUTATION_REPORT_CREATED", TRAINING_RESULT_PLANNING_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_evaluation_metadata", settings.metric_evaluation_status_artifact_path, "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED", TRAINING_RESULT_PLANNING_METRIC_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_metadata", settings.training_evaluation_status_artifact_path, "TRAINING_EVALUATION_DATASET_CREATED", TRAINING_RESULT_PLANNING_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("forward_label_metadata", settings.forward_return_label_status_artifact_path, "FORWARD_RETURN_LABELS_CREATED", TRAINING_RESULT_PLANNING_FORWARD_LABEL_INPUT_BLOCKED),
        ("replay_freeze_metadata", settings.replay_decision_freeze_status_artifact_path, "REPLAY_DECISION_FROZEN", TRAINING_RESULT_PLANNING_REPLAY_FREEZE_INPUT_BLOCKED),
    ]
    for meta_key, status_path, expected, blocked_status in expected_statuses:
        observed = _metadata_status(metas[meta_key]) or _status_value(status_path)
        if observed != expected:
            return _blocked(blocked_status, "precondition", meta_key, f"expected {expected}, observed {observed}")
    for path in [
        settings.metric_extension_health_artifact_path,
        settings.metric_computation_health_artifact_path,
        settings.metric_evaluation_health_artifact_path,
        settings.training_evaluation_health_artifact_path,
        settings.forward_return_label_health_artifact_path,
        settings.replay_decision_freeze_health_artifact_path,
    ]:
        if _status_value(path) != "PASS":
            return _blocked(TRAINING_RESULT_PLANNING_HEALTH_BLOCKED, "precondition", "health", "upstream health must be PASS")

    for path in [
        settings.metric_extension_safety_flags_path,
        settings.metric_computation_safety_flags_path,
        settings.metric_evaluation_safety_flags_path,
        settings.training_evaluation_safety_flags_path,
        settings.side_effect_evidence_bundle_path,
    ]:
        if _unsafe_side_effects(_load_json(path)):
            return _blocked(TRAINING_RESULT_PLANNING_SIDE_EFFECT_BLOCKED, "side_effect_guard", str(path), "unsafe side-effect flag")
    overclaim = _load_json(settings.overclaim_evidence_bundle_path)
    if any(not _truthy(overclaim.get(field)) for field in REQUIRED_OVERCLAIM_TRUE):
        return _blocked(TRAINING_RESULT_PLANNING_OVERCLAIM_BLOCKED, "overclaim_guard", "overclaim_bundle", "required overclaim guard missing")
    leakage = _load_json(settings.leakage_evidence_bundle_path)
    if any(_truthy(value) for value in leakage.values()):
        return _blocked(TRAINING_RESULT_PLANNING_LEAKAGE_BLOCKED, "leakage_guard", "leakage_bundle", "leakage flag true")

    metric_extension_rows = pd.read_csv(settings.metric_extension_result_rows_path, dtype=str)
    metric_computation_summary = pd.read_csv(settings.metric_computation_summary_path, dtype=str)
    training_rows = pd.read_csv(settings.training_evaluation_sample_rows_path, dtype=str)
    metric_evaluation_sample_scope = pd.read_csv(settings.metric_evaluation_sample_scope_path, dtype=str)
    metric_evaluation_denominators = pd.read_csv(settings.metric_evaluation_denominator_rules_path, dtype=str)

    missing_col_status = _required_column_blocker(metric_extension_rows, LINEAGE_COLUMNS, TRAINING_RESULT_PLANNING_LINEAGE_BLOCKED)
    if missing_col_status:
        return missing_col_status
    if "denominator_count" not in metric_extension_rows.columns:
        return _blocked(TRAINING_RESULT_PLANNING_DENOMINATOR_BLOCKED, "metric_evidence", "denominator_count", "denominator count missing")
    for column in ["report_only", "diagnostic_only"]:
        if column not in metric_extension_rows.columns:
            return _blocked(TRAINING_RESULT_PLANNING_REPORT_ONLY_BLOCKED, "metric_evidence", column, "report-only flags missing")
    if "metric_name" not in metric_computation_summary.columns:
        return _blocked(TRAINING_RESULT_PLANNING_METRIC_EVIDENCE_BLOCKED, "metric_evidence", "metric_name", "metric evidence missing")
    if "split_role" not in training_rows.columns:
        return _blocked(TRAINING_RESULT_PLANNING_SAMPLE_SCOPE_BLOCKED, "sample_scope", "split_role", "sample scope missing")
    if not _all_true(metric_extension_rows, "report_only") or not _all_true(metric_extension_rows, "diagnostic_only"):
        return _blocked(TRAINING_RESULT_PLANNING_REPORT_ONLY_BLOCKED, "metric_evidence", "report_only", "report-only flags must be true")
    if not _all_true(metric_evaluation_sample_scope, "report_only") or not _all_true(metric_evaluation_denominators, "report_only"):
        return _blocked(TRAINING_RESULT_PLANNING_REPORT_ONLY_BLOCKED, "sample_scope", "report_only", "sample/denominator report-only flags must be true")
    if _duplicate_unquarantined(training_rows):
        return _blocked(TRAINING_RESULT_PLANNING_SAMPLE_SCOPE_BLOCKED, "sample_scope", "duplicates", "duplicate sample rows without quarantine")

    evidence_index = _metric_evidence(metric_computation_summary, metric_extension_rows)
    evidence_names = {row["metric_name"] for row in evidence_index}
    if not REQUIRED_METRIC_EVIDENCE.issubset(evidence_names):
        return _blocked(TRAINING_RESULT_PLANNING_METRIC_EVIDENCE_BLOCKED, "metric_evidence", "metric_names", "required metric evidence missing")
    if metric_extension_rows["denominator_count"].isna().any() or (metric_extension_rows["denominator_count"].astype(str) == "").any():
        return _blocked(TRAINING_RESULT_PLANNING_DENOMINATOR_BLOCKED, "metric_evidence", "denominator_count", "denominator missing")

    status = TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED if settings.allow_training_result_planning else READY_FOR_TRAINING_RESULT_PLANNING
    return {
        "status": status,
        "gate_results": [
            TrainingResultPlanningGateResult("precondition", "all_required_inputs", status, True, ""),
            TrainingResultPlanningGateResult("approval", "exact_approval", status, True, ""),
            TrainingResultPlanningGateResult("input_lineage", "lineage_complete", status, True, ""),
            TrainingResultPlanningGateResult("metric_evidence", "metric_evidence_complete", status, True, ""),
            TrainingResultPlanningGateResult("leakage_guard", "no_leakage", status, True, ""),
            TrainingResultPlanningGateResult("side_effect_guard", "no_side_effects", status, True, ""),
            TrainingResultPlanningGateResult("overclaim_guard", "no_overclaim", status, True, ""),
        ],
        **metas,
        "metric_evidence_index": evidence_index,
        "metric_evidence_names": sorted(evidence_names),
        "lineage_rows": metric_extension_rows.to_dict("records"),
        "quarantined_planning_input_count": int(pd.to_numeric(training_rows.get("quarantine_count", 0), errors="coerce").fillna(0).sum()),
    }


def _is_no_input(settings: TrainingResultPlanningSettings) -> bool:
    return all(
        getattr(settings, field) is None
        for field in TrainingResultPlanningSettings.__dataclass_fields__
        if field.endswith("_path")
    )


def _blocked(status: str, group: str, name: str, reason: str) -> dict[str, Any]:
    return {
        "status": status,
        "gate_results": [TrainingResultPlanningGateResult(group, name, status, False, reason)],
    }


def _first_missing_required_path(settings: TrainingResultPlanningSettings) -> tuple[str, str] | None:
    groups = [
        ("approval_manifest_path", TRAINING_RESULT_PLANNING_APPROVAL_BLOCKED),
        ("training_result_planning_request_manifest_path", TRAINING_RESULT_PLANNING_APPROVAL_BLOCKED),
        ("metric_extension_metadata_path", TRAINING_RESULT_PLANNING_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_result_rows_path", TRAINING_RESULT_PLANNING_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_summary_path", TRAINING_RESULT_PLANNING_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_safety_flags_path", TRAINING_RESULT_PLANNING_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_status_artifact_path", TRAINING_RESULT_PLANNING_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_health_artifact_path", TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("metric_computation_metadata_path", TRAINING_RESULT_PLANNING_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_result_rows_path", TRAINING_RESULT_PLANNING_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_summary_path", TRAINING_RESULT_PLANNING_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_safety_flags_path", TRAINING_RESULT_PLANNING_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_status_artifact_path", TRAINING_RESULT_PLANNING_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_health_artifact_path", TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("metric_evaluation_metadata_path", TRAINING_RESULT_PLANNING_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_input_index_path", TRAINING_RESULT_PLANNING_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_sample_scope_path", TRAINING_RESULT_PLANNING_SAMPLE_SCOPE_BLOCKED),
        ("metric_evaluation_denominator_rules_path", TRAINING_RESULT_PLANNING_DENOMINATOR_BLOCKED),
        ("metric_evaluation_safety_flags_path", TRAINING_RESULT_PLANNING_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_status_artifact_path", TRAINING_RESULT_PLANNING_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_health_artifact_path", TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("training_evaluation_metadata_path", TRAINING_RESULT_PLANNING_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_sample_rows_path", TRAINING_RESULT_PLANNING_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_safety_flags_path", TRAINING_RESULT_PLANNING_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_status_artifact_path", TRAINING_RESULT_PLANNING_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_health_artifact_path", TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("forward_return_label_metadata_path", TRAINING_RESULT_PLANNING_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_rows_path", TRAINING_RESULT_PLANNING_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_status_artifact_path", TRAINING_RESULT_PLANNING_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_health_artifact_path", TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("replay_decision_freeze_metadata_path", TRAINING_RESULT_PLANNING_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_rows_path", TRAINING_RESULT_PLANNING_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_status_artifact_path", TRAINING_RESULT_PLANNING_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_health_artifact_path", TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("leakage_evidence_bundle_path", TRAINING_RESULT_PLANNING_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", TRAINING_RESULT_PLANNING_OVERCLAIM_BLOCKED),
        ("side_effect_evidence_bundle_path", TRAINING_RESULT_PLANNING_SIDE_EFFECT_BLOCKED),
    ]
    for field, status in groups:
        path = getattr(settings, field)
        if path is None or not Path(path).exists():
            return field, status
    return None


def _metadata_status(metadata: dict[str, Any]) -> str:
    return str(metadata.get("status", metadata.get("execution_status", "")))


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def _status_value(path: Path | None) -> str:
    payload = _load_json(path)
    return str(payload.get("status", payload.get("health_status", "")))


def _any_truthy(payload: dict[str, Any], fields: set[str]) -> bool:
    return any(_truthy(payload.get(field)) for field in fields)


def _unsafe_side_effects(payload: dict[str, Any]) -> bool:
    return any(_truthy(payload.get(field)) for field in DOWNSTREAM_FALSE_FIELDS)


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _all_true(frame: pd.DataFrame, column: str) -> bool:
    if column not in frame.columns:
        return False
    return frame[column].map(_truthy).all()


def _required_column_blocker(
    frame: pd.DataFrame,
    columns: set[str],
    status: str,
) -> dict[str, Any] | None:
    missing = sorted(columns - set(frame.columns))
    if missing:
        return _blocked(status, "input_lineage", missing[0], "required lineage column missing")
    return None


def _duplicate_unquarantined(frame: pd.DataFrame) -> bool:
    keys = ["replay_decision_id", "forward_return_label_id", "symbol", "replay_as_of_date", "split_role"]
    if not set(keys).issubset(frame.columns):
        return True
    duplicates = frame.duplicated(keys, keep=False)
    if not duplicates.any():
        return False
    quarantine = pd.to_numeric(frame.get("quarantine_count", 0), errors="coerce").fillna(0)
    return (quarantine[duplicates] <= 0).any()


def _forbidden_artifact_exists(settings: TrainingResultPlanningSettings) -> bool:
    parents = {
        Path(path).parent
        for field in TrainingResultPlanningSettings.__dataclass_fields__
        if field.endswith("_path")
        for path in [getattr(settings, field)]
        if path is not None
    }
    return any((parent / name).exists() for parent in parents for name in FORBIDDEN_ARTIFACT_NAMES)


def _metric_evidence(metric_summary: pd.DataFrame, extension_rows: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for frame, source in [(metric_summary, "metric_computation"), (extension_rows, "metric_extension")]:
        for record in frame.to_dict("records"):
            name = str(record.get("metric_name", ""))
            if name not in REQUIRED_METRIC_EVIDENCE:
                continue
            rows.append(
                {
                    "metric_name": name,
                    "metric_value": record.get("metric_value", ""),
                    "source_artifact_family": source,
                    "accepted_interpretation": "planning evidence only",
                    "forbidden_interpretation": "not training_result; not strategy performance validation; not profitability proof",
                    "numerator_count": record.get("numerator_count", ""),
                    "denominator_count": record.get("denominator_count", ""),
                    "report_only": True,
                    "diagnostic_only": True,
                }
            )
    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        deduped.setdefault(str(row["metric_name"]), row)
    return list(deduped.values())


def _input_index(result: TrainingResultPlanningResult) -> pd.DataFrame:
    rows = [
        ("metric_extension", result.source_metric_extension_run_id, result.source_metric_extension_status, result.source_metric_extension_health_status),
        ("metric_computation", result.source_metric_computation_run_id, result.source_metric_computation_status, result.source_metric_computation_health_status),
        ("metric_evaluation", result.source_metric_evaluation_planning_run_id, result.source_metric_evaluation_status, result.source_metric_evaluation_health_status),
        ("training_evaluation", result.source_training_evaluation_run_id, result.source_training_evaluation_status, result.source_training_evaluation_health_status),
        ("forward_return_label", result.source_forward_return_label_run_id, result.source_forward_return_label_status, result.source_forward_return_label_health_status),
        ("replay_decision_freeze", result.source_replay_decision_freeze_run_id, result.source_replay_decision_freeze_status, result.source_replay_decision_freeze_health_status),
    ]
    return pd.DataFrame(
        [
            {
                "input_family": family,
                "source_run_id": run_id,
                "source_status": status,
                "source_health_status": health,
                "accepted_for_training_result_planning": True,
                "report_only": True,
                "diagnostic_only": True,
            }
            for family, run_id, status, health in rows
        ]
    )


def _model_scope() -> pd.DataFrame:
    rows = [
        ("planning_metadata", True),
        ("input_index", True),
        ("metric_evidence_index", True),
        ("lineage_matrix", True),
        ("model_scope_plan", True),
        ("limitations", True),
        ("overfit_warnings", True),
        ("health_plan", True),
        ("status_plan", True),
        ("model_weights", False),
        ("model_version", False),
        ("parameter_version", False),
        ("thresholds", False),
        ("predictions", False),
        ("calibrated_probabilities", False),
        ("feature_importance", False),
        ("stock_profile", False),
        ("buy_review", False),
        ("paper_approval", False),
        ("performance_validation", False),
        ("trading", False),
    ]
    return pd.DataFrame(
        [
            {
                "scope_item": item,
                "allowed_in_phase_1": allowed,
                "scope_boundary": "report-only planning" if allowed else "forbidden in phase 1",
            }
            for item, allowed in rows
        ]
    )


def _limitations() -> str:
    return (
        "# Training Result Planning Limitations\n\n"
        "These are report-only planning artifacts, not actual training_result artifacts.\n\n"
        "This phase is not weights, not model_version, not parameter_version, not thresholds, not predictions/probabilities/feature importance, "
        "not stock_profile, not buy-review, not paper approval, not performance validation, and not trading.\n"
    )


def _overfit_warnings() -> list[dict[str, str]]:
    return [
        {"risk_item": item, "required_guard": "document limitation before any future training_result", "report_only": "True"}
        for item in [
            "small sample",
            "class imbalance",
            "duplicate sample rows",
            "non-numeric labels",
            "single-stock overfit",
            "single-industry overfit",
            "single-regime overfit",
            "metric selection bias",
            "multiple comparisons",
            "threshold overfit",
            "benchmark mismatch",
            "industry classification drift",
            "survivorship bias",
            "lookahead leakage",
            "paper-overfit risk",
        ]
    ]


def _health_plan() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"future_gate": "upstream health PASS", "required": True, "fail_condition": "any upstream health is not PASS"},
            {"future_gate": "lineage complete", "required": True, "fail_condition": "source or row lineage missing"},
            {"future_gate": "report-only flags", "required": True, "fail_condition": "report_only/diagnostic_only missing"},
            {"future_gate": "no forbidden downstream fields", "required": True, "fail_condition": "training/model/profile/paper/trading field true"},
            {"future_gate": "no unsafe side effects", "required": True, "fail_condition": "API/broker/order/message/cache/data side effect true"},
            {"future_gate": "no overclaim wording", "required": True, "fail_condition": "performance or trading overclaim"},
        ]
    )


def _status_plan() -> pd.DataFrame:
    fields = [
        "training_result_created",
        "weights_trained",
        "model_version_created",
        "parameter_version_created",
        "thresholds_optimized",
        "predictions_created",
        "calibrated_probabilities_created",
        "feature_importance_created",
        "stock_profile_created",
        "approved_for_paper",
        "strategy_performance_validated",
        "trading_allowed",
    ]
    rows = [{"status_field": field, "expected_value": "False"} for field in fields]
    rows.append({"status_field": "planning_phase", "expected_value": "report-only"})
    return pd.DataFrame(rows)


def _metadata(result: TrainingResultPlanningResult) -> dict[str, Any]:
    payload = {
        "training_result_planning_run_id": result.training_result_planning_run_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "execution_status": result.status,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "ready_for_training_result_planning": result.ready_for_training_result_planning,
        "training_result_planning_executed": result.training_result_planning_executed,
        "training_result_planning_artifacts_created": result.training_result_planning_artifacts_created,
        "metric_evidence_names_present": result.metric_evidence_names_present,
        "metric_evidence_row_count": result.metric_evidence_row_count,
        "planning_input_row_count": result.planning_input_row_count,
        "eligible_planning_input_count": result.eligible_planning_input_count,
        "quarantined_planning_input_count": result.quarantined_planning_input_count,
        "model_scope_rows_created": result.model_scope_rows_created,
        "limitations_created": result.limitations_created,
        "overfit_warnings_created": result.overfit_warnings_created,
        "health_plan_created": result.health_plan_created,
        "status_plan_created": result.status_plan_created,
        "artifact_path": result.artifact_path,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
    }
    for field in [
        "source_metric_extension_run_id",
        "source_metric_extension_status",
        "source_metric_extension_health_status",
        "source_metric_computation_run_id",
        "source_metric_computation_status",
        "source_metric_computation_health_status",
        "source_metric_evaluation_planning_run_id",
        "source_metric_evaluation_status",
        "source_metric_evaluation_health_status",
        "source_training_evaluation_run_id",
        "source_training_evaluation_status",
        "source_training_evaluation_health_status",
        "source_forward_return_label_run_id",
        "source_forward_return_label_status",
        "source_forward_return_label_health_status",
        "source_replay_decision_freeze_run_id",
        "source_replay_decision_freeze_status",
        "source_replay_decision_freeze_health_status",
    ]:
        payload[field] = getattr(result, field)
    return payload | _safety_flags(result)


def _safety_flags(result: TrainingResultPlanningResult) -> dict[str, Any]:
    return {
        "training_result_planning_artifacts_created": result.training_result_planning_artifacts_created,
        **{field: getattr(result, field) for field in DOWNSTREAM_FALSE_FIELDS},
        "parameter_version_created": result.parameter_version_created,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
    }


def _render_report(result: TrainingResultPlanningResult) -> str:
    return (
        "# Training Result Planning Phase 1 Report\n\n"
        f"- training_result_planning_run_id: {result.training_result_planning_run_id}\n"
        f"- status: {result.status}\n"
        f"- workflow_stage: {result.workflow_stage}\n"
        f"- ready_for_training_result_planning: {result.ready_for_training_result_planning}\n"
        f"- training_result_planning_artifacts_created: {result.training_result_planning_artifacts_created}\n"
        f"- metric_evidence_names_present: {result.metric_evidence_names_present}\n"
        f"- metric_evidence_row_count: {result.metric_evidence_row_count}\n\n"
        "This workflow creates report-only planning artifacts only. It is not actual training_result, "
        "not weights, not model_version, not thresholds, not predictions/probabilities/feature importance, "
        "not stock_profile, not buy-review, not paper approval, not performance validation, and not trading.\n"
    )


def _recommended_next_task(result: TrainingResultPlanningResult) -> str:
    if result.status == TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED:
        return "Training Result Planning Artifact Views Report-Only v0.1\n"
    if result.status == READY_FOR_TRAINING_RESULT_PLANNING:
        return "Review ready state and rerun with --allow-training-result-planning only if report-only planning artifacts should be created.\n"
    return "Provide exact approval and complete upstream report-only lineage before training result planning.\n"


def _gate_frame(gates: list[TrainingResultPlanningGateResult], group: str) -> pd.DataFrame:
    rows = [
        {
            "gate_group": gate.gate_group,
            "gate_name": gate.gate_name,
            "status": gate.status,
            "passed": gate.passed,
            "blocker_reason": gate.blocker_reason,
            "evidence_path": gate.evidence_path,
            "observed_value": gate.observed_value,
        }
        for gate in gates
        if gate.gate_group == group
    ]
    return pd.DataFrame(rows, columns=["gate_group", "gate_name", "status", "passed", "blocker_reason", "evidence_path", "observed_value"])


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _next_action(status: str) -> str:
    if status == TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED:
        return "Review report-only training result planning artifacts before adding artifact views."
    if status == READY_FOR_TRAINING_RESULT_PLANNING:
        return "Rerun with explicit allow only if report-only planning artifacts should be created."
    if status == NO_TRAINING_RESULT_PLANNING_INPUT:
        return "Provide exact approval and immutable upstream report-only artifacts."
    return "Resolve blocked training result planning gates before rerun."


def _assert_manual_diagnostics_output(path: Path) -> None:
    normalized = str(path).replace("\\", "/")
    if "/outputs/reports/manual_diagnostics/" not in f"/{normalized}/" and not normalized.startswith("outputs/reports/manual_diagnostics/"):
        raise ValueError("training result planning output must stay under outputs/reports/manual_diagnostics")


def _stable_id(settings: TrainingResultPlanningSettings) -> str:
    payload = {
        field: str(getattr(settings, field))
        for field in TrainingResultPlanningSettings.__dataclass_fields__
        if field not in {"write_artifacts"}
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:12]
