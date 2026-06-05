"""Report-only first-batch reviewer evidence completion planning.

This workflow gathers the first-batch stock/ETF evidence rows and turns the
remaining PIT evidence gaps into manual completion templates. It never applies
approval, creates clean review updates, writes universe inputs, runs PIT review,
exports data, builds snapshots, runs current-candidates, computes labels, or
mutates cache.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns


EXCEPTION_TYPES = [
    "DELISTING",
    "ST_RISK_WARNING",
    "SUSPENSION_RESUMPTION",
    "SURVIVORSHIP_RATIONALE",
]

REQUIRED_METADATA_FIELDS = [
    "as_of_date",
    "name",
    "instrument_type",
    "exchange",
    "industry",
    "min_lot",
    "t_plus_rule",
    "available_time",
    "revision_id",
    "source",
]

PLAN_COLUMNS = [
    "plan_id",
    "source_evidence_update_plan_id",
    "downstream_impact_id",
    "reviewer_no_hit_acceptance_id",
    "enrichment_id",
    "source_packet_id",
    "reviewed_no_hit_policy_comparison_id",
    "validator_id",
    "activation_id",
    "acceptance_id",
    "replacement_plan_id",
    "source_split_plan_id",
    "source_policy_audit_id",
    "source_worklist_id",
    "signal_date",
    "symbol",
    "universe_name",
    "resolved_instrument_type",
    "review_status",
    "include_flag",
    "valid_for_signal_date",
    "survivorship_bias_resolved",
    "reviewer_completion_required",
    "no_hit_acceptance_required",
    "survivorship_rationale_required",
    "metadata_completion_required",
    "strong_official_date_specific_quotation",
    "reviewed_no_hit_context_supported",
    "accepted_no_hit_context_count",
    "accepted_no_hit_exception_types",
    "missing_no_hit_exception_types",
    "missing_evidence_fields",
    "missing_evidence_categories",
    "checklist_pass",
    "remaining_blocked",
    "checklist_blockers",
    "quotation_source_url",
    "quotation_proves_not_delisted",
    "quotation_proves_st_no_st",
    "quotation_resolves_survivorship",
    "approved_for_pit_universe_candidate",
    "clean_review_updates_created",
    "approval_applied",
    "pit_review_run",
    "export_readiness_run",
    "export_staging_run",
    "universe_exported",
    "active_worklist_mutated",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "no_snapshot_built",
    "no_forward_labels",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "completion_planning_only",
]

MISSING_MATRIX_COLUMNS = [
    "plan_id",
    "signal_date",
    "symbol",
    "universe_name",
    "missing_evidence_fields",
    "missing_evidence_categories",
    "checklist_blockers",
    "reviewer_completion_required",
    "remaining_blocked",
]

TODO_COLUMNS = [
    "plan_id",
    "signal_date",
    "symbol",
    "universe_name",
    "exception_type",
    "acceptance_status",
    "accepted_no_hit_context",
    "reviewer_action",
    "source_lineage",
    "approval_applied",
]

TEMPLATE_COLUMNS = [
    "signal_date",
    "symbol",
    "universe_name",
    "review_status",
    "include_flag",
    "valid_for_signal_date",
    "survivorship_bias_resolved",
    "reviewer",
    "reviewed_at",
    "review_reason",
    "evidence_source",
    "evidence_path",
    "evidence_reference",
    "listed_date",
    "delisted_date",
    "is_active",
    "is_st",
    "is_suspended",
    "listed_date_evidence",
    "delisted_date_evidence",
    "is_active_evidence",
    "as_of_date",
    "name",
    "instrument_type",
    "exchange",
    "industry",
    "min_lot",
    "t_plus_rule",
    "available_time",
    "revision_id",
    "source",
    "completion_notes",
]

SAFETY_STATEMENT = (
    "No approval, rejection, clean review updates, PIT review, export-readiness, "
    "staging, universe export, data/raw write, data/processed write, active worklist "
    "mutation, current-candidates generation, snapshot build, forward labels, live "
    "trading, broker API, orders, messages, API/LLM calls, or cache mutation was invoked."
)


@dataclass(frozen=True)
class FirstBatchReviewerEvidenceCompletionPlanSettings:
    output_dir: Path = Path("outputs/reports/first_batch_reviewer_evidence_completion_plan")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    enable_approval: bool = False
    enable_clean_review_updates: bool = False
    enable_pit_review: bool = False
    enable_export_readiness: bool = False
    enable_export_staging: bool = False
    enable_universe_export: bool = False
    enable_data_raw_write: bool = False
    enable_data_processed_write: bool = False
    enable_current_candidates: bool = False
    enable_snapshot_build: bool = False
    enable_forward_labels: bool = False
    enable_cache_mutation: bool = False
    enable_live_trading: bool = False
    enable_broker_api: bool = False
    enable_order_placement: bool = False
    enable_message_delivery: bool = False


@dataclass(frozen=True)
class FirstBatchReviewerEvidenceCompletionPlanRequest:
    evidence_update_plan: Path
    downstream_impact: Path | None = None
    enrichment: Path | None = None
    validator: Path | None = None
    policy_comparison: Path | None = None


@dataclass(frozen=True)
class FirstBatchReviewerEvidenceCompletionPlanResult:
    plan_id: str
    status: str
    request: FirstBatchReviewerEvidenceCompletionPlanRequest
    source_evidence_update_plan_id: str
    downstream_impact_id: str
    reviewer_no_hit_acceptance_id: str
    enrichment_id: str
    source_packet_id: str
    reviewed_no_hit_policy_comparison_id: str
    validator_id: str
    row_count: int
    stock_core_row_count: int
    etf_core_row_count: int
    reviewer_completion_required_count: int
    no_hit_acceptance_required_count: int
    survivorship_rationale_required_count: int
    metadata_completion_required_count: int
    checklist_pass_count: int
    remaining_blocked_count: int
    clean_review_updates_created: bool
    approval_applied: bool
    plan_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_first_batch_reviewer_evidence_completion_plan(
    *,
    evidence_update_plan: str | Path = "outputs/reports/activated_replacement_worklist_evidence_update_plan/4e268d67bd7d",
    downstream_impact: str | Path | None = "outputs/reports/reviewer_no_hit_acceptance_downstream_impact/9e164963455e",
    enrichment: str | Path | None = "outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c",
    validator: str | Path | None = "outputs/reports/pit_evidence_checklist_validator/62e9eb747197",
    policy_comparison: str | Path | None = "outputs/reports/pit_evidence_policy_profile_comparison/c1a75d1091c6",
    output_dir: str | Path | None = None,
    settings: FirstBatchReviewerEvidenceCompletionPlanSettings | None = None,
) -> FirstBatchReviewerEvidenceCompletionPlanResult:
    resolved_settings = settings or FirstBatchReviewerEvidenceCompletionPlanSettings()
    if output_dir is not None:
        resolved_settings = _replace_output_dir(resolved_settings, Path(output_dir))
    _assert_settings_safe(resolved_settings)
    request = FirstBatchReviewerEvidenceCompletionPlanRequest(
        evidence_update_plan=Path(evidence_update_plan),
        downstream_impact=Path(downstream_impact) if downstream_impact else None,
        enrichment=Path(enrichment) if enrichment else None,
        validator=Path(validator) if validator else None,
        policy_comparison=Path(policy_comparison) if policy_comparison else None,
    )

    first_batch = load_first_batch_rows_for_completion_plan(request.evidence_update_plan)
    downstream_frame = _read_optional_artifact_csv(request.downstream_impact, "reviewer_no_hit_acceptance_downstream_impact.csv")
    enrichment_frame = _read_optional_artifact_csv(request.enrichment, "pit_official_status_evidence_packet_enrichment.csv")
    validator_frame = _read_optional_artifact_csv(request.validator, "pit_evidence_checklist_validation.csv")
    policy_frame = _read_optional_artifact_csv(request.policy_comparison, "pit_evidence_policy_profile_comparison.csv")
    metadata = _lineage_metadata(request)
    plan_id = _plan_id(request, first_batch, resolved_settings)
    plan_frame = _build_plan_frame(
        plan_id=plan_id,
        first_batch=first_batch,
        downstream_frame=downstream_frame,
        enrichment_frame=enrichment_frame,
        validator_frame=validator_frame,
        policy_frame=policy_frame,
        metadata=metadata,
    )
    counts = _counts(plan_frame)
    paths = resolve_first_batch_reviewer_evidence_completion_plan_paths(resolved_settings.output_dir, plan_id)
    result = FirstBatchReviewerEvidenceCompletionPlanResult(
        plan_id=plan_id,
        status="WARN" if counts["remaining_blocked_count"] else "PASS",
        request=request,
        source_evidence_update_plan_id=metadata["source_evidence_update_plan_id"],
        downstream_impact_id=metadata["downstream_impact_id"],
        reviewer_no_hit_acceptance_id=metadata["reviewer_no_hit_acceptance_id"],
        enrichment_id=metadata["enrichment_id"],
        source_packet_id=metadata["source_packet_id"],
        reviewed_no_hit_policy_comparison_id=metadata["reviewed_no_hit_policy_comparison_id"],
        validator_id=metadata["validator_id"],
        row_count=len(plan_frame),
        stock_core_row_count=_equals_count(plan_frame, "universe_name", "stock_core"),
        etf_core_row_count=_equals_count(plan_frame, "universe_name", "etf_core"),
        reviewer_completion_required_count=counts["reviewer_completion_required_count"],
        no_hit_acceptance_required_count=counts["no_hit_acceptance_required_count"],
        survivorship_rationale_required_count=counts["survivorship_rationale_required_count"],
        metadata_completion_required_count=counts["metadata_completion_required_count"],
        checklist_pass_count=counts["checklist_pass_count"],
        remaining_blocked_count=counts["remaining_blocked_count"],
        clean_review_updates_created=False,
        approval_applied=False,
        plan_frame=plan_frame,
        artifact_paths=paths,
        warnings=[],
        audit_metadata=_audit_metadata(resolved_settings),
    )
    if resolved_settings.write_artifacts:
        write_first_batch_reviewer_evidence_completion_plan_artifacts(result, downstream_frame)
    return result


def load_first_batch_rows_for_completion_plan(evidence_update_plan: str | Path) -> pd.DataFrame:
    path = Path(evidence_update_plan)
    if not path.exists():
        raise FileNotFoundError(f"Evidence update plan path not found: {path}")
    if path.is_file():
        frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
        return _first_batch_from_plan_frame(frame)
    stock = path / "stock_core_first_batch_package.csv"
    etf = path / "etf_core_first_batch_package.csv"
    if stock.exists() and etf.exists():
        return _finalize_first_batch(pd.concat([_read_csv(stock), _read_csv(etf)], ignore_index=True))
    plan_csv = path / "activated_replacement_worklist_evidence_update_plan.csv"
    if plan_csv.exists():
        return _first_batch_from_plan_frame(_read_csv(plan_csv))
    raise FileNotFoundError(f"No first-batch package or evidence update plan CSV found under: {path}")


def resolve_first_batch_reviewer_evidence_completion_plan_paths(output_dir: str | Path, plan_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / plan_id
    return {
        "artifact_dir": artifact_dir,
        "plan_csv": artifact_dir / "first_batch_reviewer_evidence_completion_plan.csv",
        "row_level_missing_evidence_matrix": artifact_dir / "row_level_missing_evidence_matrix.csv",
        "reusable_symbol_level_evidence_plan": artifact_dir / "reusable_symbol_level_evidence_plan.csv",
        "date_specific_evidence_plan": artifact_dir / "date_specific_evidence_plan.csv",
        "reviewer_completion_template": artifact_dir / "reviewer_completion_template.csv",
        "reviewer_no_hit_acceptance_todo": artifact_dir / "reviewer_no_hit_acceptance_todo.csv",
        "survivorship_rationale_todo": artifact_dir / "survivorship_rationale_todo.csv",
        "metadata_completion_todo": artifact_dir / "metadata_completion_todo.csv",
        "source_lineage_summary": artifact_dir / "source_lineage_summary.csv",
        "report": artifact_dir / "report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def write_first_batch_reviewer_evidence_completion_plan_artifacts(
    result: FirstBatchReviewerEvidenceCompletionPlanResult,
    downstream_frame: pd.DataFrame | None = None,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.plan_frame.to_csv(paths["plan_csv"], index=False)
    _missing_matrix(result.plan_frame).to_csv(paths["row_level_missing_evidence_matrix"], index=False)
    _reusable_symbol_level_plan(result.plan_frame).to_csv(paths["reusable_symbol_level_evidence_plan"], index=False)
    _date_specific_plan(result.plan_frame).to_csv(paths["date_specific_evidence_plan"], index=False)
    _reviewer_completion_template(result.plan_frame).to_csv(paths["reviewer_completion_template"], index=False)
    _no_hit_todo(result.plan_frame, downstream_frame if downstream_frame is not None else pd.DataFrame()).to_csv(
        paths["reviewer_no_hit_acceptance_todo"],
        index=False,
    )
    _survivorship_todo(result.plan_frame).to_csv(paths["survivorship_rationale_todo"], index=False)
    _metadata_completion_todo(result.plan_frame).to_csv(paths["metadata_completion_todo"], index=False)
    _source_lineage_summary(result).to_csv(paths["source_lineage_summary"], index=False)
    paths["report"].write_text(render_first_batch_reviewer_evidence_completion_plan_report(result), encoding="utf-8")
    paths["metadata"].write_text(
        json.dumps(_json_safe(build_first_batch_reviewer_evidence_completion_plan_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths


def render_first_batch_reviewer_evidence_completion_plan_report(
    result: FirstBatchReviewerEvidenceCompletionPlanResult,
) -> str:
    return "\n".join(
        [
            f"# First-Batch Reviewer Evidence Completion Plan: {result.plan_id}",
            "",
            SAFETY_STATEMENT,
            "",
            "This is a manual evidence completion planning artifact only. It does not approve rows and it does not create clean review updates.",
            "",
            "## Summary",
            "",
            f"- row_count: {result.row_count}",
            f"- stock_core_row_count: {result.stock_core_row_count}",
            f"- etf_core_row_count: {result.etf_core_row_count}",
            f"- reviewer_completion_required_count: {result.reviewer_completion_required_count}",
            f"- no_hit_acceptance_required_count: {result.no_hit_acceptance_required_count}",
            f"- survivorship_rationale_required_count: {result.survivorship_rationale_required_count}",
            f"- metadata_completion_required_count: {result.metadata_completion_required_count}",
            f"- checklist_pass_count: {result.checklist_pass_count}",
            f"- remaining_blocked_count: {result.remaining_blocked_count}",
            f"- clean_review_updates_created: {result.clean_review_updates_created}",
            f"- approval_applied: {result.approval_applied}",
            "",
            "## Planning Rules",
            "",
            "- Official same-date quotation evidence remains quotation/traded context only.",
            "- Quotation evidence does not prove not-delisted, ST/no-ST, or survivorship resolution by itself.",
            "- Reviewer no-hit acceptance remains supporting context only until a separate review workflow is explicitly run.",
            "- Reviewer completion templates keep all rows non-approved.",
            "",
            "## Recommended Next Action",
            "",
            "Manually complete evidence fields and reviewer no-hit acceptance context, then rerun diagnostics-only ingestion and validator checks before any PIT review.",
            "",
        ]
    )


def build_first_batch_reviewer_evidence_completion_plan_metadata(
    result: FirstBatchReviewerEvidenceCompletionPlanResult,
) -> dict[str, Any]:
    return {
        "plan_id": result.plan_id,
        "status": result.status,
        "source_evidence_update_plan_id": result.source_evidence_update_plan_id,
        "downstream_impact_id": result.downstream_impact_id,
        "reviewer_no_hit_acceptance_id": result.reviewer_no_hit_acceptance_id,
        "enrichment_id": result.enrichment_id,
        "source_packet_id": result.source_packet_id,
        "reviewed_no_hit_policy_comparison_id": result.reviewed_no_hit_policy_comparison_id,
        "validator_id": result.validator_id,
        "row_count": result.row_count,
        "stock_core_row_count": result.stock_core_row_count,
        "etf_core_row_count": result.etf_core_row_count,
        "reviewer_completion_required_count": result.reviewer_completion_required_count,
        "no_hit_acceptance_required_count": result.no_hit_acceptance_required_count,
        "survivorship_rationale_required_count": result.survivorship_rationale_required_count,
        "metadata_completion_required_count": result.metadata_completion_required_count,
        "checklist_pass_count": result.checklist_pass_count,
        "remaining_blocked_count": result.remaining_blocked_count,
        "clean_review_updates_created": False,
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
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "completion_planning_only": True,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
        "safety_statement": SAFETY_STATEMENT,
        "warnings": result.warnings,
        **result.audit_metadata,
        "known_limitations": [
            "This workflow is report-only and does not create clean review_updates.csv.",
            "Reviewer no-hit context remains supporting context only.",
            "Quotation evidence does not resolve not-delisted, ST/no-ST, or survivorship by itself.",
            "Rows remain blocked until manually reviewed evidence is completed in a later workflow.",
        ],
    }


def _build_plan_frame(
    *,
    plan_id: str,
    first_batch: pd.DataFrame,
    downstream_frame: pd.DataFrame,
    enrichment_frame: pd.DataFrame,
    validator_frame: pd.DataFrame,
    policy_frame: pd.DataFrame,
    metadata: dict[str, str],
) -> pd.DataFrame:
    enrichment_by_key = {_row_key(row): row for row in enrichment_frame.to_dict("records")}
    validator_by_key = {_row_key(row): row for row in validator_frame.to_dict("records")}
    policy_by_key = {_row_key(row): row for row in policy_frame.to_dict("records")}
    accepted_by_key = _accepted_context_by_key(downstream_frame)
    rows: list[dict[str, Any]] = []
    for raw in first_batch.to_dict("records"):
        key = _row_key(raw)
        enrichment = enrichment_by_key.get(key, {})
        validator = validator_by_key.get(key, {})
        policy = policy_by_key.get(key, {})
        accepted = accepted_by_key.get(key, {"count": 0, "types": []})
        missing_fields = _missing_fields(raw, validator)
        missing_categories = _text(enrichment.get("missing_evidence_categories")) or _text(policy.get("remaining_blockers"))
        survivorship_required = "survivorship" in (missing_categories + " " + _text(validator.get("blocker_reason"))).lower()
        row = {
            "plan_id": plan_id,
            **metadata,
            "signal_date": _text(raw.get("signal_date")),
            "symbol": normalize_symbol_value(raw.get("symbol")),
            "universe_name": _text(raw.get("universe_name")) or _text(raw.get("future_universe_name")),
            "resolved_instrument_type": _text(raw.get("resolved_instrument_type")),
            "review_status": "NEEDS_MORE_EVIDENCE",
            "include_flag": False,
            "valid_for_signal_date": False,
            "survivorship_bias_resolved": False,
            "reviewer_completion_required": True,
            "no_hit_acceptance_required": _to_bool(enrichment.get("reviewer_acceptance_required")) or accepted["count"] < len(EXCEPTION_TYPES),
            "survivorship_rationale_required": survivorship_required,
            "metadata_completion_required": bool(missing_fields),
            "strong_official_date_specific_quotation": _to_bool(enrichment.get("strong_official_date_specific_quotation")),
            "reviewed_no_hit_context_supported": _to_bool(enrichment.get("reviewed_no_hit_context_supported")),
            "accepted_no_hit_context_count": accepted["count"],
            "accepted_no_hit_exception_types": ";".join(accepted["types"]),
            "missing_no_hit_exception_types": ";".join([item for item in EXCEPTION_TYPES if item not in accepted["types"]]),
            "missing_evidence_fields": ";".join(missing_fields),
            "missing_evidence_categories": missing_categories,
            "checklist_pass": _to_bool(validator.get("checklist_pass")) or _to_bool(enrichment.get("checklist_pass")),
            "remaining_blocked": _to_bool(validator.get("blocked")) or _to_bool(enrichment.get("remaining_blocked")),
            "checklist_blockers": _text(validator.get("blocker_reason")),
            "quotation_source_url": _text(enrichment.get("quotation_source_url")),
            "quotation_proves_not_delisted": False,
            "quotation_proves_st_no_st": False,
            "quotation_resolves_survivorship": False,
            "approved_for_pit_universe_candidate": False,
            "clean_review_updates_created": False,
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
            "no_live_trading": True,
            "no_broker_api": True,
            "no_order_placement": True,
            "no_message_sent": True,
            "completion_planning_only": True,
        }
        rows.append(row)
    return _finalize(pd.DataFrame(rows), PLAN_COLUMNS).sort_values(["universe_name", "signal_date", "symbol"]).reset_index(drop=True)


def _first_batch_from_plan_frame(frame: pd.DataFrame) -> pd.DataFrame:
    stock = _first_symbol_frame(frame.loc[frame.get("universe_name", "") == "stock_core"])
    etf = _first_symbol_frame(frame.loc[frame.get("universe_name", "") == "etf_core"])
    return _finalize_first_batch(pd.concat([stock, etf], ignore_index=True))


def _first_symbol_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "symbol" not in frame:
        return frame
    first_symbol = normalize_symbol_value(frame.iloc[0]["symbol"])
    return frame.loc[frame["symbol"].map(normalize_symbol_value) == first_symbol].copy()


def _finalize_first_batch(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["signal_date", "symbol", "universe_name"])
    frame = frame.copy()
    frame["symbol"] = frame["symbol"].map(normalize_symbol_value)
    return frame.sort_values(["universe_name", "signal_date", "symbol"]).reset_index(drop=True)


def _missing_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    return _finalize(frame.loc[:, MISSING_MATRIX_COLUMNS].copy(), MISSING_MATRIX_COLUMNS)


def _reusable_symbol_level_plan(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (symbol, universe), group in frame.groupby(["symbol", "universe_name"], sort=True):
        rows.append(
            {
                "plan_id": _first_text(group, "plan_id"),
                "symbol": symbol,
                "universe_name": universe,
                "signal_date_count": len(group),
                "identity_listing_metadata_needed": True,
                "survivorship_rationale_required_count": _true_count(group, "survivorship_rationale_required"),
                "metadata_completion_required_count": _true_count(group, "metadata_completion_required"),
                "suggested_scope": "Reusable symbol-level evidence can be copied across dates only after manual reviewer verification.",
                "approval_applied": False,
            }
        )
    return pd.DataFrame(rows)


def _date_specific_plan(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "plan_id",
        "signal_date",
        "symbol",
        "universe_name",
        "strong_official_date_specific_quotation",
        "no_hit_acceptance_required",
        "metadata_completion_required",
        "remaining_blocked",
        "quotation_proves_not_delisted",
        "quotation_proves_st_no_st",
        "quotation_resolves_survivorship",
        "approval_applied",
    ]
    return _finalize(frame.loc[:, columns].copy(), columns)


def _reviewer_completion_template(frame: pd.DataFrame) -> pd.DataFrame:
    template = pd.DataFrame(columns=TEMPLATE_COLUMNS)
    for _, row in frame.iterrows():
        template.loc[len(template)] = {
            "signal_date": row["signal_date"],
            "symbol": row["symbol"],
            "universe_name": row["universe_name"],
            "review_status": "NEEDS_MORE_EVIDENCE",
            "include_flag": False,
            "valid_for_signal_date": False,
            "survivorship_bias_resolved": False,
            "reviewer": "",
            "reviewed_at": "",
            "review_reason": "",
            "evidence_source": "",
            "evidence_path": "",
            "evidence_reference": "",
            "listed_date": "",
            "delisted_date": "",
            "is_active": "",
            "is_st": "",
            "is_suspended": "",
            "listed_date_evidence": "",
            "delisted_date_evidence": "",
            "is_active_evidence": "",
            "as_of_date": "",
            "name": "",
            "instrument_type": "",
            "exchange": "",
            "industry": "",
            "min_lot": "",
            "t_plus_rule": "",
            "available_time": "",
            "revision_id": "",
            "source": "",
            "completion_notes": "Manual evidence completion only; do not set approval in this planning artifact.",
        }
    return template


def _no_hit_todo(frame: pd.DataFrame, downstream_frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if not downstream_frame.empty:
        for row in downstream_frame.to_dict("records"):
            rows.append(
                {
                    "plan_id": _first_text(frame, "plan_id"),
                    "signal_date": _text(row.get("signal_date")),
                    "symbol": normalize_symbol_value(row.get("symbol")),
                    "universe_name": _text(row.get("universe_name")),
                    "exception_type": _text(row.get("exception_type")),
                    "acceptance_status": _text(row.get("acceptance_status")) or "NEEDS_REVIEW",
                    "accepted_no_hit_context": _to_bool(row.get("accepted_no_hit_context")),
                    "reviewer_action": "Review source coverage as supporting context only; do not approve PIT rows here.",
                    "source_lineage": _text(row.get("evidence_reference")),
                    "approval_applied": False,
                }
            )
    else:
        for _, row in frame.iterrows():
            for exception_type in EXCEPTION_TYPES:
                rows.append(
                    {
                        "plan_id": row["plan_id"],
                        "signal_date": row["signal_date"],
                        "symbol": row["symbol"],
                        "universe_name": row["universe_name"],
                        "exception_type": exception_type,
                        "acceptance_status": "NEEDS_REVIEW",
                        "accepted_no_hit_context": False,
                        "reviewer_action": "Review source coverage as supporting context only; do not approve PIT rows here.",
                        "source_lineage": "",
                        "approval_applied": False,
                    }
                )
    return _finalize(pd.DataFrame(rows), TODO_COLUMNS)


def _survivorship_todo(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in frame.to_dict("records"):
        if _to_bool(row.get("survivorship_rationale_required")):
            rows.append(
                {
                    "plan_id": row["plan_id"],
                    "signal_date": row["signal_date"],
                    "symbol": row["symbol"],
                    "universe_name": row["universe_name"],
                    "survivorship_rationale_required": True,
                    "survivorship_bias_resolved": False,
                    "reviewer_action": "Document why the row is not survivorship-derived before any later PIT review.",
                    "approval_applied": False,
                }
            )
    return pd.DataFrame(rows)


def _metadata_completion_todo(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in frame.to_dict("records"):
        if _to_bool(row.get("metadata_completion_required")):
            rows.append(
                {
                    "plan_id": row["plan_id"],
                    "signal_date": row["signal_date"],
                    "symbol": row["symbol"],
                    "universe_name": row["universe_name"],
                    "missing_metadata_fields": row["missing_evidence_fields"],
                    "reviewer_action": "Fill only with reviewed PIT-safe evidence; leave blank if not verified.",
                    "approval_applied": False,
                }
            )
    return pd.DataFrame(rows)


def _source_lineage_summary(result: FirstBatchReviewerEvidenceCompletionPlanResult) -> pd.DataFrame:
    rows = [
        ("source_evidence_update_plan_id", result.source_evidence_update_plan_id, str(result.request.evidence_update_plan)),
        ("downstream_impact_id", result.downstream_impact_id, str(result.request.downstream_impact or "")),
        ("reviewer_no_hit_acceptance_id", result.reviewer_no_hit_acceptance_id, ""),
        ("enrichment_id", result.enrichment_id, str(result.request.enrichment or "")),
        ("source_packet_id", result.source_packet_id, ""),
        ("reviewed_no_hit_policy_comparison_id", result.reviewed_no_hit_policy_comparison_id, str(result.request.policy_comparison or "")),
        ("validator_id", result.validator_id, str(result.request.validator or "")),
    ]
    return pd.DataFrame(
        [{"plan_id": result.plan_id, "lineage_field": key, "lineage_id": value, "source_path": path} for key, value, path in rows]
    )


def _lineage_metadata(request: FirstBatchReviewerEvidenceCompletionPlanRequest) -> dict[str, str]:
    evidence_meta = _load_json_from_artifact(request.evidence_update_plan)
    downstream_meta = _load_json_from_artifact(request.downstream_impact)
    enrichment_meta = _load_json_from_artifact(request.enrichment)
    validator_meta = _load_json_from_artifact(request.validator)
    policy_meta = _load_json_from_artifact(request.policy_comparison)
    return {
        "source_evidence_update_plan_id": _text(evidence_meta.get("plan_id")) or _artifact_name(request.evidence_update_plan),
        "downstream_impact_id": _text(downstream_meta.get("impact_id")) or _artifact_name(request.downstream_impact),
        "reviewer_no_hit_acceptance_id": _text(downstream_meta.get("acceptance_id")),
        "enrichment_id": _text(downstream_meta.get("enrichment_id")) or _text(enrichment_meta.get("enrichment_id")),
        "source_packet_id": _text(downstream_meta.get("source_packet_id")) or _text(enrichment_meta.get("source_packet_id")),
        "reviewed_no_hit_policy_comparison_id": (
            _text(downstream_meta.get("reviewed_no_hit_policy_comparison_id"))
            or _text(enrichment_meta.get("policy_comparison_id"))
            or _text(policy_meta.get("comparison_id"))
        ),
        "validator_id": _text(downstream_meta.get("validator_id")) or _text(validator_meta.get("validator_id")),
        "activation_id": _text(evidence_meta.get("activation_id")),
        "acceptance_id": _text(evidence_meta.get("acceptance_id")),
        "replacement_plan_id": _text(evidence_meta.get("replacement_plan_id")),
        "source_split_plan_id": _text(evidence_meta.get("source_split_plan_id")),
        "source_policy_audit_id": _text(evidence_meta.get("source_policy_audit_id")),
        "source_worklist_id": _text(evidence_meta.get("source_worklist_id")),
    }


def _read_optional_artifact_csv(path: Path | None, filename: str) -> pd.DataFrame:
    if path is None:
        return pd.DataFrame()
    actual = path if path.is_file() else path / filename
    if not actual.exists():
        return pd.DataFrame()
    return _read_csv(actual)


def _read_csv(path: Path) -> pd.DataFrame:
    return read_csv_preserve_symbol_columns(path, keep_default_na=False)


def _load_json_from_artifact(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    metadata_path = path / "metadata.json" if path.is_dir() else path.with_name("metadata.json")
    if not metadata_path.exists():
        return {}
    try:
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _accepted_context_by_key(frame: pd.DataFrame) -> dict[tuple[str, str, str], dict[str, Any]]:
    accepted: dict[tuple[str, str, str], dict[str, Any]] = {}
    if frame.empty:
        return accepted
    for row in frame.to_dict("records"):
        if not _to_bool(row.get("accepted_no_hit_context")):
            continue
        key = _row_key(row)
        bucket = accepted.setdefault(key, {"count": 0, "types": []})
        exception_type = _text(row.get("exception_type"))
        if exception_type and exception_type not in bucket["types"]:
            bucket["types"].append(exception_type)
            bucket["count"] += 1
    return accepted


def _missing_fields(row: dict[str, Any], validator_row: dict[str, Any]) -> list[str]:
    raw = _text(validator_row.get("missing_required_fields"))
    parts = [item.strip() for item in raw.replace(";", ",").split(",") if item.strip()]
    if not parts:
        parts = [field for field in REQUIRED_METADATA_FIELDS if not _text(row.get(field))]
    return sorted(dict.fromkeys(parts))


def _row_key(row: dict[str, Any]) -> tuple[str, str, str]:
    universe = _text(row.get("universe_name")) or _text(row.get("recommended_future_universe"))
    return (_text(row.get("signal_date")), normalize_symbol_value(row.get("symbol")), universe)


def _counts(frame: pd.DataFrame) -> dict[str, int]:
    return {
        "reviewer_completion_required_count": _true_count(frame, "reviewer_completion_required"),
        "no_hit_acceptance_required_count": _true_count(frame, "no_hit_acceptance_required"),
        "survivorship_rationale_required_count": _true_count(frame, "survivorship_rationale_required"),
        "metadata_completion_required_count": _true_count(frame, "metadata_completion_required"),
        "checklist_pass_count": _true_count(frame, "checklist_pass"),
        "remaining_blocked_count": _true_count(frame, "remaining_blocked"),
    }


def _plan_id(
    request: FirstBatchReviewerEvidenceCompletionPlanRequest,
    first_batch: pd.DataFrame,
    settings: FirstBatchReviewerEvidenceCompletionPlanSettings,
) -> str:
    payload = {
        "config_version": settings.config_version,
        "evidence_update_plan": str(request.evidence_update_plan),
        "downstream_impact": str(request.downstream_impact or ""),
        "enrichment": str(request.enrichment or ""),
        "validator": str(request.validator or ""),
        "policy_comparison": str(request.policy_comparison or ""),
        "rows": first_batch[[column for column in ["signal_date", "symbol", "universe_name"] if column in first_batch]].to_dict("records"),
    }
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _replace_output_dir(
    settings: FirstBatchReviewerEvidenceCompletionPlanSettings,
    output_dir: Path,
) -> FirstBatchReviewerEvidenceCompletionPlanSettings:
    return FirstBatchReviewerEvidenceCompletionPlanSettings(
        output_dir=output_dir,
        config_version=settings.config_version,
        write_artifacts=settings.write_artifacts,
        enable_approval=settings.enable_approval,
        enable_clean_review_updates=settings.enable_clean_review_updates,
        enable_pit_review=settings.enable_pit_review,
        enable_export_readiness=settings.enable_export_readiness,
        enable_export_staging=settings.enable_export_staging,
        enable_universe_export=settings.enable_universe_export,
        enable_data_raw_write=settings.enable_data_raw_write,
        enable_data_processed_write=settings.enable_data_processed_write,
        enable_current_candidates=settings.enable_current_candidates,
        enable_snapshot_build=settings.enable_snapshot_build,
        enable_forward_labels=settings.enable_forward_labels,
        enable_cache_mutation=settings.enable_cache_mutation,
        enable_live_trading=settings.enable_live_trading,
        enable_broker_api=settings.enable_broker_api,
        enable_order_placement=settings.enable_order_placement,
        enable_message_delivery=settings.enable_message_delivery,
    )


def _audit_metadata(settings: FirstBatchReviewerEvidenceCompletionPlanSettings) -> dict[str, Any]:
    return {
        "config_version": settings.config_version,
        "approval_applied": False,
        "clean_review_updates_created": False,
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
    }


def _assert_settings_safe(settings: FirstBatchReviewerEvidenceCompletionPlanSettings) -> None:
    unsafe = {
        "enable_approval": settings.enable_approval,
        "enable_clean_review_updates": settings.enable_clean_review_updates,
        "enable_pit_review": settings.enable_pit_review,
        "enable_export_readiness": settings.enable_export_readiness,
        "enable_export_staging": settings.enable_export_staging,
        "enable_universe_export": settings.enable_universe_export,
        "enable_data_raw_write": settings.enable_data_raw_write,
        "enable_data_processed_write": settings.enable_data_processed_write,
        "enable_current_candidates": settings.enable_current_candidates,
        "enable_snapshot_build": settings.enable_snapshot_build,
        "enable_forward_labels": settings.enable_forward_labels,
        "enable_cache_mutation": settings.enable_cache_mutation,
        "enable_live_trading": settings.enable_live_trading,
        "enable_broker_api": settings.enable_broker_api,
        "enable_order_placement": settings.enable_order_placement,
        "enable_message_delivery": settings.enable_message_delivery,
    }
    enabled = [name for name, value in unsafe.items() if value]
    if enabled:
        raise ValueError("First-batch reviewer evidence completion plan is report-only; unsafe settings enabled: " + ", ".join(enabled))


def _finalize(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=columns)
    for column in columns:
        if column not in frame:
            frame[column] = ""
    return frame.loc[:, columns]


def _artifact_name(path: Path | None) -> str:
    return path.name if path is not None else ""


def _first_text(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame:
        return ""
    values = [_text(value) for value in frame[column].tolist() if _text(value)]
    return values[0] if values else ""


def _equals_count(frame: pd.DataFrame, column: str, value: str) -> int:
    if frame.empty or column not in frame:
        return 0
    return int((frame[column].astype(str) == value).sum())


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame:
        return 0
    return int(frame[column].map(_to_bool).sum())


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value
