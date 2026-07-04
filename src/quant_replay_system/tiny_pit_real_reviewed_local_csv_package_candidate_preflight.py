"""Report-only preflight core for Tiny PIT reviewed LOCAL_CSV candidates.

This module aggregates explicit JSON metadata references and reports missing
evidence, blockers, warnings, and safety flags. It does not open target CSVs or
source artifacts, recompute hashes, compare available_time to decision time,
validate PIT/reviewer/source semantics, create package candidates, or enable
replay/buy-review/trading behavior.
"""

from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence


PREFLIGHT_NONE = "PREFLIGHT_NONE"
PACKAGE_CREATION_NONE = "PACKAGE_CREATION_NONE"
CSV_READ_NONE = "CSV_READ_NONE"
SOURCE_HASH_VALIDATION_NONE = "SOURCE_HASH_VALIDATION_NONE"
REVISION_ID_VALIDATION_NONE = "REVISION_ID_VALIDATION_NONE"
AVAILABLE_TIME_VALIDATION_NONE = "AVAILABLE_TIME_VALIDATION_NONE"
PIT_ADMISSIBILITY_NONE = "PIT_ADMISSIBILITY_NONE"
REVIEWER_AUTHORITY_NONE = "REVIEWER_AUTHORITY_NONE"
QUALITY_STATUS_NONE = "QUALITY_STATUS_NONE"
LIMITATION_REVIEW_NONE = "LIMITATION_REVIEW_NONE"
PERMISSION_REVIEW_NONE = "PERMISSION_REVIEW_NONE"
SOURCE_RELIABILITY_NONE = "SOURCE_RELIABILITY_NONE"
ACTIVE_INPUT_NONE = "ACTIVE_INPUT_NONE"
REPLAY_READINESS_NONE = "REPLAY_READINESS_NONE"
PREFLIGHT_METADATA_REFERENCES_ONLY = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_METADATA_REFERENCES_ONLY"
)
MAX_MANIFEST_SIZE_BYTES = 1_048_576

STATUS_NO_INPUT = "NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_INPUT"
STATUS_METADATA_CONTEXT_REPORT_ONLY = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_METADATA_CONTEXT_REPORT_ONLY"
)
STATUS_WARN_MISSING_OPTIONAL_EVIDENCE = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_WARN_MISSING_OPTIONAL_EVIDENCE"
)
STATUS_WARN_UNVALIDATED_SOURCE_HASH = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_WARN_UNVALIDATED_SOURCE_HASH"
)
STATUS_WARN_NO_AVAILABLE_TIME_PIT_GATE = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_WARN_NO_AVAILABLE_TIME_PIT_GATE"
)
STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_BLOCKED_BY_MISSING_ALLOW_FLAG"
)
STATUS_BLOCKED_BY_MANIFEST_SCHEMA = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_BLOCKED_BY_MANIFEST_SCHEMA"
)
STATUS_BLOCKED_BY_PATH_GUARD = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_BLOCKED_BY_PATH_GUARD"
)
STATUS_BLOCKED_BY_MISSING_REQUIRED_METADATA = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_BLOCKED_BY_MISSING_REQUIRED_METADATA"
)
STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_BLOCKED_BY_UNSAFE_REFERENCE_METADATA"
)
STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
)
STATUS_BLOCKED_BY_REVIEWER_QUALITY_LIMITATION = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_BLOCKED_BY_REVIEWER_QUALITY_LIMITATION"
)
STATUS_BLOCKED_BY_PERMISSION = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_BLOCKED_BY_PERMISSION"
)
STATUS_BLOCKED_BY_UNSUPPORTED_VALIDATION_CLAIM = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_BLOCKED_BY_UNSUPPORTED_VALIDATION_CLAIM"
)
STATUS_HEALTH_FAILED = "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_HEALTH_FAILED"

WORKFLOW_NAME = "tiny_pit_real_reviewed_local_csv_package_candidate_preflight"
WORKFLOW_STAGE = "TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_CORE_CREATED_REPORT_ONLY"
CREATED_AT = "2026-07-04T00:00:00Z"
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Artifact Views "
    "Report-Only v0.1"
)

ARTIFACT_FILENAMES = {
    "metadata": "metadata.json",
    "report": "real_reviewed_local_csv_package_candidate_preflight_report.md",
    "limitations": "limitations.md",
    "issues": "issues.csv",
    "summary": "real_reviewed_local_csv_package_candidate_preflight_summary.csv",
    "forbidden_downstream_flags": "forbidden_downstream_flags.json",
    "evidence_reference_matrix": "evidence_reference_matrix.csv",
}

REQUIRED_REFERENCE_NAMES = [
    "csv_structural_header_metadata",
    "local_file_byte_hash_metadata",
    "expected_hash_verification_metadata",
    "csv_physical_data_line_count_metadata",
    "source_revision_time_metadata",
    "reviewer_quality_limitation_metadata",
]
OPTIONAL_REFERENCE_NAMES = [
    "metadata_reference_following_metadata",
    "manifest_only_preflight_metadata",
]
REFERENCE_ARG_NAMES = {
    "csv_structural_header_metadata": "csv_structural_header_metadata_path",
    "local_file_byte_hash_metadata": "local_file_byte_hash_metadata_path",
    "expected_hash_verification_metadata": "expected_hash_verification_metadata_path",
    "csv_physical_data_line_count_metadata": "csv_physical_data_line_count_metadata_path",
    "source_revision_time_metadata": "source_revision_time_metadata_path",
    "reviewer_quality_limitation_metadata": "reviewer_quality_limitation_metadata_path",
    "metadata_reference_following_metadata": "metadata_reference_following_metadata_path",
    "manifest_only_preflight_metadata": "manifest_only_preflight_metadata_path",
}

REQUIRED_MANIFEST_FIELDS = [
    "preflight_id",
    "declared_package_id",
    "package_schema_version",
    "created_at",
    "prepared_by",
    "report_only",
    "diagnostic_only",
    "requested_preflight_level",
    "requested_package_creation_level",
    "requested_csv_read_level",
    "requested_source_hash_validation_level",
    "requested_revision_id_validation_level",
    "requested_available_time_validation_level",
    "requested_pit_admissibility_level",
    "requested_reviewer_authority_level",
    "requested_quality_status_level",
    "requested_limitation_review_level",
    "requested_permission_review_level",
    "requested_source_reliability_level",
    "requested_active_input_level",
    "requested_replay_readiness_level",
    "evidence_references",
    "required_evidence_policy",
    "warning_policy",
    "blocker_policy",
    "disclosure_policy",
    "forbidden_downstream_flags",
    "limitations",
]
REQUIRED_REFERENCE_FIELDS = [
    "reference_name",
    "reference_type",
    "path",
    "required",
    "expected_workflow_area",
    "expected_report_only",
    "expected_diagnostic_only",
    "expected_metadata_only",
    "expected_negative_flags",
    "allow_statuses",
    "warn_statuses",
    "block_statuses",
    "disclosure_level",
]
NEGATIVE_FALSE_FIELDS = [
    "target_csv_opened",
    "source_artifact_opened",
    "source_content_read",
    "csv_header_read_by_preflight",
    "csv_physical_data_line_count_computed_by_preflight",
    "source_hash_recomputed",
    "local_file_hash_recomputed",
    "expected_hash_reverified",
    "available_time_compared_to_decision_time",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "reviewer_authority_validated",
    "quality_status_validated",
    "permission_class_validated",
    "source_reliability_scored",
    "real_reviewed_csv_package_created",
    "real_package_candidate_created",
    "active_reviewed_input_candidate_created",
    "real_replay_input_created",
    "active_replay_input",
    "replay_execution_allowed",
    "buy_review_allowed",
    "trading_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]
UNSUPPORTED_TRUE_FIELDS = [
    "source_hash_recomputed",
    "local_file_hash_recomputed",
    "expected_hash_reverified",
    "available_time_compared_to_decision_time",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "reviewer_authority_validated",
    "quality_status_validated",
    "permission_class_validated",
    "source_reliability_scored",
]
UNSAFE_REFERENCE_TRUE_FIELDS = [
    "real_reviewed_csv_package_created",
    "real_package_candidate_created",
    "active_reviewed_input_candidate_created",
    "real_replay_input_created",
    "active_replay_input",
    "replay_execution_allowed",
    "buy_review_allowed",
    "trading_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]
FORBIDDEN_STATUS_WORDING = [
    "REAL_PACKAGE_CANDIDATE_CREATED",
    "PACKAGE_APPROVED",
    "PACKAGE_ADMISSIBLE",
    "PIT_ADMISSIBLE_PACKAGE",
    "READY_FOR_REPLAY",
    "REPLAY_INPUT_READY",
    "ACTIVE_REPLAY_INPUT_READY",
    "APPROVED_FOR_ACTIVE_INPUT",
    "BUY_REVIEW_READY",
    "TRADING_READY",
    "PERFORMANCE_VALIDATED",
]
NETWORK_PREFIXES = ("http://", "https://", "ftp://", "s3://", "gs://", "oss://", "file://")
PROTECTED_PATH_PAIRS = {("data", "raw"), ("data", "processed"), ("data", "cache"), ("docs", "project_sources")}
PROTECTED_PATH_TOKENS = ("secrets", "secret", "auth", "token", "credential", "key", ".env")
FORBIDDEN_PERMISSION_CLASSES = {"restricted", "private", "illegal_or_do_not_use", "unknown"}


def preflight_statuses() -> list[str]:
    return [
        STATUS_NO_INPUT,
        STATUS_METADATA_CONTEXT_REPORT_ONLY,
        STATUS_WARN_MISSING_OPTIONAL_EVIDENCE,
        STATUS_WARN_UNVALIDATED_SOURCE_HASH,
        STATUS_WARN_NO_AVAILABLE_TIME_PIT_GATE,
        STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
        STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
        STATUS_BLOCKED_BY_PATH_GUARD,
        STATUS_BLOCKED_BY_MISSING_REQUIRED_METADATA,
        STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA,
        STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
        STATUS_BLOCKED_BY_REVIEWER_QUALITY_LIMITATION,
        STATUS_BLOCKED_BY_PERMISSION,
        STATUS_BLOCKED_BY_UNSUPPORTED_VALIDATION_CLAIM,
        STATUS_HEALTH_FAILED,
    ]


def run_real_reviewed_local_csv_package_candidate_preflight(
    *,
    output_root: Path | str,
    run_id: str | None = None,
    preflight_manifest_path: Path | str | None = None,
    preflight_metadata_path: Path | str | None = None,
    allowed_manifest_roots: Sequence[Path | str] | None = None,
    csv_structural_header_metadata_path: Path | str | None = None,
    local_file_byte_hash_metadata_path: Path | str | None = None,
    expected_hash_verification_metadata_path: Path | str | None = None,
    csv_physical_data_line_count_metadata_path: Path | str | None = None,
    source_revision_time_metadata_path: Path | str | None = None,
    reviewer_quality_limitation_metadata_path: Path | str | None = None,
    metadata_reference_following_metadata_path: Path | str | None = None,
    manifest_only_preflight_metadata_path: Path | str | None = None,
    preflight_level: str = PREFLIGHT_NONE,
    package_creation_level: str = PACKAGE_CREATION_NONE,
    csv_read_level: str = CSV_READ_NONE,
    source_hash_validation_level: str = SOURCE_HASH_VALIDATION_NONE,
    revision_id_validation_level: str = REVISION_ID_VALIDATION_NONE,
    available_time_validation_level: str = AVAILABLE_TIME_VALIDATION_NONE,
    pit_admissibility_level: str = PIT_ADMISSIBILITY_NONE,
    reviewer_authority_level: str = REVIEWER_AUTHORITY_NONE,
    quality_status_level: str = QUALITY_STATUS_NONE,
    limitation_review_level: str = LIMITATION_REVIEW_NONE,
    permission_review_level: str = PERMISSION_REVIEW_NONE,
    source_reliability_level: str = SOURCE_RELIABILITY_NONE,
    active_input_level: str = ACTIVE_INPUT_NONE,
    replay_readiness_level: str = REPLAY_READINESS_NONE,
    allow_real_reviewed_local_csv_package_candidate_preflight: bool = False,
    max_manifest_size_bytes: int = MAX_MANIFEST_SIZE_BYTES,
) -> dict[str, Any]:
    """Run report-only metadata-reference preflight diagnostics."""

    output_root_path = _validate_output_root(Path(output_root))
    safe_run_id = run_id or uuid.uuid4().hex[:12]
    artifact_dir = output_root_path / safe_run_id
    artifact_paths = {name: artifact_dir / filename for name, filename in ARTIFACT_FILENAMES.items()}

    supplied_paths = {
        "preflight_metadata_path": preflight_metadata_path,
        "csv_structural_header_metadata_path": csv_structural_header_metadata_path,
        "local_file_byte_hash_metadata_path": local_file_byte_hash_metadata_path,
        "expected_hash_verification_metadata_path": expected_hash_verification_metadata_path,
        "csv_physical_data_line_count_metadata_path": csv_physical_data_line_count_metadata_path,
        "source_revision_time_metadata_path": source_revision_time_metadata_path,
        "reviewer_quality_limitation_metadata_path": reviewer_quality_limitation_metadata_path,
        "metadata_reference_following_metadata_path": metadata_reference_following_metadata_path,
        "manifest_only_preflight_metadata_path": manifest_only_preflight_metadata_path,
    }

    if preflight_manifest_path is None:
        result = _base_result(
            run_id=safe_run_id,
            artifact_dir=artifact_dir,
            artifact_paths=artifact_paths,
            runtime_status=STATUS_NO_INPUT,
            health_status="PASS",
            preflight_level=PREFLIGHT_NONE,
            package_creation_level=PACKAGE_CREATION_NONE,
            csv_read_level=CSV_READ_NONE,
        )
        _write_artifacts(result)
        return result

    if not allow_real_reviewed_local_csv_package_candidate_preflight:
        result = _base_result(
            run_id=safe_run_id,
            artifact_dir=artifact_dir,
            artifact_paths=artifact_paths,
            runtime_status=STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
            health_status="FAIL",
        )
        result["issues"].append("missing explicit preflight allow flag")
        result["issue_count"] = len(result["issues"])
        result["promotion_blocker_count"] = 1
        _write_artifacts(result)
        return result

    path_error = _guard_path(preflight_manifest_path, allowed_manifest_roots, must_exist=True)
    if path_error:
        result = _base_result(
            run_id=safe_run_id,
            artifact_dir=artifact_dir,
            artifact_paths=artifact_paths,
            runtime_status=STATUS_BLOCKED_BY_PATH_GUARD,
            health_status="FAIL",
        )
        result["issues"].append(path_error)
        result["issue_count"] = len(result["issues"])
        result["promotion_blocker_count"] = 1
        _write_artifacts(result)
        return result

    manifest_path = Path(preflight_manifest_path).resolve()
    manifest, manifest_error = _read_json_object(manifest_path, max_manifest_size_bytes)
    if manifest_error:
        result = _base_result(
            run_id=safe_run_id,
            artifact_dir=artifact_dir,
            artifact_paths=artifact_paths,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            health_status="FAIL",
        )
        result["issues"].append(manifest_error)
        result["preflight_manifest_read"] = False
        result["issue_count"] = len(result["issues"])
        result["promotion_blocker_count"] = 1
        _write_artifacts(result)
        return result

    schema_errors = _manifest_schema_errors(manifest)
    if schema_errors:
        result = _base_result(
            run_id=safe_run_id,
            artifact_dir=artifact_dir,
            artifact_paths=artifact_paths,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            health_status="FAIL",
        )
        result["preflight_manifest_read"] = True
        result["issues"].extend(schema_errors)
        result["issue_count"] = len(result["issues"])
        result["promotion_blocker_count"] = 1
        _write_artifacts(result)
        return result

    result = _base_result(
        run_id=safe_run_id,
        artifact_dir=artifact_dir,
        artifact_paths=artifact_paths,
        runtime_status=STATUS_METADATA_CONTEXT_REPORT_ONLY,
        health_status="PASS",
        preflight_id=str(manifest.get("preflight_id", "")),
        declared_package_id=str(manifest.get("declared_package_id", "")),
        preflight_level=PREFLIGHT_METADATA_REFERENCES_ONLY,
        package_creation_level=PACKAGE_CREATION_NONE,
        csv_read_level=CSV_READ_NONE,
    )
    result.update(
        {
            "preflight_manifest_read": True,
            "references_declared": True,
            "references_followed_metadata_only": True,
            "evidence_reference_matrix_created": True,
            "source_hash_recompute_not_performed": True,
            "available_time_pit_gate_not_performed": True,
            "reviewer_authority_validation_not_performed": True,
            "package_creation_not_performed": True,
            "unvalidated_capability_count": 4,
        }
    )

    unsupported_claims = _unsupported_manifest_claims(
        manifest,
        supplied_levels={
            "preflight_level": preflight_level,
            "package_creation_level": package_creation_level,
            "csv_read_level": csv_read_level,
            "source_hash_validation_level": source_hash_validation_level,
            "revision_id_validation_level": revision_id_validation_level,
            "available_time_validation_level": available_time_validation_level,
            "pit_admissibility_level": pit_admissibility_level,
            "reviewer_authority_level": reviewer_authority_level,
            "quality_status_level": quality_status_level,
            "limitation_review_level": limitation_review_level,
            "permission_review_level": permission_review_level,
            "source_reliability_level": source_reliability_level,
            "active_input_level": active_input_level,
            "replay_readiness_level": replay_readiness_level,
        },
    )
    forbidden_downstream = _true_flags(manifest.get("forbidden_downstream_flags"))
    if forbidden_downstream:
        result["runtime_status"] = STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM
        result["health_status"] = "FAIL"
        result["issues"].append("forbidden downstream flag(s): " + ",".join(forbidden_downstream))

    manifest_refs = _manifest_reference_paths(manifest)
    path_inputs = _reference_path_inputs(supplied_paths, manifest_refs)
    matrix_rows = []
    for reference_name in [*REQUIRED_REFERENCE_NAMES, *OPTIONAL_REFERENCE_NAMES]:
        path = path_inputs.get(reference_name)
        required = reference_name in REQUIRED_REFERENCE_NAMES
        if not required and path is None:
            continue
        row = _inspect_reference(reference_name, path, required, allowed_manifest_roots)
        matrix_rows.append(row)
        _apply_reference_decision(result, row)

    result["evidence_reference_matrix"] = matrix_rows
    result["evidence_reference_count"] = len([row for row in matrix_rows if row["reference_present"]])
    result["required_reference_count"] = len(REQUIRED_REFERENCE_NAMES)
    result["required_reference_present_count"] = len(
        [
            row
            for row in matrix_rows
            if row["reference_name"] in REQUIRED_REFERENCE_NAMES and row["reference_present"]
        ]
    )
    result["missing_required_reference_count"] = len(
        [
            row
            for row in matrix_rows
            if row["reference_name"] in REQUIRED_REFERENCE_NAMES and not row["reference_present"]
        ]
    )
    result["optional_reference_count"] = len(
        [row for row in matrix_rows if row["reference_name"] in OPTIONAL_REFERENCE_NAMES and row["reference_path_preview"]]
    )
    result["missing_optional_reference_count"] = len(
        [
            row
            for row in matrix_rows
            if row["reference_name"] in OPTIONAL_REFERENCE_NAMES
            and row["reference_path_preview"]
            and not row["reference_present"]
        ]
    )

    if unsupported_claims and result["health_status"] != "FAIL":
        result["runtime_status"] = STATUS_BLOCKED_BY_UNSUPPORTED_VALIDATION_CLAIM
        result["health_status"] = "FAIL"
        result["issues"].extend(unsupported_claims)
    elif result["missing_required_reference_count"] and result["health_status"] != "FAIL":
        result["runtime_status"] = STATUS_BLOCKED_BY_MISSING_REQUIRED_METADATA
        result["health_status"] = "FAIL"
    elif result["missing_optional_reference_count"] and result["health_status"] != "FAIL":
        result["runtime_status"] = STATUS_WARN_MISSING_OPTIONAL_EVIDENCE
        result["health_status"] = "WARN"
        result["warning_count"] += result["missing_optional_reference_count"]
    elif result["warning_count"] and result["health_status"] != "FAIL":
        result["runtime_status"] = STATUS_WARN_MISSING_OPTIONAL_EVIDENCE
        result["health_status"] = "WARN"

    result["issue_count"] = len(result["issues"])
    if result["health_status"] == "FAIL":
        result["promotion_blocker_count"] = max(1, result["promotion_blocker_count"])

    _write_artifacts(result)
    return result


def _base_result(
    *,
    run_id: str,
    artifact_dir: Path,
    artifact_paths: Mapping[str, Path],
    runtime_status: str,
    health_status: str,
    preflight_id: str = "",
    declared_package_id: str = "",
    preflight_level: str = PREFLIGHT_NONE,
    package_creation_level: str = PACKAGE_CREATION_NONE,
    csv_read_level: str = CSV_READ_NONE,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "workflow_name": WORKFLOW_NAME,
        "workflow_stage": WORKFLOW_STAGE,
        "run_id": run_id,
        "preflight_id": preflight_id,
        "declared_package_id": declared_package_id,
        "runtime_status": runtime_status,
        "status": runtime_status,
        "health_status": health_status,
        "created_at": CREATED_AT,
        "artifact_dir": str(artifact_dir),
        "artifact_paths": {name: str(path) for name, path in artifact_paths.items()},
        "report_only": True,
        "diagnostic_only": True,
        "preflight_level": preflight_level,
        "package_creation_level": package_creation_level,
        "csv_read_level": csv_read_level,
        "source_hash_validation_level": SOURCE_HASH_VALIDATION_NONE,
        "revision_id_validation_level": REVISION_ID_VALIDATION_NONE,
        "available_time_validation_level": AVAILABLE_TIME_VALIDATION_NONE,
        "pit_admissibility_level": PIT_ADMISSIBILITY_NONE,
        "reviewer_authority_level": REVIEWER_AUTHORITY_NONE,
        "quality_status_level": QUALITY_STATUS_NONE,
        "limitation_review_level": LIMITATION_REVIEW_NONE,
        "permission_review_level": PERMISSION_REVIEW_NONE,
        "source_reliability_level": SOURCE_RELIABILITY_NONE,
        "active_input_level": ACTIVE_INPUT_NONE,
        "replay_readiness_level": REPLAY_READINESS_NONE,
        "preflight_manifest_read": False,
        "preflight_metadata_read": False,
        "references_declared": False,
        "references_followed_metadata_only": False,
        "evidence_reference_matrix_created": False,
        "evidence_reference_count": 0,
        "required_reference_count": 0,
        "required_reference_present_count": 0,
        "missing_required_reference_count": 0,
        "optional_reference_count": 0,
        "missing_optional_reference_count": 0,
        "unvalidated_capability_count": 0,
        "source_hash_recompute_not_performed": True,
        "available_time_pit_gate_not_performed": True,
        "reviewer_authority_validation_not_performed": True,
        "package_creation_not_performed": True,
        "promotion_blocker_count": 0,
        "warning_count": 0,
        "issue_count": 0,
        "issues": [],
        "limitations": ["preflight is metadata-reference context only"],
        "forbidden_downstream_flags": {field: False for field in NEGATIVE_FALSE_FIELDS},
        "evidence_reference_matrix": [],
        "recommended_next_task": NEXT_TASK,
    }
    for field in NEGATIVE_FALSE_FIELDS:
        result[field] = False
    return result


def _manifest_schema_errors(manifest: Mapping[str, Any]) -> list[str]:
    errors = [f"missing required manifest field: {field}" for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    if manifest.get("report_only") is not True:
        errors.append("manifest report_only must be true")
    if manifest.get("diagnostic_only") is not True:
        errors.append("manifest diagnostic_only must be true")
    refs = manifest.get("evidence_references")
    if not isinstance(refs, list):
        errors.append("manifest evidence_references must be a list")
    else:
        for idx, ref in enumerate(refs):
            if not isinstance(ref, dict):
                errors.append(f"evidence_references[{idx}] must be an object")
                continue
            for field in REQUIRED_REFERENCE_FIELDS:
                if field not in ref:
                    errors.append(f"evidence_references[{idx}] missing {field}")
    return errors


def _unsupported_manifest_claims(manifest: Mapping[str, Any], *, supplied_levels: Mapping[str, str]) -> list[str]:
    errors = []
    expected = {
        "requested_package_creation_level": PACKAGE_CREATION_NONE,
        "requested_csv_read_level": CSV_READ_NONE,
        "requested_source_hash_validation_level": SOURCE_HASH_VALIDATION_NONE,
        "requested_revision_id_validation_level": REVISION_ID_VALIDATION_NONE,
        "requested_available_time_validation_level": AVAILABLE_TIME_VALIDATION_NONE,
        "requested_pit_admissibility_level": PIT_ADMISSIBILITY_NONE,
        "requested_source_reliability_level": SOURCE_RELIABILITY_NONE,
        "requested_active_input_level": ACTIVE_INPUT_NONE,
        "requested_replay_readiness_level": REPLAY_READINESS_NONE,
    }
    for field, expected_value in expected.items():
        if manifest.get(field) != expected_value:
            errors.append(f"unsupported validation claim in manifest: {field}")
    supplied_expected = {
        "package_creation_level": PACKAGE_CREATION_NONE,
        "csv_read_level": CSV_READ_NONE,
        "source_hash_validation_level": SOURCE_HASH_VALIDATION_NONE,
        "revision_id_validation_level": REVISION_ID_VALIDATION_NONE,
        "available_time_validation_level": AVAILABLE_TIME_VALIDATION_NONE,
        "pit_admissibility_level": PIT_ADMISSIBILITY_NONE,
        "source_reliability_level": SOURCE_RELIABILITY_NONE,
        "active_input_level": ACTIVE_INPUT_NONE,
        "replay_readiness_level": REPLAY_READINESS_NONE,
    }
    for field, expected_value in supplied_expected.items():
        if supplied_levels.get(field) != expected_value:
            errors.append(f"unsupported validation claim in API level: {field}")
    return errors


def _manifest_reference_paths(manifest: Mapping[str, Any]) -> dict[str, str]:
    paths = {}
    refs = manifest.get("evidence_references")
    if not isinstance(refs, list):
        return paths
    for ref in refs:
        if isinstance(ref, dict) and ref.get("reference_name") in [*REQUIRED_REFERENCE_NAMES, *OPTIONAL_REFERENCE_NAMES]:
            paths[str(ref["reference_name"])] = str(ref.get("path", ""))
    return paths


def _reference_path_inputs(
    supplied_paths: Mapping[str, Path | str | None],
    manifest_refs: Mapping[str, str],
) -> dict[str, Path | str | None]:
    inputs: dict[str, Path | str | None] = {}
    for reference_name, arg_name in REFERENCE_ARG_NAMES.items():
        inputs[reference_name] = supplied_paths.get(arg_name) or manifest_refs.get(reference_name)
    return inputs


def _inspect_reference(
    reference_name: str,
    path: Path | str | None,
    required: bool,
    allowed_roots: Sequence[Path | str] | None,
) -> dict[str, Any]:
    row = {
        "reference_name": reference_name,
        "reference_path_preview": _path_preview(path),
        "reference_present": False,
        "reference_read_as_json": False,
        "reference_runtime_status": "",
        "reference_health_status": "",
        "reference_workflow_stage": "",
        "reference_report_only": False,
        "reference_diagnostic_only": False,
        "reference_negative_flags_ok": False,
        "reference_issue_count": 0,
        "reference_warning_count": 0,
        "reference_blocker_count": 0,
        "reference_decision": "MISSING_REQUIRED" if required else "MISSING_OPTIONAL",
        "reference_missing_reason": "reference path not supplied",
        "reference_warning_reason": "",
        "reference_blocker_reason": "",
        "source_hash_preview": "",
        "reviewer_id_preview": "",
        "_metadata": {},
    }
    if path is None:
        return row

    path_error = _guard_path(path, allowed_roots, must_exist=False)
    if path_error:
        row.update(
            {
                "reference_decision": "PATH_GUARD_BLOCK",
                "reference_missing_reason": "",
                "reference_blocker_reason": path_error,
            }
        )
        return row
    metadata_path = Path(path).resolve()
    if not metadata_path.exists():
        row["reference_missing_reason"] = "reference metadata file missing"
        return row

    metadata, error = _read_json_object(metadata_path, 256 * 1024)
    if error:
        row.update(
            {
                "reference_present": True,
                "reference_decision": "BLOCK",
                "reference_missing_reason": "",
                "reference_blocker_reason": error,
            }
        )
        return row

    true_unsafe = _true_flags({field: metadata.get(field) for field in UNSAFE_REFERENCE_TRUE_FIELDS})
    true_unsupported = _true_flags({field: metadata.get(field) for field in UNSUPPORTED_TRUE_FIELDS})
    downstream_flags = _true_flags(metadata.get("forbidden_downstream_flags"))
    health_status = str(metadata.get("health_status", ""))
    runtime_status = str(metadata.get("runtime_status", ""))
    workflow_stage = str(metadata.get("workflow_stage", ""))
    forbidden_wording = _forbidden_wording_fields(
        {
            "runtime_status": runtime_status,
            "workflow_stage": workflow_stage,
            "recommended_next_task": metadata.get("recommended_next_task", ""),
        }
    )
    blocker_count = _int_value(metadata.get("blocker_count"))
    warning_count = _int_value(metadata.get("warning_count"))

    row.update(
        {
            "reference_present": True,
            "reference_read_as_json": True,
            "reference_runtime_status": runtime_status,
            "reference_health_status": health_status,
            "reference_workflow_stage": workflow_stage,
            "reference_report_only": metadata.get("report_only") is True,
            "reference_diagnostic_only": metadata.get("diagnostic_only") is True,
            "reference_issue_count": _int_value(metadata.get("issue_count")),
            "reference_warning_count": warning_count,
            "reference_blocker_count": blocker_count,
            "source_hash_preview": str(metadata.get("source_hash_preview", "")),
            "reviewer_id_preview": str(metadata.get("reviewer_id_preview", "")),
            "_metadata": metadata,
        }
    )
    row["reference_negative_flags_ok"] = not (
        true_unsafe or true_unsupported or downstream_flags
    )

    if forbidden_wording:
        row["reference_decision"] = "UNSAFE_REFERENCE_METADATA"
        row["reference_blocker_reason"] = "forbidden readiness wording in reference metadata"
    elif true_unsupported:
        row["reference_decision"] = "UNSUPPORTED_VALIDATION_CLAIM"
        row["reference_blocker_reason"] = "unsupported validation claim(s): " + ",".join(true_unsupported)
    elif true_unsafe:
        row["reference_decision"] = "UNSAFE_REFERENCE_METADATA"
        row["reference_blocker_reason"] = "unsafe downstream claim(s): " + ",".join(true_unsafe)
    elif downstream_flags:
        row["reference_decision"] = "FORBIDDEN_DOWNSTREAM"
        row["reference_blocker_reason"] = "forbidden downstream flag(s): " + ",".join(downstream_flags)
    elif reference_name == "reviewer_quality_limitation_metadata" and _is_permission_block(metadata):
        row["reference_decision"] = "PERMISSION_BLOCK"
        row["reference_blocker_reason"] = "forbidden permission metadata"
    elif reference_name == "reviewer_quality_limitation_metadata" and _is_reviewer_quality_block(metadata):
        row["reference_decision"] = "REVIEWER_QUALITY_LIMITATION_BLOCK"
        row["reference_blocker_reason"] = "reviewer quality limitation blocker"
    elif health_status == "FAIL" or blocker_count:
        row["reference_decision"] = "BLOCK"
        row["reference_blocker_reason"] = "reference health failed or blocker count positive"
    elif health_status == "WARN" or warning_count or "WARN" in runtime_status:
        row["reference_decision"] = "WARN"
        row["reference_warning_reason"] = "reference warning context"
    else:
        row["reference_decision"] = "PASS"
    row["reference_missing_reason"] = ""
    return row


def _apply_reference_decision(result: dict[str, Any], row: Mapping[str, Any]) -> None:
    decision = row["reference_decision"]
    if decision == "BLOCK":
        result["runtime_status"] = STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA
        result["health_status"] = "FAIL"
        result["issues"].append(str(row["reference_blocker_reason"]))
    elif decision == "UNSUPPORTED_VALIDATION_CLAIM":
        result["runtime_status"] = STATUS_BLOCKED_BY_UNSUPPORTED_VALIDATION_CLAIM
        result["health_status"] = "FAIL"
        result["issues"].append(str(row["reference_blocker_reason"]))
    elif decision == "UNSAFE_REFERENCE_METADATA":
        result["runtime_status"] = STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA
        result["health_status"] = "FAIL"
        result["issues"].append(str(row["reference_blocker_reason"]))
    elif decision == "FORBIDDEN_DOWNSTREAM":
        result["runtime_status"] = STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM
        result["health_status"] = "FAIL"
        result["issues"].append(str(row["reference_blocker_reason"]))
    elif decision == "REVIEWER_QUALITY_LIMITATION_BLOCK":
        result["runtime_status"] = STATUS_BLOCKED_BY_REVIEWER_QUALITY_LIMITATION
        result["health_status"] = "FAIL"
        result["issues"].append(str(row["reference_blocker_reason"]))
    elif decision == "PERMISSION_BLOCK":
        result["runtime_status"] = STATUS_BLOCKED_BY_PERMISSION
        result["health_status"] = "FAIL"
        result["issues"].append(str(row["reference_blocker_reason"]))
    elif decision == "PATH_GUARD_BLOCK":
        result["runtime_status"] = STATUS_BLOCKED_BY_PATH_GUARD
        result["health_status"] = "FAIL"
        result["issues"].append(str(row["reference_blocker_reason"]))
    elif decision == "MISSING_REQUIRED":
        result["issues"].append(f"missing required evidence: {row['reference_name']}")
    elif decision == "MISSING_OPTIONAL":
        if row["reference_path_preview"]:
            result["warning_count"] += 1
    elif decision == "WARN":
        result["warning_count"] += 1


def _is_reviewer_quality_block(metadata: Mapping[str, Any]) -> bool:
    status = str(metadata.get("runtime_status", ""))
    severity = str(metadata.get("limitation_severity_max", ""))
    return (
        "BLOCKING_LIMITATION" in status
        or severity == "BLOCKER"
        or _int_value(metadata.get("blocking_limitation_count")) > 0
    )


def _is_permission_block(metadata: Mapping[str, Any]) -> bool:
    status = str(metadata.get("runtime_status", ""))
    permission = str(metadata.get("permission_class", ""))
    return "FORBIDDEN_PERMISSION" in status or permission in FORBIDDEN_PERMISSION_CLASSES


def _write_artifacts(result: dict[str, Any]) -> None:
    artifact_dir = Path(result["artifact_dir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_paths = {name: Path(path) for name, path in result["artifact_paths"].items()}
    metadata = _metadata_payload(result)
    artifact_paths["metadata"].write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    artifact_paths["limitations"].write_text(
        "\n".join(["# Limitations", *[f"- {_safe_text(item)}" for item in result["limitations"]], ""]),
        encoding="utf-8",
    )
    artifact_paths["report"].write_text(_report_text(result), encoding="utf-8")
    artifact_paths["forbidden_downstream_flags"].write_text(
        json.dumps(result["forbidden_downstream_flags"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_csv(
        artifact_paths["issues"],
        [{"issue": _safe_text(issue)} for issue in result["issues"]],
        fieldnames=["issue"],
    )
    _write_csv(
        artifact_paths["summary"],
        [_summary_row(result)],
        fieldnames=list(_summary_row(result).keys()),
    )
    matrix_rows = [
        {key: _safe_text(value) for key, value in row.items() if not key.startswith("_")}
        for row in result["evidence_reference_matrix"]
    ]
    _write_csv(
        artifact_paths["evidence_reference_matrix"],
        matrix_rows,
        fieldnames=[
            "reference_name",
            "reference_path_preview",
            "reference_present",
            "reference_read_as_json",
            "reference_runtime_status",
            "reference_health_status",
            "reference_workflow_stage",
            "reference_report_only",
            "reference_diagnostic_only",
            "reference_negative_flags_ok",
            "reference_issue_count",
            "reference_warning_count",
            "reference_blocker_count",
            "reference_decision",
            "reference_missing_reason",
            "reference_warning_reason",
            "reference_blocker_reason",
            "source_hash_preview",
            "reviewer_id_preview",
        ],
    )


def _metadata_payload(result: Mapping[str, Any]) -> dict[str, Any]:
    keys = [
        "workflow_name",
        "workflow_stage",
        "run_id",
        "preflight_id",
        "declared_package_id",
        "runtime_status",
        "health_status",
        "created_at",
        "report_only",
        "diagnostic_only",
        "preflight_level",
        "package_creation_level",
        "csv_read_level",
        "evidence_reference_count",
        "required_reference_count",
        "required_reference_present_count",
        "missing_required_reference_count",
        "optional_reference_count",
        "missing_optional_reference_count",
        "unvalidated_capability_count",
        "source_hash_recompute_not_performed",
        "available_time_pit_gate_not_performed",
        "reviewer_authority_validation_not_performed",
        "package_creation_not_performed",
        "promotion_blocker_count",
        "warning_count",
        "issue_count",
        "recommended_next_task",
        *NEGATIVE_FALSE_FIELDS,
    ]
    payload = {key: result[key] for key in keys if key in result}
    payload["artifact_paths"] = result["artifact_paths"]
    return payload


def _summary_row(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "run_id": result["run_id"],
        "preflight_id": result["preflight_id"],
        "declared_package_id": result["declared_package_id"],
        "runtime_status": result["runtime_status"],
        "health_status": result["health_status"],
        "preflight_level": result["preflight_level"],
        "package_creation_level": result["package_creation_level"],
        "csv_read_level": result["csv_read_level"],
        "evidence_reference_count": result["evidence_reference_count"],
        "missing_required_reference_count": result["missing_required_reference_count"],
        "missing_optional_reference_count": result["missing_optional_reference_count"],
        "warning_count": result["warning_count"],
        "issue_count": result["issue_count"],
        "real_package_candidate_created": result["real_package_candidate_created"],
        "active_replay_input": result["active_replay_input"],
        "buy_review_allowed": result["buy_review_allowed"],
        "trading_allowed": result["trading_allowed"],
        "recommended_next_task": result["recommended_next_task"],
    }


def _report_text(result: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight",
            "",
            f"- Runtime status: `{result['runtime_status']}`",
            f"- Health status: `{result['health_status']}`",
            f"- Preflight id: `{result['preflight_id']}`",
            f"- Declared package id: `{result['declared_package_id']}`",
            f"- Preflight level: `{result['preflight_level']}`",
            f"- Package creation level: `{result['package_creation_level']}`",
            f"- CSV read level: `{result['csv_read_level']}`",
            f"- Evidence reference count: `{result['evidence_reference_count']}`",
            f"- Missing required reference count: `{result['missing_required_reference_count']}`",
            f"- Missing optional reference count: `{result['missing_optional_reference_count']}`",
            f"- Warning count: `{result['warning_count']}`",
            f"- Issue count: `{result['issue_count']}`",
            f"- Real package candidate created: `{str(result['real_package_candidate_created']).lower()}`",
            f"- Active replay input: `{str(result['active_replay_input']).lower()}`",
            f"- Buy review allowed: `{str(result['buy_review_allowed']).lower()}`",
            f"- Trading allowed: `{str(result['trading_allowed']).lower()}`",
            f"- Recommended next task: `{result['recommended_next_task']}`",
            "",
            "This artifact is report-only metadata-reference context and does not validate package, PIT, source, reviewer, replay, buy-review, or trading semantics.",
            "",
        ]
    )


def _write_csv(path: Path, rows: list[Mapping[str, Any]], *, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _read_json_object(path: Path, max_bytes: int) -> tuple[dict[str, Any], str | None]:
    try:
        if path.stat().st_size > max_bytes:
            return {}, f"JSON file exceeds size limit: {_path_preview(path)}"
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return {}, f"unable to read JSON metadata: {exc}"
    except json.JSONDecodeError as exc:
        return {}, f"malformed JSON: {exc.msg}"
    if not isinstance(payload, dict):
        return {}, "JSON payload must be an object"
    return payload, None


def _validate_output_root(output_root: Path) -> Path:
    path_error = _protected_path_reason(output_root)
    if path_error:
        raise ValueError(path_error)
    return output_root


def _guard_path(
    path: Path | str,
    allowed_roots: Sequence[Path | str] | None,
    *,
    must_exist: bool,
) -> str | None:
    text = str(path)
    lowered = text.lower()
    if lowered.startswith(NETWORK_PREFIXES):
        return "path guard blocked URL-like path"
    path_obj = Path(path)
    if any(part == ".." for part in path_obj.parts):
        return "path guard blocked traversal path"
    protected = _protected_path_reason(path_obj)
    if protected:
        return protected
    if any(token in lowered for token in PROTECTED_PATH_TOKENS):
        return "path guard blocked secret/auth/token-like path"
    if allowed_roots is None:
        return "allowed_manifest_roots required"
    resolved = path_obj.resolve()
    roots = [Path(root).resolve() for root in allowed_roots]
    if not any(root == resolved or root in resolved.parents for root in roots):
        return "path guard blocked path outside allowed roots"
    if must_exist and not resolved.exists():
        return "path guard blocked missing required path"
    return None


def _protected_path_reason(path: Path) -> str | None:
    parts = tuple(part.lower() for part in path.parts)
    for pair in PROTECTED_PATH_PAIRS:
        for idx in range(len(parts) - 1):
            if parts[idx : idx + 2] == pair:
                return "path guard blocked protected path"
    return None


def _true_flags(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    return sorted(str(key) for key, item in value.items() if item is True)


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _safe_text(value: Any) -> str:
    text = str(value)
    for phrase in FORBIDDEN_STATUS_WORDING:
        text = text.replace(phrase, "[blocked-wording]")
    if len(text) > 160:
        return text[:157] + "..."
    return text


def _forbidden_wording_fields(values: Mapping[str, Any]) -> list[str]:
    fields = []
    for field, value in values.items():
        text = "" if value is None else str(value)
        if any(phrase in text for phrase in FORBIDDEN_STATUS_WORDING):
            fields.append(field)
    return fields


def _path_preview(path: Path | str | None) -> str:
    if path is None:
        return ""
    return Path(str(path)).name


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
