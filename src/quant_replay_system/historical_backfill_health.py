"""Local-only health checks for historical-backfill artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import HistoricalBackfillHealthSettings, Settings, load_settings
from quant_replay_system.data import read_csv_preserve_symbol_columns
from quant_replay_system.historical_backfill_index import (
    INDEX_COLUMNS,
    NO_LIVE_STATEMENTS,
    build_historical_backfill_index,
)


HISTORICAL_BACKFILL_HEALTH_LIMITATIONS = [
    "Checks local historical-backfill artifacts referenced by the index only.",
    "Does not regenerate backfills, repair missing files, mutate the market cache, or call external APIs.",
    "Health checks artifact completeness and safety metadata; they do not certify market data correctness.",
]

HEALTH_COLUMNS = [
    "backfill_id",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]


@dataclass(frozen=True)
class HistoricalBackfillHealthArtifactPaths:
    artifact_dir: Path
    historical_backfill_health_report: Path
    historical_backfill_health_issues: Path
    historical_backfill_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "historical_backfill_health_report": self.historical_backfill_health_report,
            "historical_backfill_health_issues": self.historical_backfill_health_issues,
            "historical_backfill_health_summary": self.historical_backfill_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class HistoricalBackfillHealthResult:
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


def check_historical_backfill_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: Settings | HistoricalBackfillHealthSettings | dict[str, Any] | None = None,
) -> HistoricalBackfillHealthResult:
    project_settings, health_settings = _resolve_settings(settings)
    if health_settings.enable_live_trading or health_settings.enable_broker_api:
        raise ValueError("Historical backfill health cannot enable live trading or broker API access")

    index_frame, index_source, load_warnings, load_issues = _load_index(
        index_df=index_df,
        index_path=index_path,
        root=root,
        settings=health_settings,
    )
    health_frame = build_historical_backfill_health_frame(index_frame, settings=health_settings)
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_historical_backfill_health(health_frame, checked_artifact_count=len(index_frame))
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = generate_historical_backfill_health_id(
        index_frame,
        index_source=index_source,
        settings=health_settings,
    )
    paths = resolve_historical_backfill_health_paths(
        Path(output_dir) if output_dir is not None else health_settings.output_dir,
        health_check_id,
    )
    audit_metadata = {
        "health_check_id": health_check_id,
        "index_source": index_source,
        "checked_artifact_count": len(index_frame),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "historical_backfill_health_only": True,
        "config_version": health_settings.config_version,
    }
    result = HistoricalBackfillHealthResult(
        status=status,
        checked_artifact_count=len(index_frame),
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=load_warnings,
        known_limitations=HISTORICAL_BACKFILL_HEALTH_LIMITATIONS,
        health_check_id=health_check_id,
        audit_metadata=audit_metadata,
    )
    if health_settings.write_artifacts:
        write_historical_backfill_health_artifacts(result)
    _ = project_settings
    return result


def build_historical_backfill_health_frame(
    index_df: pd.DataFrame,
    *,
    settings: HistoricalBackfillHealthSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    cfg = _coerce_settings(settings)
    issues: list[dict[str, Any]] = []
    index_frame = _prepare_index_frame(index_df)
    for row in index_frame.to_dict("records"):
        backfill_id = _string(row.get("backfill_id"))
        metadata = _check_json_path(row, "metadata_path", issues, required=True)
        report_path = _check_file_path(row, "report_path", issues, required=True, issue_code="MISSING_REPORT")
        _check_no_live_statement(row, "report_path", report_path, issues, cfg)
        tasks_frame = _check_csv_path(row, "tasks_path", issues, required=True, issue_code="UNREADABLE_TASKS")
        results_frame = _check_csv_path(row, "results_path", issues, required=True, issue_code="UNREADABLE_RESULTS")
        _check_manifest_path(row, metadata, issues, cfg)
        _check_metadata_safety(row, metadata, issues)
        _check_summary_counts(row, metadata, tasks_frame, results_frame, issues)
        _check_expected_dry_run_warning(row, metadata, issues)
        if not backfill_id:
            issues.append(
                _issue(
                    "",
                    "backfill_id",
                    "",
                    "ERROR",
                    "STALE_OR_PARTIAL_ARTIFACT",
                    "Indexed backfill row is missing a backfill_id.",
                    "Regenerate the historical-backfill artifact or index.",
                )
            )
    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_historical_backfill_health(
    health_frame: pd.DataFrame,
    *,
    checked_artifact_count: int,
) -> pd.DataFrame:
    frame = _finalize_health_frame(health_frame)
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARN").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else ("WARN" if warning_count else "PASS")
    return pd.DataFrame(
        [
            {
                "status": status,
                "checked_artifact_count": checked_artifact_count,
                "issue_count": int(len(frame)),
                "error_count": error_count,
                "warning_count": warning_count,
                "no_live_trading": True,
                "no_broker_api": True,
            }
        ]
    )


def resolve_historical_backfill_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> HistoricalBackfillHealthArtifactPaths:
    artifact_dir = Path(output_dir) / health_check_id
    return HistoricalBackfillHealthArtifactPaths(
        artifact_dir=artifact_dir,
        historical_backfill_health_report=artifact_dir / "historical_backfill_health_report.md",
        historical_backfill_health_issues=artifact_dir / "historical_backfill_health_issues.csv",
        historical_backfill_health_summary=artifact_dir / "historical_backfill_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_historical_backfill_health_artifacts(result: HistoricalBackfillHealthResult) -> dict[str, Path]:
    paths = HistoricalBackfillHealthArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths.historical_backfill_health_issues, index=False)
    result.summary_frame.to_csv(paths.historical_backfill_health_summary, index=False)
    metadata = {
        "health_check_id": result.health_check_id,
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.historical_backfill_health_report.write_text(
        render_historical_backfill_health_report(result),
        encoding="utf-8",
    )
    return paths.as_dict()


def render_historical_backfill_health_report(result: HistoricalBackfillHealthResult) -> str:
    lines = [
        "# Historical Backfill Artifact Health",
        "",
        "No live trading or broker API was invoked. This report checks local historical-backfill artifacts only.",
        "",
        "## Summary",
        "",
        result.summary_frame.to_markdown(index=False),
        "",
        "## Issues",
        "",
        result.health_frame.to_markdown(index=False) if not result.health_frame.empty else "No issues.",
    ]
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in result.known_limitations)
    return "\n".join(lines) + "\n"


def _load_index(
    *,
    index_df: pd.DataFrame | None,
    index_path: str | Path | None,
    root: str | Path | None,
    settings: HistoricalBackfillHealthSettings,
) -> tuple[pd.DataFrame, str, list[str], list[dict[str, Any]]]:
    if index_df is not None:
        return _prepare_index_frame(index_df), "DATAFRAME", [], []
    if index_path is not None:
        path = Path(index_path)
        if not path.exists():
            issue = _issue(
                "",
                "index_path",
                str(path),
                "ERROR",
                "INDEX_NOT_FOUND",
                "Historical backfill index CSV was not found.",
                "Run historical-backfill-index or pass --root.",
            )
            return _prepare_index_frame(pd.DataFrame()), str(path), [], [issue]
        return read_csv_preserve_symbol_columns(path, keep_default_na=False), str(path), [], []
    effective_root = Path(root) if root is not None else settings.root_dir
    index = build_historical_backfill_index(
        root=effective_root,
        output_dir=settings.output_dir / "_generated_index",
        include_missing_metadata=True,
        settings={"write_artifacts": False},
    )
    return index.index_frame, str(effective_root), index.warnings, []


def _check_file_path(
    row: dict[str, Any],
    field: str,
    issues: list[dict[str, Any]],
    *,
    required: bool,
    issue_code: str = "FILE_NOT_FOUND",
) -> Path | None:
    value = _string(row.get(field))
    backfill_id = _string(row.get("backfill_id"))
    if not value:
        if required:
            issues.append(
                _issue(
                    backfill_id,
                    field,
                    value,
                    "ERROR",
                    "MISSING_PATH_VALUE",
                    f"Required path field {field} is empty.",
                    "Regenerate the historical backfill index or source artifact.",
                )
            )
        return None
    path = Path(value)
    if not path.exists():
        issues.append(
            _issue(
                backfill_id,
                field,
                value,
                "ERROR" if required else "WARN",
                issue_code,
                f"Referenced file does not exist: {path}",
                "Regenerate or repair the linked local artifact.",
            )
        )
        return path
    return path


def _check_csv_path(
    row: dict[str, Any],
    field: str,
    issues: list[dict[str, Any]],
    *,
    required: bool,
    issue_code: str,
) -> pd.DataFrame | None:
    path = _check_file_path(row, field, issues, required=required, issue_code=issue_code)
    if path is None or not path.exists():
        return None
    try:
        return read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception as exc:  # pragma: no cover - defensive against parser detail changes
        issues.append(
            _issue(
                _string(row.get("backfill_id")),
                field,
                str(path),
                "ERROR",
                issue_code,
                f"CSV could not be read safely: {exc}",
                "Inspect or regenerate the CSV artifact.",
            )
        )
    return None


def _check_json_path(
    row: dict[str, Any],
    field: str,
    issues: list[dict[str, Any]],
    *,
    required: bool,
) -> dict[str, Any]:
    path = _check_file_path(row, field, issues, required=required, issue_code="MISSING_METADATA")
    if path is None or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # pragma: no cover - defensive against parser detail changes
        issues.append(
            _issue(
                _string(row.get("backfill_id")),
                field,
                str(path),
                "ERROR",
                "MISSING_METADATA",
                f"JSON could not be read safely: {exc}",
                "Inspect or regenerate the JSON artifact.",
            )
        )
    return {}


def _check_manifest_path(
    row: dict[str, Any],
    metadata: dict[str, Any],
    issues: list[dict[str, Any]],
    settings: HistoricalBackfillHealthSettings,
) -> None:
    manifest_path = _string(metadata.get("manifest_path")) or _string(row.get("manifest_path"))
    if not manifest_path:
        issues.append(
            _issue(
                _string(row.get("backfill_id")),
                "manifest_path",
                "",
                settings.missing_manifest_severity,
                "STALE_OR_PARTIAL_ARTIFACT",
                "Metadata does not record the reviewed backfill manifest path.",
                "Regenerate the backfill artifact with the current workflow.",
            )
        )
        return
    path = Path(manifest_path)
    if not path.exists():
        issues.append(
            _issue(
                _string(row.get("backfill_id")),
                "manifest_path",
                manifest_path,
                settings.missing_manifest_severity,
                "STALE_OR_PARTIAL_ARTIFACT",
                "Referenced reviewed manifest is not present on this machine.",
                "Restore the manifest or keep the artifact as historical-only evidence.",
            )
        )


def _check_no_live_statement(
    row: dict[str, Any],
    field: str,
    path: Path | None,
    issues: list[dict[str, Any]],
    settings: HistoricalBackfillHealthSettings,
) -> None:
    if path is None or not path.exists():
        return
    content = path.read_text(encoding="utf-8", errors="ignore")
    if not any(statement in content for statement in NO_LIVE_STATEMENTS):
        issues.append(
            _issue(
                _string(row.get("backfill_id")),
                field,
                str(path),
                settings.missing_no_live_statement_severity,
                "MISSING_NO_LIVE_TRADING_STATEMENT",
                "Report is missing a no-live-trading/no-broker statement.",
                "Regenerate the local artifact with the current report renderer.",
            )
        )


def _check_metadata_safety(row: dict[str, Any], metadata: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    backfill_id = _string(row.get("backfill_id"))
    if not metadata:
        return
    if "cache_write_occurred" not in metadata:
        issues.append(
            _issue(
                backfill_id,
                "metadata_path",
                _string(row.get("metadata_path")),
                "ERROR",
                "STALE_OR_PARTIAL_ARTIFACT",
                "Metadata is missing cache_write_occurred.",
                "Regenerate the historical-backfill artifact with current metadata.",
            )
        )
    if metadata.get("live_trading_enabled") not in {False, "False", "false", 0, "0"}:
        issues.append(
            _issue(
                backfill_id,
                "metadata_path",
                _string(row.get("metadata_path")),
                "ERROR",
                "MISSING_NO_LIVE_TRADING_STATEMENT",
                "Metadata live_trading_enabled is missing or not false.",
                "Inspect and regenerate the local-only backfill artifact.",
            )
        )
    if metadata.get("broker_api_invoked") not in {False, "False", "false", 0, "0"}:
        issues.append(
            _issue(
                backfill_id,
                "metadata_path",
                _string(row.get("metadata_path")),
                "ERROR",
                "MISSING_NO_LIVE_TRADING_STATEMENT",
                "Metadata broker_api_invoked is missing or not false.",
                "Inspect and regenerate the local-only backfill artifact.",
            )
        )


def _check_summary_counts(
    row: dict[str, Any],
    metadata: dict[str, Any],
    tasks_frame: pd.DataFrame | None,
    results_frame: pd.DataFrame | None,
    issues: list[dict[str, Any]],
) -> None:
    if not metadata:
        return
    backfill_id = _string(row.get("backfill_id"))
    metadata_task_count = int(_number(metadata.get("task_count", 0)))
    if tasks_frame is not None and metadata_task_count != len(tasks_frame):
        issues.append(
            _issue(
                backfill_id,
                "tasks_path",
                _string(row.get("tasks_path")),
                "ERROR",
                "SUMMARY_COUNT_MISMATCH",
                f"Metadata task_count={metadata_task_count} does not match tasks CSV rows={len(tasks_frame)}.",
                "Inspect or regenerate the backfill artifact.",
            )
        )
    counts = metadata.get("task_result_counts", {}) if isinstance(metadata.get("task_result_counts"), dict) else {}
    expected_result_count = sum(int(_number(value)) for value in counts.values())
    if results_frame is not None and expected_result_count != len(results_frame):
        issues.append(
            _issue(
                backfill_id,
                "results_path",
                _string(row.get("results_path")),
                "ERROR",
                "SUMMARY_COUNT_MISMATCH",
                f"Metadata task_result_counts total={expected_result_count} does not match results CSV rows={len(results_frame)}.",
                "Inspect or regenerate the backfill artifact.",
            )
        )


def _check_expected_dry_run_warning(
    row: dict[str, Any],
    metadata: dict[str, Any],
    issues: list[dict[str, Any]],
) -> None:
    if not metadata:
        return
    if str(metadata.get("status", "")).upper() != "WARN":
        return
    if bool(metadata.get("cache_write_occurred", False)):
        return
    warnings = metadata.get("warnings", [])
    if not warnings:
        return
    issues.append(
        _issue(
            _string(row.get("backfill_id")),
            "metadata_path",
            _string(row.get("metadata_path")),
            "WARN",
            "EXPECTED_DRY_RUN_WARNING",
            "Backfill dry-run completed with reviewable WARN tasks.",
            "Review WARN tasks before using --accept-cache-write.",
        )
    )


def _issue(
    backfill_id: str,
    path_field: str,
    path_value: str,
    severity: str,
    issue_code: str,
    issue_message: str,
    suggested_action: str,
) -> dict[str, Any]:
    return {
        "backfill_id": backfill_id,
        "path_field": path_field,
        "path_value": path_value,
        "severity": severity.upper(),
        "issue_code": issue_code,
        "issue_message": issue_message,
        "suggested_action": suggested_action,
    }


def _finalize_health_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    output = frame.copy(deep=True)
    for column in HEALTH_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[HEALTH_COLUMNS].reset_index(drop=True)


def _prepare_index_frame(index_df: pd.DataFrame) -> pd.DataFrame:
    frame = index_df.copy(deep=True)
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[INDEX_COLUMNS].reset_index(drop=True)


def _coerce_settings(
    settings: HistoricalBackfillHealthSettings | dict[str, Any] | None,
) -> HistoricalBackfillHealthSettings:
    if settings is None:
        return HistoricalBackfillHealthSettings()
    if isinstance(settings, HistoricalBackfillHealthSettings):
        return settings
    return HistoricalBackfillHealthSettings(**settings)


def _resolve_settings(
    settings: Settings | HistoricalBackfillHealthSettings | dict[str, Any] | None,
) -> tuple[Settings, HistoricalBackfillHealthSettings]:
    project = load_settings(Path("config/default.yaml"))
    if settings is None:
        return project, project.historical_backfill_health
    if isinstance(settings, Settings):
        return settings, settings.historical_backfill_health
    if isinstance(settings, HistoricalBackfillHealthSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.historical_backfill_health.model_dump())
        payload.update(settings.get("historical_backfill_health", settings))
        return project, HistoricalBackfillHealthSettings(**payload)
    raise TypeError("settings must be Settings, HistoricalBackfillHealthSettings, dict, or None")


def generate_historical_backfill_health_id(
    index_frame: pd.DataFrame,
    *,
    index_source: str,
    settings: HistoricalBackfillHealthSettings,
) -> str:
    payload = {
        "index_source": index_source,
        "backfill_ids": sorted(index_frame.get("backfill_id", pd.Series(dtype="object")).astype(str).tolist()),
        "config_version": settings.config_version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value
