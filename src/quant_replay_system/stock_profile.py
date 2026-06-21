"""Report-only stock profile phase 1 research-governed workflow."""

from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_STOCK_PROFILE_INPUT = "NO_STOCK_PROFILE_INPUT"
STOCK_PROFILE_INPUT_FOUND = "STOCK_PROFILE_INPUT_FOUND"
STOCK_PROFILE_APPROVAL_BLOCKED = "STOCK_PROFILE_APPROVAL_BLOCKED"
STOCK_PROFILE_ACTIVE_MODEL_INPUT_BLOCKED = "STOCK_PROFILE_ACTIVE_MODEL_INPUT_BLOCKED"
STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED = "STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED"
STOCK_PROFILE_TRAINING_RESULT_INPUT_BLOCKED = "STOCK_PROFILE_TRAINING_RESULT_INPUT_BLOCKED"
STOCK_PROFILE_TRAINING_RESULT_PLANNING_INPUT_BLOCKED = "STOCK_PROFILE_TRAINING_RESULT_PLANNING_INPUT_BLOCKED"
STOCK_PROFILE_METRIC_EXTENSION_INPUT_BLOCKED = "STOCK_PROFILE_METRIC_EXTENSION_INPUT_BLOCKED"
STOCK_PROFILE_METRIC_COMPUTATION_INPUT_BLOCKED = "STOCK_PROFILE_METRIC_COMPUTATION_INPUT_BLOCKED"
STOCK_PROFILE_METRIC_EVALUATION_INPUT_BLOCKED = "STOCK_PROFILE_METRIC_EVALUATION_INPUT_BLOCKED"
STOCK_PROFILE_TRAINING_EVALUATION_INPUT_BLOCKED = "STOCK_PROFILE_TRAINING_EVALUATION_INPUT_BLOCKED"
STOCK_PROFILE_FORWARD_LABEL_INPUT_BLOCKED = "STOCK_PROFILE_FORWARD_LABEL_INPUT_BLOCKED"
STOCK_PROFILE_REPLAY_FREEZE_INPUT_BLOCKED = "STOCK_PROFILE_REPLAY_FREEZE_INPUT_BLOCKED"
STOCK_PROFILE_HEALTH_BLOCKED = "STOCK_PROFILE_HEALTH_BLOCKED"
STOCK_PROFILE_LINEAGE_BLOCKED = "STOCK_PROFILE_LINEAGE_BLOCKED"
STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED = "STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED"
STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED = "STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED"
STOCK_PROFILE_TRAINING_RESULT_ROWS_BLOCKED = "STOCK_PROFILE_TRAINING_RESULT_ROWS_BLOCKED"
STOCK_PROFILE_METRIC_EVIDENCE_BLOCKED = "STOCK_PROFILE_METRIC_EVIDENCE_BLOCKED"
STOCK_PROFILE_LIMITATIONS_BLOCKED = "STOCK_PROFILE_LIMITATIONS_BLOCKED"
STOCK_PROFILE_OVERFIT_WARNING_BLOCKED = "STOCK_PROFILE_OVERFIT_WARNING_BLOCKED"
STOCK_PROFILE_SAFETY_FLAG_BLOCKED = "STOCK_PROFILE_SAFETY_FLAG_BLOCKED"
STOCK_PROFILE_FORBIDDEN_ARTIFACT_BLOCKED = "STOCK_PROFILE_FORBIDDEN_ARTIFACT_BLOCKED"
STOCK_PROFILE_LEAKAGE_BLOCKED = "STOCK_PROFILE_LEAKAGE_BLOCKED"
STOCK_PROFILE_SIDE_EFFECT_BLOCKED = "STOCK_PROFILE_SIDE_EFFECT_BLOCKED"
STOCK_PROFILE_OVERCLAIM_BLOCKED = "STOCK_PROFILE_OVERCLAIM_BLOCKED"
READY_FOR_STOCK_PROFILE_PHASE1 = "READY_FOR_STOCK_PROFILE_PHASE1"
STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED = "STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED"

ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED = "ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED"
MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED = "MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED"

EXACT_STOCK_PROFILE_APPROVAL_TEXT = (
    "I explicitly authorize only Stock Profile Implementation Phase 1, limited to report-only / "
    "research-governed stock_profile phase-1 artifacts. It may create stock_profile_metadata, "
    "stock_profile_input_index, stock_profile_lineage_matrix, stock_profile_factor_coverage_summary, "
    "stock_profile_symbol_coverage, stock_profile_market_regime_coverage, stock_profile_metric_summary, "
    "stock_profile_limitations, stock_profile_overfit_warnings, stock_profile_safety_flags, gate results, "
    "and recommended_next_task only when immutable ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED, "
    "MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED, TRAINING_RESULT_CREATED, "
    "TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED, METRIC_EXTENSION_REPORT_CREATED, "
    "METRIC_COMPUTATION_REPORT_CREATED, METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED, "
    "TRAINING_EVALUATION_DATASET_CREATED, FORWARD_RETURN_LABELS_CREATED, and REPLAY_DECISION_FROZEN "
    "artifacts have complete lineage and PASS health. This phase must not create real buy-review eligibility, "
    "paper approval, strategy performance validation, current-candidates integration, snapshots, "
    "signal_semantics mutation, promoted model, production model, active thresholds, advisory predictions, "
    "active probabilities, broker/order/message/API integration, or trading. If exact approval, upstream "
    "lineage, health, available_time, source_hash, revision_id, quality_status, report_only/diagnostic_only, "
    "research_governed, metric evidence, training_result rows, active-model artifacts, model-weight-versioning "
    "artifacts, limitations, overfit warnings, or safety flags are missing, it must fail closed."
)

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/stock_profile_v0_1")

ARTIFACT_FILES = {
    "stock_profile_metadata": "stock_profile_metadata.json",
    "stock_profile_input_index": "stock_profile_input_index.csv",
    "stock_profile_lineage_matrix": "stock_profile_lineage_matrix.csv",
    "stock_profile_factor_coverage_summary": "stock_profile_factor_coverage_summary.csv",
    "stock_profile_symbol_coverage": "stock_profile_symbol_coverage.csv",
    "stock_profile_market_regime_coverage": "stock_profile_market_regime_coverage.csv",
    "stock_profile_metric_summary": "stock_profile_metric_summary.csv",
    "stock_profile_limitations": "stock_profile_limitations.md",
    "stock_profile_overfit_warnings": "stock_profile_overfit_warnings.csv",
    "stock_profile_safety_flags": "stock_profile_safety_flags.json",
    "stock_profile_precondition_results": "stock_profile_precondition_results.csv",
    "stock_profile_approval_results": "stock_profile_approval_results.csv",
    "stock_profile_upstream_lineage_results": "stock_profile_upstream_lineage_results.csv",
    "stock_profile_active_model_input_results": "stock_profile_active_model_input_results.csv",
    "stock_profile_model_weight_versioning_input_results": "stock_profile_model_weight_versioning_input_results.csv",
    "stock_profile_training_result_input_results": "stock_profile_training_result_input_results.csv",
    "stock_profile_metric_evidence_results": "stock_profile_metric_evidence_results.csv",
    "stock_profile_leakage_guard_results": "stock_profile_leakage_guard_results.csv",
    "stock_profile_side_effect_guard_results": "stock_profile_side_effect_guard_results.csv",
    "stock_profile_overclaim_guard_results": "stock_profile_overclaim_guard_results.csv",
    "recommended_next_task": "recommended_next_task.md",
}

SUBSTANTIVE_ARTIFACT_KEYS = {
    "stock_profile_input_index",
    "stock_profile_lineage_matrix",
    "stock_profile_factor_coverage_summary",
    "stock_profile_symbol_coverage",
    "stock_profile_market_regime_coverage",
    "stock_profile_metric_summary",
    "stock_profile_limitations",
    "stock_profile_overfit_warnings",
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
    "research_governed",
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
    "stock-profile overfit",
    "benchmark mismatch",
    "industry classification drift",
    "survivorship bias",
    "lookahead leakage",
    "paper-overfit risk",
}

FACTOR_LAYERS = [
    "market_structure",
    "price_volume",
    "fundamental_quality",
    "growth_revision",
    "valuation",
    "risk_liquidity",
    "event_sentiment",
    "portfolio_context",
]

DOWNSTREAM_FALSE_FIELDS = [
    "active_stock_profile_created",
    "real_buy_review_eligible",
    "buy_review_allowed",
    "approved_for_paper",
    "strategy_performance_validated",
    "trading_allowed",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
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

REQUEST_OVERCLAIM_FIELDS = {
    "real_buy_review_requested",
    "buy_review_requested",
    "paper_approval_requested",
    "performance_validation_requested",
    "promoted_model_requested",
    "production_model_requested",
    "active_thresholds_requested",
    "advisory_predictions_requested",
    "active_probabilities_requested",
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
    "external_api_called",
}

REQUIRED_STOCK_PROFILE_OVERCLAIM_TRUE = {
    "stock_profile_research_governed_only",
    "stock_profile_not_active_stock_profile",
    "stock_profile_not_buy_review",
    "stock_profile_not_paper_approval",
    "stock_profile_not_performance_validation",
    "stock_profile_not_current_candidates",
    "stock_profile_not_snapshot",
    "stock_profile_not_signal_semantics",
    "stock_profile_not_promoted_model",
    "stock_profile_not_production_model",
    "stock_profile_not_active_thresholds",
    "stock_profile_not_advisory_predictions",
    "stock_profile_not_active_probabilities",
    "stock_profile_not_trading",
}

FORBIDDEN_ARTIFACT_PATTERNS = {
    "buy_review*",
    "paper_approval*",
    "approved_for_paper*",
    "performance_validation*",
    "strategy_performance*",
    "current_candidates*",
    "snapshot*",
    "signal_semantics*",
    "broker*",
    "order*",
    "trade*",
    "message*",
    "promoted_model*",
    "production_model*",
    "active_threshold*",
    "advisory_prediction*",
    "active_probability*",
    "scheduler*",
    "cron*",
    "serving*",
}


@dataclass(frozen=True)
class StockProfileSettings:
    approval_manifest_path: Path | None = None
    stock_profile_request_manifest_path: Path | None = None
    active_model_metadata_path: Path | None = None
    active_model_pointer_path: Path | None = None
    active_model_registry_entry_path: Path | None = None
    active_parameter_pointer_path: Path | None = None
    active_model_activation_status_path: Path | None = None
    active_model_input_index_path: Path | None = None
    active_model_lineage_matrix_path: Path | None = None
    active_model_limitations_path: Path | None = None
    active_model_overfit_warnings_path: Path | None = None
    active_model_safety_flags_path: Path | None = None
    active_model_status_artifact_path: Path | None = None
    active_model_health_artifact_path: Path | None = None
    model_weight_versioning_metadata_path: Path | None = None
    model_weights_reference_path: Path | None = None
    model_version_metadata_path: Path | None = None
    parameter_version_metadata_path: Path | None = None
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
    allow_stock_profile: bool = False
    write_artifacts: bool = True
    research_governed: bool = True
    diagnostic_output: bool = True


@dataclass(frozen=True)
class StockProfileGateResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str = ""
    observed_value: str = ""


StockProfileApprovalResult = StockProfileGateResult
StockProfileInputLineageResult = StockProfileGateResult
StockProfileActiveModelInputResult = StockProfileGateResult
StockProfileModelWeightVersioningInputResult = StockProfileGateResult
StockProfileTrainingResultInputResult = StockProfileGateResult
StockProfileMetricEvidenceResult = StockProfileGateResult
StockProfileLeakageGuardResult = StockProfileGateResult
StockProfileSideEffectGuardResult = StockProfileGateResult
StockProfileOverclaimResult = StockProfileGateResult


@dataclass(frozen=True)
class StockProfileResult:
    stock_profile_run_id: str
    status: str
    workflow_stage: str
    ready_for_stock_profile_phase1: bool
    stock_profile_phase1_executed: bool
    stock_profile_phase1_report_only_artifacts_created: bool
    artifact_path: str
    source_active_model_run_id: str = ""
    source_active_model_status: str = ""
    source_active_model_health_status: str = ""
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
    quarantined_training_result_row_count: int = 0
    metric_evidence_names_present: str = ""
    metric_evidence_reference_count: int = 0
    stock_profile_metadata_created: bool = False
    stock_profile_input_index_created: bool = False
    stock_profile_lineage_matrix_created: bool = False
    stock_profile_factor_coverage_summary_created: bool = False
    stock_profile_symbol_coverage_created: bool = False
    stock_profile_market_regime_coverage_created: bool = False
    stock_profile_metric_summary_created: bool = False
    stock_profile_limitations_created: bool = False
    stock_profile_overfit_warnings_created: bool = False
    stock_profile_safety_flags_created: bool = True
    blocker_count: int = 0
    warning_count: int = 0
    next_action: str = ""
    research_governed: bool = True
    diagnostic_output: bool = True
    artifact_paths: dict[str, Path] = field(default_factory=dict)
    gate_results: list[StockProfileGateResult] = field(default_factory=list)
    active_stock_profile_created: bool = False
    real_buy_review_eligible: bool = False
    buy_review_allowed: bool = False
    approved_for_paper: bool = False
    strategy_performance_validated: bool = False
    trading_allowed: bool = False
    current_candidates_run: bool = False
    snapshot_built: bool = False
    signal_semantics_changed: bool = False
    promoted_model_created: bool = False
    production_model_created: bool = False
    active_thresholds_created: bool = False
    advisory_predictions_created: bool = False
    active_probabilities_created: bool = False
    order_placed: bool = False
    broker_api_called: bool = False
    message_sent: bool = False
    llm_api_called: bool = False
    external_api_called: bool = False
    cache_mutated: bool = False
    data_raw_written: bool = False
    data_processed_written: bool = False
    data_cache_written: bool = False


def run_stock_profile(settings: StockProfileSettings | None = None) -> StockProfileResult:
    settings = settings or StockProfileSettings()
    output_root = Path(settings.output_dir)
    _assert_manual_diagnostics_output(output_root)
    run_id = _stable_id(settings)
    artifact_dir = output_root / run_id
    artifact_paths = {"artifact_dir": artifact_dir} | {
        key: artifact_dir / filename for key, filename in ARTIFACT_FILES.items()
    }
    state = _evaluate(settings)
    created = state["status"] == STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED
    ready = state["status"] in {READY_FOR_STOCK_PROFILE_PHASE1, STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED}
    active_meta = state.get("active_model_metadata", {})
    model_meta = state.get("model_weight_versioning_metadata", {})
    rows = state.get("training_result_rows", [])
    evidence_names = sorted(state.get("metric_evidence_names", []))

    result = StockProfileResult(
        stock_profile_run_id=run_id,
        status=state["status"],
        workflow_stage="STOCK_PROFILE_NO_INPUT" if state["status"] == NO_STOCK_PROFILE_INPUT else state["status"],
        ready_for_stock_profile_phase1=ready,
        stock_profile_phase1_executed=created,
        stock_profile_phase1_report_only_artifacts_created=created,
        artifact_path=str(artifact_dir),
        source_active_model_run_id=str(active_meta.get("active_model_run_id", "")),
        source_active_model_status=_source_status(active_meta),
        source_active_model_health_status=_status_value(settings.active_model_health_artifact_path),
        source_model_workflow_run_id=str(active_meta.get("source_model_workflow_run_id", "")),
        source_model_weight_versioning_status=str(active_meta.get("source_model_weight_versioning_status", _source_status(model_meta))),
        source_model_weight_versioning_health_status=str(active_meta.get("source_model_weight_versioning_health_status", _status_value(settings.model_weight_versioning_health_artifact_path))),
        model_weight_reference_id=str(active_meta.get("model_weight_reference_id", state.get("model_weights_reference", {}).get("weight_reference_id", ""))),
        model_version_id=str(active_meta.get("model_version_id", state.get("model_version_metadata", {}).get("model_version_id", ""))),
        parameter_version_id=str(active_meta.get("parameter_version_id", state.get("parameter_version_metadata", {}).get("parameter_version_id", ""))),
        source_training_result_run_id=str(active_meta.get("source_training_result_run_id", "")),
        source_training_result_status=str(active_meta.get("source_training_result_status", "")),
        source_training_result_health_status=str(active_meta.get("source_training_result_health_status", "")),
        source_training_result_planning_run_id=str(active_meta.get("source_training_result_planning_run_id", "")),
        source_training_result_planning_status=str(active_meta.get("source_training_result_planning_status", "")),
        source_training_result_planning_health_status=str(active_meta.get("source_training_result_planning_health_status", "")),
        source_metric_extension_run_id=str(active_meta.get("source_metric_extension_run_id", "")),
        source_metric_extension_status=str(active_meta.get("source_metric_extension_status", "")),
        source_metric_extension_health_status=str(active_meta.get("source_metric_extension_health_status", "")),
        source_metric_computation_run_id=str(active_meta.get("source_metric_computation_run_id", "")),
        source_metric_computation_status=str(active_meta.get("source_metric_computation_status", "")),
        source_metric_computation_health_status=str(active_meta.get("source_metric_computation_health_status", "")),
        source_metric_evaluation_planning_run_id=str(active_meta.get("source_metric_evaluation_planning_run_id", "")),
        source_metric_evaluation_status=str(active_meta.get("source_metric_evaluation_status", "")),
        source_metric_evaluation_health_status=str(active_meta.get("source_metric_evaluation_health_status", "")),
        source_training_evaluation_run_id=str(active_meta.get("source_training_evaluation_run_id", "")),
        source_training_evaluation_status=str(active_meta.get("source_training_evaluation_status", "")),
        source_training_evaluation_health_status=str(active_meta.get("source_training_evaluation_health_status", "")),
        source_forward_return_label_run_id=str(active_meta.get("source_forward_return_label_run_id", "")),
        source_forward_return_label_status=str(active_meta.get("source_forward_return_label_status", "")),
        source_forward_return_label_health_status=str(active_meta.get("source_forward_return_label_health_status", "")),
        source_replay_decision_freeze_run_id=str(active_meta.get("source_replay_decision_freeze_run_id", "")),
        source_replay_decision_freeze_status=str(active_meta.get("source_replay_decision_freeze_status", "")),
        source_replay_decision_freeze_health_status=str(active_meta.get("source_replay_decision_freeze_health_status", "")),
        training_result_row_count=len(rows),
        eligible_training_result_row_count=len(rows),
        quarantined_training_result_row_count=_quarantine_count(rows),
        metric_evidence_names_present=",".join(evidence_names),
        metric_evidence_reference_count=len(evidence_names),
        stock_profile_metadata_created=created,
        stock_profile_input_index_created=created,
        stock_profile_lineage_matrix_created=created,
        stock_profile_factor_coverage_summary_created=created,
        stock_profile_symbol_coverage_created=created,
        stock_profile_market_regime_coverage_created=created,
        stock_profile_metric_summary_created=created,
        stock_profile_limitations_created=created,
        stock_profile_overfit_warnings_created=created,
        stock_profile_safety_flags_created=True,
        blocker_count=0 if ready else len(state.get("gate_results", [])),
        next_action=_next_action(state["status"]),
        research_governed=settings.research_governed,
        diagnostic_output=settings.diagnostic_output,
        artifact_paths=artifact_paths,
        gate_results=state.get("gate_results", []),
    )
    if settings.write_artifacts:
        write_stock_profile_artifacts(result, state)
    return result


def write_stock_profile_artifacts(result: StockProfileResult, state: dict[str, Any]) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_json(result.artifact_paths["stock_profile_metadata"], _metadata(result))
    _write_json(result.artifact_paths["stock_profile_safety_flags"], _safety_flags(result))
    result.artifact_paths["recommended_next_task"].write_text(_recommended_next_task(result), encoding="utf-8")
    for group, key in [
        ("precondition", "stock_profile_precondition_results"),
        ("approval", "stock_profile_approval_results"),
        ("upstream_lineage", "stock_profile_upstream_lineage_results"),
        ("active_model_input", "stock_profile_active_model_input_results"),
        ("model_weight_versioning_input", "stock_profile_model_weight_versioning_input_results"),
        ("training_result_input", "stock_profile_training_result_input_results"),
        ("metric_evidence", "stock_profile_metric_evidence_results"),
        ("leakage", "stock_profile_leakage_guard_results"),
        ("side_effect", "stock_profile_side_effect_guard_results"),
        ("overclaim", "stock_profile_overclaim_guard_results"),
    ]:
        _write_csv(result.artifact_paths[key], _gate_frame(result.gate_results, group))
    if not result.stock_profile_phase1_report_only_artifacts_created:
        return

    rows = state.get("training_result_rows", [])
    _write_csv(result.artifact_paths["stock_profile_input_index"], pd.DataFrame(_stock_profile_input_index(result)))
    _write_csv(result.artifact_paths["stock_profile_lineage_matrix"], pd.DataFrame(_stock_profile_lineage_matrix(result, rows)))
    _write_csv(result.artifact_paths["stock_profile_factor_coverage_summary"], pd.DataFrame(_stock_profile_factor_coverage_summary(result, rows)))
    _write_csv(result.artifact_paths["stock_profile_symbol_coverage"], pd.DataFrame(_stock_profile_symbol_coverage(result, rows)))
    _write_csv(result.artifact_paths["stock_profile_market_regime_coverage"], pd.DataFrame(_stock_profile_market_regime_coverage(result, rows)))
    _write_csv(result.artifact_paths["stock_profile_metric_summary"], pd.DataFrame(_stock_profile_metric_summary(result, rows)))
    result.artifact_paths["stock_profile_limitations"].write_text(_stock_profile_limitations(), encoding="utf-8")
    _write_csv(result.artifact_paths["stock_profile_overfit_warnings"], pd.DataFrame(_stock_profile_overfit_warnings()))


def _evaluate(settings: StockProfileSettings) -> dict[str, Any]:
    if not _has_any_input(settings):
        return _state(NO_STOCK_PROFILE_INPUT)
    if not settings.approval_manifest_path or not Path(settings.approval_manifest_path).exists():
        return _state(STOCK_PROFILE_APPROVAL_BLOCKED, "approval", "approval_manifest", "exact stock profile approval missing")
    approval = _load_json(settings.approval_manifest_path)
    if not _valid_exact_approval(str(approval.get("approval_text", ""))):
        return _state(STOCK_PROFILE_APPROVAL_BLOCKED, "approval", "approval_text", "exact stock profile approval text missing or invalid")

    request = _load_json(settings.stock_profile_request_manifest_path)
    if _any_truthy(request, REQUEST_OVERCLAIM_FIELDS):
        return _state(STOCK_PROFILE_OVERCLAIM_BLOCKED, "overclaim", "request_scope", "unsafe stock profile downstream scope requested")
    if _any_truthy(request, REQUEST_LEAKAGE_FIELDS):
        return _state(STOCK_PROFILE_LEAKAGE_BLOCKED, "leakage", "request_scope", "unsafe integration or leakage path requested")
    if _any_truthy(request, REQUEST_SIDE_EFFECT_FIELDS):
        return _state(STOCK_PROFILE_SIDE_EFFECT_BLOCKED, "side_effect", "request_scope", "unsafe side effect requested")

    missing = _first_missing_required_path(settings)
    if missing:
        field, status = missing
        return _state(status, _group_for_status(status), field, "required input artifact missing")
    if _forbidden_artifact_exists(settings):
        return _state(STOCK_PROFILE_FORBIDDEN_ARTIFACT_BLOCKED, "precondition", "forbidden_artifacts", "forbidden downstream artifact present")

    active_meta = _load_json(settings.active_model_metadata_path)
    model_meta = _load_json(settings.model_weight_versioning_metadata_path)
    if _source_status(active_meta) != ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED:
        return _state(STOCK_PROFILE_ACTIVE_MODEL_INPUT_BLOCKED, "active_model_input", "active_model_metadata", "active model source is not research-governed created", active_meta, model_meta)
    if _status_value(settings.active_model_status_artifact_path) != ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED:
        return _state(STOCK_PROFILE_ACTIVE_MODEL_INPUT_BLOCKED, "active_model_input", "active_model_status", "active model status mismatch", active_meta, model_meta)
    if _status_value(settings.active_model_health_artifact_path) != "PASS":
        return _state(STOCK_PROFILE_HEALTH_BLOCKED, "active_model_input", "active_model_health", "active model health is not PASS", active_meta, model_meta)
    if not _active_model_artifacts_safe(settings, active_meta):
        return _state(STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED, "active_model_input", "active_model_artifacts", "active model artifacts are unsafe or incomplete", active_meta, model_meta)

    if _source_status(model_meta) != MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED:
        return _state(STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED, "model_weight_versioning_input", "model_weight_versioning_metadata", "model weight versioning source is not created", active_meta, model_meta)
    if _status_value(settings.model_weight_versioning_status_artifact_path) != MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED:
        return _state(STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED, "model_weight_versioning_input", "model_weight_versioning_status", "model weight versioning status mismatch", active_meta, model_meta)
    if _status_value(settings.model_weight_versioning_health_artifact_path) != "PASS":
        return _state(STOCK_PROFILE_HEALTH_BLOCKED, "model_weight_versioning_input", "model_weight_versioning_health", "model weight versioning health is not PASS", active_meta, model_meta)

    model_weights = _load_json(settings.model_weights_reference_path)
    model_version = _load_json(settings.model_version_metadata_path)
    parameter_version = _load_json(settings.parameter_version_metadata_path)
    if not model_weights.get("weight_reference_id") or not model_version.get("model_version_id") or not parameter_version.get("parameter_version_id"):
        return _state(STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED, "model_weight_versioning_input", "model_reference_ids", "model reference ids missing", active_meta, model_meta)
    if _truthy(model_version.get("promoted_model")) or _truthy(model_version.get("production_model")):
        return _state(STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED, "model_weight_versioning_input", "model_version_metadata", "model version is promoted/production", active_meta, model_meta)
    if _truthy(parameter_version.get("active_parameters")):
        return _state(STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED, "model_weight_versioning_input", "parameter_version_metadata", "parameter version is already active", active_meta, model_meta)
    if not _model_weight_versioning_artifacts_safe(settings):
        return _state(STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED, "model_weight_versioning_input", "model_artifacts", "model weight versioning artifacts are unsafe or incomplete", active_meta, model_meta)

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
            return _state(STOCK_PROFILE_HEALTH_BLOCKED, "upstream_lineage", health_field, "upstream health is not PASS", active_meta, model_meta)

    status_blocker = _source_status_blocker(settings, model_meta)
    if status_blocker:
        name, expected, status = status_blocker
        return _state(status, "upstream_lineage", name, f"expected status {expected}", active_meta, model_meta)

    training_rows_frame = _load_csv(settings.training_result_rows_path)
    if training_rows_frame.empty:
        return _state(STOCK_PROFILE_TRAINING_RESULT_ROWS_BLOCKED, "training_result_input", "training_result_rows", "training_result rows missing", active_meta, model_meta)
    column_blocker = _required_column_blocker(training_rows_frame, LINEAGE_COLUMNS)
    if column_blocker:
        return _state(column_blocker["status"], "upstream_lineage", column_blocker["column"], column_blocker["reason"], active_meta, model_meta)
    if not _all_true(training_rows_frame, "report_only") or not _all_true(training_rows_frame, "diagnostic_only") or not _all_true(training_rows_frame, "research_governed"):
        return _state(STOCK_PROFILE_LINEAGE_BLOCKED, "upstream_lineage", "report_only", "report_only/diagnostic_only/research_governed flags missing", active_meta, model_meta)

    active_lineage = _load_csv(settings.active_model_lineage_matrix_path)
    model_lineage = _load_csv(settings.model_lineage_matrix_path)
    if "lineage_item" not in active_lineage.columns or "lineage_item" not in model_lineage.columns:
        return _state(STOCK_PROFILE_LINEAGE_BLOCKED, "upstream_lineage", "lineage_matrix", "lineage matrix missing lineage_item", active_meta, model_meta)

    sample_rows = _load_csv(settings.training_evaluation_sample_rows_path)
    if _duplicate_unquarantined(sample_rows):
        return _state(STOCK_PROFILE_LINEAGE_BLOCKED, "upstream_lineage", "duplicate_samples", "duplicate sample rows not quarantined", active_meta, model_meta)

    metric_names = _metric_names_present(model_meta, settings)
    if REQUIRED_METRICS - metric_names:
        return _state(STOCK_PROFILE_METRIC_EVIDENCE_BLOCKED, "metric_evidence", "metric_evidence", "required metric evidence missing", active_meta, model_meta)
    if _metric_names_overclaim(model_meta):
        return _state(STOCK_PROFILE_OVERCLAIM_BLOCKED, "overclaim", "metric_evidence", "metric evidence overclaims performance validation", active_meta, model_meta)

    if any(phrase not in _load_text(settings.active_model_limitations_path).lower() for phrase in _active_model_limitation_phrases()):
        return _state(STOCK_PROFILE_LIMITATIONS_BLOCKED, "overclaim", "active_model_limitations", "active model limitation wording missing", active_meta, model_meta)
    model_limitations = _load_text(settings.model_limitations_path).lower()
    if not _model_limitations_safe(model_limitations):
        return _state(STOCK_PROFILE_LIMITATIONS_BLOCKED, "overclaim", "model_limitations", "model limitation wording missing", active_meta, model_meta)

    active_warnings = _load_csv(settings.active_model_overfit_warnings_path)
    model_warnings = _load_csv(settings.model_overfit_warnings_path)
    if _required_warning_subset() - set(active_warnings.get("risk_item", pd.Series(dtype=str)).astype(str)):
        return _state(STOCK_PROFILE_OVERFIT_WARNING_BLOCKED, "overclaim", "active_model_overfit_warnings", "active model overfit warning missing", active_meta, model_meta)
    if (_required_warning_subset() - {"stock-profile overfit", "prediction overfit"}) - set(model_warnings.get("risk_item", pd.Series(dtype=str)).astype(str)):
        return _state(STOCK_PROFILE_OVERFIT_WARNING_BLOCKED, "overclaim", "model_overfit_warnings", "model overfit warning missing", active_meta, model_meta)

    active_safety = _load_json(settings.active_model_safety_flags_path)
    model_safety = _load_json(settings.model_safety_flags_path)
    if not _truthy(active_safety.get("active_model_artifacts_created")):
        return _state(STOCK_PROFILE_SAFETY_FLAG_BLOCKED, "active_model_input", "active_model_safety_flags", "active model safety flags do not confirm artifacts", active_meta, model_meta)
    if not _truthy(model_safety.get("model_weight_versioning_research_artifacts_created")):
        return _state(STOCK_PROFILE_SAFETY_FLAG_BLOCKED, "model_weight_versioning_input", "model_safety_flags", "model safety flags do not confirm research artifacts", active_meta, model_meta)
    for payload_name, payload in [("active_model_safety_flags", active_safety), ("model_safety_flags", model_safety)]:
        for field in _unsafe_safety_fields():
            if _truthy(payload.get(field)):
                return _state(STOCK_PROFILE_SAFETY_FLAG_BLOCKED, "precondition", f"{payload_name}.{field}", "unsafe upstream safety flag true", active_meta, model_meta)

    leakage = _load_json(settings.leakage_evidence_bundle_path)
    if any(_truthy(value) for value in leakage.values()):
        return _state(STOCK_PROFILE_LEAKAGE_BLOCKED, "leakage", "leakage_bundle", "leakage guard failed", active_meta, model_meta)
    side_effect = _load_json(settings.side_effect_evidence_bundle_path)
    if any(_truthy(side_effect.get(field)) for field in DOWNSTREAM_FALSE_FIELDS):
        return _state(STOCK_PROFILE_SIDE_EFFECT_BLOCKED, "side_effect", "side_effect_bundle", "side effect guard failed", active_meta, model_meta)
    overclaim = _load_json(settings.overclaim_evidence_bundle_path)
    if not all(_truthy(overclaim.get(field)) for field in REQUIRED_STOCK_PROFILE_OVERCLAIM_TRUE):
        return _state(STOCK_PROFILE_OVERCLAIM_BLOCKED, "overclaim", "overclaim_bundle", "overclaim guard failed", active_meta, model_meta)

    status = STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED if settings.allow_stock_profile else READY_FOR_STOCK_PROFILE_PHASE1
    return {
        "status": status,
        "gate_results": [_passed_gate("precondition", "all_required_inputs")],
        "active_model_metadata": active_meta,
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
    active_model_metadata: dict[str, Any] | None = None,
    model_weight_versioning_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "gate_results": [] if status == NO_STOCK_PROFILE_INPUT else [_blocked(status, group, name, reason)],
        "active_model_metadata": active_model_metadata or {},
        "model_weight_versioning_metadata": model_weight_versioning_metadata or {},
        "model_weights_reference": {},
        "model_version_metadata": {},
        "parameter_version_metadata": {},
        "training_result_rows": [],
        "metric_evidence_names": set(),
    }


def _first_missing_required_path(settings: StockProfileSettings) -> tuple[str, str] | None:
    groups = [
        ("active_model_metadata_path", STOCK_PROFILE_ACTIVE_MODEL_INPUT_BLOCKED),
        ("active_model_pointer_path", STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED),
        ("active_model_registry_entry_path", STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED),
        ("active_parameter_pointer_path", STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED),
        ("active_model_activation_status_path", STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED),
        ("active_model_input_index_path", STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED),
        ("active_model_lineage_matrix_path", STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED),
        ("active_model_limitations_path", STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED),
        ("active_model_overfit_warnings_path", STOCK_PROFILE_OVERFIT_WARNING_BLOCKED),
        ("active_model_safety_flags_path", STOCK_PROFILE_SAFETY_FLAG_BLOCKED),
        ("active_model_status_artifact_path", STOCK_PROFILE_ACTIVE_MODEL_INPUT_BLOCKED),
        ("active_model_health_artifact_path", STOCK_PROFILE_HEALTH_BLOCKED),
        ("model_weight_versioning_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("model_weights_reference_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_version_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("parameter_version_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_input_index_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_lineage_matrix_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_limitations_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_overfit_warnings_path", STOCK_PROFILE_OVERFIT_WARNING_BLOCKED),
        ("model_safety_flags_path", STOCK_PROFILE_SAFETY_FLAG_BLOCKED),
        ("model_weight_versioning_status_artifact_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("model_weight_versioning_health_artifact_path", STOCK_PROFILE_HEALTH_BLOCKED),
        ("training_result_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("training_result_rows_path", STOCK_PROFILE_TRAINING_RESULT_ROWS_BLOCKED),
        ("training_result_status_artifact_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("training_result_health_artifact_path", STOCK_PROFILE_HEALTH_BLOCKED),
        ("training_result_planning_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("training_result_planning_health_artifact_path", STOCK_PROFILE_HEALTH_BLOCKED),
        ("metric_extension_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("metric_extension_result_rows_path", STOCK_PROFILE_METRIC_EVIDENCE_BLOCKED),
        ("metric_extension_health_artifact_path", STOCK_PROFILE_HEALTH_BLOCKED),
        ("metric_computation_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("metric_computation_result_rows_path", STOCK_PROFILE_METRIC_EVIDENCE_BLOCKED),
        ("metric_computation_health_artifact_path", STOCK_PROFILE_HEALTH_BLOCKED),
        ("metric_evaluation_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("metric_evaluation_health_artifact_path", STOCK_PROFILE_HEALTH_BLOCKED),
        ("training_evaluation_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("training_evaluation_sample_rows_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("training_evaluation_health_artifact_path", STOCK_PROFILE_HEALTH_BLOCKED),
        ("forward_return_label_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("forward_return_label_rows_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("forward_return_label_health_artifact_path", STOCK_PROFILE_HEALTH_BLOCKED),
        ("replay_decision_freeze_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("replay_decision_freeze_rows_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("replay_decision_freeze_health_artifact_path", STOCK_PROFILE_HEALTH_BLOCKED),
        ("leakage_evidence_bundle_path", STOCK_PROFILE_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", STOCK_PROFILE_OVERCLAIM_BLOCKED),
        ("side_effect_evidence_bundle_path", STOCK_PROFILE_SIDE_EFFECT_BLOCKED),
    ]
    for field, status in groups:
        path = getattr(settings, field)
        if path is None or not Path(path).exists():
            return field, status
    return None


def _source_status_blocker(settings: StockProfileSettings, model_meta: dict[str, Any]) -> tuple[str, str, str] | None:
    expectations = {
        "source_training_result_status": ("TRAINING_RESULT_CREATED", STOCK_PROFILE_TRAINING_RESULT_INPUT_BLOCKED),
        "source_training_result_planning_status": ("TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED", STOCK_PROFILE_TRAINING_RESULT_PLANNING_INPUT_BLOCKED),
        "source_metric_extension_status": ("METRIC_EXTENSION_REPORT_CREATED", STOCK_PROFILE_METRIC_EXTENSION_INPUT_BLOCKED),
        "source_metric_computation_status": ("METRIC_COMPUTATION_REPORT_CREATED", STOCK_PROFILE_METRIC_COMPUTATION_INPUT_BLOCKED),
        "source_metric_evaluation_status": ("METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED", STOCK_PROFILE_METRIC_EVALUATION_INPUT_BLOCKED),
        "source_training_evaluation_status": ("TRAINING_EVALUATION_DATASET_CREATED", STOCK_PROFILE_TRAINING_EVALUATION_INPUT_BLOCKED),
        "source_forward_return_label_status": ("FORWARD_RETURN_LABELS_CREATED", STOCK_PROFILE_FORWARD_LABEL_INPUT_BLOCKED),
        "source_replay_decision_freeze_status": ("REPLAY_DECISION_FROZEN", STOCK_PROFILE_REPLAY_FREEZE_INPUT_BLOCKED),
    }
    for key, (expected, status) in expectations.items():
        if str(model_meta.get(key, "")) != expected:
            return key, expected, status
    meta_paths = {
        "training_result_metadata_path": ("TRAINING_RESULT_CREATED", STOCK_PROFILE_TRAINING_RESULT_INPUT_BLOCKED),
        "training_result_planning_metadata_path": ("TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED", STOCK_PROFILE_TRAINING_RESULT_PLANNING_INPUT_BLOCKED),
        "metric_extension_metadata_path": ("METRIC_EXTENSION_REPORT_CREATED", STOCK_PROFILE_METRIC_EXTENSION_INPUT_BLOCKED),
        "metric_computation_metadata_path": ("METRIC_COMPUTATION_REPORT_CREATED", STOCK_PROFILE_METRIC_COMPUTATION_INPUT_BLOCKED),
        "metric_evaluation_metadata_path": ("METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED", STOCK_PROFILE_METRIC_EVALUATION_INPUT_BLOCKED),
        "training_evaluation_metadata_path": ("TRAINING_EVALUATION_DATASET_CREATED", STOCK_PROFILE_TRAINING_EVALUATION_INPUT_BLOCKED),
        "forward_return_label_metadata_path": ("FORWARD_RETURN_LABELS_CREATED", STOCK_PROFILE_FORWARD_LABEL_INPUT_BLOCKED),
        "replay_decision_freeze_metadata_path": ("REPLAY_DECISION_FROZEN", STOCK_PROFILE_REPLAY_FREEZE_INPUT_BLOCKED),
    }
    for field, (expected, status) in meta_paths.items():
        if _source_status(_load_json(getattr(settings, field))) != expected:
            return field, expected, status
    return None


def _active_model_artifacts_safe(settings: StockProfileSettings, active_meta: dict[str, Any]) -> bool:
    if not _truthy(active_meta.get("active_model_artifacts_created")):
        return False
    pointer = _load_json(settings.active_model_pointer_path)
    registry = _load_json(settings.active_model_registry_entry_path)
    parameter = _load_json(settings.active_parameter_pointer_path)
    activation = _load_json(settings.active_model_activation_status_path)
    if pointer.get("pointer_role") != "research_governed_active_model":
        return False
    if _truthy(pointer.get("serving_enabled")) or _truthy(pointer.get("current_candidates_integration")):
        return False
    if _truthy(pointer.get("snapshot_integration")) or _truthy(pointer.get("signal_semantics_mutated")):
        return False
    if _truthy(registry.get("promoted_model")) or _truthy(registry.get("production_model")):
        return False
    if _truthy(registry.get("serving_enabled")) or _truthy(registry.get("trading_enabled")):
        return False
    if _truthy(parameter.get("active_thresholds_created")) or _truthy(parameter.get("signal_semantics_mutated")):
        return False
    if any(_truthy(activation.get(field)) for field in DOWNSTREAM_FALSE_FIELDS):
        return False
    input_index = _load_csv(settings.active_model_input_index_path)
    if {"source_run_id", "health_status"} - set(input_index.columns):
        return False
    return True


def _model_weight_versioning_artifacts_safe(settings: StockProfileSettings) -> bool:
    model_input = _load_csv(settings.model_input_index_path)
    if {"source_run_id", "health_status"} - set(model_input.columns):
        return False
    feature_importance = _load_csv(settings.model_overfit_warnings_path)
    return not feature_importance.empty


def _metadata(result: StockProfileResult) -> dict[str, Any]:
    payload = {
        "stock_profile_run_id": result.stock_profile_run_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "execution_status": result.status,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "ready_for_stock_profile_phase1": result.ready_for_stock_profile_phase1,
        "stock_profile_phase1_executed": result.stock_profile_phase1_executed,
        "stock_profile_phase1_report_only_artifacts_created": result.stock_profile_phase1_report_only_artifacts_created,
        "training_result_row_count": result.training_result_row_count,
        "eligible_training_result_row_count": result.eligible_training_result_row_count,
        "quarantined_training_result_row_count": result.quarantined_training_result_row_count,
        "metric_evidence_names_present": result.metric_evidence_names_present,
        "metric_evidence_reference_count": result.metric_evidence_reference_count,
        "artifact_path": result.artifact_path,
        "research_governed": result.research_governed,
        "diagnostic_output": result.diagnostic_output,
    }
    for field in [
        "source_active_model_run_id",
        "source_active_model_status",
        "source_active_model_health_status",
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
        "stock_profile_metadata_created",
        "stock_profile_input_index_created",
        "stock_profile_lineage_matrix_created",
        "stock_profile_factor_coverage_summary_created",
        "stock_profile_symbol_coverage_created",
        "stock_profile_market_regime_coverage_created",
        "stock_profile_metric_summary_created",
        "stock_profile_limitations_created",
        "stock_profile_overfit_warnings_created",
        "stock_profile_safety_flags_created",
    ]:
        payload[field] = getattr(result, field)
    return payload | _safety_flags(result)


def _safety_flags(result: StockProfileResult) -> dict[str, Any]:
    return {
        "stock_profile_phase1_report_only_artifacts_created": result.stock_profile_phase1_report_only_artifacts_created,
        "stock_profile_metadata_created": result.stock_profile_metadata_created,
        "stock_profile_input_index_created": result.stock_profile_input_index_created,
        "stock_profile_lineage_matrix_created": result.stock_profile_lineage_matrix_created,
        "stock_profile_factor_coverage_summary_created": result.stock_profile_factor_coverage_summary_created,
        "stock_profile_symbol_coverage_created": result.stock_profile_symbol_coverage_created,
        "stock_profile_market_regime_coverage_created": result.stock_profile_market_regime_coverage_created,
        "stock_profile_metric_summary_created": result.stock_profile_metric_summary_created,
        "stock_profile_limitations_created": result.stock_profile_limitations_created,
        "stock_profile_overfit_warnings_created": result.stock_profile_overfit_warnings_created,
        "stock_profile_safety_flags_created": result.stock_profile_safety_flags_created,
        **{field: getattr(result, field) for field in DOWNSTREAM_FALSE_FIELDS},
        "report_only": True,
        "research_governed": result.research_governed,
        "diagnostic_output": result.diagnostic_output,
    }


def _stock_profile_input_index(result: StockProfileResult) -> list[dict[str, Any]]:
    rows = [
        ("active_model", result.source_active_model_run_id, result.source_active_model_status, result.source_active_model_health_status),
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
            "stock_profile_run_id": result.stock_profile_run_id,
            "input_component": component,
            "source_run_id": run_id,
            "source_status": status,
            "health_status": health,
            "required_for_stock_profile_phase1": True,
            "immutable_required": True,
            "research_governed": True,
            "diagnostic_output": True,
        }
        for component, run_id, status, health in rows
    ]


def _stock_profile_lineage_matrix(result: StockProfileResult, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    row = rows[0] if rows else {}
    metric_names = result.metric_evidence_names_present.split(",") if result.metric_evidence_names_present else [""]
    lineage = {
        "stock_profile_run_id": result.stock_profile_run_id,
        "active_model_run_id": result.source_active_model_run_id,
        "model_workflow_run_id": result.source_model_workflow_run_id,
        "model_weight_reference_id": result.model_weight_reference_id,
        "model_version_id": result.model_version_id,
        "parameter_version_id": result.parameter_version_id,
        "training_result_run_id": result.source_training_result_run_id,
        "training_result_row_id": row.get("training_result_row_id", ""),
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
        "instrument_type": row.get("instrument_type", ""),
        "replay_as_of_date": row.get("replay_as_of_date", ""),
        "split_role": row.get("split_role", ""),
        "label_name": row.get("label_name", ""),
        "horizon_trading_days": row.get("horizon_trading_days", ""),
        "benchmark_id": row.get("benchmark_id", ""),
        "benchmark_name": row.get("benchmark_name", ""),
        "industry_id": row.get("industry_id", ""),
        "industry_name": row.get("industry_name", ""),
        "market_regime_id": row.get("market_regime_id", ""),
        "factor_layer": row.get("factor_layer", FACTOR_LAYERS[0]),
        "factor_id": row.get("factor_id", ""),
        "factor_name": row.get("factor_name", ""),
        "metric_name": metric_names[0],
        "metric_value": row.get("metric_value", ""),
        "numerator_count": row.get("numerator_count", ""),
        "denominator_count": row.get("denominator_count", ""),
        "source_hash": row.get("source_hash", ""),
        "revision_id": row.get("revision_id", ""),
        "available_time": row.get("available_time", ""),
        "quality_status": row.get("quality_status", ""),
        "report_only": row.get("report_only", ""),
        "diagnostic_only": row.get("diagnostic_only", ""),
        "research_governed": row.get("research_governed", ""),
    }
    return [
        {
            "stock_profile_run_id": result.stock_profile_run_id,
            "lineage_item": item,
            "source_value": value,
            "required": True,
            "observed": bool(value),
            "research_governed": True,
            "diagnostic_output": True,
        }
        for item, value in lineage.items()
    ]


def _stock_profile_factor_coverage_summary(result: StockProfileResult, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    observed = {str(row.get("factor_layer", "")) for row in rows if row.get("factor_layer")}
    return [
        {
            "stock_profile_run_id": result.stock_profile_run_id,
            "factor_layer": layer,
            "observed_in_training_result_rows": layer in observed,
            "coverage_role": "8-layer taxonomy skeleton",
            "notes": "Expandable coverage; not fixed 12-factor final coverage; not alpha proof.",
        }
        for layer in FACTOR_LAYERS
    ]


def _stock_profile_symbol_coverage(result: StockProfileResult, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], int] = {}
    for row in rows:
        key = (str(row.get("symbol", "")), str(row.get("instrument_type", "")))
        grouped[key] = grouped.get(key, 0) + 1
    return [
        {
            "stock_profile_run_id": result.stock_profile_run_id,
            "symbol": symbol,
            "instrument_type": instrument_type,
            "training_result_row_count": count,
            "real_buy_review_eligible": False,
            "buy_review_allowed": False,
            "notes": "Symbol coverage only; no real buy-review eligibility.",
        }
        for (symbol, instrument_type), count in sorted(grouped.items())
    ]


def _stock_profile_market_regime_coverage(result: StockProfileResult, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, int] = {}
    for row in rows:
        key = str(row.get("market_regime_id", "UNSPECIFIED") or "UNSPECIFIED")
        grouped[key] = grouped.get(key, 0) + 1
    return [
        {
            "stock_profile_run_id": result.stock_profile_run_id,
            "market_regime_id": regime,
            "training_result_row_count": count,
            "interpretation": "regime coverage context only; no regime robustness claim",
        }
        for regime, count in sorted(grouped.items())
    ]


def _stock_profile_metric_summary(result: StockProfileResult, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    row = rows[0] if rows else {}
    return [
        {
            "stock_profile_run_id": result.stock_profile_run_id,
            "metric_name": metric,
            "metric_value": row.get(metric, row.get("metric_value", "")),
            "source": "approved upstream metric evidence reference",
            "interpretation": "descriptive evidence only; not profitability proof; not strategy validation",
        }
        for metric in sorted(REQUIRED_METRICS)
    ]


def _stock_profile_limitations() -> str:
    return (
        "# Stock Profile Phase 1 Limitations\n\n"
        "Stock profile phase 1 is report-only and research-governed.\n\n"
        "- stock_profile is a validation profile draft, not trading instruction\n"
        "- no real buy-review eligibility\n"
        "- no paper approval\n"
        "- no strategy performance validation\n"
        "- no current-candidates integration\n"
        "- no snapshot integration\n"
        "- no signal_semantics mutation\n"
        "- no broker/order/message/API/trading\n"
        "- no promoted model\n"
        "- no production model\n"
        "- no active thresholds\n"
        "- no advisory predictions\n"
        "- no active probabilities\n"
        "- metrics are evidence only, not profitability proof\n"
        "- PIT lineage and source governance remain required\n"
        "- paper validation remains future separate workflow\n"
    )


def _stock_profile_overfit_warnings() -> list[dict[str, Any]]:
    return [
        {
            "warning_id": f"stock_profile_overfit_{index:03d}",
            "risk_item": risk,
            "applies_to_stock_profile_phase1": True,
            "guard_required": True,
            "severity": "WARN",
            "notes": "Required stock profile phase 1 report-only overfit warning.",
        }
        for index, risk in enumerate(sorted(REQUIRED_OVERFIT_WARNINGS), start=1)
    ]


def _recommended_next_task(result: StockProfileResult) -> str:
    if result.status == STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED:
        return "Stock Profile Artifact Views Report-Only v0.1\n"
    if result.status == READY_FOR_STOCK_PROFILE_PHASE1:
        return "Rerun with --allow-stock-profile only if report-only stock_profile phase-1 artifacts should be created.\n"
    return "Provide exact approval and complete upstream PASS-health active-model/model/training/metric/replay lineage before stock profile phase 1.\n"


def _next_action(status: str) -> str:
    if status == STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED:
        return "Review stock profile phase-1 artifacts before adding artifact views."
    if status == READY_FOR_STOCK_PROFILE_PHASE1:
        return "Rerun with explicit allow only if report-only stock_profile phase-1 artifacts should be created."
    if status == NO_STOCK_PROFILE_INPUT:
        return "Provide exact stock profile approval and complete upstream inputs."
    return "Resolve blocked stock profile gates before rerun."


def _valid_exact_approval(text: str) -> bool:
    stripped = text.strip()
    if stripped == EXACT_STOCK_PROFILE_APPROVAL_TEXT:
        return True
    lowered = stripped.lower()
    required_phrases = [
        "explicitly authorize only stock profile implementation phase 1",
        "report-only",
        "research-governed",
        "active_model_research_governed_artifacts_created",
        "model_weight_versioning_research_artifacts_created",
        "training_result_created",
        "replay_decision_frozen",
        "must not create real buy-review eligibility",
        "paper approval",
        "strategy performance validation",
        "current-candidates",
        "snapshot",
        "signal_semantics",
        "promoted model",
        "production model",
        "active thresholds",
        "advisory predictions",
        "active probabilities",
        "trading",
        "fail closed",
    ]
    return all(phrase in lowered for phrase in required_phrases)


def _has_any_input(settings: StockProfileSettings) -> bool:
    return any(
        getattr(settings, field) is not None
        for field in StockProfileSettings.__dataclass_fields__
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
            "status": STOCK_PROFILE_TRAINING_RESULT_ROWS_BLOCKED,
            "column": column,
            "reason": "training_result row id missing",
        }
    return {"status": STOCK_PROFILE_LINEAGE_BLOCKED, "column": column, "reason": "required lineage column missing"}


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


def _forbidden_artifact_exists(settings: StockProfileSettings) -> bool:
    parents = {
        Path(path).parent
        for field in StockProfileSettings.__dataclass_fields__
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


def _metric_names_present(model_meta: dict[str, Any], settings: StockProfileSettings) -> set[str]:
    names = {name.strip() for name in str(model_meta.get("metric_evidence_names_present", "")).split(",") if name.strip()}
    if names:
        return names
    frames = [_load_csv(settings.metric_extension_result_rows_path), _load_csv(settings.metric_computation_result_rows_path)]
    output: set[str] = set()
    for frame in frames:
        output |= {str(name) for name in frame.get("metric_name", pd.Series(dtype=str)).astype(str)}
    return output


def _metric_names_overclaim(model_meta: dict[str, Any]) -> bool:
    return "strategy performance validated" in str(model_meta.get("metric_evidence_names_present", "")).lower()


def _quarantine_count(rows: list[dict[str, Any]]) -> int:
    total = 0
    for row in rows:
        try:
            total += int(float(row.get("quarantine_count", 0) or 0))
        except ValueError:
            continue
    return total


def _active_model_limitation_phrases() -> set[str]:
    return {
        "no stock_profile",
        "no buy-review",
        "no paper approval",
        "no performance validation",
        "no trading",
    }


def _model_limitations_safe(text: str) -> bool:
    if "report-only" not in text:
        return False
    required_topics = [
        ("stock_profile", "stock profile"),
        ("buy-review", "buy review"),
        ("paper approval",),
        ("performance validation", "strategy performance"),
        ("trading",),
    ]
    return all(any(topic in text for topic in topics) for topics in required_topics)


def _required_warning_subset() -> set[str]:
    return {
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
        "prediction overfit",
        "benchmark mismatch",
        "industry classification drift",
        "survivorship bias",
        "lookahead leakage",
        "paper-overfit risk",
    }


def _unsafe_safety_fields() -> list[str]:
    return [
        "active_stock_profile_exists",
        "stock_profile_created",
        "active_stock_profile_created",
        "buy_review_allowed",
        "real_buy_review_eligible",
        "approved_for_paper",
        "strategy_performance_validated",
        "trading_allowed",
        "current_candidates_run",
        "snapshot_built",
        "signal_semantics_changed",
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


def _group_for_status(status: str) -> str:
    if status == STOCK_PROFILE_HEALTH_BLOCKED:
        return "upstream_lineage"
    if status == STOCK_PROFILE_ACTIVE_MODEL_INPUT_BLOCKED or status == STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED:
        return "active_model_input"
    if status == STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED or status == STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED:
        return "model_weight_versioning_input"
    if status == STOCK_PROFILE_TRAINING_RESULT_ROWS_BLOCKED:
        return "training_result_input"
    if status == STOCK_PROFILE_METRIC_EVIDENCE_BLOCKED:
        return "metric_evidence"
    if status == STOCK_PROFILE_LEAKAGE_BLOCKED:
        return "leakage"
    if status == STOCK_PROFILE_SIDE_EFFECT_BLOCKED:
        return "side_effect"
    if status == STOCK_PROFILE_OVERCLAIM_BLOCKED:
        return "overclaim"
    return "precondition"


def _blocked(status: str, group: str, name: str, reason: str) -> StockProfileGateResult:
    return StockProfileGateResult(group, name, status, False, reason)


def _passed_gate(group: str, name: str) -> StockProfileGateResult:
    return StockProfileGateResult(group, name, "PASS", True, "")


def _gate_frame(gates: list[StockProfileGateResult], group: str) -> pd.DataFrame:
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
        raise ValueError("stock profile output must stay under outputs/reports/manual_diagnostics")


def _stable_id(settings: StockProfileSettings) -> str:
    payload = {
        field: str(getattr(settings, field))
        for field in StockProfileSettings.__dataclass_fields__
        if field != "write_artifacts"
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:12]
