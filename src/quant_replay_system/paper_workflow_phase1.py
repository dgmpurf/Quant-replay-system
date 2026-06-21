"""Report-only Paper Workflow Phase 1 artifact workflow."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_PAPER_WORKFLOW_PHASE1_INPUT = "NO_PAPER_WORKFLOW_PHASE1_INPUT"
PAPER_WORKFLOW_PHASE1_INPUT_FOUND = "PAPER_WORKFLOW_PHASE1_INPUT_FOUND"
PAPER_WORKFLOW_PHASE1_APPROVAL_BLOCKED = "PAPER_WORKFLOW_PHASE1_APPROVAL_BLOCKED"
PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_INPUT_BLOCKED = "PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_INPUT_BLOCKED"
PAPER_WORKFLOW_PHASE1_ACTIVE_MODEL_INPUT_BLOCKED = "PAPER_WORKFLOW_PHASE1_ACTIVE_MODEL_INPUT_BLOCKED"
PAPER_WORKFLOW_PHASE1_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED = "PAPER_WORKFLOW_PHASE1_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED"
PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_INPUT_BLOCKED = "PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_INPUT_BLOCKED"
PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_ROWS_BLOCKED = "PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_ROWS_BLOCKED"
PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_PLANNING_INPUT_BLOCKED = "PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_PLANNING_INPUT_BLOCKED"
PAPER_WORKFLOW_PHASE1_METRIC_EXTENSION_INPUT_BLOCKED = "PAPER_WORKFLOW_PHASE1_METRIC_EXTENSION_INPUT_BLOCKED"
PAPER_WORKFLOW_PHASE1_METRIC_COMPUTATION_INPUT_BLOCKED = "PAPER_WORKFLOW_PHASE1_METRIC_COMPUTATION_INPUT_BLOCKED"
PAPER_WORKFLOW_PHASE1_METRIC_EVALUATION_INPUT_BLOCKED = "PAPER_WORKFLOW_PHASE1_METRIC_EVALUATION_INPUT_BLOCKED"
PAPER_WORKFLOW_PHASE1_TRAINING_EVALUATION_INPUT_BLOCKED = "PAPER_WORKFLOW_PHASE1_TRAINING_EVALUATION_INPUT_BLOCKED"
PAPER_WORKFLOW_PHASE1_FORWARD_LABEL_INPUT_BLOCKED = "PAPER_WORKFLOW_PHASE1_FORWARD_LABEL_INPUT_BLOCKED"
PAPER_WORKFLOW_PHASE1_REPLAY_FREEZE_INPUT_BLOCKED = "PAPER_WORKFLOW_PHASE1_REPLAY_FREEZE_INPUT_BLOCKED"
PAPER_WORKFLOW_PHASE1_HEALTH_BLOCKED = "PAPER_WORKFLOW_PHASE1_HEALTH_BLOCKED"
PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED = "PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED"
PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_ARTIFACT_BLOCKED = "PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_ARTIFACT_BLOCKED"
PAPER_WORKFLOW_PHASE1_PAPER_CONTEXT_BLOCKED = "PAPER_WORKFLOW_PHASE1_PAPER_CONTEXT_BLOCKED"
PAPER_WORKFLOW_PHASE1_METRIC_EVIDENCE_BLOCKED = "PAPER_WORKFLOW_PHASE1_METRIC_EVIDENCE_BLOCKED"
PAPER_WORKFLOW_PHASE1_LIMITATIONS_BLOCKED = "PAPER_WORKFLOW_PHASE1_LIMITATIONS_BLOCKED"
PAPER_WORKFLOW_PHASE1_OVERFIT_WARNING_BLOCKED = "PAPER_WORKFLOW_PHASE1_OVERFIT_WARNING_BLOCKED"
PAPER_WORKFLOW_PHASE1_SAFETY_FLAG_BLOCKED = "PAPER_WORKFLOW_PHASE1_SAFETY_FLAG_BLOCKED"
PAPER_WORKFLOW_PHASE1_FORBIDDEN_ARTIFACT_BLOCKED = "PAPER_WORKFLOW_PHASE1_FORBIDDEN_ARTIFACT_BLOCKED"
PAPER_WORKFLOW_PHASE1_LEAKAGE_BLOCKED = "PAPER_WORKFLOW_PHASE1_LEAKAGE_BLOCKED"
PAPER_WORKFLOW_PHASE1_SIDE_EFFECT_BLOCKED = "PAPER_WORKFLOW_PHASE1_SIDE_EFFECT_BLOCKED"
PAPER_WORKFLOW_PHASE1_OVERCLAIM_BLOCKED = "PAPER_WORKFLOW_PHASE1_OVERCLAIM_BLOCKED"
READY_FOR_PAPER_WORKFLOW_PHASE1 = "READY_FOR_PAPER_WORKFLOW_PHASE1"
PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED = "PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED"

EXACT_PAPER_WORKFLOW_PHASE1_APPROVAL_TEXT = (
    "I explicitly authorize only Paper Workflow Phase 1, limited to report-only paper workflow phase-1 "
    "metadata / lineage / review-context / safety artifacts. It may create paper_workflow_metadata, "
    "paper_workflow_input_index, paper_workflow_lineage_matrix, paper_candidate_review_context, "
    "paper_decision_draft, paper_review_queue, paper_workflow_limitations, "
    "paper_workflow_overfit_warnings, paper_workflow_safety_flags, gate/precondition results, "
    "recommended_next_task, and similar report-only paper workflow phase-1 artifacts only when immutable "
    "STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED, ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED, "
    "MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED, TRAINING_RESULT_CREATED, "
    "TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED, METRIC_EXTENSION_REPORT_CREATED, "
    "METRIC_COMPUTATION_REPORT_CREATED, METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED, "
    "TRAINING_EVALUATION_DATASET_CREATED, FORWARD_RETURN_LABELS_CREATED, and REPLAY_DECISION_FROZEN "
    "artifacts have complete lineage and PASS health. This phase must not create APPROVED_FOR_PAPER, "
    "real buy-review eligibility, strategy performance validation, current-candidates integration, snapshots, "
    "signal_semantics mutation, active stock_profile, promoted model, production model, active thresholds, "
    "advisory predictions, active probabilities, broker/order/message/API integration, or trading. If any "
    "upstream lineage, health, available_time, source_hash, revision_id, quality_status, "
    "report_only/diagnostic_only, research_governed, metric evidence, training_result rows, "
    "stock-profile artifacts, active-model artifacts, model-weight-versioning artifacts, limitations, "
    "overfit warnings, safety flags, or exact approval are missing, it must fail closed and create no paper "
    "workflow phase-1 artifacts."
)

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/paper_workflow_phase1_v0_1")

ARTIFACT_FILES = {
    "paper_workflow_metadata": "paper_workflow_metadata.json",
    "paper_workflow_input_index": "paper_workflow_input_index.csv",
    "paper_workflow_lineage_matrix": "paper_workflow_lineage_matrix.csv",
    "paper_candidate_review_context": "paper_candidate_review_context.csv",
    "paper_decision_draft": "paper_decision_draft.csv",
    "paper_review_queue": "paper_review_queue.csv",
    "paper_workflow_limitations": "paper_workflow_limitations.md",
    "paper_workflow_overfit_warnings": "paper_workflow_overfit_warnings.csv",
    "paper_workflow_safety_flags": "paper_workflow_safety_flags.json",
    "paper_workflow_precondition_results": "paper_workflow_precondition_results.csv",
    "paper_workflow_approval_results": "paper_workflow_approval_results.csv",
    "paper_workflow_upstream_lineage_results": "paper_workflow_upstream_lineage_results.csv",
    "paper_workflow_stock_profile_input_results": "paper_workflow_stock_profile_input_results.csv",
    "paper_workflow_existing_paper_context_results": "paper_workflow_existing_paper_context_results.csv",
    "paper_workflow_leakage_guard_results": "paper_workflow_leakage_guard_results.csv",
    "paper_workflow_side_effect_guard_results": "paper_workflow_side_effect_guard_results.csv",
    "paper_workflow_overclaim_guard_results": "paper_workflow_overclaim_guard_results.csv",
    "recommended_next_task": "recommended_next_task.md",
}

SUBSTANTIVE_ARTIFACT_KEYS = {
    "paper_workflow_input_index",
    "paper_workflow_lineage_matrix",
    "paper_candidate_review_context",
    "paper_decision_draft",
    "paper_review_queue",
    "paper_workflow_limitations",
    "paper_workflow_overfit_warnings",
}

DOWNSTREAM_FALSE_FIELDS = [
    "approved_for_paper",
    "approved_for_paper_created",
    "paper_approval_created",
    "real_buy_review_eligible",
    "buy_review_allowed",
    "strategy_performance_validated",
    "trading_allowed",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "active_stock_profile_created",
    "promoted_model_created",
    "production_model_created",
    "active_thresholds_created",
    "advisory_predictions_created",
    "active_probabilities_created",
    "order_placed",
    "broker_api_called",
    "message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]

REQUIRED_TRAINING_ROW_COLUMNS = {
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
}

REQUIRED_OVERFIT_WARNINGS = [
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
    "stock-profile overfit",
    "paper-decision overfit",
    "benchmark mismatch",
    "industry classification drift",
    "survivorship bias",
    "lookahead leakage",
    "fill/slippage assumption risk",
    "paper-overfit risk",
]

OVERCLAIM_REQUEST_FIELDS = {
    "real_buy_review_requested",
    "performance_validation_requested",
    "active_stock_profile_requested",
    "promoted_model_requested",
    "production_model_requested",
    "active_thresholds_requested",
    "advisory_predictions_requested",
    "active_probabilities_requested",
}

LEAKAGE_REQUEST_FIELDS = {
    "current_candidates_integration_requested",
    "snapshot_build_requested",
    "signal_semantics_mutation_requested",
}

SIDE_EFFECT_REQUEST_FIELDS = {
    "broker_api_called",
    "order_placed",
    "message_sent",
    "external_api_called",
    "trading_requested",
}


@dataclass(frozen=True)
class PaperWorkflowPhase1Settings:
    approval_manifest_path: str | Path | None = None
    paper_workflow_request_manifest_path: str | Path | None = None
    stock_profile_metadata_path: str | Path | None = None
    stock_profile_input_index_path: str | Path | None = None
    stock_profile_lineage_matrix_path: str | Path | None = None
    stock_profile_factor_coverage_summary_path: str | Path | None = None
    stock_profile_symbol_coverage_path: str | Path | None = None
    stock_profile_market_regime_coverage_path: str | Path | None = None
    stock_profile_metric_summary_path: str | Path | None = None
    stock_profile_limitations_path: str | Path | None = None
    stock_profile_overfit_warnings_path: str | Path | None = None
    stock_profile_safety_flags_path: str | Path | None = None
    stock_profile_status_artifact_path: str | Path | None = None
    stock_profile_health_artifact_path: str | Path | None = None
    active_model_metadata_path: str | Path | None = None
    active_model_pointer_path: str | Path | None = None
    active_model_lineage_matrix_path: str | Path | None = None
    active_model_limitations_path: str | Path | None = None
    active_model_overfit_warnings_path: str | Path | None = None
    active_model_safety_flags_path: str | Path | None = None
    active_model_status_artifact_path: str | Path | None = None
    active_model_health_artifact_path: str | Path | None = None
    model_weight_versioning_metadata_path: str | Path | None = None
    model_weights_reference_path: str | Path | None = None
    model_version_metadata_path: str | Path | None = None
    parameter_version_metadata_path: str | Path | None = None
    model_weight_versioning_status_artifact_path: str | Path | None = None
    model_weight_versioning_health_artifact_path: str | Path | None = None
    training_result_metadata_path: str | Path | None = None
    training_result_rows_path: str | Path | None = None
    training_result_status_artifact_path: str | Path | None = None
    training_result_health_artifact_path: str | Path | None = None
    training_result_planning_metadata_path: str | Path | None = None
    training_result_planning_health_artifact_path: str | Path | None = None
    metric_extension_metadata_path: str | Path | None = None
    metric_extension_result_rows_path: str | Path | None = None
    metric_extension_health_artifact_path: str | Path | None = None
    metric_computation_metadata_path: str | Path | None = None
    metric_computation_result_rows_path: str | Path | None = None
    metric_computation_health_artifact_path: str | Path | None = None
    metric_evaluation_metadata_path: str | Path | None = None
    metric_evaluation_health_artifact_path: str | Path | None = None
    training_evaluation_metadata_path: str | Path | None = None
    training_evaluation_sample_rows_path: str | Path | None = None
    training_evaluation_health_artifact_path: str | Path | None = None
    forward_return_label_metadata_path: str | Path | None = None
    forward_return_label_rows_path: str | Path | None = None
    forward_return_label_health_artifact_path: str | Path | None = None
    replay_decision_freeze_metadata_path: str | Path | None = None
    replay_decision_freeze_rows_path: str | Path | None = None
    replay_decision_freeze_health_artifact_path: str | Path | None = None
    existing_paper_workflow_status_path: str | Path | None = None
    existing_paper_context_manifest_path: str | Path | None = None
    leakage_evidence_bundle_path: str | Path | None = None
    overclaim_evidence_bundle_path: str | Path | None = None
    side_effect_evidence_bundle_path: str | Path | None = None
    allow_paper_workflow_phase1: bool = False
    output_dir: str | Path = DEFAULT_OUTPUT_DIR
    write_artifacts: bool = True
    research_governed: bool = True
    diagnostic_output: bool = True


@dataclass(frozen=True)
class PaperWorkflowPhase1GateResult:
    gate: str
    status: str
    message: str


PaperWorkflowPhase1ApprovalResult = PaperWorkflowPhase1GateResult
PaperWorkflowPhase1InputLineageResult = PaperWorkflowPhase1GateResult
PaperWorkflowPhase1StockProfileInputResult = PaperWorkflowPhase1GateResult
PaperWorkflowPhase1PaperContextResult = PaperWorkflowPhase1GateResult
PaperWorkflowPhase1LeakageGuardResult = PaperWorkflowPhase1GateResult
PaperWorkflowPhase1SideEffectGuardResult = PaperWorkflowPhase1GateResult
PaperWorkflowPhase1OverclaimResult = PaperWorkflowPhase1GateResult


@dataclass(frozen=True)
class PaperWorkflowPhase1Result:
    paper_workflow_run_id: str
    status: str
    workflow_stage: str
    ready_for_paper_workflow_phase1: bool
    paper_workflow_phase1_executed: bool
    paper_workflow_phase1_report_only_artifacts_created: bool
    paper_workflow_metadata_created: bool
    paper_workflow_input_index_created: bool
    paper_workflow_lineage_matrix_created: bool
    paper_candidate_review_context_created: bool
    paper_decision_draft_created: bool
    paper_review_queue_created: bool
    paper_workflow_limitations_created: bool
    paper_workflow_overfit_warnings_created: bool
    paper_workflow_safety_flags_created: bool
    source_stock_profile_run_id: str
    source_stock_profile_status: str
    source_stock_profile_health_status: str
    source_active_model_run_id: str
    source_active_model_status: str
    source_active_model_health_status: str
    source_model_workflow_run_id: str
    source_model_weight_versioning_status: str
    source_model_weight_versioning_health_status: str
    model_weight_reference_id: str
    model_version_id: str
    parameter_version_id: str
    approved_for_paper: bool
    approved_for_paper_created: bool
    paper_approval_created: bool
    real_buy_review_eligible: bool
    buy_review_allowed: bool
    strategy_performance_validated: bool
    trading_allowed: bool
    current_candidates_run: bool
    snapshot_built: bool
    signal_semantics_changed: bool
    active_stock_profile_created: bool
    promoted_model_created: bool
    production_model_created: bool
    active_thresholds_created: bool
    advisory_predictions_created: bool
    active_probabilities_created: bool
    order_placed: bool
    broker_api_called: bool
    message_sent: bool
    llm_api_called: bool
    external_api_called: bool
    cache_mutated: bool
    data_raw_written: bool
    data_processed_written: bool
    data_cache_written: bool
    report_only: bool
    research_governed: bool
    diagnostic_output: bool
    artifact_path: str
    artifact_paths: dict[str, Path]
    gate_results: list[PaperWorkflowPhase1GateResult]


def run_paper_workflow_phase1(settings: PaperWorkflowPhase1Settings | None = None) -> PaperWorkflowPhase1Result:
    settings = settings or PaperWorkflowPhase1Settings()
    run_id = _run_id(settings)
    artifact_dir = Path(settings.output_dir) / run_id
    artifact_paths = {key: artifact_dir / filename for key, filename in ARTIFACT_FILES.items()}
    source = _source_summary(settings)
    gates: list[PaperWorkflowPhase1GateResult] = []

    if not _has_input(settings):
        result = _build_result(
            settings,
            artifact_paths,
            run_id,
            NO_PAPER_WORKFLOW_PHASE1_INPUT,
            "PAPER_WORKFLOW_PHASE1_NO_INPUT",
            source,
            gates,
        )
        return write_paper_workflow_phase1_artifacts(result, settings, artifact_paths, source)

    status = _validate(settings, source, gates)
    if status != READY_FOR_PAPER_WORKFLOW_PHASE1:
        result = _build_result(settings, artifact_paths, run_id, status, status, source, gates)
        return write_paper_workflow_phase1_artifacts(result, settings, artifact_paths, source)

    if settings.allow_paper_workflow_phase1:
        status = PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED
    result = _build_result(settings, artifact_paths, run_id, status, status, source, gates)
    return write_paper_workflow_phase1_artifacts(result, settings, artifact_paths, source)


def write_paper_workflow_phase1_artifacts(
    result: PaperWorkflowPhase1Result,
    settings: PaperWorkflowPhase1Settings,
    artifact_paths: dict[str, Path],
    source: dict[str, Any],
) -> PaperWorkflowPhase1Result:
    if not settings.write_artifacts:
        return result
    artifact_dir = Path(result.artifact_path)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    _write_json(artifact_paths["paper_workflow_metadata"], _metadata(result, source))
    _write_json(artifact_paths["paper_workflow_safety_flags"], _safety_flags(result))
    _write_gate_csv(artifact_paths["paper_workflow_precondition_results"], result.gate_results or [_gate("precondition", result.status, result.workflow_stage)])
    _write_gate_csv(artifact_paths["paper_workflow_approval_results"], [g for g in result.gate_results if "approval" in g.gate] or [_gate("approval", result.status, result.status)])
    _write_gate_csv(artifact_paths["paper_workflow_upstream_lineage_results"], [g for g in result.gate_results if "lineage" in g.gate] or [_gate("upstream_lineage", result.status, result.status)])
    _write_gate_csv(artifact_paths["paper_workflow_stock_profile_input_results"], [g for g in result.gate_results if "stock_profile" in g.gate] or [_gate("stock_profile_input", result.status, result.status)])
    _write_gate_csv(artifact_paths["paper_workflow_existing_paper_context_results"], [g for g in result.gate_results if "paper_context" in g.gate] or [_gate("existing_paper_context", result.status, result.status)])
    _write_gate_csv(artifact_paths["paper_workflow_leakage_guard_results"], [g for g in result.gate_results if "leakage" in g.gate] or [_gate("leakage_guard", result.status, result.status)])
    _write_gate_csv(artifact_paths["paper_workflow_side_effect_guard_results"], [g for g in result.gate_results if "side_effect" in g.gate] or [_gate("side_effect_guard", result.status, result.status)])
    _write_gate_csv(artifact_paths["paper_workflow_overclaim_guard_results"], [g for g in result.gate_results if "overclaim" in g.gate] or [_gate("overclaim_guard", result.status, result.status)])
    artifact_paths["recommended_next_task"].write_text(_recommended_next_task(result), encoding="utf-8")

    if result.paper_workflow_phase1_report_only_artifacts_created:
        _write_input_index(artifact_paths["paper_workflow_input_index"], settings)
        _write_lineage_matrix(artifact_paths["paper_workflow_lineage_matrix"], result, settings, source)
        _write_candidate_context(artifact_paths["paper_candidate_review_context"], settings, result)
        _write_decision_draft(artifact_paths["paper_decision_draft"], settings, result)
        _write_review_queue(artifact_paths["paper_review_queue"], settings, result)
        artifact_paths["paper_workflow_limitations"].write_text(_limitations_text(), encoding="utf-8")
        pd.DataFrame({"warning_item": REQUIRED_OVERFIT_WARNINGS, "required": True}).to_csv(
            artifact_paths["paper_workflow_overfit_warnings"], index=False
        )
    return result


def _validate(
    settings: PaperWorkflowPhase1Settings,
    source: dict[str, Any],
    gates: list[PaperWorkflowPhase1GateResult],
) -> str:
    if not _output_under_manual_diagnostics(settings.output_dir):
        gates.append(_gate("side_effect_output_path", PAPER_WORKFLOW_PHASE1_SIDE_EFFECT_BLOCKED, "output path outside manual diagnostics"))
        return PAPER_WORKFLOW_PHASE1_SIDE_EFFECT_BLOCKED
    if _has_forbidden_artifact(Path(settings.output_dir)):
        gates.append(_gate("forbidden_artifact", PAPER_WORKFLOW_PHASE1_FORBIDDEN_ARTIFACT_BLOCKED, "forbidden artifact found"))
        return PAPER_WORKFLOW_PHASE1_FORBIDDEN_ARTIFACT_BLOCKED
    approval = _read_json_path(settings.approval_manifest_path)
    if approval.get("approval_text") != EXACT_PAPER_WORKFLOW_PHASE1_APPROVAL_TEXT:
        gates.append(_gate("approval", PAPER_WORKFLOW_PHASE1_APPROVAL_BLOCKED, "missing exact approval"))
        return PAPER_WORKFLOW_PHASE1_APPROVAL_BLOCKED
    request = _read_json_path(settings.paper_workflow_request_manifest_path)
    if request.get("approved_for_paper_requested") or request.get("paper_approval_requested"):
        gates.append(_gate("approval_scope", PAPER_WORKFLOW_PHASE1_APPROVAL_BLOCKED, "paper approval requested"))
        return PAPER_WORKFLOW_PHASE1_APPROVAL_BLOCKED
    unsafe_status = _unsafe_request_status(request)
    if unsafe_status:
        gates.append(_gate("request_scope", unsafe_status, "unsafe request scope"))
        return unsafe_status

    missing_checks = [
        ("stock_profile_metadata_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        ("stock_profile_input_index_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_ARTIFACT_BLOCKED),
        ("stock_profile_lineage_matrix_path", PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED),
        ("stock_profile_factor_coverage_summary_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_ARTIFACT_BLOCKED),
        ("stock_profile_symbol_coverage_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_ARTIFACT_BLOCKED),
        ("stock_profile_market_regime_coverage_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_ARTIFACT_BLOCKED),
        ("stock_profile_metric_summary_path", PAPER_WORKFLOW_PHASE1_METRIC_EVIDENCE_BLOCKED),
        ("stock_profile_limitations_path", PAPER_WORKFLOW_PHASE1_LIMITATIONS_BLOCKED),
        ("stock_profile_overfit_warnings_path", PAPER_WORKFLOW_PHASE1_OVERFIT_WARNING_BLOCKED),
        ("stock_profile_safety_flags_path", PAPER_WORKFLOW_PHASE1_SAFETY_FLAG_BLOCKED),
        ("stock_profile_status_artifact_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        ("stock_profile_health_artifact_path", PAPER_WORKFLOW_PHASE1_HEALTH_BLOCKED),
        ("active_model_metadata_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        ("active_model_pointer_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_ARTIFACT_BLOCKED),
        ("active_model_lineage_matrix_path", PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED),
        ("model_weight_versioning_metadata_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        ("model_weights_reference_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_ARTIFACT_BLOCKED),
        ("model_version_metadata_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_ARTIFACT_BLOCKED),
        ("parameter_version_metadata_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_ARTIFACT_BLOCKED),
        ("training_result_metadata_path", PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_INPUT_BLOCKED),
        ("training_result_rows_path", PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_ROWS_BLOCKED),
        ("metric_extension_result_rows_path", PAPER_WORKFLOW_PHASE1_METRIC_EVIDENCE_BLOCKED),
        ("metric_computation_result_rows_path", PAPER_WORKFLOW_PHASE1_METRIC_EVIDENCE_BLOCKED),
        ("forward_return_label_rows_path", PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED),
        ("replay_decision_freeze_rows_path", PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED),
        ("existing_paper_workflow_status_path", PAPER_WORKFLOW_PHASE1_PAPER_CONTEXT_BLOCKED),
        ("leakage_evidence_bundle_path", PAPER_WORKFLOW_PHASE1_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", PAPER_WORKFLOW_PHASE1_OVERCLAIM_BLOCKED),
        ("side_effect_evidence_bundle_path", PAPER_WORKFLOW_PHASE1_SIDE_EFFECT_BLOCKED),
    ]
    for field, status in missing_checks:
        if not _path_exists(getattr(settings, field)):
            gates.append(_gate(field, status, "missing required input"))
            return status

    status_checks = [
        (settings.stock_profile_metadata_path, "STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        (settings.stock_profile_status_artifact_path, "STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        (settings.active_model_metadata_path, "ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED", PAPER_WORKFLOW_PHASE1_ACTIVE_MODEL_INPUT_BLOCKED),
        (settings.model_weight_versioning_metadata_path, "MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED", PAPER_WORKFLOW_PHASE1_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        (settings.training_result_metadata_path, "TRAINING_RESULT_CREATED", PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_INPUT_BLOCKED),
        (settings.training_result_planning_metadata_path, "TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED", PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_PLANNING_INPUT_BLOCKED),
        (settings.metric_extension_metadata_path, "METRIC_EXTENSION_REPORT_CREATED", PAPER_WORKFLOW_PHASE1_METRIC_EXTENSION_INPUT_BLOCKED),
        (settings.metric_computation_metadata_path, "METRIC_COMPUTATION_REPORT_CREATED", PAPER_WORKFLOW_PHASE1_METRIC_COMPUTATION_INPUT_BLOCKED),
        (settings.metric_evaluation_metadata_path, "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED", PAPER_WORKFLOW_PHASE1_METRIC_EVALUATION_INPUT_BLOCKED),
        (settings.training_evaluation_metadata_path, "TRAINING_EVALUATION_DATASET_CREATED", PAPER_WORKFLOW_PHASE1_TRAINING_EVALUATION_INPUT_BLOCKED),
        (settings.forward_return_label_metadata_path, "FORWARD_RETURN_LABELS_CREATED", PAPER_WORKFLOW_PHASE1_FORWARD_LABEL_INPUT_BLOCKED),
        (settings.replay_decision_freeze_metadata_path, "REPLAY_DECISION_FROZEN", PAPER_WORKFLOW_PHASE1_REPLAY_FREEZE_INPUT_BLOCKED),
    ]
    for path, required, fail_status in status_checks:
        if _read_json_path(path).get("status") != required:
            gates.append(_gate("status", fail_status, f"required {required}"))
            return fail_status
    for path in [
        settings.stock_profile_health_artifact_path,
        settings.active_model_health_artifact_path,
        settings.model_weight_versioning_health_artifact_path,
        settings.training_result_health_artifact_path,
        settings.training_result_planning_health_artifact_path,
        settings.metric_extension_health_artifact_path,
        settings.metric_computation_health_artifact_path,
        settings.metric_evaluation_health_artifact_path,
        settings.training_evaluation_health_artifact_path,
        settings.forward_return_label_health_artifact_path,
        settings.replay_decision_freeze_health_artifact_path,
    ]:
        if path is not None and _path_exists(path) and _read_json_path(path).get("status") != "PASS":
            gates.append(_gate("health", PAPER_WORKFLOW_PHASE1_HEALTH_BLOCKED, "health not PASS"))
            return PAPER_WORKFLOW_PHASE1_HEALTH_BLOCKED

    stock_lineage = _read_csv_path(settings.stock_profile_lineage_matrix_path)
    if "lineage_item" not in stock_lineage.columns:
        return PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED
    rows = _read_csv_path(settings.training_result_rows_path)
    missing = REQUIRED_TRAINING_ROW_COLUMNS - set(rows.columns)
    if "training_result_row_id" in missing:
        return PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_ROWS_BLOCKED
    if missing:
        return PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED
    if rows.empty:
        return PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_ROWS_BLOCKED
    for column in ["source_hash", "revision_id", "available_time", "quality_status"]:
        if rows[column].isna().any() or (rows[column].astype(str).str.strip() == "").any():
            return PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED

    if _read_csv_path(settings.metric_computation_result_rows_path).empty:
        return PAPER_WORKFLOW_PHASE1_METRIC_EVIDENCE_BLOCKED
    if _read_csv_path(settings.metric_extension_result_rows_path).empty:
        return PAPER_WORKFLOW_PHASE1_METRIC_EVIDENCE_BLOCKED
    if not Path(settings.stock_profile_limitations_path).read_text(encoding="utf-8").strip():
        return PAPER_WORKFLOW_PHASE1_LIMITATIONS_BLOCKED
    warnings = _read_csv_path(settings.stock_profile_overfit_warnings_path)
    if warnings.empty:
        return PAPER_WORKFLOW_PHASE1_OVERFIT_WARNING_BLOCKED
    safety = _read_json_path(settings.stock_profile_safety_flags_path)
    if _any_true(safety, DOWNSTREAM_FALSE_FIELDS):
        return PAPER_WORKFLOW_PHASE1_SAFETY_FLAG_BLOCKED

    paper = _read_json_path(settings.existing_paper_workflow_status_path)
    if int(paper.get("approved_count") or 0) > 0 or "APPROVED_FOR_PAPER" in json.dumps(paper):
        return PAPER_WORKFLOW_PHASE1_PAPER_CONTEXT_BLOCKED
    if _unsafe_bundle(settings.leakage_evidence_bundle_path, LEAKAGE_REQUEST_FIELDS):
        return PAPER_WORKFLOW_PHASE1_LEAKAGE_BLOCKED
    overclaim = _read_json_path(settings.overclaim_evidence_bundle_path)
    if _unsafe_bundle(settings.overclaim_evidence_bundle_path, OVERCLAIM_REQUEST_FIELDS) or any(value is False for value in overclaim.values()):
        return PAPER_WORKFLOW_PHASE1_OVERCLAIM_BLOCKED
    if _unsafe_bundle(settings.side_effect_evidence_bundle_path, set(DOWNSTREAM_FALSE_FIELDS) | SIDE_EFFECT_REQUEST_FIELDS):
        return PAPER_WORKFLOW_PHASE1_SIDE_EFFECT_BLOCKED
    gates.append(_gate("ready", READY_FOR_PAPER_WORKFLOW_PHASE1, "all gates passed"))
    return READY_FOR_PAPER_WORKFLOW_PHASE1


def _build_result(
    settings: PaperWorkflowPhase1Settings,
    artifact_paths: dict[str, Path],
    run_id: str,
    status: str,
    workflow_stage: str,
    source: dict[str, Any],
    gates: list[PaperWorkflowPhase1GateResult],
) -> PaperWorkflowPhase1Result:
    created = status == PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED
    ready = status in {READY_FOR_PAPER_WORKFLOW_PHASE1, PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED}
    return PaperWorkflowPhase1Result(
        paper_workflow_run_id=run_id,
        status=status,
        workflow_stage=workflow_stage,
        ready_for_paper_workflow_phase1=ready,
        paper_workflow_phase1_executed=created,
        paper_workflow_phase1_report_only_artifacts_created=created,
        paper_workflow_metadata_created=created,
        paper_workflow_input_index_created=created,
        paper_workflow_lineage_matrix_created=created,
        paper_candidate_review_context_created=created,
        paper_decision_draft_created=created,
        paper_review_queue_created=created,
        paper_workflow_limitations_created=created,
        paper_workflow_overfit_warnings_created=created,
        paper_workflow_safety_flags_created=True,
        source_stock_profile_run_id=str(source.get("stock_profile_run_id", "")),
        source_stock_profile_status=str(source.get("stock_profile_status", "")),
        source_stock_profile_health_status=str(source.get("stock_profile_health_status", "")),
        source_active_model_run_id=str(source.get("active_model_run_id", "")),
        source_active_model_status=str(source.get("active_model_status", "")),
        source_active_model_health_status=str(source.get("active_model_health_status", "")),
        source_model_workflow_run_id=str(source.get("model_workflow_run_id", "")),
        source_model_weight_versioning_status=str(source.get("model_weight_versioning_status", "")),
        source_model_weight_versioning_health_status=str(source.get("model_weight_versioning_health_status", "")),
        model_weight_reference_id=str(source.get("model_weight_reference_id", "")),
        model_version_id=str(source.get("model_version_id", "")),
        parameter_version_id=str(source.get("parameter_version_id", "")),
        **{field: False for field in DOWNSTREAM_FALSE_FIELDS},
        report_only=True,
        research_governed=settings.research_governed,
        diagnostic_output=settings.diagnostic_output,
        artifact_path=str(Path(artifact_paths["paper_workflow_metadata"]).parent),
        artifact_paths=artifact_paths,
        gate_results=gates,
    )


def _source_summary(settings: PaperWorkflowPhase1Settings) -> dict[str, Any]:
    stock = _read_json_path(settings.stock_profile_metadata_path)
    active = _read_json_path(settings.active_model_metadata_path)
    model = _read_json_path(settings.model_weight_versioning_metadata_path)
    return {
        "stock_profile_run_id": stock.get("stock_profile_run_id", ""),
        "stock_profile_status": stock.get("status", ""),
        "stock_profile_health_status": _read_json_path(settings.stock_profile_health_artifact_path).get("status", ""),
        "active_model_run_id": stock.get("source_active_model_run_id") or active.get("active_model_run_id", ""),
        "active_model_status": active.get("status", ""),
        "active_model_health_status": _read_json_path(settings.active_model_health_artifact_path).get("status", ""),
        "model_workflow_run_id": stock.get("source_model_workflow_run_id") or model.get("model_workflow_run_id", ""),
        "model_weight_versioning_status": model.get("status", ""),
        "model_weight_versioning_health_status": _read_json_path(settings.model_weight_versioning_health_artifact_path).get("status", ""),
        "model_weight_reference_id": stock.get("model_weight_reference_id") or model.get("model_weight_reference_id", ""),
        "model_version_id": stock.get("model_version_id") or model.get("model_version_id", ""),
        "parameter_version_id": stock.get("parameter_version_id") or model.get("parameter_version_id", ""),
    }


def _metadata(result: PaperWorkflowPhase1Result, source: dict[str, Any]) -> dict[str, Any]:
    return {
        "paper_workflow_run_id": result.paper_workflow_run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "execution_status": result.status,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "ready_for_paper_workflow_phase1": result.ready_for_paper_workflow_phase1,
        "paper_workflow_phase1_executed": result.paper_workflow_phase1_executed,
        "paper_workflow_phase1_report_only_artifacts_created": result.paper_workflow_phase1_report_only_artifacts_created,
        "source_stock_profile_run_id": result.source_stock_profile_run_id,
        "source_stock_profile_status": result.source_stock_profile_status,
        "source_stock_profile_health_status": result.source_stock_profile_health_status,
        "source_active_model_run_id": result.source_active_model_run_id,
        "source_active_model_status": result.source_active_model_status,
        "source_active_model_health_status": result.source_active_model_health_status,
        "source_model_workflow_run_id": result.source_model_workflow_run_id,
        "source_model_weight_versioning_status": result.source_model_weight_versioning_status,
        "source_model_weight_versioning_health_status": result.source_model_weight_versioning_health_status,
        "model_weight_reference_id": result.model_weight_reference_id,
        "model_version_id": result.model_version_id,
        "parameter_version_id": result.parameter_version_id,
        "training_result_row_count": 0,
        "eligible_training_result_row_count": 0,
        "quarantined_training_result_row_count": 0,
        "metric_evidence_names_present": "",
        "metric_evidence_reference_count": 0,
        **{key: getattr(result, key) for key in [
            "paper_workflow_metadata_created",
            "paper_workflow_input_index_created",
            "paper_workflow_lineage_matrix_created",
            "paper_candidate_review_context_created",
            "paper_decision_draft_created",
            "paper_review_queue_created",
            "paper_workflow_limitations_created",
            "paper_workflow_overfit_warnings_created",
            "paper_workflow_safety_flags_created",
        ]},
        **_safety_flags(result),
    }


def _safety_flags(result: PaperWorkflowPhase1Result) -> dict[str, Any]:
    return {
        "paper_workflow_phase1_report_only_artifacts_created": result.paper_workflow_phase1_report_only_artifacts_created,
        "paper_workflow_metadata_created": result.paper_workflow_metadata_created,
        "paper_workflow_input_index_created": result.paper_workflow_input_index_created,
        "paper_workflow_lineage_matrix_created": result.paper_workflow_lineage_matrix_created,
        "paper_candidate_review_context_created": result.paper_candidate_review_context_created,
        "paper_decision_draft_created": result.paper_decision_draft_created,
        "paper_review_queue_created": result.paper_review_queue_created,
        "paper_workflow_limitations_created": result.paper_workflow_limitations_created,
        "paper_workflow_overfit_warnings_created": result.paper_workflow_overfit_warnings_created,
        "paper_workflow_safety_flags_created": result.paper_workflow_safety_flags_created,
        **{field: getattr(result, field) for field in DOWNSTREAM_FALSE_FIELDS},
        "report_only": True,
        "research_governed": True,
        "diagnostic_output": True,
    }


def _write_input_index(path: Path, settings: PaperWorkflowPhase1Settings) -> None:
    rows = []
    for field, value in settings.__dict__.items():
        if field.endswith("_path") and value is not None:
            rows.append({"source_artifact": field, "path": str(value), "exists": Path(value).exists(), "row_count": _row_count(value)})
    pd.DataFrame(rows).to_csv(path, index=False)


def _write_lineage_matrix(path: Path, result: PaperWorkflowPhase1Result, settings: PaperWorkflowPhase1Settings, source: dict[str, Any]) -> None:
    rows = _read_csv_path(settings.training_result_rows_path).head(1).to_dict("records") or [{}]
    row = rows[0]
    payload = {
        "paper_workflow_run_id": result.paper_workflow_run_id,
        "stock_profile_run_id": result.source_stock_profile_run_id,
        "active_model_run_id": result.source_active_model_run_id,
        "model_workflow_run_id": result.source_model_workflow_run_id,
        "model_weight_reference_id": result.model_weight_reference_id,
        "model_version_id": result.model_version_id,
        "parameter_version_id": result.parameter_version_id,
        **{column: row.get(column, "") for column in REQUIRED_TRAINING_ROW_COLUMNS},
        "instrument_type": row.get("instrument_type", ""),
        "benchmark_id": row.get("benchmark_id", ""),
        "benchmark_name": row.get("benchmark_name", ""),
        "industry_id": row.get("industry_id", ""),
        "industry_name": row.get("industry_name", ""),
        "market_regime_id": row.get("market_regime_id", ""),
        "factor_layer": row.get("factor_layer", ""),
        "factor_id": row.get("factor_id", ""),
        "factor_name": row.get("factor_name", ""),
        "metric_name": row.get("metric_name", ""),
        "metric_value": row.get("metric_value", ""),
        "numerator_count": row.get("numerator_count", ""),
        "denominator_count": row.get("denominator_count", ""),
        "report_only": True,
        "diagnostic_only": True,
        "research_governed": True,
    }
    pd.DataFrame([payload]).to_csv(path, index=False)


def _write_candidate_context(path: Path, settings: PaperWorkflowPhase1Settings, result: PaperWorkflowPhase1Result) -> None:
    row = (_read_csv_path(settings.training_result_rows_path).head(1).to_dict("records") or [{}])[0]
    pd.DataFrame([{
        "paper_workflow_run_id": result.paper_workflow_run_id,
        "symbol": row.get("symbol", ""),
        "human_review_context": "review only context",
        "draft_review_label": "PAPER_REVIEW_DRAFT",
        "source_stock_profile_run_id": result.source_stock_profile_run_id,
        "performance_validation": False,
        "paper_approval": False,
    }]).to_csv(path, index=False)


def _write_decision_draft(path: Path, settings: PaperWorkflowPhase1Settings, result: PaperWorkflowPhase1Result) -> None:
    row = (_read_csv_path(settings.training_result_rows_path).head(1).to_dict("records") or [{}])[0]
    pd.DataFrame([{
        "paper_workflow_run_id": result.paper_workflow_run_id,
        "symbol": row.get("symbol", ""),
        "draft_review_label": "PAPER_REVIEW_DRAFT",
        "review_note": "human review required",
    }]).to_csv(path, index=False)


def _write_review_queue(path: Path, settings: PaperWorkflowPhase1Settings, result: PaperWorkflowPhase1Result) -> None:
    row = (_read_csv_path(settings.training_result_rows_path).head(1).to_dict("records") or [{}])[0]
    pd.DataFrame([{
        "paper_workflow_run_id": result.paper_workflow_run_id,
        "queue_position": 1,
        "symbol": row.get("symbol", ""),
        "review_task": "human_review_required",
        "review_status": "NEEDS_HUMAN_REVIEW",
    }]).to_csv(path, index=False)


def _limitations_text() -> str:
    return "\n".join([
        "# Paper Workflow Phase 1 Limitations",
        "",
        "- phase 1 is report-only;",
        "- paper workflow phase 1 does not create `APPROVED_FOR_PAPER`;",
        "- no real buy-review eligibility;",
        "- no strategy performance validation;",
        "- no current-candidates integration;",
        "- no snapshot integration;",
        "- no signal_semantics mutation;",
        "- no active stock_profile;",
        "- no promoted model;",
        "- no production model;",
        "- no active thresholds;",
        "- no advisory predictions;",
        "- no active probabilities;",
        "- no broker/order/message/API/trading;",
        "- paper decisions are human-review artifacts, not trading instructions;",
        "- metrics are evidence only, not profitability proof;",
        "- PIT lineage and source governance remain required;",
        "- fill/slippage assumptions remain future separate validation.",
    ])


def _recommended_next_task(result: PaperWorkflowPhase1Result) -> str:
    if result.paper_workflow_phase1_report_only_artifacts_created:
        return "# Recommended Next Task\n\nPaper Workflow Phase 1 Artifact Views Report-Only v0.1\n"
    if result.ready_for_paper_workflow_phase1:
        return "# Recommended Next Task\n\nRerun with --allow-paper-workflow-phase1 only if exact approval remains valid.\n"
    return "# Recommended Next Task\n\nResolve Paper Workflow Phase 1 blockers before creating report-only artifacts.\n"


def _has_input(settings: PaperWorkflowPhase1Settings) -> bool:
    ignored = {"output_dir", "allow_paper_workflow_phase1", "write_artifacts", "research_governed", "diagnostic_output"}
    return any(getattr(settings, field) is not None for field in settings.__dataclass_fields__ if field not in ignored)


def _unsafe_request_status(request: dict[str, Any]) -> str | None:
    if any(request.get(field) for field in OVERCLAIM_REQUEST_FIELDS):
        return PAPER_WORKFLOW_PHASE1_OVERCLAIM_BLOCKED
    if any(request.get(field) for field in LEAKAGE_REQUEST_FIELDS):
        return PAPER_WORKFLOW_PHASE1_LEAKAGE_BLOCKED
    if any(request.get(field) for field in SIDE_EFFECT_REQUEST_FIELDS):
        return PAPER_WORKFLOW_PHASE1_SIDE_EFFECT_BLOCKED
    return None


def _output_under_manual_diagnostics(output_dir: str | Path) -> bool:
    parts = [part.lower() for part in Path(output_dir).parts]
    needle = ["outputs", "reports", "manual_diagnostics"]
    return any(parts[index : index + 3] == needle for index in range(max(len(parts) - 2, 0)))


def _has_forbidden_artifact(output_dir: Path) -> bool:
    if not output_dir.exists():
        return False
    forbidden = [
        "approved_for_paper",
        "real_buy_review",
        "performance_validation",
        "current_candidates",
        "snapshot",
        "signal_semantics",
        "broker",
        "order",
        "trading",
        "active_stock_profile",
        "promoted_model",
        "production_model",
        "active_threshold",
        "advisory_prediction",
        "active_probability",
    ]
    return any(any(token in path.name.lower() for token in forbidden) for path in output_dir.rglob("*") if path.is_file())


def _read_json_path(path: str | Path | None) -> dict[str, Any]:
    if path is None or not Path(path).exists():
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv_path(path: str | Path | None) -> pd.DataFrame:
    if path is None or not Path(path).exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str)


def _path_exists(path: str | Path | None) -> bool:
    return path is not None and Path(path).exists()


def _any_true(payload: dict[str, Any], fields: list[str]) -> bool:
    return any(payload.get(field) is True or str(payload.get(field)).lower() == "true" for field in fields)


def _unsafe_bundle(path: str | Path | None, fields: set[str]) -> bool:
    payload = _read_json_path(path)
    return any(payload.get(field) is True or str(payload.get(field)).lower() == "true" for field in fields)


def _row_count(path: str | Path) -> int:
    if str(path).lower().endswith(".csv"):
        try:
            return len(pd.read_csv(path, dtype=str))
        except Exception:
            return 0
    return 1


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_gate_csv(path: Path, gates: list[PaperWorkflowPhase1GateResult]) -> None:
    pd.DataFrame([gate.__dict__ for gate in gates]).to_csv(path, index=False)


def _gate(gate: str, status: str, message: str) -> PaperWorkflowPhase1GateResult:
    return PaperWorkflowPhase1GateResult(gate=gate, status=status, message=message)


def _run_id(settings: PaperWorkflowPhase1Settings) -> str:
    payload = {
        key: str(value)
        for key, value in settings.__dict__.items()
        if key not in {"write_artifacts"}
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]
