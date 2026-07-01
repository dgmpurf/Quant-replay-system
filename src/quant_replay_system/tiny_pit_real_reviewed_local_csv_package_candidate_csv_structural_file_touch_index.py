"""Index view for CSV structural header-only file-touch artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch import (
    ARTIFACT_FILENAMES,
    REQUIRED_FALSE_FLAGS,
)


DEFAULT_ROOT = (
    "outputs/reports/manual_diagnostics/"
    "tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch_v0_1"
)
VIEW_DIR_NAMES = {"index", "health", "status"}
INDEX_COLUMNS = [
    "run_id",
    "runtime_status",
    "health_status",
    "workflow_stage",
    "artifact_path",
    "report_path",
    "file_touch_level",
    "csv_read_level",
    "local_file_hash_level",
    "csv_file_opened_structurally",
    "csv_header_read",
    "csv_header_column_count",
    "csv_row_count_computed",
    "local_file_byte_hash_computed",
    "real_csv_consumed",
    *REQUIRED_FALSE_FLAGS,
]


@dataclass(frozen=True)
class CsvStructuralFileTouchIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_csv_structural_file_touch_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/index",
) -> CsvStructuralFileTouchIndexResult:
    root_path = Path(root)
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not root_path.exists():
        warnings.append(f"CSV structural file-touch root does not exist: {root_path}")
    else:
        for artifact_dir in _candidate_dirs(root_path):
            row = _row_from_artifact_dir(artifact_dir)
            if row:
                rows.append(row)
    frame = _finalize(pd.DataFrame(rows))
    paths = _paths(output_dir)
    result = CsvStructuralFileTouchIndexResult(
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
        "report_path": str(artifact_dir / ARTIFACT_FILENAMES["report"]),
        "file_touch_level": _text(metadata.get("file_touch_level")),
        "csv_read_level": _text(metadata.get("csv_read_level")),
        "local_file_hash_level": _text(metadata.get("local_file_hash_level")),
        "csv_file_opened_structurally": _to_bool(metadata.get("csv_file_opened_structurally")),
        "csv_header_read": _to_bool(metadata.get("csv_header_read")),
        "csv_header_column_count": _to_int(metadata.get("csv_header_column_count")),
        "csv_row_count_computed": _to_bool(metadata.get("csv_row_count_computed")),
        "local_file_byte_hash_computed": _to_bool(metadata.get("local_file_byte_hash_computed")),
        "real_csv_consumed": _to_bool(metadata.get("real_csv_consumed")),
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
    return {"artifact_dir": root, "index_csv": root / "csv_structural_file_touch_index.csv", "metadata_json": root / "metadata.json"}


def _write(result: CsvStructuralFileTouchIndexResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(result.artifact_paths["index_csv"], index=False)
    metadata = {
        "artifact_count": result.artifact_count,
        "status": "PASS",
        "warnings": result.warnings,
        "index_csv": str(result.artifact_paths["index_csv"]),
    }
    result.artifact_paths["metadata_json"].write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
