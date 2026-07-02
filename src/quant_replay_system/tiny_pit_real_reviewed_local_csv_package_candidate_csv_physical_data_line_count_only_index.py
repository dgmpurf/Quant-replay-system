"""Index view for CSV physical data-line count-only artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only import (
    ARTIFACT_FILENAMES,
    REQUIRED_FALSE_FLAGS,
)


DEFAULT_ROOT = (
    "outputs/reports/manual_diagnostics/"
    "tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_v0_1"
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
    "expected_hash_verification_level",
    "csv_physical_data_line_count_level",
    "csv_physical_data_line_count_computed",
    "csv_physical_data_line_count",
    "csv_physical_data_line_count_policy",
    "csv_physical_line_count_total",
    "csv_header_dependency_policy",
    "header_metadata_reused",
    "csv_header_read",
    "csv_header_values_recorded",
    "csv_header_line_skipped_by_policy",
    "target_csv_opened_for_physical_data_line_count",
    "csv_values_read",
    "csv_value_fields_parsed",
    "csv_row_values_stored",
    "csv_full_content_semantically_read",
    "csv_full_content_read",
    "real_csv_consumed",
    "local_file_byte_hash_computed",
    "local_file_byte_hash_recomputed",
    "expected_hash_verification_performed",
    "expected_hash_verified_against_local_metadata",
    "expected_hash_verified_against_source_hash",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "source_reliability_scored",
    "reviewer_authority_validated",
    "issue_count",
    "warning_count",
    *REQUIRED_FALSE_FLAGS,
    "recommended_next_task",
]


@dataclass(frozen=True)
class CsvPhysicalDataLineCountIndexResult:
    artifact_count: int
    rows: list[dict[str, Any]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_csv_physical_data_line_count_only_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/index",
) -> CsvPhysicalDataLineCountIndexResult:
    root_path = Path(root)
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not root_path.exists():
        warnings.append(f"Artifact root does not exist: {root_path}")
    else:
        for artifact_dir in _candidate_dirs(root_path):
            row = _row_from_artifact_dir(artifact_dir)
            if row is not None:
                rows.append(row)
    rows = [_finalize_row(row) for row in rows]
    paths = _paths(output_dir)
    result = CsvPhysicalDataLineCountIndexResult(
        artifact_count=len(rows),
        rows=rows,
        artifact_paths=paths,
        warnings=warnings,
    )
    _write(result)
    return result


def _row_from_artifact_dir(artifact_dir: Path) -> dict[str, Any] | None:
    metadata_path = artifact_dir / ARTIFACT_FILENAMES["metadata"]
    try:
        with metadata_path.open("r", encoding="utf-8") as handle:
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
        "file_touch_level": _text(metadata.get("file_touch_level")),
        "csv_read_level": _text(metadata.get("csv_read_level")),
        "local_file_hash_level": _text(metadata.get("local_file_hash_level")),
        "expected_hash_verification_level": _text(metadata.get("expected_hash_verification_level")),
        "csv_physical_data_line_count_level": _text(
            metadata.get("csv_physical_data_line_count_level")
        ),
        "csv_physical_data_line_count_computed": _to_bool(
            metadata.get("csv_physical_data_line_count_computed")
        ),
        "csv_physical_data_line_count": _value(metadata.get("csv_physical_data_line_count")),
        "csv_physical_data_line_count_policy": _text(
            metadata.get("csv_physical_data_line_count_policy")
        ),
        "csv_physical_line_count_total": _value(metadata.get("csv_physical_line_count_total")),
        "csv_header_dependency_policy": _text(metadata.get("csv_header_dependency_policy")),
        "header_metadata_reused": _to_bool(metadata.get("header_metadata_reused")),
        "csv_header_read": _to_bool(metadata.get("csv_header_read")),
        "csv_header_values_recorded": _to_bool(metadata.get("csv_header_values_recorded")),
        "csv_header_line_skipped_by_policy": _to_bool(
            metadata.get("csv_header_line_skipped_by_policy")
        ),
        "target_csv_opened_for_physical_data_line_count": _to_bool(
            metadata.get("target_csv_opened_for_physical_data_line_count")
        ),
        "csv_values_read": _to_bool(metadata.get("csv_values_read")),
        "csv_value_fields_parsed": _to_bool(metadata.get("csv_value_fields_parsed")),
        "csv_row_values_stored": _to_bool(metadata.get("csv_row_values_stored")),
        "csv_full_content_semantically_read": _to_bool(
            metadata.get("csv_full_content_semantically_read")
        ),
        "csv_full_content_read": _to_bool(metadata.get("csv_full_content_read")),
        "real_csv_consumed": _to_bool(metadata.get("real_csv_consumed")),
        "local_file_byte_hash_computed": _to_bool(metadata.get("local_file_byte_hash_computed")),
        "local_file_byte_hash_recomputed": _to_bool(metadata.get("local_file_byte_hash_recomputed")),
        "expected_hash_verification_performed": _to_bool(
            metadata.get("expected_hash_verification_performed")
        ),
        "expected_hash_verified_against_local_metadata": _to_bool(
            metadata.get("expected_hash_verified_against_local_metadata")
        ),
        "expected_hash_verified_against_source_hash": _to_bool(
            metadata.get("expected_hash_verified_against_source_hash")
        ),
        "source_hash_validated": _to_bool(metadata.get("source_hash_validated")),
        "revision_id_validated": _to_bool(metadata.get("revision_id_validated")),
        "available_time_validated": _to_bool(metadata.get("available_time_validated")),
        "pit_admissibility_validated": _to_bool(metadata.get("pit_admissibility_validated")),
        "source_reliability_scored": _to_bool(metadata.get("source_reliability_scored")),
        "reviewer_authority_validated": _to_bool(metadata.get("reviewer_authority_validated")),
        "issue_count": _value(metadata.get("issue_count")),
        "warning_count": _value(metadata.get("warning_count")),
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


def _finalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {column: row.get(column, "") for column in INDEX_COLUMNS}


def _paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {
        "artifact_dir": root,
        "index_csv": root / "csv_physical_data_line_count_only_index.csv",
        "index_md": root / "csv_physical_data_line_count_only_index.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: CsvPhysicalDataLineCountIndexResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_rows(result.artifact_paths["index_csv"], INDEX_COLUMNS, result.rows)
    _write_text(result.artifact_paths["index_md"], _index_markdown(result))
    metadata = {
        "artifact_count": result.artifact_count,
        "status": "PASS",
        "warnings": result.warnings,
        "index_csv": str(result.artifact_paths["index_csv"]),
    }
    _write_json(result.artifact_paths["metadata_json"], metadata)


def _index_markdown(result: CsvPhysicalDataLineCountIndexResult) -> str:
    lines = [
        "# CSV Physical Data-Line Count-Only Index",
        "",
        f"- Artifact count: `{result.artifact_count}`",
        "- This index exposes counts and safety flags only; it does not expose header values, row values, parsed fields, samples, or fingerprint values.",
        "",
        "| Run id | Status | Health | Physical data lines | Policy |",
        "|---|---|---|---|---|",
    ]
    for row in result.rows:
        lines.append(
            f"| `{row['run_id']}` | `{row['runtime_status']}` | `{row['health_status']}` | "
            f"`{row['csv_physical_data_line_count']}` | `{row['csv_physical_data_line_count_policy']}` |"
        )
    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _write_rows(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(",".join(fields) + "\n")
        for row in rows:
            handle.write(",".join(_cell(row.get(field, "")) for field in fields) + "\n")


def _cell(value: Any) -> str:
    text = str(value)
    if any(char in text for char in [",", '"', "\n", "\r"]):
        return '"' + text.replace('"', '""') + '"'
    return text


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _value(value: Any) -> Any:
    return "" if value is None else value


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)
