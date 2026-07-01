"""Index view for Local File Byte-Hash-Only artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only import (
    ARTIFACT_FILENAMES,
    REQUIRED_FALSE_FLAGS,
)


DEFAULT_ROOT = (
    "outputs/reports/manual_diagnostics/"
    "tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only_v0_1"
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
    "file_touch_level",
    "csv_read_level",
    "local_file_hash_level",
    "local_file_byte_hash_computed",
    "local_file_byte_hash_algorithm",
    "local_file_byte_hash_preview",
    "local_file_byte_hash_full_recorded_in_metadata",
    "local_file_byte_hash_disclosure_level",
    "local_file_byte_hash_verified_against_manifest",
    "local_file_byte_hash_expected_present",
    "local_file_bytes_read_for_hash",
    "local_file_size_bytes",
    "local_file_size_limit_bytes",
    "csv_file_opened_structurally",
    "csv_header_read",
    "csv_row_count_computed",
    "csv_row_count",
    "csv_values_read",
    "csv_full_content_read",
    "real_csv_consumed",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "source_reliability_scored",
    "reviewer_authority_validated",
    *REQUIRED_FALSE_FLAGS,
    "recommended_next_task",
]


@dataclass(frozen=True)
class LocalFileByteHashOnlyIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_local_file_byte_hash_only_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/index",
) -> LocalFileByteHashOnlyIndexResult:
    root_path = Path(root)
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not root_path.exists():
        warnings.append(f"Local file byte-hash-only root does not exist: {root_path}")
    else:
        for artifact_dir in _candidate_dirs(root_path):
            row = _row_from_artifact_dir(artifact_dir)
            if row:
                rows.append(row)
    frame = _finalize(pd.DataFrame(rows))
    paths = _paths(output_dir)
    result = LocalFileByteHashOnlyIndexResult(
        artifact_count=len(frame),
        index_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
    )
    _write(result)
    return result


def _row_from_artifact_dir(artifact_dir: Path) -> dict[str, Any] | None:
    metadata_path = artifact_dir / ARTIFACT_FILENAMES["metadata"]
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
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
        "forbidden_downstream_flags_path": str(artifact_dir / ARTIFACT_FILENAMES["forbidden_downstream_flags"]),
        "report_only": _to_bool(metadata.get("report_only")),
        "diagnostic_only": _to_bool(metadata.get("diagnostic_only")),
        "file_touch_level": _text(metadata.get("file_touch_level")),
        "csv_read_level": _text(metadata.get("csv_read_level")),
        "local_file_hash_level": _text(metadata.get("local_file_hash_level")),
        "local_file_byte_hash_computed": _to_bool(metadata.get("local_file_byte_hash_computed")),
        "local_file_byte_hash_algorithm": _text(metadata.get("local_file_byte_hash_algorithm")),
        "local_file_byte_hash_preview": _text(metadata.get("local_file_byte_hash_preview")),
        "local_file_byte_hash_full_recorded_in_metadata": _to_bool(
            metadata.get("local_file_byte_hash_full_recorded_in_metadata")
        ),
        "local_file_byte_hash_disclosure_level": _text(metadata.get("local_file_byte_hash_disclosure_level")),
        "local_file_byte_hash_verified_against_manifest": _to_bool(
            metadata.get("local_file_byte_hash_verified_against_manifest")
        ),
        "local_file_byte_hash_expected_present": _to_bool(metadata.get("local_file_byte_hash_expected_present")),
        "local_file_bytes_read_for_hash": _to_bool(metadata.get("local_file_bytes_read_for_hash")),
        "local_file_size_bytes": _text(metadata.get("local_file_size_bytes")),
        "local_file_size_limit_bytes": _text(metadata.get("local_file_size_limit_bytes")),
        "csv_file_opened_structurally": _to_bool(metadata.get("csv_file_opened_structurally")),
        "csv_header_read": _to_bool(metadata.get("csv_header_read")),
        "csv_row_count_computed": _to_bool(metadata.get("csv_row_count_computed")),
        "csv_row_count": _text(metadata.get("csv_row_count")),
        "csv_values_read": _to_bool(metadata.get("csv_values_read")),
        "csv_full_content_read": _to_bool(metadata.get("csv_full_content_read")),
        "real_csv_consumed": _to_bool(metadata.get("real_csv_consumed")),
        "source_hash_validated": _to_bool(metadata.get("source_hash_validated")),
        "revision_id_validated": _to_bool(metadata.get("revision_id_validated")),
        "available_time_validated": _to_bool(metadata.get("available_time_validated")),
        "pit_admissibility_validated": _to_bool(metadata.get("pit_admissibility_validated")),
        "source_reliability_scored": _to_bool(metadata.get("source_reliability_scored")),
        "reviewer_authority_validated": _to_bool(metadata.get("reviewer_authority_validated")),
        "recommended_next_task": _text(metadata.get("recommended_next_task")),
    }
    row.update({flag: _to_bool(metadata.get(flag)) for flag in REQUIRED_FALSE_FLAGS})
    return row


def _candidate_dirs(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir()
        and path.name not in VIEW_DIR_NAMES
        and not path.name.startswith("_")
        and (path / ARTIFACT_FILENAMES["metadata"]).exists()
    )


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.Series(dtype="object")
    return frame[INDEX_COLUMNS]


def _paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {
        "artifact_dir": root,
        "index_csv": root / "local_file_byte_hash_only_index.csv",
        "index_md": root / "local_file_byte_hash_only_index.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: LocalFileByteHashOnlyIndexResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(result.artifact_paths["index_csv"], index=False)
    result.artifact_paths["index_md"].write_text(_index_markdown(result), encoding="utf-8")
    metadata = {
        "artifact_count": result.artifact_count,
        "status": "PASS",
        "warnings": result.warnings,
        "index_csv": str(result.artifact_paths["index_csv"]),
    }
    result.artifact_paths["metadata_json"].write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _index_markdown(result: LocalFileByteHashOnlyIndexResult) -> str:
    lines = [
        "# Local File Byte-Hash-Only Index",
        "",
        f"- Artifact count: `{result.artifact_count}`",
        "- Full SHA-256 values are not exposed by this index.",
        "",
        "| Run id | Status | Health | Hash preview |",
        "|---|---|---|---|",
    ]
    for row in result.index_frame.to_dict("records"):
        lines.append(
            f"| `{row['run_id']}` | `{row['runtime_status']}` | `{row['health_status']}` | "
            f"`{row['local_file_byte_hash_preview']}` |"
        )
    return "\n".join(lines) + "\n"


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)
