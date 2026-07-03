"""Status view for Reviewer Authority / Quality / Limitation artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_reviewer_authority_quality_limitation import (
    PACKAGE_PROMOTION_NONE,
    PERMISSION_REVIEW_NONE,
    QUALITY_STATUS_NONE,
    REQUIRED_FALSE_FLAGS,
    REVIEWER_AUTHORITY_NONE,
    STATUS_NO_INPUT,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_reviewer_authority_quality_limitation_health import (
    check_reviewer_authority_quality_limitation_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_reviewer_authority_quality_limitation_index import (
    DEFAULT_ROOT,
    build_reviewer_authority_quality_limitation_index,
)


NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Reviewer Authority Quality "
    "Limitation Checkpoint Planning Report-Only v0.1"
)
NO_ARTIFACT_STAGE = (
    "NO_TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_REVIEWER_AUTHORITY_"
    "QUALITY_LIMITATION"
)
STATUS_COLUMNS = [
    "latest_run_id",
    "latest_runtime_status",
    "latest_health_status",
    "latest_workflow_stage",
    "latest_artifact_path",
    "latest_report_path",
    "latest_metadata_path",
    "latest_summary_path",
    "latest_reviewer_authority_level",
    "latest_quality_status_level",
    "latest_limitation_review_level",
    "latest_permission_review_level",
    "latest_package_promotion_level",
    "latest_reviewer_metadata_present",
    "latest_reviewer_id_recorded",
    "latest_reviewer_id_preview",
    "latest_reviewer_role",
    "latest_reviewer_role_supported",
    "latest_reviewer_type",
    "latest_reviewer_attestation_present",
    "latest_reviewer_authority_scope_declared",
    "latest_reviewer_authority_validated",
    "latest_quality_status_present",
    "latest_quality_status_declared",
    "latest_quality_status_validated",
    "latest_quality_issue_count",
    "latest_quality_warning_count",
    "latest_quality_blocker_count",
    "latest_limitations_present",
    "latest_limitation_count",
    "latest_limitation_severity_max",
    "latest_limitation_categories",
    "latest_unresolved_limitation_count",
    "latest_blocking_limitation_count",
    "latest_limitations_overridden_by_reviewer",
    "latest_limitations_overridden_by_quality",
    "latest_permission_class_present",
    "latest_permission_class",
    "latest_legality_flag",
    "latest_permission_class_validated",
    "latest_restricted_use_blocked",
    "latest_private_source_blocked",
    "latest_source_hash_validated",
    "latest_revision_id_validated",
    "latest_available_time_validated",
    "latest_pit_admissibility_validated",
    "latest_source_reliability_scored",
    "reviewer_authority_validated",
    "quality_status_validated",
    "permission_class_validated",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "source_reliability_scored",
    "latest_issue_count",
    "latest_warning_count",
    *[f"latest_{field}" for field in REQUIRED_FALSE_FLAGS],
    *REQUIRED_FALSE_FLAGS,
    "report_only",
    "diagnostic_only",
    "recommended_next_task",
]


@dataclass(frozen=True)
class ReviewerAuthorityQualityLimitationStatusResult:
    latest_run_id: str
    latest_runtime_status: str
    latest_health_status: str
    latest_workflow_stage: str
    latest_artifact_path: str
    latest_report_path: str
    latest_metadata_path: str
    latest_summary_path: str
    latest_reviewer_id_preview: str
    latest_reviewer_role: str
    latest_reviewer_type: str
    latest_quality_status_declared: bool
    latest_limitation_severity_max: str
    latest_permission_class: str
    recommended_next_task: str
    summary: dict[str, Any]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def run_reviewer_authority_quality_limitation_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/status",
) -> ReviewerAuthorityQualityLimitationStatusResult:
    root_path = Path(root)
    status_dir = Path(output_dir)
    index = build_reviewer_authority_quality_limitation_index(
        root=root_path,
        output_dir=status_dir.parent / "index",
    )
    health = check_reviewer_authority_quality_limitation_health(
        root=root_path,
        output_dir=status_dir.parent / "health",
    )
    if index.rows:
        latest = sorted(index.rows, key=lambda row: str(row.get("run_id") or ""))[-1]
        summary = _summary_from_latest(latest, health.status)
    else:
        summary = _no_artifact_summary(root_path, health.status)
    paths = _paths(status_dir)
    result = ReviewerAuthorityQualityLimitationStatusResult(
        latest_run_id=str(summary["latest_run_id"]),
        latest_runtime_status=str(summary["latest_runtime_status"]),
        latest_health_status=str(summary["latest_health_status"]),
        latest_workflow_stage=str(summary["latest_workflow_stage"]),
        latest_artifact_path=str(summary["latest_artifact_path"]),
        latest_report_path=str(summary["latest_report_path"]),
        latest_metadata_path=str(summary["latest_metadata_path"]),
        latest_summary_path=str(summary["latest_summary_path"]),
        latest_reviewer_id_preview=str(summary["latest_reviewer_id_preview"]),
        latest_reviewer_role=str(summary["latest_reviewer_role"]),
        latest_reviewer_type=str(summary["latest_reviewer_type"]),
        latest_quality_status_declared=_to_bool(summary["latest_quality_status_declared"]),
        latest_limitation_severity_max=str(summary["latest_limitation_severity_max"]),
        latest_permission_class=str(summary["latest_permission_class"]),
        recommended_next_task=str(summary["recommended_next_task"]),
        summary=summary,
        artifact_paths=paths,
        warnings=[] if health.status == "PASS" else [f"Health view reported {health.status}."],
    )
    _write(result)
    return result


def _summary_from_latest(latest: dict[str, Any], health_status: str) -> dict[str, Any]:
    runtime_status = str(latest.get("runtime_status") or "")
    if health_status == "FAIL":
        runtime_status = "FAIL"
    summary: dict[str, Any] = {
        "latest_run_id": _text(latest.get("run_id")),
        "latest_runtime_status": runtime_status,
        "latest_health_status": health_status,
        "latest_workflow_stage": _text(latest.get("workflow_stage")),
        "latest_artifact_path": _text(latest.get("artifact_path")),
        "latest_report_path": _text(latest.get("report_path")),
        "latest_metadata_path": _text(latest.get("metadata_path")),
        "latest_summary_path": _text(latest.get("summary_path")),
        "latest_reviewer_authority_level": _text(latest.get("reviewer_authority_level")),
        "latest_quality_status_level": _text(latest.get("quality_status_level")),
        "latest_limitation_review_level": _text(latest.get("limitation_review_level")),
        "latest_permission_review_level": _text(latest.get("permission_review_level")),
        "latest_package_promotion_level": _text(latest.get("package_promotion_level")),
        "latest_reviewer_metadata_present": _to_bool(latest.get("reviewer_metadata_present")),
        "latest_reviewer_id_recorded": _to_bool(latest.get("reviewer_id_recorded")),
        "latest_reviewer_id_preview": _text(latest.get("reviewer_id_preview")),
        "latest_reviewer_role": _text(latest.get("reviewer_role")),
        "latest_reviewer_role_supported": _to_bool(latest.get("reviewer_role_supported")),
        "latest_reviewer_type": _text(latest.get("reviewer_type")),
        "latest_reviewer_attestation_present": _to_bool(
            latest.get("reviewer_attestation_present")
        ),
        "latest_reviewer_authority_scope_declared": _to_bool(
            latest.get("reviewer_authority_scope_declared")
        ),
        "latest_reviewer_authority_validated": _to_bool(
            latest.get("reviewer_authority_validated")
        ),
        "latest_quality_status_present": _to_bool(latest.get("quality_status_present")),
        "latest_quality_status_declared": _to_bool(latest.get("quality_status_declared")),
        "latest_quality_status_validated": _to_bool(latest.get("quality_status_validated")),
        "latest_quality_issue_count": _value(latest.get("quality_issue_count")),
        "latest_quality_warning_count": _value(latest.get("quality_warning_count")),
        "latest_quality_blocker_count": _value(latest.get("quality_blocker_count")),
        "latest_limitations_present": _to_bool(latest.get("limitations_present")),
        "latest_limitation_count": _value(latest.get("limitation_count")),
        "latest_limitation_severity_max": _text(latest.get("limitation_severity_max")),
        "latest_limitation_categories": _value(latest.get("limitation_categories")),
        "latest_unresolved_limitation_count": _value(
            latest.get("unresolved_limitation_count")
        ),
        "latest_blocking_limitation_count": _value(latest.get("blocking_limitation_count")),
        "latest_limitations_overridden_by_reviewer": _to_bool(
            latest.get("limitations_overridden_by_reviewer")
        ),
        "latest_limitations_overridden_by_quality": _to_bool(
            latest.get("limitations_overridden_by_quality")
        ),
        "latest_permission_class_present": _to_bool(latest.get("permission_class_present")),
        "latest_permission_class": _text(latest.get("permission_class")),
        "latest_legality_flag": _text(latest.get("legality_flag")),
        "latest_permission_class_validated": _to_bool(
            latest.get("permission_class_validated")
        ),
        "latest_restricted_use_blocked": _to_bool(latest.get("restricted_use_blocked")),
        "latest_private_source_blocked": _to_bool(latest.get("private_source_blocked")),
        "latest_source_hash_validated": _to_bool(latest.get("source_hash_validated")),
        "latest_revision_id_validated": _to_bool(latest.get("revision_id_validated")),
        "latest_available_time_validated": _to_bool(latest.get("available_time_validated")),
        "latest_pit_admissibility_validated": _to_bool(
            latest.get("pit_admissibility_validated")
        ),
        "latest_source_reliability_scored": _to_bool(latest.get("source_reliability_scored")),
        "reviewer_authority_validated": _to_bool(latest.get("reviewer_authority_validated")),
        "quality_status_validated": _to_bool(latest.get("quality_status_validated")),
        "permission_class_validated": _to_bool(latest.get("permission_class_validated")),
        "source_hash_validated": _to_bool(latest.get("source_hash_validated")),
        "revision_id_validated": _to_bool(latest.get("revision_id_validated")),
        "available_time_validated": _to_bool(latest.get("available_time_validated")),
        "pit_admissibility_validated": _to_bool(latest.get("pit_admissibility_validated")),
        "source_reliability_scored": _to_bool(latest.get("source_reliability_scored")),
        "latest_issue_count": _value(latest.get("issue_count")),
        "latest_warning_count": _value(latest.get("warning_count")),
        "report_only": True,
        "diagnostic_only": True,
        "recommended_next_task": NEXT_TASK,
    }
    for field in REQUIRED_FALSE_FLAGS:
        value = _to_bool(latest.get(field))
        summary[f"latest_{field}"] = value
        summary[field] = value
    return _finalize_summary(summary)


def _no_artifact_summary(root: Path, health_status: str) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "latest_run_id": "",
        "latest_runtime_status": STATUS_NO_INPUT,
        "latest_health_status": health_status,
        "latest_workflow_stage": NO_ARTIFACT_STAGE,
        "latest_artifact_path": str(root),
        "latest_report_path": "",
        "latest_metadata_path": "",
        "latest_summary_path": "",
        "latest_reviewer_authority_level": REVIEWER_AUTHORITY_NONE,
        "latest_quality_status_level": QUALITY_STATUS_NONE,
        "latest_limitation_review_level": "",
        "latest_permission_review_level": PERMISSION_REVIEW_NONE,
        "latest_package_promotion_level": PACKAGE_PROMOTION_NONE,
        "latest_reviewer_metadata_present": False,
        "latest_reviewer_id_recorded": False,
        "latest_reviewer_id_preview": "",
        "latest_reviewer_role": "",
        "latest_reviewer_role_supported": False,
        "latest_reviewer_type": "",
        "latest_reviewer_attestation_present": False,
        "latest_reviewer_authority_scope_declared": False,
        "latest_reviewer_authority_validated": False,
        "latest_quality_status_present": False,
        "latest_quality_status_declared": False,
        "latest_quality_status_validated": False,
        "latest_quality_issue_count": 0,
        "latest_quality_warning_count": 0,
        "latest_quality_blocker_count": 0,
        "latest_limitations_present": False,
        "latest_limitation_count": 0,
        "latest_limitation_severity_max": "",
        "latest_limitation_categories": [],
        "latest_unresolved_limitation_count": 0,
        "latest_blocking_limitation_count": 0,
        "latest_limitations_overridden_by_reviewer": False,
        "latest_limitations_overridden_by_quality": False,
        "latest_permission_class_present": False,
        "latest_permission_class": "",
        "latest_legality_flag": "",
        "latest_permission_class_validated": False,
        "latest_restricted_use_blocked": False,
        "latest_private_source_blocked": False,
        "latest_source_hash_validated": False,
        "latest_revision_id_validated": False,
        "latest_available_time_validated": False,
        "latest_pit_admissibility_validated": False,
        "latest_source_reliability_scored": False,
        "reviewer_authority_validated": False,
        "quality_status_validated": False,
        "permission_class_validated": False,
        "source_hash_validated": False,
        "revision_id_validated": False,
        "available_time_validated": False,
        "pit_admissibility_validated": False,
        "source_reliability_scored": False,
        "latest_issue_count": 0,
        "latest_warning_count": 0,
        "report_only": True,
        "diagnostic_only": True,
        "recommended_next_task": NEXT_TASK,
    }
    for field in REQUIRED_FALSE_FLAGS:
        summary[f"latest_{field}"] = False
        summary[field] = False
    return _finalize_summary(summary)


def _finalize_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {column: summary.get(column, "") for column in STATUS_COLUMNS}


def _paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {
        "artifact_dir": root,
        "status_csv": root / "reviewer_quality_limitation_status.csv",
        "status_md": root / "reviewer_quality_limitation_status.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: ReviewerAuthorityQualityLimitationStatusResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_rows(result.artifact_paths["status_csv"], STATUS_COLUMNS, [result.summary])
    _write_text(result.artifact_paths["status_md"], _status_markdown(result))
    _write_json(
        result.artifact_paths["metadata_json"],
        {
            "latest_run_id": result.latest_run_id,
            "latest_runtime_status": result.latest_runtime_status,
            "latest_health_status": result.latest_health_status,
            "latest_workflow_stage": result.latest_workflow_stage,
            "recommended_next_task": result.recommended_next_task,
            "summary": result.summary,
        },
    )


def _status_markdown(result: ReviewerAuthorityQualityLimitationStatusResult) -> str:
    lines = [
        "# Reviewer Authority Quality Limitation Status",
        "",
        f"- Latest run id: `{result.latest_run_id}`",
        f"- Latest status: `{result.latest_runtime_status}`",
        f"- Health: `{result.latest_health_status}`",
        f"- Reviewer preview: `{result.latest_reviewer_id_preview}`",
        f"- Reviewer role: `{result.latest_reviewer_role}`",
        f"- Quality declared: `{str(result.latest_quality_status_declared).lower()}`",
        f"- Limitation severity: `{result.latest_limitation_severity_max}`",
        f"- Permission class: `{result.latest_permission_class}`",
        f"- Recommended next task: `{result.recommended_next_task}`",
        "",
        "This view is report-only and diagnostic-only. It summarizes generated core artifacts",
        "without reopening reviewer metadata, consuming CSV rows, validating authority,",
        "promoting package quality, creating replay input, allowing buy review, or allowing trading.",
    ]
    return "\n".join(lines) + "\n"


def _write_rows(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(text)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _value(value: Any) -> Any:
    if value is None:
        return ""
    return value


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)
