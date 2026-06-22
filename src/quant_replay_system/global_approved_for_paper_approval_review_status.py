"""Status summary for report-only Global APPROVED_FOR_PAPER approval-review artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.global_approved_for_paper_approval_review import (
    DOWNSTREAM_FALSE_FIELDS,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED,
    NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_INPUT,
    READY_FOR_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW,
)
from quant_replay_system.global_approved_for_paper_approval_review_health import (
    check_global_approved_for_paper_approval_review_health,
)
from quant_replay_system.global_approved_for_paper_approval_review_index import (
    DEFAULT_ROOT,
    _text,
    _to_bool,
    _to_int,
    build_global_approved_for_paper_approval_review_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"
NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_ARTIFACT_FOUND = (
    "NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_ARTIFACT_FOUND"
)
GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_ARTIFACT_HEALTH_FAILED = (
    "GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_ARTIFACT_HEALTH_FAILED"
)

SUMMARY_COLUMNS = [
    "latest_global_approved_for_paper_approval_review_id",
    "status",
    "health_status",
    "workflow_stage",
    "ready_for_global_approved_for_paper_approval_review",
    "global_approved_for_paper_approval_review_executed",
    "global_approved_for_paper_approval_review_report_only_artifacts_created",
    "scoped_global_approved_for_paper_approval_review",
    "global_approved_for_paper",
    "global_approved_for_paper_scope",
    "source_approved_for_paper_phase1_run_id",
    "source_approved_for_paper_phase1_status",
    "source_approved_for_paper_phase1_health_status",
    "source_paper_workflow_phase1_run_id",
    "source_model_workflow_run_id",
    *DOWNSTREAM_FALSE_FIELDS,
    "blocker_count",
    "warning_count",
    "report_path",
    "safety_statement",
    "next_action",
]


@dataclass(frozen=True)
class GlobalApprovedForPaperApprovalReviewStatusResult:
    latest_global_approved_for_paper_approval_review_id: str
    status: str
    health_status: str
    workflow_stage: str
    ready_for_global_approved_for_paper_approval_review: bool
    global_approved_for_paper_approval_review_executed: bool
    global_approved_for_paper_approval_review_report_only_artifacts_created: bool
    scoped_global_approved_for_paper_approval_review: bool
    global_approved_for_paper: bool
    global_approved_for_paper_scope: str
    source_approved_for_paper_phase1_run_id: str
    source_approved_for_paper_phase1_status: str
    source_approved_for_paper_phase1_health_status: str
    source_paper_workflow_phase1_run_id: str
    source_model_workflow_run_id: str
    real_buy_review_eligible: bool
    buy_review_allowed: bool
    strategy_performance_validated: bool
    trading_allowed: bool
    current_candidates_run: bool
    snapshot_built: bool
    signal_semantics_changed: bool
    active_stock_profile_created: bool
    promoted_model_created: bool
    production_model_created: bool
    active_thresholds_created: bool
    advisory_predictions_created: bool
    active_probabilities_created: bool
    broker_api_called: bool
    order_placed: bool
    message_sent: bool
    llm_api_called: bool
    external_api_called: bool
    cache_mutated: bool
    data_raw_written: bool
    data_processed_written: bool
    data_cache_written: bool
    blocker_count: int
    warning_count: int
    report_path: str
    safety_statement: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_global_approved_for_paper_approval_review_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> GlobalApprovedForPaperApprovalReviewStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_global_approved_for_paper_approval_review_index(root=root, output_dir=sibling_root / "index")
    health = check_global_approved_for_paper_approval_review_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        frame = index.index_frame.copy()
        frame["_status_priority"] = frame["status"].map(_status_priority)
        latest = frame.sort_values(["created_at", "_status_priority", "global_approved_for_paper_approval_review_id"]).iloc[-1].to_dict()
        result = _result_from_latest(latest, health.status, health.error_count, health.warning_count, output_dir, root)
    _write(result)
    return result


def _result_from_latest(
    latest: dict[str, Any],
    health_status: str,
    error_count: int,
    warning_count: int,
    output_dir: str | Path,
    root: str | Path,
) -> GlobalApprovedForPaperApprovalReviewStatusResult:
    status = _text(latest.get("status"))
    stage = (
        GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_ARTIFACT_HEALTH_FAILED
        if health_status == "FAIL"
        else _text(latest.get("workflow_stage")) or status
    )
    summary = {
        "latest_global_approved_for_paper_approval_review_id": _text(
            latest.get("global_approved_for_paper_approval_review_id")
        ),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "ready_for_global_approved_for_paper_approval_review": _to_bool(
            latest.get("ready_for_global_approved_for_paper_approval_review")
        ),
        "global_approved_for_paper_approval_review_executed": _to_bool(
            latest.get("global_approved_for_paper_approval_review_executed")
        ),
        "global_approved_for_paper_approval_review_report_only_artifacts_created": _to_bool(
            latest.get("global_approved_for_paper_approval_review_report_only_artifacts_created")
        ),
        "scoped_global_approved_for_paper_approval_review": _to_bool(
            latest.get("scoped_global_approved_for_paper_approval_review")
        ),
        "global_approved_for_paper": _to_bool(latest.get("global_approved_for_paper")),
        "global_approved_for_paper_scope": _text(latest.get("global_approved_for_paper_scope")),
        "source_approved_for_paper_phase1_run_id": _text(latest.get("source_approved_for_paper_phase1_run_id")),
        "source_approved_for_paper_phase1_status": _text(latest.get("source_approved_for_paper_phase1_status")),
        "source_approved_for_paper_phase1_health_status": _text(
            latest.get("source_approved_for_paper_phase1_health_status")
        ),
        "source_paper_workflow_phase1_run_id": _text(latest.get("source_paper_workflow_phase1_run_id")),
        "source_model_workflow_run_id": _text(latest.get("source_model_workflow_run_id")),
        **{field: _to_bool(latest.get(field)) for field in DOWNSTREAM_FALSE_FIELDS},
        "blocker_count": max(_to_int(latest.get("blocker_count")), error_count),
        "warning_count": max(_to_int(latest.get("warning_count")), warning_count),
        "report_path": _existing_path_text(latest.get("global_approved_for_paper_limitations_path")),
        "safety_statement": _safety_statement(),
        "next_action": _next_action(stage, status),
    }
    return _result(summary, output_dir, root, [])


def _no_artifact_result(
    output_dir: str | Path,
    root: str | Path,
    health_status: str,
    error_count: int,
    warning_count: int,
) -> GlobalApprovedForPaperApprovalReviewStatusResult:
    summary = {
        "latest_global_approved_for_paper_approval_review_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_ARTIFACT_FOUND,
        "ready_for_global_approved_for_paper_approval_review": False,
        "global_approved_for_paper_approval_review_executed": False,
        "global_approved_for_paper_approval_review_report_only_artifacts_created": False,
        "scoped_global_approved_for_paper_approval_review": False,
        "global_approved_for_paper": False,
        "global_approved_for_paper_scope": "",
        "source_approved_for_paper_phase1_run_id": "",
        "source_approved_for_paper_phase1_status": "",
        "source_approved_for_paper_phase1_health_status": "",
        "source_paper_workflow_phase1_run_id": "",
        "source_model_workflow_run_id": "",
        **{field: False for field in DOWNSTREAM_FALSE_FIELDS},
        "blocker_count": max(error_count, 1),
        "warning_count": warning_count,
        "report_path": "",
        "safety_statement": _safety_statement(),
        "next_action": "Create or provide report-only Global APPROVED_FOR_PAPER approval-review artifacts before checking status.",
    }
    return _result(summary, output_dir, root, [])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> GlobalApprovedForPaperApprovalReviewStatusResult:
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "global_approved_for_paper_approval_review_status.csv",
        "status_report": Path(output_dir) / "global_approved_for_paper_approval_review_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    return GlobalApprovedForPaperApprovalReviewStatusResult(
        summary_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata={"root": str(root), "report_only": True, "diagnostic_only": True},
        **summary,
    )


def _write(result: GlobalApprovedForPaperApprovalReviewStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "latest_global_approved_for_paper_approval_review_id": result.latest_global_approved_for_paper_approval_review_id,
                "status": result.status,
                "health_status": result.health_status,
                "workflow_stage": result.workflow_stage,
                "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
                **result.audit_metadata,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Global APPROVED_FOR_PAPER Approval Review Status",
                "",
                result.safety_statement,
                "",
                f"- latest_global_approved_for_paper_approval_review_id: {result.latest_global_approved_for_paper_approval_review_id}",
                f"- status: {result.status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                "f- global_approved_for_paper_approval_review_report_only_artifacts_created: "
                f"{result.global_approved_for_paper_approval_review_report_only_artifacts_created}",
                f"- global_approved_for_paper: {result.global_approved_for_paper}",
                f"- next_action: {result.next_action}",
                "",
                result.summary_frame.to_markdown(index=False),
            ]
        ),
        encoding="utf-8",
    )


def _safety_statement() -> str:
    return (
        "Global APPROVED_FOR_PAPER approval-review status is report-only governance context only. "
        "It does not create global APPROVED_FOR_PAPER as an operational state, real buy-review eligibility, "
        "buy_review_allowed, strategy performance validation, current-candidates integration, snapshots, "
        "signal_semantics mutation, active stock_profile, promoted/production models, active thresholds, "
        "advisory predictions, active probabilities, broker/order/message/API behavior, or trading."
    )


def _next_action(stage: str, status: str) -> str:
    if stage == GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_ARTIFACT_HEALTH_FAILED:
        return "Resolve Global APPROVED_FOR_PAPER approval-review artifact health failures before any future integration."
    if status == GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED:
        return "Research-status integration and checkpoint can be considered only after these report-only views remain stable."
    if status == READY_FOR_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW:
        return "Rerun global-approved-for-paper-approval-review with explicit allow only if exact approval remains valid."
    if status == NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_INPUT:
        return "Provide exact approval and complete upstream report-only lineage before Global APPROVED_FOR_PAPER approval review."
    return "Resolve blocked Global APPROVED_FOR_PAPER approval-review gates before rerun."


def _status_priority(status: str) -> int:
    if status == GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED:
        return 30
    if status == READY_FOR_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW:
        return 20
    if status == NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_INPUT:
        return 10
    return 0


def _existing_path_text(value: Any) -> str:
    text = _text(value)
    return text if text and Path(text).exists() else ""
