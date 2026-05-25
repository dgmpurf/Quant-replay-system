"""Local-only index for reviewed market-cache-export artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketCacheExportIndexSettings, Settings, load_settings
from quant_replay_system.data import read_csv_preserve_symbol_columns
from quant_replay_system.data_pipeline import (
    generate_data_pipeline_id,
    load_data_pipeline_manifest,
    resolve_data_pipeline_artifact_paths,
)


NO_LIVE_STATEMENTS = [
    "No broker or live trading integration was invoked",
    "No live trading or broker API was invoked",
]

MARKET_CACHE_EXPORT_INDEX_LIMITATIONS = [
    "Scans local market-cache-export artifact folders only.",
    "Reads metadata, exported CSVs, and linked local pipeline artifacts when available.",
    "Does not mutate the market cache, fetch real data, place orders, or call broker APIs.",
]

INDEX_COLUMNS = [
    "export_id",
    "artifact_dir",
    "created_at",
    "artifact_updated_at",
    "status",
    "exported_market_csv_path",
    "exported_row_count",
    "duplicate_key_count",
    "generated_pipeline_manifest_path",
    "pipeline_id",
    "data_pipeline_status",
    "data_pipeline_report_path",
    "data_quality_status",
    "data_quality_report_path",
    "snapshot_manifest_path",
    "snapshot_quality_status",
    "snapshot_quality_report_path",
    "report_path",
    "rows_path",
    "issues_path",
    "metadata_path",
    "source_upstream_selections",
    "symbols",
    "min_trade_date",
    "max_trade_date",
    "warning_count",
    "no_live_trading_statement_present",
]


@dataclass(frozen=True)
class MarketCacheExportIndexArtifactPaths:
    artifact_dir: Path
    market_cache_export_index_report: Path
    market_cache_export_index_csv: Path
    market_cache_export_index_json: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_cache_export_index_report": self.market_cache_export_index_report,
            "market_cache_export_index_csv": self.market_cache_export_index_csv,
            "market_cache_export_index_json": self.market_cache_export_index_json,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MarketCacheExportIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_market_cache_export_artifacts(
    root: str | Path | None = None,
    *,
    include_missing_metadata: bool = False,
    settings: Settings | None = None,
) -> pd.DataFrame:
    project_settings = settings or load_settings(Path("config/default.yaml"))
    rows, _ = _scan_rows(
        Path(root) if root is not None else project_settings.market_cache_export_index.root_dir,
        include_missing_metadata=include_missing_metadata,
        project_settings=project_settings,
    )
    return _finalize_index_frame(pd.DataFrame(rows))


def build_market_cache_export_index(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    include_missing_metadata: bool | None = None,
    settings: Settings | MarketCacheExportIndexSettings | dict[str, Any] | None = None,
) -> MarketCacheExportIndexResult:
    project_settings, index_settings = _resolve_settings(settings)
    if index_settings.enable_live_trading or index_settings.enable_broker_api:
        raise ValueError("Market cache export index cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else index_settings.root_dir
    effective_output = Path(output_dir) if output_dir is not None else index_settings.output_dir
    effective_include_missing = (
        bool(include_missing_metadata)
        if include_missing_metadata is not None
        else index_settings.include_missing_metadata
    )
    rows, warnings = _scan_rows(
        effective_root,
        include_missing_metadata=effective_include_missing,
        project_settings=project_settings,
    )
    frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_market_cache_export_index_paths(effective_output)
    audit_metadata = {
        "root_dir": effective_root,
        "include_missing_metadata": effective_include_missing,
        "artifact_count": len(frame),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "market_cache_export_index_only": True,
        "config_version": index_settings.config_version,
    }
    result = MarketCacheExportIndexResult(
        artifact_count=len(frame),
        index_frame=frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=MARKET_CACHE_EXPORT_INDEX_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if index_settings.write_artifacts:
        write_market_cache_export_index(result)
    return result


def resolve_market_cache_export_index_paths(output_dir: str | Path) -> MarketCacheExportIndexArtifactPaths:
    artifact_dir = Path(output_dir)
    return MarketCacheExportIndexArtifactPaths(
        artifact_dir=artifact_dir,
        market_cache_export_index_report=artifact_dir / "market_cache_export_index_report.md",
        market_cache_export_index_csv=artifact_dir / "market_cache_export_index.csv",
        market_cache_export_index_json=artifact_dir / "market_cache_export_index.json",
        metadata=artifact_dir / "metadata.json",
    )


def write_market_cache_export_index(result: MarketCacheExportIndexResult) -> dict[str, Path]:
    paths = MarketCacheExportIndexArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    export = _sanitize_dataframe_for_export(result.index_frame)
    export.to_csv(paths.market_cache_export_index_csv, index=False)
    paths.market_cache_export_index_json.write_text(
        json.dumps(_json_safe(export.to_dict("records")), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    metadata = build_market_cache_export_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.market_cache_export_index_report.write_text(
        render_market_cache_export_index_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_market_cache_export_index_metadata(
    result: MarketCacheExportIndexResult,
    paths: MarketCacheExportIndexArtifactPaths,
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


def render_market_cache_export_index_report(
    result: MarketCacheExportIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {"index_id": _generate_index_id(result.index_frame, result.audit_metadata)}
    lines = [
        "# Market Cache Export Artifact Index",
        "",
        "No live trading or broker API was invoked. This index scans local reviewed cache-export artifacts only.",
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
        "## Reviewed Cache Exports",
        "",
        _markdown_table(
            result.index_frame,
            [
                "export_id",
                "status",
                "exported_row_count",
                "duplicate_key_count",
                "pipeline_id",
                "data_quality_status",
                "snapshot_quality_status",
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


def _scan_rows(
    root: Path,
    *,
    include_missing_metadata: bool,
    project_settings: Settings,
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not root.exists():
        warnings.append(f"Market cache export root not found: {root}")
        return rows, warnings
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"}:
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, metadata_path))
            else:
                warnings.append(f"Skipping market cache export folder missing metadata.json: {artifact_dir}")
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Skipping unreadable metadata {metadata_path}: {exc}")
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, metadata_path, status="FAIL"))
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata, project_settings))
    return rows, warnings


def _row_from_metadata(
    artifact_dir: Path,
    metadata_path: Path,
    metadata: dict[str, Any],
    project_settings: Settings,
) -> dict[str, Any]:
    paths = metadata.get("artifact_paths", {}) if isinstance(metadata.get("artifact_paths"), dict) else {}
    audit = metadata.get("audit_metadata", {}) if isinstance(metadata.get("audit_metadata"), dict) else {}
    report_path = _path_or_default(paths.get("market_cache_export_report"), artifact_dir / "market_cache_export_report.md")
    rows_path = _path_or_default(paths.get("market_cache_export_rows"), artifact_dir / "market_cache_export_rows.csv")
    issues_path = _path_or_default(paths.get("market_cache_export_issues"), artifact_dir / "market_cache_export_issues.csv")
    exported_path = _string(metadata.get("exported_market_csv_path")) or _string(paths.get("exported_market_csv"))
    generated_manifest = (
        _string(metadata.get("generated_pipeline_manifest_path"))
        or _string(audit.get("generated_pipeline_manifest_path"))
        or _string(paths.get("generated_pipeline_manifest"))
    )
    export_rows = metadata.get("export_rows", []) if isinstance(metadata.get("export_rows"), list) else []
    coverage = _coverage_from_export_rows(export_rows)
    if not coverage["symbols"] and exported_path:
        coverage = _coverage_from_exported_csv(Path(exported_path), coverage)
    linked = _linked_pipeline_fields(metadata, generated_manifest, project_settings)
    return {
        "export_id": str(metadata.get("export_id") or audit.get("export_id") or artifact_dir.name),
        "artifact_dir": str(artifact_dir),
        "created_at": str(metadata.get("created_at") or ""),
        "artifact_updated_at": _artifact_updated_at(metadata_path, artifact_dir),
        "status": str(metadata.get("status") or ""),
        "exported_market_csv_path": exported_path,
        "exported_row_count": int(_number(metadata.get("row_count", audit.get("row_count", 0)))),
        "duplicate_key_count": int(_number(metadata.get("duplicate_key_count", audit.get("duplicate_key_count", 0)))),
        "generated_pipeline_manifest_path": generated_manifest,
        "pipeline_id": linked["pipeline_id"],
        "data_pipeline_status": linked["data_pipeline_status"],
        "data_pipeline_report_path": linked["data_pipeline_report_path"],
        "data_quality_status": linked["data_quality_status"],
        "data_quality_report_path": linked["data_quality_report_path"],
        "snapshot_manifest_path": linked["snapshot_manifest_path"],
        "snapshot_quality_status": linked["snapshot_quality_status"],
        "snapshot_quality_report_path": linked["snapshot_quality_report_path"],
        "report_path": str(report_path),
        "rows_path": str(rows_path),
        "issues_path": str(issues_path),
        "metadata_path": str(metadata_path),
        "source_upstream_selections": coverage["source_upstream_selections"],
        "symbols": coverage["symbols"],
        "min_trade_date": coverage["min_trade_date"],
        "max_trade_date": coverage["max_trade_date"],
        "warning_count": len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else 0,
        "no_live_trading_statement_present": _report_has_no_live_statement(report_path),
    }


def _linked_pipeline_fields(metadata: dict[str, Any], generated_manifest: str, project_settings: Settings) -> dict[str, str]:
    direct = {
        "pipeline_id": _string(metadata.get("pipeline_id")),
        "data_pipeline_status": _string(metadata.get("data_pipeline_status") or metadata.get("pipeline_status")),
        "data_pipeline_report_path": _string(metadata.get("data_pipeline_report_path")),
        "data_quality_status": _string(metadata.get("data_quality_status")),
        "data_quality_report_path": _string(metadata.get("data_quality_report_path")),
        "snapshot_manifest_path": _string(metadata.get("snapshot_manifest_path")),
        "snapshot_quality_status": _string(metadata.get("snapshot_quality_status")),
        "snapshot_quality_report_path": _string(metadata.get("snapshot_quality_report_path")),
    }
    if direct["pipeline_id"] and direct["data_pipeline_status"]:
        return direct

    inferred = {key: "" for key in direct}
    manifest_path = Path(generated_manifest) if generated_manifest else None
    if manifest_path is None or not manifest_path.exists():
        return {**inferred, **{key: value for key, value in direct.items() if value}}
    try:
        requests = load_data_pipeline_manifest(manifest_path)
    except Exception:
        return {**inferred, **{key: value for key, value in direct.items() if value}}
    pipeline_id = generate_data_pipeline_id(
        requests,
        project_settings.data_pipeline,
        run_data_quality=project_settings.data_pipeline.run_data_quality,
        build_snapshot_manifest=project_settings.data_pipeline.build_snapshot_manifest,
    )
    pipeline_paths = resolve_data_pipeline_artifact_paths(project_settings.data_pipeline.output_dir, pipeline_id)
    pipeline_metadata_path = pipeline_paths.metadata
    if not pipeline_metadata_path.exists():
        return {**inferred, **{key: value for key, value in direct.items() if value}}
    try:
        pipeline_metadata = json.loads(pipeline_metadata_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {**inferred, **{key: value for key, value in direct.items() if value}}

    market_quality = _market_quality_from_pipeline_metadata(pipeline_metadata)
    snapshot_manifest = _string(pipeline_metadata.get("snapshot_manifest_path")) or _string(
        pipeline_metadata.get("output_files", {}).get("snapshot_manifest")
        if isinstance(pipeline_metadata.get("output_files"), dict)
        else ""
    )
    snapshot_quality = _find_snapshot_quality(
        f"pipeline_{pipeline_id}",
        project_settings.snapshot_quality_gate.output_dir,
    )
    inferred.update(
        {
            "pipeline_id": pipeline_id,
            "data_pipeline_status": _string(pipeline_metadata.get("status")),
            "data_pipeline_report_path": _string(
                pipeline_metadata.get("output_files", {}).get("data_pipeline_report")
                if isinstance(pipeline_metadata.get("output_files"), dict)
                else pipeline_paths.data_pipeline_report
            )
            or str(pipeline_paths.data_pipeline_report),
            "data_quality_status": market_quality["data_quality_status"],
            "data_quality_report_path": market_quality["data_quality_report_path"],
            "snapshot_manifest_path": snapshot_manifest,
            "snapshot_quality_status": snapshot_quality["snapshot_quality_status"],
            "snapshot_quality_report_path": snapshot_quality["snapshot_quality_report_path"],
        }
    )
    inferred.update({key: value for key, value in direct.items() if value})
    return inferred


def _market_quality_from_pipeline_metadata(metadata: dict[str, Any]) -> dict[str, str]:
    results = metadata.get("dataset_results", [])
    if isinstance(results, list):
        for row in results:
            if isinstance(row, dict) and str(row.get("dataset_type", "")).lower() == "market":
                return {
                    "data_quality_status": _string(row.get("data_quality_status")),
                    "data_quality_report_path": _string(row.get("data_quality_report_path")),
                }
    return {"data_quality_status": "", "data_quality_report_path": ""}


def _find_snapshot_quality(snapshot_id: str, root: str | Path) -> dict[str, str]:
    candidates: list[tuple[float, Path, dict[str, Any]]] = []
    root_path = Path(root)
    if not root_path.exists():
        return {"snapshot_quality_status": "", "snapshot_quality_report_path": ""}
    for metadata_path in root_path.glob("*/metadata.json"):
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if str(metadata.get("snapshot_id", "")) != snapshot_id:
            continue
        try:
            mtime = metadata_path.stat().st_mtime
        except OSError:
            mtime = 0.0
        candidates.append((mtime, metadata_path, metadata))
    if not candidates:
        return {"snapshot_quality_status": "", "snapshot_quality_report_path": ""}
    _, metadata_path, metadata = sorted(candidates, key=lambda item: item[0], reverse=True)[0]
    output_files = metadata.get("output_files", {}) if isinstance(metadata.get("output_files"), dict) else {}
    report_path = _string(output_files.get("snapshot_quality_gate_report")) or str(
        metadata_path.parent / "snapshot_quality_gate_report.md"
    )
    return {
        "snapshot_quality_status": _string(metadata.get("status")),
        "snapshot_quality_report_path": report_path,
    }


def _missing_metadata_row(artifact_dir: Path, metadata_path: Path, *, status: str = "MISSING_METADATA") -> dict[str, Any]:
    return {
        **{column: "" for column in INDEX_COLUMNS},
        "export_id": artifact_dir.name,
        "artifact_dir": str(artifact_dir),
        "status": status,
        "report_path": str(artifact_dir / "market_cache_export_report.md"),
        "metadata_path": str(metadata_path),
    }


def _coverage_from_export_rows(rows: list[Any]) -> dict[str, str]:
    if not rows:
        return {"symbols": "", "min_trade_date": "", "max_trade_date": "", "source_upstream_selections": ""}
    symbols: list[str] = []
    sources: list[str] = []
    starts: list[str] = []
    ends: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        symbol = _string(row.get("symbol"))
        source = _string(row.get("source"))
        upstream = _string(row.get("upstream_source"))
        if symbol:
            symbols.append(symbol)
        if source or upstream:
            sources.append(f"{source}/{upstream}".strip("/"))
        starts.append(_string(row.get("min_trade_date") or row.get("start_date")))
        ends.append(_string(row.get("max_trade_date") or row.get("end_date")))
    return {
        "symbols": ",".join(dict.fromkeys(sorted(value for value in symbols if value))),
        "min_trade_date": min(value for value in starts if value) if any(starts) else "",
        "max_trade_date": max(value for value in ends if value) if any(ends) else "",
        "source_upstream_selections": ",".join(dict.fromkeys(sorted(value for value in sources if value))),
    }


def _coverage_from_exported_csv(path: Path, fallback: dict[str, str]) -> dict[str, str]:
    if not path.exists():
        return fallback
    try:
        frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception:
        return fallback
    symbols = sorted(str(value).strip() for value in frame.get("symbol", pd.Series(dtype="object")).tolist() if str(value).strip())
    trade_dates = [str(value).strip() for value in frame.get("trade_date", pd.Series(dtype="object")).tolist() if str(value).strip()]
    sources = []
    if {"source", "upstream_source"}.issubset(frame.columns):
        sources = [
            f"{str(row.source).strip()}/{str(row.upstream_source).strip()}".strip("/")
            for row in frame[["source", "upstream_source"]].drop_duplicates().itertuples(index=False)
        ]
    return {
        "symbols": fallback.get("symbols") or ",".join(dict.fromkeys(symbols)),
        "min_trade_date": fallback.get("min_trade_date") or (min(trade_dates) if trade_dates else ""),
        "max_trade_date": fallback.get("max_trade_date") or (max(trade_dates) if trade_dates else ""),
        "source_upstream_selections": fallback.get("source_upstream_selections") or ",".join(dict.fromkeys(sorted(sources))),
    }


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS)
    output = frame.copy(deep=True)
    for column in INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    output = output[INDEX_COLUMNS]
    output["_created_sort"] = pd.to_datetime(output["created_at"], errors="coerce")
    output["_updated_sort"] = pd.to_datetime(output["artifact_updated_at"], errors="coerce")
    output = output.sort_values(
        ["_created_sort", "_updated_sort", "export_id"],
        ascending=[False, False, False],
        na_position="last",
    )
    output = output.drop(columns=["_created_sort", "_updated_sort"])
    return output.reset_index(drop=True)


def _path_or_default(value: Any, default: Path) -> Path:
    text = _string(value)
    return Path(text) if text else default


def _artifact_updated_at(metadata_path: Path, artifact_dir: Path) -> str:
    for path in [metadata_path, artifact_dir]:
        try:
            timestamp = path.stat().st_mtime
        except OSError:
            continue
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
    return ""


def _report_has_no_live_statement(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return any(statement in content for statement in NO_LIVE_STATEMENTS)


def _resolve_settings(
    settings: Settings | MarketCacheExportIndexSettings | dict[str, Any] | None,
) -> tuple[Settings, MarketCacheExportIndexSettings]:
    project = load_settings(Path("config/default.yaml"))
    if settings is None:
        return project, project.market_cache_export_index
    if isinstance(settings, Settings):
        return settings, settings.market_cache_export_index
    if isinstance(settings, MarketCacheExportIndexSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.market_cache_export_index.model_dump())
        payload.update(settings.get("market_cache_export_index", settings))
        return project, MarketCacheExportIndexSettings(**payload)
    raise TypeError("settings must be Settings, MarketCacheExportIndexSettings, dict, or None")


def _generate_index_id(frame: pd.DataFrame, metadata: dict[str, Any]) -> str:
    payload = {
        "root_dir": str(metadata.get("root_dir", "")),
        "export_ids": sorted(frame.get("export_id", pd.Series(dtype="object")).astype(str).tolist()),
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
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return value
