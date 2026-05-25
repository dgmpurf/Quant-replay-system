"""Local-only status view for reviewed market-cache-export artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketCacheExportStatusSettings, Settings, load_settings
from quant_replay_system.market_cache_export_health import check_market_cache_export_health
from quant_replay_system.market_cache_export_index import build_market_cache_export_index


MARKET_CACHE_EXPORT_STATUS_LIMITATIONS = [
    "Scans local market-cache-export metadata only.",
    "Does not regenerate exports, mutate the market cache, fetch data, place orders, or call broker APIs.",
    "Stage inference is conservative when linked pipeline or snapshot artifacts are missing.",
]

STATUS_COLUMNS = [
    "component",
    "status",
    "latest_export_id",
    "report_path",
    "metadata_path",
    "issue_count",
    "warning_count",
    "error_count",
    "next_action",
    "notes",
]


@dataclass(frozen=True)
class MarketCacheExportStatusArtifactPaths:
    artifact_dir: Path
    market_cache_export_status_report: Path
    market_cache_export_status_csv: Path
    market_cache_export_status_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_cache_export_status_report": self.market_cache_export_status_report,
            "market_cache_export_status_csv": self.market_cache_export_status_csv,
            "market_cache_export_status_summary": self.market_cache_export_status_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MarketCacheExportStatusResult:
    status_id: str
    status: str
    workflow_stage: str
    latest_export_id: str
    next_manual_action: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_market_cache_export_status(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    config: Settings | MarketCacheExportStatusSettings | dict[str, Any] | str | Path | None = None,
) -> MarketCacheExportStatusResult:
    project_settings, status_settings = _resolve_settings(config)
    if status_settings.enable_live_trading or status_settings.enable_broker_api:
        raise ValueError("Market cache export status cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else status_settings.root_dir
    effective_output = Path(output_dir) if output_dir is not None else status_settings.output_dir
    index = build_market_cache_export_index(
        root=effective_root,
        output_dir=effective_output / "_index",
        settings=project_settings.model_copy(
            update={
                "market_cache_export_index": project_settings.market_cache_export_index.model_copy(
                    update={"write_artifacts": False}
                )
            }
        ),
    )
    health = check_market_cache_export_health(
        index_df=index.index_frame,
        output_dir=effective_output / "_health",
        settings=project_settings.model_copy(
            update={
                "market_cache_export_health": project_settings.market_cache_export_health.model_copy(
                    update={"write_artifacts": False}
                )
            }
        ),
    )
    latest = _latest_export(index.index_frame)
    workflow_stage = infer_market_cache_export_stage(latest, health.status)
    next_action = infer_market_cache_export_next_action(latest, health.status, workflow_stage)
    status_frame = build_market_cache_export_status_frame(index.index_frame, health, latest)
    summary_frame = summarize_market_cache_export_status(
        latest,
        health,
        workflow_stage=workflow_stage,
        next_manual_action=next_action,
    )
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "WARN"
    status_id = generate_market_cache_export_status_id(
        status_frame,
        root=effective_root,
        config_version=status_settings.config_version,
    )
    paths = resolve_market_cache_export_status_paths(effective_output, status_id)
    warnings = list(index.warnings) + list(health.warnings)
    audit_metadata = {
        "status_id": status_id,
        "root_dir": effective_root,
        "workflow_stage": workflow_stage,
        "latest_export_id": str(latest.get("export_id", "")),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "market_cache_export_status_only": True,
        "config_version": status_settings.config_version,
    }
    result = MarketCacheExportStatusResult(
        status_id=status_id,
        status=status,
        workflow_stage=workflow_stage,
        latest_export_id=str(latest.get("export_id", "")),
        next_manual_action=next_action,
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=MARKET_CACHE_EXPORT_STATUS_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if status_settings.write_artifacts:
        write_market_cache_export_status_artifacts(result)
    return result


def build_market_cache_export_status_frame(
    index_frame: pd.DataFrame,
    health_result: Any,
    latest: dict[str, Any],
) -> pd.DataFrame:
    rows = [
        {
            "component": "MARKET_CACHE_EXPORT_INDEX",
            "status": "PASS" if not index_frame.empty else "WARN",
            "latest_export_id": str(latest.get("export_id", "")),
            "report_path": "",
            "metadata_path": "",
            "issue_count": 0,
            "warning_count": 0,
            "error_count": 0,
            "next_action": "Run market-cache-export-health.",
            "notes": f"{len(index_frame)} reviewed cache export artifact(s) indexed.",
        },
        {
            "component": "MARKET_CACHE_EXPORT_HEALTH",
            "status": health_result.status,
            "latest_export_id": str(latest.get("export_id", "")),
            "report_path": health_result.artifact_paths.get("market_cache_export_health_report", ""),
            "metadata_path": health_result.artifact_paths.get("metadata", ""),
            "issue_count": health_result.issue_count,
            "warning_count": health_result.warning_count,
            "error_count": health_result.error_count,
            "next_action": "Repair missing or duplicate reviewed export artifacts." if health_result.status == "FAIL" else "",
            "notes": f"{health_result.checked_artifact_count} reviewed cache export artifact(s) checked.",
        },
        {
            "component": "LATEST_MARKET_CACHE_EXPORT",
            "status": str(latest.get("status", "MISSING")) if latest else "MISSING",
            "latest_export_id": str(latest.get("export_id", "")),
            "report_path": str(latest.get("report_path", "")),
            "metadata_path": str(latest.get("metadata_path", "")),
            "issue_count": 0,
            "warning_count": int(_number(latest.get("warning_count", 0))) if latest else 0,
            "error_count": int(_number(latest.get("duplicate_key_count", 0))) if latest else 0,
            "next_action": "",
            "notes": _latest_notes(latest),
        },
    ]
    return pd.DataFrame(rows, columns=STATUS_COLUMNS)


def summarize_market_cache_export_status(
    latest: dict[str, Any],
    health_result: Any,
    *,
    workflow_stage: str,
    next_manual_action: str,
) -> pd.DataFrame:
    if not latest:
        status = "WARN"
    elif health_result.status == "FAIL":
        status = "FAIL"
    elif str(latest.get("status", "")).upper() == "FAIL":
        status = "FAIL"
    elif health_result.status == "WARN" or str(latest.get("status", "")).upper() == "WARN":
        status = "WARN"
    else:
        status = str(latest.get("status") or "PASS").upper()
    return pd.DataFrame(
        [
            {
                "status": status,
                "workflow_stage": workflow_stage,
                "latest_export_id": str(latest.get("export_id", "")),
                "exported_row_count": int(_number(latest.get("exported_row_count", 0))) if latest else 0,
                "duplicate_key_count": int(_number(latest.get("duplicate_key_count", 0))) if latest else 0,
                "generated_pipeline_manifest_path": str(latest.get("generated_pipeline_manifest_path", "")),
                "pipeline_id": str(latest.get("pipeline_id", "")),
                "data_pipeline_status": str(latest.get("data_pipeline_status", "")),
                "data_quality_status": str(latest.get("data_quality_status", "")),
                "snapshot_quality_status": str(latest.get("snapshot_quality_status", "")),
                "health_status": health_result.status,
                "issue_count": health_result.issue_count,
                "warning_count": health_result.warning_count,
                "error_count": health_result.error_count,
                "next_manual_action": next_manual_action,
                "report_path": str(latest.get("report_path", "")),
                "no_live_trading": True,
                "no_broker_api": True,
            }
        ]
    )


def infer_market_cache_export_stage(latest: dict[str, Any], health_status: str) -> str:
    if not latest:
        return "NO_CACHE_EXPORT_ARTIFACTS"
    if health_status == "FAIL":
        return "CACHE_EXPORT_FAILED"
    if str(latest.get("status", "")).upper() == "FAIL":
        return "CACHE_EXPORT_FAILED"
    if health_status == "WARN":
        return "CACHE_EXPORT_HEALTH_WARN"
    if str(latest.get("snapshot_quality_status", "")).upper() == "PASS":
        return "SNAPSHOT_READY_FROM_EXPORT"
    if str(latest.get("data_quality_status", "")).upper() == "PASS":
        return "DATA_QUALITY_READY_FROM_EXPORT"
    if str(latest.get("data_pipeline_status", "")).upper() == "PASS" or str(latest.get("pipeline_id", "")):
        return "PIPELINE_READY_FROM_EXPORT"
    if str(latest.get("status", "")).upper() == "PASS" and int(_number(latest.get("duplicate_key_count", 0))) == 0:
        return "CACHE_EXPORT_READY"
    return "CACHE_EXPORT_HEALTH_WARN"


def infer_market_cache_export_next_action(
    latest: dict[str, Any],
    health_status: str,
    workflow_stage: str,
) -> str:
    if not latest:
        return "Run market-cache-export with a reviewed source/upstream manifest."
    if health_status == "FAIL" or workflow_stage == "CACHE_EXPORT_FAILED":
        return "Review market-cache-export-health errors before using this export downstream."
    if workflow_stage == "SNAPSHOT_READY_FROM_EXPORT":
        return "Use the snapshot manifest for current-candidates or link this export into research-status."
    if workflow_stage == "DATA_QUALITY_READY_FROM_EXPORT":
        return "Run snapshot-quality on the linked pipeline snapshot manifest before research use."
    if workflow_stage == "PIPELINE_READY_FROM_EXPORT":
        return "Run data-quality/snapshot-quality if not already completed for the exported market CSV."
    if workflow_stage == "CACHE_EXPORT_READY":
        return "Run data-pipeline with the generated manifest, then data-quality and snapshot-quality."
    return "Inspect export health warnings before downstream snapshot workflows."


def resolve_market_cache_export_status_paths(
    output_dir: str | Path,
    status_id: str,
) -> MarketCacheExportStatusArtifactPaths:
    artifact_dir = Path(output_dir) / status_id
    return MarketCacheExportStatusArtifactPaths(
        artifact_dir=artifact_dir,
        market_cache_export_status_report=artifact_dir / "market_cache_export_status_report.md",
        market_cache_export_status_csv=artifact_dir / "market_cache_export_status.csv",
        market_cache_export_status_summary=artifact_dir / "market_cache_export_status_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_market_cache_export_status_artifacts(result: MarketCacheExportStatusResult) -> dict[str, Path]:
    paths = MarketCacheExportStatusArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.status_frame.to_csv(paths.market_cache_export_status_csv, index=False)
    result.summary_frame.to_csv(paths.market_cache_export_status_summary, index=False)
    metadata = {
        "status_id": result.status_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_export_id": result.latest_export_id,
        "next_manual_action": result.next_manual_action,
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.market_cache_export_status_report.write_text(
        render_market_cache_export_status_report(result),
        encoding="utf-8",
    )
    return paths.as_dict()


def render_market_cache_export_status_report(result: MarketCacheExportStatusResult) -> str:
    lines = [
        "# Market Cache Export Status",
        "",
        "No live trading or broker API was invoked. This status view summarizes local reviewed cache-export artifacts only.",
        "",
        "## Summary",
        "",
        result.summary_frame.to_markdown(index=False),
        "",
        "## Components",
        "",
        result.status_frame.to_markdown(index=False),
    ]
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in result.known_limitations)
    return "\n".join(lines) + "\n"


def _latest_export(index_frame: pd.DataFrame) -> dict[str, Any]:
    if index_frame.empty:
        return {}
    frame = index_frame.copy(deep=True)
    frame["_created_sort"] = pd.to_datetime(frame.get("created_at", ""), errors="coerce")
    frame["_updated_sort"] = pd.to_datetime(frame.get("artifact_updated_at", ""), errors="coerce")
    frame = frame.sort_values(
        ["_created_sort", "_updated_sort", "export_id"],
        ascending=[False, False, False],
        na_position="last",
    )
    return frame.drop(columns=["_created_sort", "_updated_sort"]).iloc[0].to_dict()


def _latest_notes(latest: dict[str, Any]) -> str:
    if not latest:
        return "No market-cache-export artifacts found."
    return (
        f"exported_row_count={latest.get('exported_row_count', '')}; "
        f"duplicate_key_count={latest.get('duplicate_key_count', '')}; "
        f"pipeline_id={latest.get('pipeline_id', '')}; "
        f"data_quality_status={latest.get('data_quality_status', '')}; "
        f"snapshot_quality_status={latest.get('snapshot_quality_status', '')}"
    )


def _resolve_settings(
    config: Settings | MarketCacheExportStatusSettings | dict[str, Any] | str | Path | None,
) -> tuple[Settings, MarketCacheExportStatusSettings]:
    if isinstance(config, (str, Path)):
        project = load_settings(config)
        return project, project.market_cache_export_status
    project = load_settings(Path("config/default.yaml"))
    if config is None:
        return project, project.market_cache_export_status
    if isinstance(config, Settings):
        return config, config.market_cache_export_status
    if isinstance(config, MarketCacheExportStatusSettings):
        return project, config
    if isinstance(config, dict):
        payload = dict(project.market_cache_export_status.model_dump())
        payload.update(config.get("market_cache_export_status", config))
        return project, MarketCacheExportStatusSettings(**payload)
    raise TypeError("config must be Settings, MarketCacheExportStatusSettings, dict, path, or None")


def generate_market_cache_export_status_id(
    status_frame: pd.DataFrame,
    *,
    root: Path,
    config_version: str,
) -> str:
    payload = {
        "root": str(root),
        "components": status_frame.to_dict("records"),
        "config_version": config_version,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


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
