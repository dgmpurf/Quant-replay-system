"""Report-only reviewer material evidence fill guidance.

This workflow converts a material PIT evidence gate closure plan into
human-readable reviewer fill guidance. It does not approve rows, create clean
review updates, run PIT review/export workflows, write universe inputs, run
current-candidates, build snapshots, compute labels, or mutate cache.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns


SAFETY_STATEMENT = (
    "No approval, rejection, clean review updates, PIT review, export-readiness, "
    "staging, universe export, data/raw write, data/processed write, active worklist "
    "mutation, current-candidates generation, snapshot build, forward labels, live "
    "trading, broker API, orders, messages, paid/private APIs, or cache mutation was invoked."
)

GUIDANCE_COLUMNS = [
    "guidance_id",
    "material_pit_evidence_gate_closure_plan_id",
    "first_batch_partial_completion_impact_id",
    "first_batch_reviewer_evidence_completion_plan_id",
    "validator_id",
    "enrichment_id",
    "reviewer_no_hit_acceptance_id",
    "reviewer_no_hit_downstream_impact_id",
    "signal_date",
    "symbol",
    "universe_name",
    "resolved_instrument_type",
    "fill_groups_required",
    "first_reviewer_action",
    "remaining_blocked",
    "checklist_pass_candidate",
    "include_flag",
    "valid_for_signal_date",
    "survivorship_bias_resolved",
    "approval_applied",
    "clean_review_updates_created",
    "guidance_only",
]

SAFE_TEMPLATE_COLUMNS = [
    "guidance_id",
    "signal_date",
    "symbol",
    "universe_name",
    "closure_path",
    "review_status",
    "reviewer",
    "reviewed_at",
    "review_reason",
    "evidence_source",
    "evidence_reference",
    "evidence_path",
    "source_limitations",
    "reviewer_notes",
    "include_flag",
    "valid_for_signal_date",
    "survivorship_bias_resolved",
    "approval_applied",
    "guidance_only",
]


@dataclass(frozen=True)
class ReviewerMaterialEvidenceFillGuidanceSettings:
    output_dir: Path = Path("outputs/reports/reviewer_material_evidence_fill_guidance")
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
class ReviewerMaterialEvidenceFillGuidanceRequest:
    material_plan: Path
    audit: Path | None
    completion_plan: Path | None
    partial_impact: Path | None
    validator: Path | None
    enrichment: Path | None
    reviewer_no_hit_acceptance: Path | None
    reviewer_no_hit_downstream_impact: Path | None


@dataclass(frozen=True)
class ReviewerMaterialEvidenceFillGuidanceResult:
    guidance_id: str
    status: str
    request: ReviewerMaterialEvidenceFillGuidanceRequest
    material_pit_evidence_gate_closure_plan_id: str
    first_batch_partial_completion_impact_id: str
    first_batch_reviewer_evidence_completion_plan_id: str
    validator_id: str
    enrichment_id: str
    reviewer_no_hit_acceptance_id: str
    reviewer_no_hit_downstream_impact_id: str
    row_count: int
    reviewer_guidance_row_count: int
    symbol_level_guidance_count: int
    date_specific_guidance_count: int
    no_hit_acceptance_guidance_count: int
    survivorship_rationale_guidance_count: int
    metadata_guidance_count: int
    checklist_pass_candidate_count: int
    remaining_blocked_count: int
    clean_review_updates_created: bool
    approval_applied: bool
    guidance_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_reviewer_material_evidence_fill_guidance(
    *,
    material_plan: str | Path = "outputs/reports/material_pit_evidence_gate_closure_plan/2d6ab8e7f9f8",
    audit: str | Path | None = "outputs/reports/manual_diagnostics/reviewer_material_evidence_fill_guidance_audit_v0_1",
    completion_plan: str | Path | None = "outputs/reports/first_batch_reviewer_evidence_completion_plan/c630522f235a",
    partial_impact: str | Path | None = "outputs/reports/first_batch_partial_completion_impact/ea81f81ae764",
    validator: str | Path | None = "outputs/reports/pit_evidence_checklist_validator/62e9eb747197",
    enrichment: str | Path | None = "outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c",
    reviewer_no_hit_acceptance: str | Path | None = (
        "outputs/reports/reviewer_no_hit_source_coverage_acceptance/2e05e4b74794"
    ),
    reviewer_no_hit_downstream_impact: str | Path | None = (
        "outputs/reports/reviewer_no_hit_acceptance_downstream_impact/9e164963455e"
    ),
    output_dir: str | Path | None = None,
    settings: ReviewerMaterialEvidenceFillGuidanceSettings | None = None,
) -> ReviewerMaterialEvidenceFillGuidanceResult:
    resolved_settings = settings or ReviewerMaterialEvidenceFillGuidanceSettings()
    if output_dir is not None:
        resolved_settings = ReviewerMaterialEvidenceFillGuidanceSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)
    request = ReviewerMaterialEvidenceFillGuidanceRequest(
        material_plan=Path(material_plan),
        audit=Path(audit) if audit else None,
        completion_plan=Path(completion_plan) if completion_plan else None,
        partial_impact=Path(partial_impact) if partial_impact else None,
        validator=Path(validator) if validator else None,
        enrichment=Path(enrichment) if enrichment else None,
        reviewer_no_hit_acceptance=Path(reviewer_no_hit_acceptance) if reviewer_no_hit_acceptance else None,
        reviewer_no_hit_downstream_impact=Path(reviewer_no_hit_downstream_impact)
        if reviewer_no_hit_downstream_impact
        else None,
    )
    frames, metadata = load_reviewer_material_evidence_fill_guidance_inputs(request)
    lineage = _lineage(frames, metadata)
    guidance_id = _guidance_id(request, frames["material_plan"], lineage)
    guidance = build_reviewer_material_evidence_fill_guidance_frame(guidance_id, frames["material_plan"], lineage)
    symbol_level = _symbol_level_guidance(guidance_id, frames)
    date_specific = _date_specific_guidance(guidance_id, frames)
    no_hit = _no_hit_guidance(guidance_id, frames)
    survivorship = _survivorship_guidance(guidance_id, frames)
    metadata_guidance = _metadata_guidance(guidance_id, frames)
    safe_template = _safe_reviewer_template(guidance_id, frames)
    counts = _counts(guidance, symbol_level, date_specific, no_hit, survivorship, metadata_guidance)
    paths = resolve_reviewer_material_evidence_fill_guidance_paths(resolved_settings.output_dir, guidance_id)
    result = ReviewerMaterialEvidenceFillGuidanceResult(
        guidance_id=guidance_id,
        status="WARN" if counts["remaining_blocked_count"] else "PASS",
        request=request,
        material_pit_evidence_gate_closure_plan_id=lineage["material_pit_evidence_gate_closure_plan_id"],
        first_batch_partial_completion_impact_id=lineage["first_batch_partial_completion_impact_id"],
        first_batch_reviewer_evidence_completion_plan_id=lineage[
            "first_batch_reviewer_evidence_completion_plan_id"
        ],
        validator_id=lineage["validator_id"],
        enrichment_id=lineage["enrichment_id"],
        reviewer_no_hit_acceptance_id=lineage["reviewer_no_hit_acceptance_id"],
        reviewer_no_hit_downstream_impact_id=lineage["reviewer_no_hit_downstream_impact_id"],
        row_count=len(guidance),
        reviewer_guidance_row_count=counts["reviewer_guidance_row_count"],
        symbol_level_guidance_count=len(symbol_level),
        date_specific_guidance_count=len(date_specific),
        no_hit_acceptance_guidance_count=len(no_hit),
        survivorship_rationale_guidance_count=len(survivorship),
        metadata_guidance_count=len(metadata_guidance),
        checklist_pass_candidate_count=counts["checklist_pass_candidate_count"],
        remaining_blocked_count=counts["remaining_blocked_count"],
        clean_review_updates_created=False,
        approval_applied=False,
        guidance_frame=guidance,
        artifact_paths=paths,
        warnings=[],
    )
    if resolved_settings.write_artifacts:
        write_reviewer_material_evidence_fill_guidance_artifacts(
            result,
            fill_order=_recommended_fill_order(guidance_id),
            symbol_level=symbol_level,
            date_specific=date_specific,
            no_hit=no_hit,
            survivorship=survivorship,
            metadata_guidance=metadata_guidance,
            risk_controls=_risk_controls(guidance_id),
            safe_template=safe_template,
            lineage_summary=_source_lineage_summary(guidance_id, lineage, request),
        )
    return result


def load_reviewer_material_evidence_fill_guidance_inputs(
    request: ReviewerMaterialEvidenceFillGuidanceRequest,
) -> tuple[dict[str, pd.DataFrame], dict[str, dict[str, Any]]]:
    frames = {
        "material_plan": _read_artifact_csv(
            request.material_plan,
            "material_pit_evidence_gate_closure_plan.csv",
            required=True,
        ),
        "symbol_level": _read_artifact_csv(
            request.material_plan,
            "reusable_symbol_level_closure_plan.csv",
            required=True,
        ),
        "date_specific": _read_artifact_csv(request.material_plan, "date_specific_closure_plan.csv", required=True),
        "no_hit": _read_artifact_csv(
            request.material_plan,
            "reviewer_no_hit_acceptance_closure_plan.csv",
            required=True,
        ),
        "survivorship": _read_artifact_csv(
            request.material_plan,
            "survivorship_rationale_closure_plan.csv",
            required=True,
        ),
        "metadata_guidance": _read_artifact_csv(request.material_plan, "metadata_closure_plan.csv", required=True),
        "fill_template": _read_artifact_csv(
            request.material_plan,
            "reviewer_fill_template_by_closure_path.csv",
            required=True,
        ),
        "audit_fill_order": _read_artifact_csv(request.audit, "recommended_fill_order.csv", required=False),
        "completion_plan": _read_artifact_csv(
            request.completion_plan,
            "first_batch_reviewer_evidence_completion_plan.csv",
            required=False,
        ),
        "partial_impact": _read_artifact_csv(
            request.partial_impact,
            "first_batch_partial_completion_impact.csv",
            required=False,
        ),
        "validator": _read_artifact_csv(
            request.validator,
            "pit_evidence_checklist_validation.csv",
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
    metadata = {
        "material_plan": _read_metadata(request.material_plan),
        "completion_plan": _read_metadata(request.completion_plan),
        "partial_impact": _read_metadata(request.partial_impact),
        "validator": _read_metadata(request.validator),
        "enrichment": _read_metadata(request.enrichment),
        "reviewer_no_hit_acceptance": _read_metadata(request.reviewer_no_hit_acceptance),
        "reviewer_no_hit_downstream_impact": _read_metadata(request.reviewer_no_hit_downstream_impact),
    }
    for key, frame in frames.items():
        frames[key] = _normalize_identity(frame)
    return frames, metadata


def build_reviewer_material_evidence_fill_guidance_frame(
    guidance_id: str,
    material_plan: pd.DataFrame,
    lineage: dict[str, str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for raw in material_plan.to_dict("records"):
        groups = _fill_groups(raw)
        rows.append(
            {
                "guidance_id": guidance_id,
                **lineage,
                "signal_date": _text(raw.get("signal_date")),
                "symbol": normalize_symbol_value(raw.get("symbol")),
                "universe_name": _text(raw.get("universe_name")),
                "resolved_instrument_type": _text(raw.get("resolved_instrument_type")),
                "fill_groups_required": ";".join(groups),
                "first_reviewer_action": "Start with SAFETY_BASELINE, then fill reusable symbol-level evidence before date-specific rows.",
                "remaining_blocked": True,
                "checklist_pass_candidate": False,
                "include_flag": False,
                "valid_for_signal_date": False,
                "survivorship_bias_resolved": False,
                "approval_applied": False,
                "clean_review_updates_created": False,
                "guidance_only": True,
            }
        )
    return pd.DataFrame(rows, columns=GUIDANCE_COLUMNS)


def resolve_reviewer_material_evidence_fill_guidance_paths(output_dir: str | Path, guidance_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / guidance_id
    return {
        "artifact_dir": artifact_dir,
        "guidance_csv": artifact_dir / "reviewer_material_evidence_fill_guidance.csv",
        "recommended_fill_order": artifact_dir / "recommended_fill_order.csv",
        "symbol_level_fill_guidance": artifact_dir / "symbol_level_fill_guidance.csv",
        "date_specific_fill_guidance": artifact_dir / "date_specific_fill_guidance.csv",
        "no_hit_acceptance_fill_guidance": artifact_dir / "no_hit_acceptance_fill_guidance.csv",
        "survivorship_rationale_fill_guidance": artifact_dir / "survivorship_rationale_fill_guidance.csv",
        "metadata_fill_guidance": artifact_dir / "metadata_fill_guidance.csv",
        "reviewer_risk_controls": artifact_dir / "reviewer_risk_controls.csv",
        "reviewer_fill_template_safe_defaults": artifact_dir / "reviewer_fill_template_safe_defaults.csv",
        "source_lineage_summary": artifact_dir / "source_lineage_summary.csv",
        "report": artifact_dir / "report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def write_reviewer_material_evidence_fill_guidance_artifacts(
    result: ReviewerMaterialEvidenceFillGuidanceResult,
    *,
    fill_order: pd.DataFrame,
    symbol_level: pd.DataFrame,
    date_specific: pd.DataFrame,
    no_hit: pd.DataFrame,
    survivorship: pd.DataFrame,
    metadata_guidance: pd.DataFrame,
    risk_controls: pd.DataFrame,
    safe_template: pd.DataFrame,
    lineage_summary: pd.DataFrame,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.guidance_frame.to_csv(paths["guidance_csv"], index=False)
    fill_order.to_csv(paths["recommended_fill_order"], index=False)
    symbol_level.to_csv(paths["symbol_level_fill_guidance"], index=False)
    date_specific.to_csv(paths["date_specific_fill_guidance"], index=False)
    no_hit.to_csv(paths["no_hit_acceptance_fill_guidance"], index=False)
    survivorship.to_csv(paths["survivorship_rationale_fill_guidance"], index=False)
    metadata_guidance.to_csv(paths["metadata_fill_guidance"], index=False)
    risk_controls.to_csv(paths["reviewer_risk_controls"], index=False)
    safe_template.to_csv(paths["reviewer_fill_template_safe_defaults"], index=False)
    lineage_summary.to_csv(paths["source_lineage_summary"], index=False)
    paths["report"].write_text(render_reviewer_material_evidence_fill_guidance_report(result), encoding="utf-8")
    paths["metadata"].write_text(
        json.dumps(_json_safe(build_reviewer_material_evidence_fill_guidance_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths


def render_reviewer_material_evidence_fill_guidance_report(
    result: ReviewerMaterialEvidenceFillGuidanceResult,
) -> str:
    return "\n".join(
        [
            f"# Reviewer Material Evidence Fill Guidance: {result.guidance_id}",
            "",
            SAFETY_STATEMENT,
            "",
            "This is a reviewer guidance artifact only. It keeps every row non-approved and does not create clean review updates.",
            "",
            "## Summary",
            "",
            f"- row_count: {result.row_count}",
            f"- reviewer_guidance_row_count: {result.reviewer_guidance_row_count}",
            f"- symbol_level_guidance_count: {result.symbol_level_guidance_count}",
            f"- date_specific_guidance_count: {result.date_specific_guidance_count}",
            f"- no_hit_acceptance_guidance_count: {result.no_hit_acceptance_guidance_count}",
            f"- survivorship_rationale_guidance_count: {result.survivorship_rationale_guidance_count}",
            f"- metadata_guidance_count: {result.metadata_guidance_count}",
            f"- checklist_pass_candidate_count: {result.checklist_pass_candidate_count}",
            f"- remaining_blocked_count: {result.remaining_blocked_count}",
            f"- clean_review_updates_created: {result.clean_review_updates_created}",
            f"- approval_applied: {result.approval_applied}",
            "",
            "## Fill Order",
            "",
            "1. Diagnostics copy only.",
            "2. Reusable symbol-level identity evidence.",
            "3. Date-specific PIT status evidence.",
            "4. Reviewer no-hit acceptance as supporting context only.",
            "5. Survivorship rationale.",
            "6. Metadata completion.",
            "7. Diagnostics validation.",
            "",
            "## Risk Controls",
            "",
            "- Do not set approval flags in this workflow.",
            "- Do not treat SZSE 1815 quotation as not-delisted, no-ST, or no-suspension evidence by itself.",
            "- Do not treat no-hit context as approval without reviewer acceptance.",
            "- Do not create clean review updates here.",
            "",
        ]
    )


def build_reviewer_material_evidence_fill_guidance_metadata(
    result: ReviewerMaterialEvidenceFillGuidanceResult,
) -> dict[str, Any]:
    return {
        "guidance_id": result.guidance_id,
        "status": result.status,
        "material_pit_evidence_gate_closure_plan_id": result.material_pit_evidence_gate_closure_plan_id,
        "first_batch_partial_completion_impact_id": result.first_batch_partial_completion_impact_id,
        "first_batch_reviewer_evidence_completion_plan_id": result.first_batch_reviewer_evidence_completion_plan_id,
        "validator_id": result.validator_id,
        "enrichment_id": result.enrichment_id,
        "reviewer_no_hit_acceptance_id": result.reviewer_no_hit_acceptance_id,
        "reviewer_no_hit_downstream_impact_id": result.reviewer_no_hit_downstream_impact_id,
        "row_count": result.row_count,
        "reviewer_guidance_row_count": result.reviewer_guidance_row_count,
        "symbol_level_guidance_count": result.symbol_level_guidance_count,
        "date_specific_guidance_count": result.date_specific_guidance_count,
        "no_hit_acceptance_guidance_count": result.no_hit_acceptance_guidance_count,
        "survivorship_rationale_guidance_count": result.survivorship_rationale_guidance_count,
        "metadata_guidance_count": result.metadata_guidance_count,
        "checklist_pass_candidate_count": result.checklist_pass_candidate_count,
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
        "cache_mutated": False,
        "guidance_only": True,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
        "safety_statement": SAFETY_STATEMENT,
        "known_limitations": [
            "This workflow creates reviewer guidance only and does not create clean review updates.",
            "No row is a checklist-pass candidate under the current active evidence state.",
            "Reviewer no-hit acceptance remains supporting context only.",
        ],
    }


def _symbol_level_guidance(guidance_id: str, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frame = frames["symbol_level"].copy()
    frame.insert(0, "guidance_id", guidance_id)
    frame["fill_group"] = "REUSABLE_SYMBOL_LEVEL"
    frame["required_source_type"] = "official/public symbol-level source or reviewed local source with limitations"
    frame["not_sufficient_for_row_approval"] = True
    frame["include_flag"] = False
    frame["valid_for_signal_date"] = False
    frame["approval_applied"] = False
    return frame


def _date_specific_guidance(guidance_id: str, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frame = frames["date_specific"].copy()
    frame.insert(0, "guidance_id", guidance_id)
    frame["fill_group"] = "DATE_SPECIFIC_PIT_STATUS"
    frame["decision_time_required"] = True
    frame["quotation_is_not_complete_status_proof"] = True
    frame["include_flag"] = False
    frame["valid_for_signal_date"] = False
    frame["approval_applied"] = False
    return frame


def _no_hit_guidance(guidance_id: str, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frame = frames["no_hit"].copy()
    frame.insert(0, "guidance_id", guidance_id)
    frame["fill_group"] = "REVIEWER_NO_HIT_ACCEPTANCE"
    frame["fields_reviewer_must_complete"] = (
        "source_coverage_accepted;query_window_accepted;no_hit_inference_accepted;"
        "accepted_by;accepted_at;acceptance_reason;evidence_reference;limitations"
    )
    frame["supporting_context_only"] = True
    frame["can_approve_row"] = False
    frame["approval_applied"] = False
    return frame


def _survivorship_guidance(guidance_id: str, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frame = frames["survivorship"].copy()
    frame.insert(0, "guidance_id", guidance_id)
    frame["fill_group"] = "SURVIVORSHIP_RATIONALE"
    frame["write_after_evidence_chain_reviewed"] = True
    frame["survivorship_bias_resolved"] = False
    frame["approval_applied"] = False
    return frame


def _metadata_guidance(guidance_id: str, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frame = frames["metadata_guidance"].copy()
    frame.insert(0, "guidance_id", guidance_id)
    frame["fill_group"] = "PIT_METADATA"
    frame["source_rule"] = "Fill only from reviewed evidence and source lineage, not future-dated universe hints."
    frame["include_flag"] = False
    frame["valid_for_signal_date"] = False
    frame["approval_applied"] = False
    return frame


def _safe_reviewer_template(guidance_id: str, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    template = frames["fill_template"].copy()
    rows: list[dict[str, Any]] = []
    for raw in template.to_dict("records"):
        rows.append(
            {
                "guidance_id": guidance_id,
                "signal_date": _text(raw.get("signal_date")),
                "symbol": normalize_symbol_value(raw.get("symbol")),
                "universe_name": _text(raw.get("universe_name")),
                "closure_path": _text(raw.get("closure_path")),
                "review_status": _text(raw.get("review_status")) or "NEEDS_MORE_EVIDENCE",
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
                "survivorship_bias_resolved": False,
                "approval_applied": False,
                "guidance_only": True,
            }
        )
    return pd.DataFrame(rows, columns=SAFE_TEMPLATE_COLUMNS)


def _recommended_fill_order(guidance_id: str) -> pd.DataFrame:
    rows = [
        (1, "SAFETY_BASELINE", "diagnostics copy only", "Keep all approval and execution flags false."),
        (2, "REUSABLE_SYMBOL_LEVEL", "symbol/profile", "Attach reusable identity/listing/profile evidence."),
        (3, "DATE_SPECIFIC_PIT_STATUS", "symbol/date/profile", "Attach same-date PIT status evidence and decision-time reasoning."),
        (4, "REVIEWER_NO_HIT_ACCEPTANCE", "exception row", "Accept no-hit source coverage as supporting context only."),
        (5, "SURVIVORSHIP_RATIONALE", "symbol/date/profile", "Explain why the row does not rely on future universe membership."),
        (6, "PIT_METADATA", "symbol/date/profile", "Fill metadata only from reviewed source lineage."),
        (7, "DIAGNOSTICS_VALIDATION", "diagnostics artifact", "Run report-only validation before any later review workflow."),
    ]
    return pd.DataFrame(
        [
            {
                "guidance_id": guidance_id,
                "step": step,
                "fill_group": group,
                "scope": scope,
                "reviewer_instruction": instruction,
                "include_flag": False,
                "valid_for_signal_date": False,
                "approval_applied": False,
            }
            for step, group, scope, instruction in rows
        ]
    )


def _risk_controls(guidance_id: str) -> pd.DataFrame:
    rows = [
        ("Do not set approval flags in this workflow.", "accidental approval"),
        ("Do not treat SZSE 1815 quotation as not-delisted, no-ST, or no-suspension by itself.", "overstated evidence"),
        ("Do not treat no-hit context as approval without reviewer acceptance.", "unsupported approval inference"),
        ("Do not create clean review_updates.csv here.", "accidental downstream PIT review"),
        ("Do not write data/raw or data/processed.", "usable universe export before evidence closure"),
        ("Do not run PIT review, export-readiness, staging, or current-candidates.", "workflow boundary violation"),
        ("Keep include_flag and valid_for_signal_date false.", "premature execution readiness"),
    ]
    return pd.DataFrame(
        [
            {
                "guidance_id": guidance_id,
                "risk_control": control,
                "risk_prevented": risk,
                "required_default": "false/non-approved",
                "guidance_only": True,
            }
            for control, risk in rows
        ]
    )


def _source_lineage_summary(
    guidance_id: str,
    lineage: dict[str, str],
    request: ReviewerMaterialEvidenceFillGuidanceRequest,
) -> pd.DataFrame:
    path_by_field = {
        "material_pit_evidence_gate_closure_plan_id": request.material_plan,
        "first_batch_partial_completion_impact_id": request.partial_impact,
        "first_batch_reviewer_evidence_completion_plan_id": request.completion_plan,
        "validator_id": request.validator,
        "enrichment_id": request.enrichment,
        "reviewer_no_hit_acceptance_id": request.reviewer_no_hit_acceptance,
        "reviewer_no_hit_downstream_impact_id": request.reviewer_no_hit_downstream_impact,
    }
    return pd.DataFrame(
        [
            {
                "guidance_id": guidance_id,
                "lineage_field": field,
                "lineage_value": value,
                "source_path": str(path_by_field.get(field) or ""),
            }
            for field, value in lineage.items()
        ]
    )


def _counts(
    guidance: pd.DataFrame,
    symbol_level: pd.DataFrame,
    date_specific: pd.DataFrame,
    no_hit: pd.DataFrame,
    survivorship: pd.DataFrame,
    metadata_guidance: pd.DataFrame,
) -> dict[str, int]:
    return {
        "reviewer_guidance_row_count": (
            len(symbol_level) + len(date_specific) + len(no_hit) + len(survivorship) + len(metadata_guidance)
        ),
        "checklist_pass_candidate_count": _true_count(guidance, "checklist_pass_candidate"),
        "remaining_blocked_count": _true_count(guidance, "remaining_blocked"),
    }


def _lineage(frames: dict[str, pd.DataFrame], metadata: dict[str, dict[str, Any]]) -> dict[str, str]:
    plan = frames["material_plan"]
    material_metadata = metadata.get("material_plan", {})
    return {
        "material_pit_evidence_gate_closure_plan_id": _text(
            material_metadata.get("plan_id") or _first_non_empty(plan, "plan_id")
        ),
        "first_batch_partial_completion_impact_id": _text(
            material_metadata.get("first_batch_partial_completion_impact_id")
            or _first_non_empty(plan, "first_batch_partial_completion_impact_id")
        ),
        "first_batch_reviewer_evidence_completion_plan_id": _text(
            material_metadata.get("first_batch_reviewer_evidence_completion_plan_id")
            or _first_non_empty(plan, "first_batch_reviewer_evidence_completion_plan_id")
        ),
        "validator_id": _text(material_metadata.get("validator_id") or _first_non_empty(plan, "validator_id")),
        "enrichment_id": _text(material_metadata.get("enrichment_id") or _first_non_empty(plan, "enrichment_id")),
        "reviewer_no_hit_acceptance_id": _text(
            material_metadata.get("reviewer_no_hit_acceptance_id")
            or _first_non_empty(plan, "reviewer_no_hit_acceptance_id")
        ),
        "reviewer_no_hit_downstream_impact_id": _text(
            material_metadata.get("reviewer_no_hit_downstream_impact_id")
            or _first_non_empty(plan, "reviewer_no_hit_downstream_impact_id")
        ),
    }


def _fill_groups(row: dict[str, Any]) -> list[str]:
    groups = ["SAFETY_BASELINE"]
    if _bool(row.get("reusable_symbol_level_closure_required")):
        groups.append("REUSABLE_SYMBOL_LEVEL")
    if _bool(row.get("date_specific_closure_required")):
        groups.append("DATE_SPECIFIC_PIT_STATUS")
    if _bool(row.get("reviewer_no_hit_acceptance_required")):
        groups.append("REVIEWER_NO_HIT_ACCEPTANCE")
    if _bool(row.get("survivorship_rationale_required")):
        groups.append("SURVIVORSHIP_RATIONALE")
    if _bool(row.get("metadata_closure_required")):
        groups.append("PIT_METADATA")
    groups.append("DIAGNOSTICS_VALIDATION")
    return groups


def _read_artifact_csv(path: str | Path | None, filename: str, *, required: bool) -> pd.DataFrame:
    if path is None:
        if required:
            raise FileNotFoundError(filename)
        return pd.DataFrame()
    root = Path(path)
    csv_path = root if root.is_file() else root / filename
    if not csv_path.exists():
        if required:
            raise FileNotFoundError(f"Required CSV not found: {csv_path}")
        return pd.DataFrame()
    return read_csv_preserve_symbol_columns(csv_path, keep_default_na=False)


def _read_metadata(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    root = Path(path)
    metadata_path = root.parent / "metadata.json" if root.is_file() else root / "metadata.json"
    if not metadata_path.exists():
        return {}
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def _normalize_identity(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    result = frame.copy()
    if "symbol" in result:
        result["symbol"] = result["symbol"].map(normalize_symbol_value)
    for column in ["signal_date", "universe_name"]:
        if column in result:
            result[column] = result[column].map(_text)
    return result


def _guidance_id(
    request: ReviewerMaterialEvidenceFillGuidanceRequest,
    material_plan: pd.DataFrame,
    lineage: dict[str, str],
) -> str:
    payload = {
        "request": {key: str(value) for key, value in request.__dict__.items()},
        "lineage": lineage,
        "rows": material_plan[["signal_date", "symbol", "universe_name"]].to_dict("records"),
    }
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _assert_settings_safe(settings: ReviewerMaterialEvidenceFillGuidanceSettings) -> None:
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
    enabled = [key for key, value in unsafe.items() if value]
    if enabled:
        raise ValueError(f"Reviewer material evidence fill guidance is report-only; unsafe settings: {enabled}")


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame:
        return 0
    return int(frame[column].map(_bool).sum())


def _first_non_empty(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame:
        return ""
    for value in frame[column].tolist():
        text = _text(value)
        if text:
            return text
    return ""


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_json_safe(inner) for inner in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            return str(value)
    return value
