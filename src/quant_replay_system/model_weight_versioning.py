"""Report-only model weights/versioning/threshold/prediction phase 1 workflow."""

from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_MODEL_WEIGHT_VERSIONING_INPUT = "NO_MODEL_WEIGHT_VERSIONING_INPUT"
MODEL_WEIGHT_VERSIONING_INPUT_FOUND = "MODEL_WEIGHT_VERSIONING_INPUT_FOUND"
MODEL_WEIGHT_VERSIONING_APPROVAL_BLOCKED = "MODEL_WEIGHT_VERSIONING_APPROVAL_BLOCKED"
MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_INPUT_BLOCKED = "MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_INPUT_BLOCKED"
MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_PLANNING_INPUT_BLOCKED = (
    "MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_PLANNING_INPUT_BLOCKED"
)
MODEL_WEIGHT_VERSIONING_METRIC_EXTENSION_INPUT_BLOCKED = (
    "MODEL_WEIGHT_VERSIONING_METRIC_EXTENSION_INPUT_BLOCKED"
)
MODEL_WEIGHT_VERSIONING_METRIC_COMPUTATION_INPUT_BLOCKED = (
    "MODEL_WEIGHT_VERSIONING_METRIC_COMPUTATION_INPUT_BLOCKED"
)
MODEL_WEIGHT_VERSIONING_METRIC_EVALUATION_INPUT_BLOCKED = (
    "MODEL_WEIGHT_VERSIONING_METRIC_EVALUATION_INPUT_BLOCKED"
)
MODEL_WEIGHT_VERSIONING_TRAINING_EVALUATION_INPUT_BLOCKED = (
    "MODEL_WEIGHT_VERSIONING_TRAINING_EVALUATION_INPUT_BLOCKED"
)
MODEL_WEIGHT_VERSIONING_FORWARD_LABEL_INPUT_BLOCKED = "MODEL_WEIGHT_VERSIONING_FORWARD_LABEL_INPUT_BLOCKED"
MODEL_WEIGHT_VERSIONING_REPLAY_FREEZE_INPUT_BLOCKED = "MODEL_WEIGHT_VERSIONING_REPLAY_FREEZE_INPUT_BLOCKED"
MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED = "MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED"
MODEL_WEIGHT_VERSIONING_LINEAGE_BLOCKED = "MODEL_WEIGHT_VERSIONING_LINEAGE_BLOCKED"
MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_ROWS_BLOCKED = (
    "MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_ROWS_BLOCKED"
)
MODEL_WEIGHT_VERSIONING_METRIC_EVIDENCE_BLOCKED = "MODEL_WEIGHT_VERSIONING_METRIC_EVIDENCE_BLOCKED"
MODEL_WEIGHT_VERSIONING_LIMITATIONS_BLOCKED = "MODEL_WEIGHT_VERSIONING_LIMITATIONS_BLOCKED"
MODEL_WEIGHT_VERSIONING_OVERFIT_WARNING_BLOCKED = "MODEL_WEIGHT_VERSIONING_OVERFIT_WARNING_BLOCKED"
MODEL_WEIGHT_VERSIONING_REPORT_ONLY_BLOCKED = "MODEL_WEIGHT_VERSIONING_REPORT_ONLY_BLOCKED"
MODEL_WEIGHT_VERSIONING_FORBIDDEN_ARTIFACT_BLOCKED = "MODEL_WEIGHT_VERSIONING_FORBIDDEN_ARTIFACT_BLOCKED"
MODEL_WEIGHT_VERSIONING_LEAKAGE_BLOCKED = "MODEL_WEIGHT_VERSIONING_LEAKAGE_BLOCKED"
MODEL_WEIGHT_VERSIONING_SIDE_EFFECT_BLOCKED = "MODEL_WEIGHT_VERSIONING_SIDE_EFFECT_BLOCKED"
MODEL_WEIGHT_VERSIONING_OVERCLAIM_BLOCKED = "MODEL_WEIGHT_VERSIONING_OVERCLAIM_BLOCKED"
READY_FOR_MODEL_WEIGHT_VERSIONING = "READY_FOR_MODEL_WEIGHT_VERSIONING"
MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED = "MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED"

EXACT_MODEL_WEIGHT_VERSIONING_APPROVAL_TEXT = (
    "I explicitly authorize Model Weights / Versioning / Threshold / Prediction Implementation phase 1 only, "
    "and only report-only research artifacts. It may create model training metadata, model weights reference, "
    "model_version metadata, parameter_version metadata, threshold plan, prediction rows, probability calibration "
    "report, feature importance report, model input index, model lineage matrix, model limitations, model overfit "
    "warnings, model safety flags, recommended_next_task, and similar report-only research artifacts only when "
    "immutable TRAINING_RESULT_CREATED, TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED, "
    "METRIC_EXTENSION_REPORT_CREATED, METRIC_COMPUTATION_REPORT_CREATED, "
    "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED, TRAINING_EVALUATION_DATASET_CREATED, "
    "FORWARD_RETURN_LABELS_CREATED, and REPLAY_DECISION_FROZEN artifacts have complete lineage and PASS health. "
    "This phase must not create active stock_profile, generate real buy-review eligibility, apply paper approval, "
    "claim strategy performance validation, integrate broker/order/message, or trade. If any upstream lineage, "
    "health, available_time, source_hash, revision_id, quality_status, report_only/diagnostic_only, "
    "training_result rows, metric evidence, limitations, overfit warnings, or exact approval are missing, it must "
    "fail closed and create no model/weights/versioning/threshold/prediction artifacts."
)

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/model_weight_versioning_v0_1")

ARTIFACT_FILES = {
    "model_training_metadata": "model_training_metadata.json",
    "report": "model_weight_versioning_report.md",
    "model_weights_reference": "model_weights_reference.json",
    "model_version_metadata": "model_version_metadata.json",
    "parameter_version_metadata": "parameter_version_metadata.json",
    "threshold_plan": "threshold_plan.csv",
    "prediction_rows": "prediction_rows.csv",
    "probability_calibration_report": "probability_calibration_report.md",
    "feature_importance_report": "feature_importance_report.csv",
    "model_input_index": "model_input_index.csv",
    "model_lineage_matrix": "model_lineage_matrix.csv",
    "model_limitations": "model_limitations.md",
    "model_overfit_warnings": "model_overfit_warnings.csv",
    "model_safety_flags": "model_safety_flags.json",
    "model_precondition_results": "model_precondition_results.csv",
    "model_approval_results": "model_approval_results.csv",
    "model_input_lineage_results": "model_input_lineage_results.csv",
    "model_training_result_input_results": "model_training_result_input_results.csv",
    "model_metric_evidence_results": "model_metric_evidence_results.csv",
    "model_leakage_guard_results": "model_leakage_guard_results.csv",
    "model_side_effect_guard_results": "model_side_effect_guard_results.csv",
    "model_overclaim_guard_results": "model_overclaim_guard_results.csv",
    "recommended_next_task": "recommended_next_task.md",
}

SUBSTANTIVE_ARTIFACT_KEYS = {
    "model_weights_reference",
    "model_version_metadata",
    "parameter_version_metadata",
    "threshold_plan",
    "prediction_rows",
    "probability_calibration_report",
    "feature_importance_report",
    "model_input_index",
    "model_lineage_matrix",
    "model_limitations",
    "model_overfit_warnings",
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

REQUIRED_MODEL_OVERCLAIM_TRUE = {
    "model_artifacts_report_only",
    "model_artifacts_not_stock_profile",
    "model_artifacts_not_buy_review",
    "model_artifacts_not_paper_approval",
    "model_artifacts_not_performance_validation",
    "model_artifacts_not_trading",
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
    "benchmark mismatch",
    "industry classification drift",
    "survivorship bias",
    "lookahead leakage",
    "paper-overfit risk",
}

REQUIRED_LIMITATION_PHRASES = {
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

DOWNSTREAM_FALSE_FIELDS = [
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

FORBIDDEN_ARTIFACT_PATTERNS = {
    "active_stock_profile*",
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
    "active_model*",
    "promoted_model*",
    "production_model*",
    "current_candidates*",
    "snapshot*",
}

SOURCE_STATUS_EXPECTATIONS = {
    "training_result": ("TRAINING_RESULT_CREATED", MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_INPUT_BLOCKED),
    "training_result_planning": (
        "TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED",
        MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_PLANNING_INPUT_BLOCKED,
    ),
    "metric_extension": ("METRIC_EXTENSION_REPORT_CREATED", MODEL_WEIGHT_VERSIONING_METRIC_EXTENSION_INPUT_BLOCKED),
    "metric_computation": ("METRIC_COMPUTATION_REPORT_CREATED", MODEL_WEIGHT_VERSIONING_METRIC_COMPUTATION_INPUT_BLOCKED),
    "metric_evaluation": (
        "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED",
        MODEL_WEIGHT_VERSIONING_METRIC_EVALUATION_INPUT_BLOCKED,
    ),
    "training_evaluation": ("TRAINING_EVALUATION_DATASET_CREATED", MODEL_WEIGHT_VERSIONING_TRAINING_EVALUATION_INPUT_BLOCKED),
    "forward_return_label": ("FORWARD_RETURN_LABELS_CREATED", MODEL_WEIGHT_VERSIONING_FORWARD_LABEL_INPUT_BLOCKED),
    "replay_decision_freeze": ("REPLAY_DECISION_FROZEN", MODEL_WEIGHT_VERSIONING_REPLAY_FREEZE_INPUT_BLOCKED),
}


@dataclass(frozen=True)
class ModelWeightVersioningSettings:
    approval_manifest_path: Path | None = None
    model_request_manifest_path: Path | None = None
    training_result_metadata_path: Path | None = None
    training_result_rows_path: Path | None = None
    training_result_status_artifact_path: Path | None = None
    training_result_health_artifact_path: Path | None = None
    training_result_input_index_path: Path | None = None
    training_result_metric_evidence_reference_path: Path | None = None
    training_result_lineage_matrix_path: Path | None = None
    training_result_limitations_path: Path | None = None
    training_result_overfit_warnings_path: Path | None = None
    training_result_safety_flags_path: Path | None = None
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
    allow_model_weight_versioning: bool = False
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class ModelWeightVersioningGateResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str = ""
    observed_value: str = ""


ModelWeightVersioningApprovalResult = ModelWeightVersioningGateResult
ModelWeightVersioningInputLineageResult = ModelWeightVersioningGateResult
ModelWeightVersioningMetricEvidenceResult = ModelWeightVersioningGateResult
ModelWeightVersioningTrainingResultInputResult = ModelWeightVersioningGateResult
ModelWeightVersioningLeakageGuardResult = ModelWeightVersioningGateResult
ModelWeightVersioningSideEffectGuardResult = ModelWeightVersioningGateResult
ModelWeightVersioningOverclaimResult = ModelWeightVersioningGateResult


@dataclass(frozen=True)
class ModelWeightVersioningResult:
    model_workflow_run_id: str
    status: str
    workflow_stage: str
    ready_for_model_weight_versioning: bool
    model_weight_versioning_executed: bool
    model_weight_versioning_research_artifacts_created: bool
    artifact_path: str
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
    quarantined_training_result_row_count: int = 0
    metric_evidence_names_present: str = ""
    metric_evidence_reference_count: int = 0
    model_weights_reference_created: bool = False
    model_version_metadata_created: bool = False
    parameter_version_metadata_created: bool = False
    threshold_plan_created: bool = False
    prediction_rows_created: bool = False
    probability_calibration_report_created: bool = False
    feature_importance_report_created: bool = False
    blocker_count: int = 0
    warning_count: int = 0
    next_action: str = ""
    report_only: bool = True
    diagnostic_only: bool = True
    artifact_paths: dict[str, Path] = field(default_factory=dict)
    gate_results: list[ModelWeightVersioningGateResult] = field(default_factory=list)
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


def run_model_weight_versioning(settings: ModelWeightVersioningSettings | None = None) -> ModelWeightVersioningResult:
    settings = settings or ModelWeightVersioningSettings()
    output_root = Path(settings.output_dir)
    _assert_manual_diagnostics_output(output_root)
    run_id = _stable_id(settings)
    artifact_dir = output_root / run_id
    artifact_paths = {"artifact_dir": artifact_dir} | {
        key: artifact_dir / filename for key, filename in ARTIFACT_FILES.items()
    }
    state = _evaluate(settings)
    created = state["status"] == MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED
    ready = state["status"] in {READY_FOR_MODEL_WEIGHT_VERSIONING, MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED}
    rows = state.get("training_result_rows", [])
    evidence = state.get("metric_evidence", [])
    metas = state.get("metas", {})
    training_result_meta = metas.get("training_result", {})

    result = ModelWeightVersioningResult(
        model_workflow_run_id=run_id,
        status=state["status"],
        workflow_stage="MODEL_WEIGHT_VERSIONING_NO_INPUT" if state["status"] == NO_MODEL_WEIGHT_VERSIONING_INPUT else state["status"],
        ready_for_model_weight_versioning=ready,
        model_weight_versioning_executed=created,
        model_weight_versioning_research_artifacts_created=created,
        artifact_path=str(artifact_dir),
        source_training_result_run_id=str(training_result_meta.get("training_result_run_id", "")),
        source_training_result_status=_source_status(training_result_meta),
        source_training_result_health_status=_status_value(settings.training_result_health_artifact_path),
        source_training_result_planning_run_id=_source_run_id(metas.get("training_result_planning", {}), "training_result_planning_run_id"),
        source_training_result_planning_status=_source_status(metas.get("training_result_planning", {})),
        source_training_result_planning_health_status=_status_value(settings.training_result_planning_health_artifact_path),
        source_metric_extension_run_id=_source_run_id(metas.get("metric_extension", {}), "metric_extension_run_id"),
        source_metric_extension_status=_source_status(metas.get("metric_extension", {})),
        source_metric_extension_health_status=_status_value(settings.metric_extension_health_artifact_path),
        source_metric_computation_run_id=_source_run_id(metas.get("metric_computation", {}), "metric_computation_run_id"),
        source_metric_computation_status=_source_status(metas.get("metric_computation", {})),
        source_metric_computation_health_status=_status_value(settings.metric_computation_health_artifact_path),
        source_metric_evaluation_planning_run_id=_source_run_id(metas.get("metric_evaluation", {}), "metric_evaluation_run_id"),
        source_metric_evaluation_status=_source_status(metas.get("metric_evaluation", {})),
        source_metric_evaluation_health_status=_status_value(settings.metric_evaluation_health_artifact_path),
        source_training_evaluation_run_id=_source_run_id(metas.get("training_evaluation", {}), "training_evaluation_run_id"),
        source_training_evaluation_status=_source_status(metas.get("training_evaluation", {})),
        source_training_evaluation_health_status=_status_value(settings.training_evaluation_health_artifact_path),
        source_forward_return_label_run_id=_source_run_id(metas.get("forward_return_label", {}), "forward_return_label_run_id"),
        source_forward_return_label_status=_source_status(metas.get("forward_return_label", {})),
        source_forward_return_label_health_status=_status_value(settings.forward_return_label_health_artifact_path),
        source_replay_decision_freeze_run_id=_source_run_id(metas.get("replay_decision_freeze", {}), "replay_decision_freeze_run_id"),
        source_replay_decision_freeze_status=_source_status(metas.get("replay_decision_freeze", {})),
        source_replay_decision_freeze_health_status=_status_value(settings.replay_decision_freeze_health_artifact_path),
        training_result_row_count=len(rows),
        eligible_training_result_row_count=len(rows),
        quarantined_training_result_row_count=state.get("quarantined_training_result_row_count", 0),
        metric_evidence_names_present=",".join(sorted({str(row.get("metric_name", "")) for row in evidence})),
        metric_evidence_reference_count=len(evidence),
        model_weights_reference_created=created,
        model_version_metadata_created=created,
        parameter_version_metadata_created=created,
        threshold_plan_created=created,
        prediction_rows_created=created,
        probability_calibration_report_created=created,
        feature_importance_report_created=created,
        blocker_count=0 if ready else len(state.get("gate_results", [])),
        next_action=_next_action(state["status"]),
        artifact_paths=artifact_paths,
        gate_results=state.get("gate_results", []),
        report_only=settings.report_only,
        diagnostic_only=settings.diagnostic_only,
    )
    if settings.write_artifacts:
        write_model_weight_versioning_artifacts(result, state)
    return result


def write_model_weight_versioning_artifacts(result: ModelWeightVersioningResult, state: dict[str, Any]) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_json(result.artifact_paths["model_training_metadata"], _metadata(result))
    _write_json(result.artifact_paths["model_safety_flags"], _safety_flags(result))
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(_recommended_next_task(result), encoding="utf-8")

    for group, key in [
        ("precondition", "model_precondition_results"),
        ("approval", "model_approval_results"),
        ("input_lineage", "model_input_lineage_results"),
        ("training_result_input", "model_training_result_input_results"),
        ("metric_evidence", "model_metric_evidence_results"),
        ("leakage", "model_leakage_guard_results"),
        ("side_effect", "model_side_effect_guard_results"),
        ("overclaim", "model_overclaim_guard_results"),
    ]:
        _write_csv(result.artifact_paths[key], _gate_frame(result.gate_results, group))

    if not result.model_weight_versioning_research_artifacts_created:
        return

    rows = state.get("training_result_rows", [])
    evidence = state.get("metric_evidence", [])
    _write_json(result.artifact_paths["model_weights_reference"], _model_weights_reference(result, rows))
    _write_json(result.artifact_paths["model_version_metadata"], _model_version_metadata(result))
    _write_json(result.artifact_paths["parameter_version_metadata"], _parameter_version_metadata(result))
    _write_csv(result.artifact_paths["threshold_plan"], pd.DataFrame(_threshold_plan(result)))
    _write_csv(result.artifact_paths["prediction_rows"], pd.DataFrame(_prediction_rows(result, rows)))
    result.artifact_paths["probability_calibration_report"].write_text(_probability_calibration_report(), encoding="utf-8")
    _write_csv(result.artifact_paths["feature_importance_report"], pd.DataFrame(_feature_importance_report(result, evidence)))
    _write_csv(result.artifact_paths["model_input_index"], pd.DataFrame(_model_input_index(result)))
    _write_csv(result.artifact_paths["model_lineage_matrix"], pd.DataFrame(_model_lineage_matrix(result, rows)))
    result.artifact_paths["model_limitations"].write_text(_model_limitations(), encoding="utf-8")
    _write_csv(result.artifact_paths["model_overfit_warnings"], pd.DataFrame(_model_overfit_warnings()))


def _evaluate(settings: ModelWeightVersioningSettings) -> dict[str, Any]:
    if not _has_any_input(settings):
        return _state(NO_MODEL_WEIGHT_VERSIONING_INPUT)
    if not settings.approval_manifest_path or not Path(settings.approval_manifest_path).exists():
        return _state(MODEL_WEIGHT_VERSIONING_APPROVAL_BLOCKED, "approval", "approval_manifest", "exact approval missing")
    approval = _load_json(settings.approval_manifest_path)
    if str(approval.get("approval_text", "")).strip() != EXACT_MODEL_WEIGHT_VERSIONING_APPROVAL_TEXT:
        return _state(MODEL_WEIGHT_VERSIONING_APPROVAL_BLOCKED, "approval", "approval_text", "exact approval text missing or invalid")
    request = _load_json(settings.model_request_manifest_path)
    if _any_truthy(
        request,
        {"stock_profile_requested", "buy_review_requested", "paper_approval_requested", "performance_validation_requested"},
    ):
        return _state(MODEL_WEIGHT_VERSIONING_OVERCLAIM_BLOCKED, "overclaim", "request_scope", "unsafe downstream scope requested")
    if _any_truthy(request, {"trading_requested", "broker_api_called", "order_placed", "message_sent"}):
        return _state(MODEL_WEIGHT_VERSIONING_SIDE_EFFECT_BLOCKED, "side_effect", "request_scope", "unsafe side effect requested")

    missing = _first_missing_required_path(settings)
    if missing:
        field, status = missing
        return _state(status, "precondition", field, "required input artifact missing")
    if _forbidden_artifact_exists(settings):
        return _state(MODEL_WEIGHT_VERSIONING_FORBIDDEN_ARTIFACT_BLOCKED, "precondition", "forbidden_artifacts", "forbidden downstream artifact present")

    metas = _load_metas(settings)
    for key, (expected, status) in SOURCE_STATUS_EXPECTATIONS.items():
        if _source_status(metas.get(key, {})) != expected:
            return _state(status, "input_lineage", key, f"expected status {expected}", metas=metas)
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
            return _state(MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED, "input_lineage", health_field, "upstream health is not PASS", metas=metas)

    training_rows_frame = _load_csv(settings.training_result_rows_path)
    if training_rows_frame.empty:
        return _state(MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_ROWS_BLOCKED, "training_result_input", "training_result_rows", "training_result rows missing", metas=metas)
    column_blocker = _required_column_blocker(training_rows_frame, LINEAGE_COLUMNS)
    if column_blocker:
        return _state(column_blocker["status"], "input_lineage", column_blocker["column"], column_blocker["reason"], metas=metas)
    if not _all_true(training_rows_frame, "report_only") or not _all_true(training_rows_frame, "diagnostic_only"):
        return _state(MODEL_WEIGHT_VERSIONING_REPORT_ONLY_BLOCKED, "input_lineage", "report_only", "report_only/diagnostic_only flags missing", metas=metas)

    safety = _load_json(settings.training_result_safety_flags_path)
    if not _truthy(safety.get("report_only")) or not _truthy(safety.get("diagnostic_only")):
        return _state(MODEL_WEIGHT_VERSIONING_REPORT_ONLY_BLOCKED, "training_result_input", "safety_flags", "report_only/diagnostic_only missing", metas=metas)
    if any(_truthy(safety.get(field)) for field in DOWNSTREAM_FALSE_FIELDS):
        return _state(MODEL_WEIGHT_VERSIONING_SIDE_EFFECT_BLOCKED, "side_effect", "training_result_safety", "unsafe downstream flag true", metas=metas)

    evidence_frame = _load_csv(settings.training_result_metric_evidence_reference_path)
    if REQUIRED_METRICS - set(evidence_frame.get("metric_name", pd.Series(dtype=str)).astype(str)):
        return _state(MODEL_WEIGHT_VERSIONING_METRIC_EVIDENCE_BLOCKED, "metric_evidence", "metric_evidence", "required metric evidence missing", metas=metas)

    limitations = _load_text(settings.training_result_limitations_path)
    if any(phrase not in limitations for phrase in REQUIRED_LIMITATION_PHRASES):
        return _state(MODEL_WEIGHT_VERSIONING_LIMITATIONS_BLOCKED, "overclaim", "limitations", "required limitation wording missing", metas=metas)

    warnings_frame = _load_csv(settings.training_result_overfit_warnings_path)
    if REQUIRED_OVERFIT_WARNINGS - set(warnings_frame.get("risk_item", pd.Series(dtype=str)).astype(str)):
        return _state(MODEL_WEIGHT_VERSIONING_OVERFIT_WARNING_BLOCKED, "overclaim", "overfit_warnings", "required overfit warning missing", metas=metas)

    sample_rows = _load_csv(settings.training_evaluation_sample_rows_path)
    if _duplicate_unquarantined(sample_rows):
        return _state(MODEL_WEIGHT_VERSIONING_LINEAGE_BLOCKED, "input_lineage", "duplicate_samples", "duplicate sample rows not quarantined", metas=metas)

    leakage = _load_json(settings.leakage_evidence_bundle_path)
    if any(_truthy(value) for value in leakage.values()):
        return _state(MODEL_WEIGHT_VERSIONING_LEAKAGE_BLOCKED, "leakage", "leakage_bundle", "leakage guard failed", metas=metas)
    side_effect = _load_json(settings.side_effect_evidence_bundle_path)
    if any(_truthy(side_effect.get(field)) for field in DOWNSTREAM_FALSE_FIELDS):
        return _state(MODEL_WEIGHT_VERSIONING_SIDE_EFFECT_BLOCKED, "side_effect", "side_effect_bundle", "side effect guard failed", metas=metas)
    overclaim = _load_json(settings.overclaim_evidence_bundle_path)
    if not all(_truthy(overclaim.get(field)) for field in REQUIRED_MODEL_OVERCLAIM_TRUE):
        return _state(MODEL_WEIGHT_VERSIONING_OVERCLAIM_BLOCKED, "overclaim", "overclaim_bundle", "overclaim guard failed", metas=metas)

    status = MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED if settings.allow_model_weight_versioning else READY_FOR_MODEL_WEIGHT_VERSIONING
    return {
        "status": status,
        "gate_results": [_passed_gate("precondition", "all_required_inputs")],
        "metas": metas,
        "training_result_rows": training_rows_frame.to_dict("records"),
        "metric_evidence": evidence_frame.to_dict("records"),
        "quarantined_training_result_row_count": int(metas.get("training_result", {}).get("quarantined_training_result_row_count", 0) or 0),
    }


def _state(
    status: str,
    group: str = "precondition",
    name: str = "input",
    reason: str = "",
    metas: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "gate_results": [] if status == NO_MODEL_WEIGHT_VERSIONING_INPUT else [_blocked(status, group, name, reason)],
        "metas": metas or {},
        "training_result_rows": [],
        "metric_evidence": [],
    }


def _first_missing_required_path(settings: ModelWeightVersioningSettings) -> tuple[str, str] | None:
    groups = [
        ("training_result_metadata_path", MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_INPUT_BLOCKED),
        ("training_result_rows_path", MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_ROWS_BLOCKED),
        ("training_result_status_artifact_path", MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_INPUT_BLOCKED),
        ("training_result_health_artifact_path", MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("training_result_input_index_path", MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_INPUT_BLOCKED),
        ("training_result_metric_evidence_reference_path", MODEL_WEIGHT_VERSIONING_METRIC_EVIDENCE_BLOCKED),
        ("training_result_lineage_matrix_path", MODEL_WEIGHT_VERSIONING_LINEAGE_BLOCKED),
        ("training_result_limitations_path", MODEL_WEIGHT_VERSIONING_LIMITATIONS_BLOCKED),
        ("training_result_overfit_warnings_path", MODEL_WEIGHT_VERSIONING_OVERFIT_WARNING_BLOCKED),
        ("training_result_safety_flags_path", MODEL_WEIGHT_VERSIONING_REPORT_ONLY_BLOCKED),
        ("training_result_planning_metadata_path", MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_PLANNING_INPUT_BLOCKED),
        ("training_result_planning_health_artifact_path", MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("metric_extension_metadata_path", MODEL_WEIGHT_VERSIONING_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_result_rows_path", MODEL_WEIGHT_VERSIONING_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_health_artifact_path", MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("metric_computation_metadata_path", MODEL_WEIGHT_VERSIONING_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_result_rows_path", MODEL_WEIGHT_VERSIONING_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_health_artifact_path", MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("metric_evaluation_metadata_path", MODEL_WEIGHT_VERSIONING_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_health_artifact_path", MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("training_evaluation_metadata_path", MODEL_WEIGHT_VERSIONING_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_sample_rows_path", MODEL_WEIGHT_VERSIONING_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_health_artifact_path", MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("forward_return_label_metadata_path", MODEL_WEIGHT_VERSIONING_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_rows_path", MODEL_WEIGHT_VERSIONING_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_health_artifact_path", MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("replay_decision_freeze_metadata_path", MODEL_WEIGHT_VERSIONING_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_rows_path", MODEL_WEIGHT_VERSIONING_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_health_artifact_path", MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("leakage_evidence_bundle_path", MODEL_WEIGHT_VERSIONING_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", MODEL_WEIGHT_VERSIONING_OVERCLAIM_BLOCKED),
        ("side_effect_evidence_bundle_path", MODEL_WEIGHT_VERSIONING_SIDE_EFFECT_BLOCKED),
    ]
    for field, status in groups:
        path = getattr(settings, field)
        if path is None or not Path(path).exists():
            return field, status
    return None


def _load_metas(settings: ModelWeightVersioningSettings) -> dict[str, dict[str, Any]]:
    return {
        "training_result": _load_json(settings.training_result_metadata_path),
        "training_result_planning": _load_json(settings.training_result_planning_metadata_path),
        "metric_extension": _load_json(settings.metric_extension_metadata_path),
        "metric_computation": _load_json(settings.metric_computation_metadata_path),
        "metric_evaluation": _load_json(settings.metric_evaluation_metadata_path),
        "training_evaluation": _load_json(settings.training_evaluation_metadata_path),
        "forward_return_label": _load_json(settings.forward_return_label_metadata_path),
        "replay_decision_freeze": _load_json(settings.replay_decision_freeze_metadata_path),
    }


def _metadata(result: ModelWeightVersioningResult) -> dict[str, Any]:
    payload = {
        "model_workflow_run_id": result.model_workflow_run_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "execution_status": result.status,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "ready_for_model_weight_versioning": result.ready_for_model_weight_versioning,
        "model_weight_versioning_executed": result.model_weight_versioning_executed,
        "model_weight_versioning_research_artifacts_created": result.model_weight_versioning_research_artifacts_created,
        "training_result_row_count": result.training_result_row_count,
        "eligible_training_result_row_count": result.eligible_training_result_row_count,
        "quarantined_training_result_row_count": result.quarantined_training_result_row_count,
        "metric_evidence_names_present": result.metric_evidence_names_present,
        "metric_evidence_reference_count": result.metric_evidence_reference_count,
        "model_weights_reference_created": result.model_weights_reference_created,
        "model_version_metadata_created": result.model_version_metadata_created,
        "parameter_version_metadata_created": result.parameter_version_metadata_created,
        "threshold_plan_created": result.threshold_plan_created,
        "prediction_rows_created": result.prediction_rows_created,
        "probability_calibration_report_created": result.probability_calibration_report_created,
        "feature_importance_report_created": result.feature_importance_report_created,
        "artifact_path": result.artifact_path,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
    }
    for field in [
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


def _safety_flags(result: ModelWeightVersioningResult) -> dict[str, Any]:
    return {
        "model_weight_versioning_research_artifacts_created": result.model_weight_versioning_research_artifacts_created,
        **{field: getattr(result, field) for field in DOWNSTREAM_FALSE_FIELDS},
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
    }


def _model_weights_reference(result: ModelWeightVersioningResult, rows: list[dict[str, Any]]) -> dict[str, Any]:
    row = rows[0] if rows else {}
    return {
        "model_workflow_run_id": result.model_workflow_run_id,
        "training_result_run_id": result.source_training_result_run_id,
        "weight_reference_id": f"{result.model_workflow_run_id}_weights_reference",
        "reference_type": "report_only_reference",
        "permitted_interpretation": "report-only research reference",
        "forbidden_interpretation": "executable trading model / stock_profile / paper approval / strategy validation / trading permission",
        "source_hash": row.get("source_hash", ""),
        "revision_id": row.get("revision_id", ""),
        "report_only": True,
        "diagnostic_only": True,
    }


def _model_version_metadata(result: ModelWeightVersioningResult) -> dict[str, Any]:
    return {
        "model_workflow_run_id": result.model_workflow_run_id,
        "model_version_id": f"{result.model_workflow_run_id}_model_version",
        "version_role": "report_only_research",
        "active_model": False,
        "promoted_model": False,
        "production_model": False,
        "report_only": True,
        "diagnostic_only": True,
    }


def _parameter_version_metadata(result: ModelWeightVersioningResult) -> dict[str, Any]:
    return {
        "model_workflow_run_id": result.model_workflow_run_id,
        "parameter_version_id": f"{result.model_workflow_run_id}_parameter_version",
        "parameter_role": "report_only_research",
        "active_parameters": False,
        "report_only": True,
        "diagnostic_only": True,
    }


def _threshold_plan(result: ModelWeightVersioningResult) -> list[dict[str, Any]]:
    items = ["research_threshold_placeholder", "calibration_placeholder"]
    return [
        {
            "model_workflow_run_id": result.model_workflow_run_id,
            "threshold_item": item,
            "proposed_value_or_placeholder": "placeholder_only",
            "threshold_role": "report_only_research",
            "permitted_interpretation": "report-only threshold planning artifact",
            "forbidden_interpretation": "no signal_semantics change; no buy/sell candidates; no active thresholds",
            "report_only": True,
            "diagnostic_only": True,
        }
        for item in items
    ]


def _prediction_rows(result: ModelWeightVersioningResult, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for index, row in enumerate(rows, start=1):
        output.append(
            {
                "model_workflow_run_id": result.model_workflow_run_id,
                "prediction_row_id": f"{result.model_workflow_run_id}_prediction_{index:04d}",
                "training_result_row_id": row.get("training_result_row_id", ""),
                "replay_decision_id": row.get("replay_decision_id", ""),
                "forward_return_label_id": row.get("forward_return_label_id", ""),
                "symbol": row.get("symbol", ""),
                "replay_as_of_date": row.get("replay_as_of_date", ""),
                "split_role": row.get("split_role", ""),
                "label_name": row.get("label_name", ""),
                "horizon_trading_days": row.get("horizon_trading_days", ""),
                "prediction_value_or_placeholder": "placeholder_only",
                "prediction_role": "report_only_research",
                "permitted_interpretation": "report-only prediction research artifact",
                "forbidden_interpretation": "not advisory signals; not current-candidates; not signal_semantics; not trading permission",
                "report_only": True,
                "diagnostic_only": True,
            }
        )
    return output


def _probability_calibration_report() -> str:
    return (
        "# Probability Calibration Report\n\n"
        "Report-only probability calibration research artifact only.\n\n"
        "- no active probabilities\n"
        "- no buy/sell candidates\n"
        "- no stock_profile\n"
        "- no paper approval\n"
        "- no performance validation\n"
        "- no trading\n"
    )


def _feature_importance_report(result: ModelWeightVersioningResult, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    names = [str(row.get("metric_name", "")) for row in evidence] or ["placeholder_feature_group"]
    return [
        {
            "model_workflow_run_id": result.model_workflow_run_id,
            "feature_group_or_name": name,
            "importance_value_or_placeholder": "placeholder_only",
            "importance_role": "report_only_research",
            "permitted_interpretation": "report-only feature importance planning artifact",
            "forbidden_interpretation": "not SHAP for active stock_profile; not buy-review explanation; not trading signal",
            "report_only": True,
            "diagnostic_only": True,
        }
        for name in names
    ]


def _model_input_index(result: ModelWeightVersioningResult) -> list[dict[str, Any]]:
    rows = [
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
            "model_workflow_run_id": result.model_workflow_run_id,
            "input_component": family,
            "source_run_id": run_id,
            "source_status": status,
            "health_status": health,
            "required_for_model_weight_versioning": True,
            "immutable_required": True,
            "report_only": True,
            "diagnostic_only": True,
        }
        for family, run_id, status, health in rows
    ]


def _model_lineage_matrix(result: ModelWeightVersioningResult, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    row = rows[0] if rows else {}
    lineage = {
        "training_result_run_id": result.source_training_result_run_id,
        "training_result_planning_run_id": result.source_training_result_planning_run_id,
        "metric_extension_run_id": result.source_metric_extension_run_id,
        "metric_computation_run_id": result.source_metric_computation_run_id,
        "metric_evaluation_run_id": result.source_metric_evaluation_planning_run_id,
        "training_evaluation_run_id": result.source_training_evaluation_run_id,
        "forward_return_label_run_id": result.source_forward_return_label_run_id,
        "replay_decision_freeze_run_id": result.source_replay_decision_freeze_run_id,
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
            "model_workflow_run_id": result.model_workflow_run_id,
            "lineage_item": item,
            "source_value": value,
            "required": True,
            "observed": bool(value),
            "report_only": True,
            "diagnostic_only": True,
        }
        for item, value in lineage.items()
    ]


def _model_limitations() -> str:
    return (
        "# Model Weight Versioning Limitations\n\n"
        "These are report-only research artifacts.\n\n"
        "They provide model weights/versioning/threshold/prediction phase 1 research context only.\n\n"
        "There is no stock_profile, no buy-review, no paper approval, no performance validation, and no trading.\n"
    )


def _model_overfit_warnings() -> list[dict[str, Any]]:
    return [
        {
            "warning_id": f"model_overfit_{index:03d}",
            "risk_item": risk,
            "applies_to_model_weight_versioning": True,
            "guard_required": True,
            "severity": "WARN",
            "notes": "Required report-only model overfit warning.",
        }
        for index, risk in enumerate(sorted(REQUIRED_OVERFIT_WARNINGS), start=1)
    ]


def _render_report(result: ModelWeightVersioningResult) -> str:
    return (
        "# Model Weights / Versioning / Threshold / Prediction Phase 1 Report\n\n"
        f"- model_workflow_run_id: {result.model_workflow_run_id}\n"
        f"- status: {result.status}\n"
        f"- workflow_stage: {result.workflow_stage}\n"
        f"- ready_for_model_weight_versioning: {result.ready_for_model_weight_versioning}\n"
        f"- model_weight_versioning_research_artifacts_created: {result.model_weight_versioning_research_artifacts_created}\n"
        f"- training_result_row_count: {result.training_result_row_count}\n"
        f"- metric_evidence_reference_count: {result.metric_evidence_reference_count}\n\n"
        "This workflow creates report-only research artifacts only. There is no stock_profile, no buy-review, "
        "no paper approval, no performance validation, and no trading.\n"
    )


def _recommended_next_task(result: ModelWeightVersioningResult) -> str:
    if result.status == MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED:
        return "Model Weights / Versioning / Threshold / Prediction Artifact Views Report-Only v0.1\n"
    if result.status == READY_FOR_MODEL_WEIGHT_VERSIONING:
        return "Rerun with --allow-model-weight-versioning only if report-only model research artifacts should be created.\n"
    return "Provide exact approval and complete upstream TRAINING_RESULT_CREATED lineage before model weight versioning.\n"


def _next_action(status: str) -> str:
    if status == MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED:
        return "Review report-only model artifacts before adding artifact views."
    if status == READY_FOR_MODEL_WEIGHT_VERSIONING:
        return "Rerun with explicit allow only if report-only model artifacts should be created."
    if status == NO_MODEL_WEIGHT_VERSIONING_INPUT:
        return "Provide exact approval and immutable TRAINING_RESULT_CREATED inputs."
    return "Resolve blocked model weight versioning gates before rerun."


def _has_any_input(settings: ModelWeightVersioningSettings) -> bool:
    return any(
        getattr(settings, field) is not None
        for field in ModelWeightVersioningSettings.__dataclass_fields__
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


def _source_run_id(metadata: dict[str, Any], key: str) -> str:
    return str(metadata.get(key, ""))


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
        return {"status": MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_ROWS_BLOCKED, "column": column, "reason": "training_result row id missing"}
    if column in {"report_only", "diagnostic_only"}:
        return {"status": MODEL_WEIGHT_VERSIONING_REPORT_ONLY_BLOCKED, "column": column, "reason": "report-only flag missing"}
    return {"status": MODEL_WEIGHT_VERSIONING_LINEAGE_BLOCKED, "column": column, "reason": "required lineage column missing"}


def _duplicate_unquarantined(frame: pd.DataFrame) -> bool:
    keys = ["replay_decision_id", "forward_return_label_id", "symbol", "replay_as_of_date", "split_role"]
    if not set(keys).issubset(frame.columns):
        return True
    duplicates = frame.duplicated(keys, keep=False)
    if not duplicates.any():
        return False
    quarantine = pd.to_numeric(frame.get("quarantine_count", 0), errors="coerce").fillna(0)
    return (quarantine[duplicates] <= 0).any()


def _forbidden_artifact_exists(settings: ModelWeightVersioningSettings) -> bool:
    parents = {
        Path(path).parent
        for field in ModelWeightVersioningSettings.__dataclass_fields__
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


def _blocked(status: str, group: str, name: str, reason: str) -> ModelWeightVersioningGateResult:
    return ModelWeightVersioningGateResult(group, name, status, False, reason)


def _passed_gate(group: str, name: str) -> ModelWeightVersioningGateResult:
    return ModelWeightVersioningGateResult(group, name, "PASS", True, "")


def _gate_frame(gates: list[ModelWeightVersioningGateResult], group: str) -> pd.DataFrame:
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
        raise ValueError("model weight versioning output must stay under outputs/reports/manual_diagnostics")


def _stable_id(settings: ModelWeightVersioningSettings) -> str:
    payload = {
        field: str(getattr(settings, field))
        for field in ModelWeightVersioningSettings.__dataclass_fields__
        if field != "write_artifacts"
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:12]
