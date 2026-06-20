"""Status summary for research-governed active model phase 1 report-only artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.active_model import (
    ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED,
    DOWNSTREAM_FALSE_FIELDS,
    NO_ACTIVE_MODEL_INPUT,
    READY_FOR_ACTIVE_MODEL,
)
from quant_replay_system.active_model_health import check_active_model_health
from quant_replay_system.active_model_index import DEFAULT_ROOT, build_active_model_index
from quant_replay_system.active_model_index import _text, _to_bool, _to_int


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"
NO_ACTIVE_MODEL_ARTIFACT_FOUND = "NO_ACTIVE_MODEL_ARTIFACT_FOUND"
ACTIVE_MODEL_HEALTH_FAILED = "ACTIVE_MODEL_HEALTH_FAILED"

SUMMARY_COLUMNS = [
    "latest_active_model_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "ready_for_active_model",
    "active_model_executed",
    "active_model_artifacts_created",
    "active_model_pointer_created",
    "active_model_registry_entry_created",
    "active_parameter_pointer_created",
    "active_model_activation_status_created",
    "active_model_rollback_plan_created",
    "active_model_input_index_created",
    "active_model_lineage_matrix_created",
    "active_model_limitations_created",
    "active_model_overfit_warnings_created",
    "active_model_safety_flags_created",
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
class ActiveModelStatusResult:
    latest_active_model_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    ready_for_active_model: bool
    active_model_executed: bool
    active_model_artifacts_created: bool
    active_model_pointer_created: bool
    active_model_registry_entry_created: bool
    active_parameter_pointer_created: bool
    active_model_activation_status_created: bool
    active_model_rollback_plan_created: bool
    active_model_input_index_created: bool
    active_model_lineage_matrix_created: bool
    active_model_limitations_created: bool
    active_model_overfit_warnings_created: bool
    active_model_safety_flags_created: bool
    source_model_workflow_run_id: str
    source_model_weight_versioning_status: str
    source_model_weight_versioning_health_status: str
    model_weight_reference_id: str
    model_version_id: str
    parameter_version_id: str
    promoted_model_created: bool
    production_model_created: bool
    active_thresholds_created: bool
    advisory_predictions_created: bool
    active_probabilities_created: bool
    stock_profile_created: bool
    buy_review_allowed: bool
    real_buy_review_eligible: bool
    approved_for_paper: bool
    strategy_performance_validated: bool
    trading_allowed: bool
    order_placed: bool
    broker_api_called: bool
    message_sent: bool
    llm_api_called: bool
    external_api_called: bool
    cache_mutated: bool
    data_raw_written: bool
    data_processed_written: bool
    data_cache_written: bool
    current_candidates_run: bool
    snapshot_built: bool
    signal_semantics_changed: bool
    blocker_count: int
    warning_count: int
    report_path: str
    safety_statement: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_active_model_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ActiveModelStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_active_model_index(root=root, output_dir=sibling_root / "index")
    health = check_active_model_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        frame = index.index_frame.copy()
        frame["_status_priority"] = frame["status"].map(_status_priority)
        latest = frame.sort_values(["created_at", "_status_priority", "active_model_run_id"]).iloc[-1].to_dict()
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
) -> ActiveModelStatusResult:
    status = _text(latest.get("status"))
    stage = ACTIVE_MODEL_HEALTH_FAILED if health_status == "FAIL" else _text(latest.get("workflow_stage")) or status
    summary = {
        "latest_active_model_run_id": _text(latest.get("active_model_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "ready_for_active_model": _to_bool(latest.get("ready_for_active_model")),
        "active_model_executed": _to_bool(latest.get("active_model_executed")),
        "active_model_artifacts_created": _to_bool(latest.get("active_model_artifacts_created")),
        "active_model_pointer_created": _to_bool(latest.get("active_model_pointer_created")),
        "active_model_registry_entry_created": _to_bool(latest.get("active_model_registry_entry_created")),
        "active_parameter_pointer_created": _to_bool(latest.get("active_parameter_pointer_created")),
        "active_model_activation_status_created": _to_bool(latest.get("active_model_activation_status_created")),
        "active_model_rollback_plan_created": _to_bool(latest.get("active_model_rollback_plan_created")),
        "active_model_input_index_created": _to_bool(latest.get("active_model_input_index_created")),
        "active_model_lineage_matrix_created": _to_bool(latest.get("active_model_lineage_matrix_created")),
        "active_model_limitations_created": _to_bool(latest.get("active_model_limitations_created")),
        "active_model_overfit_warnings_created": _to_bool(latest.get("active_model_overfit_warnings_created")),
        "active_model_safety_flags_created": _to_bool(latest.get("active_model_safety_flags_created")),
        "source_model_workflow_run_id": _text(latest.get("source_model_workflow_run_id")),
        "source_model_weight_versioning_status": _text(latest.get("source_model_weight_versioning_status")),
        "source_model_weight_versioning_health_status": _text(latest.get("source_model_weight_versioning_health_status")),
        "model_weight_reference_id": _text(latest.get("model_weight_reference_id")),
        "model_version_id": _text(latest.get("model_version_id")),
        "parameter_version_id": _text(latest.get("parameter_version_id")),
        **{field: _to_bool(latest.get(field)) for field in DOWNSTREAM_FALSE_FIELDS},
        "blocker_count": max(_to_int(latest.get("blocker_count")), error_count),
        "warning_count": max(_to_int(latest.get("warning_count")), warning_count),
        "report_path": _text(latest.get("report_path")),
        "safety_statement": _safety_statement(status),
        "next_action": _next_action(stage, status),
    }
    return _result(summary, output_dir, root, [])


def _no_artifact_result(
    output_dir: str | Path,
    root: str | Path,
    health_status: str,
    error_count: int,
    warning_count: int,
) -> ActiveModelStatusResult:
    summary = {
        "latest_active_model_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_ACTIVE_MODEL_ARTIFACT_FOUND,
        "ready_for_active_model": False,
        "active_model_executed": False,
        "active_model_artifacts_created": False,
        "active_model_pointer_created": False,
        "active_model_registry_entry_created": False,
        "active_parameter_pointer_created": False,
        "active_model_activation_status_created": False,
        "active_model_rollback_plan_created": False,
        "active_model_input_index_created": False,
        "active_model_lineage_matrix_created": False,
        "active_model_limitations_created": False,
        "active_model_overfit_warnings_created": False,
        "active_model_safety_flags_created": False,
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
        "safety_statement": _safety_statement(""),
        "next_action": "Create or provide report-only active-model artifacts before checking status.",
    }
    return _result(summary, output_dir, root, [])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> ActiveModelStatusResult:
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "active_model_status.csv",
        "status_report": Path(output_dir) / "active_model_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    return ActiveModelStatusResult(
        summary_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata={"root": str(root), "report_only": True, "diagnostic_only": True},
        **summary,
    )


def _write(result: ActiveModelStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "latest_active_model_run_id": result.latest_active_model_run_id,
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
                "# Active Model Status",
                "",
                result.safety_statement,
                "",
                f"- latest_active_model_run_id: {result.latest_active_model_run_id}",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- active_model_artifacts_created: {result.active_model_artifacts_created}",
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


def _safety_statement(status: str) -> str:
    return (
        "Active Model Phase 1 is research-governed active-model artifact creation only. "
        "ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED means research-governed active-model "
        "metadata, pointer, registry, parameter, activation, rollback, lineage, limitations, warnings, "
        "and safety artifacts only; it does not create promoted model, does not create production model, "
        "does not create active thresholds, does not create advisory predictions, does not create active "
        "probabilities, does not create stock_profile, does not create buy-review eligibility, does not "
        "apply paper approval, does not claim strategy performance validation, does not authorize trading, "
        "does not integrate current-candidates, does not build snapshots, and does not mutate signal_semantics."
    )


def _next_action(stage: str, status: str) -> str:
    if stage == ACTIVE_MODEL_HEALTH_FAILED:
        return "Resolve active-model artifact health failures before any future research-status integration."
    if status == ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED:
        return "Add research-status integration and checkpoint only after these report-only views remain stable."
    if status == READY_FOR_ACTIVE_MODEL:
        return "Rerun active-model with explicit allow only if research-governed active-model artifacts should be created."
    if status == NO_ACTIVE_MODEL_INPUT:
        return "Provide exact approval and complete model-weight-versioning lineage before active model phase 1."
    return "Resolve blocked active-model gates before rerun."


def _status_priority(status: str) -> int:
    if status == ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED:
        return 30
    if status == READY_FOR_ACTIVE_MODEL:
        return 20
    if status == NO_ACTIVE_MODEL_INPUT:
        return 10
    return 0
