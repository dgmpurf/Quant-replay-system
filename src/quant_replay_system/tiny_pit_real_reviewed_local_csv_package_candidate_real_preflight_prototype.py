"""Manifest-only Tiny PIT real reviewed LOCAL_CSV preflight prototype.

This module is report-only and diagnostic-only. It reads at most one explicit
top-level JSON package manifest under caller-provided allowed roots. It never
reads CSV content, follows manifest references, computes local file hashes,
creates package candidates, creates replay inputs, runs replay, creates labels
or training artifacts, or enables broker/API/order/message/trading behavior.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence


INPUT_MODE_NO_INPUT_SYNTHETIC_DECLARATIONS = "NO_INPUT_SYNTHETIC_DECLARATIONS"
INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY = "EXPLICIT_MANIFEST_METADATA_ONLY"

FORBIDDEN_INPUT_MODES = [
    "PACKAGE_ROOT_DISCOVERY",
    "EXPLICIT_REVIEWED_CSV_PATH",
    "AUTO_DISCOVERY",
    "CSV_HEADER_ONLY",
    "CSV_ROW_COUNT_ONLY",
    "CSV_FULL_CONTENT",
    "LOCAL_FILE_HASH_COMPUTE",
]

STATUS_NO_REAL_INPUT = "NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_INPUT"
STATUS_NO_INPUT = "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_PROTOTYPE_NO_INPUT"
STATUS_MANIFEST_DECLARED_REPORT_ONLY = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_PROTOTYPE_MANIFEST_DECLARED_REPORT_ONLY"
)
STATUS_MANIFEST_SCHEMA_DESIGNED_REPORT_ONLY = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_PROTOTYPE_MANIFEST_SCHEMA_DESIGNED_REPORT_ONLY"
)
STATUS_METADATA_NEEDS_REVIEW = "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_PROTOTYPE_METADATA_NEEDS_REVIEW"
STATUS_BLOCKED_BY_MANIFEST_SCHEMA = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_PROTOTYPE_BLOCKED_BY_MANIFEST_SCHEMA"
)
STATUS_BLOCKED_BY_PATH_GUARD = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_PROTOTYPE_BLOCKED_BY_PATH_GUARD"
)
STATUS_BLOCKED_BY_PROTECTED_PATH = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_PROTOTYPE_BLOCKED_BY_PROTECTED_PATH"
)
STATUS_BLOCKED_BY_SOURCE_LINEAGE_METADATA = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_PROTOTYPE_BLOCKED_BY_SOURCE_LINEAGE_METADATA"
)
STATUS_BLOCKED_BY_AVAILABLE_TIME_METADATA = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_PROTOTYPE_BLOCKED_BY_AVAILABLE_TIME_METADATA"
)
STATUS_BLOCKED_BY_REVISION_METADATA = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_PROTOTYPE_BLOCKED_BY_REVISION_METADATA"
)
STATUS_BLOCKED_BY_REVIEWER_AUTHORITY_METADATA = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_PROTOTYPE_BLOCKED_BY_REVIEWER_AUTHORITY_METADATA"
)
STATUS_BLOCKED_BY_QUALITY_METADATA = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_PROTOTYPE_BLOCKED_BY_QUALITY_METADATA"
)
STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_PROTOTYPE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
)
STATUS_REPORT_ONLY_PASS_CANDIDATE = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_PROTOTYPE_REPORT_ONLY_PASS_CANDIDATE_FOR_HUMAN_REVIEW"
)

WORKFLOW_NAME = "tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype"
WORKFLOW_STAGE = (
    "TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_MANIFEST_ONLY_PREFLIGHT_PROTOTYPE_CORE_CREATED_REPORT_ONLY"
)
CREATED_AT = "2026-06-30T00:00:00Z"
FIXTURE_VERSION = "v0.1"
CSV_READ_LEVEL_NONE = "CSV_READ_NONE"
DEFAULT_OUTPUT_ROOT = (
    "outputs/reports/manual_diagnostics/"
    "tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_v0_1"
)
MAX_MANIFEST_BYTES = 65536

REQUIRED_MANIFEST_FIELDS = [
    "manifest_schema_version",
    "package_id",
    "package_version",
    "package_type",
    "package_created_at",
    "package_prepared_by",
    "replay_decision_time",
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
    "declared_csv_read_level",
    "declared_real_csv_required",
    "declared_real_csv_consumed",
    "declared_real_package_candidate_created",
    "declared_active_reviewed_input_candidate_created",
    "declared_active_replay_input_ready_emitted",
    "declared_trading_allowed",
]

REFERENCE_FIELDS = [
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

DECLARED_FALSE_FIELDS = [
    "declared_real_csv_required",
    "declared_real_csv_consumed",
    "declared_real_package_candidate_created",
    "declared_active_reviewed_input_candidate_created",
    "declared_active_replay_input_ready_emitted",
    "declared_trading_allowed",
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

METADATA_REQUIRED_FALSE_FLAGS = [
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

ARTIFACT_FILENAMES = {
    "metadata": "metadata.json",
    "report": "preflight_prototype_report.md",
    "package_manifest_inspection": "package_manifest_inspection.csv",
    "path_guard_report": "path_guard_report.csv",
    "manifest_schema_presence": "manifest_schema_presence.csv",
    "manifest_reference_presence": "manifest_reference_presence.csv",
    "forbidden_downstream_flags": "forbidden_downstream_flags.json",
    "limitations": "limitations.md",
}

PROTECTED_PATH_PAIRS = {("data", "raw"), ("data", "processed"), ("data", "cache"), ("docs", "project_sources")}
PROTECTED_PATH_TOKENS = [".env", "secrets", "auth", "token", "credential"]
NETWORK_PREFIXES = ("http://", "https://", "ftp://", "s3://")
VISIBLE_REFERENCE_BLOCKERS = ("..", "http://", "https://", "ftp://", "s3://", ".env", "secrets", "auth", "token", "credential")


def real_reviewed_local_csv_package_candidate_real_preflight_prototype_statuses() -> list[str]:
    return [
        STATUS_NO_REAL_INPUT,
        STATUS_NO_INPUT,
        STATUS_MANIFEST_DECLARED_REPORT_ONLY,
        STATUS_MANIFEST_SCHEMA_DESIGNED_REPORT_ONLY,
        STATUS_METADATA_NEEDS_REVIEW,
        STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
        STATUS_BLOCKED_BY_PATH_GUARD,
        STATUS_BLOCKED_BY_PROTECTED_PATH,
        STATUS_BLOCKED_BY_SOURCE_LINEAGE_METADATA,
        STATUS_BLOCKED_BY_AVAILABLE_TIME_METADATA,
        STATUS_BLOCKED_BY_REVISION_METADATA,
        STATUS_BLOCKED_BY_REVIEWER_AUTHORITY_METADATA,
        STATUS_BLOCKED_BY_QUALITY_METADATA,
        STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
        STATUS_REPORT_ONLY_PASS_CANDIDATE,
    ]


def run_manifest_only_preflight_prototype(
    *,
    output_root: Path | str | None = None,
    package_manifest_path: Path | str | None = None,
    allowed_manifest_roots: Sequence[Path | str] | None = None,
    input_mode: str = INPUT_MODE_NO_INPUT_SYNTHETIC_DECLARATIONS,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Run the report-only manifest preflight prototype and write artifacts."""

    root = _validate_output_root(Path(output_root or DEFAULT_OUTPUT_ROOT))
    context = _evaluate_input(
        input_mode=input_mode,
        package_manifest_path=package_manifest_path,
        allowed_manifest_roots=allowed_manifest_roots,
    )
    safe_run_id = run_id or _stable_run_id(context)
    artifact_path = root / safe_run_id
    artifact_paths = {"artifact_dir": artifact_path}
    artifact_paths.update({key: artifact_path / filename for key, filename in ARTIFACT_FILENAMES.items()})
    _validate_artifact_paths(artifact_path, artifact_paths)

    result = _result_payload(
        context=context,
        run_id=safe_run_id,
        artifact_path=artifact_path,
        artifact_paths=artifact_paths,
    )
    _write_artifacts(result, artifact_paths)
    return result


def _evaluate_input(
    *,
    input_mode: str,
    package_manifest_path: Path | str | None,
    allowed_manifest_roots: Sequence[Path | str] | None,
) -> dict[str, Any]:
    if input_mode in FORBIDDEN_INPUT_MODES:
        return _blocked_context(
            input_mode=input_mode,
            status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            reasons=[f"input_mode {input_mode} is deferred or forbidden for manifest-only core"],
        )

    if input_mode == INPUT_MODE_NO_INPUT_SYNTHETIC_DECLARATIONS:
        if package_manifest_path is not None:
            return _blocked_context(
                input_mode=input_mode,
                status=STATUS_BLOCKED_BY_PATH_GUARD,
                reasons=["package_manifest_path is not accepted in no-input mode"],
            )
        return {
            "input_mode": input_mode,
            "runtime_status": STATUS_NO_INPUT,
            "health_status": "PASS",
            "pass_candidate": False,
            "manifest_read": False,
            "manifest": {},
            "missing_required_fields": [],
            "missing_false_flags": [],
            "forbidden_flag_failures": [],
            "reference_findings": [],
            "path_guard_findings": ["no package manifest path supplied; synthetic declarations only"],
            "blocker_reasons": [],
        }

    if input_mode != INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY:
        return _blocked_context(
            input_mode=input_mode,
            status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            reasons=[f"unsupported input_mode {input_mode}"],
        )

    path_check = _check_manifest_path(package_manifest_path, allowed_manifest_roots)
    if path_check["blocked"]:
        return _blocked_context(
            input_mode=input_mode,
            status=path_check["status"],
            reasons=list(path_check["reasons"]),
            path_guard_findings=list(path_check["reasons"]),
        )

    manifest_path = path_check["path"]
    assert isinstance(manifest_path, Path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _blocked_context(
            input_mode=input_mode,
            status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            reasons=[f"malformed JSON package manifest: {exc.msg}"],
            path_guard_findings=["manifest path passed guard before JSON parse"],
            manifest_read=True,
        )
    if not isinstance(manifest, dict):
        return _blocked_context(
            input_mode=input_mode,
            status=STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
            reasons=["package manifest top-level JSON must be an object"],
            path_guard_findings=["manifest path passed guard before JSON parse"],
            manifest_read=True,
        )

    missing_required = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    missing_false_flags = [flag for flag in REQUIRED_FALSE_FLAGS if flag not in manifest]
    forbidden_flag_failures = [
        flag for flag in REQUIRED_FALSE_FLAGS if flag in manifest and bool(manifest.get(flag)) is not False
    ]
    declared_false_failures = [
        field for field in DECLARED_FALSE_FIELDS if field in manifest and bool(manifest.get(field)) is not False
    ]
    reference_findings = _reference_findings(manifest)

    status = STATUS_REPORT_ONLY_PASS_CANDIDATE
    blocker_reasons: list[str] = []
    if missing_required or manifest.get("declared_csv_read_level") != CSV_READ_LEVEL_NONE:
        status = STATUS_BLOCKED_BY_MANIFEST_SCHEMA
        if missing_required:
            blocker_reasons.append("missing required manifest fields")
        if manifest.get("declared_csv_read_level") != CSV_READ_LEVEL_NONE:
            blocker_reasons.append("declared_csv_read_level must be CSV_READ_NONE")
    elif missing_false_flags or forbidden_flag_failures or declared_false_failures:
        status = STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM
        blocker_reasons.append("required false downstream flags must be present and false")
    elif any(row["blocked"] for row in reference_findings):
        status = STATUS_BLOCKED_BY_PATH_GUARD
        blocker_reasons.append("one or more declared references contains visibly forbidden path or URL text")

    return {
        "input_mode": input_mode,
        "runtime_status": status,
        "health_status": "PASS" if status == STATUS_REPORT_ONLY_PASS_CANDIDATE else "FAIL",
        "pass_candidate": status == STATUS_REPORT_ONLY_PASS_CANDIDATE,
        "manifest_read": True,
        "manifest": manifest,
        "missing_required_fields": missing_required,
        "missing_false_flags": missing_false_flags,
        "forbidden_flag_failures": forbidden_flag_failures + declared_false_failures,
        "reference_findings": reference_findings,
        "path_guard_findings": ["manifest path passed guard; references declared but not followed"],
        "blocker_reasons": blocker_reasons,
    }


def _check_manifest_path(
    package_manifest_path: Path | str | None,
    allowed_manifest_roots: Sequence[Path | str] | None,
) -> dict[str, Any]:
    if package_manifest_path is None:
        return {
            "blocked": True,
            "status": STATUS_BLOCKED_BY_PATH_GUARD,
            "reasons": ["package_manifest_path is required for explicit manifest metadata-only mode"],
        }
    raw_path = str(package_manifest_path)
    if raw_path.lower().startswith(NETWORK_PREFIXES):
        return {
            "blocked": True,
            "status": STATUS_BLOCKED_BY_PATH_GUARD,
            "reasons": ["network URL package_manifest_path is rejected"],
        }
    if ".." in Path(raw_path).parts:
        return {
            "blocked": True,
            "status": STATUS_BLOCKED_BY_PATH_GUARD,
            "reasons": ["path traversal package_manifest_path is rejected"],
        }
    path = Path(package_manifest_path)
    if _is_protected_path(path):
        return {
            "blocked": True,
            "status": STATUS_BLOCKED_BY_PROTECTED_PATH,
            "reasons": ["package_manifest_path is under or contains a protected path token"],
        }
    if not allowed_manifest_roots:
        return {
            "blocked": True,
            "status": STATUS_BLOCKED_BY_PATH_GUARD,
            "reasons": ["allowed_manifest_roots must be explicit for manifest metadata-only mode"],
        }
    if path.suffix.lower() != ".json":
        return {
            "blocked": True,
            "status": STATUS_BLOCKED_BY_PATH_GUARD,
            "reasons": ["package_manifest_path must have .json extension"],
        }
    resolved = path.resolve(strict=False)
    allowed_roots = [Path(root).resolve(strict=False) for root in allowed_manifest_roots]
    if not any(_is_relative_to(resolved, root) for root in allowed_roots):
        return {
            "blocked": True,
            "status": STATUS_BLOCKED_BY_PATH_GUARD,
            "reasons": ["package_manifest_path must be under an explicit allowed_manifest_root"],
        }
    if not path.exists() or not path.is_file():
        return {
            "blocked": True,
            "status": STATUS_BLOCKED_BY_PATH_GUARD,
            "reasons": ["package_manifest_path must be an existing regular file"],
        }
    real_resolved = path.resolve(strict=True)
    if not any(_is_relative_to(real_resolved, root) for root in allowed_roots):
        return {
            "blocked": True,
            "status": STATUS_BLOCKED_BY_PATH_GUARD,
            "reasons": ["package_manifest_path symlink escape is rejected"],
        }
    if path.stat().st_size > MAX_MANIFEST_BYTES:
        return {
            "blocked": True,
            "status": STATUS_BLOCKED_BY_PATH_GUARD,
            "reasons": ["package_manifest_path exceeds manifest-only size limit"],
        }
    return {"blocked": False, "path": path, "reasons": []}


def _blocked_context(
    *,
    input_mode: str,
    status: str,
    reasons: list[str],
    path_guard_findings: list[str] | None = None,
    manifest_read: bool = False,
) -> dict[str, Any]:
    return {
        "input_mode": input_mode,
        "runtime_status": status,
        "health_status": "FAIL" if status != STATUS_NO_INPUT else "PASS",
        "pass_candidate": False,
        "manifest_read": manifest_read,
        "manifest": {},
        "missing_required_fields": [],
        "missing_false_flags": [],
        "forbidden_flag_failures": [],
        "reference_findings": [],
        "path_guard_findings": path_guard_findings or reasons,
        "blocker_reasons": reasons,
    }


def _reference_findings(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    findings = []
    for field in REFERENCE_FIELDS:
        value = manifest.get(field)
        value_text = "" if value is None else str(value)
        lowered = value_text.lower()
        blocked = any(token in lowered for token in VISIBLE_REFERENCE_BLOCKERS)
        findings.append(
            {
                "field_name": field,
                "reference_declared": bool(value_text),
                "reference_value": value_text,
                "reference_followed": False,
                "blocked": blocked,
                "finding": "REFERENCE_DECLARED_NOT_FOLLOWED" if value_text and not blocked else "REFERENCE_BLOCKED_OR_MISSING",
            }
        )
    return findings


def _result_payload(
    *,
    context: dict[str, Any],
    run_id: str,
    artifact_path: Path,
    artifact_paths: dict[str, Path],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "run_id": run_id,
        "fixture_id": run_id,
        "fixture_version": FIXTURE_VERSION,
        "workflow_name": WORKFLOW_NAME,
        "workflow_stage": WORKFLOW_STAGE,
        "created_at": CREATED_AT,
        "runtime_status": context["runtime_status"],
        "status": context["runtime_status"],
        "health_status": context["health_status"],
        "input_mode": context["input_mode"],
        "pass_candidate": context["pass_candidate"],
        "report_only": True,
        "diagnostic_only": True,
        "csv_read_level": CSV_READ_LEVEL_NONE,
        "manifest_read": context["manifest_read"],
        "references_followed": False,
        "local_file_hash_computed": False,
        "external_source_validated": False,
        "pit_admissibility_validated": False,
        "artifact_path": str(artifact_path),
        "report_path": str(artifact_paths["report"]),
        "artifact_files": {key: str(value) for key, value in artifact_paths.items() if key != "artifact_dir"},
        "missing_required_fields": list(context["missing_required_fields"]),
        "missing_false_flags": list(context["missing_false_flags"]),
        "forbidden_flag_failures": list(context["forbidden_flag_failures"]),
        "blocker_reasons": list(context["blocker_reasons"]),
        "reference_count": len(context["reference_findings"]),
        "references_blocked_count": sum(1 for row in context["reference_findings"] if row["blocked"]),
    }
    result.update({flag: False for flag in REQUIRED_FALSE_FLAGS})
    for flag in METADATA_REQUIRED_FALSE_FLAGS:
        result.setdefault(flag, False)
    return result


def _write_artifacts(result: dict[str, Any], artifact_paths: dict[str, Path]) -> None:
    artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    context_manifest = _manifest_from_result(result)
    _write_json(artifact_paths["metadata"], result)
    artifact_paths["report"].write_text(_report_text(result), encoding="utf-8")
    _write_csv(artifact_paths["package_manifest_inspection"], _package_manifest_inspection_rows(result, context_manifest))
    _write_csv(artifact_paths["path_guard_report"], _path_guard_rows(result))
    _write_csv(artifact_paths["manifest_schema_presence"], _manifest_schema_rows(result, context_manifest))
    _write_csv(artifact_paths["manifest_reference_presence"], _manifest_reference_rows(result, context_manifest))
    _write_json(artifact_paths["forbidden_downstream_flags"], {flag: False for flag in REQUIRED_FALSE_FLAGS})
    artifact_paths["limitations"].write_text(_limitations_text(), encoding="utf-8")


def _manifest_from_result(result: dict[str, Any]) -> dict[str, Any]:
    # The written artifacts are intentionally summaries; no referenced files are opened.
    metadata_path = Path(result["artifact_path"]) / ARTIFACT_FILENAMES["metadata"]
    return {"artifact_metadata_path": str(metadata_path)}


def _package_manifest_inspection_rows(result: dict[str, Any], _: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "run_id": result["run_id"],
            "input_mode": result["input_mode"],
            "runtime_status": result["runtime_status"],
            "manifest_read": result["manifest_read"],
            "csv_read_level": result["csv_read_level"],
            "references_followed": result["references_followed"],
            "pass_candidate": result["pass_candidate"],
            "report_only": result["report_only"],
            "diagnostic_only": result["diagnostic_only"],
        }
    ]


def _path_guard_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    reasons = result.get("blocker_reasons") or ["no path guard blocker"]
    return [
        {
            "run_id": result["run_id"],
            "runtime_status": result["runtime_status"],
            "guard_result": "BLOCK" if result["blocker_reasons"] else "PASS",
            "reason": reason,
            "protected_path_allowed": False,
            "references_followed": False,
        }
        for reason in reasons
    ]


def _manifest_schema_rows(result: dict[str, Any], _: dict[str, Any]) -> list[dict[str, Any]]:
    missing = set(result["missing_required_fields"])
    return [
        {
            "field_name": field,
            "required": True,
            "present": field not in missing and result["manifest_read"],
            "missing_blocks": field in missing,
            "runtime_status": result["runtime_status"],
        }
        for field in REQUIRED_MANIFEST_FIELDS
    ]


def _manifest_reference_rows(result: dict[str, Any], _: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "field_name": field,
            "reference_declared": result["manifest_read"],
            "reference_followed": False,
            "csv_read_level": CSV_READ_LEVEL_NONE,
            "notes": "References are declaration-only in this core.",
        }
        for field in REFERENCE_FIELDS
    ]


def _report_text(result: dict[str, Any]) -> str:
    return f"""# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Manifest-Only Preflight Prototype

This is a report-only, diagnostic-only manifest metadata preflight prototype.

- Run id: `{result["run_id"]}`
- Runtime status: `{result["runtime_status"]}`
- Workflow stage: `{result["workflow_stage"]}`
- Health: `{result["health_status"]}`
- Input mode: `{result["input_mode"]}`
- CSV read level: `{result["csv_read_level"]}`
- Manifest read: `{str(result["manifest_read"]).lower()}`
- References followed: `false`
- Local file hash computed: `false`
- Pass candidate: `{str(result["pass_candidate"]).lower()}`

The prototype does not read CSV files, follow manifest references, compute local file hashes, create real package candidates, create active inputs, emit replay readiness, run replay, create labels/training/model/stock_profile/paper/buy-review/trading behavior, or write protected data roots.
"""


def _limitations_text() -> str:
    return (
        "# Limitations\n\n"
        "- Manifest-only / metadata-only report prototype.\n"
        "- Top-level JSON manifest only, and only under explicit allowed roots.\n"
        "- No CSV rows, headers, row counts, or file-byte hashes are read.\n"
        "- No referenced metadata manifests are followed.\n"
        "- No PIT admissibility, replay readiness, buy-review, performance validation, or trading permission is created.\n"
    )


def _stable_run_id(context: dict[str, Any]) -> str:
    payload = {
        "input_mode": context["input_mode"],
        "runtime_status": context["runtime_status"],
        "pass_candidate": context["pass_candidate"],
        "missing_required_fields": context["missing_required_fields"],
        "missing_false_flags": context["missing_false_flags"],
        "forbidden_flag_failures": context["forbidden_flag_failures"],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _validate_output_root(output_root: Path) -> Path:
    resolved = output_root.resolve(strict=False)
    if _is_protected_path(resolved):
        raise ValueError(f"Protected output root is not allowed: {output_root}")
    return resolved


def _validate_artifact_paths(root: Path, artifact_paths: dict[str, Path]) -> None:
    for key, path in artifact_paths.items():
        if key == "artifact_dir":
            continue
        if not _is_relative_to(path.resolve(strict=False), root.resolve(strict=False)):
            raise ValueError(f"Artifact path escapes output root: {path}")


def _is_protected_path(path: Path) -> bool:
    lowered_parts = [part.lower() for part in path.parts]
    if any((first, second) in PROTECTED_PATH_PAIRS for first, second in zip(lowered_parts, lowered_parts[1:])):
        return True
    return any(any(token in part for token in PROTECTED_PATH_TOKENS) for part in lowered_parts)


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

