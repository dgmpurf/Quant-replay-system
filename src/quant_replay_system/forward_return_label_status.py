"""Status summary for report-only forward return label artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.forward_return_label import (
    FORWARD_RETURN_LABELS_CREATED,
    NO_FORWARD_RETURN_LABEL_INPUT,
    READY_FOR_FORWARD_RETURN_LABEL,
)
from quant_replay_system.forward_return_label_health import check_forward_return_label_health
from quant_replay_system.forward_return_label_index import DEFAULT_ROOT, build_forward_return_label_index


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"

NO_FORWARD_RETURN_LABEL_ARTIFACT_FOUND = "NO_FORWARD_RETURN_LABEL_ARTIFACT_FOUND"
FORWARD_RETURN_LABEL_HEALTH_FAILED = "FORWARD_RETURN_LABEL_HEALTH_FAILED"

SUMMARY_COLUMNS = [
    "latest_forward_return_label_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "source_replay_decision_freeze_run_id",
    "replay_decision_freeze_status",
    "replay_decision_freeze_health_status",
    "replay_decision_frozen",
    "replay_decisions_exist",
    "ready_for_forward_return_label",
    "forward_return_label_executed",
    "forward_return_label_artifacts_created",
    "forward_labels_allowed",
    "forward_labels_exist",
    "forward_return_labels_created",
    "forward_return_label_artifact_path",
    "label_row_count",
    "label_name_set",
    "symbol_count",
    "training_allowed",
    "weights_trained",
    "training_result_created",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "stock_profile_created",
    "buy_review_allowed",
    "real_buy_review_eligible",
    "approved_for_paper",
    "strategy_performance_validated",
    "trading_allowed",
    "blocker_count",
    "warning_count",
    "report_path",
    "safety_statement",
    "next_action",
]


@dataclass(frozen=True)
class ForwardReturnLabelStatusResult:
    latest_forward_return_label_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    source_replay_decision_freeze_run_id: str
    replay_decision_freeze_status: str
    replay_decision_freeze_health_status: str
    replay_decision_frozen: bool
    replay_decisions_exist: bool
    ready_for_forward_return_label: bool
    forward_return_label_executed: bool
    forward_return_label_artifacts_created: bool
    forward_labels_allowed: bool
    forward_labels_exist: bool
    forward_return_labels_created: bool
    forward_return_label_artifact_path: str
    label_row_count: int
    label_name_set: str
    symbol_count: int
    training_allowed: bool
    weights_trained: bool
    training_result_created: bool
    stock_profile_allowed: bool
    active_stock_profile_exists: bool
    stock_profile_created: bool
    buy_review_allowed: bool
    real_buy_review_eligible: bool
    approved_for_paper: bool
    strategy_performance_validated: bool
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


def run_forward_return_label_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ForwardReturnLabelStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_forward_return_label_index(root=root, output_dir=sibling_root / "index")
    health = check_forward_return_label_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        latest = index.index_frame.sort_values(["generated_at", "forward_return_label_run_id"]).iloc[-1].to_dict()
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
) -> ForwardReturnLabelStatusResult:
    status = _text(latest.get("status"))
    stage = _stage_for_latest(status, _text(latest.get("workflow_stage")), health_status)
    summary = {
        "latest_forward_return_label_run_id": _text(latest.get("forward_return_label_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "source_replay_decision_freeze_run_id": _text(latest.get("source_replay_decision_freeze_run_id")),
        "replay_decision_freeze_status": _text(latest.get("replay_decision_freeze_status")),
        "replay_decision_freeze_health_status": _text(latest.get("replay_decision_freeze_health_status")),
        "replay_decision_frozen": _to_bool(latest.get("replay_decision_frozen")),
        "replay_decisions_exist": _to_bool(latest.get("replay_decisions_exist")),
        "ready_for_forward_return_label": _to_bool(latest.get("ready_for_forward_return_label")),
        "forward_return_label_executed": _to_bool(latest.get("forward_return_label_executed")),
        "forward_return_label_artifacts_created": _to_bool(latest.get("forward_return_label_artifacts_created")),
        "forward_labels_allowed": _to_bool(latest.get("forward_labels_allowed")),
        "forward_labels_exist": _to_bool(latest.get("forward_labels_exist")),
        "forward_return_labels_created": _to_bool(latest.get("forward_return_labels_created")),
        "forward_return_label_artifact_path": _text(latest.get("forward_return_label_artifact_path")),
        "label_row_count": _to_int(latest.get("label_row_count")),
        "label_name_set": _text(latest.get("label_name_set")),
        "symbol_count": _to_int(latest.get("symbol_count")),
        "training_allowed": _to_bool(latest.get("training_allowed")),
        "weights_trained": _to_bool(latest.get("weights_trained")),
        "training_result_created": _to_bool(latest.get("training_result_created")),
        "stock_profile_allowed": _to_bool(latest.get("stock_profile_allowed")),
        "active_stock_profile_exists": _to_bool(latest.get("active_stock_profile_exists")),
        "stock_profile_created": _to_bool(latest.get("stock_profile_created")),
        "buy_review_allowed": _to_bool(latest.get("buy_review_allowed")),
        "real_buy_review_eligible": _to_bool(latest.get("real_buy_review_eligible")),
        "approved_for_paper": _to_bool(latest.get("approved_for_paper")),
        "strategy_performance_validated": _to_bool(latest.get("strategy_performance_validated")),
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
) -> ForwardReturnLabelStatusResult:
    summary = {
        "latest_forward_return_label_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_FORWARD_RETURN_LABEL_ARTIFACT_FOUND,
        "source_replay_decision_freeze_run_id": "",
        "replay_decision_freeze_status": "",
        "replay_decision_freeze_health_status": "",
        "replay_decision_frozen": False,
        "replay_decisions_exist": False,
        "ready_for_forward_return_label": False,
        "forward_return_label_executed": False,
        "forward_return_label_artifacts_created": False,
        "forward_labels_allowed": False,
        "forward_labels_exist": False,
        "forward_return_labels_created": False,
        "forward_return_label_artifact_path": "",
        "label_row_count": 0,
        "label_name_set": "",
        "symbol_count": 0,
        "training_allowed": False,
        "weights_trained": False,
        "training_result_created": False,
        "stock_profile_allowed": False,
        "active_stock_profile_exists": False,
        "stock_profile_created": False,
        "buy_review_allowed": False,
        "real_buy_review_eligible": False,
        "approved_for_paper": False,
        "strategy_performance_validated": False,
        "trading_allowed": False,
        "blocker_count": error_count,
        "warning_count": warning_count,
        "report_path": "",
        "safety_statement": _safety_statement(),
        "next_action": "Run forward-return-label after frozen replay decisions; do not train, create stock_profile, buy-review, paper approval, or trading outputs.",
    }
    return _result(summary, output_dir, root, [f"No forward return label artifacts found under {root}"])


def _result(summary: dict[str, Any], output_dir: str | Path, root: str | Path, warnings: list[str]) -> ForwardReturnLabelStatusResult:
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "forward_return_label_status.csv",
        "status_report": Path(output_dir) / "forward_return_label_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return ForwardReturnLabelStatusResult(
        latest_forward_return_label_run_id=str(summary["latest_forward_return_label_run_id"]),
        status=str(summary["status"]),
        health_status=str(summary["health_status"]),
        workflow_stage=str(summary["workflow_stage"]),
        source_replay_decision_freeze_run_id=str(summary["source_replay_decision_freeze_run_id"]),
        replay_decision_freeze_status=str(summary["replay_decision_freeze_status"]),
        replay_decision_freeze_health_status=str(summary["replay_decision_freeze_health_status"]),
        replay_decision_frozen=bool(summary["replay_decision_frozen"]),
        replay_decisions_exist=bool(summary["replay_decisions_exist"]),
        ready_for_forward_return_label=bool(summary["ready_for_forward_return_label"]),
        forward_return_label_executed=bool(summary["forward_return_label_executed"]),
        forward_return_label_artifacts_created=bool(summary["forward_return_label_artifacts_created"]),
        forward_labels_allowed=bool(summary["forward_labels_allowed"]),
        forward_labels_exist=bool(summary["forward_labels_exist"]),
        forward_return_labels_created=bool(summary["forward_return_labels_created"]),
        forward_return_label_artifact_path=str(summary["forward_return_label_artifact_path"]),
        label_row_count=int(summary["label_row_count"]),
        label_name_set=str(summary["label_name_set"]),
        symbol_count=int(summary["symbol_count"]),
        training_allowed=bool(summary["training_allowed"]),
        weights_trained=bool(summary["weights_trained"]),
        training_result_created=bool(summary["training_result_created"]),
        stock_profile_allowed=bool(summary["stock_profile_allowed"]),
        active_stock_profile_exists=bool(summary["active_stock_profile_exists"]),
        stock_profile_created=bool(summary["stock_profile_created"]),
        buy_review_allowed=bool(summary["buy_review_allowed"]),
        real_buy_review_eligible=bool(summary["real_buy_review_eligible"]),
        approved_for_paper=bool(summary["approved_for_paper"]),
        strategy_performance_validated=bool(summary["strategy_performance_validated"]),
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


def _stage_for_latest(status: str, workflow_stage: str, health_status: str) -> str:
    if health_status == "FAIL":
        return FORWARD_RETURN_LABEL_HEALTH_FAILED
    if workflow_stage:
        return workflow_stage
    if status == NO_FORWARD_RETURN_LABEL_INPUT:
        return "FORWARD_RETURN_LABEL_NO_INPUT"
    if status in {READY_FOR_FORWARD_RETURN_LABEL, FORWARD_RETURN_LABELS_CREATED}:
        return status
    return status or NO_FORWARD_RETURN_LABEL_ARTIFACT_FOUND


def _next_action(stage: str) -> str:
    if stage == FORWARD_RETURN_LABELS_CREATED:
        return "Review report-only future outcome labels; next add research-status only in a separate checkpoint task."
    if stage == READY_FOR_FORWARD_RETURN_LABEL:
        return "Review gates and rerun core with explicit allow only if report-only labels are intended."
    if stage == "FORWARD_RETURN_LABEL_NO_INPUT":
        return "Provide frozen replay decision lineage and price inputs."
    if stage == FORWARD_RETURN_LABEL_HEALTH_FAILED:
        return "Fix health blockers before using forward label context."
    return "Resolve blocker gates; do not train, create stock_profile, buy-review, paper approval, or trading outputs."


def _safety_statement() -> str:
    return (
        "forward_return_label is report-only at this stage; FORWARD_RETURN_LABELS_CREATED means future outcome labels only. "
        "Labels do not train weights, do not create training_result, do not create stock_profile, do not create buy-review eligibility, "
        "do not apply paper approval, do not validate strategy performance, and do not authorize trading."
    )


def _write(result: ForwardReturnLabelStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "status_id": f"{result.latest_forward_return_label_run_id}:{result.workflow_stage}",
                "latest_forward_return_label_run_id": result.latest_forward_return_label_run_id,
                "status": result.status,
                "health_status": result.health_status,
                "workflow_stage": result.workflow_stage,
                "warnings": result.warnings,
                "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
                **result.audit_metadata,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Forward Return Label Status",
                "",
                f"- latest_forward_return_label_run_id: {result.latest_forward_return_label_run_id}",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- forward_return_labels_created: {result.forward_return_labels_created}",
                f"- label_row_count: {result.label_row_count}",
                "",
                result.safety_statement,
                "",
                f"Next action: {result.next_action}",
            ]
        ),
        encoding="utf-8",
    )


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _to_int(value: Any) -> int:
    try:
        if value is None or value == "" or pd.isna(value):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0
