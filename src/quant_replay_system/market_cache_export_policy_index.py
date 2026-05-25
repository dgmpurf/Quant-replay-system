"""Local-only index for market-cache-export policy recommendation plans."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketCacheExportPolicyIndexSettings, Settings, load_settings
from quant_replay_system.data import read_csv_preserve_symbol_columns
from quant_replay_system.market_cache_export_index import build_market_cache_export_index


NO_LIVE_STATEMENTS = [
    "No broker or live trading integration was invoked",
    "No live trading or broker API was invoked",
]

MARKET_CACHE_EXPORT_POLICY_INDEX_LIMITATIONS = [
    "Scans local market-cache-export policy recommendation artifacts only.",
    "Reads generated manifests and linked local export artifacts when available.",
    "Does not run export, mutate the market cache, fetch real data, place orders, or call broker APIs.",
]

INDEX_COLUMNS = [
    "plan_id",
    "artifact_dir",
    "created_at",
    "artifact_updated_at",
    "status",
    "recommendation_count",
    "recommended_count",
    "recommended_with_warnings_count",
    "no_reliable_source_count",
    "no_cache_rows_count",
    "comparison_pass_count",
    "comparison_warn_count",
    "comparison_fail_count",
    "comparison_unavailable_count",
    "comparison_required_but_missing_count",
    "comparison_supported_recommendation_count",
    "comparison_unsupported_recommendation_count",
    "generated_reviewed_manifest_path",
    "report_path",
    "recommendations_path",
    "issues_path",
    "metadata_path",
    "symbols",
    "min_start_date",
    "max_end_date",
    "downstream_export_id",
    "downstream_export_status",
    "downstream_export_report_path",
    "downstream_pipeline_id",
    "downstream_snapshot_quality_status",
    "downstream_snapshot_quality_report_path",
    "warning_count",
    "no_live_trading_statement_present",
]


@dataclass(frozen=True)
class MarketCacheExportPolicyIndexArtifactPaths:
    artifact_dir: Path
    market_cache_export_policy_index_report: Path
    market_cache_export_policy_index_csv: Path
    market_cache_export_policy_index_json: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_cache_export_policy_index_report": self.market_cache_export_policy_index_report,
            "market_cache_export_policy_index_csv": self.market_cache_export_policy_index_csv,
            "market_cache_export_policy_index_json": self.market_cache_export_policy_index_json,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MarketCacheExportPolicyIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_market_cache_export_policy_artifacts(
    root: str | Path | None = None,
    *,
    include_missing_metadata: bool = False,
    settings: Settings | None = None,
) -> pd.DataFrame:
    project_settings = settings or load_settings(Path("config/default.yaml"))
    rows, _warnings = _scan_rows(
        Path(root) if root is not None else project_settings.market_cache_export_policy_index.root_dir,
        include_missing_metadata=include_missing_metadata,
        project_settings=project_settings,
    )
    return _finalize_index_frame(pd.DataFrame(rows))


def build_market_cache_export_policy_index(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    include_missing_metadata: bool | None = None,
    settings: Settings | MarketCacheExportPolicyIndexSettings | dict[str, Any] | None = None,
) -> MarketCacheExportPolicyIndexResult:
    project_settings, index_settings = _resolve_settings(settings)
    if index_settings.enable_live_trading or index_settings.enable_broker_api:
        raise ValueError("Market cache export policy index cannot enable live trading or broker API access")

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
    paths = resolve_market_cache_export_policy_index_paths(effective_output)
    audit_metadata = {
        "root_dir": effective_root,
        "include_missing_metadata": effective_include_missing,
        "artifact_count": len(frame),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "market_cache_export_policy_index_only": True,
        "config_version": index_settings.config_version,
    }
    result = MarketCacheExportPolicyIndexResult(
        artifact_count=len(frame),
        index_frame=frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=MARKET_CACHE_EXPORT_POLICY_INDEX_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if index_settings.write_artifacts:
        write_market_cache_export_policy_index(result)
    return result


def resolve_market_cache_export_policy_index_paths(
    output_dir: str | Path,
) -> MarketCacheExportPolicyIndexArtifactPaths:
    artifact_dir = Path(output_dir)
    return MarketCacheExportPolicyIndexArtifactPaths(
        artifact_dir=artifact_dir,
        market_cache_export_policy_index_report=artifact_dir / "market_cache_export_policy_index_report.md",
        market_cache_export_policy_index_csv=artifact_dir / "market_cache_export_policy_index.csv",
        market_cache_export_policy_index_json=artifact_dir / "market_cache_export_policy_index.json",
        metadata=artifact_dir / "metadata.json",
    )


def write_market_cache_export_policy_index(result: MarketCacheExportPolicyIndexResult) -> dict[str, Path]:
    paths = MarketCacheExportPolicyIndexArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    export = _sanitize_dataframe_for_export(result.index_frame)
    export.to_csv(paths.market_cache_export_policy_index_csv, index=False)
    paths.market_cache_export_policy_index_json.write_text(
        json.dumps(_json_safe(export.to_dict("records")), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    metadata = build_market_cache_export_policy_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.market_cache_export_policy_index_report.write_text(
        render_market_cache_export_policy_index_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_market_cache_export_policy_index_metadata(
    result: MarketCacheExportPolicyIndexResult,
    paths: MarketCacheExportPolicyIndexArtifactPaths,
) -> dict[str, Any]:
    return {
        "index_id": _generate_index_id(result.index_frame, result.audit_metadata),
        "artifact_count": result.artifact_count,
        "root_dir": str(result.audit_metadata.get("root_dir", "")),
        "comparison_totals": _comparison_totals(result.index_frame),
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }


def render_market_cache_export_policy_index_report(
    result: MarketCacheExportPolicyIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {"index_id": _generate_index_id(result.index_frame, result.audit_metadata)}
    lines = [
        "# Market Cache Export Policy Artifact Index",
        "",
        "No live trading or broker API was invoked. This index scans local policy recommendation artifacts only.",
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
        "## Policy Plans",
        "",
        _markdown_table(
            result.index_frame,
            [
                "plan_id",
                "status",
                "recommendation_count",
                "recommended_count",
                "recommended_with_warnings_count",
                "comparison_pass_count",
                "comparison_fail_count",
                "comparison_unavailable_count",
                "downstream_export_id",
                "downstream_snapshot_quality_status",
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
        warnings.append(f"Market cache export policy root not found: {root}")
        return rows, warnings
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, metadata_path))
            else:
                warnings.append(f"Skipping market cache export policy folder missing metadata.json: {artifact_dir}")
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
    plan_id = str(metadata.get("plan_id") or audit.get("plan_id") or artifact_dir.name)
    report_path = _path_or_default(
        paths.get("market_cache_export_policy_report"),
        artifact_dir / "market_cache_export_policy_report.md",
    )
    recommendations_path = _path_or_default(
        paths.get("market_cache_export_policy_recommendations"),
        artifact_dir / "market_cache_export_policy_recommendations.csv",
    )
    issues_path = _path_or_default(
        paths.get("market_cache_export_policy_issues"),
        artifact_dir / "market_cache_export_policy_issues.csv",
    )
    generated_manifest = (
        _string(metadata.get("generated_reviewed_manifest_path"))
        or _string(audit.get("generated_reviewed_manifest_path"))
        or _string(paths.get("recommended_manifest"))
    )
    recommendations = metadata.get("recommendations", []) if isinstance(metadata.get("recommendations"), list) else []
    recommendation_frame = _recommendations_frame(recommendations, recommendations_path)
    counts = _recommendation_counts(recommendation_frame)
    comparison = _comparison_counts(recommendation_frame)
    coverage = _coverage_from_recommendations(recommendation_frame)
    downstream = _linked_export_fields(generated_manifest, project_settings)
    return {
        "plan_id": plan_id,
        "artifact_dir": str(artifact_dir),
        "created_at": str(metadata.get("created_at") or ""),
        "artifact_updated_at": _artifact_updated_at(metadata_path, artifact_dir),
        "status": str(metadata.get("status") or ""),
        "recommendation_count": int(_number(metadata.get("recommendation_count", counts["recommendation_count"]))),
        "recommended_count": counts["recommended_count"],
        "recommended_with_warnings_count": counts["recommended_with_warnings_count"],
        "no_reliable_source_count": counts["no_reliable_source_count"],
        "no_cache_rows_count": counts["no_cache_rows_count"],
        "comparison_pass_count": comparison["comparison_pass_count"],
        "comparison_warn_count": comparison["comparison_warn_count"],
        "comparison_fail_count": comparison["comparison_fail_count"],
        "comparison_unavailable_count": comparison["comparison_unavailable_count"],
        "comparison_required_but_missing_count": comparison["comparison_required_but_missing_count"],
        "comparison_supported_recommendation_count": comparison["comparison_supported_recommendation_count"],
        "comparison_unsupported_recommendation_count": comparison["comparison_unsupported_recommendation_count"],
        "generated_reviewed_manifest_path": generated_manifest,
        "report_path": str(report_path),
        "recommendations_path": str(recommendations_path),
        "issues_path": str(issues_path),
        "metadata_path": str(metadata_path),
        "symbols": coverage["symbols"],
        "min_start_date": coverage["min_start_date"],
        "max_end_date": coverage["max_end_date"],
        "downstream_export_id": downstream["downstream_export_id"],
        "downstream_export_status": downstream["downstream_export_status"],
        "downstream_export_report_path": downstream["downstream_export_report_path"],
        "downstream_pipeline_id": downstream["downstream_pipeline_id"],
        "downstream_snapshot_quality_status": downstream["downstream_snapshot_quality_status"],
        "downstream_snapshot_quality_report_path": downstream["downstream_snapshot_quality_report_path"],
        "warning_count": len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else 0,
        "no_live_trading_statement_present": _report_has_no_live_statement(report_path),
    }


def _recommendations_frame(recommendations: list[Any], recommendations_path: Path) -> pd.DataFrame:
    frame = pd.DataFrame([row for row in recommendations if isinstance(row, dict)])
    if frame.empty and recommendations_path.exists():
        try:
            frame = read_csv_preserve_symbol_columns(recommendations_path, keep_default_na=False)
        except Exception:
            frame = pd.DataFrame()
    return frame


def _recommendation_counts(frame: pd.DataFrame) -> dict[str, int]:
    if frame.empty or "status" not in frame.columns:
        return {
            "recommendation_count": 0,
            "recommended_count": 0,
            "recommended_with_warnings_count": 0,
            "no_reliable_source_count": 0,
            "no_cache_rows_count": 0,
        }
    statuses = frame["status"].astype(str).str.upper()
    return {
        "recommendation_count": int(statuses.isin({"RECOMMENDED", "RECOMMENDED_WITH_WARNINGS"}).sum()),
        "recommended_count": int(statuses.eq("RECOMMENDED").sum()),
        "recommended_with_warnings_count": int(statuses.eq("RECOMMENDED_WITH_WARNINGS").sum()),
        "no_reliable_source_count": int(statuses.eq("NO_RELIABLE_SOURCE").sum()),
        "no_cache_rows_count": int(statuses.eq("NO_CACHE_ROWS").sum()),
    }


def _comparison_counts(frame: pd.DataFrame) -> dict[str, int]:
    empty = {
        "comparison_pass_count": 0,
        "comparison_warn_count": 0,
        "comparison_fail_count": 0,
        "comparison_unavailable_count": 0,
        "comparison_required_but_missing_count": 0,
        "comparison_supported_recommendation_count": 0,
        "comparison_unsupported_recommendation_count": 0,
    }
    if frame.empty or "status" not in frame.columns:
        return empty
    statuses = frame["status"].astype(str).str.upper()
    acceptable = statuses.isin({"RECOMMENDED", "RECOMMENDED_WITH_WARNINGS"})
    if "comparison_status" not in frame.columns:
        return empty
    comparison_statuses = frame["comparison_status"].fillna("").astype(str).str.strip().str.upper()
    missing = acceptable & comparison_statuses.eq("")
    unavailable = acceptable & comparison_statuses.eq("UNAVAILABLE")
    supported = acceptable & comparison_statuses.isin({"PASS", "WARN", "FAIL"})
    unsupported = acceptable & (unavailable | missing)
    security = (
        frame["security_type"].fillna("").astype(str).str.upper()
        if "security_type" in frame.columns
        else pd.Series([""] * len(frame), index=frame.index)
    )
    required_missing = missing | (acceptable & security.eq("STOCK") & unavailable)
    return {
        "comparison_pass_count": int((acceptable & comparison_statuses.eq("PASS")).sum()),
        "comparison_warn_count": int((acceptable & comparison_statuses.eq("WARN")).sum()),
        "comparison_fail_count": int((acceptable & comparison_statuses.eq("FAIL")).sum()),
        "comparison_unavailable_count": int(unavailable.sum()),
        "comparison_required_but_missing_count": int(required_missing.sum()),
        "comparison_supported_recommendation_count": int(supported.sum()),
        "comparison_unsupported_recommendation_count": int(unsupported.sum()),
    }


def _coverage_from_recommendations(frame: pd.DataFrame) -> dict[str, str]:
    if frame.empty:
        return {"symbols": "", "min_start_date": "", "max_end_date": ""}
    symbols = sorted(str(value).strip() for value in frame.get("symbol", pd.Series(dtype="object")).tolist() if str(value).strip())
    starts = [str(value).strip() for value in frame.get("start_date", pd.Series(dtype="object")).tolist() if str(value).strip()]
    ends = [str(value).strip() for value in frame.get("end_date", pd.Series(dtype="object")).tolist() if str(value).strip()]
    return {
        "symbols": ",".join(dict.fromkeys(symbols)),
        "min_start_date": min(starts) if starts else "",
        "max_end_date": max(ends) if ends else "",
    }


def _linked_export_fields(generated_manifest: str, project_settings: Settings) -> dict[str, str]:
    empty = {
        "downstream_export_id": "",
        "downstream_export_status": "",
        "downstream_export_report_path": "",
        "downstream_pipeline_id": "",
        "downstream_snapshot_quality_status": "",
        "downstream_snapshot_quality_report_path": "",
    }
    if not generated_manifest:
        return empty
    export_root = project_settings.market_cache_export_index.root_dir
    if not export_root.exists():
        return empty
    manifest_path = str(Path(generated_manifest))
    candidates: list[tuple[float, dict[str, Any]]] = []
    for metadata_path in export_root.glob("*/metadata.json"):
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if str(Path(_string(metadata.get("manifest_path")))) != manifest_path:
            continue
        try:
            mtime = metadata_path.stat().st_mtime
        except OSError:
            mtime = 0.0
        candidates.append((mtime, metadata))
    if not candidates:
        return empty
    _mtime, metadata = sorted(candidates, key=lambda item: item[0], reverse=True)[0]
    paths = metadata.get("artifact_paths", {}) if isinstance(metadata.get("artifact_paths"), dict) else {}
    export_id = _string(metadata.get("export_id"))
    indexed = _indexed_export_fields(export_id, project_settings)
    return {
        "downstream_export_id": export_id,
        "downstream_export_status": _string(metadata.get("status")),
        "downstream_export_report_path": _string(paths.get("market_cache_export_report")),
        "downstream_pipeline_id": indexed.get("pipeline_id") or _string(metadata.get("pipeline_id")),
        "downstream_snapshot_quality_status": indexed.get("snapshot_quality_status") or _string(metadata.get("snapshot_quality_status")),
        "downstream_snapshot_quality_report_path": indexed.get("snapshot_quality_report_path") or _string(metadata.get("snapshot_quality_report_path")),
    }


def _indexed_export_fields(export_id: str, project_settings: Settings) -> dict[str, str]:
    if not export_id:
        return {}
    try:
        index = build_market_cache_export_index(
            root=project_settings.market_cache_export_index.root_dir,
            output_dir=project_settings.market_cache_export_index.output_dir / "_policy_link",
            settings=project_settings.model_copy(
                update={
                    "market_cache_export_index": project_settings.market_cache_export_index.model_copy(
                        update={"write_artifacts": False}
                    )
                }
            ),
        )
    except Exception:
        return {}
    frame = index.index_frame
    if frame.empty or "export_id" not in frame.columns:
        return {}
    matched = frame.loc[frame["export_id"].astype(str) == export_id]
    if matched.empty:
        return {}
    row = matched.iloc[0].to_dict()
    return {
        "pipeline_id": _string(row.get("pipeline_id")),
        "snapshot_quality_status": _string(row.get("snapshot_quality_status")),
        "snapshot_quality_report_path": _string(row.get("snapshot_quality_report_path")),
    }


def _missing_metadata_row(artifact_dir: Path, metadata_path: Path, *, status: str = "MISSING_METADATA") -> dict[str, Any]:
    return {
        **{column: "" for column in INDEX_COLUMNS},
        "plan_id": artifact_dir.name,
        "artifact_dir": str(artifact_dir),
        "status": status,
        "report_path": str(artifact_dir / "market_cache_export_policy_report.md"),
        "metadata_path": str(metadata_path),
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
        ["_created_sort", "_updated_sort", "plan_id"],
        ascending=[False, False, False],
        na_position="last",
    )
    return output.drop(columns=["_created_sort", "_updated_sort"]).reset_index(drop=True)


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
    settings: Settings | MarketCacheExportPolicyIndexSettings | dict[str, Any] | None,
) -> tuple[Settings, MarketCacheExportPolicyIndexSettings]:
    project = load_settings(Path("config/default.yaml"))
    if settings is None:
        return project, project.market_cache_export_policy_index
    if isinstance(settings, Settings):
        return settings, settings.market_cache_export_policy_index
    if isinstance(settings, MarketCacheExportPolicyIndexSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.market_cache_export_policy_index.model_dump())
        payload.update(settings.get("market_cache_export_policy_index", settings))
        return project, MarketCacheExportPolicyIndexSettings(**payload)
    raise TypeError("settings must be Settings, MarketCacheExportPolicyIndexSettings, dict, or None")


def _generate_index_id(frame: pd.DataFrame, metadata: dict[str, Any]) -> str:
    payload = {
        "root_dir": str(metadata.get("root_dir", "")),
        "plan_ids": sorted(frame.get("plan_id", pd.Series(dtype="object")).astype(str).tolist()),
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


def _comparison_totals(frame: pd.DataFrame) -> dict[str, int]:
    columns = [
        "comparison_pass_count",
        "comparison_warn_count",
        "comparison_fail_count",
        "comparison_unavailable_count",
        "comparison_required_but_missing_count",
        "comparison_supported_recommendation_count",
        "comparison_unsupported_recommendation_count",
    ]
    return {column: int(pd.to_numeric(frame.get(column, pd.Series(dtype="object")), errors="coerce").fillna(0).sum()) for column in columns}


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
