"""Report-only reviewer acceptance for no-hit source coverage."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns


EXCEPTION_TYPES = [
    "DELISTING",
    "ST_RISK_WARNING",
    "SUSPENSION_RESUMPTION",
    "SURVIVORSHIP_RATIONALE",
]

VALID_ACCEPTANCE_STATUSES = {
    "NEEDS_REVIEW",
    "ACCEPTED_AS_SUPPORTING_CONTEXT",
    "REJECTED",
    "NEEDS_MORE_EVIDENCE",
}

SAFETY_FLAGS = {
    "approval_applied": False,
    "pit_review_run": False,
    "export_readiness_run": False,
    "export_staging_run": False,
    "universe_exported": False,
    "active_worklist_mutated": False,
    "no_clean_review_updates_created": True,
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
    "acceptance_only": True,
}

ACCEPTANCE_COLUMNS = [
    "acceptance_id",
    "enrichment_id",
    "source_packet_id",
    "policy_comparison_id",
    "evidence_update_plan_id",
    "activation_id",
    "replacement_acceptance_id",
    "replacement_plan_id",
    "signal_date",
    "symbol",
    "universe_name",
    "exception_type",
    "source_name",
    "source_url_or_endpoint",
    "source_type",
    "source_access_status",
    "parse_status",
    "query_window",
    "query_terms",
    "positive_hit_found",
    "no_hit_observed",
    "acceptance_status",
    "source_coverage_accepted",
    "query_window_accepted",
    "no_hit_inference_accepted",
    "reviewer_acceptance_present",
    "accepted_as_supporting_context",
    "accepted_by",
    "accepted_at",
    "acceptance_reason",
    "limitations",
    "survivorship_rationale",
    "evidence_reference",
    "survivorship_bias_resolved_candidate",
    "checklist_pass_candidate",
    "remaining_blocked",
    "blocker_reason",
    "approval_applied",
    "pit_review_run",
    "export_readiness_run",
    "export_staging_run",
    "universe_exported",
    "no_clean_review_updates_created",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "acceptance_only",
]

TEMPLATE_COLUMNS = [
    "signal_date",
    "symbol",
    "universe_name",
    "exception_type",
    "acceptance_status",
    "source_coverage_accepted",
    "query_window_accepted",
    "no_hit_inference_accepted",
    "accepted_by",
    "accepted_at",
    "acceptance_reason",
    "limitations",
    "survivorship_rationale",
    "evidence_reference",
]

SUMMARY_COLUMNS = [
    "acceptance_id",
    "status",
    "enrichment_id",
    "source_packet_id",
    "policy_comparison_id",
    "row_count",
    "accepted_count",
    "rejected_count",
    "needs_more_evidence_count",
    "needs_review_count",
    "reviewer_acceptance_required_count",
    "accepted_supporting_context_count",
    "survivorship_rationale_required_count",
    "checklist_pass_count",
    "remaining_blocked_count",
    "approval_applied",
]


@dataclass(frozen=True)
class ReviewerNoHitSourceCoverageAcceptanceResult:
    acceptance_id: str
    status: str
    enrichment_id: str
    source_packet_id: str
    policy_comparison_id: str
    row_count: int
    accepted_count: int
    rejected_count: int
    needs_more_evidence_count: int
    needs_review_count: int
    reviewer_acceptance_required_count: int
    accepted_supporting_context_count: int
    survivorship_rationale_required_count: int
    checklist_pass_count: int
    remaining_blocked_count: int
    acceptance_frame: pd.DataFrame
    template_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]


def build_reviewer_no_hit_source_coverage_acceptance(
    *,
    enrichment: str | Path = "outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c",
    audit: str | Path = "outputs/reports/manual_diagnostics/reviewer_no_hit_source_coverage_acceptance_audit_v0_1",
    policy_comparison: str | Path = "outputs/reports/pit_evidence_policy_profile_comparison/c1a75d1091c6",
    reviewer_acceptance: str | Path | None = None,
    output_dir: str | Path = "outputs/reports/reviewer_no_hit_source_coverage_acceptance",
) -> ReviewerNoHitSourceCoverageAcceptanceResult:
    enrichment_dir = Path(enrichment)
    audit_dir = Path(audit)
    comparison_dir = Path(policy_comparison)
    enrichment_meta = _load_json(enrichment_dir / "metadata.json")
    enrichment_id = _string(enrichment_meta.get("enrichment_id")) or enrichment_dir.name
    source_packet_id = _string(enrichment_meta.get("source_packet_id"))
    policy_comparison_id = _string(enrichment_meta.get("policy_comparison_id")) or _comparison_id_from_dir(comparison_dir)
    enriched = read_csv_preserve_symbol_columns(
        enrichment_dir / "pit_official_status_evidence_packet_enrichment.csv",
        keep_default_na=False,
    )
    exception_context = _load_exception_context()
    reviewer_updates = (
        read_csv_preserve_symbol_columns(reviewer_acceptance, keep_default_na=False)
        if reviewer_acceptance is not None and Path(reviewer_acceptance).exists()
        else pd.DataFrame(columns=TEMPLATE_COLUMNS)
    )
    reviewer_by_key = {_acceptance_key(row): row for row in reviewer_updates.to_dict("records")}
    acceptance_id = _stable_id(
        {
            "enrichment_id": enrichment_id,
            "source_packet_id": source_packet_id,
            "policy_comparison_id": policy_comparison_id,
            "reviewer_acceptance": str(reviewer_acceptance or ""),
        }
    )
    rows = []
    for row in enriched.to_dict("records"):
        for exception_type in EXCEPTION_TYPES:
            base = _base_acceptance_row(
                acceptance_id=acceptance_id,
                enrichment_id=enrichment_id,
                source_packet_id=source_packet_id,
                policy_comparison_id=policy_comparison_id,
                enriched_row=row,
                exception_type=exception_type,
                exception_context=exception_context,
            )
            merged = {**base, **_reviewer_fields(reviewer_by_key.get(_acceptance_key(base), {}))}
            rows.append(_validate_acceptance_row(merged))
    acceptance = _finalize(pd.DataFrame(rows), ACCEPTANCE_COLUMNS)
    template = _template_frame(acceptance)
    summary = _summary(acceptance_id, enrichment_id, source_packet_id, policy_comparison_id, acceptance)
    status = _string(summary.iloc[0].get("status")) if not summary.empty else "WARN"
    paths = _paths(output_dir, acceptance_id)
    result = ReviewerNoHitSourceCoverageAcceptanceResult(
        acceptance_id=acceptance_id,
        status=status,
        enrichment_id=enrichment_id,
        source_packet_id=source_packet_id,
        policy_comparison_id=policy_comparison_id,
        row_count=len(acceptance),
        accepted_count=_status_count(acceptance, "ACCEPTED_AS_SUPPORTING_CONTEXT"),
        rejected_count=_status_count(acceptance, "REJECTED"),
        needs_more_evidence_count=_status_count(acceptance, "NEEDS_MORE_EVIDENCE"),
        needs_review_count=_status_count(acceptance, "NEEDS_REVIEW"),
        reviewer_acceptance_required_count=len(acceptance),
        accepted_supporting_context_count=_true_count(acceptance, "accepted_as_supporting_context"),
        survivorship_rationale_required_count=int((acceptance["exception_type"] == "SURVIVORSHIP_RATIONALE").sum()),
        checklist_pass_count=_true_count(acceptance, "checklist_pass_candidate"),
        remaining_blocked_count=_unique_blocked_count(acceptance),
        acceptance_frame=acceptance,
        template_frame=template,
        summary_frame=summary,
        artifact_paths=paths,
    )
    _write_artifacts(result, audit_dir, enrichment_dir, comparison_dir)
    return result


def _base_acceptance_row(
    *,
    acceptance_id: str,
    enrichment_id: str,
    source_packet_id: str,
    policy_comparison_id: str,
    enriched_row: dict[str, Any],
    exception_type: str,
    exception_context: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    signal_date = _string(enriched_row.get("signal_date"))
    symbol = _string(enriched_row.get("symbol"))
    universe_name = _string(enriched_row.get("universe_name"))
    context = exception_context.get("|".join([signal_date, symbol, universe_name, exception_type]), {})
    return {
        "acceptance_id": acceptance_id,
        "enrichment_id": enrichment_id,
        "source_packet_id": source_packet_id,
        "policy_comparison_id": policy_comparison_id,
        "evidence_update_plan_id": "",
        "activation_id": "",
        "replacement_acceptance_id": "",
        "replacement_plan_id": "",
        "signal_date": signal_date,
        "symbol": symbol,
        "universe_name": universe_name,
        "exception_type": exception_type,
        "source_name": _string(context.get("source_name")) or _default_source_name(exception_type),
        "source_url_or_endpoint": _string(context.get("source_url_or_endpoint")) or _string(enriched_row.get("quotation_source_url")),
        "source_type": _string(context.get("source_type")) or _default_source_type(exception_type),
        "source_access_status": _string(context.get("source_access_status")) or "SEE_ENRICHMENT_CONTEXT",
        "parse_status": _string(context.get("parse_status")) or "SEE_ENRICHMENT_CONTEXT",
        "query_window": _string(context.get("query_window")) or _default_query_window(exception_type, signal_date),
        "query_terms": _string(context.get("query_terms")) or symbol,
        "positive_hit_found": _bool(context.get("positive_hit_found")),
        "no_hit_observed": _bool(context.get("no_hit_observed")) or _bool(enriched_row.get("reviewed_no_hit_context_supported")),
        "acceptance_status": "NEEDS_REVIEW",
        "source_coverage_accepted": False,
        "query_window_accepted": False,
        "no_hit_inference_accepted": False,
        "reviewer_acceptance_present": False,
        "accepted_as_supporting_context": False,
        "accepted_by": "",
        "accepted_at": "",
        "acceptance_reason": "",
        "limitations": "No-hit support is policy-dependent and cannot approve a row by itself.",
        "survivorship_rationale": "",
        "evidence_reference": _string(context.get("source_url_or_endpoint")) or _string(enriched_row.get("quotation_source_url")),
        "survivorship_bias_resolved_candidate": False,
        "checklist_pass_candidate": False,
        "remaining_blocked": True,
        "blocker_reason": _string(enriched_row.get("missing_evidence_categories")),
        **SAFETY_FLAGS,
    }


def _reviewer_fields(row: dict[str, Any]) -> dict[str, Any]:
    if not row:
        return {}
    return {
        "acceptance_status": _string(row.get("acceptance_status")) or "NEEDS_REVIEW",
        "source_coverage_accepted": _bool(row.get("source_coverage_accepted")),
        "query_window_accepted": _bool(row.get("query_window_accepted")),
        "no_hit_inference_accepted": _bool(row.get("no_hit_inference_accepted")),
        "accepted_by": _string(row.get("accepted_by")),
        "accepted_at": _string(row.get("accepted_at")),
        "acceptance_reason": _string(row.get("acceptance_reason")),
        "limitations": _string(row.get("limitations")),
        "survivorship_rationale": _string(row.get("survivorship_rationale")),
        "evidence_reference": _string(row.get("evidence_reference")),
    }


def _validate_acceptance_row(row: dict[str, Any]) -> dict[str, Any]:
    status = _string(row.get("acceptance_status")).upper() or "NEEDS_REVIEW"
    blockers = []
    if status not in VALID_ACCEPTANCE_STATUSES:
        status = "NEEDS_MORE_EVIDENCE"
        blockers.append("invalid_acceptance_status")
    if status == "ACCEPTED_AS_SUPPORTING_CONTEXT":
        for field in ["accepted_by", "accepted_at", "acceptance_reason", "evidence_reference"]:
            if not _string(row.get(field)):
                blockers.append(f"missing_{field}")
        for field in ["source_coverage_accepted", "query_window_accepted", "no_hit_inference_accepted"]:
            if not _bool(row.get(field)):
                blockers.append(f"{field}_false")
        if _string(row.get("exception_type")) == "SURVIVORSHIP_RATIONALE" and not _string(
            row.get("survivorship_rationale")
        ):
            blockers.append("missing_survivorship_rationale")
        if blockers:
            status = "NEEDS_MORE_EVIDENCE"
    row["acceptance_status"] = status
    row["reviewer_acceptance_present"] = status == "ACCEPTED_AS_SUPPORTING_CONTEXT" and not blockers
    row["accepted_as_supporting_context"] = bool(row["reviewer_acceptance_present"])
    row["survivorship_bias_resolved_candidate"] = (
        row["accepted_as_supporting_context"] and _string(row.get("exception_type")) == "SURVIVORSHIP_RATIONALE"
    )
    row["checklist_pass_candidate"] = False
    existing = _string(row.get("blocker_reason"))
    row["blocker_reason"] = "; ".join(item for item in [existing, "; ".join(blockers)] if item)
    row["remaining_blocked"] = True
    row.update(SAFETY_FLAGS)
    return row


def _summary(
    acceptance_id: str,
    enrichment_id: str,
    source_packet_id: str,
    policy_comparison_id: str,
    frame: pd.DataFrame,
) -> pd.DataFrame:
    accepted = _status_count(frame, "ACCEPTED_AS_SUPPORTING_CONTEXT")
    remaining = _unique_blocked_count(frame)
    status = "WARN" if remaining or len(frame) else "PASS"
    return pd.DataFrame(
        [
            {
                "acceptance_id": acceptance_id,
                "status": status,
                "enrichment_id": enrichment_id,
                "source_packet_id": source_packet_id,
                "policy_comparison_id": policy_comparison_id,
                "row_count": len(frame),
                "accepted_count": accepted,
                "rejected_count": _status_count(frame, "REJECTED"),
                "needs_more_evidence_count": _status_count(frame, "NEEDS_MORE_EVIDENCE"),
                "needs_review_count": _status_count(frame, "NEEDS_REVIEW"),
                "reviewer_acceptance_required_count": len(frame),
                "accepted_supporting_context_count": _true_count(frame, "accepted_as_supporting_context"),
                "survivorship_rationale_required_count": int((frame["exception_type"] == "SURVIVORSHIP_RATIONALE").sum()) if not frame.empty else 0,
                "checklist_pass_count": _true_count(frame, "checklist_pass_candidate"),
                "remaining_blocked_count": remaining,
                "approval_applied": False,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _write_artifacts(
    result: ReviewerNoHitSourceCoverageAcceptanceResult,
    audit_dir: Path,
    enrichment_dir: Path,
    comparison_dir: Path,
) -> None:
    artifact_dir = result.artifact_paths["artifact_dir"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    result.acceptance_frame.to_csv(result.artifact_paths["acceptance_csv"], index=False)
    result.template_frame.to_csv(result.artifact_paths["template_csv"], index=False)
    result.summary_frame.to_csv(result.artifact_paths["summary_csv"], index=False)
    for source_name, dest_key in [
        ("source_coverage_acceptance_rules.csv", "source_rules_csv"),
        ("query_window_rules.csv", "query_rules_csv"),
        ("survivorship_rationale_template.csv", "survivorship_template_csv"),
        ("blocker_after_acceptance_matrix.csv", "blocker_matrix_csv"),
    ]:
        source = audit_dir / source_name
        dest = result.artifact_paths[dest_key]
        if source.exists():
            dest.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            pd.DataFrame().to_csv(dest, index=False)
    metadata = {
        "acceptance_id": result.acceptance_id,
        "status": result.status,
        "enrichment_id": result.enrichment_id,
        "source_packet_id": result.source_packet_id,
        "policy_comparison_id": result.policy_comparison_id,
        "row_count": result.row_count,
        "accepted_count": result.accepted_count,
        "rejected_count": result.rejected_count,
        "needs_more_evidence_count": result.needs_more_evidence_count,
        "needs_review_count": result.needs_review_count,
        "reviewer_acceptance_required_count": result.reviewer_acceptance_required_count,
        "accepted_supporting_context_count": result.accepted_supporting_context_count,
        "survivorship_rationale_required_count": result.survivorship_rationale_required_count,
        "checklist_pass_count": result.checklist_pass_count,
        "remaining_blocked_count": result.remaining_blocked_count,
        "enrichment_root": str(enrichment_dir),
        "policy_comparison_root": str(comparison_dir),
        "created_at": pd.Timestamp.utcnow().isoformat(),
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
        **SAFETY_FLAGS,
    }
    result.artifact_paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")


def _render_report(result: ReviewerNoHitSourceCoverageAcceptanceResult) -> str:
    return "\n".join(
        [
            "# Reviewer No-Hit Source Coverage Acceptance",
            "",
            "This workflow is report-only. It records reviewer acceptance context for no-hit source coverage and does not approve PIT universe rows.",
            "",
            "## Summary",
            "",
            _dict_table(result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}),
            "",
            "## Interpretation",
            "",
            "Accepted no-hit coverage can only become supporting context.",
            "Checklist pass remains false and remaining PIT metadata/survivorship blockers stay visible for later validators.",
        ]
    )


def _template_frame(frame: pd.DataFrame) -> pd.DataFrame:
    template = frame[TEMPLATE_COLUMNS].copy()
    template["acceptance_status"] = "NEEDS_REVIEW"
    template["source_coverage_accepted"] = False
    template["query_window_accepted"] = False
    template["no_hit_inference_accepted"] = False
    template["accepted_by"] = ""
    template["accepted_at"] = ""
    template["acceptance_reason"] = ""
    return template


def _load_exception_context() -> dict[str, dict[str, Any]]:
    path = Path("outputs/reports/manual_diagnostics/szse_exception_no_hit_status_probe_v0_1/exception_search_results.csv")
    if not path.exists():
        return {}
    frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    rows = {}
    for row in frame.to_dict("records"):
        exception_type = _string(row.get("exception_type"))
        for signal_date in _first_batch_dates():
            key = "|".join([signal_date, _string(row.get("symbol")), _universe_for_symbol(row.get("symbol")), exception_type])
            rows.setdefault(key, row)
    return rows


def _first_batch_dates() -> list[str]:
    return ["2024-04-02", "2024-04-09", "2024-04-11", "2024-04-16", "2024-04-19", "2024-04-24", "2024-04-26", "2024-05-06"]


def _universe_for_symbol(symbol: Any) -> str:
    return "stock_core" if _string(symbol) == "000001" else "etf_core"


def _default_source_name(exception_type: str) -> str:
    return "Reviewer survivorship rationale" if exception_type == "SURVIVORSHIP_RATIONALE" else "Official exception no-hit source coverage"


def _default_source_type(exception_type: str) -> str:
    return "reviewer_survivorship_rationale" if exception_type == "SURVIVORSHIP_RATIONALE" else "official_exception_no_hit_context"


def _default_query_window(exception_type: str, signal_date: str) -> str:
    if exception_type == "SUSPENSION_RESUMPTION":
        return f"prior trading-day window through {signal_date} close"
    if exception_type == "ST_RISK_WARNING":
        return f"risk-warning effective-status window through {signal_date}"
    if exception_type == "SURVIVORSHIP_RATIONALE":
        return f"identity/listing plus accepted exception no-hit coverage through {signal_date}"
    return f"listed-date or market-entry through {signal_date}"


def _paths(output_dir: str | Path, acceptance_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / acceptance_id
    return {
        "artifact_dir": artifact_dir,
        "acceptance_csv": artifact_dir / "reviewer_no_hit_source_coverage_acceptance.csv",
        "template_csv": artifact_dir / "reviewer_no_hit_acceptance_template.csv",
        "summary_csv": artifact_dir / "reviewer_no_hit_source_coverage_acceptance_summary.csv",
        "source_rules_csv": artifact_dir / "source_coverage_acceptance_rules.csv",
        "query_rules_csv": artifact_dir / "query_window_acceptance_rules.csv",
        "survivorship_template_csv": artifact_dir / "survivorship_rationale_template.csv",
        "blocker_matrix_csv": artifact_dir / "blocker_after_acceptance_matrix.csv",
        "report": artifact_dir / "report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def _finalize(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=columns)
    for column in columns:
        if column not in frame.columns:
            frame[column] = ""
    for column in [
        "positive_hit_found",
        "no_hit_observed",
        "source_coverage_accepted",
        "query_window_accepted",
        "no_hit_inference_accepted",
        "reviewer_acceptance_present",
        "accepted_as_supporting_context",
        "survivorship_bias_resolved_candidate",
        "checklist_pass_candidate",
        "remaining_blocked",
        "approval_applied",
        "pit_review_run",
        "export_readiness_run",
        "export_staging_run",
        "universe_exported",
        "no_clean_review_updates_created",
        "no_data_raw_write",
        "no_data_processed_write",
        "no_current_candidates_generated",
        "acceptance_only",
    ]:
        frame[column] = frame[column].map(_bool).astype(object)
    return frame[columns].reset_index(drop=True)


def _comparison_id_from_dir(path: Path) -> str:
    metadata = _load_json(path / "metadata.json")
    return _string(metadata.get("comparison_id")) or path.name


def _acceptance_key(row: dict[str, Any]) -> str:
    return "|".join([
        _string(row.get("signal_date")),
        _string(row.get("symbol")),
        _string(row.get("universe_name")),
        _string(row.get("exception_type")),
    ])


def _status_count(frame: pd.DataFrame, status: str) -> int:
    if frame.empty or "acceptance_status" not in frame.columns:
        return 0
    return int((frame["acceptance_status"].astype(str).str.upper() == status).sum())


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_bool).sum())


def _unique_blocked_count(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    blocked = frame.loc[frame["remaining_blocked"].map(_bool)]
    if blocked.empty:
        return 0
    return len(blocked[["signal_date", "symbol", "universe_name"]].drop_duplicates())


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
