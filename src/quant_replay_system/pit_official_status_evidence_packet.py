"""Report-only PIT official status evidence packets.

This workflow consolidates official/public source-access diagnostics, local
EOD cache context, and prior non-relaxed PIT evidence drafts into evidence
packets. It writes reports only and never applies approvals or exports usable
universe inputs.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns
from quant_replay_system.pit_evidence_checklist_validator import build_pit_evidence_checklist_validator
from quant_replay_system.pit_evidence_policy_profile_comparison import (
    build_pit_evidence_policy_profile_comparison,
)
from quant_replay_system.point_in_time_universe_evidence_update_ingestion import (
    COMPLETED_UPDATE_COLUMNS,
    build_pit_universe_evidence_update_ingestion,
)


STRONG_OFFICIAL_DATE_SPECIFIC = "STRONG_OFFICIAL_DATE_SPECIFIC"
SUPPORTING_OFFICIAL_SYMBOL_LEVEL = "SUPPORTING_OFFICIAL_SYMBOL_LEVEL"
SUPPORTING_LOCAL_EOD_CACHE = "SUPPORTING_LOCAL_EOD_CACHE"
CONTEXT_ONLY = "CONTEXT_ONLY"
MISSING = "MISSING"

PACKET_COLUMNS = [
    "packet_id",
    "signal_date",
    "symbol",
    "universe_name",
    "evidence_field",
    "evidence_strength",
    "source_name",
    "source_url_or_path",
    "source_type",
    "accessed_at",
    "pit_suitability",
    "fields_supported",
    "field_status",
    "blocker_status",
    "evidence_reference",
    "context_only_or_approval_candidate",
    "approval_candidate_preview_only",
    "should_apply_approval",
    "no_approval_applied",
    "no_pit_review_run",
    "no_export_readiness_run",
    "no_staging_run",
    "no_universe_export",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "no_snapshot_built",
    "no_forward_labels",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "packet_only",
]

PER_SYMBOL_DATE_COLUMNS = [
    "packet_id",
    "signal_date",
    "symbol",
    "universe_name",
    "strong_official_date_specific_count",
    "supporting_official_symbol_level_count",
    "supporting_local_eod_cache_count",
    "context_only_count",
    "missing_count",
    "checklist_pass",
    "blocked",
    "blocker_reason",
    "review_status",
    "include_flag",
    "survivorship_bias_resolved",
]

SOURCE_COVERAGE_COLUMNS = [
    "packet_id",
    "source_name",
    "source_url_or_path",
    "source_type",
    "access_status",
    "parseable",
    "symbols_observed",
    "dates_observed",
    "pit_suitability",
    "strong_official_date_specific_count",
    "supporting_official_symbol_level_count",
    "supporting_local_eod_cache_count",
    "context_only_count",
    "missing_count",
]

STRENGTH_MATRIX_COLUMNS = [
    "packet_id",
    "symbol",
    "universe_name",
    "evidence_field",
    "evidence_strength",
    "row_count",
]

SAFETY_STATEMENT = (
    "No approval applied, PIT review, export-readiness, staging, universe export, active mutation, "
    "data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, "
    "live trading, broker API, order placement, message delivery, external API, LLM/API, or cache mutation was invoked."
)


@dataclass(frozen=True)
class PitOfficialStatusEvidencePacketResult:
    packet_id: str
    status: str
    row_count: int
    evidence_packet_row_count: int
    strong_official_date_specific_count: int
    supporting_official_symbol_level_count: int
    supporting_local_eod_cache_count: int
    context_only_count: int
    missing_count: int
    checklist_pass_count: int
    blocked_count: int
    eod_low_budget_checklist_pass_count: int
    source_rows: pd.DataFrame
    per_symbol_date_frame: pd.DataFrame
    evidence_strength_matrix: pd.DataFrame
    source_coverage_summary: pd.DataFrame
    updated_draft_completed_updates: pd.DataFrame
    artifact_paths: dict[str, Path]
    approval_applied: bool
    universe_exported: bool
    current_candidates_generated: bool
    audit_metadata: dict[str, Any]


def build_pit_official_status_evidence_packet(
    *,
    source_smoke_root: str | Path = "outputs/reports/manual_diagnostics/szse_status_source_access_smoke_v0_1",
    non_relaxed_root: str | Path = "outputs/reports/manual_diagnostics/codex_non_relaxed_pit_evidence_gap_acquisition_v0_1",
    policy_comparison: str | Path = "outputs/reports/pit_evidence_policy_profile_comparison/0ef6d2f3bae6",
    validator: str | Path = "outputs/reports/pit_evidence_checklist_validator/62e9eb747197",
    activated_plan: str | Path = "outputs/reports/activated_replacement_worklist_evidence_update_plan/4e268d67bd7d",
    stock_checklist: str | Path = "outputs/reports/manual_diagnostics/pit_strict_evidence_checklist_v0_3/stock_core_strict_evidence_checklist.csv",
    etf_checklist: str | Path = "outputs/reports/manual_diagnostics/pit_strict_evidence_checklist_v0_3/etf_core_strict_evidence_checklist.csv",
    source_acceptance: str | Path | None = "outputs/reports/manual_diagnostics/pit_strict_evidence_checklist_v0_3/source_acceptance_matrix.csv",
    output_dir: str | Path = "outputs/reports/pit_official_status_evidence_packet",
) -> PitOfficialStatusEvidencePacketResult:
    source_smoke_root = Path(source_smoke_root)
    non_relaxed_root = Path(non_relaxed_root)
    validator = Path(validator)
    activated_plan = Path(activated_plan)
    policy_comparison = Path(policy_comparison)
    draft = _read_draft_updates(non_relaxed_root, activated_plan)
    validator_frame = _read_validator_frame(validator)
    probe = _read_csv(source_smoke_root / "per_symbol_date_status_probe.csv")
    source_access = _read_csv(source_smoke_root / "source_access_results.csv")
    source_records = _read_csv(non_relaxed_root / "non_relaxed_source_records.csv")
    packet_id = _packet_id(
        {
            "source_smoke_root": source_smoke_root,
            "non_relaxed_root": non_relaxed_root,
            "validator": validator,
            "activated_plan": activated_plan,
            "row_count": len(draft),
        }
    )
    packet_frame = _build_packet_frame(packet_id, draft, validator_frame, probe, source_access, source_records)
    per_symbol = _per_symbol_date_frame(packet_id, draft, validator_frame, packet_frame)
    source_summary = _source_coverage_summary(packet_id, source_access, packet_frame)
    matrix = _strength_matrix(packet_frame)
    safe_draft = _safe_updated_draft(draft)
    paths = _paths(output_dir, packet_id)
    diagnostics = _run_diagnostics(
        packet_id=packet_id,
        safe_draft=safe_draft,
        paths=paths,
        activated_plan=activated_plan,
        stock_checklist=Path(stock_checklist),
        etf_checklist=Path(etf_checklist),
        source_acceptance=Path(source_acceptance) if source_acceptance else None,
        policy_audit=policy_comparison,
    )
    checklist_pass_count = int(diagnostics.get("checklist_pass_count", 0))
    blocked_count = int(diagnostics.get("blocked_count", len(draft)))
    eod_pass_count = int(diagnostics.get("eod_low_budget_checklist_pass_count", 0))
    status = "PASS" if checklist_pass_count > 0 and blocked_count == 0 else "WARN"
    result = PitOfficialStatusEvidencePacketResult(
        packet_id=packet_id,
        status=status,
        row_count=len(draft),
        evidence_packet_row_count=len(packet_frame),
        strong_official_date_specific_count=_strength_count(packet_frame, STRONG_OFFICIAL_DATE_SPECIFIC),
        supporting_official_symbol_level_count=_strength_count(packet_frame, SUPPORTING_OFFICIAL_SYMBOL_LEVEL),
        supporting_local_eod_cache_count=_strength_count(packet_frame, SUPPORTING_LOCAL_EOD_CACHE),
        context_only_count=_strength_count(packet_frame, CONTEXT_ONLY),
        missing_count=_strength_count(packet_frame, MISSING),
        checklist_pass_count=checklist_pass_count,
        blocked_count=blocked_count,
        eod_low_budget_checklist_pass_count=eod_pass_count,
        source_rows=packet_frame,
        per_symbol_date_frame=per_symbol,
        evidence_strength_matrix=matrix,
        source_coverage_summary=source_summary,
        updated_draft_completed_updates=safe_draft,
        artifact_paths=paths,
        approval_applied=False,
        universe_exported=False,
        current_candidates_generated=False,
        audit_metadata={
            "source_smoke_root": str(source_smoke_root),
            "non_relaxed_root": str(non_relaxed_root),
            "validator": str(validator),
            "activated_plan": str(activated_plan),
            "policy_comparison": str(policy_comparison),
            "stock_checklist": str(stock_checklist),
            "etf_checklist": str(etf_checklist),
            "source_acceptance": str(source_acceptance) if source_acceptance else "",
            **diagnostics,
            **_safety_metadata(),
        },
    )
    _write_artifacts(result)
    return result


def classify_official_status_evidence_strength(
    *,
    source_type: str,
    pit_suitability: str,
    date_specific: bool,
    local_cache: bool,
    context_only: bool,
) -> str:
    source = _string(source_type).lower()
    suitability = _string(pit_suitability).lower()
    if local_cache or "local_market_cache" in source:
        return SUPPORTING_LOCAL_EOD_CACHE
    if date_specific and "official" in source and "context" not in suitability:
        return STRONG_OFFICIAL_DATE_SPECIFIC
    if "official" in source and not context_only:
        return SUPPORTING_OFFICIAL_SYMBOL_LEVEL
    if source or suitability:
        return CONTEXT_ONLY
    return MISSING


def _build_packet_frame(
    packet_id: str,
    draft: pd.DataFrame,
    validator: pd.DataFrame,
    probe: pd.DataFrame,
    source_access: pd.DataFrame,
    source_records: pd.DataFrame,
) -> pd.DataFrame:
    validator_by_key = {_key(row): row for row in validator.to_dict("records")}
    probe_by_key = {_key(row): row for row in probe.to_dict("records")}
    rows: list[dict[str, Any]] = []
    for row in draft.to_dict("records"):
        key = _key(row)
        validation = validator_by_key.get(key, {})
        probe_row = probe_by_key.get(key, {})
        rows.extend(_packet_rows_for_update(packet_id, row, validation, probe_row, source_access, source_records))
    return _finalize(pd.DataFrame(rows), PACKET_COLUMNS)


def _packet_rows_for_update(
    packet_id: str,
    row: dict[str, Any],
    validation: dict[str, Any],
    probe: dict[str, Any],
    source_access: pd.DataFrame,
    source_records: pd.DataFrame,
) -> list[dict[str, Any]]:
    symbol = _string(row.get("symbol"))
    signal_date = _string(row.get("signal_date"))
    universe = _string(row.get("universe_name"))
    base = {
        "packet_id": packet_id,
        "signal_date": signal_date,
        "symbol": symbol,
        "universe_name": universe,
        "blocker_status": _string(validation.get("blocker_reason")),
        "approval_candidate_preview_only": False,
        "should_apply_approval": False,
        **_safety_row(),
    }
    evidence_rows: list[dict[str, Any]] = []
    local_status = _string(probe.get("local_cache_row_found")).lower() == "true"
    if local_status:
        evidence_rows.append(
            {
                **base,
                "evidence_field": "active_or_suspension_context",
                "evidence_strength": SUPPORTING_LOCAL_EOD_CACHE,
                "source_name": "local_market_cache",
                "source_url_or_path": _string(row.get("evidence_path")) or "data/cache/market/daily_bars.csv",
                "source_type": "local_market_cache",
                "accessed_at": _string(row.get("available_time")),
                "pit_suitability": "EOD_SUPPORT_ONLY",
                "fields_supported": "is_active_context,is_suspended_context",
                "field_status": _string(probe.get("local_cache_support")),
                "evidence_reference": _string(row.get("evidence_reference")),
                "context_only_or_approval_candidate": "supporting_eod_context_only",
            }
        )
    official_daily = _string(probe.get("official_date_specific_status_found")).lower() == "true"
    daily_source = _match_source(source_access, symbol, signal_date, prefer_date=True)
    if official_daily:
        evidence_rows.append(
            {
                **base,
                "evidence_field": "official_date_specific_status",
                "evidence_strength": STRONG_OFFICIAL_DATE_SPECIFIC,
                "source_name": _string(daily_source.get("source_name")) or "official date-specific status source",
                "source_url_or_path": _string(daily_source.get("source_url_or_path")),
                "source_type": _string(daily_source.get("source_type")) or "official_exchange_daily_status",
                "accessed_at": _string(daily_source.get("accessed_at")),
                "pit_suitability": _string(daily_source.get("PIT_suitability")) or "DATE_SPECIFIC_STATUS_CANDIDATE",
                "fields_supported": _string(daily_source.get("fields_observed")),
                "field_status": "official_date_specific_status_found",
                "evidence_reference": _string(daily_source.get("source_url_or_path")),
                "context_only_or_approval_candidate": _string(daily_source.get("context_only_or_approval_candidate")),
            }
        )
    context = _string(probe.get("monthly_or_disclosure_context_found"))
    symbol_source = _match_source(source_access, symbol, signal_date, prefer_date=False)
    record = _match_source_record(source_records, symbol)
    if context or record:
        evidence_rows.append(
            {
                **base,
                "evidence_field": "official_symbol_or_period_context",
                "evidence_strength": SUPPORTING_OFFICIAL_SYMBOL_LEVEL,
                "source_name": _string(record.get("source_name")) or _string(symbol_source.get("source_name")) or "official/public context source",
                "source_url_or_path": _string(record.get("url")) or _string(symbol_source.get("source_url_or_path")),
                "source_type": _string(record.get("source_type")) or _string(symbol_source.get("source_type")) or "official_public_context",
                "accessed_at": _string(record.get("accessed_at")),
                "pit_suitability": _string(record.get("pit_safe_for_signal_date")) or _string(symbol_source.get("PIT_suitability")),
                "fields_supported": _string(record.get("supports_fields")) or _string(symbol_source.get("fields_observed")),
                "field_status": context,
                "evidence_reference": _string(record.get("url")) or _string(symbol_source.get("source_url_or_path")),
                "context_only_or_approval_candidate": "context_only",
            }
        )
    for field, status_name in [
        ("not_delisted", "not_delisted_evidence_status"),
        ("stock_st_no_st", "st_no_st_evidence_status"),
        ("survivorship_bias_resolution", "survivorship_resolution_status"),
    ]:
        status = _string(probe.get(status_name))
        if not status or status == "not_applicable":
            continue
        if "missing" in status.lower():
            evidence_rows.append(
                {
                    **base,
                    "evidence_field": field,
                    "evidence_strength": MISSING,
                    "source_name": "",
                    "source_url_or_path": "",
                    "source_type": "",
                    "accessed_at": "",
                    "pit_suitability": "MISSING",
                    "fields_supported": "",
                    "field_status": status,
                    "evidence_reference": "",
                    "context_only_or_approval_candidate": "missing",
                }
            )
    return evidence_rows


def _per_symbol_date_frame(packet_id: str, draft: pd.DataFrame, validator: pd.DataFrame, packet: pd.DataFrame) -> pd.DataFrame:
    validation_by_key = {_key(row): row for row in validator.to_dict("records")}
    rows = []
    for row in draft.to_dict("records"):
        subset = packet.loc[(packet["symbol"] == _string(row.get("symbol"))) & (packet["signal_date"] == _string(row.get("signal_date")))]
        validation = validation_by_key.get(_key(row), {})
        rows.append(
            {
                "packet_id": packet_id,
                "signal_date": _string(row.get("signal_date")),
                "symbol": _string(row.get("symbol")),
                "universe_name": _string(row.get("universe_name")),
                "strong_official_date_specific_count": _strength_count(subset, STRONG_OFFICIAL_DATE_SPECIFIC),
                "supporting_official_symbol_level_count": _strength_count(subset, SUPPORTING_OFFICIAL_SYMBOL_LEVEL),
                "supporting_local_eod_cache_count": _strength_count(subset, SUPPORTING_LOCAL_EOD_CACHE),
                "context_only_count": _strength_count(subset, CONTEXT_ONLY),
                "missing_count": _strength_count(subset, MISSING),
                "checklist_pass": _bool(validation.get("checklist_pass")),
                "blocked": _bool(validation.get("blocked", True)),
                "blocker_reason": _string(validation.get("blocker_reason")),
                "review_status": _string(row.get("review_status")) or "NEEDS_MORE_EVIDENCE",
                "include_flag": False,
                "survivorship_bias_resolved": _bool(row.get("survivorship_bias_resolved")),
            }
        )
    return _finalize(pd.DataFrame(rows), PER_SYMBOL_DATE_COLUMNS)


def _source_coverage_summary(packet_id: str, source_access: pd.DataFrame, packet: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for source in source_access.to_dict("records"):
        source_name = _string(source.get("source_name"))
        subset = packet.loc[packet["source_name"] == source_name] if "source_name" in packet.columns else pd.DataFrame()
        rows.append(
            {
                "packet_id": packet_id,
                "source_name": source_name,
                "source_url_or_path": _string(source.get("source_url_or_path")),
                "source_type": _string(source.get("source_type")),
                "access_status": _string(source.get("access_status")),
                "parseable": _string(source.get("parseable")),
                "symbols_observed": _string(source.get("symbols_observed")),
                "dates_observed": _string(source.get("dates_observed")),
                "pit_suitability": _string(source.get("PIT_suitability")),
                "strong_official_date_specific_count": _strength_count(subset, STRONG_OFFICIAL_DATE_SPECIFIC),
                "supporting_official_symbol_level_count": _strength_count(subset, SUPPORTING_OFFICIAL_SYMBOL_LEVEL),
                "supporting_local_eod_cache_count": _strength_count(subset, SUPPORTING_LOCAL_EOD_CACHE),
                "context_only_count": _strength_count(subset, CONTEXT_ONLY),
                "missing_count": _strength_count(subset, MISSING),
            }
        )
    if not rows and not packet.empty:
        rows.append({"packet_id": packet_id, "source_name": "local_packet_sources"})
    return _finalize(pd.DataFrame(rows), SOURCE_COVERAGE_COLUMNS)


def _strength_matrix(packet: pd.DataFrame) -> pd.DataFrame:
    if packet.empty:
        return pd.DataFrame(columns=STRENGTH_MATRIX_COLUMNS)
    grouped = (
        packet.groupby(["packet_id", "symbol", "universe_name", "evidence_field", "evidence_strength"], dropna=False)
        .size()
        .reset_index(name="row_count")
    )
    return _finalize(grouped, STRENGTH_MATRIX_COLUMNS)


def _safe_updated_draft(draft: pd.DataFrame) -> pd.DataFrame:
    frame = draft.copy()
    for column in COMPLETED_UPDATE_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    frame = frame[COMPLETED_UPDATE_COLUMNS].copy()
    frame["review_status"] = "NEEDS_MORE_EVIDENCE"
    frame["include_flag"] = "False"
    frame["survivorship_bias_resolved"] = "False"
    return frame


def _run_diagnostics(
    *,
    packet_id: str,
    safe_draft: pd.DataFrame,
    paths: dict[str, Path],
    activated_plan: Path,
    stock_checklist: Path,
    etf_checklist: Path,
    source_acceptance: Path | None,
    policy_audit: Path,
) -> dict[str, Any]:
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    safe_draft.to_csv(paths["updated_draft_completed_updates"], index=False)
    worklist = _worklist_path(activated_plan)
    ingestion = build_pit_universe_evidence_update_ingestion(
        completed_updates=paths["updated_draft_completed_updates"],
        worklist=worklist if worklist.exists() else None,
        output_dir=paths["artifact_dir"] / "ingestion_validation",
    )
    validator = build_pit_evidence_checklist_validator(
        completed_updates=ingestion.artifact_paths["review_updates"],
        stock_checklist=stock_checklist,
        etf_checklist=etf_checklist,
        source_acceptance=source_acceptance,
        output_dir=paths["artifact_dir"] / "checklist_validator",
    )
    comparison = build_pit_evidence_policy_profile_comparison(
        validator=validator.artifact_paths["artifact_dir"],
        completed_updates=ingestion.artifact_paths["review_updates"],
        policy_audit=policy_audit,
        output_dir=paths["artifact_dir"] / "policy_comparison",
    )
    ingestion_summary = pd.DataFrame(
        [
            {
                "ingestion_id": ingestion.ingestion_id,
                "status": ingestion.status,
                "row_count": ingestion.row_count,
                "ready_for_review_update_count": ingestion.ready_for_review_update_count,
                "blocked_count": ingestion.blocked_count,
                "approval_requested_count": ingestion.approval_requested_count,
                "approved_ready_count": ingestion.approved_ready_count,
                "needs_more_evidence_ready_count": ingestion.needs_more_evidence_ready_count,
                "duplicate_identity_count": ingestion.duplicate_identity_count,
            }
        ]
    )
    paths["ingestion_validation_report"].write_text(_diag_report("Ingestion Validation", ingestion_summary), encoding="utf-8")
    paths["checklist_validator_rerun_report"].write_text(_diag_report("Checklist Validator Rerun", validator.summary_frame), encoding="utf-8")
    paths["policy_comparison_rerun_report"].write_text(_diag_report("Policy Comparison Rerun", comparison.summary_frame), encoding="utf-8")
    return {
        "ingestion_id": ingestion.ingestion_id,
        "ingestion_row_count": ingestion.row_count,
        "ready_for_review_update_count": ingestion.ready_for_review_update_count,
        "approval_requested_count": ingestion.approval_requested_count,
        "validator_id": validator.validator_id,
        "checklist_pass_count": validator.checklist_pass_count,
        "blocked_count": validator.blocked_count,
        "policy_comparison_id": comparison.comparison_id,
        "eod_low_budget_checklist_pass_count": comparison.eod_low_budget_checklist_pass_count,
        "remaining_blocked_count": comparison.remaining_blocked_count,
    }


def _write_artifacts(result: PitOfficialStatusEvidencePacketResult) -> None:
    for path in result.artifact_paths.values():
        if path.name != "metadata.json" and path.suffix == "":
            path.mkdir(parents=True, exist_ok=True)
    artifact_dir = result.artifact_paths["artifact_dir"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    result.source_rows.to_csv(result.artifact_paths["packet_csv"], index=False)
    result.source_coverage_summary.to_csv(result.artifact_paths["source_coverage_summary"], index=False)
    result.per_symbol_date_frame.to_csv(result.artifact_paths["per_symbol_date_status_evidence"], index=False)
    result.evidence_strength_matrix.to_csv(result.artifact_paths["evidence_strength_matrix"], index=False)
    result.updated_draft_completed_updates.to_csv(result.artifact_paths["updated_draft_completed_updates"], index=False)
    metadata = {
        "packet_id": result.packet_id,
        "created_at": _mtime_text(artifact_dir),
        "status": result.status,
        "row_count": result.row_count,
        "evidence_packet_row_count": result.evidence_packet_row_count,
        "strong_official_date_specific_count": result.strong_official_date_specific_count,
        "supporting_official_symbol_level_count": result.supporting_official_symbol_level_count,
        "supporting_local_eod_cache_count": result.supporting_local_eod_cache_count,
        "context_only_count": result.context_only_count,
        "missing_count": result.missing_count,
        "checklist_pass_count": result.checklist_pass_count,
        "blocked_count": result.blocked_count,
        "eod_low_budget_checklist_pass_count": result.eod_low_budget_checklist_pass_count,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
        "safety_statement": SAFETY_STATEMENT,
    }
    result.artifact_paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")


def _render_report(result: PitOfficialStatusEvidencePacketResult) -> str:
    summary = {
        "packet_id": result.packet_id,
        "status": result.status,
        "row_count": result.row_count,
        "strong_official_date_specific_count": result.strong_official_date_specific_count,
        "supporting_official_symbol_level_count": result.supporting_official_symbol_level_count,
        "supporting_local_eod_cache_count": result.supporting_local_eod_cache_count,
        "missing_count": result.missing_count,
        "checklist_pass_count": result.checklist_pass_count,
        "blocked_count": result.blocked_count,
    }
    return "\n".join(
        [
            "# PIT Official Status Evidence Packet",
            "",
            SAFETY_STATEMENT,
            "",
            "## Summary",
            "",
            _dict_table(summary),
            "",
            "## Interpretation",
            "",
            "Evidence packets are diagnostics-only. Official symbol-level and local EOD context do not apply approvals; incomplete rows remain NEEDS_MORE_EVIDENCE.",
            "",
        ]
    )


def _diag_report(title: str, frame: pd.DataFrame) -> str:
    body = frame.to_markdown(index=False) if not frame.empty else "_No rows._"
    return f"# {title}\n\n{body}\n\n{SAFETY_STATEMENT}\n"


def _paths(output_dir: str | Path, packet_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / packet_id
    return {
        "artifact_dir": artifact_dir,
        "packet_csv": artifact_dir / "pit_official_status_evidence_packet.csv",
        "source_coverage_summary": artifact_dir / "source_coverage_summary.csv",
        "per_symbol_date_status_evidence": artifact_dir / "per_symbol_date_status_evidence.csv",
        "evidence_strength_matrix": artifact_dir / "evidence_strength_matrix.csv",
        "updated_draft_completed_updates": artifact_dir / "updated_draft_completed_updates.csv",
        "ingestion_validation_report": artifact_dir / "ingestion_validation_report.md",
        "checklist_validator_rerun_report": artifact_dir / "checklist_validator_rerun_report.md",
        "policy_comparison_rerun_report": artifact_dir / "policy_comparison_rerun_report.md",
        "report": artifact_dir / "report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def _read_draft_updates(non_relaxed_root: Path, activated_plan: Path) -> pd.DataFrame:
    draft_path = non_relaxed_root / "updated_non_relaxed_draft_completed_updates.csv"
    if draft_path.exists():
        frame = read_csv_preserve_symbol_columns(draft_path, keep_default_na=False)
    else:
        frames = []
        for name in ["stock_core_first_batch_package.csv", "etf_core_first_batch_package.csv"]:
            path = activated_plan / name
            if path.exists():
                frames.append(read_csv_preserve_symbol_columns(path, keep_default_na=False))
        frame = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=COMPLETED_UPDATE_COLUMNS)
    for column in COMPLETED_UPDATE_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    frame = frame[COMPLETED_UPDATE_COLUMNS].copy()
    if "symbol" in frame.columns:
        frame["symbol"] = frame["symbol"].map(_string)
    return frame.reset_index(drop=True)


def _read_validator_frame(root: Path) -> pd.DataFrame:
    path = root / "pit_evidence_checklist_validation.csv"
    return _read_csv(path)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return read_csv_preserve_symbol_columns(path, keep_default_na=False)


def _match_source(source_access: pd.DataFrame, symbol: str, signal_date: str, *, prefer_date: bool) -> dict[str, Any]:
    if source_access.empty:
        return {}
    rows = source_access.copy()
    if "symbols_observed" in rows.columns:
        rows = rows.loc[rows["symbols_observed"].map(lambda value: symbol in _string(value))]
    if prefer_date and "dates_observed" in rows.columns:
        exact = rows.loc[rows["dates_observed"].map(lambda value: signal_date in _string(value))]
        if not exact.empty:
            return exact.iloc[0].to_dict()
    if not rows.empty:
        return rows.iloc[0].to_dict()
    return {}


def _match_source_record(source_records: pd.DataFrame, symbol: str) -> dict[str, Any]:
    if source_records.empty or "symbol" not in source_records.columns:
        return {}
    rows = source_records.loc[source_records["symbol"].map(_string) == symbol]
    return rows.iloc[0].to_dict() if not rows.empty else {}


def _worklist_path(activated_plan: Path) -> Path:
    combined = activated_plan / "activated_replacement_worklist_evidence_update_plan.csv"
    if combined.exists():
        return combined
    return activated_plan / "__missing_combined_worklist__.csv"


def _strength_count(frame: pd.DataFrame, strength: str) -> int:
    if frame.empty or "evidence_strength" not in frame.columns:
        return 0
    return int((frame["evidence_strength"] == strength).sum())


def _finalize(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=columns)
    for column in columns:
        if column not in frame.columns:
            frame[column] = ""
    if "symbol" in frame.columns:
        frame["symbol"] = frame["symbol"].map(_string)
    return frame[columns].reset_index(drop=True)


def _packet_id(payload: dict[str, Any]) -> str:
    normalized = json.dumps({key: str(value) for key, value in payload.items()}, sort_keys=True)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


def _key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        _string(row.get("signal_date")),
        _string(row.get("symbol")),
        _string(row.get("universe_name")) or _string(row.get("profile")),
    )


def _safety_row() -> dict[str, bool]:
    return {
        "no_approval_applied": True,
        "no_pit_review_run": True,
        "no_export_readiness_run": True,
        "no_staging_run": True,
        "no_universe_export": True,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "packet_only": True,
    }


def _safety_metadata() -> dict[str, bool]:
    return {
        "approval_applied": False,
        "pit_review_run": False,
        "export_readiness_run": False,
        "export_staging_run": False,
        "universe_exported": False,
        "active_worklist_mutated": False,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
        "cache_mutated": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "packet_only": True,
    }


def _dict_table(values: dict[str, Any]) -> str:
    return "\n".join(["| key | value |", "| --- | --- |", *[f"| {key} | {value} |" for key, value in values.items()]])


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _string(value).lower() in {"1", "true", "yes", "y"}


def _string(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _mtime_text(path: Path) -> str:
    try:
        return pd.Timestamp(path.stat().st_mtime, unit="s", tz="UTC").isoformat()
    except Exception:
        return pd.Timestamp.utcnow().isoformat()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    return value
