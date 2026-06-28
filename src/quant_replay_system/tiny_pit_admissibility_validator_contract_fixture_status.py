"""Status view for tiny PIT admissibility validator contract fixture artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_admissibility_validator_contract_fixture import SAFETY_FALSE_FLAGS
from quant_replay_system.tiny_pit_admissibility_validator_contract_fixture_health import (
    check_tiny_pit_admissibility_validator_contract_fixture_health,
)
from quant_replay_system.tiny_pit_admissibility_validator_contract_fixture_index import (
    NO_TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE,
    TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED,
    TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_INVALID,
    build_tiny_pit_admissibility_validator_contract_fixture_index,
)


SUMMARY_COLUMNS = [
    "latest_fixture_id",
    "status",
    "workflow_stage",
    "health_status",
    "case_count",
    "package_section_count",
    "gate_group_count",
    "timing_rule_count",
    "validation_issue_count",
    "report_only",
    "diagnostic_only",
    "contract_fixture",
    "forbidden_future_status_present",
    *SAFETY_FALSE_FLAGS,
    "artifact_path",
    "report_path",
    "next_action",
]

VIEWS_NEXT_ACTION = (
    "Tiny PIT Admissibility Validator Contract Fixture Post-Checkpoint Governance Audit Report-Only v0.1"
)


@dataclass(frozen=True)
class TinyPitAdmissibilityValidatorContractFixtureStatusResult:
    latest_fixture_id: str
    status: str
    workflow_stage: str
    health_status: str
    case_count: int
    package_section_count: int
    gate_group_count: int
    timing_rule_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    contract_fixture: bool
    forbidden_future_status_present: bool
    real_reviewed_csv_package_created: bool
    active_reviewed_input_candidate_created: bool
    pit_admissibility_validator_implemented: bool
    real_replay_input_created: bool
    real_replay_evidence_bundle_created: bool
    real_replay_decision_created: bool
    replay_decision_frozen: bool
    real_forward_labels_created: bool
    future_labels_joined: bool
    future_labels_joined_to_decision_inputs: bool
    future_labels_joined_to_training_dataset: bool
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
    order_placed: bool
    message_sent: bool
    trading_allowed: bool
    data_raw_written: bool
    data_processed_written: bool
    data_cache_written: bool
    artifact_path: str
    report_path: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_tiny_pit_admissibility_validator_contract_fixture_status(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/tiny_pit_admissibility_validator_contract_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/tiny_pit_admissibility_validator_contract_fixture_v0_1/status",
) -> TinyPitAdmissibilityValidatorContractFixtureStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_tiny_pit_admissibility_validator_contract_fixture_index(root=root, output_dir=sibling_root / "index")
    health = check_tiny_pit_admissibility_validator_contract_fixture_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root)
    else:
        latest = index.index_frame.sort_values(
            ["created_at", "tiny_pit_admissibility_validator_contract_fixture_id"]
        ).iloc[-1].to_dict()
        if health.status == "FAIL":
            result = _result_from_latest(
                latest,
                status="FAIL",
                stage=TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_INVALID,
                health_status=health.status,
                next_action=(
                    "Repair tiny PIT admissibility validator contract fixture artifacts before relying on view context. "
                    "This remains report-only and creates no real reviewed package, PIT validator, replay, labels, "
                    "training, stock_profile, paper validation, buy-review, performance validation, or trading."
                ),
                output_dir=output_dir,
                root=root,
            )
        else:
            result = _result_from_latest(
                latest,
                status="PASS",
                stage=TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED,
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
) -> TinyPitAdmissibilityValidatorContractFixtureStatusResult:
    summary = {
        "latest_fixture_id": _text(latest.get("tiny_pit_admissibility_validator_contract_fixture_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health_status,
        "case_count": _to_int(latest.get("case_count")),
        "package_section_count": _to_int(latest.get("package_section_count")),
        "gate_group_count": _to_int(latest.get("gate_group_count")),
        "timing_rule_count": _to_int(latest.get("timing_rule_count")),
        "validation_issue_count": _to_int(latest.get("validation_issue_count")),
        "report_only": _to_bool(latest.get("report_only")),
        "diagnostic_only": _to_bool(latest.get("diagnostic_only")),
        "contract_fixture": _to_bool(latest.get("contract_fixture")),
        "forbidden_future_status_present": _to_bool(latest.get("forbidden_future_status_present")),
        **{flag: _to_bool(latest.get(flag)) for flag in SAFETY_FALSE_FLAGS},
        "artifact_path": _text(latest.get("artifact_path")),
        "report_path": _text(latest.get("report_path")),
        "next_action": next_action,
    }
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return TinyPitAdmissibilityValidatorContractFixtureStatusResult(
        latest_fixture_id=summary["latest_fixture_id"],
        status=status,
        workflow_stage=stage,
        health_status=health_status,
        case_count=summary["case_count"],
        package_section_count=summary["package_section_count"],
        gate_group_count=summary["gate_group_count"],
        timing_rule_count=summary["timing_rule_count"],
        validation_issue_count=summary["validation_issue_count"],
        report_only=summary["report_only"],
        diagnostic_only=summary["diagnostic_only"],
        contract_fixture=summary["contract_fixture"],
        forbidden_future_status_present=summary["forbidden_future_status_present"],
        artifact_path=summary["artifact_path"],
        report_path=summary["report_path"],
        next_action=next_action,
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health_status == "PASS" else [f"Tiny PIT contract fixture health is {health_status}."],
        audit_metadata=_audit_metadata(root),
        **{flag: summary[flag] for flag in SAFETY_FALSE_FLAGS},
    )


def _no_artifact_result(
    output_dir: str | Path,
    root: str | Path,
) -> TinyPitAdmissibilityValidatorContractFixtureStatusResult:
    summary = {
        "latest_fixture_id": "",
        "status": "NO_INPUT",
        "workflow_stage": NO_TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE,
        "health_status": "PASS",
        "case_count": 0,
        "package_section_count": 0,
        "gate_group_count": 0,
        "timing_rule_count": 0,
        "validation_issue_count": 0,
        "report_only": True,
        "diagnostic_only": True,
        "contract_fixture": False,
        "forbidden_future_status_present": False,
        **{flag: False for flag in SAFETY_FALSE_FLAGS},
        "artifact_path": "",
        "report_path": "",
        "next_action": "Run tiny-pit-admissibility-validator-contract-fixture to create report-only contract artifacts.",
    }
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return TinyPitAdmissibilityValidatorContractFixtureStatusResult(
        latest_fixture_id="",
        status="NO_INPUT",
        workflow_stage=NO_TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE,
        health_status="PASS",
        case_count=0,
        package_section_count=0,
        gate_group_count=0,
        timing_rule_count=0,
        validation_issue_count=0,
        report_only=True,
        diagnostic_only=True,
        contract_fixture=False,
        forbidden_future_status_present=False,
        artifact_path="",
        report_path="",
        next_action=summary["next_action"],
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[f"No tiny PIT contract fixture artifacts found under {root}."],
        audit_metadata=_audit_metadata(root),
        **{flag: False for flag in SAFETY_FALSE_FLAGS},
    )


def _write(result: TinyPitAdmissibilityValidatorContractFixtureStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Tiny PIT Admissibility Validator Contract Fixture Status",
                "",
                f"- status: {result.status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_fixture_id: {result.latest_fixture_id}",
                f"- health_status: {result.health_status}",
                f"- case_count: {result.case_count}",
                f"- package_section_count: {result.package_section_count}",
                f"- gate_group_count: {result.gate_group_count}",
                f"- timing_rule_count: {result.timing_rule_count}",
                f"- validation_issue_count: {result.validation_issue_count}",
                f"- forbidden_future_status_present: {result.forbidden_future_status_present}",
                "",
                "This is a report-only status view. It does not create real reviewed CSV packages, active reviewed input candidates, PIT validators, replay inputs, evidence bundles, decisions, freezes, forward labels, future-label joins, training datasets, metrics, signal_score, models, stock_profile validation, paper validation, buy-review, performance validation, current-candidates, snapshots, signal_semantics mutation, broker/API/order/message behavior, trading, or data writes.",
                "",
                f"Next action: {result.next_action}",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "latest_fixture_id": result.latest_fixture_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "health_status": result.health_status,
        "case_count": result.case_count,
        "package_section_count": result.package_section_count,
        "gate_group_count": result.gate_group_count,
        "timing_rule_count": result.timing_rule_count,
        "validation_issue_count": result.validation_issue_count,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
        "contract_fixture": result.contract_fixture,
        "forbidden_future_status_present": result.forbidden_future_status_present,
        **{flag: getattr(result, flag) for flag in SAFETY_FALSE_FLAGS},
        "artifact_path": result.artifact_path,
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
        "status_csv": artifact_dir / "tiny_pit_admissibility_validator_contract_fixture_status.csv",
        "status_report": artifact_dir / "tiny_pit_admissibility_validator_contract_fixture_status_report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def _audit_metadata(root: str | Path) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "report_only": True,
        "diagnostic_only": True,
        "tiny_pit_admissibility_validator_contract_fixture_status_created": True,
        **{flag: False for flag in SAFETY_FALSE_FLAGS},
    }


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


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
    return value
