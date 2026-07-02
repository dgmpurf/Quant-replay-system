"""Status view for Expected-Hash Verification artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification import (
    CSV_READ_NONE,
    EXPECTED_HASH_VERIFICATION_NONE,
    FILE_TOUCH_NONE,
    LOCAL_FILE_HASH_NONE,
    STATUS_NO_INPUT,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification_health import (
    check_expected_hash_verification_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification_index import (
    DEFAULT_ROOT,
    build_expected_hash_verification_index,
)


NO_ARTIFACT_STAGE = "NO_TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_EXPECTED_HASH_VERIFICATION"
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Expected-Hash Verification "
    "Checkpoint Planning Report-Only v0.1"
)


@dataclass(frozen=True)
class ExpectedHashVerificationStatusResult:
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
    latest_expected_hash_verification_level: str
    latest_expected_hash_verification_performed: bool
    latest_expected_hash_algorithm: str
    latest_expected_hash_present: bool
    latest_expected_hash_preview: str
    latest_actual_local_file_byte_hash_algorithm: str
    latest_actual_local_file_byte_hash_preview: str
    latest_expected_hash_matched: bool
    latest_expected_hash_mismatch: bool
    latest_expected_hash_verified_against_local_metadata: bool
    latest_expected_hash_verified_against_source_hash: bool
    latest_local_file_byte_hash_recomputed: bool
    latest_target_file_opened_for_expected_hash_verification: bool
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
    latest_actionable_mismatch: bool
    recommended_next_task: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]


def run_expected_hash_verification_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/status",
) -> ExpectedHashVerificationStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_expected_hash_verification_index(root=root, output_dir=sibling_root / "index")
    health = check_expected_hash_verification_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        summary = _no_artifact_summary(health.status)
    else:
        latest = index.index_frame.sort_values(["run_id"]).iloc[-1].to_dict()
        summary = _summary_from_latest(latest, health.status)
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary])
    result = ExpectedHashVerificationStatusResult(
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health.status == "PASS" else [f"Expected-hash verification health is {health.status}."],
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
        "latest_expected_hash_verification_level": _text(latest.get("expected_hash_verification_level")),
        "latest_expected_hash_verification_performed": _to_bool(
            latest.get("expected_hash_verification_performed")
        ),
        "latest_expected_hash_algorithm": _text(latest.get("expected_hash_algorithm")),
        "latest_expected_hash_present": _to_bool(latest.get("expected_hash_present")),
        "latest_expected_hash_preview": _text(latest.get("expected_hash_preview")),
        "latest_actual_local_file_byte_hash_algorithm": _text(
            latest.get("actual_local_file_byte_hash_algorithm")
        ),
        "latest_actual_local_file_byte_hash_preview": _text(
            latest.get("actual_local_file_byte_hash_preview")
        ),
        "latest_expected_hash_matched": _to_bool(latest.get("expected_hash_matched")),
        "latest_expected_hash_mismatch": _to_bool(latest.get("expected_hash_mismatch")),
        "latest_expected_hash_verified_against_local_metadata": _to_bool(
            latest.get("expected_hash_verified_against_local_metadata")
        ),
        "latest_expected_hash_verified_against_source_hash": _to_bool(
            latest.get("expected_hash_verified_against_source_hash")
        ),
        "latest_local_file_byte_hash_recomputed": _to_bool(latest.get("local_file_byte_hash_recomputed")),
        "latest_target_file_opened_for_expected_hash_verification": _to_bool(
            latest.get("target_file_opened_for_expected_hash_verification")
        ),
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
        "latest_actionable_mismatch": _to_bool(latest.get("actionable_mismatch")),
        "recommended_next_task": NEXT_TASK,
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
        "latest_expected_hash_verification_level": EXPECTED_HASH_VERIFICATION_NONE,
        "latest_expected_hash_verification_performed": False,
        "latest_expected_hash_algorithm": "",
        "latest_expected_hash_present": False,
        "latest_expected_hash_preview": "",
        "latest_actual_local_file_byte_hash_algorithm": "",
        "latest_actual_local_file_byte_hash_preview": "",
        "latest_expected_hash_matched": False,
        "latest_expected_hash_mismatch": False,
        "latest_expected_hash_verified_against_local_metadata": False,
        "latest_expected_hash_verified_against_source_hash": False,
        "latest_local_file_byte_hash_recomputed": False,
        "latest_target_file_opened_for_expected_hash_verification": False,
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
        "latest_actionable_mismatch": False,
        "recommended_next_task": NEXT_TASK,
    }


def _paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {
        "artifact_dir": root,
        "status_csv": root / "expected_hash_verification_status.csv",
        "status_md": root / "expected_hash_verification_status.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: ExpectedHashVerificationStatusResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(result.artifact_paths["status_csv"], index=False)
    result.artifact_paths["status_md"].write_text(_status_markdown(result), encoding="utf-8")
    metadata = result.summary_frame.iloc[0].to_dict()
    result.artifact_paths["metadata_json"].write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _status_markdown(result: ExpectedHashVerificationStatusResult) -> str:
    return "\n".join(
        [
            "# Expected-Hash Verification Status",
            "",
            f"- Latest run id: `{result.latest_run_id}`",
            f"- Latest runtime status: `{result.latest_runtime_status}`",
            f"- Latest health status: `{result.latest_health_status}`",
            f"- Latest workflow stage: `{result.latest_workflow_stage}`",
            f"- Expected hash preview: `{result.latest_expected_hash_preview}`",
            f"- Actual local file byte hash preview: `{result.latest_actual_local_file_byte_hash_preview}`",
            f"- Expected hash matched: `{str(result.latest_expected_hash_matched).lower()}`",
            f"- Expected hash mismatch: `{str(result.latest_expected_hash_mismatch).lower()}`",
            f"- CSV read level: `{result.latest_csv_read_level}`",
            "- Target file opened for expected-hash verification: `false`",
            "- Local file byte hash recomputed: `false`",
            "- CSV header read: `false`",
            "- CSV row count computed: `false`",
            "- CSV values read: `false`",
            "- CSV full content read: `false`",
            "- Real CSV consumed: `false`",
            "- Source hash validated: `false`",
            "- Revision id validated: `false`",
            "- Available time validated: `false`",
            "- PIT admissibility validated: `false`",
            "- Reviewer authority validated: `false`",
            "- Active replay input: `false`",
            "- Trading allowed: `false`",
            "- Buy review allowed: `false`",
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
