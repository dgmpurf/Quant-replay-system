"""Report-only actual training_result phase 1 workflow."""

from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_TRAINING_RESULT_INPUT = "NO_TRAINING_RESULT_INPUT"
TRAINING_RESULT_INPUT_FOUND = "TRAINING_RESULT_INPUT_FOUND"
TRAINING_RESULT_APPROVAL_BLOCKED = "TRAINING_RESULT_APPROVAL_BLOCKED"
TRAINING_RESULT_PLANNING_INPUT_BLOCKED = "TRAINING_RESULT_PLANNING_INPUT_BLOCKED"
TRAINING_RESULT_METRIC_EXTENSION_INPUT_BLOCKED = "TRAINING_RESULT_METRIC_EXTENSION_INPUT_BLOCKED"
TRAINING_RESULT_METRIC_COMPUTATION_INPUT_BLOCKED = "TRAINING_RESULT_METRIC_COMPUTATION_INPUT_BLOCKED"
TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED = "TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED"
TRAINING_RESULT_TRAINING_EVALUATION_INPUT_BLOCKED = "TRAINING_RESULT_TRAINING_EVALUATION_INPUT_BLOCKED"
TRAINING_RESULT_FORWARD_LABEL_INPUT_BLOCKED = "TRAINING_RESULT_FORWARD_LABEL_INPUT_BLOCKED"
TRAINING_RESULT_REPLAY_FREEZE_INPUT_BLOCKED = "TRAINING_RESULT_REPLAY_FREEZE_INPUT_BLOCKED"
TRAINING_RESULT_HEALTH_BLOCKED = "TRAINING_RESULT_HEALTH_BLOCKED"
TRAINING_RESULT_LINEAGE_BLOCKED = "TRAINING_RESULT_LINEAGE_BLOCKED"
TRAINING_RESULT_METRIC_EVIDENCE_BLOCKED = "TRAINING_RESULT_METRIC_EVIDENCE_BLOCKED"
TRAINING_RESULT_LIMITATIONS_BLOCKED = "TRAINING_RESULT_LIMITATIONS_BLOCKED"
TRAINING_RESULT_OVERFIT_WARNING_BLOCKED = "TRAINING_RESULT_OVERFIT_WARNING_BLOCKED"
TRAINING_RESULT_REPORT_ONLY_BLOCKED = "TRAINING_RESULT_REPORT_ONLY_BLOCKED"
TRAINING_RESULT_FORBIDDEN_ARTIFACT_BLOCKED = "TRAINING_RESULT_FORBIDDEN_ARTIFACT_BLOCKED"
TRAINING_RESULT_LEAKAGE_BLOCKED = "TRAINING_RESULT_LEAKAGE_BLOCKED"
TRAINING_RESULT_SIDE_EFFECT_BLOCKED = "TRAINING_RESULT_SIDE_EFFECT_BLOCKED"
TRAINING_RESULT_OVERCLAIM_BLOCKED = "TRAINING_RESULT_OVERCLAIM_BLOCKED"
READY_FOR_TRAINING_RESULT = "READY_FOR_TRAINING_RESULT"
TRAINING_RESULT_CREATED = "TRAINING_RESULT_CREATED"

EXACT_TRAINING_RESULT_APPROVAL_TEXT = (
    "I explicitly authorize Actual Training Result Implementation phase 1 only, and only "
    "report-only actual training_result artifacts. It may create actual training_result metadata, "
    "training_result rows, training_result status, input index, metric evidence reference, lineage "
    "matrix, limitations, overfit warnings, safety flags, recommended_next_task, and similar "
    "report-only artifacts only when immutable TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED, "
    "METRIC_EXTENSION_REPORT_CREATED, METRIC_COMPUTATION_REPORT_CREATED, "
    "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED, TRAINING_EVALUATION_DATASET_CREATED, "
    "FORWARD_RETURN_LABELS_CREATED, and REPLAY_DECISION_FROZEN artifacts have complete lineage "
    "and PASS health. This phase must not train weights, create model_version, create "
    "parameter_version, optimize thresholds, create predictions, create calibrated probabilities, "
    "create feature importance, create stock_profile, generate buy-review eligibility, apply paper "
    "approval, claim strategy performance validation, integrate broker/order/message, or trade. "
    "If any upstream lineage, health, available_time, source_hash, revision_id, quality_status, "
    "report_only/diagnostic_only, metric evidence, limitations, or overfit warnings are missing, "
    "it must fail closed and create no actual training_result artifacts."
)

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/training_result_v0_1")

ARTIFACT_FILES = {
    "metadata": "training_result_metadata.json",
    "report": "training_result_report.md",
    "rows": "training_result_rows.csv",
    "status_json": "training_result_status.json",
    "input_index": "training_result_input_index.csv",
    "metric_evidence_reference": "training_result_metric_evidence_reference.csv",
    "lineage_matrix": "training_result_lineage_matrix.csv",
    "limitations": "training_result_limitations.md",
    "overfit_warnings": "training_result_overfit_warnings.csv",
    "safety_flags": "training_result_safety_flags.json",
    "precondition_results": "training_result_precondition_results.csv",
    "approval_results": "training_result_approval_results.csv",
    "input_lineage_results": "training_result_input_lineage_results.csv",
    "metric_evidence_results": "training_result_metric_evidence_results.csv",
    "leakage_guard_results": "training_result_leakage_guard_results.csv",
    "side_effect_guard_results": "training_result_side_effect_guard_results.csv",
    "overclaim_guard_results": "training_result_overclaim_guard_results.csv",
    "recommended_next_task": "recommended_next_task.md",
}

FORBIDDEN_ARTIFACT_PATTERNS = {
    "model_weights.*",
    "weights.*",
    "model_version.*",
    "parameter_version.*",
    "threshold*",
    "prediction*",
    "probability*",
    "calibrated_probability*",
    "feature_importance*",
    "calibration_report*",
    "validation_report*",
    "performance_validation*",
    "stock_profile*",
    "buy_review*",
    "paper_approval*",
    "broker*",
    "order*",
    "trade*",
    "message*",
}

DOWNSTREAM_FALSE_FIELDS = [
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

UNSAFE_INPUT_FIELDS = ["training_result_created", *DOWNSTREAM_FALSE_FIELDS]

OVERCLAIM_REQUEST_FIELDS = {
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
    "actual_training_result_report_only",
    "actual_training_result_not_weights",
    "actual_training_result_not_model_version",
    "actual_training_result_not_parameter_version",
    "actual_training_result_not_thresholds",
    "actual_training_result_not_predictions",
    "actual_training_result_not_probabilities",
    "actual_training_result_not_feature_importance",
    "actual_training_result_not_stock_profile",
    "actual_training_result_not_buy_review",
    "actual_training_result_not_paper_approval",
    "actual_training_result_not_performance_validation",
    "actual_training_result_not_trading",
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
    "training_result_planning_run_id",
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
    "benchmark_id",
    "benchmark_name",
    "industry_id",
    "industry_name",
    "metric_name",
    "metric_value",
    "numerator_count",
    "denominator_count",
    "source_hash",
    "revision_id",
    "available_time",
    "quality_status",
    "report_only",
    "diagnostic_only",
}
REQUIRED_LIMITATION_PHRASES = {
    "report-only actual training_result artifacts",
    "not weights",
    "not model_version",
    "not parameter_version",
    "not thresholds",
    "not predictions/probabilities/feature importance",
    "not stock_profile",
    "not buy-review",
    "not paper approval",
    "not performance validation",
    "not trading",
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
    "benchmark mismatch",
    "industry classification drift",
    "survivorship bias",
    "lookahead leakage",
    "paper-overfit risk",
}


@dataclass(frozen=True)
class TrainingResultSettings:
    approval_manifest_path: Path | None = None
    training_result_request_manifest_path: Path | None = None
    training_result_planning_metadata_path: Path | None = None
    training_result_planning_input_index_path: Path | None = None
    training_result_planning_metric_evidence_index_path: Path | None = None
    training_result_planning_lineage_matrix_path: Path | None = None
    training_result_planning_limitations_path: Path | None = None
    training_result_planning_overfit_warnings_path: Path | None = None
    training_result_planning_status_artifact_path: Path | None = None
    training_result_planning_health_artifact_path: Path | None = None
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
    allow_training_result: bool = False
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class TrainingResultGateResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str = ""
    observed_value: str = ""


TrainingResultApprovalResult = TrainingResultGateResult
TrainingResultInputLineageResult = TrainingResultGateResult
TrainingResultMetricEvidenceResult = TrainingResultGateResult
TrainingResultLimitationResult = TrainingResultGateResult
TrainingResultOverfitWarningResult = TrainingResultGateResult
TrainingResultLeakageGuardResult = TrainingResultGateResult
TrainingResultSideEffectGuardResult = TrainingResultGateResult
TrainingResultOverclaimResult = TrainingResultGateResult


@dataclass(frozen=True)
class TrainingResultResult:
    training_result_run_id: str
    status: str
    workflow_stage: str
    ready_for_training_result: bool
    training_result_executed: bool
    training_result_created: bool
    artifact_path: str
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
    metric_evidence_names_present: str = ""
    metric_evidence_reference_count: int = 0
    training_result_row_count: int = 0
    eligible_training_result_row_count: int = 0
    quarantined_training_result_row_count: int = 0
    limitations_created: bool = False
    overfit_warnings_created: bool = False
    blocker_count: int = 0
    warning_count: int = 0
    next_action: str = ""
    safety_statement: str = (
        "TRAINING_RESULT_CREATED means report-only actual training_result artifacts only: "
        "not weights, not model_version, not parameter_version, not thresholds, "
        "not predictions/probabilities/feature importance, not stock_profile, not buy-review, "
        "not paper approval, not performance validation, and not trading."
    )
    report_only: bool = True
    diagnostic_only: bool = True
    artifact_paths: dict[str, Path] = field(default_factory=dict)
    gate_results: list[TrainingResultGateResult] = field(default_factory=list)
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


def run_training_result(settings: TrainingResultSettings | None = None) -> TrainingResultResult:
    settings = settings or TrainingResultSettings()
    output_root = Path(settings.output_dir)
    _assert_manual_diagnostics_output(output_root)
    run_id = _stable_id(settings)
    artifact_dir = output_root / run_id
    artifact_paths = {"artifact_dir": artifact_dir} | {
        key: artifact_dir / filename for key, filename in ARTIFACT_FILES.items()
    }
    state = _evaluate(settings)
    created = state["status"] == TRAINING_RESULT_CREATED
    ready = state["status"] in {READY_FOR_TRAINING_RESULT, TRAINING_RESULT_CREATED}
    metas = state.get("metas", {})
    lineage_rows = state.get("lineage_rows", [])
    evidence_rows = state.get("metric_evidence_reference", [])
    result = TrainingResultResult(
        training_result_run_id=run_id,
        status=state["status"],
        workflow_stage="TRAINING_RESULT_NO_INPUT" if state["status"] == NO_TRAINING_RESULT_INPUT else state["status"],
        ready_for_training_result=ready,
        training_result_executed=created,
        training_result_created=created,
        artifact_path=str(artifact_dir),
        source_training_result_planning_run_id=str(metas.get("training_result_planning", {}).get("training_result_planning_run_id", "")),
        source_training_result_planning_status=_source_status(metas.get("training_result_planning", {})),
        source_training_result_planning_health_status=_status_value(settings.training_result_planning_health_artifact_path),
        source_metric_extension_run_id=str(metas.get("metric_extension", {}).get("metric_extension_run_id", "")),
        source_metric_extension_status=_source_status(metas.get("metric_extension", {})),
        source_metric_extension_health_status=_status_value(settings.metric_extension_health_artifact_path),
        source_metric_computation_run_id=str(metas.get("metric_computation", {}).get("metric_computation_run_id", "")),
        source_metric_computation_status=_source_status(metas.get("metric_computation", {})),
        source_metric_computation_health_status=_status_value(settings.metric_computation_health_artifact_path),
        source_metric_evaluation_planning_run_id=str(metas.get("metric_evaluation", {}).get("metric_evaluation_run_id", "")),
        source_metric_evaluation_status=_source_status(metas.get("metric_evaluation", {})),
        source_metric_evaluation_health_status=_status_value(settings.metric_evaluation_health_artifact_path),
        source_training_evaluation_run_id=str(metas.get("training_evaluation", {}).get("training_evaluation_run_id", "")),
        source_training_evaluation_status=_source_status(metas.get("training_evaluation", {})),
        source_training_evaluation_health_status=_status_value(settings.training_evaluation_health_artifact_path),
        source_forward_return_label_run_id=str(metas.get("forward_return_label", {}).get("forward_return_label_run_id", "")),
        source_forward_return_label_status=_source_status(metas.get("forward_return_label", {})),
        source_forward_return_label_health_status=_status_value(settings.forward_return_label_health_artifact_path),
        source_replay_decision_freeze_run_id=str(metas.get("replay_decision_freeze", {}).get("replay_decision_freeze_run_id", "")),
        source_replay_decision_freeze_status=_source_status(metas.get("replay_decision_freeze", {})),
        source_replay_decision_freeze_health_status=_status_value(settings.replay_decision_freeze_health_artifact_path),
        metric_evidence_names_present=",".join(sorted({str(row.get("metric_name", "")) for row in evidence_rows})),
        metric_evidence_reference_count=len(evidence_rows),
        training_result_row_count=len(lineage_rows) if created else 0,
        eligible_training_result_row_count=len(lineage_rows) if created else 0,
        quarantined_training_result_row_count=state.get("quarantined_training_result_row_count", 0),
        limitations_created=created,
        overfit_warnings_created=created,
        blocker_count=0 if ready else len(state.get("gate_results", [])),
        warning_count=0,
        next_action=_next_action(state["status"]),
        report_only=settings.report_only,
        diagnostic_only=settings.diagnostic_only,
        artifact_paths=artifact_paths,
        gate_results=state.get("gate_results", []),
    )
    if settings.write_artifacts:
        write_training_result_artifacts(result, state)
    return result


def write_training_result_artifacts(result: TrainingResultResult, state: dict[str, Any] | None = None) -> None:
    state = state or {}
    artifact_dir = result.artifact_paths["artifact_dir"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    result.artifact_paths["metadata"].write_text(json.dumps(_metadata(result), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["status_json"].write_text(json.dumps(_status_json(result), indent=2, sort_keys=True), encoding="utf-8")
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
    if result.training_result_created:
        _write_csv(result.artifact_paths["rows"], pd.DataFrame(_training_result_rows(result, state.get("lineage_rows", []))))
        _write_csv(result.artifact_paths["input_index"], pd.DataFrame(_input_index(result)))
        _write_csv(result.artifact_paths["metric_evidence_reference"], pd.DataFrame(state.get("metric_evidence_reference", [])))
        _write_csv(result.artifact_paths["lineage_matrix"], pd.DataFrame(_lineage_matrix(result)))
        result.artifact_paths["limitations"].write_text(_limitations(), encoding="utf-8")
        _write_csv(result.artifact_paths["overfit_warnings"], pd.DataFrame(_overfit_warnings()))


def _evaluate(settings: TrainingResultSettings) -> dict[str, Any]:
    state: dict[str, Any] = {"status": NO_TRAINING_RESULT_INPUT, "gate_results": []}
    if _is_no_input(settings):
        return state
    approval = _load_json(settings.approval_manifest_path)
    if str(approval.get("approval_text", "")) != EXACT_TRAINING_RESULT_APPROVAL_TEXT:
        return _blocked(TRAINING_RESULT_APPROVAL_BLOCKED, "approval", "exact_approval", "exact approval missing")
    request = _load_json(settings.training_result_request_manifest_path)
    if _any_truthy(request, OVERCLAIM_REQUEST_FIELDS):
        return _blocked(TRAINING_RESULT_OVERCLAIM_BLOCKED, "overclaim_guard", "request_scope", "request asks for forbidden downstream artifact")
    if _any_truthy(request, SIDE_EFFECT_REQUEST_FIELDS):
        return _blocked(TRAINING_RESULT_SIDE_EFFECT_BLOCKED, "side_effect_guard", "request_side_effect", "request asks for side effects")
    missing = _first_missing_required_path(settings)
    if missing:
        return _blocked(missing[1], "precondition", missing[0], "required input missing")
    if _forbidden_artifact_exists(settings):
        return _blocked(TRAINING_RESULT_FORBIDDEN_ARTIFACT_BLOCKED, "precondition", "forbidden_artifact", "forbidden training/model/trading artifact exists in input folders")

    metas = {
        "training_result_planning": _load_json(settings.training_result_planning_metadata_path),
        "metric_extension": _load_json(settings.metric_extension_metadata_path),
        "metric_computation": _load_json(settings.metric_computation_metadata_path),
        "metric_evaluation": _load_json(settings.metric_evaluation_metadata_path),
        "training_evaluation": _load_json(settings.training_evaluation_metadata_path),
        "forward_return_label": _load_json(settings.forward_return_label_metadata_path),
        "replay_decision_freeze": _load_json(settings.replay_decision_freeze_metadata_path),
    }
    expected_statuses = [
        ("training_result_planning", settings.training_result_planning_status_artifact_path, "TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED", TRAINING_RESULT_PLANNING_INPUT_BLOCKED),
        ("metric_extension", settings.metric_extension_status_artifact_path, "METRIC_EXTENSION_REPORT_CREATED", TRAINING_RESULT_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_computation", settings.metric_computation_status_artifact_path, "METRIC_COMPUTATION_REPORT_CREATED", TRAINING_RESULT_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_evaluation", settings.metric_evaluation_status_artifact_path, "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED", TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation", settings.training_evaluation_status_artifact_path, "TRAINING_EVALUATION_DATASET_CREATED", TRAINING_RESULT_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("forward_return_label", settings.forward_return_label_status_artifact_path, "FORWARD_RETURN_LABELS_CREATED", TRAINING_RESULT_FORWARD_LABEL_INPUT_BLOCKED),
        ("replay_decision_freeze", settings.replay_decision_freeze_status_artifact_path, "REPLAY_DECISION_FROZEN", TRAINING_RESULT_REPLAY_FREEZE_INPUT_BLOCKED),
    ]
    for meta_key, status_path, expected, blocked_status in expected_statuses:
        observed = _source_status(metas[meta_key]) or _status_value(status_path)
        if observed != expected:
            return _blocked(blocked_status, "precondition", meta_key, f"expected {expected}, observed {observed}")
    for path in [
        settings.training_result_planning_health_artifact_path,
        settings.metric_extension_health_artifact_path,
        settings.metric_computation_health_artifact_path,
        settings.metric_evaluation_health_artifact_path,
        settings.training_evaluation_health_artifact_path,
        settings.forward_return_label_health_artifact_path,
        settings.replay_decision_freeze_health_artifact_path,
    ]:
        if _status_value(path) != "PASS":
            return _blocked(TRAINING_RESULT_HEALTH_BLOCKED, "precondition", "health", "upstream health must be PASS")

    for path in [
        settings.metric_extension_safety_flags_path,
        settings.metric_computation_safety_flags_path,
        settings.metric_evaluation_safety_flags_path,
        settings.training_evaluation_safety_flags_path,
        settings.side_effect_evidence_bundle_path,
    ]:
        if _unsafe_side_effects(_load_json(path)):
            return _blocked(TRAINING_RESULT_SIDE_EFFECT_BLOCKED, "side_effect_guard", str(path), "unsafe side-effect flag")
    overclaim = _load_json(settings.overclaim_evidence_bundle_path)
    if any(not _truthy(overclaim.get(field)) for field in REQUIRED_OVERCLAIM_TRUE):
        return _blocked(TRAINING_RESULT_OVERCLAIM_BLOCKED, "overclaim_guard", "overclaim_bundle", "required overclaim guard missing")
    leakage = _load_json(settings.leakage_evidence_bundle_path)
    if any(_truthy(value) for value in leakage.values()):
        return _blocked(TRAINING_RESULT_LEAKAGE_BLOCKED, "leakage_guard", "leakage_bundle", "leakage flag true")

    planning_index = pd.read_csv(settings.training_result_planning_input_index_path, dtype=str)
    planning_evidence = pd.read_csv(settings.training_result_planning_metric_evidence_index_path, dtype=str)
    planning_lineage = pd.read_csv(settings.training_result_planning_lineage_matrix_path, dtype=str)
    overfit_warnings = pd.read_csv(settings.training_result_planning_overfit_warnings_path, dtype=str)
    metric_extension_rows = pd.read_csv(settings.metric_extension_result_rows_path, dtype=str)
    metric_computation_summary = pd.read_csv(settings.metric_computation_summary_path, dtype=str)
    training_rows = pd.read_csv(settings.training_evaluation_sample_rows_path, dtype=str)
    metric_evaluation_sample_scope = pd.read_csv(settings.metric_evaluation_sample_scope_path, dtype=str)
    metric_evaluation_denominators = pd.read_csv(settings.metric_evaluation_denominator_rules_path, dtype=str)

    for frame, status in [
        (planning_lineage, TRAINING_RESULT_LINEAGE_BLOCKED),
        (metric_extension_rows, TRAINING_RESULT_LINEAGE_BLOCKED),
    ]:
        missing_col_status = _required_column_blocker(frame, LINEAGE_COLUMNS, status)
        if missing_col_status:
            return missing_col_status
    if "metric_name" not in planning_evidence.columns or "metric_name" not in metric_computation_summary.columns:
        return _blocked(TRAINING_RESULT_METRIC_EVIDENCE_BLOCKED, "metric_evidence", "metric_name", "metric evidence missing")
    if "split_role" not in training_rows.columns:
        return _blocked(TRAINING_RESULT_LINEAGE_BLOCKED, "input_lineage", "split_role", "sample split missing")
    for frame in [planning_lineage, metric_extension_rows, planning_evidence, planning_index, metric_evaluation_sample_scope, metric_evaluation_denominators]:
        if not _all_true(frame, "report_only") or not _all_true(frame, "diagnostic_only"):
            return _blocked(TRAINING_RESULT_REPORT_ONLY_BLOCKED, "precondition", "report_only", "report-only flags must be true")
    if _duplicate_unquarantined(training_rows):
        return _blocked(TRAINING_RESULT_LINEAGE_BLOCKED, "input_lineage", "duplicates", "duplicate sample rows without quarantine")

    evidence_rows = _metric_evidence(planning_evidence)
    evidence_names = {row["metric_name"] for row in evidence_rows}
    if not REQUIRED_METRIC_EVIDENCE.issubset(evidence_names):
        return _blocked(TRAINING_RESULT_METRIC_EVIDENCE_BLOCKED, "metric_evidence", "metric_names", "required metric evidence missing")
    limitations_text = _load_text(settings.training_result_planning_limitations_path)
    if any(phrase not in limitations_text for phrase in REQUIRED_LIMITATION_PHRASES):
        return _blocked(TRAINING_RESULT_LIMITATIONS_BLOCKED, "limitations", "limitations", "required limitations missing")
    if "risk_item" not in overfit_warnings.columns or not REQUIRED_OVERFIT_WARNINGS.issubset(set(overfit_warnings["risk_item"].astype(str))):
        return _blocked(TRAINING_RESULT_OVERFIT_WARNING_BLOCKED, "overfit_warning", "risk_item", "required overfit warnings missing")

    status = TRAINING_RESULT_CREATED if settings.allow_training_result else READY_FOR_TRAINING_RESULT
    return {
        "status": status,
        "gate_results": [
            TrainingResultGateResult("precondition", "all_required_inputs", status, True, ""),
            TrainingResultGateResult("approval", "exact_approval", status, True, ""),
            TrainingResultGateResult("input_lineage", "lineage_complete", status, True, ""),
            TrainingResultGateResult("metric_evidence", "metric_evidence_complete", status, True, ""),
            TrainingResultGateResult("leakage_guard", "no_leakage", status, True, ""),
            TrainingResultGateResult("side_effect_guard", "no_side_effects", status, True, ""),
            TrainingResultGateResult("overclaim_guard", "no_overclaim", status, True, ""),
        ],
        "metas": metas,
        "metric_evidence_reference": evidence_rows,
        "lineage_rows": planning_lineage.to_dict("records"),
        "quarantined_training_result_row_count": int(pd.to_numeric(training_rows.get("quarantine_count", 0), errors="coerce").fillna(0).sum()),
    }


def _is_no_input(settings: TrainingResultSettings) -> bool:
    return all(
        getattr(settings, field) is None
        for field in TrainingResultSettings.__dataclass_fields__
        if field.endswith("_path")
    )


def _blocked(status: str, group: str, name: str, reason: str) -> dict[str, Any]:
    return {
        "status": status,
        "gate_results": [TrainingResultGateResult(group, name, status, False, reason)],
    }


def _first_missing_required_path(settings: TrainingResultSettings) -> tuple[str, str] | None:
    groups = [
        ("approval_manifest_path", TRAINING_RESULT_APPROVAL_BLOCKED),
        ("training_result_request_manifest_path", TRAINING_RESULT_APPROVAL_BLOCKED),
        ("training_result_planning_metadata_path", TRAINING_RESULT_PLANNING_INPUT_BLOCKED),
        ("training_result_planning_input_index_path", TRAINING_RESULT_PLANNING_INPUT_BLOCKED),
        ("training_result_planning_metric_evidence_index_path", TRAINING_RESULT_METRIC_EVIDENCE_BLOCKED),
        ("training_result_planning_lineage_matrix_path", TRAINING_RESULT_LINEAGE_BLOCKED),
        ("training_result_planning_limitations_path", TRAINING_RESULT_LIMITATIONS_BLOCKED),
        ("training_result_planning_overfit_warnings_path", TRAINING_RESULT_OVERFIT_WARNING_BLOCKED),
        ("training_result_planning_status_artifact_path", TRAINING_RESULT_PLANNING_INPUT_BLOCKED),
        ("training_result_planning_health_artifact_path", TRAINING_RESULT_HEALTH_BLOCKED),
        ("metric_extension_metadata_path", TRAINING_RESULT_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_result_rows_path", TRAINING_RESULT_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_summary_path", TRAINING_RESULT_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_safety_flags_path", TRAINING_RESULT_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_status_artifact_path", TRAINING_RESULT_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_health_artifact_path", TRAINING_RESULT_HEALTH_BLOCKED),
        ("metric_computation_metadata_path", TRAINING_RESULT_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_result_rows_path", TRAINING_RESULT_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_summary_path", TRAINING_RESULT_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_safety_flags_path", TRAINING_RESULT_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_status_artifact_path", TRAINING_RESULT_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_health_artifact_path", TRAINING_RESULT_HEALTH_BLOCKED),
        ("metric_evaluation_metadata_path", TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_input_index_path", TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_sample_scope_path", TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_denominator_rules_path", TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_safety_flags_path", TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_status_artifact_path", TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_health_artifact_path", TRAINING_RESULT_HEALTH_BLOCKED),
        ("training_evaluation_metadata_path", TRAINING_RESULT_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_sample_rows_path", TRAINING_RESULT_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_safety_flags_path", TRAINING_RESULT_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_status_artifact_path", TRAINING_RESULT_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_health_artifact_path", TRAINING_RESULT_HEALTH_BLOCKED),
        ("forward_return_label_metadata_path", TRAINING_RESULT_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_rows_path", TRAINING_RESULT_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_status_artifact_path", TRAINING_RESULT_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_health_artifact_path", TRAINING_RESULT_HEALTH_BLOCKED),
        ("replay_decision_freeze_metadata_path", TRAINING_RESULT_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_rows_path", TRAINING_RESULT_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_status_artifact_path", TRAINING_RESULT_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_health_artifact_path", TRAINING_RESULT_HEALTH_BLOCKED),
        ("leakage_evidence_bundle_path", TRAINING_RESULT_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", TRAINING_RESULT_OVERCLAIM_BLOCKED),
        ("side_effect_evidence_bundle_path", TRAINING_RESULT_SIDE_EFFECT_BLOCKED),
    ]
    for field, status in groups:
        path = getattr(settings, field)
        if path is None or not Path(path).exists():
            return field, status
    return None


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


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


def _any_truthy(payload: dict[str, Any], fields: set[str]) -> bool:
    return any(_truthy(payload.get(field)) for field in fields)


def _unsafe_side_effects(payload: dict[str, Any]) -> bool:
    return any(_truthy(payload.get(field)) for field in UNSAFE_INPUT_FIELDS)


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _all_true(frame: pd.DataFrame, column: str) -> bool:
    if column not in frame.columns:
        return False
    return frame[column].map(_truthy).all()


def _required_column_blocker(frame: pd.DataFrame, columns: set[str], status: str) -> dict[str, Any] | None:
    missing = sorted(columns - set(frame.columns))
    if missing:
        if missing[0] in {"report_only", "diagnostic_only"}:
            return _blocked(TRAINING_RESULT_REPORT_ONLY_BLOCKED, "input_lineage", missing[0], "report-only flag missing")
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


def _forbidden_artifact_exists(settings: TrainingResultSettings) -> bool:
    parents = {
        Path(path).parent
        for field in TrainingResultSettings.__dataclass_fields__
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


def _metric_evidence(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in frame.to_dict("records"):
        name = str(record.get("metric_name", ""))
        if name not in REQUIRED_METRIC_EVIDENCE:
            continue
        rows.append(
            {
                "training_result_run_id": "",
                "evidence_source_stage": str(record.get("source_artifact_family", "")),
                "source_run_id": str(record.get("source_run_id", "")),
                "metric_name": name,
                "metric_value": record.get("metric_value", ""),
                "numerator_count": record.get("numerator_count", ""),
                "denominator_count": record.get("denominator_count", ""),
                "evidence_role": "training_result evidence reference",
                "permitted_interpretation": "evidence only; descriptive report-only context",
                "forbidden_interpretation": "not strategy performance validation; not profitability proof; not model weights; not predictions; not trading permission",
                "report_only": True,
                "diagnostic_only": True,
            }
        )
    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        deduped.setdefault(str(row["metric_name"]), row)
    return list(deduped.values())


def _training_result_rows(result: TrainingResultResult, lineage_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(lineage_rows, start=1):
        rows.append(
            {
                "training_result_run_id": result.training_result_run_id,
                "training_result_row_id": f"{result.training_result_run_id}_{index:04d}",
                "replay_decision_id": row.get("replay_decision_id", ""),
                "forward_return_label_id": row.get("forward_return_label_id", ""),
                "symbol": row.get("symbol", ""),
                "replay_as_of_date": row.get("replay_as_of_date", ""),
                "split_role": row.get("split_role", ""),
                "label_name": row.get("label_name", ""),
                "horizon_trading_days": row.get("horizon_trading_days", ""),
                "source_training_result_planning_run_id": row.get("training_result_planning_run_id", ""),
                "source_metric_extension_run_id": row.get("metric_extension_run_id", ""),
                "source_metric_computation_run_id": row.get("metric_computation_run_id", ""),
                "source_metric_evaluation_run_id": row.get("metric_evaluation_run_id", ""),
                "source_training_evaluation_run_id": row.get("training_evaluation_run_id", ""),
                "source_forward_return_label_run_id": row.get("forward_return_label_run_id", ""),
                "source_replay_decision_freeze_run_id": row.get("replay_decision_freeze_run_id", ""),
                "metric_evidence_names": result.metric_evidence_names_present,
                "metric_evidence_reference_count": result.metric_evidence_reference_count,
                "limitation_reference": "training_result_limitations.md",
                "overfit_warning_reference": "training_result_overfit_warnings.csv",
                "source_hash": row.get("source_hash", ""),
                "revision_id": row.get("revision_id", ""),
                "available_time": row.get("available_time", ""),
                "quality_status": row.get("quality_status", ""),
                "report_only": True,
                "diagnostic_only": True,
            }
        )
    return rows


def _input_index(result: TrainingResultResult) -> list[dict[str, Any]]:
    rows = [
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
            "training_result_run_id": result.training_result_run_id,
            "input_component": family,
            "artifact_name": family,
            "artifact_path": "",
            "source_stage": family,
            "source_run_id": run_id,
            "row_count": result.training_result_row_count,
            "required_for_training_result": True,
            "immutable_required": True,
            "source_hash_coverage": "PASS",
            "revision_id_coverage": "PASS",
            "available_time_coverage": "PASS",
            "quality_status_coverage": "PASS",
            "health_status": health,
            "report_only": True,
            "diagnostic_only": True,
        }
        for family, run_id, _status, health in rows
    ]


def _lineage_matrix(result: TrainingResultResult) -> list[dict[str, Any]]:
    lineage = {
        "training_result_planning_run_id": result.source_training_result_planning_run_id,
        "metric_extension_run_id": result.source_metric_extension_run_id,
        "metric_computation_run_id": result.source_metric_computation_run_id,
        "metric_evaluation_run_id": result.source_metric_evaluation_planning_run_id,
        "training_evaluation_run_id": result.source_training_evaluation_run_id,
        "forward_return_label_run_id": result.source_forward_return_label_run_id,
        "replay_decision_freeze_run_id": result.source_replay_decision_freeze_run_id,
    }
    return [
        {
            "training_result_run_id": result.training_result_run_id,
            "lineage_item": item,
            "source_stage": item.replace("_run_id", ""),
            "source_run_id": value,
            "required": True,
            "observed": bool(value),
            "health_status": "PASS",
            "available_time_coverage": "PASS",
            "source_hash_coverage": "PASS",
            "revision_id_coverage": "PASS",
            "quality_status_coverage": "PASS",
            "accepted_for_training_result": True,
            "report_only": True,
            "diagnostic_only": True,
        }
        for item, value in lineage.items()
    ]


def _limitations() -> str:
    return (
        "# Training Result Limitations\n\n"
        "This workflow creates report-only actual training_result artifacts only.\n\n"
        "It is not weights, not model_version, not parameter_version, not thresholds, "
        "not predictions/probabilities/feature importance, not stock_profile, not buy-review, "
        "not paper approval, not performance validation, and not trading.\n\n"
        "Metric evidence is bounded and descriptive. Positive relative return is not profitability proof.\n"
    )


def _overfit_warnings() -> list[dict[str, Any]]:
    return [
        {
            "warning_id": f"tr_overfit_{index:03d}",
            "risk_item": risk,
            "applies_to_training_result": True,
            "guard_required": True,
            "severity": "WARN",
            "notes": "Required report-only overfit warning.",
        }
        for index, risk in enumerate(sorted(REQUIRED_OVERFIT_WARNINGS), start=1)
    ]


def _metadata(result: TrainingResultResult) -> dict[str, Any]:
    payload = {
        "training_result_run_id": result.training_result_run_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "execution_status": result.status,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "ready_for_training_result": result.ready_for_training_result,
        "training_result_executed": result.training_result_executed,
        "training_result_created": result.training_result_created,
        "metric_evidence_names_present": result.metric_evidence_names_present,
        "metric_evidence_reference_count": result.metric_evidence_reference_count,
        "training_result_row_count": result.training_result_row_count,
        "eligible_training_result_row_count": result.eligible_training_result_row_count,
        "quarantined_training_result_row_count": result.quarantined_training_result_row_count,
        "limitations_created": result.limitations_created,
        "overfit_warnings_created": result.overfit_warnings_created,
        "artifact_path": result.artifact_path,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
    }
    for field in [
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


def _status_json(result: TrainingResultResult) -> dict[str, Any]:
    return {
        "training_result_run_id": result.training_result_run_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "ready_for_training_result": result.ready_for_training_result,
        "training_result_executed": result.training_result_executed,
        "training_result_created": result.training_result_created,
        "training_result_row_count": result.training_result_row_count,
        "metric_evidence_names_present": result.metric_evidence_names_present,
        "limitations_created": result.limitations_created,
        "overfit_warnings_created": result.overfit_warnings_created,
        "next_action": result.next_action,
        **_safety_flags(result),
    }


def _safety_flags(result: TrainingResultResult) -> dict[str, Any]:
    return {
        "training_result_created": result.training_result_created,
        **{field: getattr(result, field) for field in DOWNSTREAM_FALSE_FIELDS},
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
    }


def _render_report(result: TrainingResultResult) -> str:
    return (
        "# Actual Training Result Phase 1 Report\n\n"
        f"- training_result_run_id: {result.training_result_run_id}\n"
        f"- status: {result.status}\n"
        f"- workflow_stage: {result.workflow_stage}\n"
        f"- ready_for_training_result: {result.ready_for_training_result}\n"
        f"- training_result_created: {result.training_result_created}\n"
        f"- training_result_row_count: {result.training_result_row_count}\n"
        f"- metric_evidence_names_present: {result.metric_evidence_names_present}\n\n"
        "This workflow creates report-only actual training_result artifacts only. It is not weights, "
        "not model_version, not parameter_version, not thresholds, not predictions/probabilities/feature importance, "
        "not stock_profile, not buy-review, not paper approval, not performance validation, and not trading.\n"
    )


def _recommended_next_task(result: TrainingResultResult) -> str:
    if result.status == TRAINING_RESULT_CREATED:
        return "Actual Training Result Artifact Views Report-Only v0.1\n"
    if result.status == READY_FOR_TRAINING_RESULT:
        return "Review ready state and rerun with --allow-training-result only if report-only actual training_result artifacts should be created.\n"
    return "Provide exact approval and complete upstream report-only lineage before actual training_result creation.\n"


def _next_action(status: str) -> str:
    if status == TRAINING_RESULT_CREATED:
        return "Review report-only actual training_result artifacts before adding artifact views."
    if status == READY_FOR_TRAINING_RESULT:
        return "Rerun with explicit allow only if report-only actual training_result artifacts should be created."
    if status == NO_TRAINING_RESULT_INPUT:
        return "Provide exact approval and immutable upstream report-only artifacts."
    return "Resolve blocked actual training_result gates before rerun."


def _gate_frame(gates: list[TrainingResultGateResult], group: str) -> pd.DataFrame:
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


def _assert_manual_diagnostics_output(path: Path) -> None:
    normalized = str(path).replace("\\", "/")
    if "/outputs/reports/manual_diagnostics/" not in f"/{normalized}/" and not normalized.startswith("outputs/reports/manual_diagnostics/"):
        raise ValueError("training result output must stay under outputs/reports/manual_diagnostics")


def _stable_id(settings: TrainingResultSettings) -> str:
    payload = {
        field: str(getattr(settings, field))
        for field in TrainingResultSettings.__dataclass_fields__
        if field != "write_artifacts"
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:12]
