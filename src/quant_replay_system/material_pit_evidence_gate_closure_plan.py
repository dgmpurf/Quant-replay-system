"""Report-only material PIT evidence gate closure planning.

This workflow turns first-batch blocker diagnostics into fill templates grouped
by closure path. It does not approve rows, create clean review updates, run PIT
review/export workflows, write universe inputs, run current-candidates, build
snapshots, compute labels, or mutate cache.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns


MATERIAL_FIELDS = [
    "as_of_date",
    "industry",
    "is_active",
    "is_active_evidence",
    "revision_id",
    "t_plus_rule",
    "is_st",
]

CLOSURE_PATHS = [
    "REUSABLE_SYMBOL_LEVEL",
    "DATE_SPECIFIC",
    "REVIEWER_NO_HIT_ACCEPTANCE",
    "SURVIVORSHIP_RATIONALE",
    "PIT_METADATA",
    "STOCK_ONLY_ST_NO_ST",
    "STILL_BLOCKED",
]

PLAN_COLUMNS = [
    "plan_id",
    "first_batch_partial_completion_impact_id",
    "first_batch_reviewer_evidence_completion_plan_id",
    "validator_id",
    "policy_comparison_id",
    "reviewed_no_hit_policy_comparison_id",
    "enrichment_id",
    "reviewer_no_hit_acceptance_id",
    "reviewer_no_hit_downstream_impact_id",
    "signal_date",
    "symbol",
    "universe_name",
    "resolved_instrument_type",
    "missing_material_fields",
    "missing_evidence_categories",
    "closure_paths_required",
    "reusable_symbol_level_closure_required",
    "date_specific_closure_required",
    "reviewer_no_hit_acceptance_required",
    "survivorship_rationale_required",
    "metadata_closure_required",
    "stock_st_no_st_required",
    "checklist_pass_candidate",
    "remaining_blocked",
    "include_flag",
    "valid_for_signal_date",
    "approval_applied",
    "clean_review_updates_created",
    "pit_review_run",
    "export_readiness_run",
    "export_staging_run",
    "universe_exported",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "no_snapshot_built",
    "no_forward_labels",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "planning_only",
]

SAFETY_STATEMENT = (
    "No approval, rejection, clean review updates, PIT review, export-readiness, "
    "staging, universe export, data/raw write, data/processed write, active worklist "
    "mutation, current-candidates generation, snapshot build, forward labels, live "
    "trading, broker API, orders, messages, paid/private APIs, or cache mutation was invoked."
)


@dataclass(frozen=True)
class MaterialPitEvidenceGateClosurePlanSettings:
    output_dir: Path = Path("outputs/reports/material_pit_evidence_gate_closure_plan")
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
class MaterialPitEvidenceGateClosurePlanRequest:
    audit: Path | None
    partial_impact: Path
    completion_plan: Path
    validator: Path | None
    policy_comparison: Path | None
    enrichment: Path | None
    reviewer_no_hit_acceptance: Path | None
    reviewer_no_hit_downstream_impact: Path | None


@dataclass(frozen=True)
class MaterialPitEvidenceGateClosurePlanResult:
    plan_id: str
    status: str
    request: MaterialPitEvidenceGateClosurePlanRequest
    row_count: int
    checklist_pass_candidate_count: int
    remaining_blocked_count: int
    reusable_symbol_level_closure_count: int
    date_specific_closure_required_count: int
    reviewer_no_hit_acceptance_required_count: int
    survivorship_rationale_required_count: int
    metadata_closure_required_count: int
    stock_st_no_st_required_count: int
    clean_review_updates_created: bool
    approval_applied: bool
    plan_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    lineage: dict[str, str]
    warnings: list[str]


def build_material_pit_evidence_gate_closure_plan(
    *,
    audit: str | Path | None = "outputs/reports/manual_diagnostics/material_pit_evidence_gate_closure_planning_audit_v0_1",
    partial_impact: str | Path = "outputs/reports/first_batch_partial_completion_impact/ea81f81ae764",
    completion_plan: str | Path = "outputs/reports/first_batch_reviewer_evidence_completion_plan/c630522f235a",
    validator: str | Path | None = "outputs/reports/pit_evidence_checklist_validator/62e9eb747197",
    policy_comparison: str | Path | None = "outputs/reports/pit_evidence_policy_profile_comparison/c1a75d1091c6",
    enrichment: str | Path | None = "outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c",
    reviewer_no_hit_acceptance: str | Path | None = (
        "outputs/reports/reviewer_no_hit_source_coverage_acceptance/2e05e4b74794"
    ),
    reviewer_no_hit_downstream_impact: str | Path | None = (
        "outputs/reports/reviewer_no_hit_acceptance_downstream_impact/9e164963455e"
    ),
    output_dir: str | Path | None = None,
    settings: MaterialPitEvidenceGateClosurePlanSettings | None = None,
) -> MaterialPitEvidenceGateClosurePlanResult:
    resolved_settings = settings or MaterialPitEvidenceGateClosurePlanSettings()
    if output_dir is not None:
        resolved_settings = MaterialPitEvidenceGateClosurePlanSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)
    request = MaterialPitEvidenceGateClosurePlanRequest(
        audit=Path(audit) if audit else None,
        partial_impact=Path(partial_impact),
        completion_plan=Path(completion_plan),
        validator=Path(validator) if validator else None,
        policy_comparison=Path(policy_comparison) if policy_comparison else None,
        enrichment=Path(enrichment) if enrichment else None,
        reviewer_no_hit_acceptance=Path(reviewer_no_hit_acceptance) if reviewer_no_hit_acceptance else None,
        reviewer_no_hit_downstream_impact=Path(reviewer_no_hit_downstream_impact)
        if reviewer_no_hit_downstream_impact
        else None,
    )
    frames, metadata = load_material_pit_evidence_gate_closure_inputs(request)
    lineage = _lineage(metadata, frames)
    plan_id = _plan_id(request, frames["completion_plan"], frames["partial_impact"])
    plan_frame = build_material_pit_evidence_gate_closure_frame(plan_id, frames, lineage)
    counts = _counts(plan_frame)
    paths = resolve_material_pit_evidence_gate_closure_plan_paths(resolved_settings.output_dir, plan_id)
    result = MaterialPitEvidenceGateClosurePlanResult(
        plan_id=plan_id,
        status="WARN" if counts["remaining_blocked_count"] else "PASS",
        request=request,
        row_count=len(plan_frame),
        checklist_pass_candidate_count=counts["checklist_pass_candidate_count"],
        remaining_blocked_count=counts["remaining_blocked_count"],
        reusable_symbol_level_closure_count=counts["reusable_symbol_level_closure_count"],
        date_specific_closure_required_count=counts["date_specific_closure_required_count"],
        reviewer_no_hit_acceptance_required_count=counts["reviewer_no_hit_acceptance_required_count"],
        survivorship_rationale_required_count=counts["survivorship_rationale_required_count"],
        metadata_closure_required_count=counts["metadata_closure_required_count"],
        stock_st_no_st_required_count=counts["stock_st_no_st_required_count"],
        clean_review_updates_created=False,
        approval_applied=False,
        plan_frame=plan_frame,
        artifact_paths=paths,
        lineage=lineage,
        warnings=[],
    )
    if resolved_settings.write_artifacts:
        write_material_pit_evidence_gate_closure_plan_artifacts(result, frames)
    return result


def load_material_pit_evidence_gate_closure_inputs(
    request: MaterialPitEvidenceGateClosurePlanRequest,
) -> tuple[dict[str, pd.DataFrame], dict[str, dict[str, Any]]]:
    frames = {
        "completion_plan": _read_artifact_csv(
            request.completion_plan,
            "first_batch_reviewer_evidence_completion_plan.csv",
            required=True,
        ),
        "partial_impact": _read_artifact_csv(
            request.partial_impact,
            "first_batch_partial_completion_impact.csv",
            required=True,
        ),
        "validator": _read_artifact_csv(
            request.validator,
            "pit_evidence_checklist_validation.csv",
            required=False,
        ),
        "policy_comparison": _read_artifact_csv(
            request.policy_comparison,
            "pit_evidence_policy_profile_comparison.csv",
            required=False,
        ),
        "enrichment": _read_artifact_csv(
            request.enrichment,
            "pit_official_status_evidence_packet_enrichment.csv",
            required=False,
        ),
        "reviewer_no_hit_acceptance": _read_artifact_csv(
            request.reviewer_no_hit_acceptance,
            "reviewer_no_hit_source_coverage_acceptance.csv",
            required=False,
        ),
        "reviewer_no_hit_downstream_impact": _read_artifact_csv(
            request.reviewer_no_hit_downstream_impact,
            "reviewer_no_hit_acceptance_downstream_impact.csv",
            required=False,
        ),
    }
    if request.audit:
        frames["audit_blocker_matrix"] = _read_artifact_csv(
            request.audit,
            "row_level_material_blocker_matrix.csv",
            required=False,
        )
    metadata = {
        "completion_plan": _read_metadata(request.completion_plan),
        "partial_impact": _read_metadata(request.partial_impact),
        "validator": _read_metadata(request.validator),
        "policy_comparison": _read_metadata(request.policy_comparison),
        "enrichment": _read_metadata(request.enrichment),
        "reviewer_no_hit_acceptance": _read_metadata(request.reviewer_no_hit_acceptance),
        "reviewer_no_hit_downstream_impact": _read_metadata(request.reviewer_no_hit_downstream_impact),
    }
    for key, frame in frames.items():
        frames[key] = _normalize_identity(frame)
    return frames, metadata


def build_material_pit_evidence_gate_closure_frame(
    plan_id: str,
    frames: dict[str, pd.DataFrame],
    lineage: dict[str, str],
) -> pd.DataFrame:
    completion = frames["completion_plan"]
    rows: list[dict[str, Any]] = []
    for row in completion.to_dict("records"):
        symbol = normalize_symbol_value(row.get("symbol"))
        universe_name = _string(row.get("universe_name"))
        instrument_type = _string(row.get("resolved_instrument_type"))
        missing_fields = _split_values(_string(row.get("missing_evidence_fields")))
        missing_categories = _split_values(_string(row.get("missing_evidence_categories")))
        reusable_required = any(field in missing_fields for field in ["industry", "t_plus_rule"])
        date_required = any(field in missing_fields for field in ["as_of_date", "is_active", "is_active_evidence"])
        no_hit_required = "reviewer_no_hit_acceptance" in missing_categories or _bool(
            row.get("no_hit_acceptance_required")
        )
        survivorship_required = (
            "survivorship_bias_resolution" in missing_categories
            or _bool(row.get("survivorship_rationale_required"))
            or not _bool(row.get("survivorship_bias_resolved"))
        )
        metadata_required = bool(missing_fields)
        stock_st_required = symbol == "000001" and (
            "is_st" in missing_fields or "stock_st_no_st_evidence" in missing_categories
        )
        closure_paths = _closure_paths(
            reusable_required=reusable_required,
            date_required=date_required,
            no_hit_required=no_hit_required,
            survivorship_required=survivorship_required,
            metadata_required=metadata_required,
            stock_st_required=stock_st_required,
        )
        rows.append(
            {
                "plan_id": plan_id,
                **lineage,
                "signal_date": _string(row.get("signal_date")),
                "symbol": symbol,
                "universe_name": universe_name,
                "resolved_instrument_type": instrument_type,
                "missing_material_fields": ";".join(missing_fields),
                "missing_evidence_categories": ";".join(missing_categories),
                "closure_paths_required": ";".join(closure_paths),
                "reusable_symbol_level_closure_required": reusable_required,
                "date_specific_closure_required": date_required,
                "reviewer_no_hit_acceptance_required": no_hit_required,
                "survivorship_rationale_required": survivorship_required,
                "metadata_closure_required": metadata_required,
                "stock_st_no_st_required": stock_st_required,
                "checklist_pass_candidate": False,
                "remaining_blocked": True,
                "include_flag": False,
                "valid_for_signal_date": False,
                "approval_applied": False,
                "clean_review_updates_created": False,
                "pit_review_run": False,
                "export_readiness_run": False,
                "export_staging_run": False,
                "universe_exported": False,
                "no_data_raw_write": True,
                "no_data_processed_write": True,
                "no_current_candidates_generated": True,
                "no_snapshot_built": True,
                "no_forward_labels": True,
                "no_live_trading": True,
                "no_broker_api": True,
                "no_order_placement": True,
                "no_message_sent": True,
                "planning_only": True,
            }
        )
    return pd.DataFrame(rows, columns=PLAN_COLUMNS)


def resolve_material_pit_evidence_gate_closure_plan_paths(output_dir: str | Path, plan_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / plan_id
    return {
        "artifact_dir": artifact_dir,
        "plan_csv": artifact_dir / "material_pit_evidence_gate_closure_plan.csv",
        "row_level_material_blocker_matrix": artifact_dir / "row_level_material_blocker_matrix.csv",
        "reusable_symbol_level_closure_plan": artifact_dir / "reusable_symbol_level_closure_plan.csv",
        "date_specific_closure_plan": artifact_dir / "date_specific_closure_plan.csv",
        "reviewer_no_hit_acceptance_closure_plan": artifact_dir / "reviewer_no_hit_acceptance_closure_plan.csv",
        "survivorship_rationale_closure_plan": artifact_dir / "survivorship_rationale_closure_plan.csv",
        "metadata_closure_plan": artifact_dir / "metadata_closure_plan.csv",
        "checklist_pass_candidate_requirements": artifact_dir / "checklist_pass_candidate_requirements.csv",
        "reviewer_fill_template_by_closure_path": artifact_dir / "reviewer_fill_template_by_closure_path.csv",
        "source_lineage_summary": artifact_dir / "source_lineage_summary.csv",
        "report": artifact_dir / "report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def write_material_pit_evidence_gate_closure_plan_artifacts(
    result: MaterialPitEvidenceGateClosurePlanResult,
    frames: dict[str, pd.DataFrame],
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.plan_frame.to_csv(paths["plan_csv"], index=False)
    _row_level_material_blocker_matrix(result.plan_frame, frames).to_csv(
        paths["row_level_material_blocker_matrix"], index=False
    )
    _reusable_symbol_level_closure_plan(result.plan_frame).to_csv(
        paths["reusable_symbol_level_closure_plan"], index=False
    )
    _date_specific_closure_plan(result.plan_frame, frames).to_csv(paths["date_specific_closure_plan"], index=False)
    _reviewer_no_hit_acceptance_closure_plan(result.plan_frame, frames).to_csv(
        paths["reviewer_no_hit_acceptance_closure_plan"], index=False
    )
    _survivorship_rationale_closure_plan(result.plan_frame).to_csv(
        paths["survivorship_rationale_closure_plan"], index=False
    )
    _metadata_closure_plan(result.plan_frame).to_csv(paths["metadata_closure_plan"], index=False)
    _checklist_pass_candidate_requirements(result.plan_frame).to_csv(
        paths["checklist_pass_candidate_requirements"], index=False
    )
    _reviewer_fill_template_by_closure_path(result.plan_frame).to_csv(
        paths["reviewer_fill_template_by_closure_path"], index=False
    )
    _source_lineage_summary(result).to_csv(paths["source_lineage_summary"], index=False)
    paths["report"].write_text(render_material_pit_evidence_gate_closure_plan_report(result), encoding="utf-8")
    paths["metadata"].write_text(
        json.dumps(_json_safe(build_material_pit_evidence_gate_closure_plan_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths


def render_material_pit_evidence_gate_closure_plan_report(
    result: MaterialPitEvidenceGateClosurePlanResult,
) -> str:
    return "\n".join(
        [
            f"# Material PIT Evidence Gate Closure Plan: {result.plan_id}",
            "",
            SAFETY_STATEMENT,
            "",
            "This is a closure planning artifact only. It does not create clean review updates or apply PIT approval.",
            "",
            "## Summary",
            "",
            f"- row_count: {result.row_count}",
            f"- checklist_pass_candidate_count: {result.checklist_pass_candidate_count}",
            f"- remaining_blocked_count: {result.remaining_blocked_count}",
            f"- reusable_symbol_level_closure_count: {result.reusable_symbol_level_closure_count}",
            f"- date_specific_closure_required_count: {result.date_specific_closure_required_count}",
            f"- reviewer_no_hit_acceptance_required_count: {result.reviewer_no_hit_acceptance_required_count}",
            f"- survivorship_rationale_required_count: {result.survivorship_rationale_required_count}",
            f"- metadata_closure_required_count: {result.metadata_closure_required_count}",
            f"- stock_st_no_st_required_count: {result.stock_st_no_st_required_count}",
            f"- clean_review_updates_created: {result.clean_review_updates_created}",
            f"- approval_applied: {result.approval_applied}",
            "",
            "## Interpretation",
            "",
            "All current rows remain blocked. Reusable symbol-level evidence can reduce repeated review work, but every row still needs date-specific PIT status context, reviewer no-hit acceptance, survivorship rationale, and metadata completion before any later checklist-pass candidate preview.",
            "",
        ]
    )


def build_material_pit_evidence_gate_closure_plan_metadata(
    result: MaterialPitEvidenceGateClosurePlanResult,
) -> dict[str, Any]:
    return {
        "plan_id": result.plan_id,
        "status": result.status,
        **result.lineage,
        "row_count": result.row_count,
        "checklist_pass_candidate_count": result.checklist_pass_candidate_count,
        "remaining_blocked_count": result.remaining_blocked_count,
        "reusable_symbol_level_closure_count": result.reusable_symbol_level_closure_count,
        "date_specific_closure_required_count": result.date_specific_closure_required_count,
        "reviewer_no_hit_acceptance_required_count": result.reviewer_no_hit_acceptance_required_count,
        "survivorship_rationale_required_count": result.survivorship_rationale_required_count,
        "metadata_closure_required_count": result.metadata_closure_required_count,
        "stock_st_no_st_required_count": result.stock_st_no_st_required_count,
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
        "cache_mutated": False,
        "planning_only": True,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
        "safety_statement": SAFETY_STATEMENT,
        "known_limitations": [
            "This workflow creates fill templates only and does not create clean review updates.",
            "No row is a checklist-pass candidate under the current active evidence state.",
            "Reviewer no-hit acceptance remains supporting context only until later explicit workflows use it.",
        ],
    }


def _row_level_material_blocker_matrix(plan: pd.DataFrame, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    validator = _by_identity(frames.get("validator", pd.DataFrame()))
    rows: list[dict[str, Any]] = []
    for row in plan.to_dict("records"):
        linked = validator.get(_identity_key(row), {})
        missing_fields = _split_values(_string(row.get("missing_material_fields")))
        rows.append(
            {
                "plan_id": row.get("plan_id", ""),
                "signal_date": row.get("signal_date", ""),
                "symbol": row.get("symbol", ""),
                "universe_name": row.get("universe_name", ""),
                "resolved_instrument_type": row.get("resolved_instrument_type", ""),
                "missing_material_fields": row.get("missing_material_fields", ""),
                "missing_evidence_categories": row.get("missing_evidence_categories", ""),
                "closure_paths_required": row.get("closure_paths_required", ""),
                "missing_as_of_date": "as_of_date" in missing_fields,
                "missing_industry": "industry" in missing_fields,
                "missing_is_active": "is_active" in missing_fields,
                "missing_is_active_evidence": "is_active_evidence" in missing_fields,
                "missing_revision_id": "revision_id" in missing_fields,
                "missing_t_plus_rule": "t_plus_rule" in missing_fields,
                "missing_is_st": "is_st" in missing_fields,
                "validator_blocker_reason": _string(linked.get("blocker_reason")),
                "checklist_pass_candidate": False,
                "remaining_blocked": True,
                "approval_applied": False,
            }
        )
    return pd.DataFrame(rows)


def _reusable_symbol_level_closure_plan(plan: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (symbol, universe_name), group in plan.groupby(["symbol", "universe_name"], sort=True):
        required = group["reusable_symbol_level_closure_required"].map(_bool).any()
        fields = set()
        for value in group["missing_material_fields"].tolist():
            for field in _split_values(value):
                if field in {"industry", "t_plus_rule"}:
                    fields.add(field)
        fields.update({"symbol_identity", "listed_date", "exchange", "instrument_type"})
        rows.append(
            {
                "plan_id": group.iloc[0]["plan_id"],
                "symbol": symbol,
                "universe_name": universe_name,
                "resolved_instrument_type": group.iloc[0]["resolved_instrument_type"],
                "signal_date_count": len(group),
                "closure_path": "REUSABLE_SYMBOL_LEVEL",
                "closure_required": required,
                "fields_or_prerequisites": ";".join(sorted(fields)),
                "reviewer_action": "Attach reviewed symbol-level source references and explain why they can be reused across all first-batch dates.",
                "can_close_row_by_itself": False,
                "approval_applied": False,
            }
        )
    return pd.DataFrame(rows)


def _date_specific_closure_plan(plan: pd.DataFrame, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    enrichment = _by_identity(frames.get("enrichment", pd.DataFrame()))
    rows: list[dict[str, Any]] = []
    for row in plan.to_dict("records"):
        linked = enrichment.get(_identity_key(row), {})
        fields = [
            field
            for field in _split_values(_string(row.get("missing_material_fields")))
            if field in {"as_of_date", "is_active", "is_active_evidence", "is_st"}
        ]
        rows.append(
            {
                "plan_id": row.get("plan_id", ""),
                "signal_date": row.get("signal_date", ""),
                "symbol": row.get("symbol", ""),
                "universe_name": row.get("universe_name", ""),
                "closure_path": "DATE_SPECIFIC",
                "closure_required": _bool(row.get("date_specific_closure_required")),
                "date_specific_fields_needed": ";".join(fields),
                "strong_official_date_specific_quotation": _string(
                    linked.get("strong_official_date_specific_quotation")
                ),
                "quotation_source_url": _string(linked.get("quotation_source_url")),
                "reviewer_action": "Attach date-specific PIT evidence and decision-time/available-time reasoning.",
                "can_close_row_by_itself": False,
                "approval_applied": False,
            }
        )
    return pd.DataFrame(rows)


def _reviewer_no_hit_acceptance_closure_plan(plan: pd.DataFrame, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    acceptance = frames.get("reviewer_no_hit_acceptance", pd.DataFrame())
    if not acceptance.empty:
        result = acceptance[
            [
                "signal_date",
                "symbol",
                "universe_name",
                "exception_type",
                "acceptance_status",
                "source_name",
                "source_url_or_endpoint",
                "query_window",
                "source_coverage_accepted",
                "query_window_accepted",
                "no_hit_inference_accepted",
                "accepted_as_supporting_context",
            ]
        ].copy()
        result["plan_id"] = plan["plan_id"].iloc[0] if not plan.empty else ""
        result["closure_path"] = "REVIEWER_NO_HIT_ACCEPTANCE"
        result["reviewer_action"] = (
            "Accept source coverage, query window, no-hit inference, evidence reference, and limitations. "
            "Accepted no-hit rows remain supporting context only."
        )
        result["can_approve_row"] = False
        result["approval_applied"] = False
        columns = ["plan_id", "closure_path"] + [col for col in result.columns if col not in {"plan_id", "closure_path"}]
        return result.loc[:, columns]
    rows: list[dict[str, Any]] = []
    for row in plan.to_dict("records"):
        for exception_type in ["DELISTING", "ST_RISK_WARNING", "SUSPENSION_RESUMPTION", "SURVIVORSHIP_RATIONALE"]:
            rows.append(
                {
                    "plan_id": row.get("plan_id", ""),
                    "closure_path": "REVIEWER_NO_HIT_ACCEPTANCE",
                    "signal_date": row.get("signal_date", ""),
                    "symbol": row.get("symbol", ""),
                    "universe_name": row.get("universe_name", ""),
                    "exception_type": exception_type,
                    "acceptance_status": "NEEDS_REVIEW",
                    "reviewer_action": "Complete reviewer no-hit acceptance before checklist-pass preview.",
                    "can_approve_row": False,
                    "approval_applied": False,
                }
            )
    return pd.DataFrame(rows)


def _survivorship_rationale_closure_plan(plan: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "plan_id": row.get("plan_id", ""),
                "signal_date": row.get("signal_date", ""),
                "symbol": row.get("symbol", ""),
                "universe_name": row.get("universe_name", ""),
                "closure_path": "SURVIVORSHIP_RATIONALE",
                "closure_required": row.get("survivorship_rationale_required", False),
                "reviewer_action": "Write explicit rationale tying identity, date-specific quotation/status context, accepted no-hit context, and future-universe bias limits to this symbol/date.",
                "survivorship_bias_resolved_candidate": False,
                "can_close_row_by_itself": False,
                "approval_applied": False,
            }
            for row in plan.to_dict("records")
        ]
    )


def _metadata_closure_plan(plan: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "plan_id": row.get("plan_id", ""),
                "signal_date": row.get("signal_date", ""),
                "symbol": row.get("symbol", ""),
                "universe_name": row.get("universe_name", ""),
                "closure_path": "PIT_METADATA",
                "closure_required": row.get("metadata_closure_required", False),
                "metadata_fields_needed": row.get("missing_material_fields", ""),
                "reviewer_action": "Fill reviewed PIT metadata only from accepted evidence and source lineage.",
                "can_close_row_by_itself": False,
                "approval_applied": False,
            }
            for row in plan.to_dict("records")
        ]
    )


def _checklist_pass_candidate_requirements(plan: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in plan.to_dict("records"):
        reqs = [
            "reviewer metadata completed",
            "date-specific PIT active/status evidence accepted",
            "PIT metadata completed",
            "reviewer no-hit acceptance completed",
            "survivorship rationale accepted",
        ]
        if _bool(row.get("stock_st_no_st_required")):
            reqs.append("stock ST/no-ST evidence accepted")
        rows.append(
            {
                "plan_id": row.get("plan_id", ""),
                "signal_date": row.get("signal_date", ""),
                "symbol": row.get("symbol", ""),
                "universe_name": row.get("universe_name", ""),
                "requirements_before_checklist_pass_candidate_preview": ";".join(reqs),
                "checklist_pass_candidate_now": False,
                "approval_allowed_now": False,
                "clean_review_updates_allowed_now": False,
            }
        )
    return pd.DataFrame(rows)


def _reviewer_fill_template_by_closure_path(plan: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in plan.to_dict("records"):
        for path in _split_values(_string(row.get("closure_paths_required"))):
            if path == "STILL_BLOCKED":
                continue
            rows.append(
                {
                    "plan_id": row.get("plan_id", ""),
                    "signal_date": row.get("signal_date", ""),
                    "symbol": row.get("symbol", ""),
                    "universe_name": row.get("universe_name", ""),
                    "closure_path": path,
                    "review_status": "NEEDS_MORE_EVIDENCE",
                    "reviewer": "",
                    "reviewed_at": "",
                    "review_reason": "",
                    "evidence_source": "",
                    "evidence_reference": "",
                    "evidence_path": "",
                    "source_limitations": "",
                    "reviewer_notes": "",
                    "include_flag": False,
                    "valid_for_signal_date": False,
                    "approval_applied": False,
                    "planning_only": True,
                }
            )
    return pd.DataFrame(rows)


def _source_lineage_summary(result: MaterialPitEvidenceGateClosurePlanResult) -> pd.DataFrame:
    rows = []
    for key, value in result.lineage.items():
        rows.append(
            {
                "plan_id": result.plan_id,
                "lineage_field": key,
                "lineage_id": value,
                "source_role": _source_role(key),
                "approval_applied": False,
                "planning_only": True,
            }
        )
    return pd.DataFrame(rows)


def _counts(frame: pd.DataFrame) -> dict[str, int]:
    return {
        "checklist_pass_candidate_count": int(frame["checklist_pass_candidate"].map(_bool).sum()),
        "remaining_blocked_count": int(frame["remaining_blocked"].map(_bool).sum()),
        "reusable_symbol_level_closure_count": int(
            frame.loc[frame["reusable_symbol_level_closure_required"].map(_bool), ["symbol", "universe_name"]]
            .drop_duplicates()
            .shape[0]
        ),
        "date_specific_closure_required_count": int(frame["date_specific_closure_required"].map(_bool).sum()),
        "reviewer_no_hit_acceptance_required_count": int(
            frame["reviewer_no_hit_acceptance_required"].map(_bool).sum()
        ),
        "survivorship_rationale_required_count": int(frame["survivorship_rationale_required"].map(_bool).sum()),
        "metadata_closure_required_count": int(frame["metadata_closure_required"].map(_bool).sum()),
        "stock_st_no_st_required_count": int(frame["stock_st_no_st_required"].map(_bool).sum()),
    }


def _lineage(metadata: dict[str, dict[str, Any]], frames: dict[str, pd.DataFrame]) -> dict[str, str]:
    completion = frames.get("completion_plan", pd.DataFrame())
    return {
        "first_batch_partial_completion_impact_id": _metadata_or_frame_id(
            metadata.get("partial_impact", {}), frames.get("partial_impact", pd.DataFrame()), "impact_id"
        ),
        "first_batch_reviewer_evidence_completion_plan_id": _metadata_or_frame_id(
            metadata.get("completion_plan", {}), completion, "plan_id"
        ),
        "validator_id": _metadata_or_frame_id(metadata.get("validator", {}), frames.get("validator", pd.DataFrame()), "validator_id"),
        "policy_comparison_id": _metadata_or_frame_id(
            metadata.get("policy_comparison", {}), frames.get("policy_comparison", pd.DataFrame()), "comparison_id"
        ),
        "reviewed_no_hit_policy_comparison_id": _first_non_empty(
            completion, "reviewed_no_hit_policy_comparison_id"
        ),
        "enrichment_id": _metadata_or_frame_id(
            metadata.get("enrichment", {}), frames.get("enrichment", pd.DataFrame()), "enrichment_id"
        ),
        "reviewer_no_hit_acceptance_id": _metadata_or_frame_id(
            metadata.get("reviewer_no_hit_acceptance", {}),
            frames.get("reviewer_no_hit_acceptance", pd.DataFrame()),
            "acceptance_id",
        ),
        "reviewer_no_hit_downstream_impact_id": _metadata_or_frame_id(
            metadata.get("reviewer_no_hit_downstream_impact", {}),
            frames.get("reviewer_no_hit_downstream_impact", pd.DataFrame()),
            "impact_id",
        ),
    }


def _read_artifact_csv(path: Path | None, filename: str, *, required: bool) -> pd.DataFrame:
    if path is None:
        if required:
            raise FileNotFoundError(filename)
        return pd.DataFrame()
    candidate = path if path.is_file() else path / filename
    if not candidate.exists():
        if required:
            raise FileNotFoundError(f"Required artifact CSV not found: {candidate}")
        return pd.DataFrame()
    return read_csv_preserve_symbol_columns(candidate, keep_default_na=False)


def _read_metadata(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    metadata_path = path.parent / "metadata.json" if path.is_file() else path / "metadata.json"
    if not metadata_path.exists():
        return {}
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def _normalize_identity(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if result.empty:
        return result
    for column in ["signal_date", "symbol", "universe_name"]:
        if column not in result.columns:
            result[column] = ""
    result["symbol"] = result["symbol"].map(normalize_symbol_value)
    result["signal_date"] = result["signal_date"].astype(str)
    result["universe_name"] = result["universe_name"].astype(str)
    return result


def _closure_paths(
    *,
    reusable_required: bool,
    date_required: bool,
    no_hit_required: bool,
    survivorship_required: bool,
    metadata_required: bool,
    stock_st_required: bool,
) -> list[str]:
    paths: list[str] = []
    if reusable_required:
        paths.append("REUSABLE_SYMBOL_LEVEL")
    if date_required:
        paths.append("DATE_SPECIFIC")
    if no_hit_required:
        paths.append("REVIEWER_NO_HIT_ACCEPTANCE")
    if survivorship_required:
        paths.append("SURVIVORSHIP_RATIONALE")
    if metadata_required:
        paths.append("PIT_METADATA")
    if stock_st_required:
        paths.append("STOCK_ONLY_ST_NO_ST")
    paths.append("STILL_BLOCKED")
    return paths


def _by_identity(frame: pd.DataFrame) -> dict[tuple[str, str, str], dict[str, Any]]:
    if frame.empty:
        return {}
    return {_identity_key(row): row for row in frame.to_dict("records")}


def _identity_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        _string(row.get("signal_date")),
        normalize_symbol_value(row.get("symbol")),
        _string(row.get("universe_name")),
    )


def _metadata_or_frame_id(metadata: dict[str, Any], frame: pd.DataFrame, field: str) -> str:
    return _string(metadata.get(field)) or _first_non_empty(frame, field)


def _first_non_empty(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return ""
    for value in frame[column].tolist():
        text = _string(value)
        if text:
            return text
    return ""


def _source_role(lineage_field: str) -> str:
    return {
        "first_batch_partial_completion_impact_id": "active partial blocker impact",
        "first_batch_reviewer_evidence_completion_plan_id": "first-batch reviewer completion plan",
        "validator_id": "strict checklist validator",
        "policy_comparison_id": "reviewed no-hit policy comparison",
        "reviewed_no_hit_policy_comparison_id": "reviewed no-hit policy comparison lineage",
        "enrichment_id": "official status evidence packet enrichment",
        "reviewer_no_hit_acceptance_id": "reviewer no-hit acceptance template",
        "reviewer_no_hit_downstream_impact_id": "reviewer no-hit downstream impact",
    }.get(lineage_field, "source artifact")


def _plan_id(
    request: MaterialPitEvidenceGateClosurePlanRequest,
    completion_plan: pd.DataFrame,
    partial_impact: pd.DataFrame,
) -> str:
    digest = hashlib.sha256()
    digest.update(str(request.completion_plan).encode("utf-8"))
    digest.update(str(request.partial_impact).encode("utf-8"))
    digest.update("|".join(completion_plan.get("symbol", pd.Series(dtype=str)).astype(str).tolist()).encode("utf-8"))
    digest.update("|".join(partial_impact.get("symbol", pd.Series(dtype=str)).astype(str).tolist()).encode("utf-8"))
    return digest.hexdigest()[:12]


def _split_values(value: str) -> list[str]:
    normalized = value.replace(",", ";")
    return [part.strip() for part in normalized.split(";") if part.strip()]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _string(value).lower() in {"true", "1", "yes", "y"}


def _string(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _assert_settings_safe(settings: MaterialPitEvidenceGateClosurePlanSettings) -> None:
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
        raise ValueError(f"Unsafe material PIT evidence gate closure plan settings enabled: {', '.join(enabled)}")


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        return value.item()
    return value

