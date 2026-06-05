"""Report-only downstream impact for reviewer no-hit acceptance context."""

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
    "impact_only": True,
}

IMPACT_COLUMNS = [
    "impact_id",
    "acceptance_id",
    "enrichment_id",
    "source_packet_id",
    "reviewed_no_hit_policy_comparison_id",
    "validator_id",
    "signal_date",
    "symbol",
    "universe_name",
    "exception_type",
    "acceptance_status",
    "accepted_as_supporting_context",
    "accepted_no_hit_context",
    "accepted_no_hit_context_only",
    "source_coverage_accepted",
    "query_window_accepted",
    "no_hit_inference_accepted",
    "accepted_by",
    "accepted_at",
    "acceptance_reason",
    "limitations",
    "survivorship_rationale",
    "evidence_reference",
    "packet_context_linked",
    "checklist_row_linked",
    "policy_row_linked",
    "packet_context_gap_reduced",
    "accepted_no_hit_context_count_for_row",
    "accepted_no_hit_exception_types_for_row",
    "accepted_no_hit_missing_exception_types_for_row",
    "checklist_pass_before",
    "checklist_pass_after",
    "policy_reviewed_no_hit_support_pass_before",
    "policy_reviewed_no_hit_support_pass_after",
    "remaining_blocked",
    "checklist_blockers",
    "policy_remaining_blockers",
    "approval_applied",
    "pit_review_run",
    "export_readiness_run",
    "export_staging_run",
    "universe_exported",
    "no_clean_review_updates_created",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "impact_only",
]

PACKET_LINK_COLUMNS = [
    "impact_id",
    "acceptance_id",
    "enrichment_id",
    "source_packet_id",
    "signal_date",
    "symbol",
    "universe_name",
    "packet_context_linked",
    "accepted_no_hit_context_count",
    "accepted_no_hit_exception_types",
    "accepted_no_hit_missing_exception_types",
    "packet_context_gap_reduced",
    "packet_remaining_blocked",
    "checklist_pass_after",
    "approval_applied",
]

CHECKLIST_POLICY_COLUMNS = [
    "impact_id",
    "acceptance_id",
    "validator_id",
    "reviewed_no_hit_policy_comparison_id",
    "signal_date",
    "symbol",
    "universe_name",
    "accepted_no_hit_context_count",
    "accepted_no_hit_exception_types",
    "checklist_row_linked",
    "policy_row_linked",
    "checklist_pass_before",
    "checklist_pass_after",
    "policy_reviewed_no_hit_support_pass_before",
    "policy_reviewed_no_hit_support_pass_after",
    "remaining_blocked",
    "checklist_blockers",
    "policy_remaining_blockers",
    "approval_applied",
]

BLOCKER_COLUMNS = [
    "impact_id",
    "signal_date",
    "symbol",
    "universe_name",
    "accepted_no_hit_context_count",
    "accepted_no_hit_exception_types",
    "remaining_blocker",
    "blocker_source",
    "checklist_pass_after",
    "approval_applied",
]


@dataclass(frozen=True)
class ReviewerNoHitAcceptanceDownstreamImpactResult:
    impact_id: str
    status: str
    acceptance_id: str
    enrichment_id: str
    source_packet_id: str
    reviewed_no_hit_policy_comparison_id: str
    validator_id: str
    row_count: int
    accepted_no_hit_context_count: int
    packet_context_gap_reduced_count: int
    checklist_pass_count: int
    remaining_blocked_count: int
    impact_frame: pd.DataFrame
    packet_linkage_frame: pd.DataFrame
    checklist_policy_frame: pd.DataFrame
    remaining_blocker_frame: pd.DataFrame
    artifact_paths: dict[str, Path]


def build_reviewer_no_hit_acceptance_downstream_impact(
    *,
    acceptance: str | Path = "outputs/reports/reviewer_no_hit_source_coverage_acceptance/2e05e4b74794",
    enrichment: str | Path | None = "outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c",
    validator: str | Path | None = "outputs/reports/pit_evidence_checklist_validator/62e9eb747197",
    policy_comparison: str | Path | None = "outputs/reports/pit_evidence_policy_profile_comparison/c1a75d1091c6",
    output_dir: str | Path = "outputs/reports/reviewer_no_hit_acceptance_downstream_impact",
) -> ReviewerNoHitAcceptanceDownstreamImpactResult:
    acceptance_dir = Path(acceptance)
    enrichment_dir = Path(enrichment) if enrichment else None
    validator_dir = Path(validator) if validator else None
    policy_dir = Path(policy_comparison) if policy_comparison else None

    acceptance_meta = _load_json(acceptance_dir / "metadata.json")
    enrichment_meta = _load_json(enrichment_dir / "metadata.json") if enrichment_dir else {}
    validator_meta = _load_json(validator_dir / "metadata.json") if validator_dir else {}
    policy_meta = _load_json(policy_dir / "metadata.json") if policy_dir else {}

    acceptance_id = _string(acceptance_meta.get("acceptance_id")) or acceptance_dir.name
    enrichment_id = _string(acceptance_meta.get("enrichment_id")) or _string(enrichment_meta.get("enrichment_id"))
    source_packet_id = _string(acceptance_meta.get("source_packet_id")) or _string(enrichment_meta.get("source_packet_id"))
    comparison_id = (
        _string(acceptance_meta.get("policy_comparison_id"))
        or _string(enrichment_meta.get("policy_comparison_id"))
        or _string(policy_meta.get("comparison_id"))
    )
    validator_id = _string(validator_meta.get("validator_id")) or (validator_dir.name if validator_dir else "")

    acceptance_frame = _read_optional_csv(
        acceptance_dir / "reviewer_no_hit_source_coverage_acceptance.csv",
        fallback_columns=["signal_date", "symbol", "universe_name", "exception_type"],
    )
    enrichment_frame = _read_optional_csv(
        enrichment_dir / "pit_official_status_evidence_packet_enrichment.csv" if enrichment_dir else None,
        fallback_columns=["signal_date", "symbol", "universe_name"],
    )
    validator_frame = _read_optional_csv(
        validator_dir / "pit_evidence_checklist_validation.csv" if validator_dir else None,
        fallback_columns=["signal_date", "symbol", "universe_name"],
    )
    policy_frame = _read_optional_csv(
        policy_dir / "pit_evidence_policy_profile_comparison.csv" if policy_dir else None,
        fallback_columns=["signal_date", "symbol", "recommended_future_universe"],
    )

    impact_id = _stable_id(
        {
            "acceptance_id": acceptance_id,
            "enrichment_id": enrichment_id,
            "source_packet_id": source_packet_id,
            "policy_comparison_id": comparison_id,
            "validator_id": validator_id,
            "acceptance": acceptance_dir,
            "enrichment": enrichment_dir or "",
            "validator": validator_dir or "",
            "policy_comparison": policy_dir or "",
        }
    )

    enrichment_by_key = {_row_key(row): row for row in enrichment_frame.to_dict("records")}
    validator_by_key = {_row_key(row): row for row in validator_frame.to_dict("records")}
    policy_by_key = {_row_key(row): row for row in policy_frame.to_dict("records")}
    accepted_by_row = _accepted_context_by_row(acceptance_frame)

    rows = []
    for raw_row in acceptance_frame.to_dict("records"):
        row_key = _row_key(raw_row)
        row_context = accepted_by_row.get(row_key, {"count": 0, "types": []})
        rows.append(
            _impact_row(
                impact_id=impact_id,
                acceptance_id=acceptance_id,
                enrichment_id=enrichment_id,
                source_packet_id=source_packet_id,
                comparison_id=comparison_id,
                validator_id=validator_id,
                acceptance_row=raw_row,
                accepted_context=row_context,
                enrichment_row=enrichment_by_key.get(row_key, {}),
                validator_row=validator_by_key.get(row_key, {}),
                policy_row=policy_by_key.get(row_key, {}),
            )
        )
    impact = _finalize(pd.DataFrame(rows), IMPACT_COLUMNS)
    packet_linkage = _packet_linkage(impact)
    checklist_policy = _checklist_policy(impact)
    blockers = _remaining_blockers(impact)
    accepted_count = _true_count(impact, "accepted_no_hit_context")
    remaining_count = _unique_remaining_blocked_count(impact)
    checklist_pass_count = _true_count(impact.drop_duplicates(["signal_date", "symbol", "universe_name"]), "checklist_pass_after")
    status = "WARN" if remaining_count else "PASS"
    paths = _paths(output_dir, impact_id)
    result = ReviewerNoHitAcceptanceDownstreamImpactResult(
        impact_id=impact_id,
        status=status,
        acceptance_id=acceptance_id,
        enrichment_id=enrichment_id,
        source_packet_id=source_packet_id,
        reviewed_no_hit_policy_comparison_id=comparison_id,
        validator_id=validator_id,
        row_count=len(impact),
        accepted_no_hit_context_count=accepted_count,
        packet_context_gap_reduced_count=_true_count(packet_linkage, "packet_context_gap_reduced"),
        checklist_pass_count=checklist_pass_count,
        remaining_blocked_count=remaining_count,
        impact_frame=impact,
        packet_linkage_frame=packet_linkage,
        checklist_policy_frame=checklist_policy,
        remaining_blocker_frame=blockers,
        artifact_paths=paths,
    )
    _write_artifacts(result, acceptance_dir, enrichment_dir, validator_dir, policy_dir)
    return result


def _impact_row(
    *,
    impact_id: str,
    acceptance_id: str,
    enrichment_id: str,
    source_packet_id: str,
    comparison_id: str,
    validator_id: str,
    acceptance_row: dict[str, Any],
    accepted_context: dict[str, Any],
    enrichment_row: dict[str, Any],
    validator_row: dict[str, Any],
    policy_row: dict[str, Any],
) -> dict[str, Any]:
    exception_type = _string(acceptance_row.get("exception_type"))
    accepted = (
        exception_type in EXCEPTION_TYPES
        and _string(acceptance_row.get("acceptance_status")).upper() == "ACCEPTED_AS_SUPPORTING_CONTEXT"
        and _bool(acceptance_row.get("accepted_as_supporting_context"))
    )
    accepted_types = accepted_context.get("types", [])
    missing_types = [item for item in EXCEPTION_TYPES if item not in accepted_types]
    checklist_pass_before = _bool(validator_row.get("checklist_pass"))
    policy_pass_before = _bool(policy_row.get("checklist_pass_under_reviewed_no_hit_support"))
    checklist_blockers = _string(validator_row.get("blocker_reason")) or _string(enrichment_row.get("missing_evidence_categories"))
    policy_blockers = _string(policy_row.get("remaining_blockers"))
    remaining_blocked = True
    return {
        "impact_id": impact_id,
        "acceptance_id": acceptance_id,
        "enrichment_id": enrichment_id,
        "source_packet_id": source_packet_id,
        "reviewed_no_hit_policy_comparison_id": comparison_id,
        "validator_id": validator_id,
        "signal_date": _string(acceptance_row.get("signal_date")),
        "symbol": _string(acceptance_row.get("symbol")),
        "universe_name": _string(acceptance_row.get("universe_name")),
        "exception_type": exception_type,
        "acceptance_status": _string(acceptance_row.get("acceptance_status")),
        "accepted_as_supporting_context": _bool(acceptance_row.get("accepted_as_supporting_context")),
        "accepted_no_hit_context": accepted,
        "accepted_no_hit_context_only": accepted,
        "source_coverage_accepted": _bool(acceptance_row.get("source_coverage_accepted")),
        "query_window_accepted": _bool(acceptance_row.get("query_window_accepted")),
        "no_hit_inference_accepted": _bool(acceptance_row.get("no_hit_inference_accepted")),
        "accepted_by": _string(acceptance_row.get("accepted_by")),
        "accepted_at": _string(acceptance_row.get("accepted_at")),
        "acceptance_reason": _string(acceptance_row.get("acceptance_reason")),
        "limitations": _string(acceptance_row.get("limitations")),
        "survivorship_rationale": _string(acceptance_row.get("survivorship_rationale")),
        "evidence_reference": _string(acceptance_row.get("evidence_reference")),
        "packet_context_linked": bool(enrichment_row),
        "checklist_row_linked": bool(validator_row),
        "policy_row_linked": bool(policy_row),
        "packet_context_gap_reduced": accepted,
        "accepted_no_hit_context_count_for_row": int(accepted_context.get("count", 0)),
        "accepted_no_hit_exception_types_for_row": ";".join(accepted_types),
        "accepted_no_hit_missing_exception_types_for_row": ";".join(missing_types),
        "checklist_pass_before": checklist_pass_before,
        "checklist_pass_after": False,
        "policy_reviewed_no_hit_support_pass_before": policy_pass_before,
        "policy_reviewed_no_hit_support_pass_after": False,
        "remaining_blocked": remaining_blocked,
        "checklist_blockers": checklist_blockers,
        "policy_remaining_blockers": policy_blockers,
        **SAFETY_FLAGS,
    }


def _accepted_context_by_row(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    if frame.empty:
        return rows
    for row in frame.to_dict("records"):
        exception_type = _string(row.get("exception_type"))
        if not exception_type:
            continue
        if _string(row.get("acceptance_status")).upper() != "ACCEPTED_AS_SUPPORTING_CONTEXT":
            continue
        if not _bool(row.get("accepted_as_supporting_context")):
            continue
        context = rows.setdefault(_row_key(row), {"count": 0, "types": []})
        context["count"] += 1
        if exception_type not in context["types"]:
            context["types"].append(exception_type)
    for context in rows.values():
        context["types"] = [item for item in EXCEPTION_TYPES if item in context["types"]]
    return rows


def _packet_linkage(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if not frame.empty:
        for _, group in frame.groupby(["signal_date", "symbol", "universe_name"], dropna=False):
            first = group.iloc[0]
            rows.append(
                {
                    "impact_id": first["impact_id"],
                    "acceptance_id": first["acceptance_id"],
                    "enrichment_id": first["enrichment_id"],
                    "source_packet_id": first["source_packet_id"],
                    "signal_date": first["signal_date"],
                    "symbol": first["symbol"],
                    "universe_name": first["universe_name"],
                    "packet_context_linked": _bool(first["packet_context_linked"]),
                    "accepted_no_hit_context_count": int(first["accepted_no_hit_context_count_for_row"]),
                    "accepted_no_hit_exception_types": first["accepted_no_hit_exception_types_for_row"],
                    "accepted_no_hit_missing_exception_types": first["accepted_no_hit_missing_exception_types_for_row"],
                    "packet_context_gap_reduced": _bool(group["packet_context_gap_reduced"].map(_bool).any()),
                    "packet_remaining_blocked": _bool(first["remaining_blocked"]),
                    "checklist_pass_after": False,
                    "approval_applied": False,
                }
            )
    return _finalize(pd.DataFrame(rows), PACKET_LINK_COLUMNS)


def _checklist_policy(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if not frame.empty:
        for _, group in frame.groupby(["signal_date", "symbol", "universe_name"], dropna=False):
            first = group.iloc[0]
            rows.append(
                {
                    "impact_id": first["impact_id"],
                    "acceptance_id": first["acceptance_id"],
                    "validator_id": first["validator_id"],
                    "reviewed_no_hit_policy_comparison_id": first["reviewed_no_hit_policy_comparison_id"],
                    "signal_date": first["signal_date"],
                    "symbol": first["symbol"],
                    "universe_name": first["universe_name"],
                    "accepted_no_hit_context_count": int(first["accepted_no_hit_context_count_for_row"]),
                    "accepted_no_hit_exception_types": first["accepted_no_hit_exception_types_for_row"],
                    "checklist_row_linked": _bool(first["checklist_row_linked"]),
                    "policy_row_linked": _bool(first["policy_row_linked"]),
                    "checklist_pass_before": _bool(first["checklist_pass_before"]),
                    "checklist_pass_after": False,
                    "policy_reviewed_no_hit_support_pass_before": _bool(first["policy_reviewed_no_hit_support_pass_before"]),
                    "policy_reviewed_no_hit_support_pass_after": False,
                    "remaining_blocked": True,
                    "checklist_blockers": first["checklist_blockers"],
                    "policy_remaining_blockers": first["policy_remaining_blockers"],
                    "approval_applied": False,
                }
            )
    return _finalize(pd.DataFrame(rows), CHECKLIST_POLICY_COLUMNS)


def _remaining_blockers(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if not frame.empty:
        for _, group in frame.groupby(["signal_date", "symbol", "universe_name"], dropna=False):
            first = group.iloc[0]
            blockers = _split_blockers(first["checklist_blockers"]) or _split_blockers(first["policy_remaining_blockers"])
            if not blockers:
                blockers = ["remaining_pit_evidence_review_required"]
            for blocker in blockers:
                rows.append(
                    {
                        "impact_id": first["impact_id"],
                        "signal_date": first["signal_date"],
                        "symbol": first["symbol"],
                        "universe_name": first["universe_name"],
                        "accepted_no_hit_context_count": int(first["accepted_no_hit_context_count_for_row"]),
                        "accepted_no_hit_exception_types": first["accepted_no_hit_exception_types_for_row"],
                        "remaining_blocker": blocker,
                        "blocker_source": "checklist_validator_or_policy_comparison",
                        "checklist_pass_after": False,
                        "approval_applied": False,
                    }
                )
    return _finalize(pd.DataFrame(rows), BLOCKER_COLUMNS)


def _write_artifacts(
    result: ReviewerNoHitAcceptanceDownstreamImpactResult,
    acceptance_dir: Path,
    enrichment_dir: Path | None,
    validator_dir: Path | None,
    policy_dir: Path | None,
) -> None:
    artifact_dir = result.artifact_paths["artifact_dir"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    result.impact_frame.to_csv(result.artifact_paths["impact_csv"], index=False)
    result.packet_linkage_frame.to_csv(result.artifact_paths["packet_linkage_csv"], index=False)
    result.checklist_policy_frame.to_csv(result.artifact_paths["checklist_policy_csv"], index=False)
    result.remaining_blocker_frame.to_csv(result.artifact_paths["remaining_blockers_csv"], index=False)
    metadata = {
        "impact_id": result.impact_id,
        "status": result.status,
        "acceptance_id": result.acceptance_id,
        "enrichment_id": result.enrichment_id,
        "source_packet_id": result.source_packet_id,
        "reviewed_no_hit_policy_comparison_id": result.reviewed_no_hit_policy_comparison_id,
        "validator_id": result.validator_id,
        "row_count": result.row_count,
        "accepted_no_hit_context_count": result.accepted_no_hit_context_count,
        "packet_context_gap_reduced_count": result.packet_context_gap_reduced_count,
        "checklist_pass_count": result.checklist_pass_count,
        "remaining_blocked_count": result.remaining_blocked_count,
        "acceptance_root": str(acceptance_dir),
        "enrichment_root": str(enrichment_dir or ""),
        "validator_root": str(validator_dir or ""),
        "policy_comparison_root": str(policy_dir or ""),
        "created_at": pd.Timestamp.utcnow().isoformat(),
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
        **SAFETY_FLAGS,
    }
    result.artifact_paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")


def _render_report(result: ReviewerNoHitAcceptanceDownstreamImpactResult) -> str:
    summary = {
        "impact_id": result.impact_id,
        "status": result.status,
        "acceptance_id": result.acceptance_id,
        "enrichment_id": result.enrichment_id,
        "source_packet_id": result.source_packet_id,
        "reviewed_no_hit_policy_comparison_id": result.reviewed_no_hit_policy_comparison_id,
        "validator_id": result.validator_id,
        "row_count": result.row_count,
        "accepted_no_hit_context_count": result.accepted_no_hit_context_count,
        "packet_context_gap_reduced_count": result.packet_context_gap_reduced_count,
        "checklist_pass_count": result.checklist_pass_count,
        "remaining_blocked_count": result.remaining_blocked_count,
        "approval_applied": False,
    }
    return "\n".join(
        [
            "# Reviewer No-Hit Acceptance Downstream Impact",
            "",
            "This workflow is report-only. It links reviewer-accepted no-hit supporting context to packet, checklist, and policy impact views without approving PIT universe rows.",
            "",
            "## Summary",
            "",
            _dict_table(summary),
            "",
            "## Interpretation",
            "",
            "Accepted no-hit context can reduce context gaps only.",
            "Checklist pass remains false, remaining blockers remain visible, and no clean review updates are created.",
        ]
    )


def _paths(output_dir: str | Path, impact_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / impact_id
    return {
        "artifact_dir": artifact_dir,
        "impact_csv": artifact_dir / "reviewer_no_hit_acceptance_downstream_impact.csv",
        "packet_linkage_csv": artifact_dir / "acceptance_to_packet_linkage_matrix.csv",
        "checklist_policy_csv": artifact_dir / "acceptance_to_checklist_policy_matrix.csv",
        "remaining_blockers_csv": artifact_dir / "remaining_blockers_after_acceptance.csv",
        "report": artifact_dir / "report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def _read_optional_csv(path: Path | None, fallback_columns: list[str]) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame(columns=fallback_columns)
    return read_csv_preserve_symbol_columns(path, keep_default_na=False)


def _finalize(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=columns)
    for column in columns:
        if column not in frame.columns:
            frame[column] = ""
    for column in [
        "accepted_as_supporting_context",
        "accepted_no_hit_context",
        "accepted_no_hit_context_only",
        "source_coverage_accepted",
        "query_window_accepted",
        "no_hit_inference_accepted",
        "packet_context_linked",
        "checklist_row_linked",
        "policy_row_linked",
        "packet_context_gap_reduced",
        "checklist_pass_before",
        "checklist_pass_after",
        "policy_reviewed_no_hit_support_pass_before",
        "policy_reviewed_no_hit_support_pass_after",
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
        "impact_only",
    ]:
        if column in frame.columns:
            frame[column] = frame[column].map(_bool).astype(object)
    return frame[columns].reset_index(drop=True)


def _row_key(row: dict[str, Any]) -> str:
    universe = _string(row.get("universe_name")) or _string(row.get("recommended_future_universe"))
    return "|".join([_string(row.get("signal_date")), _string(row.get("symbol")), universe])


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_bool).sum())


def _unique_remaining_blocked_count(frame: pd.DataFrame) -> int:
    if frame.empty or "remaining_blocked" not in frame.columns:
        return 0
    blocked = frame.loc[frame["remaining_blocked"].map(_bool)]
    if blocked.empty:
        return 0
    return len(blocked[["signal_date", "symbol", "universe_name"]].drop_duplicates())


def _split_blockers(value: Any) -> list[str]:
    text = _string(value)
    if not text:
        return []
    normalized = text.replace(",", ";")
    return [item.strip() for item in normalized.split(";") if item.strip()]


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
