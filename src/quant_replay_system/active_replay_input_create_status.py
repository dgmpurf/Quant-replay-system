"""Status summary for report-only active replay input creation artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.active_replay_input_create import (
    ACTIVE_REPLAY_INPUT_CREATED,
    NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT,
    READY_FOR_ACTIVE_REPLAY_INPUT_CREATION,
)
from quant_replay_system.active_replay_input_create_health import check_active_replay_input_create_health
from quant_replay_system.active_replay_input_create_index import (
    DEFAULT_ROOT,
    build_active_replay_input_create_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"

NO_ACTIVE_REPLAY_INPUT_CREATE_ARTIFACT_FOUND = "NO_ACTIVE_REPLAY_INPUT_CREATE_ARTIFACT_FOUND"
ACTIVE_REPLAY_INPUT_CREATE_NO_INPUT = "ACTIVE_REPLAY_INPUT_CREATE_NO_INPUT"
READY_FOR_ACTIVE_REPLAY_INPUT_CREATE_REVIEW = "READY_FOR_ACTIVE_REPLAY_INPUT_CREATE_REVIEW"
ACTIVE_REPLAY_INPUT_CREATE_CREATED = "ACTIVE_REPLAY_INPUT_CREATE_CREATED"
ACTIVE_REPLAY_INPUT_CREATE_BLOCKED = "ACTIVE_REPLAY_INPUT_CREATE_BLOCKED"
ACTIVE_REPLAY_INPUT_CREATE_HEALTH_FAILED = "ACTIVE_REPLAY_INPUT_CREATE_HEALTH_FAILED"

SUMMARY_COLUMNS = [
    "latest_active_replay_input_creation_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "active_replay_input_created",
    "active_replay_input",
    "active_replay_input_file_exists",
    "source_marker_run_id",
    "marker_status",
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
class ActiveReplayInputCreateStatusResult:
    latest_active_replay_input_creation_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    active_replay_input_created: bool
    active_replay_input: bool
    active_replay_input_file_exists: bool
    source_marker_run_id: str
    marker_status: str
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


def run_active_replay_input_create_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ActiveReplayInputCreateStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_active_replay_input_create_index(root=root, output_dir=sibling_root / "index")
    health = check_active_replay_input_create_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        latest = index.index_frame.sort_values(["generated_at", "active_input_creation_run_id"]).iloc[-1].to_dict()
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
) -> ActiveReplayInputCreateStatusResult:
    status = _text(latest.get("status"))
    stage = _stage_for_latest(status, health_status)
    summary = {
        "latest_active_replay_input_creation_run_id": _text(latest.get("active_input_creation_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "active_replay_input_created": _to_bool(latest.get("active_replay_input_created")),
        "active_replay_input": _to_bool(latest.get("active_replay_input")),
        "active_replay_input_file_exists": _to_bool(latest.get("active_replay_input_file_exists")),
        "source_marker_run_id": _text(latest.get("source_marker_run_id")),
        "marker_status": _text(latest.get("marker_status")),
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
        "report_path": _text(latest.get("report_path")),
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
) -> ActiveReplayInputCreateStatusResult:
    summary = {
        "latest_active_replay_input_creation_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_ACTIVE_REPLAY_INPUT_CREATE_ARTIFACT_FOUND,
        "active_replay_input_created": False,
        "active_replay_input": False,
        "active_replay_input_file_exists": False,
        "source_marker_run_id": "",
        "marker_status": "",
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
        "next_action": "Run active-replay-input-create before artifact views.",
    }
    return _result(summary, output_dir, root, [f"No active input creation artifacts found under {root}"])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> ActiveReplayInputCreateStatusResult:
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "active_replay_input_create_status.csv",
        "status_report": Path(output_dir) / "active_replay_input_create_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return ActiveReplayInputCreateStatusResult(
        latest_active_replay_input_creation_run_id=str(summary["latest_active_replay_input_creation_run_id"]),
        status=str(summary["status"]),
        health_status=str(summary["health_status"]),
        workflow_stage=str(summary["workflow_stage"]),
        active_replay_input_created=bool(summary["active_replay_input_created"]),
        active_replay_input=bool(summary["active_replay_input"]),
        active_replay_input_file_exists=bool(summary["active_replay_input_file_exists"]),
        source_marker_run_id=str(summary["source_marker_run_id"]),
        marker_status=str(summary["marker_status"]),
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


def _write(result: ActiveReplayInputCreateStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Active Replay Input Creation Status",
                "",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_active_replay_input_creation_run_id: {result.latest_active_replay_input_creation_run_id}",
                f"- active_replay_input_created: {result.active_replay_input_created}",
                f"- active_replay_input: {result.active_replay_input}",
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
                "status": result.status,
                "health_status": result.health_status,
                "workflow_stage": result.workflow_stage,
                "latest_active_replay_input_creation_run_id": result.latest_active_replay_input_creation_run_id,
                "warnings": result.warnings,
                "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
                **result.audit_metadata,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _stage_for_latest(status: str, health_status: str) -> str:
    if health_status == "FAIL":
        return ACTIVE_REPLAY_INPUT_CREATE_HEALTH_FAILED
    if status == NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT:
        return ACTIVE_REPLAY_INPUT_CREATE_NO_INPUT
    if status == READY_FOR_ACTIVE_REPLAY_INPUT_CREATION:
        return READY_FOR_ACTIVE_REPLAY_INPUT_CREATE_REVIEW
    if status == ACTIVE_REPLAY_INPUT_CREATED:
        return ACTIVE_REPLAY_INPUT_CREATE_CREATED
    return ACTIVE_REPLAY_INPUT_CREATE_BLOCKED


def _next_action(stage: str) -> str:
    if stage == ACTIVE_REPLAY_INPUT_CREATE_NO_INPUT:
        return "Supply report-only active replay input creation manifests; do not run replay."
    if stage == READY_FOR_ACTIVE_REPLAY_INPUT_CREATE_REVIEW:
        return "Review before explicit report-only active input creation; do not run replay."
    if stage == ACTIVE_REPLAY_INPUT_CREATE_CREATED:
        return "Add artifact views or later governance only; active input still does not run replay."
    if stage == ACTIVE_REPLAY_INPUT_CREATE_HEALTH_FAILED:
        return "Fix active input creation artifact health issues before any later workflow."
    return "Resolve active input creation blockers without running replay or creating decisions."


def _safety_statement() -> str:
    return (
        "This workflow is report-only and diagnostic-only. Active replay input creation does not run replay; "
        "does not create replay decisions; does not compute labels; does not train weights; does not create "
        "stock_profile; does not create buy-review eligibility; and does not authorize trading."
    )


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "pass"}
    return False


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
