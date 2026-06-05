"""Status view for first-batch partial completion impact artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.first_batch_partial_completion_impact_health import (
    check_first_batch_partial_completion_impact_health,
)
from quant_replay_system.first_batch_partial_completion_impact_index import (
    build_first_batch_partial_completion_impact_index,
)


NO_FIRST_BATCH_PARTIAL_COMPLETION_IMPACT = "NO_FIRST_BATCH_PARTIAL_COMPLETION_IMPACT"
FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_NO_COMPLETION = "FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_NO_COMPLETION"
FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_METADATA_ONLY_REDUCTION = (
    "FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_METADATA_ONLY_REDUCTION"
)
FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_MATERIAL_BLOCKERS_REMAIN = (
    "FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_MATERIAL_BLOCKERS_REMAIN"
)
FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_FAILED = "FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_FAILED"

SUMMARY_COLUMNS = [
    "latest_impact_id",
    "status",
    "workflow_stage",
    "health_status",
    "completion_plan_id",
    "partial_completion_path",
    "row_count",
    "completed_row_count",
    "completed_field_count",
    "blocker_reduced_count",
    "material_blocker_reduced_count",
    "checklist_pass_count",
    "remaining_blocked_count",
    "clean_review_updates_created",
    "approval_applied",
    "report_path",
    "next_manual_action",
]


@dataclass(frozen=True)
class FirstBatchPartialCompletionImpactStatusResult:
    latest_impact_id: str
    status: str
    workflow_stage: str
    health_status: str
    completion_plan_id: str
    partial_completion_path: str
    row_count: int
    completed_row_count: int
    completed_field_count: int
    blocker_reduced_count: int
    material_blocker_reduced_count: int
    checklist_pass_count: int
    remaining_blocked_count: int
    clean_review_updates_created: bool
    approval_applied: bool
    report_path: str
    next_manual_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_first_batch_partial_completion_impact_status(
    *,
    root: str | Path = "outputs/reports/first_batch_partial_completion_impact",
    output_dir: str | Path = "outputs/reports/first_batch_partial_completion_impact/status",
) -> FirstBatchPartialCompletionImpactStatusResult:
    index = build_first_batch_partial_completion_impact_index(root=root)
    health = check_first_batch_partial_completion_impact_health(root=root)
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root)
    else:
        latest = index.index_frame.sort_values(["created_at", "impact_id"]).iloc[-1].to_dict()
        if health.status == "FAIL":
            status = "FAIL"
            stage = FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_FAILED
            next_action = "Repair first-batch partial completion impact artifacts before reviewer evidence work."
        elif _to_int(latest.get("completed_row_count")) == 0:
            status = "WARN"
            stage = FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_NO_COMPLETION
            next_action = "Complete reviewer fields in a diagnostics fixture; no PIT approval has been applied."
        elif _to_int(latest.get("material_blocker_reduced_count")) == 0:
            status = "WARN"
            stage = FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_METADATA_ONLY_REDUCTION
            next_action = "Reviewer metadata was observed, but material PIT blockers remain; continue evidence collection."
        else:
            status = "WARN"
            stage = FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_MATERIAL_BLOCKERS_REMAIN
            next_action = "Review material blocker deltas manually; do not create clean review updates without a later explicit workflow."
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
) -> FirstBatchPartialCompletionImpactStatusResult:
    summary = {
        "latest_impact_id": _text(latest.get("impact_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health_status,
        "completion_plan_id": _text(latest.get("completion_plan_id")),
        "partial_completion_path": _text(latest.get("partial_completion_path")),
        "row_count": _to_int(latest.get("row_count")),
        "completed_row_count": _to_int(latest.get("completed_row_count")),
        "completed_field_count": _to_int(latest.get("completed_field_count")),
        "blocker_reduced_count": _to_int(latest.get("blocker_reduced_count")),
        "material_blocker_reduced_count": _to_int(latest.get("material_blocker_reduced_count")),
        "checklist_pass_count": _to_int(latest.get("checklist_pass_count")),
        "remaining_blocked_count": _to_int(latest.get("remaining_blocked_count")),
        "clean_review_updates_created": _to_bool(latest.get("clean_review_updates_created")),
        "approval_applied": _to_bool(latest.get("approval_applied")),
        "report_path": _text(latest.get("report_path")),
        "next_manual_action": next_action,
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = _paths(output_dir, _hash_payload(summary))
    return FirstBatchPartialCompletionImpactStatusResult(
        latest_impact_id=summary["latest_impact_id"],
        status=status,
        workflow_stage=stage,
        health_status=health_status,
        completion_plan_id=summary["completion_plan_id"],
        partial_completion_path=summary["partial_completion_path"],
        row_count=summary["row_count"],
        completed_row_count=summary["completed_row_count"],
        completed_field_count=summary["completed_field_count"],
        blocker_reduced_count=summary["blocker_reduced_count"],
        material_blocker_reduced_count=summary["material_blocker_reduced_count"],
        checklist_pass_count=summary["checklist_pass_count"],
        remaining_blocked_count=summary["remaining_blocked_count"],
        clean_review_updates_created=summary["clean_review_updates_created"],
        approval_applied=summary["approval_applied"],
        report_path=summary["report_path"],
        next_manual_action=next_action,
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health_status == "PASS" else [f"First-batch partial completion impact health is {health_status}."],
        audit_metadata=_safe_audit_metadata(root),
    )


def _no_artifact_result(output_dir: str | Path, root: str | Path) -> FirstBatchPartialCompletionImpactStatusResult:
    summary = {
        "latest_impact_id": "",
        "status": "WARN",
        "workflow_stage": NO_FIRST_BATCH_PARTIAL_COMPLETION_IMPACT,
        "health_status": "WARN",
        "completion_plan_id": "",
        "partial_completion_path": "",
        "row_count": 0,
        "completed_row_count": 0,
        "completed_field_count": 0,
        "blocker_reduced_count": 0,
        "material_blocker_reduced_count": 0,
        "checklist_pass_count": 0,
        "remaining_blocked_count": 0,
        "clean_review_updates_created": False,
        "approval_applied": False,
        "report_path": "",
        "next_manual_action": "Run first-batch-partial-completion-impact after creating a first-batch completion plan.",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = _paths(output_dir, _hash_payload(summary))
    return FirstBatchPartialCompletionImpactStatusResult(
        latest_impact_id="",
        status="WARN",
        workflow_stage=NO_FIRST_BATCH_PARTIAL_COMPLETION_IMPACT,
        health_status="WARN",
        completion_plan_id="",
        partial_completion_path="",
        row_count=0,
        completed_row_count=0,
        completed_field_count=0,
        blocker_reduced_count=0,
        material_blocker_reduced_count=0,
        checklist_pass_count=0,
        remaining_blocked_count=0,
        clean_review_updates_created=False,
        approval_applied=False,
        report_path="",
        next_manual_action=summary["next_manual_action"],
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[f"No first-batch partial completion impact artifacts found under {root}."],
        audit_metadata=_safe_audit_metadata(root),
    )


def _write(result: FirstBatchPartialCompletionImpactStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# First-Batch Partial Completion Impact Status",
                "",
                f"- status: {result.status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_impact_id: {result.latest_impact_id}",
                f"- health_status: {result.health_status}",
                f"- row_count: {result.row_count}",
                f"- completed_row_count: {result.completed_row_count}",
                f"- completed_field_count: {result.completed_field_count}",
                f"- blocker_reduced_count: {result.blocker_reduced_count}",
                f"- material_blocker_reduced_count: {result.material_blocker_reduced_count}",
                f"- checklist_pass_count: {result.checklist_pass_count}",
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
        "latest_impact_id": result.latest_impact_id,
        "row_count": result.row_count,
        "completed_row_count": result.completed_row_count,
        "completed_field_count": result.completed_field_count,
        "blocker_reduced_count": result.blocker_reduced_count,
        "material_blocker_reduced_count": result.material_blocker_reduced_count,
        "checklist_pass_count": result.checklist_pass_count,
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
        "status_csv": artifact_dir / "first_batch_partial_completion_impact_status.csv",
        "status_report": artifact_dir / "first_batch_partial_completion_impact_status_report.md",
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

