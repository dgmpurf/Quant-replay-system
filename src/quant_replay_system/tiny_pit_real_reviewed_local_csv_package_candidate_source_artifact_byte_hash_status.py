"""Status view for Tiny PIT source artifact byte-hash report-only artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash import (
    REQUIRED_FALSE_FLAGS,
    SOURCE_CONTENT_READ_NONE,
    SOURCE_HASH_VALIDATION_NONE,
    STATUS_NO_INPUT,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash_health import (
    check_source_artifact_byte_hash_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash_index import (
    DEFAULT_ROOT,
    build_source_artifact_byte_hash_index,
)


NO_ARTIFACT_STAGE = (
    "NO_TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_SOURCE_ARTIFACT_BYTE_HASH"
)
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Artifact Byte-Hash "
    "CLI Report-Only v0.1"
)
STATUS_COLUMNS = [
    "latest_run_id",
    "latest_runtime_status",
    "latest_health_status",
    "latest_workflow_stage",
    "latest_artifact_path",
    "latest_report_path",
    "latest_metadata_path",
    "latest_source_id",
    "latest_source_artifact_id",
    "latest_source_artifact_name_preview",
    "latest_source_artifact_path_preview",
    "latest_source_artifact_file_size_bytes",
    "latest_source_hash_algorithm",
    "latest_computed_source_hash_preview",
    "latest_declared_source_hash_preview",
    "latest_source_artifact_byte_identity_matched",
    "latest_source_artifact_byte_identity_mismatch",
    "latest_source_artifact_byte_identity_actionable_mismatch",
    "latest_source_artifact_byte_read_level",
    "latest_source_hash_recompute_level",
    "latest_source_content_read_level",
    "latest_csv_read_level",
    "latest_local_file_hash_level",
    "latest_expected_hash_verification_level",
    "latest_source_hash_validation_level",
    "latest_revision_id_validation_level",
    "latest_available_time_validation_level",
    "latest_pit_admissibility_level",
    "latest_source_reliability_level",
    "latest_reviewer_authority_level",
    "latest_package_creation_level",
    "latest_active_input_level",
    "latest_replay_readiness_level",
    "latest_source_artifact_opened_for_hash",
    "latest_source_artifact_bytes_streamed_for_hash",
    "latest_source_content_read",
    "latest_source_content_semantically_read",
    "latest_target_csv_opened",
    "latest_csv_header_read",
    "latest_csv_values_read",
    "latest_csv_full_content_read",
    "latest_source_hash_recomputed",
    "latest_source_hash_validated",
    "latest_source_reliability_scored",
    "latest_reviewer_authority_validated",
    "latest_issue_count",
    "latest_warning_count",
    *[f"latest_{field}" for field in REQUIRED_FALSE_FLAGS],
    "report_only",
    "diagnostic_only",
    "recommended_next_task",
]


@dataclass(frozen=True)
class SourceArtifactByteHashStatusResult:
    latest_run_id: str
    latest_runtime_status: str
    latest_health_status: str
    latest_workflow_stage: str
    latest_artifact_path: str
    latest_report_path: str
    latest_metadata_path: str
    recommended_next_task: str
    summary: dict[str, Any]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def run_source_artifact_byte_hash_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/status",
) -> SourceArtifactByteHashStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_source_artifact_byte_hash_index(root=root, output_dir=sibling_root / "index")
    health = check_source_artifact_byte_hash_health(root=root, output_dir=sibling_root / "health")
    if not index.rows:
        summary = _no_artifact_summary(health.status)
    else:
        latest = sorted(index.rows, key=lambda row: str(row.get("run_id") or ""))[-1]
        summary = _summary_from_latest(latest, health.status)
    paths = _paths(output_dir)
    result = SourceArtifactByteHashStatusResult(
        latest_run_id=str(summary["latest_run_id"]),
        latest_runtime_status=str(summary["latest_runtime_status"]),
        latest_health_status=str(summary["latest_health_status"]),
        latest_workflow_stage=str(summary["latest_workflow_stage"]),
        latest_artifact_path=str(summary["latest_artifact_path"]),
        latest_report_path=str(summary["latest_report_path"]),
        latest_metadata_path=str(summary["latest_metadata_path"]),
        recommended_next_task=NEXT_TASK,
        summary=summary,
        artifact_paths=paths,
        warnings=[] if health.status == "PASS" else [f"Source artifact byte-hash health is {health.status}."],
    )
    _write(result)
    return result


def _summary_from_latest(latest: dict[str, Any], health_status: str) -> dict[str, Any]:
    summary = {
        "latest_run_id": _text(latest.get("run_id")),
        "latest_runtime_status": _text(latest.get("runtime_status")),
        "latest_health_status": health_status,
        "latest_workflow_stage": _text(latest.get("workflow_stage")),
        "latest_artifact_path": _text(latest.get("artifact_path")),
        "latest_report_path": _text(latest.get("report_path")),
        "latest_metadata_path": _text(latest.get("metadata_path")),
        "latest_source_id": _text(latest.get("source_id")),
        "latest_source_artifact_id": _text(latest.get("source_artifact_id")),
        "latest_source_artifact_name_preview": _text(latest.get("source_artifact_name_preview")),
        "latest_source_artifact_path_preview": _text(latest.get("source_artifact_path_preview")),
        "latest_source_artifact_file_size_bytes": _value(latest.get("source_artifact_file_size_bytes")),
        "latest_source_hash_algorithm": _text(latest.get("source_hash_algorithm")),
        "latest_computed_source_hash_preview": _text(latest.get("computed_source_hash_preview"))[:16],
        "latest_declared_source_hash_preview": _text(latest.get("declared_source_hash_preview"))[:16],
        "latest_source_artifact_byte_identity_matched": _to_bool(latest.get("source_artifact_byte_identity_matched")),
        "latest_source_artifact_byte_identity_mismatch": _to_bool(latest.get("source_artifact_byte_identity_mismatch")),
        "latest_source_artifact_byte_identity_actionable_mismatch": _to_bool(
            latest.get("source_artifact_byte_identity_actionable_mismatch")
        ),
        "latest_source_artifact_byte_read_level": _text(latest.get("source_artifact_byte_read_level")),
        "latest_source_hash_recompute_level": _text(latest.get("source_hash_recompute_level")),
        "latest_source_content_read_level": _text(latest.get("source_content_read_level")),
        "latest_csv_read_level": _text(latest.get("csv_read_level")),
        "latest_local_file_hash_level": _text(latest.get("local_file_hash_level")),
        "latest_expected_hash_verification_level": _text(latest.get("expected_hash_verification_level")),
        "latest_source_hash_validation_level": _text(latest.get("source_hash_validation_level")),
        "latest_revision_id_validation_level": _text(latest.get("revision_id_validation_level")),
        "latest_available_time_validation_level": _text(latest.get("available_time_validation_level")),
        "latest_pit_admissibility_level": _text(latest.get("pit_admissibility_level")),
        "latest_source_reliability_level": _text(latest.get("source_reliability_level")),
        "latest_reviewer_authority_level": _text(latest.get("reviewer_authority_level")),
        "latest_package_creation_level": _text(latest.get("package_creation_level")),
        "latest_active_input_level": _text(latest.get("active_input_level")),
        "latest_replay_readiness_level": _text(latest.get("replay_readiness_level")),
        "latest_source_artifact_opened_for_hash": _to_bool(latest.get("source_artifact_opened_for_hash")),
        "latest_source_artifact_bytes_streamed_for_hash": _to_bool(latest.get("source_artifact_bytes_streamed_for_hash")),
        "latest_source_content_read": _to_bool(latest.get("source_content_read")),
        "latest_source_content_semantically_read": _to_bool(latest.get("source_content_semantically_read")),
        "latest_target_csv_opened": _to_bool(latest.get("target_csv_opened")),
        "latest_csv_header_read": _to_bool(latest.get("csv_header_read")),
        "latest_csv_values_read": _to_bool(latest.get("csv_values_read")),
        "latest_csv_full_content_read": _to_bool(latest.get("csv_full_content_read")),
        "latest_source_hash_recomputed": _to_bool(latest.get("source_hash_recomputed")),
        "latest_source_hash_validated": _to_bool(latest.get("source_hash_validated")),
        "latest_source_reliability_scored": _to_bool(latest.get("source_reliability_scored")),
        "latest_reviewer_authority_validated": _to_bool(latest.get("reviewer_authority_validated")),
        "latest_issue_count": _value(latest.get("issue_count")),
        "latest_warning_count": _value(latest.get("warning_count")),
        "report_only": True,
        "diagnostic_only": True,
        "recommended_next_task": NEXT_TASK,
    }
    for field in REQUIRED_FALSE_FLAGS:
        summary[f"latest_{field}"] = _to_bool(latest.get(field))
    return {column: summary.get(column, "") for column in STATUS_COLUMNS}


def _no_artifact_summary(health_status: str) -> dict[str, Any]:
    summary = {column: "" for column in STATUS_COLUMNS}
    summary.update(
        {
            "latest_run_id": "",
            "latest_runtime_status": STATUS_NO_INPUT,
            "latest_health_status": health_status,
            "latest_workflow_stage": NO_ARTIFACT_STAGE,
            "latest_source_content_read_level": SOURCE_CONTENT_READ_NONE,
            "latest_source_hash_validation_level": SOURCE_HASH_VALIDATION_NONE,
            "report_only": True,
            "diagnostic_only": True,
            "recommended_next_task": NEXT_TASK,
        }
    )
    return summary


def _paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {
        "artifact_dir": root,
        "status_csv": root / "source_artifact_byte_hash_status.csv",
        "status_md": root / "source_artifact_byte_hash_status.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: SourceArtifactByteHashStatusResult) -> None:
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
            "summary": result.summary,
            "recommended_next_task": result.recommended_next_task,
            "warnings": result.warnings,
        },
    )


def _status_markdown(result: SourceArtifactByteHashStatusResult) -> str:
    summary = result.summary
    lines = [
        "# Source Artifact Byte-Hash Status",
        "",
        f"- Latest run id: `{summary['latest_run_id']}`",
        f"- Latest runtime status: `{summary['latest_runtime_status']}`",
        f"- Latest health status: `{summary['latest_health_status']}`",
        f"- Latest workflow stage: `{summary['latest_workflow_stage']}`",
        f"- Source artifact id: `{summary['latest_source_artifact_id']}`",
        f"- Source artifact name preview: `{summary['latest_source_artifact_name_preview']}`",
        f"- Source artifact path preview: `{summary['latest_source_artifact_path_preview']}`",
        f"- Computed source hash preview: `{summary['latest_computed_source_hash_preview']}`",
        f"- Declared source hash preview: `{summary['latest_declared_source_hash_preview']}`",
        f"- Byte identity matched: `{str(summary['latest_source_artifact_byte_identity_matched']).lower()}`",
        f"- Byte identity mismatch: `{str(summary['latest_source_artifact_byte_identity_mismatch']).lower()}`",
        "- Source hash validated: `false`",
        "- Source reliability scored: `false`",
        "- Source content read: `false`",
        "- Target CSV opened: `false`",
        "- Real package candidate created: `false`",
        "- Active replay input: `false`",
        "- Buy review allowed: `false`",
        "- Trading allowed: `false`",
        f"- Recommended next task: `{NEXT_TASK}`",
        "",
    ]
    return "\n".join(lines)


def _write_rows(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _open_path(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _open_path(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _open_path(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def _open_path(path: Path, *args: Any, **kwargs: Any) -> Any:
    return getattr(path, "open")(*args, **kwargs)


def _text(value: Any) -> str:
    return str(value or "").replace("\n", " ")[:240]


def _value(value: Any) -> Any:
    return "" if value is None else value


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)
