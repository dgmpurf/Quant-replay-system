"""Report-only metric extension phase 1 workflow."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_METRIC_EXTENSION_INPUT = "NO_METRIC_EXTENSION_INPUT"
METRIC_EXTENSION_INPUT_FOUND = "METRIC_EXTENSION_INPUT_FOUND"
METRIC_EXTENSION_APPROVAL_BLOCKED = "METRIC_EXTENSION_APPROVAL_BLOCKED"
METRIC_EXTENSION_METRIC_COMPUTATION_INPUT_BLOCKED = "METRIC_EXTENSION_METRIC_COMPUTATION_INPUT_BLOCKED"
METRIC_EXTENSION_METRIC_EVALUATION_INPUT_BLOCKED = "METRIC_EXTENSION_METRIC_EVALUATION_INPUT_BLOCKED"
METRIC_EXTENSION_TRAINING_EVALUATION_INPUT_BLOCKED = "METRIC_EXTENSION_TRAINING_EVALUATION_INPUT_BLOCKED"
METRIC_EXTENSION_FORWARD_LABEL_INPUT_BLOCKED = "METRIC_EXTENSION_FORWARD_LABEL_INPUT_BLOCKED"
METRIC_EXTENSION_REPLAY_FREEZE_INPUT_BLOCKED = "METRIC_EXTENSION_REPLAY_FREEZE_INPUT_BLOCKED"
METRIC_EXTENSION_HEALTH_BLOCKED = "METRIC_EXTENSION_HEALTH_BLOCKED"
METRIC_EXTENSION_LINEAGE_BLOCKED = "METRIC_EXTENSION_LINEAGE_BLOCKED"
METRIC_EXTENSION_BENCHMARK_MAPPING_BLOCKED = "METRIC_EXTENSION_BENCHMARK_MAPPING_BLOCKED"
METRIC_EXTENSION_INDUSTRY_MAPPING_BLOCKED = "METRIC_EXTENSION_INDUSTRY_MAPPING_BLOCKED"
METRIC_EXTENSION_RETURN_FIELD_BLOCKED = "METRIC_EXTENSION_RETURN_FIELD_BLOCKED"
METRIC_EXTENSION_DENOMINATOR_BLOCKED = "METRIC_EXTENSION_DENOMINATOR_BLOCKED"
METRIC_EXTENSION_SAMPLE_SCOPE_BLOCKED = "METRIC_EXTENSION_SAMPLE_SCOPE_BLOCKED"
METRIC_EXTENSION_UNSUPPORTED_METRIC_BLOCKED = "METRIC_EXTENSION_UNSUPPORTED_METRIC_BLOCKED"
METRIC_EXTENSION_RESULT_ROW_BLOCKED = "METRIC_EXTENSION_RESULT_ROW_BLOCKED"
METRIC_EXTENSION_LEAKAGE_BLOCKED = "METRIC_EXTENSION_LEAKAGE_BLOCKED"
METRIC_EXTENSION_SIDE_EFFECT_BLOCKED = "METRIC_EXTENSION_SIDE_EFFECT_BLOCKED"
METRIC_EXTENSION_OVERCLAIM_BLOCKED = "METRIC_EXTENSION_OVERCLAIM_BLOCKED"
READY_FOR_METRIC_EXTENSION = "READY_FOR_METRIC_EXTENSION"
METRIC_EXTENSION_REPORT_CREATED = "METRIC_EXTENSION_REPORT_CREATED"

EXACT_METRIC_EXTENSION_APPROVAL_TEXT = (
    "I explicitly authorize Metric Extension Implementation phase 1 only, and only as "
    "report-only metric extension. It may create report-only extended metric artifacts "
    "and result rows only when immutable v1.47 METRIC_COMPUTATION_REPORT_CREATED artifacts, "
    "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED artifacts, TRAINING_EVALUATION_DATASET_CREATED "
    "artifacts, FORWARD_RETURN_LABELS_CREATED artifacts, and REPLAY_DECISION_FROZEN artifacts "
    "have complete lineage and PASS health. This phase is limited to benchmark_relative_return "
    "and industry_relative_return. It must validate benchmark mapping, industry mapping, return "
    "fields, available_time, source_hash, revision_id, quality_status, denominator contract, and "
    "sample scope contract. If inputs or lineage are missing, it must fail closed and compute "
    "nothing. It must not implement max_drawdown, max_runup, IC, rank IC, Sharpe-like metric, "
    "confidence_interval, out_of_sample_metric, regime_robustness, false_positive_cost, "
    "false_negative_opportunity_cost, turnover, slippage_sensitivity, or any other advanced/path/"
    "cost metrics. It must not create training_result, train weights, create model_version, "
    "optimize thresholds, create predictions, create calibrated probabilities, create feature "
    "importance, create stock_profile, generate buy-review eligibility, apply paper approval, "
    "claim strategy performance validation, integrate broker/order/message, or trade."
)

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/metric_extension_v0_1")
ALLOWED_EXTENSION_METRIC_SET = ["benchmark_relative_return", "industry_relative_return"]

UNSUPPORTED_METRIC_SET = {
    "max_drawdown",
    "max_runup",
    "information_coefficient",
    "ic",
    "rank_information_coefficient",
    "rank_ic",
    "sharpe_like_metric",
    "confidence_interval",
    "out_of_sample_metric",
    "regime_robustness",
    "false_positive_cost",
    "false_negative_opportunity_cost",
    "turnover",
    "slippage_sensitivity",
}

ARTIFACT_FILES = {
    "metadata": "metric_extension_metadata.json",
    "report": "metric_extension_report.md",
    "input_index": "metric_extension_input_index.csv",
    "metric_definitions_used": "metric_extension_metric_definitions_used.csv",
    "benchmark_mapping_used": "metric_extension_benchmark_mapping_used.csv",
    "industry_mapping_used": "metric_extension_industry_mapping_used.csv",
    "return_fields_used": "metric_extension_return_fields_used.csv",
    "sample_scope_used": "metric_extension_sample_scope_used.csv",
    "denominator_rules_used": "metric_extension_denominator_rules_used.csv",
    "result_rows": "metric_extension_result_rows.csv",
    "summary": "metric_extension_summary.csv",
    "safety_flags": "metric_extension_safety_flags.json",
    "precondition_results": "metric_extension_precondition_results.csv",
    "approval_results": "metric_extension_approval_results.csv",
    "input_lineage_results": "metric_extension_input_lineage_results.csv",
    "metric_definition_results": "metric_extension_metric_definition_results.csv",
    "benchmark_mapping_results": "metric_extension_benchmark_mapping_results.csv",
    "industry_mapping_results": "metric_extension_industry_mapping_results.csv",
    "return_field_results": "metric_extension_return_field_results.csv",
    "denominator_results": "metric_extension_denominator_results.csv",
    "sample_scope_results": "metric_extension_sample_scope_results.csv",
    "result_row_results": "metric_extension_result_row_results.csv",
    "leakage_guard_results": "metric_extension_leakage_guard_results.csv",
    "side_effect_guard_results": "metric_extension_side_effect_guard_results.csv",
    "overclaim_guard_results": "metric_extension_overclaim_guard_results.csv",
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
    "metric_extension_not_strategy_validation",
    "metric_extension_not_training_result",
    "metric_extension_not_weights",
    "metric_extension_not_model_version",
    "metric_extension_not_thresholds",
    "metric_extension_not_predictions",
    "metric_extension_not_probabilities",
    "metric_extension_not_feature_importance",
    "metric_extension_not_stock_profile",
    "metric_extension_not_buy_review",
    "metric_extension_not_paper_approval",
    "metric_extension_not_performance_validation",
    "metric_extension_not_trading",
}

SAMPLE_REQUIRED_COLUMNS = {
    "training_evaluation_sample_id",
    "metric_computation_run_id",
    "metric_computation_result_row_id",
    "metric_evaluation_run_id",
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
    "report_only",
    "diagnostic_only",
}
SAMPLE_LINEAGE_COLUMNS = {
    "source_hash_coverage",
    "revision_id_coverage",
    "available_time_coverage",
    "quality_status_coverage",
    "metric_computation_run_id",
    "metric_evaluation_run_id",
    "training_evaluation_run_id",
    "replay_decision_freeze_run_id",
    "forward_return_label_run_id",
}
BENCHMARK_REQUIRED_COLUMNS = {
    "symbol",
    "replay_as_of_date",
    "horizon_trading_days",
    "benchmark_id",
    "benchmark_name",
    "benchmark_return_value",
    "benchmark_available_time",
    "benchmark_source_hash",
    "benchmark_revision_id",
    "benchmark_quality_status",
    "benchmark_denominator_eligible",
    "report_only",
    "diagnostic_only",
}
BENCHMARK_LINEAGE_COLUMNS = {
    "benchmark_available_time",
    "benchmark_source_hash",
    "benchmark_revision_id",
    "benchmark_quality_status",
}
INDUSTRY_REQUIRED_COLUMNS = {
    "symbol",
    "replay_as_of_date",
    "horizon_trading_days",
    "industry_id",
    "industry_name",
    "industry_return_value",
    "industry_classification_available_time",
    "industry_return_available_time",
    "industry_source_hash",
    "industry_revision_id",
    "industry_quality_status",
    "industry_denominator_eligible",
    "report_only",
    "diagnostic_only",
}
INDUSTRY_LINEAGE_COLUMNS = {
    "industry_classification_available_time",
    "industry_return_available_time",
    "industry_source_hash",
    "industry_revision_id",
    "industry_quality_status",
}


@dataclass(frozen=True)
class MetricExtensionSettings:
    approval_manifest_path: Path | None = None
    metric_extension_request_manifest_path: Path | None = None
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
    benchmark_mapping_path: Path | None = None
    industry_mapping_path: Path | None = None
    benchmark_return_rows_path: Path | None = None
    industry_return_rows_path: Path | None = None
    leakage_evidence_bundle_path: Path | None = None
    overclaim_evidence_bundle_path: Path | None = None
    side_effect_evidence_bundle_path: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    allow_metric_extension: bool = False
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class MetricExtensionGateResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str = ""
    observed_value: str = ""


MetricExtensionApprovalResult = MetricExtensionGateResult
MetricExtensionInputLineageResult = MetricExtensionGateResult
MetricExtensionMetricDefinitionResult = MetricExtensionGateResult
MetricExtensionBenchmarkMappingResult = MetricExtensionGateResult
MetricExtensionIndustryMappingResult = MetricExtensionGateResult
MetricExtensionReturnFieldResult = MetricExtensionGateResult
MetricExtensionDenominatorResult = MetricExtensionGateResult
MetricExtensionSampleScopeResult = MetricExtensionGateResult
MetricExtensionResultRowResult = MetricExtensionGateResult
MetricExtensionLeakageGuardResult = MetricExtensionGateResult
MetricExtensionSideEffectGuardResult = MetricExtensionGateResult
MetricExtensionOverclaimResult = MetricExtensionGateResult


@dataclass(frozen=True)
class MetricExtensionResult:
    metric_extension_run_id: str
    status: str
    workflow_stage: str
    ready_for_metric_extension: bool
    metric_extension_executed: bool
    metric_extension_report_created: bool
    extended_metric_result_rows_created: bool
    extended_metric_summary_created: bool
    extended_metrics_computed: bool
    artifact_path: str
    allowed_extension_metric_set: str
    requested_extension_metric_set: str = ""
    unsupported_metrics_requested: bool = False
    source_metric_computation_run_id: str = ""
    source_metric_computation_artifact_path: str = ""
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
    sample_row_count: int = 0
    eligible_sample_count: int = 0
    quarantined_sample_count: int = 0
    benchmark_mapping_row_count: int = 0
    industry_mapping_row_count: int = 0
    benchmark_denominator_count: int = 0
    industry_denominator_count: int = 0
    benchmark_relative_return_created: bool = False
    industry_relative_return_created: bool = False
    blocker_count: int = 0
    warning_count: int = 0
    next_action: str = ""
    report_only: bool = True
    diagnostic_only: bool = True
    artifact_paths: dict[str, Path] = field(default_factory=dict)
    gate_results: list[MetricExtensionGateResult] = field(default_factory=list)
    safety_statement: str = (
        "Metric extension is report-only benchmark/industry relative metrics for a bounded sample: "
        "not strategy validation, not training_result, not weights, not model_version, not thresholds, "
        "not predictions, not calibrated probabilities, not feature importance, not stock_profile, "
        "not buy-review, not paper approval, not performance validation, and not trading."
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


def run_metric_extension(settings: MetricExtensionSettings | None = None) -> MetricExtensionResult:
    settings = settings or MetricExtensionSettings()
    output_root = Path(settings.output_dir)
    _assert_manual_diagnostics_output(output_root)
    run_id = _stable_id(settings)
    artifact_dir = output_root / run_id
    artifact_paths = {"artifact_dir": artifact_dir} | {
        key: artifact_dir / filename for key, filename in ARTIFACT_FILES.items()
    }
    state = _evaluate(settings)
    created = state["status"] == METRIC_EXTENSION_REPORT_CREATED
    ready = state["status"] in {READY_FOR_METRIC_EXTENSION, METRIC_EXTENSION_REPORT_CREATED}
    metric_meta = state["metric_computation_metadata"]
    metric_eval_meta = state["metric_evaluation_metadata"]
    training_meta = state["training_evaluation_metadata"]
    label_meta = state["forward_label_metadata"]
    freeze_meta = state["replay_freeze_metadata"]
    result = MetricExtensionResult(
        metric_extension_run_id=run_id,
        status=state["status"],
        workflow_stage="METRIC_EXTENSION_NO_INPUT" if state["status"] == NO_METRIC_EXTENSION_INPUT else state["status"],
        ready_for_metric_extension=ready,
        metric_extension_executed=created,
        metric_extension_report_created=created,
        extended_metric_result_rows_created=created,
        extended_metric_summary_created=created,
        extended_metrics_computed=created,
        artifact_path=str(artifact_dir),
        allowed_extension_metric_set=",".join(ALLOWED_EXTENSION_METRIC_SET),
        requested_extension_metric_set=",".join(state["requested_extension_metric_set"]),
        unsupported_metrics_requested=state["unsupported_metrics_requested"],
        source_metric_computation_run_id=str(metric_meta.get("metric_computation_run_id", "")),
        source_metric_computation_artifact_path=str(Path(settings.metric_computation_metadata_path).parent if settings.metric_computation_metadata_path else ""),
        source_metric_computation_status=str(metric_meta.get("status", metric_meta.get("execution_status", ""))),
        source_metric_computation_health_status=_status_value(settings.metric_computation_health_artifact_path),
        source_metric_evaluation_planning_run_id=str(metric_eval_meta.get("metric_evaluation_run_id", metric_meta.get("source_metric_evaluation_planning_run_id", ""))),
        source_metric_evaluation_status=str(metric_eval_meta.get("status", metric_eval_meta.get("execution_status", ""))),
        source_metric_evaluation_health_status=_status_value(settings.metric_evaluation_health_artifact_path),
        source_training_evaluation_run_id=str(training_meta.get("training_evaluation_run_id", metric_meta.get("source_training_evaluation_run_id", ""))),
        source_training_evaluation_status=str(training_meta.get("status", training_meta.get("execution_status", ""))),
        source_training_evaluation_health_status=_status_value(settings.training_evaluation_health_artifact_path),
        source_forward_return_label_run_id=str(label_meta.get("forward_return_label_run_id", metric_meta.get("source_forward_return_label_run_id", ""))),
        source_forward_return_label_status=str(label_meta.get("status", label_meta.get("execution_status", ""))),
        source_forward_return_label_health_status=_status_value(settings.forward_return_label_health_artifact_path),
        source_replay_decision_freeze_run_id=str(freeze_meta.get("replay_decision_freeze_run_id", metric_meta.get("source_replay_decision_freeze_run_id", ""))),
        source_replay_decision_freeze_status=str(freeze_meta.get("status", freeze_meta.get("execution_status", ""))),
        source_replay_decision_freeze_health_status=_status_value(settings.replay_decision_freeze_health_artifact_path),
        sample_row_count=state["sample_row_count"],
        eligible_sample_count=state["eligible_sample_count"],
        quarantined_sample_count=state["quarantined_sample_count"],
        benchmark_mapping_row_count=len(state["benchmark_mapping"]),
        industry_mapping_row_count=len(state["industry_mapping"]),
        benchmark_denominator_count=state["benchmark_denominator_count"],
        industry_denominator_count=state["industry_denominator_count"],
        benchmark_relative_return_created=created,
        industry_relative_return_created=created,
        blocker_count=0 if ready else 1 if state["status"] != NO_METRIC_EXTENSION_INPUT else 0,
        warning_count=state["quarantined_sample_count"],
        next_action=_next_action(state["status"]),
        artifact_paths=artifact_paths,
        gate_results=state["gate_results"],
    )
    if settings.write_artifacts:
        write_metric_extension_artifacts(result, state)
    return result


def write_metric_extension_artifacts(result: MetricExtensionResult, state: dict[str, Any] | None = None) -> None:
    state = state or {}
    artifact_dir = result.artifact_paths["artifact_dir"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    result.artifact_paths["metadata"].write_text(json.dumps(_metadata(result), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["safety_flags"].write_text(json.dumps(_safety_flags(result), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(_recommended_next_task(result), encoding="utf-8")
    frames = {
        "input_index": _input_index_rows(result, state),
        "metric_definitions_used": _metric_definitions(result.metric_extension_run_id),
        "benchmark_mapping_used": state.get("benchmark_mapping", _empty_artifact_frame("benchmark_mapping_used")),
        "industry_mapping_used": state.get("industry_mapping", _empty_artifact_frame("industry_mapping_used")),
        "return_fields_used": _return_fields_used(result.metric_extension_run_id),
        "sample_scope_used": state.get("sample_scope", _empty_artifact_frame("sample_scope_used")),
        "denominator_rules_used": state.get("denominator_rules", _empty_artifact_frame("denominator_rules_used")),
        "result_rows": state.get("result_rows", _empty_artifact_frame("result_rows")),
        "summary": state.get("summary_rows", _empty_artifact_frame("summary")),
        "precondition_results": _gate_frame(state.get("gate_results", []), "precondition"),
        "approval_results": _gate_frame(state.get("gate_results", []), "approval"),
        "input_lineage_results": _gate_frame(state.get("gate_results", []), "input_lineage"),
        "metric_definition_results": _gate_frame(state.get("gate_results", []), "metric_definition"),
        "benchmark_mapping_results": _gate_frame(state.get("gate_results", []), "benchmark_mapping"),
        "industry_mapping_results": _gate_frame(state.get("gate_results", []), "industry_mapping"),
        "return_field_results": _gate_frame(state.get("gate_results", []), "return_field"),
        "denominator_results": _gate_frame(state.get("gate_results", []), "denominator"),
        "sample_scope_results": _gate_frame(state.get("gate_results", []), "sample_scope"),
        "result_row_results": _gate_frame(state.get("gate_results", []), "result_row"),
        "leakage_guard_results": _gate_frame(state.get("gate_results", []), "leakage_guard"),
        "side_effect_guard_results": _gate_frame(state.get("gate_results", []), "side_effect_guard"),
        "overclaim_guard_results": _gate_frame(state.get("gate_results", []), "overclaim_guard"),
    }
    for key, frame in frames.items():
        _write_csv(result.artifact_paths[key], frame)


def _evaluate(settings: MetricExtensionSettings) -> dict[str, Any]:
    state: dict[str, Any] = {
        "status": NO_METRIC_EXTENSION_INPUT,
        "gate_results": [],
        "requested_extension_metric_set": list(ALLOWED_EXTENSION_METRIC_SET),
        "unsupported_metrics_requested": False,
        "metric_computation_metadata": {},
        "metric_evaluation_metadata": {},
        "training_evaluation_metadata": {},
        "forward_label_metadata": {},
        "replay_freeze_metadata": {},
        "sample_rows": pd.DataFrame(),
        "benchmark_mapping": pd.DataFrame(),
        "industry_mapping": pd.DataFrame(),
        "sample_scope": pd.DataFrame(),
        "denominator_rules": pd.DataFrame(),
        "result_rows": _empty_artifact_frame("result_rows"),
        "summary_rows": _empty_artifact_frame("summary"),
        "sample_row_count": 0,
        "eligible_sample_count": 0,
        "quarantined_sample_count": 0,
        "benchmark_denominator_count": 0,
        "industry_denominator_count": 0,
    }
    if not _has_any_input(settings):
        state["gate_results"].append(_gate("precondition", "input_presence", NO_METRIC_EXTENSION_INPUT, True, "no metric extension input supplied"))
        return state

    approval = _read_json(settings.approval_manifest_path)
    if not _approval_valid(str(approval.get("approval_text", ""))):
        return _blocked(state, METRIC_EXTENSION_APPROVAL_BLOCKED, "approval", "exact_metric_extension_scope", "exact narrow metric extension approval text missing", settings.approval_manifest_path)
    state["gate_results"].append(_gate("approval", "exact_metric_extension_scope", "PASS", True, "", settings.approval_manifest_path))

    request = _read_json(settings.metric_extension_request_manifest_path)
    request_status = _request_block_status(request)
    requested = request.get("requested_extension_metric_set", ALLOWED_EXTENSION_METRIC_SET)
    state["requested_extension_metric_set"] = [str(item) for item in requested]
    if request_status:
        if request_status == METRIC_EXTENSION_UNSUPPORTED_METRIC_BLOCKED:
            state["unsupported_metrics_requested"] = True
        return _blocked(state, request_status, "metric_definition", "request_scope", "request asks outside metric extension phase 1", settings.metric_extension_request_manifest_path)

    missing_status = _missing_required_path_status(settings)
    if missing_status is not None:
        status, group, gate_name, reason = missing_status
        return _blocked(state, status, group, gate_name, reason, None)

    metric_meta = _read_json(settings.metric_computation_metadata_path)
    state["metric_computation_metadata"] = metric_meta
    status_check = _source_status_check(
        "metric_computation",
        metric_meta,
        settings.metric_computation_status_artifact_path,
        settings.metric_computation_health_artifact_path,
        "METRIC_COMPUTATION_REPORT_CREATED",
        METRIC_EXTENSION_METRIC_COMPUTATION_INPUT_BLOCKED,
    )
    if status_check:
        return _blocked(state, status_check[0], "input_lineage", status_check[1], status_check[2], status_check[3])

    metric_eval_meta = _read_json(settings.metric_evaluation_metadata_path)
    state["metric_evaluation_metadata"] = metric_eval_meta
    status_check = _source_status_check(
        "metric_evaluation",
        metric_eval_meta,
        settings.metric_evaluation_status_artifact_path,
        settings.metric_evaluation_health_artifact_path,
        "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED",
        METRIC_EXTENSION_METRIC_EVALUATION_INPUT_BLOCKED,
    )
    if status_check:
        return _blocked(state, status_check[0], "input_lineage", status_check[1], status_check[2], status_check[3])

    training_meta = _read_json(settings.training_evaluation_metadata_path)
    state["training_evaluation_metadata"] = training_meta
    status_check = _source_status_check(
        "training_evaluation",
        training_meta,
        settings.training_evaluation_status_artifact_path,
        settings.training_evaluation_health_artifact_path,
        "TRAINING_EVALUATION_DATASET_CREATED",
        METRIC_EXTENSION_TRAINING_EVALUATION_INPUT_BLOCKED,
    )
    if status_check:
        return _blocked(state, status_check[0], "input_lineage", status_check[1], status_check[2], status_check[3])

    label_meta = _read_json(settings.forward_return_label_metadata_path)
    state["forward_label_metadata"] = label_meta
    status_check = _source_status_check(
        "forward_return_label",
        label_meta,
        settings.forward_return_label_status_artifact_path,
        settings.forward_return_label_health_artifact_path,
        "FORWARD_RETURN_LABELS_CREATED",
        METRIC_EXTENSION_FORWARD_LABEL_INPUT_BLOCKED,
    )
    if status_check:
        return _blocked(state, status_check[0], "input_lineage", status_check[1], status_check[2], status_check[3])

    freeze_meta = _read_json(settings.replay_decision_freeze_metadata_path)
    state["replay_freeze_metadata"] = freeze_meta
    status_check = _source_status_check(
        "replay_decision_freeze",
        freeze_meta,
        settings.replay_decision_freeze_status_artifact_path,
        settings.replay_decision_freeze_health_artifact_path,
        "REPLAY_DECISION_FROZEN",
        METRIC_EXTENSION_REPLAY_FREEZE_INPUT_BLOCKED,
    )
    if status_check:
        return _blocked(state, status_check[0], "input_lineage", status_check[1], status_check[2], status_check[3])

    sample_scope = _read_csv(settings.metric_evaluation_sample_scope_path)
    if sample_scope.empty:
        return _blocked(state, METRIC_EXTENSION_SAMPLE_SCOPE_BLOCKED, "sample_scope", "sample_scope_contract", "sample scope contract missing or empty", settings.metric_evaluation_sample_scope_path)
    state["sample_scope"] = sample_scope
    denominator_rules = _read_csv(settings.metric_evaluation_denominator_rules_path)
    if denominator_rules.empty or not set(ALLOWED_EXTENSION_METRIC_SET).issubset(set(denominator_rules.get("metric_name", []))):
        return _blocked(state, METRIC_EXTENSION_DENOMINATOR_BLOCKED, "denominator", "denominator_contract", "denominator contract missing allowed extension metrics", settings.metric_evaluation_denominator_rules_path)
    state["denominator_rules"] = denominator_rules

    sample_rows = _read_csv(settings.training_evaluation_sample_rows_path)
    state["sample_rows"] = sample_rows
    state["sample_row_count"] = len(sample_rows)
    sample_missing = SAMPLE_REQUIRED_COLUMNS - set(sample_rows.columns)
    if sample_missing & SAMPLE_LINEAGE_COLUMNS:
        return _blocked(state, METRIC_EXTENSION_LINEAGE_BLOCKED, "input_lineage", "sample_lineage_columns", f"missing sample lineage columns: {', '.join(sorted(sample_missing))}", settings.training_evaluation_sample_rows_path)
    if sample_missing:
        return _blocked(state, METRIC_EXTENSION_SAMPLE_SCOPE_BLOCKED, "sample_scope", "sample_required_columns", f"missing sample columns: {', '.join(sorted(sample_missing))}", settings.training_evaluation_sample_rows_path)
    if not _coverage_pass(sample_rows):
        return _blocked(state, METRIC_EXTENSION_LINEAGE_BLOCKED, "input_lineage", "sample_lineage_coverage", "sample source_hash/revision/available_time/quality coverage missing", settings.training_evaluation_sample_rows_path)
    if sample_rows.duplicated(subset=["training_evaluation_sample_id"]).any() or sample_rows.duplicated(subset=["replay_decision_id", "forward_return_label_id"]).any():
        return _blocked(state, METRIC_EXTENSION_SAMPLE_SCOPE_BLOCKED, "sample_scope", "sample_identity_uniqueness", "duplicate sample identity rows must be quarantined before metric extension", settings.training_evaluation_sample_rows_path)

    benchmark = _load_comparator_frame(settings.benchmark_mapping_path, settings.benchmark_return_rows_path, "benchmark")
    state["benchmark_mapping"] = benchmark
    benchmark_missing = BENCHMARK_REQUIRED_COLUMNS - set(benchmark.columns)
    if "benchmark_return_value" in benchmark_missing:
        return _blocked(state, METRIC_EXTENSION_RETURN_FIELD_BLOCKED, "return_field", "benchmark_return_value", "benchmark return field missing", settings.benchmark_mapping_path)
    if benchmark_missing & BENCHMARK_LINEAGE_COLUMNS:
        return _blocked(state, METRIC_EXTENSION_LINEAGE_BLOCKED, "input_lineage", "benchmark_lineage_columns", f"missing benchmark lineage columns: {', '.join(sorted(benchmark_missing))}", settings.benchmark_mapping_path)
    if benchmark_missing:
        return _blocked(state, METRIC_EXTENSION_BENCHMARK_MAPPING_BLOCKED, "benchmark_mapping", "benchmark_required_columns", f"missing benchmark columns: {', '.join(sorted(benchmark_missing))}", settings.benchmark_mapping_path)
    if not _benchmark_lineage_pass(benchmark):
        return _blocked(state, METRIC_EXTENSION_LINEAGE_BLOCKED, "input_lineage", "benchmark_lineage_coverage", "benchmark lineage coverage missing", settings.benchmark_mapping_path)

    industry = _load_comparator_frame(settings.industry_mapping_path, settings.industry_return_rows_path, "industry")
    state["industry_mapping"] = industry
    industry_missing = INDUSTRY_REQUIRED_COLUMNS - set(industry.columns)
    if "industry_return_value" in industry_missing:
        return _blocked(state, METRIC_EXTENSION_RETURN_FIELD_BLOCKED, "return_field", "industry_return_value", "industry return field missing", settings.industry_mapping_path)
    if industry_missing & INDUSTRY_LINEAGE_COLUMNS:
        return _blocked(state, METRIC_EXTENSION_LINEAGE_BLOCKED, "input_lineage", "industry_lineage_columns", f"missing industry lineage columns: {', '.join(sorted(industry_missing))}", settings.industry_mapping_path)
    if industry_missing:
        return _blocked(state, METRIC_EXTENSION_INDUSTRY_MAPPING_BLOCKED, "industry_mapping", "industry_required_columns", f"missing industry columns: {', '.join(sorted(industry_missing))}", settings.industry_mapping_path)
    if not _industry_lineage_pass(industry):
        return _blocked(state, METRIC_EXTENSION_LINEAGE_BLOCKED, "input_lineage", "industry_lineage_coverage", "industry lineage coverage missing", settings.industry_mapping_path)

    leakage = _read_json(settings.leakage_evidence_bundle_path)
    if not _path_exists(settings.leakage_evidence_bundle_path) or any(bool(v) for v in leakage.values() if isinstance(v, bool)):
        return _blocked(state, METRIC_EXTENSION_LEAKAGE_BLOCKED, "leakage_guard", "future_leakage", "leakage evidence bundle is missing or unsafe", settings.leakage_evidence_bundle_path)
    side_effect = _read_json(settings.side_effect_evidence_bundle_path)
    if not _path_exists(settings.side_effect_evidence_bundle_path) or any(bool(side_effect.get(field, False)) for field in SIDE_EFFECT_TRUE_FIELDS):
        return _blocked(state, METRIC_EXTENSION_SIDE_EFFECT_BLOCKED, "side_effect_guard", "side_effect_flags", "side-effect evidence bundle is missing or unsafe", settings.side_effect_evidence_bundle_path)
    overclaim = _read_json(settings.overclaim_evidence_bundle_path)
    if not _path_exists(settings.overclaim_evidence_bundle_path) or any(not bool(overclaim.get(field, False)) for field in REQUIRED_OVERCLAIM_TRUE):
        return _blocked(state, METRIC_EXTENSION_OVERCLAIM_BLOCKED, "overclaim_guard", "overclaim_flags", "overclaim evidence bundle is missing or unsafe", settings.overclaim_evidence_bundle_path)

    result_rows, summary_rows, counts = _build_metric_rows(sample_rows, benchmark, industry, state)
    state["result_rows"] = result_rows if settings.allow_metric_extension else _empty_artifact_frame("result_rows")
    state["summary_rows"] = summary_rows if settings.allow_metric_extension else _empty_artifact_frame("summary")
    state.update(counts)
    if counts["benchmark_denominator_count"] == 0 and counts["industry_denominator_count"] == 0:
        return _blocked(state, METRIC_EXTENSION_RESULT_ROW_BLOCKED, "result_row", "eligible_relative_rows", "no eligible benchmark or industry relative rows available", settings.training_evaluation_sample_rows_path)
    state["eligible_sample_count"] = max(counts["benchmark_denominator_count"], counts["industry_denominator_count"])
    state["gate_results"].extend(
        [
            _gate("input_lineage", "immutable_lineage", METRIC_EXTENSION_INPUT_FOUND, True, "", settings.metric_computation_metadata_path),
            _gate("metric_definition", "allowed_metric_set", METRIC_EXTENSION_INPUT_FOUND, True, "", settings.metric_extension_request_manifest_path),
            _gate("benchmark_mapping", "benchmark_mapping", METRIC_EXTENSION_INPUT_FOUND, True, "", settings.benchmark_mapping_path),
            _gate("industry_mapping", "industry_mapping", METRIC_EXTENSION_INPUT_FOUND, True, "", settings.industry_mapping_path),
            _gate("return_field", "return_fields", METRIC_EXTENSION_INPUT_FOUND, True, "", settings.benchmark_return_rows_path),
            _gate("denominator", "denominator_rules", METRIC_EXTENSION_INPUT_FOUND, True, "", settings.metric_evaluation_denominator_rules_path),
            _gate("sample_scope", "sample_scope", METRIC_EXTENSION_INPUT_FOUND, True, "", settings.metric_evaluation_sample_scope_path),
            _gate("result_row", "eligible_relative_rows", METRIC_EXTENSION_INPUT_FOUND, True, "", settings.training_evaluation_sample_rows_path),
            _gate("leakage_guard", "future_leakage", METRIC_EXTENSION_INPUT_FOUND, True, "", settings.leakage_evidence_bundle_path),
            _gate("side_effect_guard", "side_effect_flags", METRIC_EXTENSION_INPUT_FOUND, True, "", settings.side_effect_evidence_bundle_path),
            _gate("overclaim_guard", "overclaim_flags", METRIC_EXTENSION_INPUT_FOUND, True, "", settings.overclaim_evidence_bundle_path),
        ]
    )
    state["status"] = METRIC_EXTENSION_REPORT_CREATED if settings.allow_metric_extension else READY_FOR_METRIC_EXTENSION
    return state


def _build_metric_rows(
    sample_rows: pd.DataFrame,
    benchmark: pd.DataFrame,
    industry: pd.DataFrame,
    state: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    sample = sample_rows.copy()
    sample["label_numeric"] = pd.to_numeric(sample["label_value"], errors="coerce")
    key = ["symbol", "replay_as_of_date", "horizon_trading_days"]
    bench = benchmark.copy()
    bench["benchmark_numeric"] = pd.to_numeric(bench["benchmark_return_value"], errors="coerce")
    ind = industry.copy()
    ind["industry_numeric"] = pd.to_numeric(ind["industry_return_value"], errors="coerce")
    bench_merged = sample.merge(bench, on=key, how="left")
    ind_merged = sample.merge(ind, on=key, how="left")
    bench_eligible = bench_merged[
        bench_merged["label_numeric"].notna()
        & bench_merged["benchmark_numeric"].notna()
        & bench_merged["benchmark_denominator_eligible"].map(_truthy)
    ].copy()
    ind_eligible = ind_merged[
        ind_merged["label_numeric"].notna()
        & ind_merged["industry_numeric"].notna()
        & ind_merged["industry_denominator_eligible"].map(_truthy)
    ].copy()
    rows = []
    rows.extend(_relative_rows(bench_eligible, "benchmark_relative_return", "benchmark_numeric", "benchmark", len(bench_eligible), state))
    rows.extend(_relative_rows(ind_eligible, "industry_relative_return", "industry_numeric", "industry", len(ind_eligible), state))
    result_rows = pd.DataFrame(rows, columns=_empty_artifact_frame("result_rows").columns)
    summary_rows = _summary_rows(result_rows)
    bad_label = int(sample["label_numeric"].isna().sum())
    bad_benchmark = int(bench_merged["benchmark_numeric"].isna().sum())
    bad_industry = int(ind_merged["industry_numeric"].isna().sum())
    return (
        result_rows,
        summary_rows,
        {
            "benchmark_denominator_count": len(bench_eligible),
            "industry_denominator_count": len(ind_eligible),
            "quarantined_sample_count": max(bad_label, bad_benchmark, bad_industry),
        },
    )


def _relative_rows(
    frame: pd.DataFrame,
    metric_name: str,
    comparator_column: str,
    comparator_kind: str,
    denominator_count: int,
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        metric_value = float(row["label_numeric"]) - float(row[comparator_column])
        rows.append(
            {
                "metric_extension_run_id": "",
                "source_metric_computation_run_id": str(row.get("metric_computation_run_id", state["metric_computation_metadata"].get("metric_computation_run_id", ""))),
                "source_metric_evaluation_planning_run_id": str(row.get("metric_evaluation_run_id", state["metric_evaluation_metadata"].get("metric_evaluation_run_id", ""))),
                "source_training_evaluation_run_id": str(row.get("training_evaluation_run_id", state["training_evaluation_metadata"].get("training_evaluation_run_id", ""))),
                "source_forward_return_label_run_id": str(row.get("forward_return_label_run_id", state["forward_label_metadata"].get("forward_return_label_run_id", ""))),
                "source_replay_decision_freeze_run_id": str(row.get("replay_decision_freeze_run_id", state["replay_freeze_metadata"].get("replay_decision_freeze_run_id", ""))),
                "replay_decision_id": str(row.get("replay_decision_id", "")),
                "forward_return_label_id": str(row.get("forward_return_label_id", "")),
                "symbol": str(row.get("symbol", "")),
                "replay_as_of_date": str(row.get("replay_as_of_date", "")),
                "split_role": str(row.get("split_role", "")),
                "label_name": str(row.get("label_name", "")),
                "horizon_trading_days": int(row.get("horizon_trading_days", 0)),
                "metric_name": metric_name,
                "metric_value": metric_value,
                "numerator_count": 1,
                "denominator_count": denominator_count,
                "benchmark_id": str(row.get("benchmark_id", "")),
                "benchmark_name": str(row.get("benchmark_name", "")),
                "industry_id": str(row.get("industry_id", "")),
                "industry_name": str(row.get("industry_name", "")),
                "sample_scope": "eligible bounded report-only sample",
                "computation_rule": "label_value - benchmark_return_value" if comparator_kind == "benchmark" else "label_value - industry_return_value",
                "denominator_rule": f"eligible {comparator_kind} rows only",
                "exclusion_count": 0,
                "quarantine_count": 0,
                "overclaim_guard": "report-only; not strategy validation",
                "report_only": True,
                "diagnostic_only": True,
            }
        )
    return rows


def _summary_rows(result_rows: pd.DataFrame) -> pd.DataFrame:
    if result_rows.empty:
        return _empty_artifact_frame("summary")
    rows = []
    for metric_name, group in result_rows.groupby("metric_name", sort=True):
        rows.append(
            {
                "metric_extension_run_id": "",
                "metric_name": metric_name,
                "metric_value": float(group["metric_value"].mean()),
                "numerator_count": int(group["numerator_count"].sum()),
                "denominator_count": int(group["denominator_count"].iloc[0]),
                "interpretation": "report-only relative return over bounded sample",
                "limitation": "not strategy validation, not training_result, not trading",
                "report_only": True,
                "diagnostic_only": True,
            }
        )
    return pd.DataFrame(rows)


def _metadata(result: MetricExtensionResult) -> dict[str, Any]:
    payload = {
        "metric_extension_run_id": result.metric_extension_run_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "execution_status": result.status,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "source_metric_computation_run_id": result.source_metric_computation_run_id,
        "source_metric_computation_artifact_path": result.source_metric_computation_artifact_path,
        "source_metric_computation_status": result.source_metric_computation_status,
        "source_metric_computation_health_status": result.source_metric_computation_health_status,
        "source_metric_evaluation_planning_run_id": result.source_metric_evaluation_planning_run_id,
        "source_metric_evaluation_status": result.source_metric_evaluation_status,
        "source_metric_evaluation_health_status": result.source_metric_evaluation_health_status,
        "source_training_evaluation_run_id": result.source_training_evaluation_run_id,
        "source_training_evaluation_status": result.source_training_evaluation_status,
        "source_training_evaluation_health_status": result.source_training_evaluation_health_status,
        "source_forward_return_label_run_id": result.source_forward_return_label_run_id,
        "source_forward_return_label_status": result.source_forward_return_label_status,
        "source_forward_return_label_health_status": result.source_forward_return_label_health_status,
        "source_replay_decision_freeze_run_id": result.source_replay_decision_freeze_run_id,
        "source_replay_decision_freeze_status": result.source_replay_decision_freeze_status,
        "source_replay_decision_freeze_health_status": result.source_replay_decision_freeze_health_status,
        "allowed_extension_metric_set": result.allowed_extension_metric_set,
        "requested_extension_metric_set": result.requested_extension_metric_set,
        "unsupported_metrics_requested": result.unsupported_metrics_requested,
        "sample_row_count": result.sample_row_count,
        "eligible_sample_count": result.eligible_sample_count,
        "quarantined_sample_count": result.quarantined_sample_count,
        "benchmark_mapping_row_count": result.benchmark_mapping_row_count,
        "industry_mapping_row_count": result.industry_mapping_row_count,
        "benchmark_denominator_count": result.benchmark_denominator_count,
        "industry_denominator_count": result.industry_denominator_count,
        "ready_for_metric_extension": result.ready_for_metric_extension,
        "metric_extension_executed": result.metric_extension_executed,
        "metric_extension_report_created": result.metric_extension_report_created,
        "extended_metric_result_rows_created": result.extended_metric_result_rows_created,
        "extended_metric_summary_created": result.extended_metric_summary_created,
        "extended_metrics_computed": result.extended_metrics_computed,
        "benchmark_relative_return_created": result.benchmark_relative_return_created,
        "industry_relative_return_created": result.industry_relative_return_created,
        "artifact_path": result.artifact_path,
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update({field: False for field in FORBIDDEN_FALSE_FIELDS})
    return payload


def _safety_flags(result: MetricExtensionResult) -> dict[str, bool]:
    return {
        "extended_metrics_computed": result.extended_metrics_computed,
        "extended_metric_result_rows_created": result.extended_metric_result_rows_created,
        "metric_extension_report_created": result.metric_extension_report_created,
        "benchmark_relative_return_created": result.benchmark_relative_return_created,
        "industry_relative_return_created": result.industry_relative_return_created,
        "report_only": True,
        "diagnostic_only": True,
    } | {field: False for field in FORBIDDEN_FALSE_FIELDS}


def _render_report(result: MetricExtensionResult) -> str:
    return (
        "# Metric Extension Phase 1 Report\n\n"
        f"- metric_extension_run_id: {result.metric_extension_run_id}\n"
        f"- status: {result.status}\n"
        f"- workflow_stage: {result.workflow_stage}\n"
        f"- ready_for_metric_extension: {result.ready_for_metric_extension}\n"
        f"- extended_metrics_computed: {result.extended_metrics_computed}\n"
        f"- extended_metric_result_rows_created: {result.extended_metric_result_rows_created}\n"
        f"- sample_row_count: {result.sample_row_count}\n"
        f"- eligible_sample_count: {result.eligible_sample_count}\n"
        f"- benchmark_denominator_count: {result.benchmark_denominator_count}\n"
        f"- industry_denominator_count: {result.industry_denominator_count}\n\n"
        "This workflow creates report-only benchmark/industry relative metrics for a bounded sample "
        "when explicitly allowed. It is not strategy validation, not training_result, not weights, "
        "not model_version, not thresholds, not predictions, not calibrated probabilities, not feature "
        "importance, not stock_profile, not buy-review, not paper approval, not performance validation, "
        "and not trading.\n"
    )


def _recommended_next_task(result: MetricExtensionResult) -> str:
    if result.status == METRIC_EXTENSION_REPORT_CREATED:
        return "Next task: Metric Extension Artifact Views Report-Only v0.1, only after reviewing report-only extension artifacts.\n"
    if result.status == READY_FOR_METRIC_EXTENSION:
        return "Next task: rerun metric-extension with --allow-metric-extension only after reviewing all gates.\n"
    return "Next task: resolve metric extension blockers before creating report-only extended metric result rows.\n"


def _next_action(status: str) -> str:
    if status == NO_METRIC_EXTENSION_INPUT:
        return "Provide exact approval plus immutable metric computation, metric evaluation, dataset, label, freeze, benchmark, and industry artifacts."
    if status == READY_FOR_METRIC_EXTENSION:
        return "Review all gates; optionally rerun with explicit report-only metric extension allowance."
    if status == METRIC_EXTENSION_REPORT_CREATED:
        return "Review report-only benchmark/industry relative metrics; do not treat them as strategy validation."
    return "Resolve the blocking gate before creating report-only extension metrics."


def _input_index_rows(result: MetricExtensionResult, state: dict[str, Any]) -> pd.DataFrame:
    components = [
        ("metric_computation_metadata", result.source_metric_computation_run_id, result.source_metric_computation_health_status),
        ("metric_evaluation_metadata", result.source_metric_evaluation_planning_run_id, result.source_metric_evaluation_health_status),
        ("training_evaluation_metadata", result.source_training_evaluation_run_id, result.source_training_evaluation_health_status),
        ("forward_return_label_metadata", result.source_forward_return_label_run_id, result.source_forward_return_label_health_status),
        ("replay_decision_freeze_metadata", result.source_replay_decision_freeze_run_id, result.source_replay_decision_freeze_health_status),
        ("benchmark_mapping", "benchmark_mapping", "PASS" if result.benchmark_mapping_row_count else ""),
        ("industry_mapping", "industry_mapping", "PASS" if result.industry_mapping_row_count else ""),
    ]
    return pd.DataFrame(
        [
            {
                "metric_extension_run_id": result.metric_extension_run_id,
                "input_component": component,
                "artifact_name": component,
                "artifact_path": "",
                "source_stage": component.replace("_metadata", ""),
                "source_run_id": source_run_id,
                "row_count": result.sample_row_count if component == "training_evaluation_metadata" else 1,
                "required_for_metric_extension": True,
                "immutable_required": True,
                "source_hash_coverage": "PASS",
                "revision_id_coverage": "PASS",
                "available_time_coverage": "PASS",
                "quality_status_coverage": "PASS",
                "health_status": health,
                "report_only": True,
                "diagnostic_only": True,
            }
            for component, source_run_id, health in components
        ]
    )


def _metric_definitions(run_id: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "metric_extension_run_id": run_id,
                "metric_name": "benchmark_relative_return",
                "definition_plain_language": "label_value minus benchmark_return_value",
                "computation_rule": "label_value - benchmark_return_value",
                "allowed_in_phase_1": True,
                "report_only": True,
                "diagnostic_only": True,
            },
            {
                "metric_extension_run_id": run_id,
                "metric_name": "industry_relative_return",
                "definition_plain_language": "label_value minus industry_return_value",
                "computation_rule": "label_value - industry_return_value",
                "allowed_in_phase_1": True,
                "report_only": True,
                "diagnostic_only": True,
            },
        ]
    )


def _return_fields_used(run_id: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "metric_extension_run_id": run_id,
                "metric_name": "benchmark_relative_return",
                "label_field": "label_value",
                "comparison_return_field": "benchmark_return_value",
                "report_only": True,
                "diagnostic_only": True,
            },
            {
                "metric_extension_run_id": run_id,
                "metric_name": "industry_relative_return",
                "label_field": "label_value",
                "comparison_return_field": "industry_return_value",
                "report_only": True,
                "diagnostic_only": True,
            },
        ]
    )


def _gate_frame(gates: list[MetricExtensionGateResult], gate_group: str) -> pd.DataFrame:
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
        "result_rows": [
            "metric_extension_run_id",
            "source_metric_computation_run_id",
            "source_metric_evaluation_planning_run_id",
            "source_training_evaluation_run_id",
            "source_forward_return_label_run_id",
            "source_replay_decision_freeze_run_id",
            "replay_decision_id",
            "forward_return_label_id",
            "symbol",
            "replay_as_of_date",
            "split_role",
            "label_name",
            "horizon_trading_days",
            "metric_name",
            "metric_value",
            "numerator_count",
            "denominator_count",
            "benchmark_id",
            "benchmark_name",
            "industry_id",
            "industry_name",
            "sample_scope",
            "computation_rule",
            "denominator_rule",
            "exclusion_count",
            "quarantine_count",
            "overclaim_guard",
            "report_only",
            "diagnostic_only",
        ],
        "summary": [
            "metric_extension_run_id",
            "metric_name",
            "metric_value",
            "numerator_count",
            "denominator_count",
            "interpretation",
            "limitation",
            "report_only",
            "diagnostic_only",
        ],
        "sample_scope_used": ["scope_item", "report_only", "diagnostic_only"],
        "denominator_rules_used": ["metric_name", "denominator_scope", "report_only", "diagnostic_only"],
        "benchmark_mapping_used": list(BENCHMARK_REQUIRED_COLUMNS),
        "industry_mapping_used": list(INDUSTRY_REQUIRED_COLUMNS),
    }
    return pd.DataFrame(columns=columns.get(key, ["metric_extension_run_id", "report_only", "diagnostic_only"]))


def _blocked(state: dict[str, Any], status: str, group: str, gate_name: str, reason: str, path: Path | None) -> dict[str, Any]:
    state["status"] = status
    state["gate_results"].append(_gate(group, gate_name, status, False, reason, path))
    return state


def _gate(gate_group: str, gate_name: str, status: str, passed: bool, blocker_reason: str, evidence_path: Path | None = None) -> MetricExtensionGateResult:
    return MetricExtensionGateResult(
        gate_group=gate_group,
        gate_name=gate_name,
        status=status,
        passed=passed,
        blocker_reason=blocker_reason,
        evidence_path=str(evidence_path or ""),
    )


def _approval_valid(text: str) -> bool:
    normalized = " ".join(text.strip().replace("鈥淚", "I").replace("鈥?", "").split())
    exact = " ".join(EXACT_METRIC_EXTENSION_APPROVAL_TEXT.split())
    if normalized == exact:
        return True
    required_fragments = [
        "Metric Extension Implementation phase 1",
        "report-only metric extension",
        "benchmark_relative_return",
        "industry_relative_return",
        "must validate benchmark mapping",
        "fail closed",
        "must not create training_result",
        "must not create model_version",
        "must not create predictions",
        "must not create stock_profile",
        "must not claim strategy performance validation",
        "or trade",
    ]
    return all(fragment in normalized for fragment in required_fragments)


def _request_block_status(request: dict[str, Any]) -> str | None:
    requested = {str(item) for item in request.get("requested_extension_metric_set", ALLOWED_EXTENSION_METRIC_SET)}
    if not requested <= set(ALLOWED_EXTENSION_METRIC_SET):
        return METRIC_EXTENSION_UNSUPPORTED_METRIC_BLOCKED
    if requested & UNSUPPORTED_METRIC_SET:
        return METRIC_EXTENSION_UNSUPPORTED_METRIC_BLOCKED
    if any(bool(request.get(field, False)) for field in OVERCLAIM_REQUEST_FIELDS):
        return METRIC_EXTENSION_OVERCLAIM_BLOCKED
    if any(bool(request.get(field, False)) for field in SIDE_EFFECT_REQUEST_FIELDS):
        return METRIC_EXTENSION_SIDE_EFFECT_BLOCKED
    return None


def _missing_required_path_status(settings: MetricExtensionSettings) -> tuple[str, str, str, str] | None:
    checks = [
        (settings.metric_computation_health_artifact_path, METRIC_EXTENSION_HEALTH_BLOCKED, "input_lineage", "metric_computation_health", "metric computation health artifact missing"),
        (settings.metric_computation_metadata_path, METRIC_EXTENSION_METRIC_COMPUTATION_INPUT_BLOCKED, "input_lineage", "metric_computation_metadata", "metric computation metadata missing"),
        (settings.metric_computation_result_rows_path, METRIC_EXTENSION_METRIC_COMPUTATION_INPUT_BLOCKED, "input_lineage", "metric_computation_result_rows", "metric computation result rows missing"),
        (settings.metric_computation_summary_path, METRIC_EXTENSION_METRIC_COMPUTATION_INPUT_BLOCKED, "input_lineage", "metric_computation_summary", "metric computation summary missing"),
        (settings.metric_computation_safety_flags_path, METRIC_EXTENSION_METRIC_COMPUTATION_INPUT_BLOCKED, "input_lineage", "metric_computation_safety_flags", "metric computation safety flags missing"),
        (settings.metric_computation_status_artifact_path, METRIC_EXTENSION_METRIC_COMPUTATION_INPUT_BLOCKED, "input_lineage", "metric_computation_status", "metric computation status missing"),
        (settings.metric_evaluation_health_artifact_path, METRIC_EXTENSION_HEALTH_BLOCKED, "input_lineage", "metric_evaluation_health", "metric evaluation health artifact missing"),
        (settings.metric_evaluation_metadata_path, METRIC_EXTENSION_METRIC_EVALUATION_INPUT_BLOCKED, "input_lineage", "metric_evaluation_metadata", "metric evaluation metadata missing"),
        (settings.metric_evaluation_input_index_path, METRIC_EXTENSION_METRIC_EVALUATION_INPUT_BLOCKED, "input_lineage", "metric_evaluation_input_index", "metric evaluation input index missing"),
        (settings.metric_evaluation_sample_scope_path, METRIC_EXTENSION_SAMPLE_SCOPE_BLOCKED, "sample_scope", "sample_scope_contract", "sample scope contract missing"),
        (settings.metric_evaluation_denominator_rules_path, METRIC_EXTENSION_DENOMINATOR_BLOCKED, "denominator", "denominator_contract", "denominator rules missing"),
        (settings.metric_evaluation_safety_flags_path, METRIC_EXTENSION_METRIC_EVALUATION_INPUT_BLOCKED, "input_lineage", "metric_evaluation_safety_flags", "metric evaluation safety flags missing"),
        (settings.metric_evaluation_status_artifact_path, METRIC_EXTENSION_METRIC_EVALUATION_INPUT_BLOCKED, "input_lineage", "metric_evaluation_status", "metric evaluation status missing"),
        (settings.training_evaluation_health_artifact_path, METRIC_EXTENSION_HEALTH_BLOCKED, "input_lineage", "training_evaluation_health", "training evaluation health missing"),
        (settings.training_evaluation_metadata_path, METRIC_EXTENSION_TRAINING_EVALUATION_INPUT_BLOCKED, "input_lineage", "training_evaluation_metadata", "training evaluation metadata missing"),
        (settings.training_evaluation_sample_rows_path, METRIC_EXTENSION_TRAINING_EVALUATION_INPUT_BLOCKED, "sample_scope", "training_evaluation_sample_rows", "training evaluation sample rows missing"),
        (settings.training_evaluation_safety_flags_path, METRIC_EXTENSION_TRAINING_EVALUATION_INPUT_BLOCKED, "input_lineage", "training_evaluation_safety_flags", "training evaluation safety flags missing"),
        (settings.training_evaluation_status_artifact_path, METRIC_EXTENSION_TRAINING_EVALUATION_INPUT_BLOCKED, "input_lineage", "training_evaluation_status", "training evaluation status missing"),
        (settings.forward_return_label_health_artifact_path, METRIC_EXTENSION_HEALTH_BLOCKED, "input_lineage", "forward_label_health", "forward label health missing"),
        (settings.forward_return_label_metadata_path, METRIC_EXTENSION_FORWARD_LABEL_INPUT_BLOCKED, "input_lineage", "forward_label_metadata", "forward label metadata missing"),
        (settings.forward_return_label_rows_path, METRIC_EXTENSION_FORWARD_LABEL_INPUT_BLOCKED, "input_lineage", "forward_label_rows", "forward label rows missing"),
        (settings.forward_return_label_status_artifact_path, METRIC_EXTENSION_FORWARD_LABEL_INPUT_BLOCKED, "input_lineage", "forward_label_status", "forward label status missing"),
        (settings.replay_decision_freeze_health_artifact_path, METRIC_EXTENSION_HEALTH_BLOCKED, "input_lineage", "replay_freeze_health", "replay freeze health missing"),
        (settings.replay_decision_freeze_metadata_path, METRIC_EXTENSION_REPLAY_FREEZE_INPUT_BLOCKED, "input_lineage", "replay_freeze_metadata", "replay freeze metadata missing"),
        (settings.replay_decision_freeze_rows_path, METRIC_EXTENSION_REPLAY_FREEZE_INPUT_BLOCKED, "input_lineage", "replay_freeze_rows", "replay freeze rows missing"),
        (settings.replay_decision_freeze_status_artifact_path, METRIC_EXTENSION_REPLAY_FREEZE_INPUT_BLOCKED, "input_lineage", "replay_freeze_status", "replay freeze status missing"),
        (settings.benchmark_mapping_path, METRIC_EXTENSION_BENCHMARK_MAPPING_BLOCKED, "benchmark_mapping", "benchmark_mapping", "benchmark mapping missing"),
        (settings.benchmark_return_rows_path, METRIC_EXTENSION_BENCHMARK_MAPPING_BLOCKED, "benchmark_mapping", "benchmark_return_rows", "benchmark return rows missing"),
        (settings.industry_mapping_path, METRIC_EXTENSION_INDUSTRY_MAPPING_BLOCKED, "industry_mapping", "industry_mapping", "industry mapping missing"),
        (settings.industry_return_rows_path, METRIC_EXTENSION_INDUSTRY_MAPPING_BLOCKED, "industry_mapping", "industry_return_rows", "industry return rows missing"),
        (settings.leakage_evidence_bundle_path, METRIC_EXTENSION_LEAKAGE_BLOCKED, "leakage_guard", "future_leakage", "leakage evidence bundle missing"),
        (settings.overclaim_evidence_bundle_path, METRIC_EXTENSION_OVERCLAIM_BLOCKED, "overclaim_guard", "overclaim_flags", "overclaim evidence bundle missing"),
        (settings.side_effect_evidence_bundle_path, METRIC_EXTENSION_SIDE_EFFECT_BLOCKED, "side_effect_guard", "side_effect_flags", "side-effect evidence bundle missing"),
    ]
    for path, status, group, gate, reason in checks:
        if not _path_exists(path):
            return status, group, gate, reason
    return None


def _source_status_check(
    name: str,
    metadata: dict[str, Any],
    status_path: Path | None,
    health_path: Path | None,
    expected_status: str,
    block_status: str,
) -> tuple[str, str, str, Path | None] | None:
    health = _status_value(health_path)
    if health != "PASS":
        return METRIC_EXTENSION_HEALTH_BLOCKED, f"{name}_health", f"{name} health is not PASS", health_path
    metadata_statuses = [
        str(metadata.get(field, ""))
        for field in ["status", "execution_status", "workflow_stage"]
        if str(metadata.get(field, "")) != ""
    ]
    status_value = _status_value(status_path)
    if status_value and status_value != expected_status:
        return block_status, f"{name}_status", f"{name} status is not {expected_status}", status_path
    if metadata_statuses and any(value != expected_status for value in metadata_statuses):
        return block_status, f"{name}_metadata_status", f"{name} metadata status is not {expected_status}", status_path
    return None


def _load_comparator_frame(mapping_path: Path | None, return_rows_path: Path | None, prefix: str) -> pd.DataFrame:
    mapping = _read_csv(mapping_path)
    returns = _read_csv(return_rows_path)
    if mapping_path == return_rows_path or returns.empty:
        return mapping
    key = ["symbol", "replay_as_of_date", "horizon_trading_days"]
    value_column = f"{prefix}_return_value"
    columns_to_add = [column for column in returns.columns if column not in mapping.columns or column in key or column == value_column]
    return mapping.merge(returns[columns_to_add], on=key, how="left")


def _coverage_pass(sample_rows: pd.DataFrame) -> bool:
    for column in ["source_hash_coverage", "revision_id_coverage", "available_time_coverage", "quality_status_coverage"]:
        if not sample_rows[column].astype(str).str.upper().eq("PASS").all():
            return False
    return True


def _benchmark_lineage_pass(frame: pd.DataFrame) -> bool:
    return (
        frame["benchmark_available_time"].astype(str).str.len().gt(0).all()
        and frame["benchmark_source_hash"].astype(str).str.len().gt(0).all()
        and frame["benchmark_revision_id"].astype(str).str.len().gt(0).all()
        and frame["benchmark_quality_status"].astype(str).str.upper().eq("PASS").all()
    )


def _industry_lineage_pass(frame: pd.DataFrame) -> bool:
    return (
        frame["industry_classification_available_time"].astype(str).str.len().gt(0).all()
        and frame["industry_return_available_time"].astype(str).str.len().gt(0).all()
        and frame["industry_source_hash"].astype(str).str.len().gt(0).all()
        and frame["industry_revision_id"].astype(str).str.len().gt(0).all()
        and frame["industry_quality_status"].astype(str).str.upper().eq("PASS").all()
    )


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _has_any_input(settings: MetricExtensionSettings) -> bool:
    return any(
        _path_exists(path)
        for path in [
            settings.approval_manifest_path,
            settings.metric_extension_request_manifest_path,
            settings.metric_computation_metadata_path,
            settings.training_evaluation_sample_rows_path,
            settings.benchmark_mapping_path,
            settings.industry_mapping_path,
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
    if "metric_extension_run_id" in frame.columns:
        frame = frame.copy()
        frame.loc[:, "metric_extension_run_id"] = path.parent.name
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


def _path_exists(path: Path | None) -> bool:
    return path is not None and Path(path).exists()


def _assert_manual_diagnostics_output(output_dir: Path) -> None:
    parts = {part.lower() for part in output_dir.parts}
    if "manual_diagnostics" not in parts:
        raise ValueError("metric-extension output_dir must be under outputs/reports/manual_diagnostics")


def _stable_id(settings: MetricExtensionSettings) -> str:
    payload = {
        "approval_manifest_path": str(settings.approval_manifest_path or ""),
        "metric_computation_metadata_path": str(settings.metric_computation_metadata_path or ""),
        "metric_evaluation_metadata_path": str(settings.metric_evaluation_metadata_path or ""),
        "training_evaluation_metadata_path": str(settings.training_evaluation_metadata_path or ""),
        "allow_metric_extension": settings.allow_metric_extension,
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]

