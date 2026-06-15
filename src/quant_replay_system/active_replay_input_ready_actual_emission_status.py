"""Status summary for report-only actual ACTIVE_REPLAY_INPUT_READY marker artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.active_replay_input_ready_actual_emission import (
    ACTIVE_REPLAY_INPUT_READY,
    NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT,
    READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION,
)
from quant_replay_system.active_replay_input_ready_actual_emission_health import (
    check_actual_active_replay_input_ready_emission_health,
)
from quant_replay_system.active_replay_input_ready_actual_emission_index import (
    DEFAULT_ROOT,
    build_actual_active_replay_input_ready_emission_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"

NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_ARTIFACT_FOUND = (
    "NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_ARTIFACT_FOUND"
)
ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_NO_INPUT = "ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_NO_INPUT"
READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_REVIEW = (
    "READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_REVIEW"
)
ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_MARKER_ONLY = "ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_MARKER_ONLY"
ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_BLOCKED = "ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_BLOCKED"
ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_HEALTH_FAILED = "ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_HEALTH_FAILED"

SUMMARY_COLUMNS = [
    "latest_actual_active_replay_input_ready_emission_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "active_replay_input_ready_marker_emitted",
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
    "marker_file_exists",
    "report_path",
    "safety_statement",
    "next_action",
]


@dataclass(frozen=True)
class ActualActiveReplayInputReadyEmissionStatusResult:
    latest_actual_active_replay_input_ready_emission_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    active_replay_input_ready_marker_emitted: bool
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
    marker_file_exists: bool
    report_path: str
    safety_statement: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_actual_active_replay_input_ready_emission_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ActualActiveReplayInputReadyEmissionStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_actual_active_replay_input_ready_emission_index(root=root, output_dir=sibling_root / "index")
    health = check_actual_active_replay_input_ready_emission_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        latest = index.index_frame.sort_values(["generated_at", "actual_emission_run_id"]).iloc[-1].to_dict()
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
) -> ActualActiveReplayInputReadyEmissionStatusResult:
    status = _text(latest.get("status"))
    stage = _stage_for_latest(status, health_status)
    summary = {
        "latest_actual_active_replay_input_ready_emission_run_id": _text(
            latest.get("actual_emission_run_id")
        ),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "active_replay_input_ready_marker_emitted": _to_bool(
            latest.get("active_replay_input_ready_marker_emitted")
        ),
        "active_replay_input_ready": _to_bool(latest.get("active_replay_input_ready")),
        "active_replay_input": False,
        "active_ready_emitted": _to_bool(latest.get("active_ready_emitted")),
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
        "marker_file_exists": _to_bool(latest.get("marker_file_exists")),
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
) -> ActualActiveReplayInputReadyEmissionStatusResult:
    summary = {
        "latest_actual_active_replay_input_ready_emission_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_ARTIFACT_FOUND,
        "active_replay_input_ready_marker_emitted": False,
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
        "marker_file_exists": False,
        "report_path": "",
        "safety_statement": _safety_statement(),
        "next_action": "Run active-replay-input-ready-actual-emission before artifact views.",
    }
    return _result(summary, output_dir, root, [f"No actual emission artifacts found under {root}"])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> ActualActiveReplayInputReadyEmissionStatusResult:
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "active_replay_input_ready_actual_emission_status.csv",
        "status_report": Path(output_dir) / "active_replay_input_ready_actual_emission_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return ActualActiveReplayInputReadyEmissionStatusResult(
        latest_actual_active_replay_input_ready_emission_run_id=str(
            summary["latest_actual_active_replay_input_ready_emission_run_id"]
        ),
        status=str(summary["status"]),
        health_status=str(summary["health_status"]),
        workflow_stage=str(summary["workflow_stage"]),
        active_replay_input_ready_marker_emitted=bool(summary["active_replay_input_ready_marker_emitted"]),
        active_replay_input_ready=bool(summary["active_replay_input_ready"]),
        active_replay_input=False,
        active_ready_emitted=bool(summary["active_ready_emitted"]),
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
        marker_file_exists=bool(summary["marker_file_exists"]),
        report_path=str(summary["report_path"]),
        safety_statement=str(summary["safety_statement"]),
        next_action=str(summary["next_action"]),
        summary_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata={"root": str(root), "report_only": True, "diagnostic_only": True},
    )


def _write(result: ActualActiveReplayInputReadyEmissionStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Actual ACTIVE_REPLAY_INPUT_READY Emission Status",
                "",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                (
                    "- latest_actual_active_replay_input_ready_emission_run_id: "
                    f"{result.latest_actual_active_replay_input_ready_emission_run_id}"
                ),
                f"- active_replay_input_ready_marker_emitted: {result.active_replay_input_ready_marker_emitted}",
                f"- active_replay_input_ready: {result.active_replay_input_ready}",
                f"- active_replay_input: {result.active_replay_input}",
                f"- active_ready_emitted: {result.active_ready_emitted}",
                f"- replay_execution_allowed: {result.replay_execution_allowed}",
                f"- replay_decisions_exist: {result.replay_decisions_exist}",
                f"- marker_file_exists: {result.marker_file_exists}",
                f"- blocker_count: {result.blocker_count}",
                f"- warning_count: {result.warning_count}",
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
                "latest_actual_active_replay_input_ready_emission_run_id": (
                    result.latest_actual_active_replay_input_ready_emission_run_id
                ),
                "active_replay_input_ready_marker_emitted": result.active_replay_input_ready_marker_emitted,
                "active_replay_input_ready": result.active_replay_input_ready,
                "active_replay_input": result.active_replay_input,
                "active_ready_emitted": result.active_ready_emitted,
                "blocker_count": result.blocker_count,
                "warning_count": result.warning_count,
                "marker_file_exists": result.marker_file_exists,
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
        return ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_HEALTH_FAILED
    if status == NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT:
        return ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_NO_INPUT
    if status == READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION:
        return READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_REVIEW
    if status == ACTIVE_REPLAY_INPUT_READY:
        return ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_MARKER_ONLY
    return ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_BLOCKED


def _next_action(stage: str) -> str:
    if stage == ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_MARKER_ONLY:
        return "Review marker-only ACTIVE_REPLAY_INPUT_READY artifact; do not create active replay input yet."
    if stage == READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_REVIEW:
        return "Review whether explicit marker-only emission allow flag should be used."
    if stage == ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_NO_INPUT:
        return "Provide actual marker-emission manifests before review."
    if stage == ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_HEALTH_FAILED:
        return "Fix health failures before interpreting marker-emission artifacts."
    if stage == NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_ARTIFACT_FOUND:
        return "Run active-replay-input-ready-actual-emission before artifact views."
    return "Resolve blockers before marker-only ACTIVE_REPLAY_INPUT_READY emission."


def _safety_statement() -> str:
    return (
        "This workflow is report-only and diagnostic-only. ACTIVE_REPLAY_INPUT_READY here is marker-only. "
        "The emitted marker does not create active replay input, does not run replay, does not create replay "
        "decisions, does not compute labels, does not train weights, does not create stock_profile, does not "
        "create buy-review eligibility, and does not authorize trading."
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


__all__ = [
    "ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_BLOCKED",
    "ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_HEALTH_FAILED",
    "ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_MARKER_ONLY",
    "ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_NO_INPUT",
    "NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_ARTIFACT_FOUND",
    "READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_REVIEW",
    "ActualActiveReplayInputReadyEmissionStatusResult",
    "run_actual_active_replay_input_ready_emission_status",
]
