"""Status view for Tiny PIT real reviewed LOCAL_CSV preflight fixture artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture import (
    SAFETY_FALSE_FLAGS,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_health import (
    check_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_index import (
    DEFAULT_ROOT,
    NO_TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_CONTRACT_FIXTURE,
    build_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_index,
)


VIEWS_NEXT_ACTION = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Contract Fixture "
    "Research-Status and Checkpoint Report-Only v0.1"
)

PREFIX = "latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture"

SUMMARY_COLUMNS = [
    f"{PREFIX}_id",
    f"{PREFIX}_status",
    f"{PREFIX}_health_status",
    f"{PREFIX}_workflow_stage",
    f"{PREFIX}_artifact_path",
    f"{PREFIX}_report_path",
    f"{PREFIX}_case_count",
    f"{PREFIX}_pass_candidate_count",
    f"{PREFIX}_warn_count",
    f"{PREFIX}_fail_count",
    f"{PREFIX}_blocker_count",
    f"{PREFIX}_warning_count",
    f"{PREFIX}_report_only",
    f"{PREFIX}_diagnostic_only",
    f"{PREFIX}_synthetic_only",
    f"{PREFIX}_real_csv_required",
    f"{PREFIX}_real_csv_consumed",
    f"{PREFIX}_real_reviewed_csv_package_created",
    f"{PREFIX}_real_package_candidate_created",
    f"{PREFIX}_active_reviewed_input_candidate_created",
    f"{PREFIX}_real_replay_input_created",
    f"{PREFIX}_active_replay_input",
    f"{PREFIX}_active_replay_ready",
    f"{PREFIX}_active_replay_input_ready_emitted",
    f"{PREFIX}_replay_execution_allowed",
    f"{PREFIX}_trading_allowed",
    f"{PREFIX}_buy_review_allowed",
    f"{PREFIX}_data_raw_written",
    f"{PREFIX}_data_processed_written",
    f"{PREFIX}_data_cache_written",
    "recommended_next_task",
    *SAFETY_FALSE_FLAGS,
]


@dataclass(frozen=True)
class TinyPitRealReviewedLocalCsvPackageCandidatePreflightContractFixtureStatusResult:
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_id: str
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_status: str
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_health_status: str
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_workflow_stage: str
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifact_path: str
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_report_path: str
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_case_count: int
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_pass_candidate_count: int
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_warn_count: int
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_fail_count: int
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_blocker_count: int
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_warning_count: int
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_report_only: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_diagnostic_only: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_synthetic_only: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_real_csv_required: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_real_csv_consumed: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_real_reviewed_csv_package_created: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_real_package_candidate_created: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_active_reviewed_input_candidate_created: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_real_replay_input_created: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_active_replay_input: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_active_replay_ready: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_active_replay_input_ready_emitted: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_replay_execution_allowed: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_trading_allowed: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_buy_review_allowed: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_data_raw_written: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_data_processed_written: bool
    latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_data_cache_written: bool
    recommended_next_task: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    real_csv_required: bool
    real_csv_consumed: bool
    real_reviewed_csv_package_created: bool
    real_package_candidate_created: bool
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
    signal_score_input_authorized: bool
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


def run_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/status",
) -> TinyPitRealReviewedLocalCsvPackageCandidatePreflightContractFixtureStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_index(
        root=root,
        output_dir=sibling_root / "index",
    )
    health = check_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_health(
        root=root,
        output_dir=sibling_root / "health",
    )
    if index.index_frame.empty:
        summary = _no_artifact_summary(health.status)
    else:
        latest = index.index_frame.sort_values(["created_at", "fixture_id"]).iloc[-1].to_dict()
        summary = _summary_from_latest(latest, health.status)
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    result = TinyPitRealReviewedLocalCsvPackageCandidatePreflightContractFixtureStatusResult(
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health.status == "PASS" else [f"Tiny PIT LOCAL_CSV preflight health is {health.status}."],
        **summary,
    )
    _write(result)
    return result


def _summary_from_latest(latest: dict[str, Any], health_status: str) -> dict[str, Any]:
    status = "FAIL" if health_status == "FAIL" else _text(latest.get("status"))
    return {
        f"{PREFIX}_id": _text(latest.get("fixture_id")),
        f"{PREFIX}_status": status,
        f"{PREFIX}_health_status": health_status,
        f"{PREFIX}_workflow_stage": _text(latest.get("workflow_stage")),
        f"{PREFIX}_artifact_path": _text(latest.get("artifact_path")),
        f"{PREFIX}_report_path": _text(latest.get("report_path")),
        f"{PREFIX}_case_count": _to_int(latest.get("case_count")),
        f"{PREFIX}_pass_candidate_count": _to_int(latest.get("pass_candidate_count")),
        f"{PREFIX}_warn_count": _to_int(latest.get("warn_count")),
        f"{PREFIX}_fail_count": _to_int(latest.get("fail_count")),
        f"{PREFIX}_blocker_count": _to_int(latest.get("blocker_count")),
        f"{PREFIX}_warning_count": _to_int(latest.get("warning_count")),
        f"{PREFIX}_report_only": _to_bool(latest.get("report_only")),
        f"{PREFIX}_diagnostic_only": _to_bool(latest.get("diagnostic_only")),
        f"{PREFIX}_synthetic_only": _to_bool(latest.get("synthetic_only")),
        f"{PREFIX}_real_csv_required": False,
        f"{PREFIX}_real_csv_consumed": False,
        f"{PREFIX}_real_reviewed_csv_package_created": False,
        f"{PREFIX}_real_package_candidate_created": False,
        f"{PREFIX}_active_reviewed_input_candidate_created": False,
        f"{PREFIX}_real_replay_input_created": False,
        f"{PREFIX}_active_replay_input": False,
        f"{PREFIX}_active_replay_ready": False,
        f"{PREFIX}_active_replay_input_ready_emitted": False,
        f"{PREFIX}_replay_execution_allowed": False,
        f"{PREFIX}_trading_allowed": False,
        f"{PREFIX}_buy_review_allowed": False,
        f"{PREFIX}_data_raw_written": False,
        f"{PREFIX}_data_processed_written": False,
        f"{PREFIX}_data_cache_written": False,
        "recommended_next_task": VIEWS_NEXT_ACTION if health_status == "PASS" else "Repair Tiny PIT LOCAL_CSV preflight fixture artifacts.",
        **{flag: False for flag in SAFETY_FALSE_FLAGS},
    }


def _no_artifact_summary(health_status: str) -> dict[str, Any]:
    return {
        f"{PREFIX}_id": "",
        f"{PREFIX}_status": "NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE",
        f"{PREFIX}_health_status": health_status,
        f"{PREFIX}_workflow_stage": NO_TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_CONTRACT_FIXTURE,
        f"{PREFIX}_artifact_path": "",
        f"{PREFIX}_report_path": "",
        f"{PREFIX}_case_count": 0,
        f"{PREFIX}_pass_candidate_count": 0,
        f"{PREFIX}_warn_count": 0,
        f"{PREFIX}_fail_count": 0,
        f"{PREFIX}_blocker_count": 0,
        f"{PREFIX}_warning_count": 0,
        f"{PREFIX}_report_only": True,
        f"{PREFIX}_diagnostic_only": True,
        f"{PREFIX}_synthetic_only": True,
        f"{PREFIX}_real_csv_required": False,
        f"{PREFIX}_real_csv_consumed": False,
        f"{PREFIX}_real_reviewed_csv_package_created": False,
        f"{PREFIX}_real_package_candidate_created": False,
        f"{PREFIX}_active_reviewed_input_candidate_created": False,
        f"{PREFIX}_real_replay_input_created": False,
        f"{PREFIX}_active_replay_input": False,
        f"{PREFIX}_active_replay_ready": False,
        f"{PREFIX}_active_replay_input_ready_emitted": False,
        f"{PREFIX}_replay_execution_allowed": False,
        f"{PREFIX}_trading_allowed": False,
        f"{PREFIX}_buy_review_allowed": False,
        f"{PREFIX}_data_raw_written": False,
        f"{PREFIX}_data_processed_written": False,
        f"{PREFIX}_data_cache_written": False,
        "recommended_next_task": (
            "Run tiny-pit-real-reviewed-local-csv-package-candidate-preflight-contract-fixture "
            "to create report-only synthetic artifacts."
        ),
        **{flag: False for flag in SAFETY_FALSE_FLAGS},
    }


def _write(result: TinyPitRealReviewedLocalCsvPackageCandidatePreflightContractFixtureStatusResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(result.artifact_paths["status_csv"], index=False)
    metadata = {
        "status": result.latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_status,
        "health_status": result.latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_health_status,
        "workflow_stage": result.latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_workflow_stage,
        "latest_fixture_id": result.latest_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_id,
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
        "status_csv": artifact_dir
        / "tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_status.csv",
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
