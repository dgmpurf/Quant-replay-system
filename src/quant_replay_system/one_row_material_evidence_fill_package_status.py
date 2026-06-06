"""Status view for one-row material evidence fill package artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.one_row_material_evidence_fill_package_health import (
    check_one_row_material_evidence_fill_package_health,
)
from quant_replay_system.one_row_material_evidence_fill_package_index import (
    build_one_row_material_evidence_fill_package_index,
)


NO_ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE = "NO_ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE"
ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE_REMAINS_BLOCKED = (
    "ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE_REMAINS_BLOCKED"
)
ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE_CONTEXT_DRAFTED = (
    "ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE_CONTEXT_DRAFTED"
)
ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE_FAILED = "ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE_FAILED"

SUMMARY_COLUMNS = [
    "latest_package_id",
    "status",
    "workflow_stage",
    "health_status",
    "target_signal_date",
    "target_symbol",
    "target_universe_name",
    "package_row_count",
    "context_field_drafted_count",
    "material_blocker_closed_count",
    "checklist_pass_candidate_count",
    "remaining_blocked_count",
    "clean_review_updates_created",
    "approval_applied",
    "report_path",
    "next_manual_action",
]


@dataclass(frozen=True)
class OneRowMaterialEvidenceFillPackageStatusResult:
    latest_package_id: str
    status: str
    workflow_stage: str
    health_status: str
    target_signal_date: str
    target_symbol: str
    target_universe_name: str
    package_row_count: int
    context_field_drafted_count: int
    material_blocker_closed_count: int
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


def run_one_row_material_evidence_fill_package_status(
    *,
    root: str | Path = "outputs/reports/one_row_material_evidence_fill_package",
    output_dir: str | Path = "outputs/reports/one_row_material_evidence_fill_package/status",
) -> OneRowMaterialEvidenceFillPackageStatusResult:
    index = build_one_row_material_evidence_fill_package_index(root=root)
    health = check_one_row_material_evidence_fill_package_health(root=root)
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root)
    else:
        latest = index.index_frame.sort_values(["created_at", "package_id"]).iloc[-1].to_dict()
        if health.status == "FAIL":
            status = "FAIL"
            stage = ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE_FAILED
            next_action = "Repair one-row material evidence fill package artifacts before using them as reviewer context."
        elif _to_int(latest.get("context_field_drafted_count")) > 0:
            status = "WARN"
            stage = ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE_CONTEXT_DRAFTED
            next_action = "Review drafted context fields; material PIT blockers remain and no approval has been applied."
        else:
            status = "WARN"
            stage = ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE_REMAINS_BLOCKED
            next_action = "Create context field drafts or gather approval-grade PIT evidence in a later explicit workflow."
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
) -> OneRowMaterialEvidenceFillPackageStatusResult:
    summary = {
        "latest_package_id": _text(latest.get("package_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health_status,
        "target_signal_date": _text(latest.get("target_signal_date")),
        "target_symbol": _text(latest.get("target_symbol")),
        "target_universe_name": _text(latest.get("target_universe_name")),
        "package_row_count": _to_int(latest.get("package_row_count")),
        "context_field_drafted_count": _to_int(latest.get("context_field_drafted_count")),
        "material_blocker_closed_count": _to_int(latest.get("material_blocker_closed_count")),
        "checklist_pass_candidate_count": _to_int(latest.get("checklist_pass_candidate_count")),
        "remaining_blocked_count": _to_int(latest.get("remaining_blocked_count")),
        "clean_review_updates_created": _to_bool(latest.get("clean_review_updates_created")),
        "approval_applied": _to_bool(latest.get("approval_applied")),
        "report_path": _text(latest.get("report_path")),
        "next_manual_action": next_action,
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = _paths(output_dir, _hash_payload(summary))
    return OneRowMaterialEvidenceFillPackageStatusResult(
        latest_package_id=summary["latest_package_id"],
        status=status,
        workflow_stage=stage,
        health_status=health_status,
        target_signal_date=summary["target_signal_date"],
        target_symbol=summary["target_symbol"],
        target_universe_name=summary["target_universe_name"],
        package_row_count=summary["package_row_count"],
        context_field_drafted_count=summary["context_field_drafted_count"],
        material_blocker_closed_count=summary["material_blocker_closed_count"],
        checklist_pass_candidate_count=summary["checklist_pass_candidate_count"],
        remaining_blocked_count=summary["remaining_blocked_count"],
        clean_review_updates_created=summary["clean_review_updates_created"],
        approval_applied=summary["approval_applied"],
        report_path=summary["report_path"],
        next_manual_action=next_action,
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health_status == "PASS" else [f"One-row package health is {health_status}."],
        audit_metadata=_safe_audit_metadata(root),
    )


def _no_artifact_result(output_dir: str | Path, root: str | Path) -> OneRowMaterialEvidenceFillPackageStatusResult:
    summary = {
        "latest_package_id": "",
        "status": "WARN",
        "workflow_stage": NO_ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE,
        "health_status": "WARN",
        "target_signal_date": "",
        "target_symbol": "",
        "target_universe_name": "",
        "package_row_count": 0,
        "context_field_drafted_count": 0,
        "material_blocker_closed_count": 0,
        "checklist_pass_candidate_count": 0,
        "remaining_blocked_count": 0,
        "clean_review_updates_created": False,
        "approval_applied": False,
        "report_path": "",
        "next_manual_action": "Run one-row-material-evidence-fill-package after reviewer material guidance is available.",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    paths = _paths(output_dir, _hash_payload(summary))
    return OneRowMaterialEvidenceFillPackageStatusResult(
        latest_package_id="",
        status="WARN",
        workflow_stage=NO_ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE,
        health_status="WARN",
        target_signal_date="",
        target_symbol="",
        target_universe_name="",
        package_row_count=0,
        context_field_drafted_count=0,
        material_blocker_closed_count=0,
        checklist_pass_candidate_count=0,
        remaining_blocked_count=0,
        clean_review_updates_created=False,
        approval_applied=False,
        report_path="",
        next_manual_action=summary["next_manual_action"],
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[f"No one-row material evidence fill package artifacts found under {root}."],
        audit_metadata=_safe_audit_metadata(root),
    )


def _write(result: OneRowMaterialEvidenceFillPackageStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# One-Row Material Evidence Fill Package Status",
                "",
                f"- status: {result.status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_package_id: {result.latest_package_id}",
                f"- health_status: {result.health_status}",
                f"- target_signal_date: {result.target_signal_date}",
                f"- target_symbol: {result.target_symbol}",
                f"- target_universe_name: {result.target_universe_name}",
                f"- package_row_count: {result.package_row_count}",
                f"- context_field_drafted_count: {result.context_field_drafted_count}",
                f"- material_blocker_closed_count: {result.material_blocker_closed_count}",
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
        "latest_package_id": result.latest_package_id,
        "target_signal_date": result.target_signal_date,
        "target_symbol": result.target_symbol,
        "target_universe_name": result.target_universe_name,
        "package_row_count": result.package_row_count,
        "context_field_drafted_count": result.context_field_drafted_count,
        "material_blocker_closed_count": result.material_blocker_closed_count,
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
        "status_csv": artifact_dir / "one_row_material_evidence_fill_package_status.csv",
        "status_report": artifact_dir / "one_row_material_evidence_fill_package_status_report.md",
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
