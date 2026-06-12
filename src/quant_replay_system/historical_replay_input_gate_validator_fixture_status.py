"""Status summary for report-only historical replay input gate validator fixtures."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.historical_replay_input_gate_validator_fixture_health import (
    check_historical_replay_input_gate_validator_fixture_health,
)
from quant_replay_system.historical_replay_input_gate_validator_fixture_index import (
    build_historical_replay_input_gate_validator_fixture_index,
)


NO_FIXTURE_FOUND = "NO_FIXTURE_FOUND"
INPUT_GATE_VALIDATOR_FIXTURE_READY = "INPUT_GATE_VALIDATOR_FIXTURE_READY"
INPUT_GATE_VALIDATOR_FIXTURE_BLOCKED = "INPUT_GATE_VALIDATOR_FIXTURE_BLOCKED"

SUMMARY_COLUMNS = [
    "latest_fixture_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "case_count",
    "blocked_case_count",
    "pass_candidate_case_count",
    "active_ready_case_count",
    "validation_issue_count",
    "overclaim_guard_pass_count",
    "overclaim_guard_total_count",
    "active_replay_input",
    "forward_labels_exist",
    "weights_trained",
    "active_stock_profile_exists",
    "real_buy_review_eligible",
    "report_only",
    "diagnostic_only",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "validator_implemented",
    "active_ready_status_allowed",
    "report_path",
    "safety_statement",
    "next_manual_action",
]


@dataclass(frozen=True)
class HistoricalReplayInputGateValidatorFixtureStatusResult:
    latest_fixture_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    case_count: int
    blocked_case_count: int
    pass_candidate_case_count: int
    active_ready_case_count: int
    validation_issue_count: int
    overclaim_guard_pass_count: int
    overclaim_guard_total_count: int
    active_replay_input: bool
    forward_labels_exist: bool
    weights_trained: bool
    active_stock_profile_exists: bool
    real_buy_review_eligible: bool
    report_only: bool
    diagnostic_only: bool
    no_live_trading: bool
    no_broker_api: bool
    no_order_placement: bool
    no_message_sent: bool
    llm_api_called: bool
    external_api_called: bool
    cache_mutated: bool
    current_candidates_run: bool
    snapshot_built: bool
    signal_semantics_changed: bool
    validator_implemented: bool
    active_ready_status_allowed: bool
    report_path: str
    safety_statement: str
    next_manual_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_historical_replay_input_gate_validator_fixture_status(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1/status",
) -> HistoricalReplayInputGateValidatorFixtureStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_historical_replay_input_gate_validator_fixture_index(root=root, output_dir=sibling_root / "index")
    health = check_historical_replay_input_gate_validator_fixture_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_fixture_result(output_dir, root, health.status)
    else:
        latest = index.index_frame.sort_values(["generated_at", "fixture_run_id"]).iloc[-1].to_dict()
        stage = INPUT_GATE_VALIDATOR_FIXTURE_READY if health.status == "PASS" else INPUT_GATE_VALIDATOR_FIXTURE_BLOCKED
        status = "PASS" if health.status == "PASS" else "FAIL"
        result = _result_from_latest(latest, status, health.status, stage, output_dir, root)
    _write(result)
    return result


def _result_from_latest(
    latest: dict[str, Any],
    status: str,
    health_status: str,
    stage: str,
    output_dir: str | Path,
    root: str | Path,
) -> HistoricalReplayInputGateValidatorFixtureStatusResult:
    summary = {
        "latest_fixture_run_id": _text(latest.get("fixture_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "case_count": _to_int(latest.get("case_count")),
        "blocked_case_count": _to_int(latest.get("blocked_case_count")),
        "pass_candidate_case_count": _to_int(latest.get("pass_candidate_case_count")),
        "active_ready_case_count": _to_int(latest.get("active_ready_case_count")),
        "validation_issue_count": _to_int(latest.get("validation_issue_count")),
        "overclaim_guard_pass_count": _to_int(latest.get("overclaim_guard_pass_count")),
        "overclaim_guard_total_count": _to_int(latest.get("overclaim_guard_total_count")),
        "active_replay_input": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
        "report_only": True,
        "diagnostic_only": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "llm_api_called": False,
        "external_api_called": False,
        "cache_mutated": False,
        "current_candidates_run": False,
        "snapshot_built": False,
        "signal_semantics_changed": False,
        "validator_implemented": False,
        "active_ready_status_allowed": False,
        "report_path": _text(latest.get("report_path")),
        "safety_statement": _safety_statement(),
        "next_manual_action": "Add research-status integration only after fixture index/health/status remain stable and explicitly scoped; do not implement the real validator or run replay.",
    }
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return HistoricalReplayInputGateValidatorFixtureStatusResult(
        latest_fixture_run_id=summary["latest_fixture_run_id"],
        status=status,
        health_status=health_status,
        workflow_stage=stage,
        case_count=summary["case_count"],
        blocked_case_count=summary["blocked_case_count"],
        pass_candidate_case_count=summary["pass_candidate_case_count"],
        active_ready_case_count=summary["active_ready_case_count"],
        validation_issue_count=summary["validation_issue_count"],
        overclaim_guard_pass_count=summary["overclaim_guard_pass_count"],
        overclaim_guard_total_count=summary["overclaim_guard_total_count"],
        active_replay_input=False,
        forward_labels_exist=False,
        weights_trained=False,
        active_stock_profile_exists=False,
        real_buy_review_eligible=False,
        report_only=True,
        diagnostic_only=True,
        no_live_trading=True,
        no_broker_api=True,
        no_order_placement=True,
        no_message_sent=True,
        llm_api_called=False,
        external_api_called=False,
        cache_mutated=False,
        current_candidates_run=False,
        snapshot_built=False,
        signal_semantics_changed=False,
        validator_implemented=False,
        active_ready_status_allowed=False,
        report_path=summary["report_path"],
        safety_statement=summary["safety_statement"],
        next_manual_action=summary["next_manual_action"],
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health_status == "PASS" else [f"Fixture health is {health_status}."],
        audit_metadata=_audit_metadata(root),
    )


def _no_fixture_result(output_dir: str | Path, root: str | Path, health_status: str) -> HistoricalReplayInputGateValidatorFixtureStatusResult:
    summary = {
        "latest_fixture_run_id": "",
        "status": "WARN",
        "health_status": health_status,
        "workflow_stage": NO_FIXTURE_FOUND,
        "case_count": 0,
        "blocked_case_count": 0,
        "pass_candidate_case_count": 0,
        "active_ready_case_count": 0,
        "validation_issue_count": 0,
        "overclaim_guard_pass_count": 0,
        "overclaim_guard_total_count": 0,
        "active_replay_input": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
        "report_only": True,
        "diagnostic_only": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "llm_api_called": False,
        "external_api_called": False,
        "cache_mutated": False,
        "current_candidates_run": False,
        "snapshot_built": False,
        "signal_semantics_changed": False,
        "validator_implemented": False,
        "active_ready_status_allowed": False,
        "report_path": "",
        "safety_statement": _safety_statement(),
        "next_manual_action": "Run historical-replay-input-gate-validator-fixture to create report-only fixture artifacts.",
    }
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return HistoricalReplayInputGateValidatorFixtureStatusResult(
        latest_fixture_run_id="",
        status="WARN",
        health_status=health_status,
        workflow_stage=NO_FIXTURE_FOUND,
        case_count=0,
        blocked_case_count=0,
        pass_candidate_case_count=0,
        active_ready_case_count=0,
        validation_issue_count=0,
        overclaim_guard_pass_count=0,
        overclaim_guard_total_count=0,
        active_replay_input=False,
        forward_labels_exist=False,
        weights_trained=False,
        active_stock_profile_exists=False,
        real_buy_review_eligible=False,
        report_only=True,
        diagnostic_only=True,
        no_live_trading=True,
        no_broker_api=True,
        no_order_placement=True,
        no_message_sent=True,
        llm_api_called=False,
        external_api_called=False,
        cache_mutated=False,
        current_candidates_run=False,
        snapshot_built=False,
        signal_semantics_changed=False,
        validator_implemented=False,
        active_ready_status_allowed=False,
        report_path="",
        safety_statement=summary["safety_statement"],
        next_manual_action=summary["next_manual_action"],
        summary_frame=frame,
        artifact_paths=paths,
        warnings=["No historical replay input gate validator fixture artifacts found."],
        audit_metadata=_audit_metadata(root),
    )


def _write(result: HistoricalReplayInputGateValidatorFixtureStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Historical Replay Input Gate Validator Fixture Status",
                "",
                f"- status: {result.status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- health_status: {result.health_status}",
                f"- latest_fixture_run_id: {result.latest_fixture_run_id}",
                f"- case_count: {result.case_count}",
                f"- pass_candidate_case_count: {result.pass_candidate_case_count}",
                f"- active_ready_case_count: {result.active_ready_case_count}",
                "",
                result.safety_statement,
                "",
                result.summary_frame.to_markdown(index=False),
            ]
        ),
        encoding="utf-8",
    )
    paths["metadata"].write_text(
        json.dumps(
            {
                "status": result.status,
                "workflow_stage": result.workflow_stage,
                "health_status": result.health_status,
                "latest_fixture_run_id": result.latest_fixture_run_id,
                "case_count": result.case_count,
                "blocked_case_count": result.blocked_case_count,
                "pass_candidate_case_count": result.pass_candidate_case_count,
                "active_ready_case_count": result.active_ready_case_count,
                "active_replay_input": result.active_replay_input,
                "forward_labels_exist": result.forward_labels_exist,
                "weights_trained": result.weights_trained,
                "active_stock_profile_exists": result.active_stock_profile_exists,
                "real_buy_review_eligible": result.real_buy_review_eligible,
                "report_only": result.report_only,
                "diagnostic_only": result.diagnostic_only,
                "safety_statement": result.safety_statement,
                "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
                **result.audit_metadata,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _paths(output_dir: str | Path) -> dict[str, Path]:
    return {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "historical_replay_input_gate_validator_fixture_status.csv",
        "status_report": Path(output_dir) / "historical_replay_input_gate_validator_fixture_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }


def _audit_metadata(root: str | Path) -> dict[str, Any]:
    return {
        "root": str(root),
        "report_only": True,
        "diagnostic_only": True,
        "active_replay_input": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
    }


def _safety_statement() -> str:
    return (
        "This fixture workflow is report-only. It is not the real validator. "
        "It is not real replay. It is not active replay input. "
        "It does not compute forward labels. It does not train weights. "
        "It does not create active stock profiles. It does not create real buy-review eligibility."
    )


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


__all__ = [
    "HistoricalReplayInputGateValidatorFixtureStatusResult",
    "INPUT_GATE_VALIDATOR_FIXTURE_BLOCKED",
    "INPUT_GATE_VALIDATOR_FIXTURE_READY",
    "NO_FIXTURE_FOUND",
    "run_historical_replay_input_gate_validator_fixture_status",
]
