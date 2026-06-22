"""Report-only Global APPROVED_FOR_PAPER approval-review core workflow."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_INPUT = "NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_INPUT"
GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_APPROVAL_BLOCKED = (
    "GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_APPROVAL_BLOCKED"
)
GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_FORBIDDEN_ARTIFACT_BLOCKED = (
    "GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_FORBIDDEN_ARTIFACT_BLOCKED"
)
GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_HEALTH_BLOCKED = "GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_HEALTH_BLOCKED"
GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_LINEAGE_BLOCKED = "GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_LINEAGE_BLOCKED"
GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_OVERCLAIM_BLOCKED = (
    "GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_OVERCLAIM_BLOCKED"
)
GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_SIDE_EFFECT_BLOCKED = (
    "GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_SIDE_EFFECT_BLOCKED"
)
READY_FOR_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW = "READY_FOR_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW"
GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED = (
    "GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED"
)

EXACT_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_TEXT = (
    "I explicitly authorize only Global APPROVED_FOR_PAPER Approval Review Core Report-Only v0.1, "
    "limited to report-only global approved-for-paper approval-review metadata, approval-manifest "
    "review, immutable lineage matrix, health precondition review, forbidden-output guard results, "
    "overclaim guard results, side-effect guard results, research-status preview, limitations, and "
    "recommended_next_task governance review artifacts. It must not create global APPROVED_FOR_PAPER "
    "as an operational state, real buy-review eligibility, buy_review_allowed, strategy performance "
    "validation, current-candidates integration, snapshots, signal_semantics mutation, active "
    "stock_profile, promoted model, production model, active thresholds, advisory predictions, active "
    "probabilities, broker/order/message/API integration, or trading. If any required upstream "
    "lineage, health, available_time, source_hash, revision_id, quality_status, report_only, "
    "diagnostic_only, research_governed, metric evidence, training_result rows, approved-for-paper "
    "phase-1 artifacts, limitations, overfit warnings, safety flags, or exact approval are missing "
    "or unsafe, it must fail closed."
)

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/global_approved_for_paper_approval_review_v0_1")

ARTIFACT_FILES = {
    "global_approved_for_paper_approval_review_metadata": "global_approved_for_paper_approval_review_metadata.json",
    "global_approved_for_paper_approval_manifest_review": "global_approved_for_paper_approval_manifest_review.csv",
    "global_approved_for_paper_lineage_matrix": "global_approved_for_paper_lineage_matrix.csv",
    "global_approved_for_paper_precondition_results": "global_approved_for_paper_precondition_results.csv",
    "global_approved_for_paper_forbidden_output_guard": "global_approved_for_paper_forbidden_output_guard.csv",
    "global_approved_for_paper_overclaim_guard": "global_approved_for_paper_overclaim_guard.csv",
    "global_approved_for_paper_side_effect_guard": "global_approved_for_paper_side_effect_guard.csv",
    "global_approved_for_paper_research_status_preview": "global_approved_for_paper_research_status_preview.csv",
    "global_approved_for_paper_limitations": "global_approved_for_paper_limitations.md",
    "recommended_next_task": "recommended_next_task.md",
}

SUBSTANTIVE_ARTIFACT_KEYS = {
    "global_approved_for_paper_approval_manifest_review",
    "global_approved_for_paper_lineage_matrix",
    "global_approved_for_paper_research_status_preview",
    "global_approved_for_paper_limitations",
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
    "broker_api_called",
    "order_placed",
    "message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]

OVERCLAIM_REQUEST_FIELDS = {
    "real_buy_review_requested",
    "buy_review_requested",
    "performance_validation_requested",
    "active_stock_profile_requested",
    "promoted_model_requested",
    "production_model_requested",
    "active_thresholds_requested",
    "advisory_predictions_requested",
    "active_probabilities_requested",
}

SIDE_EFFECT_REQUEST_FIELDS = {
    "current_candidates_integration_requested",
    "snapshot_build_requested",
    "signal_semantics_mutation_requested",
    "broker_api_called",
    "order_placed",
    "message_sent",
    "external_api_called",
    "llm_api_called",
    "trading_requested",
    *DOWNSTREAM_FALSE_FIELDS,
}

FORBIDDEN_ARTIFACT_TOKENS = [
    "real_buy_review",
    "buy_review",
    "performance_validation",
    "current_candidates",
    "snapshot",
    "signal_semantics",
    "active_stock_profile",
    "promoted_model",
    "production_model",
    "active_threshold",
    "advisory_prediction",
    "active_probability",
    "broker",
    "order",
    "message",
    "trading",
]

EXPECTED_PHASE1_STATUS = "APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED"

EXPECTED_UPSTREAM_STATUSES = {
    "source_paper_workflow_phase1_status": "PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED",
    "source_stock_profile_status": "STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED",
    "source_active_model_status": "ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED",
    "source_model_weight_versioning_status": "MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED",
    "source_training_result_status": "TRAINING_RESULT_CREATED",
    "source_training_result_planning_status": "TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED",
    "source_metric_extension_status": "METRIC_EXTENSION_REPORT_CREATED",
    "source_metric_computation_status": "METRIC_COMPUTATION_REPORT_CREATED",
    "source_metric_evaluation_status": "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED",
    "source_training_evaluation_status": "TRAINING_EVALUATION_DATASET_CREATED",
    "source_forward_return_label_status": "FORWARD_RETURN_LABELS_CREATED",
    "source_replay_decision_freeze_status": "REPLAY_DECISION_FROZEN",
}

REQUIRED_UPSTREAM_IDS = [
    "approved_for_paper_run_id",
    "source_paper_workflow_phase1_run_id",
    "source_stock_profile_run_id",
    "source_active_model_run_id",
    "source_model_workflow_run_id",
    "source_training_result_run_id",
    "source_training_result_planning_run_id",
    "source_metric_extension_run_id",
    "source_metric_computation_run_id",
    "source_metric_evaluation_planning_run_id",
    "source_training_evaluation_run_id",
    "source_forward_return_label_run_id",
    "source_replay_decision_freeze_run_id",
    "model_weight_reference_id",
    "model_version_id",
    "parameter_version_id",
]

REQUIRED_LINEAGE_COLUMNS = {"source_hash", "revision_id", "available_time", "quality_status"}


@dataclass(frozen=True)
class GlobalApprovedForPaperApprovalReviewSettings:
    approval_manifest_path: str | Path | None = None
    approved_for_paper_phase1_metadata_path: str | Path | None = None
    approved_for_paper_phase1_status_artifact_path: str | Path | None = None
    approved_for_paper_phase1_health_artifact_path: str | Path | None = None
    approved_for_paper_phase1_lineage_matrix_path: str | Path | None = None
    approved_for_paper_phase1_limitations_path: str | Path | None = None
    approved_for_paper_phase1_safety_flags_path: str | Path | None = None
    allow_global_approved_for_paper_approval_review: bool = False
    output_dir: str | Path = DEFAULT_OUTPUT_DIR
    write_artifacts: bool = True
    research_governed: bool = True
    diagnostic_output: bool = True


@dataclass(frozen=True)
class GlobalApprovedForPaperApprovalReviewGateResult:
    gate: str
    status: str
    message: str


@dataclass(frozen=True)
class GlobalApprovedForPaperApprovalReviewResult:
    global_approved_for_paper_approval_review_id: str
    status: str
    workflow_stage: str
    ready_for_global_approved_for_paper_approval_review: bool
    global_approved_for_paper_approval_review_executed: bool
    global_approved_for_paper_approval_review_report_only_artifacts_created: bool
    global_approved_for_paper_approval_review_metadata_created: bool
    global_approved_for_paper_approval_manifest_review_created: bool
    global_approved_for_paper_lineage_matrix_created: bool
    global_approved_for_paper_precondition_results_created: bool
    global_approved_for_paper_forbidden_output_guard_created: bool
    global_approved_for_paper_overclaim_guard_created: bool
    global_approved_for_paper_side_effect_guard_created: bool
    global_approved_for_paper_research_status_preview_created: bool
    global_approved_for_paper_limitations_created: bool
    scoped_global_approved_for_paper_approval_review: bool
    global_approved_for_paper: bool
    global_approved_for_paper_scope: str
    source_approved_for_paper_phase1_run_id: str
    source_approved_for_paper_phase1_status: str
    source_approved_for_paper_phase1_health_status: str
    source_paper_workflow_phase1_run_id: str
    source_model_workflow_run_id: str
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
    broker_api_called: bool
    order_placed: bool
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
    gate_results: list[GlobalApprovedForPaperApprovalReviewGateResult]


def run_global_approved_for_paper_approval_review(
    settings: GlobalApprovedForPaperApprovalReviewSettings | None = None,
) -> GlobalApprovedForPaperApprovalReviewResult:
    settings = settings or GlobalApprovedForPaperApprovalReviewSettings()
    run_id = _run_id(settings)
    artifact_dir = Path(settings.output_dir) / run_id
    artifact_paths = {key: artifact_dir / filename for key, filename in ARTIFACT_FILES.items()}
    gates: list[GlobalApprovedForPaperApprovalReviewGateResult] = []
    source = _source_summary(settings)

    if not _has_input(settings):
        result = _build_result(
            settings,
            artifact_paths,
            run_id,
            NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_INPUT,
            "GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_NO_INPUT",
            source,
            gates,
        )
        return write_global_approved_for_paper_approval_review_artifacts(result, settings, artifact_paths, source)

    status = _validate(settings, source, gates)
    if status != READY_FOR_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW:
        result = _build_result(settings, artifact_paths, run_id, status, status, source, gates)
        return write_global_approved_for_paper_approval_review_artifacts(result, settings, artifact_paths, source)

    if settings.allow_global_approved_for_paper_approval_review:
        status = GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED
    result = _build_result(settings, artifact_paths, run_id, status, status, source, gates)
    return write_global_approved_for_paper_approval_review_artifacts(result, settings, artifact_paths, source)


def write_global_approved_for_paper_approval_review_artifacts(
    result: GlobalApprovedForPaperApprovalReviewResult,
    settings: GlobalApprovedForPaperApprovalReviewSettings,
    artifact_paths: dict[str, Path],
    source: dict[str, Any],
) -> GlobalApprovedForPaperApprovalReviewResult:
    if not settings.write_artifacts:
        return result
    artifact_dir = Path(result.artifact_path)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    _write_json(artifact_paths["global_approved_for_paper_approval_review_metadata"], _metadata(result, source))
    _write_gate_csv(
        artifact_paths["global_approved_for_paper_precondition_results"],
        result.gate_results or [_gate("precondition", result.status, result.workflow_stage)],
    )
    _write_gate_csv(
        artifact_paths["global_approved_for_paper_forbidden_output_guard"],
        [gate for gate in result.gate_results if "forbidden" in gate.gate]
        or [_gate("forbidden_output_guard", result.status, result.status)],
    )
    _write_gate_csv(
        artifact_paths["global_approved_for_paper_overclaim_guard"],
        [gate for gate in result.gate_results if "overclaim" in gate.gate]
        or [_gate("overclaim_guard", result.status, result.status)],
    )
    _write_gate_csv(
        artifact_paths["global_approved_for_paper_side_effect_guard"],
        [gate for gate in result.gate_results if "side_effect" in gate.gate]
        or [_gate("side_effect_guard", result.status, result.status)],
    )
    artifact_paths["recommended_next_task"].write_text(_recommended_next_task(result), encoding="utf-8")

    if result.global_approved_for_paper_approval_review_report_only_artifacts_created:
        _write_approval_manifest_review(artifact_paths["global_approved_for_paper_approval_manifest_review"], settings)
        _write_lineage_matrix(artifact_paths["global_approved_for_paper_lineage_matrix"], result, settings, source)
        _write_research_status_preview(
            artifact_paths["global_approved_for_paper_research_status_preview"], result, source
        )
        artifact_paths["global_approved_for_paper_limitations"].write_text(_limitations_text(), encoding="utf-8")
    return result


def _build_result(
    settings: GlobalApprovedForPaperApprovalReviewSettings,
    artifact_paths: dict[str, Path],
    run_id: str,
    status: str,
    stage: str,
    source: dict[str, Any],
    gates: list[GlobalApprovedForPaperApprovalReviewGateResult],
) -> GlobalApprovedForPaperApprovalReviewResult:
    created = status == GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED
    ready = status in {READY_FOR_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW, GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED}
    return GlobalApprovedForPaperApprovalReviewResult(
        global_approved_for_paper_approval_review_id=run_id,
        status=status,
        workflow_stage=stage,
        ready_for_global_approved_for_paper_approval_review=ready,
        global_approved_for_paper_approval_review_executed=created,
        global_approved_for_paper_approval_review_report_only_artifacts_created=created,
        global_approved_for_paper_approval_review_metadata_created=created,
        global_approved_for_paper_approval_manifest_review_created=created,
        global_approved_for_paper_lineage_matrix_created=created,
        global_approved_for_paper_precondition_results_created=True,
        global_approved_for_paper_forbidden_output_guard_created=True,
        global_approved_for_paper_overclaim_guard_created=True,
        global_approved_for_paper_side_effect_guard_created=True,
        global_approved_for_paper_research_status_preview_created=created,
        global_approved_for_paper_limitations_created=created,
        scoped_global_approved_for_paper_approval_review=created,
        global_approved_for_paper=False,
        global_approved_for_paper_scope="report_only_global_approval_review_only" if created else "",
        source_approved_for_paper_phase1_run_id=source.get("approved_for_paper_run_id", ""),
        source_approved_for_paper_phase1_status=source.get("phase1_status", ""),
        source_approved_for_paper_phase1_health_status=source.get("phase1_health_status", ""),
        source_paper_workflow_phase1_run_id=source.get("source_paper_workflow_phase1_run_id", ""),
        source_model_workflow_run_id=source.get("source_model_workflow_run_id", ""),
        **{field: False for field in DOWNSTREAM_FALSE_FIELDS},
        report_only=True,
        research_governed=settings.research_governed,
        diagnostic_output=settings.diagnostic_output,
        artifact_path=str(Path(settings.output_dir) / run_id),
        artifact_paths=artifact_paths,
        gate_results=gates,
    )


def _validate(
    settings: GlobalApprovedForPaperApprovalReviewSettings,
    source: dict[str, Any],
    gates: list[GlobalApprovedForPaperApprovalReviewGateResult],
) -> str:
    if not _output_under_manual_diagnostics(settings.output_dir):
        return _block(gates, "side_effect_output_boundary", GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_SIDE_EFFECT_BLOCKED)
    if _has_forbidden_artifact(Path(settings.output_dir)):
        return _block(gates, "forbidden_artifact", GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_FORBIDDEN_ARTIFACT_BLOCKED)

    approval = _read_record(settings.approval_manifest_path)
    if approval.get("approval_text") != EXACT_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_TEXT:
        return _block(gates, "exact_approval", GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_APPROVAL_BLOCKED)
    if not all(_text(approval.get(field)) for field in ["approved_by", "approved_at", "approval_scope"]):
        return _block(gates, "approval_manifest_fields", GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_APPROVAL_BLOCKED)
    unsafe = _unsafe_manifest_status(approval)
    if unsafe is not None:
        return _block(gates, "approval_manifest_scope", unsafe)

    required_paths = {
        "approved_for_paper_phase1_metadata_path": GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_LINEAGE_BLOCKED,
        "approved_for_paper_phase1_status_artifact_path": GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_LINEAGE_BLOCKED,
        "approved_for_paper_phase1_health_artifact_path": GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_HEALTH_BLOCKED,
        "approved_for_paper_phase1_lineage_matrix_path": GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_LINEAGE_BLOCKED,
        "approved_for_paper_phase1_limitations_path": GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_LINEAGE_BLOCKED,
        "approved_for_paper_phase1_safety_flags_path": GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_LINEAGE_BLOCKED,
    }
    for field, status in required_paths.items():
        if not _path_exists(getattr(settings, field)):
            return _block(gates, field, status)

    if source.get("phase1_status") != EXPECTED_PHASE1_STATUS:
        return _block(gates, "approved_for_paper_phase1_status", GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_LINEAGE_BLOCKED)
    if source.get("phase1_health_status") != "PASS":
        return _block(gates, "approved_for_paper_phase1_health", GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_HEALTH_BLOCKED)

    phase1 = _read_record(settings.approved_for_paper_phase1_metadata_path)
    for field, expected in EXPECTED_UPSTREAM_STATUSES.items():
        if phase1.get(field) != expected:
            return _block(gates, field, GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_LINEAGE_BLOCKED)
    for field in [key for key in phase1 if key.endswith("_health_status")]:
        if _text(phase1.get(field)) and phase1.get(field) != "PASS":
            return _block(gates, field, GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_HEALTH_BLOCKED)
    for field in REQUIRED_UPSTREAM_IDS:
        if not _text(phase1.get(field)):
            return _block(gates, field, GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_LINEAGE_BLOCKED)

    safety = _read_record(settings.approved_for_paper_phase1_safety_flags_path)
    if not _truthy(safety.get("approved_for_paper_phase1_report_only_artifacts_created")):
        return _block(gates, "phase1_report_only_flag", GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_LINEAGE_BLOCKED)
    if _unsafe_manifest_status(safety) is not None:
        return _block(gates, "phase1_safety_flags", GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_SIDE_EFFECT_BLOCKED)

    lineage = _read_csv_path(settings.approved_for_paper_phase1_lineage_matrix_path)
    if lineage.empty or REQUIRED_LINEAGE_COLUMNS.difference(lineage.columns):
        return _block(gates, "phase1_lineage_columns", GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_LINEAGE_BLOCKED)

    limitations = Path(settings.approved_for_paper_phase1_limitations_path).read_text(encoding="utf-8").lower()
    for phrase in ["no real buy-review eligibility", "no strategy performance validation", "no broker/order/message/api/trading"]:
        if phrase not in limitations:
            return _block(gates, "phase1_limitations", GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_OVERCLAIM_BLOCKED)

    gates.append(
        _gate(
            "ready",
            READY_FOR_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW,
            "All report-only Global APPROVED_FOR_PAPER approval-review gates passed.",
        )
    )
    return READY_FOR_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW


def _source_summary(settings: GlobalApprovedForPaperApprovalReviewSettings) -> dict[str, Any]:
    phase1 = _read_record(settings.approved_for_paper_phase1_metadata_path)
    status = _read_record(settings.approved_for_paper_phase1_status_artifact_path)
    health = _read_record(settings.approved_for_paper_phase1_health_artifact_path)
    return {
        **phase1,
        "phase1_status": phase1.get("status") or status.get("status", ""),
        "phase1_health_status": health.get("status") or status.get("health_status", ""),
    }


def _metadata(result: GlobalApprovedForPaperApprovalReviewResult, source: dict[str, Any]) -> dict[str, Any]:
    return {
        "global_approved_for_paper_approval_review_id": result.global_approved_for_paper_approval_review_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "execution_status": result.status,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "ready_for_global_approved_for_paper_approval_review": result.ready_for_global_approved_for_paper_approval_review,
        "global_approved_for_paper_approval_review_executed": result.global_approved_for_paper_approval_review_executed,
        "global_approved_for_paper_approval_review_report_only_artifacts_created": result.global_approved_for_paper_approval_review_report_only_artifacts_created,
        "scoped_global_approved_for_paper_approval_review": result.scoped_global_approved_for_paper_approval_review,
        "global_approved_for_paper": result.global_approved_for_paper,
        "global_approved_for_paper_scope": result.global_approved_for_paper_scope,
        "source_approved_for_paper_phase1_run_id": result.source_approved_for_paper_phase1_run_id,
        "source_approved_for_paper_phase1_status": result.source_approved_for_paper_phase1_status,
        "source_approved_for_paper_phase1_health_status": result.source_approved_for_paper_phase1_health_status,
        "source_paper_workflow_phase1_run_id": result.source_paper_workflow_phase1_run_id,
        "source_model_workflow_run_id": result.source_model_workflow_run_id,
        "global_approved_for_paper_approval_review_metadata_created": result.global_approved_for_paper_approval_review_metadata_created,
        "global_approved_for_paper_approval_manifest_review_created": result.global_approved_for_paper_approval_manifest_review_created,
        "global_approved_for_paper_lineage_matrix_created": result.global_approved_for_paper_lineage_matrix_created,
        "global_approved_for_paper_precondition_results_created": result.global_approved_for_paper_precondition_results_created,
        "global_approved_for_paper_forbidden_output_guard_created": result.global_approved_for_paper_forbidden_output_guard_created,
        "global_approved_for_paper_overclaim_guard_created": result.global_approved_for_paper_overclaim_guard_created,
        "global_approved_for_paper_side_effect_guard_created": result.global_approved_for_paper_side_effect_guard_created,
        "global_approved_for_paper_research_status_preview_created": result.global_approved_for_paper_research_status_preview_created,
        "global_approved_for_paper_limitations_created": result.global_approved_for_paper_limitations_created,
        **_safety_flags(result),
    }


def _safety_flags(result: GlobalApprovedForPaperApprovalReviewResult) -> dict[str, Any]:
    return {
        "global_approved_for_paper_approval_review_report_only_artifacts_created": result.global_approved_for_paper_approval_review_report_only_artifacts_created,
        "scoped_global_approved_for_paper_approval_review": result.scoped_global_approved_for_paper_approval_review,
        "global_approved_for_paper": result.global_approved_for_paper,
        "global_approved_for_paper_scope": result.global_approved_for_paper_scope,
        **{field: getattr(result, field) for field in DOWNSTREAM_FALSE_FIELDS},
        "report_only": True,
        "research_governed": True,
        "diagnostic_output": True,
    }


def _write_approval_manifest_review(path: Path, settings: GlobalApprovedForPaperApprovalReviewSettings) -> None:
    approval = _read_record(settings.approval_manifest_path)
    pd.DataFrame(
        [
            {
                "approval_scope": approval.get("approval_scope", ""),
                "approved_by": approval.get("approved_by", ""),
                "approved_at": approval.get("approved_at", ""),
                "exact_approval_text_matched": approval.get("approval_text") == EXACT_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_TEXT,
                "report_only_approval_review_only": True,
            }
        ]
    ).to_csv(path, index=False)


def _write_lineage_matrix(
    path: Path,
    result: GlobalApprovedForPaperApprovalReviewResult,
    settings: GlobalApprovedForPaperApprovalReviewSettings,
    source: dict[str, Any],
) -> None:
    phase1_lineage = (_read_csv_path(settings.approved_for_paper_phase1_lineage_matrix_path).head(1).to_dict("records") or [{}])[0]
    payload = {
        "global_approved_for_paper_approval_review_id": result.global_approved_for_paper_approval_review_id,
        "source_approved_for_paper_phase1_run_id": result.source_approved_for_paper_phase1_run_id,
        "source_paper_workflow_phase1_run_id": result.source_paper_workflow_phase1_run_id,
        "source_model_workflow_run_id": result.source_model_workflow_run_id,
        "source_training_result_run_id": source.get("source_training_result_run_id", ""),
        "source_metric_computation_run_id": source.get("source_metric_computation_run_id", ""),
        "source_forward_return_label_run_id": source.get("source_forward_return_label_run_id", ""),
        "source_replay_decision_freeze_run_id": source.get("source_replay_decision_freeze_run_id", ""),
        **{column: phase1_lineage.get(column, "") for column in REQUIRED_LINEAGE_COLUMNS},
        "report_only": True,
        "diagnostic_only": True,
        "research_governed": True,
    }
    pd.DataFrame([payload]).to_csv(path, index=False)


def _write_research_status_preview(
    path: Path,
    result: GlobalApprovedForPaperApprovalReviewResult,
    source: dict[str, Any],
) -> None:
    pd.DataFrame(
        [
            {
                "latest_global_approved_for_paper_approval_review_id": result.global_approved_for_paper_approval_review_id,
                "latest_global_approved_for_paper_approval_review_status": result.status,
                "global_approved_for_paper_approval_review_report_only_artifacts_created": result.global_approved_for_paper_approval_review_report_only_artifacts_created,
                "global_approved_for_paper": False,
                "source_approved_for_paper_phase1_run_id": source.get("approved_for_paper_run_id", ""),
                **{field: getattr(result, field) for field in DOWNSTREAM_FALSE_FIELDS},
            }
        ]
    ).to_csv(path, index=False)


def _limitations_text() -> str:
    return "\n".join(
        [
            "# Global APPROVED_FOR_PAPER Approval Review Limitations",
            "",
            "- report-only approval-review;",
            "- not global approved_for_paper as operational state;",
            "- no real buy-review eligibility;",
            "- no buy_review_allowed;",
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
        ]
    )


def _recommended_next_task(result: GlobalApprovedForPaperApprovalReviewResult) -> str:
    if result.global_approved_for_paper_approval_review_report_only_artifacts_created:
        return "# Recommended Next Task\n\nGlobal APPROVED_FOR_PAPER Approval Review Artifact Views Report-Only v0.1\n"
    if result.ready_for_global_approved_for_paper_approval_review:
        return "# Recommended Next Task\n\nRerun with --allow-global-approved-for-paper-approval-review only if exact approval remains valid.\n"
    return "# Recommended Next Task\n\nResolve Global APPROVED_FOR_PAPER approval-review blockers before creating report-only artifacts.\n"


def _unsafe_manifest_status(payload: dict[str, Any]) -> str | None:
    if any(_truthy(payload.get(field)) for field in OVERCLAIM_REQUEST_FIELDS):
        return GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_OVERCLAIM_BLOCKED
    if any(_truthy(payload.get(field)) for field in SIDE_EFFECT_REQUEST_FIELDS):
        return GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_SIDE_EFFECT_BLOCKED
    return None


def _has_input(settings: GlobalApprovedForPaperApprovalReviewSettings) -> bool:
    ignored = {
        "output_dir",
        "allow_global_approved_for_paper_approval_review",
        "write_artifacts",
        "research_governed",
        "diagnostic_output",
    }
    return any(getattr(settings, field) is not None for field in settings.__dataclass_fields__ if field not in ignored)


def _output_under_manual_diagnostics(output_dir: str | Path) -> bool:
    parts = [part.lower() for part in Path(output_dir).parts]
    needle = ["outputs", "reports", "manual_diagnostics"]
    return any(parts[index : index + 3] == needle for index in range(max(len(parts) - 2, 0)))


def _has_forbidden_artifact(output_dir: Path) -> bool:
    if not output_dir.exists():
        return False
    for path in output_dir.rglob("*"):
        name = path.name.lower()
        if any(token in name for token in FORBIDDEN_ARTIFACT_TOKENS):
            return True
    return False


def _path_exists(path: str | Path | None) -> bool:
    return path is not None and Path(path).exists()


def _read_record(path: str | Path | None) -> dict[str, Any]:
    if path is None or not Path(path).exists():
        return {}
    resolved = Path(path)
    if resolved.suffix.lower() == ".csv":
        frame = _read_csv_path(resolved)
        return (frame.head(1).to_dict("records") or [{}])[0]
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_csv_path(path: str | Path | None) -> pd.DataFrame:
    if path is None or not Path(path).exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype=str)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_gate_csv(path: Path, gates: list[GlobalApprovedForPaperApprovalReviewGateResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([gate.__dict__ for gate in gates]).to_csv(path, index=False)


def _gate(gate: str, status: str, message: str) -> GlobalApprovedForPaperApprovalReviewGateResult:
    return GlobalApprovedForPaperApprovalReviewGateResult(gate=gate, status=status, message=message)


def _block(gates: list[GlobalApprovedForPaperApprovalReviewGateResult], gate: str, status: str) -> str:
    gates.append(_gate(gate, status, status))
    return status


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _run_id(settings: GlobalApprovedForPaperApprovalReviewSettings) -> str:
    payload = {
        key: str(value)
        for key, value in sorted(settings.__dict__.items())
        if key not in {"write_artifacts", "research_governed", "diagnostic_output"}
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]
