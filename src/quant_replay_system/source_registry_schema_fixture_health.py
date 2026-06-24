"""Health view for report-only source registry schema fixture artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.source_registry_schema_fixture import (
    FORBIDDEN_SIDE_EFFECT_FLAGS,
    REQUIRED_SOURCE_REGISTRY_FIELDS,
)
from quant_replay_system.source_registry_schema_fixture_index import VIEW_DIR_NAMES


HEALTH_COLUMNS = ["run_id", "status", "severity", "issue_code", "message", "artifact_path"]
REQUIRED_ARTIFACTS = {
    "metadata": "source_registry_schema_fixture_metadata.json",
    "schema_fields": "source_registry_schema_fields.csv",
    "fixture_rows": "source_registry_fixture_rows.csv",
    "permission_matrix": "source_registry_permission_matrix.csv",
    "replay_suitability_matrix": "source_registry_replay_suitability_matrix.csv",
    "validation_summary": "source_registry_validation_summary.csv",
    "limitations": "source_registry_limitations.md",
    "recommended_next_task": "recommended_next_task.md",
}


@dataclass(frozen=True)
class SourceRegistrySchemaFixtureHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_source_registry_schema_fixture_health(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/source_registry_schema_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/source_registry_schema_fixture_v0_1/health",
) -> SourceRegistrySchemaFixtureHealthResult:
    candidate_dirs = _candidate_dirs(Path(root))
    issues: list[dict[str, Any]] = []
    for artifact_dir in candidate_dirs:
        issues.extend(_issues_for_artifact_dir(artifact_dir))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "source_registry_schema_fixture_health.csv",
        "health_report": Path(output_dir) / "source_registry_schema_fixture_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = SourceRegistrySchemaFixtureHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=[] if Path(root).exists() else [f"Source registry schema fixture root does not exist: {root}"],
        audit_metadata=_audit_metadata(root, len(candidate_dirs)),
    )
    _write(result)
    return result


def _issues_for_artifact_dir(artifact_dir: Path) -> list[dict[str, Any]]:
    run_id = artifact_dir.name
    issues: list[dict[str, Any]] = []
    paths = {key: artifact_dir / filename for key, filename in REQUIRED_ARTIFACTS.items()}

    for path in paths.values():
        if not path.exists():
            issues.append(_issue(run_id, "ERROR", "MISSING_REQUIRED_ARTIFACT", f"Required artifact missing: {path}", path))

    metadata: dict[str, Any] | None = None
    if paths["metadata"].exists():
        try:
            metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(_issue(run_id, "ERROR", "METADATA_UNREADABLE", f"Metadata cannot be read: {exc}", paths["metadata"]))

    if metadata is not None:
        run_id = _text(metadata.get("source_registry_schema_fixture_id")) or run_id
        issues.extend(_metadata_issues(run_id, metadata, paths["metadata"]))

    if paths["schema_fields"].exists():
        issues.extend(_schema_field_issues(run_id, paths["schema_fields"]))
    if paths["fixture_rows"].exists():
        issues.extend(_fixture_row_issues(run_id, paths["fixture_rows"]))
    if paths["replay_suitability_matrix"].exists():
        issues.extend(_replay_matrix_issues(run_id, paths["replay_suitability_matrix"]))

    return issues


def _metadata_issues(run_id: str, metadata: dict[str, Any], metadata_path: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    status = _text(metadata.get("status"))
    if status not in {"PASS", "FAIL"}:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_STATUS", f"Unknown fixture status: {status}", metadata_path))
    if status == "FAIL":
        issues.append(_issue(run_id, "ERROR", "FIXTURE_STATUS_NOT_PASS", "Fixture metadata status is FAIL.", metadata_path))
    if not _to_bool(metadata.get("source_registry_schema_fixture_created")):
        issues.append(_issue(run_id, "ERROR", "CREATED_FLAG_MISSING", "source_registry_schema_fixture_created is not true.", metadata_path))
    if not _to_bool(metadata.get("report_only")):
        issues.append(_issue(run_id, "ERROR", "METADATA_REPORT_ONLY_NOT_TRUE", "metadata report_only is not true.", metadata_path))
    if not _to_bool(metadata.get("diagnostic_only")):
        issues.append(_issue(run_id, "ERROR", "METADATA_DIAGNOSTIC_ONLY_NOT_TRUE", "metadata diagnostic_only is not true.", metadata_path))
    for flag in FORBIDDEN_SIDE_EFFECT_FLAGS:
        if _to_bool(metadata.get(flag)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_SIDE_EFFECT_FLAG_TRUE", f"{flag} is true.", metadata_path))
    artifact_paths = metadata.get("artifact_paths") if isinstance(metadata.get("artifact_paths"), dict) else {}
    for key, value in artifact_paths.items():
        if _unsafe_path_text(value):
            issues.append(_issue(run_id, "ERROR", "UNSAFE_ARTIFACT_PATH", f"Unsafe artifact path for {key}: {value}", metadata_path))
    return issues


def _schema_field_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        fields = pd.read_csv(path, dtype=str)
    except Exception as exc:
        return [_issue(run_id, "ERROR", "SCHEMA_FIELDS_UNREADABLE", f"Schema fields cannot be read: {exc}", path)]
    if "field_name" not in fields.columns:
        return [_issue(run_id, "ERROR", "SCHEMA_FIELDS_REQUIRED_FIELDS_MISSING", "schema fields missing field_name column.", path)]
    missing = sorted(set(REQUIRED_SOURCE_REGISTRY_FIELDS) - set(fields["field_name"].dropna().astype(str)))
    if missing:
        return [
            _issue(
                run_id,
                "ERROR",
                "SCHEMA_FIELDS_REQUIRED_FIELDS_MISSING",
                f"schema fields missing required field names: {','.join(missing)}",
                path,
            )
        ]
    return []


def _fixture_row_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        rows = pd.read_csv(path, dtype=str)
    except Exception as exc:
        return [_issue(run_id, "ERROR", "FIXTURE_ROWS_UNREADABLE", f"fixture rows cannot be read: {exc}", path)]
    issues: list[dict[str, Any]] = []
    missing = sorted(set(REQUIRED_SOURCE_REGISTRY_FIELDS) - set(rows.columns))
    if missing:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "FIXTURE_ROWS_REQUIRED_COLUMNS_MISSING",
                f"fixture rows missing required columns: {','.join(missing)}",
                path,
            )
        )
        return issues

    row_text = " ".join(rows.fillna("").astype(str).agg(" ".join, axis=1)).lower()
    if "token" in row_text or "secret" in row_text or any("token" in str(column).lower() or "secret" in str(column).lower() for column in rows.columns):
        issues.append(_issue(run_id, "ERROR", "SENSITIVE_TEXT_DETECTED", "token/secret-looking text appears in fixture rows.", path))
    if not rows["report_only"].map(_to_bool).all():
        issues.append(_issue(run_id, "ERROR", "ROW_REPORT_ONLY_NOT_TRUE", "All fixture rows must be report_only true.", path))
    if not rows["diagnostic_only"].map(_to_bool).all():
        issues.append(_issue(run_id, "ERROR", "ROW_DIAGNOSTIC_ONLY_NOT_TRUE", "All fixture rows must be diagnostic_only true.", path))

    blocked = rows[
        rows["source_type"].isin(["BLOCKED_PRIVATE"])
        | rows["permission_class"].isin(["PROHIBITED"])
        | rows["reliability_status"].isin(["BLOCKED"])
    ]
    if not blocked.empty and blocked["replay_suitability"].eq("REPLAY_READY_AFTER_REVIEW").any():
        issues.append(_issue(run_id, "ERROR", "BLOCKED_SOURCE_REPLAY_READY", "Blocked/private/prohibited source is replay-ready.", path))

    paid = rows[rows["source_id"] == "PAID_VENDOR_FUTURE_BACKUP_SAMPLE"]
    if not paid.empty and not paid["project_role"].eq("FUTURE_BACKUP").all():
        issues.append(_issue(run_id, "ERROR", "PAID_VENDOR_CURRENT_DEPENDENCY", "Paid vendor sample is not future backup only.", path))

    wrapper = rows[rows["source_id"] == "PUBLIC_WRAPPER_OPTIONAL_SAMPLE"]
    if not wrapper.empty and wrapper["reliability_status"].eq("VERIFIED").any():
        issues.append(_issue(run_id, "ERROR", "PUBLIC_WRAPPER_AUTO_VERIFIED", "Public wrapper sample is automatically verified.", path))

    local = rows[rows["source_id"] == "LOCAL_CSV_REVIEWED_SAMPLE"]
    if not local.empty and not local["manual_review_required"].map(_to_bool).all():
        issues.append(_issue(run_id, "ERROR", "LOCAL_CSV_MANUAL_REVIEW_MISSING", "LOCAL_CSV sample lacks manual review.", path))
    return issues


def _replay_matrix_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        matrix = pd.read_csv(path, dtype=str)
    except Exception as exc:
        return [_issue(run_id, "ERROR", "REPLAY_MATRIX_UNREADABLE", f"replay matrix cannot be read: {exc}", path)]
    issues: list[dict[str, Any]] = []
    if {"source_id", "current_dependency_allowed", "canonical_permission_source"}.issubset(matrix.columns):
        paid = matrix[matrix["source_id"] == "PAID_VENDOR_FUTURE_BACKUP_SAMPLE"]
        if not paid.empty and paid["current_dependency_allowed"].map(_to_bool).any():
            issues.append(_issue(run_id, "ERROR", "PAID_VENDOR_CURRENT_DEPENDENCY", "Paid vendor sample is a current dependency.", path))
        wrapper = matrix[matrix["source_id"] == "PUBLIC_WRAPPER_OPTIONAL_SAMPLE"]
        if not wrapper.empty and wrapper["canonical_permission_source"].map(_to_bool).any():
            issues.append(_issue(run_id, "ERROR", "PUBLIC_WRAPPER_CANONICAL_PERMISSION", "Public wrapper sample is canonical permission.", path))
    return issues


def _candidate_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and path.name not in VIEW_DIR_NAMES and not path.name.startswith("_")
        and any((path / filename).exists() for filename in REQUIRED_ARTIFACTS.values())
    )


def _write(result: SourceRegistrySchemaFixtureHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Source Registry Schema Fixture Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                "This health view is report-only. It does not create real source permissions, production source state, buy-review eligibility, performance validation, API calls, broker behavior, orders, messages, or trading.",
                "",
                result.health_frame.to_markdown(index=False) if not result.health_frame.empty else "No issues.",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "warnings": result.warnings,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")


def _issue(run_id: str, severity: str, code: str, message: str, path: str | Path) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "status": "OPEN",
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    for column in HEALTH_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame.loc[:, HEALTH_COLUMNS]


def _audit_metadata(root: str | Path, checked_count: int) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "checked_artifact_count": checked_count,
        "report_only": True,
        "diagnostic_only": True,
        "source_registry_schema_fixture_health_created": True,
        **{flag: False for flag in FORBIDDEN_SIDE_EFFECT_FLAGS},
    }


def _unsafe_path_text(value: Any) -> bool:
    text = _text(value).replace("\\", "/").lower()
    unsafe_fragments = [
        "data/raw",
        "data/processed",
        "data/cache",
        "broker",
        "order",
        "trading",
        "current-candidates",
        "current_candidates",
        "snapshot",
        "signal_semantics",
    ]
    return any(fragment in text for fragment in unsafe_fragments)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _hash_payload(value: Any) -> str:
    return hashlib.sha256(json.dumps(_json_safe(value), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
