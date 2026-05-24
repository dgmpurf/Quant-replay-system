"""Local-only health checks for market-update-handoff artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketUpdateHandoffHealthSettings, Settings, load_settings
from quant_replay_system.data import read_csv_preserve_symbol_columns
from quant_replay_system.market_update_handoff_index import (
    INDEX_COLUMNS,
    NO_LIVE_STATEMENTS,
    build_market_update_handoff_index,
)


MARKET_UPDATE_HANDOFF_HEALTH_LIMITATIONS = [
    "Checks local market-update-handoff artifacts referenced by the index only.",
    "Does not regenerate handoffs, repair missing files, mutate the market cache, or call external APIs.",
    "Linked current-candidate checks use explicit paths when recorded in metadata.",
]

HEALTH_COLUMNS = [
    "handoff_id",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]


@dataclass(frozen=True)
class MarketUpdateHandoffHealthArtifactPaths:
    artifact_dir: Path
    market_update_handoff_health_report: Path
    market_update_handoff_health_issues: Path
    market_update_handoff_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_update_handoff_health_report": self.market_update_handoff_health_report,
            "market_update_handoff_health_issues": self.market_update_handoff_health_issues,
            "market_update_handoff_health_summary": self.market_update_handoff_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MarketUpdateHandoffHealthResult:
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


def check_market_update_handoff_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: Settings | MarketUpdateHandoffHealthSettings | dict[str, Any] | None = None,
) -> MarketUpdateHandoffHealthResult:
    project_settings, health_settings = _resolve_settings(settings)
    if health_settings.enable_live_trading or health_settings.enable_broker_api:
        raise ValueError("Market update handoff health cannot enable live trading or broker API access")

    index_frame, index_source, load_warnings, load_issues = _load_index(
        index_df=index_df,
        index_path=index_path,
        root=root,
        settings=health_settings,
    )
    health_frame = build_market_update_handoff_health_frame(index_frame, settings=health_settings)
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_market_update_handoff_health(
        health_frame,
        checked_artifact_count=len(index_frame),
    )
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = generate_market_update_handoff_health_id(
        index_frame,
        index_source=index_source,
        settings=health_settings,
    )
    paths = resolve_market_update_handoff_health_paths(
        Path(output_dir) if output_dir is not None else health_settings.output_dir,
        health_check_id,
    )
    audit_metadata = {
        "health_check_id": health_check_id,
        "index_source": index_source,
        "checked_artifact_count": len(index_frame),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "market_update_handoff_health_only": True,
        "config_version": health_settings.config_version,
    }
    result = MarketUpdateHandoffHealthResult(
        status=status,
        checked_artifact_count=len(index_frame),
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=load_warnings,
        known_limitations=MARKET_UPDATE_HANDOFF_HEALTH_LIMITATIONS,
        health_check_id=health_check_id,
        audit_metadata=audit_metadata,
    )
    if health_settings.write_artifacts:
        write_market_update_handoff_health_artifacts(result)
    _ = project_settings
    return result


def build_market_update_handoff_health_frame(
    index_df: pd.DataFrame,
    *,
    settings: MarketUpdateHandoffHealthSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    cfg = _coerce_settings(settings)
    issues: list[dict[str, Any]] = []
    index_frame = _prepare_index_frame(index_df)
    for row in index_frame.to_dict("records"):
        handoff_id = _string(row.get("handoff_id"))
        metadata = _check_json_path(row, "metadata_path", issues, required=True)
        report_path = _check_file_path(row, "handoff_report_path", issues, required=True)
        _check_no_live_statement(row, "handoff_report_path", report_path, issues, cfg)
        _check_csv_path(row, "handoff_rows_path", issues, required=True)
        _check_csv_path(row, "batch_market_csv_path", issues, required=True)
        _check_json_path(row, "generated_pipeline_manifest_path", issues, required=True)
        artifact_manifest = _string(row.get("generated_pipeline_manifest_artifact_path"))
        if artifact_manifest:
            _check_json_path(row, "generated_pipeline_manifest_artifact_path", issues, required=False)

        if _string(row.get("pipeline_id")):
            _check_report_path(row, "data_pipeline_report_path", issues, cfg)
            _check_json_path(row, "snapshot_manifest_path", issues, required=False)
        if _string(row.get("snapshot_quality_status")):
            _check_report_path(row, "snapshot_quality_report_path", issues, cfg)
        if _string(row.get("current_candidate_run_id")):
            for field in [
                "current_candidate_report_path",
                "current_candidate_metadata_path",
                "factor_dataset_path",
                "scored_dataset_path",
                "candidates_path",
            ]:
                if _string(row.get(field)):
                    if field.endswith("_path") and field != "current_candidate_report_path":
                        _check_file_path(row, field, issues, required=False)
                    else:
                        _check_file_path(row, field, issues, required=False)
                else:
                    issues.append(
                        _issue(
                            handoff_id,
                            field,
                            "",
                            cfg.missing_linked_artifact_severity,
                            "MISSING_LINKED_CURRENT_CANDIDATE_PATH",
                            f"Current-candidate run {row.get('current_candidate_run_id')} has no {field}.",
                            "Regenerate the handoff with current_candidate_artifact_paths metadata or rerun current-candidates.",
                        )
                    )
            current_report = Path(_string(row.get("current_candidate_report_path")))
            if _string(row.get("current_candidate_report_path")):
                _check_no_live_statement(row, "current_candidate_report_path", current_report, issues, cfg)

        if metadata and metadata.get("live_trading_enabled") not in {False, "False", "false", 0, "0"}:
            issues.append(
                _issue(
                    handoff_id,
                    "metadata_path",
                    _string(row.get("metadata_path")),
                    "ERROR",
                    "LIVE_TRADING_FLAG_ENABLED",
                    "Handoff metadata has live_trading_enabled not false.",
                    "Inspect and regenerate the local-only handoff artifact.",
                )
            )
        if metadata and metadata.get("broker_api_invoked") not in {False, "False", "false", 0, "0"}:
            issues.append(
                _issue(
                    handoff_id,
                    "metadata_path",
                    _string(row.get("metadata_path")),
                    "ERROR",
                    "BROKER_API_FLAG_ENABLED",
                    "Handoff metadata has broker_api_invoked not false.",
                    "Inspect and regenerate the local-only handoff artifact.",
                )
            )
    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_market_update_handoff_health(
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


def resolve_market_update_handoff_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> MarketUpdateHandoffHealthArtifactPaths:
    artifact_dir = Path(output_dir) / health_check_id
    return MarketUpdateHandoffHealthArtifactPaths(
        artifact_dir=artifact_dir,
        market_update_handoff_health_report=artifact_dir / "market_update_handoff_health_report.md",
        market_update_handoff_health_issues=artifact_dir / "market_update_handoff_health_issues.csv",
        market_update_handoff_health_summary=artifact_dir / "market_update_handoff_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_market_update_handoff_health_artifacts(
    result: MarketUpdateHandoffHealthResult,
) -> dict[str, Path]:
    paths = MarketUpdateHandoffHealthArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths.market_update_handoff_health_issues, index=False)
    result.summary_frame.to_csv(paths.market_update_handoff_health_summary, index=False)
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
    paths.market_update_handoff_health_report.write_text(
        render_market_update_handoff_health_report(result),
        encoding="utf-8",
    )
    return paths.as_dict()


def render_market_update_handoff_health_report(result: MarketUpdateHandoffHealthResult) -> str:
    lines = [
        "# Market Update Handoff Artifact Health",
        "",
        "No live trading or broker API was invoked. This report checks local handoff artifacts only.",
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
    settings: MarketUpdateHandoffHealthSettings,
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
                "Market update handoff index CSV was not found.",
                "Run market-update-handoff-index or pass --root.",
            )
            return _prepare_index_frame(pd.DataFrame()), str(path), [], [issue]
        return read_csv_preserve_symbol_columns(path, keep_default_na=False), str(path), [], []
    effective_root = Path(root) if root is not None else settings.root_dir
    index = build_market_update_handoff_index(
        root=effective_root,
        output_dir=settings.output_dir / "_generated_index",
        settings={"write_artifacts": False},
    )
    return index.index_frame, str(effective_root), index.warnings, []


def _check_file_path(
    row: dict[str, Any],
    field: str,
    issues: list[dict[str, Any]],
    *,
    required: bool,
) -> Path | None:
    value = _string(row.get(field))
    handoff_id = _string(row.get("handoff_id"))
    if not value:
        if required:
            issues.append(
                _issue(
                    handoff_id,
                    field,
                    value,
                    "ERROR",
                    "MISSING_PATH_VALUE",
                    f"Required path field {field} is empty.",
                    "Regenerate the handoff index or source artifact.",
                )
            )
        return None
    path = Path(value)
    if not path.exists():
        issues.append(
            _issue(
                handoff_id,
                field,
                value,
                "ERROR" if required else "WARN",
                "FILE_NOT_FOUND",
                f"Referenced file does not exist: {path}",
                "Regenerate or repair the linked local artifact.",
            )
        )
        return path
    return path


def _check_csv_path(row: dict[str, Any], field: str, issues: list[dict[str, Any]], *, required: bool) -> Path | None:
    path = _check_file_path(row, field, issues, required=required)
    if path is None or not path.exists():
        return path
    try:
        read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception as exc:  # pragma: no cover - defensive against parser detail changes
        issues.append(
            _issue(
                _string(row.get("handoff_id")),
                field,
                str(path),
                "ERROR",
                "CSV_UNREADABLE",
                f"CSV could not be read safely: {exc}",
                "Inspect or regenerate the CSV artifact.",
            )
        )
    return path


def _check_json_path(row: dict[str, Any], field: str, issues: list[dict[str, Any]], *, required: bool) -> dict[str, Any]:
    path = _check_file_path(row, field, issues, required=required)
    if path is None or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # pragma: no cover - defensive against parser detail changes
        issues.append(
            _issue(
                _string(row.get("handoff_id")),
                field,
                str(path),
                "ERROR",
                "JSON_UNREADABLE",
                f"JSON could not be read safely: {exc}",
                "Inspect or regenerate the JSON artifact.",
            )
        )
    return {}


def _check_report_path(
    row: dict[str, Any],
    field: str,
    issues: list[dict[str, Any]],
    settings: MarketUpdateHandoffHealthSettings,
) -> None:
    path = _check_file_path(row, field, issues, required=True)
    if path is not None:
        _check_no_live_statement(row, field, path, issues, settings)


def _check_no_live_statement(
    row: dict[str, Any],
    field: str,
    path: Path | None,
    issues: list[dict[str, Any]],
    settings: MarketUpdateHandoffHealthSettings,
) -> None:
    if path is None or not path.exists():
        return
    content = path.read_text(encoding="utf-8", errors="ignore")
    if not any(statement in content for statement in NO_LIVE_STATEMENTS):
        issues.append(
            _issue(
                _string(row.get("handoff_id")),
                field,
                str(path),
                settings.missing_no_live_statement_severity,
                "MISSING_NO_LIVE_TRADING_STATEMENT",
                "Report is missing a no-live-trading/no-broker statement.",
                "Regenerate the local artifact with the current report renderer.",
            )
        )


def _issue(
    handoff_id: str,
    path_field: str,
    path_value: str,
    severity: str,
    issue_code: str,
    issue_message: str,
    suggested_action: str,
) -> dict[str, Any]:
    return {
        "handoff_id": handoff_id,
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
    settings: MarketUpdateHandoffHealthSettings | dict[str, Any] | None,
) -> MarketUpdateHandoffHealthSettings:
    if settings is None:
        return MarketUpdateHandoffHealthSettings()
    if isinstance(settings, MarketUpdateHandoffHealthSettings):
        return settings
    return MarketUpdateHandoffHealthSettings(**settings)


def _resolve_settings(
    settings: Settings | MarketUpdateHandoffHealthSettings | dict[str, Any] | None,
) -> tuple[Settings, MarketUpdateHandoffHealthSettings]:
    project = load_settings(Path("config/default.yaml"))
    if settings is None:
        return project, project.market_update_handoff_health
    if isinstance(settings, Settings):
        return settings, settings.market_update_handoff_health
    if isinstance(settings, MarketUpdateHandoffHealthSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.market_update_handoff_health.model_dump())
        payload.update(settings.get("market_update_handoff_health", settings))
        return project, MarketUpdateHandoffHealthSettings(**payload)
    raise TypeError("settings must be Settings, MarketUpdateHandoffHealthSettings, dict, or None")


def generate_market_update_handoff_health_id(
    index_frame: pd.DataFrame,
    *,
    index_source: str,
    settings: MarketUpdateHandoffHealthSettings,
) -> str:
    payload = {
        "index_source": index_source,
        "handoff_ids": sorted(index_frame.get("handoff_id", pd.Series(dtype="object")).astype(str).tolist()),
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
