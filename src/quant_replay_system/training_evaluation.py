"""Report-only training/evaluation phase 1 planning workflow.

This module deliberately stops at bounded dataset/planning diagnostics. It can
assemble a small training/evaluation input preview from frozen replay decisions
and existing forward labels, but it never computes metrics, trains weights,
creates model versions, creates stock profiles, grants buy-review eligibility,
approves paper workflow, validates strategy performance, or touches trading
systems.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_TRAINING_EVALUATION_INPUT = "NO_TRAINING_EVALUATION_INPUT"
TRAINING_EVALUATION_INPUT_FOUND = "TRAINING_EVALUATION_INPUT_FOUND"
TRAINING_EVALUATION_APPROVAL_BLOCKED = "TRAINING_EVALUATION_APPROVAL_BLOCKED"
TRAINING_EVALUATION_LINEAGE_BLOCKED = "TRAINING_EVALUATION_LINEAGE_BLOCKED"
TRAINING_EVALUATION_FORWARD_LABEL_BLOCKED = "TRAINING_EVALUATION_FORWARD_LABEL_BLOCKED"
TRAINING_EVALUATION_FROZEN_DECISION_BLOCKED = "TRAINING_EVALUATION_FROZEN_DECISION_BLOCKED"
TRAINING_EVALUATION_DATASET_BOUNDARY_BLOCKED = "TRAINING_EVALUATION_DATASET_BOUNDARY_BLOCKED"
TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED = "TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED"
TRAINING_EVALUATION_SPLIT_BLOCKED = "TRAINING_EVALUATION_SPLIT_BLOCKED"
TRAINING_EVALUATION_LABEL_PLAN_BLOCKED = "TRAINING_EVALUATION_LABEL_PLAN_BLOCKED"
TRAINING_EVALUATION_LEAKAGE_BLOCKED = "TRAINING_EVALUATION_LEAKAGE_BLOCKED"
TRAINING_EVALUATION_METRIC_BLOCKED = "TRAINING_EVALUATION_METRIC_BLOCKED"
TRAINING_EVALUATION_SIDE_EFFECT_BLOCKED = "TRAINING_EVALUATION_SIDE_EFFECT_BLOCKED"
TRAINING_EVALUATION_OVERCLAIM_BLOCKED = "TRAINING_EVALUATION_OVERCLAIM_BLOCKED"
TRAINING_EVALUATION_REVIEW_BLOCKED = "TRAINING_EVALUATION_REVIEW_BLOCKED"
READY_FOR_TRAINING_EVALUATION_DATASET = "READY_FOR_TRAINING_EVALUATION_DATASET"
TRAINING_EVALUATION_DATASET_CREATED = "TRAINING_EVALUATION_DATASET_CREATED"

EXACT_APPROVAL_TEXT = (
    "I explicitly authorize implementation of training/evaluation core phase 1 only, "
    "report-only dataset/planning-only. It may create metadata, dataset index, bounded sample rows, "
    "label coverage report, split plan, feature plan, label plan, and safety artifacts. It must not "
    "compute metrics, create training_result, train weights, create model_version, optimize thresholds, "
    "create stock_profile, generate buy-review eligibility, apply paper approval, claim strategy "
    "performance validation, integrate broker/order/message, or trade."
)

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/training_evaluation_v0_1")
MAX_SAMPLE_ROWS = 50

ARTIFACT_FILES = {
    "metadata": "training_evaluation_metadata.json",
    "report": "training_evaluation_report.md",
    "dataset_index": "training_evaluation_dataset_index.csv",
    "training_evaluation_sample_rows": "training_evaluation_sample_rows.csv",
    "sample_rows": "training_evaluation_sample_rows.csv",
    "label_coverage_report": "training_evaluation_label_coverage_report.csv",
    "split_plan": "training_evaluation_split_plan.csv",
    "feature_plan": "training_evaluation_feature_plan.csv",
    "label_plan": "training_evaluation_label_plan.csv",
    "safety_flags": "training_evaluation_safety_flags.json",
    "precondition_results": "training_evaluation_precondition_results.csv",
    "approval_results": "training_evaluation_approval_results.csv",
    "lineage_results": "training_evaluation_lineage_results.csv",
    "dataset_boundary_results": "training_evaluation_dataset_boundary_results.csv",
    "feature_governance_results": "training_evaluation_feature_governance_results.csv",
    "split_guard_results": "training_evaluation_split_guard_results.csv",
    "label_guard_results": "training_evaluation_label_guard_results.csv",
    "leakage_side_effect_guard_results": "training_evaluation_leakage_side_effect_guard_results.csv",
    "overclaim_guard_results": "training_evaluation_overclaim_guard_results.csv",
    "recommended_next_task": "recommended_next_task.md",
}

FORBIDDEN_FALSE_FIELDS = [
    "metrics_computed",
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
METRIC_REQUEST_FIELDS = {
    "metrics_computation_requested",
    "training_result_requested",
    "weights_requested",
    "model_version_requested",
    "thresholds_requested",
    "predictions_requested",
    "calibrated_probabilities_requested",
    "feature_importance_requested",
}
SIDE_EFFECT_REQUEST_FIELDS = {"trading_requested"}
OVERCLAIM_REQUEST_FIELDS = {"buy_review_requested", "paper_approval_requested", "performance_validation_requested"}
FEATURE_FORBIDDEN_FIELDS = {
    "uses_future_label_as_feature",
    "uses_future_price_as_feature",
    "uses_paper_outcome_as_feature",
    "uses_stock_profile_fields",
    "uses_broker_order_fill_fields",
}
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
    "training_evaluation_not_training_result",
    "training_evaluation_not_model_weights",
    "training_evaluation_not_stock_profile",
    "training_evaluation_not_buy_review",
    "training_evaluation_not_paper_approval",
    "training_evaluation_not_performance_validation",
    "training_evaluation_not_trading",
}
FORWARD_LABEL_ROW_COLUMNS = {
    "replay_decision_id",
    "replay_decision_freeze_run_id",
    "forward_return_label_run_id",
    "symbol",
    "label_name",
    "label_horizon_trading_days",
    "label_start_date",
    "label_end_date",
    "forward_return",
    "price_source_id",
    "price_source_hash",
    "price_revision_id",
    "price_available_time",
    "price_quality_status",
}
REPLAY_DECISION_ROW_COLUMNS = {"replay_decision_id", "replay_decision_freeze_run_id", "symbol"}


@dataclass(frozen=True)
class TrainingEvaluationSettings:
    approval_manifest_path: Path | None = None
    training_evaluation_request_manifest_path: Path | None = None
    forward_return_label_metadata_path: Path | None = None
    forward_return_label_rows_path: Path | None = None
    forward_return_label_status_artifact_path: Path | None = None
    forward_return_label_health_artifact_path: Path | None = None
    forward_return_label_safety_flags_path: Path | None = None
    replay_decision_metadata_path: Path | None = None
    replay_decision_rows_path: Path | None = None
    replay_decision_evidence_index_path: Path | None = None
    factor_observation_index_path: Path | None = None
    event_structured_index_path: Path | None = None
    company_exposure_index_path: Path | None = None
    source_registry_path: Path | None = None
    split_plan_request_path: Path | None = None
    feature_plan_request_path: Path | None = None
    label_plan_request_path: Path | None = None
    leakage_side_effect_evidence_bundle_path: Path | None = None
    overclaim_evidence_bundle_path: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    allow_training_evaluation_dataset: bool = False
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class TrainingEvaluationGateResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str = ""
    observed_value: str = ""


TrainingEvaluationPreconditionResult = TrainingEvaluationGateResult
TrainingEvaluationApprovalResult = TrainingEvaluationGateResult
TrainingEvaluationLineageResult = TrainingEvaluationGateResult
TrainingEvaluationDatasetBoundaryResult = TrainingEvaluationGateResult
TrainingEvaluationFeatureGovernanceResult = TrainingEvaluationGateResult
TrainingEvaluationSplitPlanResult = TrainingEvaluationGateResult
TrainingEvaluationLabelPlanResult = TrainingEvaluationGateResult
TrainingEvaluationLeakageSideEffectResult = TrainingEvaluationGateResult
TrainingEvaluationOverclaimResult = TrainingEvaluationGateResult


@dataclass(frozen=True)
class TrainingEvaluationResult:
    training_evaluation_run_id: str
    status: str
    workflow_stage: str
    ready_for_training_evaluation_dataset: bool
    training_evaluation_executed: bool
    training_evaluation_dataset_artifacts_created: bool
    bounded_sample_rows_created: bool
    label_coverage_report_created: bool
    split_plan_created: bool
    feature_plan_created: bool
    label_plan_created: bool
    training_evaluation_dataset_artifact_path: str
    source_forward_return_label_run_id: str = ""
    source_forward_return_label_artifact_path: str = ""
    source_forward_return_label_status: str = ""
    source_forward_return_label_health_status: str = ""
    source_replay_decision_freeze_run_id: str = ""
    forward_labels_exist: bool = False
    forward_return_labels_created: bool = False
    label_row_count: int = 0
    replay_decision_count: int = 0
    symbol_count: int = 0
    label_name_set: str = ""
    dataset_sample_row_count: int = 0
    max_sample_rows: int = MAX_SAMPLE_ROWS
    feature_plan_ref: str = ""
    label_plan_ref: str = ""
    split_plan_ref: str = ""
    approval_scope: str = "training_evaluation_phase_1_report_only_dataset_planning_only"
    blocker_count: int = 0
    warning_count: int = 0
    next_action: str = ""
    report_only: bool = True
    diagnostic_only: bool = True
    artifact_paths: dict[str, Path] = field(default_factory=dict)
    gate_results: list[TrainingEvaluationGateResult] = field(default_factory=list)
    metrics_computed: bool = False
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


def run_training_evaluation(settings: TrainingEvaluationSettings | None = None) -> TrainingEvaluationResult:
    settings = settings or TrainingEvaluationSettings()
    output_root = Path(settings.output_dir)
    _assert_manual_diagnostics_output(output_root)
    run_id = _stable_id(settings)
    artifact_dir = output_root / run_id
    artifact_paths = {"artifact_dir": artifact_dir} | {
        key: artifact_dir / filename for key, filename in ARTIFACT_FILES.items()
    }

    state = _evaluate(settings)
    status = state["status"]
    created = status == TRAINING_EVALUATION_DATASET_CREATED
    ready = status in {READY_FOR_TRAINING_EVALUATION_DATASET, TRAINING_EVALUATION_DATASET_CREATED}
    rows = state.get("forward_rows", pd.DataFrame())
    replay_rows = state.get("replay_rows", pd.DataFrame())
    sample = _build_sample_rows(rows, replay_rows) if created else _empty_sample_rows()

    result = TrainingEvaluationResult(
        training_evaluation_run_id=run_id,
        status=status,
        workflow_stage="TRAINING_EVALUATION_NO_INPUT" if status == NO_TRAINING_EVALUATION_INPUT else status,
        ready_for_training_evaluation_dataset=ready,
        training_evaluation_executed=created,
        training_evaluation_dataset_artifacts_created=created,
        bounded_sample_rows_created=created and not sample.empty,
        label_coverage_report_created=created,
        split_plan_created=created,
        feature_plan_created=created,
        label_plan_created=created,
        training_evaluation_dataset_artifact_path=str(artifact_paths["training_evaluation_sample_rows"]),
        source_forward_return_label_run_id=str(state["forward_metadata"].get("forward_return_label_run_id", "")),
        source_forward_return_label_artifact_path=str(settings.forward_return_label_rows_path or ""),
        source_forward_return_label_status=str(state["forward_metadata"].get("status", "")),
        source_forward_return_label_health_status=str(state["forward_metadata"].get("health_status", "")),
        source_replay_decision_freeze_run_id=str(state["replay_metadata"].get("replay_decision_freeze_run_id", "")),
        forward_labels_exist=bool(state["forward_metadata"].get("forward_labels_exist", False)),
        forward_return_labels_created=bool(state["forward_metadata"].get("forward_return_labels_created", False)),
        label_row_count=len(rows),
        replay_decision_count=len(replay_rows),
        symbol_count=_symbol_count(rows),
        label_name_set=",".join(sorted(rows["label_name"].dropna().astype(str).unique())) if "label_name" in rows else "",
        dataset_sample_row_count=len(sample),
        feature_plan_ref=str(settings.feature_plan_request_path or ""),
        label_plan_ref=str(settings.label_plan_request_path or ""),
        split_plan_ref=str(settings.split_plan_request_path or ""),
        blocker_count=0 if ready else 1 if status != NO_TRAINING_EVALUATION_INPUT else 0,
        warning_count=0,
        next_action=_next_action(status),
        artifact_paths=artifact_paths,
        gate_results=state["gate_results"],
    )
    if settings.write_artifacts:
        _write_artifacts(result, state, sample)
    return result


def write_training_evaluation_artifacts(result: TrainingEvaluationResult) -> None:
    """Rewrite artifacts already represented by a result.

    The normal public entry point is :func:`run_training_evaluation`; this
    helper exists so follow-on report-only views can reuse the artifact writer
    without expanding scope into metrics or model training.
    """

    _write_artifacts(result, {"forward_rows": pd.DataFrame()}, _empty_sample_rows())


def _evaluate(settings: TrainingEvaluationSettings) -> dict[str, Any]:
    gate_results: list[TrainingEvaluationGateResult] = []
    state: dict[str, Any] = {
        "status": NO_TRAINING_EVALUATION_INPUT,
        "forward_metadata": {},
        "replay_metadata": {},
        "forward_rows": pd.DataFrame(),
        "replay_rows": pd.DataFrame(),
        "gate_results": gate_results,
    }
    if not _has_any_input(settings):
        gate_results.append(_gate("precondition", "input_presence", NO_TRAINING_EVALUATION_INPUT, True, "no input supplied"))
        return state

    approval = _read_json(settings.approval_manifest_path)
    if approval.get("approval_text") != EXACT_APPROVAL_TEXT:
        return _blocked(state, TRAINING_EVALUATION_APPROVAL_BLOCKED, "approval", "exact_phase_1_scope", "exact narrow approval text missing", settings.approval_manifest_path)
    gate_results.append(_gate("approval", "exact_phase_1_scope", "PASS", True, "", settings.approval_manifest_path))

    request = _read_json(settings.training_evaluation_request_manifest_path)
    status = _request_block_status(request)
    if status:
        return _blocked(state, status, "approval", "request_scope", "request asks for work outside report-only phase 1", settings.training_evaluation_request_manifest_path)

    forward_metadata = _read_json(settings.forward_return_label_metadata_path)
    state["forward_metadata"] = forward_metadata
    if (
        forward_metadata.get("status") != "FORWARD_RETURN_LABELS_CREATED"
        or forward_metadata.get("health_status") != "PASS"
        or forward_metadata.get("forward_labels_exist") is not True
        or forward_metadata.get("forward_return_labels_created") is not True
    ):
        return _blocked(state, TRAINING_EVALUATION_FORWARD_LABEL_BLOCKED, "lineage", "forward_label_metadata", "forward label metadata is not complete/PASS", settings.forward_return_label_metadata_path)
    forward_rows = _read_csv(settings.forward_return_label_rows_path)
    state["forward_rows"] = forward_rows
    missing = FORWARD_LABEL_ROW_COLUMNS - set(forward_rows.columns)
    if missing or forward_rows.empty:
        return _blocked(state, TRAINING_EVALUATION_FORWARD_LABEL_BLOCKED, "lineage", "forward_label_rows", f"missing forward label columns/rows: {sorted(missing)}", settings.forward_return_label_rows_path)
    gate_results.append(_gate("lineage", "forward_labels", "PASS", True, "", settings.forward_return_label_rows_path))

    replay_metadata = _read_json(settings.replay_decision_metadata_path)
    state["replay_metadata"] = replay_metadata
    replay_rows = _read_csv(settings.replay_decision_rows_path)
    state["replay_rows"] = replay_rows
    if (
        replay_metadata.get("execution_status") != "REPLAY_DECISION_FROZEN"
        or replay_metadata.get("replay_decision_frozen") is not True
        or replay_metadata.get("health_status") != "PASS"
        or replay_rows.empty
        or (REPLAY_DECISION_ROW_COLUMNS - set(replay_rows.columns))
        or not _path_exists(settings.replay_decision_evidence_index_path)
    ):
        return _blocked(state, TRAINING_EVALUATION_FROZEN_DECISION_BLOCKED, "lineage", "replay_decision_freeze", "frozen replay decision inputs are missing or not PASS", settings.replay_decision_metadata_path)
    gate_results.append(_gate("lineage", "replay_decision_freeze", "PASS", True, "", settings.replay_decision_metadata_path))

    feature_block = _feature_governance_block(settings)
    if feature_block:
        return _blocked(state, TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED, "feature_governance", "feature_inputs", feature_block, settings.feature_plan_request_path)
    gate_results.append(_gate("feature_governance", "feature_inputs", "PASS", True, "", settings.feature_plan_request_path))

    split = _read_json(settings.split_plan_request_path)
    if split.get("valid_split_plan") is not True:
        return _blocked(state, TRAINING_EVALUATION_SPLIT_BLOCKED, "split", "split_plan", "split plan is not valid", settings.split_plan_request_path)
    gate_results.append(_gate("split", "split_plan", "PASS", True, "", settings.split_plan_request_path))

    label = _read_json(settings.label_plan_request_path)
    if label.get("valid_label_plan") is not True or label.get("forward_labels_target_only") is not True:
        return _blocked(state, TRAINING_EVALUATION_LABEL_PLAN_BLOCKED, "label", "label_plan", "label plan is not target-only", settings.label_plan_request_path)
    gate_results.append(_gate("label", "label_plan", "PASS", True, "", settings.label_plan_request_path))

    if not _path_exists(settings.leakage_side_effect_evidence_bundle_path):
        return _blocked(
            state,
            TRAINING_EVALUATION_LEAKAGE_BLOCKED,
            "leakage",
            "leakage_bundle",
            "leakage/side-effect evidence bundle is missing",
            settings.leakage_side_effect_evidence_bundle_path,
        )
    leakage = _read_json(settings.leakage_side_effect_evidence_bundle_path)
    if any(leakage.get(field) is True for field in SIDE_EFFECT_TRUE_FIELDS):
        return _blocked(state, TRAINING_EVALUATION_SIDE_EFFECT_BLOCKED, "side_effect", "side_effect_flags", "side-effect flag is true", settings.leakage_side_effect_evidence_bundle_path)
    if any(leakage.get(field) is True for field in FORBIDDEN_FALSE_FIELDS if field not in SIDE_EFFECT_TRUE_FIELDS):
        return _blocked(state, TRAINING_EVALUATION_LEAKAGE_BLOCKED, "leakage", "leakage_flags", "leakage flag is true", settings.leakage_side_effect_evidence_bundle_path)
    gate_results.append(_gate("leakage_side_effect", "safety_flags", "PASS", True, "", settings.leakage_side_effect_evidence_bundle_path))

    overclaim = _read_json(settings.overclaim_evidence_bundle_path)
    if any(overclaim.get(field) is not True for field in REQUIRED_OVERCLAIM_TRUE) or overclaim.get("strategy_performance_validated") is True:
        return _blocked(state, TRAINING_EVALUATION_OVERCLAIM_BLOCKED, "overclaim", "overclaim_bundle", "overclaim guard not satisfied", settings.overclaim_evidence_bundle_path)
    gate_results.append(_gate("overclaim", "overclaim_bundle", "PASS", True, "", settings.overclaim_evidence_bundle_path))

    state["status"] = TRAINING_EVALUATION_DATASET_CREATED if settings.allow_training_evaluation_dataset else READY_FOR_TRAINING_EVALUATION_DATASET
    return state


def _request_block_status(request: dict[str, Any]) -> str | None:
    if any(request.get(field) is True for field in METRIC_REQUEST_FIELDS):
        return TRAINING_EVALUATION_METRIC_BLOCKED
    if request.get("stock_profile_requested") is True:
        return TRAINING_EVALUATION_LEAKAGE_BLOCKED
    if any(request.get(field) is True for field in OVERCLAIM_REQUEST_FIELDS):
        return TRAINING_EVALUATION_OVERCLAIM_BLOCKED
    if any(request.get(field) is True for field in SIDE_EFFECT_REQUEST_FIELDS):
        return TRAINING_EVALUATION_SIDE_EFFECT_BLOCKED
    return None


def _feature_governance_block(settings: TrainingEvaluationSettings) -> str:
    for path in [
        settings.factor_observation_index_path,
        settings.event_structured_index_path,
        settings.company_exposure_index_path,
        settings.source_registry_path,
    ]:
        if not _path_exists(path):
            return f"missing feature governance input: {path}"
        frame = _read_csv(path)
        if frame.empty:
            return f"empty feature governance input: {path}"
        for column in ["source_hash_coverage", "revision_id_coverage", "available_time_coverage", "quality_status_coverage"]:
            if column in frame.columns and not frame[column].astype(str).str.upper().eq("PASS").all():
                return f"{column} is not PASS in {path}"
    if not _path_exists(settings.feature_plan_request_path):
        return f"missing feature plan request: {settings.feature_plan_request_path}"
    feature_plan = _read_json(settings.feature_plan_request_path)
    if feature_plan.get("valid_feature_plan", True) is not True:
        return "feature plan is not valid"
    if any(feature_plan.get(field) is True for field in FEATURE_FORBIDDEN_FIELDS):
        return "feature plan references future/forbidden fields"
    return ""


def _blocked(
    state: dict[str, Any],
    status: str,
    group: str,
    gate_name: str,
    reason: str,
    path: Path | None = None,
) -> dict[str, Any]:
    state["status"] = status
    state["gate_results"].append(_gate(group, gate_name, status, False, reason, path))
    return state


def _build_sample_rows(forward_rows: pd.DataFrame, replay_rows: pd.DataFrame) -> pd.DataFrame:
    merged = forward_rows.merge(
        replay_rows,
        on=["replay_decision_id", "replay_decision_freeze_run_id", "symbol"],
        how="left",
        suffixes=("", "_decision"),
    ).head(MAX_SAMPLE_ROWS)
    if merged.empty:
        return _empty_sample_rows()
    return pd.DataFrame(
        {
            "training_evaluation_row_id": [
                _hash_text(f"{row.replay_decision_id}|{row.symbol}|{row.label_name}") for row in merged.itertuples()
            ],
            "replay_decision_id": merged["replay_decision_id"].astype(str),
            "replay_decision_freeze_run_id": merged["replay_decision_freeze_run_id"].astype(str),
            "forward_return_label_run_id": merged["forward_return_label_run_id"].astype(str),
            "symbol": merged["symbol"].astype(str).str.zfill(6),
            "instrument_type": _merged_series(merged, "instrument_type", "instrument_type_decision"),
            "replay_as_of_date": _merged_series(merged, "replay_as_of_date", "replay_as_of_date_decision"),
            "feature_snapshot_ref": _merged_series(merged, "feature_snapshot_ref"),
            "label_name": merged["label_name"].astype(str),
            "label_horizon_trading_days": merged["label_horizon_trading_days"],
            "label_start_date": merged["label_start_date"].astype(str),
            "label_end_date": merged["label_end_date"].astype(str),
            "label_value": merged["forward_return"],
            "label_source_field": "forward_return",
            "split_role": "planning_preview",
            "report_only": True,
            "diagnostic_only": True,
        }
    )


def _empty_sample_rows() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "training_evaluation_row_id",
            "replay_decision_id",
            "replay_decision_freeze_run_id",
            "forward_return_label_run_id",
            "symbol",
            "instrument_type",
            "replay_as_of_date",
            "feature_snapshot_ref",
            "label_name",
            "label_horizon_trading_days",
            "label_start_date",
            "label_end_date",
            "label_value",
            "label_source_field",
            "split_role",
            "report_only",
            "diagnostic_only",
        ]
    )


def _merged_series(frame: pd.DataFrame, primary: str, fallback: str | None = None) -> pd.Series:
    if primary in frame.columns:
        return frame[primary].astype(str)
    if fallback and fallback in frame.columns:
        return frame[fallback].astype(str)
    return pd.Series([""] * len(frame), index=frame.index, dtype="string")


def _write_artifacts(result: TrainingEvaluationResult, state: dict[str, Any], sample: pd.DataFrame) -> None:
    artifact_dir = result.artifact_paths["artifact_dir"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    metadata = _metadata(result)
    result.artifact_paths["metadata"].write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["safety_flags"].write_text(json.dumps(_safety_flags(), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(_recommended_next_task(result), encoding="utf-8")

    _write_csv(result.artifact_paths["training_evaluation_sample_rows"], sample)
    _write_csv(result.artifact_paths["dataset_index"], _dataset_index_rows(result))
    _write_csv(result.artifact_paths["label_coverage_report"], _label_coverage(state.get("forward_rows", pd.DataFrame())))
    _write_csv(result.artifact_paths["split_plan"], _planning_rows("split_plan", result.split_plan_ref))
    _write_csv(result.artifact_paths["feature_plan"], _planning_rows("feature_plan", result.feature_plan_ref))
    _write_csv(result.artifact_paths["label_plan"], _planning_rows("label_plan", result.label_plan_ref))
    gates = pd.DataFrame([asdict(gate) for gate in result.gate_results])
    for key in [
        "precondition_results",
        "approval_results",
        "lineage_results",
        "dataset_boundary_results",
        "feature_governance_results",
        "split_guard_results",
        "label_guard_results",
        "leakage_side_effect_guard_results",
        "overclaim_guard_results",
    ]:
        group_prefix = key.replace("_results", "").split("_")[0]
        subset = gates[gates["gate_group"].str.startswith(group_prefix)] if not gates.empty else gates
        _write_csv(result.artifact_paths[key], subset if not subset.empty else _empty_gate_frame(key))


def _metadata(result: TrainingEvaluationResult) -> dict[str, Any]:
    payload = {
        "training_evaluation_run_id": result.training_evaluation_run_id,
        "execution_status": result.status,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "ready_for_training_evaluation_dataset": result.ready_for_training_evaluation_dataset,
        "training_evaluation_executed": result.training_evaluation_executed,
        "training_evaluation_dataset_artifacts_created": result.training_evaluation_dataset_artifacts_created,
        "bounded_sample_rows_created": result.bounded_sample_rows_created,
        "label_coverage_report_created": result.label_coverage_report_created,
        "split_plan_created": result.split_plan_created,
        "feature_plan_created": result.feature_plan_created,
        "label_plan_created": result.label_plan_created,
        "training_evaluation_dataset_artifact_path": result.training_evaluation_dataset_artifact_path,
        "label_row_count": result.label_row_count,
        "replay_decision_count": result.replay_decision_count,
        "symbol_count": result.symbol_count,
        "dataset_sample_row_count": result.dataset_sample_row_count,
        "source_forward_return_label_run_id": result.source_forward_return_label_run_id,
        "source_forward_return_label_status": result.source_forward_return_label_status,
        "source_forward_return_label_health_status": result.source_forward_return_label_health_status,
        "source_replay_decision_freeze_run_id": result.source_replay_decision_freeze_run_id,
        "forward_labels_exist": result.forward_labels_exist,
        "forward_return_labels_created": result.forward_return_labels_created,
        "label_name_set": result.label_name_set,
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update(_safety_flags())
    return payload


def _safety_flags() -> dict[str, bool]:
    return {field: False for field in FORBIDDEN_FALSE_FIELDS} | {"report_only": True, "diagnostic_only": True}


def _dataset_index_rows(result: TrainingEvaluationResult) -> pd.DataFrame:
    rows = [
        {"artifact_name": "training_evaluation_sample_rows", "artifact_path": result.training_evaluation_dataset_artifact_path},
        {"artifact_name": "label_coverage_report", "artifact_path": str(result.artifact_paths["label_coverage_report"])},
        {"artifact_name": "split_plan", "artifact_path": str(result.artifact_paths["split_plan"])},
        {"artifact_name": "feature_plan", "artifact_path": str(result.artifact_paths["feature_plan"])},
        {"artifact_name": "label_plan", "artifact_path": str(result.artifact_paths["label_plan"])},
    ]
    return pd.DataFrame(
        [
            row
            | {
                "source_hash_coverage": "PASS" if result.ready_for_training_evaluation_dataset else "NOT_EVALUATED",
                "revision_id_coverage": "PASS" if result.ready_for_training_evaluation_dataset else "NOT_EVALUATED",
                "available_time_coverage": "PASS" if result.ready_for_training_evaluation_dataset else "NOT_EVALUATED",
                "quality_status_coverage": "PASS" if result.ready_for_training_evaluation_dataset else "NOT_EVALUATED",
                "report_only": True,
                "diagnostic_only": True,
            }
            for row in rows
        ]
    )


def _label_coverage(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty or "label_name" not in rows:
        return pd.DataFrame(columns=["label_name", "label_horizon_trading_days", "row_count", "symbol_count", "report_only", "diagnostic_only"])
    grouped = (
        rows.groupby(["label_name", "label_horizon_trading_days"], dropna=False)
        .agg(row_count=("label_name", "size"), symbol_count=("symbol", "nunique"))
        .reset_index()
    )
    grouped["report_only"] = True
    grouped["diagnostic_only"] = True
    return grouped


def _planning_rows(plan_type: str, source_ref: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "plan_type": plan_type,
                "source_ref": source_ref,
                "planning_status": "REPORT_ONLY_PLANNED",
                "report_only": True,
                "diagnostic_only": True,
            }
        ]
    )


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


def _render_report(result: TrainingEvaluationResult) -> str:
    return "\n".join(
        [
            "# Training / Evaluation Phase 1 Report",
            "",
            f"- status: {result.status}",
            f"- training_evaluation_run_id: {result.training_evaluation_run_id}",
            f"- ready_for_training_evaluation_dataset: {result.ready_for_training_evaluation_dataset}",
            f"- training_evaluation_dataset_artifacts_created: {result.training_evaluation_dataset_artifacts_created}",
            "",
            "This is dataset/planning-only output: not metrics, not training_result, not weights, "
            "not model_version, not stock_profile, not buy-review, not paper approval, "
            "not performance validation, and not trading.",
        ]
    )


def _recommended_next_task(result: TrainingEvaluationResult) -> str:
    if result.status == TRAINING_EVALUATION_DATASET_CREATED:
        return "Next task: review the report-only training/evaluation dataset planning artifacts before any metrics or training design.\n"
    if result.ready_for_training_evaluation_dataset:
        return "Next task: rerun with --allow-training-evaluation-dataset only if report-only dataset/planning artifacts are explicitly needed.\n"
    return "Next task: resolve the reported gate blocker before creating any report-only dataset/planning artifacts.\n"


def _next_action(status: str) -> str:
    if status == NO_TRAINING_EVALUATION_INPUT:
        return "Provide frozen replay decision, forward label, governance, approval, leakage, and overclaim inputs."
    if status == READY_FOR_TRAINING_EVALUATION_DATASET:
        return "Review gates; optionally rerun with explicit dataset/planning allowance."
    if status == TRAINING_EVALUATION_DATASET_CREATED:
        return "Review report-only bounded sample, label coverage, split, feature, and label plans."
    return "Resolve blocker; no training/evaluation dataset planning artifact should be trusted yet."


def _has_any_input(settings: TrainingEvaluationSettings) -> bool:
    paths = [
        settings.approval_manifest_path,
        settings.training_evaluation_request_manifest_path,
        settings.forward_return_label_metadata_path,
        settings.forward_return_label_rows_path,
        settings.replay_decision_metadata_path,
        settings.replay_decision_rows_path,
    ]
    return any(_path_exists(path) for path in paths)


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


def _gate(
    gate_group: str,
    gate_name: str,
    status: str,
    passed: bool,
    blocker_reason: str,
    evidence_path: Path | None = None,
    observed_value: str = "",
) -> TrainingEvaluationGateResult:
    return TrainingEvaluationGateResult(
        gate_group=gate_group,
        gate_name=gate_name,
        status=status,
        passed=passed,
        blocker_reason=blocker_reason,
        evidence_path=str(evidence_path or ""),
        observed_value=observed_value,
    )


def _symbol_count(rows: pd.DataFrame) -> int:
    if rows.empty or "symbol" not in rows:
        return 0
    return int(rows["symbol"].astype(str).nunique())


def _path_exists(path: Path | None) -> bool:
    return path is not None and Path(path).exists()


def _assert_manual_diagnostics_output(output_dir: Path) -> None:
    parts = {part.lower() for part in output_dir.parts}
    if "manual_diagnostics" not in parts:
        raise ValueError("training-evaluation output_dir must be under outputs/reports/manual_diagnostics")


def _stable_id(settings: TrainingEvaluationSettings) -> str:
    payload = {
        "approval_manifest_path": str(settings.approval_manifest_path or ""),
        "forward_return_label_metadata_path": str(settings.forward_return_label_metadata_path or ""),
        "forward_return_label_rows_path": str(settings.forward_return_label_rows_path or ""),
        "replay_decision_metadata_path": str(settings.replay_decision_metadata_path or ""),
        "allow_training_evaluation_dataset": settings.allow_training_evaluation_dataset,
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
