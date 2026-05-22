"""Local-only health checks for indexed data preparation artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import DataPreparationArtifactHealthSettings, Settings, load_settings
from quant_replay_system.data_preparation_artifact_index import (
    DATA_PREP_INDEX_COLUMNS,
    NO_LIVE_STATEMENTS,
    scan_data_preparation_artifacts,
)


DATA_PREP_HEALTH_LIMITATIONS = [
    "Checks local data preparation artifacts referenced by the index only.",
    "Does not rerun data source fetching, ingestion, data quality, snapshot quality, or candidate generation.",
    "Does not repair missing or stale artifact paths.",
    "Does not call market data APIs, connect to brokers, place orders, or automate execution.",
]

HEALTH_COLUMNS = [
    "artifact_type",
    "artifact_id",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]

ISSUE_CODES = {
    "MISSING_PATH_VALUE",
    "FILE_NOT_FOUND",
    "CSV_UNREADABLE",
    "JSON_UNREADABLE",
    "CSV_EMPTY",
    "MISSING_REQUIRED_METADATA_FIELD",
    "MISSING_NO_LIVE_TRADING_STATEMENT",
    "BROKEN_ARTIFACT_REFERENCE",
    "UNSUPPORTED_ARTIFACT_TYPE",
    "INVALID_STATUS",
    "INVALID_NUMERIC_FIELD",
    "MISSING_REQUIRED_CANDIDATE_COLUMN",
}

SUPPORTED_ARTIFACT_TYPES = {"DATA_PIPELINE", "DATA_QUALITY", "SNAPSHOT_QUALITY", "CURRENT_CANDIDATES"}
VALID_STATUS_VALUES = {"PASS", "WARN", "FAIL"}
REQUIRED_CANDIDATE_COLUMNS = ["symbol", "final_score", "action"]

REQUIRED_METADATA_FIELDS = {
    "DATA_PIPELINE": ["pipeline_id", "created_at", "status", "output_files"],
    "DATA_QUALITY": ["quality_run_id", "dataset_type", "created_at", "status", "output_files"],
    "SNAPSHOT_QUALITY": ["snapshot_id", "quality_gate_id", "created_at", "status", "output_files"],
    "CURRENT_CANDIDATES": ["run_id", "decision_date", "universe_name", "created_at", "output_files"],
}

OPTIONAL_PATH_FIELDS = ["snapshot_manifest_path", "processed_path"]


@dataclass(frozen=True)
class DataPreparationArtifactHealthPaths:
    artifact_dir: Path
    data_preparation_artifact_health_report: Path
    data_preparation_artifact_health_issues: Path
    data_preparation_artifact_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "data_preparation_artifact_health_report": self.data_preparation_artifact_health_report,
            "data_preparation_artifact_health_issues": self.data_preparation_artifact_health_issues,
            "data_preparation_artifact_health_summary": self.data_preparation_artifact_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class DataPreparationArtifactHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    health_check_id: str
    audit_metadata: dict[str, Any]


def check_data_preparation_artifact_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: Settings | DataPreparationArtifactHealthSettings | dict[str, Any] | None = None,
) -> DataPreparationArtifactHealthResult:
    """Check indexed data preparation artifacts for missing or unreadable files."""

    project_settings, health_settings = _resolve_settings(settings)
    if health_settings.enable_live_trading or health_settings.enable_broker_api:
        raise ValueError("Data preparation artifact health check cannot enable live trading or broker API access")

    index_frame, index_source, base_dir, load_warnings, load_issues = _load_index_for_health(
        index_df=index_df,
        index_path=index_path,
        root=root,
        settings=health_settings,
    )
    checked_count = len(index_frame)
    health_frame = build_data_preparation_artifact_health_frame(
        index_frame,
        base_dir=base_dir,
        settings=health_settings,
    )
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_data_preparation_artifact_health(health_frame, checked_artifact_count=checked_count)
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = generate_data_preparation_health_check_id(
        index_frame,
        index_source=index_source,
        settings=health_settings,
    )
    paths = resolve_data_preparation_artifact_health_paths(
        Path(output_dir) if output_dir is not None else health_settings.output_dir,
        health_check_id,
    )
    audit_metadata = {
        "health_check_id": health_check_id,
        "index_source": index_source,
        "checked_artifact_count": checked_count,
        "strict": health_settings.strict,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "network_api_calls_used_in_tests": False,
        "data_preparation_artifacts_only": True,
        "config_version": health_settings.config_version,
    }
    result = DataPreparationArtifactHealthResult(
        status=status,
        checked_artifact_count=checked_count,
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=load_warnings,
        known_limitations=DATA_PREP_HEALTH_LIMITATIONS,
        health_check_id=health_check_id,
        audit_metadata=audit_metadata,
    )
    if health_settings.write_artifacts:
        write_data_preparation_artifact_health_artifacts(result)
    _ = project_settings
    return result


def build_data_preparation_artifact_health_frame(
    index_df: pd.DataFrame,
    *,
    base_dir: str | Path | None = None,
    settings: DataPreparationArtifactHealthSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Build one health issue row per data preparation artifact problem."""

    cfg = _coerce_health_settings(settings)
    index_frame = _prepare_index_frame(index_df)
    issues: list[dict[str, Any]] = []
    base_path = Path(base_dir) if base_dir is not None else None

    for row in index_frame.to_dict("records"):
        artifact_type = _artifact_type(row)
        artifact_id = _string_or_empty(row.get("artifact_id"))
        if not artifact_type:
            issues.append(
                _issue(
                    row,
                    path_field="artifact_type",
                    severity="ERROR",
                    issue_code="BROKEN_ARTIFACT_REFERENCE",
                    issue_message="Index row is missing artifact_type.",
                    suggested_action="Regenerate data_preparation_artifact_index.csv.",
                )
            )
            continue
        if artifact_type not in SUPPORTED_ARTIFACT_TYPES:
            issues.append(
                _issue(
                    row,
                    path_field="artifact_type",
                    severity="ERROR",
                    issue_code="UNSUPPORTED_ARTIFACT_TYPE",
                    issue_message=f"Unsupported artifact_type: {artifact_type}.",
                    suggested_action="Regenerate the data preparation index or filter unsupported rows.",
                )
            )
            continue
        if not artifact_id:
            issues.append(
                _issue(
                    row,
                    path_field="artifact_id",
                    severity="ERROR",
                    issue_code="BROKEN_ARTIFACT_REFERENCE",
                    issue_message="Index row is missing artifact_id.",
                    suggested_action="Regenerate data_preparation_artifact_index.csv.",
                )
            )

        metadata_path = _check_single_path(row, "metadata_path", base_path, issues, required=True, settings=cfg)
        metadata = _check_metadata_file(row, metadata_path, cfg, issues)

        report_path = _check_single_path(row, "report_path", base_path, issues, required=True, settings=cfg)
        _check_file_content(row, "report_path", report_path, cfg, issues)

        _check_status_fields(row, metadata, cfg, issues)
        _check_numeric_fields(row, cfg, issues)

        if artifact_type == "CURRENT_CANDIDATES":
            candidates_path = _check_single_path(
                row,
                "candidates_path",
                base_path,
                issues,
                required=True,
                settings=cfg,
            )
            _check_candidates_csv(row, candidates_path, cfg, issues)
        elif _present(row.get("candidates_path")):
            for path in _path_values(row.get("candidates_path"), base_path):
                resolved = _check_path_value(row, "candidates_path", path, issues, required=False, settings=cfg)
                _check_file_content(row, "candidates_path", resolved, cfg, issues)

        for path_field in OPTIONAL_PATH_FIELDS:
            values = _path_values(row.get(path_field), base_path)
            if not values:
                if _optional_path_expected(artifact_type, path_field):
                    issues.append(
                        _issue(
                            row,
                            path_field=path_field,
                            severity=_configured_severity(cfg.missing_optional_field_severity, cfg),
                            issue_code="MISSING_PATH_VALUE",
                            issue_message=f"Optional artifact path is missing: {path_field}.",
                            suggested_action="Confirm this output was intentionally skipped or regenerate the artifact.",
                        )
                    )
                continue
            for path in values:
                resolved = _check_path_value(row, path_field, path, issues, required=False, settings=cfg)
                _check_file_content(row, path_field, resolved, cfg, issues)

    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_data_preparation_artifact_health(
    health_frame: pd.DataFrame,
    *,
    checked_artifact_count: int,
) -> pd.DataFrame:
    """Summarize data preparation artifact health issues."""

    frame = _finalize_health_frame(health_frame)
    issue_count = len(frame)
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARN").sum()) if not frame.empty else 0
    info_count = int((frame["severity"] == "INFO").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    rows = [
        {
            "status": status,
            "checked_artifact_count": checked_artifact_count,
            "issue_count": issue_count,
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count,
        }
    ]
    if not frame.empty:
        for issue_code, group in frame.groupby("issue_code", dropna=False):
            rows.append(
                {
                    "status": status,
                    "checked_artifact_count": checked_artifact_count,
                    "issue_count": len(group),
                    "error_count": int((group["severity"] == "ERROR").sum()),
                    "warning_count": int((group["severity"] == "WARN").sum()),
                    "info_count": int((group["severity"] == "INFO").sum()),
                    "issue_code": issue_code,
                }
            )
    return pd.DataFrame(rows)


def resolve_data_preparation_artifact_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> DataPreparationArtifactHealthPaths:
    """Resolve stable health-check artifact paths."""

    artifact_dir = Path(output_dir) / health_check_id
    return DataPreparationArtifactHealthPaths(
        artifact_dir=artifact_dir,
        data_preparation_artifact_health_report=artifact_dir / "data_preparation_artifact_health_report.md",
        data_preparation_artifact_health_issues=artifact_dir / "data_preparation_artifact_health_issues.csv",
        data_preparation_artifact_health_summary=artifact_dir / "data_preparation_artifact_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_data_preparation_artifact_health_artifacts(
    result: DataPreparationArtifactHealthResult,
) -> dict[str, Path]:
    """Write data preparation health issues, summary, report, and metadata."""

    paths = DataPreparationArtifactHealthPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.health_frame, paths.data_preparation_artifact_health_issues)
    _export_dataframe(result.summary_frame, paths.data_preparation_artifact_health_summary)
    metadata = build_data_preparation_artifact_health_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.data_preparation_artifact_health_report.write_text(
        render_data_preparation_artifact_health_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_data_preparation_artifact_health_metadata(
    result: DataPreparationArtifactHealthResult,
    paths: DataPreparationArtifactHealthPaths,
) -> dict[str, Any]:
    """Build metadata for data preparation health-check artifacts."""

    return {
        "health_check_id": result.health_check_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "config_summary": {
            "index_source": result.audit_metadata.get("index_source", ""),
            "strict": bool(result.audit_metadata.get("strict", False)),
            "config_version": result.audit_metadata.get("config_version", ""),
        },
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "network_api_calls_used_in_tests": False,
        "data_preparation_artifacts_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_data_preparation_artifact_health_report(
    result: DataPreparationArtifactHealthResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render a markdown data preparation artifact health report."""

    _ = metadata
    lines = [
        f"# Data Preparation Artifact Health Check: {result.health_check_id}",
        "",
        "No broker or live trading integration was invoked. This health check validates local data preparation artifacts only.",
        "",
        "## Health Summary",
        "",
        _markdown_table(
            result.summary_frame,
            [
                "status",
                "checked_artifact_count",
                "issue_count",
                "error_count",
                "warning_count",
                "info_count",
                "issue_code",
            ],
        ),
        "",
        "## Issues",
        "",
        _markdown_table(
            result.health_frame,
            [
                "artifact_type",
                "artifact_id",
                "path_field",
                "severity",
                "issue_code",
                "issue_message",
                "suggested_action",
            ],
            max_rows=100,
        ),
        "",
        "## Warnings",
        "",
        _warnings_section(result.warnings),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in result.known_limitations),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def generate_data_preparation_health_check_id(
    index_frame: pd.DataFrame,
    *,
    index_source: str,
    settings: DataPreparationArtifactHealthSettings,
) -> str:
    """Generate a deterministic health-check id from index identity and settings."""

    frame = _prepare_index_frame(index_frame)
    payload = {
        "index_source": index_source,
        "artifact_ids": sorted(str(value) for value in frame.get("artifact_id", pd.Series(dtype="object")).dropna()),
        "artifact_types": sorted(str(value) for value in frame.get("artifact_type", pd.Series(dtype="object")).dropna()),
        "strict": settings.strict,
        "empty_candidates_severity": settings.empty_candidates_severity,
        "missing_no_live_statement_severity": settings.missing_no_live_statement_severity,
        "missing_metadata_field_severity": settings.missing_metadata_field_severity,
        "missing_optional_field_severity": settings.missing_optional_field_severity,
        "config_version": settings.config_version,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _load_index_for_health(
    *,
    index_df: pd.DataFrame | None,
    index_path: str | Path | None,
    root: str | Path | None,
    settings: DataPreparationArtifactHealthSettings,
) -> tuple[pd.DataFrame, str, Path | None, list[str], list[dict[str, Any]]]:
    warnings: list[str] = []
    issues: list[dict[str, Any]] = []
    if index_df is not None:
        return _prepare_index_frame(index_df), "dataframe", None, warnings, issues
    if index_path is not None:
        return _load_index_path(Path(index_path), warnings, issues)
    if root is not None:
        root_path = Path(root)
        return scan_data_preparation_artifacts(root_path), str(root_path), None, warnings, issues
    if settings.index_path.exists():
        return _load_index_path(settings.index_path, warnings, issues)
    warnings.append(f"Index path not found; scanning root instead: {settings.index_path}")
    return scan_data_preparation_artifacts(settings.root_dir), str(settings.root_dir), None, warnings, issues


def _load_index_path(
    path: Path,
    warnings: list[str],
    issues: list[dict[str, Any]],
) -> tuple[pd.DataFrame, str, Path | None, list[str], list[dict[str, Any]]]:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        issues.append(
            _issue(
                {"artifact_type": "", "artifact_id": ""},
                path_field="index_path",
                path_value=path,
                severity="ERROR",
                issue_code="BROKEN_ARTIFACT_REFERENCE",
                issue_message=f"Could not read data preparation artifact index CSV: {exc}",
                suggested_action="Regenerate data_preparation_artifact_index.csv.",
            )
        )
        warnings.append(f"Could not read index CSV: {path}: {exc}")
        return _prepare_index_frame(pd.DataFrame(columns=DATA_PREP_INDEX_COLUMNS)), str(path), path.parent, warnings, issues
    return _prepare_index_frame(frame), str(path), path.parent, warnings, issues


def _prepare_index_frame(index_df: pd.DataFrame) -> pd.DataFrame:
    frame = index_df.copy(deep=True) if index_df is not None else pd.DataFrame(columns=DATA_PREP_INDEX_COLUMNS)
    for column in DATA_PREP_INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    if frame.empty:
        return frame[DATA_PREP_INDEX_COLUMNS]
    return frame[DATA_PREP_INDEX_COLUMNS].sort_values(["artifact_type", "artifact_id"], na_position="last").reset_index(drop=True)


def _artifact_type(row: dict[str, Any]) -> str:
    return _string_or_empty(row.get("artifact_type")).upper()


def _check_metadata_file(
    row: dict[str, Any],
    metadata_path: Path | None,
    settings: DataPreparationArtifactHealthSettings,
    issues: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if metadata_path is None:
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception as exc:
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                path_value=metadata_path,
                severity="ERROR",
                issue_code="JSON_UNREADABLE",
                issue_message=f"Metadata JSON could not be read: {exc}",
                suggested_action="Regenerate metadata.json for this artifact.",
            )
        )
        return None
    for field in REQUIRED_METADATA_FIELDS.get(_artifact_type(row), []):
        if field not in metadata:
            issues.append(
                _issue(
                    row,
                    path_field="metadata_path",
                    path_value=metadata_path,
                    severity=_configured_severity(settings.missing_metadata_field_severity, settings),
                    issue_code="MISSING_REQUIRED_METADATA_FIELD",
                    issue_message=f"Metadata is missing required field: {field}.",
                    suggested_action="Regenerate metadata.json with the current artifact writer.",
                )
            )
    return metadata


def _check_status_fields(
    row: dict[str, Any],
    metadata: dict[str, Any] | None,
    settings: DataPreparationArtifactHealthSettings,
    issues: list[dict[str, Any]],
) -> None:
    artifact_type = _artifact_type(row)
    status = _string_or_empty(row.get("status") or (metadata or {}).get("status")).upper()
    if artifact_type == "SNAPSHOT_QUALITY" and status and status not in VALID_STATUS_VALUES:
        issues.append(
            _issue(
                row,
                path_field="status",
                severity="ERROR",
                issue_code="INVALID_STATUS",
                issue_message=f"Snapshot-quality status must be PASS, WARN, or FAIL; found {status}.",
                suggested_action="Regenerate the snapshot-quality artifact metadata and index.",
            )
        )
    _ = settings


def _check_numeric_fields(
    row: dict[str, Any],
    settings: DataPreparationArtifactHealthSettings,
    issues: list[dict[str, Any]],
) -> None:
    if _artifact_type(row) != "DATA_QUALITY":
        return
    for field in ["issue_count", "warning_count", "error_count"]:
        value = row.get(field)
        if not _present(value):
            continue
        try:
            int(value)
        except (TypeError, ValueError):
            issues.append(
                _issue(
                    row,
                    path_field=field,
                    severity="ERROR",
                    issue_code="INVALID_NUMERIC_FIELD",
                    issue_message=f"Data-quality {field} must be numeric when present.",
                    suggested_action="Regenerate the data preparation index from data-quality metadata.",
                )
            )
    _ = settings


def _check_single_path(
    row: dict[str, Any],
    path_field: str,
    base_dir: Path | None,
    issues: list[dict[str, Any]],
    *,
    required: bool,
    settings: DataPreparationArtifactHealthSettings,
) -> Path | None:
    values = _path_values(row.get(path_field), base_dir)
    if not values:
        if required:
            issues.append(
                _issue(
                    row,
                    path_field=path_field,
                    severity="ERROR",
                    issue_code="MISSING_PATH_VALUE",
                    issue_message=f"Missing required path value: {path_field}.",
                    suggested_action="Regenerate the data preparation artifact index.",
                )
            )
        return None
    return _check_path_value(row, path_field, values[0], issues, required=required, settings=settings)


def _check_path_value(
    row: dict[str, Any],
    path_field: str,
    path_value: Any,
    issues: list[dict[str, Any]],
    *,
    required: bool,
    settings: DataPreparationArtifactHealthSettings,
) -> Path | None:
    if not _present(path_value):
        if required:
            issues.append(
                _issue(
                    row,
                    path_field=path_field,
                    severity="ERROR",
                    issue_code="MISSING_PATH_VALUE",
                    issue_message=f"Missing required path value: {path_field}.",
                    suggested_action="Regenerate the data preparation artifact index.",
                )
            )
        return None
    path = Path(str(path_value))
    if not path.exists():
        issues.append(
            _issue(
                row,
                path_field=path_field,
                path_value=path_value,
                severity="ERROR",
                issue_code="FILE_NOT_FOUND",
                issue_message=f"Referenced file does not exist: {path_value}.",
                suggested_action="Regenerate the missing artifact or rebuild the data preparation index.",
            )
        )
        return None
    if path.is_dir():
        issues.append(
            _issue(
                row,
                path_field=path_field,
                path_value=path_value,
                severity="ERROR",
                issue_code="BROKEN_ARTIFACT_REFERENCE",
                issue_message=f"Referenced path is a directory, not a file: {path_value}.",
                suggested_action="Regenerate the index with file paths.",
            )
        )
        return None
    _ = settings
    return path


def _path_values(value: Any, base_dir: Path | None) -> list[Path]:
    if not _present(value):
        return []
    raw = str(value).strip()
    parsed: Any = raw
    if raw.startswith("{") or raw.startswith("["):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
    if isinstance(parsed, dict):
        values = [item for item in parsed.values() if _present(item)]
    elif isinstance(parsed, list):
        values = [item for item in parsed if _present(item)]
    else:
        values = [part.strip() for part in str(parsed).split(";") if part.strip()]
    paths: list[Path] = []
    for item in values:
        path = Path(str(item))
        if not path.is_absolute():
            candidates = [Path.cwd() / path]
            if base_dir is not None:
                candidates.append(base_dir / path)
            path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
        paths.append(path)
    return paths


def _optional_path_expected(artifact_type: str, path_field: str) -> bool:
    if artifact_type != "DATA_PIPELINE":
        return False
    return path_field in {"snapshot_manifest_path", "processed_path"}


def _check_file_content(
    row: dict[str, Any],
    path_field: str,
    path: Path | None,
    settings: DataPreparationArtifactHealthSettings,
    issues: list[dict[str, Any]],
) -> None:
    if path is None:
        return
    suffix = path.suffix.lower()
    if suffix == ".csv":
        _check_csv_file(row, path_field, path, settings, issues)
    elif suffix == ".json":
        _check_json_file(row, path_field, path, issues)
    elif suffix == ".md":
        _check_markdown_report(row, path_field, path, settings, issues)


def _check_csv_file(
    row: dict[str, Any],
    path_field: str,
    path: Path,
    settings: DataPreparationArtifactHealthSettings,
    issues: list[dict[str, Any]],
) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        issues.append(
            _issue(
                row,
                path_field=path_field,
                path_value=path,
                severity="ERROR",
                issue_code="CSV_UNREADABLE",
                issue_message=f"CSV file could not be read: {exc}",
                suggested_action="Regenerate the CSV artifact.",
            )
        )
        return None
    if frame.empty and path_field == "candidates_path":
        issues.append(
            _issue(
                row,
                path_field=path_field,
                path_value=path,
                severity=_configured_severity(settings.empty_candidates_severity, settings),
                issue_code="CSV_EMPTY",
                issue_message="Current-candidate candidates.csv has no rows.",
                suggested_action="Confirm no candidates passed filters or regenerate the current-candidate run.",
            )
        )
    return frame


def _check_candidates_csv(
    row: dict[str, Any],
    path: Path | None,
    settings: DataPreparationArtifactHealthSettings,
    issues: list[dict[str, Any]],
) -> None:
    if path is None:
        return
    frame = _check_csv_file(row, "candidates_path", path, settings, issues)
    if frame is None:
        return
    missing = sorted(set(REQUIRED_CANDIDATE_COLUMNS).difference(frame.columns))
    if missing:
        issues.append(
            _issue(
                row,
                path_field="candidates_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_REQUIRED_CANDIDATE_COLUMN",
                issue_message=f"candidates.csv missing required columns: {', '.join(missing)}.",
                suggested_action="Regenerate candidates.csv with the current-candidate artifact writer.",
            )
        )


def _check_json_file(row: dict[str, Any], path_field: str, path: Path, issues: list[dict[str, Any]]) -> None:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        issues.append(
            _issue(
                row,
                path_field=path_field,
                path_value=path,
                severity="ERROR",
                issue_code="JSON_UNREADABLE",
                issue_message=f"JSON file could not be read: {exc}",
                suggested_action="Regenerate the JSON artifact.",
            )
        )


def _check_markdown_report(
    row: dict[str, Any],
    path_field: str,
    path: Path,
    settings: DataPreparationArtifactHealthSettings,
    issues: list[dict[str, Any]],
) -> None:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(
            _issue(
                row,
                path_field=path_field,
                path_value=path,
                severity="ERROR",
                issue_code="BROKEN_ARTIFACT_REFERENCE",
                issue_message=f"Markdown report could not be read: {exc}",
                suggested_action="Regenerate the markdown artifact.",
            )
        )
        return
    if not any(statement in content for statement in NO_LIVE_STATEMENTS):
        issues.append(
            _issue(
                row,
                path_field=path_field,
                path_value=path,
                severity=_configured_severity(settings.missing_no_live_statement_severity, settings),
                issue_code="MISSING_NO_LIVE_TRADING_STATEMENT",
                issue_message="Markdown report is missing the no-live-trading statement.",
                suggested_action="Regenerate the report with the local-only safety statement.",
            )
        )


def _configured_severity(value: str, settings: DataPreparationArtifactHealthSettings) -> str:
    if settings.strict:
        return "ERROR"
    return str(value).upper()


def _issue(
    row: dict[str, Any],
    *,
    path_field: str,
    severity: str,
    issue_code: str,
    issue_message: str,
    suggested_action: str,
    path_value: Any | None = None,
) -> dict[str, Any]:
    if issue_code not in ISSUE_CODES:
        raise ValueError(f"Unsupported data preparation health issue_code: {issue_code}")
    return {
        "artifact_type": _artifact_type(row),
        "artifact_id": _string_or_empty(row.get("artifact_id")),
        "path_field": path_field,
        "path_value": _string_or_empty(path_value if path_value is not None else row.get(path_field, "")),
        "severity": str(severity).upper(),
        "issue_code": issue_code,
        "issue_message": issue_message,
        "suggested_action": suggested_action,
    }


def _finalize_health_frame(frame: pd.DataFrame) -> pd.DataFrame:
    health = frame.copy(deep=True)
    for column in HEALTH_COLUMNS:
        if column not in health.columns:
            health[column] = ""
    if health.empty:
        return health[HEALTH_COLUMNS]
    return health[HEALTH_COLUMNS].sort_values(
        ["severity", "artifact_type", "artifact_id", "issue_code", "path_field"],
        na_position="last",
    ).reset_index(drop=True)


def _coerce_health_settings(
    settings: DataPreparationArtifactHealthSettings | dict[str, Any] | None,
) -> DataPreparationArtifactHealthSettings:
    if settings is None:
        return DataPreparationArtifactHealthSettings()
    if isinstance(settings, DataPreparationArtifactHealthSettings):
        return settings
    if isinstance(settings, dict):
        return DataPreparationArtifactHealthSettings(**settings)
    if hasattr(settings, "model_dump"):
        return DataPreparationArtifactHealthSettings(**settings.model_dump())
    raise TypeError("settings must be DataPreparationArtifactHealthSettings, dict, or None")


def _resolve_settings(
    settings: Settings | DataPreparationArtifactHealthSettings | dict[str, Any] | None,
) -> tuple[Settings, DataPreparationArtifactHealthSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.data_preparation_artifact_health
    if isinstance(settings, Settings):
        return settings, settings.data_preparation_artifact_health
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, DataPreparationArtifactHealthSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.data_preparation_artifact_health.model_dump())
        for key, value in settings.items():
            if key == "data_preparation_artifact_health" and isinstance(value, dict):
                payload.update(value)
            elif key in payload:
                payload[key] = value
        return project, DataPreparationArtifactHealthSettings(**payload)
    raise TypeError("settings must be Settings, DataPreparationArtifactHealthSettings, dict, or None")


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    export = _sanitize_dataframe_for_export(frame)
    path.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(path, index=False)


def _sanitize_dataframe_for_export(frame: pd.DataFrame) -> pd.DataFrame:
    export = frame.copy(deep=True)
    for column in export.columns:
        if pd.api.types.is_datetime64_any_dtype(export[column]):
            export[column] = export[column].dt.strftime("%Y-%m-%d %H:%M:%S")
        elif export[column].dtype == "object":
            export[column] = export[column].map(_cell_to_export_value)
    return export


def _cell_to_export_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True)
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return value


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 50) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "_No rows._"
    table = frame[available].head(max_rows).copy()
    rows = [
        "| " + " | ".join(available) + " |",
        "| " + " | ".join("---" for _ in available) + " |",
    ]
    for record in table.to_dict("records"):
        rows.append("| " + " | ".join(_format_markdown_value(record[column]) for column in available) + " |")
    return "\n".join(rows)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)


def _format_markdown_value(value: Any) -> str:
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        return f"{value:.6f}"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True).replace("|", "\\|")
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).replace("|", "\\|").replace("\n", " ")


def _present(value: Any) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    return str(value).strip() != ""


def _string_or_empty(value: Any) -> str:
    return str(value).strip() if _present(value) else ""


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
