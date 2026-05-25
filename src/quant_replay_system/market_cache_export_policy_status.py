"""Local-only status view for market-cache-export policy recommendation plans."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketCacheExportPolicyStatusSettings, Settings, load_settings
from quant_replay_system.market_cache_export_policy_health import check_market_cache_export_policy_health
from quant_replay_system.market_cache_export_policy_index import build_market_cache_export_policy_index


MARKET_CACHE_EXPORT_POLICY_STATUS_LIMITATIONS = [
    "Scans local policy recommendation metadata only.",
    "Does not regenerate plans, run exports, mutate the market cache, fetch data, place orders, or call broker APIs.",
    "Stage inference is conservative when linked export or snapshot artifacts are missing.",
]

STATUS_COLUMNS = [
    "component",
    "status",
    "latest_plan_id",
    "report_path",
    "metadata_path",
    "issue_count",
    "warning_count",
    "error_count",
    "next_action",
    "notes",
]


@dataclass(frozen=True)
class MarketCacheExportPolicyStatusArtifactPaths:
    artifact_dir: Path
    market_cache_export_policy_status_report: Path
    market_cache_export_policy_status_csv: Path
    market_cache_export_policy_status_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_cache_export_policy_status_report": self.market_cache_export_policy_status_report,
            "market_cache_export_policy_status_csv": self.market_cache_export_policy_status_csv,
            "market_cache_export_policy_status_summary": self.market_cache_export_policy_status_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MarketCacheExportPolicyStatusResult:
    status_id: str
    status: str
    workflow_stage: str
    latest_plan_id: str
    next_manual_action: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_market_cache_export_policy_status(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    config: Settings | MarketCacheExportPolicyStatusSettings | dict[str, Any] | str | Path | None = None,
) -> MarketCacheExportPolicyStatusResult:
    project_settings, status_settings = _resolve_settings(config)
    if status_settings.enable_live_trading or status_settings.enable_broker_api:
        raise ValueError("Market cache export policy status cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else status_settings.root_dir
    effective_output = Path(output_dir) if output_dir is not None else status_settings.output_dir
    index = build_market_cache_export_policy_index(
        root=effective_root,
        output_dir=effective_output / "_index",
        settings=project_settings.model_copy(
            update={
                "market_cache_export_policy_index": project_settings.market_cache_export_policy_index.model_copy(
                    update={"write_artifacts": False}
                )
            }
        ),
    )
    health = check_market_cache_export_policy_health(
        index_df=index.index_frame,
        output_dir=effective_output / "_health",
        settings=project_settings.model_copy(
            update={
                "market_cache_export_policy_health": project_settings.market_cache_export_policy_health.model_copy(
                    update={"write_artifacts": False}
                )
            }
        ),
    )
    latest = _latest_plan(index.index_frame)
    workflow_stage = infer_market_cache_export_policy_stage(latest, health.status)
    next_action = infer_market_cache_export_policy_next_action(latest, health.status, workflow_stage)
    status_frame = build_market_cache_export_policy_status_frame(index.index_frame, health, latest)
    summary_frame = summarize_market_cache_export_policy_status(
        latest,
        health,
        workflow_stage=workflow_stage,
        next_manual_action=next_action,
    )
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "WARN"
    status_id = generate_market_cache_export_policy_status_id(
        status_frame,
        root=effective_root,
        config_version=status_settings.config_version,
    )
    paths = resolve_market_cache_export_policy_status_paths(effective_output, status_id)
    warnings = list(index.warnings) + list(health.warnings)
    audit_metadata = {
        "status_id": status_id,
        "root_dir": effective_root,
        "workflow_stage": workflow_stage,
        "latest_plan_id": str(latest.get("plan_id", "")),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "market_cache_export_policy_status_only": True,
        "config_version": status_settings.config_version,
    }
    result = MarketCacheExportPolicyStatusResult(
        status_id=status_id,
        status=status,
        workflow_stage=workflow_stage,
        latest_plan_id=str(latest.get("plan_id", "")),
        next_manual_action=next_action,
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=MARKET_CACHE_EXPORT_POLICY_STATUS_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if status_settings.write_artifacts:
        write_market_cache_export_policy_status_artifacts(result)
    return result


def build_market_cache_export_policy_status_frame(
    index_frame: pd.DataFrame,
    health_result: Any,
    latest: dict[str, Any],
) -> pd.DataFrame:
    rows = [
        {
            "component": "MARKET_CACHE_EXPORT_POLICY_INDEX",
            "status": "PASS" if not index_frame.empty else "WARN",
            "latest_plan_id": str(latest.get("plan_id", "")),
            "report_path": "",
            "metadata_path": "",
            "issue_count": 0,
            "warning_count": 0,
            "error_count": 0,
            "next_action": "Run market-cache-export-plan-health.",
            "notes": f"{len(index_frame)} policy plan artifact(s) indexed.",
        },
        {
            "component": "MARKET_CACHE_EXPORT_POLICY_HEALTH",
            "status": health_result.status,
            "latest_plan_id": str(latest.get("plan_id", "")),
            "report_path": health_result.artifact_paths.get("market_cache_export_policy_health_report", ""),
            "metadata_path": health_result.artifact_paths.get("metadata", ""),
            "issue_count": health_result.issue_count,
            "warning_count": health_result.warning_count,
            "error_count": health_result.error_count,
            "next_action": "Repair missing or malformed policy plan artifacts." if health_result.status == "FAIL" else "",
            "notes": f"{health_result.checked_artifact_count} policy plan artifact(s) checked.",
        },
        {
            "component": "LATEST_MARKET_CACHE_EXPORT_POLICY_PLAN",
            "status": str(latest.get("status", "MISSING")) if latest else "MISSING",
            "latest_plan_id": str(latest.get("plan_id", "")),
            "report_path": str(latest.get("report_path", "")),
            "metadata_path": str(latest.get("metadata_path", "")),
            "issue_count": 0,
            "warning_count": int(_number(latest.get("warning_count", 0))) if latest else 0,
            "error_count": int(_number(latest.get("no_reliable_source_count", 0)) + _number(latest.get("no_cache_rows_count", 0)))
            if latest
            else 0,
            "next_action": "",
            "notes": _latest_notes(latest),
        },
    ]
    return pd.DataFrame(rows, columns=STATUS_COLUMNS)


def summarize_market_cache_export_policy_status(
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
                "latest_plan_id": str(latest.get("plan_id", "")),
                "recommendation_count": int(_number(latest.get("recommendation_count", 0))) if latest else 0,
                "recommended_count": int(_number(latest.get("recommended_count", 0))) if latest else 0,
                "recommended_with_warnings_count": int(_number(latest.get("recommended_with_warnings_count", 0)))
                if latest
                else 0,
                "no_reliable_source_count": int(_number(latest.get("no_reliable_source_count", 0))) if latest else 0,
                "no_cache_rows_count": int(_number(latest.get("no_cache_rows_count", 0))) if latest else 0,
                "generated_reviewed_manifest_path": str(latest.get("generated_reviewed_manifest_path", "")),
                "downstream_export_id": str(latest.get("downstream_export_id", "")),
                "downstream_export_status": str(latest.get("downstream_export_status", "")),
                "downstream_pipeline_id": str(latest.get("downstream_pipeline_id", "")),
                "downstream_snapshot_quality_status": str(latest.get("downstream_snapshot_quality_status", "")),
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


def infer_market_cache_export_policy_stage(latest: dict[str, Any], health_status: str) -> str:
    if not latest:
        return "NO_POLICY_PLAN_ARTIFACTS"
    if health_status == "FAIL" or str(latest.get("status", "")).upper() == "FAIL":
        return "POLICY_PLAN_FAILED"
    if str(latest.get("downstream_snapshot_quality_status", "")).upper() == "PASS":
        return "SNAPSHOT_READY_FROM_POLICY_PLAN"
    if str(latest.get("downstream_export_status", "")).upper() == "PASS":
        return "EXPORT_READY_FROM_POLICY_PLAN"
    if health_status == "WARN" or str(latest.get("status", "")).upper() == "WARN":
        return "POLICY_PLAN_WARNINGS_NEED_REVIEW"
    if str(latest.get("generated_reviewed_manifest_path", "")):
        return "REVIEWED_MANIFEST_READY"
    return "POLICY_PLAN_READY_FOR_REVIEW"


def infer_market_cache_export_policy_next_action(
    latest: dict[str, Any],
    health_status: str,
    workflow_stage: str,
) -> str:
    if not latest:
        return "Run market-cache-export-plan with a reviewed policy request manifest."
    if health_status == "FAIL" or workflow_stage == "POLICY_PLAN_FAILED":
        return "Review market-cache-export-plan-health errors before using the generated manifest."
    if workflow_stage == "SNAPSHOT_READY_FROM_POLICY_PLAN":
        return "Review policy warnings, then use the linked snapshot/export outputs for downstream research if appropriate."
    if workflow_stage == "EXPORT_READY_FROM_POLICY_PLAN":
        return "Run or inspect data-pipeline, data-quality, and snapshot-quality for the linked export."
    if workflow_stage == "POLICY_PLAN_WARNINGS_NEED_REVIEW":
        return "Review PROVISIONAL or policy warnings in the generated manifest before running market-cache-export."
    if workflow_stage == "REVIEWED_MANIFEST_READY":
        return "Review the generated manifest, then run market-cache-export explicitly."
    return "Review policy recommendations before generating or using a cache export manifest."


def resolve_market_cache_export_policy_status_paths(
    output_dir: str | Path,
    status_id: str,
) -> MarketCacheExportPolicyStatusArtifactPaths:
    artifact_dir = Path(output_dir) / status_id
    return MarketCacheExportPolicyStatusArtifactPaths(
        artifact_dir=artifact_dir,
        market_cache_export_policy_status_report=artifact_dir / "market_cache_export_policy_status_report.md",
        market_cache_export_policy_status_csv=artifact_dir / "market_cache_export_policy_status.csv",
        market_cache_export_policy_status_summary=artifact_dir / "market_cache_export_policy_status_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_market_cache_export_policy_status_artifacts(
    result: MarketCacheExportPolicyStatusResult,
) -> dict[str, Path]:
    paths = MarketCacheExportPolicyStatusArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.status_frame.to_csv(paths.market_cache_export_policy_status_csv, index=False)
    result.summary_frame.to_csv(paths.market_cache_export_policy_status_summary, index=False)
    metadata = {
        "status_id": result.status_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_plan_id": result.latest_plan_id,
        "next_manual_action": result.next_manual_action,
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.market_cache_export_policy_status_report.write_text(
        render_market_cache_export_policy_status_report(result),
        encoding="utf-8",
    )
    return paths.as_dict()


def render_market_cache_export_policy_status_report(
    result: MarketCacheExportPolicyStatusResult,
) -> str:
    lines = [
        "# Market Cache Export Policy Status",
        "",
        "No live trading or broker API was invoked. This status view summarizes local policy recommendation artifacts only.",
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


def _latest_plan(index_frame: pd.DataFrame) -> dict[str, Any]:
    if index_frame.empty:
        return {}
    frame = index_frame.copy(deep=True)
    frame["_created_sort"] = pd.to_datetime(frame.get("created_at", ""), errors="coerce")
    frame["_updated_sort"] = pd.to_datetime(frame.get("artifact_updated_at", ""), errors="coerce")
    frame = frame.sort_values(
        ["_created_sort", "_updated_sort", "plan_id"],
        ascending=[False, False, False],
        na_position="last",
    )
    return frame.drop(columns=["_created_sort", "_updated_sort"]).iloc[0].to_dict()


def _latest_notes(latest: dict[str, Any]) -> str:
    if not latest:
        return "No market-cache-export policy plan artifacts found."
    return (
        f"recommendation_count={latest.get('recommendation_count', '')}; "
        f"recommended_with_warnings_count={latest.get('recommended_with_warnings_count', '')}; "
        f"generated_manifest={latest.get('generated_reviewed_manifest_path', '')}; "
        f"downstream_export_id={latest.get('downstream_export_id', '')}; "
        f"downstream_snapshot_quality_status={latest.get('downstream_snapshot_quality_status', '')}"
    )


def _resolve_settings(
    config: Settings | MarketCacheExportPolicyStatusSettings | dict[str, Any] | str | Path | None,
) -> tuple[Settings, MarketCacheExportPolicyStatusSettings]:
    if isinstance(config, (str, Path)):
        project = load_settings(config)
        return project, project.market_cache_export_policy_status
    project = load_settings(Path("config/default.yaml"))
    if config is None:
        return project, project.market_cache_export_policy_status
    if isinstance(config, Settings):
        return config, config.market_cache_export_policy_status
    if isinstance(config, MarketCacheExportPolicyStatusSettings):
        return project, config
    if isinstance(config, dict):
        payload = dict(project.market_cache_export_policy_status.model_dump())
        payload.update(config.get("market_cache_export_policy_status", config))
        return project, MarketCacheExportPolicyStatusSettings(**payload)
    raise TypeError("config must be Settings, MarketCacheExportPolicyStatusSettings, dict, path, or None")


def generate_market_cache_export_policy_status_id(
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
