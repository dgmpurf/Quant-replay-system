"""Local-only daily market update skeleton with cache preflight gating."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketDailyUpdateSettings, Settings, load_settings
from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns
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

MARKET_DAILY_UPDATE_MANIFEST_REQUIRED_COLUMNS = [
    "symbol",
    "source",
    "dataset_type",
    "start_date",
    "end_date",
    "enabled",
]

MARKET_DAILY_UPDATE_SYMBOL_RESULT_COLUMNS = [
    "manifest_row",
    "symbol",
    "source",
    "dataset_type",
    "start_date",
    "end_date",
    "enabled",
    "status",
    "preflight_status",
    "cache_write_occurred",
    "raw_data_path",
    "metadata_path",
    "report_path",
    "row_count",
    "issue_count",
    "warning_count",
    "error_count",
    "reference_source",
    "require_fields",
    "strict_provisional",
    "preferred_upstream",
    "message",
    "no_live_trading",
    "no_broker_api",
]


@dataclass(frozen=True)
class MarketDailyUpdateSymbolManifestRow:
    manifest_row: int
    symbol: str
    source: str
    dataset_type: str
    start_date: str
    end_date: str
    enabled: bool
    security_type: str = ""
    preferred_upstream: str = ""
    required_fields: list[str] = field(default_factory=list)
    reference_source: str = ""
    strict_provisional: bool = False
    notes: str = ""
    raw_input: str | Path | None = None
    metadata_path: str | Path | None = None
    raw_output_dir: str | Path | None = None
    revision_id: str | None = None

    def to_request(
        self,
        *,
        allow_real_data: bool,
        dry_run: bool,
        accept_cache_write: bool,
        cache_path: str | Path | None,
        output_dir: str | Path | None,
        fallback_required_fields: list[str],
    ) -> "MarketDailyUpdateRequest":
        return MarketDailyUpdateRequest(
            source=self.source,
            symbol=self.symbol,
            start_date=self.start_date,
            end_date=self.end_date,
            raw_input=self.raw_input,
            metadata_path=self.metadata_path,
            allow_real_data=allow_real_data,
            dry_run=dry_run,
            accept_cache_write=accept_cache_write,
            reference_source=self.reference_source or None,
            required_fields=self.required_fields or fallback_required_fields,
            cache_path=cache_path,
            output_dir=output_dir,
            raw_output_dir=self.raw_output_dir,
            revision_id=self.revision_id,
            security_type=self.security_type,
            preferred_upstream=self.preferred_upstream,
            strict_provisional=self.strict_provisional,
        )


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
    security_type: str = ""
    preferred_upstream: str = ""
    strict_provisional: bool | None = None


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
    market_daily_update_symbol_results: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_daily_update_report": self.market_daily_update_report,
            "market_daily_update_steps": self.market_daily_update_steps,
            "market_daily_update_symbol_results": self.market_daily_update_symbol_results,
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
    symbol_results_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]

    @property
    def cache_write_occurred(self) -> bool:
        return self.cache_ingest_result is not None


@dataclass(frozen=True)
class MarketDailyUpdateManifestResult:
    update_id: str
    status: str
    manifest_path: Path
    symbol_results_frame: pd.DataFrame
    steps_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]

    @property
    def cache_write_occurred(self) -> bool:
        if self.symbol_results_frame.empty:
            return False
        return bool(self.symbol_results_frame["cache_write_occurred"].map(_coerce_bool).any())


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
    security_type: str | None = None,
    preferred_upstream: str | None = None,
    strict_provisional: bool | None = None,
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
        security_type=security_type or "",
        preferred_upstream=preferred_upstream or "",
        strict_provisional=strict_provisional,
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


def load_market_daily_update_symbol_manifest(
    path: str | Path,
    *,
    settings: MarketDailyUpdateSettings | None = None,
) -> list[MarketDailyUpdateSymbolManifestRow]:
    """Load a reviewed daily market update symbol manifest."""

    daily_settings = settings or load_settings(Path("config/default.yaml")).market_daily_update
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Market daily update symbol manifest not found: {manifest_path}")
    frame = read_csv_preserve_symbol_columns(manifest_path, keep_default_na=False)
    missing = [column for column in MARKET_DAILY_UPDATE_MANIFEST_REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Market daily update symbol manifest missing columns: {', '.join(missing)}")

    rows: list[MarketDailyUpdateSymbolManifestRow] = []
    for index, row in frame.iterrows():
        enabled = _coerce_bool(row.get("enabled"))
        required_fields = _normalize_required_fields(_string_or_none(row.get("require_fields")), daily_settings)
        rows.append(
            MarketDailyUpdateSymbolManifestRow(
                manifest_row=int(index) + 2,
                symbol=normalize_symbol_value(row.get("symbol")),
                source=_normalize_source(row.get("source")),
                dataset_type=str(row.get("dataset_type") or "").strip().lower(),
                start_date=str(row.get("start_date") or "").strip(),
                end_date=str(row.get("end_date") or "").strip(),
                enabled=enabled,
                security_type=str(row.get("security_type") or "").strip().upper(),
                preferred_upstream=str(row.get("preferred_upstream") or "").strip().upper(),
                required_fields=required_fields,
                reference_source=_normalize_source(row.get("reference_source")),
                strict_provisional=_coerce_bool(row.get("strict_provisional")),
                notes=str(row.get("notes") or "").strip(),
                raw_input=_optional_manifest_path(row.get("raw_input") or row.get("raw_data_path")),
                metadata_path=_optional_manifest_path(row.get("metadata_path") or row.get("metadata")),
                raw_output_dir=_optional_manifest_path(row.get("raw_output_dir")),
                revision_id=_string_or_none(row.get("revision_id")),
            )
        )
    return rows


def run_market_daily_update_manifest(
    symbol_manifest: str | Path,
    *,
    allow_real_data: bool = False,
    dry_run: bool | None = None,
    accept_cache_write: bool = False,
    fail_fast: bool | None = None,
    cache_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    raw_output_dir: str | Path | None = None,
    config: Settings | MarketDailyUpdateSettings | dict[str, Any] | None = None,
) -> MarketDailyUpdateManifestResult:
    """Run a reviewed symbol manifest through local daily update rows."""

    project_settings, update_settings = _resolve_settings(config)
    if update_settings.enable_live_trading or update_settings.enable_broker_api:
        raise ValueError("Market daily update cannot enable live trading or broker API access")
    manifest_path = Path(symbol_manifest)
    rows = load_market_daily_update_symbol_manifest(manifest_path, settings=update_settings)
    should_stop_on_fail = update_settings.fail_fast if fail_fast is None else bool(fail_fast)
    effective_dry_run = update_settings.default_dry_run if dry_run is None else bool(dry_run)
    update_id = generate_market_daily_update_manifest_id(
        manifest_path=manifest_path,
        allow_real_data=allow_real_data,
        accept_cache_write=accept_cache_write,
        fail_fast=should_stop_on_fail,
        rows=rows,
        settings=update_settings,
    )
    paths = resolve_market_daily_update_artifact_paths(
        Path(output_dir) if output_dir is not None else update_settings.output_dir,
        update_id,
    )
    symbol_result_rows: list[dict[str, Any]] = []
    step_rows: list[dict[str, Any]] = []

    for row in rows:
        if not row.enabled:
            symbol_result_rows.append(_disabled_symbol_result(row))
            continue
        if row.dataset_type != "market":
            symbol_result_rows.append(
                _manifest_symbol_result(
                    row,
                    status="FAIL",
                    message=f"Unsupported dataset_type for market daily update: {row.dataset_type}",
                )
            )
            if should_stop_on_fail:
                break
            continue
        if not row.raw_input and _is_real_source(row.source) and not allow_real_data:
            symbol_result_rows.append(
                _manifest_symbol_result(
                    row,
                    status="BLOCKED_NEEDS_ALLOW_REAL_DATA",
                    message=f"{row.source} requires --allow-real-data when raw input is not provided.",
                )
            )
            if should_stop_on_fail:
                break
            continue

        row_output_dir = paths.artifact_dir / f"symbol_{len(symbol_result_rows) + 1}_{row.symbol}"
        request = row.to_request(
            allow_real_data=allow_real_data,
            dry_run=effective_dry_run,
            accept_cache_write=accept_cache_write,
            cache_path=cache_path,
            output_dir=row_output_dir,
            fallback_required_fields=list(update_settings.default_required_fields),
        )
        if raw_output_dir is not None and request.raw_output_dir is None:
            request = MarketDailyUpdateRequest(
                **{**request.__dict__, "raw_output_dir": Path(raw_output_dir) / row.symbol}
            )
        row_result = run_market_daily_update(request, config=project_settings)
        symbol_row = _symbol_result_from_single_result(row, row_result)
        symbol_result_rows.append(symbol_row)
        for step in row_result.steps_frame.to_dict("records"):
            step_rows.append(
                {
                    "manifest_row": row.manifest_row,
                    "symbol": row.symbol,
                    "source": row.source,
                    **step,
                }
            )
        if should_stop_on_fail and symbol_row["status"] in {
            "FAIL",
            "BLOCKED_NEEDS_ALLOW_REAL_DATA",
            "BLOCKED_PREFLIGHT_REJECT",
        }:
            break

    symbol_results = pd.DataFrame(symbol_result_rows, columns=MARKET_DAILY_UPDATE_SYMBOL_RESULT_COLUMNS)
    steps = pd.DataFrame(step_rows)
    status = _manifest_overall_status(symbol_results)
    result = MarketDailyUpdateManifestResult(
        update_id=update_id,
        status=status,
        manifest_path=manifest_path,
        symbol_results_frame=symbol_results,
        steps_frame=steps,
        artifact_paths=paths.as_dict(),
        warnings=_manifest_warnings(symbol_results),
        known_limitations=MARKET_DAILY_UPDATE_LIMITATIONS,
        audit_metadata={
            "update_id": update_id,
            "operation": "market_daily_update_manifest",
            "symbol_manifest": manifest_path,
            "allow_real_data": allow_real_data,
            "accept_cache_write": accept_cache_write,
            "dry_run": effective_dry_run,
            "fail_fast": should_stop_on_fail,
            "cache_write_occurred": bool(symbol_results["cache_write_occurred"].map(_coerce_bool).any())
            if not symbol_results.empty
            else False,
            "symbol_result_counts": _symbol_result_counts(symbol_results),
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "market_daily_update_only": True,
            "config_version": update_settings.config_version,
        },
    )
    if update_settings.write_artifacts:
        write_market_daily_update_manifest_artifacts(result)
    return result


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
            requested_upstream=request.preferred_upstream or None,
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
        fetch_settings = _settings_with_preferred_upstream(fetch_settings, request)
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
        strict_provisional=request.strict_provisional,
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
    result.symbol_results_frame.to_csv(paths.market_daily_update_symbol_results, index=False)
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
        "symbol_results": result.symbol_results_frame.to_dict("records"),
        "symbol_result_counts": _symbol_result_counts(result.symbol_results_frame),
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


def write_market_daily_update_manifest_artifacts(result: MarketDailyUpdateManifestResult) -> dict[str, Path]:
    paths = MarketDailyUpdateArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.steps_frame.to_csv(paths.market_daily_update_steps, index=False)
    result.symbol_results_frame.to_csv(paths.market_daily_update_symbol_results, index=False)
    paths.market_daily_update_report.write_text(render_market_daily_update_manifest_report(result), encoding="utf-8")
    metadata = {
        "update_id": result.update_id,
        "status": result.status,
        "symbol_manifest": str(result.manifest_path),
        "symbol_result_counts": _symbol_result_counts(result.symbol_results_frame),
        "cache_write_occurred": result.cache_write_occurred,
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
        "symbol_results": result.symbol_results_frame.to_dict("records"),
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
    if not result.symbol_results_frame.empty:
        lines.extend(
            [
                "",
                "## Symbol Results",
                "",
                result.symbol_results_frame.to_markdown(index=False),
            ]
        )
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in result.known_limitations)
    return "\n".join(lines) + "\n"


def render_market_daily_update_manifest_report(result: MarketDailyUpdateManifestResult) -> str:
    counts = _symbol_result_counts(result.symbol_results_frame)
    lines = [
        "# Local Daily Market Update Symbol Manifest",
        "",
        f"- update_id: {result.update_id}",
        f"- status: {result.status}",
        f"- symbol_manifest: {result.manifest_path}",
        f"- symbol_row_count: {len(result.symbol_results_frame)}",
        f"- cache_write_occurred: {result.cache_write_occurred}",
        f"- pass_count: {counts.get('PASS', 0)}",
        f"- warn_count: {counts.get('WARN', 0)}",
        f"- fail_count: {counts.get('FAIL', 0)}",
        f"- skipped_disabled_count: {counts.get('SKIPPED_DISABLED', 0)}",
        f"- blocked_needs_allow_real_data_count: {counts.get('BLOCKED_NEEDS_ALLOW_REAL_DATA', 0)}",
        f"- blocked_preflight_reject_count: {counts.get('BLOCKED_PREFLIGHT_REJECT', 0)}",
        "",
        "No live trading or broker API was invoked.",
        "",
        "## Symbol Results",
        "",
        result.symbol_results_frame.to_markdown(index=False)
        if not result.symbol_results_frame.empty
        else "No symbol rows.",
    ]
    if not result.steps_frame.empty:
        lines.extend(["", "## Steps", "", result.steps_frame.to_markdown(index=False)])
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
        market_daily_update_symbol_results=artifact_dir / "market_daily_update_symbol_results.csv",
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
        "security_type": request.security_type,
        "preferred_upstream": request.preferred_upstream,
        "strict_provisional": request.strict_provisional,
        "config_version": settings.config_version,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def generate_market_daily_update_manifest_id(
    *,
    manifest_path: Path,
    allow_real_data: bool,
    accept_cache_write: bool,
    fail_fast: bool,
    rows: list[MarketDailyUpdateSymbolManifestRow],
    settings: MarketDailyUpdateSettings,
) -> str:
    payload = {
        "manifest_path": str(manifest_path),
        "allow_real_data": allow_real_data,
        "accept_cache_write": accept_cache_write,
        "fail_fast": fail_fast,
        "rows": [
            {
                "manifest_row": row.manifest_row,
                "symbol": row.symbol,
                "source": row.source,
                "dataset_type": row.dataset_type,
                "start_date": row.start_date,
                "end_date": row.end_date,
                "enabled": row.enabled,
                "preferred_upstream": row.preferred_upstream,
                "required_fields": row.required_fields,
                "reference_source": row.reference_source,
                "strict_provisional": row.strict_provisional,
                "raw_input": str(row.raw_input) if row.raw_input is not None else "",
                "metadata_path": str(row.metadata_path) if row.metadata_path is not None else "",
            }
            for row in rows
        ],
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
    symbol_results_frame = _single_symbol_result_frame(
        request=request,
        status=status,
        raw_data_path=raw_data_path,
        metadata_path=metadata_path,
        preflight_result=preflight_result,
        cache_ingest_result=cache_ingest_result,
        paths=paths,
    )
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
        symbol_results_frame=symbol_results_frame,
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


def _single_symbol_result_frame(
    *,
    request: MarketDailyUpdateRequest,
    status: str,
    raw_data_path: Path | None,
    metadata_path: Path | None,
    preflight_result: MarketCachePreflightResult | None,
    cache_ingest_result: MarketDataCacheIngestResult | None,
    paths: MarketDailyUpdateArtifactPaths,
) -> pd.DataFrame:
    preflight_status = preflight_result.status if preflight_result is not None else ""
    row_status = _row_status_from_single_status(status, preflight_status)
    row = {
        "manifest_row": 0,
        "symbol": request.symbol,
        "source": request.source,
        "dataset_type": "market",
        "start_date": request.start_date,
        "end_date": request.end_date,
        "enabled": True,
        "status": row_status,
        "preflight_status": preflight_status,
        "cache_write_occurred": cache_ingest_result is not None,
        "raw_data_path": str(raw_data_path) if raw_data_path is not None else "",
        "metadata_path": str(metadata_path) if metadata_path is not None else "",
        "report_path": str(paths.market_daily_update_report),
        "row_count": preflight_result.row_count if preflight_result is not None else 0,
        "issue_count": preflight_result.issue_count if preflight_result is not None else 0,
        "warning_count": preflight_result.warning_count if preflight_result is not None else 0,
        "error_count": preflight_result.error_count if preflight_result is not None else 0,
        "reference_source": request.reference_source or "",
        "require_fields": ",".join(request.required_fields),
        "strict_provisional": bool(request.strict_provisional),
        "preferred_upstream": request.preferred_upstream,
        "message": _row_message_from_single_status(status, preflight_status),
        "no_live_trading": True,
        "no_broker_api": True,
    }
    return pd.DataFrame([row], columns=MARKET_DAILY_UPDATE_SYMBOL_RESULT_COLUMNS)


def _disabled_symbol_result(row: MarketDailyUpdateSymbolManifestRow) -> dict[str, Any]:
    return _manifest_symbol_result(row, status="SKIPPED_DISABLED", message="Manifest row is disabled.")


def _manifest_symbol_result(
    row: MarketDailyUpdateSymbolManifestRow,
    *,
    status: str,
    message: str,
    preflight_status: str = "",
    cache_write_occurred: bool = False,
    raw_data_path: str = "",
    metadata_path: str = "",
    report_path: str = "",
    row_count: int = 0,
    issue_count: int = 0,
    warning_count: int = 0,
    error_count: int = 0,
) -> dict[str, Any]:
    return {
        "manifest_row": row.manifest_row,
        "symbol": row.symbol,
        "source": row.source,
        "dataset_type": row.dataset_type,
        "start_date": row.start_date,
        "end_date": row.end_date,
        "enabled": row.enabled,
        "status": status,
        "preflight_status": preflight_status,
        "cache_write_occurred": cache_write_occurred,
        "raw_data_path": raw_data_path,
        "metadata_path": metadata_path,
        "report_path": report_path,
        "row_count": row_count,
        "issue_count": issue_count,
        "warning_count": warning_count,
        "error_count": error_count,
        "reference_source": row.reference_source,
        "require_fields": ",".join(row.required_fields),
        "strict_provisional": row.strict_provisional,
        "preferred_upstream": row.preferred_upstream,
        "message": message,
        "no_live_trading": True,
        "no_broker_api": True,
    }


def _symbol_result_from_single_result(
    row: MarketDailyUpdateSymbolManifestRow,
    result: MarketDailyUpdateResult,
) -> dict[str, Any]:
    preflight_status = result.preflight_result.status if result.preflight_result is not None else ""
    status = _row_status_from_single_status(result.status, preflight_status)
    return _manifest_symbol_result(
        row,
        status=status,
        message=_row_message_from_single_status(result.status, preflight_status),
        preflight_status=preflight_status,
        cache_write_occurred=result.cache_write_occurred,
        raw_data_path=str(result.raw_data_path) if result.raw_data_path is not None else "",
        metadata_path=str(result.metadata_path) if result.metadata_path is not None else "",
        report_path=str(result.artifact_paths["market_daily_update_report"]),
        row_count=result.preflight_result.row_count if result.preflight_result is not None else 0,
        issue_count=result.preflight_result.issue_count if result.preflight_result is not None else 0,
        warning_count=result.preflight_result.warning_count if result.preflight_result is not None else 0,
        error_count=result.preflight_result.error_count if result.preflight_result is not None else 0,
    )


def _row_status_from_single_status(status: str, preflight_status: str) -> str:
    if preflight_status == "REJECT":
        return "BLOCKED_PREFLIGHT_REJECT"
    if status == "PASS":
        return "PASS"
    if status == "WARN":
        return "WARN"
    return "FAIL"


def _row_message_from_single_status(status: str, preflight_status: str) -> str:
    if preflight_status == "REJECT":
        return "Preflight rejected candidate rows; cache ingest blocked."
    if status == "PASS":
        return "Symbol update row completed."
    if status == "WARN":
        return "Symbol update row completed with warnings."
    return "Symbol update row failed."


def _manifest_overall_status(symbol_results: pd.DataFrame) -> str:
    if symbol_results.empty:
        return "WARN"
    statuses = set(symbol_results["status"].astype(str))
    if statuses & {"FAIL", "BLOCKED_NEEDS_ALLOW_REAL_DATA", "BLOCKED_PREFLIGHT_REJECT"}:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"


def _manifest_warnings(symbol_results: pd.DataFrame) -> list[str]:
    if symbol_results.empty:
        return ["Symbol manifest produced no rows."]
    warnings: list[str] = []
    for row in symbol_results.to_dict("records"):
        if str(row.get("status", "")) in {"WARN", "FAIL", "BLOCKED_NEEDS_ALLOW_REAL_DATA", "BLOCKED_PREFLIGHT_REJECT"}:
            warnings.append(f"{row.get('symbol')} {row.get('status')}: {row.get('message')}")
    return warnings


def _symbol_result_counts(symbol_results: pd.DataFrame) -> dict[str, int]:
    if symbol_results.empty or "status" not in symbol_results.columns:
        return {}
    counts = symbol_results["status"].astype(str).value_counts().to_dict()
    return {str(key): int(value) for key, value in counts.items()}


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
        security_type=str(kwargs.get("security_type") or "").strip().upper(),
        preferred_upstream=str(kwargs.get("preferred_upstream") or "").strip().upper(),
        strict_provisional=kwargs.get("strict_provisional"),
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


def _settings_with_preferred_upstream(settings: Settings, request: MarketDailyUpdateRequest) -> Settings:
    upstream = str(request.preferred_upstream or "").strip().upper()
    if not upstream or _normalize_source(request.source) != "AKSHARE_OPTIONAL":
        return settings
    security_type = str(request.security_type or "").strip().upper() or _infer_security_type_from_symbol(request.symbol)
    updates: dict[str, Any] = {}
    if security_type == "ETF":
        updates["akshare_market_etf_fallback_order"] = [upstream]
    elif security_type == "INDEX":
        updates["akshare_market_index_fallback_order"] = [upstream]
    else:
        updates["akshare_market_stock_fallback_order"] = [upstream]
    return settings.model_copy(
        update={"data_sources": settings.data_sources.model_copy(update=updates)}
    )


def _infer_security_type_from_symbol(symbol: str) -> str:
    text = normalize_symbol_value(symbol)
    if text.startswith(("510", "511", "512", "513", "515", "516", "159")):
        return "ETF"
    return "STOCK"


def _is_real_source(source: str) -> bool:
    return _normalize_source(source) in REAL_DATA_SOURCES


def _normalize_source(source: str) -> str:
    return str(source or "").strip().upper()


def _coerce_bool(value: Any) -> bool:
    text = str(value or "").strip().lower()
    if text in {"true", "1", "yes", "y", "enabled"}:
        return True
    if text in {"false", "0", "no", "n", "disabled", ""}:
        return False
    raise ValueError(f"Invalid boolean value in market daily update manifest: {value}")


def _string_or_none(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _optional_manifest_path(value: Any) -> str | Path | None:
    text = str(value or "").strip()
    return text or None


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
