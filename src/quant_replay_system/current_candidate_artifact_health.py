"""Local-only health checks for current-candidate artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import CurrentCandidateArtifactHealthSettings, Settings, load_settings
from quant_replay_system.current_candidate_artifact_index import (
    CURRENT_CANDIDATE_INDEX_COLUMNS,
    NO_LIVE_STATEMENTS,
    scan_current_candidate_artifacts,
)


CURRENT_CANDIDATE_HEALTH_LIMITATIONS = [
    "Checks local current-candidate artifacts referenced by the index only.",
    "Does not regenerate candidates, rerun scoring, or repair broken paths.",
    "Does not validate whether a candidate should be approved for paper trading.",
    "Does not place live orders or call broker APIs.",
]

HEALTH_COLUMNS = [
    "artifact_type",
    "run_id",
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
    "MISSING_REQUIRED_CANDIDATE_COLUMN",
}

REQUIRED_PATH_FIELDS = [
    "metadata_path",
    "report_path",
    "candidates_path",
    "factor_dataset_path",
    "scored_dataset_path",
]

REQUIRED_METADATA_FIELDS = ["decision_date", "universe_name", "run_id"]
REQUIRED_CANDIDATE_COLUMNS = ["symbol", "final_score", "action"]


@dataclass(frozen=True)
class CurrentCandidateArtifactHealthPaths:
    artifact_dir: Path
    current_candidate_artifact_health_report: Path
    current_candidate_artifact_health_issues: Path
    current_candidate_artifact_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "current_candidate_artifact_health_report": self.current_candidate_artifact_health_report,
            "current_candidate_artifact_health_issues": self.current_candidate_artifact_health_issues,
            "current_candidate_artifact_health_summary": self.current_candidate_artifact_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CurrentCandidateArtifactHealthResult:
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


def check_current_candidate_artifact_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: Settings | CurrentCandidateArtifactHealthSettings | dict[str, Any] | None = None,
) -> CurrentCandidateArtifactHealthResult:
    """Check indexed current-candidate artifacts for missing or unreadable files."""

    project_settings, health_settings = _resolve_settings(settings)
    if health_settings.enable_live_trading or health_settings.enable_broker_api:
        raise ValueError("Current-candidate artifact health check cannot enable live trading or broker API access")

    index_frame, index_source, base_dir, load_warnings, load_issues = _load_index_for_health(
        index_df=index_df,
        index_path=index_path,
        root=root,
        settings=health_settings,
    )
    checked_count = len(index_frame)
    health_frame = build_current_candidate_artifact_health_frame(
        index_frame,
        base_dir=base_dir,
        settings=health_settings,
    )
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_current_candidate_artifact_health(health_frame, checked_artifact_count=checked_count)
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = generate_current_candidate_health_check_id(
        index_frame,
        index_source=index_source,
        settings=health_settings,
    )
    paths = resolve_current_candidate_artifact_health_paths(
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
        "current_candidate_artifacts_only": True,
        "config_version": health_settings.config_version,
    }
    result = CurrentCandidateArtifactHealthResult(
        status=status,
        checked_artifact_count=checked_count,
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=load_warnings,
        known_limitations=CURRENT_CANDIDATE_HEALTH_LIMITATIONS,
        health_check_id=health_check_id,
        audit_metadata=audit_metadata,
    )
    if health_settings.write_artifacts:
        write_current_candidate_artifact_health_artifacts(result)
    _ = project_settings
    return result


def build_current_candidate_artifact_health_frame(
    index_df: pd.DataFrame,
    *,
    base_dir: str | Path | None = None,
    settings: CurrentCandidateArtifactHealthSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Build one health issue row per current-candidate artifact problem."""

    cfg = _coerce_health_settings(settings)
    index_frame = _prepare_index_frame(index_df)
    issues: list[dict[str, Any]] = []
    base_path = Path(base_dir) if base_dir is not None else None

    for row in index_frame.to_dict("records"):
        if _string_or_empty(row.get("artifact_type")).upper() != "CURRENT_CANDIDATES":
            issues.append(
                _issue(
                    row,
                    path_field="artifact_type",
                    severity="ERROR",
                    issue_code="BROKEN_ARTIFACT_REFERENCE",
                    issue_message="Index row is not a CURRENT_CANDIDATES artifact.",
                    suggested_action="Regenerate current_candidate_artifact_index.csv.",
                )
            )
            continue

        resolved_paths: dict[str, Path | None] = {}
        for path_field in REQUIRED_PATH_FIELDS:
            resolved_paths[path_field] = _check_path(row, path_field, base_path, issues)

        metadata = _check_metadata_file(row, resolved_paths["metadata_path"], cfg, issues)
        _check_snapshot_quality_status(row, metadata, cfg, issues)
        for path_field in ["report_path", "factor_dataset_path", "scored_dataset_path"]:
            _check_file_content(row, path_field, resolved_paths[path_field], cfg, issues)
        _check_candidates_csv(row, resolved_paths["candidates_path"], cfg, issues)

    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_current_candidate_artifact_health(
    health_frame: pd.DataFrame,
    *,
    checked_artifact_count: int,
) -> pd.DataFrame:
    """Summarize current-candidate artifact health issues."""

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


def resolve_current_candidate_artifact_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> CurrentCandidateArtifactHealthPaths:
    """Resolve stable current-candidate health-check artifact paths."""

    artifact_dir = Path(output_dir) / health_check_id
    return CurrentCandidateArtifactHealthPaths(
        artifact_dir=artifact_dir,
        current_candidate_artifact_health_report=artifact_dir / "current_candidate_artifact_health_report.md",
        current_candidate_artifact_health_issues=artifact_dir / "current_candidate_artifact_health_issues.csv",
        current_candidate_artifact_health_summary=artifact_dir / "current_candidate_artifact_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_current_candidate_artifact_health_artifacts(
    result: CurrentCandidateArtifactHealthResult,
) -> dict[str, Path]:
    """Write current-candidate health issues, summary, report, and metadata."""

    paths = CurrentCandidateArtifactHealthPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.health_frame, paths.current_candidate_artifact_health_issues)
    _export_dataframe(result.summary_frame, paths.current_candidate_artifact_health_summary)
    metadata = build_current_candidate_artifact_health_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.current_candidate_artifact_health_report.write_text(
        render_current_candidate_artifact_health_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_current_candidate_artifact_health_metadata(
    result: CurrentCandidateArtifactHealthResult,
    paths: CurrentCandidateArtifactHealthPaths,
) -> dict[str, Any]:
    """Build metadata for current-candidate health-check artifacts."""

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
        "current_candidate_artifacts_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_current_candidate_artifact_health_report(
    result: CurrentCandidateArtifactHealthResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render the markdown current-candidate artifact health report."""

    _ = metadata
    lines = [
        f"# Current Candidate Artifact Health Check: {result.health_check_id}",
        "",
        "No broker or live trading integration was invoked. This health check validates local current-candidate artifacts only.",
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
                "run_id",
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


def generate_current_candidate_health_check_id(
    index_frame: pd.DataFrame,
    *,
    index_source: str,
    settings: CurrentCandidateArtifactHealthSettings,
) -> str:
    """Generate a deterministic health-check id from index identity and settings."""

    frame = _prepare_index_frame(index_frame)
    payload = {
        "index_source": index_source,
        "run_ids": sorted(str(value) for value in frame.get("run_id", pd.Series(dtype="object")).dropna()),
        "strict": settings.strict,
        "empty_candidates_severity": settings.empty_candidates_severity,
        "missing_no_live_statement_severity": settings.missing_no_live_statement_severity,
        "missing_metadata_field_severity": settings.missing_metadata_field_severity,
        "config_version": settings.config_version,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _load_index_for_health(
    *,
    index_df: pd.DataFrame | None,
    index_path: str | Path | None,
    root: str | Path | None,
    settings: CurrentCandidateArtifactHealthSettings,
) -> tuple[pd.DataFrame, str, Path | None, list[str], list[dict[str, Any]]]:
    warnings: list[str] = []
    issues: list[dict[str, Any]] = []
    if index_df is not None:
        return _prepare_index_frame(index_df), "dataframe", None, warnings, issues
    if index_path is not None:
        return _load_index_path(Path(index_path), warnings, issues)
    if root is not None:
        root_path = Path(root)
        return scan_current_candidate_artifacts(root_path), str(root_path), None, warnings, issues
    if settings.index_path.exists():
        return _load_index_path(settings.index_path, warnings, issues)
    warnings.append(f"Index path not found; scanning root instead: {settings.index_path}")
    return scan_current_candidate_artifacts(settings.root_dir), str(settings.root_dir), None, warnings, issues


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
                {"artifact_type": "", "run_id": ""},
                path_field="index_path",
                path_value=path,
                severity="ERROR",
                issue_code="BROKEN_ARTIFACT_REFERENCE",
                issue_message=f"Could not read current-candidate artifact index CSV: {exc}",
                suggested_action="Regenerate current_candidate_artifact_index.csv.",
            )
        )
        warnings.append(f"Could not read index CSV: {path}: {exc}")
        return _prepare_index_frame(pd.DataFrame(columns=CURRENT_CANDIDATE_INDEX_COLUMNS)), str(path), path.parent, warnings, issues
    return _prepare_index_frame(frame), str(path), path.parent, warnings, issues


def _prepare_index_frame(index_df: pd.DataFrame) -> pd.DataFrame:
    frame = index_df.copy(deep=True) if index_df is not None else pd.DataFrame(columns=CURRENT_CANDIDATE_INDEX_COLUMNS)
    for column in CURRENT_CANDIDATE_INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    if frame.empty:
        return frame[CURRENT_CANDIDATE_INDEX_COLUMNS]
    return frame[CURRENT_CANDIDATE_INDEX_COLUMNS].sort_values(["decision_date", "run_id"], na_position="last").reset_index(drop=True)


def _check_path(
    row: dict[str, Any],
    path_field: str,
    base_dir: Path | None,
    issues: list[dict[str, Any]],
) -> Path | None:
    path_value = row.get(path_field, "")
    if not _present(path_value):
        issues.append(
            _issue(
                row,
                path_field=path_field,
                severity="ERROR",
                issue_code="MISSING_PATH_VALUE",
                issue_message=f"Missing required path value: {path_field}.",
                suggested_action="Regenerate the current-candidate artifact index.",
            )
        )
        return None
    path = _resolve_path(path_value, base_dir)
    if not path.exists():
        issues.append(
            _issue(
                row,
                path_field=path_field,
                path_value=path_value,
                severity="ERROR",
                issue_code="FILE_NOT_FOUND",
                issue_message=f"Referenced file does not exist: {path_value}.",
                suggested_action="Regenerate the missing artifact or rebuild the index.",
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
    return path


def _check_metadata_file(
    row: dict[str, Any],
    metadata_path: Path | None,
    settings: CurrentCandidateArtifactHealthSettings,
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
    for field in REQUIRED_METADATA_FIELDS:
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


def _check_snapshot_quality_status(
    row: dict[str, Any],
    metadata: dict[str, Any] | None,
    settings: CurrentCandidateArtifactHealthSettings,
    issues: list[dict[str, Any]],
) -> None:
    if not isinstance(metadata, dict):
        return
    audit = metadata.get("audit_metadata") if isinstance(metadata.get("audit_metadata"), dict) else {}
    if audit.get("snapshot_quality_preflight_enabled") is True and not _present(row.get("snapshot_quality_status")):
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                path_value=row.get("metadata_path", ""),
                severity=_configured_severity(settings.missing_metadata_field_severity, settings),
                issue_code="MISSING_REQUIRED_METADATA_FIELD",
                issue_message="Snapshot preflight was enabled but snapshot_quality_status is missing.",
                suggested_action="Regenerate metadata.json with snapshot quality fields.",
            )
        )


def _check_file_content(
    row: dict[str, Any],
    path_field: str,
    path: Path | None,
    settings: CurrentCandidateArtifactHealthSettings,
    issues: list[dict[str, Any]],
) -> None:
    if path is None:
        return
    suffix = path.suffix.lower()
    if suffix == ".csv":
        _check_csv_readable(row, path_field, path, settings, issues)
    elif suffix == ".md":
        _check_markdown_report(row, path_field, path, settings, issues)
    elif suffix == ".json":
        _check_json_readable(row, path_field, path, issues)


def _check_candidates_csv(
    row: dict[str, Any],
    path: Path | None,
    settings: CurrentCandidateArtifactHealthSettings,
    issues: list[dict[str, Any]],
) -> None:
    if path is None:
        return
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        issues.append(
            _issue(
                row,
                path_field="candidates_path",
                path_value=path,
                severity="ERROR",
                issue_code="CSV_UNREADABLE",
                issue_message=f"candidates.csv could not be read: {exc}",
                suggested_action="Regenerate candidates.csv.",
            )
        )
        return
    if frame.empty:
        issues.append(
            _issue(
                row,
                path_field="candidates_path",
                path_value=path,
                severity=_configured_severity(settings.empty_candidates_severity, settings),
                issue_code="CSV_EMPTY",
                issue_message="candidates.csv has no rows.",
                suggested_action="Confirm no candidates passed filters or regenerate the current-candidate run.",
            )
        )
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
                suggested_action="Regenerate candidates.csv with current-candidate artifact writer.",
            )
        )


def _check_csv_readable(
    row: dict[str, Any],
    path_field: str,
    path: Path,
    settings: CurrentCandidateArtifactHealthSettings,
    issues: list[dict[str, Any]],
) -> None:
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
        return
    if frame.empty and path_field in {"factor_dataset_path", "scored_dataset_path"}:
        issues.append(
            _issue(
                row,
                path_field=path_field,
                path_value=path,
                severity="WARN",
                issue_code="CSV_EMPTY",
                issue_message="Dataset CSV artifact has no rows.",
                suggested_action="Confirm whether empty factor/scored output is expected.",
            )
        )


def _check_json_readable(row: dict[str, Any], path_field: str, path: Path, issues: list[dict[str, Any]]) -> None:
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
    settings: CurrentCandidateArtifactHealthSettings,
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


def _configured_severity(value: str, settings: CurrentCandidateArtifactHealthSettings) -> str:
    if settings.strict:
        return "ERROR"
    return str(value).upper()


def _resolve_path(path_value: Any, base_dir: Path | None) -> Path:
    path = Path(str(path_value))
    if path.is_absolute():
        return path
    candidates = [Path.cwd() / path]
    if base_dir is not None:
        candidates.append(base_dir / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


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
        raise ValueError(f"Unsupported current-candidate health issue_code: {issue_code}")
    return {
        "artifact_type": _string_or_empty(row.get("artifact_type")).upper(),
        "run_id": _string_or_empty(row.get("run_id")),
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
        ["severity", "run_id", "issue_code", "path_field"],
        na_position="last",
    ).reset_index(drop=True)


def _coerce_health_settings(
    settings: CurrentCandidateArtifactHealthSettings | dict[str, Any] | None,
) -> CurrentCandidateArtifactHealthSettings:
    if settings is None:
        return CurrentCandidateArtifactHealthSettings()
    if isinstance(settings, CurrentCandidateArtifactHealthSettings):
        return settings
    if isinstance(settings, dict):
        return CurrentCandidateArtifactHealthSettings(**settings)
    if hasattr(settings, "model_dump"):
        return CurrentCandidateArtifactHealthSettings(**settings.model_dump())
    raise TypeError("settings must be CurrentCandidateArtifactHealthSettings, dict, or None")


def _resolve_settings(
    settings: Settings | CurrentCandidateArtifactHealthSettings | dict[str, Any] | None,
) -> tuple[Settings, CurrentCandidateArtifactHealthSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.current_candidate_artifact_health
    if isinstance(settings, Settings):
        return settings, settings.current_candidate_artifact_health
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, CurrentCandidateArtifactHealthSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.current_candidate_artifact_health.model_dump())
        for key, value in settings.items():
            if key == "current_candidate_artifact_health" and isinstance(value, dict):
                payload.update(value)
            elif key in payload:
                payload[key] = value
        return project, CurrentCandidateArtifactHealthSettings(**payload)
    raise TypeError("settings must be Settings, CurrentCandidateArtifactHealthSettings, dict, or None")


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
