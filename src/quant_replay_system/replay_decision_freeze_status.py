"""Status summary for report-only replay decision freeze artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.replay_decision_freeze import (
    NO_REPLAY_DECISION_FREEZE_INPUT,
    READY_FOR_REPLAY_DECISION_FREEZE,
    REPLAY_DECISION_FROZEN,
)
from quant_replay_system.replay_decision_freeze_health import check_replay_decision_freeze_health
from quant_replay_system.replay_decision_freeze_index import DEFAULT_ROOT, build_replay_decision_freeze_index


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"

NO_REPLAY_DECISION_FREEZE_ARTIFACT_FOUND = "NO_REPLAY_DECISION_FREEZE_ARTIFACT_FOUND"
REPLAY_DECISION_FREEZE_NO_INPUT_ARTIFACT = "REPLAY_DECISION_FREEZE_NO_INPUT_ARTIFACT"
REPLAY_DECISION_FREEZE_HEALTH_FAILED = "REPLAY_DECISION_FREEZE_HEALTH_FAILED"
REPLAY_DECISION_FREEZE_BLOCKED = "REPLAY_DECISION_FREEZE_BLOCKED"

SUMMARY_COLUMNS = [
    "latest_replay_decision_freeze_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "source_actual_replay_execution_run_id",
    "actual_replay_execution_status",
    "actual_replay_execution_health_status",
    "actual_replay_executed",
    "ready_for_replay_decision_freeze",
    "replay_decision_freeze_executed",
    "replay_decision_frozen",
    "replay_decision_artifacts_created",
    "replay_decisions_created",
    "replay_decisions_exist",
    "replay_decision_artifact_path",
    "decision_row_count",
    "decision_label_set",
    "forward_labels_allowed",
    "forward_labels_exist",
    "forward_return_labels_created",
    "training_allowed",
    "weights_trained",
    "training_result_created",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "stock_profile_created",
    "buy_review_allowed",
    "real_buy_review_eligible",
    "approved_for_paper",
    "trading_allowed",
    "blocker_count",
    "warning_count",
    "report_path",
    "safety_statement",
    "next_action",
]


@dataclass(frozen=True)
class ReplayDecisionFreezeStatusResult:
    latest_replay_decision_freeze_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    source_actual_replay_execution_run_id: str
    actual_replay_execution_status: str
    actual_replay_execution_health_status: str
    actual_replay_executed: bool
    ready_for_replay_decision_freeze: bool
    replay_decision_freeze_executed: bool
    replay_decision_frozen: bool
    replay_decision_artifacts_created: bool
    replay_decisions_created: bool
    replay_decisions_exist: bool
    replay_decision_artifact_path: str
    decision_row_count: int
    decision_label_set: str
    forward_labels_allowed: bool
    forward_labels_exist: bool
    forward_return_labels_created: bool
    training_allowed: bool
    weights_trained: bool
    training_result_created: bool
    stock_profile_allowed: bool
    active_stock_profile_exists: bool
    stock_profile_created: bool
    buy_review_allowed: bool
    real_buy_review_eligible: bool
    approved_for_paper: bool
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


def run_replay_decision_freeze_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ReplayDecisionFreezeStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_replay_decision_freeze_index(root=root, output_dir=sibling_root / "index")
    health = check_replay_decision_freeze_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        latest = index.index_frame.sort_values(["generated_at", "replay_decision_freeze_run_id"]).iloc[-1].to_dict()
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
) -> ReplayDecisionFreezeStatusResult:
    status = _text(latest.get("status"))
    stage = _stage_for_latest(status, _text(latest.get("workflow_stage")), health_status)
    summary = {
        "latest_replay_decision_freeze_run_id": _text(latest.get("replay_decision_freeze_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "source_actual_replay_execution_run_id": _text(latest.get("source_actual_replay_execution_run_id")),
        "actual_replay_execution_status": _text(latest.get("actual_replay_execution_status")),
        "actual_replay_execution_health_status": _text(latest.get("actual_replay_execution_health_status")),
        "actual_replay_executed": _to_bool(latest.get("actual_replay_executed")),
        "ready_for_replay_decision_freeze": _to_bool(latest.get("ready_for_replay_decision_freeze")),
        "replay_decision_freeze_executed": _to_bool(latest.get("replay_decision_freeze_executed")),
        "replay_decision_frozen": _to_bool(latest.get("replay_decision_frozen")),
        "replay_decision_artifacts_created": _to_bool(latest.get("replay_decision_artifacts_created")),
        "replay_decisions_created": _to_bool(latest.get("replay_decisions_created")),
        "replay_decisions_exist": _to_bool(latest.get("replay_decisions_exist")),
        "replay_decision_artifact_path": _text(latest.get("replay_decision_artifact_path")),
        "decision_row_count": _to_int(latest.get("decision_row_count")),
        "decision_label_set": _text(latest.get("decision_label_set")),
        "forward_labels_allowed": _to_bool(latest.get("forward_labels_allowed")),
        "forward_labels_exist": _to_bool(latest.get("forward_labels_exist")),
        "forward_return_labels_created": _to_bool(latest.get("forward_return_labels_created")),
        "training_allowed": _to_bool(latest.get("training_allowed")),
        "weights_trained": _to_bool(latest.get("weights_trained")),
        "training_result_created": _to_bool(latest.get("training_result_created")),
        "stock_profile_allowed": _to_bool(latest.get("stock_profile_allowed")),
        "active_stock_profile_exists": _to_bool(latest.get("active_stock_profile_exists")),
        "stock_profile_created": _to_bool(latest.get("stock_profile_created")),
        "buy_review_allowed": _to_bool(latest.get("buy_review_allowed")),
        "real_buy_review_eligible": _to_bool(latest.get("real_buy_review_eligible")),
        "approved_for_paper": _to_bool(latest.get("approved_for_paper")),
        "trading_allowed": _to_bool(latest.get("trading_allowed")),
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
) -> ReplayDecisionFreezeStatusResult:
    summary = {
        "latest_replay_decision_freeze_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_REPLAY_DECISION_FREEZE_ARTIFACT_FOUND,
        "source_actual_replay_execution_run_id": "",
        "actual_replay_execution_status": "",
        "actual_replay_execution_health_status": "",
        "actual_replay_executed": False,
        "ready_for_replay_decision_freeze": False,
        "replay_decision_freeze_executed": False,
        "replay_decision_frozen": False,
        "replay_decision_artifacts_created": False,
        "replay_decisions_created": False,
        "replay_decisions_exist": False,
        "replay_decision_artifact_path": "",
        "decision_row_count": 0,
        "decision_label_set": "",
        "forward_labels_allowed": False,
        "forward_labels_exist": False,
        "forward_return_labels_created": False,
        "training_allowed": False,
        "weights_trained": False,
        "training_result_created": False,
        "stock_profile_allowed": False,
        "active_stock_profile_exists": False,
        "stock_profile_created": False,
        "buy_review_allowed": False,
        "real_buy_review_eligible": False,
        "approved_for_paper": False,
        "trading_allowed": False,
        "blocker_count": error_count,
        "warning_count": warning_count,
        "report_path": "",
        "safety_statement": _safety_statement(),
        "next_action": "Run replay-decision-freeze before artifact views; do not compute labels, train, create stock_profile, buy-review, or trading outputs.",
    }
    return _result(summary, output_dir, root, [f"No replay decision freeze artifacts found under {root}"])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> ReplayDecisionFreezeStatusResult:
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "replay_decision_freeze_status.csv",
        "status_report": Path(output_dir) / "replay_decision_freeze_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return ReplayDecisionFreezeStatusResult(
        latest_replay_decision_freeze_run_id=str(summary["latest_replay_decision_freeze_run_id"]),
        status=str(summary["status"]),
        health_status=str(summary["health_status"]),
        workflow_stage=str(summary["workflow_stage"]),
        source_actual_replay_execution_run_id=str(summary["source_actual_replay_execution_run_id"]),
        actual_replay_execution_status=str(summary["actual_replay_execution_status"]),
        actual_replay_execution_health_status=str(summary["actual_replay_execution_health_status"]),
        actual_replay_executed=bool(summary["actual_replay_executed"]),
        ready_for_replay_decision_freeze=bool(summary["ready_for_replay_decision_freeze"]),
        replay_decision_freeze_executed=bool(summary["replay_decision_freeze_executed"]),
        replay_decision_frozen=bool(summary["replay_decision_frozen"]),
        replay_decision_artifacts_created=bool(summary["replay_decision_artifacts_created"]),
        replay_decisions_created=bool(summary["replay_decisions_created"]),
        replay_decisions_exist=bool(summary["replay_decisions_exist"]),
        replay_decision_artifact_path=str(summary["replay_decision_artifact_path"]),
        decision_row_count=int(summary["decision_row_count"]),
        decision_label_set=str(summary["decision_label_set"]),
        forward_labels_allowed=bool(summary["forward_labels_allowed"]),
        forward_labels_exist=bool(summary["forward_labels_exist"]),
        forward_return_labels_created=bool(summary["forward_return_labels_created"]),
        training_allowed=bool(summary["training_allowed"]),
        weights_trained=bool(summary["weights_trained"]),
        training_result_created=bool(summary["training_result_created"]),
        stock_profile_allowed=bool(summary["stock_profile_allowed"]),
        active_stock_profile_exists=bool(summary["active_stock_profile_exists"]),
        stock_profile_created=bool(summary["stock_profile_created"]),
        buy_review_allowed=bool(summary["buy_review_allowed"]),
        real_buy_review_eligible=bool(summary["real_buy_review_eligible"]),
        approved_for_paper=bool(summary["approved_for_paper"]),
        trading_allowed=bool(summary["trading_allowed"]),
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


def _write(result: ReplayDecisionFreezeStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Replay Decision Freeze Status",
                "",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_replay_decision_freeze_run_id: {result.latest_replay_decision_freeze_run_id}",
                f"- replay_decision_frozen: {result.replay_decision_frozen}",
                f"- replay_decisions_created: {result.replay_decisions_created}",
                f"- decision_row_count: {result.decision_row_count}",
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
                "latest_replay_decision_freeze_run_id": result.latest_replay_decision_freeze_run_id,
                "warnings": result.warnings,
                "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
                **result.audit_metadata,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _stage_for_latest(status: str, latest_stage: str, health_status: str) -> str:
    if health_status == "FAIL":
        return REPLAY_DECISION_FREEZE_HEALTH_FAILED
    if status == NO_REPLAY_DECISION_FREEZE_INPUT:
        return REPLAY_DECISION_FREEZE_NO_INPUT_ARTIFACT
    if status in {READY_FOR_REPLAY_DECISION_FREEZE, REPLAY_DECISION_FROZEN}:
        return status
    return latest_stage or REPLAY_DECISION_FREEZE_BLOCKED


def _next_action(stage: str) -> str:
    if stage == REPLAY_DECISION_FREEZE_NO_INPUT_ARTIFACT:
        return "Supply report-only replay decision freeze inputs; do not compute labels, train, create stock_profile, buy-review, or trading outputs."
    if stage == READY_FOR_REPLAY_DECISION_FREEZE:
        return "Review readiness and require explicit allow before freezing report-only decision-time review rows."
    if stage == REPLAY_DECISION_FROZEN:
        return "Review report-only frozen decision-time review rows before any later status integration; no labels, training, stock_profile, buy-review, paper approval, or trading were created."
    if stage == REPLAY_DECISION_FREEZE_HEALTH_FAILED:
        return "Fix replay decision freeze artifact health issues before any later workflow."
    return "Resolve replay decision freeze blockers without labels, training, stock_profile, buy-review, paper approval, or trading."


def _safety_statement() -> str:
    return (
        "Replay decision freeze is report-only at this stage. `REPLAY_DECISION_FROZEN` means "
        "frozen decision-time review rows only; it does not compute forward labels; does not train weights; "
        "does not create stock_profile; does not create buy-review eligibility; does not apply paper approval; "
        "and does not authorize trading."
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
