"""Local-only health checks for indexed paper-trading artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import PaperArtifactHealthSettings, Settings, load_settings
from quant_replay_system.paper_artifact_index import INDEX_COLUMNS, NO_LIVE_STATEMENTS, scan_paper_trading_artifacts


PAPER_ARTIFACT_HEALTH_LIMITATIONS = [
    "Checks local paper-trading artifacts referenced by the index only.",
    "Does not regenerate reports, rerun reconciliation, or repair broken paths.",
    "Does not place live orders or call broker APIs.",
    "CSV readability checks are schema-light in MVP v0.1.",
]

HEALTH_COLUMNS = [
    "artifact_type",
    "artifact_id",
    "path_field",
    "path_value",
    "severity",
    "actionability",
    "issue_code",
    "issue_message",
    "suggested_action",
]

EXPECTED_DEMO_WARNING = "EXPECTED_DEMO_WARNING"
STALE_ARTIFACT_WARNING = "STALE_ARTIFACT_WARNING"
ACTIONABLE_WARNING = "ACTIONABLE_WARNING"
BLOCKING_ERROR = "BLOCKING_ERROR"

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
}

SUPPORTED_ARTIFACT_TYPES = {"DAILY", "REVIEW", "RECONCILIATION"}

REQUIRED_METADATA_FIELDS = {
    "DAILY": [
        "journal_id",
        "created_at",
        "output_files",
        "live_trading_enabled",
        "broker_api_invoked",
        "paper_trading_only",
    ],
    "REVIEW": [
        "review_id",
        "created_at",
        "output_files",
        "live_trading_enabled",
        "broker_api_invoked",
        "paper_trading_only",
    ],
    "RECONCILIATION": [
        "reconciliation_id",
        "created_at",
        "status",
        "output_files",
        "live_trading_enabled",
        "broker_api_invoked",
        "paper_trading_only",
    ],
}

BASE_REQUIRED_PATH_FIELDS = {
    "DAILY": ["report_path", "metadata_path", "decisions_path", "fills_path"],
    "REVIEW": ["report_path", "metadata_path", "reviewed_decisions_path"],
    "RECONCILIATION": ["report_path", "metadata_path", "reconciliation_report_path"],
}


@dataclass(frozen=True)
class PaperArtifactHealthArtifactPaths:
    artifact_dir: Path
    artifact_health_report: Path
    artifact_health_issues: Path
    artifact_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "artifact_health_report": self.artifact_health_report,
            "artifact_health_issues": self.artifact_health_issues,
            "artifact_health_summary": self.artifact_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PaperArtifactHealthResult:
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


def check_paper_artifact_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: Settings | PaperArtifactHealthSettings | dict[str, Any] | None = None,
) -> PaperArtifactHealthResult:
    """Check indexed paper artifacts for missing or unreadable files."""

    project_settings, health_settings = _resolve_settings(settings)
    if health_settings.enable_live_trading or health_settings.enable_broker_api:
        raise ValueError("Paper artifact health check cannot enable live trading or broker API access")

    index_frame, index_source, base_dir, load_warnings, load_issues = _load_index_for_health(
        index_df=index_df,
        index_path=index_path,
        root=root,
        settings=health_settings,
    )
    checked_count = _checked_artifact_count(index_frame)
    health_frame = build_artifact_health_frame(index_frame, base_dir=base_dir, settings=health_settings)
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
        health_frame = classify_paper_artifact_health_actionability(health_frame, index_frame)
    summary_frame = summarize_artifact_health(health_frame, checked_artifact_count=checked_count)
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = generate_health_check_id(
        index_frame,
        index_source=index_source,
        settings=health_settings,
    )
    paths = resolve_paper_artifact_health_paths(
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
        "paper_trading_only": True,
        "config_version": health_settings.config_version,
    }
    result = PaperArtifactHealthResult(
        status=status,
        checked_artifact_count=checked_count,
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=load_warnings,
        known_limitations=PAPER_ARTIFACT_HEALTH_LIMITATIONS,
        health_check_id=health_check_id,
        audit_metadata=audit_metadata,
    )
    if health_settings.write_artifacts:
        write_paper_artifact_health_artifacts(result)
    _ = project_settings
    return result


def build_artifact_health_frame(
    index_df: pd.DataFrame,
    *,
    base_dir: str | Path | None = None,
    settings: PaperArtifactHealthSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Build one health issue row per artifact-path problem."""

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
                    suggested_action="Regenerate paper_artifact_index.csv.",
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
                    suggested_action="Regenerate the index or filter unsupported rows.",
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
                    suggested_action="Regenerate paper_artifact_index.csv.",
                )
            )

        metadata_path = _check_path(row, "metadata_path", base_path, issues, required=True)
        metadata = _check_metadata_file(row, metadata_path, cfg, issues)

        path_fields = _required_path_fields(row, metadata)
        for path_field in path_fields:
            if path_field == "metadata_path":
                continue
            resolved = _check_path(row, path_field, base_path, issues, required=True)
            _check_file_content(row, path_field, resolved, cfg, issues)

        for path_field in _optional_provided_path_fields(row, path_fields):
            resolved = _check_path(row, path_field, base_path, issues, required=False)
            _check_file_content(row, path_field, resolved, cfg, issues)

    health_frame = _finalize_health_frame(pd.DataFrame(issues))
    return classify_paper_artifact_health_actionability(health_frame, index_frame)


def classify_paper_artifact_health_actionability(
    health_frame: pd.DataFrame,
    index_df: pd.DataFrame,
) -> pd.DataFrame:
    """Classify health issues by whether they are expected demo warnings or actionable."""

    frame = _finalize_health_frame(health_frame)
    if frame.empty:
        return frame
    index_frame = _prepare_index_frame(index_df)
    metadata_by_artifact = _metadata_by_artifact(index_frame)
    records = []
    for row in frame.to_dict("records"):
        row = dict(row)
        if _string_or_empty(row.get("actionability")):
            records.append(row)
            continue
        row["actionability"] = _issue_actionability(row, metadata_by_artifact)
        records.append(row)
    return _finalize_health_frame(pd.DataFrame(records))


def summarize_artifact_health(
    health_frame: pd.DataFrame,
    *,
    checked_artifact_count: int,
) -> pd.DataFrame:
    """Summarize artifact health issues."""

    frame = _finalize_health_frame(health_frame)
    issue_count = len(frame)
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARN").sum()) if not frame.empty else 0
    info_count = int((frame["severity"] == "INFO").sum()) if not frame.empty else 0
    expected_demo_warning_count = int((frame["actionability"] == EXPECTED_DEMO_WARNING).sum()) if not frame.empty else 0
    stale_warning_count = int((frame["actionability"] == STALE_ARTIFACT_WARNING).sum()) if not frame.empty else 0
    actionable_warning_count = int((frame["actionability"] == ACTIONABLE_WARNING).sum()) if not frame.empty else 0
    blocking_error_count = int((frame["actionability"] == BLOCKING_ERROR).sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    rows = [
        {
            "status": status,
            "checked_artifact_count": checked_artifact_count,
            "issue_count": issue_count,
            "error_count": error_count,
            "warning_count": warning_count,
            "total_warning_count": warning_count,
            "expected_demo_warning_count": expected_demo_warning_count,
            "stale_warning_count": stale_warning_count,
            "actionable_warning_count": actionable_warning_count,
            "blocking_error_count": blocking_error_count,
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
                    "total_warning_count": int((group["severity"] == "WARN").sum()),
                    "expected_demo_warning_count": int((group["actionability"] == EXPECTED_DEMO_WARNING).sum()),
                    "stale_warning_count": int((group["actionability"] == STALE_ARTIFACT_WARNING).sum()),
                    "actionable_warning_count": int((group["actionability"] == ACTIONABLE_WARNING).sum()),
                    "blocking_error_count": int((group["actionability"] == BLOCKING_ERROR).sum()),
                    "info_count": int((group["severity"] == "INFO").sum()),
                    "issue_code": issue_code,
                }
            )
    return pd.DataFrame(rows)


def resolve_paper_artifact_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> PaperArtifactHealthArtifactPaths:
    """Resolve stable health-check artifact paths."""

    artifact_dir = Path(output_dir) / health_check_id
    return PaperArtifactHealthArtifactPaths(
        artifact_dir=artifact_dir,
        artifact_health_report=artifact_dir / "artifact_health_report.md",
        artifact_health_issues=artifact_dir / "artifact_health_issues.csv",
        artifact_health_summary=artifact_dir / "artifact_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_paper_artifact_health_report(
    result: PaperArtifactHealthResult,
    path: str | Path | None = None,
) -> Path:
    """Write only the markdown artifact health report."""

    paths = PaperArtifactHealthArtifactPaths(**result.artifact_paths)
    report_path = Path(path) if path is not None else paths.artifact_health_report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_paper_artifact_health_report(result), encoding="utf-8")
    return report_path


def write_paper_artifact_health_artifacts(result: PaperArtifactHealthResult) -> dict[str, Path]:
    """Write health issues, summary, report, and metadata."""

    paths = PaperArtifactHealthArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.health_frame, paths.artifact_health_issues)
    _export_dataframe(result.summary_frame, paths.artifact_health_summary)
    metadata = build_paper_artifact_health_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.artifact_health_report.write_text(render_paper_artifact_health_report(result, metadata), encoding="utf-8")
    return paths.as_dict()


def build_paper_artifact_health_metadata(
    result: PaperArtifactHealthResult,
    paths: PaperArtifactHealthArtifactPaths,
) -> dict[str, Any]:
    """Build metadata for health-check artifacts."""

    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    return {
        "health_check_id": result.health_check_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "total_warning_count": _int_or_zero(summary.get("total_warning_count")),
        "expected_demo_warning_count": _int_or_zero(summary.get("expected_demo_warning_count")),
        "stale_warning_count": _int_or_zero(summary.get("stale_warning_count")),
        "actionable_warning_count": _int_or_zero(summary.get("actionable_warning_count")),
        "blocking_error_count": _int_or_zero(summary.get("blocking_error_count")),
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
        "paper_trading_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_paper_artifact_health_report(
    result: PaperArtifactHealthResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render the markdown health-check report."""

    _ = metadata
    lines = [
        f"# Paper Trading Artifact Health Check: {result.health_check_id}",
        "",
        "No broker or live trading integration was invoked. This health check validates local artifact files only.",
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
                "total_warning_count",
                "expected_demo_warning_count",
                "stale_warning_count",
                "actionable_warning_count",
                "blocking_error_count",
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
                "actionability",
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


def generate_health_check_id(
    index_frame: pd.DataFrame,
    *,
    index_source: str,
    settings: PaperArtifactHealthSettings,
) -> str:
    """Generate a deterministic health-check id from index identity and settings."""

    frame = _prepare_index_frame(index_frame)
    payload = {
        "index_source": index_source,
        "artifact_ids": sorted(str(value) for value in frame.get("artifact_id", pd.Series(dtype="object")).dropna()),
        "artifact_types": sorted(str(value) for value in frame.get("artifact_type", pd.Series(dtype="object")).dropna()),
        "strict": settings.strict,
        "empty_csv_severity": settings.empty_csv_severity,
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
    settings: PaperArtifactHealthSettings,
) -> tuple[pd.DataFrame, str, Path | None, list[str], list[dict[str, Any]]]:
    warnings: list[str] = []
    issues: list[dict[str, Any]] = []
    if index_df is not None:
        return _prepare_index_frame(index_df), "dataframe", None, warnings, issues
    if index_path is not None:
        return _load_index_path(Path(index_path), warnings, issues)
    if root is not None:
        root_path = Path(root)
        return scan_paper_trading_artifacts(root_path), str(root_path), None, warnings, issues
    if settings.index_path.exists():
        return _load_index_path(settings.index_path, warnings, issues)
    warnings.append(f"Index path not found; scanning root instead: {settings.index_path}")
    return scan_paper_trading_artifacts(settings.root_dir), str(settings.root_dir), None, warnings, issues


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
                issue_message=f"Could not read paper artifact index CSV: {exc}",
                suggested_action="Regenerate paper_artifact_index.csv.",
            )
        )
        warnings.append(f"Could not read index CSV: {path}: {exc}")
        return _prepare_index_frame(pd.DataFrame(columns=INDEX_COLUMNS)), str(path), path.parent, warnings, issues
    return _prepare_index_frame(frame), str(path), path.parent, warnings, issues


def _prepare_index_frame(index_df: pd.DataFrame) -> pd.DataFrame:
    frame = index_df.copy(deep=True) if index_df is not None else pd.DataFrame(columns=INDEX_COLUMNS)
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    if frame.empty:
        return frame[INDEX_COLUMNS]
    return frame[INDEX_COLUMNS].sort_values(["artifact_type", "artifact_id"], na_position="last").reset_index(drop=True)


def _checked_artifact_count(index_frame: pd.DataFrame) -> int:
    if index_frame.empty:
        return 0
    return len(index_frame)


def _artifact_type(row: dict[str, Any]) -> str:
    return _string_or_empty(row.get("artifact_type")).upper()


def _required_path_fields(row: dict[str, Any], metadata: dict[str, Any] | None) -> list[str]:
    artifact_type = _artifact_type(row)
    fields = list(BASE_REQUIRED_PATH_FIELDS.get(artifact_type, []))
    if artifact_type == "DAILY":
        if metadata and metadata.get("reviewed_decisions_used") is True and "reviewed_decisions_path" not in fields:
            fields.append("reviewed_decisions_path")
        reconciliation = metadata.get("reconciliation") if isinstance(metadata, dict) else None
        if isinstance(reconciliation, dict) and (
            _present(reconciliation.get("status")) or _present(reconciliation.get("report_path"))
        ):
            if "reconciliation_report_path" not in fields:
                fields.append("reconciliation_report_path")
    return fields


def _optional_provided_path_fields(row: dict[str, Any], required_fields: list[str]) -> list[str]:
    optional = [
        "reviewed_decisions_path",
        "fills_path",
        "reconciliation_report_path",
    ]
    return [field for field in optional if field not in required_fields and _present(row.get(field))]


def _check_path(
    row: dict[str, Any],
    path_field: str,
    base_dir: Path | None,
    issues: list[dict[str, Any]],
    *,
    required: bool,
) -> Path | None:
    path_value = row.get(path_field, "")
    if not _present(path_value):
        if required:
            issues.append(
                _issue(
                    row,
                    path_field=path_field,
                    severity="ERROR",
                    issue_code="MISSING_PATH_VALUE",
                    issue_message=f"Missing required path value: {path_field}.",
                    suggested_action="Regenerate the artifact index or artifact metadata.",
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
                suggested_action="Regenerate the artifact index with file paths.",
            )
        )
        return None
    return path


def _check_metadata_file(
    row: dict[str, Any],
    metadata_path: Path | None,
    settings: PaperArtifactHealthSettings,
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
    required_fields = REQUIRED_METADATA_FIELDS.get(_artifact_type(row), [])
    for field in required_fields:
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


def _check_file_content(
    row: dict[str, Any],
    path_field: str,
    path: Path | None,
    settings: PaperArtifactHealthSettings,
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
    settings: PaperArtifactHealthSettings,
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
    if frame.empty:
        issues.append(
            _issue(
                row,
                path_field=path_field,
                path_value=path,
                severity=_configured_severity(settings.empty_csv_severity, settings),
                issue_code="CSV_EMPTY",
                issue_message="Required CSV artifact has no rows.",
                suggested_action="Confirm whether an empty artifact is expected or regenerate the source report.",
            )
        )


def _check_json_file(
    row: dict[str, Any],
    path_field: str,
    path: Path,
    issues: list[dict[str, Any]],
) -> None:
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
    settings: PaperArtifactHealthSettings,
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


def _configured_severity(value: str, settings: PaperArtifactHealthSettings) -> str:
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
    actionability: str | None = None,
) -> dict[str, Any]:
    if issue_code not in ISSUE_CODES:
        raise ValueError(f"Unsupported artifact health issue_code: {issue_code}")
    return {
        "artifact_type": _artifact_type(row),
        "artifact_id": _string_or_empty(row.get("artifact_id")),
        "path_field": path_field,
        "path_value": _string_or_empty(path_value if path_value is not None else row.get(path_field, "")),
        "severity": str(severity).upper(),
        "actionability": _string_or_empty(actionability),
        "issue_code": issue_code,
        "issue_message": issue_message,
        "suggested_action": suggested_action,
    }


def _issue_actionability(
    issue: dict[str, Any],
    metadata_by_artifact: dict[tuple[str, str], dict[str, Any]],
) -> str:
    severity = _string_or_empty(issue.get("severity")).upper()
    if severity == "ERROR":
        return BLOCKING_ERROR
    if severity != "WARN":
        return ""
    artifact_key = (_string_or_empty(issue.get("artifact_type")).upper(), _string_or_empty(issue.get("artifact_id")))
    metadata = metadata_by_artifact.get(artifact_key, {})
    if _is_expected_demo_empty_fills_issue(issue, metadata):
        return EXPECTED_DEMO_WARNING
    return ACTIONABLE_WARNING


def _is_expected_demo_empty_fills_issue(issue: dict[str, Any], metadata: dict[str, Any]) -> bool:
    if _string_or_empty(issue.get("artifact_type")).upper() != "DAILY":
        return False
    if _string_or_empty(issue.get("path_field")) != "fills_path":
        return False
    if _string_or_empty(issue.get("issue_code")) != "CSV_EMPTY":
        return False
    if metadata.get("reviewed_decisions_used") is not True:
        return False
    if _int_or_zero(metadata.get("fill_count")) != 0:
        return False
    if _int_or_zero(metadata.get("open_position_count")) != 0:
        return False
    if _int_or_zero(metadata.get("closed_trade_count")) != 0:
        return False
    return _reviewed_decisions_are_watch_only(metadata)


def _reviewed_decisions_are_watch_only(metadata: dict[str, Any]) -> bool:
    reviewed_path = _string_or_empty(metadata.get("reviewed_decisions_path"))
    output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    reviewed_path = reviewed_path or _string_or_empty(output_files.get("reviewed_decisions"))
    if not reviewed_path:
        return False
    path = _resolve_path(reviewed_path, None)
    if not path.exists():
        return False
    try:
        frame = pd.read_csv(path, dtype=str).fillna("")
    except Exception:
        return False
    if frame.empty or "manual_review_status" not in frame.columns:
        return False
    statuses = {str(value).strip().upper() for value in frame["manual_review_status"] if str(value).strip()}
    if not statuses or statuses != {"WATCH_ONLY"}:
        return False
    return not frame.astype(str).apply(lambda series: series.str.contains("APPROVED_FOR_PAPER", na=False)).any().any()


def _metadata_by_artifact(index_frame: pd.DataFrame) -> dict[tuple[str, str], dict[str, Any]]:
    metadata_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in index_frame.to_dict("records"):
        artifact_type = _artifact_type(row)
        artifact_id = _string_or_empty(row.get("artifact_id"))
        metadata_path = _string_or_empty(row.get("metadata_path"))
        if not artifact_type or not artifact_id or not metadata_path:
            continue
        path = _resolve_path(metadata_path, None)
        if not path.exists():
            continue
        try:
            metadata = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(metadata, dict):
            metadata_by_key[(artifact_type, artifact_id)] = metadata
    return metadata_by_key


def _default_actionability(severity: Any) -> str:
    normalized = _string_or_empty(severity).upper()
    if normalized == "ERROR":
        return BLOCKING_ERROR
    if normalized == "WARN":
        return ACTIONABLE_WARNING
    return ""


def _finalize_health_frame(frame: pd.DataFrame) -> pd.DataFrame:
    health = frame.copy(deep=True)
    for column in HEALTH_COLUMNS:
        if column not in health.columns:
            health[column] = ""
    if health.empty:
        return health[HEALTH_COLUMNS]
    return health[HEALTH_COLUMNS].sort_values(
        ["severity", "actionability", "artifact_type", "artifact_id", "issue_code", "path_field"],
        na_position="last",
    ).reset_index(drop=True)


def _coerce_health_settings(settings: PaperArtifactHealthSettings | dict[str, Any] | None) -> PaperArtifactHealthSettings:
    if settings is None:
        return PaperArtifactHealthSettings()
    if isinstance(settings, PaperArtifactHealthSettings):
        return settings
    if isinstance(settings, dict):
        return PaperArtifactHealthSettings(**settings)
    if hasattr(settings, "model_dump"):
        return PaperArtifactHealthSettings(**settings.model_dump())
    raise TypeError("settings must be PaperArtifactHealthSettings, dict, or None")


def _resolve_settings(
    settings: Settings | PaperArtifactHealthSettings | dict[str, Any] | None,
) -> tuple[Settings, PaperArtifactHealthSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.paper_artifact_health
    if isinstance(settings, Settings):
        return settings, settings.paper_artifact_health
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, PaperArtifactHealthSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.paper_artifact_health.model_dump())
        for key, value in settings.items():
            if key == "paper_artifact_health" and isinstance(value, dict):
                payload.update(value)
            elif key in payload:
                payload[key] = value
        return project, PaperArtifactHealthSettings(**payload)
    raise TypeError("settings must be Settings, PaperArtifactHealthSettings, dict, or None")


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


def _int_or_zero(value: Any) -> int:
    if not _present(value):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


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
