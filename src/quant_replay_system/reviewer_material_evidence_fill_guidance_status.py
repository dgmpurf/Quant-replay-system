"""Status view for reviewer material evidence fill guidance artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.reviewer_material_evidence_fill_guidance_health import (
    check_reviewer_material_evidence_fill_guidance_health,
)
from quant_replay_system.reviewer_material_evidence_fill_guidance_index import (
    build_reviewer_material_evidence_fill_guidance_index,
)


NO_REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE = "NO_REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE"
REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_NEEDS_FILL = (
    "REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_NEEDS_FILL"
)
REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_READY_FOR_REVIEWER = (
    "REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_READY_FOR_REVIEWER"
)
REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_FAILED = "REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_FAILED"

SUMMARY_COLUMNS = [
    "latest_guidance_id",
    "status",
    "workflow_stage",
    "health_status",
    "row_count",
    "reviewer_guidance_row_count",
    "symbol_level_guidance_count",
    "date_specific_guidance_count",
    "no_hit_acceptance_guidance_count",
    "survivorship_rationale_guidance_count",
    "metadata_guidance_count",
    "checklist_pass_candidate_count",
    "remaining_blocked_count",
    "clean_review_updates_created",
    "approval_applied",
    "report_path",
    "next_manual_action",
]


@dataclass(frozen=True)
class ReviewerMaterialEvidenceFillGuidanceStatusResult:
    latest_guidance_id: str
    status: str
    workflow_stage: str
    health_status: str
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
    report_path: str
    next_manual_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_reviewer_material_evidence_fill_guidance_status(
    *,
    root: str | Path = "outputs/reports/reviewer_material_evidence_fill_guidance",
    output_dir: str | Path = "outputs/reports/reviewer_material_evidence_fill_guidance/status",
) -> ReviewerMaterialEvidenceFillGuidanceStatusResult:
    index = build_reviewer_material_evidence_fill_guidance_index(root=root)
    health = check_reviewer_material_evidence_fill_guidance_health(root=root)
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root)
    else:
        latest = index.index_frame.sort_values(["created_at", "guidance_id"]).iloc[-1].to_dict()
        if health.status == "FAIL":
            status = "FAIL"
            stage = REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_FAILED
            next_action = "Repair reviewer material evidence fill guidance artifacts before manual evidence work."
        elif _to_int(latest.get("remaining_blocked_count")) > 0 or _to_int(latest.get("checklist_pass_candidate_count")) == 0:
            status = "WARN"
            stage = REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_NEEDS_FILL
            next_action = "Fill reviewer evidence guidance in diagnostics copies only; no PIT approval has been applied."
        else:
            status = "WARN"
            stage = REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_READY_FOR_REVIEWER
            next_action = "Review completed guidance manually; do not create clean review updates without a later explicit workflow."
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
) -> ReviewerMaterialEvidenceFillGuidanceStatusResult:
    summary = {
        "latest_guidance_id": _text(latest.get("guidance_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health_status,
        "row_count": _to_int(latest.get("row_count")),
        "reviewer_guidance_row_count": _to_int(latest.get("reviewer_guidance_row_count")),
        "symbol_level_guidance_count": _to_int(latest.get("symbol_level_guidance_count")),
        "date_specific_guidance_count": _to_int(latest.get("date_specific_guidance_count")),
        "no_hit_acceptance_guidance_count": _to_int(latest.get("no_hit_acceptance_guidance_count")),
        "survivorship_rationale_guidance_count": _to_int(latest.get("survivorship_rationale_guidance_count")),
        "metadata_guidance_count": _to_int(latest.get("metadata_guidance_count")),
        "checklist_pass_candidate_count": _to_int(latest.get("checklist_pass_candidate_count")),
        "remaining_blocked_count": _to_int(latest.get("remaining_blocked_count")),
        "clean_review_updates_created": _to_bool(latest.get("clean_review_updates_created")),
        "approval_applied": _to_bool(latest.get("approval_applied")),
        "report_path": _text(latest.get("report_path")),
        "next_manual_action": next_action,
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = _paths(output_dir, _hash_payload(summary))
    return ReviewerMaterialEvidenceFillGuidanceStatusResult(
        latest_guidance_id=summary["latest_guidance_id"],
        status=status,
        workflow_stage=stage,
        health_status=health_status,
        row_count=summary["row_count"],
        reviewer_guidance_row_count=summary["reviewer_guidance_row_count"],
        symbol_level_guidance_count=summary["symbol_level_guidance_count"],
        date_specific_guidance_count=summary["date_specific_guidance_count"],
        no_hit_acceptance_guidance_count=summary["no_hit_acceptance_guidance_count"],
        survivorship_rationale_guidance_count=summary["survivorship_rationale_guidance_count"],
        metadata_guidance_count=summary["metadata_guidance_count"],
        checklist_pass_candidate_count=summary["checklist_pass_candidate_count"],
        remaining_blocked_count=summary["remaining_blocked_count"],
        clean_review_updates_created=summary["clean_review_updates_created"],
        approval_applied=summary["approval_applied"],
        report_path=summary["report_path"],
        next_manual_action=next_action,
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health_status == "PASS" else [f"Reviewer material evidence fill guidance health is {health_status}."],
        audit_metadata=_safe_audit_metadata(root),
    )


def _no_artifact_result(output_dir: str | Path, root: str | Path) -> ReviewerMaterialEvidenceFillGuidanceStatusResult:
    summary = {
        "latest_guidance_id": "",
        "status": "WARN",
        "workflow_stage": NO_REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE,
        "health_status": "WARN",
        "row_count": 0,
        "reviewer_guidance_row_count": 0,
        "symbol_level_guidance_count": 0,
        "date_specific_guidance_count": 0,
        "no_hit_acceptance_guidance_count": 0,
        "survivorship_rationale_guidance_count": 0,
        "metadata_guidance_count": 0,
        "checklist_pass_candidate_count": 0,
        "remaining_blocked_count": 0,
        "clean_review_updates_created": False,
        "approval_applied": False,
        "report_path": "",
        "next_manual_action": "Run reviewer-material-evidence-fill-guidance after material PIT evidence gate closure planning is available.",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = _paths(output_dir, _hash_payload(summary))
    return ReviewerMaterialEvidenceFillGuidanceStatusResult(
        latest_guidance_id="",
        status="WARN",
        workflow_stage=NO_REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE,
        health_status="WARN",
        row_count=0,
        reviewer_guidance_row_count=0,
        symbol_level_guidance_count=0,
        date_specific_guidance_count=0,
        no_hit_acceptance_guidance_count=0,
        survivorship_rationale_guidance_count=0,
        metadata_guidance_count=0,
        checklist_pass_candidate_count=0,
        remaining_blocked_count=0,
        clean_review_updates_created=False,
        approval_applied=False,
        report_path="",
        next_manual_action=summary["next_manual_action"],
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[f"No reviewer material evidence fill guidance artifacts found under {root}."],
        audit_metadata=_safe_audit_metadata(root),
    )


def _write(result: ReviewerMaterialEvidenceFillGuidanceStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Reviewer Material Evidence Fill Guidance Status",
                "",
                f"- status: {result.status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_guidance_id: {result.latest_guidance_id}",
                f"- health_status: {result.health_status}",
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
        "latest_guidance_id": result.latest_guidance_id,
        "row_count": result.row_count,
        "reviewer_guidance_row_count": result.reviewer_guidance_row_count,
        "symbol_level_guidance_count": result.symbol_level_guidance_count,
        "date_specific_guidance_count": result.date_specific_guidance_count,
        "no_hit_acceptance_guidance_count": result.no_hit_acceptance_guidance_count,
        "survivorship_rationale_guidance_count": result.survivorship_rationale_guidance_count,
        "metadata_guidance_count": result.metadata_guidance_count,
        "checklist_pass_candidate_count": result.checklist_pass_candidate_count,
        "remaining_blocked_count": result.remaining_blocked_count,
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
        "status_csv": artifact_dir / "reviewer_material_evidence_fill_guidance_status.csv",
        "status_report": artifact_dir / "reviewer_material_evidence_fill_guidance_status_report.md",
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
