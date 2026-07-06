"""Report-only PIT evidence closure worklist scaffold.

This module builds a review-only worklist for a selected historical replay
sample from existing local report artifacts. It does not close PIT evidence,
approve PIT admissibility, create replay input, or run downstream workflows.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


STATUS_CREATED = "PIT_EVIDENCE_CLOSURE_WORKLIST_CREATED_REPORT_ONLY"
STATUS_WARN_NO_CONTEXT = "PIT_EVIDENCE_CLOSURE_WORKLIST_WARN_NO_CONTEXT"
STATUS_WARN_NEEDS_REVIEW = "PIT_EVIDENCE_CLOSURE_WORKLIST_WARN_NEEDS_REVIEW"
STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT = "PIT_EVIDENCE_CLOSURE_WORKLIST_BLOCKED_BY_UNSAFE_OUTPUT_ROOT"
STATUS_BLOCKED_BY_UNSAFE_INPUT = "PIT_EVIDENCE_CLOSURE_WORKLIST_BLOCKED_BY_UNSAFE_INPUT"
STATUS_HEALTH_FAILED = "PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_FAILED"

WORKFLOW_STAGE = "HISTORICAL_REPLAY_PIT_EVIDENCE_CLOSURE_WORKLIST_CREATED_REPORT_ONLY"
DEFAULT_OUTPUT_ROOT = Path(
    "outputs/reports/manual_diagnostics/historical_replay_pit_evidence_closure_worklist_v0_1"
)
RECOMMENDED_NEXT_TASK = (
    "Historical Replay Official Status Evidence Packet Closure Planning for 2024-04-02 etf_core Report-Only v0.1"
)

OUTPUT_FILES = {
    "metadata": "metadata.json",
    "worklist": "historical_replay_pit_evidence_closure_worklist.csv",
    "report": "historical_replay_pit_evidence_closure_worklist_report.md",
    "summary": "historical_replay_pit_evidence_closure_worklist_summary.csv",
    "blocker_summary": "blocker_summary.csv",
    "safety_flags": "safety_flags.json",
}

SAFETY_FALSE_FIELDS = [
    "pit_evidence_closed",
    "pit_admissibility_approved",
    "active_replay_input",
    "replay_execution_allowed",
    "replay_decision_freeze_allowed",
    "forward_labels_created",
    "training_dataset_created",
    "metric_computation_performed",
    "model_training_performed",
    "stock_profile_validation_created",
    "paper_expansion_allowed",
    "buy_review_allowed",
    "trading_allowed",
    "broker_api_called",
    "order_placed",
    "message_sent",
    "external_api_called",
    "llm_api_called",
    "current_candidates_executed",
    "snapshot_built",
    "signal_semantics_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "source_hash_validated",
]

REQUIRED_ROW_FIELDS = [
    "worklist_run_id",
    "source_artifact_family",
    "source_artifact_id",
    "signal_date",
    "universe_name",
    "symbol",
    "symbol_name_hint",
    "instrument_type",
    "exchange_or_market",
    "legacy_universe_label",
    "recommended_profile",
    "profile_conflict_flag",
    "profile_conflict_reason",
    "profile_policy_status",
    "listed_status_evidence",
    "listed_status_source_id",
    "listed_status_available_time",
    "delisted_status_evidence",
    "delisted_status_source_id",
    "st_status_evidence",
    "st_status_not_applicable_reason",
    "suspension_status_evidence",
    "trading_status_not_applicable_reason",
    "universe_membership_evidence",
    "universe_membership_source_id",
    "source_id",
    "source_name",
    "source_type",
    "permission_class",
    "raw_reference",
    "raw_reference_type",
    "source_hash_preview",
    "source_hash_disclosure_level",
    "local_file_hash_preview",
    "local_file_hash_disclosure_level",
    "revision_id",
    "revision_id_type",
    "available_time",
    "available_time_timezone",
    "fetch_time",
    "review_time",
    "timing_relation_to_decision",
    "reviewer_id",
    "reviewer_role",
    "reviewer_scope",
    "reviewer_attestation",
    "searched_source",
    "query_window",
    "no_hit_result",
    "no_hit_acceptance_status",
    "no_hit_rationale",
    "permission_status",
    "quality_status",
    "limitation_note",
    "blocker_reason",
    "blocker_status",
    "survivorship_warning_flag",
    "survivorship_rationale",
    "survivorship_source_id",
    "survivorship_available_time",
    "survivorship_review_status",
    "context_only_flag",
    "closure_status",
    "closure_status_reason",
]

ROW_FIELDS = REQUIRED_ROW_FIELDS + SAFETY_FALSE_FIELDS

PROTECTED_PATH_PARTS = [
    ("data", "raw"),
    ("data", "processed"),
    ("data", "cache"),
    ("docs", "project_sources"),
]


@dataclass(frozen=True)
class HistoricalReplayPitEvidenceClosureWorklistResult:
    worklist_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    row_count: int
    artifact_paths: dict[str, Path]
    metadata: dict[str, Any]
    rows: list[dict[str, Any]]


def run_historical_replay_pit_evidence_closure_worklist(
    *,
    root: str | Path,
    output_dir: str | Path | None = None,
    run_id: str | None = None,
    signal_date: str = "2024-04-02",
    universe_name: str = "etf_core",
) -> HistoricalReplayPitEvidenceClosureWorklistResult:
    """Build a report-only PIT evidence closure worklist scaffold."""

    root_path = Path(root)
    output_base = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_ROOT
    _validate_output_root(output_base)

    artifact_context = _discover_context(root_path, signal_date, universe_name)
    rows = _build_rows(artifact_context, signal_date, universe_name)
    if run_id is None:
        run_id = _generate_run_id(root_path, signal_date, universe_name, rows)

    artifact_dir = (output_base / run_id).resolve()
    output_base_resolved = output_base.resolve()
    if not _is_relative_to(artifact_dir, output_base_resolved):
        raise ValueError("Output artifact path escapes requested output root")

    rows = [_with_run_id(row, run_id) for row in rows]
    status = STATUS_CREATED if rows else STATUS_WARN_NO_CONTEXT
    health_status = "WARN" if status == STATUS_WARN_NO_CONTEXT or any(row["closure_status"] == "blocked" for row in rows) else "PASS"
    paths = _paths(artifact_dir)
    safety = _safety_flags()
    metadata = _metadata(
        run_id=run_id,
        signal_date=signal_date,
        universe_name=universe_name,
        status=status,
        health_status=health_status,
        rows=rows,
        source_families=artifact_context["families_seen"],
        safety=safety,
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)
    _write_json(paths["metadata"], metadata)
    _write_csv(paths["worklist"], rows, ROW_FIELDS)
    _write_report(paths["report"], metadata, rows)
    _write_summary(paths["summary"], metadata)
    _write_blocker_summary(paths["blocker_summary"], rows)
    _write_json(paths["safety_flags"], safety)

    return HistoricalReplayPitEvidenceClosureWorklistResult(
        worklist_run_id=run_id,
        status=status,
        health_status=health_status,
        workflow_stage=WORKFLOW_STAGE,
        row_count=len(rows),
        artifact_paths=paths,
        metadata=metadata,
        rows=rows,
    )


def _discover_context(root: Path, signal_date: str, universe_name: str) -> dict[str, Any]:
    overlay_rows = _read_overlay_rows(root, signal_date, universe_name)
    symbol_summary = _read_symbol_summary(root, universe_name)
    date_summary = _read_date_summary(root, signal_date, universe_name)
    execution_blocker = _read_execution_blocker(root, signal_date, universe_name)
    no_hit_status = _read_no_hit_status(root)
    families_seen = []
    if overlay_rows:
        families_seen.append("point_in_time_universe_overlay_plan")
    if symbol_summary:
        families_seen.append("point_in_time_universe_evidence_review_worklist")
    if execution_blocker:
        families_seen.append("current_candidates_backfill_execution_manifest")
    if no_hit_status != "missing":
        families_seen.append("reviewer_no_hit_source_coverage_acceptance")
    return {
        "overlay_rows": overlay_rows,
        "symbol_summary": symbol_summary,
        "date_summary": date_summary,
        "execution_blocker": execution_blocker,
        "no_hit_status": no_hit_status,
        "families_seen": families_seen,
    }


def _read_overlay_rows(root: Path, signal_date: str, universe_name: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in (root / "point_in_time_universe_overlay_plan").glob("*/point_in_time_universe_overlay_plan.csv"):
        for row in _read_csv(path):
            if row.get("signal_date") == signal_date and row.get("universe_name") == universe_name:
                row["_source_artifact_id"] = path.parent.name
                rows.append(row)
    return rows


def _read_symbol_summary(root: Path, universe_name: str) -> dict[str, dict[str, str]]:
    summaries: dict[str, dict[str, str]] = {}
    for path in (
        root / "point_in_time_universe_evidence_review_worklist"
    ).glob("*/pit_universe_evidence_review_symbol_summary.csv"):
        for row in _read_csv(path):
            if row.get("universe_name") == universe_name and row.get("symbol"):
                row["_source_artifact_id"] = path.parent.name
                summaries[row["symbol"]] = row
    return summaries


def _read_date_summary(root: Path, signal_date: str, universe_name: str) -> dict[str, str]:
    for path in (
        root / "point_in_time_universe_evidence_review_worklist"
    ).glob("*/pit_universe_evidence_review_date_summary.csv"):
        for row in _read_csv(path):
            if row.get("signal_date") == signal_date and row.get("universe_name") == universe_name:
                row["_source_artifact_id"] = path.parent.name
                return row
    return {}


def _read_execution_blocker(root: Path, signal_date: str, universe_name: str) -> dict[str, str]:
    for path in (
        root / "current_candidates_backfill_execution_manifest"
    ).glob("*/current_candidates_backfill_execution_manifest.csv"):
        for row in _read_csv(path):
            if row.get("signal_date") == signal_date and row.get("universe") == universe_name:
                row["_source_artifact_id"] = path.parent.name
                return row
    return {}


def _read_no_hit_status(root: Path) -> str:
    for path in (root / "reviewer_no_hit_source_coverage_acceptance").glob("*/metadata.json"):
        try:
            metadata = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if int(metadata.get("accepted_count", 0) or 0) > 0:
            return "no_hit_accepted_context"
        return "no_hit_review_needed"
    return "missing"


def _build_rows(context: dict[str, Any], signal_date: str, universe_name: str) -> list[dict[str, Any]]:
    rows = []
    for overlay in context["overlay_rows"]:
        symbol = str(overlay.get("symbol", ""))
        summary = context["symbol_summary"].get(symbol, {})
        instrument_type = summary.get("suggested_instrument_type") or _guess_instrument_type(symbol)
        available_time = overlay.get("available_time") or overlay.get("proposed_available_time") or "missing"
        timing_relation = _timing_relation(available_time, signal_date)
        blockers = _blockers(overlay, summary, context, available_time, timing_relation, instrument_type)
        row = {
            "worklist_run_id": "",
            "source_artifact_family": "point_in_time_universe_overlay_plan",
            "source_artifact_id": overlay.get("_source_artifact_id", "unknown"),
            "signal_date": signal_date,
            "universe_name": universe_name,
            "symbol": symbol,
            "symbol_name_hint": summary.get("suggested_name", ""),
            "instrument_type": instrument_type,
            "exchange_or_market": summary.get("suggested_exchange", "missing"),
            "legacy_universe_label": universe_name,
            "recommended_profile": _recommended_profile(instrument_type),
            "profile_conflict_flag": _bool_text(instrument_type == "STOCK"),
            "profile_conflict_reason": "STOCK row under legacy etf_core label" if instrument_type == "STOCK" else "",
            "profile_policy_status": "needs_review" if instrument_type == "STOCK" else "context_only",
            "listed_status_evidence": "missing",
            "listed_status_source_id": "missing",
            "listed_status_available_time": "missing",
            "delisted_status_evidence": "missing",
            "delisted_status_source_id": "missing",
            "st_status_evidence": "missing" if instrument_type == "STOCK" else "not_applicable",
            "st_status_not_applicable_reason": "ETF row requires ETF-specific policy review" if instrument_type == "ETF" else "",
            "suspension_status_evidence": "missing",
            "trading_status_not_applicable_reason": "",
            "universe_membership_evidence": "missing",
            "universe_membership_source_id": "missing",
            "source_id": "missing",
            "source_name": overlay.get("source") or "missing",
            "source_type": "context_only",
            "permission_class": "missing",
            "raw_reference": "context_only_existing_overlay" if overlay.get("base_universe_path") else "missing",
            "raw_reference_type": "overlay_context",
            "source_hash_preview": overlay.get("source_hash_preview") or "missing",
            "source_hash_disclosure_level": "preview_only" if overlay.get("source_hash_preview") else "missing",
            "local_file_hash_preview": overlay.get("local_file_hash_preview") or "missing",
            "local_file_hash_disclosure_level": "preview_only" if overlay.get("local_file_hash_preview") else "missing",
            "revision_id": "missing",
            "revision_id_type": "missing",
            "available_time": available_time,
            "available_time_timezone": "missing",
            "fetch_time": "missing",
            "review_time": "missing",
            "timing_relation_to_decision": timing_relation,
            "reviewer_id": "missing",
            "reviewer_role": "missing",
            "reviewer_scope": "missing",
            "reviewer_attestation": "missing",
            "searched_source": "missing",
            "query_window": "missing",
            "no_hit_result": "missing",
            "no_hit_acceptance_status": context["no_hit_status"],
            "no_hit_rationale": "reviewer no-hit context is not PIT approval" if context["no_hit_status"] == "no_hit_accepted_context" else "missing",
            "permission_status": "missing",
            "quality_status": "needs_review",
            "limitation_note": "Existing overlay/worklist context is review-only and not PIT approval.",
            "blocker_reason": _join_reasons(overlay.get("blocker_reason"), context["execution_blocker"].get("blocker_reason")),
            "blocker_status": ";".join(blockers),
            "survivorship_warning_flag": _bool_text(_is_true(overlay.get("survivorship_bias_warning"))),
            "survivorship_rationale": "missing",
            "survivorship_source_id": "missing",
            "survivorship_available_time": "missing",
            "survivorship_review_status": "missing",
            "context_only_flag": "true",
            "closure_status": "blocked" if blockers else "needs_manual_review",
            "closure_status_reason": "Known evidence blockers remain; worklist row is not PIT approval.",
        }
        row.update({field: "false" for field in SAFETY_FALSE_FIELDS})
        rows.append(row)
    return rows


def _blockers(
    overlay: dict[str, str],
    summary: dict[str, str],
    context: dict[str, Any],
    available_time: str,
    timing_relation: str,
    instrument_type: str,
) -> list[str]:
    blockers = [
        "blocker_missing_source_id",
        "blocker_missing_permission_class",
        "blocker_missing_revision_id",
        "blocker_missing_official_status_evidence",
        "blocker_missing_universe_membership_evidence",
        "blocker_missing_survivorship_rationale",
        "blocker_missing_reviewer_authority",
    ]
    if context["execution_blocker"].get("readiness_status") == "BLOCKED_UNIVERSE_AS_OF":
        blockers.append("blocker_universe_asof_after_signal")
    if _int(context["date_summary"].get("future_dated_hint_count")) > 0 or _int(summary.get("future_dated_hint_count")) > 0:
        blockers.append("blocker_future_dated_hint")
    if _int(context["date_summary"].get("authoritative_hint_count")) == 0 and context["date_summary"]:
        blockers.append("blocker_missing_authoritative_hint")
    if available_time == "missing":
        blockers.append("blocker_missing_available_time")
    if timing_relation == "after_decision":
        blockers.append("blocker_available_time_after_decision")
    if instrument_type == "STOCK":
        blockers.append("blocker_profile_conflict_unreviewed")
    if not overlay.get("source_hash_preview"):
        blockers.append("blocker_missing_source_hash")
    if overlay.get("raw_reference") == "":
        blockers.append("blocker_missing_raw_reference")
    return sorted(set(blockers))


def _metadata(
    *,
    run_id: str,
    signal_date: str,
    universe_name: str,
    status: str,
    health_status: str,
    rows: list[dict[str, Any]],
    source_families: list[str],
    safety: dict[str, bool],
) -> dict[str, Any]:
    counter = _closure_counts(rows)
    metadata: dict[str, Any] = {
        **safety,
        "worklist_run_id": run_id,
        "signal_date": signal_date,
        "universe_name": universe_name,
        "status": status,
        "health_status": health_status,
        "workflow_stage": WORKFLOW_STAGE,
        "report_only": True,
        "diagnostic_only": True,
        "local_only": True,
        "selected_sample_context_only": True,
        "row_count": len(rows),
        "blocked_count": counter.get("blocked", 0),
        "missing_evidence_count": sum("missing" in row["blocker_status"] for row in rows),
        "context_only_count": sum(row["context_only_flag"] == "true" for row in rows),
        "needs_manual_review_count": sum(row["quality_status"] == "needs_review" for row in rows),
        "no_hit_review_needed_count": sum(row["no_hit_acceptance_status"] == "no_hit_review_needed" for row in rows),
        "no_hit_accepted_context_count": sum(row["no_hit_acceptance_status"] == "no_hit_accepted_context" for row in rows),
        "closure_ready_not_pit_approved_count": counter.get("closure_ready_not_pit_approved", 0),
        "profile_conflict_count": sum(row["profile_conflict_flag"] == "true" for row in rows),
        "survivorship_warning_count": sum(row["survivorship_warning_flag"] == "true" for row in rows),
        "source_artifact_families_seen": source_families,
        "recommended_next_task": RECOMMENDED_NEXT_TASK,
    }
    return metadata


def _write_report(path: Path, metadata: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Historical Replay PIT Evidence Closure Worklist Report",
        "",
        "This report is report-only and diagnostic-only.",
        "",
        "A worklist row is not PIT approval.",
        "closure_ready_not_pit_approved is not PIT admissible.",
        "Reviewer no-hit acceptance is not source reliability scoring.",
        "Source hash preview is not source_hash validation.",
        "Local hash preview is not PIT evidence by itself.",
        "",
        f"Status: {metadata['status']}",
        f"Health: {metadata['health_status']}",
        f"Rows: {metadata['row_count']}",
        f"Blocked rows: {metadata['blocked_count']}",
        f"Recommended next task: {metadata['recommended_next_task']}",
    ]
    if not rows:
        lines.append("No local context was found for the selected sample; no readiness is implied.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_summary(path: Path, metadata: dict[str, Any]) -> None:
    fields = [
        "worklist_run_id",
        "signal_date",
        "universe_name",
        "status",
        "health_status",
        "row_count",
        "blocked_count",
        "missing_evidence_count",
        "context_only_count",
        "needs_manual_review_count",
        "profile_conflict_count",
        "survivorship_warning_count",
    ]
    _write_csv(path, [{field: metadata.get(field, "") for field in fields}], fields)


def _write_blocker_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    counts: dict[str, int] = {}
    for row in rows:
        for blocker in row.get("blocker_status", "").split(";"):
            if blocker:
                counts[blocker] = counts.get(blocker, 0) + 1
    output = [{"blocker_status": key, "row_count": value} for key, value in sorted(counts.items())]
    _write_csv(path, output, ["blocker_status", "row_count"])


def _paths(artifact_dir: Path) -> dict[str, Path]:
    return {key: artifact_dir / filename for key, filename in OUTPUT_FILES.items()}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [{key: value for key, value in row.items()} for row in csv.DictReader(handle)]


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field, "")) for field in fields})


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _generate_run_id(root: Path, signal_date: str, universe_name: str, rows: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        {"root": str(root), "signal_date": signal_date, "universe_name": universe_name, "symbols": [r.get("symbol") for r in rows]},
        sort_keys=True,
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def _with_run_id(row: dict[str, Any], run_id: str) -> dict[str, Any]:
    copy = dict(row)
    copy["worklist_run_id"] = run_id
    return copy


def _safety_flags() -> dict[str, bool]:
    return {field: False for field in SAFETY_FALSE_FIELDS}


def _closure_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("closure_status", ""))
        counts[status] = counts.get(status, 0) + 1
    return counts


def _recommended_profile(instrument_type: str) -> str:
    if instrument_type == "STOCK":
        return "stock_core"
    if instrument_type == "ETF":
        return "etf_core"
    return "needs_review"


def _guess_instrument_type(symbol: str) -> str:
    return "ETF" if symbol.startswith(("15", "51")) else "STOCK"


def _timing_relation(available_time: str, signal_date: str) -> str:
    if not available_time or available_time == "missing":
        return "unknown"
    try:
        available_day = datetime.fromisoformat(available_time.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            available_day = date.fromisoformat(available_time[:10])
        except ValueError:
            return "unknown"
    decision_day = date.fromisoformat(signal_date)
    if available_day > decision_day:
        return "after_decision"
    return "before_or_on_decision_date"


def _validate_output_root(path: Path) -> None:
    parts = [part.lower() for part in path.parts]
    if any(part == ".env" for part in parts) or any("secret" in part for part in parts):
        raise ValueError(f"{STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT}: protected output path")
    for first, second in PROTECTED_PATH_PARTS:
        for index in range(len(parts) - 1):
            if parts[index] == first and parts[index + 1] == second:
                raise ValueError(f"{STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT}: protected output path")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _join_reasons(*values: Any) -> str:
    reasons = [str(value) for value in values if value]
    return " ".join(reasons) if reasons else "Known evidence blockers remain."


def _is_true(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _csv_value(value: Any) -> Any:
    if isinstance(value, bool):
        return _bool_text(value)
    return value
