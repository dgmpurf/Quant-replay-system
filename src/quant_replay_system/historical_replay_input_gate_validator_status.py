"""Status summary for report-only historical replay input gate validator artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.historical_replay_input_gate_validator import REPLAY_INPUT_GATE_PASS_CANDIDATE
from quant_replay_system.historical_replay_input_gate_validator_health import (
    check_historical_replay_input_gate_validator_health,
)
from quant_replay_system.historical_replay_input_gate_validator_index import (
    build_historical_replay_input_gate_validator_index,
)


NO_VALIDATOR_ARTIFACT_FOUND = "NO_VALIDATOR_ARTIFACT_FOUND"
INPUT_GATE_VALIDATOR_NO_INPUT = "INPUT_GATE_VALIDATOR_NO_INPUT"
INPUT_GATE_VALIDATOR_BLOCKED = "INPUT_GATE_VALIDATOR_BLOCKED"
INPUT_GATE_VALIDATOR_PASS_CANDIDATE = "INPUT_GATE_VALIDATOR_PASS_CANDIDATE"

SUMMARY_COLUMNS = [
    "latest_validator_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "pass_candidate",
    "active_replay_input_ready",
    "active_replay_input",
    "forward_labels_exist",
    "weights_trained",
    "active_stock_profile_exists",
    "real_buy_review_eligible",
    "blocker_count",
    "warning_count",
    "report_path",
    "safety_statement",
    "next_action",
]


@dataclass(frozen=True)
class HistoricalReplayInputGateValidatorStatusResult:
    latest_validator_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    pass_candidate: bool
    active_replay_input_ready: bool
    active_replay_input: bool
    forward_labels_exist: bool
    weights_trained: bool
    active_stock_profile_exists: bool
    real_buy_review_eligible: bool
    blocker_count: int
    warning_count: int
    report_path: str
    safety_statement: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_historical_replay_input_gate_validator_status(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_v0_1/status",
) -> HistoricalReplayInputGateValidatorStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_historical_replay_input_gate_validator_index(root=root, output_dir=sibling_root / "index")
    health = check_historical_replay_input_gate_validator_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status)
    else:
        latest = index.index_frame.sort_values(["generated_at", "validator_run_id"]).iloc[-1].to_dict()
        result = _result_from_latest(latest, health.status, output_dir, root)
    _write(result)
    return result


def _result_from_latest(
    latest: dict[str, Any],
    health_status: str,
    output_dir: str | Path,
    root: str | Path,
) -> HistoricalReplayInputGateValidatorStatusResult:
    status = _text(latest.get("status"))
    stage = _stage_for_status(status, health_status)
    summary = {
        "latest_validator_run_id": _text(latest.get("validator_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "pass_candidate": _to_bool(latest.get("pass_candidate")),
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
        "blocker_count": _to_int(latest.get("blocker_count")),
        "warning_count": _to_int(latest.get("warning_count")),
        "report_path": _text(latest.get("report_path")),
        "safety_statement": _safety_statement(),
        "next_action": _next_action(stage),
    }
    return _result(summary, output_dir, root, [])


def _no_artifact_result(
    output_dir: str | Path,
    root: str | Path,
    health_status: str,
) -> HistoricalReplayInputGateValidatorStatusResult:
    summary = {
        "latest_validator_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_VALIDATOR_ARTIFACT_FOUND,
        "pass_candidate": False,
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
        "blocker_count": 0,
        "warning_count": 0,
        "report_path": "",
        "safety_statement": _safety_statement(),
        "next_action": "Run historical-replay-input-gate-validator in report-only mode before artifact views.",
    }
    return _result(summary, output_dir, root, [f"No validator artifacts found under {root}"])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> HistoricalReplayInputGateValidatorStatusResult:
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "historical_replay_input_gate_validator_status.csv",
        "status_report": Path(output_dir) / "historical_replay_input_gate_validator_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return HistoricalReplayInputGateValidatorStatusResult(
        latest_validator_run_id=str(summary["latest_validator_run_id"]),
        status=str(summary["status"]),
        health_status=str(summary["health_status"]),
        workflow_stage=str(summary["workflow_stage"]),
        pass_candidate=bool(summary["pass_candidate"]),
        active_replay_input_ready=False,
        active_replay_input=False,
        forward_labels_exist=False,
        weights_trained=False,
        active_stock_profile_exists=False,
        real_buy_review_eligible=False,
        blocker_count=int(summary["blocker_count"]),
        warning_count=int(summary["warning_count"]),
        report_path=str(summary["report_path"]),
        safety_statement=str(summary["safety_statement"]),
        next_action=str(summary["next_action"]),
        summary_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata={"root": str(root), "report_only": True, "diagnostic_only": True},
    )


def _write(result: HistoricalReplayInputGateValidatorStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Historical Replay Input Gate Validator Status",
                "",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_validator_run_id: {result.latest_validator_run_id}",
                f"- pass_candidate: {result.pass_candidate}",
                f"- active_replay_input_ready: {result.active_replay_input_ready}",
                f"- active_replay_input: {result.active_replay_input}",
                f"- blocker_count: {result.blocker_count}",
                "",
                result.safety_statement,
                "",
                f"Next action: {result.next_action}",
            ]
        ),
        encoding="utf-8",
    )
    paths["metadata"].write_text(
        json.dumps(
            {
                "latest_validator_run_id": result.latest_validator_run_id,
                "status": result.status,
                "health_status": result.health_status,
                "workflow_stage": result.workflow_stage,
                "pass_candidate": result.pass_candidate,
                "active_replay_input_ready": False,
                "active_replay_input": False,
                "forward_labels_exist": False,
                "weights_trained": False,
                "active_stock_profile_exists": False,
                "real_buy_review_eligible": False,
                "blocker_count": result.blocker_count,
                "warning_count": result.warning_count,
                "report_path": result.report_path,
                "next_action": result.next_action,
                **result.audit_metadata,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _stage_for_status(status: str, health_status: str) -> str:
    if health_status == "FAIL":
        return INPUT_GATE_VALIDATOR_BLOCKED
    if status == "NO_INPUT":
        return INPUT_GATE_VALIDATOR_NO_INPUT
    if status == REPLAY_INPUT_GATE_PASS_CANDIDATE:
        return INPUT_GATE_VALIDATOR_PASS_CANDIDATE
    return INPUT_GATE_VALIDATOR_BLOCKED


def _next_action(stage: str) -> str:
    if stage == INPUT_GATE_VALIDATOR_PASS_CANDIDATE:
        return "Review pass-candidate diagnostics; do not treat as active replay input."
    if stage == INPUT_GATE_VALIDATOR_NO_INPUT:
        return "Provide a local replay input package to the report-only validator."
    return "Resolve validator blockers; do not run replay or downstream workflows."


def _safety_statement() -> str:
    return (
        "This validator workflow is report-only. It is not real replay. It is not active replay input. "
        "It does not compute forward labels. It does not train weights. It does not create active stock profiles. "
        "It does not create real buy-review eligibility. REPLAY_INPUT_GATE_PASS_CANDIDATE is not ACTIVE_REPLAY_INPUT_READY."
    )


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_int(value: Any) -> int:
    try:
        if _text(value) == "":
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}

