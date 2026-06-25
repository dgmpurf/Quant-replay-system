"""Health view for report-only raw document store schema fixture artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.raw_document_store_schema_fixture import (
    FORBIDDEN_METADATA_FALSE_FLAGS,
    REQUIRED_RAW_DOCUMENT_STORE_FIELDS,
)
from quant_replay_system.raw_document_store_schema_fixture_index import VIEW_DIR_NAMES


HEALTH_COLUMNS = ["run_id", "status", "severity", "issue_code", "message", "artifact_path"]
REQUIRED_ARTIFACTS = {
    "metadata": "raw_document_store_schema_fixture_metadata.json",
    "schema_fields": "raw_document_store_schema_fields.csv",
    "fixture_rows": "raw_document_store_fixture_rows.csv",
    "permission_matrix": "raw_document_store_permission_matrix.csv",
    "storage_policy_matrix": "raw_document_store_storage_policy_matrix.csv",
    "pit_timing_matrix": "raw_document_store_pit_timing_matrix.csv",
    "validation_summary": "raw_document_store_validation_summary.csv",
    "limitations": "raw_document_store_limitations.md",
    "recommended_next_task": "recommended_next_task.md",
}


@dataclass(frozen=True)
class RawDocumentStoreSchemaFixtureHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_raw_document_store_schema_fixture_health(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/raw_document_store_schema_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/raw_document_store_schema_fixture_v0_1/health",
) -> RawDocumentStoreSchemaFixtureHealthResult:
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
        "health_csv": Path(output_dir) / "raw_document_store_schema_fixture_health.csv",
        "health_report": Path(output_dir) / "raw_document_store_schema_fixture_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = RawDocumentStoreSchemaFixtureHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=[] if Path(root).exists() else [f"Raw document store schema fixture root does not exist: {root}"],
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
        run_id = _text(metadata.get("raw_document_store_schema_fixture_id")) or run_id
        issues.extend(_metadata_issues(run_id, metadata, paths["metadata"]))

    if paths["schema_fields"].exists():
        issues.extend(_schema_field_issues(run_id, paths["schema_fields"]))
    if paths["fixture_rows"].exists():
        issues.extend(_fixture_row_issues(run_id, paths["fixture_rows"]))
    if paths["permission_matrix"].exists():
        issues.extend(_permission_matrix_issues(run_id, paths["permission_matrix"]))

    return issues


def _metadata_issues(run_id: str, metadata: dict[str, Any], metadata_path: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    status = _text(metadata.get("status"))
    if status not in {"PASS", "FAIL"}:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_STATUS", f"Unknown fixture status: {status}", metadata_path))
    if status == "FAIL":
        issues.append(_issue(run_id, "ERROR", "FIXTURE_STATUS_NOT_PASS", "Fixture metadata status is FAIL.", metadata_path))
    if not _to_bool(metadata.get("raw_document_store_schema_fixture_created")):
        issues.append(_issue(run_id, "ERROR", "CREATED_FLAG_MISSING", "raw_document_store_schema_fixture_created is not true.", metadata_path))
    if not _to_bool(metadata.get("report_only")):
        issues.append(_issue(run_id, "ERROR", "METADATA_REPORT_ONLY_NOT_TRUE", "metadata report_only is not true.", metadata_path))
    if not _to_bool(metadata.get("diagnostic_only")):
        issues.append(_issue(run_id, "ERROR", "METADATA_DIAGNOSTIC_ONLY_NOT_TRUE", "metadata diagnostic_only is not true.", metadata_path))
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        if _to_bool(metadata.get(flag)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{flag} is true.", metadata_path))
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
    missing = sorted(set(REQUIRED_RAW_DOCUMENT_STORE_FIELDS) - set(fields["field_name"].dropna().astype(str)))
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
        rows = pd.read_csv(path, dtype=str).fillna("")
    except Exception as exc:
        return [_issue(run_id, "ERROR", "FIXTURE_ROWS_UNREADABLE", f"fixture rows cannot be read: {exc}", path)]
    issues: list[dict[str, Any]] = []
    missing = sorted(set(REQUIRED_RAW_DOCUMENT_STORE_FIELDS) - set(rows.columns))
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

    row_text = " ".join(rows.astype(str).agg(" ".join, axis=1)).lower()
    column_text = " ".join(str(column).lower() for column in rows.columns)
    if _contains_secret_like(f"{column_text} {row_text}"):
        issues.append(_issue(run_id, "ERROR", "SENSITIVE_TEXT_DETECTED", "token/secret-looking text appears in fixture rows.", path))
    if not rows["report_only"].map(_to_bool).all():
        issues.append(_issue(run_id, "ERROR", "ROW_REPORT_ONLY_NOT_TRUE", "All fixture rows must be report_only true.", path))
    if not rows["diagnostic_only"].map(_to_bool).all():
        issues.append(_issue(run_id, "ERROR", "ROW_DIAGNOSTIC_ONLY_NOT_TRUE", "All fixture rows must be diagnostic_only true.", path))

    non_empty_checks = [
        ("document_id", "DOCUMENT_ID_MISSING"),
        ("document_version_id", "DOCUMENT_VERSION_ID_MISSING"),
        ("source_id", "SOURCE_ID_MISSING"),
        ("available_time", "AVAILABLE_TIME_MISSING"),
        ("revision_id", "REVISION_ID_MISSING"),
        ("permission_class", "PERMISSION_CLASS_MISSING"),
        ("storage_policy", "STORAGE_POLICY_MISSING"),
        ("manual_review_status", "MANUAL_REVIEW_STATUS_MISSING"),
        ("quality_status", "QUALITY_STATUS_MISSING"),
    ]
    for column, code in non_empty_checks:
        if not rows[column].map(_is_non_empty_text).all():
            issues.append(_issue(run_id, "ERROR", code, f"{column} must be populated for every fixture row.", path))

    if not rows.apply(lambda row: bool(_text(row["source_hash"])) or bool(_text(row["content_hash"])), axis=1).all():
        issues.append(_issue(run_id, "ERROR", "HASH_OR_CONTENT_HASH_MISSING", "Each fixture row needs source_hash or content_hash.", path))
    if not rows["pit_valid"].map(lambda value: _text(value).lower() in {"true", "false"}).all():
        issues.append(_issue(run_id, "ERROR", "PIT_VALID_NOT_EXPLICIT", "pit_valid must be explicit true/false.", path))
    if not rows.apply(lambda row: _timestamp_order_ok(row["published_at"], row["available_time"]), axis=1).all():
        issues.append(_issue(run_id, "ERROR", "PUBLISHED_AFTER_AVAILABLE_TIME", "published_at cannot be after available_time.", path))
    if not rows.apply(lambda row: _timestamp_order_ok(row["period_end"], row["available_time"]), axis=1).all():
        issues.append(_issue(run_id, "ERROR", "PERIOD_END_AFTER_AVAILABLE_TIME", "period_end cannot be after available_time.", path))

    blocked = rows[
        rows["source_type"].eq("BLOCKED_PRIVATE")
        | rows["permission_class"].eq("PROHIBITED")
        | rows["storage_policy"].eq("BLOCKED")
        | rows["rumor_flag"].map(_to_bool)
    ]
    if not blocked.empty and blocked["decision_time_eligible"].map(_to_bool).any():
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "BLOCKED_PRIVATE_RUMOR_DECISION_TIME_ELIGIBLE",
                "Blocked/private/rumor rows cannot be decision-time eligible.",
                path,
            )
        )

    copyrighted = rows[
        rows["source_type"].eq("COPYRIGHTED_NEWS")
        | rows["document_family"].eq("COPYRIGHTED_NEWS_REFERENCE")
        | rows["document_id"].eq("COPYRIGHTED_NEWS_REFERENCE_ONLY_SAMPLE")
    ]
    if not copyrighted.empty and copyrighted["raw_content_stored"].map(_to_bool).any():
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "COPYRIGHTED_NEWS_RAW_CONTENT_STORED",
                "Copyrighted news rows cannot store full raw content.",
                path,
            )
        )
    return issues


def _permission_matrix_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        matrix = pd.read_csv(path, dtype=str).fillna("")
    except Exception as exc:
        return [_issue(run_id, "ERROR", "PERMISSION_MATRIX_UNREADABLE", f"permission matrix cannot be read: {exc}", path)]
    issues: list[dict[str, Any]] = []
    if "source_id_implies_permission" not in matrix.columns:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "PERMISSION_MATRIX_REQUIRED_COLUMNS_MISSING",
                "permission matrix missing source_id_implies_permission.",
                path,
            )
        )
    elif matrix["source_id_implies_permission"].map(_to_bool).any():
        issues.append(_issue(run_id, "ERROR", "SOURCE_ID_IMPLIES_PERMISSION", "source_id is treated as permission.", path))
    return issues


def _candidate_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir()
        and path.name not in VIEW_DIR_NAMES
        and not path.name.startswith("_")
        and any((path / filename).exists() for filename in REQUIRED_ARTIFACTS.values())
    )


def _write(result: RawDocumentStoreSchemaFixtureHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Raw Document Store Schema Fixture Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                "This health view is report-only. It does not create a production raw document store, real source permissions, real data fetches, raw document ingestion, replay-ready evidence, buy-review eligibility, performance validation, API calls, broker behavior, orders, messages, or trading.",
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
        "raw_document_store_schema_fixture_health_created": True,
        **{flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
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


def _timestamp_order_ok(first: Any, second: Any) -> bool:
    first_text = _text(first)
    second_text = _text(second)
    if not first_text or not second_text:
        return True
    first_ts = pd.to_datetime(first_text, errors="coerce")
    second_ts = pd.to_datetime(second_text, errors="coerce")
    if pd.isna(first_ts) or pd.isna(second_ts):
        return False
    return bool(first_ts <= second_ts)


def _contains_secret_like(text: str) -> bool:
    return bool(re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", text.lower()))


def _is_non_empty_text(value: Any) -> bool:
    return bool(_text(value))


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
