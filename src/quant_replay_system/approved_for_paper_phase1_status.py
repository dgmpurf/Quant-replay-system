"""Status summary for report-only APPROVED_FOR_PAPER Phase 1 artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.approved_for_paper_phase1 import (
    DOWNSTREAM_FALSE_FIELDS,
    NO_APPROVED_FOR_PAPER_PHASE1_INPUT,
    READY_FOR_APPROVED_FOR_PAPER_PHASE1,
    APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED,
)
from quant_replay_system.approved_for_paper_phase1_health import check_approved_for_paper_phase1_health
from quant_replay_system.approved_for_paper_phase1_index import DEFAULT_ROOT, build_approved_for_paper_phase1_index
from quant_replay_system.approved_for_paper_phase1_index import _text, _to_bool, _to_int


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"
NO_APPROVED_FOR_PAPER_PHASE1_ARTIFACT_FOUND = "NO_APPROVED_FOR_PAPER_PHASE1_ARTIFACT_FOUND"
APPROVED_FOR_PAPER_PHASE1_HEALTH_FAILED = "APPROVED_FOR_PAPER_PHASE1_HEALTH_FAILED"

SUMMARY_COLUMNS = [
    "latest_approved_for_paper_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "ready_for_approved_for_paper_phase1",
    "approved_for_paper_phase1_executed",
    "approved_for_paper_phase1_report_only_artifacts_created",
    "approved_for_paper_metadata_created",
    "approved_for_paper_input_index_created",
    "approved_for_paper_lineage_matrix_created",
    "approved_for_paper_review_context_created",
    "approved_for_paper_decision_draft_created",
    "approved_for_paper_limitations_created",
    "approved_for_paper_overfit_warnings_created",
    "approved_for_paper_safety_flags_created",
    "scoped_approved_for_paper_phase1",
    "scoped_approved_for_paper",
    "approved_for_paper_scope",
    "source_paper_workflow_phase1_run_id",
    "source_paper_workflow_phase1_status",
    "source_paper_workflow_phase1_health_status",
    "source_stock_profile_run_id",
    "source_stock_profile_status",
    "source_stock_profile_health_status",
    "source_active_model_run_id",
    "source_active_model_status",
    "source_active_model_health_status",
    "source_model_workflow_run_id",
    "source_model_weight_versioning_status",
    "source_model_weight_versioning_health_status",
    "model_weight_reference_id",
    "model_version_id",
    "parameter_version_id",
    *DOWNSTREAM_FALSE_FIELDS,
    "blocker_count",
    "warning_count",
    "report_path",
    "safety_statement",
    "next_action",
]


@dataclass(frozen=True)
class ApprovedForPaperPhase1StatusResult:
    latest_approved_for_paper_run_id: str
    status: str
    health_status: str
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
    blocker_count: int
    warning_count: int
    report_path: str
    safety_statement: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_approved_for_paper_phase1_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ApprovedForPaperPhase1StatusResult:
    sibling_root = Path(output_dir).parent
    index = build_approved_for_paper_phase1_index(root=root, output_dir=sibling_root / "index")
    health = check_approved_for_paper_phase1_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        frame = index.index_frame.copy()
        frame["_status_priority"] = frame["status"].map(_status_priority)
        latest = frame.sort_values(["created_at", "_status_priority", "approved_for_paper_run_id"]).iloc[-1].to_dict()
        result = _result_from_latest(latest, health.status, health.error_count, health.warning_count, output_dir, root)
    _write(result)
    return result


def _result_from_latest(
    latest: dict[str, Any],
    health_status: str,
    error_count: int,
    warning_count: int,
    output_dir: str | Path,
    root: str | Path,
) -> ApprovedForPaperPhase1StatusResult:
    status = _text(latest.get("status"))
    stage = APPROVED_FOR_PAPER_PHASE1_HEALTH_FAILED if health_status == "FAIL" else _text(latest.get("workflow_stage")) or status
    summary = {
        "latest_approved_for_paper_run_id": _text(latest.get("approved_for_paper_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "ready_for_approved_for_paper_phase1": _to_bool(latest.get("ready_for_approved_for_paper_phase1")),
        "approved_for_paper_phase1_executed": _to_bool(latest.get("approved_for_paper_phase1_executed")),
        "approved_for_paper_phase1_report_only_artifacts_created": _to_bool(
            latest.get("approved_for_paper_phase1_report_only_artifacts_created")
        ),
        "approved_for_paper_metadata_created": _to_bool(latest.get("approved_for_paper_metadata_created")),
        "approved_for_paper_input_index_created": _to_bool(latest.get("approved_for_paper_input_index_created")),
        "approved_for_paper_lineage_matrix_created": _to_bool(latest.get("approved_for_paper_lineage_matrix_created")),
        "approved_for_paper_review_context_created": _to_bool(latest.get("approved_for_paper_review_context_created")),
        "approved_for_paper_decision_draft_created": _to_bool(latest.get("approved_for_paper_decision_draft_created")),
        "approved_for_paper_limitations_created": _to_bool(latest.get("approved_for_paper_limitations_created")),
        "approved_for_paper_overfit_warnings_created": _to_bool(latest.get("approved_for_paper_overfit_warnings_created")),
        "approved_for_paper_safety_flags_created": _to_bool(latest.get("approved_for_paper_safety_flags_created")),
        "scoped_approved_for_paper_phase1": _to_bool(latest.get("scoped_approved_for_paper_phase1")),
        "scoped_approved_for_paper": _to_bool(latest.get("scoped_approved_for_paper")),
        "approved_for_paper_scope": _text(latest.get("approved_for_paper_scope")),
        "source_paper_workflow_phase1_run_id": _text(latest.get("source_paper_workflow_phase1_run_id")),
        "source_paper_workflow_phase1_status": _text(latest.get("source_paper_workflow_phase1_status")),
        "source_paper_workflow_phase1_health_status": _text(latest.get("source_paper_workflow_phase1_health_status")),
        "source_stock_profile_run_id": _text(latest.get("source_stock_profile_run_id")),
        "source_stock_profile_status": _text(latest.get("source_stock_profile_status")),
        "source_stock_profile_health_status": _text(latest.get("source_stock_profile_health_status")),
        "source_active_model_run_id": _text(latest.get("source_active_model_run_id")),
        "source_active_model_status": _text(latest.get("source_active_model_status")),
        "source_active_model_health_status": _text(latest.get("source_active_model_health_status")),
        "source_model_workflow_run_id": _text(latest.get("source_model_workflow_run_id")),
        "source_model_weight_versioning_status": _text(latest.get("source_model_weight_versioning_status")),
        "source_model_weight_versioning_health_status": _text(latest.get("source_model_weight_versioning_health_status")),
        "model_weight_reference_id": _text(latest.get("model_weight_reference_id")),
        "model_version_id": _text(latest.get("model_version_id")),
        "parameter_version_id": _text(latest.get("parameter_version_id")),
        **{field: _to_bool(latest.get(field)) for field in DOWNSTREAM_FALSE_FIELDS},
        "blocker_count": max(_to_int(latest.get("blocker_count")), error_count),
        "warning_count": max(_to_int(latest.get("warning_count")), warning_count),
        "report_path": _text(latest.get("approved_for_paper_limitations_path")),
        "safety_statement": _safety_statement(),
        "next_action": _next_action(stage, status),
    }
    return _result(summary, output_dir, root, [])


def _no_artifact_result(
    output_dir: str | Path,
    root: str | Path,
    health_status: str,
    error_count: int,
    warning_count: int,
) -> ApprovedForPaperPhase1StatusResult:
    summary = {
        "latest_approved_for_paper_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_APPROVED_FOR_PAPER_PHASE1_ARTIFACT_FOUND,
        "ready_for_approved_for_paper_phase1": False,
        "approved_for_paper_phase1_executed": False,
        "approved_for_paper_phase1_report_only_artifacts_created": False,
        "approved_for_paper_metadata_created": False,
        "approved_for_paper_input_index_created": False,
        "approved_for_paper_lineage_matrix_created": False,
        "approved_for_paper_review_context_created": False,
        "approved_for_paper_decision_draft_created": False,
        "approved_for_paper_limitations_created": False,
        "approved_for_paper_overfit_warnings_created": False,
        "approved_for_paper_safety_flags_created": False,
        "scoped_approved_for_paper_phase1": False,
        "scoped_approved_for_paper": False,
        "approved_for_paper_scope": "",
        "source_paper_workflow_phase1_run_id": "",
        "source_paper_workflow_phase1_status": "",
        "source_paper_workflow_phase1_health_status": "",
        "source_stock_profile_run_id": "",
        "source_stock_profile_status": "",
        "source_stock_profile_health_status": "",
        "source_active_model_run_id": "",
        "source_active_model_status": "",
        "source_active_model_health_status": "",
        "source_model_workflow_run_id": "",
        "source_model_weight_versioning_status": "",
        "source_model_weight_versioning_health_status": "",
        "model_weight_reference_id": "",
        "model_version_id": "",
        "parameter_version_id": "",
        **{field: False for field in DOWNSTREAM_FALSE_FIELDS},
        "blocker_count": max(error_count, 1),
        "warning_count": warning_count,
        "report_path": "",
        "safety_statement": _safety_statement(),
        "next_action": "Create or provide report-only APPROVED_FOR_PAPER Phase 1 artifacts before checking status.",
    }
    return _result(summary, output_dir, root, [])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> ApprovedForPaperPhase1StatusResult:
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "approved_for_paper_phase1_status.csv",
        "status_report": Path(output_dir) / "approved_for_paper_phase1_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    return ApprovedForPaperPhase1StatusResult(
        summary_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata={"root": str(root), "report_only": True, "diagnostic_only": True},
        **summary,
    )


def _write(result: ApprovedForPaperPhase1StatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "latest_approved_for_paper_run_id": result.latest_approved_for_paper_run_id,
                "status": result.status,
                "health_status": result.health_status,
                "workflow_stage": result.workflow_stage,
                "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
                **result.audit_metadata,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    paths["status_report"].write_text(
        "\n".join(
            [
                "# APPROVED_FOR_PAPER Phase 1 Status",
                "",
                result.safety_statement,
                "",
                f"- latest_approved_for_paper_run_id: {result.latest_approved_for_paper_run_id}",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- approved_for_paper_phase1_report_only_artifacts_created: {result.approved_for_paper_phase1_report_only_artifacts_created}",
                f"- scoped_approved_for_paper: {result.scoped_approved_for_paper}",
                f"- model_weight_reference_id: {result.model_weight_reference_id}",
                f"- model_version_id: {result.model_version_id}",
                f"- parameter_version_id: {result.parameter_version_id}",
                f"- next_action: {result.next_action}",
                "",
                result.summary_frame.to_markdown(index=False),
            ]
        ),
        encoding="utf-8",
    )


def _safety_statement() -> str:
    return (
        "APPROVED_FOR_PAPER Phase 1 is report-only APPROVED_FOR_PAPER phase 1 artifact creation only. "
        "APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED means scoped metadata / lineage / "
        "human review context / decision draft / safety artifacts only; it does not create real "
        "buy-review eligibility, does not validate strategy performance, does not integrate "
        "current-candidates, does not build snapshots, does not mutate signal_semantics, does not "
        "create active stock_profile, does not create promoted model, does not create production model, "
        "does not create active thresholds, does not create advisory predictions, does not create active "
        "probabilities, and does not authorize broker/order/message/API/trading."
    )


def _next_action(stage: str, status: str) -> str:
    if stage == APPROVED_FOR_PAPER_PHASE1_HEALTH_FAILED:
        return "Resolve APPROVED_FOR_PAPER Phase 1 artifact health failures before any future integration."
    if status == APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED:
        return "Integrate research-status and checkpoint only after these report-only views remain stable."
    if status == READY_FOR_APPROVED_FOR_PAPER_PHASE1:
        return "Rerun approved-for-paper-phase1 with explicit allow only if report-only artifacts should be created."
    if status == NO_APPROVED_FOR_PAPER_PHASE1_INPUT:
        return "Provide exact approval and complete upstream paper workflow lineage before APPROVED_FOR_PAPER Phase 1."
    return "Resolve blocked APPROVED_FOR_PAPER Phase 1 gates before rerun."


def _status_priority(status: str) -> int:
    if status == APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED:
        return 30
    if status == READY_FOR_APPROVED_FOR_PAPER_PHASE1:
        return 20
    if status == NO_APPROVED_FOR_PAPER_PHASE1_INPUT:
        return 10
    return 0
