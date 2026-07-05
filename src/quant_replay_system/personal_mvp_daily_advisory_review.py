"""Personal MVP daily advisory review surface.

This module aggregates existing local advisory report artifacts into a
human-readable daily review surface. It does not run upstream workflows.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd


DAILY_ADVISORY_REVIEW_READY_FOR_MANUAL_REVIEW = "DAILY_ADVISORY_REVIEW_READY_FOR_MANUAL_REVIEW"
DAILY_ADVISORY_REVIEW_NO_LOCAL_CONTEXT = "DAILY_ADVISORY_REVIEW_NO_LOCAL_CONTEXT"
DAILY_ADVISORY_REVIEW_STALE_CONTEXT_REVIEW_REQUIRED = "DAILY_ADVISORY_REVIEW_STALE_CONTEXT_REVIEW_REQUIRED"
DAILY_ADVISORY_REVIEW_BLOCKED_CONTEXT_REVIEW_REQUIRED = "DAILY_ADVISORY_REVIEW_BLOCKED_CONTEXT_REVIEW_REQUIRED"
DAILY_ADVISORY_REVIEW_DEMO_ONLY_CONTEXT = "DAILY_ADVISORY_REVIEW_DEMO_ONLY_CONTEXT"
DAILY_ADVISORY_REVIEW_FAILED_SAFETY_CHECK = "DAILY_ADVISORY_REVIEW_FAILED_SAFETY_CHECK"

OUTPUT_FILES = {
    "metadata": "metadata.json",
    "daily_advisory_review_report": "daily_advisory_review_report.md",
    "daily_advisory_review_rows": "daily_advisory_review_rows.csv",
    "daily_advisory_review_summary": "daily_advisory_review_summary.csv",
    "single_symbol_drilldown_index": "single_symbol_drilldown_index.csv",
    "manual_review_checklist": "manual_review_checklist.csv",
    "safety_flags": "safety_flags.json",
}

REQUIRED_FALSE_SAFETY_FIELDS = [
    "real_buy_review_approved",
    "buy_review_allowed",
    "trading_allowed",
    "broker_api_called",
    "broker_api_approved",
    "order_placed",
    "order_placement_approved",
    "message_sent",
    "message_delivery_approved",
    "external_api_called",
    "llm_api_called",
    "active_replay_input_created",
    "active_replay_input_approved",
    "real_replay_execution_approved",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_mutated",
    "labels_created",
    "training_dataset_created",
    "model_training_performed",
    "stock_profile_created",
    "strategy_performance_validated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]

REQUIRED_TRUE_SAFETY_FIELDS = [
    "report_only",
    "diagnostic_only",
    "local_only",
    "manual_confirmation_required",
]

ROW_COLUMNS = [
    "daily_review_run_id",
    "review_date",
    "symbol",
    "name",
    "instrument_type",
    "universe_name",
    "signal_date",
    "decision_date",
    "source_component",
    "source_run_id",
    "source_artifact_path",
    "advisory_action",
    "review_bucket",
    "reason_summary",
    "confidence_level",
    "final_score",
    "risk_notes",
    "data_source_notes",
    "entry_condition",
    "exit_condition",
    "invalidation_condition",
    "valid_until",
    "demo_mode",
    "not_strategy_recommendation",
    "blocked_reason",
    "not_found_reason",
    "stale_context_reason",
    "linked_single_symbol_answer_path",
    "linked_conversation_report_path",
    "linked_paper_context_path",
    "manual_confirmation_required",
    "auto_order_allowed",
    "no_live_trading",
    "no_broker_api",
    "no_message_sent",
    "next_manual_check",
    "manual_note_placeholder",
    "non_approval_statement",
]

DRILLDOWN_COLUMNS = [
    "daily_review_run_id",
    "symbol",
    "name",
    "latest_advisory_action",
    "single_symbol_advisory_run_id",
    "single_symbol_answer_run_id",
    "answer_markdown_path",
    "answer_status",
    "answer_health_status",
    "answer_question",
    "answer_style",
    "conversation_run_id",
    "conversation_original_question",
    "conversation_parsed_intent",
    "conversation_status",
    "conversation_report_path",
    "source_artifact_path",
    "validity_context",
    "invalidation_condition",
    "risk_notes",
    "data_source_notes",
    "manual_confirmation_required",
    "not_found",
    "demo_mode",
    "blocked",
    "next_manual_check",
]

CHECKLIST_ROWS = [
    ("confirm_artifact_date", "Confirm artifact date and source run.", "decision_date"),
    ("confirm_advisory_label", "Confirm advisory label and review bucket.", "advisory_action"),
    ("confirm_demo_blocked_not_found_stale", "Confirm demo, blocked, not-found, and stale context.", "review_bucket"),
    ("read_reason_summary", "Read reason summary.", "reason_summary"),
    ("read_risk_and_data_notes", "Read risk notes and data source notes.", "risk_notes"),
    ("read_validity_and_invalidation", "Read validity and invalidation condition.", "invalidation_condition"),
    ("open_single_symbol_answer", "Open single-symbol answer when present.", "linked_single_symbol_answer_path"),
    ("inspect_optional_paper_context", "Inspect optional paper-context link when present.", "linked_paper_context_path"),
    ("record_manual_note", "Record manual note.", "manual_note_placeholder"),
    (
        "confirm_no_order_message_broker_trading",
        "Confirm no order, message, broker, or trading action follows from this report.",
        "non_approval_statement",
    ),
]


@dataclass(frozen=True)
class PersonalMvpDailyAdvisoryReviewResult:
    daily_review_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    row_count: int
    warning_count: int
    artifact_paths: dict[str, Path]
    rows: pd.DataFrame
    summary: pd.DataFrame
    drilldown: pd.DataFrame
    checklist: pd.DataFrame
    audit_metadata: dict[str, Any]
    warnings: list[str]


def run_personal_mvp_daily_advisory_review(
    *,
    root: str | Path = "outputs/reports",
    output_dir: str | Path | None = None,
    review_date: str | None = None,
    run_id: str | None = None,
    max_symbols: int | None = None,
    include_paper_context: bool = True,
    stale_after_days: int = 7,
) -> PersonalMvpDailyAdvisoryReviewResult:
    """Build a local report-only daily advisory review from existing artifacts."""

    root_path = Path(root)
    output_base = Path(output_dir) if output_dir is not None else Path("outputs/reports/personal_mvp_daily_advisory_review")
    _validate_output_base(output_base)
    effective_review_date = review_date or date.today().isoformat()
    generated_at = datetime.now().isoformat(timespec="seconds")
    rows = _discover_rows(
        root_path=root_path,
        review_date=effective_review_date,
        stale_after_days=stale_after_days,
        max_symbols=max_symbols,
        include_paper_context=include_paper_context,
    )
    if run_id is None:
        run_id = _generate_run_id(root_path, effective_review_date, rows)
    artifact_dir = (output_base / run_id).resolve()
    if not _is_relative_to(artifact_dir, output_base.resolve()):
        raise ValueError("Output artifact path escapes requested output root")

    rows = rows.copy()
    if not rows.empty:
        rows["daily_review_run_id"] = run_id
    rows = _finalize_frame(rows, ROW_COLUMNS)
    status, health_status, warnings = _infer_status(rows)
    summary = _build_summary(run_id, effective_review_date, status, health_status, rows, warnings, include_paper_context)
    drilldown = _build_drilldown(rows, root_path, run_id)
    checklist = _build_checklist(rows, run_id)
    paths = _paths(artifact_dir)
    safety_flags = _safety_flags()
    audit_metadata = {
        **safety_flags,
        "daily_review_run_id": run_id,
        "status": status,
        "health_status": health_status,
        "workflow_stage": status,
        "root": str(root_path),
        "review_date": effective_review_date,
        "generated_at": generated_at,
        "row_count": int(len(rows)),
        "warning_count": len(warnings),
        "include_paper_context": bool(include_paper_context),
        "recommended_next_manual_action": _next_manual_action(status),
        "artifact_paths": {key: str(value) for key, value in paths.items()},
    }

    artifact_dir.mkdir(parents=True, exist_ok=True)
    rows.to_csv(paths["daily_advisory_review_rows"], index=False)
    summary.to_csv(paths["daily_advisory_review_summary"], index=False)
    drilldown.to_csv(paths["single_symbol_drilldown_index"], index=False)
    checklist.to_csv(paths["manual_review_checklist"], index=False)
    paths["safety_flags"].write_text(json.dumps(safety_flags, indent=2, sort_keys=True), encoding="utf-8")
    paths["metadata"].write_text(json.dumps(audit_metadata, indent=2, sort_keys=True), encoding="utf-8")
    paths["daily_advisory_review_report"].write_text(
        _render_report(run_id, status, health_status, effective_review_date, rows, summary.iloc[0].to_dict(), warnings),
        encoding="utf-8",
    )

    return PersonalMvpDailyAdvisoryReviewResult(
        daily_review_run_id=run_id,
        status=status,
        health_status=health_status,
        workflow_stage=status,
        row_count=int(len(rows)),
        warning_count=len(warnings),
        artifact_paths=paths,
        rows=rows,
        summary=summary,
        drilldown=drilldown,
        checklist=checklist,
        audit_metadata=audit_metadata,
        warnings=warnings,
    )


def _discover_rows(
    *,
    root_path: Path,
    review_date: str,
    stale_after_days: int,
    max_symbols: int | None,
    include_paper_context: bool,
) -> pd.DataFrame:
    signal_rows = _signal_rows(root_path, review_date, stale_after_days)
    if signal_rows and max_symbols is not None:
        signal_rows = signal_rows[: max(0, max_symbols)]
    if not signal_rows:
        signal_rows = _not_found_rows(root_path, review_date)
    answer_by_symbol = _answer_metadata_by_symbol(root_path)
    conversation_by_symbol = _conversation_metadata_by_symbol(root_path)
    paper_path = _latest_paper_context_path(root_path) if include_paper_context else ""
    for row in signal_rows:
        symbol = str(row.get("symbol", ""))
        answer = answer_by_symbol.get(symbol, {})
        conversation = conversation_by_symbol.get(symbol, {})
        if answer:
            row["linked_single_symbol_answer_path"] = _string(answer.get("answer_markdown_path"))
        if conversation:
            row["linked_conversation_report_path"] = _string(conversation.get("report_path"))
        if paper_path:
            row["linked_paper_context_path"] = paper_path
    return pd.DataFrame(signal_rows)


def _signal_rows(root_path: Path, review_date: str, stale_after_days: int) -> list[dict[str, Any]]:
    artifact = _latest_child_with_file(root_path / "signals", "signals.csv")
    if artifact is None:
        return []
    signals_path = artifact / "signals.csv"
    metadata = _read_json(artifact / "metadata.json")
    frame = pd.read_csv(signals_path, dtype={"symbol": str}, keep_default_na=False)
    rows: list[dict[str, Any]] = []
    for record in frame.to_dict(orient="records"):
        action = _string(record.get("advisory_action")) or "NO_ACTION"
        stale_reason = _stale_reason(_string(record.get("decision_date")) or _string(record.get("signal_date")), review_date, stale_after_days)
        row = {
            "review_date": review_date,
            "symbol": _string(record.get("symbol")),
            "name": _string(record.get("name")),
            "instrument_type": _string(record.get("instrument_type")),
            "universe_name": _string(record.get("universe_name")),
            "signal_date": _string(record.get("signal_date")),
            "decision_date": _string(record.get("decision_date")),
            "source_component": "signal_advisory",
            "source_run_id": _string(record.get("signal_run_id")) or _string(metadata.get("signal_run_id")),
            "source_artifact_path": str(signals_path),
            "advisory_action": action,
            "review_bucket": _review_bucket(action),
            "reason_summary": _string(record.get("reason_summary")),
            "confidence_level": _string(record.get("confidence_level")),
            "final_score": _string(record.get("final_score")),
            "risk_notes": _string(record.get("risk_notes")),
            "data_source_notes": _string(record.get("data_source_notes")),
            "entry_condition": _string(record.get("entry_condition")),
            "exit_condition": _string(record.get("exit_condition")),
            "invalidation_condition": _string(record.get("invalidation_condition")),
            "valid_until": _string(record.get("valid_until")),
            "demo_mode": _bool(record.get("demo_mode")),
            "not_strategy_recommendation": _bool(record.get("not_strategy_recommendation")),
            "blocked_reason": _string(record.get("blocked_reason")) or _string(record.get("risk_precheck_reason")),
            "not_found_reason": "",
            "stale_context_reason": stale_reason,
            "linked_single_symbol_answer_path": "",
            "linked_conversation_report_path": "",
            "linked_paper_context_path": "",
            "manual_confirmation_required": True,
            "auto_order_allowed": False,
            "no_live_trading": True,
            "no_broker_api": True,
            "no_message_sent": True,
            "next_manual_check": _next_manual_check(action),
            "manual_note_placeholder": "",
            "non_approval_statement": "local advisory review context; manual confirmation required; not an order.",
        }
        rows.append(row)
    return rows


def _not_found_rows(root_path: Path, review_date: str) -> list[dict[str, Any]]:
    rows = []
    for metadata in _metadata_files(root_path / "single_symbol_advisory_answer"):
        payload = _read_json(metadata)
        stage = _string(payload.get("workflow_stage")) or _string(payload.get("status"))
        if "NOT_FOUND" not in stage:
            continue
        symbol = _string(payload.get("symbol"))
        rows.append(
            {
                "review_date": review_date,
                "symbol": symbol,
                "name": "",
                "instrument_type": "",
                "universe_name": "",
                "signal_date": "",
                "decision_date": "",
                "source_component": "single_symbol_advisory_answer",
                "source_run_id": _string(payload.get("answer_run_id")),
                "source_artifact_path": str(metadata),
                "advisory_action": "NOT_FOUND",
                "review_bucket": "NOT_FOUND",
                "reason_summary": "No recommendation was invented.",
                "confidence_level": "",
                "final_score": "",
                "risk_notes": "",
                "data_source_notes": "",
                "entry_condition": "",
                "exit_condition": "",
                "invalidation_condition": "",
                "valid_until": "",
                "demo_mode": False,
                "not_strategy_recommendation": True,
                "blocked_reason": "",
                "not_found_reason": "No local evidence for the requested symbol.",
                "stale_context_reason": "",
                "linked_single_symbol_answer_path": _string(payload.get("answer_markdown_path")),
                "linked_conversation_report_path": "",
                "linked_paper_context_path": "",
                "manual_confirmation_required": True,
                "auto_order_allowed": False,
                "no_live_trading": True,
                "no_broker_api": True,
                "no_message_sent": True,
                "next_manual_check": "No local evidence for the requested symbol.",
                "manual_note_placeholder": "",
                "non_approval_statement": "local advisory review context; manual confirmation required; not an order.",
            }
        )
    return rows


def _answer_metadata_by_symbol(root_path: Path) -> dict[str, dict[str, Any]]:
    result = {}
    for metadata in _metadata_files(root_path / "single_symbol_advisory_answer"):
        payload = _read_json(metadata)
        symbol = _string(payload.get("symbol"))
        if symbol:
            result[symbol] = payload
    return result


def _conversation_metadata_by_symbol(root_path: Path) -> dict[str, dict[str, Any]]:
    result = {}
    for metadata in _metadata_files(root_path / "advisory_conversation"):
        payload = _read_json(metadata)
        symbol = _string(payload.get("parsed_symbol"))
        if symbol:
            result[symbol] = payload
    return result


def _build_drilldown(rows: pd.DataFrame, root_path: Path, run_id: str) -> pd.DataFrame:
    answers = _answer_metadata_by_symbol(root_path)
    conversations = _conversation_metadata_by_symbol(root_path)
    drill_rows = []
    for row in rows.to_dict(orient="records"):
        symbol = _string(row.get("symbol"))
        answer = answers.get(symbol, {})
        conversation = conversations.get(symbol, {})
        drill_rows.append(
            {
                "daily_review_run_id": run_id,
                "symbol": symbol,
                "name": _string(row.get("name")),
                "latest_advisory_action": _string(row.get("advisory_action")),
                "single_symbol_advisory_run_id": _string(answer.get("advisory_run_id")),
                "single_symbol_answer_run_id": _string(answer.get("answer_run_id")),
                "answer_markdown_path": _string(answer.get("answer_markdown_path")) or _string(row.get("linked_single_symbol_answer_path")),
                "answer_status": _string(answer.get("status")),
                "answer_health_status": _string(answer.get("health_status")),
                "answer_question": _string(answer.get("question")),
                "answer_style": _string(answer.get("answer_style")),
                "conversation_run_id": _string(conversation.get("conversation_run_id")),
                "conversation_original_question": _string(conversation.get("original_question")),
                "conversation_parsed_intent": _string(conversation.get("parsed_intent")),
                "conversation_status": _string(conversation.get("status")),
                "conversation_report_path": _string(conversation.get("report_path")) or _string(row.get("linked_conversation_report_path")),
                "source_artifact_path": _string(row.get("source_artifact_path")),
                "validity_context": _string(row.get("valid_until")),
                "invalidation_condition": _string(row.get("invalidation_condition")),
                "risk_notes": _string(row.get("risk_notes")),
                "data_source_notes": _string(row.get("data_source_notes")),
                "manual_confirmation_required": True,
                "not_found": _string(row.get("advisory_action")) == "NOT_FOUND",
                "demo_mode": _bool(row.get("demo_mode")),
                "blocked": _string(row.get("advisory_action")) == "BLOCKED",
                "next_manual_check": _string(row.get("next_manual_check")),
            }
        )
    return _finalize_frame(pd.DataFrame(drill_rows), DRILLDOWN_COLUMNS)


def _build_checklist(rows: pd.DataFrame, run_id: str) -> pd.DataFrame:
    checklist = []
    for row in rows.to_dict(orient="records"):
        for check_id, label, source_field in CHECKLIST_ROWS:
            checklist.append(
                {
                    "daily_review_run_id": run_id,
                    "symbol": _string(row.get("symbol")),
                    "check_id": check_id,
                    "check_label": label,
                    "check_status": "PENDING_MANUAL_REVIEW",
                    "source_field": source_field,
                    "source_artifact_path": _string(row.get("source_artifact_path")),
                    "manual_note_placeholder": "",
                    "blocking_if_unchecked": True,
                }
            )
    return pd.DataFrame(checklist)


def _build_summary(
    run_id: str,
    review_date: str,
    status: str,
    health_status: str,
    rows: pd.DataFrame,
    warnings: list[str],
    include_paper_context: bool,
) -> pd.DataFrame:
    actions = rows["advisory_action"].tolist() if "advisory_action" in rows else []
    summary = {
        "daily_review_run_id": run_id,
        "review_date": review_date,
        "status": status,
        "health_status": health_status,
        "row_count": len(rows),
        "watch_count": actions.count("WATCH"),
        "review_buy_candidate_count": actions.count("REVIEW_BUY_CANDIDATE"),
        "review_sell_candidate_count": actions.count("REVIEW_SELL_CANDIDATE"),
        "hold_review_count": actions.count("HOLD_REVIEW"),
        "no_action_count": actions.count("NO_ACTION"),
        "blocked_count": actions.count("BLOCKED"),
        "demo_count": actions.count("DEMO_ONLY"),
        "not_found_count": actions.count("NOT_FOUND"),
        "stale_artifact_count": int(rows["stale_context_reason"].astype(bool).sum()) if "stale_context_reason" in rows else 0,
        "missing_artifact_count": 1 if len(rows) == 0 else 0,
        "warning_count": len(warnings),
        "manual_confirmation_required": True,
        "include_paper_context": include_paper_context,
        "recommended_next_manual_action": _next_manual_action(status),
    }
    return pd.DataFrame([summary])


def _infer_status(rows: pd.DataFrame) -> tuple[str, str, list[str]]:
    if rows.empty:
        return DAILY_ADVISORY_REVIEW_NO_LOCAL_CONTEXT, "WARN", ["No local advisory context was found."]
    actions = set(rows["advisory_action"].astype(str))
    warnings: list[str] = []
    if rows["stale_context_reason"].astype(bool).any():
        warnings.append("One or more artifacts are stale.")
        return DAILY_ADVISORY_REVIEW_STALE_CONTEXT_REVIEW_REQUIRED, "WARN", warnings
    if "BLOCKED" in actions:
        warnings.append("One or more rows are blocked.")
        return DAILY_ADVISORY_REVIEW_BLOCKED_CONTEXT_REVIEW_REQUIRED, "WARN", warnings
    if actions == {"DEMO_ONLY"}:
        return DAILY_ADVISORY_REVIEW_DEMO_ONLY_CONTEXT, "PASS", warnings
    return DAILY_ADVISORY_REVIEW_READY_FOR_MANUAL_REVIEW, "PASS", warnings


def _render_report(
    run_id: str,
    status: str,
    health_status: str,
    review_date: str,
    rows: pd.DataFrame,
    summary: dict[str, Any],
    warnings: list[str],
) -> str:
    lines = [
        "# Personal MVP Daily Advisory Review",
        "",
        "This report is local advisory review context.",
        "manual confirmation required.",
        "This report is not an order.",
        "This report is not broker, order, message, or trading authorization.",
        "This report does not create real buy-review eligibility.",
        "This report does not validate strategy performance.",
        "This report does not mutate signal semantics.",
        "This report does not run current-candidates or snapshots.",
        "This report does not write protected data paths.",
        "No orders were placed.",
        "No messages were sent.",
        "No broker API was invoked.",
        "No trading was authorized.",
        "",
        f"daily_review_run_id: {run_id}",
        f"review_date: {review_date}",
        f"status: {status}",
        f"health_status: {health_status}",
        f"row_count: {summary.get('row_count', 0)}",
        "",
        "## Action Wording",
        "",
        "- DEMO_ONLY = workflow validation context only.",
        "- WATCH = observe and review only.",
        "- REVIEW_BUY_CANDIDATE = manual review candidate only.",
        "- REVIEW_SELL_CANDIDATE = manual review candidate only.",
        "- HOLD_REVIEW = continue review only.",
        "- NO_ACTION = no local action from artifact.",
        "- BLOCKED = inspect blocker before downstream interpretation.",
        "- NOT_FOUND = no local evidence for the requested symbol. No recommendation was invented.",
        "- STALE = artifact freshness requires review before use.",
        "",
        "## Warnings",
    ]
    lines.extend([f"- {warning}" for warning in warnings] or ["- None."])
    lines.extend(["", "## Rows", ""])
    if rows.empty:
        lines.append("No local advisory context was found. No recommendation was invented.")
    else:
        lines.append("| symbol | action | bucket | next manual check |")
        lines.append("|---|---|---|---|")
        for row in rows.to_dict(orient="records"):
            lines.append(
                "| {symbol} | {action} | {bucket} | {check} |".format(
                    symbol=_string(row.get("symbol")),
                    action=_string(row.get("advisory_action")),
                    bucket=_string(row.get("review_bucket")),
                    check=_string(row.get("next_manual_check")),
                )
            )
    return "\n".join(lines) + "\n"


def _review_bucket(action: str) -> str:
    if action in {"REVIEW_BUY_CANDIDATE", "REVIEW_SELL_CANDIDATE"}:
        return "MANUAL_REVIEW"
    return action


def _next_manual_check(action: str) -> str:
    return {
        "DEMO_ONLY": "Workflow validation context only.",
        "WATCH": "Observe and review only.",
        "REVIEW_BUY_CANDIDATE": "Manual review candidate only.",
        "REVIEW_SELL_CANDIDATE": "Manual review candidate only.",
        "HOLD_REVIEW": "Continue review only.",
        "NO_ACTION": "No local action from artifact.",
        "BLOCKED": "Inspect blocker before downstream interpretation.",
        "NOT_FOUND": "No local evidence for the requested symbol.",
    }.get(action, "Manual confirmation required.")


def _next_manual_action(status: str) -> str:
    if status == DAILY_ADVISORY_REVIEW_NO_LOCAL_CONTEXT:
        return "No local advisory context was found; run or inspect existing advisory artifacts first."
    if status == DAILY_ADVISORY_REVIEW_STALE_CONTEXT_REVIEW_REQUIRED:
        return "Review stale artifact context before relying on this daily readout."
    if status == DAILY_ADVISORY_REVIEW_BLOCKED_CONTEXT_REVIEW_REQUIRED:
        return "Inspect blocked rows before downstream interpretation."
    return "Review the daily advisory report manually."


def _safety_flags() -> dict[str, bool]:
    flags = {field: False for field in REQUIRED_FALSE_SAFETY_FIELDS}
    flags.update({field: True for field in REQUIRED_TRUE_SAFETY_FIELDS})
    return flags


def _paths(artifact_dir: Path) -> dict[str, Path]:
    return {key: artifact_dir / filename for key, filename in OUTPUT_FILES.items()} | {"artifact_dir": artifact_dir}


def _generate_run_id(root_path: Path, review_date: str, rows: pd.DataFrame) -> str:
    payload = {
        "root": str(root_path),
        "review_date": review_date,
        "symbols": rows["symbol"].astype(str).tolist() if "symbol" in rows else [],
        "actions": rows["advisory_action"].astype(str).tolist() if "advisory_action" in rows else [],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _latest_child_with_file(root: Path, filename: str) -> Path | None:
    if not root.exists():
        return None
    candidates = [path.parent for path in root.glob(f"*/{filename}") if path.is_file()]
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: (path.stat().st_mtime, str(path)), reverse=True)[0]


def _metadata_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted([path for path in root.glob("*/metadata.json") if path.is_file()])


def _latest_paper_context_path(root_path: Path) -> str:
    artifact = _latest_child_with_file(root_path / "paper_trading" / "workflow_status", "metadata.json")
    if artifact is None:
        return ""
    metadata = _read_json(artifact / "metadata.json")
    return _string(metadata.get("report_path")) or _string(metadata.get("paper_workflow_status_report")) or str(
        artifact / "paper_workflow_status_report.md"
    )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _stale_reason(source_date: str, review_date: str, stale_after_days: int) -> str:
    try:
        source = date.fromisoformat(source_date[:10])
        review = date.fromisoformat(review_date[:10])
    except ValueError:
        return "Artifact freshness requires review before use."
    if (review - source).days > stale_after_days:
        return "Artifact freshness requires review before use."
    return ""


def _validate_output_base(output_base: Path) -> None:
    resolved = output_base.resolve()
    cwd = Path.cwd().resolve()
    protected = [
        cwd / "data" / "raw",
        cwd / "data" / "processed",
        cwd / "data" / "cache",
        cwd / "docs" / "project_sources",
        cwd / ".env",
        cwd / "secrets",
    ]
    for root in protected:
        if resolved == root or _is_relative_to(resolved, root):
            raise ValueError(f"Refusing protected output path: {output_base}")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _finalize_frame(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column not in frame.columns:
            frame[column] = ""
    return frame[columns]


def _string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)
