"""Source artifact byte-hash core for Tiny PIT reviewed LOCAL_CSV candidates.

This module is report-only and diagnostic-only. It may stream one explicit
non-CSV source artifact as opaque bytes for SHA-256 under manifest/root/allow
guards. It does not decode or parse source content, open target CSVs, validate
PIT/source/reviewer semantics, create package candidates, or enable replay,
buy-review, or trading behavior.
"""

from __future__ import annotations

import csv
import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence


STATUS_NO_INPUT = "NO_SOURCE_ARTIFACT_BYTE_HASH_INPUT"
STATUS_REPORT_ONLY = "SOURCE_ARTIFACT_BYTE_HASH_REPORT_ONLY"
STATUS_MATCHED = "SOURCE_ARTIFACT_BYTE_HASH_MATCHED_REPORT_ONLY"
STATUS_MISMATCHED = "SOURCE_ARTIFACT_BYTE_HASH_MISMATCHED_REPORT_ONLY"
STATUS_WARN_SOURCE_HASH_METADATA_MISSING = "SOURCE_ARTIFACT_BYTE_HASH_WARN_SOURCE_HASH_METADATA_MISSING"
STATUS_WARN_REVISION_OR_AVAILABLE_TIME_METADATA_MISSING = (
    "SOURCE_ARTIFACT_BYTE_HASH_WARN_REVISION_OR_AVAILABLE_TIME_METADATA_MISSING"
)
STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG = "SOURCE_ARTIFACT_BYTE_HASH_BLOCKED_BY_MISSING_ALLOW_FLAG"
STATUS_BLOCKED_BY_MANIFEST_SCHEMA = "SOURCE_ARTIFACT_BYTE_HASH_BLOCKED_BY_MANIFEST_SCHEMA"
STATUS_BLOCKED_BY_PATH_GUARD = "SOURCE_ARTIFACT_BYTE_HASH_BLOCKED_BY_PATH_GUARD"
STATUS_BLOCKED_BY_UNSUPPORTED_ALGORITHM = "SOURCE_ARTIFACT_BYTE_HASH_BLOCKED_BY_UNSUPPORTED_ALGORITHM"
STATUS_BLOCKED_BY_FILE_SIZE_LIMIT = "SOURCE_ARTIFACT_BYTE_HASH_BLOCKED_BY_FILE_SIZE_LIMIT"
STATUS_BLOCKED_BY_FORBIDDEN_EXTENSION = "SOURCE_ARTIFACT_BYTE_HASH_BLOCKED_BY_FORBIDDEN_EXTENSION"
STATUS_BLOCKED_BY_SOURCE_CONTENT_READ_ATTEMPT = (
    "SOURCE_ARTIFACT_BYTE_HASH_BLOCKED_BY_SOURCE_CONTENT_READ_ATTEMPT"
)
STATUS_BLOCKED_BY_TARGET_CSV_READ_ATTEMPT = (
    "SOURCE_ARTIFACT_BYTE_HASH_BLOCKED_BY_TARGET_CSV_READ_ATTEMPT"
)
STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM = "SOURCE_ARTIFACT_BYTE_HASH_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
STATUS_BLOCKED_BY_UNSAFE_VALIDATION_CLAIM = (
    "SOURCE_ARTIFACT_BYTE_HASH_BLOCKED_BY_UNSAFE_VALIDATION_CLAIM"
)
STATUS_HEALTH_FAILED = "SOURCE_ARTIFACT_BYTE_HASH_HEALTH_FAILED"

FORBIDDEN_LIVE_POSITIVE_STATUSES = [
    "SOURCE_RELIABILITY_VALIDATED",
    "SOURCE_HASH_VALIDATED",
    "PIT_ADMISSIBLE_PACKAGE",
    "PACKAGE_APPROVED",
    "PACKAGE_ADMISSIBLE",
    "READY_FOR_REPLAY",
    "ACTIVE_REPLAY_INPUT_READY",
    "BUY_REVIEW_READY",
    "TRADING_READY",
    "PERFORMANCE_VALIDATED",
]

WORKFLOW_NAME = "tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash"
WORKFLOW_STAGE = (
    "TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_"
    "SOURCE_ARTIFACT_BYTE_HASH_CORE_CREATED_REPORT_ONLY"
)
CREATED_AT = "2026-07-04T00:00:00Z"
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Artifact Byte-Hash "
    "Artifact Views Report-Only v0.1"
)

SOURCE_ARTIFACT_BYTE_READ_NONE = "SOURCE_ARTIFACT_BYTE_READ_NONE"
SOURCE_ARTIFACT_BYTE_READ_STREAMING_HASH_ONLY = "SOURCE_ARTIFACT_BYTE_READ_STREAMING_HASH_ONLY"
SOURCE_HASH_RECOMPUTE_NONE = "SOURCE_HASH_RECOMPUTE_NONE"
SOURCE_HASH_RECOMPUTE_SHA256_ONLY = "SOURCE_HASH_RECOMPUTE_SHA256_ONLY"
SOURCE_CONTENT_READ_NONE = "SOURCE_CONTENT_READ_NONE"
CSV_READ_NONE = "CSV_READ_NONE"
LOCAL_FILE_HASH_NONE = "LOCAL_FILE_HASH_NONE"
EXPECTED_HASH_VERIFICATION_NONE = "EXPECTED_HASH_VERIFICATION_NONE"
SOURCE_HASH_VALIDATION_NONE = "SOURCE_HASH_VALIDATION_NONE"
REVISION_ID_VALIDATION_NONE = "REVISION_ID_VALIDATION_NONE"
AVAILABLE_TIME_VALIDATION_NONE = "AVAILABLE_TIME_VALIDATION_NONE"
PIT_ADMISSIBILITY_NONE = "PIT_ADMISSIBILITY_NONE"
SOURCE_RELIABILITY_NONE = "SOURCE_RELIABILITY_NONE"
REVIEWER_AUTHORITY_NONE = "REVIEWER_AUTHORITY_NONE"
PACKAGE_CREATION_NONE = "PACKAGE_CREATION_NONE"
ACTIVE_INPUT_NONE = "ACTIVE_INPUT_NONE"
REPLAY_READINESS_NONE = "REPLAY_READINESS_NONE"
SOURCE_ARTIFACT_BYTE_IDENTITY_COMPARED_REPORT_ONLY = (
    "SOURCE_ARTIFACT_BYTE_IDENTITY_COMPARED_REPORT_ONLY"
)

MAX_MANIFEST_SIZE_BYTES = 1_048_576
DEFAULT_MAX_SOURCE_ARTIFACT_SIZE_BYTES = 104_857_600
HASH_PREVIEW_LENGTH = 16
HASH_ALGORITHM = "SHA-256"
FULL_HASH_RECORDING_LOCAL_METADATA_ONLY = "LOCAL_METADATA_ONLY"
DISCLOSURE_PREVIEW_ONLY_PUBLIC_SURFACES = "PREVIEW_ONLY_PUBLIC_SURFACES"

ARTIFACT_FILENAMES = {
    "metadata": "metadata.json",
    "report": "source_artifact_byte_hash_report.md",
    "limitations": "limitations.md",
    "issues": "issues.csv",
    "summary": "source_artifact_byte_hash_summary.csv",
    "forbidden_downstream_flags": "forbidden_downstream_flags.json",
}

REQUIRED_MANIFEST_FIELDS = [
    "source_artifact_hash_request_id",
    "source_id",
    "source_artifact_id",
    "source_artifact_declared_name",
    "source_artifact_path_ref",
    "report_only",
    "diagnostic_only",
    "requested_source_artifact_byte_read_level",
    "requested_source_hash_recompute_level",
    "requested_source_content_read_level",
    "requested_csv_read_level",
    "requested_local_file_hash_level",
    "requested_expected_hash_verification_level",
    "requested_source_hash_validation_level",
    "requested_revision_id_validation_level",
    "requested_available_time_validation_level",
    "requested_pit_admissibility_level",
    "requested_source_reliability_level",
    "requested_reviewer_authority_level",
    "requested_package_creation_level",
    "requested_active_input_level",
    "requested_replay_readiness_level",
    "source_hash_algorithm",
    "declared_source_hash",
    "source_lineage_metadata_ref",
    "revision_id_metadata_ref",
    "available_time_metadata_ref",
    "compare_to_declared_source_hash",
    "full_hash_recording_policy",
    "disclosure_policy",
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
    "metric_computation_performed",
    "signal_score_implemented",
    "model_training_performed",
    "active_weights_created",
    "active_thresholds_created",
    "stock_profile_validation_created",
    "paper_validation_created",
    "strategy_performance_validated",
    "broker_api_called",
    "order_placed",
    "message_sent",
    "external_api_called",
    "llm_api_called",
    "current_candidates_created",
    "snapshots_created",
    "signal_semantics_mutated",
]

UNSAFE_NON_NONE_LEVELS = {
    "requested_source_content_read_level": SOURCE_CONTENT_READ_NONE,
    "requested_csv_read_level": CSV_READ_NONE,
    "requested_local_file_hash_level": LOCAL_FILE_HASH_NONE,
    "requested_expected_hash_verification_level": EXPECTED_HASH_VERIFICATION_NONE,
    "requested_source_hash_validation_level": SOURCE_HASH_VALIDATION_NONE,
    "requested_revision_id_validation_level": REVISION_ID_VALIDATION_NONE,
    "requested_available_time_validation_level": AVAILABLE_TIME_VALIDATION_NONE,
    "requested_pit_admissibility_level": PIT_ADMISSIBILITY_NONE,
    "requested_source_reliability_level": SOURCE_RELIABILITY_NONE,
    "requested_reviewer_authority_level": REVIEWER_AUTHORITY_NONE,
    "requested_package_creation_level": PACKAGE_CREATION_NONE,
    "requested_active_input_level": ACTIVE_INPUT_NONE,
    "requested_replay_readiness_level": REPLAY_READINESS_NONE,
}

FORBIDDEN_PATH_TOKENS = {
    ".env",
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
NETWORK_PREFIXES = ("http://", "https://", "ftp://", "s3://", "gs://", "oss://", "file://")


def source_artifact_byte_hash_statuses() -> list[str]:
    return [
        STATUS_NO_INPUT,
        STATUS_REPORT_ONLY,
        STATUS_MATCHED,
        STATUS_MISMATCHED,
        STATUS_WARN_SOURCE_HASH_METADATA_MISSING,
        STATUS_WARN_REVISION_OR_AVAILABLE_TIME_METADATA_MISSING,
        STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
        STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
        STATUS_BLOCKED_BY_PATH_GUARD,
        STATUS_BLOCKED_BY_UNSUPPORTED_ALGORITHM,
        STATUS_BLOCKED_BY_FILE_SIZE_LIMIT,
        STATUS_BLOCKED_BY_FORBIDDEN_EXTENSION,
        STATUS_BLOCKED_BY_SOURCE_CONTENT_READ_ATTEMPT,
        STATUS_BLOCKED_BY_TARGET_CSV_READ_ATTEMPT,
        STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
        STATUS_BLOCKED_BY_UNSAFE_VALIDATION_CLAIM,
        STATUS_HEALTH_FAILED,
    ]


def source_artifact_byte_hash_safety_flags() -> dict[str, bool]:
    return {field: False for field in REQUIRED_FALSE_FLAGS}


def run_source_artifact_byte_hash(
    *,
    output_root: str | Path,
    run_id: str | None = None,
    source_artifact_hash_manifest_path: str | Path | None = None,
    source_lineage_metadata_path: str | Path | None = None,
    source_artifact_path: str | Path | None = None,
    allowed_manifest_roots: Sequence[str | Path] | None = None,
    allowed_source_artifact_roots: Sequence[str | Path] | None = None,
    allow_source_artifact_byte_hash: bool = False,
    max_manifest_size_bytes: int = MAX_MANIFEST_SIZE_BYTES,
    max_source_artifact_size_bytes: int = DEFAULT_MAX_SOURCE_ARTIFACT_SIZE_BYTES,
    hash_algorithm: str = HASH_ALGORITHM,
    source_artifact_byte_read_level: str = SOURCE_ARTIFACT_BYTE_READ_NONE,
    source_hash_recompute_level: str = SOURCE_HASH_RECOMPUTE_NONE,
    source_content_read_level: str = SOURCE_CONTENT_READ_NONE,
    csv_read_level: str = CSV_READ_NONE,
    local_file_hash_level: str = LOCAL_FILE_HASH_NONE,
    expected_hash_verification_level: str = EXPECTED_HASH_VERIFICATION_NONE,
    source_hash_validation_level: str = SOURCE_HASH_VALIDATION_NONE,
    revision_id_validation_level: str = REVISION_ID_VALIDATION_NONE,
    available_time_validation_level: str = AVAILABLE_TIME_VALIDATION_NONE,
    pit_admissibility_level: str = PIT_ADMISSIBILITY_NONE,
    source_reliability_level: str = SOURCE_RELIABILITY_NONE,
    reviewer_authority_level: str = REVIEWER_AUTHORITY_NONE,
    package_creation_level: str = PACKAGE_CREATION_NONE,
    active_input_level: str = ACTIVE_INPUT_NONE,
    replay_readiness_level: str = REPLAY_READINESS_NONE,
    compare_to_declared_source_hash: bool = True,
    full_hash_recording_policy: str = FULL_HASH_RECORDING_LOCAL_METADATA_ONLY,
    disclosure_policy: str = DISCLOSURE_PREVIEW_ONLY_PUBLIC_SURFACES,
) -> dict[str, Any]:
    artifact_root = _validated_output_root(Path(output_root)) / (run_id or uuid.uuid4().hex[:12])
    artifact_paths = _artifact_paths(artifact_root)
    max_manifest_bytes = int(max_manifest_size_bytes)
    max_artifact_bytes = int(max_source_artifact_size_bytes)

    if source_artifact_hash_manifest_path is None:
        result = _result_payload(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_NO_INPUT,
            health_status="PASS",
            max_manifest_size_bytes=max_manifest_bytes,
            max_source_artifact_size_bytes=max_artifact_bytes,
            issues=[],
            limitations=["No input supplied; no source artifact byte hash was computed."],
        )
        _write_artifacts(result)
        return result

    requested_levels = {
        "source_artifact_byte_read_level": source_artifact_byte_read_level,
        "source_hash_recompute_level": source_hash_recompute_level,
        "source_content_read_level": source_content_read_level,
        "csv_read_level": csv_read_level,
        "local_file_hash_level": local_file_hash_level,
        "expected_hash_verification_level": expected_hash_verification_level,
        "source_hash_validation_level": source_hash_validation_level,
        "revision_id_validation_level": revision_id_validation_level,
        "available_time_validation_level": available_time_validation_level,
        "pit_admissibility_level": pit_admissibility_level,
        "source_reliability_level": source_reliability_level,
        "reviewer_authority_level": reviewer_authority_level,
        "package_creation_level": package_creation_level,
        "active_input_level": active_input_level,
        "replay_readiness_level": replay_readiness_level,
    }
    level_issue = _requested_level_issue(requested_levels)
    if level_issue:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=level_issue,
            reason="Only opaque source artifact byte-hash report-only levels are supported.",
            max_manifest_size_bytes=max_manifest_bytes,
            max_source_artifact_size_bytes=max_artifact_bytes,
        )
        _write_artifacts(result)
        return result

    if hash_algorithm != HASH_ALGORITHM:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_UNSUPPORTED_ALGORITHM,
            reason="Only SHA-256 is supported.",
            max_manifest_size_bytes=max_manifest_bytes,
            max_source_artifact_size_bytes=max_artifact_bytes,
        )
        _write_artifacts(result)
        return result

    if not allow_source_artifact_byte_hash:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
            reason="allow_source_artifact_byte_hash must be true for source artifact byte hashing.",
            max_manifest_size_bytes=max_manifest_bytes,
            max_source_artifact_size_bytes=max_artifact_bytes,
        )
        _write_artifacts(result)
        return result

    manifest_check = _check_input_json_path(
        source_artifact_hash_manifest_path,
        allowed_manifest_roots,
        "source_artifact_hash_manifest_path",
        max_manifest_bytes,
    )
    if manifest_check["blocked"]:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_PATH_GUARD,
            reason=manifest_check["reason"],
            max_manifest_size_bytes=max_manifest_bytes,
            max_source_artifact_size_bytes=max_artifact_bytes,
        )
        _write_artifacts(result)
        return result

    manifest, manifest_error = _load_json_object(manifest_check["path"])
    if manifest_error:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            reason=manifest_error,
            max_manifest_size_bytes=max_manifest_bytes,
            max_source_artifact_size_bytes=max_artifact_bytes,
        )
        _write_artifacts(result)
        return result

    schema_issue = _manifest_schema_issue(manifest)
    if schema_issue:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=schema_issue if schema_issue.startswith("SOURCE_ARTIFACT_BYTE_HASH_") else STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            reason=schema_issue,
            max_manifest_size_bytes=max_manifest_bytes,
            max_source_artifact_size_bytes=max_artifact_bytes,
        )
        _write_artifacts(result)
        return result

    forbidden_issue = _forbidden_downstream_issue(manifest["forbidden_downstream_flags"])
    if forbidden_issue:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
            reason=forbidden_issue,
            max_manifest_size_bytes=max_manifest_bytes,
            max_source_artifact_size_bytes=max_artifact_bytes,
        )
        _write_artifacts(result)
        return result

    metadata = {}
    if source_lineage_metadata_path is not None:
        metadata_check = _check_input_json_path(
            source_lineage_metadata_path,
            allowed_manifest_roots,
            "source_lineage_metadata_path",
            max_manifest_bytes,
        )
        if metadata_check["blocked"]:
            result = _blocked_result(
                artifact_paths=artifact_paths,
                run_id=artifact_root.name,
                runtime_status=STATUS_BLOCKED_BY_PATH_GUARD,
                reason=metadata_check["reason"],
                max_manifest_size_bytes=max_manifest_bytes,
                max_source_artifact_size_bytes=max_artifact_bytes,
            )
            _write_artifacts(result)
            return result
        metadata, metadata_error = _load_json_object(metadata_check["path"])
        if metadata_error:
            result = _blocked_result(
                artifact_paths=artifact_paths,
                run_id=artifact_root.name,
                runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
                reason=metadata_error,
                max_manifest_size_bytes=max_manifest_bytes,
                max_source_artifact_size_bytes=max_artifact_bytes,
            )
            _write_artifacts(result)
            return result

    manifest_artifact_text = str(manifest.get("source_artifact_path_ref") or "")
    manifest_artifact_guard = _guard_path_text(manifest_artifact_text)
    if manifest_artifact_guard:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_PATH_GUARD,
            reason=f"source_artifact_path_ref: {manifest_artifact_guard}",
            source_id=str(manifest.get("source_id") or ""),
            source_artifact_id=str(manifest.get("source_artifact_id") or ""),
            source_artifact_name_preview=_safe_name(manifest.get("source_artifact_declared_name")),
            source_artifact_path_preview=_path_preview(manifest_artifact_text),
            max_manifest_size_bytes=max_manifest_bytes,
            max_source_artifact_size_bytes=max_artifact_bytes,
        )
        _write_artifacts(result)
        return result

    if source_artifact_path is not None:
        explicit_artifact_text = str(source_artifact_path)
        explicit_artifact_guard = _guard_path_text(explicit_artifact_text)
        if explicit_artifact_guard:
            result = _blocked_result(
                artifact_paths=artifact_paths,
                run_id=artifact_root.name,
                runtime_status=STATUS_BLOCKED_BY_PATH_GUARD,
                reason=f"source_artifact_path: {explicit_artifact_guard}",
                source_id=str(manifest.get("source_id") or ""),
                source_artifact_id=str(manifest.get("source_artifact_id") or ""),
                source_artifact_name_preview=_safe_name(manifest.get("source_artifact_declared_name")),
                source_artifact_path_preview=_path_preview(explicit_artifact_text),
                max_manifest_size_bytes=max_manifest_bytes,
                max_source_artifact_size_bytes=max_artifact_bytes,
            )
            _write_artifacts(result)
            return result
        if Path(explicit_artifact_text).resolve(strict=False) != Path(manifest_artifact_text).resolve(strict=False):
            result = _blocked_result(
                artifact_paths=artifact_paths,
                run_id=artifact_root.name,
                runtime_status=STATUS_BLOCKED_BY_PATH_GUARD,
                reason="source_artifact_path must match source_artifact_path_ref from manifest.",
                source_id=str(manifest.get("source_id") or ""),
                source_artifact_id=str(manifest.get("source_artifact_id") or ""),
                source_artifact_name_preview=_safe_name(manifest.get("source_artifact_declared_name")),
                source_artifact_path_preview=_path_preview(explicit_artifact_text),
                max_manifest_size_bytes=max_manifest_bytes,
                max_source_artifact_size_bytes=max_artifact_bytes,
            )
            _write_artifacts(result)
            return result

    artifact_text = str(source_artifact_path or manifest_artifact_text)
    artifact_check = _check_source_artifact_path(
        artifact_text,
        allowed_source_artifact_roots,
        max_artifact_bytes,
    )
    if artifact_check["blocked"]:
        status = artifact_check.get("status") or STATUS_BLOCKED_BY_PATH_GUARD
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=status,
            reason=artifact_check["reason"],
            source_id=str(manifest.get("source_id") or ""),
            source_artifact_id=str(manifest.get("source_artifact_id") or ""),
            source_artifact_name_preview=_safe_name(manifest.get("source_artifact_declared_name")),
            source_artifact_path_preview=_path_preview(artifact_text),
            max_manifest_size_bytes=max_manifest_bytes,
            max_source_artifact_size_bytes=max_artifact_bytes,
        )
        _write_artifacts(result)
        return result

    full_hash = _sha256_file(artifact_check["path"])
    declared_hash = _declared_hash(manifest, metadata)
    declared_present = _is_sha256_hex(declared_hash)
    match = bool(compare_to_declared_source_hash and declared_present and full_hash.lower() == declared_hash.lower())
    mismatch = bool(compare_to_declared_source_hash and declared_present and not match)
    if not declared_present:
        runtime_status = STATUS_WARN_SOURCE_HASH_METADATA_MISSING
        health_status = "WARN"
    elif mismatch:
        runtime_status = STATUS_MISMATCHED
        health_status = "WARN"
    elif match:
        runtime_status = STATUS_MATCHED
        health_status = "PASS"
    else:
        runtime_status = STATUS_REPORT_ONLY
        health_status = "PASS"

    result = _result_payload(
        artifact_paths=artifact_paths,
        run_id=artifact_root.name,
        runtime_status=runtime_status,
        health_status=health_status,
        source_id=str(manifest["source_id"]),
        source_artifact_id=str(manifest["source_artifact_id"]),
        source_artifact_name_preview=_safe_name(manifest.get("source_artifact_declared_name")),
        source_artifact_path_preview=_path_preview(artifact_check["path"]),
        source_artifact_file_size_bytes=artifact_check["size"],
        source_hash_algorithm=HASH_ALGORITHM,
        source_artifact_byte_read_level=SOURCE_ARTIFACT_BYTE_READ_STREAMING_HASH_ONLY,
        source_hash_recompute_level=SOURCE_HASH_RECOMPUTE_SHA256_ONLY,
        source_artifact_opened_for_hash=True,
        source_artifact_bytes_streamed_for_hash=True,
        source_hash_recomputed=True,
        computed_source_hash_preview=full_hash[:HASH_PREVIEW_LENGTH],
        computed_source_hash_full=(
            full_hash if full_hash_recording_policy == FULL_HASH_RECORDING_LOCAL_METADATA_ONLY else ""
        ),
        computed_source_hash_full_recorded_in_metadata=(
            full_hash_recording_policy == FULL_HASH_RECORDING_LOCAL_METADATA_ONLY
        ),
        declared_source_hash_present=declared_present,
        declared_source_hash_preview=(declared_hash[:HASH_PREVIEW_LENGTH].lower() if declared_present else ""),
        source_artifact_byte_identity_matched=match,
        source_artifact_byte_identity_mismatch=mismatch,
        source_artifact_byte_identity_actionable_mismatch=mismatch,
        max_manifest_size_bytes=max_manifest_bytes,
        max_source_artifact_size_bytes=max_artifact_bytes,
        warning_count=1 if health_status == "WARN" else 0,
        issues=(
            [
                {
                    "severity": "WARN",
                    "issue_code": runtime_status,
                    "message": "Source artifact byte hash did not match declared source hash preview.",
                }
            ]
            if mismatch
            else (
                [
                    {
                        "severity": "WARN",
                        "issue_code": runtime_status,
                        "message": "Declared source hash metadata is missing or not SHA-256 shaped.",
                    }
                ]
                if not declared_present
                else []
            )
        ),
        limitations=list(manifest["limitations"]),
    )
    _write_artifacts(result)
    return result


def _requested_level_issue(levels: dict[str, str]) -> str:
    if levels["source_artifact_byte_read_level"] not in {
        SOURCE_ARTIFACT_BYTE_READ_NONE,
        SOURCE_ARTIFACT_BYTE_READ_STREAMING_HASH_ONLY,
    }:
        return STATUS_BLOCKED_BY_UNSAFE_VALIDATION_CLAIM
    if levels["source_hash_recompute_level"] not in {SOURCE_HASH_RECOMPUTE_NONE, SOURCE_HASH_RECOMPUTE_SHA256_ONLY}:
        return STATUS_BLOCKED_BY_UNSAFE_VALIDATION_CLAIM
    if levels["source_artifact_byte_read_level"] == SOURCE_ARTIFACT_BYTE_READ_NONE and levels["source_hash_recompute_level"] == SOURCE_HASH_RECOMPUTE_SHA256_ONLY:
        return STATUS_BLOCKED_BY_UNSAFE_VALIDATION_CLAIM
    for name, expected in {
        "source_content_read_level": SOURCE_CONTENT_READ_NONE,
        "csv_read_level": CSV_READ_NONE,
        "local_file_hash_level": LOCAL_FILE_HASH_NONE,
        "expected_hash_verification_level": EXPECTED_HASH_VERIFICATION_NONE,
        "source_hash_validation_level": SOURCE_HASH_VALIDATION_NONE,
        "revision_id_validation_level": REVISION_ID_VALIDATION_NONE,
        "available_time_validation_level": AVAILABLE_TIME_VALIDATION_NONE,
        "pit_admissibility_level": PIT_ADMISSIBILITY_NONE,
        "source_reliability_level": SOURCE_RELIABILITY_NONE,
        "reviewer_authority_level": REVIEWER_AUTHORITY_NONE,
        "package_creation_level": PACKAGE_CREATION_NONE,
        "active_input_level": ACTIVE_INPUT_NONE,
        "replay_readiness_level": REPLAY_READINESS_NONE,
    }.items():
        if levels[name] != expected:
            if name == "source_content_read_level":
                return STATUS_BLOCKED_BY_SOURCE_CONTENT_READ_ATTEMPT
            if name == "csv_read_level":
                return STATUS_BLOCKED_BY_TARGET_CSV_READ_ATTEMPT
            return STATUS_BLOCKED_BY_UNSAFE_VALIDATION_CLAIM
    return ""


def _manifest_schema_issue(manifest: Any) -> str:
    if not isinstance(manifest, dict):
        return "Manifest must be a JSON object."
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    if missing:
        return f"Missing required manifest fields: {','.join(missing)}"
    if manifest.get("report_only") is not True or manifest.get("diagnostic_only") is not True:
        return "report_only and diagnostic_only must be true."
    if manifest.get("source_hash_algorithm") != HASH_ALGORITHM:
        return STATUS_BLOCKED_BY_UNSUPPORTED_ALGORITHM
    if manifest.get("requested_source_artifact_byte_read_level") != SOURCE_ARTIFACT_BYTE_READ_STREAMING_HASH_ONLY:
        return STATUS_BLOCKED_BY_UNSAFE_VALIDATION_CLAIM
    if manifest.get("requested_source_hash_recompute_level") != SOURCE_HASH_RECOMPUTE_SHA256_ONLY:
        return STATUS_BLOCKED_BY_UNSAFE_VALIDATION_CLAIM
    for field, expected in UNSAFE_NON_NONE_LEVELS.items():
        if manifest.get(field) != expected:
            if field == "requested_source_content_read_level":
                return STATUS_BLOCKED_BY_SOURCE_CONTENT_READ_ATTEMPT
            if field == "requested_csv_read_level":
                return STATUS_BLOCKED_BY_TARGET_CSV_READ_ATTEMPT
            return STATUS_BLOCKED_BY_UNSAFE_VALIDATION_CLAIM
    if manifest.get("full_hash_recording_policy") != FULL_HASH_RECORDING_LOCAL_METADATA_ONLY:
        return "full_hash_recording_policy must be LOCAL_METADATA_ONLY."
    if manifest.get("disclosure_policy") != DISCLOSURE_PREVIEW_ONLY_PUBLIC_SURFACES:
        return "disclosure_policy must be PREVIEW_ONLY_PUBLIC_SURFACES."
    if not isinstance(manifest.get("limitations"), list) or not manifest["limitations"]:
        return "limitations must be a non-empty list."
    if not isinstance(manifest.get("forbidden_downstream_flags"), dict):
        return "forbidden_downstream_flags must be an object."
    return ""


def _forbidden_downstream_issue(flags: dict[str, Any]) -> str:
    for field in REQUIRED_FALSE_FLAGS:
        if field not in flags:
            return f"Missing forbidden downstream flag: {field}"
        if bool(flags[field]):
            return f"Forbidden downstream flag is true: {field}"
    return ""


def _check_input_json_path(
    path: str | Path,
    allowed_roots: Sequence[str | Path] | None,
    label: str,
    max_bytes: int,
) -> dict[str, Any]:
    if not allowed_roots:
        return {"blocked": True, "reason": f"{label} requires explicit allowed roots"}
    raw = str(path)
    guard = _guard_path_text(raw)
    if guard:
        return {"blocked": True, "reason": guard}
    candidate = Path(path)
    if candidate.suffix.lower() != ".json":
        return {"blocked": True, "reason": f"{label} must be a JSON file"}
    check = _existing_file_under_allowed_roots(candidate, allowed_roots, label)
    if check["blocked"]:
        return check
    if check["path"].stat().st_size > max_bytes:
        return {"blocked": True, "reason": f"{label} exceeds max_manifest_size_bytes"}
    return check


def _check_source_artifact_path(
    path: str | Path,
    allowed_roots: Sequence[str | Path] | None,
    max_bytes: int,
) -> dict[str, Any]:
    if not allowed_roots:
        return {"blocked": True, "reason": "source artifact requires explicit allowed roots"}
    raw = str(path)
    guard = _guard_path_text(raw)
    if guard:
        return {"blocked": True, "reason": guard}
    candidate = Path(path)
    if candidate.suffix.lower() == ".csv":
        return {
            "blocked": True,
            "status": STATUS_BLOCKED_BY_FORBIDDEN_EXTENSION,
            "reason": ".csv source artifacts are blocked in v0.1.",
        }
    check = _existing_file_under_allowed_roots(candidate, allowed_roots, "source_artifact_path")
    if check["blocked"]:
        return check
    size = check["path"].stat().st_size
    if size <= 0 or size > max_bytes:
        return {
            "blocked": True,
            "status": STATUS_BLOCKED_BY_FILE_SIZE_LIMIT,
            "reason": "source artifact file size is outside allowed bounds.",
        }
    check["size"] = size
    return check


def _existing_file_under_allowed_roots(
    path: Path,
    allowed_roots: Sequence[str | Path] | None,
    label: str,
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
    if any(part == ".env" or part.startswith(".env") for part in parts):
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


def _load_json_object(path: Path) -> tuple[dict[str, Any], str]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        return {}, f"JSON is malformed: {exc}"
    if not isinstance(payload, dict):
        return {}, "JSON payload must be an object."
    return payload, ""


def _declared_hash(manifest: dict[str, Any], metadata: dict[str, Any]) -> str:
    manifest_hash = str(manifest.get("declared_source_hash") or "")
    if manifest_hash:
        return manifest_hash
    return str(metadata.get("source_hash_value") or "")


def _validated_output_root(root: Path) -> Path:
    normalized = root.as_posix().lower()
    forbidden = ["data/raw", "data/processed", "data/cache", "docs/project_sources"]
    if any(fragment in normalized for fragment in forbidden):
        raise ValueError(f"Unsafe source artifact byte-hash output root: {root}")
    return root


def _blocked_result(
    *,
    artifact_paths: dict[str, Path],
    run_id: str,
    runtime_status: str,
    reason: str,
    source_id: str = "",
    source_artifact_id: str = "",
    source_artifact_name_preview: str = "",
    source_artifact_path_preview: str = "",
    max_manifest_size_bytes: int,
    max_source_artifact_size_bytes: int,
) -> dict[str, Any]:
    return _result_payload(
        artifact_paths=artifact_paths,
        run_id=run_id,
        runtime_status=runtime_status,
        health_status="FAIL",
        source_id=source_id,
        source_artifact_id=source_artifact_id,
        source_artifact_name_preview=source_artifact_name_preview,
        source_artifact_path_preview=source_artifact_path_preview,
        max_manifest_size_bytes=max_manifest_size_bytes,
        max_source_artifact_size_bytes=max_source_artifact_size_bytes,
        issue_count=1,
        issues=[{"severity": "ERROR", "issue_code": runtime_status, "message": _safe_message(reason)}],
        limitations=["Blocked before any source artifact byte hash was computed."],
    )


def _result_payload(
    *,
    artifact_paths: dict[str, Path],
    run_id: str,
    runtime_status: str,
    health_status: str,
    source_id: str = "",
    source_artifact_id: str = "",
    source_artifact_name_preview: str = "",
    source_artifact_path_preview: str = "",
    source_artifact_file_size_bytes: int | str = "",
    source_hash_algorithm: str = "",
    source_artifact_byte_read_level: str = SOURCE_ARTIFACT_BYTE_READ_NONE,
    source_hash_recompute_level: str = SOURCE_HASH_RECOMPUTE_NONE,
    source_content_read_level: str = SOURCE_CONTENT_READ_NONE,
    csv_read_level: str = CSV_READ_NONE,
    local_file_hash_level: str = LOCAL_FILE_HASH_NONE,
    expected_hash_verification_level: str = EXPECTED_HASH_VERIFICATION_NONE,
    source_hash_validation_level: str = SOURCE_HASH_VALIDATION_NONE,
    revision_id_validation_level: str = REVISION_ID_VALIDATION_NONE,
    available_time_validation_level: str = AVAILABLE_TIME_VALIDATION_NONE,
    pit_admissibility_level: str = PIT_ADMISSIBILITY_NONE,
    source_reliability_level: str = SOURCE_RELIABILITY_NONE,
    reviewer_authority_level: str = REVIEWER_AUTHORITY_NONE,
    package_creation_level: str = PACKAGE_CREATION_NONE,
    active_input_level: str = ACTIVE_INPUT_NONE,
    replay_readiness_level: str = REPLAY_READINESS_NONE,
    source_artifact_opened_for_hash: bool = False,
    source_artifact_bytes_streamed_for_hash: bool = False,
    source_hash_recomputed: bool = False,
    computed_source_hash_preview: str = "",
    computed_source_hash_full: str = "",
    computed_source_hash_full_recorded_in_metadata: bool = False,
    declared_source_hash_present: bool = False,
    declared_source_hash_preview: str = "",
    source_artifact_byte_identity_matched: bool = False,
    source_artifact_byte_identity_mismatch: bool = False,
    source_artifact_byte_identity_actionable_mismatch: bool = False,
    max_manifest_size_bytes: int = MAX_MANIFEST_SIZE_BYTES,
    max_source_artifact_size_bytes: int = DEFAULT_MAX_SOURCE_ARTIFACT_SIZE_BYTES,
    issue_count: int = 0,
    warning_count: int = 0,
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
        "source_id": source_id,
        "source_artifact_id": source_artifact_id,
        "source_artifact_name_preview": source_artifact_name_preview,
        "source_artifact_path_preview": source_artifact_path_preview,
        "source_artifact_file_size_bytes": source_artifact_file_size_bytes,
        "source_hash_algorithm": source_hash_algorithm,
        "source_artifact_byte_read_level": source_artifact_byte_read_level,
        "source_hash_recompute_level": source_hash_recompute_level,
        "source_content_read_level": source_content_read_level,
        "csv_read_level": csv_read_level,
        "local_file_hash_level": local_file_hash_level,
        "expected_hash_verification_level": expected_hash_verification_level,
        "source_hash_validation_level": source_hash_validation_level,
        "revision_id_validation_level": revision_id_validation_level,
        "available_time_validation_level": available_time_validation_level,
        "pit_admissibility_level": pit_admissibility_level,
        "source_reliability_level": source_reliability_level,
        "reviewer_authority_level": reviewer_authority_level,
        "package_creation_level": package_creation_level,
        "active_input_level": active_input_level,
        "replay_readiness_level": replay_readiness_level,
        "source_artifact_opened_for_hash": source_artifact_opened_for_hash,
        "source_artifact_bytes_streamed_for_hash": source_artifact_bytes_streamed_for_hash,
        "source_content_read": False,
        "source_content_semantically_read": False,
        "target_csv_opened": False,
        "csv_header_read": False,
        "csv_values_read": False,
        "csv_full_content_read": False,
        "source_hash_recomputed": source_hash_recomputed,
        "computed_source_hash_preview": computed_source_hash_preview,
        "computed_source_hash_full": computed_source_hash_full,
        "computed_source_hash_full_recorded_in_metadata": computed_source_hash_full_recorded_in_metadata,
        "declared_source_hash_present": declared_source_hash_present,
        "declared_source_hash_preview": declared_source_hash_preview,
        "source_artifact_byte_identity_matched": source_artifact_byte_identity_matched,
        "source_artifact_byte_identity_mismatch": source_artifact_byte_identity_mismatch,
        "source_artifact_byte_identity_actionable_mismatch": source_artifact_byte_identity_actionable_mismatch,
        "source_hash_validated": False,
        "revision_id_validated": False,
        "available_time_validated": False,
        "available_time_compared_to_decision_time": False,
        "pit_admissibility_validated": False,
        "source_reliability_scored": False,
        "reviewer_authority_validated": False,
        "local_file_hash_recomputed": False,
        "expected_hash_reverified": False,
        "max_manifest_size_bytes": max_manifest_size_bytes,
        "max_source_artifact_size_bytes": max_source_artifact_size_bytes,
        "issue_count": issue_count,
        "warning_count": warning_count,
        "recommended_next_task": NEXT_TASK,
        "artifact_paths": artifact_paths,
        "issues": issues or [],
        "limitations": limitations or [],
    }
    result.update(source_artifact_byte_hash_safety_flags())
    return result


def _artifact_paths(root: Path) -> dict[str, Path]:
    return {name: root / filename for name, filename in ARTIFACT_FILENAMES.items()}


def _write_artifacts(result: dict[str, Any]) -> None:
    for path in result["artifact_paths"].values():
        path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(result["artifact_paths"]["metadata"], _metadata_payload(result))
    _write_json(result["artifact_paths"]["forbidden_downstream_flags"], source_artifact_byte_hash_safety_flags())
    _write_csv(result["artifact_paths"]["issues"], result["issues"] or [_empty_issue_row()])
    _write_csv(result["artifact_paths"]["summary"], [_summary_row(result)])
    _write_text(result["artifact_paths"]["limitations"], _limitations_text(result))
    _write_text(result["artifact_paths"]["report"], _report_text(result))


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
        "source_id",
        "source_artifact_id",
        "source_artifact_name_preview",
        "source_artifact_path_preview",
        "source_artifact_file_size_bytes",
        "source_hash_algorithm",
        "source_artifact_byte_read_level",
        "source_hash_recompute_level",
        "source_content_read_level",
        "csv_read_level",
        "computed_source_hash_preview",
        "declared_source_hash_preview",
        "source_artifact_byte_identity_matched",
        "source_artifact_byte_identity_mismatch",
        "source_artifact_byte_identity_actionable_mismatch",
        "source_hash_validated",
        "pit_admissibility_validated",
        "reviewer_authority_validated",
        "real_package_candidate_created",
        "active_replay_input",
        "buy_review_allowed",
        "trading_allowed",
        "data_raw_written",
        "data_processed_written",
        "data_cache_written",
        "issue_count",
        "warning_count",
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
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write(text)


def _limitations_text(result: dict[str, Any]) -> str:
    lines = ["# Limitations", ""]
    lines.extend(f"- {_safe_message(item)}" for item in result["limitations"])
    lines.extend(
        [
            "- Source artifact byte hashing is byte identity context only.",
            "- No source content, target CSV, PIT admissibility, package readiness, replay, buy-review, or trading behavior is created.",
            "",
        ]
    )
    return "\n".join(lines)


def _report_text(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Source Artifact Byte-Hash Report",
            "",
            f"- Runtime status: `{result['runtime_status']}`",
            f"- Health status: `{result['health_status']}`",
            f"- Source artifact id: `{result['source_artifact_id']}`",
            f"- Source artifact name preview: `{result['source_artifact_name_preview']}`",
            f"- Source artifact path preview: `{result['source_artifact_path_preview']}`",
            f"- Source artifact file size bytes: `{result['source_artifact_file_size_bytes']}`",
            f"- Source hash algorithm: `{result['source_hash_algorithm']}`",
            f"- Source artifact byte read level: `{result['source_artifact_byte_read_level']}`",
            f"- Source hash recompute level: `{result['source_hash_recompute_level']}`",
            f"- CSV read level: `{result['csv_read_level']}`",
            f"- Computed source hash preview: `{result['computed_source_hash_preview']}`",
            f"- Declared source hash preview: `{result['declared_source_hash_preview']}`",
            f"- Byte identity matched: `{str(result['source_artifact_byte_identity_matched']).lower()}`",
            f"- Byte identity mismatch: `{str(result['source_artifact_byte_identity_mismatch']).lower()}`",
            "- Source content read: `false`",
            "- Target CSV opened: `false`",
            "- Source hash validated: `false`",
            "- PIT admissibility validated: `false`",
            "- Real package candidate created: `false`",
            "- Active replay input: `false`",
            "- Buy review allowed: `false`",
            "- Trading allowed: `false`",
            f"- Recommended next task: `{result['recommended_next_task']}`",
            "",
        ]
    )


def _path_preview(path: str | Path) -> str:
    return Path(path).name[:80]


def _safe_name(value: Any) -> str:
    return _safe_message(str(value or ""))[:80]


def _safe_message(value: Any) -> str:
    text = str(value or "")
    for phrase in FORBIDDEN_LIVE_POSITIVE_STATUSES:
        text = text.replace(phrase, "[blocked wording]")
    return text.replace("\n", " ")[:240]


def _is_sha256_hex(value: str) -> bool:
    if len(value) != 64:
        return False
    return all(char in "0123456789abcdefABCDEF" for char in value)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
