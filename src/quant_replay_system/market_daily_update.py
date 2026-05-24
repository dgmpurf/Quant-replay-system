"""Local-only daily market update skeleton with cache preflight gating."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketDailyUpdateSettings, Settings, load_settings
from quant_replay_system.data_source_health import run_data_source_health_check
from quant_replay_system.data_sources import DataSourceRequest, REAL_DATA_SOURCES, run_data_source_fetch
from quant_replay_system.market_cache_preflight import MarketCachePreflightResult, run_market_cache_preflight
from quant_replay_system.market_data_cache import (
    MarketDataCacheIngestResult,
    MarketDataCacheStatusResult,
    ingest_market_cache_csv,
    summarize_market_cache_status,
)


MARKET_DAILY_UPDATE_TIMESTAMP = "1970-01-01T00:00:00+00:00"

MARKET_DAILY_UPDATE_LIMITATIONS = [
    "The daily market update workflow is local-only and manually invoked.",
    "It is not a scheduler, live trading workflow, broker integration, or order automation path.",
    "Cache writes require explicit accept_cache_write / --accept-cache-write.",
    "Real network fetches require explicit allow_real_data / --allow-real-data.",
    "Updated cache rows must still pass data-pipeline, data-quality, and snapshot-quality before research use.",
]

MARKET_DAILY_UPDATE_STEP_COLUMNS = [
    "step_order",
    "step_name",
    "status",
    "message",
    "row_count",
    "artifact_path",
    "no_live_trading",
    "no_broker_api",
]


@dataclass(frozen=True)
class MarketDailyUpdateRequest:
    source: str
    symbol: str
    start_date: str
    end_date: str
    raw_input: str | Path | None = None
    metadata_path: str | Path | None = None
    allow_real_data: bool = False
    dry_run: bool = True
    accept_cache_write: bool = False
    reference_source: str | None = None
    required_fields: list[str] = field(default_factory=list)
    cache_path: str | Path | None = None
    output_dir: str | Path | None = None
    raw_output_dir: str | Path | None = None
    revision_id: str | None = None


@dataclass(frozen=True)
class MarketDailyUpdateStepResult:
    step_order: int
    step_name: str
    status: str
    message: str
    row_count: int = 0
    artifact_path: str = ""
    no_live_trading: bool = True
    no_broker_api: bool = True

    def as_row(self) -> dict[str, Any]:
        return {
            "step_order": self.step_order,
            "step_name": self.step_name,
            "status": self.status,
            "message": self.message,
            "row_count": self.row_count,
            "artifact_path": self.artifact_path,
            "no_live_trading": self.no_live_trading,
            "no_broker_api": self.no_broker_api,
        }


@dataclass(frozen=True)
class MarketDailyUpdateArtifactPaths:
    artifact_dir: Path
    market_daily_update_report: Path
    market_daily_update_steps: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_daily_update_report": self.market_daily_update_report,
            "market_daily_update_steps": self.market_daily_update_steps,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MarketDailyUpdateResult:
    update_id: str
    status: str
    request: MarketDailyUpdateRequest
    raw_data_path: Path | None
    metadata_path: Path | None
    preflight_result: MarketCachePreflightResult | None
    cache_ingest_result: MarketDataCacheIngestResult | None
    cache_status_result: MarketDataCacheStatusResult | None
    steps_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]

    @property
    def cache_write_occurred(self) -> bool:
        return self.cache_ingest_result is not None


def run_market_daily_update(
    request: MarketDailyUpdateRequest | None = None,
    *,
    source: str | None = None,
    symbol: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    raw_input: str | Path | None = None,
    metadata_path: str | Path | None = None,
    allow_real_data: bool = False,
    dry_run: bool | None = None,
    accept_cache_write: bool = False,
    reference_source: str | None = None,
    required_fields: list[str] | str | None = None,
    cache_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    raw_output_dir: str | Path | None = None,
    revision_id: str | None = None,
    config: Settings | MarketDailyUpdateSettings | dict[str, Any] | None = None,
) -> MarketDailyUpdateResult:
    """Run a local market update skeleton with preflight-gated cache write."""

    project_settings, update_settings = _resolve_settings(config)
    if update_settings.enable_live_trading or update_settings.enable_broker_api:
        raise ValueError("Market daily update cannot enable live trading or broker API access")
    update_request = _coerce_request(
        request,
        source=source,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        raw_input=raw_input,
        metadata_path=metadata_path,
        allow_real_data=allow_real_data,
        dry_run=update_settings.default_dry_run if dry_run is None else bool(dry_run),
        accept_cache_write=accept_cache_write,
        reference_source=reference_source,
        required_fields=_normalize_required_fields(required_fields, update_settings),
        cache_path=cache_path,
        output_dir=output_dir,
        raw_output_dir=raw_output_dir,
        revision_id=revision_id,
    )
    return execute_market_daily_update_plan(
        update_request,
        settings=project_settings,
        update_settings=update_settings,
    )


def build_market_daily_update_plan(request: MarketDailyUpdateRequest) -> list[str]:
    """Return the planned local update steps for audit/reporting."""

    steps: list[str] = []
    if _is_real_source(request.source) and request.allow_real_data:
        steps.append("data_source_health")
    if request.raw_input:
        steps.append("use_existing_raw_input")
    else:
        steps.append("data_source_fetch")
    steps.append("market_cache_preflight")
    steps.append("market_cache_ingest" if request.accept_cache_write else "cache_write_skipped")
    steps.append("market_cache_status")
    return steps


def execute_market_daily_update_plan(
    request: MarketDailyUpdateRequest,
    *,
    settings: Settings | None = None,
    update_settings: MarketDailyUpdateSettings | None = None,
) -> MarketDailyUpdateResult:
    """Execute the local update plan. Cache writes require explicit acceptance."""

    project_settings = settings or load_settings(Path("config/default.yaml"))
    daily_settings = update_settings or project_settings.market_daily_update
    update_id = generate_market_daily_update_id(request, daily_settings)
    paths = resolve_market_daily_update_artifact_paths(
        Path(request.output_dir) if request.output_dir is not None else daily_settings.output_dir,
        update_id,
    )
    steps: list[MarketDailyUpdateStepResult] = []
    raw_data_path = Path(request.raw_input) if request.raw_input is not None else None
    metadata_file = Path(request.metadata_path) if request.metadata_path is not None else None
    preflight_result: MarketCachePreflightResult | None = None
    cache_ingest_result: MarketDataCacheIngestResult | None = None
    cache_status_result: MarketDataCacheStatusResult | None = None

    def add_step(name: str, status: str, message: str, *, row_count: int = 0, artifact_path: str = "") -> None:
        steps.append(
            MarketDailyUpdateStepResult(
                step_order=len(steps) + 1,
                step_name=name,
                status=status,
                message=message,
                row_count=row_count,
                artifact_path=artifact_path,
            )
        )

    if not request.raw_input and _is_real_source(request.source) and not request.allow_real_data:
        add_step(
            "real_data_guardrail",
            "FAIL",
            f"{_normalize_source(request.source)} requires --allow-real-data when raw input is not provided.",
        )
        result = _build_result(
            update_id=update_id,
            status="FAIL",
            request=request,
            raw_data_path=raw_data_path,
            metadata_path=metadata_file,
            preflight_result=preflight_result,
            cache_ingest_result=cache_ingest_result,
            cache_status_result=cache_status_result,
            steps=steps,
            paths=paths,
            settings=daily_settings,
        )
        if daily_settings.write_artifacts:
            write_market_daily_update_artifacts(result)
        return result

    if _is_real_source(request.source) and request.allow_real_data and daily_settings.run_health_check:
        health = run_data_source_health_check(
            source=request.source,
            dataset_type="market",
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            allow_real_data=True,
            output_dir=paths.artifact_dir / "data_source_health",
            config=_real_data_settings(project_settings),
        )
        add_step(
            "data_source_health",
            health.status,
            "Data source health check completed.",
            row_count=int(health.summary_frame.iloc[0].get("row_count", 0)) if not health.summary_frame.empty else 0,
            artifact_path=str(health.artifact_paths.get("data_source_health_report", "")),
        )
        if health.status == "FAIL" and raw_data_path is None:
            result = _build_result(
                update_id=update_id,
                status="FAIL",
                request=request,
                raw_data_path=raw_data_path,
                metadata_path=metadata_file,
                preflight_result=preflight_result,
                cache_ingest_result=cache_ingest_result,
                cache_status_result=cache_status_result,
                steps=steps,
                paths=paths,
                settings=daily_settings,
            )
            if daily_settings.write_artifacts:
                write_market_daily_update_artifacts(result)
            return result

    if raw_data_path is not None:
        add_step("use_existing_raw_input", "PASS", "Using caller-supplied raw_data.csv.", artifact_path=str(raw_data_path))
    else:
        fetch_settings = _real_data_settings(project_settings) if request.allow_real_data else project_settings
        fetch_result = run_data_source_fetch(
            DataSourceRequest(
                source=request.source,
                dataset_type="market",
                output_dir=request.raw_output_dir,
                revision_id=request.revision_id,
                allow_real_data=request.allow_real_data,
                symbol=request.symbol,
                start_date=request.start_date,
                end_date=request.end_date,
            ),
            settings=fetch_settings,
        )
        raw_data_path = fetch_result.artifact_paths["raw_data"]
        metadata_file = fetch_result.artifact_paths["metadata"]
        add_step(
            "data_source_fetch",
            "PASS",
            "Data source fetch completed.",
            row_count=fetch_result.row_count,
            artifact_path=str(raw_data_path),
        )

    preflight_result = run_market_cache_preflight(
        raw_data_path,
        metadata_path=metadata_file,
        reference_source=request.reference_source,
        cache_path=request.cache_path,
        required_fields=request.required_fields,
        symbol=request.symbol,
        start_date=request.start_date,
        end_date=request.end_date,
        output_dir=paths.artifact_dir / "market_cache_preflight",
        config=project_settings,
    )
    add_step(
        "market_cache_preflight",
        preflight_result.status,
        "Market cache preflight completed.",
        row_count=preflight_result.row_count,
        artifact_path=str(preflight_result.artifact_paths["market_cache_preflight_report"]),
    )

    if preflight_result.status == "REJECT":
        add_step("market_cache_ingest", "SKIPPED", "Preflight rejected candidate rows; cache ingest blocked.")
    elif request.accept_cache_write:
        cache_ingest_result = ingest_market_cache_csv(
            raw_data_path,
            metadata_path=metadata_file,
            cache_path=request.cache_path,
            output_dir=paths.artifact_dir / "market_data_cache",
            config=project_settings,
        )
        add_step(
            "market_cache_ingest",
            cache_ingest_result.status,
            "Cache ingest completed because --accept-cache-write was set.",
            row_count=cache_ingest_result.row_count,
            artifact_path=str(cache_ingest_result.artifact_paths["market_cache_report"]),
        )
    else:
        add_step(
            "cache_write_skipped",
            "SKIPPED",
            "Cache write skipped; pass --accept-cache-write to ingest accepted rows.",
        )

    if daily_settings.run_cache_status:
        cache_status_result = summarize_market_cache_status(
            cache_path=request.cache_path,
            output_dir=paths.artifact_dir / "market_data_cache_status",
            config=project_settings,
        )
        add_step(
            "market_cache_status",
            cache_status_result.status,
            "Market cache status completed.",
            row_count=cache_status_result.row_count,
            artifact_path=str(cache_status_result.artifact_paths["market_cache_report"]),
        )

    result_status = _overall_status(steps)
    result = _build_result(
        update_id=update_id,
        status=result_status,
        request=request,
        raw_data_path=raw_data_path,
        metadata_path=metadata_file,
        preflight_result=preflight_result,
        cache_ingest_result=cache_ingest_result,
        cache_status_result=cache_status_result,
        steps=steps,
        paths=paths,
        settings=daily_settings,
    )
    if daily_settings.write_artifacts:
        write_market_daily_update_artifacts(result)
    return result


def write_market_daily_update_artifacts(result: MarketDailyUpdateResult) -> dict[str, Path]:
    paths = MarketDailyUpdateArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.steps_frame.to_csv(paths.market_daily_update_steps, index=False)
    paths.market_daily_update_report.write_text(render_market_daily_update_report(result), encoding="utf-8")
    metadata = {
        "update_id": result.update_id,
        "status": result.status,
        "source": result.request.source,
        "symbol": result.request.symbol,
        "start_date": result.request.start_date,
        "end_date": result.request.end_date,
        "raw_data_path": str(result.raw_data_path) if result.raw_data_path is not None else "",
        "metadata_path": str(result.metadata_path) if result.metadata_path is not None else "",
        "preflight_status": result.preflight_result.status if result.preflight_result is not None else "",
        "cache_write_occurred": result.cache_write_occurred,
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
        "steps": result.steps_frame.to_dict("records"),
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "created_at": MARKET_DAILY_UPDATE_TIMESTAMP,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    return paths.as_dict()


def render_market_daily_update_report(result: MarketDailyUpdateResult) -> str:
    lines = [
        "# Local Daily Market Update",
        "",
        f"- update_id: {result.update_id}",
        f"- status: {result.status}",
        f"- source: {result.request.source}",
        f"- symbol: {result.request.symbol}",
        f"- date_range: {result.request.start_date} to {result.request.end_date}",
        f"- raw_data_path: {result.raw_data_path or ''}",
        f"- metadata_path: {result.metadata_path or ''}",
        f"- dry_run: {result.request.dry_run}",
        f"- accept_cache_write: {result.request.accept_cache_write}",
        f"- cache_write_occurred: {result.cache_write_occurred}",
        f"- preflight_status: {result.preflight_result.status if result.preflight_result is not None else ''}",
        "",
        "No live trading or broker API was invoked.",
        "",
        "## Steps",
        "",
        result.steps_frame.to_markdown(index=False) if not result.steps_frame.empty else "No steps.",
    ]
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in result.known_limitations)
    return "\n".join(lines) + "\n"


def resolve_market_daily_update_artifact_paths(output_dir: str | Path, update_id: str) -> MarketDailyUpdateArtifactPaths:
    artifact_dir = Path(output_dir) / update_id
    return MarketDailyUpdateArtifactPaths(
        artifact_dir=artifact_dir,
        market_daily_update_report=artifact_dir / "market_daily_update_report.md",
        market_daily_update_steps=artifact_dir / "market_daily_update_steps.csv",
        metadata=artifact_dir / "metadata.json",
    )


def generate_market_daily_update_id(
    request: MarketDailyUpdateRequest,
    settings: MarketDailyUpdateSettings,
) -> str:
    payload = {
        "source": request.source,
        "symbol": request.symbol,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "raw_input": str(request.raw_input) if request.raw_input is not None else "",
        "metadata_path": str(request.metadata_path) if request.metadata_path is not None else "",
        "allow_real_data": request.allow_real_data,
        "accept_cache_write": request.accept_cache_write,
        "reference_source": request.reference_source or "",
        "required_fields": request.required_fields,
        "config_version": settings.config_version,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _build_result(
    *,
    update_id: str,
    status: str,
    request: MarketDailyUpdateRequest,
    raw_data_path: Path | None,
    metadata_path: Path | None,
    preflight_result: MarketCachePreflightResult | None,
    cache_ingest_result: MarketDataCacheIngestResult | None,
    cache_status_result: MarketDataCacheStatusResult | None,
    steps: list[MarketDailyUpdateStepResult],
    paths: MarketDailyUpdateArtifactPaths,
    settings: MarketDailyUpdateSettings,
) -> MarketDailyUpdateResult:
    steps_frame = pd.DataFrame([step.as_row() for step in steps], columns=MARKET_DAILY_UPDATE_STEP_COLUMNS)
    warnings = [
        f"{row['step_name']}: {row['message']}"
        for row in steps_frame.to_dict("records")
        if str(row.get("status")) in {"WARN", "WARN_ACCEPT", "REJECT", "FAIL"}
    ]
    return MarketDailyUpdateResult(
        update_id=update_id,
        status=status,
        request=request,
        raw_data_path=raw_data_path,
        metadata_path=metadata_path,
        preflight_result=preflight_result,
        cache_ingest_result=cache_ingest_result,
        cache_status_result=cache_status_result,
        steps_frame=steps_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=MARKET_DAILY_UPDATE_LIMITATIONS,
        audit_metadata={
            "update_id": update_id,
            "operation": "market_daily_update",
            "cache_write_occurred": cache_ingest_result is not None,
            "accept_cache_write": request.accept_cache_write,
            "dry_run": request.dry_run,
            "allow_real_data": request.allow_real_data,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "market_daily_update_only": True,
            "config_version": settings.config_version,
        },
    )


def _overall_status(steps: list[MarketDailyUpdateStepResult]) -> str:
    statuses = [step.status for step in steps]
    if any(status in {"FAIL", "REJECT"} for status in statuses):
        return "FAIL"
    if any(status in {"WARN", "WARN_ACCEPT"} for status in statuses):
        return "WARN"
    return "PASS"


def _coerce_request(
    request: MarketDailyUpdateRequest | None,
    **kwargs: Any,
) -> MarketDailyUpdateRequest:
    if request is not None:
        return request
    if not kwargs.get("source") or not kwargs.get("symbol") or not kwargs.get("start_date") or not kwargs.get("end_date"):
        raise ValueError("market-daily-update requires source, symbol, start_date, and end_date")
    return MarketDailyUpdateRequest(
        source=_normalize_source(kwargs["source"]),
        symbol=str(kwargs["symbol"]).strip(),
        start_date=str(kwargs["start_date"]).strip(),
        end_date=str(kwargs["end_date"]).strip(),
        raw_input=kwargs.get("raw_input"),
        metadata_path=kwargs.get("metadata_path"),
        allow_real_data=bool(kwargs.get("allow_real_data")),
        dry_run=bool(kwargs.get("dry_run")),
        accept_cache_write=bool(kwargs.get("accept_cache_write")),
        reference_source=kwargs.get("reference_source"),
        required_fields=list(kwargs.get("required_fields") or []),
        cache_path=kwargs.get("cache_path"),
        output_dir=kwargs.get("output_dir"),
        raw_output_dir=kwargs.get("raw_output_dir"),
        revision_id=kwargs.get("revision_id"),
    )


def _normalize_required_fields(value: list[str] | str | None, settings: MarketDailyUpdateSettings) -> list[str]:
    if value is None:
        raw_values = settings.default_required_fields
    elif isinstance(value, str):
        raw_values = value.split(",")
    else:
        raw_values = value
    fields: list[str] = []
    for item in raw_values:
        field = str(item).strip().lower()
        if field and field not in fields:
            fields.append(field)
    return fields or list(settings.default_required_fields)


def _real_data_settings(settings: Settings) -> Settings:
    return settings.model_copy(
        update={
            "data_sources": settings.data_sources.model_copy(
                update={"allow_network_sources": True, "allow_real_data_fetch": True}
            )
        }
    )


def _is_real_source(source: str) -> bool:
    return _normalize_source(source) in REAL_DATA_SOURCES


def _normalize_source(source: str) -> str:
    return str(source or "").strip().upper()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _resolve_settings(
    config: Settings | MarketDailyUpdateSettings | dict[str, Any] | None,
) -> tuple[Settings, MarketDailyUpdateSettings]:
    if config is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.market_daily_update
    if isinstance(config, Settings):
        return config, config.market_daily_update
    project = load_settings(Path("config/default.yaml"))
    if isinstance(config, MarketDailyUpdateSettings):
        return project, config
    if isinstance(config, dict):
        update_payload = dict(project.market_daily_update.model_dump())
        project_updates: dict[str, Any] = {}
        for key, value in config.items():
            if key == "market_daily_update" and isinstance(value, dict):
                update_payload.update(value)
            elif key == "market_data_cache" and isinstance(value, dict):
                project_updates["market_data_cache"] = project.market_data_cache.model_copy(update=value)
            elif key == "market_cache_preflight" and isinstance(value, dict):
                project_updates["market_cache_preflight"] = project.market_cache_preflight.model_copy(update=value)
            elif key == "market_data_comparison" and isinstance(value, dict):
                project_updates["market_data_comparison"] = project.market_data_comparison.model_copy(update=value)
            elif key in update_payload:
                update_payload[key] = value
        if project_updates:
            project = project.model_copy(update=project_updates)
        return project, MarketDailyUpdateSettings(**update_payload)
    raise TypeError("config must be Settings, MarketDailyUpdateSettings, dict, or None")
