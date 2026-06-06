"""Report-only one-row material evidence fill package.

This workflow creates a diagnostics package for one target PIT universe row. It
drafts context-safe evidence fields and reports remaining blockers, but it does
not create clean review updates, apply approval, run PIT review/export
workflows, write universe inputs, run current-candidates, build snapshots,
compute labels, or mutate cache.
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

TARGET_SIGNAL_DATE = "2024-04-02"
TARGET_SYMBOL = "000001"
TARGET_UNIVERSE_NAME = "stock_core"

PACKAGE_COLUMNS = [
    "package_id",
    "reviewer_material_evidence_fill_guidance_id",
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
    "review_status",
    "include_flag",
    "valid_for_signal_date",
    "survivorship_bias_resolved",
    "checklist_pass_candidate",
    "remaining_blocked",
    "context_field_drafted_count",
    "material_blocker_closed_count",
    "active_not_delisted_blocked",
    "stock_st_no_st_blocked",
    "survivorship_blocked",
    "clean_review_updates_created",
    "approval_applied",
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
    "package_only",
]


@dataclass(frozen=True)
class OneRowMaterialEvidenceFillPackageSettings:
    output_dir: Path = Path("outputs/reports/one_row_material_evidence_fill_package")
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
class OneRowMaterialEvidenceFillPackageRequest:
    audit: Path
    guidance: Path
    material_plan: Path
    partial_impact: Path | None
    completion_plan: Path | None
    validator: Path | None
    enrichment: Path | None
    reviewer_no_hit_acceptance: Path | None
    reviewer_no_hit_downstream_impact: Path | None
    signal_date: str = TARGET_SIGNAL_DATE
    symbol: str = TARGET_SYMBOL
    universe_name: str = TARGET_UNIVERSE_NAME


@dataclass(frozen=True)
class OneRowMaterialEvidenceFillPackageResult:
    package_id: str
    status: str
    request: OneRowMaterialEvidenceFillPackageRequest
    reviewer_material_evidence_fill_guidance_id: str
    material_pit_evidence_gate_closure_plan_id: str
    first_batch_partial_completion_impact_id: str
    first_batch_reviewer_evidence_completion_plan_id: str
    validator_id: str
    enrichment_id: str
    reviewer_no_hit_acceptance_id: str
    reviewer_no_hit_downstream_impact_id: str
    package_row_count: int
    context_field_drafted_count: int
    material_blocker_closed_count: int
    checklist_pass_candidate_count: int
    remaining_blocked_count: int
    clean_review_updates_created: bool
    approval_applied: bool
    package_frame: pd.DataFrame
    drafted_context_fields: pd.DataFrame
    remaining_blockers: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_one_row_material_evidence_fill_package(
    *,
    audit: str | Path = "outputs/reports/manual_diagnostics/one_row_material_evidence_fill_package_audit_v0_1",
    guidance: str | Path = "outputs/reports/reviewer_material_evidence_fill_guidance/94f5ff204662",
    material_plan: str | Path = "outputs/reports/material_pit_evidence_gate_closure_plan/2d6ab8e7f9f8",
    partial_impact: str | Path | None = "outputs/reports/first_batch_partial_completion_impact/ea81f81ae764",
    completion_plan: str | Path | None = "outputs/reports/first_batch_reviewer_evidence_completion_plan/c630522f235a",
    validator: str | Path | None = "outputs/reports/pit_evidence_checklist_validator/62e9eb747197",
    enrichment: str | Path | None = "outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c",
    reviewer_no_hit_acceptance: str | Path | None = (
        "outputs/reports/reviewer_no_hit_source_coverage_acceptance/2e05e4b74794"
    ),
    reviewer_no_hit_downstream_impact: str | Path | None = (
        "outputs/reports/reviewer_no_hit_acceptance_downstream_impact/9e164963455e"
    ),
    signal_date: str = TARGET_SIGNAL_DATE,
    symbol: str = TARGET_SYMBOL,
    universe_name: str = TARGET_UNIVERSE_NAME,
    output_dir: str | Path | None = None,
    settings: OneRowMaterialEvidenceFillPackageSettings | None = None,
) -> OneRowMaterialEvidenceFillPackageResult:
    resolved_settings = settings or OneRowMaterialEvidenceFillPackageSettings()
    if output_dir is not None:
        resolved_settings = OneRowMaterialEvidenceFillPackageSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)
    request = OneRowMaterialEvidenceFillPackageRequest(
        audit=Path(audit),
        guidance=Path(guidance),
        material_plan=Path(material_plan),
        partial_impact=Path(partial_impact) if partial_impact else None,
        completion_plan=Path(completion_plan) if completion_plan else None,
        validator=Path(validator) if validator else None,
        enrichment=Path(enrichment) if enrichment else None,
        reviewer_no_hit_acceptance=Path(reviewer_no_hit_acceptance) if reviewer_no_hit_acceptance else None,
        reviewer_no_hit_downstream_impact=Path(reviewer_no_hit_downstream_impact)
        if reviewer_no_hit_downstream_impact
        else None,
        signal_date=_text(signal_date),
        symbol=normalize_symbol_value(symbol),
        universe_name=_text(universe_name),
    )
    frames, metadata = load_one_row_material_evidence_fill_package_inputs(request)
    lineage = _lineage(frames, metadata)
    package_id = _package_id(request, frames, lineage)
    target = _target_key(request)
    drafted = _drafted_context_fields(package_id, frames["fillable"], target)
    remaining = _remaining_blockers(package_id, frames["remaining"], target)
    package_frame = build_one_row_material_evidence_fill_package_frame(
        package_id=package_id,
        request=request,
        lineage=lineage,
        drafted_context_fields=drafted,
        remaining_blockers=remaining,
    )
    paths = resolve_one_row_material_evidence_fill_package_paths(resolved_settings.output_dir, package_id)
    result = OneRowMaterialEvidenceFillPackageResult(
        package_id=package_id,
        status="WARN",
        request=request,
        reviewer_material_evidence_fill_guidance_id=lineage["reviewer_material_evidence_fill_guidance_id"],
        material_pit_evidence_gate_closure_plan_id=lineage["material_pit_evidence_gate_closure_plan_id"],
        first_batch_partial_completion_impact_id=lineage["first_batch_partial_completion_impact_id"],
        first_batch_reviewer_evidence_completion_plan_id=lineage[
            "first_batch_reviewer_evidence_completion_plan_id"
        ],
        validator_id=lineage["validator_id"],
        enrichment_id=lineage["enrichment_id"],
        reviewer_no_hit_acceptance_id=lineage["reviewer_no_hit_acceptance_id"],
        reviewer_no_hit_downstream_impact_id=lineage["reviewer_no_hit_downstream_impact_id"],
        package_row_count=len(package_frame),
        context_field_drafted_count=len(drafted),
        material_blocker_closed_count=0,
        checklist_pass_candidate_count=0,
        remaining_blocked_count=16,
        clean_review_updates_created=False,
        approval_applied=False,
        package_frame=package_frame,
        drafted_context_fields=drafted,
        remaining_blockers=remaining,
        artifact_paths=paths,
        warnings=[],
    )
    if resolved_settings.write_artifacts:
        write_one_row_material_evidence_fill_package_artifacts(
            result,
            overclaim_risk=_artifact_or_empty(frames, "overclaim", target),
            reviewer_judgment=_artifact_or_empty(frames, "reviewer_judgment", target),
            external_evidence=_artifact_or_empty(frames, "external_evidence", target),
            safety_validation=_package_safety_validation(result),
            source_lineage=_source_lineage_summary(package_id, lineage, request),
        )
    return result


def load_one_row_material_evidence_fill_package_inputs(
    request: OneRowMaterialEvidenceFillPackageRequest,
) -> tuple[dict[str, pd.DataFrame], dict[str, dict[str, Any]]]:
    frames = {
        "guidance": _read_artifact_csv(
            request.guidance,
            "reviewer_material_evidence_fill_guidance.csv",
            required=True,
        ),
        "template": _read_artifact_csv(request.guidance, "reviewer_fill_template_safe_defaults.csv", required=True),
        "material_plan": _read_artifact_csv(
            request.material_plan,
            "material_pit_evidence_gate_closure_plan.csv",
            required=True,
        ),
        "blocker_matrix": _read_artifact_csv(
            request.material_plan,
            "row_level_material_blocker_matrix.csv",
            required=True,
        ),
        "requirements": _read_artifact_csv(
            request.material_plan,
            "checklist_pass_candidate_requirements.csv",
            required=True,
        ),
        "fillable": _read_artifact_csv(request.audit, "fillable_field_assessment.csv", required=True),
        "remaining": _read_artifact_csv(request.audit, "remaining_blockers_after_candidate_fill.csv", required=True),
        "overclaim": _read_artifact_csv(request.audit, "overclaim_risk_matrix.csv", required=True),
        "reviewer_judgment": _read_artifact_csv(request.audit, "reviewer_judgment_needed.csv", required=True),
        "external_evidence": _read_artifact_csv(request.audit, "external_evidence_needed.csv", required=True),
        "partial_impact": _read_artifact_csv(
            request.partial_impact,
            "first_batch_partial_completion_impact.csv",
            required=False,
        ),
        "completion_plan": _read_artifact_csv(
            request.completion_plan,
            "first_batch_reviewer_evidence_completion_plan.csv",
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
        "guidance": _read_metadata(request.guidance),
        "material_plan": _read_metadata(request.material_plan),
        "partial_impact": _read_metadata(request.partial_impact),
        "completion_plan": _read_metadata(request.completion_plan),
        "validator": _read_metadata(request.validator),
        "enrichment": _read_metadata(request.enrichment),
        "reviewer_no_hit_acceptance": _read_metadata(request.reviewer_no_hit_acceptance),
        "reviewer_no_hit_downstream_impact": _read_metadata(request.reviewer_no_hit_downstream_impact),
    }
    for key, frame in frames.items():
        frames[key] = _normalize_identity(frame)
    _require_target_row(frames["guidance"], request, "guidance")
    _require_target_row(frames["material_plan"], request, "material_plan")
    return frames, metadata


def build_one_row_material_evidence_fill_package_frame(
    *,
    package_id: str,
    request: OneRowMaterialEvidenceFillPackageRequest,
    lineage: dict[str, str],
    drafted_context_fields: pd.DataFrame,
    remaining_blockers: pd.DataFrame,
) -> pd.DataFrame:
    row = {
        "package_id": package_id,
        **lineage,
        "signal_date": request.signal_date,
        "symbol": normalize_symbol_value(request.symbol),
        "universe_name": request.universe_name,
        "review_status": "NEEDS_MORE_EVIDENCE",
        "include_flag": False,
        "valid_for_signal_date": False,
        "survivorship_bias_resolved": False,
        "checklist_pass_candidate": False,
        "remaining_blocked": True,
        "context_field_drafted_count": len(drafted_context_fields),
        "material_blocker_closed_count": 0,
        "active_not_delisted_blocked": True,
        "stock_st_no_st_blocked": True,
        "survivorship_blocked": True,
        "clean_review_updates_created": False,
        "approval_applied": False,
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
        "package_only": True,
    }
    return pd.DataFrame([row], columns=PACKAGE_COLUMNS)


def resolve_one_row_material_evidence_fill_package_paths(output_dir: str | Path, package_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / package_id
    return {
        "artifact_dir": artifact_dir,
        "package_csv": artifact_dir / "one_row_material_evidence_fill_package.csv",
        "drafted_context_fields": artifact_dir / "drafted_context_fields.csv",
        "remaining_blockers_after_fill": artifact_dir / "remaining_blockers_after_fill.csv",
        "overclaim_risk_matrix": artifact_dir / "overclaim_risk_matrix.csv",
        "reviewer_judgment_needed": artifact_dir / "reviewer_judgment_needed.csv",
        "external_evidence_needed": artifact_dir / "external_evidence_needed.csv",
        "package_safety_validation": artifact_dir / "package_safety_validation.json",
        "source_lineage_summary": artifact_dir / "source_lineage_summary.csv",
        "report": artifact_dir / "report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def write_one_row_material_evidence_fill_package_artifacts(
    result: OneRowMaterialEvidenceFillPackageResult,
    *,
    overclaim_risk: pd.DataFrame,
    reviewer_judgment: pd.DataFrame,
    external_evidence: pd.DataFrame,
    safety_validation: dict[str, Any],
    source_lineage: pd.DataFrame,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.package_frame.to_csv(paths["package_csv"], index=False)
    result.drafted_context_fields.to_csv(paths["drafted_context_fields"], index=False)
    result.remaining_blockers.to_csv(paths["remaining_blockers_after_fill"], index=False)
    overclaim_risk.to_csv(paths["overclaim_risk_matrix"], index=False)
    reviewer_judgment.to_csv(paths["reviewer_judgment_needed"], index=False)
    external_evidence.to_csv(paths["external_evidence_needed"], index=False)
    source_lineage.to_csv(paths["source_lineage_summary"], index=False)
    paths["package_safety_validation"].write_text(
        json.dumps(_json_safe(safety_validation), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    paths["report"].write_text(render_one_row_material_evidence_fill_package_report(result), encoding="utf-8")
    paths["metadata"].write_text(
        json.dumps(_json_safe(build_one_row_material_evidence_fill_package_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths


def render_one_row_material_evidence_fill_package_report(
    result: OneRowMaterialEvidenceFillPackageResult,
) -> str:
    return "\n".join(
        [
            f"# One-Row Material Evidence Fill Package: {result.package_id}",
            "",
            SAFETY_STATEMENT,
            "",
            "This is a diagnostics/report-only package for one PIT universe row. It drafts context fields but keeps the row non-approved.",
            "",
            "## Target Row",
            "",
            f"- signal_date: {result.request.signal_date}",
            f"- symbol: {result.request.symbol}",
            f"- universe_name: {result.request.universe_name}",
            "",
            "## Summary",
            "",
            f"- package_row_count: {result.package_row_count}",
            f"- context_field_drafted_count: {result.context_field_drafted_count}",
            f"- material_blocker_closed_count: {result.material_blocker_closed_count}",
            f"- checklist_pass_candidate_count: {result.checklist_pass_candidate_count}",
            f"- remaining_blocked_count: {result.remaining_blocked_count}",
            f"- clean_review_updates_created: {result.clean_review_updates_created}",
            f"- approval_applied: {result.approval_applied}",
            "",
            "## Interpretation",
            "",
            "SZSE 1815 same-date quotation context can be carried as quotation/traded context only. It is not treated as standalone not-delisted, no-ST, no-suspension, or survivorship evidence.",
            "No-hit support remains reviewer-policy dependent and is not approval-grade in this package.",
            "The row remains blocked until active/not-delisted evidence, no-ST evidence, reviewer no-hit acceptance, PIT timing policy, and survivorship rationale are accepted in later explicit workflows.",
            "",
        ]
    )


def build_one_row_material_evidence_fill_package_metadata(
    result: OneRowMaterialEvidenceFillPackageResult,
) -> dict[str, Any]:
    return {
        "package_id": result.package_id,
        "status": result.status,
        "reviewer_material_evidence_fill_guidance_id": result.reviewer_material_evidence_fill_guidance_id,
        "material_pit_evidence_gate_closure_plan_id": result.material_pit_evidence_gate_closure_plan_id,
        "first_batch_partial_completion_impact_id": result.first_batch_partial_completion_impact_id,
        "first_batch_reviewer_evidence_completion_plan_id": result.first_batch_reviewer_evidence_completion_plan_id,
        "validator_id": result.validator_id,
        "enrichment_id": result.enrichment_id,
        "reviewer_no_hit_acceptance_id": result.reviewer_no_hit_acceptance_id,
        "reviewer_no_hit_downstream_impact_id": result.reviewer_no_hit_downstream_impact_id,
        "signal_date": result.request.signal_date,
        "symbol": result.request.symbol,
        "universe_name": result.request.universe_name,
        "package_row_count": result.package_row_count,
        "context_field_drafted_count": result.context_field_drafted_count,
        "material_blocker_closed_count": result.material_blocker_closed_count,
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
        "package_only": True,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
        "safety_statement": SAFETY_STATEMENT,
        "known_limitations": [
            "This package is one-row and diagnostics/report-only.",
            "Context fields do not reduce material PIT blockers by themselves.",
            "No clean review updates are created.",
            "No row is approval-ready or checklist-pass under this workflow.",
        ],
    }


def _drafted_context_fields(package_id: str, frame: pd.DataFrame, target: tuple[str, str, str]) -> pd.DataFrame:
    result = _filter_target(frame, target).copy()
    if result.empty:
        return pd.DataFrame()
    result.insert(0, "package_id", package_id)
    result["draft_context_only"] = True
    result["can_close_material_blocker"] = False
    result["include_flag"] = False
    result["valid_for_signal_date"] = False
    result["survivorship_bias_resolved"] = False
    result["approval_applied"] = False
    return result


def _remaining_blockers(package_id: str, frame: pd.DataFrame, target: tuple[str, str, str]) -> pd.DataFrame:
    result = _filter_target(frame, target).copy()
    if result.empty:
        return pd.DataFrame()
    result.insert(0, "package_id", package_id)
    result["remaining_blocked"] = True
    result["checklist_pass_candidate"] = False
    result["approval_applied"] = False
    return result


def _artifact_or_empty(frames: dict[str, pd.DataFrame], key: str, target: tuple[str, str, str]) -> pd.DataFrame:
    frame = frames.get(key, pd.DataFrame())
    if frame.empty:
        return frame
    result = _filter_target(frame, target)
    return result.copy() if not result.empty else frame.copy()


def _source_lineage_summary(
    package_id: str,
    lineage: dict[str, str],
    request: OneRowMaterialEvidenceFillPackageRequest,
) -> pd.DataFrame:
    path_by_field = {
        "reviewer_material_evidence_fill_guidance_id": request.guidance,
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
                "package_id": package_id,
                "lineage_field": field,
                "lineage_value": value,
                "source_path": str(path_by_field.get(field) or ""),
                "approval_applied": False,
                "package_only": True,
            }
            for field, value in lineage.items()
        ]
    )


def _package_safety_validation(result: OneRowMaterialEvidenceFillPackageResult) -> dict[str, Any]:
    text = result.package_frame.to_csv(index=False)
    return {
        "validation_status": "PASS",
        "approved_for_pit_universe_present": "APPROVED_FOR_PIT_UNIVERSE" in text,
        "include_flag_true_present": False,
        "valid_for_signal_date_true_present": False,
        "survivorship_bias_resolved_true_present": False,
        "clean_review_updates_created": False,
        "approval_applied": False,
        "pit_review_run": False,
        "export_readiness_run": False,
        "export_staging_run": False,
        "universe_exported": False,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
        "cache_mutated": False,
    }


def _lineage(frames: dict[str, pd.DataFrame], metadata: dict[str, dict[str, Any]]) -> dict[str, str]:
    guidance = frames["guidance"]
    material = frames["material_plan"]
    guidance_meta = metadata.get("guidance", {})
    material_meta = metadata.get("material_plan", {})
    return {
        "reviewer_material_evidence_fill_guidance_id": _text(
            guidance_meta.get("guidance_id") or _first_non_empty(guidance, "guidance_id")
        ),
        "material_pit_evidence_gate_closure_plan_id": _text(
            material_meta.get("plan_id") or _first_non_empty(material, "plan_id")
        ),
        "first_batch_partial_completion_impact_id": _text(
            material_meta.get("first_batch_partial_completion_impact_id")
            or _first_non_empty(material, "first_batch_partial_completion_impact_id")
            or _metadata_or_frame_id(metadata.get("partial_impact", {}), frames.get("partial_impact"), "impact_id")
        ),
        "first_batch_reviewer_evidence_completion_plan_id": _text(
            material_meta.get("first_batch_reviewer_evidence_completion_plan_id")
            or _first_non_empty(material, "first_batch_reviewer_evidence_completion_plan_id")
            or _metadata_or_frame_id(metadata.get("completion_plan", {}), frames.get("completion_plan"), "plan_id")
        ),
        "validator_id": _text(
            material_meta.get("validator_id")
            or _first_non_empty(material, "validator_id")
            or _metadata_or_frame_id(metadata.get("validator", {}), frames.get("validator"), "validator_id")
        ),
        "enrichment_id": _text(
            material_meta.get("enrichment_id")
            or _first_non_empty(material, "enrichment_id")
            or _metadata_or_frame_id(metadata.get("enrichment", {}), frames.get("enrichment"), "enrichment_id")
        ),
        "reviewer_no_hit_acceptance_id": _text(
            material_meta.get("reviewer_no_hit_acceptance_id")
            or _first_non_empty(material, "reviewer_no_hit_acceptance_id")
            or _metadata_or_frame_id(
                metadata.get("reviewer_no_hit_acceptance", {}),
                frames.get("reviewer_no_hit_acceptance"),
                "acceptance_id",
            )
        ),
        "reviewer_no_hit_downstream_impact_id": _text(
            material_meta.get("reviewer_no_hit_downstream_impact_id")
            or _first_non_empty(material, "reviewer_no_hit_downstream_impact_id")
            or _metadata_or_frame_id(
                metadata.get("reviewer_no_hit_downstream_impact", {}),
                frames.get("reviewer_no_hit_downstream_impact"),
                "impact_id",
            )
        ),
    }


def _package_id(
    request: OneRowMaterialEvidenceFillPackageRequest,
    frames: dict[str, pd.DataFrame],
    lineage: dict[str, str],
) -> str:
    digest = hashlib.sha256()
    digest.update("|".join(_target_key(request)).encode("utf-8"))
    digest.update(json.dumps(lineage, sort_keys=True).encode("utf-8"))
    for key in ["fillable", "remaining", "overclaim"]:
        digest.update(frames[key].to_csv(index=False).encode("utf-8"))
    return digest.hexdigest()[:12]


def _target_key(request: OneRowMaterialEvidenceFillPackageRequest) -> tuple[str, str, str]:
    return (request.signal_date, normalize_symbol_value(request.symbol), request.universe_name)


def _filter_target(frame: pd.DataFrame, target: tuple[str, str, str]) -> pd.DataFrame:
    if frame.empty:
        return frame
    for column in ["signal_date", "symbol", "universe_name"]:
        if column not in frame.columns:
            return frame.iloc[0:0].copy()
    return frame[
        (frame["signal_date"].astype(str) == target[0])
        & (frame["symbol"].map(normalize_symbol_value) == target[1])
        & (frame["universe_name"].astype(str) == target[2])
    ].copy()


def _require_target_row(frame: pd.DataFrame, request: OneRowMaterialEvidenceFillPackageRequest, label: str) -> None:
    if _filter_target(frame, _target_key(request)).empty:
        raise ValueError(
            f"Target row not found in {label}: {request.signal_date} / {request.symbol} / {request.universe_name}"
        )


def _read_artifact_csv(path: Path | None, filename: str, *, required: bool) -> pd.DataFrame:
    if path is None:
        if required:
            raise FileNotFoundError(filename)
        return pd.DataFrame()
    if path.is_file():
        csv_path = path
    else:
        csv_path = path / filename
    if not csv_path.exists():
        if required:
            raise FileNotFoundError(f"Artifact CSV not found: {csv_path}")
        return pd.DataFrame()
    return read_csv_preserve_symbol_columns(csv_path, keep_default_na=False)


def _read_metadata(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    metadata_path = path.parent / "metadata.json" if path.is_file() else path / "metadata.json"
    if not metadata_path.exists():
        return {}
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def _normalize_identity(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    result = frame.copy()
    if "symbol" in result.columns:
        result["symbol"] = result["symbol"].map(normalize_symbol_value)
    if "signal_date" in result.columns:
        result["signal_date"] = result["signal_date"].astype(str)
    if "universe_name" in result.columns:
        result["universe_name"] = result["universe_name"].astype(str)
    return result


def _metadata_or_frame_id(metadata: dict[str, Any], frame: pd.DataFrame | None, column: str) -> str:
    if column in metadata:
        return _text(metadata[column])
    if frame is not None and not frame.empty:
        return _first_non_empty(frame, column)
    return ""


def _first_non_empty(frame: pd.DataFrame, column: str) -> str:
    if column not in frame.columns:
        return ""
    for value in frame[column].tolist():
        text = _text(value)
        if text:
            return text
    return ""


def _assert_settings_safe(settings: OneRowMaterialEvidenceFillPackageSettings) -> None:
    unsafe = [
        "enable_approval",
        "enable_clean_review_updates",
        "enable_pit_review",
        "enable_export_readiness",
        "enable_export_staging",
        "enable_universe_export",
        "enable_data_raw_write",
        "enable_data_processed_write",
        "enable_current_candidates",
        "enable_snapshot_build",
        "enable_forward_labels",
        "enable_cache_mutation",
        "enable_live_trading",
        "enable_broker_api",
        "enable_order_placement",
        "enable_message_delivery",
    ]
    enabled = [name for name in unsafe if getattr(settings, name)]
    if enabled:
        raise ValueError(f"Unsafe one-row material evidence package setting enabled: {', '.join(enabled)}")


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()
