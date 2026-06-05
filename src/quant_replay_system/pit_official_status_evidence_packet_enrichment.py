"""Report-only PIT official status evidence packet enrichment."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns


SAFETY_FLAGS = {
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
    "enrichment_only": True,
}

ENRICHED_COLUMNS = [
    "enrichment_id",
    "source_packet_id",
    "policy_comparison_id",
    "signal_date",
    "symbol",
    "universe_name",
    "strong_official_date_specific_quotation",
    "quotation_source_url",
    "quotation_fields_observed",
    "reviewed_no_hit_context_supported",
    "reviewer_acceptance_required",
    "prior_official_symbol_level_context",
    "local_eod_cache_context",
    "missing_evidence_categories",
    "remaining_blocked",
    "checklist_pass",
    "no_approval_applied",
    "no_universe_export",
    "no_current_candidates_generated",
]

SUMMARY_COLUMNS = [
    "enrichment_id",
    "status",
    "source_packet_id",
    "policy_comparison_id",
    "row_count",
    "strong_official_date_specific_quotation_count",
    "reviewed_no_hit_context_supported_count",
    "reviewer_acceptance_required_count",
    "prior_official_symbol_level_context_count",
    "local_eod_cache_context_count",
    "checklist_pass_count",
    "remaining_blocked_count",
]


@dataclass(frozen=True)
class PitOfficialStatusEvidencePacketEnrichmentResult:
    enrichment_id: str
    status: str
    source_packet_id: str
    policy_comparison_id: str
    row_count: int
    strong_official_date_specific_quotation_count: int
    reviewed_no_hit_context_supported_count: int
    reviewer_acceptance_required_count: int
    prior_official_symbol_level_context_count: int
    local_eod_cache_context_count: int
    checklist_pass_count: int
    remaining_blocked_count: int
    enriched_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    blocker_frame: pd.DataFrame
    artifact_paths: dict[str, Path]


def build_pit_official_status_evidence_packet_enrichment(
    *,
    packet: str | Path = "outputs/reports/pit_official_status_evidence_packet/8efabe2ffe62",
    quotation_probe: str | Path = "outputs/reports/manual_diagnostics/szse_1815_same_date_quotation_probe_v0_1",
    policy_comparison: str | Path = "outputs/reports/pit_evidence_policy_profile_comparison/c1a75d1091c6",
    output_dir: str | Path = "outputs/reports/pit_official_status_evidence_packet_enrichment",
) -> PitOfficialStatusEvidencePacketEnrichmentResult:
    packet_dir = Path(packet)
    quotation_dir = Path(quotation_probe)
    comparison_dir = Path(policy_comparison)
    packet_meta = _load_json(packet_dir / "metadata.json")
    source_packet_id = _string(packet_meta.get("packet_id")) or packet_dir.name
    policy_comparison_id = _comparison_id_from_dir(comparison_dir)
    updates = read_csv_preserve_symbol_columns(packet_dir / "updated_draft_completed_updates.csv", keep_default_na=False)
    quotation = read_csv_preserve_symbol_columns(quotation_dir / "per_symbol_date_quotation_presence.csv", keep_default_na=False)
    comparison = read_csv_preserve_symbol_columns(comparison_dir / "pit_evidence_policy_profile_comparison.csv", keep_default_na=False)
    enrichment_id = _stable_id(
        {
            "packet": packet_dir,
            "quotation_probe": quotation_dir,
            "policy_comparison": comparison_dir,
            "source_packet_id": source_packet_id,
            "policy_comparison_id": policy_comparison_id,
        }
    )
    quote_by_key = {_key(row): row for row in quotation.to_dict("records")}
    comparison_by_key = {_key(row): row for row in comparison.to_dict("records")}
    rows = [
        _enrich_row(
            enrichment_id=enrichment_id,
            source_packet_id=source_packet_id,
            policy_comparison_id=policy_comparison_id,
            update=row,
            quote=quote_by_key.get(_key(row), {}),
            comparison=comparison_by_key.get(_key(row), {}),
        )
        for row in updates.to_dict("records")
    ]
    enriched = _finalize(pd.DataFrame(rows), ENRICHED_COLUMNS)
    blockers = _blocker_matrix(enriched)
    summary = _summary(enrichment_id, source_packet_id, policy_comparison_id, enriched)
    status = _string(summary.iloc[0].get("status")) if not summary.empty else "WARN"
    paths = _paths(output_dir, enrichment_id)
    result = PitOfficialStatusEvidencePacketEnrichmentResult(
        enrichment_id=enrichment_id,
        status=status,
        source_packet_id=source_packet_id,
        policy_comparison_id=policy_comparison_id,
        row_count=len(enriched),
        strong_official_date_specific_quotation_count=_true_count(enriched, "strong_official_date_specific_quotation"),
        reviewed_no_hit_context_supported_count=_true_count(enriched, "reviewed_no_hit_context_supported"),
        reviewer_acceptance_required_count=_true_count(enriched, "reviewer_acceptance_required"),
        prior_official_symbol_level_context_count=_true_count(enriched, "prior_official_symbol_level_context"),
        local_eod_cache_context_count=_true_count(enriched, "local_eod_cache_context"),
        checklist_pass_count=_true_count(enriched, "checklist_pass"),
        remaining_blocked_count=_true_count(enriched, "remaining_blocked"),
        enriched_frame=enriched,
        summary_frame=summary,
        blocker_frame=blockers,
        artifact_paths=paths,
    )
    _write_artifacts(result, packet_dir, quotation_dir, comparison_dir)
    return result


def _enrich_row(
    *,
    enrichment_id: str,
    source_packet_id: str,
    policy_comparison_id: str,
    update: dict[str, Any],
    quote: dict[str, Any],
    comparison: dict[str, Any],
) -> dict[str, Any]:
    strong_quote = (
        _bool(quote.get("symbol_found"))
        and _bool(quote.get("date_found"))
        and _string(quote.get("evidence_strength_recommendation")) == "STRONG_OFFICIAL_DATE_SPECIFIC"
    )
    no_hit = _bool(comparison.get("no_hit_context_supported"))
    reviewer_required = _bool(comparison.get("reviewer_acceptance_required"))
    official_symbol = "official_public_sources" in _string(update.get("evidence_source")).lower()
    local_eod = "local_market_cache" in (
        _string(update.get("evidence_source")) + " " + _string(update.get("evidence_reference")) + " " + _string(update.get("evidence_path"))
    ).lower()
    missing = _missing_categories(update, comparison, strong_quote, no_hit)
    checklist_pass = False
    return {
        "enrichment_id": enrichment_id,
        "source_packet_id": source_packet_id,
        "policy_comparison_id": policy_comparison_id,
        "signal_date": _string(update.get("signal_date")),
        "symbol": _string(update.get("symbol")),
        "universe_name": _string(update.get("universe_name")),
        "strong_official_date_specific_quotation": strong_quote,
        "quotation_source_url": _string(quote.get("request_url")),
        "quotation_fields_observed": _string(quote.get("fields_observed")),
        "reviewed_no_hit_context_supported": no_hit,
        "reviewer_acceptance_required": reviewer_required,
        "prior_official_symbol_level_context": official_symbol,
        "local_eod_cache_context": local_eod,
        "missing_evidence_categories": "; ".join(missing),
        "remaining_blocked": bool(missing),
        "checklist_pass": checklist_pass,
        "no_approval_applied": True,
        "no_universe_export": True,
        "no_current_candidates_generated": True,
    }


def _missing_categories(update: dict[str, Any], comparison: dict[str, Any], strong_quote: bool, no_hit: bool) -> list[str]:
    missing: list[str] = []
    if not strong_quote:
        missing.append("official_same_date_quotation")
    if not no_hit:
        missing.append("reviewed_no_hit_context")
    if _bool(comparison.get("reviewer_acceptance_required")):
        missing.append("reviewer_no_hit_acceptance")
    if not _bool(update.get("survivorship_bias_resolved")):
        missing.append("survivorship_bias_resolution")
    if not _string(update.get("as_of_date")):
        missing.append("pit_safe_as_of_date")
    if not _string(update.get("is_active")):
        missing.append("active_not_delisted_evidence")
    if _string(update.get("universe_name")) == "stock_core" and not _string(update.get("is_st")):
        missing.append("stock_st_no_st_evidence")
    return sorted(set(missing))


def _summary(enrichment_id: str, packet_id: str, comparison_id: str, frame: pd.DataFrame) -> pd.DataFrame:
    blocked = _true_count(frame, "remaining_blocked")
    status = "WARN" if blocked else "PASS"
    return pd.DataFrame(
        [
            {
                "enrichment_id": enrichment_id,
                "status": status,
                "source_packet_id": packet_id,
                "policy_comparison_id": comparison_id,
                "row_count": len(frame),
                "strong_official_date_specific_quotation_count": _true_count(frame, "strong_official_date_specific_quotation"),
                "reviewed_no_hit_context_supported_count": _true_count(frame, "reviewed_no_hit_context_supported"),
                "reviewer_acceptance_required_count": _true_count(frame, "reviewer_acceptance_required"),
                "prior_official_symbol_level_context_count": _true_count(frame, "prior_official_symbol_level_context"),
                "local_eod_cache_context_count": _true_count(frame, "local_eod_cache_context"),
                "checklist_pass_count": _true_count(frame, "checklist_pass"),
                "remaining_blocked_count": blocked,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _blocker_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in frame.to_dict("records"):
        for blocker in [item.strip() for item in _string(row.get("missing_evidence_categories")).split(";") if item.strip()]:
            rows.append({"enrichment_id": row["enrichment_id"], "signal_date": row["signal_date"], "symbol": row["symbol"], "blocker": blocker})
    return pd.DataFrame(rows, columns=["enrichment_id", "signal_date", "symbol", "blocker"])


def _write_artifacts(result: PitOfficialStatusEvidencePacketEnrichmentResult, packet: Path, quotation: Path, comparison: Path) -> None:
    artifact_dir = result.artifact_paths["artifact_dir"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    result.enriched_frame.to_csv(result.artifact_paths["enriched_csv"], index=False)
    result.summary_frame.to_csv(result.artifact_paths["summary_csv"], index=False)
    result.blocker_frame.to_csv(result.artifact_paths["blocker_matrix"], index=False)
    metadata = {
        "enrichment_id": result.enrichment_id,
        "status": result.status,
        "source_packet_id": result.source_packet_id,
        "policy_comparison_id": result.policy_comparison_id,
        "row_count": result.row_count,
        "strong_official_date_specific_quotation_count": result.strong_official_date_specific_quotation_count,
        "reviewed_no_hit_context_supported_count": result.reviewed_no_hit_context_supported_count,
        "reviewer_acceptance_required_count": result.reviewer_acceptance_required_count,
        "prior_official_symbol_level_context_count": result.prior_official_symbol_level_context_count,
        "local_eod_cache_context_count": result.local_eod_cache_context_count,
        "checklist_pass_count": result.checklist_pass_count,
        "remaining_blocked_count": result.remaining_blocked_count,
        "source_packet": str(packet),
        "quotation_probe": str(quotation),
        "policy_comparison": str(comparison),
        "created_at": pd.Timestamp.utcnow().isoformat(),
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
        **SAFETY_FLAGS,
    }
    result.artifact_paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")


def _render_report(result: PitOfficialStatusEvidencePacketEnrichmentResult) -> str:
    return "\n".join(
        [
            "# PIT Official Status Evidence Packet Enrichment",
            "",
            "This workflow is report-only. It enriches evidence packet context and does not approve rows or export universe files.",
            "",
            "## Summary",
            "",
            _dict_table(result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}),
            "",
            "## Interpretation",
            "",
            "Official 1815 quotation evidence is date-specific traded-presence context.",
            "Reviewed no-hit support remains reviewer-accepted context only and does not resolve survivorship automatically.",
        ]
    )


def _paths(output_dir: str | Path, enrichment_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / enrichment_id
    return {
        "artifact_dir": artifact_dir,
        "enriched_csv": artifact_dir / "pit_official_status_evidence_packet_enrichment.csv",
        "summary_csv": artifact_dir / "pit_official_status_evidence_packet_enrichment_summary.csv",
        "blocker_matrix": artifact_dir / "remaining_enrichment_blockers.csv",
        "report": artifact_dir / "report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def _comparison_id_from_dir(path: Path) -> str:
    metadata = _load_json(path / "metadata.json")
    return _string(metadata.get("comparison_id")) or path.name


def _finalize(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=columns)
    for column in columns:
        if column not in frame.columns:
            frame[column] = ""
    for column in [
        "strong_official_date_specific_quotation",
        "reviewed_no_hit_context_supported",
        "reviewer_acceptance_required",
        "prior_official_symbol_level_context",
        "local_eod_cache_context",
        "remaining_blocked",
        "checklist_pass",
        "no_approval_applied",
        "no_universe_export",
        "no_current_candidates_generated",
    ]:
        frame[column] = frame[column].map(_bool).astype(object)
    return frame[columns].reset_index(drop=True)


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_bool).sum())


def _key(row: dict[str, Any]) -> str:
    universe = _string(row.get("universe_name")) or _string(row.get("recommended_future_universe"))
    return "|".join([_string(row.get("signal_date")), _string(row.get("symbol")), universe])


def _stable_id(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


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


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def _dict_table(values: dict[str, Any]) -> str:
    lines = ["| field | value |", "|---|---|"]
    for key, value in values.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)
