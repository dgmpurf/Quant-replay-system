"""Local-only status view for market-update-handoff artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketUpdateHandoffStatusSettings, Settings, load_settings
from quant_replay_system.market_update_handoff_health import check_market_update_handoff_health
from quant_replay_system.market_update_handoff_index import build_market_update_handoff_index


MARKET_UPDATE_HANDOFF_STATUS_LIMITATIONS = [
    "Scans local market-update-handoff metadata only.",
    "Does not regenerate handoffs, mutate the market cache, fetch data, place orders, or call broker APIs.",
    "Stage inference is conservative when metadata or linked artifacts are missing.",
]

STATUS_COLUMNS = [
    "component",
    "status",
    "latest_handoff_id",
    "report_path",
    "metadata_path",
    "issue_count",
    "warning_count",
    "error_count",
    "next_action",
    "notes",
]


@dataclass(frozen=True)
class MarketUpdateHandoffStatusArtifactPaths:
    artifact_dir: Path
    market_update_handoff_status_report: Path
    market_update_handoff_status_csv: Path
    market_update_handoff_status_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_update_handoff_status_report": self.market_update_handoff_status_report,
            "market_update_handoff_status_csv": self.market_update_handoff_status_csv,
            "market_update_handoff_status_summary": self.market_update_handoff_status_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MarketUpdateHandoffStatusResult:
    status_id: str
    status: str
    workflow_stage: str
    latest_handoff_id: str
    next_manual_action: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_market_update_handoff_status(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    config: Settings | MarketUpdateHandoffStatusSettings | dict[str, Any] | str | Path | None = None,
) -> MarketUpdateHandoffStatusResult:
    project_settings, status_settings = _resolve_settings(config)
    if status_settings.enable_live_trading or status_settings.enable_broker_api:
        raise ValueError("Market update handoff status cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else status_settings.root_dir
    effective_output = Path(output_dir) if output_dir is not None else status_settings.output_dir
    index = build_market_update_handoff_index(
        root=effective_root,
        output_dir=effective_output / "_index",
        settings={"write_artifacts": False},
    )
    health = check_market_update_handoff_health(
        index_df=index.index_frame,
        output_dir=effective_output / "_health",
        settings={"write_artifacts": False},
    )
    latest = _latest_handoff(index.index_frame)
    workflow_stage = infer_market_update_handoff_stage(latest, health.status)
    next_action = infer_market_update_handoff_next_action(latest, health.status, workflow_stage)
    status_frame = build_market_update_handoff_status_frame(index.index_frame, health, latest)
    summary_frame = summarize_market_update_handoff_status(
        latest,
        health,
        workflow_stage=workflow_stage,
        next_manual_action=next_action,
    )
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "WARN"
    status_id = generate_market_update_handoff_status_id(
        status_frame,
        root=effective_root,
        config_version=status_settings.config_version,
    )
    paths = resolve_market_update_handoff_status_paths(effective_output, status_id)
    warnings = list(index.warnings) + list(health.warnings)
    audit_metadata = {
        "status_id": status_id,
        "root_dir": effective_root,
        "workflow_stage": workflow_stage,
        "latest_handoff_id": str(latest.get("handoff_id", "")),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "market_update_handoff_status_only": True,
        "config_version": status_settings.config_version,
    }
    result = MarketUpdateHandoffStatusResult(
        status_id=status_id,
        status=status,
        workflow_stage=workflow_stage,
        latest_handoff_id=str(latest.get("handoff_id", "")),
        next_manual_action=next_action,
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=MARKET_UPDATE_HANDOFF_STATUS_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if status_settings.write_artifacts:
        write_market_update_handoff_status_artifacts(result)
    _ = project_settings
    return result


def build_market_update_handoff_status_frame(
    index_frame: pd.DataFrame,
    health_result: Any,
    latest: dict[str, Any],
) -> pd.DataFrame:
    rows = [
        {
            "component": "MARKET_UPDATE_HANDOFF_INDEX",
            "status": "PASS" if not index_frame.empty else "WARN",
            "latest_handoff_id": str(latest.get("handoff_id", "")),
            "report_path": "",
            "metadata_path": "",
            "issue_count": 0,
            "warning_count": 0,
            "error_count": 0,
            "next_action": "Run market-update-handoff-health.",
            "notes": f"{len(index_frame)} handoff artifact(s) indexed.",
        },
        {
            "component": "MARKET_UPDATE_HANDOFF_HEALTH",
            "status": health_result.status,
            "latest_handoff_id": str(latest.get("handoff_id", "")),
            "report_path": health_result.artifact_paths.get("market_update_handoff_health_report", ""),
            "metadata_path": health_result.artifact_paths.get("metadata", ""),
            "issue_count": health_result.issue_count,
            "warning_count": health_result.warning_count,
            "error_count": health_result.error_count,
            "next_action": "Repair missing linked artifacts." if health_result.status == "FAIL" else "",
            "notes": f"{health_result.checked_artifact_count} handoff artifact(s) checked.",
        },
        {
            "component": "LATEST_MARKET_UPDATE_HANDOFF",
            "status": str(latest.get("status", "MISSING")) if latest else "MISSING",
            "latest_handoff_id": str(latest.get("handoff_id", "")),
            "report_path": str(latest.get("handoff_report_path", "")),
            "metadata_path": str(latest.get("metadata_path", "")),
            "issue_count": 0,
            "warning_count": int(_number(latest.get("warning_count", 0))) if latest else 0,
            "error_count": 0,
            "next_action": "",
            "notes": _latest_notes(latest),
        },
    ]
    return pd.DataFrame(rows, columns=STATUS_COLUMNS)


def summarize_market_update_handoff_status(
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
    elif health_result.status == "WARN" or str(latest.get("status", "")).upper() == "WARN":
        status = "WARN"
    else:
        status = str(latest.get("status") or "PASS").upper()
    return pd.DataFrame(
        [
            {
                "status": status,
                "workflow_stage": workflow_stage,
                "latest_handoff_id": str(latest.get("handoff_id", "")),
                "pipeline_id": str(latest.get("pipeline_id", "")),
                "snapshot_quality_status": str(latest.get("snapshot_quality_status", "")),
                "current_candidate_run_id": str(latest.get("current_candidate_run_id", "")),
                "candidate_count": int(_number(latest.get("candidate_count", 0))) if latest else 0,
                "health_status": health_result.status,
                "issue_count": health_result.issue_count,
                "warning_count": health_result.warning_count,
                "error_count": health_result.error_count,
                "next_manual_action": next_manual_action,
                "no_live_trading": True,
                "no_broker_api": True,
            }
        ]
    )


def infer_market_update_handoff_stage(latest: dict[str, Any], health_status: str) -> str:
    if not latest:
        return "NO_MARKET_UPDATE_HANDOFF_ARTIFACTS"
    if health_status == "FAIL":
        return "HANDOFF_ARTIFACTS_NEED_REPAIR"
    if str(latest.get("status", "")).upper() == "FAIL":
        return "HANDOFF_FAILED"
    if str(latest.get("snapshot_quality_status", "")).upper() == "FAIL":
        return "SNAPSHOT_QUALITY_FAILED"
    if _number(latest.get("candidate_count", 0)) > 0:
        return "CURRENT_CANDIDATES_READY_FOR_PAPER_SMOKE_TEST"
    if str(latest.get("current_candidate_run_id", "")):
        return "CURRENT_CANDIDATES_READY"
    if str(latest.get("pipeline_id", "")):
        return "SNAPSHOT_VALIDATION_READY"
    return "HANDOFF_READY"


def infer_market_update_handoff_next_action(
    latest: dict[str, Any],
    health_status: str,
    workflow_stage: str,
) -> str:
    if not latest:
        return "Run market-update-handoff for a reviewed offline update batch."
    if health_status == "FAIL":
        return "Review market-update-handoff-health errors and repair missing local artifacts."
    if workflow_stage == "CURRENT_CANDIDATES_READY_FOR_PAPER_SMOKE_TEST":
        return "Run current-to-paper on the latest current-candidates artifact, then continue paper review smoke testing."
    if workflow_stage == "SNAPSHOT_VALIDATION_READY":
        return "Inspect snapshot and current-candidates validation outputs before paper workflow smoke testing."
    if workflow_stage == "HANDOFF_FAILED":
        return "Review the latest market-update-handoff report and rerun after fixing excluded rows."
    return "Inspect the latest handoff report and decide whether to run paper workflow smoke tests."


def resolve_market_update_handoff_status_paths(
    output_dir: str | Path,
    status_id: str,
) -> MarketUpdateHandoffStatusArtifactPaths:
    artifact_dir = Path(output_dir) / status_id
    return MarketUpdateHandoffStatusArtifactPaths(
        artifact_dir=artifact_dir,
        market_update_handoff_status_report=artifact_dir / "market_update_handoff_status_report.md",
        market_update_handoff_status_csv=artifact_dir / "market_update_handoff_status.csv",
        market_update_handoff_status_summary=artifact_dir / "market_update_handoff_status_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_market_update_handoff_status_artifacts(result: MarketUpdateHandoffStatusResult) -> dict[str, Path]:
    paths = MarketUpdateHandoffStatusArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.status_frame.to_csv(paths.market_update_handoff_status_csv, index=False)
    result.summary_frame.to_csv(paths.market_update_handoff_status_summary, index=False)
    metadata = {
        "status_id": result.status_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_handoff_id": result.latest_handoff_id,
        "next_manual_action": result.next_manual_action,
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.market_update_handoff_status_report.write_text(
        render_market_update_handoff_status_report(result),
        encoding="utf-8",
    )
    return paths.as_dict()


def render_market_update_handoff_status_report(result: MarketUpdateHandoffStatusResult) -> str:
    lines = [
        "# Market Update Handoff Status",
        "",
        "No live trading or broker API was invoked. This status view summarizes local handoff artifacts only.",
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


def _latest_handoff(index_frame: pd.DataFrame) -> dict[str, Any]:
    if index_frame.empty:
        return {}
    frame = index_frame.copy(deep=True)
    frame["_created_sort"] = pd.to_datetime(frame.get("created_at", ""), errors="coerce")
    frame = frame.sort_values(["_created_sort", "handoff_id"], ascending=[False, False], na_position="last")
    return frame.drop(columns=["_created_sort"]).iloc[0].to_dict()


def _latest_notes(latest: dict[str, Any]) -> str:
    if not latest:
        return "No handoff artifacts found."
    return (
        f"pipeline_id={latest.get('pipeline_id', '')}; "
        f"snapshot_quality_status={latest.get('snapshot_quality_status', '')}; "
        f"current_candidate_run_id={latest.get('current_candidate_run_id', '')}; "
        f"candidate_count={latest.get('candidate_count', '')}"
    )


def _resolve_settings(
    config: Settings | MarketUpdateHandoffStatusSettings | dict[str, Any] | str | Path | None,
) -> tuple[Settings, MarketUpdateHandoffStatusSettings]:
    if isinstance(config, (str, Path)):
        project = load_settings(config)
        return project, project.market_update_handoff_status
    project = load_settings(Path("config/default.yaml"))
    if config is None:
        return project, project.market_update_handoff_status
    if isinstance(config, Settings):
        return config, config.market_update_handoff_status
    if isinstance(config, MarketUpdateHandoffStatusSettings):
        return project, config
    if isinstance(config, dict):
        payload = dict(project.market_update_handoff_status.model_dump())
        payload.update(config.get("market_update_handoff_status", config))
        return project, MarketUpdateHandoffStatusSettings(**payload)
    raise TypeError("config must be Settings, MarketUpdateHandoffStatusSettings, dict, path, or None")


def generate_market_update_handoff_status_id(
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
