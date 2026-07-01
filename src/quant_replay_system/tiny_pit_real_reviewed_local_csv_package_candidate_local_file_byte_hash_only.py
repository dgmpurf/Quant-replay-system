"""Local file byte-hash-only core for Tiny PIT reviewed LOCAL_CSV candidates.

This module is report-only and diagnostic-only. It computes a SHA-256 byte hash
only for one explicitly manifested local CSV file under caller-provided roots
and an explicit allow flag. It does not parse CSV, read headers, count rows,
inspect values, validate PIT/source/reviewer semantics, create replay inputs, or
enable buy-review/trading behavior.
"""

from __future__ import annotations

import csv
import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence


STATUS_NO_INPUT = "NO_LOCAL_FILE_BYTE_HASH_INPUT"
STATUS_HASH_ONLY_REPORT_ONLY = "LOCAL_FILE_BYTE_HASH_ONLY_REPORT_ONLY"
STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG = "LOCAL_FILE_BYTE_HASH_BLOCKED_BY_MISSING_ALLOW_FLAG"
STATUS_BLOCKED_BY_MANIFEST_SCHEMA = "LOCAL_FILE_BYTE_HASH_BLOCKED_BY_MANIFEST_SCHEMA"
STATUS_BLOCKED_BY_PATH_GUARD = "LOCAL_FILE_BYTE_HASH_BLOCKED_BY_PATH_GUARD"
STATUS_BLOCKED_BY_SIZE_LIMIT = "LOCAL_FILE_BYTE_HASH_BLOCKED_BY_SIZE_LIMIT"
STATUS_BLOCKED_BY_UNSUPPORTED_LEVEL = "LOCAL_FILE_BYTE_HASH_BLOCKED_BY_UNSUPPORTED_LEVEL"
STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM = "LOCAL_FILE_BYTE_HASH_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
STATUS_HEALTH_FAILED = "LOCAL_FILE_BYTE_HASH_HEALTH_FAILED"

WORKFLOW_NAME = "tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only"
WORKFLOW_STAGE = (
    "TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_"
    "LOCAL_FILE_BYTE_HASH_ONLY_CORE_CREATED_REPORT_ONLY"
)
CREATED_AT = "2026-07-01T00:00:00Z"
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Local File Byte-Hash-Only "
    "Artifact Views Report-Only v0.1"
)

FILE_TOUCH_NONE = "FILE_TOUCH_NONE"
LOCAL_FILE_BYTE_HASH_ONLY = "LOCAL_FILE_BYTE_HASH_ONLY"
CSV_READ_NONE = "CSV_READ_NONE"
LOCAL_FILE_HASH_NONE = "LOCAL_FILE_HASH_NONE"
LOCAL_FILE_BYTE_HASH_SHA256_ONLY = "LOCAL_FILE_BYTE_HASH_SHA256_ONLY"
HASH_ALGORITHM = "SHA-256"
HASH_DISCLOSURE_LEVEL = "FULL_METADATA_PREVIEW_STATUS"
HASH_PREVIEW_HEX_CHARS = 16
MAX_HASH_INPUT_BYTES = 1_048_576
SUPPORTED_HASH_ONLY_LEVELS = (
    LOCAL_FILE_BYTE_HASH_ONLY,
    CSV_READ_NONE,
    LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
)

ARTIFACT_FILENAMES = {
    "metadata": "metadata.json",
    "report": "local_file_byte_hash_only_report.md",
    "limitations": "limitations.md",
    "issues": "issues.csv",
    "summary": "local_file_byte_hash_summary.csv",
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
    "local_file_references",
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
    "real_reviewed_csv_package_created",
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
    "labels_created",
    "training_dataset_created",
    "model_training_performed",
    "stock_profile_validation_created",
    "paper_validation_created",
    "strategy_performance_validated",
    "broker_api_called",
    "order_placed",
    "message_sent",
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
    ("outputs", "reports"),
}
NETWORK_PREFIXES = ("http://", "https://", "ftp://", "s3://", "gs://")


def local_file_byte_hash_only_statuses() -> list[str]:
    return [
        STATUS_NO_INPUT,
        STATUS_HASH_ONLY_REPORT_ONLY,
        STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
        STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
        STATUS_BLOCKED_BY_PATH_GUARD,
        STATUS_BLOCKED_BY_SIZE_LIMIT,
        STATUS_BLOCKED_BY_UNSUPPORTED_LEVEL,
        STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
        STATUS_HEALTH_FAILED,
    ]


def local_file_byte_hash_only_safety_flags() -> dict[str, bool]:
    return {flag: False for flag in REQUIRED_FALSE_FLAGS}


def run_local_file_byte_hash_only(
    *,
    output_root: str | Path,
    run_id: str | None = None,
    package_manifest_path: str | Path | None = None,
    allowed_manifest_roots: Sequence[str | Path] | None = None,
    file_touch_level: str = FILE_TOUCH_NONE,
    csv_read_level: str = CSV_READ_NONE,
    local_file_hash_level: str = LOCAL_FILE_HASH_NONE,
    allow_local_file_byte_hash_only: bool = False,
    max_hash_input_bytes: int = MAX_HASH_INPUT_BYTES,
) -> dict[str, Any]:
    artifact_root = _validated_output_root(Path(output_root)) / (run_id or uuid.uuid4().hex[:12])
    artifact_paths = _artifact_paths(artifact_root)
    size_limit = int(max_hash_input_bytes)

    if package_manifest_path is None:
        result = _result_payload(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_NO_INPUT,
            health_status="PASS",
            file_touch_level=FILE_TOUCH_NONE,
            csv_read_level=CSV_READ_NONE,
            local_file_hash_level=LOCAL_FILE_HASH_NONE,
            local_file_size_limit_bytes=size_limit,
            issues=[],
            limitations=["No input supplied; no local file byte hash computed."],
        )
        _write_artifacts(result)
        return result

    if (file_touch_level, csv_read_level, local_file_hash_level) != SUPPORTED_HASH_ONLY_LEVELS:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_UNSUPPORTED_LEVEL,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            local_file_hash_level=local_file_hash_level,
            local_file_size_limit_bytes=size_limit,
            reason="Only LOCAL_FILE_BYTE_HASH_ONLY / CSV_READ_NONE / LOCAL_FILE_BYTE_HASH_SHA256_ONLY is supported.",
        )
        _write_artifacts(result)
        return result

    if not allow_local_file_byte_hash_only:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            local_file_hash_level=local_file_hash_level,
            local_file_size_limit_bytes=size_limit,
            reason="allow_local_file_byte_hash_only must be true for byte-hash-only reads.",
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
            local_file_size_limit_bytes=size_limit,
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
            local_file_size_limit_bytes=size_limit,
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
            local_file_size_limit_bytes=size_limit,
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
            local_file_size_limit_bytes=size_limit,
            reason=forbidden_issue,
        )
        _write_artifacts(result)
        return result

    reference = manifest["local_file_references"][0]
    reference_issue = _reference_schema_issue(reference)
    if reference_issue:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            local_file_hash_level=local_file_hash_level,
            local_file_size_limit_bytes=size_limit,
            reason=reference_issue,
        )
        _write_artifacts(result)
        return result

    file_check = _check_local_csv_reference_path(
        reference["path"],
        manifest_path=manifest_check["path"],
        allowed_manifest_roots=allowed_manifest_roots,
    )
    if file_check["blocked"]:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_PATH_GUARD,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            local_file_hash_level=local_file_hash_level,
            local_file_size_limit_bytes=size_limit,
            reason=file_check["reason"],
        )
        _write_artifacts(result)
        return result

    local_file_size = file_check["path"].stat().st_size
    if local_file_size <= 0:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_SIZE_LIMIT,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            local_file_hash_level=local_file_hash_level,
            local_file_size_limit_bytes=size_limit,
            local_file_size_bytes=local_file_size,
            reason="Local CSV file is empty; byte-hash-only evidence requires a non-empty file.",
        )
        _write_artifacts(result)
        return result
    if local_file_size > size_limit:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_SIZE_LIMIT,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            local_file_hash_level=local_file_hash_level,
            local_file_size_limit_bytes=size_limit,
            local_file_size_bytes=local_file_size,
            reason="Local CSV file exceeds max_hash_input_bytes.",
        )
        _write_artifacts(result)
        return result

    full_hash = _sha256_file(file_check["path"])
    result = _result_payload(
        artifact_paths=artifact_paths,
        run_id=artifact_root.name,
        runtime_status=STATUS_HASH_ONLY_REPORT_ONLY,
        health_status="PASS",
        file_touch_level=file_touch_level,
        csv_read_level=csv_read_level,
        local_file_hash_level=local_file_hash_level,
        local_file_byte_hash_computed=True,
        local_file_byte_hash_algorithm=HASH_ALGORITHM,
        local_file_byte_hash_value=full_hash,
        local_file_byte_hash_preview=full_hash[:HASH_PREVIEW_HEX_CHARS],
        local_file_byte_hash_full_recorded_in_metadata=True,
        local_file_byte_hash_disclosure_level=HASH_DISCLOSURE_LEVEL,
        local_file_bytes_read_for_hash=True,
        local_file_size_bytes=local_file_size,
        local_file_size_limit_bytes=size_limit,
        local_file_byte_hash_expected_present=any(
            field in reference or field in manifest for field in ("expected_hash", "expected_sha256")
        ),
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
    if manifest.get("requested_file_touch_level") != LOCAL_FILE_BYTE_HASH_ONLY:
        return "requested_file_touch_level must be LOCAL_FILE_BYTE_HASH_ONLY."
    if manifest.get("requested_csv_read_level") != CSV_READ_NONE:
        return "requested_csv_read_level must be CSV_READ_NONE."
    if manifest.get("requested_local_file_hash_level") != LOCAL_FILE_BYTE_HASH_SHA256_ONLY:
        return "requested_local_file_hash_level must be LOCAL_FILE_BYTE_HASH_SHA256_ONLY."
    references = manifest.get("local_file_references")
    if not isinstance(references, list) or len(references) != 1:
        return "local_file_references must contain exactly one reference."
    if not isinstance(manifest.get("limitations"), list) or not manifest["limitations"]:
        return "limitations must be a non-empty list."
    if not isinstance(manifest.get("forbidden_downstream_flags"), dict):
        return "forbidden_downstream_flags must be an object."
    return ""


def _reference_schema_issue(reference: Any) -> str:
    if not isinstance(reference, dict):
        return "Local file reference must be an object."
    missing = [field for field in REQUIRED_REFERENCE_FIELDS if field not in reference]
    if missing:
        return f"Missing required reference fields: {','.join(missing)}"
    if reference.get("reference_type") != "reviewed_local_csv_file_ref":
        return "reference_type must be reviewed_local_csv_file_ref."
    if reference.get("intended_touch_level") != LOCAL_FILE_BYTE_HASH_ONLY:
        return "intended_touch_level must be LOCAL_FILE_BYTE_HASH_ONLY."
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


def _check_local_csv_reference_path(
    path_text: str, *, manifest_path: Path, allowed_manifest_roots: Sequence[str | Path] | None
) -> dict[str, Any]:
    guard_reason = _guard_path_text(path_text)
    if guard_reason:
        return {"blocked": True, "reason": guard_reason}
    raw_path = Path(path_text)
    path = raw_path if raw_path.is_absolute() else manifest_path.parent / raw_path
    if path.suffix.lower() != ".csv":
        return {"blocked": True, "reason": "Local byte-hash-only touch requires a .csv file"}
    return _existing_file_under_allowed_roots(path, allowed_manifest_roots, "local_file_reference")


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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validated_output_root(root: Path) -> Path:
    normalized = root.as_posix().lower()
    forbidden_fragments = {
        "data/raw",
        "data/processed",
        "data/cache",
        "docs/project_sources",
    }
    if any(fragment in normalized for fragment in forbidden_fragments):
        raise ValueError(f"Unsafe local file byte-hash-only output root: {root}")
    return root


def _blocked_result(
    *,
    artifact_paths: dict[str, Path],
    run_id: str,
    runtime_status: str,
    file_touch_level: str,
    csv_read_level: str,
    local_file_hash_level: str,
    local_file_size_limit_bytes: int,
    reason: str,
    local_file_size_bytes: int | str = "",
) -> dict[str, Any]:
    return _result_payload(
        artifact_paths=artifact_paths,
        run_id=run_id,
        runtime_status=runtime_status,
        health_status="FAIL",
        file_touch_level=file_touch_level,
        csv_read_level=csv_read_level,
        local_file_hash_level=local_file_hash_level,
        local_file_size_bytes=local_file_size_bytes,
        local_file_size_limit_bytes=local_file_size_limit_bytes,
        issues=[{"severity": "ERROR", "issue_code": runtime_status, "message": reason}],
        limitations=["Blocked before any local file byte hash was computed."],
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
    local_file_byte_hash_computed: bool = False,
    local_file_byte_hash_algorithm: str = "",
    local_file_byte_hash_value: str = "",
    local_file_byte_hash_preview: str = "",
    local_file_byte_hash_full_recorded_in_metadata: bool = False,
    local_file_byte_hash_disclosure_level: str = "",
    local_file_bytes_read_for_hash: bool = False,
    local_file_size_bytes: int | str = "",
    local_file_size_limit_bytes: int = MAX_HASH_INPUT_BYTES,
    local_file_byte_hash_expected_present: bool = False,
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
        "local_file_byte_hash_computed": local_file_byte_hash_computed,
        "local_file_byte_hash_algorithm": local_file_byte_hash_algorithm,
        "local_file_byte_hash_value": local_file_byte_hash_value,
        "local_file_byte_hash_preview": local_file_byte_hash_preview,
        "local_file_byte_hash_full_recorded_in_metadata": local_file_byte_hash_full_recorded_in_metadata,
        "local_file_byte_hash_disclosure_level": local_file_byte_hash_disclosure_level,
        "local_file_bytes_read_for_hash": local_file_bytes_read_for_hash,
        "local_file_size_bytes": local_file_size_bytes,
        "local_file_size_limit_bytes": local_file_size_limit_bytes,
        "local_file_byte_hash_verified_against_manifest": False,
        "local_file_byte_hash_expected_present": local_file_byte_hash_expected_present,
        "csv_file_opened_structurally": False,
        "csv_header_read": False,
        "csv_header_column_count": 0,
        "csv_row_count_computed": False,
        "csv_row_count": "",
        "csv_values_read": False,
        "csv_full_content_read": False,
        "real_csv_consumed": False,
        "source_hash_validated": False,
        "revision_id_validated": False,
        "available_time_validated": False,
        "pit_admissibility_validated": False,
        "source_reliability_scored": False,
        "reviewer_authority_validated": False,
        "recommended_next_task": NEXT_TASK,
        "artifact_paths": artifact_paths,
        "issues": issues or [],
        "limitations": limitations or [],
    }
    result.update(local_file_byte_hash_only_safety_flags())
    return result


def _artifact_paths(root: Path) -> dict[str, Path]:
    return {name: root / filename for name, filename in ARTIFACT_FILENAMES.items()}


def _write_artifacts(result: dict[str, Any]) -> None:
    for path in result["artifact_paths"].values():
        path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(result["artifact_paths"]["metadata"], _metadata_payload(result))
    _write_json(result["artifact_paths"]["forbidden_downstream_flags"], local_file_byte_hash_only_safety_flags())
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
        "local_file_byte_hash_computed",
        "local_file_byte_hash_algorithm",
        "local_file_byte_hash_preview",
        "local_file_byte_hash_full_recorded_in_metadata",
        "local_file_byte_hash_disclosure_level",
        "local_file_bytes_read_for_hash",
        "local_file_size_bytes",
        "local_file_size_limit_bytes",
        "local_file_byte_hash_verified_against_manifest",
        "local_file_byte_hash_expected_present",
        "csv_file_opened_structurally",
        "csv_header_read",
        "csv_header_column_count",
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
        "real_reviewed_csv_package_created",
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
    return {field: result[field] for field in fields}


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
            "- Byte-hash-only evidence is local file identity context, not CSV semantic content.",
            "- No CSV header, row count, values, full content, PIT admissibility, replay input, buy-review, or trading behavior is created.",
            "",
        ]
    )
    return "\n".join(lines)


def _report_text(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Local File Byte-Hash-Only Report",
            "",
            f"- Runtime status: `{result['runtime_status']}`",
            f"- Health status: `{result['health_status']}`",
            f"- File touch level: `{result['file_touch_level']}`",
            f"- CSV read level: `{result['csv_read_level']}`",
            f"- Local file hash level: `{result['local_file_hash_level']}`",
            f"- Local file byte hash computed: `{str(result['local_file_byte_hash_computed']).lower()}`",
            f"- Local file byte hash algorithm: `{result['local_file_byte_hash_algorithm']}`",
            f"- Local file byte hash preview: `{result['local_file_byte_hash_preview']}`",
            f"- Local file byte hash disclosure level: `{result['local_file_byte_hash_disclosure_level']}`",
            f"- Local file size bytes: `{result['local_file_size_bytes']}`",
            f"- Local file size limit bytes: `{result['local_file_size_limit_bytes']}`",
            "- CSV header read: `false`",
            "- CSV row count computed: `false`",
            "- CSV values read: `false`",
            "- CSV full content read: `false`",
            "- Real CSV consumed: `false`",
            "- Source hash validated: `false`",
            "- Revision id validated: `false`",
            "- Available time validated: `false`",
            "- PIT admissibility validated: `false`",
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
