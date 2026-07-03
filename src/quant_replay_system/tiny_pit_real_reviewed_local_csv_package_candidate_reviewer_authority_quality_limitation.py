"""Reviewer authority / quality / limitation metadata boundary for Tiny PIT.

This module is report-only and diagnostic-only. It checks JSON metadata
presence, schema shape, reviewer role vocabulary, declared quality status
vocabulary, limitation severity/categories, permission/legal blocker fields,
disclosure boundaries, and forbidden downstream flags. It does not validate
reviewer authority, promote quality to package readiness, score source
reliability, open CSV/source artifacts, run replay, or enable buy-review/trading.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Sequence


STATUS_NO_INPUT = "NO_REVIEWER_QUALITY_LIMITATION_INPUT"
STATUS_METADATA_PRESENT = "REVIEWER_QUALITY_LIMITATION_METADATA_PRESENT_REPORT_ONLY"
STATUS_WARN_LIMITATIONS = "REVIEWER_QUALITY_LIMITATION_WARN_LIMITATIONS_PRESENT"
STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG = (
    "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_MISSING_ALLOW_FLAG"
)
STATUS_BLOCKED_BY_MANIFEST_SCHEMA = "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_MANIFEST_SCHEMA"
STATUS_BLOCKED_BY_PATH_GUARD = "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_PATH_GUARD"
STATUS_BLOCKED_BY_MISSING_REVIEWER_METADATA = (
    "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_MISSING_REVIEWER_METADATA"
)
STATUS_BLOCKED_BY_UNSUPPORTED_REVIEWER_ROLE = (
    "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_UNSUPPORTED_REVIEWER_ROLE"
)
STATUS_BLOCKED_BY_MISSING_QUALITY_STATUS = (
    "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_MISSING_QUALITY_STATUS"
)
STATUS_BLOCKED_BY_BLOCKING_LIMITATION = (
    "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_BLOCKING_LIMITATION"
)
STATUS_BLOCKED_BY_FORBIDDEN_PERMISSION = (
    "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_FORBIDDEN_PERMISSION"
)
STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM = (
    "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
)
STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA = (
    "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_UNSAFE_REFERENCE_METADATA"
)

WORKFLOW_NAME = (
    "tiny_pit_real_reviewed_local_csv_package_candidate_reviewer_authority_"
    "quality_limitation"
)
WORKFLOW_STAGE = (
    "TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_REVIEWER_AUTHORITY_"
    "QUALITY_LIMITATION_CORE_CREATED_REPORT_ONLY"
)
CREATED_AT = "2026-07-03T00:00:00Z"
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Reviewer Authority Quality "
    "Limitation Artifact Views Report-Only v0.1"
)

REVIEWER_AUTHORITY_NONE = "REVIEWER_AUTHORITY_NONE"
QUALITY_STATUS_NONE = "QUALITY_STATUS_NONE"
LIMITATION_REVIEW_NONE = "LIMITATION_REVIEW_NONE"
PERMISSION_REVIEW_NONE = "PERMISSION_REVIEW_NONE"
PACKAGE_PROMOTION_NONE = "PACKAGE_PROMOTION_NONE"
REVIEWER_METADATA_PRESENT_ONLY = "REVIEWER_METADATA_PRESENT_ONLY"
QUALITY_METADATA_PRESENT_ONLY = "QUALITY_METADATA_PRESENT_ONLY"
LIMITATION_METADATA_PRESENT_ONLY = "LIMITATION_METADATA_PRESENT_ONLY"
PERMISSION_CLASS_METADATA_PRESENT_ONLY = "PERMISSION_CLASS_METADATA_PRESENT_ONLY"
REVIEWER_QUALITY_LIMITATION_METADATA_PRESENT_ONLY = (
    "REVIEWER_QUALITY_LIMITATION_METADATA_PRESENT_ONLY"
)
MAX_MANIFEST_SIZE_BYTES = 1_048_576
REVIEWER_ID_PREVIEW_CHARS = 12

ARTIFACT_FILENAMES = {
    "metadata": "metadata.json",
    "report": "reviewer_quality_limitation_report.md",
    "limitations": "limitations.md",
    "issues": "issues.csv",
    "summary": "reviewer_quality_limitation_summary.csv",
    "forbidden_downstream_flags": "forbidden_downstream_flags.json",
}

REQUIRED_MANIFEST_FIELDS = [
    "package_id",
    "package_schema_version",
    "created_at",
    "prepared_by",
    "report_only",
    "diagnostic_only",
    "requested_reviewer_authority_level",
    "requested_quality_status_level",
    "requested_limitation_review_level",
    "requested_permission_review_level",
    "requested_package_promotion_level",
    "reviewer_quality_metadata_reference",
    "reviewer_policy",
    "quality_policy",
    "limitation_policy",
    "permission_policy",
    "disclosure_policy",
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
REQUIRED_REVIEWER_METADATA_FIELDS = [
    "reviewer_id_recorded",
    "reviewer_id_preview",
    "reviewer_role",
    "reviewer_type",
    "reviewer_attestation_present",
    "reviewer_authority_scope_declared",
    "reviewer_authority_validated",
    "manual_review_status",
    "quality_status",
    "quality_status_validated",
    "quality_issue_count",
    "quality_warning_count",
    "quality_blocker_count",
    "limitations_present",
    "limitation_count",
    "limitation_severity_max",
    "limitation_categories",
    "unresolved_limitation_count",
    "blocking_limitation_count",
    "limitation_policy",
    "assumptions_present",
    "assumption_count",
    "permission_class",
    "legality_flag",
    "permission_class_validated",
    "report_only",
    "diagnostic_only",
    "forbidden_downstream_flags",
    "limitations",
]
REVIEWER_METADATA_CORE_FIELDS = {
    "reviewer_id_recorded",
    "reviewer_id_preview",
    "reviewer_role",
    "reviewer_type",
    "reviewer_attestation_present",
    "reviewer_authority_scope_declared",
}
ALLOWED_REVIEWER_ROLES = {
    "preparer",
    "reviewer",
    "approver_declared_only",
    "owner_declared_only",
    "automated_check",
    "manual_review",
}
ALLOWED_REVIEWER_TYPES = {
    "human_declared_only",
    "automated_check",
    "mixed_declared_only",
}
ALLOWED_QUALITY_STATUSES = {
    "QUALITY_METADATA_PRESENT_ONLY",
    "QUALITY_STATUS_NEEDS_REVIEW",
    "QUALITY_STATUS_WARN_LIMITATIONS",
    "QUALITY_STATUS_BLOCKED_BY_LIMITATIONS",
    "QUALITY_STATUS_BLOCKED_BY_PERMISSION",
    "QUALITY_STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM",
    "QUALITY_STATUS_BLOCKED_BY_UNSAFE_METADATA",
}
ALLOWED_LIMITATION_SEVERITIES = {"INFO", "WARN", "BLOCKER", ""}
ALLOWED_LIMITATION_CATEGORIES = {
    "coverage_gap",
    "missing_revision",
    "missing_available_time",
    "manual_review_needed",
    "source_permission_uncertain",
    "sample_size_limited",
    "schema_assumption",
    "timezone_assumption",
    "unknown_provenance",
    "incomplete_rows",
    "known_data_quality_issue",
    "unsupported_source_type",
    "restricted_use",
    "private_or_sensitive_source",
    "downstream_forbidden",
}
PASS_COMPATIBLE_PERMISSION_CLASSES = {"public", "public_with_terms"}
FORBIDDEN_PERMISSION_CLASSES = {
    "restricted",
    "private",
    "illegal_or_do_not_use",
    "unknown",
}
ALLOWED_PERMISSION_CLASSES = PASS_COMPATIBLE_PERMISSION_CLASSES | {
    "internal_reviewed",
    *FORBIDDEN_PERMISSION_CLASSES,
}
ALLOWED_LEGALITY_FLAGS = {
    "public_confirmed",
    "terms_review_required",
    "restricted_use",
    "private_source",
    "illegal_or_do_not_use",
    "unknown",
}
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
    "trading_allowed",
    "buy_review_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]
UNSAFE_REFERENCE_TRUE_FIELDS = [
    "reviewer_authority_validated",
    "quality_status_validated",
    "permission_class_validated",
    "source_reliability_scored",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
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
    ".env",
}
PROTECTED_PATH_PAIRS = {
    ("data", "raw"),
    ("data", "processed"),
    ("data", "cache"),
    ("docs", "project_sources"),
}
NETWORK_PREFIXES = ("http://", "https://", "ftp://", "s3://", "gs://")


def reviewer_authority_quality_limitation_statuses() -> list[str]:
    return [
        STATUS_NO_INPUT,
        STATUS_METADATA_PRESENT,
        STATUS_WARN_LIMITATIONS,
        STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
        STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
        STATUS_BLOCKED_BY_PATH_GUARD,
        STATUS_BLOCKED_BY_MISSING_REVIEWER_METADATA,
        STATUS_BLOCKED_BY_UNSUPPORTED_REVIEWER_ROLE,
        STATUS_BLOCKED_BY_MISSING_QUALITY_STATUS,
        STATUS_BLOCKED_BY_BLOCKING_LIMITATION,
        STATUS_BLOCKED_BY_FORBIDDEN_PERMISSION,
        STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
        STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA,
    ]


def reviewer_authority_quality_limitation_safety_flags() -> dict[str, bool]:
    return {field: False for field in REQUIRED_FALSE_FLAGS}


def run_reviewer_authority_quality_limitation(
    *,
    output_root: str | Path,
    run_id: str | None = None,
    reviewer_quality_manifest_path: str | Path | None = None,
    reviewer_quality_metadata_path: str | Path | None = None,
    source_revision_time_metadata_path: str | Path | None = None,
    expected_hash_verification_metadata_path: str | Path | None = None,
    local_file_byte_hash_metadata_path: str | Path | None = None,
    physical_data_line_count_metadata_path: str | Path | None = None,
    allowed_manifest_roots: Sequence[str | Path] | None = None,
    reviewer_authority_level: str = REVIEWER_AUTHORITY_NONE,
    quality_status_level: str = QUALITY_STATUS_NONE,
    limitation_review_level: str = LIMITATION_REVIEW_NONE,
    permission_review_level: str = PERMISSION_REVIEW_NONE,
    package_promotion_level: str = PACKAGE_PROMOTION_NONE,
    allow_reviewer_quality_limitation_metadata: bool = False,
    max_manifest_size_bytes: int = MAX_MANIFEST_SIZE_BYTES,
) -> dict[str, Any]:
    del source_revision_time_metadata_path
    del expected_hash_verification_metadata_path
    del local_file_byte_hash_metadata_path
    del physical_data_line_count_metadata_path

    artifact_root = _validated_output_root(Path(output_root)) / (run_id or uuid.uuid4().hex[:12])
    artifact_paths = _artifact_paths(artifact_root)
    max_bytes = int(max_manifest_size_bytes)

    if reviewer_quality_manifest_path is None:
        result = _result_payload(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_NO_INPUT,
            health_status="PASS",
            reviewer_authority_level=REVIEWER_AUTHORITY_NONE,
            quality_status_level=QUALITY_STATUS_NONE,
            limitation_review_level=LIMITATION_REVIEW_NONE,
            permission_review_level=PERMISSION_REVIEW_NONE,
            package_promotion_level=PACKAGE_PROMOTION_NONE,
            issues=[],
            warnings=[],
            limitations=["No input supplied; no reviewer/quality/limitation metadata checked."],
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    expected_levels = (
        REVIEWER_METADATA_PRESENT_ONLY,
        QUALITY_METADATA_PRESENT_ONLY,
        LIMITATION_METADATA_PRESENT_ONLY,
        PERMISSION_CLASS_METADATA_PRESENT_ONLY,
        PACKAGE_PROMOTION_NONE,
    )
    if (
        reviewer_authority_level,
        quality_status_level,
        limitation_review_level,
        permission_review_level,
        package_promotion_level,
    ) != expected_levels:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            reason="Only metadata-present reviewer/quality/limitation levels are supported.",
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    if not allow_reviewer_quality_limitation_metadata:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
            reason="allow_reviewer_quality_limitation_metadata must be true.",
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    if reviewer_quality_metadata_path is None:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_MISSING_REVIEWER_METADATA,
            reason="reviewer_quality_metadata_path is required when a manifest is supplied.",
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    manifest_check = _check_input_path(reviewer_quality_manifest_path, allowed_manifest_roots)
    metadata_check = _check_input_path(reviewer_quality_metadata_path, allowed_manifest_roots)
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
            runtime_status=STATUS_BLOCKED_BY_MISSING_REVIEWER_METADATA,
            reason=metadata_error,
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

    metadata_issue, issue_status = _validate_reviewer_quality_metadata(metadata)
    if metadata_issue is not None:
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=issue_status,
            reason=metadata_issue,
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    if _has_unsafe_claim(metadata):
        result = _blocked_result(
            artifact_paths=artifact_paths,
            run_id=artifact_root.name,
            runtime_status=STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA,
            reason="Reviewer/quality metadata must not claim validation or downstream side effects.",
            max_manifest_size_bytes=max_bytes,
        )
        _write_artifacts(result)
        return result

    limitation_severity = str(metadata.get("limitation_severity_max") or "")
    permission_class = str(metadata.get("permission_class") or "")
    warnings: list[str] = []
    if permission_class == "internal_reviewed":
        warnings.append("internal_reviewed permission remains reviewer-context only.")
    if limitation_severity == "WARN":
        warnings.append("WARN limitations require human review before any future promotion.")
        runtime_status = STATUS_WARN_LIMITATIONS
        health_status = "WARN"
    elif warnings:
        runtime_status = STATUS_METADATA_PRESENT
        health_status = "WARN"
    else:
        runtime_status = STATUS_METADATA_PRESENT
        health_status = "PASS"

    result = _result_payload(
        artifact_paths=artifact_paths,
        run_id=artifact_root.name,
        runtime_status=runtime_status,
        health_status=health_status,
        reviewer_authority_level=REVIEWER_METADATA_PRESENT_ONLY,
        quality_status_level=QUALITY_METADATA_PRESENT_ONLY,
        limitation_review_level=LIMITATION_METADATA_PRESENT_ONLY,
        permission_review_level=PERMISSION_CLASS_METADATA_PRESENT_ONLY,
        package_promotion_level=PACKAGE_PROMOTION_NONE,
        issues=[],
        warnings=warnings,
        limitations=_safe_limitations(metadata),
        max_manifest_size_bytes=max_bytes,
        reviewer_metadata_present=True,
        reviewer_id_recorded=bool(metadata.get("reviewer_id_recorded")),
        reviewer_id_preview=_bounded_preview(str(metadata.get("reviewer_id_preview") or "")),
        reviewer_role=str(metadata.get("reviewer_role") or ""),
        reviewer_role_supported=True,
        reviewer_type=str(metadata.get("reviewer_type") or ""),
        reviewer_attestation_present=bool(metadata.get("reviewer_attestation_present")),
        reviewer_authority_scope_declared=bool(metadata.get("reviewer_authority_scope_declared")),
        quality_status_present=True,
        quality_status_declared=True,
        quality_issue_count=int(metadata.get("quality_issue_count") or 0),
        quality_warning_count=int(metadata.get("quality_warning_count") or 0),
        quality_blocker_count=int(metadata.get("quality_blocker_count") or 0),
        limitations_present=bool(metadata.get("limitations_present")),
        limitation_count=int(metadata.get("limitation_count") or 0),
        limitation_severity_max=limitation_severity,
        limitation_categories=list(metadata.get("limitation_categories") or []),
        unresolved_limitation_count=int(metadata.get("unresolved_limitation_count") or 0),
        blocking_limitation_count=int(metadata.get("blocking_limitation_count") or 0),
        limitations_overridden_by_reviewer=bool(
            metadata.get("limitations_overridden_by_reviewer")
        ),
        limitations_overridden_by_quality=bool(metadata.get("limitations_overridden_by_quality")),
        permission_class_present=True,
        permission_class=permission_class,
        legality_flag=str(metadata.get("legality_flag") or ""),
        restricted_use_blocked=False,
        private_source_blocked=False,
    )
    _write_artifacts(result)
    return result


def _result_payload(
    *,
    artifact_paths: dict[str, Path],
    run_id: str,
    runtime_status: str,
    health_status: str,
    reviewer_authority_level: str,
    quality_status_level: str,
    limitation_review_level: str,
    permission_review_level: str,
    package_promotion_level: str,
    issues: list[str],
    warnings: list[str],
    limitations: list[str],
    max_manifest_size_bytes: int,
    reviewer_metadata_present: bool = False,
    reviewer_id_recorded: bool = False,
    reviewer_id_preview: str = "",
    reviewer_role: str = "",
    reviewer_role_supported: bool = False,
    reviewer_type: str = "",
    reviewer_attestation_present: bool = False,
    reviewer_authority_scope_declared: bool = False,
    quality_status_present: bool = False,
    quality_status_declared: bool = False,
    quality_issue_count: int = 0,
    quality_warning_count: int = 0,
    quality_blocker_count: int = 0,
    limitations_present: bool = False,
    limitation_count: int = 0,
    limitation_severity_max: str = "",
    limitation_categories: list[str] | None = None,
    unresolved_limitation_count: int = 0,
    blocking_limitation_count: int = 0,
    limitations_overridden_by_reviewer: bool = False,
    limitations_overridden_by_quality: bool = False,
    permission_class_present: bool = False,
    permission_class: str = "",
    legality_flag: str = "",
    restricted_use_blocked: bool = False,
    private_source_blocked: bool = False,
) -> dict[str, Any]:
    issue_list = list(issues)
    warning_list = list(warnings)
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
        "reviewer_authority_level": reviewer_authority_level,
        "quality_status_level": quality_status_level,
        "limitation_review_level": limitation_review_level,
        "permission_review_level": permission_review_level,
        "package_promotion_level": package_promotion_level,
        "reviewer_metadata_present": reviewer_metadata_present,
        "reviewer_id_recorded": reviewer_id_recorded,
        "reviewer_id_preview": reviewer_id_preview,
        "reviewer_role": reviewer_role,
        "reviewer_role_supported": reviewer_role_supported,
        "reviewer_type": reviewer_type,
        "reviewer_attestation_present": reviewer_attestation_present,
        "reviewer_authority_scope_declared": reviewer_authority_scope_declared,
        "reviewer_authority_validated": False,
        "quality_status_present": quality_status_present,
        "quality_status_declared": quality_status_declared,
        "quality_status_validated": False,
        "quality_issue_count": quality_issue_count,
        "quality_warning_count": quality_warning_count,
        "quality_blocker_count": quality_blocker_count,
        "limitations_present": limitations_present,
        "limitation_count": limitation_count,
        "limitation_severity_max": limitation_severity_max,
        "limitation_categories": limitation_categories or [],
        "unresolved_limitation_count": unresolved_limitation_count,
        "blocking_limitation_count": blocking_limitation_count,
        "limitations_overridden_by_reviewer": limitations_overridden_by_reviewer,
        "limitations_overridden_by_quality": limitations_overridden_by_quality,
        "permission_class_present": permission_class_present,
        "permission_class": permission_class,
        "legality_flag": legality_flag,
        "permission_class_validated": False,
        "restricted_use_blocked": restricted_use_blocked,
        "private_source_blocked": private_source_blocked,
        "source_reliability_scored": False,
        "source_hash_validated": False,
        "revision_id_validated": False,
        "available_time_validated": False,
        "pit_admissibility_validated": False,
        "issue_count": len(issue_list),
        "warning_count": len(warning_list),
        "issues": issue_list,
        "warnings": warning_list,
        "limitations": limitations,
        "max_manifest_size_bytes": max_manifest_size_bytes,
        "recommended_next_task": NEXT_TASK,
    }
    result.update(reviewer_authority_quality_limitation_safety_flags())
    return result


def _blocked_result(
    *,
    artifact_paths: dict[str, Path],
    run_id: str,
    runtime_status: str,
    reason: str,
    max_manifest_size_bytes: int,
) -> dict[str, Any]:
    restricted = runtime_status == STATUS_BLOCKED_BY_FORBIDDEN_PERMISSION
    return _result_payload(
        artifact_paths=artifact_paths,
        run_id=run_id,
        runtime_status=runtime_status,
        health_status="FAIL",
        reviewer_authority_level=REVIEWER_AUTHORITY_NONE,
        quality_status_level=QUALITY_STATUS_NONE,
        limitation_review_level=LIMITATION_REVIEW_NONE,
        permission_review_level=PERMISSION_REVIEW_NONE,
        package_promotion_level=PACKAGE_PROMOTION_NONE,
        issues=[reason],
        warnings=[],
        limitations=["Blocked before metadata could be accepted as report-only context."],
        max_manifest_size_bytes=max_manifest_size_bytes,
        restricted_use_blocked=restricted,
        private_source_blocked=restricted,
    )


def _artifact_paths(root: Path) -> dict[str, Path]:
    paths = {"root": root}
    paths.update({name: root / filename for name, filename in ARTIFACT_FILENAMES.items()})
    return paths


def _write_artifacts(result: dict[str, Any]) -> None:
    artifact_root = Path(result["artifact_root"])
    artifact_root.mkdir(parents=True, exist_ok=True)
    paths = {name: Path(path) for name, path in result["artifact_paths"].items()}
    _write_json(paths["metadata"], _serializable_result(result))
    _write_json(paths["forbidden_downstream_flags"], reviewer_authority_quality_limitation_safety_flags())
    _write_summary(paths["summary"], result)
    _write_issues(paths["issues"], result)
    paths["limitations"].write_text("\n".join(_safe_public_limitations(result)) + "\n", encoding="utf-8")
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
        "reviewer_authority_level",
        "quality_status_level",
        "limitation_review_level",
        "permission_review_level",
        "package_promotion_level",
        "reviewer_metadata_present",
        "reviewer_id_recorded",
        "reviewer_id_preview",
        "reviewer_role",
        "reviewer_role_supported",
        "reviewer_type",
        "quality_status_present",
        "quality_status_declared",
        "limitation_count",
        "limitation_severity_max",
        "permission_class",
        "legality_flag",
        "reviewer_authority_validated",
        "quality_status_validated",
        "permission_class_validated",
        "real_package_candidate_created",
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
        "# Tiny PIT Reviewer Authority Quality Limitation Metadata Boundary",
        "",
        "This report is diagnostic-only and report-only.",
        "",
        f"- Runtime status: `{result['runtime_status']}`",
        f"- Health status: `{result['health_status']}`",
        f"- Reviewer authority level: `{result['reviewer_authority_level']}`",
        f"- Quality status level: `{result['quality_status_level']}`",
        f"- Limitation review level: `{result['limitation_review_level']}`",
        f"- Permission review level: `{result['permission_review_level']}`",
        f"- Package promotion level: `{result['package_promotion_level']}`",
        f"- Reviewer id recorded: `{str(result['reviewer_id_recorded']).lower()}`",
        f"- Reviewer id preview: `{result['reviewer_id_preview']}`",
        f"- Reviewer role: `{result['reviewer_role']}`",
        f"- Quality status declared: `{str(result['quality_status_declared']).lower()}`",
        f"- Limitation severity max: `{result['limitation_severity_max']}`",
        f"- Permission class: `{result['permission_class']}`",
        f"- Reviewer authority validated: `{str(result['reviewer_authority_validated']).lower()}`",
        f"- Quality status validated: `{str(result['quality_status_validated']).lower()}`",
        f"- Permission class validated: `{str(result['permission_class_validated']).lower()}`",
        f"- Source reliability scored: `{str(result['source_reliability_scored']).lower()}`",
        f"- Real package candidate created: `{str(result['real_package_candidate_created']).lower()}`",
        f"- Active replay input: `{str(result['active_replay_input']).lower()}`",
        f"- Buy review allowed: `{str(result['buy_review_allowed']).lower()}`",
        f"- Trading allowed: `{str(result['trading_allowed']).lower()}`",
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
    expected = {
        "requested_reviewer_authority_level": REVIEWER_METADATA_PRESENT_ONLY,
        "requested_quality_status_level": QUALITY_METADATA_PRESENT_ONLY,
        "requested_limitation_review_level": LIMITATION_METADATA_PRESENT_ONLY,
        "requested_permission_review_level": PERMISSION_CLASS_METADATA_PRESENT_ONLY,
        "requested_package_promotion_level": PACKAGE_PROMOTION_NONE,
    }
    for field, value in expected.items():
        if manifest.get(field) != value:
            return f"{field} must be {value}."
    reference = manifest.get("reviewer_quality_metadata_reference")
    if not isinstance(reference, dict):
        return "reviewer_quality_metadata_reference must be an object."
    missing_ref = [field for field in REQUIRED_REFERENCE_FIELDS if field not in reference]
    if missing_ref:
        return f"Missing reviewer_quality_metadata_reference fields: {', '.join(missing_ref)}"
    if reference.get("required") is not True:
        return "reviewer_quality_metadata_reference.required must be true."
    if reference.get("reference_type") != "reviewer_quality_limitation_metadata_ref":
        return "reviewer_quality_metadata_reference.reference_type is unsupported."
    if reference.get("intended_touch_level") != REVIEWER_QUALITY_LIMITATION_METADATA_PRESENT_ONLY:
        return "reviewer_quality_metadata_reference.intended_touch_level is unsupported."
    if reference.get("declared_only") is not False:
        return "reviewer_quality_metadata_reference.declared_only must be false."
    if Path(str(reference.get("path") or "")).resolve() != metadata_path.resolve():
        return "reviewer_quality_metadata_reference.path must match reviewer_quality_metadata_path."
    if not isinstance(manifest.get("limitations"), list) or not manifest["limitations"]:
        return "limitations must be a non-empty list."
    return None


def _validate_reviewer_quality_metadata(metadata: dict[str, Any]) -> tuple[str | None, str]:
    missing = [field for field in REQUIRED_REVIEWER_METADATA_FIELDS if field not in metadata]
    if missing:
        if any(field in REVIEWER_METADATA_CORE_FIELDS for field in missing):
            return (
                f"Missing reviewer metadata fields: {', '.join(missing)}",
                STATUS_BLOCKED_BY_MISSING_REVIEWER_METADATA,
            )
        if "quality_status" in missing:
            return "Missing quality_status.", STATUS_BLOCKED_BY_MISSING_QUALITY_STATUS
        return (
            f"Missing reviewer/quality metadata fields: {', '.join(missing)}",
            STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
        )
    if metadata.get("report_only") is not True or metadata.get("diagnostic_only") is not True:
        return "Reviewer/quality metadata must be report_only and diagnostic_only.", STATUS_BLOCKED_BY_MANIFEST_SCHEMA
    if str(metadata.get("reviewer_role") or "") not in ALLOWED_REVIEWER_ROLES:
        return "reviewer_role is unsupported.", STATUS_BLOCKED_BY_UNSUPPORTED_REVIEWER_ROLE
    if str(metadata.get("reviewer_type") or "") not in ALLOWED_REVIEWER_TYPES:
        return "reviewer_type is unsupported.", STATUS_BLOCKED_BY_MISSING_REVIEWER_METADATA
    quality_status = str(metadata.get("quality_status") or "")
    if quality_status not in ALLOWED_QUALITY_STATUSES:
        return "quality_status is unsupported.", STATUS_BLOCKED_BY_MISSING_QUALITY_STATUS
    if str(metadata.get("limitation_severity_max") or "") not in ALLOWED_LIMITATION_SEVERITIES:
        return "limitation_severity_max is unsupported.", STATUS_BLOCKED_BY_BLOCKING_LIMITATION
    categories = metadata.get("limitation_categories")
    if not isinstance(categories, list) or not set(categories) <= ALLOWED_LIMITATION_CATEGORIES:
        return "limitation_categories are unsupported.", STATUS_BLOCKED_BY_BLOCKING_LIMITATION
    permission_class = str(metadata.get("permission_class") or "")
    if permission_class not in ALLOWED_PERMISSION_CLASSES:
        return "permission_class is unsupported.", STATUS_BLOCKED_BY_FORBIDDEN_PERMISSION
    if str(metadata.get("legality_flag") or "") not in ALLOWED_LEGALITY_FLAGS:
        return "legality_flag is unsupported.", STATUS_BLOCKED_BY_FORBIDDEN_PERMISSION
    if metadata.get("limitations_overridden_by_reviewer") or metadata.get("limitations_overridden_by_quality"):
        return "Limitations cannot be overridden.", STATUS_BLOCKED_BY_BLOCKING_LIMITATION
    if str(metadata.get("limitation_severity_max") or "") == "BLOCKER":
        return "BLOCKER limitations block metadata acceptance.", STATUS_BLOCKED_BY_BLOCKING_LIMITATION
    if permission_class in FORBIDDEN_PERMISSION_CLASSES:
        return "permission_class blocks future promotion.", STATUS_BLOCKED_BY_FORBIDDEN_PERMISSION
    if not isinstance(metadata.get("limitations"), list) or not metadata["limitations"]:
        return "limitations must be a non-empty list.", STATUS_BLOCKED_BY_BLOCKING_LIMITATION
    return None, ""


def _has_forbidden_downstream(payload: dict[str, Any]) -> bool:
    flags = payload.get("forbidden_downstream_flags")
    if not isinstance(flags, dict):
        return True
    return any(bool(flags.get(field)) for field in REQUIRED_FALSE_FLAGS)


def _has_unsafe_claim(payload: dict[str, Any]) -> bool:
    return any(bool(payload.get(field)) for field in UNSAFE_REFERENCE_TRUE_FIELDS)


def _safe_limitations(metadata: dict[str, Any]) -> list[str]:
    severity = str(metadata.get("limitation_severity_max") or "")
    categories = metadata.get("limitation_categories") or []
    if not categories:
        return ["No public limitation categories supplied."]
    return [f"{severity or 'INFO'} limitation category: {category}" for category in categories]


def _safe_public_limitations(result: dict[str, Any]) -> list[str]:
    if result["limitations"]:
        return list(result["limitations"])
    return ["No public limitation text emitted."]


def _bounded_preview(value: str) -> str:
    return value[:REVIEWER_ID_PREVIEW_CHARS]


def _is_protected_or_secret_path(path: Path) -> bool:
    parts = tuple(part.lower() for part in path.parts)
    if any(token in parts for token in FORBIDDEN_PATH_TOKENS):
        return True
    return any(_contains_path_pair(parts, pair) for pair in PROTECTED_PATH_PAIRS)


def _contains_path_pair(parts: tuple[str, ...], pair: tuple[str, str]) -> bool:
    return any(parts[index : index + 2] == pair for index in range(max(len(parts) - 1, 0)))


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
