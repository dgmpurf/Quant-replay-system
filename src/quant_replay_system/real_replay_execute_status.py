"""Status summary for report-only real replay execution precheck artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.real_replay_execute import (
    NO_REAL_REPLAY_EXECUTION_INPUT,
    READY_FOR_REAL_REPLAY_EXECUTION_REVIEW,
)
from quant_replay_system.real_replay_execute_health import check_real_replay_execute_health
from quant_replay_system.real_replay_execute_index import (
    DEFAULT_ROOT,
    build_real_replay_execute_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"

NO_REAL_REPLAY_EXECUTION_ARTIFACT_FOUND = "NO_REAL_REPLAY_EXECUTION_ARTIFACT_FOUND"
REAL_REPLAY_EXECUTION_NO_INPUT = "REAL_REPLAY_EXECUTION_NO_INPUT"
REAL_REPLAY_EXECUTION_HEALTH_FAILED = "REAL_REPLAY_EXECUTION_HEALTH_FAILED"
REAL_REPLAY_EXECUTION_PRECHECK_BLOCKED = "REAL_REPLAY_EXECUTION_PRECHECK_BLOCKED"

SUMMARY_COLUMNS = [
    "latest_real_replay_execution_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "ready_for_real_replay_execution_review",
    "source_active_input_creation_run_id",
    "source_active_replay_input_artifact_path",
    "active_replay_input_created",
    "active_replay_input",
    "replay_as_of_date",
    "replay_calendar",
    "symbol_universe_ref",
    "pit_universe_ref",
    "source_registry_ref",
    "raw_document_store_ref",
    "factor_definition_ref",
    "factor_observation_ref",
    "event_structured_ref",
    "company_exposure_ref",
    "evidence_bundle_ref",
    "source_hash_coverage",
    "revision_id_coverage",
    "available_time_policy",
    "taxonomy_coverage",
    "future_labels_excluded",
    "deterministic_only",
    "replay_execution_started",
    "replay_execution_completed",
    "real_replay_executed",
    "replay_execution_allowed",
    "replay_decisions_created",
    "replay_decisions_exist",
    "replay_decision_artifact_path",
    "forward_labels_allowed",
    "forward_labels_exist",
    "training_allowed",
    "weights_trained",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "buy_review_allowed",
    "real_buy_review_eligible",
    "trading_allowed",
    "order_placed",
    "broker_api_called",
    "message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "report_only",
    "diagnostic_only",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "blocker_count",
    "warning_count",
    "report_path",
    "safety_statement",
    "next_action",
]


@dataclass(frozen=True)
class RealReplayExecuteStatusResult:
    latest_real_replay_execution_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    ready_for_real_replay_execution_review: bool
    source_active_input_creation_run_id: str
    source_active_replay_input_artifact_path: str
    active_replay_input_created: bool
    active_replay_input: bool
    replay_as_of_date: str
    replay_calendar: str
    symbol_universe_ref: str
    pit_universe_ref: str
    source_registry_ref: str
    raw_document_store_ref: str
    factor_definition_ref: str
    factor_observation_ref: str
    event_structured_ref: str
    company_exposure_ref: str
    evidence_bundle_ref: str
    source_hash_coverage: str
    revision_id_coverage: str
    available_time_policy: str
    taxonomy_coverage: str
    future_labels_excluded: bool
    deterministic_only: bool
    replay_execution_started: bool
    replay_execution_completed: bool
    real_replay_executed: bool
    replay_execution_allowed: bool
    replay_decisions_created: bool
    replay_decisions_exist: bool
    replay_decision_artifact_path: str
    forward_labels_allowed: bool
    forward_labels_exist: bool
    training_allowed: bool
    weights_trained: bool
    stock_profile_allowed: bool
    active_stock_profile_exists: bool
    buy_review_allowed: bool
    real_buy_review_eligible: bool
    trading_allowed: bool
    order_placed: bool
    broker_api_called: bool
    message_sent: bool
    llm_api_called: bool
    external_api_called: bool
    cache_mutated: bool
    data_raw_written: bool
    data_processed_written: bool
    data_cache_written: bool
    current_candidates_run: bool
    snapshot_built: bool
    signal_semantics_changed: bool
    report_only: bool
    diagnostic_only: bool
    no_live_trading: bool
    no_broker_api: bool
    no_order_placement: bool
    no_message_sent: bool
    blocker_count: int
    warning_count: int
    report_path: str
    safety_statement: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_real_replay_execute_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> RealReplayExecuteStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_real_replay_execute_index(root=root, output_dir=sibling_root / "index")
    health = check_real_replay_execute_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        latest = index.index_frame.sort_values(["generated_at", "real_replay_execution_run_id"]).iloc[-1].to_dict()
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
) -> RealReplayExecuteStatusResult:
    status = _text(latest.get("status"))
    stage = _stage_for_latest(status, _text(latest.get("workflow_stage")), health_status)
    summary = {
        "latest_real_replay_execution_run_id": _text(latest.get("real_replay_execution_run_id")),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "ready_for_real_replay_execution_review": _to_bool(latest.get("ready_for_real_replay_execution_review")),
        "source_active_input_creation_run_id": _text(latest.get("source_active_input_creation_run_id")),
        "source_active_replay_input_artifact_path": _text(latest.get("source_active_replay_input_artifact_path")),
        "active_replay_input_created": _to_bool(latest.get("active_replay_input_created")),
        "active_replay_input": _to_bool(latest.get("active_replay_input")),
        "replay_as_of_date": _text(latest.get("replay_as_of_date")),
        "replay_calendar": _text(latest.get("replay_calendar")),
        "symbol_universe_ref": _text(latest.get("symbol_universe_ref")),
        "pit_universe_ref": _text(latest.get("pit_universe_ref")),
        "source_registry_ref": _text(latest.get("source_registry_ref")),
        "raw_document_store_ref": _text(latest.get("raw_document_store_ref")),
        "factor_definition_ref": _text(latest.get("factor_definition_ref")),
        "factor_observation_ref": _text(latest.get("factor_observation_ref")),
        "event_structured_ref": _text(latest.get("event_structured_ref")),
        "company_exposure_ref": _text(latest.get("company_exposure_ref")),
        "evidence_bundle_ref": _text(latest.get("evidence_bundle_ref")),
        "source_hash_coverage": _text(latest.get("source_hash_coverage")),
        "revision_id_coverage": _text(latest.get("revision_id_coverage")),
        "available_time_policy": _text(latest.get("available_time_policy")),
        "taxonomy_coverage": _text(latest.get("taxonomy_coverage")),
        "future_labels_excluded": _to_bool(latest.get("future_labels_excluded")),
        "deterministic_only": _to_bool(latest.get("deterministic_only")),
        "replay_execution_started": _to_bool(latest.get("replay_execution_started")),
        "replay_execution_completed": _to_bool(latest.get("replay_execution_completed")),
        "real_replay_executed": _to_bool(latest.get("real_replay_executed")),
        "replay_execution_allowed": _to_bool(latest.get("replay_execution_allowed")),
        "replay_decisions_created": _to_bool(latest.get("replay_decisions_created")),
        "replay_decisions_exist": _to_bool(latest.get("replay_decisions_exist")),
        "replay_decision_artifact_path": _text(latest.get("replay_decision_artifact_path")),
        "forward_labels_allowed": _to_bool(latest.get("forward_labels_allowed")),
        "forward_labels_exist": _to_bool(latest.get("forward_labels_exist")),
        "training_allowed": _to_bool(latest.get("training_allowed")),
        "weights_trained": _to_bool(latest.get("weights_trained")),
        "stock_profile_allowed": _to_bool(latest.get("stock_profile_allowed")),
        "active_stock_profile_exists": _to_bool(latest.get("active_stock_profile_exists")),
        "buy_review_allowed": _to_bool(latest.get("buy_review_allowed")),
        "real_buy_review_eligible": _to_bool(latest.get("real_buy_review_eligible")),
        "trading_allowed": _to_bool(latest.get("trading_allowed")),
        "order_placed": _to_bool(latest.get("order_placed")),
        "broker_api_called": _to_bool(latest.get("broker_api_called")),
        "message_sent": _to_bool(latest.get("message_sent")),
        "llm_api_called": _to_bool(latest.get("llm_api_called")),
        "external_api_called": _to_bool(latest.get("external_api_called")),
        "cache_mutated": _to_bool(latest.get("cache_mutated")),
        "data_raw_written": _to_bool(latest.get("data_raw_written")),
        "data_processed_written": _to_bool(latest.get("data_processed_written")),
        "data_cache_written": _to_bool(latest.get("data_cache_written")),
        "current_candidates_run": _to_bool(latest.get("current_candidates_run")),
        "snapshot_built": _to_bool(latest.get("snapshot_built")),
        "signal_semantics_changed": _to_bool(latest.get("signal_semantics_changed")),
        "report_only": _to_bool(latest.get("report_only")),
        "diagnostic_only": _to_bool(latest.get("diagnostic_only")),
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
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
) -> RealReplayExecuteStatusResult:
    summary = {
        "latest_real_replay_execution_run_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_REAL_REPLAY_EXECUTION_ARTIFACT_FOUND,
        "ready_for_real_replay_execution_review": False,
        "source_active_input_creation_run_id": "",
        "source_active_replay_input_artifact_path": "",
        "active_replay_input_created": False,
        "active_replay_input": False,
        "replay_as_of_date": "",
        "replay_calendar": "",
        "symbol_universe_ref": "",
        "pit_universe_ref": "",
        "source_registry_ref": "",
        "raw_document_store_ref": "",
        "factor_definition_ref": "",
        "factor_observation_ref": "",
        "event_structured_ref": "",
        "company_exposure_ref": "",
        "evidence_bundle_ref": "",
        "source_hash_coverage": "",
        "revision_id_coverage": "",
        "available_time_policy": "",
        "taxonomy_coverage": "",
        "future_labels_excluded": True,
        "deterministic_only": True,
        "replay_execution_started": False,
        "replay_execution_completed": False,
        "real_replay_executed": False,
        "replay_execution_allowed": False,
        "replay_decisions_created": False,
        "replay_decisions_exist": False,
        "replay_decision_artifact_path": "",
        "forward_labels_allowed": False,
        "forward_labels_exist": False,
        "training_allowed": False,
        "weights_trained": False,
        "stock_profile_allowed": False,
        "active_stock_profile_exists": False,
        "buy_review_allowed": False,
        "real_buy_review_eligible": False,
        "trading_allowed": False,
        "order_placed": False,
        "broker_api_called": False,
        "message_sent": False,
        "llm_api_called": False,
        "external_api_called": False,
        "cache_mutated": False,
        "data_raw_written": False,
        "data_processed_written": False,
        "data_cache_written": False,
        "current_candidates_run": False,
        "snapshot_built": False,
        "signal_semantics_changed": False,
        "report_only": True,
        "diagnostic_only": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "blocker_count": error_count,
        "warning_count": warning_count,
        "report_path": "",
        "safety_statement": _safety_statement(),
        "next_action": "Run real-replay-execute before artifact views.",
    }
    return _result(summary, output_dir, root, [f"No real replay execution precheck artifacts found under {root}"])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> RealReplayExecuteStatusResult:
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "real_replay_execute_status.csv",
        "status_report": Path(output_dir) / "real_replay_execute_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return RealReplayExecuteStatusResult(
        latest_real_replay_execution_run_id=str(summary["latest_real_replay_execution_run_id"]),
        status=str(summary["status"]),
        health_status=str(summary["health_status"]),
        workflow_stage=str(summary["workflow_stage"]),
        ready_for_real_replay_execution_review=bool(summary["ready_for_real_replay_execution_review"]),
        source_active_input_creation_run_id=str(summary["source_active_input_creation_run_id"]),
        source_active_replay_input_artifact_path=str(summary["source_active_replay_input_artifact_path"]),
        active_replay_input_created=bool(summary["active_replay_input_created"]),
        active_replay_input=bool(summary["active_replay_input"]),
        replay_as_of_date=str(summary["replay_as_of_date"]),
        replay_calendar=str(summary["replay_calendar"]),
        symbol_universe_ref=str(summary["symbol_universe_ref"]),
        pit_universe_ref=str(summary["pit_universe_ref"]),
        source_registry_ref=str(summary["source_registry_ref"]),
        raw_document_store_ref=str(summary["raw_document_store_ref"]),
        factor_definition_ref=str(summary["factor_definition_ref"]),
        factor_observation_ref=str(summary["factor_observation_ref"]),
        event_structured_ref=str(summary["event_structured_ref"]),
        company_exposure_ref=str(summary["company_exposure_ref"]),
        evidence_bundle_ref=str(summary["evidence_bundle_ref"]),
        source_hash_coverage=str(summary["source_hash_coverage"]),
        revision_id_coverage=str(summary["revision_id_coverage"]),
        available_time_policy=str(summary["available_time_policy"]),
        taxonomy_coverage=str(summary["taxonomy_coverage"]),
        future_labels_excluded=bool(summary["future_labels_excluded"]),
        deterministic_only=bool(summary["deterministic_only"]),
        replay_execution_started=bool(summary["replay_execution_started"]),
        replay_execution_completed=bool(summary["replay_execution_completed"]),
        real_replay_executed=bool(summary["real_replay_executed"]),
        replay_execution_allowed=bool(summary["replay_execution_allowed"]),
        replay_decisions_created=bool(summary["replay_decisions_created"]),
        replay_decisions_exist=bool(summary["replay_decisions_exist"]),
        replay_decision_artifact_path=str(summary["replay_decision_artifact_path"]),
        forward_labels_allowed=bool(summary["forward_labels_allowed"]),
        forward_labels_exist=bool(summary["forward_labels_exist"]),
        training_allowed=bool(summary["training_allowed"]),
        weights_trained=bool(summary["weights_trained"]),
        stock_profile_allowed=bool(summary["stock_profile_allowed"]),
        active_stock_profile_exists=bool(summary["active_stock_profile_exists"]),
        buy_review_allowed=bool(summary["buy_review_allowed"]),
        real_buy_review_eligible=bool(summary["real_buy_review_eligible"]),
        trading_allowed=bool(summary["trading_allowed"]),
        order_placed=bool(summary["order_placed"]),
        broker_api_called=bool(summary["broker_api_called"]),
        message_sent=bool(summary["message_sent"]),
        llm_api_called=bool(summary["llm_api_called"]),
        external_api_called=bool(summary["external_api_called"]),
        cache_mutated=bool(summary["cache_mutated"]),
        data_raw_written=bool(summary["data_raw_written"]),
        data_processed_written=bool(summary["data_processed_written"]),
        data_cache_written=bool(summary["data_cache_written"]),
        current_candidates_run=bool(summary["current_candidates_run"]),
        snapshot_built=bool(summary["snapshot_built"]),
        signal_semantics_changed=bool(summary["signal_semantics_changed"]),
        report_only=bool(summary["report_only"]),
        diagnostic_only=bool(summary["diagnostic_only"]),
        no_live_trading=bool(summary["no_live_trading"]),
        no_broker_api=bool(summary["no_broker_api"]),
        no_order_placement=bool(summary["no_order_placement"]),
        no_message_sent=bool(summary["no_message_sent"]),
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


def _write(result: RealReplayExecuteStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Real Replay Execution Precheck Status",
                "",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_real_replay_execution_run_id: {result.latest_real_replay_execution_run_id}",
                f"- ready_for_real_replay_execution_review: {result.ready_for_real_replay_execution_review}",
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
                "latest_real_replay_execution_run_id": result.latest_real_replay_execution_run_id,
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
        return REAL_REPLAY_EXECUTION_HEALTH_FAILED
    if status == NO_REAL_REPLAY_EXECUTION_INPUT:
        return REAL_REPLAY_EXECUTION_NO_INPUT
    if status == READY_FOR_REAL_REPLAY_EXECUTION_REVIEW:
        return READY_FOR_REAL_REPLAY_EXECUTION_REVIEW
    return latest_stage or REAL_REPLAY_EXECUTION_PRECHECK_BLOCKED


def _next_action(stage: str) -> str:
    if stage == REAL_REPLAY_EXECUTION_NO_INPUT:
        return "Supply report-only real replay pre-execution manifests; do not run replay."
    if stage == READY_FOR_REAL_REPLAY_EXECUTION_REVIEW:
        return "Review real replay execution readiness before any separate future implementation; do not run replay here."
    if stage == REAL_REPLAY_EXECUTION_HEALTH_FAILED:
        return "Fix real replay execution precheck artifact health issues before any later workflow."
    return "Resolve real replay precheck blockers without executing replay or creating decisions."


def _safety_statement() -> str:
    return (
        "This workflow is report-only and diagnostic-only. Current real-replay-execute is "
        "pre-execution review-ready only; it does not run replay; does not create replay decisions; "
        "does not compute labels; does not train weights; does not create stock_profile; does not "
        "create buy-review eligibility; and does not authorize trading."
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
