"""Status view for CSV structural header-only file-touch artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch import (
    REQUIRED_FALSE_FLAGS,
    STATUS_NO_INPUT,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch_health import (
    check_csv_structural_file_touch_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch_index import (
    DEFAULT_ROOT,
    build_csv_structural_file_touch_index,
)


NO_ARTIFACT_STAGE = "NO_TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_CSV_STRUCTURAL_FILE_TOUCH"
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Structural Header-Only "
    "CLI Report-Only v0.1"
)


@dataclass(frozen=True)
class CsvStructuralFileTouchStatusResult:
    latest_run_id: str
    latest_runtime_status: str
    latest_health_status: str
    latest_workflow_stage: str
    latest_artifact_path: str
    latest_report_path: str
    file_touch_level: str
    csv_read_level: str
    local_file_hash_level: str
    csv_file_opened_structurally: bool
    csv_header_read: bool
    csv_header_column_count: int
    csv_row_count_computed: bool
    csv_row_count: str
    csv_values_read: bool
    csv_full_content_read: bool
    local_file_byte_hash_computed: bool
    local_file_byte_hash_algorithm: str
    real_csv_consumed: bool
    recommended_next_task: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    real_package_candidate_created: bool
    active_reviewed_input_candidate_created: bool
    real_replay_input_created: bool
    active_replay_input: bool
    active_replay_ready: bool
    active_replay_input_ready_emitted: bool
    replay_execution_allowed: bool
    trading_allowed: bool
    buy_review_allowed: bool
    data_raw_written: bool
    data_processed_written: bool
    data_cache_written: bool


def run_csv_structural_file_touch_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/status",
) -> CsvStructuralFileTouchStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_csv_structural_file_touch_index(root=root, output_dir=sibling_root / "index")
    health = check_csv_structural_file_touch_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        summary = _no_artifact_summary(health.status)
    else:
        latest = index.index_frame.sort_values(["run_id"]).iloc[-1].to_dict()
        summary = _summary_from_latest(latest, health.status)
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary])
    result = CsvStructuralFileTouchStatusResult(
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health.status == "PASS" else [f"CSV structural file-touch health is {health.status}."],
        **summary,
    )
    _write(result)
    return result


def _summary_from_latest(latest: dict[str, Any], health_status: str) -> dict[str, Any]:
    runtime_status = "FAIL" if health_status == "FAIL" else _text(latest.get("runtime_status"))
    metadata = _metadata_for_latest(latest)
    return {
        "latest_run_id": _text(latest.get("run_id")),
        "latest_runtime_status": runtime_status,
        "latest_health_status": health_status,
        "latest_workflow_stage": _text(latest.get("workflow_stage")),
        "latest_artifact_path": _text(latest.get("artifact_path")),
        "latest_report_path": _text(latest.get("report_path")),
        "file_touch_level": _text(latest.get("file_touch_level")),
        "csv_read_level": _text(latest.get("csv_read_level")),
        "local_file_hash_level": _text(latest.get("local_file_hash_level")),
        "csv_file_opened_structurally": _to_bool(latest.get("csv_file_opened_structurally")),
        "csv_header_read": _to_bool(latest.get("csv_header_read")),
        "csv_header_column_count": _to_int(latest.get("csv_header_column_count")),
        "csv_row_count_computed": _to_bool(latest.get("csv_row_count_computed")),
        "csv_row_count": _text(metadata.get("csv_row_count")),
        "csv_values_read": _to_bool(metadata.get("csv_values_read")),
        "csv_full_content_read": _to_bool(metadata.get("csv_full_content_read")),
        "local_file_byte_hash_computed": _to_bool(latest.get("local_file_byte_hash_computed")),
        "local_file_byte_hash_algorithm": _text(metadata.get("local_file_byte_hash_algorithm")),
        "real_csv_consumed": _to_bool(latest.get("real_csv_consumed")),
        "recommended_next_task": NEXT_TASK if health_status == "PASS" else "Repair CSV structural header-only artifacts.",
        **{flag: _to_bool(latest.get(flag)) for flag in REQUIRED_FALSE_FLAGS},
    }


def _no_artifact_summary(health_status: str) -> dict[str, Any]:
    return {
        "latest_run_id": "",
        "latest_runtime_status": STATUS_NO_INPUT,
        "latest_health_status": health_status,
        "latest_workflow_stage": NO_ARTIFACT_STAGE,
        "latest_artifact_path": "",
        "latest_report_path": "",
        "file_touch_level": "FILE_TOUCH_NONE",
        "csv_read_level": "CSV_READ_NONE",
        "local_file_hash_level": "LOCAL_FILE_HASH_NONE",
        "csv_file_opened_structurally": False,
        "csv_header_read": False,
        "csv_header_column_count": 0,
        "csv_row_count_computed": False,
        "csv_row_count": "",
        "csv_values_read": False,
        "csv_full_content_read": False,
        "local_file_byte_hash_computed": False,
        "local_file_byte_hash_algorithm": "",
        "real_csv_consumed": False,
        "recommended_next_task": NEXT_TASK,
        **{flag: False for flag in REQUIRED_FALSE_FLAGS},
    }


def _paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {"artifact_dir": root, "status_csv": root / "csv_structural_file_touch_status.csv", "metadata_json": root / "metadata.json"}


def _metadata_for_latest(latest: dict[str, Any]) -> dict[str, Any]:
    metadata_path = Path(_text(latest.get("artifact_path"))) / "metadata.json"
    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _write(result: CsvStructuralFileTouchStatusResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(result.artifact_paths["status_csv"], index=False)
    metadata = result.summary_frame.iloc[0].to_dict()
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
