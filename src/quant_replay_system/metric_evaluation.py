"""Report-only metric/evaluation phase 1 structural planning workflow."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_METRIC_EVALUATION_INPUT = "NO_METRIC_EVALUATION_INPUT"
METRIC_EVALUATION_INPUT_FOUND = "METRIC_EVALUATION_INPUT_FOUND"
METRIC_EVALUATION_APPROVAL_BLOCKED = "METRIC_EVALUATION_APPROVAL_BLOCKED"
METRIC_EVALUATION_DATASET_INPUT_BLOCKED = "METRIC_EVALUATION_DATASET_INPUT_BLOCKED"
METRIC_EVALUATION_DATASET_HEALTH_BLOCKED = "METRIC_EVALUATION_DATASET_HEALTH_BLOCKED"
METRIC_EVALUATION_LINEAGE_BLOCKED = "METRIC_EVALUATION_LINEAGE_BLOCKED"
METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED = "METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED"
METRIC_EVALUATION_DEFINITION_BLOCKED = "METRIC_EVALUATION_DEFINITION_BLOCKED"
METRIC_EVALUATION_COMPUTATION_BLOCKED = "METRIC_EVALUATION_COMPUTATION_BLOCKED"
METRIC_EVALUATION_RESULT_ROWS_BLOCKED = "METRIC_EVALUATION_RESULT_ROWS_BLOCKED"
METRIC_EVALUATION_LEAKAGE_BLOCKED = "METRIC_EVALUATION_LEAKAGE_BLOCKED"
METRIC_EVALUATION_SIDE_EFFECT_BLOCKED = "METRIC_EVALUATION_SIDE_EFFECT_BLOCKED"
METRIC_EVALUATION_OVERCLAIM_BLOCKED = "METRIC_EVALUATION_OVERCLAIM_BLOCKED"
READY_FOR_METRIC_EVALUATION_PLANNING_ARTIFACTS = "READY_FOR_METRIC_EVALUATION_PLANNING_ARTIFACTS"
METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED = "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED"

EXACT_METRIC_EVALUATION_APPROVAL_TEXT = (
    "I explicitly authorize implementation of metric/evaluation core phase 1 only, "
    "limited to report-only metadata/input-index/metric-definition/sample-scope/health-status/"
    "research-status planning artifacts. It may create report-only structural metric/evaluation "
    "artifacts from immutable TRAINING_EVALUATION_DATASET_CREATED artifacts. It must not compute "
    "metrics, create metric/evaluation result rows, create training_result, train weights, create "
    "model_version, optimize thresholds, create predictions, create calibrated probabilities, create "
    "feature importance, create stock_profile, generate buy-review eligibility, apply paper approval, "
    "claim strategy performance validation, integrate broker/order/message, or trade."
)

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/metric_evaluation_v0_1")

ARTIFACT_FILES = {
    "metadata": "metric_evaluation_metadata.json",
    "report": "metric_evaluation_report.md",
    "input_index": "metric_evaluation_input_index.csv",
    "metric_definitions": "metric_evaluation_metric_definitions.csv",
    "sample_scope": "metric_evaluation_sample_scope.csv",
    "denominator_rules": "metric_evaluation_denominator_rules.csv",
    "split_window_plan": "metric_evaluation_split_window_plan.csv",
    "benchmark_industry_plan": "metric_evaluation_benchmark_industry_plan.csv",
    "health_status_plan": "metric_evaluation_health_status_plan.csv",
    "research_status_plan": "metric_evaluation_research_status_plan.json",
    "safety_flags": "metric_evaluation_safety_flags.json",
    "precondition_results": "metric_evaluation_precondition_results.csv",
    "approval_results": "metric_evaluation_approval_results.csv",
    "input_lineage_results": "metric_evaluation_input_lineage_results.csv",
    "dataset_scope_results": "metric_evaluation_dataset_scope_results.csv",
    "metric_definition_results": "metric_evaluation_metric_definition_results.csv",
    "computation_exclusion_results": "metric_evaluation_computation_exclusion_results.csv",
    "leakage_guard_results": "metric_evaluation_leakage_guard_results.csv",
    "side_effect_guard_results": "metric_evaluation_side_effect_guard_results.csv",
    "overclaim_guard_results": "metric_evaluation_overclaim_guard_results.csv",
    "recommended_next_task": "recommended_next_task.md",
}

FORBIDDEN_FALSE_FIELDS = [
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

RESULT_ROW_REQUEST_FIELDS = {"metric_result_rows_requested", "metric_evaluation_results_requested", "evaluation_result_summary_requested"}
COMPUTATION_REQUEST_FIELDS = {"metric_computation_requested"}
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
    "metric_evaluation_not_metrics_computed",
    "metric_evaluation_not_result_rows",
    "metric_evaluation_not_training_result",
    "metric_evaluation_not_model_weights",
    "metric_evaluation_not_model_version",
    "metric_evaluation_not_stock_profile",
    "metric_evaluation_not_buy_review",
    "metric_evaluation_not_paper_approval",
    "metric_evaluation_not_performance_validation",
    "metric_evaluation_not_trading",
}

SAMPLE_REQUIRED_COLUMNS = {
    "training_evaluation_row_id",
    "replay_decision_id",
    "replay_decision_freeze_run_id",
    "forward_return_label_run_id",
    "symbol",
    "replay_as_of_date",
    "label_name",
    "label_value",
    "split_role",
}

FUTURE_METRICS = [
    "sample_count",
    "label_coverage",
    "hit_rate",
    "average_return",
    "median_return",
    "benchmark_relative_return",
    "industry_relative_return",
    "max_drawdown",
    "max_runup",
    "false_positive_cost",
    "false_negative_opportunity_cost",
    "turnover",
    "slippage_sensitivity",
    "regime_robustness",
    "confidence_interval",
    "out_of_sample_metric",
    "information_coefficient",
    "rank_information_coefficient",
    "sharpe_like_metric",
]


@dataclass(frozen=True)
class MetricEvaluationSettings:
    approval_manifest_path: Path | None = None
    metric_evaluation_request_manifest_path: Path | None = None
    training_evaluation_metadata_path: Path | None = None
    training_evaluation_dataset_index_path: Path | None = None
    training_evaluation_sample_rows_path: Path | None = None
    training_evaluation_label_coverage_report_path: Path | None = None
    training_evaluation_split_plan_path: Path | None = None
    training_evaluation_feature_plan_path: Path | None = None
    training_evaluation_label_plan_path: Path | None = None
    training_evaluation_safety_flags_path: Path | None = None
    training_evaluation_status_artifact_path: Path | None = None
    training_evaluation_health_artifact_path: Path | None = None
    metric_definition_request_path: Path | None = None
    sample_scope_request_path: Path | None = None
    denominator_rule_request_path: Path | None = None
    benchmark_industry_request_path: Path | None = None
    leakage_evidence_bundle_path: Path | None = None
    overclaim_evidence_bundle_path: Path | None = None
    side_effect_evidence_bundle_path: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    allow_metric_evaluation_planning_artifacts: bool = False
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class MetricEvaluationGateResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str = ""
    observed_value: str = ""


MetricEvaluationApprovalResult = MetricEvaluationGateResult
MetricEvaluationInputLineageResult = MetricEvaluationGateResult
MetricEvaluationDatasetScopeResult = MetricEvaluationGateResult
MetricEvaluationMetricDefinitionResult = MetricEvaluationGateResult
MetricEvaluationComputationExclusionResult = MetricEvaluationGateResult
MetricEvaluationLeakageGuardResult = MetricEvaluationGateResult
MetricEvaluationSideEffectGuardResult = MetricEvaluationGateResult
MetricEvaluationOverclaimResult = MetricEvaluationGateResult


@dataclass(frozen=True)
class MetricEvaluationResult:
    metric_evaluation_run_id: str
    status: str
    workflow_stage: str
    ready_for_metric_evaluation_planning_artifacts: bool
    metric_evaluation_executed: bool
    metric_evaluation_planning_artifacts_created: bool
    metric_evaluation_input_index_created: bool
    metric_definitions_created: bool
    sample_scope_created: bool
    denominator_rules_created: bool
    health_status_plan_created: bool
    research_status_plan_created: bool
    artifact_path: str
    source_training_evaluation_run_id: str = ""
    source_training_evaluation_artifact_path: str = ""
    source_training_evaluation_status: str = ""
    source_training_evaluation_health_status: str = ""
    source_forward_return_label_run_id: str = ""
    source_replay_decision_freeze_run_id: str = ""
    training_evaluation_dataset_artifacts_created: bool = False
    training_evaluation_sample_row_count: int = 0
    training_evaluation_label_row_count: int = 0
    symbol_count: int = 0
    label_name_set: str = ""
    metric_definition_count: int = 0
    sample_scope_row_count: int = 0
    denominator_rule_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    next_action: str = ""
    report_only: bool = True
    diagnostic_only: bool = True
    artifact_paths: dict[str, Path] = field(default_factory=dict)
    gate_results: list[MetricEvaluationGateResult] = field(default_factory=list)
    metrics_computed: bool = False
    metric_result_rows_created: bool = False
    metric_evaluation_results_created: bool = False
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


def run_metric_evaluation(settings: MetricEvaluationSettings | None = None) -> MetricEvaluationResult:
    settings = settings or MetricEvaluationSettings()
    output_root = Path(settings.output_dir)
    _assert_manual_diagnostics_output(output_root)
    run_id = _stable_id(settings)
    artifact_dir = output_root / run_id
    artifact_paths = {"artifact_dir": artifact_dir} | {
        key: artifact_dir / filename for key, filename in ARTIFACT_FILES.items()
    }
    state = _evaluate(settings)
    status = state["status"]
    created = status == METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED
    ready = status in {READY_FOR_METRIC_EVALUATION_PLANNING_ARTIFACTS, METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED}
    metadata = state["training_metadata"]
    sample_rows = state["sample_rows"]
    result = MetricEvaluationResult(
        metric_evaluation_run_id=run_id,
        status=status,
        workflow_stage="METRIC_EVALUATION_NO_INPUT" if status == NO_METRIC_EVALUATION_INPUT else status,
        ready_for_metric_evaluation_planning_artifacts=ready,
        metric_evaluation_executed=created,
        metric_evaluation_planning_artifacts_created=created,
        metric_evaluation_input_index_created=created,
        metric_definitions_created=created,
        sample_scope_created=created,
        denominator_rules_created=created,
        health_status_plan_created=created,
        research_status_plan_created=created,
        artifact_path=str(artifact_dir),
        source_training_evaluation_run_id=str(metadata.get("training_evaluation_run_id", "")),
        source_training_evaluation_artifact_path=str(Path(settings.training_evaluation_metadata_path).parent if settings.training_evaluation_metadata_path else ""),
        source_training_evaluation_status=str(metadata.get("status", metadata.get("execution_status", ""))),
        source_training_evaluation_health_status=str(metadata.get("health_status", "")),
        source_forward_return_label_run_id=str(metadata.get("source_forward_return_label_run_id", "")),
        source_replay_decision_freeze_run_id=str(metadata.get("source_replay_decision_freeze_run_id", "")),
        training_evaluation_dataset_artifacts_created=bool(metadata.get("training_evaluation_dataset_artifacts_created", False)),
        training_evaluation_sample_row_count=int(metadata.get("dataset_sample_row_count", 0) or 0),
        training_evaluation_label_row_count=int(metadata.get("label_row_count", 0) or 0),
        symbol_count=int(metadata.get("symbol_count", 0) or _symbol_count(sample_rows)),
        label_name_set=str(metadata.get("label_name_set", "")),
        metric_definition_count=len(FUTURE_METRICS) if created else 0,
        sample_scope_row_count=len(_sample_scope_rows(run_id, metadata)) if created else 0,
        denominator_rule_count=len(FUTURE_METRICS) if created else 0,
        blocker_count=0 if ready else 1 if status != NO_METRIC_EVALUATION_INPUT else 0,
        warning_count=0,
        next_action=_next_action(status),
        artifact_paths=artifact_paths,
        gate_results=state["gate_results"],
    )
    if settings.write_artifacts:
        write_metric_evaluation_artifacts(result, state)
    return result


def write_metric_evaluation_artifacts(result: MetricEvaluationResult, state: dict[str, Any] | None = None) -> None:
    state = state or {"training_metadata": {}, "dataset_index": pd.DataFrame(), "sample_rows": pd.DataFrame()}
    artifact_dir = result.artifact_paths["artifact_dir"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    result.artifact_paths["metadata"].write_text(json.dumps(_metadata(result), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["safety_flags"].write_text(json.dumps(_safety_flags(), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["research_status_plan"].write_text(json.dumps(_research_status_plan(result), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(_recommended_next_task(result), encoding="utf-8")

    if result.metric_evaluation_planning_artifacts_created:
        _write_csv(result.artifact_paths["input_index"], _input_index_rows(result, state))
        _write_csv(result.artifact_paths["metric_definitions"], _metric_definition_rows())
        _write_csv(result.artifact_paths["sample_scope"], _sample_scope_rows(result.metric_evaluation_run_id, state["training_metadata"]))
        _write_csv(result.artifact_paths["denominator_rules"], _denominator_rule_rows(result.metric_evaluation_run_id))
        _write_csv(result.artifact_paths["split_window_plan"], _split_window_rows(result.metric_evaluation_run_id))
        _write_csv(result.artifact_paths["benchmark_industry_plan"], _benchmark_industry_rows(result.metric_evaluation_run_id))
        _write_csv(result.artifact_paths["health_status_plan"], _health_status_rows())
    else:
        for key in [
            "input_index",
            "metric_definitions",
            "sample_scope",
            "denominator_rules",
            "split_window_plan",
            "benchmark_industry_plan",
            "health_status_plan",
        ]:
            _write_csv(result.artifact_paths[key], _empty_artifact_frame(key))

    gates = pd.DataFrame([asdict(gate) for gate in result.gate_results])
    for key in [
        "precondition_results",
        "approval_results",
        "input_lineage_results",
        "dataset_scope_results",
        "metric_definition_results",
        "computation_exclusion_results",
        "leakage_guard_results",
        "side_effect_guard_results",
        "overclaim_guard_results",
    ]:
        prefix = key.replace("_results", "").split("_")[0]
        subset = gates[gates["gate_group"].str.startswith(prefix)] if not gates.empty else gates
        _write_csv(result.artifact_paths[key], subset if not subset.empty else _empty_gate_frame(key))


def _evaluate(settings: MetricEvaluationSettings) -> dict[str, Any]:
    gate_results: list[MetricEvaluationGateResult] = []
    state: dict[str, Any] = {
        "status": NO_METRIC_EVALUATION_INPUT,
        "training_metadata": {},
        "dataset_index": pd.DataFrame(),
        "sample_rows": pd.DataFrame(),
        "gate_results": gate_results,
    }
    if not _has_any_input(settings):
        gate_results.append(_gate("precondition", "input_presence", NO_METRIC_EVALUATION_INPUT, True, "no input supplied"))
        return state

    approval = _read_json(settings.approval_manifest_path)
    if approval.get("approval_text") != EXACT_METRIC_EVALUATION_APPROVAL_TEXT:
        return _blocked(state, METRIC_EVALUATION_APPROVAL_BLOCKED, "approval", "exact_phase_1_scope", "exact narrow metric/evaluation approval text missing", settings.approval_manifest_path)
    gate_results.append(_gate("approval", "exact_phase_1_scope", "PASS", True, "", settings.approval_manifest_path))

    request = _read_json(settings.metric_evaluation_request_manifest_path)
    request_status = _request_block_status(request)
    if request_status:
        return _blocked(state, request_status, "computation", "request_scope", "request asks outside structural planning phase 1", settings.metric_evaluation_request_manifest_path)

    missing_dataset = _missing_paths(
        [
            settings.training_evaluation_metadata_path,
            settings.training_evaluation_dataset_index_path,
            settings.training_evaluation_sample_rows_path,
            settings.training_evaluation_label_coverage_report_path,
            settings.training_evaluation_split_plan_path,
            settings.training_evaluation_feature_plan_path,
            settings.training_evaluation_label_plan_path,
            settings.training_evaluation_safety_flags_path,
        ]
    )
    if missing_dataset:
        return _blocked(state, METRIC_EVALUATION_DATASET_INPUT_BLOCKED, "input_lineage", "training_evaluation_artifacts", f"missing input artifacts: {missing_dataset}", None)

    metadata = _read_json(settings.training_evaluation_metadata_path)
    state["training_metadata"] = metadata
    if (
        metadata.get("status", metadata.get("execution_status")) != "TRAINING_EVALUATION_DATASET_CREATED"
        or metadata.get("training_evaluation_dataset_artifacts_created") is not True
    ):
        return _blocked(state, METRIC_EVALUATION_DATASET_INPUT_BLOCKED, "input_lineage", "training_evaluation_status", "source is not TRAINING_EVALUATION_DATASET_CREATED", settings.training_evaluation_metadata_path)

    if _status_csv_value(settings.training_evaluation_health_artifact_path) != "PASS":
        return _blocked(state, METRIC_EVALUATION_DATASET_HEALTH_BLOCKED, "input_lineage", "training_evaluation_health", "source health is not PASS", settings.training_evaluation_health_artifact_path)
    if _status_csv_value(settings.training_evaluation_status_artifact_path) != "TRAINING_EVALUATION_DATASET_CREATED":
        return _blocked(state, METRIC_EVALUATION_DATASET_HEALTH_BLOCKED, "input_lineage", "training_evaluation_status_artifact", "source status artifact is not dataset-created", settings.training_evaluation_status_artifact_path)

    if not metadata.get("source_replay_decision_freeze_run_id") or not metadata.get("source_forward_return_label_run_id"):
        return _blocked(state, METRIC_EVALUATION_LINEAGE_BLOCKED, "input_lineage", "source_lineage", "source replay or label lineage missing", settings.training_evaluation_metadata_path)
    gate_results.append(_gate("input_lineage", "metadata", "PASS", True, "", settings.training_evaluation_metadata_path))

    dataset_index = _read_csv(settings.training_evaluation_dataset_index_path)
    state["dataset_index"] = dataset_index
    for column in ["source_hash_coverage", "revision_id_coverage", "available_time_coverage", "quality_status_coverage"]:
        if column not in dataset_index.columns or not dataset_index[column].astype(str).str.upper().eq("PASS").all():
            return _blocked(state, METRIC_EVALUATION_LINEAGE_BLOCKED, "input_lineage", column, f"{column} missing or not PASS", settings.training_evaluation_dataset_index_path)
    gate_results.append(_gate("input_lineage", "dataset_index_coverage", "PASS", True, "", settings.training_evaluation_dataset_index_path))

    sample_rows = _read_csv(settings.training_evaluation_sample_rows_path)
    state["sample_rows"] = sample_rows
    missing_columns = SAMPLE_REQUIRED_COLUMNS - set(sample_rows.columns)
    if sample_rows.empty or missing_columns:
        return _blocked(state, METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED, "dataset_scope", "sample_rows_schema", f"missing sample columns/rows: {sorted(missing_columns)}", settings.training_evaluation_sample_rows_path)
    if sample_rows["label_value"].isna().any() or sample_rows["label_value"].astype(str).str.strip().eq("").any():
        return _blocked(state, METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED, "dataset_scope", "label_targets", "sample rows missing label targets", settings.training_evaluation_sample_rows_path)
    if sample_rows["split_role"].isna().any() or sample_rows["split_role"].astype(str).str.strip().eq("").any():
        return _blocked(state, METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED, "dataset_scope", "split_role", "sample rows missing split_role", settings.training_evaluation_sample_rows_path)
    gate_results.append(_gate("dataset_scope", "sample_rows", "PASS", True, "", settings.training_evaluation_sample_rows_path))

    metric_def = _read_json(settings.metric_definition_request_path)
    if metric_def.get("valid_metric_definitions") is not True:
        return _blocked(state, METRIC_EVALUATION_DEFINITION_BLOCKED, "metric_definition", "metric_definition_request", "metric definition request invalid or missing", settings.metric_definition_request_path)
    gate_results.append(_gate("metric_definition", "metric_definition_request", "PASS", True, "", settings.metric_definition_request_path))

    sample_scope = _read_json(settings.sample_scope_request_path)
    if sample_scope.get("valid_sample_scope") is not True:
        return _blocked(state, METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED, "dataset_scope", "sample_scope_request", "sample scope request invalid or missing", settings.sample_scope_request_path)
    if sample_rows["replay_decision_id"].duplicated().any() and sample_scope.get("duplicate_sample_rows_quarantined") is not True:
        return _blocked(state, METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED, "dataset_scope", "duplicate_sample_rows", "duplicate sample rows not quarantined", settings.sample_scope_request_path)
    denominator = _read_json(settings.denominator_rule_request_path)
    if denominator.get("valid_denominator_rules") is not True:
        return _blocked(state, METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED, "dataset_scope", "denominator_rules", "denominator rules invalid or missing", settings.denominator_rule_request_path)
    benchmark = _read_json(settings.benchmark_industry_request_path)
    if benchmark.get("valid_benchmark_industry_plan") is not True:
        return _blocked(state, METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED, "dataset_scope", "benchmark_industry", "benchmark/industry plan invalid or missing", settings.benchmark_industry_request_path)
    gate_results.append(_gate("dataset_scope", "scope_rules", "PASS", True, "", settings.sample_scope_request_path))

    if not _path_exists(settings.leakage_evidence_bundle_path):
        return _blocked(state, METRIC_EVALUATION_LEAKAGE_BLOCKED, "leakage", "leakage_bundle", "leakage evidence bundle missing", settings.leakage_evidence_bundle_path)
    leakage = _read_json(settings.leakage_evidence_bundle_path)
    if leakage.get("future_feature_leakage") is True:
        return _blocked(state, METRIC_EVALUATION_LEAKAGE_BLOCKED, "leakage", "leakage_bundle", "future feature leakage flag is true", settings.leakage_evidence_bundle_path)
    gate_results.append(_gate("leakage", "leakage_bundle", "PASS", True, "", settings.leakage_evidence_bundle_path))

    if not _path_exists(settings.side_effect_evidence_bundle_path):
        return _blocked(state, METRIC_EVALUATION_SIDE_EFFECT_BLOCKED, "side_effect", "side_effect_bundle", "side-effect evidence bundle missing", settings.side_effect_evidence_bundle_path)
    side_effect = _read_json(settings.side_effect_evidence_bundle_path)
    if any(side_effect.get(field) is True for field in SIDE_EFFECT_TRUE_FIELDS):
        return _blocked(state, METRIC_EVALUATION_SIDE_EFFECT_BLOCKED, "side_effect", "side_effect_bundle", "side-effect flag is true", settings.side_effect_evidence_bundle_path)
    gate_results.append(_gate("side_effect", "side_effect_bundle", "PASS", True, "", settings.side_effect_evidence_bundle_path))

    overclaim = _read_json(settings.overclaim_evidence_bundle_path)
    if any(overclaim.get(field) is not True for field in REQUIRED_OVERCLAIM_TRUE):
        return _blocked(state, METRIC_EVALUATION_OVERCLAIM_BLOCKED, "overclaim", "overclaim_bundle", "overclaim guard missing", settings.overclaim_evidence_bundle_path)
    gate_results.append(_gate("overclaim", "overclaim_bundle", "PASS", True, "", settings.overclaim_evidence_bundle_path))

    state["status"] = (
        METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED
        if settings.allow_metric_evaluation_planning_artifacts
        else READY_FOR_METRIC_EVALUATION_PLANNING_ARTIFACTS
    )
    return state


def _request_block_status(request: dict[str, Any]) -> str | None:
    if any(request.get(field) is True for field in COMPUTATION_REQUEST_FIELDS):
        return METRIC_EVALUATION_COMPUTATION_BLOCKED
    if any(request.get(field) is True for field in RESULT_ROW_REQUEST_FIELDS):
        return METRIC_EVALUATION_RESULT_ROWS_BLOCKED
    if any(request.get(field) is True for field in SIDE_EFFECT_REQUEST_FIELDS):
        return METRIC_EVALUATION_SIDE_EFFECT_BLOCKED
    if any(request.get(field) is True for field in OVERCLAIM_REQUEST_FIELDS):
        return METRIC_EVALUATION_OVERCLAIM_BLOCKED
    return None


def _metadata(result: MetricEvaluationResult) -> dict[str, Any]:
    payload = {
        "metric_evaluation_run_id": result.metric_evaluation_run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "execution_status": result.status,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "source_training_evaluation_run_id": result.source_training_evaluation_run_id,
        "source_training_evaluation_artifact_path": result.source_training_evaluation_artifact_path,
        "source_training_evaluation_status": result.source_training_evaluation_status,
        "source_training_evaluation_health_status": result.source_training_evaluation_health_status,
        "source_forward_return_label_run_id": result.source_forward_return_label_run_id,
        "source_replay_decision_freeze_run_id": result.source_replay_decision_freeze_run_id,
        "training_evaluation_dataset_artifacts_created": result.training_evaluation_dataset_artifacts_created,
        "training_evaluation_sample_row_count": result.training_evaluation_sample_row_count,
        "training_evaluation_label_row_count": result.training_evaluation_label_row_count,
        "symbol_count": result.symbol_count,
        "label_name_set": result.label_name_set,
        "metric_definition_count": result.metric_definition_count,
        "sample_scope_row_count": result.sample_scope_row_count,
        "denominator_rule_count": result.denominator_rule_count,
        "ready_for_metric_evaluation_planning_artifacts": result.ready_for_metric_evaluation_planning_artifacts,
        "metric_evaluation_executed": result.metric_evaluation_executed,
        "metric_evaluation_planning_artifacts_created": result.metric_evaluation_planning_artifacts_created,
        "metric_evaluation_input_index_created": result.metric_evaluation_input_index_created,
        "metric_definitions_created": result.metric_definitions_created,
        "sample_scope_created": result.sample_scope_created,
        "denominator_rules_created": result.denominator_rules_created,
        "health_status_plan_created": result.health_status_plan_created,
        "research_status_plan_created": result.research_status_plan_created,
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update(_safety_flags())
    return payload


def _safety_flags() -> dict[str, bool]:
    return {field: False for field in FORBIDDEN_FALSE_FIELDS} | {"report_only": True, "diagnostic_only": True}


def _research_status_plan(result: MetricEvaluationResult) -> dict[str, Any]:
    return {
        "latest_metric_evaluation_run_id": result.metric_evaluation_run_id,
        "latest_metric_evaluation_status": result.status,
        "latest_metric_evaluation_health_status": "PLANNED_ONLY",
        "metric_evaluation_planning_artifacts_created": result.metric_evaluation_planning_artifacts_created,
        "metric_computation_executed": False,
        "metric_results_created": False,
        "metrics_computed": False,
        "training_result_created": False,
        "weights_trained": False,
        "model_version_created": False,
        "thresholds_optimized": False,
        "predictions_created": False,
        "calibrated_probabilities_created": False,
        "feature_importance_created": False,
        "stock_profile_created": False,
        "buy_review_allowed": False,
        "approved_for_paper": False,
        "strategy_performance_validated": False,
        "trading_allowed": False,
        "preserve_paper_workflow_ready_priority": True,
    }


def _input_index_rows(result: MetricEvaluationResult, state: dict[str, Any]) -> pd.DataFrame:
    index = state.get("dataset_index", pd.DataFrame())
    components = [
        ("metadata", "training_evaluation_metadata.json", result.source_training_evaluation_artifact_path),
        ("dataset_index", "training_evaluation_dataset_index.csv", ""),
        ("sample_rows", "training_evaluation_sample_rows.csv", ""),
        ("label_coverage", "training_evaluation_label_coverage_report.csv", ""),
        ("split_plan", "training_evaluation_split_plan.csv", ""),
        ("feature_plan", "training_evaluation_feature_plan.csv", ""),
        ("label_plan", "training_evaluation_label_plan.csv", ""),
    ]
    coverage = _coverage_from_index(index)
    return pd.DataFrame(
        [
            {
                "metric_evaluation_run_id": result.metric_evaluation_run_id,
                "input_component": component,
                "artifact_name": name,
                "artifact_path": path,
                "source_stage": "training_evaluation_phase_1",
                "source_run_id": result.source_training_evaluation_run_id,
                "row_count": result.training_evaluation_sample_row_count if component == "sample_rows" else 1,
                "required_for_future_metric_computation": True,
                "immutable_required": True,
                "source_hash_coverage": coverage["source_hash_coverage"],
                "revision_id_coverage": coverage["revision_id_coverage"],
                "available_time_coverage": coverage["available_time_coverage"],
                "quality_status_coverage": coverage["quality_status_coverage"],
                "report_only": True,
                "diagnostic_only": True,
            }
            for component, name, path in components
        ]
    )


def _metric_definition_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "metric_name": name,
                "definition_plain_language": f"Future planning definition for {name}.",
                "numerator": "future_approved_numerator",
                "denominator": "future_approved_denominator",
                "required_inputs": "immutable_training_evaluation_dataset_created_artifacts",
                "computation_allowed_in_current_phase": False,
                "result_rows_allowed_in_current_phase": False,
                "requires_future_exact_approval": True,
                "overclaim_risk": "high" if name not in {"sample_count", "label_coverage"} else "medium",
                "report_only": True,
                "diagnostic_only": True,
            }
            for name in FUTURE_METRICS
        ]
    )


def _sample_scope_rows(run_id: str, metadata: dict[str, Any]) -> pd.DataFrame:
    scopes = [
        "all_dataset_sample_rows",
        "missing_label_rows",
        "invalid_lineage_rows",
        "unsupported_horizon_rows",
        "benchmark_mapping_missing_rows",
        "industry_mapping_missing_rows",
        "duplicate_replay_decision_rows",
    ]
    return pd.DataFrame(
        [
            {
                "metric_evaluation_run_id": run_id,
                "scope_item": scope,
                "source_training_evaluation_run_id": metadata.get("training_evaluation_run_id", ""),
                "source_training_evaluation_component": "training_evaluation_sample_rows",
                "denominator_rule": "future_approved_denominator_only",
                "inclusion_rule": "include only accepted immutable rows",
                "exclusion_rule": "exclude blocked rows",
                "quarantine_rule": "quarantine until reviewed",
                "future_blocker": "SAMPLE_SCOPE_REVIEW_REQUIRED",
                "computation_allowed_in_current_phase": False,
                "report_only": True,
                "diagnostic_only": True,
            }
            for scope in scopes
        ]
    )


def _denominator_rule_rows(run_id: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "metric_evaluation_run_id": run_id,
                "metric_name": name,
                "denominator_scope": "future_approved_scope",
                "include_condition": "accepted immutable source row",
                "exclude_condition": "missing label or lineage blocker",
                "quarantine_condition": "duplicate or unsafe quality",
                "missing_data_rule": "block or exclude with explicit reason",
                "duplicate_rule": "deduplicate by replay_decision_id and label identity",
                "split_role_requirement": "split_role required",
                "computation_allowed_in_current_phase": False,
                "report_only": True,
                "diagnostic_only": True,
            }
            for name in FUTURE_METRICS
        ]
    )


def _split_window_rows(run_id: str) -> pd.DataFrame:
    items = ["train window", "validation window", "test window", "out-of-sample window", "walk-forward window", "embargo period", "replay decision date", "label window", "benchmark window", "industry-relative window"]
    return pd.DataFrame(
        [
            {
                "metric_evaluation_run_id": run_id,
                "split_or_window_item": item,
                "role": "future_metric_planning",
                "future_metric_use": "define metric grouping only",
                "leakage_guard": "no post-decision feature use",
                "required_evidence": "immutable split/window lineage",
                "computation_allowed_in_current_phase": False,
                "notes": "structural planning only",
                "report_only": True,
                "diagnostic_only": True,
            }
            for item in items
        ]
    )


def _benchmark_industry_rows(run_id: str) -> pd.DataFrame:
    items = ["benchmark symbol/index", "industry classification", "industry index/proxy", "benchmark return window", "industry return window", "excess return definition", "missing benchmark handling", "missing industry handling"]
    return pd.DataFrame(
        [
            {
                "metric_evaluation_run_id": run_id,
                "item": item,
                "required_for_future_metric_computation": True,
                "data_requirement": "PIT governed comparator data",
                "leakage_guard": "available_time and revision governance required",
                "missing_data_rule": "block metric or mark unavailable",
                "computation_allowed_in_current_phase": False,
                "notes": "planning only",
                "report_only": True,
                "diagnostic_only": True,
            }
            for item in items
        ]
    )


def _health_status_rows() -> pd.DataFrame:
    rows = [
        ("explicit approval", "approval_valid", "exact phase 1 approval", "approval missing", METRIC_EVALUATION_APPROVAL_BLOCKED),
        ("source health", "source_training_evaluation_health_status", "PASS", "source health not PASS", METRIC_EVALUATION_DATASET_HEALTH_BLOCKED),
        ("lineage", "lineage_complete", "replay and label lineage present", "lineage missing", METRIC_EVALUATION_LINEAGE_BLOCKED),
        ("metric computation", "metrics_computed", "false", "metrics computed", METRIC_EVALUATION_COMPUTATION_BLOCKED),
        ("result rows", "metric_result_rows_created", "false", "result rows created", METRIC_EVALUATION_RESULT_ROWS_BLOCKED),
        ("side effects", "side_effects", "all false", "unsafe side effects", METRIC_EVALUATION_SIDE_EFFECT_BLOCKED),
        ("overclaim", "overclaim_guards", "present", "overclaim guard failed", METRIC_EVALUATION_OVERCLAIM_BLOCKED),
    ]
    return pd.DataFrame(
        [
            {
                "gate_name": gate,
                "future_status_field": field,
                "required_condition": required,
                "unsafe_condition": unsafe,
                "failure_status": failure,
                "current_phase_value": "planned_only",
                "notes": "future health/status planning artifact only",
            }
            for gate, field, required, unsafe, failure in rows
        ]
    )


def _render_report(result: MetricEvaluationResult) -> str:
    return "\n".join(
        [
            "# Metric / Evaluation Phase 1 Report",
            "",
            f"- status: {result.status}",
            f"- metric_evaluation_run_id: {result.metric_evaluation_run_id}",
            f"- ready_for_metric_evaluation_planning_artifacts: {result.ready_for_metric_evaluation_planning_artifacts}",
            f"- metric_evaluation_planning_artifacts_created: {result.metric_evaluation_planning_artifacts_created}",
            "",
            "This is structural planning only: not metrics computed, not metric result rows, "
            "not training_result, not weights, not model_version, not thresholds, not predictions, "
            "not calibrated probabilities, not feature importance, not stock_profile, not buy-review, "
            "not paper approval, not performance validation, and not trading.",
        ]
    )


def _recommended_next_task(result: MetricEvaluationResult) -> str:
    if result.status == METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED:
        return "Next task: add metric/evaluation artifact views only after reviewing structural planning artifacts.\n"
    if result.ready_for_metric_evaluation_planning_artifacts:
        return "Next task: rerun with --allow-metric-evaluation-planning-artifacts only if structural planning artifacts are explicitly needed.\n"
    return "Next task: resolve metric/evaluation gate blockers before creating structural planning artifacts.\n"


def _next_action(status: str) -> str:
    if status == NO_METRIC_EVALUATION_INPUT:
        return "Provide exact approval and immutable TRAINING_EVALUATION_DATASET_CREATED inputs."
    if status == READY_FOR_METRIC_EVALUATION_PLANNING_ARTIFACTS:
        return "Review gates; optionally rerun with explicit structural planning allowance."
    if status == METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED:
        return "Review structural metric/evaluation planning artifacts; do not compute metrics."
    return "Resolve blocker; no metric/evaluation planning artifact should be trusted yet."


def _blocked(state: dict[str, Any], status: str, group: str, gate_name: str, reason: str, path: Path | None) -> dict[str, Any]:
    state["status"] = status
    state["gate_results"].append(_gate(group, gate_name, status, False, reason, path))
    return state


def _gate(gate_group: str, gate_name: str, status: str, passed: bool, blocker_reason: str, evidence_path: Path | None = None) -> MetricEvaluationGateResult:
    return MetricEvaluationGateResult(
        gate_group=gate_group,
        gate_name=gate_name,
        status=status,
        passed=passed,
        blocker_reason=blocker_reason,
        evidence_path=str(evidence_path or ""),
    )


def _has_any_input(settings: MetricEvaluationSettings) -> bool:
    return any(
        _path_exists(path)
        for path in [
            settings.approval_manifest_path,
            settings.metric_evaluation_request_manifest_path,
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


def _empty_gate_frame(key: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "gate_group": key.replace("_results", ""),
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
        "input_index": [
            "metric_evaluation_run_id",
            "input_component",
            "artifact_name",
            "artifact_path",
            "source_stage",
            "source_run_id",
            "row_count",
            "required_for_future_metric_computation",
            "immutable_required",
            "source_hash_coverage",
            "revision_id_coverage",
            "available_time_coverage",
            "quality_status_coverage",
            "report_only",
            "diagnostic_only",
        ],
        "metric_definitions": [
            "metric_name",
            "definition_plain_language",
            "numerator",
            "denominator",
            "required_inputs",
            "computation_allowed_in_current_phase",
            "result_rows_allowed_in_current_phase",
            "requires_future_exact_approval",
            "overclaim_risk",
            "report_only",
            "diagnostic_only",
        ],
        "sample_scope": [
            "metric_evaluation_run_id",
            "scope_item",
            "source_training_evaluation_run_id",
            "source_training_evaluation_component",
            "denominator_rule",
            "inclusion_rule",
            "exclusion_rule",
            "quarantine_rule",
            "future_blocker",
            "computation_allowed_in_current_phase",
            "report_only",
            "diagnostic_only",
        ],
        "denominator_rules": [
            "metric_evaluation_run_id",
            "metric_name",
            "denominator_scope",
            "include_condition",
            "exclude_condition",
            "quarantine_condition",
            "missing_data_rule",
            "duplicate_rule",
            "split_role_requirement",
            "computation_allowed_in_current_phase",
            "report_only",
            "diagnostic_only",
        ],
        "split_window_plan": [
            "metric_evaluation_run_id",
            "split_or_window_item",
            "role",
            "future_metric_use",
            "leakage_guard",
            "required_evidence",
            "computation_allowed_in_current_phase",
            "notes",
            "report_only",
            "diagnostic_only",
        ],
        "benchmark_industry_plan": [
            "metric_evaluation_run_id",
            "item",
            "required_for_future_metric_computation",
            "data_requirement",
            "leakage_guard",
            "missing_data_rule",
            "computation_allowed_in_current_phase",
            "notes",
            "report_only",
            "diagnostic_only",
        ],
        "health_status_plan": [
            "gate_name",
            "future_status_field",
            "required_condition",
            "unsafe_condition",
            "failure_status",
            "current_phase_value",
            "notes",
        ],
    }
    return pd.DataFrame(columns=columns[key])


def _missing_paths(paths: list[Path | None]) -> str:
    return ", ".join(str(path) for path in paths if not _path_exists(path))


def _path_exists(path: Path | None) -> bool:
    return path is not None and Path(path).exists()


def _status_csv_value(path: Path | None) -> str:
    frame = _read_csv(path)
    if frame.empty or "status" not in frame.columns:
        return ""
    return str(frame["status"].iloc[0])


def _coverage_from_index(frame: pd.DataFrame) -> dict[str, str]:
    coverage = {}
    for column in ["source_hash_coverage", "revision_id_coverage", "available_time_coverage", "quality_status_coverage"]:
        coverage[column] = "PASS" if column in frame.columns and frame[column].astype(str).str.upper().eq("PASS").all() else "MISSING"
    return coverage


def _symbol_count(rows: pd.DataFrame) -> int:
    if rows.empty or "symbol" not in rows:
        return 0
    return int(rows["symbol"].astype(str).nunique())


def _assert_manual_diagnostics_output(output_dir: Path) -> None:
    parts = {part.lower() for part in output_dir.parts}
    if "manual_diagnostics" not in parts:
        raise ValueError("metric-evaluation output_dir must be under outputs/reports/manual_diagnostics")


def _stable_id(settings: MetricEvaluationSettings) -> str:
    payload = {
        "approval_manifest_path": str(settings.approval_manifest_path or ""),
        "training_evaluation_metadata_path": str(settings.training_evaluation_metadata_path or ""),
        "allow_metric_evaluation_planning_artifacts": settings.allow_metric_evaluation_planning_artifacts,
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]
