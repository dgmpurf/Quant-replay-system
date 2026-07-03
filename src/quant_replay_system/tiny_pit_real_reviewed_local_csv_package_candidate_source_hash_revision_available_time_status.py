"""Status view for Source Hash / Revision ID / Available-Time artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time import (
    AVAILABLE_TIME_VALIDATION_NONE,
    PIT_ADMISSIBILITY_NONE,
    REQUIRED_FALSE_FLAGS,
    REVISION_ID_VALIDATION_NONE,
    SOURCE_HASH_VALIDATION_NONE,
    STATUS_NO_INPUT,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time_health import (
    check_source_hash_revision_available_time_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time_index import (
    DEFAULT_ROOT,
    build_source_hash_revision_available_time_index,
)


NO_ARTIFACT_STAGE = (
    "NO_TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_"
    "SOURCE_HASH_REVISION_AVAILABLE_TIME"
)
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Hash Revision "
    "Available-Time Research-Status Planning Report-Only v0.1"
)
STATUS_NEGATIVE_PROOF_FIELDS = [
    "source_hash_recomputed",
    "source_artifact_opened",
    "source_content_read",
    "local_file_hash_recomputed",
    "expected_hash_reverified",
    "target_csv_opened",
    "real_csv_consumed",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "source_reliability_scored",
    "reviewer_authority_validated",
    *REQUIRED_FALSE_FLAGS,
]
STATUS_COLUMNS = [
    "latest_run_id",
    "latest_runtime_status",
    "latest_health_status",
    "latest_workflow_stage",
    "latest_artifact_path",
    "latest_report_path",
    "latest_metadata_path",
    "latest_summary_path",
    "latest_source_hash_validation_level",
    "latest_revision_id_validation_level",
    "latest_available_time_validation_level",
    "latest_pit_admissibility_level",
    "latest_source_hash_metadata_present",
    "latest_source_hash_format_checked",
    "latest_source_hash_algorithm_supported",
    "latest_source_hash_algorithm",
    "latest_source_hash_preview",
    "latest_revision_id_metadata_present",
    "latest_revision_id_type",
    "latest_revision_id_type_supported",
    "latest_revision_id_value_recorded",
    "latest_revision_consistency_checked",
    "latest_available_time_metadata_present",
    "latest_available_time_parseable",
    "latest_available_time_timezone_present",
    "latest_available_time_timezone_policy",
    "latest_available_time_compared_to_decision_time",
    "latest_source_hash_recomputed",
    "latest_source_artifact_opened",
    "latest_source_content_read",
    "latest_target_csv_opened",
    "latest_real_csv_consumed",
    "latest_local_file_hash_recomputed",
    "latest_expected_hash_reverified",
    "latest_source_hash_validated",
    "latest_revision_id_validated",
    "latest_available_time_validated",
    "latest_pit_admissibility_validated",
    "latest_source_reliability_scored",
    "latest_reviewer_authority_validated",
    "latest_issue_count",
    "latest_warning_count",
    *[f"latest_{field}" for field in REQUIRED_FALSE_FLAGS],
    *STATUS_NEGATIVE_PROOF_FIELDS,
    "report_only",
    "diagnostic_only",
    "recommended_next_task",
]


@dataclass(frozen=True)
class SourceHashRevisionAvailableTimeStatusResult:
    latest_run_id: str
    latest_runtime_status: str
    latest_health_status: str
    latest_workflow_stage: str
    latest_artifact_path: str
    latest_report_path: str
    latest_metadata_path: str
    latest_summary_path: str
    latest_source_hash_preview: str
    latest_revision_id_type: str
    latest_available_time_parseable: bool
    latest_available_time_timezone_present: bool
    latest_available_time_compared_to_decision_time: bool
    recommended_next_task: str
    summary: dict[str, Any]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def run_source_hash_revision_available_time_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/status",
) -> SourceHashRevisionAvailableTimeStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_source_hash_revision_available_time_index(root=root, output_dir=sibling_root / "index")
    health = check_source_hash_revision_available_time_health(root=root, output_dir=sibling_root / "health")
    if not index.rows:
        summary = _no_artifact_summary(health.status)
    else:
        latest = sorted(index.rows, key=lambda row: str(row.get("run_id") or ""))[-1]
        summary = _summary_from_latest(latest, health.status)
    paths = _paths(output_dir)
    result = SourceHashRevisionAvailableTimeStatusResult(
        latest_run_id=str(summary["latest_run_id"]),
        latest_runtime_status=str(summary["latest_runtime_status"]),
        latest_health_status=str(summary["latest_health_status"]),
        latest_workflow_stage=str(summary["latest_workflow_stage"]),
        latest_artifact_path=str(summary["latest_artifact_path"]),
        latest_report_path=str(summary["latest_report_path"]),
        latest_metadata_path=str(summary["latest_metadata_path"]),
        latest_summary_path=str(summary["latest_summary_path"]),
        latest_source_hash_preview=str(summary["latest_source_hash_preview"]),
        latest_revision_id_type=str(summary["latest_revision_id_type"]),
        latest_available_time_parseable=_to_bool(summary["latest_available_time_parseable"]),
        latest_available_time_timezone_present=_to_bool(
            summary["latest_available_time_timezone_present"]
        ),
        latest_available_time_compared_to_decision_time=_to_bool(
            summary["latest_available_time_compared_to_decision_time"]
        ),
        recommended_next_task=NEXT_TASK,
        summary=summary,
        artifact_paths=paths,
        warnings=[] if health.status == "PASS" else [f"Source hash revision available-time health is {health.status}."],
    )
    _write(result)
    return result


def _summary_from_latest(latest: dict[str, Any], health_status: str) -> dict[str, Any]:
    runtime_status = "FAIL" if health_status == "FAIL" else _text(latest.get("runtime_status"))
    summary = {
        "latest_run_id": _text(latest.get("run_id")),
        "latest_runtime_status": runtime_status,
        "latest_health_status": health_status,
        "latest_workflow_stage": _text(latest.get("workflow_stage")),
        "latest_artifact_path": _text(latest.get("artifact_path")),
        "latest_report_path": _text(latest.get("report_path")),
        "latest_metadata_path": _text(latest.get("metadata_path")),
        "latest_summary_path": _text(latest.get("summary_path")),
        "latest_source_hash_validation_level": _text(latest.get("source_hash_validation_level")),
        "latest_revision_id_validation_level": _text(latest.get("revision_id_validation_level")),
        "latest_available_time_validation_level": _text(latest.get("available_time_validation_level")),
        "latest_pit_admissibility_level": _text(latest.get("pit_admissibility_level")),
        "latest_source_hash_metadata_present": _to_bool(latest.get("source_hash_metadata_present")),
        "latest_source_hash_format_checked": _to_bool(latest.get("source_hash_format_checked")),
        "latest_source_hash_algorithm_supported": _to_bool(
            latest.get("source_hash_algorithm_supported")
        ),
        "latest_source_hash_algorithm": _text(latest.get("source_hash_algorithm")),
        "latest_source_hash_preview": _text(latest.get("source_hash_preview"))[:16],
        "latest_revision_id_metadata_present": _to_bool(latest.get("revision_id_metadata_present")),
        "latest_revision_id_type": _text(latest.get("revision_id_type")),
        "latest_revision_id_type_supported": _to_bool(latest.get("revision_id_type_supported")),
        "latest_revision_id_value_recorded": _to_bool(latest.get("revision_id_value_recorded")),
        "latest_revision_consistency_checked": _to_bool(latest.get("revision_consistency_checked")),
        "latest_available_time_metadata_present": _to_bool(latest.get("available_time_metadata_present")),
        "latest_available_time_parseable": _to_bool(latest.get("available_time_parseable")),
        "latest_available_time_timezone_present": _to_bool(
            latest.get("available_time_timezone_present")
        ),
        "latest_available_time_timezone_policy": _text(
            latest.get("available_time_timezone_policy")
        ),
        "latest_available_time_compared_to_decision_time": _to_bool(
            latest.get("available_time_compared_to_decision_time")
        ),
        "latest_source_hash_recomputed": _to_bool(latest.get("source_hash_recomputed")),
        "latest_source_artifact_opened": _to_bool(latest.get("source_artifact_opened")),
        "latest_source_content_read": _to_bool(latest.get("source_content_read")),
        "latest_target_csv_opened": _to_bool(latest.get("target_csv_opened")),
        "latest_real_csv_consumed": _to_bool(latest.get("real_csv_consumed")),
        "latest_local_file_hash_recomputed": _to_bool(latest.get("local_file_hash_recomputed")),
        "latest_expected_hash_reverified": _to_bool(latest.get("expected_hash_reverified")),
        "latest_source_hash_validated": _to_bool(latest.get("source_hash_validated")),
        "latest_revision_id_validated": _to_bool(latest.get("revision_id_validated")),
        "latest_available_time_validated": _to_bool(latest.get("available_time_validated")),
        "latest_pit_admissibility_validated": _to_bool(latest.get("pit_admissibility_validated")),
        "latest_source_reliability_scored": _to_bool(latest.get("source_reliability_scored")),
        "latest_reviewer_authority_validated": _to_bool(latest.get("reviewer_authority_validated")),
        "latest_issue_count": _value(latest.get("issue_count")),
        "latest_warning_count": _value(latest.get("warning_count")),
        "report_only": True,
        "diagnostic_only": True,
        "recommended_next_task": NEXT_TASK,
    }
    summary.update({f"latest_{field}": _to_bool(latest.get(field)) for field in REQUIRED_FALSE_FLAGS})
    summary.update({field: summary.get(f"latest_{field}", False) for field in STATUS_NEGATIVE_PROOF_FIELDS})
    return _finalize_summary(summary)


def _no_artifact_summary(health_status: str) -> dict[str, Any]:
    summary = {
        "latest_run_id": "",
        "latest_runtime_status": STATUS_NO_INPUT,
        "latest_health_status": health_status,
        "latest_workflow_stage": NO_ARTIFACT_STAGE,
        "latest_artifact_path": "",
        "latest_report_path": "",
        "latest_metadata_path": "",
        "latest_summary_path": "",
        "latest_source_hash_validation_level": SOURCE_HASH_VALIDATION_NONE,
        "latest_revision_id_validation_level": REVISION_ID_VALIDATION_NONE,
        "latest_available_time_validation_level": AVAILABLE_TIME_VALIDATION_NONE,
        "latest_pit_admissibility_level": PIT_ADMISSIBILITY_NONE,
        "latest_source_hash_metadata_present": False,
        "latest_source_hash_format_checked": False,
        "latest_source_hash_algorithm_supported": False,
        "latest_source_hash_algorithm": "",
        "latest_source_hash_preview": "",
        "latest_revision_id_metadata_present": False,
        "latest_revision_id_type": "",
        "latest_revision_id_type_supported": False,
        "latest_revision_id_value_recorded": False,
        "latest_revision_consistency_checked": False,
        "latest_available_time_metadata_present": False,
        "latest_available_time_parseable": False,
        "latest_available_time_timezone_present": False,
        "latest_available_time_timezone_policy": "",
        "latest_available_time_compared_to_decision_time": False,
        "latest_source_hash_recomputed": False,
        "latest_source_artifact_opened": False,
        "latest_source_content_read": False,
        "latest_target_csv_opened": False,
        "latest_real_csv_consumed": False,
        "latest_local_file_hash_recomputed": False,
        "latest_expected_hash_reverified": False,
        "latest_source_hash_validated": False,
        "latest_revision_id_validated": False,
        "latest_available_time_validated": False,
        "latest_pit_admissibility_validated": False,
        "latest_source_reliability_scored": False,
        "latest_reviewer_authority_validated": False,
        "latest_issue_count": 0,
        "latest_warning_count": 0,
        "report_only": True,
        "diagnostic_only": True,
        "recommended_next_task": NEXT_TASK,
    }
    summary.update({f"latest_{field}": False for field in REQUIRED_FALSE_FLAGS})
    summary.update({field: False for field in STATUS_NEGATIVE_PROOF_FIELDS})
    return _finalize_summary(summary)


def _finalize_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {column: summary.get(column, "") for column in STATUS_COLUMNS}


def _paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {
        "artifact_dir": root,
        "status_csv": root / "source_hash_revision_available_time_status.csv",
        "status_md": root / "source_hash_revision_available_time_status.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: SourceHashRevisionAvailableTimeStatusResult) -> None:
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
            "report_only": True,
            "diagnostic_only": True,
        },
    )


def _status_markdown(result: SourceHashRevisionAvailableTimeStatusResult) -> str:
    lines = [
        "# Source Hash Revision Available-Time Status",
        "",
        f"- Latest run id: `{result.latest_run_id}`",
        f"- Latest runtime status: `{result.latest_runtime_status}`",
        f"- Latest health status: `{result.latest_health_status}`",
        f"- Latest source hash preview: `{result.latest_source_hash_preview}`",
        f"- Latest revision id type: `{result.latest_revision_id_type}`",
        f"- Latest available-time parseable: `{str(result.latest_available_time_parseable).lower()}`",
        f"- Latest available-time timezone present: `{str(result.latest_available_time_timezone_present).lower()}`",
        f"- Latest available-time compared to decision time: `{str(result.latest_available_time_compared_to_decision_time).lower()}`",
        "- Context: report-only and diagnostic-only; not PIT admissibility, package approval, replay readiness, buy-review, or trading readiness.",
        f"- Recommended next task: {result.recommended_next_task}",
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
