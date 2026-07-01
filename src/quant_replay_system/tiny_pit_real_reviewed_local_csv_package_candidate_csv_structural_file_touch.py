"""CSV structural file-touch core for Tiny PIT reviewed LOCAL_CSV candidates.

This module is report-only and diagnostic-only. The first implementation slice
supports only a top-level JSON manifest that explicitly allows a header-only
structural read of a local CSV file under caller-provided roots. It does not
count rows, read data values, compute byte hashes, create package candidates,
create replay inputs, run replay, create downstream artifacts, or enable
buy-review/trading behavior.
"""

from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence


STATUS_NO_INPUT = "NO_CSV_STRUCTURAL_FILE_TOUCH_INPUT"
STATUS_HEADER_ONLY_REPORT_ONLY = "CSV_STRUCTURAL_HEADER_ONLY_REPORT_ONLY"
STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG = "CSV_STRUCTURAL_FILE_TOUCH_BLOCKED_BY_MISSING_ALLOW_FLAG"
STATUS_BLOCKED_BY_MANIFEST_SCHEMA = "CSV_STRUCTURAL_FILE_TOUCH_BLOCKED_BY_MANIFEST_SCHEMA"
STATUS_BLOCKED_BY_PATH_GUARD = "CSV_STRUCTURAL_FILE_TOUCH_BLOCKED_BY_PATH_GUARD"
STATUS_BLOCKED_BY_UNSUPPORTED_TOUCH_LEVEL = "CSV_STRUCTURAL_FILE_TOUCH_BLOCKED_BY_UNSUPPORTED_TOUCH_LEVEL"
STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM = "CSV_STRUCTURAL_FILE_TOUCH_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"

WORKFLOW_NAME = "tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch"
WORKFLOW_STAGE = (
    "TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_"
    "CSV_STRUCTURAL_HEADER_ONLY_CORE_CREATED_REPORT_ONLY"
)
CREATED_AT = "2026-07-01T00:00:00Z"
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Structural Header-Only "
    "Artifact Views Report-Only v0.1"
)

FILE_TOUCH_NONE = "FILE_TOUCH_NONE"
FILE_TOUCH_HEADER_ONLY = "CSV_STRUCTURAL_HEADER_ONLY"
CSV_READ_NONE = "CSV_READ_NONE"
CSV_READ_HEADER_ONLY = "CSV_HEADER_ONLY"
LOCAL_FILE_HASH_NONE = "LOCAL_FILE_HASH_NONE"
SUPPORTED_HEADER_ONLY_LEVELS = (FILE_TOUCH_HEADER_ONLY, CSV_READ_HEADER_ONLY, LOCAL_FILE_HASH_NONE)

ARTIFACT_FILENAMES = {
    "metadata": "metadata.json",
    "report": "csv_structural_file_touch_report.md",
    "limitations": "limitations.md",
    "issues": "issues.csv",
    "summary": "csv_structural_summary.csv",
    "forbidden_downstream_flags": "forbidden_downstream_flags.json",
}

REQUIRED_MANIFEST_FIELDS = [
    "package_id",
    "package_schema_version",
    "created_at",
    "prepared_by",
    "report_only",
    "diagnostic_only",
    "requested_file_touch_level",
    "requested_csv_read_level",
    "requested_local_file_hash_level",
    "csv_file_references",
    "forbidden_downstream_flags",
    "limitations",
]
REQUIRED_REFERENCE_FIELDS = [
    "reference_type",
    "reference_name",
    "path",
    "required",
    "intended_touch_level",
    "declared_only",
]
REQUIRED_FALSE_FLAGS = [
    "real_package_candidate_created",
    "active_reviewed_input_candidate_created",
    "real_replay_input_created",
    "active_replay_input",
    "active_replay_ready",
    "active_replay_input_ready_emitted",
    "replay_execution_allowed",
    "trading_allowed",
    "buy_review_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]
FORBIDDEN_PATH_TOKENS = {
    "secret",
    "secrets",
    "auth",
    "token",
    "tokens",
    "credential",
    "credentials",
    "key",
    "keys",
}
PROTECTED_PATH_PAIRS = {
    ("data", "raw"),
    ("data", "processed"),
    ("data", "cache"),
    ("docs", "project_sources"),
}
NETWORK_PREFIXES = ("http://", "https://", "ftp://", "s3://", "gs://")


def csv_structural_file_touch_statuses() -> list[str]:
    return [
        STATUS_NO_INPUT,
        STATUS_HEADER_ONLY_REPORT_ONLY,
        STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
        STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
        STATUS_BLOCKED_BY_PATH_GUARD,
        STATUS_BLOCKED_BY_UNSUPPORTED_TOUCH_LEVEL,
        STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
    ]


def csv_structural_file_touch_safety_flags() -> dict[str, bool]:
    return {flag: False for flag in REQUIRED_FALSE_FLAGS}


def run_csv_structural_file_touch(
    *,
    output_root: str | Path,
    run_id: str | None = None,
    package_manifest_path: str | Path | None = None,
    allowed_manifest_roots: Sequence[str | Path] | None = None,
    file_touch_level: str = FILE_TOUCH_NONE,
    csv_read_level: str = CSV_READ_NONE,
    local_file_hash_level: str = LOCAL_FILE_HASH_NONE,
    allow_csv_header_only: bool = False,
) -> dict[str, Any]:
    artifact_root = Path(output_root) / (run_id or uuid.uuid4().hex[:12])
    artifact_paths = _artifact_paths(artifact_root)
    if package_manifest_path is None:
        result = _result_payload(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_NO_INPUT,
            health_status="PASS",
            file_touch_level=FILE_TOUCH_NONE,
            csv_read_level=CSV_READ_NONE,
            local_file_hash_level=LOCAL_FILE_HASH_NONE,
            issues=[],
            limitations=["No input supplied; no CSV structural touch performed."],
        )
        _write_artifacts(result)
        return result

    if (file_touch_level, csv_read_level, local_file_hash_level) != SUPPORTED_HEADER_ONLY_LEVELS:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_UNSUPPORTED_TOUCH_LEVEL,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            local_file_hash_level=local_file_hash_level,
            reason="Only CSV_STRUCTURAL_HEADER_ONLY / CSV_HEADER_ONLY / LOCAL_FILE_HASH_NONE is supported.",
        )
        _write_artifacts(result)
        return result

    if not allow_csv_header_only:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            local_file_hash_level=local_file_hash_level,
            reason="allow_csv_header_only must be true for header-only structural reads.",
        )
        _write_artifacts(result)
        return result

    manifest_check = _check_manifest_path(package_manifest_path, allowed_manifest_roots)
    if manifest_check["blocked"]:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_PATH_GUARD,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            local_file_hash_level=local_file_hash_level,
            reason=manifest_check["reason"],
        )
        _write_artifacts(result)
        return result

    try:
        manifest = json.loads(manifest_check["path"].read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            local_file_hash_level=local_file_hash_level,
            reason=f"Manifest JSON is malformed: {exc}",
        )
        _write_artifacts(result)
        return result

    schema_issue = _manifest_schema_issue(manifest)
    if schema_issue:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            local_file_hash_level=local_file_hash_level,
            reason=schema_issue,
        )
        _write_artifacts(result)
        return result

    forbidden_issue = _forbidden_downstream_issue(manifest["forbidden_downstream_flags"])
    if forbidden_issue:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            local_file_hash_level=local_file_hash_level,
            reason=forbidden_issue,
        )
        _write_artifacts(result)
        return result

    reference = manifest["csv_file_references"][0]
    reference_issue = _reference_schema_issue(reference)
    if reference_issue:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            local_file_hash_level=local_file_hash_level,
            reason=reference_issue,
        )
        _write_artifacts(result)
        return result

    csv_check = _check_csv_reference_path(
        reference["path"],
        manifest_path=manifest_check["path"],
        allowed_manifest_roots=allowed_manifest_roots,
    )
    if csv_check["blocked"]:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_PATH_GUARD,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            local_file_hash_level=local_file_hash_level,
            reason=csv_check["reason"],
        )
        _write_artifacts(result)
        return result

    with csv_check["path"].open("r", encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle), [])

    result = _result_payload(
        artifact_paths=artifact_paths,
        run_id=artifact_root.name,
        runtime_status=STATUS_HEADER_ONLY_REPORT_ONLY,
        health_status="PASS",
        file_touch_level=file_touch_level,
        csv_read_level=csv_read_level,
        local_file_hash_level=local_file_hash_level,
        csv_file_opened_structurally=True,
        csv_header_read=True,
        csv_header_column_count=len(header),
        csv_header_columns=header,
        issues=[],
        limitations=list(manifest["limitations"]),
    )
    _write_artifacts(result)
    return result


def _manifest_schema_issue(manifest: Any) -> str:
    if not isinstance(manifest, dict):
        return "Manifest must be a JSON object."
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    if missing:
        return f"Missing required manifest fields: {','.join(missing)}"
    if manifest.get("report_only") is not True or manifest.get("diagnostic_only") is not True:
        return "report_only and diagnostic_only must be true."
    if manifest.get("requested_file_touch_level") != FILE_TOUCH_HEADER_ONLY:
        return "requested_file_touch_level must be CSV_STRUCTURAL_HEADER_ONLY."
    if manifest.get("requested_csv_read_level") != CSV_READ_HEADER_ONLY:
        return "requested_csv_read_level must be CSV_HEADER_ONLY."
    if manifest.get("requested_local_file_hash_level") != LOCAL_FILE_HASH_NONE:
        return "requested_local_file_hash_level must be LOCAL_FILE_HASH_NONE."
    references = manifest.get("csv_file_references")
    if not isinstance(references, list) or len(references) != 1:
        return "csv_file_references must contain exactly one reference."
    if not isinstance(manifest.get("limitations"), list) or not manifest["limitations"]:
        return "limitations must be a non-empty list."
    if not isinstance(manifest.get("forbidden_downstream_flags"), dict):
        return "forbidden_downstream_flags must be an object."
    return ""


def _reference_schema_issue(reference: Any) -> str:
    if not isinstance(reference, dict):
        return "CSV file reference must be an object."
    missing = [field for field in REQUIRED_REFERENCE_FIELDS if field not in reference]
    if missing:
        return f"Missing required reference fields: {','.join(missing)}"
    if reference.get("reference_type") != "reviewed_local_csv_file_ref":
        return "reference_type must be reviewed_local_csv_file_ref."
    if reference.get("intended_touch_level") != CSV_READ_HEADER_ONLY:
        return "intended_touch_level must be CSV_HEADER_ONLY."
    if reference.get("declared_only") is not False:
        return "declared_only must be false."
    return ""


def _forbidden_downstream_issue(flags: dict[str, Any]) -> str:
    for flag in REQUIRED_FALSE_FLAGS:
        if flag not in flags:
            return f"Missing forbidden downstream flag: {flag}"
        if bool(flags.get(flag)):
            return f"Forbidden downstream flag is true: {flag}"
    return ""


def _check_manifest_path(
    package_manifest_path: str | Path, allowed_manifest_roots: Sequence[str | Path] | None
) -> dict[str, Any]:
    if not allowed_manifest_roots:
        return {"blocked": True, "reason": "allowed_manifest_roots must be explicit"}
    raw_path = str(package_manifest_path)
    guard_reason = _guard_path_text(raw_path)
    if guard_reason:
        return {"blocked": True, "reason": guard_reason}
    path = Path(package_manifest_path)
    if path.suffix.lower() != ".json":
        return {"blocked": True, "reason": "package_manifest_path must be a JSON file"}
    return _existing_file_under_allowed_roots(path, allowed_manifest_roots, "package_manifest_path")


def _check_csv_reference_path(
    path_text: str, *, manifest_path: Path, allowed_manifest_roots: Sequence[str | Path] | None
) -> dict[str, Any]:
    guard_reason = _guard_path_text(path_text)
    if guard_reason:
        return {"blocked": True, "reason": guard_reason}
    raw_path = Path(path_text)
    path = raw_path if raw_path.is_absolute() else manifest_path.parent / raw_path
    if path.suffix.lower() != ".csv":
        return {"blocked": True, "reason": "CSV structural touch requires a .csv file"}
    return _existing_file_under_allowed_roots(path, allowed_manifest_roots, "csv_file_reference")


def _existing_file_under_allowed_roots(
    path: Path, allowed_roots: Sequence[str | Path] | None, label: str
) -> dict[str, Any]:
    resolved = path.resolve(strict=False)
    roots = [Path(root).resolve(strict=False) for root in (allowed_roots or [])]
    if not any(_is_relative_to(resolved, root) for root in roots):
        return {"blocked": True, "reason": f"{label} must stay under explicit allowed roots"}
    if not path.exists() or not path.is_file():
        return {"blocked": True, "reason": f"{label} must be an existing regular file"}
    real_resolved = path.resolve(strict=True)
    if real_resolved != resolved or not any(_is_relative_to(real_resolved, root) for root in roots):
        return {"blocked": True, "reason": f"{label} symlink escape is rejected"}
    return {"blocked": False, "path": path}


def _guard_path_text(path_text: str) -> str:
    if not path_text:
        return "path is required"
    lowered = path_text.lower()
    if lowered.startswith(NETWORK_PREFIXES):
        return "URL paths are rejected"
    parts = [part.lower() for part in Path(path_text).parts]
    if ".." in parts:
        return "path traversal is rejected"
    if any(part == ".env" or part.startswith(".env") or part.startswith(".") for part in parts):
        return "hidden or environment paths are rejected"
    if any((first, second) in PROTECTED_PATH_PAIRS for first, second in zip(parts, parts[1:])):
        return "protected repository path is rejected"
    if any(any(token in part for token in FORBIDDEN_PATH_TOKENS) for part in parts):
        return "secret/auth/token/credential/key path is rejected"
    return ""


def _blocked_result(
    *,
    artifact_paths: dict[str, Path],
    run_id: str,
    runtime_status: str,
    file_touch_level: str,
    csv_read_level: str,
    local_file_hash_level: str,
    reason: str,
) -> dict[str, Any]:
    return _result_payload(
        artifact_paths=artifact_paths,
        run_id=run_id,
        runtime_status=runtime_status,
        health_status="FAIL",
        file_touch_level=file_touch_level,
        csv_read_level=csv_read_level,
        local_file_hash_level=local_file_hash_level,
        issues=[{"severity": "ERROR", "issue_code": runtime_status, "message": reason}],
        limitations=["Blocked before any CSV header read."],
    )


def _result_payload(
    *,
    artifact_paths: dict[str, Path],
    run_id: str,
    runtime_status: str,
    health_status: str,
    file_touch_level: str,
    csv_read_level: str,
    local_file_hash_level: str,
    csv_file_opened_structurally: bool = False,
    csv_header_read: bool = False,
    csv_header_column_count: int = 0,
    csv_header_columns: list[str] | None = None,
    issues: list[dict[str, Any]] | None = None,
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "run_id": run_id,
        "created_at": CREATED_AT,
        "workflow_name": WORKFLOW_NAME,
        "runtime_status": runtime_status,
        "status": runtime_status,
        "health_status": health_status,
        "workflow_stage": WORKFLOW_STAGE,
        "report_only": True,
        "diagnostic_only": True,
        "file_touch_level": file_touch_level,
        "csv_read_level": csv_read_level,
        "local_file_hash_level": local_file_hash_level,
        "csv_file_opened_structurally": csv_file_opened_structurally,
        "csv_header_read": csv_header_read,
        "csv_header_column_count": csv_header_column_count,
        "csv_header_columns": csv_header_columns or [],
        "csv_row_count_computed": False,
        "csv_row_count": "",
        "csv_values_read": False,
        "csv_full_content_read": False,
        "local_file_byte_hash_computed": False,
        "local_file_byte_hash_algorithm": "",
        "real_csv_consumed": False,
        "recommended_next_task": NEXT_TASK,
        "artifact_paths": artifact_paths,
        "issues": issues or [],
        "limitations": limitations or [],
    }
    result.update(csv_structural_file_touch_safety_flags())
    return result


def _artifact_paths(root: Path) -> dict[str, Path]:
    return {name: root / filename for name, filename in ARTIFACT_FILENAMES.items()}


def _write_artifacts(result: dict[str, Any]) -> None:
    for path in result["artifact_paths"].values():
        path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(result["artifact_paths"]["metadata"], _metadata_payload(result))
    _write_json(result["artifact_paths"]["forbidden_downstream_flags"], csv_structural_file_touch_safety_flags())
    _write_csv(result["artifact_paths"]["issues"], result["issues"] or [_empty_issue_row()])
    _write_csv(result["artifact_paths"]["summary"], [_summary_row(result)])
    result["artifact_paths"]["limitations"].write_text(_limitations_text(result), encoding="utf-8")
    result["artifact_paths"]["report"].write_text(_report_text(result), encoding="utf-8")


def _metadata_payload(result: dict[str, Any]) -> dict[str, Any]:
    excluded = {"artifact_paths", "issues", "limitations"}
    return {key: value for key, value in result.items() if key not in excluded}


def _summary_row(result: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "run_id",
        "runtime_status",
        "health_status",
        "workflow_stage",
        "report_only",
        "diagnostic_only",
        "file_touch_level",
        "csv_read_level",
        "local_file_hash_level",
        "csv_file_opened_structurally",
        "csv_header_read",
        "csv_header_column_count",
        "csv_header_columns",
        "csv_row_count_computed",
        "csv_row_count",
        "csv_values_read",
        "csv_full_content_read",
        "local_file_byte_hash_computed",
        "local_file_byte_hash_algorithm",
        "real_csv_consumed",
        "real_package_candidate_created",
        "active_reviewed_input_candidate_created",
        "real_replay_input_created",
        "active_replay_input",
        "active_replay_ready",
        "active_replay_input_ready_emitted",
        "replay_execution_allowed",
        "trading_allowed",
        "buy_review_allowed",
        "data_raw_written",
        "data_processed_written",
        "data_cache_written",
        "recommended_next_task",
    ]
    row = {field: result[field] for field in fields}
    row["csv_header_columns"] = "|".join(result["csv_header_columns"])
    return row


def _empty_issue_row() -> dict[str, str]:
    return {"severity": "", "issue_code": "", "message": ""}


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _limitations_text(result: dict[str, Any]) -> str:
    lines = ["# Limitations", ""]
    lines.extend(f"- {item}" for item in result["limitations"])
    lines.extend(
        [
            "- Header-only structural metadata is not CSV value consumption.",
            "- No row count, file byte hash, replay input, buy-review, or trading behavior is created.",
            "",
        ]
    )
    return "\n".join(lines)


def _report_text(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# CSV Structural File-Touch Report",
            "",
            f"- Runtime status: `{result['runtime_status']}`",
            f"- Health status: `{result['health_status']}`",
            f"- File touch level: `{result['file_touch_level']}`",
            f"- CSV read level: `{result['csv_read_level']}`",
            f"- Local file hash level: `{result['local_file_hash_level']}`",
            f"- CSV header read: `{str(result['csv_header_read']).lower()}`",
            f"- CSV header column count: `{result['csv_header_column_count']}`",
            f"- CSV header columns: `{', '.join(result['csv_header_columns'])}`",
            "- CSV row count computed: `false`",
            "- CSV values read: `false`",
            "- CSV full content read: `false`",
            "- Local file byte hash computed: `false`",
            "- Real CSV consumed: `false`",
            "- Real package candidate created: `false`",
            "- Active replay input emitted: `false`",
            "- Trading allowed: `false`",
            f"- Recommended next task: `{result['recommended_next_task']}`",
            "",
        ]
    )


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
