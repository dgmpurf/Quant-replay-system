"""Status view for reviewed replacement worklist plan artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.reviewed_replacement_worklist_plan_health import check_reviewed_replacement_worklist_plan_health
from quant_replay_system.reviewed_replacement_worklist_plan_index import build_reviewed_replacement_worklist_plan_index


NO_REVIEWED_REPLACEMENT_WORKLIST_PLAN = "NO_REVIEWED_REPLACEMENT_WORKLIST_PLAN"
REVIEWED_REPLACEMENT_WORKLIST_PLAN_READY = "REVIEWED_REPLACEMENT_WORKLIST_PLAN_READY"
REVIEWED_REPLACEMENT_WORKLIST_PLAN_HEALTH_WARN = "REVIEWED_REPLACEMENT_WORKLIST_PLAN_HEALTH_WARN"
REVIEWED_REPLACEMENT_WORKLIST_PLAN_FAILED = "REVIEWED_REPLACEMENT_WORKLIST_PLAN_FAILED"

SUMMARY_COLUMNS = [
    "latest_replacement_plan_id",
    "status",
    "workflow_stage",
    "health_status",
    "source_split_plan_id",
    "row_count",
    "stock_core_row_count",
    "etf_core_row_count",
    "mixed_demo_core_row_count",
    "profile_conflict_count",
    "active_worklist_mutated",
    "report_path",
    "next_manual_action",
]


@dataclass(frozen=True)
class ReviewedReplacementWorklistPlanStatusResult:
    latest_replacement_plan_id: str
    status: str
    workflow_stage: str
    health_status: str
    source_split_plan_id: str
    row_count: int
    stock_core_row_count: int
    etf_core_row_count: int
    mixed_demo_core_row_count: int
    profile_conflict_count: int
    active_worklist_mutated: bool
    report_path: str
    next_manual_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_reviewed_replacement_worklist_plan_status(
    *,
    root: str | Path = "outputs/reports/reviewed_replacement_worklist_plan",
    output_dir: str | Path = "outputs/reports/reviewed_replacement_worklist_plan/status",
) -> ReviewedReplacementWorklistPlanStatusResult:
    index = build_reviewed_replacement_worklist_plan_index(root=root)
    health = check_reviewed_replacement_worklist_plan_health(root=root)
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root)
    else:
        latest = index.index_frame.sort_values(["created_at", "replacement_plan_id"]).iloc[-1].to_dict()
        health_status = health.status
        if health_status == "FAIL":
            status = "FAIL"
            stage = REVIEWED_REPLACEMENT_WORKLIST_PLAN_FAILED
            next_action = "Repair reviewed replacement worklist plan artifacts before using replacement templates."
        elif health_status == "WARN":
            status = "WARN"
            stage = REVIEWED_REPLACEMENT_WORKLIST_PLAN_HEALTH_WARN
            next_action = "Review replacement worklist plan health warnings before replacement-template review."
        else:
            status = "PASS"
            stage = REVIEWED_REPLACEMENT_WORKLIST_PLAN_READY
            next_action = "Review replacement worklist templates manually; do not mutate the active legacy worklist."
        result = _result_from_latest(latest, status, stage, health_status, next_action, output_dir, root)
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
) -> ReviewedReplacementWorklistPlanStatusResult:
    summary = {
        "latest_replacement_plan_id": _text(latest.get("replacement_plan_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health_status,
        "source_split_plan_id": _text(latest.get("source_split_plan_id")),
        "row_count": _to_int(latest.get("row_count")),
        "stock_core_row_count": _to_int(latest.get("stock_core_row_count")),
        "etf_core_row_count": _to_int(latest.get("etf_core_row_count")),
        "mixed_demo_core_row_count": _to_int(latest.get("mixed_demo_core_row_count")),
        "profile_conflict_count": _to_int(latest.get("profile_conflict_count")),
        "active_worklist_mutated": _to_bool(latest.get("active_worklist_mutated")),
        "report_path": _text(latest.get("report_path")),
        "next_manual_action": next_action,
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = _paths(output_dir, _hash_payload(summary))
    return ReviewedReplacementWorklistPlanStatusResult(
        latest_replacement_plan_id=summary["latest_replacement_plan_id"],
        status=status,
        workflow_stage=stage,
        health_status=health_status,
        source_split_plan_id=summary["source_split_plan_id"],
        row_count=summary["row_count"],
        stock_core_row_count=summary["stock_core_row_count"],
        etf_core_row_count=summary["etf_core_row_count"],
        mixed_demo_core_row_count=summary["mixed_demo_core_row_count"],
        profile_conflict_count=summary["profile_conflict_count"],
        active_worklist_mutated=summary["active_worklist_mutated"],
        report_path=summary["report_path"],
        next_manual_action=next_action,
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if status == "PASS" else [f"Reviewed replacement worklist plan health is {health_status}."],
        audit_metadata=_safe_audit_metadata(root),
    )


def _no_artifact_result(output_dir: str | Path, root: str | Path) -> ReviewedReplacementWorklistPlanStatusResult:
    summary = {
        "latest_replacement_plan_id": "",
        "status": "WARN",
        "workflow_stage": NO_REVIEWED_REPLACEMENT_WORKLIST_PLAN,
        "health_status": "WARN",
        "source_split_plan_id": "",
        "row_count": 0,
        "stock_core_row_count": 0,
        "etf_core_row_count": 0,
        "mixed_demo_core_row_count": 0,
        "profile_conflict_count": 0,
        "active_worklist_mutated": False,
        "report_path": "",
        "next_manual_action": "Run reviewed-replacement-worklist-plan after reviewing split-worklist plan artifacts.",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = _paths(output_dir, _hash_payload(summary))
    return ReviewedReplacementWorklistPlanStatusResult(
        latest_replacement_plan_id="",
        status="WARN",
        workflow_stage=NO_REVIEWED_REPLACEMENT_WORKLIST_PLAN,
        health_status="WARN",
        source_split_plan_id="",
        row_count=0,
        stock_core_row_count=0,
        etf_core_row_count=0,
        mixed_demo_core_row_count=0,
        profile_conflict_count=0,
        active_worklist_mutated=False,
        report_path="",
        next_manual_action=summary["next_manual_action"],
        summary_frame=frame,
        artifact_paths=paths,
        warnings=["No reviewed replacement worklist plan artifacts found."],
        audit_metadata=_safe_audit_metadata(root),
    )


def _paths(output_dir: str | Path, status_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / status_id
    return {
        "artifact_dir": artifact_dir,
        "reviewed_replacement_worklist_plan_status_csv": artifact_dir / "reviewed_replacement_worklist_plan_status.csv",
        "reviewed_replacement_worklist_plan_status_report": artifact_dir / "reviewed_replacement_worklist_plan_status_report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def _write(result: ReviewedReplacementWorklistPlanStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["reviewed_replacement_worklist_plan_status_csv"], index=False)
    paths["reviewed_replacement_worklist_plan_status_report"].write_text(
        "\n".join(
            [
                "# Reviewed Replacement Worklist Plan Status",
                "",
                f"- status: {result.status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_replacement_plan_id: {result.latest_replacement_plan_id}",
                f"- row_count: {result.row_count}",
                f"- stock_core_row_count: {result.stock_core_row_count}",
                f"- etf_core_row_count: {result.etf_core_row_count}",
                f"- mixed_demo_core_row_count: {result.mixed_demo_core_row_count}",
                f"- next_manual_action: {result.next_manual_action}",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "status_id": paths["artifact_dir"].name,
        **result.summary_frame.iloc[0].to_dict(),
        "warnings": result.warnings,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")


def _safe_audit_metadata(root: str | Path) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "active_worklist_mutated": False,
        "no_approval_applied": True,
        "no_rejection_applied": True,
        "no_universe_export": True,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "current_candidates_executed": False,
        "snapshot_manifest_built": False,
        "forward_returns_computed": False,
        "cache_mutated": False,
        "network_api_called": False,
        "external_api_called": False,
        "llm_api_called": False,
        "broker_api_invoked": False,
        "message_sent": False,
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
