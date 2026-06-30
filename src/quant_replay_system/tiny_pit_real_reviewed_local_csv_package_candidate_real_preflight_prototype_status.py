"""Status view for manifest-only Tiny PIT real reviewed LOCAL_CSV preflight artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype import (
    REQUIRED_FALSE_FLAGS,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_health import (
    check_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_index import (
    DEFAULT_ROOT,
    build_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_index,
)


VIEWS_NEXT_ACTION = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Manifest-Only Preflight Prototype "
    "Research-Status and Checkpoint Report-Only v0.1"
)
NO_ARTIFACT_STAGE = "NO_TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_MANIFEST_ONLY_PREFLIGHT_PROTOTYPE"
PREFIX = "latest_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype"


@dataclass(frozen=True)
class TinyPitRealReviewedLocalCsvPackageCandidateRealPreflightPrototypeStatusResult:
    latest_run_id: str
    latest_runtime_status: str
    latest_health_status: str
    latest_workflow_stage: str
    latest_artifact_path: str
    latest_report_path: str
    csv_read_level: str
    report_only: bool
    diagnostic_only: bool
    synthetic_only: bool
    real_manifest_read: bool
    references_followed: bool
    local_file_hash_computed: bool
    external_source_validated: bool
    pit_admissibility_validated: bool
    recommended_next_task: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    real_csv_consumed: bool
    real_reviewed_csv_package_created: bool
    real_package_candidate_created: bool
    active_reviewed_input_candidate_created: bool
    real_replay_input_created: bool
    active_replay_input: bool
    active_replay_ready: bool
    active_replay_input_ready_emitted: bool
    replay_execution_allowed: bool
    replay_evidence_bundle_created: bool
    replay_decision_created: bool
    replay_decision_freeze_created: bool
    forward_labels_created: bool
    future_labels_joined: bool
    training_dataset_created: bool
    metric_computation_performed: bool
    signal_score_implemented: bool
    signal_score_input_authorized: bool
    model_training_performed: bool
    active_weights_created: bool
    active_thresholds_created: bool
    stock_profile_validation_created: bool
    paper_validation_created: bool
    real_buy_review_eligible: bool
    buy_review_allowed: bool
    strategy_performance_validated: bool
    current_candidates_created: bool
    snapshots_created: bool
    signal_semantics_mutated: bool
    broker_api_called: bool
    order_placed: bool
    message_sent: bool
    external_api_called: bool
    llm_api_called: bool
    trading_allowed: bool
    data_raw_written: bool
    data_processed_written: bool
    data_cache_written: bool


def run_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/status",
) -> TinyPitRealReviewedLocalCsvPackageCandidateRealPreflightPrototypeStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_index(
        root=root,
        output_dir=sibling_root / "index",
    )
    health = check_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_health(
        root=root,
        output_dir=sibling_root / "health",
    )
    if index.index_frame.empty:
        summary = _no_artifact_summary(health.status)
    else:
        latest = index.index_frame.sort_values(["created_at", "run_id"]).iloc[-1].to_dict()
        summary = _summary_from_latest(latest, health.status)
    paths = _paths(output_dir)
    frame = pd.DataFrame([_prefixed_summary(summary)])
    result = TinyPitRealReviewedLocalCsvPackageCandidateRealPreflightPrototypeStatusResult(
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health.status == "PASS" else [f"Tiny PIT manifest-only preflight health is {health.status}."],
        **summary,
    )
    _write(result)
    return result


def _summary_from_latest(latest: dict[str, Any], health_status: str) -> dict[str, Any]:
    runtime_status = "FAIL" if health_status == "FAIL" else _text(latest.get("runtime_status"))
    return {
        "latest_run_id": _text(latest.get("run_id")),
        "latest_runtime_status": runtime_status,
        "latest_health_status": health_status,
        "latest_workflow_stage": _text(latest.get("workflow_stage")),
        "latest_artifact_path": _text(latest.get("artifact_path")),
        "latest_report_path": _text(latest.get("report_path")),
        "csv_read_level": _text(latest.get("csv_read_level")) or "CSV_READ_NONE",
        "report_only": _to_bool(latest.get("report_only")),
        "diagnostic_only": _to_bool(latest.get("diagnostic_only")),
        "synthetic_only": _to_bool(latest.get("synthetic_only")),
        "real_manifest_read": _to_bool(latest.get("real_manifest_read")),
        "references_followed": False,
        "local_file_hash_computed": False,
        "external_source_validated": False,
        "pit_admissibility_validated": False,
        "recommended_next_task": VIEWS_NEXT_ACTION if health_status == "PASS" else "Repair Tiny PIT manifest-only preflight artifacts.",
        **{flag: False for flag in REQUIRED_FALSE_FLAGS},
    }


def _no_artifact_summary(health_status: str) -> dict[str, Any]:
    return {
        "latest_run_id": "",
        "latest_runtime_status": "NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_INPUT",
        "latest_health_status": health_status,
        "latest_workflow_stage": NO_ARTIFACT_STAGE,
        "latest_artifact_path": "",
        "latest_report_path": "",
        "csv_read_level": "CSV_READ_NONE",
        "report_only": True,
        "diagnostic_only": True,
        "synthetic_only": True,
        "real_manifest_read": False,
        "references_followed": False,
        "local_file_hash_computed": False,
        "external_source_validated": False,
        "pit_admissibility_validated": False,
        "recommended_next_task": "Run manifest-only preflight prototype no-input report-only command.",
        **{flag: False for flag in REQUIRED_FALSE_FLAGS},
    }


def _prefixed_summary(summary: dict[str, Any]) -> dict[str, Any]:
    row = {f"{PREFIX}_{key.removeprefix('latest_')}": value for key, value in summary.items() if key.startswith("latest_")}
    for key, value in summary.items():
        if not key.startswith("latest_"):
            row[key] = value
    return row


def _write(result: TinyPitRealReviewedLocalCsvPackageCandidateRealPreflightPrototypeStatusResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(result.artifact_paths["status_csv"], index=False)
    metadata = {
        "latest_run_id": result.latest_run_id,
        "runtime_status": result.latest_runtime_status,
        "health_status": result.latest_health_status,
        "workflow_stage": result.latest_workflow_stage,
        "recommended_next_task": result.recommended_next_task,
        "report_only": True,
        "diagnostic_only": True,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
    }
    metadata.update({flag: False for flag in REQUIRED_FALSE_FLAGS})
    result.artifact_paths["metadata"].write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _paths(output_dir: str | Path) -> dict[str, Path]:
    artifact_dir = Path(output_dir)
    return {
        "artifact_dir": artifact_dir,
        "status_csv": artifact_dir / "tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_status.csv",
        "metadata": artifact_dir / "metadata.json",
    }


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)

