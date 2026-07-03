"""Source hash / revision / available-time metadata boundary for Tiny PIT.

This module is report-only and diagnostic-only. It checks metadata presence,
shape, parseability, disclosure, and semantic separation for future reviewed
LOCAL_CSV package candidate governance. It does not open source artifacts or
target CSVs, recompute hashes, compare available_time to replay decision time,
validate PIT admissibility, score source reliability, validate reviewer
authority, create package/replay inputs, or enable buy-review/trading.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence


STATUS_NO_INPUT = "NO_SOURCE_REVISION_TIME_INPUT"
STATUS_METADATA_PRESENT = "SOURCE_REVISION_TIME_METADATA_PRESENT_REPORT_ONLY"
STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG = "SOURCE_REVISION_TIME_BLOCKED_BY_MISSING_ALLOW_FLAG"
STATUS_BLOCKED_BY_MANIFEST_SCHEMA = "SOURCE_REVISION_TIME_BLOCKED_BY_MANIFEST_SCHEMA"
STATUS_BLOCKED_BY_PATH_GUARD = "SOURCE_REVISION_TIME_BLOCKED_BY_PATH_GUARD"
STATUS_BLOCKED_BY_UNSUPPORTED_HASH_ALGORITHM = (
    "SOURCE_REVISION_TIME_BLOCKED_BY_UNSUPPORTED_HASH_ALGORITHM"
)
STATUS_BLOCKED_BY_MALFORMED_SOURCE_HASH = (
    "SOURCE_REVISION_TIME_BLOCKED_BY_MALFORMED_SOURCE_HASH"
)
STATUS_BLOCKED_BY_MISSING_REVISION_ID = "SOURCE_REVISION_TIME_BLOCKED_BY_MISSING_REVISION_ID"
STATUS_BLOCKED_BY_MALFORMED_AVAILABLE_TIME = (
    "SOURCE_REVISION_TIME_BLOCKED_BY_MALFORMED_AVAILABLE_TIME"
)
STATUS_WARN_TIMEZONE_ASSUMPTION_REQUIRED = (
    "SOURCE_REVISION_TIME_WARN_TIMEZONE_ASSUMPTION_REQUIRED"
)
STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM = (
    "SOURCE_REVISION_TIME_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
)
STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA = (
    "SOURCE_REVISION_TIME_BLOCKED_BY_UNSAFE_REFERENCE_METADATA"
)

WORKFLOW_NAME = (
    "tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time"
)
WORKFLOW_STAGE = (
    "TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_"
    "SOURCE_HASH_REVISION_AVAILABLE_TIME_CORE_CREATED_REPORT_ONLY"
)
CREATED_AT = "2026-07-03T00:00:00Z"
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Hash Revision "
    "Available-Time Checkpoint Planning Report-Only v0.1"
)

SOURCE_HASH_VALIDATION_NONE = "SOURCE_HASH_VALIDATION_NONE"
REVISION_ID_VALIDATION_NONE = "REVISION_ID_VALIDATION_NONE"
AVAILABLE_TIME_VALIDATION_NONE = "AVAILABLE_TIME_VALIDATION_NONE"
PIT_ADMISSIBILITY_NONE = "PIT_ADMISSIBILITY_NONE"
SOURCE_HASH_METADATA_PRESENT_ONLY = "SOURCE_HASH_METADATA_PRESENT_ONLY"
REVISION_ID_METADATA_PRESENT_ONLY = "REVISION_ID_METADATA_PRESENT_ONLY"
AVAILABLE_TIME_METADATA_PRESENT_ONLY = "AVAILABLE_TIME_METADATA_PRESENT_ONLY"
SOURCE_REVISION_TIME_METADATA_PRESENT_ONLY = "SOURCE_REVISION_TIME_METADATA_PRESENT_ONLY"
HASH_ALGORITHM = "SHA-256"
SOURCE_HASH_PREVIEW_HEX_CHARS = 16
MAX_MANIFEST_SIZE_BYTES = 1_048_576

ARTIFACT_FILENAMES = {
    "metadata": "metadata.json",
    "report": "source_revision_time_report.md",
    "limitations": "limitations.md",
    "issues": "issues.csv",
    "summary": "source_revision_time_summary.csv",
    "forbidden_downstream_flags": "forbidden_downstream_flags.json",
}

REQUIRED_MANIFEST_FIELDS = [
    "package_id",
    "package_schema_version",
    "created_at",
    "prepared_by",
    "report_only",
    "diagnostic_only",
    "requested_source_hash_validation_level",
    "requested_revision_id_validation_level",
    "requested_available_time_validation_level",
    "requested_pit_admissibility_level",
    "source_lineage_metadata_reference",
    "source_hash_policy",
    "revision_id_policy",
    "available_time_policy",
    "timezone_policy",
    "forbidden_downstream_flags",
    "limitations",
]
REQUIRED_REFERENCE_FIELDS = [
    "path",
    "required",
    "reference_type",
    "intended_touch_level",
    "declared_only",
]
REQUIRED_SOURCE_METADATA_FIELDS = [
    "source_id",
    "source_name",
    "source_type",
    "permission_class",
    "source_hash_algorithm",
    "source_hash_value",
    "source_hash_disclosure_level",
    "revision_id",
    "revision_id_type",
    "available_time",
    "available_time_timezone",
    "available_time_policy",
    "quality_status",
    "manual_review_status",
    "report_only",
    "diagnostic_only",
    "forbidden_downstream_flags",
    "limitations",
]
ALLOWED_REVISION_ID_TYPES = {
    "provider_revision_id",
    "document_version",
    "source_release_id",
    "manual_review_revision_id",
    "local_metadata_revision_id",
}
FORBIDDEN_REVISION_ID_TYPES = {
    "filename_as_revision",
    "file_path_as_revision",
}
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
UNSAFE_REFERENCE_TRUE_FIELDS = [
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "source_reliability_scored",
    "reviewer_authority_validated",
    "source_hash_recomputed",
    "source_artifact_opened",
    "source_content_read",
    "local_file_hash_recomputed",
    "expected_hash_reverified",
    "target_csv_opened",
    "real_csv_consumed",
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


def source_hash_revision_available_time_statuses() -> list[str]:
    return [
        STATUS_NO_INPUT,
        STATUS_METADATA_PRESENT,
        STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
        STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
        STATUS_BLOCKED_BY_PATH_GUARD,
        STATUS_BLOCKED_BY_UNSUPPORTED_HASH_ALGORITHM,
        STATUS_BLOCKED_BY_MALFORMED_SOURCE_HASH,
        STATUS_BLOCKED_BY_MISSING_REVISION_ID,
        STATUS_BLOCKED_BY_MALFORMED_AVAILABLE_TIME,
        STATUS_WARN_TIMEZONE_ASSUMPTION_REQUIRED,
        STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
        STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA,
    ]


def source_hash_revision_available_time_safety_flags() -> dict[str, bool]:
    return {field: False for field in REQUIRED_FALSE_FLAGS}


def run_source_hash_revision_available_time(
    *,
    output_root: str | Path,
    run_id: str | None = None,
    source_lineage_manifest_path: str | Path | None = None,
    source_lineage_metadata_path: str | Path | None = None,
    local_file_byte_hash_metadata_path: str | Path | None = None,
    expected_hash_verification_metadata_path: str | Path | None = None,
    physical_data_line_count_metadata_path: str | Path | None = None,
    allowed_manifest_roots: Sequence[str | Path] | None = None,
    source_hash_validation_level: str = SOURCE_HASH_VALIDATION_NONE,
    revision_id_validation_level: str = REVISION_ID_VALIDATION_NONE,
    available_time_validation_level: str = AVAILABLE_TIME_VALIDATION_NONE,
    pit_admissibility_level: str = PIT_ADMISSIBILITY_NONE,
    allow_source_revision_time_metadata: bool = False,
    max_manifest_size_bytes: int = MAX_MANIFEST_SIZE_BYTES,
) -> dict[str, Any]:
    del local_file_byte_hash_metadata_path
    del expected_hash_verification_metadata_path
    del physical_data_line_count_metadata_path

    artifact_root = _validated_output_root(Path(output_root)) / (run_id or uuid.uuid4().hex[:12])
    artifact_paths = _artifact_paths(artifact_root)
    max_bytes = int(max_manifest_size_bytes)

    if source_lineage_manifest_path is None:
        result = _result_payload(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_NO_INPUT,
            health_status="PASS",
            source_hash_validation_level=SOURCE_HASH_VALIDATION_NONE,
            revision_id_validation_level=REVISION_ID_VALIDATION_NONE,
            available_time_validation_level=AVAILABLE_TIME_VALIDATION_NONE,
            pit_admissibility_level=PIT_ADMISSIBILITY_NONE,
            issues=[],
            limitations=["No input supplied; no source/revision/time metadata checked."],
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    if (
        source_hash_validation_level,
        revision_id_validation_level,
        available_time_validation_level,
        pit_admissibility_level,
    ) != (
        SOURCE_HASH_METADATA_PRESENT_ONLY,
        REVISION_ID_METADATA_PRESENT_ONLY,
        AVAILABLE_TIME_METADATA_PRESENT_ONLY,
        PIT_ADMISSIBILITY_NONE,
    ):
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            reason="Only metadata-present source/revision/time levels are supported in v0.1.",
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    if not allow_source_revision_time_metadata:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
            reason="allow_source_revision_time_metadata must be true for metadata-present checks.",
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    if source_lineage_metadata_path is None:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            reason="source_lineage_metadata_path is required when a manifest is supplied.",
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    manifest_check = _check_input_path(source_lineage_manifest_path, allowed_manifest_roots)
    metadata_check = _check_input_path(source_lineage_metadata_path, allowed_manifest_roots)
    if manifest_check["blocked"] or metadata_check["blocked"]:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_PATH_GUARD,
            reason=str(manifest_check.get("reason") or metadata_check.get("reason")),
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    manifest_path = Path(manifest_check["path"])
    metadata_path = Path(metadata_check["path"])
    manifest, manifest_error = _read_json_object(manifest_path, max_bytes)
    if manifest_error is not None:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            reason=manifest_error,
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    manifest_issue = _validate_manifest(manifest, metadata_path)
    if manifest_issue is not None:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            reason=manifest_issue,
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    metadata, metadata_error = _read_json_object(metadata_path, max_bytes)
    if metadata_error is not None:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            reason=metadata_error,
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    metadata_issue = _validate_source_metadata_schema(metadata)
    if metadata_issue is not None:
        if metadata_issue == "missing_source_hash_value":
            runtime_status = STATUS_BLOCKED_BY_MALFORMED_SOURCE_HASH
        elif metadata_issue == "missing_revision_id":
            runtime_status = STATUS_BLOCKED_BY_MISSING_REVISION_ID
        elif metadata_issue == "unsafe_metadata":
            runtime_status = STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA
        else:
            runtime_status = STATUS_BLOCKED_BY_MANIFEST_SCHEMA
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=runtime_status,
            reason=metadata_issue,
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    if _has_forbidden_downstream(manifest) or _has_forbidden_downstream(metadata):
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
            reason="forbidden_downstream_flags must remain false.",
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    if _has_unsafe_claim(metadata):
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA,
            reason="Source metadata must not claim validation or downstream side effects.",
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    source_id = str(metadata.get("source_id") or "")
    source_name = str(metadata.get("source_name") or "")
    if _looks_secret_like(source_id) or _looks_secret_like(source_name):
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA,
            reason="source_id and source_name must not contain path/secret-like tokens.",
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    source_hash_algorithm = str(metadata.get("source_hash_algorithm") or "")
    if source_hash_algorithm.upper() != HASH_ALGORITHM:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_UNSUPPORTED_HASH_ALGORITHM,
            reason="Only SHA-256 source hash metadata is supported in v0.1.",
            max_manifest_size_bytes=max_bytes,
            source_hash_algorithm=source_hash_algorithm,
        )
        _write_artifacts(result)
        return result

    source_hash_value = str(metadata.get("source_hash_value") or "")
    if not _is_sha256_hex(source_hash_value):
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MALFORMED_SOURCE_HASH,
            reason="source_hash_value must be exactly 64 hex characters.",
            max_manifest_size_bytes=max_bytes,
            source_hash_algorithm=source_hash_algorithm,
        )
        _write_artifacts(result)
        return result

    revision_id = str(metadata.get("revision_id") or "")
    revision_id_type = str(metadata.get("revision_id_type") or "")
    if (
        not revision_id
        or revision_id_type in FORBIDDEN_REVISION_ID_TYPES
        or revision_id_type not in ALLOWED_REVISION_ID_TYPES
        or _looks_path_like(revision_id)
        or _looks_secret_like(revision_id)
    ):
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MISSING_REVISION_ID,
            reason="revision_id and revision_id_type must be safe supported metadata values.",
            max_manifest_size_bytes=max_bytes,
            revision_id_type=revision_id_type,
        )
        _write_artifacts(result)
        return result

    available_time = str(metadata.get("available_time") or "")
    parsed_time = _parse_iso_datetime(available_time)
    if parsed_time is None:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MALFORMED_AVAILABLE_TIME,
            reason="available_time must be parseable ISO 8601 metadata.",
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    timezone_present = parsed_time.tzinfo is not None and bool(metadata.get("available_time_timezone"))
    health_status = "PASS" if timezone_present else "WARN"
    runtime_status = (
        STATUS_METADATA_PRESENT if timezone_present else STATUS_WARN_TIMEZONE_ASSUMPTION_REQUIRED
    )
    issues = []
    warnings = []
    if not timezone_present:
        warnings.append("available_time timezone assumption requires review.")

    result = _result_payload(
        artifact_paths=artifact_paths,
        run_id=artifact_root.name,
        runtime_status=runtime_status,
        health_status=health_status,
        source_hash_validation_level=SOURCE_HASH_METADATA_PRESENT_ONLY,
        revision_id_validation_level=REVISION_ID_METADATA_PRESENT_ONLY,
        available_time_validation_level=AVAILABLE_TIME_METADATA_PRESENT_ONLY,
        pit_admissibility_level=PIT_ADMISSIBILITY_NONE,
        source_hash_metadata_present=True,
        source_hash_format_checked=True,
        source_hash_algorithm_supported=True,
        source_hash_algorithm=HASH_ALGORITHM,
        source_hash_preview=source_hash_value[:SOURCE_HASH_PREVIEW_HEX_CHARS].lower(),
        revision_id_metadata_present=True,
        revision_id_type=revision_id_type,
        revision_id_type_supported=True,
        revision_id_value_recorded=True,
        available_time_metadata_present=True,
        available_time_parseable=True,
        available_time_timezone_present=timezone_present,
        available_time_timezone_policy=str(metadata.get("available_time_timezone") or ""),
        issues=issues,
        warnings=warnings,
        limitations=list(metadata.get("limitations") or manifest.get("limitations") or []),
        max_manifest_size_bytes=max_bytes,
    )
    _write_artifacts(result)
    return result


def _result_payload(
    *,
    artifact_paths: dict[str, Path],
    run_id: str,
    runtime_status: str,
    health_status: str,
    source_hash_validation_level: str,
    revision_id_validation_level: str,
    available_time_validation_level: str,
    pit_admissibility_level: str,
    issues: list[str],
    limitations: list[str],
    max_manifest_size_bytes: int,
    warnings: list[str] | None = None,
    source_hash_metadata_present: bool = False,
    source_hash_format_checked: bool = False,
    source_hash_algorithm_supported: bool = False,
    source_hash_algorithm: str = "",
    source_hash_preview: str = "",
    revision_id_metadata_present: bool = False,
    revision_id_type: str = "",
    revision_id_type_supported: bool = False,
    revision_id_value_recorded: bool = False,
    available_time_metadata_present: bool = False,
    available_time_parseable: bool = False,
    available_time_timezone_present: bool = False,
    available_time_timezone_policy: str = "",
) -> dict[str, Any]:
    issue_list = list(issues)
    warning_list = list(warnings or [])
    result: dict[str, Any] = {
        "run_id": run_id,
        "runtime_status": runtime_status,
        "health_status": health_status,
        "workflow_name": WORKFLOW_NAME,
        "workflow_stage": WORKFLOW_STAGE,
        "created_at": CREATED_AT,
        "artifact_root": str(artifact_paths["root"]),
        "artifact_paths": {name: str(path) for name, path in artifact_paths.items() if name != "root"},
        "report_path": str(artifact_paths["report"]),
        "report_only": True,
        "diagnostic_only": True,
        "source_hash_validation_level": source_hash_validation_level,
        "revision_id_validation_level": revision_id_validation_level,
        "available_time_validation_level": available_time_validation_level,
        "pit_admissibility_level": pit_admissibility_level,
        "source_hash_metadata_present": source_hash_metadata_present,
        "source_hash_format_checked": source_hash_format_checked,
        "source_hash_algorithm_supported": source_hash_algorithm_supported,
        "source_hash_algorithm": source_hash_algorithm,
        "source_hash_preview": source_hash_preview,
        "source_hash_recomputed": False,
        "source_artifact_opened": False,
        "source_content_read": False,
        "revision_id_metadata_present": revision_id_metadata_present,
        "revision_id_type": revision_id_type,
        "revision_id_type_supported": revision_id_type_supported,
        "revision_id_value_recorded": revision_id_value_recorded,
        "revision_consistency_checked": False,
        "available_time_metadata_present": available_time_metadata_present,
        "available_time_parseable": available_time_parseable,
        "available_time_timezone_present": available_time_timezone_present,
        "available_time_timezone_policy": available_time_timezone_policy,
        "available_time_compared_to_decision_time": False,
        "target_csv_opened": False,
        "real_csv_consumed": False,
        "local_file_hash_recomputed": False,
        "expected_hash_reverified": False,
        "source_hash_validated": False,
        "revision_id_validated": False,
        "available_time_validated": False,
        "pit_admissibility_validated": False,
        "source_reliability_scored": False,
        "reviewer_authority_validated": False,
        "issue_count": len(issue_list),
        "warning_count": len(warning_list),
        "issues": issue_list,
        "warnings": warning_list,
        "limitations": limitations,
        "max_manifest_size_bytes": max_manifest_size_bytes,
        "recommended_next_task": NEXT_TASK,
    }
    result.update(source_hash_revision_available_time_safety_flags())
    return result


def _blocked_result(
    *,
    artifact_paths: dict[str, Path],
    run_id: str,
    runtime_status: str,
    reason: str,
    max_manifest_size_bytes: int,
    source_hash_algorithm: str = "",
    revision_id_type: str = "",
) -> dict[str, Any]:
    return _result_payload(
        artifact_paths=artifact_paths,
        run_id=run_id,
        runtime_status=runtime_status,
        health_status="FAIL",
        source_hash_validation_level=SOURCE_HASH_VALIDATION_NONE,
        revision_id_validation_level=REVISION_ID_VALIDATION_NONE,
        available_time_validation_level=AVAILABLE_TIME_VALIDATION_NONE,
        pit_admissibility_level=PIT_ADMISSIBILITY_NONE,
        source_hash_algorithm=source_hash_algorithm,
        revision_id_type=revision_id_type,
        issues=[reason],
        limitations=["Blocked before metadata could be accepted as report-only context."],
        max_manifest_size_bytes=max_manifest_size_bytes,
    )


def _artifact_paths(root: Path) -> dict[str, Path]:
    paths = {"root": root}
    paths.update({name: root / filename for name, filename in ARTIFACT_FILENAMES.items()})
    return paths


def _write_artifacts(result: dict[str, Any]) -> None:
    artifact_root = Path(result["artifact_root"])
    artifact_root.mkdir(parents=True, exist_ok=True)
    paths = {name: Path(path) for name, path in result["artifact_paths"].items()}
    safe_result = _serializable_result(result)
    _write_json(paths["metadata"], safe_result)
    _write_json(paths["forbidden_downstream_flags"], source_hash_revision_available_time_safety_flags())
    _write_summary(paths["summary"], result)
    _write_issues(paths["issues"], result)
    paths["limitations"].write_text("\n".join(result["limitations"]) + "\n", encoding="utf-8")
    paths["report"].write_text(_report_text(result), encoding="utf-8")


def _serializable_result(result: dict[str, Any]) -> dict[str, Any]:
    safe = dict(result)
    safe.pop("artifact_paths", None)
    safe["artifact_paths"] = dict(result["artifact_paths"])
    return safe


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_summary(path: Path, result: dict[str, Any]) -> None:
    fields = [
        "run_id",
        "runtime_status",
        "health_status",
        "workflow_stage",
        "source_hash_validation_level",
        "revision_id_validation_level",
        "available_time_validation_level",
        "pit_admissibility_level",
        "source_hash_metadata_present",
        "source_hash_algorithm",
        "source_hash_preview",
        "revision_id_metadata_present",
        "revision_id_type",
        "revision_id_value_recorded",
        "available_time_metadata_present",
        "available_time_parseable",
        "available_time_timezone_present",
        "available_time_compared_to_decision_time",
        "source_hash_validated",
        "revision_id_validated",
        "available_time_validated",
        "pit_admissibility_validated",
        "real_csv_consumed",
        "active_replay_input",
        "buy_review_allowed",
        "trading_allowed",
        "issue_count",
        "warning_count",
    ]
    rows = [",".join(fields), ",".join(_csv_value(result.get(field, "")) for field in fields)]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def _write_issues(path: Path, result: dict[str, Any]) -> None:
    rows = ["severity,message"]
    rows.extend(f"ISSUE,{_csv_value(issue)}" for issue in result["issues"])
    rows.extend(f"WARNING,{_csv_value(warning)}" for warning in result["warnings"])
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def _report_text(result: dict[str, Any]) -> str:
    lines = [
        "# Tiny PIT Source Hash Revision Available-Time Metadata Boundary",
        "",
        "This report is diagnostic-only and report-only.",
        "",
        f"- Runtime status: `{result['runtime_status']}`",
        f"- Health status: `{result['health_status']}`",
        f"- Source hash validation level: `{result['source_hash_validation_level']}`",
        f"- Revision id validation level: `{result['revision_id_validation_level']}`",
        f"- Available-time validation level: `{result['available_time_validation_level']}`",
        f"- PIT admissibility level: `{result['pit_admissibility_level']}`",
        f"- Source hash preview: `{result['source_hash_preview']}`",
        f"- Revision id type: `{result['revision_id_type']}`",
        f"- Available-time parseable: `{str(result['available_time_parseable']).lower()}`",
        f"- Available time compared to decision time: `{str(result['available_time_compared_to_decision_time']).lower()}`",
        f"- Source hash recomputed: `{str(result['source_hash_recomputed']).lower()}`",
        f"- Source artifact opened: `{str(result['source_artifact_opened']).lower()}`",
        f"- Target CSV opened: `{str(result['target_csv_opened']).lower()}`",
        f"- Real CSV consumed: `{str(result['real_csv_consumed']).lower()}`",
        f"- Source hash validated: `{str(result['source_hash_validated']).lower()}`",
        f"- Revision id validated: `{str(result['revision_id_validated']).lower()}`",
        f"- Available time validated: `{str(result['available_time_validated']).lower()}`",
        f"- PIT admissibility validated: `{str(result['pit_admissibility_validated']).lower()}`",
        f"- Recommended next task: {result['recommended_next_task']}",
    ]
    return "\n".join(lines) + "\n"


def _csv_value(value: Any) -> str:
    text = str(value).replace('"', '""')
    if any(char in text for char in [",", "\n", '"']):
        return f'"{text}"'
    return text


def _validated_output_root(output_root: Path) -> Path:
    if _is_protected_or_secret_path(output_root):
        raise ValueError("output_root must not target protected data/source paths.")
    return output_root


def _check_input_path(path: str | Path, allowed_roots: Sequence[str | Path] | None) -> dict[str, Any]:
    raw = str(path)
    if raw.lower().startswith(NETWORK_PREFIXES):
        return {"blocked": True, "reason": "Network/URL paths are not allowed."}
    candidate = Path(path)
    if _is_protected_or_secret_path(candidate):
        return {"blocked": True, "reason": "Path contains protected or secret-like segments."}
    if ".." in candidate.parts:
        return {"blocked": True, "reason": "Path traversal is not allowed."}
    resolved = candidate.resolve()
    roots = [Path(root).resolve() for root in (allowed_roots or [])]
    if roots and not any(_is_relative_to(resolved, root) for root in roots):
        return {"blocked": True, "reason": "Path is outside allowed manifest roots."}
    return {"blocked": False, "path": resolved}


def _read_json_object(path: Path, max_bytes: int) -> tuple[dict[str, Any], str | None]:
    if not path.is_file():
        return {}, f"{path.name} is missing."
    if path.stat().st_size > max_bytes:
        return {}, f"{path.name} exceeds max_manifest_size_bytes."
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"JSON metadata could not be read: {exc}"
    if not isinstance(payload, dict):
        return {}, "JSON payload must be an object."
    return payload, None


def _validate_manifest(manifest: dict[str, Any], metadata_path: Path) -> str | None:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    if missing:
        return f"Missing manifest fields: {', '.join(missing)}"
    if manifest.get("report_only") is not True or manifest.get("diagnostic_only") is not True:
        return "Manifest must be report_only and diagnostic_only."
    if manifest.get("requested_source_hash_validation_level") != SOURCE_HASH_METADATA_PRESENT_ONLY:
        return "requested_source_hash_validation_level must be SOURCE_HASH_METADATA_PRESENT_ONLY."
    if manifest.get("requested_revision_id_validation_level") != REVISION_ID_METADATA_PRESENT_ONLY:
        return "requested_revision_id_validation_level must be REVISION_ID_METADATA_PRESENT_ONLY."
    if manifest.get("requested_available_time_validation_level") != AVAILABLE_TIME_METADATA_PRESENT_ONLY:
        return "requested_available_time_validation_level must be AVAILABLE_TIME_METADATA_PRESENT_ONLY."
    if manifest.get("requested_pit_admissibility_level") != PIT_ADMISSIBILITY_NONE:
        return "requested_pit_admissibility_level must be PIT_ADMISSIBILITY_NONE."
    reference = manifest.get("source_lineage_metadata_reference")
    if not isinstance(reference, dict):
        return "source_lineage_metadata_reference must be an object."
    missing_ref = [field for field in REQUIRED_REFERENCE_FIELDS if field not in reference]
    if missing_ref:
        return f"Missing source_lineage_metadata_reference fields: {', '.join(missing_ref)}"
    if reference.get("required") is not True:
        return "source_lineage_metadata_reference.required must be true."
    if reference.get("reference_type") != "source_lineage_metadata_ref":
        return "source_lineage_metadata_reference.reference_type is unsupported."
    if reference.get("intended_touch_level") != SOURCE_REVISION_TIME_METADATA_PRESENT_ONLY:
        return "source_lineage_metadata_reference.intended_touch_level is unsupported."
    if reference.get("declared_only") is not False:
        return "source_lineage_metadata_reference.declared_only must be false."
    if Path(str(reference.get("path") or "")).resolve() != metadata_path.resolve():
        return "source_lineage_metadata_reference.path must match source_lineage_metadata_path."
    if not isinstance(manifest.get("limitations"), list) or not manifest["limitations"]:
        return "limitations must be a non-empty list."
    return None


def _validate_source_metadata_schema(metadata: dict[str, Any]) -> str | None:
    missing = [field for field in REQUIRED_SOURCE_METADATA_FIELDS if field not in metadata]
    if missing:
        if "source_hash_value" in missing:
            return "missing_source_hash_value"
        if "revision_id" in missing:
            return "missing_revision_id"
        return f"Missing source metadata fields: {', '.join(missing)}"
    if metadata.get("report_only") is not True or metadata.get("diagnostic_only") is not True:
        return "Source metadata must be report_only and diagnostic_only."
    if not isinstance(metadata.get("limitations"), list) or not metadata["limitations"]:
        return "Source metadata limitations must be a non-empty list."
    if any(_looks_secret_like(str(metadata.get(field) or "")) for field in ["source_id", "source_name"]):
        return "unsafe_metadata"
    return None


def _has_forbidden_downstream(payload: dict[str, Any]) -> bool:
    flags = payload.get("forbidden_downstream_flags")
    if not isinstance(flags, dict):
        return True
    return any(bool(flags.get(field)) for field in REQUIRED_FALSE_FLAGS)


def _has_unsafe_claim(payload: dict[str, Any]) -> bool:
    return any(bool(payload.get(field)) for field in UNSAFE_REFERENCE_TRUE_FIELDS)


def _is_sha256_hex(value: str) -> bool:
    if len(value) != 64:
        return False
    return all(char in "0123456789abcdefABCDEF" for char in value)


def _parse_iso_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_protected_or_secret_path(path: Path) -> bool:
    parts = tuple(part.lower() for part in path.parts)
    if any(part.startswith(".env") for part in parts):
        return True
    if any(token in parts for token in FORBIDDEN_PATH_TOKENS):
        return True
    return any(_contains_pair(parts, pair) for pair in PROTECTED_PATH_PAIRS)


def _looks_path_like(value: str) -> bool:
    return "/" in value or "\\" in value or ":" in value


def _looks_secret_like(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered.split("/") for token in FORBIDDEN_PATH_TOKENS) or any(
        token in lowered.split("\\") for token in FORBIDDEN_PATH_TOKENS
    )


def _contains_pair(parts: tuple[str, ...], pair: tuple[str, str]) -> bool:
    return any(parts[index : index + 2] == pair for index in range(max(len(parts) - 1, 0)))


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
