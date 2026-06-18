"""Report-only metric computation phase 1 workflow."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_METRIC_COMPUTATION_INPUT = "NO_METRIC_COMPUTATION_INPUT"
METRIC_COMPUTATION_INPUT_FOUND = "METRIC_COMPUTATION_INPUT_FOUND"
METRIC_COMPUTATION_APPROVAL_BLOCKED = "METRIC_COMPUTATION_APPROVAL_BLOCKED"
METRIC_COMPUTATION_PLANNING_INPUT_BLOCKED = "METRIC_COMPUTATION_PLANNING_INPUT_BLOCKED"
METRIC_COMPUTATION_DATASET_INPUT_BLOCKED = "METRIC_COMPUTATION_DATASET_INPUT_BLOCKED"
METRIC_COMPUTATION_HEALTH_BLOCKED = "METRIC_COMPUTATION_HEALTH_BLOCKED"
METRIC_COMPUTATION_LINEAGE_BLOCKED = "METRIC_COMPUTATION_LINEAGE_BLOCKED"
METRIC_COMPUTATION_SAMPLE_SCOPE_BLOCKED = "METRIC_COMPUTATION_SAMPLE_SCOPE_BLOCKED"
METRIC_COMPUTATION_DENOMINATOR_BLOCKED = "METRIC_COMPUTATION_DENOMINATOR_BLOCKED"
METRIC_COMPUTATION_UNSUPPORTED_METRIC_BLOCKED = "METRIC_COMPUTATION_UNSUPPORTED_METRIC_BLOCKED"
METRIC_COMPUTATION_RESULT_ROW_BLOCKED = "METRIC_COMPUTATION_RESULT_ROW_BLOCKED"
METRIC_COMPUTATION_LEAKAGE_BLOCKED = "METRIC_COMPUTATION_LEAKAGE_BLOCKED"
METRIC_COMPUTATION_SIDE_EFFECT_BLOCKED = "METRIC_COMPUTATION_SIDE_EFFECT_BLOCKED"
METRIC_COMPUTATION_OVERCLAIM_BLOCKED = "METRIC_COMPUTATION_OVERCLAIM_BLOCKED"
READY_FOR_METRIC_COMPUTATION = "READY_FOR_METRIC_COMPUTATION"
METRIC_COMPUTATION_REPORT_CREATED = "METRIC_COMPUTATION_REPORT_CREATED"

EXACT_METRIC_COMPUTATION_APPROVAL_TEXT = (
    "I explicitly authorize implementation of metric computation core phase 1 only, "
    "report-only metric computation. It may create report-only computed metric artifacts "
    "and result rows from immutable METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED and "
    "TRAINING_EVALUATION_DATASET_CREATED artifacts. The first metric set is limited to "
    "sample_count, label_coverage, average_return, median_return, and hit_rate. It must "
    "not create training_result, train weights, create model_version, optimize thresholds, "
    "create predictions, create calibrated probabilities, create feature importance, create "
    "stock_profile, generate buy-review eligibility, apply paper approval, claim strategy "
    "performance validation, integrate broker/order/message, or trade."
)

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/metric_computation_v0_1")

ALLOWED_METRIC_SET = ["sample_count", "label_coverage", "average_return", "median_return", "hit_rate"]
ADVANCED_METRIC_SET = {
    "benchmark_relative_return",
    "industry_relative_return",
    "max_drawdown",
    "information_coefficient",
    "rank_information_coefficient",
    "sharpe_like_metric",
    "turnover",
    "slippage_sensitivity",
    "regime_robustness",
    "false_positive_cost",
    "false_negative_opportunity_cost",
    "prediction",
    "calibrated_probability",
}

ARTIFACT_FILES = {
    "metadata": "metric_computation_metadata.json",
    "report": "metric_computation_report.md",
    "input_index": "metric_computation_input_index.csv",
    "metric_definitions_used": "metric_computation_metric_definitions_used.csv",
    "sample_scope_used": "metric_computation_sample_scope_used.csv",
    "denominator_rules_used": "metric_computation_denominator_rules_used.csv",
    "result_rows": "metric_computation_result_rows.csv",
    "summary": "metric_computation_summary.csv",
    "safety_flags": "metric_computation_safety_flags.json",
    "precondition_results": "metric_computation_precondition_results.csv",
    "approval_results": "metric_computation_approval_results.csv",
    "input_lineage_results": "metric_computation_input_lineage_results.csv",
    "dataset_input_results": "metric_computation_dataset_input_results.csv",
    "metric_definition_results": "metric_computation_metric_definition_results.csv",
    "denominator_results": "metric_computation_denominator_results.csv",
    "result_row_results": "metric_computation_result_row_results.csv",
    "leakage_guard_results": "metric_computation_leakage_guard_results.csv",
    "side_effect_guard_results": "metric_computation_side_effect_guard_results.csv",
    "overclaim_guard_results": "metric_computation_overclaim_guard_results.csv",
    "recommended_next_task": "recommended_next_task.md",
}

FORBIDDEN_FALSE_FIELDS = [
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
    "training_result_requested",
    "weights_requested",
    "model_version_requested",
    "thresholds_requested",
    "predictions_requested",
    "calibrated_probabilities_requested",
    "feature_importance_requested",
    "stock_profile_requested",
    "buy_review_requested",
    "paper_approval_requested",
    "performance_validation_requested",
}
SIDE_EFFECT_REQUEST_FIELDS = {"trading_requested"}
SIDE_EFFECT_TRUE_FIELDS = {
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
}
REQUIRED_OVERCLAIM_TRUE = {
    "metric_computation_not_strategy_validation",
    "metric_computation_not_training_result",
    "metric_computation_not_weights",
    "metric_computation_not_model_version",
    "metric_computation_not_thresholds",
    "metric_computation_not_predictions",
    "metric_computation_not_probabilities",
    "metric_computation_not_feature_importance",
    "metric_computation_not_stock_profile",
    "metric_computation_not_buy_review",
    "metric_computation_not_paper_approval",
    "metric_computation_not_performance_validation",
    "metric_computation_not_trading",
}
SAMPLE_REQUIRED_COLUMNS = {
    "training_evaluation_sample_id",
    "training_evaluation_run_id",
    "replay_decision_id",
    "forward_return_label_id",
    "replay_decision_freeze_run_id",
    "forward_return_label_run_id",
    "replay_as_of_date",
    "symbol",
    "split_role",
    "label_name",
    "label_value",
    "horizon_trading_days",
    "source_hash_coverage",
    "revision_id_coverage",
    "available_time_coverage",
    "quality_status_coverage",
}
LINEAGE_COLUMNS = {
    "forward_return_label_id",
    "forward_return_label_run_id",
    "replay_decision_freeze_run_id",
    "source_hash_coverage",
    "revision_id_coverage",
    "available_time_coverage",
    "quality_status_coverage",
}


@dataclass(frozen=True)
class MetricComputationSettings:
    approval_manifest_path: Path | None = None
    metric_computation_request_manifest_path: Path | None = None
    metric_evaluation_metadata_path: Path | None = None
    metric_evaluation_input_index_path: Path | None = None
    metric_evaluation_metric_definitions_path: Path | None = None
    metric_evaluation_sample_scope_path: Path | None = None
    metric_evaluation_denominator_rules_path: Path | None = None
    metric_evaluation_safety_flags_path: Path | None = None
    metric_evaluation_status_artifact_path: Path | None = None
    metric_evaluation_health_artifact_path: Path | None = None
    training_evaluation_metadata_path: Path | None = None
    training_evaluation_sample_rows_path: Path | None = None
    training_evaluation_label_coverage_report_path: Path | None = None
    training_evaluation_safety_flags_path: Path | None = None
    training_evaluation_status_artifact_path: Path | None = None
    training_evaluation_health_artifact_path: Path | None = None
    leakage_evidence_bundle_path: Path | None = None
    overclaim_evidence_bundle_path: Path | None = None
    side_effect_evidence_bundle_path: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    allow_metric_computation: bool = False
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class MetricComputationGateResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str = ""
    observed_value: str = ""


MetricComputationApprovalResult = MetricComputationGateResult
MetricComputationInputLineageResult = MetricComputationGateResult
MetricComputationDatasetInputResult = MetricComputationGateResult
MetricComputationMetricDefinitionResult = MetricComputationGateResult
MetricComputationDenominatorResult = MetricComputationGateResult
MetricComputationResultRowResult = MetricComputationGateResult
MetricComputationLeakageGuardResult = MetricComputationGateResult
MetricComputationSideEffectGuardResult = MetricComputationGateResult
MetricComputationOverclaimGuardResult = MetricComputationGateResult


@dataclass(frozen=True)
class MetricComputationResult:
    metric_computation_run_id: str
    status: str
    workflow_stage: str
    ready_for_metric_computation: bool
    metric_computation_executed: bool
    metric_computation_report_created: bool
    metric_result_rows_created: bool
    metric_summary_created: bool
    metrics_computed: bool
    artifact_path: str
    allowed_metric_set: str
    requested_metric_set: str = ""
    unsupported_metrics_requested: bool = False
    source_metric_evaluation_planning_run_id: str = ""
    source_metric_evaluation_artifact_path: str = ""
    source_metric_evaluation_status: str = ""
    source_metric_evaluation_health_status: str = ""
    source_training_evaluation_run_id: str = ""
    source_training_evaluation_artifact_path: str = ""
    source_training_evaluation_status: str = ""
    source_training_evaluation_health_status: str = ""
    source_forward_return_label_run_id: str = ""
    source_replay_decision_freeze_run_id: str = ""
    sample_row_count: int = 0
    eligible_sample_count: int = 0
    quarantined_sample_count: int = 0
    label_coverage_numerator: int = 0
    label_coverage_denominator: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    next_action: str = ""
    report_only: bool = True
    diagnostic_only: bool = True
    artifact_paths: dict[str, Path] = field(default_factory=dict)
    gate_results: list[MetricComputationGateResult] = field(default_factory=list)
    safety_statement: str = (
        "Metric computation is report-only: not strategy validation, not training_result, "
        "not weights, not model_version, not thresholds, not predictions, not calibrated probabilities, "
        "not feature importance, not stock_profile, not buy-review, not paper approval, not performance "
        "validation, and not trading."
    )
    evaluation_execution_completed: bool = False
    training_allowed: bool = False
    weights_trained: bool = False
    training_result_created: bool = False
    model_version_created: bool = False
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


def run_metric_computation(settings: MetricComputationSettings | None = None) -> MetricComputationResult:
    settings = settings or MetricComputationSettings()
    output_root = Path(settings.output_dir)
    _assert_manual_diagnostics_output(output_root)
    run_id = _stable_id(settings)
    artifact_dir = output_root / run_id
    artifact_paths = {"artifact_dir": artifact_dir} | {key: artifact_dir / filename for key, filename in ARTIFACT_FILES.items()}
    state = _evaluate(settings)
    state["metric_metadata_path"] = settings.metric_evaluation_metadata_path
    state["training_metadata_path"] = settings.training_evaluation_metadata_path
    state["sample_rows_path"] = settings.training_evaluation_sample_rows_path
    result_rows = _metric_result_rows(run_id, state) if state["status"] == METRIC_COMPUTATION_REPORT_CREATED else _empty_artifact_frame("result_rows")
    summary_rows = _summary_rows(result_rows) if state["status"] == METRIC_COMPUTATION_REPORT_CREATED else _empty_artifact_frame("summary")
    ready = state["status"] in {READY_FOR_METRIC_COMPUTATION, METRIC_COMPUTATION_REPORT_CREATED}
    computed = state["status"] == METRIC_COMPUTATION_REPORT_CREATED
    metric_metadata = state["metric_metadata"]
    training_metadata = state["training_metadata"]
    result = MetricComputationResult(
        metric_computation_run_id=run_id,
        status=state["status"],
        workflow_stage="METRIC_COMPUTATION_NO_INPUT" if state["status"] == NO_METRIC_COMPUTATION_INPUT else state["status"],
        ready_for_metric_computation=ready,
        metric_computation_executed=computed,
        metric_computation_report_created=computed,
        metric_result_rows_created=computed,
        metric_summary_created=computed,
        metrics_computed=computed,
        artifact_path=str(artifact_dir),
        allowed_metric_set=",".join(ALLOWED_METRIC_SET),
        requested_metric_set=",".join(state["requested_metric_set"]),
        unsupported_metrics_requested=state["unsupported_metrics_requested"],
        source_metric_evaluation_planning_run_id=str(metric_metadata.get("metric_evaluation_run_id", "")),
        source_metric_evaluation_artifact_path=str(Path(settings.metric_evaluation_metadata_path).parent if settings.metric_evaluation_metadata_path else ""),
        source_metric_evaluation_status=str(metric_metadata.get("status", metric_metadata.get("execution_status", ""))),
        source_metric_evaluation_health_status=_status_value(settings.metric_evaluation_health_artifact_path),
        source_training_evaluation_run_id=str(training_metadata.get("training_evaluation_run_id", "")),
        source_training_evaluation_artifact_path=str(Path(settings.training_evaluation_metadata_path).parent if settings.training_evaluation_metadata_path else ""),
        source_training_evaluation_status=str(training_metadata.get("status", training_metadata.get("execution_status", ""))),
        source_training_evaluation_health_status=_status_value(settings.training_evaluation_health_artifact_path),
        source_forward_return_label_run_id=str(training_metadata.get("source_forward_return_label_run_id", "")),
        source_replay_decision_freeze_run_id=str(training_metadata.get("source_replay_decision_freeze_run_id", "")),
        sample_row_count=state["sample_row_count"],
        eligible_sample_count=state["eligible_sample_count"],
        quarantined_sample_count=state["quarantined_sample_count"],
        label_coverage_numerator=state["eligible_sample_count"],
        label_coverage_denominator=state["sample_row_count"] - state["quarantined_sample_count"],
        blocker_count=0 if ready else 1 if state["status"] != NO_METRIC_COMPUTATION_INPUT else 0,
        warning_count=state["quarantined_sample_count"],
        next_action=_next_action(state["status"]),
        artifact_paths=artifact_paths,
        gate_results=state["gate_results"],
    )
    state["result_rows"] = result_rows
    state["summary_rows"] = summary_rows
    if settings.write_artifacts:
        write_metric_computation_artifacts(result, state)
    return result


def write_metric_computation_artifacts(result: MetricComputationResult, state: dict[str, Any] | None = None) -> None:
    state = state or {}
    artifact_dir = result.artifact_paths["artifact_dir"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    result.artifact_paths["metadata"].write_text(json.dumps(_metadata(result), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["safety_flags"].write_text(json.dumps(_safety_flags(result), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(_recommended_next_task(result), encoding="utf-8")

    frames = {
        "input_index": _input_index_rows(result, state),
        "metric_definitions_used": state.get("metric_definitions", _empty_artifact_frame("metric_definitions_used")),
        "sample_scope_used": state.get("sample_scope", _empty_artifact_frame("sample_scope_used")),
        "denominator_rules_used": state.get("denominator_rules", _empty_artifact_frame("denominator_rules_used")),
        "result_rows": state.get("result_rows", _empty_artifact_frame("result_rows")),
        "summary": state.get("summary_rows", _empty_artifact_frame("summary")),
        "precondition_results": _gate_frame(state.get("gate_results", []), "precondition"),
        "approval_results": _gate_frame(state.get("gate_results", []), "approval"),
        "input_lineage_results": _gate_frame(state.get("gate_results", []), "input_lineage"),
        "dataset_input_results": _gate_frame(state.get("gate_results", []), "dataset_input"),
        "metric_definition_results": _gate_frame(state.get("gate_results", []), "metric_definition"),
        "denominator_results": _gate_frame(state.get("gate_results", []), "denominator"),
        "result_row_results": _gate_frame(state.get("gate_results", []), "result_row"),
        "leakage_guard_results": _gate_frame(state.get("gate_results", []), "leakage_guard"),
        "side_effect_guard_results": _gate_frame(state.get("gate_results", []), "side_effect_guard"),
        "overclaim_guard_results": _gate_frame(state.get("gate_results", []), "overclaim_guard"),
    }
    for key, frame in frames.items():
        _write_csv(result.artifact_paths[key], frame)


def _evaluate(settings: MetricComputationSettings) -> dict[str, Any]:
    state: dict[str, Any] = {
        "status": NO_METRIC_COMPUTATION_INPUT,
        "gate_results": [],
        "metric_metadata": {},
        "training_metadata": {},
        "sample_rows": pd.DataFrame(),
        "eligible_rows": pd.DataFrame(),
        "quarantined_rows": pd.DataFrame(),
        "metric_definitions": pd.DataFrame(),
        "sample_scope": pd.DataFrame(),
        "denominator_rules": pd.DataFrame(),
        "requested_metric_set": list(ALLOWED_METRIC_SET),
        "unsupported_metrics_requested": False,
        "sample_row_count": 0,
        "eligible_sample_count": 0,
        "quarantined_sample_count": 0,
    }
    if not _has_any_input(settings):
        state["gate_results"].append(_gate("precondition", "input_presence", NO_METRIC_COMPUTATION_INPUT, True, "no metric computation input supplied"))
        return state

    approval = _read_json(settings.approval_manifest_path)
    if str(approval.get("approval_text", "")).strip() != EXACT_METRIC_COMPUTATION_APPROVAL_TEXT:
        return _blocked(state, METRIC_COMPUTATION_APPROVAL_BLOCKED, "approval", "exact_approval_text", "exact metric computation approval text is required", settings.approval_manifest_path)
    state["gate_results"].append(_gate("approval", "exact_approval_text", METRIC_COMPUTATION_INPUT_FOUND, True, "", settings.approval_manifest_path))

    request = _read_json(settings.metric_computation_request_manifest_path)
    requested = [str(metric) for metric in request.get("requested_metric_set", ALLOWED_METRIC_SET)]
    state["requested_metric_set"] = requested
    unsupported = sorted(set(requested) - set(ALLOWED_METRIC_SET) | (set(requested) & ADVANCED_METRIC_SET))
    if unsupported:
        state["unsupported_metrics_requested"] = True
        return _blocked(state, METRIC_COMPUTATION_UNSUPPORTED_METRIC_BLOCKED, "metric_definition", "allowed_metric_set", f"unsupported metrics requested: {', '.join(unsupported)}", settings.metric_computation_request_manifest_path)
    if any(bool(request.get(field, False)) for field in OVERCLAIM_REQUEST_FIELDS):
        return _blocked(state, METRIC_COMPUTATION_OVERCLAIM_BLOCKED, "overclaim_guard", "request_scope", "request asks for downstream training/model/profile/performance scope", settings.metric_computation_request_manifest_path)
    if any(bool(request.get(field, False)) for field in SIDE_EFFECT_REQUEST_FIELDS):
        return _blocked(state, METRIC_COMPUTATION_SIDE_EFFECT_BLOCKED, "side_effect_guard", "request_scope", "request asks for trading or side effects", settings.metric_computation_request_manifest_path)

    missing_planning = _missing_paths(
        [
            settings.metric_evaluation_metadata_path,
            settings.metric_evaluation_input_index_path,
            settings.metric_evaluation_metric_definitions_path,
            settings.metric_evaluation_safety_flags_path,
            settings.metric_evaluation_status_artifact_path,
        ]
    )
    if missing_planning:
        return _blocked(state, METRIC_COMPUTATION_PLANNING_INPUT_BLOCKED, "precondition", "metric_evaluation_artifacts", f"missing metric evaluation artifacts: {missing_planning}", None)
    if not _path_exists(settings.metric_evaluation_sample_scope_path):
        return _blocked(state, METRIC_COMPUTATION_SAMPLE_SCOPE_BLOCKED, "precondition", "sample_scope_artifact", "missing metric evaluation sample scope", settings.metric_evaluation_sample_scope_path)
    if not _path_exists(settings.metric_evaluation_denominator_rules_path):
        return _blocked(state, METRIC_COMPUTATION_DENOMINATOR_BLOCKED, "precondition", "denominator_rules_artifact", "missing metric evaluation denominator rules", settings.metric_evaluation_denominator_rules_path)
    if not _path_exists(settings.metric_evaluation_health_artifact_path):
        return _blocked(state, METRIC_COMPUTATION_HEALTH_BLOCKED, "precondition", "metric_evaluation_health_artifact", "missing metric evaluation health artifact", settings.metric_evaluation_health_artifact_path)

    metric_metadata = _read_json(settings.metric_evaluation_metadata_path)
    metric_health = _status_value(settings.metric_evaluation_health_artifact_path)
    metric_status_values = [
        str(metric_metadata.get(field, ""))
        for field in ["status", "execution_status", "workflow_stage"]
        if str(metric_metadata.get(field, "")) != ""
    ]
    if (
        any(value != "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED" for value in metric_status_values)
        or metric_metadata.get("metric_evaluation_planning_artifacts_created") is False
    ):
        return _blocked(state, METRIC_COMPUTATION_PLANNING_INPUT_BLOCKED, "precondition", "metric_evaluation_status", "metric evaluation planning artifacts are not created", settings.metric_evaluation_metadata_path)
    if metric_health != "PASS":
        return _blocked(state, METRIC_COMPUTATION_HEALTH_BLOCKED, "precondition", "metric_evaluation_health", "metric evaluation health is not PASS", settings.metric_evaluation_health_artifact_path)
    state["metric_metadata"] = metric_metadata
    state["metric_definitions"] = _read_csv(settings.metric_evaluation_metric_definitions_path)
    state["sample_scope"] = _read_csv(settings.metric_evaluation_sample_scope_path)
    state["denominator_rules"] = _read_csv(settings.metric_evaluation_denominator_rules_path)
    state["gate_results"].append(_gate("precondition", "metric_evaluation_inputs", METRIC_COMPUTATION_INPUT_FOUND, True, "", settings.metric_evaluation_metadata_path))

    missing_dataset = _missing_paths(
        [
            settings.training_evaluation_metadata_path,
            settings.training_evaluation_sample_rows_path,
            settings.training_evaluation_label_coverage_report_path,
            settings.training_evaluation_safety_flags_path,
            settings.training_evaluation_status_artifact_path,
        ]
    )
    if missing_dataset:
        return _blocked(state, METRIC_COMPUTATION_DATASET_INPUT_BLOCKED, "dataset_input", "training_evaluation_artifacts", f"missing training evaluation artifacts: {missing_dataset}", None)
    if not _path_exists(settings.training_evaluation_health_artifact_path):
        return _blocked(state, METRIC_COMPUTATION_HEALTH_BLOCKED, "dataset_input", "training_evaluation_health_artifact", "missing training evaluation health artifact", settings.training_evaluation_health_artifact_path)

    training_metadata = _read_json(settings.training_evaluation_metadata_path)
    training_health = _status_value(settings.training_evaluation_health_artifact_path)
    training_status = _status_value(settings.training_evaluation_status_artifact_path) or str(training_metadata.get("execution_status", training_metadata.get("status", "")))
    training_status_values = [
        str(training_metadata.get(field, ""))
        for field in ["status", "execution_status", "workflow_stage"]
        if str(training_metadata.get(field, "")) != ""
    ]
    if (
        training_status != "TRAINING_EVALUATION_DATASET_CREATED"
        or any(value != "TRAINING_EVALUATION_DATASET_CREATED" for value in training_status_values)
        or training_metadata.get("training_evaluation_dataset_artifacts_created") is False
    ):
        return _blocked(state, METRIC_COMPUTATION_DATASET_INPUT_BLOCKED, "dataset_input", "training_evaluation_status", "training evaluation dataset is not created", settings.training_evaluation_status_artifact_path)
    if training_health != "PASS":
        return _blocked(state, METRIC_COMPUTATION_HEALTH_BLOCKED, "dataset_input", "training_evaluation_health", "training evaluation health is not PASS", settings.training_evaluation_health_artifact_path)
    if not training_metadata.get("source_forward_return_label_run_id") or not training_metadata.get("source_replay_decision_freeze_run_id"):
        return _blocked(state, METRIC_COMPUTATION_LINEAGE_BLOCKED, "input_lineage", "training_lineage", "missing replay decision or forward label lineage", settings.training_evaluation_metadata_path)
    state["training_metadata"] = training_metadata

    sample_rows = _read_csv(settings.training_evaluation_sample_rows_path)
    state["sample_rows"] = sample_rows
    state["sample_row_count"] = len(sample_rows)
    sample_missing_set = SAMPLE_REQUIRED_COLUMNS - set(sample_rows.columns)
    sample_missing = sorted(sample_missing_set)
    if sample_missing_set & LINEAGE_COLUMNS:
        return _blocked(state, METRIC_COMPUTATION_LINEAGE_BLOCKED, "input_lineage", "sample_lineage_columns", f"missing lineage columns: {', '.join(sample_missing)}", settings.training_evaluation_sample_rows_path)
    if sample_missing:
        return _blocked(state, METRIC_COMPUTATION_SAMPLE_SCOPE_BLOCKED, "dataset_input", "sample_required_columns", f"missing sample columns: {', '.join(sample_missing)}", settings.training_evaluation_sample_rows_path)
    if sample_rows.duplicated(subset=["training_evaluation_sample_id"]).any() or sample_rows.duplicated(subset=["replay_decision_id", "forward_return_label_id"]).any():
        return _blocked(state, METRIC_COMPUTATION_SAMPLE_SCOPE_BLOCKED, "dataset_input", "sample_identity_uniqueness", "duplicate sample identity rows must be quarantined before computation", settings.training_evaluation_sample_rows_path)

    numeric = pd.to_numeric(sample_rows["label_value"], errors="coerce")
    eligible_rows = sample_rows[numeric.notna()].copy()
    eligible_rows["metric_label_value"] = numeric[numeric.notna()].astype(float)
    quarantined_rows = sample_rows[numeric.isna()].copy()
    state["eligible_rows"] = eligible_rows
    state["quarantined_rows"] = quarantined_rows
    state["eligible_sample_count"] = len(eligible_rows)
    state["quarantined_sample_count"] = len(quarantined_rows)
    if eligible_rows.empty:
        return _blocked(state, METRIC_COMPUTATION_RESULT_ROW_BLOCKED, "result_row", "eligible_numeric_labels", "no numeric label rows available for report-only computation", settings.training_evaluation_sample_rows_path)

    leakage = _read_json(settings.leakage_evidence_bundle_path)
    if not _path_exists(settings.leakage_evidence_bundle_path) or any(bool(v) for v in leakage.values() if isinstance(v, bool)):
        return _blocked(state, METRIC_COMPUTATION_LEAKAGE_BLOCKED, "leakage_guard", "future_leakage", "leakage evidence bundle is missing or unsafe", settings.leakage_evidence_bundle_path)
    side_effect = _read_json(settings.side_effect_evidence_bundle_path)
    if not _path_exists(settings.side_effect_evidence_bundle_path) or any(bool(side_effect.get(field, False)) for field in SIDE_EFFECT_TRUE_FIELDS):
        return _blocked(state, METRIC_COMPUTATION_SIDE_EFFECT_BLOCKED, "side_effect_guard", "side_effect_flags", "side-effect evidence bundle is missing or unsafe", settings.side_effect_evidence_bundle_path)
    overclaim = _read_json(settings.overclaim_evidence_bundle_path)
    if not _path_exists(settings.overclaim_evidence_bundle_path) or any(not bool(overclaim.get(field, False)) for field in REQUIRED_OVERCLAIM_TRUE):
        return _blocked(state, METRIC_COMPUTATION_OVERCLAIM_BLOCKED, "overclaim_guard", "overclaim_flags", "overclaim evidence bundle is missing or unsafe", settings.overclaim_evidence_bundle_path)
    state["gate_results"].extend(
        [
            _gate("input_lineage", "immutable_lineage", METRIC_COMPUTATION_INPUT_FOUND, True, "", settings.training_evaluation_metadata_path),
            _gate("dataset_input", "training_dataset_created", METRIC_COMPUTATION_INPUT_FOUND, True, "", settings.training_evaluation_sample_rows_path),
            _gate("metric_definition", "allowed_metric_set", METRIC_COMPUTATION_INPUT_FOUND, True, "", settings.metric_evaluation_metric_definitions_path),
            _gate("denominator", "denominator_rules", METRIC_COMPUTATION_INPUT_FOUND, True, "", settings.metric_evaluation_denominator_rules_path),
            _gate("result_row", "eligible_numeric_labels", METRIC_COMPUTATION_INPUT_FOUND, True, "", settings.training_evaluation_sample_rows_path),
            _gate("leakage_guard", "future_leakage", METRIC_COMPUTATION_INPUT_FOUND, True, "", settings.leakage_evidence_bundle_path),
            _gate("side_effect_guard", "side_effect_flags", METRIC_COMPUTATION_INPUT_FOUND, True, "", settings.side_effect_evidence_bundle_path),
            _gate("overclaim_guard", "overclaim_flags", METRIC_COMPUTATION_INPUT_FOUND, True, "", settings.overclaim_evidence_bundle_path),
        ]
    )
    state["status"] = METRIC_COMPUTATION_REPORT_CREATED if settings.allow_metric_computation else READY_FOR_METRIC_COMPUTATION
    return state


def _metric_result_rows(run_id: str, state: dict[str, Any]) -> pd.DataFrame:
    rows = state["eligible_rows"]
    values = rows["metric_label_value"].astype(float)
    numerator = len(rows)
    denominator = max(state["sample_row_count"] - state["quarantined_sample_count"], 0)
    base = {
        "metric_computation_run_id": run_id,
        "source_metric_evaluation_planning_run_id": str(state["metric_metadata"].get("metric_evaluation_run_id", "")),
        "source_training_evaluation_run_id": str(state["training_metadata"].get("training_evaluation_run_id", "")),
        "split_role": str(rows["split_role"].iloc[0]) if "split_role" in rows else "",
        "label_name": str(rows["label_name"].iloc[0]) if "label_name" in rows else "",
        "horizon_trading_days": int(rows["horizon_trading_days"].iloc[0]) if "horizon_trading_days" in rows else 0,
        "threshold_used": 0.0,
        "report_only": True,
        "diagnostic_only": True,
    }
    metric_values = {
        "sample_count": float(numerator),
        "label_coverage": float(numerator / denominator) if denominator else 0.0,
        "average_return": float(values.mean()),
        "median_return": float(values.median()),
        "hit_rate": float((values > 0).sum() / numerator) if numerator else 0.0,
    }
    return pd.DataFrame([{**base, "metric_name": metric, "metric_value": metric_values[metric], "numerator": numerator, "denominator": denominator} for metric in ALLOWED_METRIC_SET])


def _summary_rows(result_rows: pd.DataFrame) -> pd.DataFrame:
    if result_rows.empty:
        return _empty_artifact_frame("summary")
    return result_rows[
        [
            "metric_computation_run_id",
            "metric_name",
            "metric_value",
            "numerator",
            "denominator",
            "source_metric_evaluation_planning_run_id",
            "source_training_evaluation_run_id",
            "report_only",
            "diagnostic_only",
        ]
    ].copy()


def _metadata(result: MetricComputationResult) -> dict[str, Any]:
    return {
        "metric_computation_run_id": result.metric_computation_run_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "execution_status": result.status,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "ready_for_metric_computation": result.ready_for_metric_computation,
        "metric_computation_executed": result.metric_computation_executed,
        "metric_computation_report_created": result.metric_computation_report_created,
        "metric_result_rows_created": result.metric_result_rows_created,
        "metric_summary_created": result.metric_summary_created,
        "metrics_computed": result.metrics_computed,
        "allowed_metric_set": result.allowed_metric_set,
        "requested_metric_set": result.requested_metric_set,
        "unsupported_metrics_requested": result.unsupported_metrics_requested,
        "source_metric_evaluation_planning_run_id": result.source_metric_evaluation_planning_run_id,
        "source_metric_evaluation_artifact_path": result.source_metric_evaluation_artifact_path,
        "source_metric_evaluation_status": result.source_metric_evaluation_status,
        "source_metric_evaluation_health_status": result.source_metric_evaluation_health_status,
        "source_training_evaluation_run_id": result.source_training_evaluation_run_id,
        "source_training_evaluation_artifact_path": result.source_training_evaluation_artifact_path,
        "source_training_evaluation_status": result.source_training_evaluation_status,
        "source_training_evaluation_health_status": result.source_training_evaluation_health_status,
        "source_forward_return_label_run_id": result.source_forward_return_label_run_id,
        "source_replay_decision_freeze_run_id": result.source_replay_decision_freeze_run_id,
        "sample_row_count": result.sample_row_count,
        "eligible_sample_count": result.eligible_sample_count,
        "quarantined_sample_count": result.quarantined_sample_count,
        "label_coverage_numerator": result.label_coverage_numerator,
        "label_coverage_denominator": result.label_coverage_denominator,
        "artifact_path": result.artifact_path,
        "report_only": True,
        "diagnostic_only": True,
    } | {field: False for field in FORBIDDEN_FALSE_FIELDS}


def _safety_flags(result: MetricComputationResult) -> dict[str, bool]:
    return {
        "metric_computation_executed": result.metric_computation_executed,
        "metric_computation_report_created": result.metric_computation_report_created,
        "metric_result_rows_created": result.metric_result_rows_created,
        "metric_summary_created": result.metric_summary_created,
        "metrics_computed": result.metrics_computed,
        "report_only": True,
        "diagnostic_only": True,
    } | {field: False for field in FORBIDDEN_FALSE_FIELDS}


def _render_report(result: MetricComputationResult) -> str:
    return (
        "# Metric Computation Core Phase 1 Report\n\n"
        f"- metric_computation_run_id: {result.metric_computation_run_id}\n"
        f"- status: {result.status}\n"
        f"- workflow_stage: {result.workflow_stage}\n"
        f"- ready_for_metric_computation: {result.ready_for_metric_computation}\n"
        f"- metrics_computed: {result.metrics_computed}\n"
        f"- metric_result_rows_created: {result.metric_result_rows_created}\n"
        f"- sample_row_count: {result.sample_row_count}\n"
        f"- eligible_sample_count: {result.eligible_sample_count}\n"
        f"- quarantined_sample_count: {result.quarantined_sample_count}\n\n"
        "This workflow creates report-only historical metrics when explicitly allowed. "
        "It is not strategy validation, not training_result, not weights, not model_version, "
        "not thresholds, not predictions, not calibrated probabilities, not feature importance, "
        "not stock_profile, not buy-review, not paper approval, not performance validation, and not trading.\n"
    )


def _recommended_next_task(result: MetricComputationResult) -> str:
    if result.status == METRIC_COMPUTATION_REPORT_CREATED:
        return "Next task: Metric Computation Artifact Views Report-Only v0.1.\n"
    if result.status == READY_FOR_METRIC_COMPUTATION:
        return "Next task: rerun metric-computation with exact --allow-metric-computation only after reviewing all gates.\n"
    return "Next task: resolve metric computation blockers before creating report-only computed metric rows.\n"


def _next_action(status: str) -> str:
    if status == NO_METRIC_COMPUTATION_INPUT:
        return "Provide exact approval plus immutable metric evaluation planning and training evaluation dataset artifacts."
    if status == READY_FOR_METRIC_COMPUTATION:
        return "Review all gates; optionally rerun with explicit report-only metric computation allowance."
    if status == METRIC_COMPUTATION_REPORT_CREATED:
        return "Review report-only historical metrics; do not treat them as strategy validation."
    return "Resolve the blocking gate before computing report-only metrics."


def _input_index_rows(result: MetricComputationResult, state: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "metric_computation_run_id": result.metric_computation_run_id,
                "input_component": component,
                "artifact_path": str(path or ""),
                "source_run_id": source_run_id,
                "required": True,
                "report_only": True,
                "diagnostic_only": True,
            }
            for component, path, source_run_id in [
                ("metric_evaluation_metadata", state.get("metric_metadata_path"), result.source_metric_evaluation_planning_run_id),
                ("training_evaluation_metadata", state.get("training_metadata_path"), result.source_training_evaluation_run_id),
                ("training_evaluation_sample_rows", state.get("sample_rows_path"), result.source_training_evaluation_run_id),
            ]
        ]
    )


def _gate_frame(gates: list[MetricComputationGateResult], gate_group: str) -> pd.DataFrame:
    rows = [gate.__dict__ for gate in gates if gate.gate_group == gate_group]
    if not rows:
        return _empty_gate_frame(gate_group)
    return pd.DataFrame(rows)


def _empty_gate_frame(gate_group: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "gate_group": gate_group,
                "gate_name": "not_applicable",
                "status": "NOT_EVALUATED",
                "passed": True,
                "blocker_reason": "",
                "evidence_path": "",
                "observed_value": "",
            }
        ]
    )


def _empty_artifact_frame(key: str) -> pd.DataFrame:
    columns = {
        "metric_definitions_used": [
            "metric_computation_run_id",
            "metric_name",
            "definition_plain_language",
            "source_metric_evaluation_planning_run_id",
            "report_only",
            "diagnostic_only",
        ],
        "sample_scope_used": [
            "metric_computation_run_id",
            "scope_item",
            "denominator_rule",
            "quarantine_rule",
            "report_only",
            "diagnostic_only",
        ],
        "denominator_rules_used": [
            "metric_computation_run_id",
            "metric_name",
            "denominator_scope",
            "include_condition",
            "exclude_condition",
            "report_only",
            "diagnostic_only",
        ],
        "result_rows": [
            "metric_computation_run_id",
            "metric_name",
            "metric_value",
            "numerator",
            "denominator",
            "threshold_used",
            "source_metric_evaluation_planning_run_id",
            "source_training_evaluation_run_id",
            "split_role",
            "label_name",
            "horizon_trading_days",
            "report_only",
            "diagnostic_only",
        ],
        "summary": [
            "metric_computation_run_id",
            "metric_name",
            "metric_value",
            "numerator",
            "denominator",
            "source_metric_evaluation_planning_run_id",
            "source_training_evaluation_run_id",
            "report_only",
            "diagnostic_only",
        ],
    }
    return pd.DataFrame(columns=columns.get(key, ["metric_computation_run_id", "report_only", "diagnostic_only"]))


def _blocked(state: dict[str, Any], status: str, group: str, gate_name: str, reason: str, path: Path | None) -> dict[str, Any]:
    state["status"] = status
    state["gate_results"].append(_gate(group, gate_name, status, False, reason, path))
    return state


def _gate(gate_group: str, gate_name: str, status: str, passed: bool, blocker_reason: str, evidence_path: Path | None = None) -> MetricComputationGateResult:
    return MetricComputationGateResult(
        gate_group=gate_group,
        gate_name=gate_name,
        status=status,
        passed=passed,
        blocker_reason=blocker_reason,
        evidence_path=str(evidence_path or ""),
    )


def _has_any_input(settings: MetricComputationSettings) -> bool:
    return any(
        _path_exists(path)
        for path in [
            settings.approval_manifest_path,
            settings.metric_computation_request_manifest_path,
            settings.metric_evaluation_metadata_path,
            settings.training_evaluation_metadata_path,
            settings.training_evaluation_sample_rows_path,
        ]
    )


def _read_json(path: Path | None) -> dict[str, Any]:
    if not _path_exists(path):
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv(path: Path | None) -> pd.DataFrame:
    if not _path_exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, dtype={"symbol": "string"})


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _status_value(path: Path | None) -> str:
    if not _path_exists(path):
        return ""
    path = Path(path)
    if path.suffix.lower() == ".json":
        payload = _read_json(path)
        return str(payload.get("status", payload.get("execution_status", payload.get("health_status", ""))))
    frame = _read_csv(path)
    if frame.empty or "status" not in frame.columns:
        return ""
    return str(frame["status"].iloc[0])


def _missing_paths(paths: list[Path | None]) -> str:
    return ", ".join(str(path) for path in paths if not _path_exists(path))


def _path_exists(path: Path | None) -> bool:
    return path is not None and Path(path).exists()


def _assert_manual_diagnostics_output(output_dir: Path) -> None:
    parts = {part.lower() for part in output_dir.parts}
    if "manual_diagnostics" not in parts:
        raise ValueError("metric-computation output_dir must be under outputs/reports/manual_diagnostics")


def _stable_id(settings: MetricComputationSettings) -> str:
    payload = {
        "approval_manifest_path": str(settings.approval_manifest_path or ""),
        "metric_evaluation_metadata_path": str(settings.metric_evaluation_metadata_path or ""),
        "training_evaluation_metadata_path": str(settings.training_evaluation_metadata_path or ""),
        "allow_metric_computation": settings.allow_metric_computation,
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]
