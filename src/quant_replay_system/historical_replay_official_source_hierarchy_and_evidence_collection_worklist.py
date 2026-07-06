"""Report-only official source hierarchy and evidence collection worklist.

This module creates a deterministic scaffold for the selected
2024-04-02 / etf_core historical replay sample. It does not fetch, read,
collect, accept, or close official evidence and it does not authorize
downstream replay, labels, models, buy-review, or trading.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STATUS_CREATED = "source_hierarchy_worklist_created_report_only"
STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT = (
    "historical_replay_official_source_hierarchy_worklist_blocked_by_unsafe_output_root"
)
STATUS_BLOCKED_BY_UNSAFE_INPUT = (
    "historical_replay_official_source_hierarchy_worklist_blocked_by_unsafe_input"
)
WORKFLOW_STAGE = (
    "HISTORICAL_REPLAY_OFFICIAL_SOURCE_HIERARCHY_AND_EVIDENCE_COLLECTION_WORKLIST_CREATED_REPORT_ONLY"
)
WORKFLOW_NAME = "historical_replay_official_source_hierarchy_and_evidence_collection_worklist"
DEFAULT_OUTPUT_ROOT = Path(
    "outputs/reports/manual_diagnostics/"
    "historical_replay_official_source_hierarchy_and_evidence_collection_worklist_v0_1"
)
RECOMMENDED_NEXT_TASK = (
    "Historical Replay Official Source Hierarchy and Evidence Collection Worklist "
    "Artifact Views / Status Report-Only v0.1"
)

OUTPUT_FILES = {
    "metadata": "metadata.json",
    "source_hierarchy_matrix": "official_source_hierarchy_matrix.csv",
    "worklist": "official_evidence_collection_worklist.csv",
    "evidence_family_requirement_matrix": "official_evidence_family_requirement_matrix.csv",
    "source_lineage_requirement_matrix": "official_source_lineage_requirement_matrix.csv",
    "no_hit_handoff_matrix": "official_no_hit_query_handoff_matrix.csv",
    "blocker_matrix": "official_collection_blocker_matrix.csv",
    "safety_flags": "official_collection_safety_flags.json",
    "report": "official_source_hierarchy_and_evidence_collection_worklist_report.md",
}

SAFETY_FALSE_FIELDS = [
    "official_source_hierarchy_approved",
    "official_evidence_collection_approved",
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

REQUIRED_COLLECTION_FIELDS = [
    "run_id",
    "source_family_row_id",
    "historical_decision_date",
    "universe_name",
    "symbol",
    "instrument_type",
    "legacy_universe_label",
    "recommended_profile",
    "profile_conflict",
    "profile_conflict_reason",
    "evidence_family",
    "source_class_rank",
    "source_class",
    "source_id",
    "source_name",
    "source_type",
    "permission_class",
    "raw_reference_type",
    "raw_reference",
    "source_hash_preview",
    "source_hash_disclosure_policy",
    "local_file_hash_preview",
    "revision_id",
    "revision_id_type",
    "available_time",
    "available_time_timezone",
    "available_time_policy",
    "quality_status",
    "limitation_note",
    "manual_review_required",
    "collection_required",
    "blocked",
    "status",
    "closure_status",
    "blocker_reason",
    "survivorship_warning_flag",
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

COMMON_EVIDENCE_FAMILIES = [
    "listed_active_status",
    "delisted_not_delisted_status",
    "suspension_trading_status",
    "universe_membership",
    "source_lineage",
    "reviewer_no_hit_handoff",
    "survivorship_rationale",
]
EVIDENCE_FAMILIES = [
    "listed_active_status",
    "delisted_not_delisted_status",
    "st_no_st_status",
    "etf_st_not_applicable_policy",
    "suspension_trading_status",
    "universe_membership",
    "source_lineage",
    "reviewer_no_hit_handoff",
    "survivorship_rationale",
]

SOURCE_CLASSES = [
    {
        "source_class_rank": "1",
        "source_class": "exchange official listing and trading-status source",
        "source_id_pattern": "exchange_official_listing_status_{market}",
        "source_name_pattern": "Exchange official listing and trading-status source",
        "source_type": "official_exchange",
        "evidence_families": "listed_active_status;delisted_not_delisted_status;suspension_trading_status",
        "permission_class": "public_review_allowed",
        "raw_reference_type": "official page, file, bulletin, or notice reference",
        "revision_id_type": "file date, notice id, publication id, or archived source revision",
        "available_time_requirement": "publication or file availability not after decision time",
        "timezone_policy": "explicit source timezone or reviewed market default required",
        "hash_disclosure_policy": "preview_only_or_hidden_full_hash",
        "manual_review_required": "true",
        "limitation_note_required": "true",
        "missing_blocker": "blocker_missing_source_class",
    },
    {
        "source_class_rank": "2",
        "source_class": "exchange disclosure or issuer announcement source",
        "source_id_pattern": "exchange_disclosure_{market}_{symbol}",
        "source_name_pattern": "Exchange disclosure or issuer announcement source",
        "source_type": "official_disclosure",
        "evidence_families": "st_no_st_status;delisted_not_delisted_status;suspension_trading_status",
        "permission_class": "public_review_allowed",
        "raw_reference_type": "announcement id or disclosure record",
        "revision_id_type": "announcement id plus publish timestamp",
        "available_time_requirement": "publish and availability time not after decision time",
        "timezone_policy": "explicit source timezone required",
        "hash_disclosure_policy": "preview_only_or_hidden_full_hash",
        "manual_review_required": "true",
        "limitation_note_required": "true",
        "missing_blocker": "blocker_missing_raw_reference",
    },
    {
        "source_class_rank": "3",
        "source_class": "official quotation or trading-status publication source",
        "source_id_pattern": "official_market_quote_{market}",
        "source_name_pattern": "Official quotation or trading-status publication source",
        "source_type": "official_market_data",
        "evidence_families": "suspension_trading_status",
        "permission_class": "public_review_allowed",
        "raw_reference_type": "official daily file or quote page",
        "revision_id_type": "file date, data batch id, or publication timestamp",
        "available_time_requirement": "publication availability not after decision time",
        "timezone_policy": "explicit source timezone required",
        "hash_disclosure_policy": "preview_only_or_hidden_full_hash",
        "manual_review_required": "true",
        "limitation_note_required": "true",
        "missing_blocker": "blocker_missing_available_time",
    },
    {
        "source_class_rank": "4",
        "source_class": "ETF issuer or fund company disclosure source",
        "source_id_pattern": "etf_issuer_disclosure_{fund_code}",
        "source_name_pattern": "ETF issuer or fund company disclosure source",
        "source_type": "official_fund_issuer",
        "evidence_families": (
            "listed_active_status;delisted_not_delisted_status;"
            "etf_st_not_applicable_policy;suspension_trading_status"
        ),
        "permission_class": "public_review_allowed",
        "raw_reference_type": "fund announcement, product page, or filing",
        "revision_id_type": "announcement id, filing id, or page revision",
        "available_time_requirement": "publish and availability time not after decision time",
        "timezone_policy": "explicit source timezone required",
        "hash_disclosure_policy": "preview_only_or_hidden_full_hash",
        "manual_review_required": "true",
        "limitation_note_required": "true",
        "missing_blocker": "blocker_missing_etf_st_not_applicable_policy",
    },
    {
        "source_class_rank": "5",
        "source_class": "index or provider membership source",
        "source_id_pattern": "index_or_universe_membership_{provider}_{universe}",
        "source_name_pattern": "Index or provider membership source",
        "source_type": "official_or_reviewed_provider",
        "evidence_families": "universe_membership",
        "permission_class": "public_or_reviewed_context",
        "raw_reference_type": "constituent page, membership file, or reviewed export",
        "revision_id_type": "effective date, publication id, file revision, or provider snapshot",
        "available_time_requirement": "effective and publication availability not after decision time",
        "timezone_policy": "explicit source timezone or reviewed provider default required",
        "hash_disclosure_policy": "preview_only_or_hidden_full_hash",
        "manual_review_required": "true",
        "limitation_note_required": "true",
        "missing_blocker": "blocker_missing_universe_membership_source",
    },
    {
        "source_class_rank": "6",
        "source_class": "reviewed local manual evidence metadata source",
        "source_id_pattern": "reviewed_local_csv_official_status_{review_id}",
        "source_name_pattern": "Reviewed local manual evidence metadata source",
        "source_type": "reviewed_local_artifact",
        "evidence_families": "source_lineage",
        "permission_class": "local_review_only",
        "raw_reference_type": "reviewed metadata row",
        "revision_id_type": "package version and reviewer revision id",
        "available_time_requirement": "source available_time plus reviewed_at; reviewed_at alone is insufficient",
        "timezone_policy": "explicit reviewer timezone required",
        "hash_disclosure_policy": "preview_only_or_hidden_full_hash",
        "manual_review_required": "true",
        "limitation_note_required": "true",
        "missing_blocker": "blocker_missing_reviewer_handoff",
    },
    {
        "source_class_rank": "7",
        "source_class": "reviewer no-hit query log source",
        "source_id_pattern": "reviewer_no_hit_official_status_{review_id}",
        "source_name_pattern": "Reviewer no-hit query log source",
        "source_type": "reviewed_no_hit_log",
        "evidence_families": "reviewer_no_hit_handoff;survivorship_rationale",
        "permission_class": "local_review_only",
        "raw_reference_type": "query log or reviewer attestation",
        "revision_id_type": "review log id",
        "available_time_requirement": "reviewed_at plus query-window timing; cannot override source/timing gaps",
        "timezone_policy": "explicit reviewer timezone required",
        "hash_disclosure_policy": "preview_only_or_hidden_full_hash",
        "manual_review_required": "true",
        "limitation_note_required": "true",
        "missing_blocker": "blocker_missing_no_hit_query_window",
    },
]

PROTECTED_PATH_PARTS = [
    ("data", "raw"),
    ("data", "processed"),
    ("data", "cache"),
    ("docs", "project_sources"),
]


@dataclass(frozen=True)
class HistoricalReplayOfficialSourceHierarchyWorklistResult:
    run_id: str
    status: str
    health_status: str
    workflow_stage: str
    artifact_paths: dict[str, Path]
    metadata: dict[str, Any]
    collection_rows: list[dict[str, Any]]


def run_historical_replay_official_source_hierarchy_and_evidence_collection_worklist(
    *,
    root: str | Path,
    output_dir: str | Path | None = None,
    run_id: str | None = None,
    historical_decision_date: str = "2024-04-02",
    universe_name: str = "etf_core",
) -> HistoricalReplayOfficialSourceHierarchyWorklistResult:
    """Create deterministic report-only manual diagnostic worklist artifacts."""

    root_path = Path(root)
    output_root = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_ROOT
    _validate_output_root(output_root)

    if run_id is None:
        run_id = _generate_run_id(root_path, historical_decision_date, universe_name)
    _validate_run_id(run_id)

    output_root_resolved = output_root.resolve()
    artifact_dir = (output_root / run_id).resolve()
    if not _is_relative_to(artifact_dir, output_root_resolved):
        raise ValueError(f"{STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT}: output path escapes requested root")

    collection_rows = _build_collection_rows(run_id, historical_decision_date, universe_name)
    source_hierarchy_rows = [dict(row) for row in SOURCE_CLASSES]
    family_rows = _evidence_family_requirement_rows()
    lineage_rows = _source_lineage_rows(collection_rows)
    no_hit_rows = _no_hit_rows(run_id, historical_decision_date, universe_name)
    blocker_rows = _blocker_rows(collection_rows)
    metadata = _metadata(
        run_id=run_id,
        historical_decision_date=historical_decision_date,
        universe_name=universe_name,
        collection_rows=collection_rows,
        source_hierarchy_rows=source_hierarchy_rows,
        family_rows=family_rows,
        no_hit_rows=no_hit_rows,
    )
    paths = _paths(artifact_dir)
    metadata["artifact_paths"] = {key: str(path) for key, path in paths.items()}
    metadata["report_path"] = str(paths["report"])

    artifact_dir.mkdir(parents=True, exist_ok=True)
    _write_json(paths["metadata"], metadata)
    _write_csv(paths["source_hierarchy_matrix"], source_hierarchy_rows, _source_hierarchy_fields())
    _write_csv(paths["worklist"], collection_rows, REQUIRED_COLLECTION_FIELDS)
    _write_csv(paths["evidence_family_requirement_matrix"], family_rows, _family_fields())
    _write_csv(paths["source_lineage_requirement_matrix"], lineage_rows, _lineage_fields())
    _write_csv(paths["no_hit_handoff_matrix"], no_hit_rows, _no_hit_fields())
    _write_csv(paths["blocker_matrix"], blocker_rows, ["blocker", "row_count", "report_only_note"])
    _write_json(paths["safety_flags"], _safety_flags())
    _write_report(paths["report"], metadata)

    return HistoricalReplayOfficialSourceHierarchyWorklistResult(
        run_id=run_id,
        status=STATUS_CREATED,
        health_status="WARN",
        workflow_stage=WORKFLOW_STAGE,
        artifact_paths=paths,
        metadata=metadata,
        collection_rows=collection_rows,
    )


def _build_collection_rows(run_id: str, decision_date: str, universe_name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for symbol, instrument_type, recommended_profile, profile_conflict in SELECTED_ROWS:
        families = list(COMMON_EVIDENCE_FAMILIES)
        if instrument_type == "STOCK":
            families.insert(2, "st_no_st_status")
        else:
            families.insert(2, "etf_st_not_applicable_policy")

        for family in families:
            source_class = _source_class_for_family(family, instrument_type)
            blockers = _blockers_for_family(family, profile_conflict)
            row: dict[str, Any] = {
                "run_id": run_id,
                "source_family_row_id": f"{symbol}_{family}_{source_class['source_class_rank']}",
                "historical_decision_date": decision_date,
                "universe_name": universe_name,
                "symbol": symbol,
                "instrument_type": instrument_type,
                "legacy_universe_label": universe_name,
                "recommended_profile": recommended_profile,
                "profile_conflict": _bool_text(profile_conflict),
                "profile_conflict_reason": "STOCK row under legacy etf_core label" if profile_conflict else "",
                "evidence_family": family,
                "source_class_rank": source_class["source_class_rank"],
                "source_class": source_class["source_class"],
                "source_id": "missing",
                "source_name": "missing",
                "source_type": source_class["source_type"],
                "permission_class": "missing",
                "raw_reference_type": source_class["raw_reference_type"],
                "raw_reference": "missing",
                "source_hash_preview": "missing",
                "source_hash_disclosure_policy": "preview_only_or_hidden_full_hash",
                "local_file_hash_preview": "missing",
                "revision_id": "missing",
                "revision_id_type": source_class["revision_id_type"],
                "available_time": "missing",
                "available_time_timezone": "missing",
                "available_time_policy": source_class["available_time_requirement"],
                "quality_status": "missing",
                "limitation_note": "missing",
                "manual_review_required": "true",
                "collection_required": "true",
                "blocked": "true",
                "status": _status_for_family(family),
                "closure_status": "blocked",
                "blocker_reason": ";".join(blockers),
                "survivorship_warning_flag": "true",
            }
            row.update({field: "false" for field in SAFETY_FALSE_FIELDS})
            rows.append(row)
    return rows


def _source_class_for_family(family: str, instrument_type: str) -> dict[str, str]:
    if family == "st_no_st_status":
        return SOURCE_CLASSES[1]
    if family == "etf_st_not_applicable_policy":
        return SOURCE_CLASSES[3]
    if family == "suspension_trading_status":
        return SOURCE_CLASSES[2]
    if family == "universe_membership":
        return SOURCE_CLASSES[4]
    if family == "source_lineage":
        return SOURCE_CLASSES[5]
    if family in {"reviewer_no_hit_handoff", "survivorship_rationale"}:
        return SOURCE_CLASSES[6]
    if instrument_type == "ETF":
        return SOURCE_CLASSES[3]
    return SOURCE_CLASSES[0]


def _blockers_for_family(family: str, profile_conflict: bool) -> list[str]:
    blockers = [
        "blocker_missing_source_class",
        "blocker_missing_source_id",
        "blocker_missing_raw_reference",
        "blocker_missing_permission_class",
        "blocker_missing_revision_id",
        "blocker_missing_available_time",
        "blocker_missing_timezone_policy",
        "blocker_missing_quality_status",
        "blocker_missing_limitation_note",
        "blocker_missing_survivorship_rationale",
    ]
    if family == "st_no_st_status":
        blockers.append("blocker_missing_stock_st_source")
    if family == "etf_st_not_applicable_policy":
        blockers.append("blocker_missing_etf_st_not_applicable_policy")
    if family == "universe_membership":
        blockers.append("blocker_missing_universe_membership_source")
    if family == "reviewer_no_hit_handoff":
        blockers.extend(["blocker_missing_reviewer_handoff", "blocker_missing_no_hit_query_window"])
    if profile_conflict:
        blockers.append("blocker_profile_conflict_unreviewed")
    return blockers


def _status_for_family(family: str) -> str:
    if family == "source_lineage":
        return "lineage_fields_missing"
    if family == "reviewer_no_hit_handoff":
        return "no_hit_query_required"
    if family in {"etf_st_not_applicable_policy", "survivorship_rationale"}:
        return "manual_review_required"
    return "collection_required"


def _evidence_family_requirement_rows() -> list[dict[str, str]]:
    rows = []
    for family in EVIDENCE_FAMILIES:
        rows.append(
            {
                "evidence_family": family,
                "required_for": _family_required_for(family),
                "purpose": _family_purpose(family),
                "default_status": _status_for_family(family),
                "default_blocker": _family_blocker(family),
                "non_approval_note": "Requirement row only; not evidence closure or PIT approval.",
            }
        )
    return rows


def _source_lineage_rows(collection_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "source_family_row_id": row["source_family_row_id"],
            "source_class_rank": row["source_class_rank"],
            "source_id_required": "true",
            "source_name_required": "true",
            "source_type_required": "true",
            "permission_class_required": "true",
            "raw_reference_type_required": "true",
            "raw_reference_required": "true",
            "source_hash_preview_policy": "preview_only_or_hidden_full_hash",
            "source_hash_disclosure_policy_required": "true",
            "local_file_hash_preview_policy": "preview_only_not_pit_evidence",
            "revision_id_required": "true",
            "revision_id_type_required": "true",
            "available_time_required": "true",
            "available_time_timezone_required": "true",
            "available_time_policy_required": "true",
            "quality_status_required": "true",
            "limitation_note_required": "true",
            "default_status": "lineage_fields_missing",
            "default_blocker_reason": (
                "blocker_missing_source_id;blocker_missing_raw_reference;"
                "blocker_missing_permission_class;blocker_missing_revision_id;"
                "blocker_missing_available_time;blocker_missing_timezone_policy;"
                "blocker_missing_quality_status;blocker_missing_limitation_note"
            ),
        }
        for row in collection_rows
    ]


def _no_hit_rows(run_id: str, decision_date: str, universe_name: str) -> list[dict[str, str]]:
    return [
        {
            "run_id": run_id,
            "historical_decision_date": decision_date,
            "universe_name": universe_name,
            "symbol": symbol,
            "instrument_type": instrument_type,
            "no_hit_review_needed": "true",
            "no_hit_source_family": "official_source_hierarchy_and_evidence_collection",
            "no_hit_query_window_start": "missing",
            "no_hit_query_window_end": "missing",
            "no_hit_query_terms": "missing",
            "no_hit_result": "missing",
            "no_hit_acceptance_status": "not_accepted",
            "no_hit_reviewer_required": "true",
            "reviewer_id": "missing",
            "reviewer_role": "missing",
            "reviewer_scope": "missing",
            "no_hit_acceptance_rationale": "missing",
            "limitation_note": "missing",
            "blocker_reason": "blocker_missing_reviewer_handoff;blocker_missing_no_hit_query_window",
            "non_approval_note": "No-hit query handoff is not source reliability scoring.",
        }
        for symbol, instrument_type, _, _ in SELECTED_ROWS
    ]


def _blocker_rows(collection_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in collection_rows:
        for blocker in row["blocker_reason"].split(";"):
            counts[blocker] = counts.get(blocker, 0) + 1
    return [
        {
            "blocker": blocker,
            "row_count": count,
            "report_only_note": "Blocker preserves manual review boundary and does not close evidence.",
        }
        for blocker, count in sorted(counts.items())
    ]


def _metadata(
    *,
    run_id: str,
    historical_decision_date: str,
    universe_name: str,
    collection_rows: list[dict[str, Any]],
    source_hierarchy_rows: list[dict[str, str]],
    family_rows: list[dict[str, str]],
    no_hit_rows: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        **_safety_flags(),
        "run_id": run_id,
        "workflow_name": WORKFLOW_NAME,
        "workflow_stage": WORKFLOW_STAGE,
        "runtime_status": STATUS_CREATED,
        "health_status": "WARN",
        "historical_decision_date": historical_decision_date,
        "universe_name": universe_name,
        "report_only": True,
        "diagnostic_only": True,
        "local_only": True,
        "selected_sample_context_only": True,
        "source_hierarchy_worklist_design_reference": True,
        "row_count": len(SELECTED_ROWS),
        "stock_row_count": sum(row[1] == "STOCK" for row in SELECTED_ROWS),
        "etf_row_count": sum(row[1] == "ETF" for row in SELECTED_ROWS),
        "source_class_count": len(source_hierarchy_rows),
        "evidence_family_count": len(family_rows),
        "evidence_collection_worklist_row_count": len(collection_rows),
        "no_hit_handoff_row_count": len(no_hit_rows),
        "profile_conflict_count": sum(row[3] for row in SELECTED_ROWS),
        "survivorship_warning_count": len(SELECTED_ROWS),
        "blocked_count": sum(row["blocked"] == "true" for row in collection_rows),
        "manual_review_required_count": sum(row["manual_review_required"] == "true" for row in collection_rows),
        "collection_required_count": sum(row["collection_required"] == "true" for row in collection_rows),
        "missing_source_id_count": sum(row["source_id"] == "missing" for row in collection_rows),
        "missing_raw_reference_count": sum(row["raw_reference"] == "missing" for row in collection_rows),
        "missing_permission_class_count": sum(row["permission_class"] == "missing" for row in collection_rows),
        "missing_revision_id_count": sum(row["revision_id"] == "missing" for row in collection_rows),
        "missing_available_time_count": sum(row["available_time"] == "missing" for row in collection_rows),
        "missing_timezone_policy_count": sum(
            row["available_time_timezone"] == "missing" for row in collection_rows
        ),
        "missing_quality_status_count": sum(row["quality_status"] == "missing" for row in collection_rows),
        "missing_limitation_note_count": sum(row["limitation_note"] == "missing" for row in collection_rows),
        "missing_no_hit_query_window_count": len(no_hit_rows),
        "missing_survivorship_rationale_count": len(SELECTED_ROWS),
        "recommended_next_task": RECOMMENDED_NEXT_TASK,
    }


def _write_report(path: Path, metadata: dict[str, Any]) -> None:
    lines = [
        "# Historical Replay Official Source Hierarchy and Evidence Collection Worklist Report",
        "",
        "This artifact is report-only, diagnostic-only, local-only selected-sample context.",
        "A worklist row is not PIT approval, not replay readiness, and not trading permission.",
        "row_ready_for_manual_collection_not_pit_approved is not PIT admissible.",
        "no_hit_query_required is not source reliability scoring.",
        "source_hash_preview is not source hash validation.",
        "local_file_hash_preview is not PIT evidence by itself.",
        "Same-day quotation presence is not automatically listed, not-delisted, no-ST, not-suspended,",
        "or universe-membership proof.",
        "ETF ST not-applicable policy is required for ETF rows if no ST evidence applies.",
        "STOCK rows under legacy etf_core remain profile-conflict review context until separately resolved.",
        "Universe membership cannot be inferred from legacy etf_core label alone.",
        "Forward returns remain future information.",
        "The 8-layer factor taxonomy remains the primary structure. Fixed 12 factors are not final.",
        "",
        f"Status: {metadata['runtime_status']}",
        f"Health: {metadata['health_status']}",
        f"Evidence collection worklist rows: {metadata['evidence_collection_worklist_row_count']}",
        f"Blocked rows: {metadata['blocked_count']}",
        f"Recommended next task: {metadata['recommended_next_task']}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _family_required_for(family: str) -> str:
    if family == "st_no_st_status":
        return "STOCK"
    if family == "etf_st_not_applicable_policy":
        return "ETF"
    return "STOCK;ETF"


def _family_purpose(family: str) -> str:
    purposes = {
        "listed_active_status": "show listed or active instrument context",
        "delisted_not_delisted_status": "reduce survivor-only inclusion risk",
        "st_no_st_status": "show STOCK special-treatment context",
        "etf_st_not_applicable_policy": "explain ETF not-applicable policy for stock ST status",
        "suspension_trading_status": "show suspension or trading-status context",
        "universe_membership": "show selected universe membership as of or before decision date",
        "source_lineage": "require source id, raw reference, permission, revision, timing, and quality fields",
        "reviewer_no_hit_handoff": "define reviewer no-hit query handoff",
        "survivorship_rationale": "explain why row is not survivor-only",
    }
    return purposes[family]


def _family_blocker(family: str) -> str:
    blockers = {
        "listed_active_status": "blocker_missing_source_id",
        "delisted_not_delisted_status": "blocker_missing_source_id",
        "st_no_st_status": "blocker_missing_stock_st_source",
        "etf_st_not_applicable_policy": "blocker_missing_etf_st_not_applicable_policy",
        "suspension_trading_status": "blocker_missing_source_id",
        "universe_membership": "blocker_missing_universe_membership_source",
        "source_lineage": "blocker_missing_source_id",
        "reviewer_no_hit_handoff": "blocker_missing_no_hit_query_window",
        "survivorship_rationale": "blocker_missing_survivorship_rationale",
    }
    return blockers[family]


def _source_hierarchy_fields() -> list[str]:
    return [
        "source_class_rank",
        "source_class",
        "source_id_pattern",
        "source_name_pattern",
        "source_type",
        "evidence_families",
        "permission_class",
        "raw_reference_type",
        "revision_id_type",
        "available_time_requirement",
        "timezone_policy",
        "hash_disclosure_policy",
        "manual_review_required",
        "limitation_note_required",
        "missing_blocker",
    ]


def _family_fields() -> list[str]:
    return [
        "evidence_family",
        "required_for",
        "purpose",
        "default_status",
        "default_blocker",
        "non_approval_note",
    ]


def _lineage_fields() -> list[str]:
    return [
        "source_family_row_id",
        "source_class_rank",
        "source_id_required",
        "source_name_required",
        "source_type_required",
        "permission_class_required",
        "raw_reference_type_required",
        "raw_reference_required",
        "source_hash_preview_policy",
        "source_hash_disclosure_policy_required",
        "local_file_hash_preview_policy",
        "revision_id_required",
        "revision_id_type_required",
        "available_time_required",
        "available_time_timezone_required",
        "available_time_policy_required",
        "quality_status_required",
        "limitation_note_required",
        "default_status",
        "default_blocker_reason",
    ]


def _no_hit_fields() -> list[str]:
    return [
        "run_id",
        "historical_decision_date",
        "universe_name",
        "symbol",
        "instrument_type",
        "no_hit_review_needed",
        "no_hit_source_family",
        "no_hit_query_window_start",
        "no_hit_query_window_end",
        "no_hit_query_terms",
        "no_hit_result",
        "no_hit_acceptance_status",
        "no_hit_reviewer_required",
        "reviewer_id",
        "reviewer_role",
        "reviewer_scope",
        "no_hit_acceptance_rationale",
        "limitation_note",
        "blocker_reason",
        "non_approval_note",
    ]


def _safety_flags() -> dict[str, bool]:
    return {field: False for field in SAFETY_FALSE_FIELDS}


def _paths(artifact_dir: Path) -> dict[str, Path]:
    return {key: artifact_dir / filename for key, filename in OUTPUT_FILES.items()}


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


def _generate_run_id(root: Path, decision_date: str, universe_name: str) -> str:
    payload = json.dumps(
        {
            "root": str(root),
            "historical_decision_date": decision_date,
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
