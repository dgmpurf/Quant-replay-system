"""CSV physical data-line count-only core for Tiny PIT LOCAL_CSV candidates.

This module is report-only and diagnostic-only. It counts newline-delimited
physical non-header lines in a manifest-referenced local CSV under explicit
allowed roots and an explicit allow flag. It does not parse CSV fields, support
semantic quoted-multiline record counting, store line values, recompute file
fingerprints, validate source/revision/PIT/reviewer semantics, create replay
inputs, or enable buy-review/trading behavior.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Sequence


STATUS_NO_INPUT = "NO_CSV_PHYSICAL_DATA_LINE_COUNT_INPUT"
STATUS_COUNT_ONLY_REPORT_ONLY = "CSV_PHYSICAL_DATA_LINE_COUNT_ONLY_REPORT_ONLY"
STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG = "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_MISSING_ALLOW_FLAG"
STATUS_BLOCKED_BY_MANIFEST_SCHEMA = "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_MANIFEST_SCHEMA"
STATUS_BLOCKED_BY_PATH_GUARD = "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_PATH_GUARD"
STATUS_BLOCKED_BY_UNSUPPORTED_LEVEL = "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_UNSUPPORTED_LEVEL"
STATUS_BLOCKED_BY_HEADER_POLICY = "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_HEADER_POLICY"
STATUS_BLOCKED_BY_SIZE_LIMIT = "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_SIZE_LIMIT"
STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM = "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
STATUS_BLOCKED_BY_UNSUPPORTED_FILE_TYPE = "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_UNSUPPORTED_FILE_TYPE"
STATUS_WARN_ZERO_DATA_LINES = "CSV_PHYSICAL_DATA_LINE_COUNT_WARN_ZERO_DATA_LINES"

WORKFLOW_NAME = (
    "tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only"
)
WORKFLOW_STAGE = (
    "TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_"
    "CSV_PHYSICAL_DATA_LINE_COUNT_ONLY_CORE_CREATED_REPORT_ONLY"
)
CREATED_AT = "2026-07-02T00:00:00Z"
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Physical Data-Line "
    "Count-Only Artifact Views Report-Only v0.1"
)

FILE_TOUCH_NONE = "FILE_TOUCH_NONE"
CSV_READ_NONE = "CSV_READ_NONE"
LOCAL_FILE_HASH_NONE = "LOCAL_FILE_HASH_NONE"
EXPECTED_HASH_VERIFICATION_NONE = "EXPECTED_HASH_VERIFICATION_NONE"
CSV_PHYSICAL_DATA_LINE_COUNT_NONE = "CSV_PHYSICAL_DATA_LINE_COUNT_NONE"
CSV_PHYSICAL_DATA_LINE_COUNT_ONLY = "CSV_PHYSICAL_DATA_LINE_COUNT_ONLY"
PHYSICAL_NON_HEADER_LINE_COUNT = "PHYSICAL_NON_HEADER_LINE_COUNT"
CSV_HEADER_DEPENDENCY_POLICY = "REQUIRE_PRIOR_HEADER_ONLY_METADATA"
MAX_COUNT_INPUT_BYTES = 1_048_576

ARTIFACT_FILENAMES = {
    "metadata": "metadata.json",
    "report": "csv_physical_data_line_count_only_report.md",
    "limitations": "limitations.md",
    "issues": "issues.csv",
    "summary": "csv_physical_data_line_count_summary.csv",
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
    "requested_csv_physical_data_line_count_level",
    "requested_local_file_hash_level",
    "requested_expected_hash_verification_level",
    "csv_file_references",
    "header_metadata_reference",
    "row_count_policy",
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
    "notes",
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
HEADER_POLICY_TRUE_FIELDS = [
    "csv_row_count_computed",
    "csv_values_read",
    "csv_full_content_read",
    "real_csv_consumed",
    "local_file_byte_hash_computed",
    "expected_hash_verification_performed",
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


def csv_physical_data_line_count_statuses() -> list[str]:
    return [
        STATUS_NO_INPUT,
        STATUS_COUNT_ONLY_REPORT_ONLY,
        STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
        STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
        STATUS_BLOCKED_BY_PATH_GUARD,
        STATUS_BLOCKED_BY_UNSUPPORTED_LEVEL,
        STATUS_BLOCKED_BY_HEADER_POLICY,
        STATUS_BLOCKED_BY_SIZE_LIMIT,
        STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
        STATUS_BLOCKED_BY_UNSUPPORTED_FILE_TYPE,
        STATUS_WARN_ZERO_DATA_LINES,
    ]


def csv_physical_data_line_count_safety_flags() -> dict[str, bool]:
    return {field: False for field in REQUIRED_FALSE_FLAGS}


def run_csv_physical_data_line_count_only(
    *,
    output_root: str | Path,
    run_id: str | None = None,
    package_manifest_path: str | Path | None = None,
    header_metadata_path: str | Path | None = None,
    allowed_manifest_roots: Sequence[str | Path] | None = None,
    file_touch_level: str = FILE_TOUCH_NONE,
    csv_read_level: str = CSV_READ_NONE,
    csv_physical_data_line_count_level: str = CSV_PHYSICAL_DATA_LINE_COUNT_NONE,
    allow_csv_physical_data_line_count_only: bool = False,
    max_count_input_bytes: int = MAX_COUNT_INPUT_BYTES,
) -> dict[str, Any]:
    artifact_root = _validated_output_root(Path(output_root)) / (run_id or uuid.uuid4().hex[:12])
    artifact_paths = _artifact_paths(artifact_root)
    max_bytes = int(max_count_input_bytes)

    if package_manifest_path is None:
        result = _result_payload(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_NO_INPUT,
            health_status="PASS",
            file_touch_level=FILE_TOUCH_NONE,
            csv_read_level=CSV_READ_NONE,
            csv_physical_data_line_count_level=CSV_PHYSICAL_DATA_LINE_COUNT_NONE,
            issues=[],
            limitations=["No input supplied; no CSV physical data-line count performed."],
            max_count_input_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    if (
        file_touch_level,
        csv_read_level,
        csv_physical_data_line_count_level,
    ) != (
        CSV_PHYSICAL_DATA_LINE_COUNT_ONLY,
        CSV_PHYSICAL_DATA_LINE_COUNT_ONLY,
        CSV_PHYSICAL_DATA_LINE_COUNT_ONLY,
    ):
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_UNSUPPORTED_LEVEL,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            csv_physical_data_line_count_level=csv_physical_data_line_count_level,
            reason="Only CSV_PHYSICAL_DATA_LINE_COUNT_ONLY levels are supported in this prototype.",
            max_count_input_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    if not allow_csv_physical_data_line_count_only:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            csv_physical_data_line_count_level=csv_physical_data_line_count_level,
            reason="allow_csv_physical_data_line_count_only must be true for physical data-line counting.",
            max_count_input_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    if header_metadata_path is None:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_HEADER_POLICY,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            csv_physical_data_line_count_level=csv_physical_data_line_count_level,
            reason="header_metadata_path is required when a package manifest is supplied.",
            max_count_input_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    roots = _resolved_allowed_roots(allowed_manifest_roots)
    manifest_path, manifest_error = _guard_existing_file(
        package_manifest_path, allowed_roots=roots, expected_suffix=".json"
    )
    if manifest_error:
        result = _path_guard_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            reason=manifest_error,
            max_count_input_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    header_path, header_error = _guard_existing_file(
        header_metadata_path, allowed_roots=roots, expected_suffix=".json"
    )
    if header_error:
        result = _path_guard_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            reason=header_error,
            max_count_input_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    manifest, manifest_error = _load_json_object(manifest_path)
    if manifest_error:
        result = _manifest_schema_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            reason=manifest_error,
            max_count_input_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    manifest_error = _validate_manifest_schema(manifest)
    if manifest_error:
        runtime_status = (
            STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM
            if manifest_error == "forbidden downstream flag true"
            else STATUS_BLOCKED_BY_MANIFEST_SCHEMA
        )
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=runtime_status,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            csv_physical_data_line_count_level=csv_physical_data_line_count_level,
            reason=manifest_error,
            max_count_input_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    header_reference = _resolve_manifest_reference(manifest["header_metadata_reference"], manifest_path)
    if header_reference.resolve() != header_path.resolve():
        result = _manifest_schema_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            reason="manifest header_metadata_reference must match header_metadata_path.",
            max_count_input_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    csv_reference = manifest["csv_file_references"][0]
    csv_path, csv_error_status, csv_error = _resolve_and_guard_csv_reference(
        csv_reference["path"], manifest_path=manifest_path, allowed_roots=roots
    )
    if csv_error_status:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=csv_error_status,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            csv_physical_data_line_count_level=csv_physical_data_line_count_level,
            reason=csv_error,
            max_count_input_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    header_metadata, header_error = _load_json_object(header_path)
    if header_error:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_HEADER_POLICY,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            csv_physical_data_line_count_level=csv_physical_data_line_count_level,
            reason=header_error,
            max_count_input_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    header_error = _validate_header_metadata(header_metadata, csv_path)
    if header_error:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_HEADER_POLICY,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            csv_physical_data_line_count_level=csv_physical_data_line_count_level,
            reason=header_error,
            max_count_input_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    try:
        input_size = csv_path.stat().st_size
    except OSError as exc:
        result = _path_guard_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            reason=f"target CSV stat failed: {exc}",
            max_count_input_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    if input_size > max_bytes:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_SIZE_LIMIT,
            file_touch_level=file_touch_level,
            csv_read_level=csv_read_level,
            csv_physical_data_line_count_level=csv_physical_data_line_count_level,
            reason="target CSV exceeds max_count_input_bytes before scan.",
            max_count_input_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    total_physical_lines = _count_physical_lines(csv_path)
    data_line_count = max(total_physical_lines - 1, 0)
    warning = data_line_count == 0
    result = _result_payload(
        artifact_paths=artifact_paths,
        run_id=artifact_root.name,
        runtime_status=STATUS_WARN_ZERO_DATA_LINES if warning else STATUS_COUNT_ONLY_REPORT_ONLY,
        health_status="WARN" if warning else "PASS",
        file_touch_level=file_touch_level,
        csv_read_level=csv_read_level,
        csv_physical_data_line_count_level=csv_physical_data_line_count_level,
        csv_physical_data_line_count_computed=True,
        csv_physical_data_line_count=data_line_count,
        csv_physical_line_count_total=total_physical_lines,
        csv_physical_data_line_count_policy=PHYSICAL_NON_HEADER_LINE_COUNT,
        csv_header_dependency_policy=CSV_HEADER_DEPENDENCY_POLICY,
        header_metadata_reused=True,
        csv_header_line_skipped_by_policy=total_physical_lines > 0,
        target_csv_opened_for_physical_data_line_count=True,
        issues=(
            [
                {
                    "severity": "WARN",
                    "status": STATUS_WARN_ZERO_DATA_LINES,
                    "message": "Physical data-line count is zero; review package completeness before any later workflow.",
                }
            ]
            if warning
            else []
        ),
        limitations=[
            "Counts physical non-header lines only.",
            "Quoted multiline CSV records are not handled as one semantic CSV record.",
            "No CSV values, row snippets, parsed fields, or full-content samples are stored.",
            "The count is not PIT admissibility, package readiness, replay input readiness, buy-review, or trading permission.",
        ],
        max_count_input_bytes=max_bytes,
    )
    _write_artifacts(result)
    return result


def _artifact_paths(artifact_root: Path) -> dict[str, str]:
    return {key: str(artifact_root / filename) for key, filename in ARTIFACT_FILENAMES.items()}


def _result_payload(
    *,
    artifact_paths: dict[str, str],
    run_id: str,
    runtime_status: str,
    health_status: str,
    file_touch_level: str,
    csv_read_level: str,
    csv_physical_data_line_count_level: str,
    issues: list[dict[str, str]],
    limitations: list[str],
    max_count_input_bytes: int,
    csv_physical_data_line_count_computed: bool = False,
    csv_physical_data_line_count: int | str = "",
    csv_physical_line_count_total: int | str = "",
    csv_physical_data_line_count_policy: str = "",
    csv_header_dependency_policy: str = "",
    header_metadata_reused: bool = False,
    csv_header_line_skipped_by_policy: bool = False,
    target_csv_opened_for_physical_data_line_count: bool = False,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "run_id": run_id,
        "workflow_name": WORKFLOW_NAME,
        "runtime_status": runtime_status,
        "health_status": health_status,
        "workflow_stage": WORKFLOW_STAGE,
        "created_at": CREATED_AT,
        "report_only": True,
        "diagnostic_only": True,
        "artifact_root": str(Path(artifact_paths["metadata"]).parent),
        "artifact_paths": artifact_paths,
        "file_touch_level": file_touch_level,
        "csv_read_level": csv_read_level,
        "local_file_hash_level": LOCAL_FILE_HASH_NONE,
        "expected_hash_verification_level": EXPECTED_HASH_VERIFICATION_NONE,
        "csv_physical_data_line_count_level": csv_physical_data_line_count_level,
        "csv_physical_data_line_count_computed": csv_physical_data_line_count_computed,
        "csv_physical_data_line_count": csv_physical_data_line_count,
        "csv_physical_data_line_count_policy": csv_physical_data_line_count_policy,
        "csv_physical_line_count_total": csv_physical_line_count_total,
        "csv_header_dependency_policy": csv_header_dependency_policy,
        "header_metadata_reused": header_metadata_reused,
        "csv_header_read": False,
        "csv_header_values_recorded": False,
        "csv_header_line_skipped_by_policy": csv_header_line_skipped_by_policy,
        "target_csv_opened_for_physical_data_line_count": target_csv_opened_for_physical_data_line_count,
        "csv_values_read": False,
        "csv_value_fields_parsed": False,
        "csv_row_values_stored": False,
        "csv_full_content_semantically_read": False,
        "csv_full_content_read": False,
        "real_csv_consumed": False,
        "local_file_byte_hash_computed": False,
        "local_file_byte_hash_recomputed": False,
        "expected_hash_verification_performed": False,
        "expected_hash_verified_against_local_metadata": False,
        "expected_hash_verified_against_source_hash": False,
        "source_hash_validated": False,
        "revision_id_validated": False,
        "available_time_validated": False,
        "pit_admissibility_validated": False,
        "source_reliability_scored": False,
        "reviewer_authority_validated": False,
        "max_count_input_bytes": max_count_input_bytes,
        "issue_count": len([issue for issue in issues if issue.get("severity") != "WARN"]),
        "warning_count": len([issue for issue in issues if issue.get("severity") == "WARN"]),
        "issues": issues,
        "limitations": limitations,
        "recommended_next_task": NEXT_TASK,
    }
    result.update(csv_physical_data_line_count_safety_flags())
    return result


def _blocked_result(
    *,
    artifact_paths: dict[str, str],
    run_id: str,
    runtime_status: str,
    file_touch_level: str = CSV_PHYSICAL_DATA_LINE_COUNT_ONLY,
    csv_read_level: str = CSV_PHYSICAL_DATA_LINE_COUNT_ONLY,
    csv_physical_data_line_count_level: str = CSV_PHYSICAL_DATA_LINE_COUNT_ONLY,
    reason: str,
    max_count_input_bytes: int,
) -> dict[str, Any]:
    return _result_payload(
        artifact_paths=artifact_paths,
        run_id=run_id,
        runtime_status=runtime_status,
        health_status="FAIL",
        file_touch_level=file_touch_level,
        csv_read_level=csv_read_level,
        csv_physical_data_line_count_level=csv_physical_data_line_count_level,
        issues=[{"severity": "FAIL", "status": runtime_status, "message": reason}],
        limitations=[
            "Blocked before physical data-line counting.",
            "No CSV values, row snippets, parsed fields, or full-content samples are stored.",
            "The result is not package readiness, PIT admissibility, replay readiness, buy-review, or trading permission.",
        ],
        max_count_input_bytes=max_count_input_bytes,
    )


def _path_guard_result(
    *,
    artifact_paths: dict[str, str],
    run_id: str,
    reason: str,
    max_count_input_bytes: int,
) -> dict[str, Any]:
    return _blocked_result(
        artifact_paths=artifact_paths,
        run_id=run_id,
        runtime_status=STATUS_BLOCKED_BY_PATH_GUARD,
        reason=reason,
        max_count_input_bytes=max_count_input_bytes,
    )


def _manifest_schema_result(
    *,
    artifact_paths: dict[str, str],
    run_id: str,
    reason: str,
    max_count_input_bytes: int,
) -> dict[str, Any]:
    return _blocked_result(
        artifact_paths=artifact_paths,
        run_id=run_id,
        runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
        reason=reason,
        max_count_input_bytes=max_count_input_bytes,
    )


def _validated_output_root(output_root: Path) -> Path:
    if _has_blocked_path_text(str(output_root)) or _has_protected_pair(output_root.parts):
        raise ValueError("output_root points to a protected or secret-like path")
    return output_root


def _resolved_allowed_roots(allowed_roots: Sequence[str | Path] | None) -> list[Path]:
    if not allowed_roots:
        return []
    return [Path(root).resolve() for root in allowed_roots]


def _guard_existing_file(
    path_value: str | Path,
    *,
    allowed_roots: Sequence[Path],
    expected_suffix: str | None = None,
) -> tuple[Path, str | None]:
    text = str(path_value)
    if _has_blocked_path_text(text):
        return Path(text), "path contains a network, hidden, secret-like, or protected token."
    path = Path(path_value)
    if expected_suffix and path.suffix.lower() != expected_suffix:
        return path, f"path must end with {expected_suffix}."
    if _has_protected_pair(path.parts):
        return path, "path points to protected data/project-source storage."
    if not allowed_roots:
        return path, "explicit allowed_manifest_roots are required."
    try:
        resolved = path.resolve(strict=False)
    except OSError as exc:
        return path, f"path resolution failed: {exc}"
    if not any(_is_relative_to(resolved, root) for root in allowed_roots):
        return resolved, "path is outside explicit allowed roots."
    if not path.exists():
        return resolved, "path does not exist."
    try:
        strict_resolved = path.resolve(strict=True)
    except OSError as exc:
        return resolved, f"path strict resolution failed: {exc}"
    if not any(_is_relative_to(strict_resolved, root) for root in allowed_roots):
        return strict_resolved, "path resolves outside explicit allowed roots."
    if not strict_resolved.is_file():
        return strict_resolved, "path is not a file."
    return strict_resolved, None


def _resolve_and_guard_csv_reference(
    path_value: str | Path,
    *,
    manifest_path: Path,
    allowed_roots: Sequence[Path],
) -> tuple[Path, str | None, str]:
    text = str(path_value)
    candidate = Path(path_value)
    if not candidate.is_absolute() and not text.lower().startswith(NETWORK_PREFIXES):
        candidate = manifest_path.parent / candidate
    if candidate.suffix.lower() != ".csv":
        return candidate, STATUS_BLOCKED_BY_UNSUPPORTED_FILE_TYPE, "target reference must be a .csv file."
    guarded, error = _guard_existing_file(candidate, allowed_roots=allowed_roots, expected_suffix=".csv")
    if error:
        return guarded, STATUS_BLOCKED_BY_PATH_GUARD, error
    return guarded, None, ""


def _load_json_object(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"JSON object could not be read: {exc}"
    if not isinstance(payload, dict):
        return {}, "JSON payload must be a top-level object."
    return payload, None


def _validate_manifest_schema(manifest: dict[str, Any]) -> str | None:
    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in manifest:
            return f"manifest missing required field: {field}"
    if manifest.get("report_only") is not True or manifest.get("diagnostic_only") is not True:
        return "manifest must be report_only and diagnostic_only."
    expected_levels = {
        "requested_file_touch_level": CSV_PHYSICAL_DATA_LINE_COUNT_ONLY,
        "requested_csv_read_level": CSV_PHYSICAL_DATA_LINE_COUNT_ONLY,
        "requested_csv_physical_data_line_count_level": CSV_PHYSICAL_DATA_LINE_COUNT_ONLY,
        "requested_local_file_hash_level": LOCAL_FILE_HASH_NONE,
        "requested_expected_hash_verification_level": EXPECTED_HASH_VERIFICATION_NONE,
        "row_count_policy": PHYSICAL_NON_HEADER_LINE_COUNT,
    }
    for field, expected in expected_levels.items():
        if manifest.get(field) != expected:
            return f"manifest {field} must be {expected}."
    references = manifest.get("csv_file_references")
    if not isinstance(references, list) or len(references) != 1:
        return "manifest must contain exactly one csv_file_references item."
    reference = references[0]
    if not isinstance(reference, dict):
        return "csv file reference must be an object."
    for field in REQUIRED_REFERENCE_FIELDS:
        if field not in reference:
            return f"csv file reference missing required field: {field}"
    if reference.get("reference_type") != "reviewed_local_csv_file_ref":
        return "csv file reference_type must be reviewed_local_csv_file_ref."
    if reference.get("required") is not True:
        return "csv file reference required must be true."
    if reference.get("declared_only") is not False:
        return "csv file reference declared_only must be false."
    if reference.get("intended_touch_level") != CSV_PHYSICAL_DATA_LINE_COUNT_ONLY:
        return "csv file reference intended_touch_level must be CSV_PHYSICAL_DATA_LINE_COUNT_ONLY."
    flags = manifest.get("forbidden_downstream_flags")
    if not isinstance(flags, dict):
        return "forbidden_downstream_flags must be an object."
    for flag in REQUIRED_FALSE_FLAGS:
        if flags.get(flag) is not False:
            return "forbidden downstream flag true"
    limitations = manifest.get("limitations")
    if not isinstance(limitations, list) or not limitations:
        return "limitations must be a non-empty list."
    return None


def _validate_header_metadata(header: dict[str, Any], csv_path: Path) -> str | None:
    if header.get("report_only") is not True or header.get("diagnostic_only") is not True:
        return "header metadata must be report_only and diagnostic_only."
    if header.get("csv_header_read") is not True:
        return "header metadata must show prior header-only read."
    if "csv_header_column_count" in header:
        try:
            if int(header["csv_header_column_count"]) <= 0:
                return "header metadata csv_header_column_count must be positive when present."
        except (TypeError, ValueError):
            return "header metadata csv_header_column_count must be numeric when present."
    for field in HEADER_POLICY_TRUE_FIELDS:
        if header.get(field) is not False:
            return f"header metadata unsafe field must be false: {field}"
    target_reference = _header_target_reference(header)
    if target_reference is not None:
        if _resolve_header_target(target_reference).resolve(strict=False) != csv_path.resolve(strict=False):
            return "header metadata target CSV reference must match manifest CSV reference."
    return None


def _header_target_reference(header: dict[str, Any]) -> str | None:
    for field in [
        "target_csv_path",
        "target_csv_reference",
        "csv_path",
        "local_csv_path",
        "path",
    ]:
        value = header.get(field)
        if isinstance(value, str) and value:
            return value
    return None


def _resolve_header_target(value: str) -> Path:
    return Path(value)


def _resolve_manifest_reference(value: str | Path, manifest_path: Path) -> Path:
    path = Path(value)
    if path.is_absolute() or str(value).lower().startswith(NETWORK_PREFIXES):
        return path
    return manifest_path.parent / path


def _count_physical_lines(csv_path: Path) -> int:
    count = 0
    with csv_path.open("rb") as handle:
        for _line in handle:
            count += 1
    return count


def _write_artifacts(result: dict[str, Any]) -> None:
    artifact_root = Path(result["artifact_root"])
    artifact_root.mkdir(parents=True, exist_ok=True)
    _write_json(Path(result["artifact_paths"]["metadata"]), _metadata_for_artifact(result))
    _write_json(Path(result["artifact_paths"]["forbidden_downstream_flags"]), csv_physical_data_line_count_safety_flags())
    _write_text(Path(result["artifact_paths"]["report"]), _report_markdown(result))
    _write_text(Path(result["artifact_paths"]["limitations"]), _limitations_markdown(result))
    _write_rows(
        Path(result["artifact_paths"]["issues"]),
        ["severity", "status", "message"],
        result["issues"],
    )
    _write_rows(
        Path(result["artifact_paths"]["summary"]),
        ["field", "value"],
        [{"field": key, "value": result[key]} for key in _summary_fields()],
    )


def _metadata_for_artifact(result: dict[str, Any]) -> dict[str, Any]:
    excluded = {"issues", "limitations"}
    return {key: value for key, value in result.items() if key not in excluded}


def _summary_fields() -> list[str]:
    return [
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
        "csv_physical_data_line_count_level",
        "csv_physical_data_line_count_computed",
        "csv_physical_data_line_count",
        "csv_physical_data_line_count_policy",
        "csv_physical_line_count_total",
        "csv_header_dependency_policy",
        "header_metadata_reused",
        "csv_header_read",
        "csv_header_values_recorded",
        "csv_header_line_skipped_by_policy",
        "target_csv_opened_for_physical_data_line_count",
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
        "recommended_next_task",
    ]


def _report_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# CSV Physical Data-Line Count-Only Report",
        "",
        f"- runtime_status: {result['runtime_status']}",
        f"- health_status: {result['health_status']}",
        f"- workflow_stage: {result['workflow_stage']}",
        f"- report_only: {str(result['report_only']).lower()}",
        f"- diagnostic_only: {str(result['diagnostic_only']).lower()}",
        f"- csv_physical_data_line_count_computed: {str(result['csv_physical_data_line_count_computed']).lower()}",
        f"- csv_physical_data_line_count: {result['csv_physical_data_line_count']}",
        f"- csv_physical_data_line_count_policy: {result['csv_physical_data_line_count_policy']}",
        "",
        "This artifact counts physical non-header lines only. It does not parse fields, read values, store row snippets, or interpret quoted multiline content as one semantic CSV record.",
        "",
        f"Recommended next task: {result['recommended_next_task']}",
    ]
    return "\n".join(lines) + "\n"


def _limitations_markdown(result: dict[str, Any]) -> str:
    lines = ["# Limitations", ""]
    for limitation in result["limitations"]:
        lines.append(f"- {limitation}")
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
            handle.write(",".join(_csv_cell(row.get(field, "")) for field in fields) + "\n")


def _csv_cell(value: Any) -> str:
    text = str(value)
    if any(char in text for char in [",", '"', "\n", "\r"]):
        return '"' + text.replace('"', '""') + '"'
    return text


def _has_blocked_path_text(text: str) -> bool:
    lowered = text.lower().replace("\\", "/")
    if lowered.startswith(NETWORK_PREFIXES):
        return True
    parts = [part for part in lowered.split("/") if part]
    if any(part in {".env", ".venv"} or part.startswith(".env") for part in parts):
        return True
    return any(part in FORBIDDEN_PATH_TOKENS for part in parts)


def _has_protected_pair(parts: Sequence[str]) -> bool:
    lowered = [str(part).lower() for part in parts]
    return any(pair in zip(lowered, lowered[1:]) for pair in PROTECTED_PATH_PAIRS)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False
