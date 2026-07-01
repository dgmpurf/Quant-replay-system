"""Metadata-reference-following core for Tiny PIT reviewed LOCAL_CSV candidates.

This module is report-only and diagnostic-only. It accepts only an explicit
top-level JSON manifest and, in the highest inspection level, follows only
whitelisted local JSON metadata references under caller-provided roots. It never
opens CSV/data targets, computes file byte hashes, creates package candidates,
creates replay inputs, runs replay, creates labels/training/model artifacts, or
enables buy-review/trading behavior.
"""

from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence


INSPECTION_LEVEL_NO_INPUT = "NO_INPUT_SYNTHETIC_DECLARATIONS"
INSPECTION_LEVEL_EXPLICIT_MANIFEST_METADATA_ONLY = "EXPLICIT_MANIFEST_METADATA_ONLY"
INSPECTION_LEVEL_DECLARED_ONLY = "METADATA_REFERENCES_DECLARED_ONLY"
INSPECTION_LEVEL_FOLLOWED_METADATA_ONLY = "METADATA_REFERENCES_FOLLOWED_METADATA_ONLY"
INSPECTION_LEVELS = [
    INSPECTION_LEVEL_NO_INPUT,
    INSPECTION_LEVEL_EXPLICIT_MANIFEST_METADATA_ONLY,
    INSPECTION_LEVEL_DECLARED_ONLY,
    INSPECTION_LEVEL_FOLLOWED_METADATA_ONLY,
]

STATUS_NO_INPUT = "NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_INPUT"
STATUS_DECLARED_REPORT_ONLY = "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCES_DECLARED_REPORT_ONLY"
STATUS_FOLLOWED_REPORT_ONLY = "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCES_FOLLOWED_REPORT_ONLY"
STATUS_BLOCKED_BY_PATH_GUARD = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_BLOCKED_BY_PATH_GUARD"
)
STATUS_BLOCKED_BY_FORBIDDEN_DATA_REFERENCE = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_BLOCKED_BY_FORBIDDEN_DATA_REFERENCE"
)
STATUS_BLOCKED_BY_MALFORMED_METADATA = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_BLOCKED_BY_MALFORMED_METADATA"
)
STATUS_BLOCKED_BY_MISSING_REQUIRED_METADATA = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_BLOCKED_BY_MISSING_REQUIRED_METADATA"
)
STATUS_BLOCKED_BY_MANIFEST_SCHEMA = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_BLOCKED_BY_MANIFEST_SCHEMA"
)
STATUS_BLOCKED_BY_METADATA_SCHEMA = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_BLOCKED_BY_METADATA_SCHEMA"
)
STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
)
STATUS_WARN_REVIEW_REQUIRED = "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_WARN_REVIEW_REQUIRED"

WORKFLOW_NAME = "tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following"
WORKFLOW_STAGE = (
    "TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_CORE_CREATED_REPORT_ONLY"
)
CREATED_AT = "2026-06-30T00:00:00Z"
CSV_READ_LEVEL_NONE = "CSV_READ_NONE"
MAX_METADATA_BYTES = 256 * 1024
MAX_REFERENCE_COUNT = 24
MAX_FOLLOWED_METADATA_FILES = 12
DEFAULT_OUTPUT_ROOT = (
    "outputs/reports/manual_diagnostics/"
    "tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following_v0_1"
)
NEXT_BOUNDARY_DESIGN_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Metadata-Reference-Following "
    "Next Boundary Design Planning Report-Only v0.1"
)

ALLOWED_METADATA_REFERENCE_TYPES = [
    "source_registry_snapshot_ref",
    "reviewed_file_manifest_ref",
    "table_schema_manifest_ref",
    "row_lineage_manifest_ref",
    "available_time_manifest_ref",
    "source_hash_revision_manifest_ref",
    "reviewer_attestation_manifest_ref",
    "quality_review_manifest_ref",
    "limitation_manifest_ref",
    "forbidden_downstream_flags_ref",
]

DECLARED_ONLY_OR_BLOCKED_REFERENCE_TYPES = {
    "reviewed_csv_path",
    "raw_csv_path",
    "data_file_ref",
    "raw_document_body_ref",
    "full_text_ref",
    "external_url",
    "broker_api_ref",
    "model_output_ref",
    "training_dataset_ref",
    "replay_input_ref",
    "active_input_ref",
    "signal_semantics_ref",
    "current_candidates_ref",
    "snapshot_ref",
}

FORBIDDEN_DATA_EXTENSIONS = {
    ".csv",
    ".tsv",
    ".xlsx",
    ".xls",
    ".parquet",
    ".feather",
    ".arrow",
    ".h5",
    ".hdf5",
    ".db",
    ".sqlite",
    ".zip",
    ".7z",
    ".rar",
    ".pkl",
    ".pickle",
    ".joblib",
    ".pt",
    ".onnx",
    ".jsonl",
}

FORBIDDEN_STATUS_WORDING = [
    "PACKAGE_APPROVED",
    "PACKAGE_ADMISSIBLE",
    "PIT_ADMISSIBLE_PACKAGE",
    "PIT_VALIDATED_REAL_PACKAGE",
    "READY_FOR_REPLAY",
    "REPLAY_INPUT_READY",
    "ACTIVE_REPLAY_INPUT_READY",
    "APPROVED_FOR_ACTIVE_INPUT",
    "ACTIVE_REVIEWED_INPUT",
    "TRADING_READY",
    "BUY_REVIEW_READY",
    "REAL_BUY_READY",
    "PERFORMANCE_VALIDATED",
]

REQUIRED_MANIFEST_FIELDS = [
    "package_id",
    "package_schema_version",
    "created_at",
    "prepared_by",
    "report_only",
    "diagnostic_only",
    "inspection_level",
    "metadata_references",
    "forbidden_downstream_flags",
    "limitations",
]

REQUIRED_REFERENCE_FIELDS = [
    "reference_type",
    "reference_name",
    "path",
    "required",
    "expected_schema_version",
    "declared_only",
    "notes",
]

REQUIRED_FALSE_FLAGS = [
    "real_csv_consumed",
    "real_reviewed_csv_package_created",
    "real_package_candidate_created",
    "active_reviewed_input_candidate_created",
    "real_replay_input_created",
    "active_replay_input",
    "active_replay_ready",
    "active_replay_input_ready_emitted",
    "replay_execution_allowed",
    "replay_evidence_bundle_created",
    "replay_decision_created",
    "replay_decision_freeze_created",
    "forward_labels_created",
    "future_labels_joined",
    "training_dataset_created",
    "metric_computation_performed",
    "signal_score_implemented",
    "signal_score_input_authorized",
    "model_training_performed",
    "active_weights_created",
    "active_thresholds_created",
    "stock_profile_validation_created",
    "paper_validation_created",
    "real_buy_review_eligible",
    "buy_review_allowed",
    "strategy_performance_validated",
    "current_candidates_created",
    "snapshots_created",
    "signal_semantics_mutated",
    "broker_api_called",
    "order_placed",
    "message_sent",
    "external_api_called",
    "llm_api_called",
    "trading_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]

ARTIFACT_FILENAMES = {
    "metadata": "metadata.json",
    "report": "metadata_reference_following_report.md",
    "package_manifest_inspection": "package_manifest_inspection.csv",
    "metadata_reference_inspection": "metadata_reference_inspection.csv",
    "metadata_path_guard": "metadata_path_guard.csv",
    "forbidden_data_reference": "forbidden_data_reference.csv",
    "available_time_metadata_inspection": "available_time_metadata_inspection.csv",
    "source_hash_revision_metadata_inspection": "source_hash_revision_metadata_inspection.csv",
    "reviewer_quality_limitation_metadata_inspection": "reviewer_quality_limitation_metadata_inspection.csv",
    "forbidden_downstream_flags": "forbidden_downstream_flags.json",
    "limitations": "limitations.md",
}

NETWORK_PREFIXES = ("http://", "https://", "ftp://", "s3://", "gs://", "oss://", "file://")
PROTECTED_PATH_PAIRS = {("data", "raw"), ("data", "processed"), ("data", "cache"), ("docs", "project_sources")}
PROTECTED_PATH_TOKENS = ("secrets", "auth", "token", "credential", "key")


def metadata_reference_following_statuses() -> list[str]:
    return [
        STATUS_NO_INPUT,
        STATUS_DECLARED_REPORT_ONLY,
        STATUS_FOLLOWED_REPORT_ONLY,
        STATUS_BLOCKED_BY_PATH_GUARD,
        STATUS_BLOCKED_BY_FORBIDDEN_DATA_REFERENCE,
        STATUS_BLOCKED_BY_MALFORMED_METADATA,
        STATUS_BLOCKED_BY_MISSING_REQUIRED_METADATA,
        STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
        STATUS_BLOCKED_BY_METADATA_SCHEMA,
        STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
        STATUS_WARN_REVIEW_REQUIRED,
    ]


def run_metadata_reference_following(
    *,
    output_root: Path | str,
    package_manifest_path: Path | str | None = None,
    allowed_manifest_roots: Sequence[Path | str] | None = None,
    inspection_level: str = INSPECTION_LEVEL_NO_INPUT,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Run report-only metadata-reference-following diagnostics and write artifacts."""

    output_root_path = _validate_output_root(Path(output_root or DEFAULT_OUTPUT_ROOT))
    context = _evaluate_input(
        package_manifest_path=package_manifest_path,
        allowed_manifest_roots=allowed_manifest_roots,
        inspection_level=inspection_level,
    )
    safe_run_id = run_id or _stable_run_id(context)
    artifact_path = output_root_path / safe_run_id
    artifact_paths = {"artifact_dir": artifact_path}
    artifact_paths.update({key: artifact_path / name for key, name in ARTIFACT_FILENAMES.items()})
    _validate_artifact_paths(artifact_path, artifact_paths)

    result = _result_payload(context=context, run_id=safe_run_id, artifact_path=artifact_path, artifact_paths=artifact_paths)
    _write_artifacts(result, artifact_paths)
    return result


def _evaluate_input(
    *,
    package_manifest_path: Path | str | None,
    allowed_manifest_roots: Sequence[Path | str] | None,
    inspection_level: str,
) -> dict[str, Any]:
    if inspection_level not in INSPECTION_LEVELS:
        return _blocked_context(
            inspection_level=inspection_level,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            blocker_reasons=[f"unsupported inspection_level: {inspection_level}"],
        )

    if inspection_level == INSPECTION_LEVEL_NO_INPUT:
        if package_manifest_path is not None:
            return _blocked_context(
                inspection_level=inspection_level,
                runtime_status=STATUS_BLOCKED_BY_PATH_GUARD,
                blocker_reasons=["package_manifest_path is rejected in no-input synthetic declarations mode"],
            )
        return _base_context(
            inspection_level=inspection_level,
            runtime_status=STATUS_NO_INPUT,
            health_status="PASS",
            real_manifest_read=False,
        )

    manifest_check = _check_manifest_path(package_manifest_path, allowed_manifest_roots)
    if manifest_check["blocked"]:
        return _blocked_context(
            inspection_level=inspection_level,
            runtime_status=manifest_check["runtime_status"],
            blocker_reasons=list(manifest_check["reasons"]),
            path_guard_rows=list(manifest_check["path_guard_rows"]),
        )

    manifest_path = manifest_check["path"]
    assert isinstance(manifest_path, Path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _blocked_context(
            inspection_level=inspection_level,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            blocker_reasons=[f"malformed top-level manifest JSON: {exc.msg}"],
            real_manifest_read=True,
        )
    if not isinstance(manifest, dict):
        return _blocked_context(
            inspection_level=inspection_level,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            blocker_reasons=["top-level package manifest must be a JSON object"],
            real_manifest_read=True,
        )

    manifest_context = _validate_manifest_schema(manifest, inspection_level)
    if manifest_context["blocked"]:
        manifest_context["real_manifest_read"] = True
        return manifest_context

    refs = _normalized_references(manifest["metadata_references"], manifest_path=manifest_path, allowed_roots=allowed_manifest_roots)
    context = _base_context(
        inspection_level=inspection_level,
        runtime_status=STATUS_DECLARED_REPORT_ONLY,
        health_status="PASS",
        real_manifest_read=True,
        manifest=manifest,
        metadata_reference_inspection=refs,
        metadata_path_guard=manifest_check["path_guard_rows"],
    )

    context["references_declared"] = bool(refs)
    context["path_guard_blocker_count"] = sum(1 for row in refs if row["path_guard_status"] == "BLOCK")
    context["forbidden_data_references_count"] = sum(1 for row in refs if row["forbidden_data_reference"])
    context["manifest_schema_blocker_count"] = sum(1 for row in refs if row["manifest_schema_blocker"])
    context["metadata_path_guard"].extend(_path_guard_rows_from_refs(refs))
    context["forbidden_data_reference"].extend([row for row in refs if row["forbidden_data_reference"]])

    if context["forbidden_data_references_count"]:
        return _finish_blocked(context, STATUS_BLOCKED_BY_FORBIDDEN_DATA_REFERENCE, "forbidden data reference declared")
    if context["path_guard_blocker_count"]:
        return _finish_blocked(context, STATUS_BLOCKED_BY_PATH_GUARD, "metadata reference failed path guard")
    if context["manifest_schema_blocker_count"]:
        return _finish_blocked(context, STATUS_BLOCKED_BY_MANIFEST_SCHEMA, "metadata reference declaration failed schema guard")

    if inspection_level in {INSPECTION_LEVEL_EXPLICIT_MANIFEST_METADATA_ONLY, INSPECTION_LEVEL_DECLARED_ONLY}:
        return context

    followed = _follow_metadata_references(refs)
    _merge_followed_context(context, followed)
    if context["path_guard_blocker_count"]:
        return _finish_blocked(context, STATUS_BLOCKED_BY_PATH_GUARD, "metadata file path guard failed")
    if context["metadata_schema_blocker_count"]:
        return _finish_blocked(context, STATUS_BLOCKED_BY_METADATA_SCHEMA, "metadata schema blocker")
    if context["available_time_metadata_blocker_count"] or context["source_hash_revision_metadata_blocker_count"]:
        return _finish_blocked(context, STATUS_BLOCKED_BY_METADATA_SCHEMA, "syntactic metadata blocker")
    if context["reviewer_quality_metadata_blocker_count"]:
        return _finish_blocked(context, STATUS_BLOCKED_BY_METADATA_SCHEMA, "reviewer/quality metadata blocker")
    if context["missing_required_metadata_count"]:
        return _finish_blocked(context, STATUS_BLOCKED_BY_MISSING_REQUIRED_METADATA, "required metadata reference missing")
    if context["metadata_malformed_count"]:
        return _finish_blocked(context, STATUS_BLOCKED_BY_MALFORMED_METADATA, "metadata JSON malformed")
    if context["limitation_warning_count"] or context["missing_optional_metadata_count"]:
        context["runtime_status"] = STATUS_WARN_REVIEW_REQUIRED
        context["health_status"] = "WARN"
        return context

    context["runtime_status"] = STATUS_FOLLOWED_REPORT_ONLY
    context["health_status"] = "PASS"
    context["references_followed"] = context["metadata_files_followed_count"] > 0
    return context


def _validate_manifest_schema(manifest: dict[str, Any], inspection_level: str) -> dict[str, Any]:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    blockers: list[str] = []
    if missing:
        blockers.append("top-level manifest missing required fields: " + ", ".join(missing))
    if manifest.get("report_only") is not True or manifest.get("diagnostic_only") is not True:
        blockers.append("report_only and diagnostic_only must be true")
    if not isinstance(manifest.get("metadata_references"), list):
        blockers.append("metadata_references must be a list")
    if len(manifest.get("metadata_references") or []) > MAX_REFERENCE_COUNT:
        blockers.append("metadata_references exceeds reference count cap")
    flags = manifest.get("forbidden_downstream_flags")
    if not isinstance(flags, dict):
        blockers.append("forbidden_downstream_flags must be an object")
    else:
        unsafe_flags = [flag for flag in REQUIRED_FALSE_FLAGS if bool(flags.get(flag, False)) is not False]
        if unsafe_flags:
            return _blocked_context(
                inspection_level=inspection_level,
                runtime_status=STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
                blocker_reasons=["forbidden downstream flags must remain false: " + ", ".join(unsafe_flags)],
                real_manifest_read=True,
                manifest=manifest,
            )
    if blockers:
        return _blocked_context(
            inspection_level=inspection_level,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            blocker_reasons=blockers,
            real_manifest_read=True,
            manifest=manifest,
            manifest_schema_blocker_count=len(blockers),
        )
    return {"blocked": False}


def _normalized_references(
    references: list[Any], *, manifest_path: Path, allowed_roots: Sequence[Path | str] | None
) -> list[dict[str, Any]]:
    rows = []
    for index, ref in enumerate(references):
        row = _normalize_reference(ref, index=index, manifest_path=manifest_path, allowed_roots=allowed_roots)
        rows.append(row)
    return sorted(rows, key=lambda row: (row["reference_type"], row["reference_name"], row["resolved_path"]))


def _normalize_reference(
    ref: Any, *, index: int, manifest_path: Path, allowed_roots: Sequence[Path | str] | None
) -> dict[str, Any]:
    if not isinstance(ref, dict):
        return _reference_row(index=index, manifest_schema_blocker=True, issue_code="REFERENCE_NOT_OBJECT")
    missing = [field for field in REQUIRED_REFERENCE_FIELDS if field not in ref]
    reference_type = str(ref.get("reference_type", ""))
    reference_name = str(ref.get("reference_name", f"reference-{index:03d}"))
    path_text = str(ref.get("path", ""))
    required = bool(ref.get("required", False))
    expected_schema_version = str(ref.get("expected_schema_version", ""))
    forbidden_data_reference = _is_forbidden_data_reference(reference_type, path_text)
    path_guard = _guard_reference_path(path_text, manifest_path=manifest_path, allowed_roots=allowed_roots)
    allowed_type = reference_type in ALLOWED_METADATA_REFERENCE_TYPES
    declared_blocked_type = reference_type in DECLARED_ONLY_OR_BLOCKED_REFERENCE_TYPES
    manifest_schema_blocker = bool(missing) or (not allowed_type and not declared_blocked_type)
    if declared_blocked_type:
        forbidden_data_reference = True
    return _reference_row(
        index=index,
        reference_type=reference_type,
        reference_name=reference_name,
        path_text=path_text,
        resolved_path=str(path_guard.get("resolved_path", "")),
        required=required,
        expected_schema_version=expected_schema_version,
        declared_only=bool(ref.get("declared_only", False)),
        forbidden_data_reference=forbidden_data_reference,
        path_guard_status=path_guard["status"],
        path_guard_reason=path_guard["reason"],
        manifest_schema_blocker=manifest_schema_blocker,
        issue_code=_reference_issue_code(
            missing=missing,
            allowed_type=allowed_type,
            declared_blocked_type=declared_blocked_type,
            forbidden_data_reference=forbidden_data_reference,
            path_guard_status=path_guard["status"],
        ),
    )


def _reference_row(
    *,
    index: int,
    reference_type: str = "",
    reference_name: str = "",
    path_text: str = "",
    resolved_path: str = "",
    required: bool = False,
    expected_schema_version: str = "",
    declared_only: bool = False,
    forbidden_data_reference: bool = False,
    path_guard_status: str = "PASS",
    path_guard_reason: str = "",
    manifest_schema_blocker: bool = False,
    issue_code: str = "REFERENCE_DECLARED",
) -> dict[str, Any]:
    return {
        "reference_index": index,
        "reference_type": reference_type,
        "reference_name": reference_name,
        "path": path_text,
        "resolved_path": resolved_path,
        "required": required,
        "expected_schema_version": expected_schema_version,
        "declared_only": declared_only,
        "reference_followed": False,
        "metadata_read": False,
        "forbidden_data_reference": forbidden_data_reference,
        "path_guard_status": path_guard_status,
        "path_guard_reason": path_guard_reason,
        "manifest_schema_blocker": manifest_schema_blocker,
        "metadata_schema_blocker": False,
        "missing_required_metadata": False,
        "missing_optional_metadata": False,
        "malformed_metadata": False,
        "issue_code": issue_code,
    }


def _reference_issue_code(
    *,
    missing: list[str],
    allowed_type: bool,
    declared_blocked_type: bool,
    forbidden_data_reference: bool,
    path_guard_status: str,
) -> str:
    if missing:
        return "REFERENCE_SCHEMA_MISSING_FIELDS"
    if forbidden_data_reference or declared_blocked_type:
        return "FORBIDDEN_DATA_REFERENCE"
    if not allowed_type:
        return "UNKNOWN_REFERENCE_TYPE"
    if path_guard_status == "BLOCK":
        return "PATH_GUARD_BLOCKED"
    return "REFERENCE_DECLARED"


def _follow_metadata_references(refs: list[dict[str, Any]]) -> dict[str, Any]:
    followed_count = 0
    output = {
        "metadata_reference_inspection": [],
        "available_time_metadata_inspection": [],
        "source_hash_revision_metadata_inspection": [],
        "reviewer_quality_limitation_metadata_inspection": [],
        "metadata_files_followed_count": 0,
        "metadata_malformed_count": 0,
        "missing_required_metadata_count": 0,
        "missing_optional_metadata_count": 0,
        "metadata_schema_blocker_count": 0,
        "available_time_metadata_blocker_count": 0,
        "source_hash_revision_metadata_blocker_count": 0,
        "reviewer_quality_metadata_blocker_count": 0,
        "limitation_warning_count": 0,
        "path_guard_blocker_count": 0,
    }
    for row in refs:
        followed_row = dict(row)
        path = Path(row["resolved_path"])
        if followed_count >= MAX_FOLLOWED_METADATA_FILES:
            followed_row["metadata_schema_blocker"] = True
            followed_row["issue_code"] = "FOLLOWED_METADATA_FILE_COUNT_CAP_EXCEEDED"
            output["metadata_schema_blocker_count"] += 1
            output["metadata_reference_inspection"].append(followed_row)
            continue
        if not path.exists() or not path.is_file():
            if row["required"]:
                followed_row["missing_required_metadata"] = True
                followed_row["issue_code"] = "REQUIRED_METADATA_MISSING"
                output["missing_required_metadata_count"] += 1
            else:
                followed_row["missing_optional_metadata"] = True
                followed_row["issue_code"] = "OPTIONAL_METADATA_MISSING"
                output["missing_optional_metadata_count"] += 1
            output["metadata_reference_inspection"].append(followed_row)
            continue
        real_path = path.resolve(strict=True)
        if str(real_path) != row["resolved_path"]:
            followed_row["path_guard_status"] = "BLOCK"
            followed_row["path_guard_reason"] = "symlink escape or resolved-path mismatch rejected"
            followed_row["issue_code"] = "SYMLINK_ESCAPE_REJECTED"
            output["path_guard_blocker_count"] += 1
            output["metadata_reference_inspection"].append(followed_row)
            continue
        if path.stat().st_size > MAX_METADATA_BYTES:
            followed_row["path_guard_status"] = "BLOCK"
            followed_row["path_guard_reason"] = "metadata JSON size cap exceeded"
            followed_row["issue_code"] = "METADATA_SIZE_CAP_EXCEEDED"
            output["path_guard_blocker_count"] += 1
            output["metadata_reference_inspection"].append(followed_row)
            continue
        try:
            metadata = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            followed_row["malformed_metadata"] = True
            followed_row["issue_code"] = "MALFORMED_METADATA_JSON"
            output["metadata_malformed_count"] += 1
            output["metadata_reference_inspection"].append(followed_row)
            continue
        followed_count += 1
        followed_row["reference_followed"] = True
        followed_row["metadata_read"] = True
        if not isinstance(metadata, dict):
            followed_row["metadata_schema_blocker"] = True
            followed_row["issue_code"] = "METADATA_NOT_OBJECT"
            output["metadata_schema_blocker_count"] += 1
        elif "metadata_references" in metadata:
            followed_row["metadata_schema_blocker"] = True
            followed_row["issue_code"] = "REFERENCE_DEPTH_GREATER_THAN_ONE"
            output["metadata_schema_blocker_count"] += 1
        elif row["expected_schema_version"] and metadata.get("schema_version") != row["expected_schema_version"]:
            followed_row["issue_code"] = "UNEXPECTED_SCHEMA_VERSION_REVIEW_REQUIRED"
            output["limitation_warning_count"] += 1
        else:
            followed_row["issue_code"] = "METADATA_FOLLOWED_REPORT_ONLY"
        _append_metadata_family_rows(row, metadata if isinstance(metadata, dict) else {}, output)
        output["metadata_reference_inspection"].append(followed_row)
    output["metadata_files_followed_count"] = followed_count
    return output


def _append_metadata_family_rows(row: dict[str, Any], metadata: dict[str, Any], output: dict[str, Any]) -> None:
    reference_type = row["reference_type"]
    if reference_type == "available_time_manifest_ref":
        value = metadata.get("available_time")
        valid = _is_iso_timestamp(value)
        output["available_time_metadata_inspection"].append(
            {
                "reference_name": row["reference_name"],
                "field_name": "available_time",
                "field_present": bool(value),
                "timestamp_format_valid": valid,
                "syntactic_only": True,
                "pit_admissibility_validated": False,
                "blocker": not valid,
            }
        )
        if not valid:
            output["available_time_metadata_blocker_count"] += 1
    if reference_type == "source_hash_revision_manifest_ref":
        for field_name in ["source_hash", "revision_id"]:
            present = bool(metadata.get(field_name))
            output["source_hash_revision_metadata_inspection"].append(
                {
                    "reference_name": row["reference_name"],
                    "field_name": field_name,
                    "field_present": present,
                    "syntactic_only": True,
                    "external_source_validated": False,
                    "blocker": not present,
                }
            )
            if not present:
                output["source_hash_revision_metadata_blocker_count"] += 1
    if reference_type in {
        "reviewer_attestation_manifest_ref",
        "quality_review_manifest_ref",
        "limitation_manifest_ref",
        "forbidden_downstream_flags_ref",
    }:
        blocker = False
        warning = False
        if reference_type == "reviewer_attestation_manifest_ref":
            blocker = not bool(metadata.get("reviewer_id"))
        elif reference_type == "quality_review_manifest_ref":
            blocker = metadata.get("quality_status") in {"failed", "blocked", ""}
        elif reference_type == "limitation_manifest_ref":
            warning = not bool(metadata.get("limitation_note"))
        elif reference_type == "forbidden_downstream_flags_ref":
            flags = metadata.get("forbidden_downstream_flags", {})
            blocker = not isinstance(flags, dict) or any(bool(flags.get(flag, False)) for flag in REQUIRED_FALSE_FLAGS)
        output["reviewer_quality_limitation_metadata_inspection"].append(
            {
                "reference_name": row["reference_name"],
                "reference_type": reference_type,
                "syntactic_only": True,
                "reviewer_authority_validated": False,
                "blocker": blocker,
                "warning": warning,
            }
        )
        if blocker:
            output["reviewer_quality_metadata_blocker_count"] += 1
        if warning:
            output["limitation_warning_count"] += 1


def _merge_followed_context(context: dict[str, Any], followed: dict[str, Any]) -> None:
    for key, value in followed.items():
        if isinstance(value, list):
            context[key] = value
        else:
            context[key] = context.get(key, 0) + value


def _base_context(
    *,
    inspection_level: str,
    runtime_status: str,
    health_status: str,
    real_manifest_read: bool,
    manifest: dict[str, Any] | None = None,
    metadata_reference_inspection: list[dict[str, Any]] | None = None,
    metadata_path_guard: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "blocked": False,
        "inspection_level": inspection_level,
        "runtime_status": runtime_status,
        "health_status": health_status,
        "real_manifest_read": real_manifest_read,
        "manifest": manifest or {},
        "references_declared": False,
        "references_followed": False,
        "metadata_files_followed_count": 0,
        "forbidden_data_references_count": 0,
        "path_guard_blocker_count": 0,
        "manifest_schema_blocker_count": 0,
        "metadata_schema_blocker_count": 0,
        "available_time_metadata_blocker_count": 0,
        "source_hash_revision_metadata_blocker_count": 0,
        "reviewer_quality_metadata_blocker_count": 0,
        "limitation_warning_count": 0,
        "missing_required_metadata_count": 0,
        "missing_optional_metadata_count": 0,
        "metadata_malformed_count": 0,
        "blocker_reasons": [],
        "metadata_reference_inspection": metadata_reference_inspection or [],
        "metadata_path_guard": metadata_path_guard or [],
        "forbidden_data_reference": [],
        "available_time_metadata_inspection": [],
        "source_hash_revision_metadata_inspection": [],
        "reviewer_quality_limitation_metadata_inspection": [],
    }


def _blocked_context(
    *,
    inspection_level: str,
    runtime_status: str,
    blocker_reasons: list[str],
    real_manifest_read: bool = False,
    manifest: dict[str, Any] | None = None,
    path_guard_rows: list[dict[str, Any]] | None = None,
    manifest_schema_blocker_count: int = 0,
) -> dict[str, Any]:
    context = _base_context(
        inspection_level=inspection_level,
        runtime_status=runtime_status,
        health_status="FAIL",
        real_manifest_read=real_manifest_read,
        manifest=manifest,
        metadata_path_guard=path_guard_rows,
    )
    context["blocked"] = True
    context["blocker_reasons"] = blocker_reasons
    context["manifest_schema_blocker_count"] = manifest_schema_blocker_count
    if runtime_status == STATUS_BLOCKED_BY_PATH_GUARD:
        context["path_guard_blocker_count"] = max(1, len(blocker_reasons))
    return context


def _finish_blocked(context: dict[str, Any], runtime_status: str, reason: str) -> dict[str, Any]:
    context["runtime_status"] = runtime_status
    context["health_status"] = "FAIL"
    context["blocker_reasons"].append(reason)
    return context


def _check_manifest_path(
    package_manifest_path: Path | str | None, allowed_manifest_roots: Sequence[Path | str] | None
) -> dict[str, Any]:
    if package_manifest_path is None:
        return _blocked_path_result("package_manifest_path is required for explicit metadata inspection")
    if not allowed_manifest_roots:
        return _blocked_path_result("allowed_manifest_roots must be explicit")
    raw_path = str(package_manifest_path)
    path_guard = _guard_path_text(raw_path)
    if path_guard:
        return _blocked_path_result(path_guard)
    path = Path(package_manifest_path)
    if path.suffix.lower() != ".json":
        return _blocked_path_result("package_manifest_path must be a JSON metadata file")
    allowed_roots = _resolved_roots(allowed_manifest_roots)
    resolved = path.resolve(strict=False)
    if not any(_is_relative_to(resolved, root) for root in allowed_roots):
        return _blocked_path_result("package_manifest_path must be under an explicit allowed_manifest_root")
    if not path.exists() or not path.is_file():
        return _blocked_path_result("package_manifest_path must be an existing regular file")
    real_resolved = path.resolve(strict=True)
    if real_resolved != resolved or not any(_is_relative_to(real_resolved, root) for root in allowed_roots):
        return _blocked_path_result("package_manifest_path symlink escape is rejected")
    if path.stat().st_size > MAX_METADATA_BYTES:
        return _blocked_path_result("package_manifest_path exceeds metadata JSON size cap")
    return {
        "blocked": False,
        "path": path,
        "path_guard_rows": [
            {
                "path": str(path),
                "resolved_path": str(real_resolved),
                "guard_status": "PASS",
                "reason": "top-level manifest path passed guard",
            }
        ],
    }


def _guard_reference_path(
    path_text: str, *, manifest_path: Path, allowed_roots: Sequence[Path | str] | None
) -> dict[str, Any]:
    reason = _guard_path_text(path_text)
    if reason:
        return {"status": "BLOCK", "reason": reason, "resolved_path": ""}
    if Path(path_text).suffix.lower() != ".json":
        return {"status": "BLOCK", "reason": "metadata reference must point to a JSON metadata file", "resolved_path": ""}
    raw_path = Path(path_text)
    candidate = raw_path if raw_path.is_absolute() else manifest_path.parent / raw_path
    resolved = candidate.resolve(strict=False)
    allowed_roots = _resolved_roots(allowed_roots)
    if not any(_is_relative_to(resolved, root) for root in allowed_roots):
        return {"status": "BLOCK", "reason": "metadata reference must stay under explicit allowed roots", "resolved_path": str(resolved)}
    return {"status": "PASS", "reason": "metadata reference path passed guard", "resolved_path": str(resolved)}


def _guard_path_text(path_text: str) -> str:
    lowered = path_text.lower()
    if not path_text:
        return "path is required"
    if lowered.startswith(NETWORK_PREFIXES):
        return "URL paths are rejected"
    parts = [part.lower() for part in Path(path_text).parts]
    if ".." in parts:
        return "path traversal is rejected"
    if any(part == ".env" or part.startswith(".env") or part.startswith(".") for part in parts):
        return "hidden or environment paths are rejected"
    if any((first, second) in PROTECTED_PATH_PAIRS for first, second in zip(parts, parts[1:])):
        return "protected repository path is rejected"
    if any(any(token in part for token in PROTECTED_PATH_TOKENS) for part in parts):
        return "secret/auth/token/credential/key path is rejected"
    return ""


def _blocked_path_result(reason: str) -> dict[str, Any]:
    return {
        "blocked": True,
        "runtime_status": STATUS_BLOCKED_BY_PATH_GUARD,
        "reasons": [reason],
        "path_guard_rows": [{"path": "", "resolved_path": "", "guard_status": "BLOCK", "reason": reason}],
    }


def _is_forbidden_data_reference(reference_type: str, path_text: str) -> bool:
    if reference_type in DECLARED_ONLY_OR_BLOCKED_REFERENCE_TYPES:
        return True
    return Path(path_text).suffix.lower() in FORBIDDEN_DATA_EXTENSIONS


def _path_guard_rows_from_refs(refs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "reference_type": row["reference_type"],
            "reference_name": row["reference_name"],
            "path": row["path"],
            "resolved_path": row["resolved_path"],
            "guard_status": row["path_guard_status"],
            "reason": row["path_guard_reason"],
        }
        for row in refs
    ]


def _result_payload(
    *, context: dict[str, Any], run_id: str, artifact_path: Path, artifact_paths: dict[str, Path]
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "run_id": run_id,
        "created_at": CREATED_AT,
        "workflow_name": WORKFLOW_NAME,
        "runtime_status": context["runtime_status"],
        "status": context["runtime_status"],
        "workflow_stage": WORKFLOW_STAGE,
        "health_status": context["health_status"],
        "report_only": True,
        "diagnostic_only": True,
        "input_mode": context["inspection_level"],
        "inspection_level": context["inspection_level"],
        "csv_read_level": CSV_READ_LEVEL_NONE,
        "real_manifest_read": context["real_manifest_read"],
        "references_declared": context["references_declared"],
        "references_followed": context["references_followed"],
        "metadata_files_followed_count": context["metadata_files_followed_count"],
        "forbidden_data_references_count": context["forbidden_data_references_count"],
        "path_guard_blocker_count": context["path_guard_blocker_count"],
        "manifest_schema_blocker_count": context["manifest_schema_blocker_count"],
        "metadata_schema_blocker_count": context["metadata_schema_blocker_count"],
        "available_time_metadata_blocker_count": context["available_time_metadata_blocker_count"],
        "source_hash_revision_metadata_blocker_count": context["source_hash_revision_metadata_blocker_count"],
        "reviewer_quality_metadata_blocker_count": context["reviewer_quality_metadata_blocker_count"],
        "limitation_warning_count": context["limitation_warning_count"],
        "local_file_hash_computed": False,
        "external_source_validated": False,
        "pit_admissibility_validated": False,
        "real_csv_consumed": False,
        "real_reviewed_csv_package_created": False,
        "real_package_candidate_created": False,
        "active_reviewed_input_candidate_created": False,
        "real_replay_input_created": False,
        "active_replay_input": False,
        "active_replay_ready": False,
        "active_replay_input_ready_emitted": False,
        "replay_execution_allowed": False,
        "trading_allowed": False,
        "buy_review_allowed": False,
        "data_raw_written": False,
        "data_processed_written": False,
        "data_cache_written": False,
        "recommended_next_task": NEXT_BOUNDARY_DESIGN_TASK,
        "artifact_path": str(artifact_path),
        "report_path": str(artifact_paths["report"]),
        "artifact_files": {key: str(path) for key, path in artifact_paths.items() if key != "artifact_dir"},
        "blocker_reasons": list(context["blocker_reasons"]),
        "metadata_reference_inspection": list(context["metadata_reference_inspection"]),
        "metadata_path_guard": list(context["metadata_path_guard"]),
        "forbidden_data_reference": list(context["forbidden_data_reference"]),
        "available_time_metadata_inspection": list(context["available_time_metadata_inspection"]),
        "source_hash_revision_metadata_inspection": list(context["source_hash_revision_metadata_inspection"]),
        "reviewer_quality_limitation_metadata_inspection": list(context["reviewer_quality_limitation_metadata_inspection"]),
    }
    result.update({flag: False for flag in REQUIRED_FALSE_FLAGS})
    return result


def _write_artifacts(result: dict[str, Any], artifact_paths: dict[str, Path]) -> None:
    artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_json(artifact_paths["metadata"], _metadata_payload(result))
    artifact_paths["report"].write_text(_report_text(result), encoding="utf-8")
    _write_csv(artifact_paths["package_manifest_inspection"], _package_manifest_rows(result))
    _write_csv(artifact_paths["metadata_reference_inspection"], result["metadata_reference_inspection"] or [_empty_reference_row()])
    _write_csv(artifact_paths["metadata_path_guard"], result["metadata_path_guard"] or [_empty_path_guard_row()])
    _write_csv(artifact_paths["forbidden_data_reference"], result["forbidden_data_reference"] or [_empty_reference_row()])
    _write_csv(
        artifact_paths["available_time_metadata_inspection"],
        result["available_time_metadata_inspection"] or [_empty_family_row("available_time")],
    )
    _write_csv(
        artifact_paths["source_hash_revision_metadata_inspection"],
        result["source_hash_revision_metadata_inspection"] or [_empty_family_row("source_hash_revision")],
    )
    _write_csv(
        artifact_paths["reviewer_quality_limitation_metadata_inspection"],
        result["reviewer_quality_limitation_metadata_inspection"] or [_empty_family_row("reviewer_quality_limitation")],
    )
    _write_json(artifact_paths["forbidden_downstream_flags"], {flag: False for flag in REQUIRED_FALSE_FLAGS})
    artifact_paths["limitations"].write_text(_limitations_text(), encoding="utf-8")


def _metadata_payload(result: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "run_id",
        "created_at",
        "runtime_status",
        "workflow_stage",
        "health_status",
        "report_only",
        "diagnostic_only",
        "input_mode",
        "inspection_level",
        "csv_read_level",
        "real_manifest_read",
        "references_declared",
        "references_followed",
        "metadata_files_followed_count",
        "forbidden_data_references_count",
        "path_guard_blocker_count",
        "manifest_schema_blocker_count",
        "metadata_schema_blocker_count",
        "available_time_metadata_blocker_count",
        "source_hash_revision_metadata_blocker_count",
        "reviewer_quality_metadata_blocker_count",
        "limitation_warning_count",
        "local_file_hash_computed",
        "external_source_validated",
        "pit_admissibility_validated",
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
        "recommended_next_task",
    ]
    return {key: result[key] for key in keys}


def _package_manifest_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "run_id": result["run_id"],
            "runtime_status": result["runtime_status"],
            "inspection_level": result["inspection_level"],
            "csv_read_level": result["csv_read_level"],
            "real_manifest_read": result["real_manifest_read"],
            "references_declared": result["references_declared"],
            "references_followed": result["references_followed"],
            "report_only": result["report_only"],
            "diagnostic_only": result["diagnostic_only"],
        }
    ]


def _report_text(result: dict[str, Any]) -> str:
    return f"""# Tiny PIT Metadata-Reference-Following Core

This is a report-only, diagnostic-only metadata-reference-following core.

- Run id: `{result["run_id"]}`
- Runtime status: `{result["runtime_status"]}`
- Health: `{result["health_status"]}`
- Inspection level: `{result["inspection_level"]}`
- CSV read level: `{result["csv_read_level"]}`
- Real manifest read: `{str(result["real_manifest_read"]).lower()}`
- References followed: `{str(result["references_followed"]).lower()}`
- Metadata files followed: `{result["metadata_files_followed_count"]}`
- Local file byte hash computed: `false`
- PIT admissibility validated: `false`
- Trading allowed: `false`

The core follows only whitelisted local JSON metadata references under explicit
allowed roots. It does not open CSV/data targets, compute local file byte
hashes, create real package candidates, create active inputs, emit replay
readiness, run replay, create labels/training/model/stock_profile/paper
artifacts, or enable buy-review/trading behavior.
"""


def _limitations_text() -> str:
    return (
        "# Limitations\n\n"
        "- Report-only and diagnostic-only metadata-reference-following core.\n"
        "- JSON metadata only under explicit allowed roots.\n"
        "- CSV read level remains CSV_READ_NONE.\n"
        "- No CSV headers, row counts, content reads, or local file byte hashes are performed.\n"
        "- Syntactic metadata checks do not validate PIT admissibility, external source truth, or reviewer authority.\n"
        "- No real package candidate, active reviewed input, replay input, labels, training, stock_profile, paper, buy-review, or trading behavior is created.\n"
    )


def _empty_reference_row() -> dict[str, Any]:
    return _reference_row(index=0, issue_code="NO_REFERENCE_ROWS")


def _empty_path_guard_row() -> dict[str, Any]:
    return {"path": "", "resolved_path": "", "guard_status": "PASS", "reason": "no path guard rows"}


def _empty_family_row(family: str) -> dict[str, Any]:
    return {"metadata_family": family, "row_present": False, "syntactic_only": True, "blocker": False}


def _validate_output_root(output_root: Path) -> Path:
    if _guard_path_text(str(output_root)):
        raise ValueError(f"Protected output root is not allowed: {output_root}")
    return output_root.resolve(strict=False)


def _validate_artifact_paths(root: Path, artifact_paths: dict[str, Path]) -> None:
    resolved_root = root.resolve(strict=False)
    for key, path in artifact_paths.items():
        if key == "artifact_dir":
            continue
        if not _is_relative_to(path.resolve(strict=False), resolved_root):
            raise ValueError(f"artifact path escapes output root: {path}")


def _stable_run_id(context: dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "inspection_level": context["inspection_level"],
            "runtime_status": context["runtime_status"],
            "health_status": context["health_status"],
            "references_declared": context["references_declared"],
            "references_followed": context["references_followed"],
            "metadata_files_followed_count": context["metadata_files_followed_count"],
            "blocker_reasons": context["blocker_reasons"],
        },
        sort_keys=True,
    )
    return uuid.uuid5(uuid.NAMESPACE_URL, payload).hex[:12]


def _is_iso_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _resolved_roots(allowed_manifest_roots: Sequence[Path | str] | None) -> list[Path]:
    return [Path(root).resolve(strict=False) for root in (allowed_manifest_roots or [])]


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
