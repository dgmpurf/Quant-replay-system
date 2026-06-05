"""Status view for first-batch reviewer evidence completion plans."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.first_batch_reviewer_evidence_completion_plan_health import (
    check_first_batch_reviewer_evidence_completion_plan_health,
)
from quant_replay_system.first_batch_reviewer_evidence_completion_plan_index import (
    build_first_batch_reviewer_evidence_completion_plan_index,
)


NO_FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN = "NO_FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN"
FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_NEEDS_REVIEW = (
    "FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_NEEDS_REVIEW"
)
FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_READY_FOR_MANUAL_FILL = (
    "FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_READY_FOR_MANUAL_FILL"
)
FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_FAILED = "FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_FAILED"

SUMMARY_COLUMNS = [
    "latest_plan_id",
    "status",
    "workflow_stage",
    "health_status",
    "source_evidence_update_plan_id",
    "downstream_impact_id",
    "reviewer_no_hit_acceptance_id",
    "enrichment_id",
    "source_packet_id",
    "reviewed_no_hit_policy_comparison_id",
    "validator_id",
    "row_count",
    "stock_core_row_count",
    "etf_core_row_count",
    "reviewer_completion_required_count",
    "no_hit_acceptance_required_count",
    "survivorship_rationale_required_count",
    "metadata_completion_required_count",
    "checklist_pass_count",
    "remaining_blocked_count",
    "clean_review_updates_created",
    "approval_applied",
    "report_path",
    "next_manual_action",
]


@dataclass(frozen=True)
class FirstBatchReviewerEvidenceCompletionPlanStatusResult:
    latest_plan_id: str
    status: str
    workflow_stage: str
    health_status: str
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
    report_path: str
    next_manual_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_first_batch_reviewer_evidence_completion_plan_status(
    *,
    root: str | Path = "outputs/reports/first_batch_reviewer_evidence_completion_plan",
    output_dir: str | Path = "outputs/reports/first_batch_reviewer_evidence_completion_plan/status",
) -> FirstBatchReviewerEvidenceCompletionPlanStatusResult:
    index = build_first_batch_reviewer_evidence_completion_plan_index(root=root)
    health = check_first_batch_reviewer_evidence_completion_plan_health(root=root)
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root)
    else:
        latest = index.index_frame.sort_values(["created_at", "plan_id"]).iloc[-1].to_dict()
        if health.status == "FAIL":
            status = "FAIL"
            stage = FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_FAILED
            next_action = "Repair first-batch reviewer evidence completion plan artifacts before manual evidence work."
        elif _to_int(latest.get("reviewer_completion_required_count")) > 0 or _to_int(latest.get("remaining_blocked_count")) > 0:
            status = "WARN"
            stage = FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_NEEDS_REVIEW
            next_action = "Complete reviewer evidence fields and no-hit acceptance context manually; no PIT approval has been applied."
        else:
            status = "PASS"
            stage = FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_READY_FOR_MANUAL_FILL
            next_action = "Review completion templates manually before any separate diagnostics-only ingestion."
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
) -> FirstBatchReviewerEvidenceCompletionPlanStatusResult:
    summary = {
        "latest_plan_id": _text(latest.get("plan_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health_status,
        "source_evidence_update_plan_id": _text(latest.get("source_evidence_update_plan_id")),
        "downstream_impact_id": _text(latest.get("downstream_impact_id")),
        "reviewer_no_hit_acceptance_id": _text(latest.get("reviewer_no_hit_acceptance_id")),
        "enrichment_id": _text(latest.get("enrichment_id")),
        "source_packet_id": _text(latest.get("source_packet_id")),
        "reviewed_no_hit_policy_comparison_id": _text(latest.get("reviewed_no_hit_policy_comparison_id")),
        "validator_id": _text(latest.get("validator_id")),
        "row_count": _to_int(latest.get("row_count")),
        "stock_core_row_count": _to_int(latest.get("stock_core_row_count")),
        "etf_core_row_count": _to_int(latest.get("etf_core_row_count")),
        "reviewer_completion_required_count": _to_int(latest.get("reviewer_completion_required_count")),
        "no_hit_acceptance_required_count": _to_int(latest.get("no_hit_acceptance_required_count")),
        "survivorship_rationale_required_count": _to_int(latest.get("survivorship_rationale_required_count")),
        "metadata_completion_required_count": _to_int(latest.get("metadata_completion_required_count")),
        "checklist_pass_count": _to_int(latest.get("checklist_pass_count")),
        "remaining_blocked_count": _to_int(latest.get("remaining_blocked_count")),
        "clean_review_updates_created": _to_bool(latest.get("clean_review_updates_created")),
        "approval_applied": _to_bool(latest.get("approval_applied")),
        "report_path": _text(latest.get("report_path")),
        "next_manual_action": next_action,
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = _paths(output_dir, _hash_payload(summary))
    return FirstBatchReviewerEvidenceCompletionPlanStatusResult(
        latest_plan_id=summary["latest_plan_id"],
        status=status,
        workflow_stage=stage,
        health_status=health_status,
        source_evidence_update_plan_id=summary["source_evidence_update_plan_id"],
        downstream_impact_id=summary["downstream_impact_id"],
        reviewer_no_hit_acceptance_id=summary["reviewer_no_hit_acceptance_id"],
        enrichment_id=summary["enrichment_id"],
        source_packet_id=summary["source_packet_id"],
        reviewed_no_hit_policy_comparison_id=summary["reviewed_no_hit_policy_comparison_id"],
        validator_id=summary["validator_id"],
        row_count=summary["row_count"],
        stock_core_row_count=summary["stock_core_row_count"],
        etf_core_row_count=summary["etf_core_row_count"],
        reviewer_completion_required_count=summary["reviewer_completion_required_count"],
        no_hit_acceptance_required_count=summary["no_hit_acceptance_required_count"],
        survivorship_rationale_required_count=summary["survivorship_rationale_required_count"],
        metadata_completion_required_count=summary["metadata_completion_required_count"],
        checklist_pass_count=summary["checklist_pass_count"],
        remaining_blocked_count=summary["remaining_blocked_count"],
        clean_review_updates_created=summary["clean_review_updates_created"],
        approval_applied=summary["approval_applied"],
        report_path=summary["report_path"],
        next_manual_action=next_action,
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health_status == "PASS" else [f"First-batch completion plan health is {health_status}."],
        audit_metadata=_safe_audit_metadata(root),
    )


def _no_artifact_result(output_dir: str | Path, root: str | Path) -> FirstBatchReviewerEvidenceCompletionPlanStatusResult:
    summary = {
        "latest_plan_id": "",
        "status": "WARN",
        "workflow_stage": NO_FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN,
        "health_status": "WARN",
        "source_evidence_update_plan_id": "",
        "downstream_impact_id": "",
        "reviewer_no_hit_acceptance_id": "",
        "enrichment_id": "",
        "source_packet_id": "",
        "reviewed_no_hit_policy_comparison_id": "",
        "validator_id": "",
        "row_count": 0,
        "stock_core_row_count": 0,
        "etf_core_row_count": 0,
        "reviewer_completion_required_count": 0,
        "no_hit_acceptance_required_count": 0,
        "survivorship_rationale_required_count": 0,
        "metadata_completion_required_count": 0,
        "checklist_pass_count": 0,
        "remaining_blocked_count": 0,
        "clean_review_updates_created": False,
        "approval_applied": False,
        "report_path": "",
        "next_manual_action": "Run first-batch-reviewer-evidence-completion-plan after evidence update planning and no-hit impact artifacts exist.",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = _paths(output_dir, _hash_payload(summary))
    return FirstBatchReviewerEvidenceCompletionPlanStatusResult(
        latest_plan_id="",
        status="WARN",
        workflow_stage=NO_FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN,
        health_status="WARN",
        source_evidence_update_plan_id="",
        downstream_impact_id="",
        reviewer_no_hit_acceptance_id="",
        enrichment_id="",
        source_packet_id="",
        reviewed_no_hit_policy_comparison_id="",
        validator_id="",
        row_count=0,
        stock_core_row_count=0,
        etf_core_row_count=0,
        reviewer_completion_required_count=0,
        no_hit_acceptance_required_count=0,
        survivorship_rationale_required_count=0,
        metadata_completion_required_count=0,
        checklist_pass_count=0,
        remaining_blocked_count=0,
        clean_review_updates_created=False,
        approval_applied=False,
        report_path="",
        next_manual_action=summary["next_manual_action"],
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[f"No first-batch reviewer evidence completion plan artifacts found under {root}."],
        audit_metadata=_safe_audit_metadata(root),
    )


def _write(result: FirstBatchReviewerEvidenceCompletionPlanStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# First-Batch Reviewer Evidence Completion Plan Status",
                "",
                f"- status: {result.status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_plan_id: {result.latest_plan_id}",
                f"- health_status: {result.health_status}",
                f"- row_count: {result.row_count}",
                f"- reviewer_completion_required_count: {result.reviewer_completion_required_count}",
                f"- no_hit_acceptance_required_count: {result.no_hit_acceptance_required_count}",
                f"- survivorship_rationale_required_count: {result.survivorship_rationale_required_count}",
                f"- metadata_completion_required_count: {result.metadata_completion_required_count}",
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
        "latest_plan_id": result.latest_plan_id,
        "row_count": result.row_count,
        "reviewer_completion_required_count": result.reviewer_completion_required_count,
        "no_hit_acceptance_required_count": result.no_hit_acceptance_required_count,
        "survivorship_rationale_required_count": result.survivorship_rationale_required_count,
        "metadata_completion_required_count": result.metadata_completion_required_count,
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
        "status_csv": artifact_dir / "first_batch_reviewer_evidence_completion_plan_status.csv",
        "status_report": artifact_dir / "first_batch_reviewer_evidence_completion_plan_status_report.md",
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
