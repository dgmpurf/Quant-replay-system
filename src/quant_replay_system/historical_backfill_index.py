"""Local-only index for historical-backfill artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import HistoricalBackfillIndexSettings, Settings, load_settings
from quant_replay_system.data import read_csv_preserve_symbol_columns


NO_LIVE_STATEMENTS = [
    "No broker or live trading integration was invoked",
    "No live trading or broker API was invoked",
]

HISTORICAL_BACKFILL_INDEX_LIMITATIONS = [
    "Scans local historical-backfill artifact folders only.",
    "Reads metadata, task/result CSVs, and reports already written by local workflows.",
    "Does not mutate the market cache, fetch real data, place orders, or call broker APIs.",
]

INDEX_COLUMNS = [
    "backfill_id",
    "artifact_dir",
    "created_at",
    "status",
    "manifest_path",
    "task_count",
    "pass_count",
    "warn_count",
    "fail_count",
    "skipped_count",
    "cache_write_occurred",
    "min_start_date",
    "max_end_date",
    "symbols",
    "report_path",
    "tasks_path",
    "results_path",
    "metadata_path",
    "warning_count",
    "no_live_trading_statement_present",
]


@dataclass(frozen=True)
class HistoricalBackfillIndexArtifactPaths:
    artifact_dir: Path
    historical_backfill_index_report: Path
    historical_backfill_index_csv: Path
    historical_backfill_index_json: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "historical_backfill_index_report": self.historical_backfill_index_report,
            "historical_backfill_index_csv": self.historical_backfill_index_csv,
            "historical_backfill_index_json": self.historical_backfill_index_json,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class HistoricalBackfillIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_historical_backfill_artifacts(
    root: str | Path | None = None,
    *,
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    rows, _ = _scan_rows(
        Path(root) if root is not None else HistoricalBackfillIndexSettings().root_dir,
        include_missing_metadata=include_missing_metadata,
    )
    return _finalize_index_frame(pd.DataFrame(rows))


def build_historical_backfill_index(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    include_missing_metadata: bool | None = None,
    settings: Settings | HistoricalBackfillIndexSettings | dict[str, Any] | None = None,
) -> HistoricalBackfillIndexResult:
    project_settings, index_settings = _resolve_settings(settings)
    if index_settings.enable_live_trading or index_settings.enable_broker_api:
        raise ValueError("Historical backfill index cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else index_settings.root_dir
    effective_output = Path(output_dir) if output_dir is not None else index_settings.output_dir
    effective_include_missing = (
        bool(include_missing_metadata)
        if include_missing_metadata is not None
        else index_settings.include_missing_metadata
    )
    rows, warnings = _scan_rows(effective_root, include_missing_metadata=effective_include_missing)
    frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_historical_backfill_index_paths(effective_output)
    audit_metadata = {
        "root_dir": effective_root,
        "include_missing_metadata": effective_include_missing,
        "artifact_count": len(frame),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "historical_backfill_index_only": True,
        "config_version": index_settings.config_version,
    }
    result = HistoricalBackfillIndexResult(
        artifact_count=len(frame),
        index_frame=frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=HISTORICAL_BACKFILL_INDEX_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if index_settings.write_artifacts:
        write_historical_backfill_index(result)
    _ = project_settings
    return result


def resolve_historical_backfill_index_paths(output_dir: str | Path) -> HistoricalBackfillIndexArtifactPaths:
    artifact_dir = Path(output_dir)
    return HistoricalBackfillIndexArtifactPaths(
        artifact_dir=artifact_dir,
        historical_backfill_index_report=artifact_dir / "historical_backfill_index_report.md",
        historical_backfill_index_csv=artifact_dir / "historical_backfill_index.csv",
        historical_backfill_index_json=artifact_dir / "historical_backfill_index.json",
        metadata=artifact_dir / "metadata.json",
    )


def write_historical_backfill_index(result: HistoricalBackfillIndexResult) -> dict[str, Path]:
    paths = HistoricalBackfillIndexArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    export = _sanitize_dataframe_for_export(result.index_frame)
    export.to_csv(paths.historical_backfill_index_csv, index=False)
    paths.historical_backfill_index_json.write_text(
        json.dumps(_json_safe(export.to_dict("records")), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    metadata = build_historical_backfill_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.historical_backfill_index_report.write_text(
        render_historical_backfill_index_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_historical_backfill_index_metadata(
    result: HistoricalBackfillIndexResult,
    paths: HistoricalBackfillIndexArtifactPaths,
) -> dict[str, Any]:
    return {
        "index_id": _generate_index_id(result.index_frame, result.audit_metadata),
        "artifact_count": result.artifact_count,
        "root_dir": str(result.audit_metadata.get("root_dir", "")),
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }


def render_historical_backfill_index_report(
    result: HistoricalBackfillIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {"index_id": _generate_index_id(result.index_frame, result.audit_metadata)}
    lines = [
        "# Historical Backfill Artifact Index",
        "",
        "No live trading or broker API was invoked. This index scans local historical-backfill artifacts only.",
        "",
        "## Index Metadata",
        "",
        _dict_table(
            {
                "index_id": meta.get("index_id", ""),
                "root_dir": result.audit_metadata.get("root_dir", ""),
                "artifact_count": result.artifact_count,
            }
        ),
        "",
        "## Backfill Artifacts",
        "",
        _markdown_table(
            result.index_frame,
            [
                "backfill_id",
                "status",
                "task_count",
                "pass_count",
                "warn_count",
                "fail_count",
                "cache_write_occurred",
                "report_path",
            ],
        ),
    ]
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in result.known_limitations)
    return "\n".join(lines) + "\n"


def _scan_rows(root: Path, *, include_missing_metadata: bool) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not root.exists():
        warnings.append(f"Historical backfill root not found: {root}")
        return rows, warnings
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"}:
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, metadata_path))
            else:
                warnings.append(f"Skipping historical backfill folder missing metadata.json: {artifact_dir}")
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Skipping unreadable metadata {metadata_path}: {exc}")
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, metadata_path, status="FAIL"))
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    paths = metadata.get("artifact_paths", {}) if isinstance(metadata.get("artifact_paths"), dict) else {}
    counts = metadata.get("task_result_counts", {}) if isinstance(metadata.get("task_result_counts"), dict) else {}
    report_path = _path_or_default(
        paths.get("historical_backfill_report"),
        artifact_dir / "historical_backfill_report.md",
    )
    tasks_path = _path_or_default(
        paths.get("historical_backfill_tasks"),
        artifact_dir / "historical_backfill_tasks.csv",
    )
    results_path = _path_or_default(
        paths.get("historical_backfill_results"),
        artifact_dir / "historical_backfill_results.csv",
    )
    coverage = _coverage_from_artifacts(tasks_path, results_path)
    return {
        "backfill_id": str(metadata.get("backfill_id") or artifact_dir.name),
        "artifact_dir": str(artifact_dir),
        "created_at": str(metadata.get("created_at") or ""),
        "status": str(metadata.get("status") or ""),
        "manifest_path": str(metadata.get("manifest_path") or ""),
        "task_count": int(_number(metadata.get("task_count", 0))),
        "pass_count": int(_number(counts.get("PASS", 0))),
        "warn_count": int(_number(counts.get("WARN", 0))),
        "fail_count": _fail_count(counts),
        "skipped_count": int(_number(counts.get("SKIPPED_DISABLED", 0))),
        "cache_write_occurred": bool(metadata.get("cache_write_occurred", False)),
        "min_start_date": coverage["min_start_date"],
        "max_end_date": coverage["max_end_date"],
        "symbols": coverage["symbols"],
        "report_path": str(report_path),
        "tasks_path": str(tasks_path),
        "results_path": str(results_path),
        "metadata_path": str(metadata_path),
        "warning_count": len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else 0,
        "no_live_trading_statement_present": _report_has_no_live_statement(report_path),
    }


def _missing_metadata_row(artifact_dir: Path, metadata_path: Path, *, status: str = "MISSING_METADATA") -> dict[str, Any]:
    return {
        **{column: "" for column in INDEX_COLUMNS},
        "backfill_id": artifact_dir.name,
        "artifact_dir": str(artifact_dir),
        "status": status,
        "report_path": str(artifact_dir / "historical_backfill_report.md"),
        "tasks_path": str(artifact_dir / "historical_backfill_tasks.csv"),
        "results_path": str(artifact_dir / "historical_backfill_results.csv"),
        "metadata_path": str(metadata_path),
    }


def _coverage_from_artifacts(tasks_path: Path, results_path: Path) -> dict[str, str]:
    frames: list[pd.DataFrame] = []
    for path in [tasks_path, results_path]:
        if path.exists():
            try:
                frames.append(read_csv_preserve_symbol_columns(path, keep_default_na=False))
            except Exception:
                continue
    if not frames:
        return {"symbols": "", "min_start_date": "", "max_end_date": ""}
    frame = pd.concat(frames, ignore_index=True, sort=False)
    symbols = sorted(
        str(value).strip()
        for value in frame.get("symbol", pd.Series(dtype="object")).dropna().tolist()
        if str(value).strip()
    )
    start_values = _date_values(frame, ["chunk_start_date", "start_date"])
    end_values = _date_values(frame, ["chunk_end_date", "end_date"])
    return {
        "symbols": ",".join(dict.fromkeys(symbols)),
        "min_start_date": min(start_values) if start_values else "",
        "max_end_date": max(end_values) if end_values else "",
    }


def _date_values(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    values: list[str] = []
    for column in columns:
        if column not in frame.columns:
            continue
        values.extend(str(value).strip() for value in frame[column].dropna().tolist() if str(value).strip())
    return values


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS)
    output = frame.copy(deep=True)
    for column in INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    output = output[INDEX_COLUMNS]
    output["_created_sort"] = pd.to_datetime(output["created_at"], errors="coerce")
    output = output.sort_values(["_created_sort", "backfill_id"], ascending=[False, False], na_position="last")
    output = output.drop(columns=["_created_sort"])
    return output.reset_index(drop=True)


def _path_or_default(value: Any, default: Path) -> Path:
    text = str(value or "").strip()
    return Path(text) if text else default


def _report_has_no_live_statement(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return any(statement in content for statement in NO_LIVE_STATEMENTS)


def _fail_count(counts: dict[str, Any]) -> int:
    return sum(
        int(_number(counts.get(status, 0)))
        for status in [
            "FAIL",
            "BLOCKED_NEEDS_ALLOW_REAL_DATA",
            "BLOCKED_PREFLIGHT_REJECT",
            "BLOCKED_MISSING_RAW_INPUT",
        ]
    )


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _resolve_settings(
    settings: Settings | HistoricalBackfillIndexSettings | dict[str, Any] | None,
) -> tuple[Settings, HistoricalBackfillIndexSettings]:
    project = load_settings(Path("config/default.yaml"))
    if settings is None:
        return project, project.historical_backfill_index
    if isinstance(settings, Settings):
        return settings, settings.historical_backfill_index
    if isinstance(settings, HistoricalBackfillIndexSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.historical_backfill_index.model_dump())
        payload.update(settings.get("historical_backfill_index", settings))
        return project, HistoricalBackfillIndexSettings(**payload)
    raise TypeError("settings must be Settings, HistoricalBackfillIndexSettings, dict, or None")


def _generate_index_id(frame: pd.DataFrame, metadata: dict[str, Any]) -> str:
    payload = {
        "root_dir": str(metadata.get("root_dir", "")),
        "backfill_ids": sorted(frame.get("backfill_id", pd.Series(dtype="object")).astype(str).tolist()),
        "config_version": metadata.get("config_version", ""),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _sanitize_dataframe_for_export(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy(deep=True)
    for column in output.columns:
        if output[column].dtype == "object":
            output[column] = output[column].map(lambda value: "" if pd.isna(value) else value)
    return output


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "No artifacts found."
    available = [column for column in columns if column in frame.columns]
    return frame[available].to_markdown(index=False)


def _dict_table(values: dict[str, Any]) -> str:
    return pd.DataFrame([{"field": key, "value": value} for key, value in values.items()]).to_markdown(index=False)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return value
