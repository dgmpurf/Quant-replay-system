"""Health view for CSV physical data-line count-only artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only import (
    ARTIFACT_FILENAMES,
    CSV_HEADER_DEPENDENCY_POLICY,
    CSV_PHYSICAL_DATA_LINE_COUNT_NONE,
    CSV_PHYSICAL_DATA_LINE_COUNT_ONLY,
    CSV_READ_NONE,
    EXPECTED_HASH_VERIFICATION_NONE,
    FILE_TOUCH_NONE,
    LOCAL_FILE_HASH_NONE,
    PHYSICAL_NON_HEADER_LINE_COUNT,
    REQUIRED_FALSE_FLAGS,
    STATUS_COUNT_ONLY_REPORT_ONLY,
    STATUS_NO_INPUT,
    STATUS_WARN_ZERO_DATA_LINES,
    WORKFLOW_STAGE,
    csv_physical_data_line_count_statuses,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_index import (
    DEFAULT_ROOT,
    VIEW_DIR_NAMES,
    build_csv_physical_data_line_count_only_index,
)


HEALTH_COLUMNS = ["run_id", "status", "severity", "issue_code", "message", "artifact_path"]
FORBIDDEN_STATUS_WORDING = [
    "PACKAGE_APPROVED",
    "PACKAGE_ADMISSIBLE",
    "PIT_ADMISSIBLE_PACKAGE",
    "READY_FOR_REPLAY",
    "REPLAY_INPUT_READY",
    "ACTIVE_REPLAY_INPUT_READY",
    "APPROVED_FOR_ACTIVE_INPUT",
    "TRADING_READY",
    "BUY_REVIEW_READY",
    "PERFORMANCE_VALIDATED",
]
FORBIDDEN_TRUE_FIELDS = [
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
DISCLOSURE_MARKERS = [
    "HEADER_SENTINEL",
    "ROW_SENTINEL",
    "FULL_CONTENT_SAMPLE",
    "SOURCE_HASH_EXPECTED_HASH_LOCAL_BYTE_HASH",
    "row_snippet",
    "parsed_field",
    "full_content_sample",
]


@dataclass(frozen=True)
class CsvPhysicalDataLineCountHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    rows: list[dict[str, str]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def check_csv_physical_data_line_count_only_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/health",
) -> CsvPhysicalDataLineCountHealthResult:
    root_path = Path(root)
    index_output = Path(output_dir).parent / "index"
    index = build_csv_physical_data_line_count_only_index(root=root_path, output_dir=index_output)
    issues: list[dict[str, str]] = []
    if not root_path.exists():
        issues.append(_issue("", "WARNING", "ARTIFACT_ROOT_MISSING", "Artifact root is missing.", root_path))
    for artifact_dir in _candidate_dirs(root_path):
        issues.extend(_issues_for_artifact_dir(artifact_dir))
    rows = [_finalize_row(row) for row in issues]
    error_count = sum(1 for row in rows if row["severity"] == "ERROR")
    warning_count = sum(1 for row in rows if row["severity"] == "WARNING")
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = _paths(output_dir)
    result = CsvPhysicalDataLineCountHealthResult(
        status=status,
        checked_artifact_count=index.artifact_count,
        issue_count=len(rows),
        error_count=error_count,
        warning_count=warning_count,
        rows=rows,
        artifact_paths=paths,
        warnings=[] if status == "PASS" else [f"CSV physical data-line count-only health is {status}."],
    )
    _write(result)
    return result


def _issues_for_artifact_dir(artifact_dir: Path) -> list[dict[str, str]]:
    run_id = artifact_dir.name
    issues: list[dict[str, str]] = []
    paths = {key: artifact_dir / filename for key, filename in ARTIFACT_FILENAMES.items()}
    for path in paths.values():
        if not path.exists():
            issues.append(
                _issue(run_id, "ERROR", "MISSING_REQUIRED_ARTIFACT", "Required artifact is missing.", path)
            )
    metadata: dict[str, Any] | None = None
    if paths["metadata"].exists():
        try:
            with paths["metadata"].open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                metadata = loaded
            else:
                issues.append(
                    _issue(run_id, "ERROR", "METADATA_UNREADABLE", "Metadata JSON is not an object.", paths["metadata"])
                )
        except (OSError, json.JSONDecodeError):
            issues.append(
                _issue(run_id, "ERROR", "METADATA_UNREADABLE", "Metadata JSON is unreadable.", paths["metadata"])
            )
    if metadata is not None:
        run_id = str(metadata.get("run_id") or run_id)
        issues.extend(_metadata_issues(run_id, metadata, paths["metadata"]))
    if paths["forbidden_downstream_flags"].exists():
        issues.extend(_safety_flag_issues(run_id, paths["forbidden_downstream_flags"]))
    for path in paths.values():
        if path.exists():
            issues.extend(_text_issues(run_id, path))
    return issues


def _metadata_issues(run_id: str, metadata: dict[str, Any], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    runtime_status = str(metadata.get("runtime_status") or "")
    health_status = str(metadata.get("health_status") or "")
    if runtime_status not in csv_physical_data_line_count_statuses():
        issues.append(_issue(run_id, "ERROR", "INVALID_RUNTIME_STATUS", "runtime_status is invalid.", path))
    if str(metadata.get("workflow_stage") or "") != WORKFLOW_STAGE:
        issues.append(_issue(run_id, "ERROR", "WORKFLOW_STAGE_INVALID", "workflow_stage is invalid.", path))
    for field in ("runtime_status", "workflow_stage", "recommended_next_task"):
        if _has_forbidden_wording(str(metadata.get(field) or "")):
            issues.append(
                _issue(run_id, "ERROR", "FORBIDDEN_STATUS_WORDING", "Live status field contains unsafe wording.", path)
            )
    for field in ("report_only", "diagnostic_only"):
        if not _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "REQUIRED_REPORT_FLAG_FALSE", f"{field} must be true.", path))
    if runtime_status == STATUS_NO_INPUT:
        if str(metadata.get("file_touch_level") or "") != FILE_TOUCH_NONE:
            issues.append(_issue(run_id, "ERROR", "FILE_TOUCH_LEVEL_INVALID", "No-input file touch level invalid.", path))
        if str(metadata.get("csv_read_level") or "") != CSV_READ_NONE:
            issues.append(_issue(run_id, "ERROR", "CSV_READ_LEVEL_INVALID", "No-input read level invalid.", path))
        if str(metadata.get("csv_physical_data_line_count_level") or "") != CSV_PHYSICAL_DATA_LINE_COUNT_NONE:
            issues.append(
                _issue(run_id, "ERROR", "COUNT_LEVEL_INVALID", "No-input count level invalid.", path)
            )
    else:
        if str(metadata.get("file_touch_level") or "") != CSV_PHYSICAL_DATA_LINE_COUNT_ONLY:
            issues.append(_issue(run_id, "ERROR", "FILE_TOUCH_LEVEL_INVALID", "Count mode file touch level invalid.", path))
        if str(metadata.get("csv_read_level") or "") != CSV_PHYSICAL_DATA_LINE_COUNT_ONLY:
            issues.append(_issue(run_id, "ERROR", "CSV_READ_LEVEL_INVALID", "Count mode read level invalid.", path))
        if str(metadata.get("csv_physical_data_line_count_level") or "") != CSV_PHYSICAL_DATA_LINE_COUNT_ONLY:
            issues.append(_issue(run_id, "ERROR", "COUNT_LEVEL_INVALID", "Count mode level invalid.", path))
    if str(metadata.get("local_file_hash_level") or "") != LOCAL_FILE_HASH_NONE:
        issues.append(_issue(run_id, "ERROR", "LOCAL_HASH_LEVEL_INVALID", "Local file hash level invalid.", path))
    if str(metadata.get("expected_hash_verification_level") or "") != EXPECTED_HASH_VERIFICATION_NONE:
        issues.append(
            _issue(run_id, "ERROR", "EXPECTED_HASH_LEVEL_INVALID", "Expected-hash verification level invalid.", path)
        )
    if runtime_status in {STATUS_COUNT_ONLY_REPORT_ONLY, STATUS_WARN_ZERO_DATA_LINES}:
        if str(metadata.get("csv_physical_data_line_count_policy") or "") != PHYSICAL_NON_HEADER_LINE_COUNT:
            issues.append(_issue(run_id, "ERROR", "COUNT_POLICY_INVALID", "Count policy is ambiguous.", path))
        if str(metadata.get("csv_header_dependency_policy") or "") != CSV_HEADER_DEPENDENCY_POLICY:
            issues.append(
                _issue(run_id, "ERROR", "HEADER_DEPENDENCY_POLICY_INVALID", "Header dependency policy is invalid.", path)
            )
        if not _to_bool(metadata.get("csv_physical_data_line_count_computed")):
            issues.append(_issue(run_id, "ERROR", "COUNT_NOT_COMPUTED", "Count status requires computed count.", path))
    if runtime_status == STATUS_WARN_ZERO_DATA_LINES:
        if health_status != "WARN" or _number(metadata.get("csv_physical_data_line_count")) != 0:
            issues.append(_issue(run_id, "ERROR", "ZERO_COUNT_POLICY_INVALID", "Zero-line warning policy invalid.", path))
        else:
            issues.append(
                _issue(run_id, "WARNING", "ZERO_PHYSICAL_DATA_LINES", "Physical data-line count is zero.", path)
            )
    elif health_status == "WARN":
        issues.append(_issue(run_id, "WARNING", "CORE_ARTIFACT_HEALTH_WARN", "Core artifact health is WARN.", path))
    elif health_status == "FAIL":
        issues.append(_issue(run_id, "ERROR", "CORE_ARTIFACT_HEALTH_FAIL", "Core artifact health is FAIL.", path))
    for field in sorted(set(FORBIDDEN_TRUE_FIELDS)):
        if _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{field} is true.", path))
    return issues


def _safety_flag_issues(run_id: str, path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            flags = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return [_issue(run_id, "ERROR", "SAFETY_FLAGS_UNREADABLE", "Safety flags JSON is unreadable.", path)]
    if not isinstance(flags, dict):
        return [_issue(run_id, "ERROR", "SAFETY_FLAGS_UNREADABLE", "Safety flags JSON is not an object.", path)]
    issues: list[dict[str, str]] = []
    for flag in REQUIRED_FALSE_FLAGS:
        if flag not in flags:
            issues.append(_issue(run_id, "ERROR", "MISSING_SAFETY_FLAG", f"{flag} is missing.", path))
        elif _to_bool(flags.get(flag)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_SAFETY_FLAG_TRUE", f"{flag} is true.", path))
    return issues


def _text_issues(run_id: str, path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            text = handle.read()
    except OSError:
        return []
    issues: list[dict[str, str]] = []
    if _has_disclosure_marker(text):
        issues.append(
            _issue(run_id, "ERROR", "ARTIFACT_DISCLOSURE_LEAK", "Artifact contains forbidden disclosure marker.", path)
        )
    if _has_forbidden_wording(text):
        issues.append(
            _issue(run_id, "ERROR", "FORBIDDEN_STATUS_WORDING", "Artifact contains unsafe status wording.", path)
        )
    return issues


def _candidate_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir()
        and path.name not in VIEW_DIR_NAMES
        and not path.name.startswith("_")
        and (path / ARTIFACT_FILENAMES["metadata"]).exists()
    )


def _issue(run_id: str, severity: str, code: str, message: str, path: Path) -> dict[str, str]:
    return {
        "run_id": run_id,
        "status": "FAIL" if severity == "ERROR" else "WARN",
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }


def _finalize_row(row: dict[str, str]) -> dict[str, str]:
    return {column: row.get(column, "") for column in HEALTH_COLUMNS}


def _paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {
        "artifact_dir": root,
        "health_csv": root / "csv_physical_data_line_count_only_health.csv",
        "health_md": root / "csv_physical_data_line_count_only_health.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: CsvPhysicalDataLineCountHealthResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_rows(result.artifact_paths["health_csv"], HEALTH_COLUMNS, result.rows)
    _write_text(result.artifact_paths["health_md"], _health_markdown(result))
    _write_json(
        result.artifact_paths["metadata_json"],
        {
            "status": result.status,
            "checked_artifact_count": result.checked_artifact_count,
            "issue_count": result.issue_count,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "warnings": result.warnings,
        },
    )


def _health_markdown(result: CsvPhysicalDataLineCountHealthResult) -> str:
    lines = [
        "# CSV Physical Data-Line Count-Only Health",
        "",
        f"- Status: `{result.status}`",
        f"- Checked artifact count: `{result.checked_artifact_count}`",
        f"- Error count: `{result.error_count}`",
        f"- Warning count: `{result.warning_count}`",
        "- Views inspect generated artifacts only and do not reopen the source file.",
        "",
        "| Run id | Severity | Issue code |",
        "|---|---|---|",
    ]
    for row in result.rows:
        lines.append(f"| `{row['run_id']}` | `{row['severity']}` | `{row['issue_code']}` |")
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


def _has_forbidden_wording(text: str) -> bool:
    return any(word in text for word in FORBIDDEN_STATUS_WORDING)


def _has_disclosure_marker(text: str) -> bool:
    return any(marker in text for marker in DISCLOSURE_MARKERS)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _number(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
