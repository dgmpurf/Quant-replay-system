"""Status view for CSV physical data-line count-only artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only import (
    CSV_PHYSICAL_DATA_LINE_COUNT_NONE,
    CSV_READ_NONE,
    EXPECTED_HASH_VERIFICATION_NONE,
    FILE_TOUCH_NONE,
    LOCAL_FILE_HASH_NONE,
    REQUIRED_FALSE_FLAGS,
    STATUS_NO_INPUT,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_health import (
    check_csv_physical_data_line_count_only_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_index import (
    DEFAULT_ROOT,
    build_csv_physical_data_line_count_only_index,
)


NO_ARTIFACT_STAGE = "NO_TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_CSV_PHYSICAL_DATA_LINE_COUNT_ONLY"
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Physical Data-Line "
    "Count-Only Research-Status Planning Report-Only v0.1"
)
STATUS_NEGATIVE_PROOF_FIELDS = [
    "csv_header_read",
    "csv_header_values_recorded",
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
    "latest_file_touch_level",
    "latest_csv_read_level",
    "latest_local_file_hash_level",
    "latest_expected_hash_verification_level",
    "latest_csv_physical_data_line_count_level",
    "latest_csv_physical_data_line_count_computed",
    "latest_csv_physical_data_line_count",
    "latest_csv_physical_data_line_count_policy",
    "latest_csv_physical_line_count_total",
    "latest_csv_header_dependency_policy",
    "latest_header_metadata_reused",
    "latest_csv_header_read",
    "latest_csv_header_values_recorded",
    "latest_csv_header_line_skipped_by_policy",
    "latest_target_csv_opened_for_physical_data_line_count",
    "latest_csv_values_read",
    "latest_csv_value_fields_parsed",
    "latest_csv_row_values_stored",
    "latest_csv_full_content_semantically_read",
    "latest_csv_full_content_read",
    "latest_real_csv_consumed",
    "latest_local_file_byte_hash_computed",
    "latest_local_file_byte_hash_recomputed",
    "latest_expected_hash_verification_performed",
    "latest_expected_hash_verified_against_local_metadata",
    "latest_expected_hash_verified_against_source_hash",
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
    "recommended_next_task",
]


@dataclass(frozen=True)
class CsvPhysicalDataLineCountStatusResult:
    latest_run_id: str
    latest_runtime_status: str
    latest_health_status: str
    latest_workflow_stage: str
    latest_artifact_path: str
    latest_report_path: str
    latest_metadata_path: str
    latest_summary_path: str
    latest_csv_physical_data_line_count: int | str
    latest_csv_physical_data_line_count_policy: str
    recommended_next_task: str
    summary: dict[str, Any]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def run_csv_physical_data_line_count_only_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/status",
) -> CsvPhysicalDataLineCountStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_csv_physical_data_line_count_only_index(root=root, output_dir=sibling_root / "index")
    health = check_csv_physical_data_line_count_only_health(root=root, output_dir=sibling_root / "health")
    if not index.rows:
        summary = _no_artifact_summary(health.status)
    else:
        latest = sorted(index.rows, key=lambda row: str(row.get("run_id") or ""))[-1]
        summary = _summary_from_latest(latest, health.status)
    paths = _paths(output_dir)
    result = CsvPhysicalDataLineCountStatusResult(
        latest_run_id=str(summary["latest_run_id"]),
        latest_runtime_status=str(summary["latest_runtime_status"]),
        latest_health_status=str(summary["latest_health_status"]),
        latest_workflow_stage=str(summary["latest_workflow_stage"]),
        latest_artifact_path=str(summary["latest_artifact_path"]),
        latest_report_path=str(summary["latest_report_path"]),
        latest_metadata_path=str(summary["latest_metadata_path"]),
        latest_summary_path=str(summary["latest_summary_path"]),
        latest_csv_physical_data_line_count=summary["latest_csv_physical_data_line_count"],
        latest_csv_physical_data_line_count_policy=str(
            summary["latest_csv_physical_data_line_count_policy"]
        ),
        recommended_next_task=NEXT_TASK,
        summary=summary,
        artifact_paths=paths,
        warnings=[] if health.status == "PASS" else [f"CSV physical data-line count-only health is {health.status}."],
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
        "latest_file_touch_level": _text(latest.get("file_touch_level")),
        "latest_csv_read_level": _text(latest.get("csv_read_level")),
        "latest_local_file_hash_level": _text(latest.get("local_file_hash_level")),
        "latest_expected_hash_verification_level": _text(latest.get("expected_hash_verification_level")),
        "latest_csv_physical_data_line_count_level": _text(
            latest.get("csv_physical_data_line_count_level")
        ),
        "latest_csv_physical_data_line_count_computed": _to_bool(
            latest.get("csv_physical_data_line_count_computed")
        ),
        "latest_csv_physical_data_line_count": _value(latest.get("csv_physical_data_line_count")),
        "latest_csv_physical_data_line_count_policy": _text(
            latest.get("csv_physical_data_line_count_policy")
        ),
        "latest_csv_physical_line_count_total": _value(latest.get("csv_physical_line_count_total")),
        "latest_csv_header_dependency_policy": _text(latest.get("csv_header_dependency_policy")),
        "latest_header_metadata_reused": _to_bool(latest.get("header_metadata_reused")),
        "latest_csv_header_read": _to_bool(latest.get("csv_header_read")),
        "latest_csv_header_values_recorded": _to_bool(latest.get("csv_header_values_recorded")),
        "latest_csv_header_line_skipped_by_policy": _to_bool(
            latest.get("csv_header_line_skipped_by_policy")
        ),
        "latest_target_csv_opened_for_physical_data_line_count": _to_bool(
            latest.get("target_csv_opened_for_physical_data_line_count")
        ),
        "latest_csv_values_read": _to_bool(latest.get("csv_values_read")),
        "latest_csv_value_fields_parsed": _to_bool(latest.get("csv_value_fields_parsed")),
        "latest_csv_row_values_stored": _to_bool(latest.get("csv_row_values_stored")),
        "latest_csv_full_content_semantically_read": _to_bool(
            latest.get("csv_full_content_semantically_read")
        ),
        "latest_csv_full_content_read": _to_bool(latest.get("csv_full_content_read")),
        "latest_real_csv_consumed": _to_bool(latest.get("real_csv_consumed")),
        "latest_local_file_byte_hash_computed": _to_bool(
            latest.get("local_file_byte_hash_computed")
        ),
        "latest_local_file_byte_hash_recomputed": _to_bool(
            latest.get("local_file_byte_hash_recomputed")
        ),
        "latest_expected_hash_verification_performed": _to_bool(
            latest.get("expected_hash_verification_performed")
        ),
        "latest_expected_hash_verified_against_local_metadata": _to_bool(
            latest.get("expected_hash_verified_against_local_metadata")
        ),
        "latest_expected_hash_verified_against_source_hash": _to_bool(
            latest.get("expected_hash_verified_against_source_hash")
        ),
        "latest_source_hash_validated": _to_bool(latest.get("source_hash_validated")),
        "latest_revision_id_validated": _to_bool(latest.get("revision_id_validated")),
        "latest_available_time_validated": _to_bool(latest.get("available_time_validated")),
        "latest_pit_admissibility_validated": _to_bool(latest.get("pit_admissibility_validated")),
        "latest_source_reliability_scored": _to_bool(latest.get("source_reliability_scored")),
        "latest_reviewer_authority_validated": _to_bool(latest.get("reviewer_authority_validated")),
        "latest_issue_count": _value(latest.get("issue_count")),
        "latest_warning_count": _value(latest.get("warning_count")),
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
        "latest_file_touch_level": FILE_TOUCH_NONE,
        "latest_csv_read_level": CSV_READ_NONE,
        "latest_local_file_hash_level": LOCAL_FILE_HASH_NONE,
        "latest_expected_hash_verification_level": EXPECTED_HASH_VERIFICATION_NONE,
        "latest_csv_physical_data_line_count_level": CSV_PHYSICAL_DATA_LINE_COUNT_NONE,
        "latest_csv_physical_data_line_count_computed": False,
        "latest_csv_physical_data_line_count": "",
        "latest_csv_physical_data_line_count_policy": "",
        "latest_csv_physical_line_count_total": "",
        "latest_csv_header_dependency_policy": "",
        "latest_header_metadata_reused": False,
        "latest_csv_header_read": False,
        "latest_csv_header_values_recorded": False,
        "latest_csv_header_line_skipped_by_policy": False,
        "latest_target_csv_opened_for_physical_data_line_count": False,
        "latest_csv_values_read": False,
        "latest_csv_value_fields_parsed": False,
        "latest_csv_row_values_stored": False,
        "latest_csv_full_content_semantically_read": False,
        "latest_csv_full_content_read": False,
        "latest_real_csv_consumed": False,
        "latest_local_file_byte_hash_computed": False,
        "latest_local_file_byte_hash_recomputed": False,
        "latest_expected_hash_verification_performed": False,
        "latest_expected_hash_verified_against_local_metadata": False,
        "latest_expected_hash_verified_against_source_hash": False,
        "latest_source_hash_validated": False,
        "latest_revision_id_validated": False,
        "latest_available_time_validated": False,
        "latest_pit_admissibility_validated": False,
        "latest_source_reliability_scored": False,
        "latest_reviewer_authority_validated": False,
        "latest_issue_count": "",
        "latest_warning_count": "",
        "recommended_next_task": NEXT_TASK,
    }
    summary.update({f"latest_{field}": False for field in REQUIRED_FALSE_FLAGS})
    summary.update({field: False for field in STATUS_NEGATIVE_PROOF_FIELDS})
    return _finalize_summary(summary)


def _finalize_summary(summary: dict[str, Any]) -> dict[str, Any]:
    for column in STATUS_COLUMNS:
        summary.setdefault(column, "")
    return summary


def _paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {
        "artifact_dir": root,
        "status_csv": root / "csv_physical_data_line_count_only_status.csv",
        "status_md": root / "csv_physical_data_line_count_only_status.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: CsvPhysicalDataLineCountStatusResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_rows(result.artifact_paths["status_csv"], STATUS_COLUMNS, [result.summary])
    _write_text(result.artifact_paths["status_md"], _status_markdown(result))
    _write_json(result.artifact_paths["metadata_json"], result.summary)


def _status_markdown(result: CsvPhysicalDataLineCountStatusResult) -> str:
    return "\n".join(
        [
            "# CSV Physical Data-Line Count-Only Status",
            "",
            f"- Latest run id: `{result.latest_run_id}`",
            f"- Latest runtime status: `{result.latest_runtime_status}`",
            f"- Latest health status: `{result.latest_health_status}`",
            f"- Latest workflow stage: `{result.latest_workflow_stage}`",
            f"- Physical data-line count: `{result.latest_csv_physical_data_line_count}`",
            f"- Count policy: `{result.latest_csv_physical_data_line_count_policy}`",
            "- Report-only: `true`",
            "- Diagnostic-only: `true`",
            "- CSV values read: `false`",
            "- Parsed fields stored: `false`",
            "- Full content read: `false`",
            "- Local file byte fingerprint recomputed: `false`",
            "- Expected fingerprint verification performed: `false`",
            "- Source/PIT/reviewer validation performed: `false`",
            "- Package/replay/buy/trading/data-write flags: `false`",
            "",
            f"Recommended next task: {result.recommended_next_task}",
        ]
    ) + "\n"


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
