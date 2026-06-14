"""Status summary for report-only ACTIVE_REPLAY_INPUT_READY core artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.active_replay_input_ready import (
    NO_ACTIVE_REPLAY_INPUT_READY_GOVERNANCE_INPUT,
    READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY,
)
from quant_replay_system.active_replay_input_ready_health import check_active_replay_input_ready_health
from quant_replay_system.active_replay_input_ready_index import (
    DEFAULT_ROOT,
    build_active_replay_input_ready_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"

NO_ACTIVE_REPLAY_INPUT_READY_ARTIFACT_FOUND = "NO_ACTIVE_REPLAY_INPUT_READY_ARTIFACT_FOUND"
ACTIVE_REPLAY_INPUT_READY_NO_INPUT = "ACTIVE_REPLAY_INPUT_READY_NO_INPUT"
ACTIVE_REPLAY_INPUT_READY_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_HEALTH_FAILED = "ACTIVE_REPLAY_INPUT_READY_HEALTH_FAILED"
ACTIVE_REPLAY_INPUT_READY_READY_TO_EMIT = "ACTIVE_REPLAY_INPUT_READY_READY_TO_EMIT"

SUMMARY_COLUMNS = [
    "latest_active_ready_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "ready_to_emit_active_replay_input_ready",
    "active_replay_input_ready",
    "active_replay_input",
    "active_ready_emitted",
    "replay_execution_allowed",
    "replay_decisions_exist",
    "forward_labels_allowed",
    "forward_labels_exist",
    "training_allowed",
    "weights_trained",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "buy_review_allowed",
    "real_buy_review_eligible",
    "trading_allowed",
    "blocker_count",
    "warning_count",
    "report_path",
    "safety_statement",
    "next_action",
]


@dataclass(frozen=True)
class ActiveReplayInputReadyStatusResult:
    latest_active_ready_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    ready_to_emit_active_replay_input_ready: bool
    active_replay_input_ready: bool
    active_replay_input: bool
    active_ready_emitted: bool
    replay_execution_allowed: bool
    replay_decisions_exist: bool
    forward_labels_allowed: bool
    forward_labels_exist: bool
    training_allowed: bool
    weights_trained: bool
    stock_profile_allowed: bool
    active_stock_profile_exists: bool
    buy_review_allowed: bool
    real_buy_review_eligible: bool
    trading_allowed: bool
    blocker_count: int
    warning_count: int
    report_path: str
    safety_statement: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_active_replay_input_ready_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ActiveReplayInputReadyStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_active_replay_input_ready_index(root=root, output_dir=sibling_root / "index")
    health = check_active_replay_input_ready_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        latest = index.index_frame.sort_values(["generated_at", "active_ready_run_id"]).iloc[-1].to_dict()
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
) -> ActiveReplayInputReadyStatusResult:
    status = _text(latest.get("status"))
    stage = _stage_for_latest(status, health_status)
    summary = {
        "latest_active_ready_run_id": _text(latest.get("active_ready_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "ready_to_emit_active_replay_input_ready": _to_bool(
            latest.get("ready_to_emit_active_replay_input_ready")
        )
        and health_status == "PASS"
        and status == READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY,
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "active_ready_emitted": False,
        "replay_execution_allowed": False,
        "replay_decisions_exist": False,
        "forward_labels_allowed": False,
        "forward_labels_exist": False,
        "training_allowed": False,
        "weights_trained": False,
        "stock_profile_allowed": False,
        "active_stock_profile_exists": False,
        "buy_review_allowed": False,
        "real_buy_review_eligible": False,
        "trading_allowed": False,
        "blocker_count": max(_to_int(latest.get("blocker_count")), error_count),
        "warning_count": max(_to_int(latest.get("warning_count")), warning_count),
        "report_path": _text(latest.get("active_ready_report_path")),
        "safety_statement": _safety_statement(),
        "next_action": _next_action(stage),
    }
    return _result(summary, output_dir, root, [])


def _no_artifact_result(
    output_dir: str | Path,
    root: str | Path,
    health_status: str,
    error_count: int,
    warning_count: int,
) -> ActiveReplayInputReadyStatusResult:
    summary = {
        "latest_active_ready_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_ACTIVE_REPLAY_INPUT_READY_ARTIFACT_FOUND,
        "ready_to_emit_active_replay_input_ready": False,
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "active_ready_emitted": False,
        "replay_execution_allowed": False,
        "replay_decisions_exist": False,
        "forward_labels_allowed": False,
        "forward_labels_exist": False,
        "training_allowed": False,
        "weights_trained": False,
        "stock_profile_allowed": False,
        "active_stock_profile_exists": False,
        "buy_review_allowed": False,
        "real_buy_review_eligible": False,
        "trading_allowed": False,
        "blocker_count": error_count,
        "warning_count": warning_count,
        "report_path": "",
        "safety_statement": _safety_statement(),
        "next_action": "Run active-replay-input-ready before artifact views.",
    }
    return _result(summary, output_dir, root, [f"No active-ready artifacts found under {root}"])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> ActiveReplayInputReadyStatusResult:
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "active_replay_input_ready_status.csv",
        "status_report": Path(output_dir) / "active_replay_input_ready_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return ActiveReplayInputReadyStatusResult(
        latest_active_ready_run_id=str(summary["latest_active_ready_run_id"]),
        status=str(summary["status"]),
        health_status=str(summary["health_status"]),
        workflow_stage=str(summary["workflow_stage"]),
        ready_to_emit_active_replay_input_ready=bool(summary["ready_to_emit_active_replay_input_ready"]),
        active_replay_input_ready=False,
        active_replay_input=False,
        active_ready_emitted=False,
        replay_execution_allowed=False,
        replay_decisions_exist=False,
        forward_labels_allowed=False,
        forward_labels_exist=False,
        training_allowed=False,
        weights_trained=False,
        stock_profile_allowed=False,
        active_stock_profile_exists=False,
        buy_review_allowed=False,
        real_buy_review_eligible=False,
        trading_allowed=False,
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


def _write(result: ActiveReplayInputReadyStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# ACTIVE_REPLAY_INPUT_READY Status",
                "",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_active_ready_run_id: {result.latest_active_ready_run_id}",
                f"- ready_to_emit_active_replay_input_ready: {result.ready_to_emit_active_replay_input_ready}",
                f"- active_replay_input_ready: {result.active_replay_input_ready}",
                f"- active_replay_input: {result.active_replay_input}",
                f"- active_ready_emitted: {result.active_ready_emitted}",
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
                "latest_active_ready_run_id": result.latest_active_ready_run_id,
                "status": result.status,
                "health_status": result.health_status,
                "workflow_stage": result.workflow_stage,
                "ready_to_emit_active_replay_input_ready": result.ready_to_emit_active_replay_input_ready,
                "active_replay_input_ready": False,
                "active_replay_input": False,
                "active_ready_emitted": False,
                "replay_execution_allowed": False,
                "replay_decisions_exist": False,
                "forward_labels_allowed": False,
                "forward_labels_exist": False,
                "training_allowed": False,
                "weights_trained": False,
                "stock_profile_allowed": False,
                "active_stock_profile_exists": False,
                "buy_review_allowed": False,
                "real_buy_review_eligible": False,
                "trading_allowed": False,
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


def _stage_for_latest(status: str, health_status: str) -> str:
    if health_status == "FAIL":
        return ACTIVE_REPLAY_INPUT_READY_HEALTH_FAILED
    if status == NO_ACTIVE_REPLAY_INPUT_READY_GOVERNANCE_INPUT:
        return ACTIVE_REPLAY_INPUT_READY_NO_INPUT
    if status == READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY:
        return ACTIVE_REPLAY_INPUT_READY_READY_TO_EMIT
    return ACTIVE_REPLAY_INPUT_READY_BLOCKED


def _next_action(stage: str) -> str:
    return {
        NO_ACTIVE_REPLAY_INPUT_READY_ARTIFACT_FOUND: "Run active-replay-input-ready before artifact views.",
        ACTIVE_REPLAY_INPUT_READY_NO_INPUT: "Provide governance manifests before active-ready review.",
        ACTIVE_REPLAY_INPUT_READY_READY_TO_EMIT: (
            "Review report-only ready-to-emit context; do not emit ACTIVE_REPLAY_INPUT_READY without later scope."
        ),
        ACTIVE_REPLAY_INPUT_READY_HEALTH_FAILED: "Repair active-ready artifacts; do not emit ACTIVE_REPLAY_INPUT_READY.",
    }.get(stage, "Resolve report-only active-ready blockers.")


def _safety_statement() -> str:
    return (
        "This workflow is report-only. READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY is not ACTIVE_REPLAY_INPUT_READY. "
        "ACTIVE_REPLAY_INPUT_READY is not emitted. active replay input is not created. replay is not run. "
        "replay decisions are not created. labels are not computed. training is not run. stock_profile is not "
        "created. buy-review eligibility is not created. trading is not authorized."
    )


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "pass", "accepted"}
    return False


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
