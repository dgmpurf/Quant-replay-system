"""Expected-hash verification core for Tiny PIT reviewed LOCAL_CSV candidates.

This module is report-only and diagnostic-only. It compares a manifest-declared
SHA-256 value with a previously generated Local File Byte-Hash-Only metadata
value. It does not open the target CSV, recompute local hashes, parse CSV
content, validate source/revision/PIT/reviewer semantics, create replay inputs,
or enable buy-review/trading behavior.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Sequence


STATUS_NO_INPUT = "NO_EXPECTED_HASH_VERIFICATION_INPUT"
STATUS_MATCHED = "EXPECTED_HASH_VERIFICATION_MATCHED_REPORT_ONLY"
STATUS_MISMATCHED = "EXPECTED_HASH_VERIFICATION_MISMATCHED_REPORT_ONLY"
STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG = "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_MISSING_ALLOW_FLAG"
STATUS_BLOCKED_BY_MANIFEST_SCHEMA = "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_MANIFEST_SCHEMA"
STATUS_BLOCKED_BY_PATH_GUARD = "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_PATH_GUARD"
STATUS_BLOCKED_BY_UNSUPPORTED_ALGORITHM = "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_UNSUPPORTED_ALGORITHM"
STATUS_BLOCKED_BY_MISSING_LOCAL_HASH_METADATA = "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_MISSING_LOCAL_HASH_METADATA"
STATUS_BLOCKED_BY_UNSAFE_LOCAL_HASH_METADATA = "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_UNSAFE_LOCAL_HASH_METADATA"
STATUS_BLOCKED_BY_DISCLOSURE_POLICY = "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_DISCLOSURE_POLICY"
STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM = "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
STATUS_HEALTH_FAILED = "EXPECTED_HASH_VERIFICATION_HEALTH_FAILED"

WORKFLOW_NAME = "tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification"
WORKFLOW_STAGE = (
    "TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_"
    "EXPECTED_HASH_VERIFICATION_CORE_CREATED_REPORT_ONLY"
)
CREATED_AT = "2026-07-02T00:00:00Z"
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Expected-Hash Verification "
    "Artifact Views Report-Only v0.1"
)

FILE_TOUCH_NONE = "FILE_TOUCH_NONE"
CSV_READ_NONE = "CSV_READ_NONE"
LOCAL_FILE_HASH_NONE = "LOCAL_FILE_HASH_NONE"
LOCAL_FILE_HASH_SHA256_METADATA_REFERENCE_ONLY = "LOCAL_FILE_HASH_SHA256_METADATA_REFERENCE_ONLY"
EXPECTED_HASH_VERIFICATION_NONE = "EXPECTED_HASH_VERIFICATION_NONE"
EXPECTED_HASH_SHA256_AGAINST_LOCAL_METADATA_ONLY = "EXPECTED_HASH_SHA256_AGAINST_LOCAL_METADATA_ONLY"
HASH_ALGORITHM = "SHA-256"
HASH_DISCLOSURE_LEVEL = "PREVIEW_ONLY_STATUS"
HASH_PREVIEW_HEX_CHARS = 16
MAX_MANIFEST_SIZE_BYTES = 1_048_576

ARTIFACT_FILENAMES = {
    "metadata": "metadata.json",
    "report": "expected_hash_verification_report.md",
    "limitations": "limitations.md",
    "issues": "issues.csv",
    "summary": "expected_hash_verification_summary.csv",
    "forbidden_downstream_flags": "forbidden_downstream_flags.json",
}

REQUIRED_MANIFEST_FIELDS = [
    "verification_id",
    "package_id",
    "package_schema_version",
    "created_at",
    "prepared_by",
    "report_only",
    "diagnostic_only",
    "requested_expected_hash_verification_level",
    "requested_csv_read_level",
    "requested_local_file_hash_level",
    "source_local_file_byte_hash_artifact_metadata_path",
    "expected_hash_algorithm",
    "expected_hash_value",
    "expected_hash_disclosure_level",
    "forbidden_downstream_flags",
    "limitations",
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

UNSAFE_LOCAL_METADATA_TRUE_FIELDS = [
    "csv_header_read",
    "csv_row_count_computed",
    "csv_values_read",
    "csv_full_content_read",
    "real_csv_consumed",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "source_reliability_scored",
    "reviewer_authority_validated",
    *REQUIRED_FALSE_FLAGS,
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


def expected_hash_verification_statuses() -> list[str]:
    return [
        STATUS_NO_INPUT,
        STATUS_MATCHED,
        STATUS_MISMATCHED,
        STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
        STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
        STATUS_BLOCKED_BY_PATH_GUARD,
        STATUS_BLOCKED_BY_UNSUPPORTED_ALGORITHM,
        STATUS_BLOCKED_BY_MISSING_LOCAL_HASH_METADATA,
        STATUS_BLOCKED_BY_UNSAFE_LOCAL_HASH_METADATA,
        STATUS_BLOCKED_BY_DISCLOSURE_POLICY,
        STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
        STATUS_HEALTH_FAILED,
    ]


def expected_hash_verification_safety_flags() -> dict[str, bool]:
    return {flag: False for flag in REQUIRED_FALSE_FLAGS}


def run_expected_hash_verification(
    *,
    output_root: str | Path,
    run_id: str | None = None,
    expected_hash_manifest_path: str | Path | None = None,
    local_file_byte_hash_metadata_path: str | Path | None = None,
    allowed_manifest_roots: Sequence[str | Path] | None = None,
    verification_level: str = EXPECTED_HASH_VERIFICATION_NONE,
    allow_expected_hash_verification: bool = False,
    max_manifest_size_bytes: int = MAX_MANIFEST_SIZE_BYTES,
) -> dict[str, Any]:
    artifact_root = _validated_output_root(Path(output_root)) / (run_id or uuid.uuid4().hex[:12])
    artifact_paths = _artifact_paths(artifact_root)
    size_limit = int(max_manifest_size_bytes)

    if expected_hash_manifest_path is None:
        result = _result_payload(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_NO_INPUT,
            health_status="PASS",
            file_touch_level=FILE_TOUCH_NONE,
            csv_read_level=CSV_READ_NONE,
            local_file_hash_level=LOCAL_FILE_HASH_NONE,
            expected_hash_verification_level=EXPECTED_HASH_VERIFICATION_NONE,
            max_manifest_size_bytes=size_limit,
            issues=[],
            limitations=["No input supplied; no expected-hash verification performed."],
        )
        _write_artifacts(result)
        return result

    if verification_level != EXPECTED_HASH_SHA256_AGAINST_LOCAL_METADATA_ONLY:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            reason="verification_level must be EXPECTED_HASH_SHA256_AGAINST_LOCAL_METADATA_ONLY.",
            max_manifest_size_bytes=size_limit,
        )
        _write_artifacts(result)
        return result

    if not allow_expected_hash_verification:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
            reason="allow_expected_hash_verification must be true for metadata-only expected-hash comparison.",
            max_manifest_size_bytes=size_limit,
        )
        _write_artifacts(result)
        return result

    if local_file_byte_hash_metadata_path is None:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MISSING_LOCAL_HASH_METADATA,
            reason="local_file_byte_hash_metadata_path is required when a manifest is supplied.",
            max_manifest_size_bytes=size_limit,
        )
        _write_artifacts(result)
        return result

    manifest_check = _check_input_path(expected_hash_manifest_path, allowed_manifest_roots)
    metadata_check = _check_input_path(local_file_byte_hash_metadata_path, allowed_manifest_roots)
    if manifest_check["blocked"] or metadata_check["blocked"]:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_PATH_GUARD,
            reason=str(manifest_check.get("reason") or metadata_check.get("reason")),
            max_manifest_size_bytes=size_limit,
        )
        _write_artifacts(result)
        return result

    manifest_path = Path(manifest_check["path"])
    metadata_path = Path(metadata_check["path"])
    if not manifest_path.is_file():
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            reason="Expected-hash manifest file is missing.",
            max_manifest_size_bytes=size_limit,
        )
        _write_artifacts(result)
        return result
    if not metadata_path.is_file():
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MISSING_LOCAL_HASH_METADATA,
            reason="Local File Byte-Hash-Only metadata file is missing.",
            max_manifest_size_bytes=size_limit,
        )
        _write_artifacts(result)
        return result
    if manifest_path.stat().st_size > size_limit or metadata_path.stat().st_size > size_limit:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            reason="Manifest or metadata file exceeds the metadata-only size limit.",
            max_manifest_size_bytes=size_limit,
        )
        _write_artifacts(result)
        return result

    manifest = _read_json(manifest_path)
    if not isinstance(manifest, dict):
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            reason="Expected-hash manifest must be a top-level JSON object.",
            max_manifest_size_bytes=size_limit,
        )
        _write_artifacts(result)
        return result

    schema_issue = _manifest_schema_issue(manifest, metadata_path)
    if schema_issue:
        status = (
            STATUS_BLOCKED_BY_UNSUPPORTED_ALGORITHM
            if schema_issue == "unsupported_algorithm"
            else STATUS_BLOCKED_BY_DISCLOSURE_POLICY
            if schema_issue == "unsupported_disclosure"
            else STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM
            if schema_issue == "forbidden_downstream"
            else STATUS_BLOCKED_BY_MANIFEST_SCHEMA
        )
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=status,
            reason=_schema_reason(schema_issue),
            expected_hash_present="expected_hash_value" in manifest,
            expected_hash_preview=_preview_if_hex(str(manifest.get("expected_hash_value") or "")),
            max_manifest_size_bytes=size_limit,
        )
        _write_artifacts(result)
        return result

    metadata = _read_json(metadata_path)
    if not isinstance(metadata, dict):
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_UNSAFE_LOCAL_HASH_METADATA,
            reason="Local File Byte-Hash-Only metadata must be a JSON object.",
            expected_hash_present=True,
            expected_hash_preview=_preview(str(manifest["expected_hash_value"]).lower()),
            max_manifest_size_bytes=size_limit,
        )
        _write_artifacts(result)
        return result

    metadata_issue = _local_metadata_issue(metadata)
    if metadata_issue:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_UNSAFE_LOCAL_HASH_METADATA,
            reason=metadata_issue,
            expected_hash_present=True,
            expected_hash_preview=_preview(str(manifest["expected_hash_value"]).lower()),
            max_manifest_size_bytes=size_limit,
        )
        _write_artifacts(result)
        return result

    expected_value = str(manifest["expected_hash_value"]).lower()
    actual_value = str(metadata["local_file_byte_hash_value"]).lower()
    matched = expected_value == actual_value
    result = _result_payload(
        artifact_paths=artifact_paths,
        run_id=artifact_root.name,
        runtime_status=STATUS_MATCHED if matched else STATUS_MISMATCHED,
        health_status="PASS" if matched else "WARN",
        file_touch_level=FILE_TOUCH_NONE,
        csv_read_level=CSV_READ_NONE,
        local_file_hash_level=LOCAL_FILE_HASH_SHA256_METADATA_REFERENCE_ONLY,
        expected_hash_verification_level=EXPECTED_HASH_SHA256_AGAINST_LOCAL_METADATA_ONLY,
        expected_hash_verification_performed=True,
        expected_hash_algorithm=HASH_ALGORITHM,
        expected_hash_present=True,
        expected_hash_preview=_preview(expected_value),
        actual_local_file_byte_hash_algorithm=HASH_ALGORITHM,
        actual_local_file_byte_hash_preview=_preview(actual_value),
        expected_hash_matched=matched,
        expected_hash_mismatch=not matched,
        expected_hash_verified_against_local_metadata=True,
        issue_count=0 if matched else 1,
        warning_count=0 if matched else 1,
        actionable_mismatch=not matched,
        max_manifest_size_bytes=size_limit,
        issues=[]
        if matched
        else [
            {
                "severity": "WARN",
                "issue_code": STATUS_MISMATCHED,
                "message": "Expected hash preview does not match local metadata preview.",
            }
        ],
        limitations=[
            "Expected-hash verification compares manifest metadata against local byte-hash metadata only.",
        ],
    )
    _write_artifacts(result)
    return result


def _manifest_schema_issue(manifest: dict[str, Any], metadata_path: Path) -> str:
    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in manifest:
            return f"missing_{field}"
    if manifest.get("report_only") is not True or manifest.get("diagnostic_only") is not True:
        return "report_only_required"
    if manifest.get("requested_expected_hash_verification_level") != EXPECTED_HASH_SHA256_AGAINST_LOCAL_METADATA_ONLY:
        return "expected_hash_level"
    if manifest.get("requested_csv_read_level") != CSV_READ_NONE:
        return "csv_read_level"
    if manifest.get("requested_local_file_hash_level") != LOCAL_FILE_HASH_SHA256_METADATA_REFERENCE_ONLY:
        return "local_hash_level"
    if str(manifest.get("expected_hash_algorithm") or "").upper() != HASH_ALGORITHM:
        return "unsupported_algorithm"
    if manifest.get("expected_hash_disclosure_level") != HASH_DISCLOSURE_LEVEL:
        return "unsupported_disclosure"
    expected_value = str(manifest.get("expected_hash_value") or "")
    if not _is_64_hex(expected_value):
        return "expected_hash_value"
    if Path(str(manifest.get("source_local_file_byte_hash_artifact_metadata_path"))).resolve() != metadata_path.resolve():
        return "metadata_path_mismatch"
    flags = manifest.get("forbidden_downstream_flags")
    if not isinstance(flags, dict):
        return "forbidden_downstream"
    for flag in REQUIRED_FALSE_FLAGS:
        if flags.get(flag) is not False:
            return "forbidden_downstream"
    if not isinstance(manifest.get("limitations"), list):
        return "limitations"
    return ""


def _local_metadata_issue(metadata: dict[str, Any]) -> str:
    if metadata.get("local_file_byte_hash_computed") is not True:
        return "Local byte-hash metadata must report local_file_byte_hash_computed=false is blocked."
    if metadata.get("local_file_byte_hash_algorithm") != HASH_ALGORITHM:
        return "Local byte-hash metadata algorithm must be SHA-256."
    if not _is_64_hex(str(metadata.get("local_file_byte_hash_value") or "")):
        return "Local byte-hash metadata value must be a 64-character hex value."
    if metadata.get("csv_read_level") != CSV_READ_NONE:
        return "Local byte-hash metadata must preserve CSV_READ_NONE."
    for field in UNSAFE_LOCAL_METADATA_TRUE_FIELDS:
        if metadata.get(field) is not False:
            return f"Unsafe local byte-hash metadata field is not false: {field}."
    return ""


def _check_input_path(path: str | Path, allowed_roots: Sequence[str | Path] | None) -> dict[str, Any]:
    path_text = str(path)
    guard_issue = _guard_path_text(path_text)
    if guard_issue:
        return {"blocked": True, "reason": guard_issue}
    candidate = Path(path).resolve()
    if _has_protected_pair(candidate):
        return {"blocked": True, "reason": "Protected input path is not allowed."}
    if candidate.is_symlink():
        return {"blocked": True, "reason": "Symlink input paths are not allowed."}
    roots = [Path(root).resolve() for root in allowed_roots or []]
    if not roots:
        return {"blocked": True, "reason": "Explicit allowed_manifest_roots are required."}
    if not any(_is_relative_to(candidate, root) for root in roots):
        return {"blocked": True, "reason": "Input path is outside explicit allowed roots."}
    return {"blocked": False, "path": candidate}


def _guard_path_text(path_text: str) -> str:
    lowered = path_text.lower().replace("\\", "/")
    if any(lowered.startswith(prefix) for prefix in NETWORK_PREFIXES):
        return "Network or URL paths are not allowed."
    if "\x00" in path_text or ".." in Path(path_text).parts:
        return "Traversal or invalid path text is not allowed."
    parts = [part.lower() for part in Path(path_text).parts]
    for part in parts:
        cleaned = part.strip(". ")
        if cleaned in FORBIDDEN_PATH_TOKENS or any(token in cleaned for token in FORBIDDEN_PATH_TOKENS):
            return "Secret/auth/token/key path segments are not allowed."
    return ""


def _validated_output_root(root: Path) -> Path:
    resolved = root.resolve()
    if _has_protected_pair(resolved):
        raise ValueError("Expected-hash verification output_root cannot target protected paths.")
    return resolved


def _has_protected_pair(path: Path) -> bool:
    parts = [part.lower() for part in path.parts]
    return any(_contains_pair(parts, pair) for pair in PROTECTED_PATH_PAIRS)


def _contains_pair(parts: list[str], pair: tuple[str, str]) -> bool:
    return any(first == pair[0] and second == pair[1] for first, second in zip(parts, parts[1:]))


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _blocked_result(
    *,
    artifact_paths: dict[str, Path],
    run_id: str,
    runtime_status: str,
    reason: str,
    max_manifest_size_bytes: int,
    expected_hash_present: bool = False,
    expected_hash_preview: str = "",
) -> dict[str, Any]:
    return _result_payload(
        artifact_paths=artifact_paths,
        run_id=run_id,
        runtime_status=runtime_status,
        health_status="FAIL",
        file_touch_level=FILE_TOUCH_NONE,
        csv_read_level=CSV_READ_NONE,
        local_file_hash_level=LOCAL_FILE_HASH_NONE,
        expected_hash_verification_level=EXPECTED_HASH_VERIFICATION_NONE,
        expected_hash_present=expected_hash_present,
        expected_hash_preview=expected_hash_preview,
        issue_count=1,
        warning_count=0,
        max_manifest_size_bytes=max_manifest_size_bytes,
        issues=[{"severity": "ERROR", "issue_code": runtime_status, "message": reason}],
        limitations=["Blocked before metadata-only expected-hash verification could run."],
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
    expected_hash_verification_level: str,
    expected_hash_verification_performed: bool = False,
    expected_hash_algorithm: str = "",
    expected_hash_present: bool = False,
    expected_hash_preview: str = "",
    actual_local_file_byte_hash_algorithm: str = "",
    actual_local_file_byte_hash_preview: str = "",
    expected_hash_matched: bool = False,
    expected_hash_mismatch: bool = False,
    expected_hash_verified_against_local_metadata: bool = False,
    issue_count: int = 0,
    warning_count: int = 0,
    actionable_mismatch: bool = False,
    max_manifest_size_bytes: int = MAX_MANIFEST_SIZE_BYTES,
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
        "expected_hash_verification_level": expected_hash_verification_level,
        "expected_hash_verification_performed": expected_hash_verification_performed,
        "expected_hash_algorithm": expected_hash_algorithm,
        "expected_hash_present": expected_hash_present,
        "expected_hash_preview": expected_hash_preview,
        "actual_local_file_byte_hash_algorithm": actual_local_file_byte_hash_algorithm,
        "actual_local_file_byte_hash_preview": actual_local_file_byte_hash_preview,
        "expected_hash_matched": expected_hash_matched,
        "expected_hash_mismatch": expected_hash_mismatch,
        "expected_hash_verified_against_local_metadata": expected_hash_verified_against_local_metadata,
        "expected_hash_verified_against_source_hash": False,
        "source_hash_validated": False,
        "revision_id_validated": False,
        "available_time_validated": False,
        "pit_admissibility_validated": False,
        "source_reliability_scored": False,
        "reviewer_authority_validated": False,
        "local_file_byte_hash_recomputed": False,
        "target_file_opened_for_expected_hash_verification": False,
        "csv_file_opened_structurally": False,
        "csv_header_read": False,
        "csv_row_count_computed": False,
        "csv_row_count": "",
        "csv_values_read": False,
        "csv_full_content_read": False,
        "real_csv_consumed": False,
        "issue_count": issue_count,
        "warning_count": warning_count,
        "actionable_mismatch": actionable_mismatch,
        "max_manifest_size_bytes": max_manifest_size_bytes,
        "recommended_next_task": NEXT_TASK,
        "artifact_paths": artifact_paths,
        "issues": issues or [],
        "limitations": limitations or [],
    }
    result.update(expected_hash_verification_safety_flags())
    return result


def _artifact_paths(root: Path) -> dict[str, Path]:
    return {name: root / filename for name, filename in ARTIFACT_FILENAMES.items()}


def _write_artifacts(result: dict[str, Any]) -> None:
    for path in result["artifact_paths"].values():
        path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(result["artifact_paths"]["metadata"], _metadata_payload(result))
    _write_json(result["artifact_paths"]["forbidden_downstream_flags"], expected_hash_verification_safety_flags())
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
        "expected_hash_verification_level",
        "expected_hash_verification_performed",
        "expected_hash_algorithm",
        "expected_hash_present",
        "expected_hash_preview",
        "actual_local_file_byte_hash_algorithm",
        "actual_local_file_byte_hash_preview",
        "expected_hash_matched",
        "expected_hash_mismatch",
        "expected_hash_verified_against_local_metadata",
        "expected_hash_verified_against_source_hash",
        "source_hash_validated",
        "revision_id_validated",
        "available_time_validated",
        "pit_admissibility_validated",
        "source_reliability_scored",
        "reviewer_authority_validated",
        "local_file_byte_hash_recomputed",
        "target_file_opened_for_expected_hash_verification",
        "csv_file_opened_structurally",
        "csv_header_read",
        "csv_row_count_computed",
        "csv_row_count",
        "csv_values_read",
        "csv_full_content_read",
        "real_csv_consumed",
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
        "issue_count",
        "warning_count",
        "actionable_mismatch",
        "recommended_next_task",
    ]
    return {field: result[field] for field in fields}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    lines = [",".join(columns)]
    for row in rows:
        lines.append(",".join(_csv_cell(row.get(column, "")) for column in columns))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _csv_cell(value: Any) -> str:
    text = str(value)
    if any(char in text for char in [",", '"', "\n", "\r"]):
        return '"' + text.replace('"', '""') + '"'
    return text


def _empty_issue_row() -> dict[str, str]:
    return {"severity": "", "issue_code": "", "message": ""}


def _limitations_text(result: dict[str, Any]) -> str:
    lines = ["# Limitations", ""]
    lines.extend(f"- {item}" for item in result["limitations"])
    lines.extend(
        [
            "- Expected-hash verification is metadata-reference-only.",
            "- It is not source_hash, revision_id, available_time, PIT, reviewer, package, replay, buy-review, performance, or trading validation.",
            "- Full hashes are not copied into generated verification artifacts.",
            "",
        ]
    )
    return "\n".join(lines)


def _report_text(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expected-Hash Verification Report",
            "",
            f"- Runtime status: `{result['runtime_status']}`",
            f"- Health status: `{result['health_status']}`",
            f"- File touch level: `{result['file_touch_level']}`",
            f"- CSV read level: `{result['csv_read_level']}`",
            f"- Local file hash level: `{result['local_file_hash_level']}`",
            f"- Expected-hash verification level: `{result['expected_hash_verification_level']}`",
            f"- Expected-hash verification performed: `{str(result['expected_hash_verification_performed']).lower()}`",
            f"- Expected hash algorithm: `{result['expected_hash_algorithm']}`",
            f"- Expected hash preview: `{result['expected_hash_preview']}`",
            f"- Actual local file byte hash preview: `{result['actual_local_file_byte_hash_preview']}`",
            f"- Expected hash matched: `{str(result['expected_hash_matched']).lower()}`",
            f"- Expected hash mismatch: `{str(result['expected_hash_mismatch']).lower()}`",
            f"- Source hash validated: `{str(result['source_hash_validated']).lower()}`",
            f"- Revision id validated: `{str(result['revision_id_validated']).lower()}`",
            f"- Available time validated: `{str(result['available_time_validated']).lower()}`",
            f"- PIT admissibility validated: `{str(result['pit_admissibility_validated']).lower()}`",
            f"- Reviewer authority validated: `{str(result['reviewer_authority_validated']).lower()}`",
            f"- Target file opened for expected-hash verification: `{str(result['target_file_opened_for_expected_hash_verification']).lower()}`",
            f"- Local file byte hash recomputed: `{str(result['local_file_byte_hash_recomputed']).lower()}`",
            f"- Real CSV consumed: `{str(result['real_csv_consumed']).lower()}`",
            f"- Issue count: `{result['issue_count']}`",
            f"- Warning count: `{result['warning_count']}`",
            f"- Actionable mismatch: `{str(result['actionable_mismatch']).lower()}`",
            f"- Recommended next task: `{result['recommended_next_task']}`",
            "",
        ]
    )


def _schema_reason(issue: str) -> str:
    if issue.startswith("missing_"):
        return "Expected-hash manifest is missing a required field."
    if issue == "unsupported_algorithm":
        return "Only SHA-256 expected-hash manifests are supported."
    if issue == "unsupported_disclosure":
        return "Expected-hash disclosure level must remain preview-only."
    if issue == "forbidden_downstream":
        return "Forbidden downstream flags must all be false."
    if issue == "expected_hash_value":
        return "expected_hash_value must be exactly 64 hex characters."
    if issue == "metadata_path_mismatch":
        return "Manifest metadata path must match the API metadata path."
    return "Expected-hash manifest schema is invalid."


def _preview(value: str) -> str:
    return value[:HASH_PREVIEW_HEX_CHARS]


def _preview_if_hex(value: str) -> str:
    return _preview(value.lower()) if _is_64_hex(value) else ""


def _is_64_hex(value: str) -> bool:
    if len(value) != 64:
        return False
    return all(char in "0123456789abcdefABCDEF" for char in value)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
