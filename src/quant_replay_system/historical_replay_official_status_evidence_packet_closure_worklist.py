"""Report-only official status evidence packet closure worklist scaffold.

This module creates a deterministic selected-sample worklist for
2024-04-02 / etf_core. It does not fetch official data, close evidence,
approve PIT admissibility, create replay input, or run downstream workflows.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STATUS_CREATED = "OFFICIAL_STATUS_EVIDENCE_PACKET_CLOSURE_WORKLIST_CREATED_REPORT_ONLY"
STATUS_WARN_NEEDS_REVIEW = "OFFICIAL_STATUS_EVIDENCE_PACKET_CLOSURE_WORKLIST_WARN_NEEDS_REVIEW"
STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT = (
    "OFFICIAL_STATUS_EVIDENCE_PACKET_CLOSURE_WORKLIST_BLOCKED_BY_UNSAFE_OUTPUT_ROOT"
)
STATUS_BLOCKED_BY_UNSAFE_INPUT = "OFFICIAL_STATUS_EVIDENCE_PACKET_CLOSURE_WORKLIST_BLOCKED_BY_UNSAFE_INPUT"
STATUS_HEALTH_FAILED = "OFFICIAL_STATUS_EVIDENCE_PACKET_CLOSURE_WORKLIST_HEALTH_FAILED"

WORKFLOW_STAGE = "HISTORICAL_REPLAY_OFFICIAL_STATUS_EVIDENCE_PACKET_CLOSURE_WORKLIST_CREATED_REPORT_ONLY"
DEFAULT_OUTPUT_ROOT = Path(
    "outputs/reports/manual_diagnostics/"
    "historical_replay_official_status_evidence_packet_closure_worklist_v0_1"
)
RECOMMENDED_NEXT_TASK = (
    "Historical Replay Official Status Evidence Packet Closure Worklist Artifact Views / "
    "Status Planning Report-Only v0.1"
)

OUTPUT_FILES = {
    "metadata": "metadata.json",
    "worklist": "official_status_evidence_packet_closure_worklist.csv",
    "evidence_family_matrix": "official_status_evidence_family_matrix.csv",
    "source_lineage_requirements": "official_status_source_lineage_requirements.csv",
    "blocker_matrix": "official_status_blocker_matrix.csv",
    "no_hit_handoff_matrix": "official_status_no_hit_handoff_matrix.csv",
    "safety_flags": "official_status_safety_flags.json",
    "report": "official_status_evidence_packet_closure_worklist_report.md",
}

SAFETY_FALSE_FIELDS = [
    "official_status_evidence_closed",
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
]

REQUIRED_ROW_FIELDS = [
    "packet_worklist_run_id",
    "signal_date",
    "universe_name",
    "symbol",
    "instrument_type",
    "exchange_or_market",
    "legacy_universe_label",
    "recommended_profile",
    "profile_conflict_flag",
    "profile_conflict_reason",
    "profile_policy_status",
    "listed_status_evidence",
    "listed_status_source_id",
    "listed_status_source_name",
    "listed_status_source_type",
    "listed_status_raw_reference",
    "listed_status_revision_id",
    "listed_status_available_time",
    "listed_status_review_status",
    "listed_status_limitation_note",
    "delisted_status_evidence",
    "delisted_status_source_id",
    "delisted_status_raw_reference",
    "delisted_status_revision_id",
    "delisted_status_available_time",
    "delisted_status_review_status",
    "delisted_no_hit_status",
    "delisted_no_hit_rationale",
    "st_status_evidence",
    "st_status_source_id",
    "st_status_raw_reference",
    "st_status_revision_id",
    "st_status_available_time",
    "st_status_review_status",
    "st_status_not_applicable_reason",
    "st_policy_status",
    "suspension_status_evidence",
    "suspension_status_source_id",
    "suspension_status_raw_reference",
    "suspension_status_revision_id",
    "suspension_status_available_time",
    "suspension_status_review_status",
    "trading_status_not_applicable_reason",
    "universe_membership_evidence",
    "universe_membership_source_id",
    "universe_membership_raw_reference",
    "universe_membership_revision_id",
    "universe_membership_available_time",
    "universe_membership_review_status",
    "universe_asof_after_signal_flag",
    "universe_membership_limitation_note",
    "survivorship_warning_flag",
    "survivorship_rationale",
    "survivorship_source_id",
    "survivorship_available_time",
    "survivorship_review_status",
    "survivorship_limitation_note",
    "permission_class",
    "source_hash_preview",
    "source_hash_disclosure_policy",
    "local_file_hash_preview",
    "revision_id_type",
    "available_time_timezone",
    "review_time",
    "reviewer_id",
    "reviewer_role",
    "reviewer_scope",
    "reviewer_attestation",
    "quality_status",
    "limitation_note",
    "blocker_reason",
    "closure_status",
    "closure_status_reason",
    "no_hit_review_needed",
    "no_hit_source_family",
    "no_hit_query_window",
    "no_hit_result",
    "no_hit_acceptance_status",
    "no_hit_acceptance_rationale",
    "no_hit_reviewer_required",
    *SAFETY_FALSE_FIELDS,
]

SELECTED_ROWS = [
    ("000001", "STOCK", "stock_core", True),
    ("000002", "STOCK", "stock_core", True),
    ("159915", "ETF", "etf_core", False),
    ("300750", "STOCK", "stock_core", True),
    ("510300", "ETF", "etf_core", False),
    ("600000", "STOCK", "stock_core", True),
    ("600519", "STOCK", "stock_core", True),
    ("601318", "STOCK", "stock_core", True),
    ("688981", "STOCK", "stock_core", True),
]

COMMON_BLOCKERS = [
    "blocker_missing_listed_status_evidence",
    "blocker_missing_delisted_status_evidence",
    "blocker_missing_suspension_or_trading_status",
    "blocker_missing_universe_membership_evidence",
    "blocker_universe_asof_after_signal",
    "blocker_missing_survivorship_rationale",
    "blocker_missing_source_id",
    "blocker_missing_raw_reference",
    "blocker_missing_permission_class",
    "blocker_missing_revision_id",
    "blocker_missing_available_time",
    "blocker_missing_reviewer_authority",
    "blocker_no_hit_unaccepted",
]

PROTECTED_PATH_PARTS = [
    ("data", "raw"),
    ("data", "processed"),
    ("data", "cache"),
    ("docs", "project_sources"),
]


@dataclass(frozen=True)
class HistoricalReplayOfficialStatusEvidencePacketClosureWorklistResult:
    packet_worklist_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    row_count: int
    artifact_paths: dict[str, Path]
    metadata: dict[str, Any]
    rows: list[dict[str, Any]]


def run_historical_replay_official_status_evidence_packet_closure_worklist(
    *,
    root: str | Path,
    output_dir: str | Path | None = None,
    run_id: str | None = None,
    signal_date: str = "2024-04-02",
    universe_name: str = "etf_core",
) -> HistoricalReplayOfficialStatusEvidencePacketClosureWorklistResult:
    """Create the selected-sample report-only official status worklist."""

    root_path = Path(root)
    output_root = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_ROOT
    _validate_output_root(output_root)

    if run_id is None:
        run_id = _generate_run_id(root_path, signal_date, universe_name)
    _validate_run_id(run_id)

    artifact_dir = (output_root / run_id).resolve()
    output_root_resolved = output_root.resolve()
    if not _is_relative_to(artifact_dir, output_root_resolved):
        raise ValueError(f"{STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT}: output path escapes requested root")

    rows = _build_rows(run_id, signal_date, universe_name)
    metadata = _metadata(run_id, signal_date, universe_name, rows)
    paths = _paths(artifact_dir)

    artifact_dir.mkdir(parents=True, exist_ok=True)
    _write_json(paths["metadata"], metadata)
    _write_csv(paths["worklist"], rows, REQUIRED_ROW_FIELDS)
    _write_csv(paths["evidence_family_matrix"], _evidence_family_matrix(run_id), _evidence_family_fields())
    _write_csv(paths["source_lineage_requirements"], _source_lineage_requirements(run_id), _source_lineage_fields())
    _write_csv(paths["blocker_matrix"], _blocker_matrix(rows), ["blocker_status", "row_count"])
    _write_csv(paths["no_hit_handoff_matrix"], _no_hit_handoff_matrix(rows), _no_hit_fields())
    _write_json(paths["safety_flags"], _safety_flags())
    _write_report(paths["report"], metadata)

    return HistoricalReplayOfficialStatusEvidencePacketClosureWorklistResult(
        packet_worklist_run_id=run_id,
        status=STATUS_CREATED,
        health_status="WARN",
        workflow_stage=WORKFLOW_STAGE,
        row_count=len(rows),
        artifact_paths=paths,
        metadata=metadata,
        rows=rows,
    )


def _build_rows(run_id: str, signal_date: str, universe_name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for symbol, instrument_type, recommended_profile, profile_conflict in SELECTED_ROWS:
        blockers = list(COMMON_BLOCKERS)
        if instrument_type == "STOCK":
            blockers.extend(["blocker_missing_st_status_evidence", "blocker_profile_conflict_unreviewed"])
            st_status_evidence = "missing"
            st_not_applicable_reason = ""
            st_policy_status = "missing_stock_st_status_evidence"
        else:
            blockers.append("blocker_missing_st_not_applicable_policy")
            st_status_evidence = "not_applicable_pending_policy"
            st_not_applicable_reason = "missing"
            st_policy_status = "missing_etf_not_applicable_policy"

        row: dict[str, Any] = {
            "packet_worklist_run_id": run_id,
            "signal_date": signal_date,
            "universe_name": universe_name,
            "symbol": symbol,
            "instrument_type": instrument_type,
            "exchange_or_market": "missing",
            "legacy_universe_label": universe_name,
            "recommended_profile": recommended_profile,
            "profile_conflict_flag": _bool_text(profile_conflict),
            "profile_conflict_reason": "STOCK row under legacy etf_core label" if profile_conflict else "",
            "profile_policy_status": "needs_manual_review" if profile_conflict else "context_only",
            "listed_status_evidence": "missing",
            "listed_status_source_id": "missing",
            "listed_status_source_name": "missing",
            "listed_status_source_type": "missing",
            "listed_status_raw_reference": "missing",
            "listed_status_revision_id": "missing",
            "listed_status_available_time": "missing",
            "listed_status_review_status": "missing",
            "listed_status_limitation_note": "missing",
            "delisted_status_evidence": "missing",
            "delisted_status_source_id": "missing",
            "delisted_status_raw_reference": "missing",
            "delisted_status_revision_id": "missing",
            "delisted_status_available_time": "missing",
            "delisted_status_review_status": "missing",
            "delisted_no_hit_status": "no_hit_review_needed",
            "delisted_no_hit_rationale": "missing",
            "st_status_evidence": st_status_evidence,
            "st_status_source_id": "missing",
            "st_status_raw_reference": "missing",
            "st_status_revision_id": "missing",
            "st_status_available_time": "missing",
            "st_status_review_status": "missing",
            "st_status_not_applicable_reason": st_not_applicable_reason,
            "st_policy_status": st_policy_status,
            "suspension_status_evidence": "missing",
            "suspension_status_source_id": "missing",
            "suspension_status_raw_reference": "missing",
            "suspension_status_revision_id": "missing",
            "suspension_status_available_time": "missing",
            "suspension_status_review_status": "missing",
            "trading_status_not_applicable_reason": "missing",
            "universe_membership_evidence": "missing",
            "universe_membership_source_id": "missing",
            "universe_membership_raw_reference": "missing",
            "universe_membership_revision_id": "missing",
            "universe_membership_available_time": "missing",
            "universe_membership_review_status": "missing",
            "universe_asof_after_signal_flag": "true",
            "universe_membership_limitation_note": "missing",
            "survivorship_warning_flag": "true",
            "survivorship_rationale": "missing",
            "survivorship_source_id": "missing",
            "survivorship_available_time": "missing",
            "survivorship_review_status": "missing",
            "survivorship_limitation_note": "missing",
            "permission_class": "missing",
            "source_hash_preview": "missing",
            "source_hash_disclosure_policy": "preview_only_or_hidden_full_hash",
            "local_file_hash_preview": "missing",
            "revision_id_type": "missing",
            "available_time_timezone": "missing",
            "review_time": "missing",
            "reviewer_id": "missing",
            "reviewer_role": "missing",
            "reviewer_scope": "missing",
            "reviewer_attestation": "missing",
            "quality_status": "needs_manual_review",
            "limitation_note": "Official status evidence is not closed; row remains blocked.",
            "blocker_reason": ";".join(blockers),
            "closure_status": "blocked",
            "closure_status_reason": "Official evidence packet worklist scaffold only; blockers remain.",
            "no_hit_review_needed": "true",
            "no_hit_source_family": "official_status_evidence",
            "no_hit_query_window": "missing",
            "no_hit_result": "missing",
            "no_hit_acceptance_status": "not_accepted",
            "no_hit_acceptance_rationale": "missing",
            "no_hit_reviewer_required": "true",
        }
        row.update({field: "false" for field in SAFETY_FALSE_FIELDS})
        rows.append(row)
    return rows


def _metadata(run_id: str, signal_date: str, universe_name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    safety = _safety_flags()
    return {
        **safety,
        "packet_worklist_run_id": run_id,
        "signal_date": signal_date,
        "universe_name": universe_name,
        "status": STATUS_CREATED,
        "health_status": "WARN",
        "workflow_stage": WORKFLOW_STAGE,
        "report_only": True,
        "diagnostic_only": True,
        "local_only": True,
        "selected_sample_context_only": True,
        "row_count": len(rows),
        "stock_row_count": sum(row["instrument_type"] == "STOCK" for row in rows),
        "etf_row_count": sum(row["instrument_type"] == "ETF" for row in rows),
        "blocked_count": sum(row["closure_status"] == "blocked" for row in rows),
        "missing_official_evidence_count": len(rows),
        "needs_manual_review_count": sum(row["quality_status"] == "needs_manual_review" for row in rows),
        "no_hit_review_needed_count": sum(row["no_hit_review_needed"] == "true" for row in rows),
        "no_hit_accepted_context_count": sum(row["no_hit_acceptance_status"] == "no_hit_accepted_context" for row in rows),
        "packet_row_ready_not_pit_approved_count": sum(
            row["closure_status"] == "packet_row_ready_not_pit_approved" for row in rows
        ),
        "profile_conflict_count": sum(row["profile_conflict_flag"] == "true" for row in rows),
        "survivorship_warning_count": sum(row["survivorship_warning_flag"] == "true" for row in rows),
        "listed_status_missing_count": sum(row["listed_status_evidence"] == "missing" for row in rows),
        "delisted_status_missing_count": sum(row["delisted_status_evidence"] == "missing" for row in rows),
        "st_status_missing_count": sum(
            row["instrument_type"] == "STOCK" and row["st_status_evidence"] == "missing" for row in rows
        ),
        "st_not_applicable_policy_missing_count": sum(
            row["instrument_type"] == "ETF" and row["st_status_not_applicable_reason"] == "missing" for row in rows
        ),
        "suspension_or_trading_status_missing_count": sum(
            row["suspension_status_evidence"] == "missing" for row in rows
        ),
        "universe_membership_missing_count": sum(row["universe_membership_evidence"] == "missing" for row in rows),
        "source_id_missing_count": sum(row["listed_status_source_id"] == "missing" for row in rows),
        "permission_class_missing_count": sum(row["permission_class"] == "missing" for row in rows),
        "revision_id_missing_count": sum(row["listed_status_revision_id"] == "missing" for row in rows),
        "available_time_missing_count": sum(row["listed_status_available_time"] == "missing" for row in rows),
        "recommended_next_task": RECOMMENDED_NEXT_TASK,
    }


def _evidence_family_matrix(run_id: str) -> list[dict[str, str]]:
    families = [
        ("listed_active_status", "listed_status_evidence", "blocker_missing_listed_status_evidence"),
        ("delisted_not_delisted_status", "delisted_status_evidence", "blocker_missing_delisted_status_evidence"),
        ("st_or_etf_not_applicable", "st_status_evidence", "blocker_missing_st_status_evidence"),
        ("suspension_or_trading_status", "suspension_status_evidence", "blocker_missing_suspension_or_trading_status"),
        ("universe_membership", "universe_membership_evidence", "blocker_missing_universe_membership_evidence"),
        ("survivorship_rationale", "survivorship_rationale", "blocker_missing_survivorship_rationale"),
    ]
    return [
        {
            "packet_worklist_run_id": run_id,
            "evidence_family": family,
            "required_field": field,
            "default_status": "missing",
            "blocker_status": blocker,
            "non_approval_note": "Required for review context only; not PIT approval.",
        }
        for family, field, blocker in families
    ]


def _source_lineage_requirements(run_id: str) -> list[dict[str, str]]:
    fields = [
        ("source_id", "blocker_missing_source_id"),
        ("raw_reference", "blocker_missing_raw_reference"),
        ("permission_class", "blocker_missing_permission_class"),
        ("revision_id", "blocker_missing_revision_id"),
        ("available_time", "blocker_missing_available_time"),
        ("source_hash_preview", "context_only_not_validation"),
        ("local_file_hash_preview", "context_only_not_pit_evidence"),
    ]
    return [
        {
            "packet_worklist_run_id": run_id,
            "source_field": field,
            "required_for_closure_review": "true",
            "default_status": "missing",
            "blocker_or_context": blocker,
        }
        for field, blocker in fields
    ]


def _blocker_matrix(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in rows:
        for blocker in row["blocker_reason"].split(";"):
            counts[blocker] = counts.get(blocker, 0) + 1
    return [{"blocker_status": key, "row_count": value} for key, value in sorted(counts.items())]


def _no_hit_handoff_matrix(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "packet_worklist_run_id": row["packet_worklist_run_id"],
            "symbol": row["symbol"],
            "no_hit_review_needed": row["no_hit_review_needed"],
            "no_hit_source_family": row["no_hit_source_family"],
            "no_hit_result": row["no_hit_result"],
            "no_hit_acceptance_status": row["no_hit_acceptance_status"],
            "no_hit_reviewer_required": row["no_hit_reviewer_required"],
            "non_approval_note": "No-hit handoff is not source reliability scoring.",
        }
        for row in rows
    ]


def _write_report(path: Path, metadata: dict[str, Any]) -> None:
    lines = [
        "# Historical Replay Official Status Evidence Packet Closure Worklist Report",
        "",
        "This artifact is report-only, diagnostic-only, local-only selected-sample context.",
        "A packet row is not PIT approval, not replay readiness, and not trading permission.",
        "packet_row_ready_not_pit_approved remains a non-approval status.",
        "no_hit_accepted_context is not source reliability scoring.",
        "source_hash_preview is not source hash validation.",
        "local_file_hash_preview is not PIT evidence by itself.",
        "Forward returns remain future information.",
        "",
        f"Status: {metadata['status']}",
        f"Health: {metadata['health_status']}",
        f"Rows: {metadata['row_count']}",
        f"Blocked rows: {metadata['blocked_count']}",
        f"Profile conflicts: {metadata['profile_conflict_count']}",
        f"Recommended next task: {metadata['recommended_next_task']}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _paths(artifact_dir: Path) -> dict[str, Path]:
    return {key: artifact_dir / filename for key, filename in OUTPUT_FILES.items()}


def _evidence_family_fields() -> list[str]:
    return [
        "packet_worklist_run_id",
        "evidence_family",
        "required_field",
        "default_status",
        "blocker_status",
        "non_approval_note",
    ]


def _source_lineage_fields() -> list[str]:
    return [
        "packet_worklist_run_id",
        "source_field",
        "required_for_closure_review",
        "default_status",
        "blocker_or_context",
    ]


def _no_hit_fields() -> list[str]:
    return [
        "packet_worklist_run_id",
        "symbol",
        "no_hit_review_needed",
        "no_hit_source_family",
        "no_hit_result",
        "no_hit_acceptance_status",
        "no_hit_reviewer_required",
        "non_approval_note",
    ]


def _safety_flags() -> dict[str, bool]:
    return {field: False for field in SAFETY_FALSE_FIELDS}


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


def _generate_run_id(root: Path, signal_date: str, universe_name: str) -> str:
    payload = json.dumps(
        {
            "root": str(root),
            "signal_date": signal_date,
            "universe_name": universe_name,
            "symbols": [row[0] for row in SELECTED_ROWS],
        },
        sort_keys=True,
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def _validate_run_id(run_id: str) -> None:
    if not run_id or "/" in run_id or "\\" in run_id or ".." in run_id:
        raise ValueError(f"{STATUS_BLOCKED_BY_UNSAFE_INPUT}: unsafe run_id")


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


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _csv_value(value: Any) -> Any:
    if isinstance(value, bool):
        return _bool_text(value)
    return value
