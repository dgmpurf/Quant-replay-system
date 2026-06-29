"""Status view for synthetic Tiny PIT admissibility validator artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_admissibility_validator import SAFETY_FALSE_FLAGS
from quant_replay_system.tiny_pit_admissibility_validator_health import check_tiny_pit_admissibility_validator_health
from quant_replay_system.tiny_pit_admissibility_validator_index import (
    NO_TINY_PIT_ADMISSIBILITY_VALIDATOR,
    build_tiny_pit_admissibility_validator_index,
)


VIEWS_NEXT_ACTION = "Tiny PIT Admissibility Validator Research-Status and Checkpoint Report-Only v0.1"
SUMMARY_COLUMNS = [
    "latest_tiny_pit_admissibility_validator_id",
    "latest_tiny_pit_admissibility_validator_status",
    "latest_tiny_pit_admissibility_validator_health_status",
    "latest_tiny_pit_admissibility_validator_workflow_stage",
    "latest_tiny_pit_admissibility_validator_artifact_path",
    "latest_tiny_pit_admissibility_validator_report_path",
    "latest_tiny_pit_admissibility_validator_case_count",
    "latest_tiny_pit_admissibility_validator_pass_candidate_count",
    "latest_tiny_pit_admissibility_validator_warning_count",
    "latest_tiny_pit_admissibility_validator_blocker_count",
    "latest_tiny_pit_admissibility_validator_report_only",
    "latest_tiny_pit_admissibility_validator_diagnostic_only",
    "latest_tiny_pit_admissibility_validator_synthetic_only",
    "latest_tiny_pit_admissibility_validator_active_replay_input",
    "latest_tiny_pit_admissibility_validator_active_replay_ready",
    "latest_tiny_pit_admissibility_validator_trading_allowed",
    "recommended_next_task",
    *SAFETY_FALSE_FLAGS,
]


@dataclass(frozen=True)
class TinyPitAdmissibilityValidatorStatusResult:
    latest_tiny_pit_admissibility_validator_id: str
    latest_tiny_pit_admissibility_validator_status: str
    latest_tiny_pit_admissibility_validator_health_status: str
    latest_tiny_pit_admissibility_validator_workflow_stage: str
    latest_tiny_pit_admissibility_validator_artifact_path: str
    latest_tiny_pit_admissibility_validator_report_path: str
    latest_tiny_pit_admissibility_validator_case_count: int
    latest_tiny_pit_admissibility_validator_pass_candidate_count: int
    latest_tiny_pit_admissibility_validator_warning_count: int
    latest_tiny_pit_admissibility_validator_blocker_count: int
    latest_tiny_pit_admissibility_validator_report_only: bool
    latest_tiny_pit_admissibility_validator_diagnostic_only: bool
    latest_tiny_pit_admissibility_validator_synthetic_only: bool
    latest_tiny_pit_admissibility_validator_active_replay_input: bool
    latest_tiny_pit_admissibility_validator_active_replay_ready: bool
    latest_tiny_pit_admissibility_validator_trading_allowed: bool
    recommended_next_task: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    real_data_allowed: bool
    active_replay_input: bool
    active_replay_ready: bool
    replay_execution_allowed: bool
    forward_labels_allowed: bool
    training_allowed: bool
    metric_computation_performed: bool
    signal_score_implemented: bool
    model_training_performed: bool
    stock_profile_allowed: bool
    paper_validation_created: bool
    real_buy_review_eligible: bool
    buy_review_allowed: bool
    trading_allowed: bool
    broker_api_calls: bool
    broker_api_called: bool
    order_placed: bool
    message_sent: bool
    external_api_called: bool
    llm_api_called: bool
    real_reviewed_csv_package_created: bool
    active_reviewed_input_candidate_created: bool
    real_replay_input_created: bool
    real_replay_evidence_bundle_created: bool
    real_replay_decision_created: bool
    replay_decision_frozen: bool
    real_forward_labels_created: bool
    future_labels_joined: bool
    future_labels_joined_to_decision_inputs: bool
    future_labels_joined_to_training_dataset: bool
    training_dataset_created: bool
    active_weights_created: bool
    active_thresholds_created: bool
    stock_profile_validation_created: bool
    strategy_performance_validated: bool
    current_candidates_run: bool
    snapshot_built: bool
    signal_semantics_changed: bool
    data_raw_written: bool
    data_processed_written: bool
    data_cache_written: bool


def run_tiny_pit_admissibility_validator_status(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/tiny_pit_admissibility_validator_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/tiny_pit_admissibility_validator_v0_1/status",
) -> TinyPitAdmissibilityValidatorStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_tiny_pit_admissibility_validator_index(root=root, output_dir=sibling_root / "index")
    health = check_tiny_pit_admissibility_validator_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        summary = _no_artifact_summary(health.status)
    else:
        latest = index.index_frame.sort_values(["created_at", "validator_run_id"]).iloc[-1].to_dict()
        summary = _summary_from_latest(latest, health.status)
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    result = TinyPitAdmissibilityValidatorStatusResult(
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health.status == "PASS" else [f"Tiny PIT validator health is {health.status}."],
        **summary,
    )
    _write(result)
    return result


def _summary_from_latest(latest: dict[str, Any], health_status: str) -> dict[str, Any]:
    status = "FAIL" if health_status == "FAIL" else _text(latest.get("status"))
    summary = {
        "latest_tiny_pit_admissibility_validator_id": _text(latest.get("validator_run_id")),
        "latest_tiny_pit_admissibility_validator_status": status,
        "latest_tiny_pit_admissibility_validator_health_status": health_status,
        "latest_tiny_pit_admissibility_validator_workflow_stage": _text(latest.get("workflow_stage")),
        "latest_tiny_pit_admissibility_validator_artifact_path": _text(latest.get("artifact_path")),
        "latest_tiny_pit_admissibility_validator_report_path": _text(latest.get("report_path")),
        "latest_tiny_pit_admissibility_validator_case_count": _to_int(latest.get("case_count")),
        "latest_tiny_pit_admissibility_validator_pass_candidate_count": _to_int(latest.get("pass_candidate_count")),
        "latest_tiny_pit_admissibility_validator_warning_count": _to_int(latest.get("warning_count")),
        "latest_tiny_pit_admissibility_validator_blocker_count": _to_int(latest.get("blocker_count")),
        "latest_tiny_pit_admissibility_validator_report_only": _to_bool(latest.get("report_only")),
        "latest_tiny_pit_admissibility_validator_diagnostic_only": _to_bool(latest.get("diagnostic_only")),
        "latest_tiny_pit_admissibility_validator_synthetic_only": _to_bool(latest.get("synthetic_only")),
        "latest_tiny_pit_admissibility_validator_active_replay_input": False,
        "latest_tiny_pit_admissibility_validator_active_replay_ready": False,
        "latest_tiny_pit_admissibility_validator_trading_allowed": False,
        "recommended_next_task": VIEWS_NEXT_ACTION if health_status == "PASS" else "Repair Tiny PIT validator artifacts.",
        **{flag: False for flag in SAFETY_FALSE_FLAGS},
    }
    return summary


def _no_artifact_summary(health_status: str) -> dict[str, Any]:
    return {
        "latest_tiny_pit_admissibility_validator_id": "",
        "latest_tiny_pit_admissibility_validator_status": "NO_INPUT",
        "latest_tiny_pit_admissibility_validator_health_status": health_status,
        "latest_tiny_pit_admissibility_validator_workflow_stage": NO_TINY_PIT_ADMISSIBILITY_VALIDATOR,
        "latest_tiny_pit_admissibility_validator_artifact_path": "",
        "latest_tiny_pit_admissibility_validator_report_path": "",
        "latest_tiny_pit_admissibility_validator_case_count": 0,
        "latest_tiny_pit_admissibility_validator_pass_candidate_count": 0,
        "latest_tiny_pit_admissibility_validator_warning_count": 0,
        "latest_tiny_pit_admissibility_validator_blocker_count": 0,
        "latest_tiny_pit_admissibility_validator_report_only": True,
        "latest_tiny_pit_admissibility_validator_diagnostic_only": True,
        "latest_tiny_pit_admissibility_validator_synthetic_only": True,
        "latest_tiny_pit_admissibility_validator_active_replay_input": False,
        "latest_tiny_pit_admissibility_validator_active_replay_ready": False,
        "latest_tiny_pit_admissibility_validator_trading_allowed": False,
        "recommended_next_task": "Run tiny-pit-admissibility-validator to create report-only synthetic artifacts.",
        **{flag: False for flag in SAFETY_FALSE_FLAGS},
    }


def _write(result: TinyPitAdmissibilityValidatorStatusResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(result.artifact_paths["status_csv"], index=False)
    metadata = {
        column: result.summary_frame.iloc[0][column]
        for column in SUMMARY_COLUMNS
    }
    metadata["warnings"] = result.warnings
    metadata["output_files"] = {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"}
    result.artifact_paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _paths(output_dir: str | Path) -> dict[str, Path]:
    artifact_dir = Path(output_dir)
    return {
        "artifact_dir": artifact_dir,
        "status_csv": artifact_dir / "tiny_pit_admissibility_validator_status.csv",
        "metadata": artifact_dir / "metadata.json",
    }


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_json_safe(inner) for inner in value]
    if isinstance(value, Path):
        return str(value)
    if value.__class__.__module__.startswith("numpy") and hasattr(value, "item"):
        return value.item()
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return value
