"""Status summary for report-only Operational Global APPROVED_FOR_PAPER planning artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.operational_global_approved_for_paper import (
    DOWNSTREAM_FALSE_FIELDS,
    NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT,
    OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED,
    READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW,
)
from quant_replay_system.operational_global_approved_for_paper_health import (
    check_operational_global_approved_for_paper_health,
)
from quant_replay_system.operational_global_approved_for_paper_index import (
    CORE_FALSE_FIELDS,
    DEFAULT_ROOT,
    _frame_to_markdown,
    _text,
    _to_bool,
    _to_int,
    build_operational_global_approved_for_paper_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "status"
NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_ARTIFACT_FOUND = "NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_ARTIFACT_FOUND"
OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_ARTIFACT_HEALTH_FAILED = (
    "OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_ARTIFACT_HEALTH_FAILED"
)

SUMMARY_COLUMNS = [
    "latest_operational_global_approved_for_paper_id",
    "status",
    "health_status",
    "workflow_stage",
    "ready_for_operational_global_approved_for_paper_review",
    "operational_global_approved_for_paper_executed",
    "operational_global_approved_for_paper_planning_artifacts_created",
    *CORE_FALSE_FIELDS,
    *DOWNSTREAM_FALSE_FIELDS,
    "blocker_count",
    "warning_count",
    "report_path",
    "safety_statement",
    "next_action",
]


@dataclass(frozen=True)
class OperationalGlobalApprovedForPaperStatusResult:
    latest_operational_global_approved_for_paper_id: str
    status: str
    health_status: str
    workflow_stage: str
    ready_for_operational_global_approved_for_paper_review: bool
    operational_global_approved_for_paper_executed: bool
    operational_global_approved_for_paper_planning_artifacts_created: bool
    operational_global_approved_for_paper_granted: bool
    global_approved_for_paper: bool
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


def run_operational_global_approved_for_paper_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> OperationalGlobalApprovedForPaperStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_operational_global_approved_for_paper_index(root=root, output_dir=sibling_root / "index")
    health = check_operational_global_approved_for_paper_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        frame = index.index_frame.copy()
        frame["_status_priority"] = frame["status"].map(_status_priority)
        latest = frame.sort_values(["created_at", "_status_priority", "operational_global_approved_for_paper_id"]).iloc[-1].to_dict()
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
) -> OperationalGlobalApprovedForPaperStatusResult:
    status = _text(latest.get("status"))
    stage = (
        OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_ARTIFACT_HEALTH_FAILED
        if health_status == "FAIL"
        else _text(latest.get("workflow_stage")) or status
    )
    summary = {
        "latest_operational_global_approved_for_paper_id": _text(
            latest.get("operational_global_approved_for_paper_id")
        ),
        "status": status,
        "health_status": health_status,
        "workflow_stage": stage,
        "ready_for_operational_global_approved_for_paper_review": _to_bool(
            latest.get("ready_for_operational_global_approved_for_paper_review")
        ),
        "operational_global_approved_for_paper_executed": _to_bool(
            latest.get("operational_global_approved_for_paper_executed")
        ),
        "operational_global_approved_for_paper_planning_artifacts_created": _to_bool(
            latest.get("operational_global_approved_for_paper_planning_artifacts_created")
        ),
        **{field: _to_bool(latest.get(field)) for field in CORE_FALSE_FIELDS},
        **{field: _to_bool(latest.get(field)) for field in DOWNSTREAM_FALSE_FIELDS},
        "blocker_count": max(_to_int(latest.get("blocker_count")), error_count),
        "warning_count": max(_to_int(latest.get("warning_count")), warning_count),
        "report_path": _existing_path_text(latest.get("operational_global_approved_for_paper_limitations_path")),
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
) -> OperationalGlobalApprovedForPaperStatusResult:
    summary = {
        "latest_operational_global_approved_for_paper_id": "",
        "status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_ARTIFACT_FOUND,
        "ready_for_operational_global_approved_for_paper_review": False,
        "operational_global_approved_for_paper_executed": False,
        "operational_global_approved_for_paper_planning_artifacts_created": False,
        **{field: False for field in CORE_FALSE_FIELDS},
        **{field: False for field in DOWNSTREAM_FALSE_FIELDS},
        "blocker_count": error_count,
        "warning_count": warning_count,
        "report_path": "",
        "safety_statement": _safety_statement(),
        "next_action": "Create or provide report-only Operational Global APPROVED_FOR_PAPER planning artifacts before checking status.",
    }
    return _result(summary, output_dir, root, [])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> OperationalGlobalApprovedForPaperStatusResult:
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "operational_global_approved_for_paper_status.csv",
        "status_report": Path(output_dir) / "operational_global_approved_for_paper_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    return OperationalGlobalApprovedForPaperStatusResult(
        summary_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata={"root": str(root), "report_only": True, "diagnostic_only": True},
        **summary,
    )


def _write(result: OperationalGlobalApprovedForPaperStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "latest_operational_global_approved_for_paper_id": result.latest_operational_global_approved_for_paper_id,
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
                "# Operational Global APPROVED_FOR_PAPER Status",
                "",
                result.safety_statement,
                "",
                _frame_to_markdown(result.summary_frame),
            ]
        ),
        encoding="utf-8",
    )


def _status_priority(status: str) -> int:
    return {
        NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT: 0,
        READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW: 1,
        OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED: 2,
    }.get(_text(status), -1)


def _existing_path_text(value: Any) -> str:
    text = _text(value)
    return text if text and Path(text).exists() else ""


def _next_action(stage: str, status: str) -> str:
    if stage == OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_ARTIFACT_HEALTH_FAILED:
        return "Fix Operational Global APPROVED_FOR_PAPER planning artifact health before any downstream visibility."
    if status == OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED:
        return "Add artifact views review or research-status integration only after confirming report-only boundaries."
    if status == READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW:
        return "Provide the exact report-only allow flag only if planning artifacts should be created."
    return "Provide a report-only Operational Global APPROVED_FOR_PAPER planning manifest before creating planning artifacts."


def _safety_statement() -> str:
    return (
        "Operational Global APPROVED_FOR_PAPER status is report-only planning context. It does not grant "
        "operational global APPROVED_FOR_PAPER, real buy-review eligibility, buy_review_allowed, strategy "
        "performance validation, current-candidates, snapshots, signal_semantics mutation, active stock_profile, "
        "promoted/production model, active thresholds, advisory predictions, active probabilities, broker/order/"
        "message/API behavior, or trading."
    )
