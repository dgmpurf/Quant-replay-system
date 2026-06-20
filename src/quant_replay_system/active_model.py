"""Research-governed active model phase 1 report-only workflow."""

from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_ACTIVE_MODEL_INPUT = "NO_ACTIVE_MODEL_INPUT"
ACTIVE_MODEL_INPUT_FOUND = "ACTIVE_MODEL_INPUT_FOUND"
ACTIVE_MODEL_APPROVAL_BLOCKED = "ACTIVE_MODEL_APPROVAL_BLOCKED"
ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED = "ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED"
ACTIVE_MODEL_TRAINING_RESULT_INPUT_BLOCKED = "ACTIVE_MODEL_TRAINING_RESULT_INPUT_BLOCKED"
ACTIVE_MODEL_TRAINING_RESULT_PLANNING_INPUT_BLOCKED = "ACTIVE_MODEL_TRAINING_RESULT_PLANNING_INPUT_BLOCKED"
ACTIVE_MODEL_METRIC_EXTENSION_INPUT_BLOCKED = "ACTIVE_MODEL_METRIC_EXTENSION_INPUT_BLOCKED"
ACTIVE_MODEL_METRIC_COMPUTATION_INPUT_BLOCKED = "ACTIVE_MODEL_METRIC_COMPUTATION_INPUT_BLOCKED"
ACTIVE_MODEL_METRIC_EVALUATION_INPUT_BLOCKED = "ACTIVE_MODEL_METRIC_EVALUATION_INPUT_BLOCKED"
ACTIVE_MODEL_TRAINING_EVALUATION_INPUT_BLOCKED = "ACTIVE_MODEL_TRAINING_EVALUATION_INPUT_BLOCKED"
ACTIVE_MODEL_FORWARD_LABEL_INPUT_BLOCKED = "ACTIVE_MODEL_FORWARD_LABEL_INPUT_BLOCKED"
ACTIVE_MODEL_REPLAY_FREEZE_INPUT_BLOCKED = "ACTIVE_MODEL_REPLAY_FREEZE_INPUT_BLOCKED"
ACTIVE_MODEL_HEALTH_BLOCKED = "ACTIVE_MODEL_HEALTH_BLOCKED"
ACTIVE_MODEL_LINEAGE_BLOCKED = "ACTIVE_MODEL_LINEAGE_BLOCKED"
ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED = "ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED"
ACTIVE_MODEL_TRAINING_RESULT_ROWS_BLOCKED = "ACTIVE_MODEL_TRAINING_RESULT_ROWS_BLOCKED"
ACTIVE_MODEL_METRIC_EVIDENCE_BLOCKED = "ACTIVE_MODEL_METRIC_EVIDENCE_BLOCKED"
ACTIVE_MODEL_LIMITATIONS_BLOCKED = "ACTIVE_MODEL_LIMITATIONS_BLOCKED"
ACTIVE_MODEL_OVERFIT_WARNING_BLOCKED = "ACTIVE_MODEL_OVERFIT_WARNING_BLOCKED"
ACTIVE_MODEL_SAFETY_FLAG_BLOCKED = "ACTIVE_MODEL_SAFETY_FLAG_BLOCKED"
ACTIVE_MODEL_FORBIDDEN_ARTIFACT_BLOCKED = "ACTIVE_MODEL_FORBIDDEN_ARTIFACT_BLOCKED"
ACTIVE_MODEL_LEAKAGE_BLOCKED = "ACTIVE_MODEL_LEAKAGE_BLOCKED"
ACTIVE_MODEL_SIDE_EFFECT_BLOCKED = "ACTIVE_MODEL_SIDE_EFFECT_BLOCKED"
ACTIVE_MODEL_OVERCLAIM_BLOCKED = "ACTIVE_MODEL_OVERCLAIM_BLOCKED"
READY_FOR_ACTIVE_MODEL = "READY_FOR_ACTIVE_MODEL"
ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED = "ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED"

MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED = "MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED"

EXACT_ACTIVE_MODEL_APPROVAL_TEXT = (
    "I explicitly authorize Active Model Implementation Phase 1 only, and only research-governed active-model "
    "artifacts. It may create active_model_metadata, active_model_pointer, active_model_registry_entry, "
    "active_parameter_pointer, active_model_activation_status, active_model_rollback_plan, active_model_input_index, "
    "active_model_lineage_matrix, active_model_limitations, active_model_overfit_warnings, active_model_safety_flags, "
    "gate reports, and recommended_next_task under outputs/reports/manual_diagnostics only when "
    "MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED and all upstream training, metric, label, and replay freeze "
    "artifacts have complete lineage and PASS health. This phase must not create promoted model, production model, "
    "active thresholds, advisory predictions, active probabilities, stock_profile, buy-review eligibility, paper "
    "approval, strategy performance validation, broker/order/message integration, current-candidates integration, "
    "snapshot integration, signal semantics mutation, or trading. If exact approval, upstream lineage, health, "
    "model weight versioning artifacts, training_result rows, metric evidence, limitations, overfit warnings, safety "
    "flags, leakage guards, side-effect guards, or overclaim guards are missing, it must fail closed."
)

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/active_model_v0_1")

ARTIFACT_FILES = {
    "active_model_metadata": "active_model_metadata.json",
    "report": "active_model_report.md",
    "active_model_pointer": "active_model_pointer.json",
    "active_model_registry_entry": "active_model_registry_entry.json",
    "active_parameter_pointer": "active_parameter_pointer.json",
    "active_model_activation_status": "active_model_activation_status.json",
    "active_model_rollback_plan": "active_model_rollback_plan.md",
    "active_model_input_index": "active_model_input_index.csv",
    "active_model_lineage_matrix": "active_model_lineage_matrix.csv",
    "active_model_limitations": "active_model_limitations.md",
    "active_model_overfit_warnings": "active_model_overfit_warnings.csv",
    "active_model_safety_flags": "active_model_safety_flags.json",
    "active_model_precondition_results": "active_model_precondition_results.csv",
    "active_model_approval_results": "active_model_approval_results.csv",
    "active_model_input_lineage_results": "active_model_input_lineage_results.csv",
    "active_model_model_weight_versioning_input_results": "active_model_model_weight_versioning_input_results.csv",
    "active_model_metric_evidence_results": "active_model_metric_evidence_results.csv",
    "active_model_leakage_guard_results": "active_model_leakage_guard_results.csv",
    "active_model_side_effect_guard_results": "active_model_side_effect_guard_results.csv",
    "active_model_overclaim_guard_results": "active_model_overclaim_guard_results.csv",
    "recommended_next_task": "recommended_next_task.md",
}

SUBSTANTIVE_ARTIFACT_KEYS = {
    "active_model_pointer",
    "active_model_registry_entry",
    "active_parameter_pointer",
    "active_model_activation_status",
    "active_model_rollback_plan",
    "active_model_input_index",
    "active_model_lineage_matrix",
    "active_model_limitations",
    "active_model_overfit_warnings",
}

REQUIRED_METRICS = {
    "sample_count",
    "label_coverage",
    "average_return",
    "median_return",
    "hit_rate",
    "benchmark_relative_return",
    "industry_relative_return",
}

LINEAGE_COLUMNS = {
    "training_result_row_id",
    "replay_decision_id",
    "forward_return_label_id",
    "symbol",
    "replay_as_of_date",
    "split_role",
    "label_name",
    "horizon_trading_days",
    "source_hash",
    "revision_id",
    "available_time",
    "quality_status",
    "report_only",
    "diagnostic_only",
}

REQUIRED_OVERFIT_WARNINGS = {
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
    "calibration overfit",
    "prediction overfit",
    "benchmark mismatch",
    "industry classification drift",
    "survivorship bias",
    "lookahead leakage",
    "paper-overfit risk",
}

SOURCE_MODEL_OVERFIT_WARNINGS = REQUIRED_OVERFIT_WARNINGS - {
    "calibration overfit",
    "prediction overfit",
}

REQUIRED_LIMITATION_PHRASES = {
    "no promoted model",
    "no production model",
    "no active thresholds",
    "no advisory predictions",
    "no active probabilities",
    "no stock_profile",
    "no buy-review",
    "no paper approval",
    "no performance validation",
    "no trading",
}

DOWNSTREAM_FALSE_FIELDS = [
    "promoted_model_created",
    "production_model_created",
    "active_thresholds_created",
    "advisory_predictions_created",
    "active_probabilities_created",
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

FORBIDDEN_ARTIFACT_PATTERNS = {
    "promoted_model*",
    "production_model*",
    "active_threshold*",
    "advisory_prediction*",
    "active_probability*",
    "stock_profile*",
    "buy_review*",
    "paper_approval*",
    "approved_for_paper*",
    "performance_validation*",
    "strategy_performance*",
    "broker*",
    "order*",
    "trade*",
    "message*",
    "current_candidates*",
    "snapshot*",
    "signal_semantics*",
    "scheduler*",
    "cron*",
    "serving*",
}

REQUEST_OVERCLAIM_FIELDS = {
    "promoted_model_requested",
    "production_model_requested",
    "active_thresholds_requested",
    "advisory_predictions_requested",
    "active_probabilities_requested",
    "stock_profile_requested",
    "buy_review_requested",
    "paper_approval_requested",
    "performance_validation_requested",
}

REQUEST_LEAKAGE_FIELDS = {
    "current_candidates_integration_requested",
    "snapshot_build_requested",
    "signal_semantics_mutation_requested",
    "threshold_to_signal_binding_requested",
    "advisory_prediction_display_requested",
}

REQUEST_SIDE_EFFECT_FIELDS = {
    "trading_requested",
    "broker_api_called",
    "order_placed",
    "message_sent",
}

REQUIRED_ACTIVE_MODEL_OVERCLAIM_TRUE = {
    "active_model_research_governed_only",
    "active_model_not_promoted_model",
    "active_model_not_production_model",
    "active_model_not_active_thresholds",
    "active_model_not_advisory_predictions",
    "active_model_not_active_probabilities",
    "active_model_not_stock_profile",
    "active_model_not_buy_review",
    "active_model_not_paper_approval",
    "active_model_not_performance_validation",
    "active_model_not_trading",
}


@dataclass(frozen=True)
class ActiveModelSettings:
    approval_manifest_path: Path | None = None
    active_model_request_manifest_path: Path | None = None
    model_weight_versioning_metadata_path: Path | None = None
    model_weights_reference_path: Path | None = None
    model_version_metadata_path: Path | None = None
    parameter_version_metadata_path: Path | None = None
    threshold_plan_path: Path | None = None
    prediction_rows_path: Path | None = None
    probability_calibration_report_path: Path | None = None
    feature_importance_report_path: Path | None = None
    model_input_index_path: Path | None = None
    model_lineage_matrix_path: Path | None = None
    model_limitations_path: Path | None = None
    model_overfit_warnings_path: Path | None = None
    model_safety_flags_path: Path | None = None
    model_weight_versioning_status_artifact_path: Path | None = None
    model_weight_versioning_health_artifact_path: Path | None = None
    training_result_metadata_path: Path | None = None
    training_result_rows_path: Path | None = None
    training_result_status_artifact_path: Path | None = None
    training_result_health_artifact_path: Path | None = None
    training_result_planning_metadata_path: Path | None = None
    training_result_planning_health_artifact_path: Path | None = None
    metric_extension_metadata_path: Path | None = None
    metric_extension_result_rows_path: Path | None = None
    metric_extension_health_artifact_path: Path | None = None
    metric_computation_metadata_path: Path | None = None
    metric_computation_result_rows_path: Path | None = None
    metric_computation_health_artifact_path: Path | None = None
    metric_evaluation_metadata_path: Path | None = None
    metric_evaluation_health_artifact_path: Path | None = None
    training_evaluation_metadata_path: Path | None = None
    training_evaluation_sample_rows_path: Path | None = None
    training_evaluation_health_artifact_path: Path | None = None
    forward_return_label_metadata_path: Path | None = None
    forward_return_label_rows_path: Path | None = None
    forward_return_label_health_artifact_path: Path | None = None
    replay_decision_freeze_metadata_path: Path | None = None
    replay_decision_freeze_rows_path: Path | None = None
    replay_decision_freeze_health_artifact_path: Path | None = None
    leakage_evidence_bundle_path: Path | None = None
    overclaim_evidence_bundle_path: Path | None = None
    side_effect_evidence_bundle_path: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    allow_active_model: bool = False
    write_artifacts: bool = True
    research_governed: bool = True
    diagnostic_output: bool = True


@dataclass(frozen=True)
class ActiveModelGateResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str = ""
    observed_value: str = ""


ActiveModelApprovalResult = ActiveModelGateResult
ActiveModelInputLineageResult = ActiveModelGateResult
ActiveModelMetricEvidenceResult = ActiveModelGateResult
ActiveModelLeakageGuardResult = ActiveModelGateResult
ActiveModelSideEffectGuardResult = ActiveModelGateResult
ActiveModelOverclaimGuardResult = ActiveModelGateResult


@dataclass(frozen=True)
class ActiveModelResult:
    active_model_run_id: str
    status: str
    workflow_stage: str
    ready_for_active_model: bool
    active_model_executed: bool
    active_model_artifacts_created: bool
    artifact_path: str
    source_model_workflow_run_id: str = ""
    source_model_weight_versioning_status: str = ""
    source_model_weight_versioning_health_status: str = ""
    model_weight_reference_id: str = ""
    model_version_id: str = ""
    parameter_version_id: str = ""
    source_training_result_run_id: str = ""
    source_training_result_status: str = ""
    source_training_result_health_status: str = ""
    source_training_result_planning_run_id: str = ""
    source_training_result_planning_status: str = ""
    source_training_result_planning_health_status: str = ""
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
    training_result_row_count: int = 0
    eligible_training_result_row_count: int = 0
    metric_evidence_names_present: str = ""
    metric_evidence_reference_count: int = 0
    active_model_pointer_created: bool = False
    active_model_registry_entry_created: bool = False
    active_parameter_pointer_created: bool = False
    active_model_activation_status_created: bool = False
    active_model_rollback_plan_created: bool = False
    active_model_input_index_created: bool = False
    active_model_lineage_matrix_created: bool = False
    active_model_limitations_created: bool = False
    active_model_overfit_warnings_created: bool = False
    active_model_safety_flags_created: bool = True
    blocker_count: int = 0
    warning_count: int = 0
    next_action: str = ""
    research_governed: bool = True
    diagnostic_output: bool = True
    artifact_paths: dict[str, Path] = field(default_factory=dict)
    gate_results: list[ActiveModelGateResult] = field(default_factory=list)
    promoted_model_created: bool = False
    production_model_created: bool = False
    active_thresholds_created: bool = False
    advisory_predictions_created: bool = False
    active_probabilities_created: bool = False
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


def run_active_model(settings: ActiveModelSettings | None = None) -> ActiveModelResult:
    settings = settings or ActiveModelSettings()
    output_root = Path(settings.output_dir)
    _assert_manual_diagnostics_output(output_root)
    run_id = _stable_id(settings)
    artifact_dir = output_root / run_id
    artifact_paths = {"artifact_dir": artifact_dir} | {
        key: artifact_dir / filename for key, filename in ARTIFACT_FILES.items()
    }
    state = _evaluate(settings)
    created = state["status"] == ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED
    ready = state["status"] in {READY_FOR_ACTIVE_MODEL, ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED}
    model_meta = state.get("model_weight_versioning_metadata", {})
    rows = state.get("training_result_rows", [])
    evidence_names = sorted(state.get("metric_evidence_names", []))

    result = ActiveModelResult(
        active_model_run_id=run_id,
        status=state["status"],
        workflow_stage="ACTIVE_MODEL_NO_INPUT" if state["status"] == NO_ACTIVE_MODEL_INPUT else state["status"],
        ready_for_active_model=ready,
        active_model_executed=created,
        active_model_artifacts_created=created,
        artifact_path=str(artifact_dir),
        source_model_workflow_run_id=str(model_meta.get("model_workflow_run_id", "")),
        source_model_weight_versioning_status=_source_status(model_meta),
        source_model_weight_versioning_health_status=_status_value(settings.model_weight_versioning_health_artifact_path),
        model_weight_reference_id=str(state.get("model_weights_reference", {}).get("weight_reference_id", "")),
        model_version_id=str(state.get("model_version_metadata", {}).get("model_version_id", "")),
        parameter_version_id=str(state.get("parameter_version_metadata", {}).get("parameter_version_id", "")),
        source_training_result_run_id=str(model_meta.get("source_training_result_run_id", "")),
        source_training_result_status=str(model_meta.get("source_training_result_status", "")),
        source_training_result_health_status=str(model_meta.get("source_training_result_health_status", "")),
        source_training_result_planning_run_id=str(model_meta.get("source_training_result_planning_run_id", "")),
        source_training_result_planning_status=str(model_meta.get("source_training_result_planning_status", "")),
        source_training_result_planning_health_status=str(model_meta.get("source_training_result_planning_health_status", "")),
        source_metric_extension_run_id=str(model_meta.get("source_metric_extension_run_id", "")),
        source_metric_extension_status=str(model_meta.get("source_metric_extension_status", "")),
        source_metric_extension_health_status=str(model_meta.get("source_metric_extension_health_status", "")),
        source_metric_computation_run_id=str(model_meta.get("source_metric_computation_run_id", "")),
        source_metric_computation_status=str(model_meta.get("source_metric_computation_status", "")),
        source_metric_computation_health_status=str(model_meta.get("source_metric_computation_health_status", "")),
        source_metric_evaluation_planning_run_id=str(model_meta.get("source_metric_evaluation_planning_run_id", "")),
        source_metric_evaluation_status=str(model_meta.get("source_metric_evaluation_status", "")),
        source_metric_evaluation_health_status=str(model_meta.get("source_metric_evaluation_health_status", "")),
        source_training_evaluation_run_id=str(model_meta.get("source_training_evaluation_run_id", "")),
        source_training_evaluation_status=str(model_meta.get("source_training_evaluation_status", "")),
        source_training_evaluation_health_status=str(model_meta.get("source_training_evaluation_health_status", "")),
        source_forward_return_label_run_id=str(model_meta.get("source_forward_return_label_run_id", "")),
        source_forward_return_label_status=str(model_meta.get("source_forward_return_label_status", "")),
        source_forward_return_label_health_status=str(model_meta.get("source_forward_return_label_health_status", "")),
        source_replay_decision_freeze_run_id=str(model_meta.get("source_replay_decision_freeze_run_id", "")),
        source_replay_decision_freeze_status=str(model_meta.get("source_replay_decision_freeze_status", "")),
        source_replay_decision_freeze_health_status=str(model_meta.get("source_replay_decision_freeze_health_status", "")),
        training_result_row_count=len(rows),
        eligible_training_result_row_count=len(rows),
        metric_evidence_names_present=",".join(evidence_names),
        metric_evidence_reference_count=len(evidence_names),
        active_model_pointer_created=created,
        active_model_registry_entry_created=created,
        active_parameter_pointer_created=created,
        active_model_activation_status_created=created,
        active_model_rollback_plan_created=created,
        active_model_input_index_created=created,
        active_model_lineage_matrix_created=created,
        active_model_limitations_created=created,
        active_model_overfit_warnings_created=created,
        active_model_safety_flags_created=True,
        blocker_count=0 if ready else len(state.get("gate_results", [])),
        next_action=_next_action(state["status"]),
        research_governed=settings.research_governed,
        diagnostic_output=settings.diagnostic_output,
        artifact_paths=artifact_paths,
        gate_results=state.get("gate_results", []),
    )
    if settings.write_artifacts:
        write_active_model_artifacts(result, state)
    return result


def write_active_model_artifacts(result: ActiveModelResult, state: dict[str, Any]) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_json(result.artifact_paths["active_model_metadata"], _metadata(result))
    _write_json(result.artifact_paths["active_model_safety_flags"], _safety_flags(result))
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(_recommended_next_task(result), encoding="utf-8")

    for group, key in [
        ("precondition", "active_model_precondition_results"),
        ("approval", "active_model_approval_results"),
        ("input_lineage", "active_model_input_lineage_results"),
        ("model_weight_versioning_input", "active_model_model_weight_versioning_input_results"),
        ("metric_evidence", "active_model_metric_evidence_results"),
        ("leakage", "active_model_leakage_guard_results"),
        ("side_effect", "active_model_side_effect_guard_results"),
        ("overclaim", "active_model_overclaim_guard_results"),
    ]:
        _write_csv(result.artifact_paths[key], _gate_frame(result.gate_results, group))

    if not result.active_model_artifacts_created:
        return

    rows = state.get("training_result_rows", [])
    _write_json(result.artifact_paths["active_model_pointer"], _active_model_pointer(result, rows))
    _write_json(result.artifact_paths["active_model_registry_entry"], _active_model_registry_entry(result))
    _write_json(result.artifact_paths["active_parameter_pointer"], _active_parameter_pointer(result))
    _write_json(result.artifact_paths["active_model_activation_status"], _active_model_activation_status(result))
    result.artifact_paths["active_model_rollback_plan"].write_text(_active_model_rollback_plan(result), encoding="utf-8")
    _write_csv(result.artifact_paths["active_model_input_index"], pd.DataFrame(_active_model_input_index(result)))
    _write_csv(result.artifact_paths["active_model_lineage_matrix"], pd.DataFrame(_active_model_lineage_matrix(result, rows)))
    result.artifact_paths["active_model_limitations"].write_text(_active_model_limitations(), encoding="utf-8")
    _write_csv(result.artifact_paths["active_model_overfit_warnings"], pd.DataFrame(_active_model_overfit_warnings()))


def _evaluate(settings: ActiveModelSettings) -> dict[str, Any]:
    if not _has_any_input(settings):
        return _state(NO_ACTIVE_MODEL_INPUT)
    if not settings.approval_manifest_path or not Path(settings.approval_manifest_path).exists():
        return _state(ACTIVE_MODEL_APPROVAL_BLOCKED, "approval", "approval_manifest", "exact approval missing")
    approval = _load_json(settings.approval_manifest_path)
    if str(approval.get("approval_text", "")).strip() != EXACT_ACTIVE_MODEL_APPROVAL_TEXT:
        return _state(ACTIVE_MODEL_APPROVAL_BLOCKED, "approval", "approval_text", "exact approval text missing or invalid")

    request = _load_json(settings.active_model_request_manifest_path)
    if _any_truthy(request, REQUEST_OVERCLAIM_FIELDS):
        return _state(ACTIVE_MODEL_OVERCLAIM_BLOCKED, "overclaim", "request_scope", "unsafe downstream active-model scope requested")
    if _any_truthy(request, REQUEST_LEAKAGE_FIELDS):
        return _state(ACTIVE_MODEL_LEAKAGE_BLOCKED, "leakage", "request_scope", "unsafe integration or leakage path requested")
    if _any_truthy(request, REQUEST_SIDE_EFFECT_FIELDS):
        return _state(ACTIVE_MODEL_SIDE_EFFECT_BLOCKED, "side_effect", "request_scope", "unsafe side effect requested")

    missing = _first_missing_required_path(settings)
    if missing:
        field, status = missing
        return _state(status, _group_for_status(status), field, "required input artifact missing")
    if _forbidden_artifact_exists(settings):
        return _state(ACTIVE_MODEL_FORBIDDEN_ARTIFACT_BLOCKED, "precondition", "forbidden_artifacts", "forbidden downstream artifact present")

    model_meta = _load_json(settings.model_weight_versioning_metadata_path)
    if _source_status(model_meta) != MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED:
        return _state(
            ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED,
            "model_weight_versioning_input",
            "model_weight_versioning_metadata",
            "model weight versioning source is not created",
            model_weight_versioning_metadata=model_meta,
        )
    if _status_value(settings.model_weight_versioning_status_artifact_path) != MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED:
        return _state(
            ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED,
            "model_weight_versioning_input",
            "model_weight_versioning_status",
            "model weight versioning status mismatch",
            model_weight_versioning_metadata=model_meta,
        )
    if _status_value(settings.model_weight_versioning_health_artifact_path) != "PASS":
        return _state(ACTIVE_MODEL_HEALTH_BLOCKED, "input_lineage", "model_weight_versioning_health", "source health is not PASS", model_weight_versioning_metadata=model_meta)

    model_weights = _load_json(settings.model_weights_reference_path)
    model_version = _load_json(settings.model_version_metadata_path)
    parameter_version = _load_json(settings.parameter_version_metadata_path)
    if not model_weights.get("weight_reference_id") or not model_version.get("model_version_id") or not parameter_version.get("parameter_version_id"):
        return _state(ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED, "model_weight_versioning_input", "model_reference_ids", "model reference ids missing", model_weight_versioning_metadata=model_meta)
    if _truthy(model_version.get("active_model")) or _truthy(model_version.get("promoted_model")) or _truthy(model_version.get("production_model")):
        return _state(ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED, "model_weight_versioning_input", "model_version_metadata", "model version is already active/promoted/production", model_weight_versioning_metadata=model_meta)
    if _truthy(parameter_version.get("active_parameters")):
        return _state(ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED, "model_weight_versioning_input", "parameter_version_metadata", "parameter version is already active", model_weight_versioning_metadata=model_meta)

    if not _model_weight_versioning_artifacts_safe(settings):
        return _state(ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED, "model_weight_versioning_input", "model_artifacts", "model weight versioning artifacts are unsafe or incomplete", model_weight_versioning_metadata=model_meta)

    for health_field in [
        "training_result_health_artifact_path",
        "training_result_planning_health_artifact_path",
        "metric_extension_health_artifact_path",
        "metric_computation_health_artifact_path",
        "metric_evaluation_health_artifact_path",
        "training_evaluation_health_artifact_path",
        "forward_return_label_health_artifact_path",
        "replay_decision_freeze_health_artifact_path",
    ]:
        if _status_value(getattr(settings, health_field)) != "PASS":
            return _state(ACTIVE_MODEL_HEALTH_BLOCKED, "input_lineage", health_field, "upstream health is not PASS", model_weight_versioning_metadata=model_meta)

    status_blocker = _source_status_blocker(settings, model_meta)
    if status_blocker:
        name, expected = status_blocker
        return _state(ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED, "input_lineage", name, f"expected status {expected}", model_weight_versioning_metadata=model_meta)

    training_rows_frame = _load_csv(settings.training_result_rows_path)
    if training_rows_frame.empty:
        return _state(ACTIVE_MODEL_TRAINING_RESULT_ROWS_BLOCKED, "model_weight_versioning_input", "training_result_rows", "training_result rows missing", model_weight_versioning_metadata=model_meta)
    column_blocker = _required_column_blocker(training_rows_frame, LINEAGE_COLUMNS)
    if column_blocker:
        return _state(column_blocker["status"], "input_lineage", column_blocker["column"], column_blocker["reason"], model_weight_versioning_metadata=model_meta)
    if not _all_true(training_rows_frame, "report_only") or not _all_true(training_rows_frame, "diagnostic_only"):
        return _state(ACTIVE_MODEL_LINEAGE_BLOCKED, "input_lineage", "report_only", "report_only/diagnostic_only flags missing", model_weight_versioning_metadata=model_meta)

    model_lineage = _load_csv(settings.model_lineage_matrix_path)
    if "lineage_item" not in model_lineage.columns:
        return _state(ACTIVE_MODEL_LINEAGE_BLOCKED, "input_lineage", "model_lineage_matrix", "model lineage matrix missing lineage_item", model_weight_versioning_metadata=model_meta)

    sample_rows = _load_csv(settings.training_evaluation_sample_rows_path)
    if _duplicate_unquarantined(sample_rows):
        return _state(ACTIVE_MODEL_LINEAGE_BLOCKED, "input_lineage", "duplicate_samples", "duplicate sample rows not quarantined", model_weight_versioning_metadata=model_meta)

    metric_names = _metric_names_present(model_meta, settings)
    if REQUIRED_METRICS - metric_names:
        return _state(ACTIVE_MODEL_METRIC_EVIDENCE_BLOCKED, "metric_evidence", "metric_evidence", "required metric evidence missing", model_weight_versioning_metadata=model_meta)
    if _metric_names_overclaim(model_meta):
        return _state(ACTIVE_MODEL_OVERCLAIM_BLOCKED, "overclaim", "metric_evidence", "metric evidence overclaims performance validation", model_weight_versioning_metadata=model_meta)

    if any(phrase not in _load_text(settings.model_limitations_path).lower() for phrase in _model_limitation_phrases()):
        return _state(ACTIVE_MODEL_LIMITATIONS_BLOCKED, "overclaim", "model_limitations", "required model limitation wording missing", model_weight_versioning_metadata=model_meta)

    warnings_frame = _load_csv(settings.model_overfit_warnings_path)
    if SOURCE_MODEL_OVERFIT_WARNINGS - set(warnings_frame.get("risk_item", pd.Series(dtype=str)).astype(str)):
        return _state(ACTIVE_MODEL_OVERFIT_WARNING_BLOCKED, "overclaim", "model_overfit_warnings", "required overfit warning missing", model_weight_versioning_metadata=model_meta)

    safety = _load_json(settings.model_safety_flags_path)
    if not _truthy(safety.get("model_weight_versioning_research_artifacts_created")):
        return _state(ACTIVE_MODEL_SAFETY_FLAG_BLOCKED, "precondition", "model_safety_flags", "model safety flags do not confirm research artifacts", model_weight_versioning_metadata=model_meta)
    for field in [
        "active_model",
        "promoted_model",
        "production_model",
        "active_parameters",
        "active_thresholds",
        "advisory_predictions_created",
        "active_probabilities_created",
        "active_stock_profile_exists",
        "stock_profile_created",
        "buy_review_allowed",
        "approved_for_paper",
        "strategy_performance_validated",
        "trading_allowed",
    ]:
        if _truthy(safety.get(field)):
            return _state(ACTIVE_MODEL_SAFETY_FLAG_BLOCKED, "precondition", field, "unsafe model safety flag true", model_weight_versioning_metadata=model_meta)

    leakage = _load_json(settings.leakage_evidence_bundle_path)
    if any(_truthy(value) for value in leakage.values()):
        return _state(ACTIVE_MODEL_LEAKAGE_BLOCKED, "leakage", "leakage_bundle", "leakage guard failed", model_weight_versioning_metadata=model_meta)
    side_effect = _load_json(settings.side_effect_evidence_bundle_path)
    if any(_truthy(side_effect.get(field)) for field in DOWNSTREAM_FALSE_FIELDS):
        return _state(ACTIVE_MODEL_SIDE_EFFECT_BLOCKED, "side_effect", "side_effect_bundle", "side effect guard failed", model_weight_versioning_metadata=model_meta)
    overclaim = _load_json(settings.overclaim_evidence_bundle_path)
    if not all(_truthy(overclaim.get(field)) for field in REQUIRED_ACTIVE_MODEL_OVERCLAIM_TRUE):
        return _state(ACTIVE_MODEL_OVERCLAIM_BLOCKED, "overclaim", "overclaim_bundle", "overclaim guard failed", model_weight_versioning_metadata=model_meta)

    status = ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED if settings.allow_active_model else READY_FOR_ACTIVE_MODEL
    return {
        "status": status,
        "gate_results": [_passed_gate("precondition", "all_required_inputs")],
        "model_weight_versioning_metadata": model_meta,
        "model_weights_reference": model_weights,
        "model_version_metadata": model_version,
        "parameter_version_metadata": parameter_version,
        "training_result_rows": training_rows_frame.to_dict("records"),
        "metric_evidence_names": metric_names,
    }


def _state(
    status: str,
    group: str = "precondition",
    name: str = "input",
    reason: str = "",
    model_weight_versioning_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "gate_results": [] if status == NO_ACTIVE_MODEL_INPUT else [_blocked(status, group, name, reason)],
        "model_weight_versioning_metadata": model_weight_versioning_metadata or {},
        "model_weights_reference": {},
        "model_version_metadata": {},
        "parameter_version_metadata": {},
        "training_result_rows": [],
        "metric_evidence_names": set(),
    }


def _first_missing_required_path(settings: ActiveModelSettings) -> tuple[str, str] | None:
    groups = [
        ("model_weight_versioning_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("model_weights_reference_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_version_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("parameter_version_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("threshold_plan_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("prediction_rows_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("probability_calibration_report_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("feature_importance_report_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_input_index_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_lineage_matrix_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_limitations_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_overfit_warnings_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_safety_flags_path", ACTIVE_MODEL_SAFETY_FLAG_BLOCKED),
        ("model_weight_versioning_status_artifact_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("model_weight_versioning_health_artifact_path", ACTIVE_MODEL_HEALTH_BLOCKED),
        ("training_result_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("training_result_rows_path", ACTIVE_MODEL_TRAINING_RESULT_ROWS_BLOCKED),
        ("training_result_status_artifact_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("training_result_health_artifact_path", ACTIVE_MODEL_HEALTH_BLOCKED),
        ("training_result_planning_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("training_result_planning_health_artifact_path", ACTIVE_MODEL_HEALTH_BLOCKED),
        ("metric_extension_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("metric_extension_result_rows_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("metric_extension_health_artifact_path", ACTIVE_MODEL_HEALTH_BLOCKED),
        ("metric_computation_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("metric_computation_result_rows_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("metric_computation_health_artifact_path", ACTIVE_MODEL_HEALTH_BLOCKED),
        ("metric_evaluation_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("metric_evaluation_health_artifact_path", ACTIVE_MODEL_HEALTH_BLOCKED),
        ("training_evaluation_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("training_evaluation_sample_rows_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("training_evaluation_health_artifact_path", ACTIVE_MODEL_HEALTH_BLOCKED),
        ("forward_return_label_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("forward_return_label_rows_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("forward_return_label_health_artifact_path", ACTIVE_MODEL_HEALTH_BLOCKED),
        ("replay_decision_freeze_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("replay_decision_freeze_rows_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("replay_decision_freeze_health_artifact_path", ACTIVE_MODEL_HEALTH_BLOCKED),
        ("leakage_evidence_bundle_path", ACTIVE_MODEL_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", ACTIVE_MODEL_OVERCLAIM_BLOCKED),
        ("side_effect_evidence_bundle_path", ACTIVE_MODEL_SIDE_EFFECT_BLOCKED),
    ]
    for field, status in groups:
        path = getattr(settings, field)
        if path is None or not Path(path).exists():
            return field, status
    return None


def _source_status_blocker(settings: ActiveModelSettings, model_meta: dict[str, Any]) -> tuple[str, str] | None:
    expectations = {
        "source_training_result_status": "TRAINING_RESULT_CREATED",
        "source_training_result_planning_status": "TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED",
        "source_metric_extension_status": "METRIC_EXTENSION_REPORT_CREATED",
        "source_metric_computation_status": "METRIC_COMPUTATION_REPORT_CREATED",
        "source_metric_evaluation_status": "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED",
        "source_training_evaluation_status": "TRAINING_EVALUATION_DATASET_CREATED",
        "source_forward_return_label_status": "FORWARD_RETURN_LABELS_CREATED",
        "source_replay_decision_freeze_status": "REPLAY_DECISION_FROZEN",
    }
    for key, expected in expectations.items():
        if str(model_meta.get(key, "")) != expected:
            return key, expected
    meta_paths = {
        "training_result_metadata_path": "TRAINING_RESULT_CREATED",
        "training_result_planning_metadata_path": "TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED",
        "metric_extension_metadata_path": "METRIC_EXTENSION_REPORT_CREATED",
        "metric_computation_metadata_path": "METRIC_COMPUTATION_REPORT_CREATED",
        "metric_evaluation_metadata_path": "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED",
        "training_evaluation_metadata_path": "TRAINING_EVALUATION_DATASET_CREATED",
        "forward_return_label_metadata_path": "FORWARD_RETURN_LABELS_CREATED",
        "replay_decision_freeze_metadata_path": "REPLAY_DECISION_FROZEN",
    }
    for field, expected in meta_paths.items():
        if _source_status(_load_json(getattr(settings, field))) != expected:
            return field, expected
    return None


def _model_weight_versioning_artifacts_safe(settings: ActiveModelSettings) -> bool:
    threshold = _load_csv(settings.threshold_plan_path)
    if "forbidden_interpretation" not in threshold.columns:
        return False
    if not threshold["forbidden_interpretation"].astype(str).str.contains("signal_semantics", regex=False).any():
        return False
    predictions = _load_csv(settings.prediction_rows_path)
    if predictions.empty or "prediction_role" not in predictions.columns:
        return False
    if not predictions["prediction_role"].astype(str).eq("report_only_research").all():
        return False
    probability = _load_text(settings.probability_calibration_report_path).lower()
    if "no active probabilities" not in probability:
        return False
    features = _load_csv(settings.feature_importance_report_path)
    if "forbidden_interpretation" not in features.columns:
        return False
    if not features["forbidden_interpretation"].astype(str).str.contains("stock_profile", regex=False).all():
        return False
    model_input = _load_csv(settings.model_input_index_path)
    if {"source_run_id", "health_status"} - set(model_input.columns):
        return False
    return True


def _metric_names_present(model_meta: dict[str, Any], settings: ActiveModelSettings) -> set[str]:
    names = {name.strip() for name in str(model_meta.get("metric_evidence_names_present", "")).split(",") if name.strip()}
    if names:
        return names
    evidence_frame = _load_csv(settings.metric_extension_result_rows_path)
    return {str(name) for name in evidence_frame.get("metric_name", pd.Series(dtype=str)).astype(str)}


def _metric_names_overclaim(model_meta: dict[str, Any]) -> bool:
    return "strategy performance validated" in str(model_meta.get("metric_evidence_names_present", "")).lower()


def _model_limitation_phrases() -> set[str]:
    return {
        "report-only research artifacts",
        "no stock_profile",
        "no buy-review",
        "no paper approval",
        "no performance validation",
        "no trading",
    }


def _metadata(result: ActiveModelResult) -> dict[str, Any]:
    payload = {
        "active_model_run_id": result.active_model_run_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "execution_status": result.status,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "ready_for_active_model": result.ready_for_active_model,
        "active_model_executed": result.active_model_executed,
        "active_model_artifacts_created": result.active_model_artifacts_created,
        "training_result_row_count": result.training_result_row_count,
        "eligible_training_result_row_count": result.eligible_training_result_row_count,
        "metric_evidence_names_present": result.metric_evidence_names_present,
        "metric_evidence_reference_count": result.metric_evidence_reference_count,
        "active_model_pointer_created": result.active_model_pointer_created,
        "active_model_registry_entry_created": result.active_model_registry_entry_created,
        "active_parameter_pointer_created": result.active_parameter_pointer_created,
        "active_model_activation_status_created": result.active_model_activation_status_created,
        "active_model_rollback_plan_created": result.active_model_rollback_plan_created,
        "active_model_input_index_created": result.active_model_input_index_created,
        "active_model_lineage_matrix_created": result.active_model_lineage_matrix_created,
        "active_model_limitations_created": result.active_model_limitations_created,
        "active_model_overfit_warnings_created": result.active_model_overfit_warnings_created,
        "active_model_safety_flags_created": result.active_model_safety_flags_created,
        "artifact_path": result.artifact_path,
        "research_governed": result.research_governed,
        "diagnostic_output": result.diagnostic_output,
    }
    for field in [
        "source_model_workflow_run_id",
        "source_model_weight_versioning_status",
        "source_model_weight_versioning_health_status",
        "model_weight_reference_id",
        "model_version_id",
        "parameter_version_id",
        "source_training_result_run_id",
        "source_training_result_status",
        "source_training_result_health_status",
        "source_training_result_planning_run_id",
        "source_training_result_planning_status",
        "source_training_result_planning_health_status",
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


def _safety_flags(result: ActiveModelResult) -> dict[str, Any]:
    return {
        "active_model_artifacts_created": result.active_model_artifacts_created,
        "active_model_pointer_created": result.active_model_pointer_created,
        "active_model_registry_entry_created": result.active_model_registry_entry_created,
        "active_parameter_pointer_created": result.active_parameter_pointer_created,
        **{field: getattr(result, field) for field in DOWNSTREAM_FALSE_FIELDS},
        "research_governed": result.research_governed,
        "diagnostic_output": result.diagnostic_output,
    }


def _active_model_pointer(result: ActiveModelResult, rows: list[dict[str, Any]]) -> dict[str, Any]:
    row = rows[0] if rows else {}
    return {
        "active_model_run_id": result.active_model_run_id,
        "pointer_role": "research_governed_active_model",
        "source_model_workflow_run_id": result.source_model_workflow_run_id,
        "model_weight_reference_id": result.model_weight_reference_id,
        "model_version_id": result.model_version_id,
        "parameter_version_id": result.parameter_version_id,
        "permitted_interpretation": "research-governed active model artifact for future review context only",
        "forbidden_interpretation": (
            "not a promoted model; not a production model; no active thresholds; no advisory predictions; "
            "no active probabilities; no stock_profile; no buy-review; no paper approval; no performance "
            "validation; no trading permission"
        ),
        "source_hash": row.get("source_hash", ""),
        "revision_id": row.get("revision_id", ""),
        "available_time": row.get("available_time", ""),
        "quality_status": row.get("quality_status", ""),
        "serving_enabled": False,
        "current_candidates_integration": False,
        "snapshot_integration": False,
        "signal_semantics_mutated": False,
        "broker_api_allowed": False,
        "order_allowed": False,
        "message_allowed": False,
        "trading_allowed": False,
        "research_governed": True,
        "diagnostic_output": True,
    }


def _active_model_registry_entry(result: ActiveModelResult) -> dict[str, Any]:
    return {
        "active_model_run_id": result.active_model_run_id,
        "registry_role": "research_governed_active_model_registry_entry",
        "source_model_workflow_run_id": result.source_model_workflow_run_id,
        "model_version_id": result.model_version_id,
        "parameter_version_id": result.parameter_version_id,
        "promoted_model": False,
        "production_model": False,
        "serving_enabled": False,
        "trading_enabled": False,
        "scheduler_enabled": False,
        "research_governed": True,
        "diagnostic_output": True,
    }


def _active_parameter_pointer(result: ActiveModelResult) -> dict[str, Any]:
    return {
        "active_model_run_id": result.active_model_run_id,
        "parameter_version_id": result.parameter_version_id,
        "parameter_pointer_role": "research_governed_active_parameter_pointer",
        "active_thresholds_created": False,
        "signal_semantics_mutated": False,
        "advisory_predictions_created": False,
        "active_probabilities_created": False,
        "research_governed": True,
        "diagnostic_output": True,
    }


def _active_model_activation_status(result: ActiveModelResult) -> dict[str, Any]:
    return {
        "active_model_run_id": result.active_model_run_id,
        "activation_status": "ACTIVE_MODEL_RESEARCH_GOVERNED",
        "ready_for_active_model": result.ready_for_active_model,
        "active_model_artifacts_created": result.active_model_artifacts_created,
        **{field: getattr(result, field) for field in DOWNSTREAM_FALSE_FIELDS},
    }


def _active_model_rollback_plan(result: ActiveModelResult) -> str:
    return (
        "# Active Model Rollback Plan\n\n"
        f"- active_model_run_id: {result.active_model_run_id}\n"
        "- no production serving exists\n"
        "- no broker/order/trading path exists\n"
        "- rollback is limited to ignoring this research-governed diagnostics artifact in future review.\n"
    )


def _active_model_input_index(result: ActiveModelResult) -> list[dict[str, Any]]:
    rows = [
        ("model_weight_versioning", result.source_model_workflow_run_id, result.source_model_weight_versioning_status, result.source_model_weight_versioning_health_status),
        ("training_result", result.source_training_result_run_id, result.source_training_result_status, result.source_training_result_health_status),
        ("training_result_planning", result.source_training_result_planning_run_id, result.source_training_result_planning_status, result.source_training_result_planning_health_status),
        ("metric_extension", result.source_metric_extension_run_id, result.source_metric_extension_status, result.source_metric_extension_health_status),
        ("metric_computation", result.source_metric_computation_run_id, result.source_metric_computation_status, result.source_metric_computation_health_status),
        ("metric_evaluation", result.source_metric_evaluation_planning_run_id, result.source_metric_evaluation_status, result.source_metric_evaluation_health_status),
        ("training_evaluation", result.source_training_evaluation_run_id, result.source_training_evaluation_status, result.source_training_evaluation_health_status),
        ("forward_return_label", result.source_forward_return_label_run_id, result.source_forward_return_label_status, result.source_forward_return_label_health_status),
        ("replay_decision_freeze", result.source_replay_decision_freeze_run_id, result.source_replay_decision_freeze_status, result.source_replay_decision_freeze_health_status),
    ]
    return [
        {
            "active_model_run_id": result.active_model_run_id,
            "input_component": family,
            "source_run_id": run_id,
            "source_status": status,
            "health_status": health,
            "required_for_active_model": True,
            "immutable_required": True,
            "research_governed": True,
            "diagnostic_output": True,
        }
        for family, run_id, status, health in rows
    ]


def _active_model_lineage_matrix(result: ActiveModelResult, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    row = rows[0] if rows else {}
    lineage = {
        "model_workflow_run_id": result.source_model_workflow_run_id,
        "model_weight_reference_id": result.model_weight_reference_id,
        "model_version_id": result.model_version_id,
        "parameter_version_id": result.parameter_version_id,
        "training_result_run_id": result.source_training_result_run_id,
        "training_result_planning_run_id": result.source_training_result_planning_run_id,
        "metric_extension_run_id": result.source_metric_extension_run_id,
        "metric_computation_run_id": result.source_metric_computation_run_id,
        "metric_evaluation_run_id": result.source_metric_evaluation_planning_run_id,
        "training_evaluation_run_id": result.source_training_evaluation_run_id,
        "forward_return_label_run_id": result.source_forward_return_label_run_id,
        "replay_decision_freeze_run_id": result.source_replay_decision_freeze_run_id,
        "training_result_row_id": row.get("training_result_row_id", ""),
        "replay_decision_id": row.get("replay_decision_id", ""),
        "forward_return_label_id": row.get("forward_return_label_id", ""),
        "symbol": row.get("symbol", ""),
        "replay_as_of_date": row.get("replay_as_of_date", ""),
        "source_hash": row.get("source_hash", ""),
        "revision_id": row.get("revision_id", ""),
        "available_time": row.get("available_time", ""),
        "quality_status": row.get("quality_status", ""),
    }
    return [
        {
            "active_model_run_id": result.active_model_run_id,
            "lineage_item": item,
            "source_value": value,
            "required": True,
            "observed": bool(value),
            "research_governed": True,
            "diagnostic_output": True,
        }
        for item, value in lineage.items()
    ]


def _active_model_limitations() -> str:
    return (
        "# Active Model Phase 1 Limitations\n\n"
        "This artifact is a research-governed active model diagnostics artifact only.\n\n"
        "- no promoted model\n"
        "- no production model\n"
        "- no active thresholds\n"
        "- no advisory predictions\n"
        "- no active probabilities\n"
        "- no stock_profile\n"
        "- no buy-review\n"
        "- no paper approval\n"
        "- no performance validation\n"
        "- no trading\n"
        "- no broker/order/message integration\n"
    )


def _active_model_overfit_warnings() -> list[dict[str, Any]]:
    return [
        {
            "warning_id": f"active_model_overfit_{index:03d}",
            "risk_item": risk,
            "applies_to_active_model": True,
            "guard_required": True,
            "severity": "WARN",
            "notes": "Required research-governed active model overfit warning.",
        }
        for index, risk in enumerate(sorted(REQUIRED_OVERFIT_WARNINGS), start=1)
    ]


def _render_report(result: ActiveModelResult) -> str:
    return (
        "# Active Model Phase 1 Report\n\n"
        f"- active_model_run_id: {result.active_model_run_id}\n"
        f"- status: {result.status}\n"
        f"- workflow_stage: {result.workflow_stage}\n"
        f"- ready_for_active_model: {result.ready_for_active_model}\n"
        f"- active_model_artifacts_created: {result.active_model_artifacts_created}\n"
        f"- training_result_row_count: {result.training_result_row_count}\n"
        f"- metric_evidence_reference_count: {result.metric_evidence_reference_count}\n\n"
        "This is a research-governed active model artifact workflow only.\n\n"
        "There is no promoted model, no production model, no active thresholds, no advisory predictions, "
        "no active probabilities, no stock_profile, no buy-review, no paper approval, no performance validation, "
        "and no trading.\n"
    )


def _recommended_next_task(result: ActiveModelResult) -> str:
    if result.status == ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED:
        return "Active Model Artifact Views Report-Only v0.1\n"
    if result.status == READY_FOR_ACTIVE_MODEL:
        return "Rerun with --allow-active-model only if research-governed active model artifacts should be created.\n"
    return "Provide exact approval and complete MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED lineage before active model phase 1.\n"


def _next_action(status: str) -> str:
    if status == ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED:
        return "Review research-governed active model artifacts before adding artifact views."
    if status == READY_FOR_ACTIVE_MODEL:
        return "Rerun with explicit allow only if research-governed active model artifacts should be created."
    if status == NO_ACTIVE_MODEL_INPUT:
        return "Provide exact approval and complete model weight versioning inputs."
    return "Resolve blocked active model gates before rerun."


def _has_any_input(settings: ActiveModelSettings) -> bool:
    return any(
        getattr(settings, field) is not None
        for field in ActiveModelSettings.__dataclass_fields__
        if field.endswith("_path")
    )


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def _load_csv(path: Path | None) -> pd.DataFrame:
    if path is None or not Path(path).exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str)


def _load_text(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _source_status(metadata: dict[str, Any]) -> str:
    return str(metadata.get("status", metadata.get("execution_status", "")))


def _status_value(path: Path | None) -> str:
    payload = _load_json(path)
    return str(payload.get("status", payload.get("health_status", "")))


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _any_truthy(payload: dict[str, Any], fields: set[str]) -> bool:
    return any(_truthy(payload.get(field)) for field in fields)


def _all_true(frame: pd.DataFrame, column: str) -> bool:
    if column not in frame.columns:
        return False
    return frame[column].map(_truthy).all()


def _required_column_blocker(frame: pd.DataFrame, columns: set[str]) -> dict[str, str] | None:
    missing = sorted(columns - set(frame.columns))
    if not missing:
        return None
    column = missing[0]
    if column == "training_result_row_id":
        return {
            "status": ACTIVE_MODEL_TRAINING_RESULT_ROWS_BLOCKED,
            "column": column,
            "reason": "training_result row id missing",
        }
    return {"status": ACTIVE_MODEL_LINEAGE_BLOCKED, "column": column, "reason": "required lineage column missing"}


def _duplicate_unquarantined(frame: pd.DataFrame) -> bool:
    keys = ["replay_decision_id", "forward_return_label_id", "symbol", "replay_as_of_date", "split_role"]
    if frame.empty:
        return True
    if not set(keys).issubset(frame.columns):
        return True
    duplicates = frame.duplicated(keys, keep=False)
    if not duplicates.any():
        return False
    quarantine = pd.to_numeric(frame.get("quarantine_count", 0), errors="coerce").fillna(0)
    return (quarantine[duplicates] <= 0).any()


def _forbidden_artifact_exists(settings: ActiveModelSettings) -> bool:
    parents = {
        Path(path).parent
        for field in ActiveModelSettings.__dataclass_fields__
        if field.endswith("_path")
        for path in [getattr(settings, field)]
        if path is not None
    }
    for parent in parents:
        if not parent.exists():
            continue
        for child in parent.iterdir():
            if any(fnmatch.fnmatch(child.name, pattern) for pattern in FORBIDDEN_ARTIFACT_PATTERNS):
                return True
    return False


def _group_for_status(status: str) -> str:
    if status == ACTIVE_MODEL_HEALTH_BLOCKED:
        return "input_lineage"
    if status == ACTIVE_MODEL_TRAINING_RESULT_ROWS_BLOCKED:
        return "model_weight_versioning_input"
    if status == ACTIVE_MODEL_LEAKAGE_BLOCKED:
        return "leakage"
    if status == ACTIVE_MODEL_SIDE_EFFECT_BLOCKED:
        return "side_effect"
    if status == ACTIVE_MODEL_OVERCLAIM_BLOCKED:
        return "overclaim"
    if status == ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED:
        return "model_weight_versioning_input"
    return "precondition"


def _blocked(status: str, group: str, name: str, reason: str) -> ActiveModelGateResult:
    return ActiveModelGateResult(group, name, status, False, reason)


def _passed_gate(group: str, name: str) -> ActiveModelGateResult:
    return ActiveModelGateResult(group, name, "PASS", True, "")


def _gate_frame(gates: list[ActiveModelGateResult], group: str) -> pd.DataFrame:
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _assert_manual_diagnostics_output(path: Path) -> None:
    normalized = str(path).replace("\\", "/")
    if "/outputs/reports/manual_diagnostics/" not in f"/{normalized}/" and not normalized.startswith("outputs/reports/manual_diagnostics/"):
        raise ValueError("active model output must stay under outputs/reports/manual_diagnostics")


def _stable_id(settings: ActiveModelSettings) -> str:
    payload = {
        field: str(getattr(settings, field))
        for field in ActiveModelSettings.__dataclass_fields__
        if field != "write_artifacts"
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:12]
