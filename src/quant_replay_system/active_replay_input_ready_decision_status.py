"""Status summary for report-only active replay input ready-decision artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.active_replay_input_ready_decision import (
    NO_ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT,
    READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION,
)
from quant_replay_system.active_replay_input_ready_decision_health import (
    check_active_replay_input_ready_decision_health,
)
from quant_replay_system.active_replay_input_ready_decision_index import (
    DEFAULT_ROOT,
    build_active_replay_input_ready_decision_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"

NO_READY_DECISION_ARTIFACT_FOUND = "NO_READY_DECISION_ARTIFACT_FOUND"
READY_DECISION_NO_INPUT = "READY_DECISION_NO_INPUT"
READY_DECISION_BLOCKED = "READY_DECISION_BLOCKED"
READY_DECISION_HEALTH_FAILED = "READY_DECISION_HEALTH_FAILED"

SUMMARY_COLUMNS = [
    "latest_decision_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "ready_for_active_replay_input_ready_decision",
    "active_replay_input_ready",
    "active_replay_input",
    "active_ready_emitted",
    "replay_execution_allowed",
    "forward_labels_allowed",
    "training_allowed",
    "stock_profile_allowed",
    "buy_review_allowed",
    "trading_allowed",
    "blocker_count",
    "warning_count",
    "report_path",
    "safety_statement",
    "next_action",
]


@dataclass(frozen=True)
class ActiveReplayInputReadyDecisionStatusResult:
    latest_decision_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    ready_for_active_replay_input_ready_decision: bool
    active_replay_input_ready: bool
    active_replay_input: bool
    active_ready_emitted: bool
    replay_execution_allowed: bool
    forward_labels_allowed: bool
    training_allowed: bool
    stock_profile_allowed: bool
    buy_review_allowed: bool
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


def run_active_replay_input_ready_decision_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ActiveReplayInputReadyDecisionStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_active_replay_input_ready_decision_index(root=root, output_dir=sibling_root / "index")
    health = check_active_replay_input_ready_decision_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        latest = index.index_frame.sort_values(["generated_at", "decision_run_id"]).iloc[-1].to_dict()
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
) -> ActiveReplayInputReadyDecisionStatusResult:
    status = _text(latest.get("status"))
    stage = _stage_for_latest(status, health_status)
    summary = {
        "latest_decision_run_id": _text(latest.get("decision_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "ready_for_active_replay_input_ready_decision": _to_bool(
            latest.get("ready_for_active_replay_input_ready_decision")
        ),
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "active_ready_emitted": False,
        "replay_execution_allowed": False,
        "forward_labels_allowed": False,
        "training_allowed": False,
        "stock_profile_allowed": False,
        "buy_review_allowed": False,
        "trading_allowed": False,
        "blocker_count": max(_to_int(latest.get("blocker_count")), error_count),
        "warning_count": max(_to_int(latest.get("warning_count")), warning_count),
        "report_path": _text(latest.get("decision_report_path")),
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
) -> ActiveReplayInputReadyDecisionStatusResult:
    summary = {
        "latest_decision_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_READY_DECISION_ARTIFACT_FOUND,
        "ready_for_active_replay_input_ready_decision": False,
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "active_ready_emitted": False,
        "replay_execution_allowed": False,
        "forward_labels_allowed": False,
        "training_allowed": False,
        "stock_profile_allowed": False,
        "buy_review_allowed": False,
        "trading_allowed": False,
        "blocker_count": error_count,
        "warning_count": warning_count,
        "report_path": "",
        "safety_statement": _safety_statement(),
        "next_action": "Run active-replay-input-ready-decision before artifact views.",
    }
    return _result(summary, output_dir, root, [f"No ready-decision artifacts found under {root}"])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> ActiveReplayInputReadyDecisionStatusResult:
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "active_replay_input_ready_decision_status.csv",
        "status_report": Path(output_dir) / "active_replay_input_ready_decision_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return ActiveReplayInputReadyDecisionStatusResult(
        latest_decision_run_id=str(summary["latest_decision_run_id"]),
        status=str(summary["status"]),
        health_status=str(summary["health_status"]),
        workflow_stage=str(summary["workflow_stage"]),
        ready_for_active_replay_input_ready_decision=bool(
            summary["ready_for_active_replay_input_ready_decision"]
        ),
        active_replay_input_ready=False,
        active_replay_input=False,
        active_ready_emitted=False,
        replay_execution_allowed=False,
        forward_labels_allowed=False,
        training_allowed=False,
        stock_profile_allowed=False,
        buy_review_allowed=False,
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


def _write(result: ActiveReplayInputReadyDecisionStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Active Replay Input Ready Decision Status",
                "",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_decision_run_id: {result.latest_decision_run_id}",
                (
                    "- ready_for_active_replay_input_ready_decision: "
                    f"{result.ready_for_active_replay_input_ready_decision}"
                ),
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
                "latest_decision_run_id": result.latest_decision_run_id,
                "status": result.status,
                "health_status": result.health_status,
                "workflow_stage": result.workflow_stage,
                "ready_for_active_replay_input_ready_decision": (
                    result.ready_for_active_replay_input_ready_decision
                ),
                "active_replay_input_ready": False,
                "active_replay_input": False,
                "active_ready_emitted": False,
                "replay_execution_allowed": False,
                "forward_labels_allowed": False,
                "training_allowed": False,
                "stock_profile_allowed": False,
                "buy_review_allowed": False,
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
        return READY_DECISION_HEALTH_FAILED
    if status == NO_ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT:
        return READY_DECISION_NO_INPUT
    if status == READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION:
        return READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION
    return READY_DECISION_BLOCKED


def _next_action(stage: str) -> str:
    if stage == READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION:
        return "Review ready-decision package manually; do not treat it as ACTIVE_REPLAY_INPUT_READY."
    if stage == READY_DECISION_NO_INPUT:
        return "Provide emission lineage and decision manifests before ready-decision review."
    if stage == READY_DECISION_HEALTH_FAILED:
        return "Resolve ready-decision health blockers before using decision context."
    if stage == NO_READY_DECISION_ARTIFACT_FOUND:
        return "Run active-replay-input-ready-decision before artifact views."
    return "Resolve ready-decision blockers; do not run replay or downstream active workflows."


def _safety_statement() -> str:
    return (
        "This ready-decision workflow is report-only. READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION "
        "is not ACTIVE_REPLAY_INPUT_READY. It does not emit ACTIVE_REPLAY_INPUT_READY. It does "
        "not create active replay input. It does not run replay. It does not compute forward "
        "labels. It does not train weights. It does not create active stock profiles. It does "
        "not create real buy-review eligibility. It does not authorize trading."
    )


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "NO_READY_DECISION_ARTIFACT_FOUND",
    "READY_DECISION_NO_INPUT",
    "READY_DECISION_BLOCKED",
    "READY_DECISION_HEALTH_FAILED",
    "ActiveReplayInputReadyDecisionStatusResult",
    "run_active_replay_input_ready_decision_status",
]
