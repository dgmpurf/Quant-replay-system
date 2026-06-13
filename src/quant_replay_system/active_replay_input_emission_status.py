"""Status summary for report-only active replay input emission artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.active_replay_input_emission import (
    EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW,
    NO_EMISSION_INPUT,
)
from quant_replay_system.active_replay_input_emission_health import (
    check_active_replay_input_emission_health,
)
from quant_replay_system.active_replay_input_emission_index import (
    DEFAULT_ROOT,
    build_active_replay_input_emission_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"

NO_EMISSION_ARTIFACT_FOUND = "NO_EMISSION_ARTIFACT_FOUND"
EMISSION_NO_INPUT = "EMISSION_NO_INPUT"
EMISSION_BLOCKED = "EMISSION_BLOCKED"
EMISSION_HEALTH_FAILED = "EMISSION_HEALTH_FAILED"

SUMMARY_COLUMNS = [
    "latest_emission_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "ready_for_active_replay_input_ready_review",
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
class ActiveReplayInputEmissionStatusResult:
    latest_emission_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    ready_for_active_replay_input_ready_review: bool
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


def run_active_replay_input_emission_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ActiveReplayInputEmissionStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_active_replay_input_emission_index(root=root, output_dir=sibling_root / "index")
    health = check_active_replay_input_emission_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        latest = index.index_frame.sort_values(["generated_at", "emission_run_id"]).iloc[-1].to_dict()
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
) -> ActiveReplayInputEmissionStatusResult:
    status = _text(latest.get("status"))
    stage = _stage_for_latest(status, health_status)
    summary = {
        "latest_emission_run_id": _text(latest.get("emission_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "ready_for_active_replay_input_ready_review": _to_bool(latest.get("ready_for_active_replay_input_ready_review")),
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
        "report_path": _text(latest.get("emission_report_path")),
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
) -> ActiveReplayInputEmissionStatusResult:
    summary = {
        "latest_emission_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_EMISSION_ARTIFACT_FOUND,
        "ready_for_active_replay_input_ready_review": False,
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
        "next_action": "Run active-replay-input-emission before artifact views.",
    }
    return _result(summary, output_dir, root, [f"No emission artifacts found under {root}"])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> ActiveReplayInputEmissionStatusResult:
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "active_replay_input_emission_status.csv",
        "status_report": Path(output_dir) / "active_replay_input_emission_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return ActiveReplayInputEmissionStatusResult(
        latest_emission_run_id=str(summary["latest_emission_run_id"]),
        status=str(summary["status"]),
        health_status=str(summary["health_status"]),
        workflow_stage=str(summary["workflow_stage"]),
        ready_for_active_replay_input_ready_review=bool(summary["ready_for_active_replay_input_ready_review"]),
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


def _write(result: ActiveReplayInputEmissionStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Active Replay Input Emission Status",
                "",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_emission_run_id: {result.latest_emission_run_id}",
                f"- ready_for_active_replay_input_ready_review: {result.ready_for_active_replay_input_ready_review}",
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
                "latest_emission_run_id": result.latest_emission_run_id,
                "status": result.status,
                "health_status": result.health_status,
                "workflow_stage": result.workflow_stage,
                "ready_for_active_replay_input_ready_review": result.ready_for_active_replay_input_ready_review,
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
        return EMISSION_HEALTH_FAILED
    if status == NO_EMISSION_INPUT:
        return EMISSION_NO_INPUT
    if status == EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW:
        return EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW
    return EMISSION_BLOCKED


def _next_action(stage: str) -> str:
    if stage == EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW:
        return "Review emission package manually; do not treat it as ACTIVE_REPLAY_INPUT_READY."
    if stage == EMISSION_NO_INPUT:
        return "Provide final-review and emission manifests before active-ready emission review."
    if stage == EMISSION_HEALTH_FAILED:
        return "Resolve emission health blockers before using emission context."
    if stage == NO_EMISSION_ARTIFACT_FOUND:
        return "Run active-replay-input-emission before artifact views."
    return "Resolve emission blockers; do not run replay or downstream active workflows."


def _safety_statement() -> str:
    return (
        "This emission workflow is report-only. EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW "
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
    "NO_EMISSION_ARTIFACT_FOUND",
    "EMISSION_NO_INPUT",
    "EMISSION_BLOCKED",
    "EMISSION_HEALTH_FAILED",
    "ActiveReplayInputEmissionStatusResult",
    "run_active_replay_input_emission_status",
]
