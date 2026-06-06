"""Status view for material PIT evidence gate closure plan artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.material_pit_evidence_gate_closure_plan_health import (
    check_material_pit_evidence_gate_closure_plan_health,
)
from quant_replay_system.material_pit_evidence_gate_closure_plan_index import (
    build_material_pit_evidence_gate_closure_plan_index,
)


NO_MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN = "NO_MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN"
MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_NEEDS_EVIDENCE = (
    "MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_NEEDS_EVIDENCE"
)
MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_READY_FOR_REVIEWER_FILL = (
    "MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_READY_FOR_REVIEWER_FILL"
)
MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_FAILED = "MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_FAILED"

SUMMARY_COLUMNS = [
    "latest_plan_id",
    "status",
    "workflow_stage",
    "health_status",
    "row_count",
    "checklist_pass_candidate_count",
    "remaining_blocked_count",
    "reusable_symbol_level_closure_count",
    "date_specific_closure_required_count",
    "reviewer_no_hit_acceptance_required_count",
    "survivorship_rationale_required_count",
    "metadata_closure_required_count",
    "stock_st_no_st_required_count",
    "clean_review_updates_created",
    "approval_applied",
    "report_path",
    "next_manual_action",
]


@dataclass(frozen=True)
class MaterialPitEvidenceGateClosurePlanStatusResult:
    latest_plan_id: str
    status: str
    workflow_stage: str
    health_status: str
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
    report_path: str
    next_manual_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_material_pit_evidence_gate_closure_plan_status(
    *,
    root: str | Path = "outputs/reports/material_pit_evidence_gate_closure_plan",
    output_dir: str | Path = "outputs/reports/material_pit_evidence_gate_closure_plan/status",
) -> MaterialPitEvidenceGateClosurePlanStatusResult:
    index = build_material_pit_evidence_gate_closure_plan_index(root=root)
    health = check_material_pit_evidence_gate_closure_plan_health(root=root)
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root)
    else:
        latest = index.index_frame.sort_values(["created_at", "plan_id"]).iloc[-1].to_dict()
        if health.status == "FAIL":
            status = "FAIL"
            stage = MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_FAILED
            next_action = "Repair material PIT evidence gate closure plan artifacts before reviewer fill planning."
        elif _to_int(latest.get("checklist_pass_candidate_count")) == 0:
            status = "WARN"
            stage = MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_NEEDS_EVIDENCE
            next_action = "Complete material PIT evidence, no-hit acceptance, survivorship rationale, and metadata before checklist-pass preview."
        else:
            status = "WARN"
            stage = MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_READY_FOR_REVIEWER_FILL
            next_action = "Review fill templates manually; do not create clean review updates without a later explicit workflow."
        result = _result_from_latest(latest, status, stage, health.status, next_action, output_dir, root)
    _write(result)
    return result


def _result_from_latest(
    latest: dict[str, Any],
    status: str,
    stage: str,
    health_status: str,
    next_action: str,
    output_dir: str | Path,
    root: str | Path,
) -> MaterialPitEvidenceGateClosurePlanStatusResult:
    summary = {
        "latest_plan_id": _text(latest.get("plan_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health_status,
        "row_count": _to_int(latest.get("row_count")),
        "checklist_pass_candidate_count": _to_int(latest.get("checklist_pass_candidate_count")),
        "remaining_blocked_count": _to_int(latest.get("remaining_blocked_count")),
        "reusable_symbol_level_closure_count": _to_int(latest.get("reusable_symbol_level_closure_count")),
        "date_specific_closure_required_count": _to_int(latest.get("date_specific_closure_required_count")),
        "reviewer_no_hit_acceptance_required_count": _to_int(latest.get("reviewer_no_hit_acceptance_required_count")),
        "survivorship_rationale_required_count": _to_int(latest.get("survivorship_rationale_required_count")),
        "metadata_closure_required_count": _to_int(latest.get("metadata_closure_required_count")),
        "stock_st_no_st_required_count": _to_int(latest.get("stock_st_no_st_required_count")),
        "clean_review_updates_created": _to_bool(latest.get("clean_review_updates_created")),
        "approval_applied": _to_bool(latest.get("approval_applied")),
        "report_path": _text(latest.get("report_path")),
        "next_manual_action": next_action,
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = _paths(output_dir, _hash_payload(summary))
    return MaterialPitEvidenceGateClosurePlanStatusResult(
        latest_plan_id=summary["latest_plan_id"],
        status=status,
        workflow_stage=stage,
        health_status=health_status,
        row_count=summary["row_count"],
        checklist_pass_candidate_count=summary["checklist_pass_candidate_count"],
        remaining_blocked_count=summary["remaining_blocked_count"],
        reusable_symbol_level_closure_count=summary["reusable_symbol_level_closure_count"],
        date_specific_closure_required_count=summary["date_specific_closure_required_count"],
        reviewer_no_hit_acceptance_required_count=summary["reviewer_no_hit_acceptance_required_count"],
        survivorship_rationale_required_count=summary["survivorship_rationale_required_count"],
        metadata_closure_required_count=summary["metadata_closure_required_count"],
        stock_st_no_st_required_count=summary["stock_st_no_st_required_count"],
        clean_review_updates_created=summary["clean_review_updates_created"],
        approval_applied=summary["approval_applied"],
        report_path=summary["report_path"],
        next_manual_action=next_action,
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health_status == "PASS" else [f"Material PIT gate closure plan health is {health_status}."],
        audit_metadata=_safe_audit_metadata(root),
    )


def _no_artifact_result(output_dir: str | Path, root: str | Path) -> MaterialPitEvidenceGateClosurePlanStatusResult:
    summary = {
        "latest_plan_id": "",
        "status": "WARN",
        "workflow_stage": NO_MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN,
        "health_status": "WARN",
        "row_count": 0,
        "checklist_pass_candidate_count": 0,
        "remaining_blocked_count": 0,
        "reusable_symbol_level_closure_count": 0,
        "date_specific_closure_required_count": 0,
        "reviewer_no_hit_acceptance_required_count": 0,
        "survivorship_rationale_required_count": 0,
        "metadata_closure_required_count": 0,
        "stock_st_no_st_required_count": 0,
        "clean_review_updates_created": False,
        "approval_applied": False,
        "report_path": "",
        "next_manual_action": "Run material-pit-evidence-gate-closure-plan after first-batch partial completion impact is available.",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = _paths(output_dir, _hash_payload(summary))
    return MaterialPitEvidenceGateClosurePlanStatusResult(
        latest_plan_id="",
        status="WARN",
        workflow_stage=NO_MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN,
        health_status="WARN",
        row_count=0,
        checklist_pass_candidate_count=0,
        remaining_blocked_count=0,
        reusable_symbol_level_closure_count=0,
        date_specific_closure_required_count=0,
        reviewer_no_hit_acceptance_required_count=0,
        survivorship_rationale_required_count=0,
        metadata_closure_required_count=0,
        stock_st_no_st_required_count=0,
        clean_review_updates_created=False,
        approval_applied=False,
        report_path="",
        next_manual_action=summary["next_manual_action"],
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[f"No material PIT evidence gate closure plan artifacts found under {root}."],
        audit_metadata=_safe_audit_metadata(root),
    )


def _write(result: MaterialPitEvidenceGateClosurePlanStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Material PIT Evidence Gate Closure Plan Status",
                "",
                f"- status: {result.status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_plan_id: {result.latest_plan_id}",
                f"- health_status: {result.health_status}",
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
                f"- next_manual_action: {result.next_manual_action}",
                "",
                "No PIT approval, clean review updates, export, current-candidates, snapshots, labels, data writes, or cache mutation was invoked.",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "status_id": paths["artifact_dir"].name,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "health_status": result.health_status,
        "latest_plan_id": result.latest_plan_id,
        "row_count": result.row_count,
        "checklist_pass_candidate_count": result.checklist_pass_candidate_count,
        "remaining_blocked_count": result.remaining_blocked_count,
        "reusable_symbol_level_closure_count": result.reusable_symbol_level_closure_count,
        "date_specific_closure_required_count": result.date_specific_closure_required_count,
        "reviewer_no_hit_acceptance_required_count": result.reviewer_no_hit_acceptance_required_count,
        "survivorship_rationale_required_count": result.survivorship_rationale_required_count,
        "metadata_closure_required_count": result.metadata_closure_required_count,
        "stock_st_no_st_required_count": result.stock_st_no_st_required_count,
        "clean_review_updates_created": result.clean_review_updates_created,
        "approval_applied": result.approval_applied,
        "report_path": result.report_path,
        "next_manual_action": result.next_manual_action,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")


def _paths(output_dir: str | Path, status_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / status_id
    return {
        "artifact_dir": artifact_dir,
        "status_csv": artifact_dir / "material_pit_evidence_gate_closure_plan_status.csv",
        "status_report": artifact_dir / "material_pit_evidence_gate_closure_plan_status_report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def _safe_audit_metadata(root: str | Path) -> dict[str, Any]:
    return {
        "root_dir": str(root),
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
        "cache_mutated": False,
    }


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _to_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


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

