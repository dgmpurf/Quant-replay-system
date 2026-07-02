"""Status view for Local File Byte-Hash-Only artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only import (
    CSV_READ_NONE,
    FILE_TOUCH_NONE,
    LOCAL_FILE_HASH_NONE,
    REQUIRED_FALSE_FLAGS,
    STATUS_NO_INPUT,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only_health import (
    check_local_file_byte_hash_only_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only_index import (
    DEFAULT_ROOT,
    build_local_file_byte_hash_only_index,
)


NO_ARTIFACT_STAGE = "NO_TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_LOCAL_FILE_BYTE_HASH_ONLY"
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Local File Byte-Hash-Only "
    "Checkpoint Planning Report-Only v0.1"
)


@dataclass(frozen=True)
class LocalFileByteHashOnlyStatusResult:
    latest_run_id: str
    latest_runtime_status: str
    latest_health_status: str
    latest_workflow_stage: str
    latest_artifact_path: str
    latest_report_path: str
    latest_metadata_path: str
    latest_summary_path: str
    latest_file_touch_level: str
    latest_csv_read_level: str
    latest_local_file_hash_level: str
    latest_local_file_byte_hash_computed: bool
    latest_local_file_byte_hash_algorithm: str
    latest_local_file_byte_hash_preview: str
    latest_local_file_byte_hash_disclosure_level: str
    latest_local_file_byte_hash_full_recorded_in_metadata: bool
    latest_local_file_byte_hash_verified_against_manifest: bool
    latest_local_file_byte_hash_expected_present: bool
    latest_csv_header_read: bool
    latest_csv_row_count_computed: bool
    latest_csv_values_read: bool
    latest_csv_full_content_read: bool
    latest_real_csv_consumed: bool
    latest_source_hash_validated: bool
    latest_revision_id_validated: bool
    latest_available_time_validated: bool
    latest_pit_admissibility_validated: bool
    latest_source_reliability_scored: bool
    latest_reviewer_authority_validated: bool
    latest_active_replay_input: bool
    latest_trading_allowed: bool
    latest_buy_review_allowed: bool
    latest_data_raw_written: bool
    latest_data_processed_written: bool
    latest_data_cache_written: bool
    recommended_next_task: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]


def run_local_file_byte_hash_only_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/status",
) -> LocalFileByteHashOnlyStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_local_file_byte_hash_only_index(root=root, output_dir=sibling_root / "index")
    health = check_local_file_byte_hash_only_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        summary = _no_artifact_summary(health.status)
    else:
        latest = index.index_frame.sort_values(["run_id"]).iloc[-1].to_dict()
        summary = _summary_from_latest(latest, health.status)
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary])
    result = LocalFileByteHashOnlyStatusResult(
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health.status == "PASS" else [f"Local file byte-hash-only health is {health.status}."],
        **summary,
    )
    _write(result)
    return result


def _summary_from_latest(latest: dict[str, Any], health_status: str) -> dict[str, Any]:
    runtime_status = "FAIL" if health_status == "FAIL" else _text(latest.get("runtime_status"))
    return {
        "latest_run_id": _text(latest.get("run_id")),
        "latest_runtime_status": runtime_status,
        "latest_health_status": health_status,
        "latest_workflow_stage": _text(latest.get("workflow_stage")),
        "latest_artifact_path": _text(latest.get("artifact_path")),
        "latest_report_path": _text(latest.get("report_path")),
        "latest_metadata_path": _text(latest.get("metadata_path")),
        "latest_summary_path": _text(latest.get("summary_path")),
        "latest_file_touch_level": _text(latest.get("file_touch_level")),
        "latest_csv_read_level": _text(latest.get("csv_read_level")),
        "latest_local_file_hash_level": _text(latest.get("local_file_hash_level")),
        "latest_local_file_byte_hash_computed": _to_bool(latest.get("local_file_byte_hash_computed")),
        "latest_local_file_byte_hash_algorithm": _text(latest.get("local_file_byte_hash_algorithm")),
        "latest_local_file_byte_hash_preview": _text(latest.get("local_file_byte_hash_preview")),
        "latest_local_file_byte_hash_disclosure_level": _text(latest.get("local_file_byte_hash_disclosure_level")),
        "latest_local_file_byte_hash_full_recorded_in_metadata": _to_bool(
            latest.get("local_file_byte_hash_full_recorded_in_metadata")
        ),
        "latest_local_file_byte_hash_verified_against_manifest": _to_bool(
            latest.get("local_file_byte_hash_verified_against_manifest")
        ),
        "latest_local_file_byte_hash_expected_present": _to_bool(latest.get("local_file_byte_hash_expected_present")),
        "latest_csv_header_read": _to_bool(latest.get("csv_header_read")),
        "latest_csv_row_count_computed": _to_bool(latest.get("csv_row_count_computed")),
        "latest_csv_values_read": _to_bool(latest.get("csv_values_read")),
        "latest_csv_full_content_read": _to_bool(latest.get("csv_full_content_read")),
        "latest_real_csv_consumed": _to_bool(latest.get("real_csv_consumed")),
        "latest_source_hash_validated": _to_bool(latest.get("source_hash_validated")),
        "latest_revision_id_validated": _to_bool(latest.get("revision_id_validated")),
        "latest_available_time_validated": _to_bool(latest.get("available_time_validated")),
        "latest_pit_admissibility_validated": _to_bool(latest.get("pit_admissibility_validated")),
        "latest_source_reliability_scored": _to_bool(latest.get("source_reliability_scored")),
        "latest_reviewer_authority_validated": _to_bool(latest.get("reviewer_authority_validated")),
        "latest_active_replay_input": _to_bool(latest.get("active_replay_input")),
        "latest_trading_allowed": _to_bool(latest.get("trading_allowed")),
        "latest_buy_review_allowed": _to_bool(latest.get("buy_review_allowed")),
        "latest_data_raw_written": _to_bool(latest.get("data_raw_written")),
        "latest_data_processed_written": _to_bool(latest.get("data_processed_written")),
        "latest_data_cache_written": _to_bool(latest.get("data_cache_written")),
        "recommended_next_task": NEXT_TASK if health_status == "PASS" else "Repair Local File Byte-Hash-Only artifacts.",
    }


def _no_artifact_summary(health_status: str) -> dict[str, Any]:
    return {
        "latest_run_id": "",
        "latest_runtime_status": STATUS_NO_INPUT,
        "latest_health_status": health_status,
        "latest_workflow_stage": NO_ARTIFACT_STAGE,
        "latest_artifact_path": "",
        "latest_report_path": "",
        "latest_metadata_path": "",
        "latest_summary_path": "",
        "latest_file_touch_level": FILE_TOUCH_NONE,
        "latest_csv_read_level": CSV_READ_NONE,
        "latest_local_file_hash_level": LOCAL_FILE_HASH_NONE,
        "latest_local_file_byte_hash_computed": False,
        "latest_local_file_byte_hash_algorithm": "",
        "latest_local_file_byte_hash_preview": "",
        "latest_local_file_byte_hash_disclosure_level": "",
        "latest_local_file_byte_hash_full_recorded_in_metadata": False,
        "latest_local_file_byte_hash_verified_against_manifest": False,
        "latest_local_file_byte_hash_expected_present": False,
        "latest_csv_header_read": False,
        "latest_csv_row_count_computed": False,
        "latest_csv_values_read": False,
        "latest_csv_full_content_read": False,
        "latest_real_csv_consumed": False,
        "latest_source_hash_validated": False,
        "latest_revision_id_validated": False,
        "latest_available_time_validated": False,
        "latest_pit_admissibility_validated": False,
        "latest_source_reliability_scored": False,
        "latest_reviewer_authority_validated": False,
        "latest_active_replay_input": False,
        "latest_trading_allowed": False,
        "latest_buy_review_allowed": False,
        "latest_data_raw_written": False,
        "latest_data_processed_written": False,
        "latest_data_cache_written": False,
        "recommended_next_task": NEXT_TASK,
    }


def _paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {
        "artifact_dir": root,
        "status_csv": root / "local_file_byte_hash_only_status.csv",
        "status_md": root / "local_file_byte_hash_only_status.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: LocalFileByteHashOnlyStatusResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(result.artifact_paths["status_csv"], index=False)
    result.artifact_paths["status_md"].write_text(_status_markdown(result), encoding="utf-8")
    metadata = result.summary_frame.iloc[0].to_dict()
    result.artifact_paths["metadata_json"].write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _status_markdown(result: LocalFileByteHashOnlyStatusResult) -> str:
    return "\n".join(
        [
            "# Local File Byte-Hash-Only Status",
            "",
            f"- Latest run id: `{result.latest_run_id}`",
            f"- Latest runtime status: `{result.latest_runtime_status}`",
            f"- Latest health status: `{result.latest_health_status}`",
            f"- Latest workflow stage: `{result.latest_workflow_stage}`",
            f"- Hash preview: `{result.latest_local_file_byte_hash_preview}`",
            f"- CSV read level: `{result.latest_csv_read_level}`",
            "- CSV header read: `false`",
            "- CSV row count computed: `false`",
            "- CSV values read: `false`",
            "- CSV full content read: `false`",
            "- Real CSV consumed: `false`",
            "- Active replay input: `false`",
            "- Trading allowed: `false`",
            f"- Recommended next task: `{result.recommended_next_task}`",
            "",
        ]
    )


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)
