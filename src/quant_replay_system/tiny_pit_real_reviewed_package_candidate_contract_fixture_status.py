"""Status view for Tiny PIT real reviewed package candidate contract fixture artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_real_reviewed_package_candidate_contract_fixture import SAFETY_FALSE_FLAGS
from quant_replay_system.tiny_pit_real_reviewed_package_candidate_contract_fixture_health import (
    check_tiny_pit_real_reviewed_package_candidate_contract_fixture_health,
)
from quant_replay_system.tiny_pit_real_reviewed_package_candidate_contract_fixture_index import (
    DEFAULT_ROOT,
    NO_TINY_PIT_REAL_REVIEWED_PACKAGE_CANDIDATE_CONTRACT_FIXTURE,
    build_tiny_pit_real_reviewed_package_candidate_contract_fixture_index,
)


VIEWS_NEXT_ACTION = (
    "Tiny PIT Real Reviewed Package Candidate Contract Fixture Post-Checkpoint Governance Audit "
    "Report-Only v0.1"
)

SUMMARY_COLUMNS = [
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_id",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_status",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_health_status",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_workflow_stage",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_artifact_path",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_report_path",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_case_count",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_pass_candidate_count",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_warn_count",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_fail_count",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_blocker_count",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_warning_count",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_report_only",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_diagnostic_only",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_synthetic_only",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_real_reviewed_csv_package_created",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_active_reviewed_input_candidate_created",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_real_replay_input_created",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_active_replay_input",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_active_replay_ready",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_active_replay_input_ready_emitted",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_replay_execution_allowed",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_trading_allowed",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_buy_review_allowed",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_data_raw_written",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_data_processed_written",
    "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_data_cache_written",
    "recommended_next_task",
    *SAFETY_FALSE_FLAGS,
]


@dataclass(frozen=True)
class TinyPitRealReviewedPackageCandidateContractFixtureStatusResult:
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_id: str
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_status: str
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_health_status: str
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_workflow_stage: str
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_artifact_path: str
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_report_path: str
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_case_count: int
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_pass_candidate_count: int
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_warn_count: int
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_fail_count: int
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_blocker_count: int
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_warning_count: int
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_report_only: bool
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_diagnostic_only: bool
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_synthetic_only: bool
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_real_reviewed_csv_package_created: bool
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_active_reviewed_input_candidate_created: bool
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_real_replay_input_created: bool
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_active_replay_input: bool
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_active_replay_ready: bool
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_active_replay_input_ready_emitted: bool
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_replay_execution_allowed: bool
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_trading_allowed: bool
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_buy_review_allowed: bool
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_data_raw_written: bool
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_data_processed_written: bool
    latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_data_cache_written: bool
    recommended_next_task: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    real_reviewed_csv_package_created: bool
    active_reviewed_input_candidate_created: bool
    real_replay_input_created: bool
    active_replay_input: bool
    active_replay_ready: bool
    active_replay_input_ready_emitted: bool
    replay_execution_allowed: bool
    replay_decisions_created: bool
    forward_labels_created: bool
    future_labels_joined: bool
    training_allowed: bool
    training_dataset_created: bool
    metric_computation_performed: bool
    signal_score_implemented: bool
    model_training_performed: bool
    active_weights_created: bool
    active_thresholds_created: bool
    stock_profile_allowed: bool
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


def run_tiny_pit_real_reviewed_package_candidate_contract_fixture_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/status",
) -> TinyPitRealReviewedPackageCandidateContractFixtureStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_tiny_pit_real_reviewed_package_candidate_contract_fixture_index(root=root, output_dir=sibling_root / "index")
    health = check_tiny_pit_real_reviewed_package_candidate_contract_fixture_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        summary = _no_artifact_summary(health.status)
    else:
        latest = index.index_frame.sort_values(["created_at", "fixture_id"]).iloc[-1].to_dict()
        summary = _summary_from_latest(latest, health.status)
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    result = TinyPitRealReviewedPackageCandidateContractFixtureStatusResult(
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health.status == "PASS" else [f"Tiny PIT real reviewed package candidate contract fixture health is {health.status}."],
        **summary,
    )
    _write(result)
    return result


def _summary_from_latest(latest: dict[str, Any], health_status: str) -> dict[str, Any]:
    status = "FAIL" if health_status == "FAIL" else _text(latest.get("status"))
    return {
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_id": _text(latest.get("fixture_id")),
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_status": status,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_health_status": health_status,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_workflow_stage": _text(latest.get("workflow_stage")),
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_artifact_path": _text(latest.get("artifact_path")),
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_report_path": _text(latest.get("report_path")),
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_case_count": _to_int(latest.get("case_count")),
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_pass_candidate_count": _to_int(latest.get("pass_candidate_count")),
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_warn_count": _to_int(latest.get("warn_count")),
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_fail_count": _to_int(latest.get("fail_count")),
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_blocker_count": _to_int(latest.get("blocker_count")),
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_warning_count": _to_int(latest.get("warning_count")),
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_report_only": _to_bool(latest.get("report_only")),
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_diagnostic_only": _to_bool(latest.get("diagnostic_only")),
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_synthetic_only": _to_bool(latest.get("synthetic_only")),
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_real_reviewed_csv_package_created": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_active_reviewed_input_candidate_created": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_real_replay_input_created": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_active_replay_input": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_active_replay_ready": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_active_replay_input_ready_emitted": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_replay_execution_allowed": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_trading_allowed": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_buy_review_allowed": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_data_raw_written": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_data_processed_written": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_data_cache_written": False,
        "recommended_next_task": VIEWS_NEXT_ACTION if health_status == "PASS" else "Repair Tiny PIT real reviewed package candidate contract fixture artifacts.",
        **{flag: False for flag in SAFETY_FALSE_FLAGS},
    }


def _no_artifact_summary(health_status: str) -> dict[str, Any]:
    return {
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_id": "",
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_status": "NO_REAL_REVIEWED_PACKAGE_CANDIDATE",
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_health_status": health_status,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_workflow_stage": NO_TINY_PIT_REAL_REVIEWED_PACKAGE_CANDIDATE_CONTRACT_FIXTURE,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_artifact_path": "",
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_report_path": "",
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_case_count": 0,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_pass_candidate_count": 0,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_warn_count": 0,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_fail_count": 0,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_blocker_count": 0,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_warning_count": 0,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_report_only": True,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_diagnostic_only": True,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_synthetic_only": True,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_real_reviewed_csv_package_created": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_active_reviewed_input_candidate_created": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_real_replay_input_created": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_active_replay_input": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_active_replay_ready": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_active_replay_input_ready_emitted": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_replay_execution_allowed": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_trading_allowed": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_buy_review_allowed": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_data_raw_written": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_data_processed_written": False,
        "latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_data_cache_written": False,
        "recommended_next_task": "Run tiny-pit-real-reviewed-package-candidate-contract-fixture to create report-only synthetic artifacts.",
        **{flag: False for flag in SAFETY_FALSE_FLAGS},
    }


def _write(result: TinyPitRealReviewedPackageCandidateContractFixtureStatusResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(result.artifact_paths["status_csv"], index=False)
    metadata = {
        "status": result.latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_status,
        "health_status": result.latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_health_status,
        "workflow_stage": result.latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_workflow_stage,
        "latest_fixture_id": result.latest_tiny_pit_real_reviewed_package_candidate_contract_fixture_id,
        "recommended_next_task": result.recommended_next_task,
        "report_only": True,
        "diagnostic_only": True,
        "synthetic_only": True,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
    }
    metadata.update({flag: False for flag in SAFETY_FALSE_FLAGS})
    result.artifact_paths["metadata"].write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _paths(output_dir: str | Path) -> dict[str, Path]:
    artifact_dir = Path(output_dir)
    return {
        "artifact_dir": artifact_dir,
        "status_csv": artifact_dir / "tiny_pit_real_reviewed_package_candidate_contract_fixture_status.csv",
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


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
