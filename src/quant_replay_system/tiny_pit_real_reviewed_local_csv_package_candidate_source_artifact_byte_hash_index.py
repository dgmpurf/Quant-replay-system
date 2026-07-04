"""Index view for Tiny PIT source artifact byte-hash report-only artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash import (
    ARTIFACT_FILENAMES,
    REQUIRED_FALSE_FLAGS,
)


DEFAULT_ROOT = (
    "outputs/reports/manual_diagnostics/"
    "tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash_v0_1"
)
VIEW_DIR_NAMES = {"index", "health", "status"}
INDEX_COLUMNS = [
    "run_id",
    "runtime_status",
    "health_status",
    "workflow_stage",
    "artifact_path",
    "metadata_path",
    "report_path",
    "summary_path",
    "limitations_path",
    "issues_path",
    "forbidden_downstream_flags_path",
    "report_only",
    "diagnostic_only",
    "source_id",
    "source_artifact_id",
    "source_artifact_name_preview",
    "source_artifact_path_preview",
    "source_artifact_file_size_bytes",
    "source_hash_algorithm",
    "computed_source_hash_preview",
    "declared_source_hash_preview",
    "computed_source_hash_full_recorded_in_metadata",
    "source_artifact_byte_identity_matched",
    "source_artifact_byte_identity_mismatch",
    "source_artifact_byte_identity_actionable_mismatch",
    "source_artifact_byte_read_level",
    "source_hash_recompute_level",
    "source_content_read_level",
    "csv_read_level",
    "local_file_hash_level",
    "expected_hash_verification_level",
    "source_hash_validation_level",
    "revision_id_validation_level",
    "available_time_validation_level",
    "pit_admissibility_level",
    "source_reliability_level",
    "reviewer_authority_level",
    "package_creation_level",
    "active_input_level",
    "replay_readiness_level",
    "source_artifact_opened_for_hash",
    "source_artifact_bytes_streamed_for_hash",
    "source_content_read",
    "source_content_semantically_read",
    "target_csv_opened",
    "csv_header_read",
    "csv_values_read",
    "csv_full_content_read",
    "source_hash_recomputed",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "available_time_compared_to_decision_time",
    "pit_admissibility_validated",
    "source_reliability_scored",
    "reviewer_authority_validated",
    "local_file_hash_recomputed",
    "expected_hash_reverified",
    "issue_count",
    "warning_count",
    *REQUIRED_FALSE_FLAGS,
    "recommended_next_task",
]


@dataclass(frozen=True)
class SourceArtifactByteHashIndexResult:
    artifact_count: int
    rows: list[dict[str, Any]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_source_artifact_byte_hash_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/index",
) -> SourceArtifactByteHashIndexResult:
    root_path = Path(root)
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []
    if not root_path.exists():
        warnings.append(f"Artifact root does not exist: {root_path}")
    else:
        for artifact_dir in _candidate_dirs(root_path):
            row = _row_from_artifact_dir(artifact_dir)
            if row is not None:
                rows.append(_finalize_row(row))
    paths = _paths(output_dir)
    result = SourceArtifactByteHashIndexResult(
        artifact_count=len(rows),
        rows=rows,
        artifact_paths=paths,
        warnings=warnings,
    )
    _write(result)
    return result


def _candidate_dirs(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir()
        and path.name not in VIEW_DIR_NAMES
        and not path.name.startswith("_")
        and (path / ARTIFACT_FILENAMES["metadata"]).exists()
    )


def _row_from_artifact_dir(artifact_dir: Path) -> dict[str, Any] | None:
    metadata_path = artifact_dir / ARTIFACT_FILENAMES["metadata"]
    try:
        with _open_path(metadata_path, "r", encoding="utf-8") as handle:
            metadata = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(metadata, dict):
        return None
    row = {
        "run_id": _text(metadata.get("run_id") or artifact_dir.name),
        "runtime_status": _text(metadata.get("runtime_status") or metadata.get("status")),
        "health_status": _text(metadata.get("health_status")),
        "workflow_stage": _text(metadata.get("workflow_stage")),
        "artifact_path": str(artifact_dir),
        "metadata_path": str(metadata_path),
        "report_path": str(artifact_dir / ARTIFACT_FILENAMES["report"]),
        "summary_path": str(artifact_dir / ARTIFACT_FILENAMES["summary"]),
        "limitations_path": str(artifact_dir / ARTIFACT_FILENAMES["limitations"]),
        "issues_path": str(artifact_dir / ARTIFACT_FILENAMES["issues"]),
        "forbidden_downstream_flags_path": str(
            artifact_dir / ARTIFACT_FILENAMES["forbidden_downstream_flags"]
        ),
        "report_only": _to_bool(metadata.get("report_only")),
        "diagnostic_only": _to_bool(metadata.get("diagnostic_only")),
        "source_id": _text(metadata.get("source_id")),
        "source_artifact_id": _text(metadata.get("source_artifact_id")),
        "source_artifact_name_preview": _preview(metadata.get("source_artifact_name_preview")),
        "source_artifact_path_preview": _preview(metadata.get("source_artifact_path_preview")),
        "source_artifact_file_size_bytes": _value(metadata.get("source_artifact_file_size_bytes")),
        "source_hash_algorithm": _text(metadata.get("source_hash_algorithm")),
        "computed_source_hash_preview": _hash_preview(metadata.get("computed_source_hash_preview")),
        "declared_source_hash_preview": _hash_preview(metadata.get("declared_source_hash_preview")),
        "computed_source_hash_full_recorded_in_metadata": _to_bool(
            metadata.get("computed_source_hash_full_recorded_in_metadata")
        ),
        "source_artifact_byte_identity_matched": _to_bool(
            metadata.get("source_artifact_byte_identity_matched")
        ),
        "source_artifact_byte_identity_mismatch": _to_bool(
            metadata.get("source_artifact_byte_identity_mismatch")
        ),
        "source_artifact_byte_identity_actionable_mismatch": _to_bool(
            metadata.get("source_artifact_byte_identity_actionable_mismatch")
        ),
        "source_artifact_byte_read_level": _text(metadata.get("source_artifact_byte_read_level")),
        "source_hash_recompute_level": _text(metadata.get("source_hash_recompute_level")),
        "source_content_read_level": _text(metadata.get("source_content_read_level")),
        "csv_read_level": _text(metadata.get("csv_read_level")),
        "local_file_hash_level": _text(metadata.get("local_file_hash_level")),
        "expected_hash_verification_level": _text(metadata.get("expected_hash_verification_level")),
        "source_hash_validation_level": _text(metadata.get("source_hash_validation_level")),
        "revision_id_validation_level": _text(metadata.get("revision_id_validation_level")),
        "available_time_validation_level": _text(metadata.get("available_time_validation_level")),
        "pit_admissibility_level": _text(metadata.get("pit_admissibility_level")),
        "source_reliability_level": _text(metadata.get("source_reliability_level")),
        "reviewer_authority_level": _text(metadata.get("reviewer_authority_level")),
        "package_creation_level": _text(metadata.get("package_creation_level")),
        "active_input_level": _text(metadata.get("active_input_level")),
        "replay_readiness_level": _text(metadata.get("replay_readiness_level")),
        "source_artifact_opened_for_hash": _to_bool(metadata.get("source_artifact_opened_for_hash")),
        "source_artifact_bytes_streamed_for_hash": _to_bool(
            metadata.get("source_artifact_bytes_streamed_for_hash")
        ),
        "source_content_read": _to_bool(metadata.get("source_content_read")),
        "source_content_semantically_read": _to_bool(metadata.get("source_content_semantically_read")),
        "target_csv_opened": _to_bool(metadata.get("target_csv_opened")),
        "csv_header_read": _to_bool(metadata.get("csv_header_read")),
        "csv_values_read": _to_bool(metadata.get("csv_values_read")),
        "csv_full_content_read": _to_bool(metadata.get("csv_full_content_read")),
        "source_hash_recomputed": _to_bool(metadata.get("source_hash_recomputed")),
        "source_hash_validated": _to_bool(metadata.get("source_hash_validated")),
        "revision_id_validated": _to_bool(metadata.get("revision_id_validated")),
        "available_time_validated": _to_bool(metadata.get("available_time_validated")),
        "available_time_compared_to_decision_time": _to_bool(
            metadata.get("available_time_compared_to_decision_time")
        ),
        "pit_admissibility_validated": _to_bool(metadata.get("pit_admissibility_validated")),
        "source_reliability_scored": _to_bool(metadata.get("source_reliability_scored")),
        "reviewer_authority_validated": _to_bool(metadata.get("reviewer_authority_validated")),
        "local_file_hash_recomputed": _to_bool(metadata.get("local_file_hash_recomputed")),
        "expected_hash_reverified": _to_bool(metadata.get("expected_hash_reverified")),
        "issue_count": _value(metadata.get("issue_count")),
        "warning_count": _value(metadata.get("warning_count")),
        "recommended_next_task": _text(metadata.get("recommended_next_task")),
    }
    row.update({field: _to_bool(metadata.get(field)) for field in REQUIRED_FALSE_FLAGS})
    return row


def _finalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {column: row.get(column, "") for column in INDEX_COLUMNS}


def _paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {
        "artifact_dir": root,
        "index_csv": root / "source_artifact_byte_hash_index.csv",
        "index_md": root / "source_artifact_byte_hash_index.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: SourceArtifactByteHashIndexResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_rows(result.artifact_paths["index_csv"], INDEX_COLUMNS, result.rows)
    _write_text(result.artifact_paths["index_md"], _index_markdown(result))
    _write_json(
        result.artifact_paths["metadata_json"],
        {
            "artifact_count": result.artifact_count,
            "status": "PASS",
            "warnings": result.warnings,
            "index_csv": str(result.artifact_paths["index_csv"]),
        },
    )


def _index_markdown(result: SourceArtifactByteHashIndexResult) -> str:
    lines = [
        "# Source Artifact Byte-Hash Index",
        "",
        f"- Artifact count: `{result.artifact_count}`",
        "- Full hashes, private paths, source content, CSV content, replay readiness, buy-review, and trading readiness are not exposed.",
        "",
        "| run_id | runtime_status | health_status | hash_preview | matched | mismatch |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in result.rows:
        lines.append(
            "| {run_id} | {runtime_status} | {health_status} | {computed_source_hash_preview} | "
            "{source_artifact_byte_identity_matched} | {source_artifact_byte_identity_mismatch} |".format(
                **row
            )
        )
    lines.append("")
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


def _hash_preview(value: Any) -> str:
    return _text(value)[:16]


def _preview(value: Any) -> str:
    return _text(value)[:80]


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
