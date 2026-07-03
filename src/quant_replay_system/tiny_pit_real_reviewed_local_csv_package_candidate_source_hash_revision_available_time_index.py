"""Index view for Source Hash / Revision ID / Available-Time artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time import (
    ARTIFACT_FILENAMES,
    REQUIRED_FALSE_FLAGS,
)


DEFAULT_ROOT = (
    "outputs/reports/manual_diagnostics/"
    "tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time_v0_1"
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
    "source_hash_validation_level",
    "revision_id_validation_level",
    "available_time_validation_level",
    "pit_admissibility_level",
    "source_hash_metadata_present",
    "source_hash_format_checked",
    "source_hash_algorithm_supported",
    "source_hash_algorithm",
    "source_hash_preview",
    "source_hash_recomputed",
    "source_artifact_opened",
    "source_content_read",
    "revision_id_metadata_present",
    "revision_id_type",
    "revision_id_type_supported",
    "revision_id_value_recorded",
    "revision_consistency_checked",
    "available_time_metadata_present",
    "available_time_parseable",
    "available_time_timezone_present",
    "available_time_timezone_policy",
    "available_time_compared_to_decision_time",
    "target_csv_opened",
    "real_csv_consumed",
    "local_file_hash_recomputed",
    "expected_hash_reverified",
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
class SourceHashRevisionAvailableTimeIndexResult:
    artifact_count: int
    rows: list[dict[str, Any]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_source_hash_revision_available_time_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/index",
) -> SourceHashRevisionAvailableTimeIndexResult:
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
    result = SourceHashRevisionAvailableTimeIndexResult(
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
        "source_hash_validation_level": _text(metadata.get("source_hash_validation_level")),
        "revision_id_validation_level": _text(metadata.get("revision_id_validation_level")),
        "available_time_validation_level": _text(metadata.get("available_time_validation_level")),
        "pit_admissibility_level": _text(metadata.get("pit_admissibility_level")),
        "source_hash_metadata_present": _to_bool(metadata.get("source_hash_metadata_present")),
        "source_hash_format_checked": _to_bool(metadata.get("source_hash_format_checked")),
        "source_hash_algorithm_supported": _to_bool(
            metadata.get("source_hash_algorithm_supported")
        ),
        "source_hash_algorithm": _text(metadata.get("source_hash_algorithm")),
        "source_hash_preview": _preview(metadata.get("source_hash_preview")),
        "source_hash_recomputed": _to_bool(metadata.get("source_hash_recomputed")),
        "source_artifact_opened": _to_bool(metadata.get("source_artifact_opened")),
        "source_content_read": _to_bool(metadata.get("source_content_read")),
        "revision_id_metadata_present": _to_bool(metadata.get("revision_id_metadata_present")),
        "revision_id_type": _text(metadata.get("revision_id_type")),
        "revision_id_type_supported": _to_bool(metadata.get("revision_id_type_supported")),
        "revision_id_value_recorded": _to_bool(metadata.get("revision_id_value_recorded")),
        "revision_consistency_checked": _to_bool(metadata.get("revision_consistency_checked")),
        "available_time_metadata_present": _to_bool(metadata.get("available_time_metadata_present")),
        "available_time_parseable": _to_bool(metadata.get("available_time_parseable")),
        "available_time_timezone_present": _to_bool(
            metadata.get("available_time_timezone_present")
        ),
        "available_time_timezone_policy": _text(metadata.get("available_time_timezone_policy")),
        "available_time_compared_to_decision_time": _to_bool(
            metadata.get("available_time_compared_to_decision_time")
        ),
        "target_csv_opened": _to_bool(metadata.get("target_csv_opened")),
        "real_csv_consumed": _to_bool(metadata.get("real_csv_consumed")),
        "local_file_hash_recomputed": _to_bool(metadata.get("local_file_hash_recomputed")),
        "expected_hash_reverified": _to_bool(metadata.get("expected_hash_reverified")),
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
        "index_csv": root / "source_hash_revision_available_time_index.csv",
        "index_md": root / "source_hash_revision_available_time_index.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: SourceHashRevisionAvailableTimeIndexResult) -> None:
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


def _index_markdown(result: SourceHashRevisionAvailableTimeIndexResult) -> str:
    lines = [
        "# Source Hash Revision Available-Time Index",
        "",
        f"- Artifact count: `{result.artifact_count}`",
        "- This index exposes metadata presence, parseability, preview, and safety flags only.",
        "- It does not expose full source hashes, source bytes, source content, target CSV text, row values, or readiness claims.",
        "",
        "| Run id | Status | Health | Hash preview | Revision type | Available-time parseable |",
        "|---|---|---|---|---|---|",
    ]
    for row in result.rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _text(row.get("run_id")),
                    _text(row.get("runtime_status")),
                    _text(row.get("health_status")),
                    _text(row.get("source_hash_preview")),
                    _text(row.get("revision_id_type")),
                    str(_to_bool(row.get("available_time_parseable"))).lower(),
                ]
            )
            + " |"
        )
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


def _preview(value: Any) -> str:
    return _text(value)[:16]


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

