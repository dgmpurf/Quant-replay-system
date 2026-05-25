"""Local-only status view for historical-backfill artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import HistoricalBackfillStatusSettings, Settings, load_settings
from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns
from quant_replay_system.historical_backfill_health import check_historical_backfill_health
from quant_replay_system.historical_backfill_index import build_historical_backfill_index


HISTORICAL_BACKFILL_STATUS_LIMITATIONS = [
    "Scans local historical-backfill metadata only.",
    "Does not regenerate backfills, mutate the market cache, fetch data, place orders, or call broker APIs.",
    "Stage inference is conservative when metadata or linked artifacts are missing.",
]

STATUS_COLUMNS = [
    "component",
    "status",
    "latest_backfill_id",
    "report_path",
    "metadata_path",
    "issue_count",
    "warning_count",
    "error_count",
    "accepted_task_count",
    "rejected_task_count",
    "preflight_rejected_count",
    "comparison_failed_count",
    "cache_write_partial",
    "rejected_symbols",
    "rejected_sources",
    "rejected_issue_categories",
    "next_action",
    "notes",
]


@dataclass(frozen=True)
class HistoricalBackfillStatusArtifactPaths:
    artifact_dir: Path
    historical_backfill_status_report: Path
    historical_backfill_status_csv: Path
    historical_backfill_status_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "historical_backfill_status_report": self.historical_backfill_status_report,
            "historical_backfill_status_csv": self.historical_backfill_status_csv,
            "historical_backfill_status_summary": self.historical_backfill_status_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class HistoricalBackfillStatusResult:
    status_id: str
    status: str
    workflow_stage: str
    latest_backfill_id: str
    next_manual_action: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


@dataclass(frozen=True)
class HistoricalBackfillActionability:
    accepted_task_count: int = 0
    rejected_task_count: int = 0
    preflight_rejected_count: int = 0
    comparison_failed_count: int = 0
    cache_write_partial: bool = False
    protective_rejection_only: bool = False
    rejected_symbols: tuple[str, ...] = ()
    rejected_sources: tuple[str, ...] = ()
    rejected_source_upstreams: tuple[str, ...] = ()
    rejected_issue_categories: tuple[str, ...] = ()

    def as_summary_dict(self) -> dict[str, Any]:
        return {
            "accepted_task_count": self.accepted_task_count,
            "rejected_task_count": self.rejected_task_count,
            "preflight_rejected_count": self.preflight_rejected_count,
            "comparison_failed_count": self.comparison_failed_count,
            "cache_write_partial": self.cache_write_partial,
            "rejected_symbols": ",".join(self.rejected_symbols),
            "rejected_sources": ",".join(self.rejected_sources),
            "rejected_source_upstreams": ",".join(self.rejected_source_upstreams),
            "rejected_issue_categories": ",".join(self.rejected_issue_categories),
            "protective_rejection_only": self.protective_rejection_only,
        }


def run_historical_backfill_status(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    config: Settings | HistoricalBackfillStatusSettings | dict[str, Any] | str | Path | None = None,
) -> HistoricalBackfillStatusResult:
    project_settings, status_settings = _resolve_settings(config)
    if status_settings.enable_live_trading or status_settings.enable_broker_api:
        raise ValueError("Historical backfill status cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else status_settings.root_dir
    effective_output = Path(output_dir) if output_dir is not None else status_settings.output_dir
    index = build_historical_backfill_index(
        root=effective_root,
        output_dir=effective_output / "_index",
        settings={"write_artifacts": False},
    )
    health = check_historical_backfill_health(
        index_df=index.index_frame,
        output_dir=effective_output / "_health",
        settings={"write_artifacts": False},
    )
    latest = _latest_backfill(index.index_frame)
    actionability = build_historical_backfill_actionability(latest)
    workflow_stage = infer_historical_backfill_stage(latest, health.status, actionability)
    next_action = infer_historical_backfill_next_action(latest, health.status, workflow_stage, actionability)
    status_frame = build_historical_backfill_status_frame(index.index_frame, health, latest, actionability)
    summary_frame = summarize_historical_backfill_status(
        latest,
        health,
        workflow_stage=workflow_stage,
        next_manual_action=next_action,
        actionability=actionability,
    )
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "WARN"
    status_id = generate_historical_backfill_status_id(
        status_frame,
        root=effective_root,
        config_version=status_settings.config_version,
    )
    paths = resolve_historical_backfill_status_paths(effective_output, status_id)
    warnings = list(index.warnings) + list(health.warnings)
    audit_metadata = {
        "status_id": status_id,
        "root_dir": effective_root,
        "workflow_stage": workflow_stage,
        "latest_backfill_id": str(latest.get("backfill_id", "")),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "historical_backfill_status_only": True,
        "config_version": status_settings.config_version,
    }
    result = HistoricalBackfillStatusResult(
        status_id=status_id,
        status=status,
        workflow_stage=workflow_stage,
        latest_backfill_id=str(latest.get("backfill_id", "")),
        next_manual_action=next_action,
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=HISTORICAL_BACKFILL_STATUS_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if status_settings.write_artifacts:
        write_historical_backfill_status_artifacts(result)
    _ = project_settings
    return result


def build_historical_backfill_status_frame(
    index_frame: pd.DataFrame,
    health_result: Any,
    latest: dict[str, Any],
    actionability: HistoricalBackfillActionability | None = None,
) -> pd.DataFrame:
    actionability = actionability or build_historical_backfill_actionability(latest)
    actionability_summary = actionability.as_summary_dict()
    rows = [
        {
            "component": "HISTORICAL_BACKFILL_INDEX",
            "status": "PASS" if not index_frame.empty else "WARN",
            "latest_backfill_id": str(latest.get("backfill_id", "")),
            "report_path": "",
            "metadata_path": "",
            "issue_count": 0,
            "warning_count": 0,
            "error_count": 0,
            "accepted_task_count": 0,
            "rejected_task_count": 0,
            "preflight_rejected_count": 0,
            "comparison_failed_count": 0,
            "cache_write_partial": False,
            "rejected_symbols": "",
            "rejected_sources": "",
            "rejected_issue_categories": "",
            "next_action": "Run historical-backfill-health.",
            "notes": f"{len(index_frame)} historical-backfill artifact(s) indexed.",
        },
        {
            "component": "HISTORICAL_BACKFILL_HEALTH",
            "status": health_result.status,
            "latest_backfill_id": str(latest.get("backfill_id", "")),
            "report_path": health_result.artifact_paths.get("historical_backfill_health_report", ""),
            "metadata_path": health_result.artifact_paths.get("metadata", ""),
            "issue_count": health_result.issue_count,
            "warning_count": health_result.warning_count,
            "error_count": health_result.error_count,
            "accepted_task_count": 0,
            "rejected_task_count": 0,
            "preflight_rejected_count": 0,
            "comparison_failed_count": 0,
            "cache_write_partial": False,
            "rejected_symbols": "",
            "rejected_sources": "",
            "rejected_issue_categories": "",
            "next_action": "Repair missing or inconsistent historical-backfill artifacts."
            if health_result.status == "FAIL"
            else "",
            "notes": f"{health_result.checked_artifact_count} historical-backfill artifact(s) checked.",
        },
        {
            "component": "LATEST_HISTORICAL_BACKFILL",
            "status": str(latest.get("status", "MISSING")) if latest else "MISSING",
            "latest_backfill_id": str(latest.get("backfill_id", "")),
            "report_path": str(latest.get("report_path", "")),
            "metadata_path": str(latest.get("metadata_path", "")),
            "issue_count": 0,
            "warning_count": int(_number(latest.get("warning_count", 0))) if latest else 0,
            "error_count": int(_number(latest.get("fail_count", 0))) if latest else 0,
            "accepted_task_count": actionability_summary["accepted_task_count"],
            "rejected_task_count": actionability_summary["rejected_task_count"],
            "preflight_rejected_count": actionability_summary["preflight_rejected_count"],
            "comparison_failed_count": actionability_summary["comparison_failed_count"],
            "cache_write_partial": actionability_summary["cache_write_partial"],
            "rejected_symbols": actionability_summary["rejected_symbols"],
            "rejected_sources": actionability_summary["rejected_sources"],
            "rejected_issue_categories": actionability_summary["rejected_issue_categories"],
            "next_action": "",
            "notes": _latest_notes(latest, actionability),
        },
    ]
    return pd.DataFrame(rows, columns=STATUS_COLUMNS)


def summarize_historical_backfill_status(
    latest: dict[str, Any],
    health_result: Any,
    *,
    workflow_stage: str,
    next_manual_action: str,
    actionability: HistoricalBackfillActionability | None = None,
) -> pd.DataFrame:
    actionability = actionability or build_historical_backfill_actionability(latest)
    partial_reviewable = _is_partial_protective_backfill(latest, health_result.status, actionability)
    if not latest:
        status = "WARN"
    elif health_result.status == "FAIL":
        status = "FAIL"
    elif partial_reviewable:
        status = "WARN"
    elif str(latest.get("status", "")).upper() == "FAIL":
        status = "FAIL"
    elif health_result.status == "WARN" or str(latest.get("status", "")).upper() == "WARN":
        status = "WARN"
    else:
        status = str(latest.get("status") or "PASS").upper()
    actionability_summary = actionability.as_summary_dict()
    return pd.DataFrame(
        [
            {
                "status": status,
                "workflow_stage": workflow_stage,
                "latest_backfill_id": str(latest.get("backfill_id", "")),
                "task_count": int(_number(latest.get("task_count", 0))) if latest else 0,
                "pass_count": int(_number(latest.get("pass_count", 0))) if latest else 0,
                "warn_count": int(_number(latest.get("warn_count", 0))) if latest else 0,
                "fail_count": int(_number(latest.get("fail_count", 0))) if latest else 0,
                "skipped_count": int(_number(latest.get("skipped_count", 0))) if latest else 0,
                "cache_write_occurred": bool(latest.get("cache_write_occurred", False)) if latest else False,
                **actionability_summary,
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


def infer_historical_backfill_stage(
    latest: dict[str, Any],
    health_status: str,
    actionability: HistoricalBackfillActionability | None = None,
) -> str:
    actionability = actionability or build_historical_backfill_actionability(latest)
    if not latest:
        return "NO_BACKFILL_ARTIFACTS"
    if health_status == "FAIL":
        return "BACKFILL_FAILED"
    if _is_partial_protective_backfill(latest, health_status, actionability):
        return "BACKFILL_PARTIAL_WITH_REJECTIONS"
    if str(latest.get("status", "")).upper() == "FAIL" or int(_number(latest.get("fail_count", 0))) > 0:
        return "BACKFILL_FAILED"
    if bool(latest.get("cache_write_occurred", False)):
        return "BACKFILL_COMPLETED"
    if str(latest.get("status", "")).upper() == "WARN" or int(_number(latest.get("warn_count", 0))) > 0:
        return "BACKFILL_WARNINGS_NEED_REVIEW"
    if str(latest.get("status", "")).upper() == "PASS":
        return "BACKFILL_CACHE_WRITE_READY"
    return "BACKFILL_DRY_RUN_READY"


def infer_historical_backfill_next_action(
    latest: dict[str, Any],
    health_status: str,
    workflow_stage: str,
    actionability: HistoricalBackfillActionability | None = None,
) -> str:
    actionability = actionability or build_historical_backfill_actionability(latest)
    if not latest:
        return "Run historical-backfill with a reviewed manifest in dry-run mode."
    if health_status == "FAIL" or workflow_stage == "BACKFILL_FAILED":
        return "Review historical-backfill-health errors and repair or rerun the failed backfill."
    if workflow_stage == "BACKFILL_PARTIAL_WITH_REJECTIONS":
        return (
            "Review rejected rows; accepted rows were cache-written. Use reviewed export/snapshot path if downstream "
            "validation passed. Do not rerun rejected rows until source comparison/preflight issues are reviewed."
        )
    if workflow_stage == "BACKFILL_WARNINGS_NEED_REVIEW":
        return "Review WARN tasks and only rerun with --accept-cache-write after manual approval."
    if workflow_stage == "BACKFILL_CACHE_WRITE_READY":
        return "Review index and health artifacts, then consider explicit --accept-cache-write if the backfill is approved."
    if workflow_stage == "BACKFILL_COMPLETED":
        return "Run market-cache-status, then data-pipeline/data-quality/snapshot-quality before research use."
    return "Inspect the latest historical backfill report before any cache write."


def resolve_historical_backfill_status_paths(
    output_dir: str | Path,
    status_id: str,
) -> HistoricalBackfillStatusArtifactPaths:
    artifact_dir = Path(output_dir) / status_id
    return HistoricalBackfillStatusArtifactPaths(
        artifact_dir=artifact_dir,
        historical_backfill_status_report=artifact_dir / "historical_backfill_status_report.md",
        historical_backfill_status_csv=artifact_dir / "historical_backfill_status.csv",
        historical_backfill_status_summary=artifact_dir / "historical_backfill_status_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_historical_backfill_status_artifacts(result: HistoricalBackfillStatusResult) -> dict[str, Path]:
    paths = HistoricalBackfillStatusArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.status_frame.to_csv(paths.historical_backfill_status_csv, index=False)
    result.summary_frame.to_csv(paths.historical_backfill_status_summary, index=False)
    metadata = {
        "status_id": result.status_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_backfill_id": result.latest_backfill_id,
        "next_manual_action": result.next_manual_action,
        **_summary_metadata(result.summary_frame),
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.historical_backfill_status_report.write_text(
        render_historical_backfill_status_report(result),
        encoding="utf-8",
    )
    return paths.as_dict()


def render_historical_backfill_status_report(result: HistoricalBackfillStatusResult) -> str:
    lines = [
        "# Historical Backfill Status",
        "",
        "No live trading or broker API was invoked. This status view summarizes local historical-backfill artifacts only.",
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


def _latest_backfill(index_frame: pd.DataFrame) -> dict[str, Any]:
    if index_frame.empty:
        return {}
    frame = index_frame.copy(deep=True)
    frame["_created_sort"] = pd.to_datetime(frame.get("created_at", ""), errors="coerce")
    frame["_updated_sort"] = pd.to_datetime(frame.get("artifact_updated_at", ""), errors="coerce")
    frame = frame.sort_values(
        ["_created_sort", "_updated_sort", "backfill_id"],
        ascending=[False, False, False],
        na_position="last",
    )
    return frame.drop(columns=["_created_sort", "_updated_sort"]).iloc[0].to_dict()


def _latest_notes(latest: dict[str, Any], actionability: HistoricalBackfillActionability | None = None) -> str:
    if not latest:
        return "No historical-backfill artifacts found."
    actionability = actionability or build_historical_backfill_actionability(latest)
    return (
        f"task_count={latest.get('task_count', '')}; "
        f"pass_count={latest.get('pass_count', '')}; "
        f"warn_count={latest.get('warn_count', '')}; "
        f"fail_count={latest.get('fail_count', '')}; "
        f"cache_write_occurred={latest.get('cache_write_occurred', '')}; "
        f"accepted_task_count={actionability.accepted_task_count}; "
        f"rejected_task_count={actionability.rejected_task_count}; "
        f"preflight_rejected_count={actionability.preflight_rejected_count}; "
        f"comparison_failed_count={actionability.comparison_failed_count}; "
        f"cache_write_partial={actionability.cache_write_partial}; "
        f"rejected_symbols={','.join(actionability.rejected_symbols)}; "
        f"rejected_sources={','.join(actionability.rejected_sources)}; "
        f"rejected_issue_categories={','.join(actionability.rejected_issue_categories)}"
    )


def build_historical_backfill_actionability(latest: dict[str, Any]) -> HistoricalBackfillActionability:
    if not latest:
        return HistoricalBackfillActionability()
    results_path = Path(str(latest.get("results_path", "")))
    if not results_path.exists():
        return HistoricalBackfillActionability()
    try:
        results = read_csv_preserve_symbol_columns(results_path)
    except Exception:
        return HistoricalBackfillActionability()
    if results.empty:
        return HistoricalBackfillActionability()

    status_series = results.get("status", pd.Series(dtype=str)).astype(str).str.upper()
    preflight_series = results.get("preflight_status", pd.Series(dtype=str)).astype(str).str.upper()
    cache_write_series = results.get("cache_write_occurred", pd.Series(dtype=str)).map(_coerce_bool)
    rejected_mask = (status_series == "BLOCKED_PREFLIGHT_REJECT") | (preflight_series == "REJECT")
    rejected_rows = results.loc[rejected_mask].copy()
    accepted_task_count = int(cache_write_series.sum())
    rejected_task_count = int(rejected_mask.sum())
    rejected_symbols = _sorted_unique(
        normalize_symbol_value(value) for value in rejected_rows.get("symbol", pd.Series(dtype=str)).tolist()
    )
    rejected_sources = _sorted_unique(str(value) for value in rejected_rows.get("source", pd.Series(dtype=str)).tolist())
    rejected_source_upstreams = _sorted_unique(
        _source_upstream_label(row) for row in rejected_rows.to_dict("records")
    )
    issue_categories = _rejected_issue_categories(rejected_rows)
    comparison_failed_count = _comparison_failed_row_count(rejected_rows)
    cache_write_occurred = _coerce_bool(latest.get("cache_write_occurred"))
    fail_count = int(_number(latest.get("fail_count", 0)))
    cache_write_partial = bool(cache_write_occurred and accepted_task_count > 0 and rejected_task_count > 0)
    protective_rejection_only = bool(
        cache_write_partial
        and rejected_task_count > 0
        and fail_count <= rejected_task_count
        and bool(issue_categories)
        and set(issue_categories).issubset({"COMPARISON_FAIL", "BLOCKED_PREFLIGHT_REJECT", "PREFLIGHT_REJECT"})
    )
    return HistoricalBackfillActionability(
        accepted_task_count=accepted_task_count,
        rejected_task_count=rejected_task_count,
        preflight_rejected_count=rejected_task_count,
        comparison_failed_count=comparison_failed_count,
        cache_write_partial=cache_write_partial,
        protective_rejection_only=protective_rejection_only,
        rejected_symbols=tuple(rejected_symbols),
        rejected_sources=tuple(rejected_sources),
        rejected_source_upstreams=tuple(rejected_source_upstreams),
        rejected_issue_categories=tuple(issue_categories),
    )


def _is_partial_protective_backfill(
    latest: dict[str, Any],
    health_status: str,
    actionability: HistoricalBackfillActionability,
) -> bool:
    return bool(
        latest
        and health_status != "FAIL"
        and actionability.cache_write_partial
        and actionability.protective_rejection_only
    )


def _rejected_issue_categories(rejected_rows: pd.DataFrame) -> list[str]:
    categories: set[str] = set()
    for row in rejected_rows.to_dict("records"):
        report_path = Path(str(row.get("preflight_report_path", "")))
        issue_path = report_path.with_name("market_cache_preflight_issues.csv") if str(report_path) else Path()
        if issue_path.exists():
            try:
                issues = read_csv_preserve_symbol_columns(issue_path)
            except Exception:
                issues = pd.DataFrame()
            if "category" in issues.columns:
                categories.update(str(value).strip().upper() for value in issues["category"].dropna().tolist() if str(value).strip())
        message = str(row.get("message", "")).upper()
        status = str(row.get("status", "")).upper()
        preflight = str(row.get("preflight_status", "")).upper()
        if "COMPARISON_FAIL" in message:
            categories.add("COMPARISON_FAIL")
        if status == "BLOCKED_PREFLIGHT_REJECT" or preflight == "REJECT":
            categories.add("BLOCKED_PREFLIGHT_REJECT")
    return sorted(categories)


def _comparison_failed_row_count(rejected_rows: pd.DataFrame) -> int:
    count = 0
    for row in rejected_rows.to_dict("records"):
        row_has_comparison_fail = "COMPARISON_FAIL" in str(row.get("message", "")).upper()
        report_path = Path(str(row.get("preflight_report_path", "")))
        issue_path = report_path.with_name("market_cache_preflight_issues.csv") if str(report_path) else Path()
        if issue_path.exists():
            try:
                issues = read_csv_preserve_symbol_columns(issue_path)
            except Exception:
                issues = pd.DataFrame()
            if "category" in issues.columns:
                row_has_comparison_fail = row_has_comparison_fail or any(
                    str(value).strip().upper() == "COMPARISON_FAIL"
                    for value in issues["category"].dropna().tolist()
                )
        if row_has_comparison_fail:
            count += 1
    return count


def _source_upstream_label(row: dict[str, Any]) -> str:
    symbol = normalize_symbol_value(row.get("symbol", ""))
    source = str(row.get("source", "")).strip()
    upstream = str(row.get("upstream_source", "") or row.get("preferred_upstream", "")).strip()
    source_part = source if not upstream else f"{source}/{upstream}"
    return f"{symbol}:{source_part}" if symbol and source_part else symbol or source_part


def _sorted_unique(values: Any) -> list[str]:
    return sorted({str(value).strip() for value in values if str(value).strip()})


def _coerce_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _summary_metadata(summary_frame: pd.DataFrame) -> dict[str, Any]:
    if summary_frame.empty:
        return {}
    summary = summary_frame.iloc[0].to_dict()
    keys = [
        "accepted_task_count",
        "rejected_task_count",
        "preflight_rejected_count",
        "comparison_failed_count",
        "cache_write_partial",
        "rejected_symbols",
        "rejected_sources",
        "rejected_source_upstreams",
        "rejected_issue_categories",
        "protective_rejection_only",
    ]
    return {key: summary.get(key) for key in keys}


def _resolve_settings(
    config: Settings | HistoricalBackfillStatusSettings | dict[str, Any] | str | Path | None,
) -> tuple[Settings, HistoricalBackfillStatusSettings]:
    if isinstance(config, (str, Path)):
        project = load_settings(config)
        return project, project.historical_backfill_status
    project = load_settings(Path("config/default.yaml"))
    if config is None:
        return project, project.historical_backfill_status
    if isinstance(config, Settings):
        return config, config.historical_backfill_status
    if isinstance(config, HistoricalBackfillStatusSettings):
        return project, config
    if isinstance(config, dict):
        payload = dict(project.historical_backfill_status.model_dump())
        payload.update(config.get("historical_backfill_status", config))
        return project, HistoricalBackfillStatusSettings(**payload)
    raise TypeError("config must be Settings, HistoricalBackfillStatusSettings, dict, path, or None")


def generate_historical_backfill_status_id(
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
