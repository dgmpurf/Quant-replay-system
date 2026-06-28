"""Status view for reviewed LOCAL_CSV replay prototype input contract fixture artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.reviewed_local_csv_replay_prototype_input_contract_fixture import SAFETY_FALSE_FLAGS
from quant_replay_system.reviewed_local_csv_replay_prototype_input_contract_fixture_health import (
    check_reviewed_local_csv_replay_prototype_input_contract_fixture_health,
)
from quant_replay_system.reviewed_local_csv_replay_prototype_input_contract_fixture_index import (
    NO_REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE,
    REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED,
    REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_INVALID,
    build_reviewed_local_csv_replay_prototype_input_contract_fixture_index,
)


SUMMARY_COLUMNS = [
    "latest_run_id",
    "status",
    "workflow_stage",
    "health_status",
    "contract_count",
    "validation_issue_count",
    "report_only",
    "diagnostic_only",
    "schema_fixture",
    *SAFETY_FALSE_FLAGS,
    "report_path",
    "next_action",
]

VIEWS_NEXT_ACTION = (
    "Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture Post-Checkpoint Governance Audit Report-Only v0.1"
)


@dataclass(frozen=True)
class ReviewedLocalCsvReplayPrototypeInputContractFixtureStatusResult:
    latest_run_id: str
    status: str
    workflow_stage: str
    health_status: str
    contract_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    schema_fixture: bool
    real_reviewed_input_package_created: bool
    active_reviewed_input_candidate_created: bool
    pit_admissibility_validator_implemented: bool
    real_replay_input_created: bool
    real_replay_evidence_bundle_created: bool
    real_replay_decision_created: bool
    replay_decision_frozen: bool
    real_forward_labels_created: bool
    future_labels_joined: bool
    future_label_joined_to_decision_input: bool
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
    current_candidates_run: bool
    snapshot_built: bool
    signal_semantics_changed: bool
    broker_api_called: bool
    external_api_called: bool
    llm_api_called: bool
    message_sent: bool
    order_placed: bool
    trading_allowed: bool
    data_raw_written: bool
    data_processed_written: bool
    data_cache_written: bool
    report_path: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_reviewed_local_csv_replay_prototype_input_contract_fixture_status(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/reviewed_local_csv_replay_prototype_input_contract_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/reviewed_local_csv_replay_prototype_input_contract_fixture_v0_1/status",
) -> ReviewedLocalCsvReplayPrototypeInputContractFixtureStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_reviewed_local_csv_replay_prototype_input_contract_fixture_index(root=root, output_dir=sibling_root / "index")
    health = check_reviewed_local_csv_replay_prototype_input_contract_fixture_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root)
    else:
        latest = index.index_frame.sort_values(
            ["created_at", "reviewed_local_csv_replay_prototype_input_contract_fixture_id"]
        ).iloc[-1].to_dict()
        if health.status == "FAIL":
            result = _result_from_latest(
                latest,
                status="FAIL",
                stage=REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_INVALID,
                health_status=health.status,
                next_action=(
                    "Repair reviewed LOCAL_CSV input contract fixture artifacts before relying on view context. "
                    "This remains report-only and creates no real reviewed input package, PIT validator, replay, labels, "
                    "training, stock_profile, paper validation, buy-review, performance validation, or trading."
                ),
                output_dir=output_dir,
                root=root,
            )
        else:
            result = _result_from_latest(
                latest,
                status="PASS",
                stage=REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED,
                health_status=health.status,
                next_action=VIEWS_NEXT_ACTION,
                output_dir=output_dir,
                root=root,
            )
    _write(result)
    return result


def _result_from_latest(
    latest: dict[str, Any],
    *,
    status: str,
    stage: str,
    health_status: str,
    next_action: str,
    output_dir: str | Path,
    root: str | Path,
) -> ReviewedLocalCsvReplayPrototypeInputContractFixtureStatusResult:
    summary = {
        "latest_run_id": _text(latest.get("reviewed_local_csv_replay_prototype_input_contract_fixture_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health_status,
        "contract_count": _to_int(latest.get("contract_count")),
        "validation_issue_count": _to_int(latest.get("validation_issue_count")),
        "report_only": _to_bool(latest.get("report_only")),
        "diagnostic_only": _to_bool(latest.get("diagnostic_only")),
        "schema_fixture": _to_bool(latest.get("schema_fixture")),
        **{flag: _to_bool(latest.get(flag)) for flag in SAFETY_FALSE_FLAGS},
        "report_path": _text(latest.get("report_path")),
        "next_action": next_action,
    }
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return ReviewedLocalCsvReplayPrototypeInputContractFixtureStatusResult(
        latest_run_id=summary["latest_run_id"],
        status=status,
        workflow_stage=stage,
        health_status=health_status,
        contract_count=summary["contract_count"],
        validation_issue_count=summary["validation_issue_count"],
        report_only=summary["report_only"],
        diagnostic_only=summary["diagnostic_only"],
        schema_fixture=summary["schema_fixture"],
        report_path=summary["report_path"],
        next_action=next_action,
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health_status == "PASS" else [f"Reviewed LOCAL_CSV contract fixture health is {health_status}."],
        audit_metadata=_audit_metadata(root),
        **{flag: summary[flag] for flag in SAFETY_FALSE_FLAGS},
    )


def _no_artifact_result(
    output_dir: str | Path,
    root: str | Path,
) -> ReviewedLocalCsvReplayPrototypeInputContractFixtureStatusResult:
    summary = {
        "latest_run_id": "",
        "status": "NO_INPUT",
        "workflow_stage": NO_REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE,
        "health_status": "PASS",
        "contract_count": 0,
        "validation_issue_count": 0,
        "report_only": True,
        "diagnostic_only": True,
        "schema_fixture": False,
        **{flag: False for flag in SAFETY_FALSE_FLAGS},
        "report_path": "",
        "next_action": "Run reviewed-local-csv-replay-prototype-input-contract-fixture to create report-only contract artifacts.",
    }
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return ReviewedLocalCsvReplayPrototypeInputContractFixtureStatusResult(
        latest_run_id="",
        status="NO_INPUT",
        workflow_stage=NO_REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE,
        health_status="PASS",
        contract_count=0,
        validation_issue_count=0,
        report_only=True,
        diagnostic_only=True,
        schema_fixture=False,
        report_path="",
        next_action=summary["next_action"],
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[f"No reviewed LOCAL_CSV contract fixture artifacts found under {root}."],
        audit_metadata=_audit_metadata(root),
        **{flag: False for flag in SAFETY_FALSE_FLAGS},
    )


def _write(result: ReviewedLocalCsvReplayPrototypeInputContractFixtureStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture Status",
                "",
                f"- status: {result.status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_run_id: {result.latest_run_id}",
                f"- health_status: {result.health_status}",
                f"- contract_count: {result.contract_count}",
                f"- validation_issue_count: {result.validation_issue_count}",
                "",
                "This is a report-only status view. It does not create real reviewed input packages, PIT validators, replay inputs, evidence bundles, decisions, freezes, forward labels, future-label joins, training datasets, metrics, signal_score, models, stock_profile validation, paper validation, buy-review, performance validation, current-candidates, snapshots, signal_semantics mutation, broker/API/order/message behavior, trading, or data writes.",
                "",
                f"Next action: {result.next_action}",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "latest_run_id": result.latest_run_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "health_status": result.health_status,
        "contract_count": result.contract_count,
        "validation_issue_count": result.validation_issue_count,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
        "schema_fixture": result.schema_fixture,
        **{flag: getattr(result, flag) for flag in SAFETY_FALSE_FLAGS},
        "report_path": result.report_path,
        "next_action": result.next_action,
        "warnings": result.warnings,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")


def _paths(output_dir: str | Path) -> dict[str, Path]:
    artifact_dir = Path(output_dir)
    return {
        "artifact_dir": artifact_dir,
        "status_csv": artifact_dir / "reviewed_local_csv_replay_prototype_input_contract_fixture_status.csv",
        "status_report": artifact_dir / "reviewed_local_csv_replay_prototype_input_contract_fixture_status_report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def _audit_metadata(root: str | Path) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "report_only": True,
        "diagnostic_only": True,
        "reviewed_local_csv_replay_prototype_input_contract_fixture_status_created": True,
        **{flag: False for flag in SAFETY_FALSE_FLAGS},
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _to_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
