"""Report-only APPROVED_FOR_PAPER Phase 1 artifact workflow."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_APPROVED_FOR_PAPER_PHASE1_INPUT = "NO_APPROVED_FOR_PAPER_PHASE1_INPUT"
APPROVED_FOR_PAPER_PHASE1_APPROVAL_BLOCKED = "APPROVED_FOR_PAPER_PHASE1_APPROVAL_BLOCKED"
APPROVED_FOR_PAPER_PHASE1_FORBIDDEN_ARTIFACT_BLOCKED = "APPROVED_FOR_PAPER_PHASE1_FORBIDDEN_ARTIFACT_BLOCKED"
APPROVED_FOR_PAPER_PHASE1_HEALTH_BLOCKED = "APPROVED_FOR_PAPER_PHASE1_HEALTH_BLOCKED"
APPROVED_FOR_PAPER_PHASE1_LEAKAGE_BLOCKED = "APPROVED_FOR_PAPER_PHASE1_LEAKAGE_BLOCKED"
APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED = "APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED"
APPROVED_FOR_PAPER_PHASE1_METRIC_EVIDENCE_BLOCKED = "APPROVED_FOR_PAPER_PHASE1_METRIC_EVIDENCE_BLOCKED"
APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED = "APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED"
APPROVED_FOR_PAPER_PHASE1_OVERFIT_WARNING_BLOCKED = "APPROVED_FOR_PAPER_PHASE1_OVERFIT_WARNING_BLOCKED"
APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_ARTIFACT_BLOCKED = (
    "APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_ARTIFACT_BLOCKED"
)
APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_INPUT_BLOCKED = "APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_INPUT_BLOCKED"
APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED = "APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED"
APPROVED_FOR_PAPER_PHASE1_SAFETY_FLAG_BLOCKED = "APPROVED_FOR_PAPER_PHASE1_SAFETY_FLAG_BLOCKED"
APPROVED_FOR_PAPER_PHASE1_SIDE_EFFECT_BLOCKED = "APPROVED_FOR_PAPER_PHASE1_SIDE_EFFECT_BLOCKED"
APPROVED_FOR_PAPER_PHASE1_STOCK_PROFILE_INPUT_BLOCKED = "APPROVED_FOR_PAPER_PHASE1_STOCK_PROFILE_INPUT_BLOCKED"
APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_INPUT_BLOCKED = "APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_INPUT_BLOCKED"
APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_PLANNING_INPUT_BLOCKED = (
    "APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_PLANNING_INPUT_BLOCKED"
)
APPROVED_FOR_PAPER_PHASE1_TRAINING_EVALUATION_INPUT_BLOCKED = (
    "APPROVED_FOR_PAPER_PHASE1_TRAINING_EVALUATION_INPUT_BLOCKED"
)
READY_FOR_APPROVED_FOR_PAPER_PHASE1 = "READY_FOR_APPROVED_FOR_PAPER_PHASE1"

EXACT_APPROVED_FOR_PAPER_PHASE1_APPROVAL_TEXT = (
    "I explicitly authorize only APPROVED_FOR_PAPER Phase 1, limited to report-only approved-for-paper "
    "phase-1 metadata / lineage / review-context / decision-draft / safety artifacts. It may create "
    "approved_for_paper_metadata, approved_for_paper_input_index, approved_for_paper_lineage_matrix, "
    "approved_for_paper_review_context, approved_for_paper_decision_draft, approved_for_paper_limitations, "
    "approved_for_paper_overfit_warnings, approved_for_paper_safety_flags, gate/precondition results, "
    "recommended_next_task, and similar report-only APPROVED_FOR_PAPER phase-1 artifacts only when immutable "
    "PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED, STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED, "
    "ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED, MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED, "
    "TRAINING_RESULT_CREATED, TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED, METRIC_EXTENSION_REPORT_CREATED, "
    "METRIC_COMPUTATION_REPORT_CREATED, METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED, "
    "TRAINING_EVALUATION_DATASET_CREATED, FORWARD_RETURN_LABELS_CREATED, and REPLAY_DECISION_FROZEN artifacts "
    "have complete lineage and PASS health. This phase must not create real buy-review eligibility, strategy "
    "performance validation, current-candidates integration, snapshots, signal_semantics mutation, active "
    "stock_profile, promoted model, production model, active thresholds, advisory predictions, active "
    "probabilities, broker/order/message/API integration, or trading. If any upstream lineage, health, "
    "available_time, source_hash, revision_id, quality_status, report_only/diagnostic_only, research_governed, "
    "metric evidence, training_result rows, paper workflow artifacts, limitations, overfit warnings, safety "
    "flags, or exact approval are missing, it must fail closed and create no APPROVED_FOR_PAPER phase-1 "
    "report-only artifacts."
)

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/approved_for_paper_phase1_v0_1")

ARTIFACT_FILES = {
    "approved_for_paper_metadata": "approved_for_paper_metadata.json",
    "approved_for_paper_input_index": "approved_for_paper_input_index.csv",
    "approved_for_paper_lineage_matrix": "approved_for_paper_lineage_matrix.csv",
    "approved_for_paper_review_context": "approved_for_paper_review_context.csv",
    "approved_for_paper_decision_draft": "approved_for_paper_decision_draft.csv",
    "approved_for_paper_limitations": "approved_for_paper_limitations.md",
    "approved_for_paper_overfit_warnings": "approved_for_paper_overfit_warnings.csv",
    "approved_for_paper_safety_flags": "approved_for_paper_safety_flags.json",
    "approved_for_paper_precondition_results": "approved_for_paper_precondition_results.csv",
    "approved_for_paper_approval_results": "approved_for_paper_approval_results.csv",
    "approved_for_paper_upstream_lineage_results": "approved_for_paper_upstream_lineage_results.csv",
    "approved_for_paper_paper_workflow_input_results": "approved_for_paper_paper_workflow_input_results.csv",
    "approved_for_paper_leakage_guard_results": "approved_for_paper_leakage_guard_results.csv",
    "approved_for_paper_side_effect_guard_results": "approved_for_paper_side_effect_guard_results.csv",
    "approved_for_paper_overclaim_guard_results": "approved_for_paper_overclaim_guard_results.csv",
    "recommended_next_task": "recommended_next_task.md",
}

SUBSTANTIVE_ARTIFACT_KEYS = {
    "approved_for_paper_input_index",
    "approved_for_paper_lineage_matrix",
    "approved_for_paper_review_context",
    "approved_for_paper_decision_draft",
    "approved_for_paper_limitations",
    "approved_for_paper_overfit_warnings",
}

DOWNSTREAM_FALSE_FIELDS = [
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

REQUIRED_OVERFIT_WARNINGS = {
    "small sample",
    "class imbalance",
    "single-stock overfit",
    "approved-for-paper overfit",
    "lookahead leakage",
    "paper-overfit risk",
}

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

FORBIDDEN_ARTIFACT_TOKENS = [
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


@dataclass(frozen=True)
class ApprovedForPaperPhase1Settings:
    approval_manifest_path: str | Path | None = None
    approved_for_paper_request_manifest_path: str | Path | None = None
    paper_workflow_metadata_path: str | Path | None = None
    paper_workflow_input_index_path: str | Path | None = None
    paper_workflow_lineage_matrix_path: str | Path | None = None
    paper_workflow_review_context_path: str | Path | None = None
    paper_workflow_decision_draft_path: str | Path | None = None
    paper_workflow_limitations_path: str | Path | None = None
    paper_workflow_overfit_warnings_path: str | Path | None = None
    paper_workflow_safety_flags_path: str | Path | None = None
    paper_workflow_status_artifact_path: str | Path | None = None
    paper_workflow_health_artifact_path: str | Path | None = None
    stock_profile_metadata_path: str | Path | None = None
    stock_profile_status_artifact_path: str | Path | None = None
    stock_profile_health_artifact_path: str | Path | None = None
    active_model_metadata_path: str | Path | None = None
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
    leakage_evidence_bundle_path: str | Path | None = None
    overclaim_evidence_bundle_path: str | Path | None = None
    side_effect_evidence_bundle_path: str | Path | None = None
    allow_approved_for_paper_phase1: bool = False
    output_dir: str | Path = DEFAULT_OUTPUT_DIR
    write_artifacts: bool = True
    research_governed: bool = True
    diagnostic_output: bool = True


@dataclass(frozen=True)
class ApprovedForPaperPhase1GateResult:
    gate: str
    status: str
    message: str


@dataclass(frozen=True)
class ApprovedForPaperPhase1Result:
    approved_for_paper_run_id: str
    status: str
    workflow_stage: str
    ready_for_approved_for_paper_phase1: bool
    approved_for_paper_phase1_executed: bool
    approved_for_paper_phase1_report_only_artifacts_created: bool
    approved_for_paper_metadata_created: bool
    approved_for_paper_input_index_created: bool
    approved_for_paper_lineage_matrix_created: bool
    approved_for_paper_review_context_created: bool
    approved_for_paper_decision_draft_created: bool
    approved_for_paper_limitations_created: bool
    approved_for_paper_overfit_warnings_created: bool
    approved_for_paper_safety_flags_created: bool
    scoped_approved_for_paper_phase1: bool
    scoped_approved_for_paper: bool
    approved_for_paper_scope: str
    source_paper_workflow_phase1_run_id: str
    source_paper_workflow_phase1_status: str
    source_paper_workflow_phase1_health_status: str
    source_stock_profile_run_id: str
    source_stock_profile_status: str
    source_stock_profile_health_status: str
    source_active_model_run_id: str
    source_active_model_status: str
    source_active_model_health_status: str
    source_model_workflow_run_id: str
    source_model_weight_versioning_status: str
    source_model_weight_versioning_health_status: str
    source_training_result_run_id: str
    source_training_result_status: str
    source_training_result_health_status: str
    source_training_result_planning_run_id: str
    source_training_result_planning_status: str
    source_training_result_planning_health_status: str
    source_metric_extension_run_id: str
    source_metric_extension_status: str
    source_metric_extension_health_status: str
    source_metric_computation_run_id: str
    source_metric_computation_status: str
    source_metric_computation_health_status: str
    source_metric_evaluation_planning_run_id: str
    source_metric_evaluation_status: str
    source_metric_evaluation_health_status: str
    source_training_evaluation_run_id: str
    source_training_evaluation_status: str
    source_training_evaluation_health_status: str
    source_forward_return_label_run_id: str
    source_forward_return_label_status: str
    source_forward_return_label_health_status: str
    source_replay_decision_freeze_run_id: str
    source_replay_decision_freeze_status: str
    source_replay_decision_freeze_health_status: str
    model_weight_reference_id: str
    model_version_id: str
    parameter_version_id: str
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
    gate_results: list[ApprovedForPaperPhase1GateResult]


def run_approved_for_paper_phase1(
    settings: ApprovedForPaperPhase1Settings | None = None,
) -> ApprovedForPaperPhase1Result:
    settings = settings or ApprovedForPaperPhase1Settings()
    run_id = _run_id(settings)
    artifact_dir = Path(settings.output_dir) / run_id
    artifact_paths = {key: artifact_dir / filename for key, filename in ARTIFACT_FILES.items()}
    source = _source_summary(settings)
    gates: list[ApprovedForPaperPhase1GateResult] = []

    if not _has_input(settings):
        result = _build_result(
            settings,
            artifact_paths,
            run_id,
            NO_APPROVED_FOR_PAPER_PHASE1_INPUT,
            "APPROVED_FOR_PAPER_PHASE1_NO_INPUT",
            source,
            gates,
        )
        return write_approved_for_paper_phase1_artifacts(result, settings, artifact_paths, source)

    status = _validate(settings, source, gates)
    if status != READY_FOR_APPROVED_FOR_PAPER_PHASE1:
        result = _build_result(settings, artifact_paths, run_id, status, status, source, gates)
        return write_approved_for_paper_phase1_artifacts(result, settings, artifact_paths, source)

    if settings.allow_approved_for_paper_phase1:
        status = APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED
    result = _build_result(settings, artifact_paths, run_id, status, status, source, gates)
    return write_approved_for_paper_phase1_artifacts(result, settings, artifact_paths, source)


def write_approved_for_paper_phase1_artifacts(
    result: ApprovedForPaperPhase1Result,
    settings: ApprovedForPaperPhase1Settings,
    artifact_paths: dict[str, Path],
    source: dict[str, Any],
) -> ApprovedForPaperPhase1Result:
    if not settings.write_artifacts:
        return result
    artifact_dir = Path(result.artifact_path)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    _write_json(artifact_paths["approved_for_paper_metadata"], _metadata(result, source))
    _write_json(artifact_paths["approved_for_paper_safety_flags"], _safety_flags(result))
    _write_gate_csv(
        artifact_paths["approved_for_paper_precondition_results"],
        result.gate_results or [_gate("precondition", result.status, result.workflow_stage)],
    )
    _write_gate_csv(
        artifact_paths["approved_for_paper_approval_results"],
        [gate for gate in result.gate_results if "approval" in gate.gate]
        or [_gate("approval", result.status, result.status)],
    )
    _write_gate_csv(
        artifact_paths["approved_for_paper_upstream_lineage_results"],
        [gate for gate in result.gate_results if "lineage" in gate.gate]
        or [_gate("upstream_lineage", result.status, result.status)],
    )
    _write_gate_csv(
        artifact_paths["approved_for_paper_paper_workflow_input_results"],
        [gate for gate in result.gate_results if "paper_workflow" in gate.gate]
        or [_gate("paper_workflow_input", result.status, result.status)],
    )
    _write_gate_csv(
        artifact_paths["approved_for_paper_leakage_guard_results"],
        [gate for gate in result.gate_results if "leakage" in gate.gate]
        or [_gate("leakage_guard", result.status, result.status)],
    )
    _write_gate_csv(
        artifact_paths["approved_for_paper_side_effect_guard_results"],
        [gate for gate in result.gate_results if "side_effect" in gate.gate]
        or [_gate("side_effect_guard", result.status, result.status)],
    )
    _write_gate_csv(
        artifact_paths["approved_for_paper_overclaim_guard_results"],
        [gate for gate in result.gate_results if "overclaim" in gate.gate]
        or [_gate("overclaim_guard", result.status, result.status)],
    )
    artifact_paths["recommended_next_task"].write_text(_recommended_next_task(result), encoding="utf-8")

    if result.approved_for_paper_phase1_report_only_artifacts_created:
        _write_input_index(artifact_paths["approved_for_paper_input_index"], settings)
        _write_lineage_matrix(artifact_paths["approved_for_paper_lineage_matrix"], result, settings, source)
        _write_review_context(artifact_paths["approved_for_paper_review_context"], result, settings)
        _write_decision_draft(artifact_paths["approved_for_paper_decision_draft"], result, settings)
        artifact_paths["approved_for_paper_limitations"].write_text(_limitations_text(), encoding="utf-8")
        _write_overfit_warnings(artifact_paths["approved_for_paper_overfit_warnings"])

    return result


def _build_result(
    settings: ApprovedForPaperPhase1Settings,
    artifact_paths: dict[str, Path],
    run_id: str,
    status: str,
    stage: str,
    source: dict[str, Any],
    gates: list[ApprovedForPaperPhase1GateResult],
) -> ApprovedForPaperPhase1Result:
    created = status == APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED
    ready = status in {READY_FOR_APPROVED_FOR_PAPER_PHASE1, APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED}
    return ApprovedForPaperPhase1Result(
        approved_for_paper_run_id=run_id,
        status=status,
        workflow_stage=stage,
        ready_for_approved_for_paper_phase1=ready,
        approved_for_paper_phase1_executed=created,
        approved_for_paper_phase1_report_only_artifacts_created=created,
        approved_for_paper_metadata_created=created,
        approved_for_paper_input_index_created=created,
        approved_for_paper_lineage_matrix_created=created,
        approved_for_paper_review_context_created=created,
        approved_for_paper_decision_draft_created=created,
        approved_for_paper_limitations_created=created,
        approved_for_paper_overfit_warnings_created=created,
        approved_for_paper_safety_flags_created=True,
        scoped_approved_for_paper_phase1=created,
        scoped_approved_for_paper=created,
        approved_for_paper_scope="report_only_phase1_artifact_state_only" if created else "",
        source_paper_workflow_phase1_run_id=source.get("paper_workflow_run_id", ""),
        source_paper_workflow_phase1_status=source.get("paper_workflow_status", ""),
        source_paper_workflow_phase1_health_status=source.get("paper_workflow_health_status", ""),
        source_stock_profile_run_id=source.get("stock_profile_run_id", ""),
        source_stock_profile_status=source.get("stock_profile_status", ""),
        source_stock_profile_health_status=source.get("stock_profile_health_status", ""),
        source_active_model_run_id=source.get("active_model_run_id", ""),
        source_active_model_status=source.get("active_model_status", ""),
        source_active_model_health_status=source.get("active_model_health_status", ""),
        source_model_workflow_run_id=source.get("model_workflow_run_id", ""),
        source_model_weight_versioning_status=source.get("model_weight_versioning_status", ""),
        source_model_weight_versioning_health_status=source.get("model_weight_versioning_health_status", ""),
        source_training_result_run_id=source.get("training_result_run_id", ""),
        source_training_result_status=source.get("training_result_status", ""),
        source_training_result_health_status=source.get("training_result_health_status", ""),
        source_training_result_planning_run_id=source.get("training_result_planning_run_id", ""),
        source_training_result_planning_status=source.get("training_result_planning_status", ""),
        source_training_result_planning_health_status=source.get("training_result_planning_health_status", ""),
        source_metric_extension_run_id=source.get("metric_extension_run_id", ""),
        source_metric_extension_status=source.get("metric_extension_status", ""),
        source_metric_extension_health_status=source.get("metric_extension_health_status", ""),
        source_metric_computation_run_id=source.get("metric_computation_run_id", ""),
        source_metric_computation_status=source.get("metric_computation_status", ""),
        source_metric_computation_health_status=source.get("metric_computation_health_status", ""),
        source_metric_evaluation_planning_run_id=source.get("metric_evaluation_planning_run_id", ""),
        source_metric_evaluation_status=source.get("metric_evaluation_status", ""),
        source_metric_evaluation_health_status=source.get("metric_evaluation_health_status", ""),
        source_training_evaluation_run_id=source.get("training_evaluation_run_id", ""),
        source_training_evaluation_status=source.get("training_evaluation_status", ""),
        source_training_evaluation_health_status=source.get("training_evaluation_health_status", ""),
        source_forward_return_label_run_id=source.get("forward_return_label_run_id", ""),
        source_forward_return_label_status=source.get("forward_return_label_status", ""),
        source_forward_return_label_health_status=source.get("forward_return_label_health_status", ""),
        source_replay_decision_freeze_run_id=source.get("replay_decision_freeze_run_id", ""),
        source_replay_decision_freeze_status=source.get("replay_decision_freeze_status", ""),
        source_replay_decision_freeze_health_status=source.get("replay_decision_freeze_health_status", ""),
        model_weight_reference_id=source.get("model_weight_reference_id", ""),
        model_version_id=source.get("model_version_id", ""),
        parameter_version_id=source.get("parameter_version_id", ""),
        **{field: False for field in DOWNSTREAM_FALSE_FIELDS},
        report_only=True,
        research_governed=settings.research_governed,
        diagnostic_output=settings.diagnostic_output,
        artifact_path=str(Path(settings.output_dir) / run_id),
        artifact_paths=artifact_paths,
        gate_results=gates,
    )


def _validate(
    settings: ApprovedForPaperPhase1Settings,
    source: dict[str, Any],
    gates: list[ApprovedForPaperPhase1GateResult],
) -> str:
    if not _output_under_manual_diagnostics(settings.output_dir):
        return _block(gates, "side_effect_output_boundary", APPROVED_FOR_PAPER_PHASE1_SIDE_EFFECT_BLOCKED)
    if _has_forbidden_artifact(Path(settings.output_dir)):
        return _block(gates, "forbidden_artifact", APPROVED_FOR_PAPER_PHASE1_FORBIDDEN_ARTIFACT_BLOCKED)

    approval = _read_json_path(settings.approval_manifest_path)
    if approval.get("approval_text") != EXACT_APPROVED_FOR_PAPER_PHASE1_APPROVAL_TEXT:
        return _block(gates, "exact_approval", APPROVED_FOR_PAPER_PHASE1_APPROVAL_BLOCKED)

    request = _read_json_path(settings.approved_for_paper_request_manifest_path)
    unsafe = _unsafe_request_status(request)
    if unsafe is not None:
        return _block(gates, "request_scope", unsafe)

    paper_required = {
        "paper_workflow_metadata_path": APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_INPUT_BLOCKED,
        "paper_workflow_status_artifact_path": APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_INPUT_BLOCKED,
        "paper_workflow_health_artifact_path": APPROVED_FOR_PAPER_PHASE1_HEALTH_BLOCKED,
        "paper_workflow_input_index_path": APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_ARTIFACT_BLOCKED,
        "paper_workflow_lineage_matrix_path": APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED,
        "paper_workflow_review_context_path": APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_ARTIFACT_BLOCKED,
        "paper_workflow_decision_draft_path": APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_ARTIFACT_BLOCKED,
        "paper_workflow_limitations_path": APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_ARTIFACT_BLOCKED,
        "paper_workflow_overfit_warnings_path": APPROVED_FOR_PAPER_PHASE1_OVERFIT_WARNING_BLOCKED,
        "paper_workflow_safety_flags_path": APPROVED_FOR_PAPER_PHASE1_SAFETY_FLAG_BLOCKED,
    }
    for field, status in paper_required.items():
        if not _path_exists(getattr(settings, field)):
            return _block(gates, field, status)

    if source.get("paper_workflow_status") != "PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED":
        return _block(gates, "paper_workflow_status", APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_INPUT_BLOCKED)
    if source.get("paper_workflow_health_status") != "PASS":
        return _block(gates, "paper_workflow_health", APPROVED_FOR_PAPER_PHASE1_HEALTH_BLOCKED)
    if not _truthy(_read_json_path(settings.paper_workflow_safety_flags_path).get("paper_workflow_phase1_report_only_artifacts_created")):
        return _block(gates, "paper_workflow_safety_flags", APPROVED_FOR_PAPER_PHASE1_SAFETY_FLAG_BLOCKED)

    paper_lineage = _read_csv_path(settings.paper_workflow_lineage_matrix_path)
    if "paper_workflow_run_id" not in paper_lineage.columns:
        return _block(gates, "paper_workflow_lineage_columns", APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED)
    for field in [
        "stock_profile_metadata_path",
        "stock_profile_status_artifact_path",
        "stock_profile_health_artifact_path",
        "active_model_metadata_path",
        "active_model_status_artifact_path",
        "active_model_health_artifact_path",
        "model_weight_versioning_metadata_path",
        "model_weights_reference_path",
        "model_version_metadata_path",
        "parameter_version_metadata_path",
        "model_weight_versioning_status_artifact_path",
        "model_weight_versioning_health_artifact_path",
    ]:
        if not _path_exists(getattr(settings, field)):
            return _block(gates, field, APPROVED_FOR_PAPER_PHASE1_STOCK_PROFILE_INPUT_BLOCKED)

    if source.get("stock_profile_status") != "STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED":
        return _block(gates, "stock_profile_status", APPROVED_FOR_PAPER_PHASE1_STOCK_PROFILE_INPUT_BLOCKED)
    if source.get("active_model_status") != "ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED":
        return _block(gates, "active_model_status", APPROVED_FOR_PAPER_PHASE1_STOCK_PROFILE_INPUT_BLOCKED)
    if source.get("model_weight_versioning_status") != "MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED":
        return _block(gates, "model_weight_versioning_status", APPROVED_FOR_PAPER_PHASE1_STOCK_PROFILE_INPUT_BLOCKED)
    if any(
        source.get(field) != "PASS"
        for field in [
            "stock_profile_health_status",
            "active_model_health_status",
            "model_weight_versioning_health_status",
        ]
    ):
        return _block(gates, "upstream_health", APPROVED_FOR_PAPER_PHASE1_HEALTH_BLOCKED)

    for field in ["training_result_metadata_path", "training_result_rows_path", "training_result_status_artifact_path", "training_result_health_artifact_path"]:
        if not _path_exists(getattr(settings, field)):
            return _block(gates, field, APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_INPUT_BLOCKED)
    if source.get("training_result_status") != "TRAINING_RESULT_CREATED":
        return _block(gates, "training_result_status", APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_INPUT_BLOCKED)
    if source.get("training_result_health_status") != "PASS":
        return _block(gates, "training_result_health", APPROVED_FOR_PAPER_PHASE1_HEALTH_BLOCKED)

    training_rows = _read_csv_path(settings.training_result_rows_path)
    if training_rows.empty:
        return _block(gates, "training_result_rows_empty", APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_INPUT_BLOCKED)
    missing_columns = REQUIRED_TRAINING_ROW_COLUMNS.difference(training_rows.columns)
    if missing_columns:
        return _block(gates, "training_result_row_columns", APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED)

    for field in ["training_result_planning_metadata_path", "training_result_planning_health_artifact_path"]:
        if not _path_exists(getattr(settings, field)):
            return _block(gates, field, APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_PLANNING_INPUT_BLOCKED)
    if source.get("training_result_planning_status") != "TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED":
        return _block(gates, "training_result_planning_status", APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_PLANNING_INPUT_BLOCKED)
    if source.get("training_result_planning_health_status") != "PASS":
        return _block(gates, "training_result_planning_health", APPROVED_FOR_PAPER_PHASE1_HEALTH_BLOCKED)

    metric_paths = [
        "metric_extension_metadata_path",
        "metric_extension_result_rows_path",
        "metric_extension_health_artifact_path",
        "metric_computation_metadata_path",
        "metric_computation_result_rows_path",
        "metric_computation_health_artifact_path",
        "metric_evaluation_metadata_path",
        "metric_evaluation_health_artifact_path",
    ]
    for field in metric_paths:
        if not _path_exists(getattr(settings, field)):
            return _block(gates, field, APPROVED_FOR_PAPER_PHASE1_METRIC_EVIDENCE_BLOCKED)
    if source.get("metric_extension_status") != "METRIC_EXTENSION_REPORT_CREATED":
        return _block(gates, "metric_extension_status", APPROVED_FOR_PAPER_PHASE1_METRIC_EVIDENCE_BLOCKED)
    if source.get("metric_computation_status") != "METRIC_COMPUTATION_REPORT_CREATED":
        return _block(gates, "metric_computation_status", APPROVED_FOR_PAPER_PHASE1_METRIC_EVIDENCE_BLOCKED)
    if source.get("metric_evaluation_status") != "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED":
        return _block(gates, "metric_evaluation_status", APPROVED_FOR_PAPER_PHASE1_METRIC_EVIDENCE_BLOCKED)
    if _read_csv_path(settings.metric_extension_result_rows_path).empty or _read_csv_path(settings.metric_computation_result_rows_path).empty:
        return _block(gates, "metric_result_rows", APPROVED_FOR_PAPER_PHASE1_METRIC_EVIDENCE_BLOCKED)

    for field in ["training_evaluation_metadata_path", "training_evaluation_sample_rows_path", "training_evaluation_health_artifact_path"]:
        if not _path_exists(getattr(settings, field)):
            return _block(gates, field, APPROVED_FOR_PAPER_PHASE1_TRAINING_EVALUATION_INPUT_BLOCKED)
    if source.get("training_evaluation_status") != "TRAINING_EVALUATION_DATASET_CREATED":
        return _block(gates, "training_evaluation_status", APPROVED_FOR_PAPER_PHASE1_TRAINING_EVALUATION_INPUT_BLOCKED)

    for field in [
        "forward_return_label_metadata_path",
        "forward_return_label_rows_path",
        "forward_return_label_health_artifact_path",
        "replay_decision_freeze_metadata_path",
        "replay_decision_freeze_rows_path",
        "replay_decision_freeze_health_artifact_path",
    ]:
        if not _path_exists(getattr(settings, field)):
            return _block(gates, field, APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED)

    for field, status in [
        ("leakage_evidence_bundle_path", APPROVED_FOR_PAPER_PHASE1_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED),
        ("side_effect_evidence_bundle_path", APPROVED_FOR_PAPER_PHASE1_SIDE_EFFECT_BLOCKED),
    ]:
        if not _path_exists(getattr(settings, field)):
            return _block(gates, field, status)
    if _unsafe_bundle(settings.leakage_evidence_bundle_path, LEAKAGE_REQUEST_FIELDS):
        return _block(gates, "leakage_bundle", APPROVED_FOR_PAPER_PHASE1_LEAKAGE_BLOCKED)
    overclaim_bundle = _read_json_path(settings.overclaim_evidence_bundle_path)
    if not _truthy(overclaim_bundle.get("approved_for_paper_not_performance_validation")):
        return _block(gates, "overclaim_bundle", APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED)
    if _unsafe_bundle(settings.side_effect_evidence_bundle_path, set(DOWNSTREAM_FALSE_FIELDS)):
        return _block(gates, "side_effect_bundle", APPROVED_FOR_PAPER_PHASE1_SIDE_EFFECT_BLOCKED)

    gates.append(_gate("ready", READY_FOR_APPROVED_FOR_PAPER_PHASE1, "All report-only APPROVED_FOR_PAPER Phase 1 gates passed."))
    return READY_FOR_APPROVED_FOR_PAPER_PHASE1


def _source_summary(settings: ApprovedForPaperPhase1Settings) -> dict[str, Any]:
    paper = _read_json_path(settings.paper_workflow_metadata_path)
    paper_status = _read_json_path(settings.paper_workflow_status_artifact_path)
    paper_health = _read_json_path(settings.paper_workflow_health_artifact_path)
    lineage = (_read_csv_path(settings.paper_workflow_lineage_matrix_path).head(1).to_dict("records") or [{}])[0]
    stock = _read_json_path(settings.stock_profile_metadata_path)
    active = _read_json_path(settings.active_model_metadata_path)
    model = _read_json_path(settings.model_weight_versioning_metadata_path)
    model_weights = _read_json_path(settings.model_weights_reference_path)
    model_version = _read_json_path(settings.model_version_metadata_path)
    parameter_version = _read_json_path(settings.parameter_version_metadata_path)
    training_result = _read_json_path(settings.training_result_metadata_path)
    training_planning = _read_json_path(settings.training_result_planning_metadata_path)
    metric_extension = _read_json_path(settings.metric_extension_metadata_path)
    metric_computation = _read_json_path(settings.metric_computation_metadata_path)
    metric_evaluation = _read_json_path(settings.metric_evaluation_metadata_path)
    training_evaluation = _read_json_path(settings.training_evaluation_metadata_path)
    forward_return = _read_json_path(settings.forward_return_label_metadata_path)
    replay_freeze = _read_json_path(settings.replay_decision_freeze_metadata_path)
    return {
        "paper_workflow_run_id": paper.get("paper_workflow_run_id", "") or lineage.get("paper_workflow_run_id", ""),
        "paper_workflow_status": paper.get("status") or paper_status.get("status", ""),
        "paper_workflow_health_status": paper_health.get("status") or paper_status.get("health_status", ""),
        "stock_profile_run_id": paper.get("source_stock_profile_run_id") or lineage.get("stock_profile_run_id", "") or stock.get("stock_profile_run_id", ""),
        "stock_profile_status": stock.get("status", ""),
        "stock_profile_health_status": _read_json_path(settings.stock_profile_health_artifact_path).get("status", ""),
        "active_model_run_id": paper.get("source_active_model_run_id") or lineage.get("active_model_run_id", "") or active.get("active_model_run_id", ""),
        "active_model_status": active.get("status", ""),
        "active_model_health_status": _read_json_path(settings.active_model_health_artifact_path).get("status", ""),
        "model_workflow_run_id": paper.get("source_model_workflow_run_id") or lineage.get("model_workflow_run_id", "") or model.get("model_workflow_run_id", ""),
        "model_weight_versioning_status": model.get("status", ""),
        "model_weight_versioning_health_status": _read_json_path(settings.model_weight_versioning_health_artifact_path).get("status", ""),
        "model_weight_reference_id": paper.get("model_weight_reference_id")
        or lineage.get("model_weight_reference_id", "")
        or model_weights.get("model_weight_reference_id", ""),
        "model_version_id": paper.get("model_version_id") or lineage.get("model_version_id", "") or model_version.get("model_version_id", ""),
        "parameter_version_id": paper.get("parameter_version_id")
        or lineage.get("parameter_version_id", "")
        or parameter_version.get("parameter_version_id", ""),
        "training_result_run_id": paper.get("source_training_result_run_id")
        or lineage.get("training_result_run_id", "")
        or training_result.get("training_result_run_id", ""),
        "training_result_status": training_result.get("status") or paper.get("source_training_result_status", ""),
        "training_result_health_status": paper.get("source_training_result_health_status")
        or _read_json_path(settings.training_result_health_artifact_path).get("status", ""),
        "training_result_planning_run_id": paper.get("source_training_result_planning_run_id")
        or training_planning.get("training_result_planning_run_id", ""),
        "training_result_planning_status": training_planning.get("status")
        or paper.get("source_training_result_planning_status", ""),
        "training_result_planning_health_status": paper.get("source_training_result_planning_health_status")
        or _read_json_path(settings.training_result_planning_health_artifact_path).get("status", ""),
        "metric_extension_run_id": paper.get("source_metric_extension_run_id") or metric_extension.get("metric_extension_run_id", ""),
        "metric_extension_status": metric_extension.get("status") or paper.get("source_metric_extension_status", ""),
        "metric_extension_health_status": paper.get("source_metric_extension_health_status")
        or _read_json_path(settings.metric_extension_health_artifact_path).get("status", ""),
        "metric_computation_run_id": paper.get("source_metric_computation_run_id") or metric_computation.get("metric_computation_run_id", ""),
        "metric_computation_status": metric_computation.get("status") or paper.get("source_metric_computation_status", ""),
        "metric_computation_health_status": paper.get("source_metric_computation_health_status")
        or _read_json_path(settings.metric_computation_health_artifact_path).get("status", ""),
        "metric_evaluation_planning_run_id": paper.get("source_metric_evaluation_planning_run_id")
        or metric_evaluation.get("metric_evaluation_run_id", ""),
        "metric_evaluation_status": metric_evaluation.get("status") or paper.get("source_metric_evaluation_status", ""),
        "metric_evaluation_health_status": paper.get("source_metric_evaluation_health_status")
        or _read_json_path(settings.metric_evaluation_health_artifact_path).get("status", ""),
        "training_evaluation_run_id": paper.get("source_training_evaluation_run_id")
        or training_evaluation.get("training_evaluation_run_id", ""),
        "training_evaluation_status": training_evaluation.get("status") or paper.get("source_training_evaluation_status", ""),
        "training_evaluation_health_status": paper.get("source_training_evaluation_health_status")
        or _read_json_path(settings.training_evaluation_health_artifact_path).get("status", ""),
        "forward_return_label_run_id": paper.get("source_forward_return_label_run_id")
        or forward_return.get("forward_return_label_run_id", ""),
        "forward_return_label_status": forward_return.get("status") or paper.get("source_forward_return_label_status", ""),
        "forward_return_label_health_status": paper.get("source_forward_return_label_health_status")
        or _read_json_path(settings.forward_return_label_health_artifact_path).get("status", ""),
        "replay_decision_freeze_run_id": paper.get("source_replay_decision_freeze_run_id")
        or replay_freeze.get("replay_decision_freeze_run_id", ""),
        "replay_decision_freeze_status": replay_freeze.get("status") or paper.get("source_replay_decision_freeze_status", ""),
        "replay_decision_freeze_health_status": paper.get("source_replay_decision_freeze_health_status")
        or _read_json_path(settings.replay_decision_freeze_health_artifact_path).get("status", ""),
    }


def _metadata(result: ApprovedForPaperPhase1Result, source: dict[str, Any]) -> dict[str, Any]:
    return {
        "approved_for_paper_run_id": result.approved_for_paper_run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "execution_status": result.status,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "ready_for_approved_for_paper_phase1": result.ready_for_approved_for_paper_phase1,
        "approved_for_paper_phase1_executed": result.approved_for_paper_phase1_executed,
        "approved_for_paper_phase1_report_only_artifacts_created": result.approved_for_paper_phase1_report_only_artifacts_created,
        "approved_for_paper_scope": result.approved_for_paper_scope,
        "source_paper_workflow_phase1_run_id": result.source_paper_workflow_phase1_run_id,
        "source_paper_workflow_phase1_status": result.source_paper_workflow_phase1_status,
        "source_paper_workflow_phase1_health_status": result.source_paper_workflow_phase1_health_status,
        "source_stock_profile_run_id": result.source_stock_profile_run_id,
        "source_stock_profile_status": result.source_stock_profile_status,
        "source_stock_profile_health_status": result.source_stock_profile_health_status,
        "source_active_model_run_id": result.source_active_model_run_id,
        "source_active_model_status": result.source_active_model_status,
        "source_active_model_health_status": result.source_active_model_health_status,
        "source_model_workflow_run_id": result.source_model_workflow_run_id,
        "source_model_weight_versioning_status": result.source_model_weight_versioning_status,
        "source_model_weight_versioning_health_status": result.source_model_weight_versioning_health_status,
        "source_training_result_run_id": result.source_training_result_run_id,
        "source_training_result_status": result.source_training_result_status,
        "source_training_result_health_status": result.source_training_result_health_status,
        "source_training_result_planning_run_id": result.source_training_result_planning_run_id,
        "source_training_result_planning_status": result.source_training_result_planning_status,
        "source_training_result_planning_health_status": result.source_training_result_planning_health_status,
        "source_metric_extension_run_id": result.source_metric_extension_run_id,
        "source_metric_extension_status": result.source_metric_extension_status,
        "source_metric_extension_health_status": result.source_metric_extension_health_status,
        "source_metric_computation_run_id": result.source_metric_computation_run_id,
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
        "model_weight_reference_id": result.model_weight_reference_id,
        "model_version_id": result.model_version_id,
        "parameter_version_id": result.parameter_version_id,
        **{
            key: getattr(result, key)
            for key in [
                "approved_for_paper_metadata_created",
                "approved_for_paper_input_index_created",
                "approved_for_paper_lineage_matrix_created",
                "approved_for_paper_review_context_created",
                "approved_for_paper_decision_draft_created",
                "approved_for_paper_limitations_created",
                "approved_for_paper_overfit_warnings_created",
                "approved_for_paper_safety_flags_created",
            ]
        },
        **_safety_flags(result),
    }


def _safety_flags(result: ApprovedForPaperPhase1Result) -> dict[str, Any]:
    return {
        "approved_for_paper_phase1_report_only_artifacts_created": result.approved_for_paper_phase1_report_only_artifacts_created,
        "scoped_approved_for_paper_phase1": result.scoped_approved_for_paper_phase1,
        "scoped_approved_for_paper": result.scoped_approved_for_paper,
        "approved_for_paper_scope": result.approved_for_paper_scope,
        **{field: getattr(result, field) for field in DOWNSTREAM_FALSE_FIELDS},
        "report_only": True,
        "research_governed": True,
        "diagnostic_output": True,
    }


def _write_input_index(path: Path, settings: ApprovedForPaperPhase1Settings) -> None:
    rows = []
    for field, value in settings.__dict__.items():
        if field.endswith("_path") and value is not None:
            rows.append({"source_artifact": field, "path": str(value), "exists": Path(value).exists(), "row_count": _row_count(value)})
    pd.DataFrame(rows).to_csv(path, index=False)


def _write_lineage_matrix(
    path: Path,
    result: ApprovedForPaperPhase1Result,
    settings: ApprovedForPaperPhase1Settings,
    source: dict[str, Any],
) -> None:
    training_row = (_read_csv_path(settings.training_result_rows_path).head(1).to_dict("records") or [{}])[0]
    paper_lineage = (_read_csv_path(settings.paper_workflow_lineage_matrix_path).head(1).to_dict("records") or [{}])[0]
    payload = {
        "approved_for_paper_run_id": result.approved_for_paper_run_id,
        "paper_workflow_phase1_run_id": result.source_paper_workflow_phase1_run_id,
        "stock_profile_run_id": result.source_stock_profile_run_id,
        "active_model_run_id": result.source_active_model_run_id,
        "model_workflow_run_id": result.source_model_workflow_run_id,
        "model_weight_reference_id": result.model_weight_reference_id,
        "model_version_id": result.model_version_id,
        "parameter_version_id": result.parameter_version_id,
        "training_result_run_id": result.source_training_result_run_id,
        "metric_computation_run_id": result.source_metric_computation_run_id,
        "metric_extension_run_id": result.source_metric_extension_run_id,
        "metric_evaluation_planning_run_id": result.source_metric_evaluation_planning_run_id,
        "forward_return_label_run_id": result.source_forward_return_label_run_id,
        "replay_decision_freeze_run_id": result.source_replay_decision_freeze_run_id,
        **{column: training_row.get(column, paper_lineage.get(column, "")) for column in REQUIRED_TRAINING_ROW_COLUMNS},
        "report_only": True,
        "diagnostic_only": True,
        "research_governed": True,
    }
    pd.DataFrame([payload]).to_csv(path, index=False)


def _write_review_context(path: Path, result: ApprovedForPaperPhase1Result, settings: ApprovedForPaperPhase1Settings) -> None:
    row = (_read_csv_path(settings.training_result_rows_path).head(1).to_dict("records") or [{}])[0]
    pd.DataFrame(
        [
            {
                "approved_for_paper_run_id": result.approved_for_paper_run_id,
                "symbol": row.get("symbol", ""),
                "human_review_context": "human review only context",
                "draft_review_label": "PAPER_APPROVAL_REVIEW_DRAFT",
                "source_paper_workflow_phase1_run_id": result.source_paper_workflow_phase1_run_id,
                "scope": "report_only_phase1_artifact_state_only",
            }
        ]
    ).to_csv(path, index=False)


def _write_decision_draft(path: Path, result: ApprovedForPaperPhase1Result, settings: ApprovedForPaperPhase1Settings) -> None:
    row = (_read_csv_path(settings.training_result_rows_path).head(1).to_dict("records") or [{}])[0]
    pd.DataFrame(
        [
            {
                "approved_for_paper_run_id": result.approved_for_paper_run_id,
                "symbol": row.get("symbol", ""),
                "draft_label": "APPROVED_FOR_PAPER_PHASE1",
                "review_note": "human paper review required before any later workflow",
            }
        ]
    ).to_csv(path, index=False)


def _write_overfit_warnings(path: Path) -> None:
    rows = [
        {"warning_item": item, "required": True, "accepted": True, "future_guard": "separate governance required"}
        for item in sorted(REQUIRED_OVERFIT_WARNINGS)
    ]
    pd.DataFrame(rows).to_csv(path, index=False)


def _limitations_text() -> str:
    return "\n".join(
        [
            "# APPROVED_FOR_PAPER Phase 1 Limitations",
            "",
            "- phase 1 is report-only;",
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
            "- no broker/order/message/api/trading;",
            "- metrics are evidence only, not profitability proof;",
            "- fill/slippage assumptions remain future separate validation.",
        ]
    )


def _recommended_next_task(result: ApprovedForPaperPhase1Result) -> str:
    if result.approved_for_paper_phase1_report_only_artifacts_created:
        return "# Recommended Next Task\n\nAPPROVED_FOR_PAPER Phase 1 Artifact Views Report-Only v0.1\n"
    if result.ready_for_approved_for_paper_phase1:
        return "# Recommended Next Task\n\nRerun with --allow-approved-for-paper-phase1 only if exact approval remains valid.\n"
    return "# Recommended Next Task\n\nResolve APPROVED_FOR_PAPER Phase 1 blockers before creating report-only artifacts.\n"


def _has_input(settings: ApprovedForPaperPhase1Settings) -> bool:
    ignored = {"output_dir", "allow_approved_for_paper_phase1", "write_artifacts", "research_governed", "diagnostic_output"}
    return any(getattr(settings, field) is not None for field in settings.__dataclass_fields__ if field not in ignored)


def _unsafe_request_status(request: dict[str, Any]) -> str | None:
    if any(_truthy(request.get(field)) for field in OVERCLAIM_REQUEST_FIELDS):
        return APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED
    if any(_truthy(request.get(field)) for field in LEAKAGE_REQUEST_FIELDS):
        return APPROVED_FOR_PAPER_PHASE1_LEAKAGE_BLOCKED
    if any(_truthy(request.get(field)) for field in SIDE_EFFECT_REQUEST_FIELDS):
        return APPROVED_FOR_PAPER_PHASE1_SIDE_EFFECT_BLOCKED
    return None


def _output_under_manual_diagnostics(output_dir: str | Path) -> bool:
    parts = [part.lower() for part in Path(output_dir).parts]
    needle = ["outputs", "reports", "manual_diagnostics"]
    return any(parts[index : index + 3] == needle for index in range(max(len(parts) - 2, 0)))


def _has_forbidden_artifact(output_dir: Path) -> bool:
    if not output_dir.exists():
        return False
    return any(
        any(token in path.name.lower() for token in FORBIDDEN_ARTIFACT_TOKENS)
        for path in output_dir.rglob("*")
        if path.is_file()
    )


def _unsafe_bundle(path: str | Path | None, fields: set[str]) -> bool:
    payload = _read_json_path(path)
    return any(_truthy(payload.get(field)) for field in fields)


def _missing_required_overfit(path: str | Path | None) -> bool:
    frame = _read_csv_path(path)
    if "warning_item" not in frame.columns:
        return True
    return not REQUIRED_OVERFIT_WARNINGS.issubset(set(frame["warning_item"].astype(str)))


def _path_exists(path: str | Path | None) -> bool:
    return path is not None and Path(path).exists()


def _read_json_path(path: str | Path | None) -> dict[str, Any]:
    if path is None or not Path(path).exists():
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv_path(path: str | Path | None) -> pd.DataFrame:
    if path is None or not Path(path).exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str)


def _row_count(path: str | Path) -> int:
    if str(path).lower().endswith(".csv"):
        try:
            return len(pd.read_csv(path, dtype=str))
        except Exception:
            return 0
    return 1


def _truthy(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _block(gates: list[ApprovedForPaperPhase1GateResult], gate: str, status: str) -> str:
    gates.append(_gate(gate, status, status))
    return status


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_gate_csv(path: Path, gates: list[ApprovedForPaperPhase1GateResult]) -> None:
    pd.DataFrame([gate.__dict__ for gate in gates]).to_csv(path, index=False)


def _gate(gate: str, status: str, message: str) -> ApprovedForPaperPhase1GateResult:
    return ApprovedForPaperPhase1GateResult(gate=gate, status=status, message=message)


def _run_id(settings: ApprovedForPaperPhase1Settings) -> str:
    payload = {key: str(value) for key, value in settings.__dict__.items() if key != "write_artifacts"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]
