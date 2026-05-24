"""Local-only historical market backfill skeleton with preflight gating."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import HistoricalBackfillSettings, Settings, load_settings
from quant_replay_system.data import normalize_symbol_series, normalize_symbol_value, read_csv_preserve_symbol_columns
from quant_replay_system.data_source_health import DataSourceHealthResult, run_data_source_health_check
from quant_replay_system.data_sources import DataSourceRequest, REAL_DATA_SOURCES, run_data_source_fetch
from quant_replay_system.market_cache_preflight import MarketCachePreflightResult, run_market_cache_preflight
from quant_replay_system.market_data_cache import (
    MarketDataCacheIngestResult,
    ingest_market_cache_csv,
)


HISTORICAL_BACKFILL_TIMESTAMP = "1970-01-01T00:00:00+00:00"

HISTORICAL_BACKFILL_LIMITATIONS = [
    "The historical backfill workflow is local-only and manually invoked.",
    "It is a planning and dry-run skeleton, not a scheduler, live trading workflow, broker integration, or order automation path.",
    "Real network fetches require explicit allow_real_data / --allow-real-data.",
    "Cache writes require explicit accept_cache_write / --accept-cache-write.",
    "Every candidate raw file is checked by market-cache-preflight before any optional cache ingest.",
    "Backfilled cache rows must still pass data-pipeline, data-quality, and snapshot-quality before research use.",
]

HISTORICAL_BACKFILL_MANIFEST_REQUIRED_COLUMNS = [
    "symbol",
    "source",
    "dataset_type",
    "start_date",
    "end_date",
    "enabled",
]

HISTORICAL_BACKFILL_TASK_COLUMNS = [
    "task_id",
    "manifest_row",
    "symbol",
    "source",
    "dataset_type",
    "start_date",
    "end_date",
    "chunk_start_date",
    "chunk_end_date",
    "enabled",
    "security_type",
    "preferred_upstream",
    "require_fields",
    "reference_source",
    "strict_provisional",
    "chunk_days",
    "raw_input",
    "metadata_path",
    "notes",
    "no_live_trading",
    "no_broker_api",
]

HISTORICAL_BACKFILL_RESULT_COLUMNS = [
    "task_id",
    "manifest_row",
    "symbol",
    "source",
    "dataset_type",
    "chunk_start_date",
    "chunk_end_date",
    "status",
    "preflight_status",
    "health_status",
    "cache_write_occurred",
    "raw_data_path",
    "metadata_path",
    "health_report_path",
    "preflight_report_path",
    "cache_report_path",
    "row_count",
    "issue_count",
    "warning_count",
    "error_count",
    "message",
    "no_live_trading",
    "no_broker_api",
]

BACKFILL_FAILURE_STATUSES = {
    "FAIL",
    "BLOCKED_NEEDS_ALLOW_REAL_DATA",
    "BLOCKED_PREFLIGHT_REJECT",
    "BLOCKED_MISSING_RAW_INPUT",
}


@dataclass(frozen=True)
class HistoricalBackfillManifestRow:
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
    chunk_days: int | None = None
    raw_input: str | Path | None = None
    metadata_path: str | Path | None = None
    notes: str = ""


@dataclass(frozen=True)
class HistoricalBackfillSymbolTask:
    task_id: str
    manifest_row: int
    symbol: str
    source: str
    dataset_type: str
    start_date: str
    end_date: str
    chunk_start_date: str
    chunk_end_date: str
    enabled: bool
    security_type: str = ""
    preferred_upstream: str = ""
    required_fields: list[str] = field(default_factory=list)
    reference_source: str = ""
    strict_provisional: bool = False
    chunk_days: int | None = None
    raw_input: str | Path | None = None
    metadata_path: str | Path | None = None
    notes: str = ""

    def as_row(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "manifest_row": self.manifest_row,
            "symbol": self.symbol,
            "source": self.source,
            "dataset_type": self.dataset_type,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "chunk_start_date": self.chunk_start_date,
            "chunk_end_date": self.chunk_end_date,
            "enabled": self.enabled,
            "security_type": self.security_type,
            "preferred_upstream": self.preferred_upstream,
            "require_fields": ",".join(self.required_fields),
            "reference_source": self.reference_source,
            "strict_provisional": self.strict_provisional,
            "chunk_days": self.chunk_days if self.chunk_days is not None else "",
            "raw_input": str(self.raw_input) if self.raw_input is not None else "",
            "metadata_path": str(self.metadata_path) if self.metadata_path is not None else "",
            "notes": self.notes,
            "no_live_trading": True,
            "no_broker_api": True,
        }


@dataclass(frozen=True)
class HistoricalBackfillRequest:
    manifest_path: str | Path
    allow_real_data: bool = False
    dry_run: bool = True
    accept_cache_write: bool = False
    fail_fast: bool = False
    cache_path: str | Path | None = None
    output_dir: str | Path | None = None
    raw_output_dir: str | Path | None = None


@dataclass(frozen=True)
class HistoricalBackfillStepResult:
    task: HistoricalBackfillSymbolTask
    status: str
    preflight_status: str = ""
    health_status: str = ""
    cache_write_occurred: bool = False
    raw_data_path: str = ""
    metadata_path: str = ""
    health_report_path: str = ""
    preflight_report_path: str = ""
    cache_report_path: str = ""
    row_count: int = 0
    issue_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    message: str = ""
    no_live_trading: bool = True
    no_broker_api: bool = True

    def as_row(self) -> dict[str, Any]:
        return {
            "task_id": self.task.task_id,
            "manifest_row": self.task.manifest_row,
            "symbol": self.task.symbol,
            "source": self.task.source,
            "dataset_type": self.task.dataset_type,
            "chunk_start_date": self.task.chunk_start_date,
            "chunk_end_date": self.task.chunk_end_date,
            "status": self.status,
            "preflight_status": self.preflight_status,
            "health_status": self.health_status,
            "cache_write_occurred": self.cache_write_occurred,
            "raw_data_path": self.raw_data_path,
            "metadata_path": self.metadata_path,
            "health_report_path": self.health_report_path,
            "preflight_report_path": self.preflight_report_path,
            "cache_report_path": self.cache_report_path,
            "row_count": self.row_count,
            "issue_count": self.issue_count,
            "warning_count": self.warning_count,
            "error_count": self.error_count,
            "message": self.message,
            "no_live_trading": self.no_live_trading,
            "no_broker_api": self.no_broker_api,
        }


@dataclass(frozen=True)
class HistoricalBackfillArtifactPaths:
    artifact_dir: Path
    historical_backfill_report: Path
    historical_backfill_tasks: Path
    historical_backfill_results: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "historical_backfill_report": self.historical_backfill_report,
            "historical_backfill_tasks": self.historical_backfill_tasks,
            "historical_backfill_results": self.historical_backfill_results,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class HistoricalBackfillResult:
    backfill_id: str
    status: str
    manifest_path: Path
    tasks_frame: pd.DataFrame
    results_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]

    @property
    def cache_write_occurred(self) -> bool:
        if self.results_frame.empty:
            return False
        return bool(self.results_frame["cache_write_occurred"].map(_coerce_bool).any())

    @property
    def task_count(self) -> int:
        return len(self.tasks_frame)


def load_historical_backfill_manifest(
    path: str | Path,
    *,
    settings: HistoricalBackfillSettings | None = None,
) -> list[HistoricalBackfillManifestRow]:
    """Load a reviewed historical backfill manifest while preserving symbol strings."""

    backfill_settings = settings or load_settings(Path("config/default.yaml")).historical_backfill
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Historical backfill manifest not found: {manifest_path}")
    frame = read_csv_preserve_symbol_columns(manifest_path, keep_default_na=False)
    missing = [column for column in HISTORICAL_BACKFILL_MANIFEST_REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Historical backfill manifest missing columns: {', '.join(missing)}")

    rows: list[HistoricalBackfillManifestRow] = []
    for index, row in frame.iterrows():
        rows.append(
            HistoricalBackfillManifestRow(
                manifest_row=int(index) + 2,
                symbol=normalize_symbol_value(row.get("symbol")),
                source=_normalize_source(row.get("source")),
                dataset_type=str(row.get("dataset_type") or "").strip().lower(),
                start_date=str(row.get("start_date") or "").strip(),
                end_date=str(row.get("end_date") or "").strip(),
                enabled=_coerce_bool(row.get("enabled")),
                security_type=str(row.get("security_type") or "").strip().upper(),
                preferred_upstream=str(row.get("preferred_upstream") or "").strip().upper(),
                required_fields=_normalize_required_fields(_string_or_none(row.get("require_fields")), backfill_settings),
                reference_source=_normalize_source(row.get("reference_source")),
                strict_provisional=_coerce_bool(row.get("strict_provisional")),
                chunk_days=_optional_positive_int(row.get("chunk_days")),
                raw_input=_optional_manifest_path(row.get("raw_input") or row.get("raw_data_path")),
                metadata_path=_optional_manifest_path(row.get("metadata_path") or row.get("metadata")),
                notes=str(row.get("notes") or "").strip(),
            )
        )
    return rows


def build_historical_backfill_plan(
    rows: list[HistoricalBackfillManifestRow],
) -> HistoricalBackfillPlan:
    """Build per-symbol/per-chunk backfill tasks from reviewed manifest rows."""

    tasks: list[HistoricalBackfillSymbolTask] = []
    for row in rows:
        if not row.enabled:
            tasks.append(_task_from_row(row, row.start_date, row.end_date, sequence=1))
            continue
        ranges = _split_date_range(row.start_date, row.end_date, row.chunk_days)
        for sequence, (chunk_start, chunk_end) in enumerate(ranges, start=1):
            tasks.append(_task_from_row(row, chunk_start, chunk_end, sequence=sequence))
    return HistoricalBackfillPlan(tasks=tasks)


@dataclass(frozen=True)
class HistoricalBackfillPlan:
    tasks: list[HistoricalBackfillSymbolTask]

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([task.as_row() for task in self.tasks], columns=HISTORICAL_BACKFILL_TASK_COLUMNS)


def run_historical_backfill(
    manifest: str | Path | None = None,
    *,
    request: HistoricalBackfillRequest | None = None,
    allow_real_data: bool = False,
    dry_run: bool | None = None,
    accept_cache_write: bool = False,
    fail_fast: bool | None = None,
    cache_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    raw_output_dir: str | Path | None = None,
    config: Settings | HistoricalBackfillSettings | dict[str, Any] | None = None,
) -> HistoricalBackfillResult:
    """Run the local historical backfill skeleton over a reviewed manifest."""

    project_settings, backfill_settings = _resolve_settings(config)
    if backfill_settings.enable_live_trading or backfill_settings.enable_broker_api:
        raise ValueError("Historical backfill cannot enable live trading or broker API access")

    backfill_request = _coerce_request(
        request,
        manifest=manifest,
        allow_real_data=allow_real_data,
        dry_run=backfill_settings.default_dry_run if dry_run is None else bool(dry_run),
        accept_cache_write=accept_cache_write,
        fail_fast=backfill_settings.fail_fast if fail_fast is None else bool(fail_fast),
        cache_path=cache_path,
        output_dir=output_dir,
        raw_output_dir=raw_output_dir,
    )
    manifest_path = Path(backfill_request.manifest_path)
    rows = load_historical_backfill_manifest(manifest_path, settings=backfill_settings)
    plan = build_historical_backfill_plan(rows)
    backfill_id = generate_historical_backfill_id(backfill_request, plan, backfill_settings)
    paths = resolve_historical_backfill_artifact_paths(
        Path(backfill_request.output_dir) if backfill_request.output_dir is not None else backfill_settings.output_dir,
        backfill_id,
    )

    result_rows: list[dict[str, Any]] = []
    for task in plan.tasks:
        step = run_single_backfill_task(
            task,
            request=backfill_request,
            paths=paths,
            settings=project_settings,
            backfill_settings=backfill_settings,
        )
        result_rows.append(step.as_row())
        if backfill_request.fail_fast and step.status in BACKFILL_FAILURE_STATUSES:
            break

    tasks_frame = plan.to_frame()
    results_frame = pd.DataFrame(result_rows, columns=HISTORICAL_BACKFILL_RESULT_COLUMNS)
    status = _overall_status(results_frame)
    warnings = _result_warnings(results_frame)
    result = HistoricalBackfillResult(
        backfill_id=backfill_id,
        status=status,
        manifest_path=manifest_path,
        tasks_frame=tasks_frame,
        results_frame=results_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=HISTORICAL_BACKFILL_LIMITATIONS,
        audit_metadata={
            "backfill_id": backfill_id,
            "operation": "historical_backfill",
            "manifest_path": manifest_path,
            "allow_real_data": backfill_request.allow_real_data,
            "dry_run": backfill_request.dry_run,
            "accept_cache_write": backfill_request.accept_cache_write,
            "fail_fast": backfill_request.fail_fast,
            "cache_write_occurred": bool(results_frame["cache_write_occurred"].map(_coerce_bool).any())
            if not results_frame.empty
            else False,
            "task_result_counts": _result_counts(results_frame),
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "historical_backfill_only": True,
            "config_version": backfill_settings.config_version,
        },
    )
    if backfill_settings.write_artifacts:
        write_historical_backfill_artifacts(result)
    return result


def run_single_backfill_task(
    task: HistoricalBackfillSymbolTask,
    *,
    request: HistoricalBackfillRequest,
    paths: HistoricalBackfillArtifactPaths,
    settings: Settings,
    backfill_settings: HistoricalBackfillSettings,
) -> HistoricalBackfillStepResult:
    """Run one local backfill task through health/fetch-or-raw/preflight/cache gates."""

    if not task.enabled:
        return _step(task, "SKIPPED_DISABLED", message="Manifest row is disabled.")
    if task.dataset_type != "market":
        return _step(task, "FAIL", message=f"Unsupported dataset_type for historical backfill: {task.dataset_type}")

    raw_data_path: Path | None = None
    metadata_path = Path(task.metadata_path) if task.metadata_path is not None else None
    health_result: DataSourceHealthResult | None = None
    preflight_result: MarketCachePreflightResult | None = None
    cache_result: MarketDataCacheIngestResult | None = None

    if task.metadata_path and not metadata_path.exists():
        return _step(
            task,
            "FAIL",
            metadata_path=str(metadata_path),
            message=f"Manifest metadata_path does not exist: {metadata_path}",
        )

    if task.raw_input:
        source_raw = Path(task.raw_input)
        if not source_raw.exists():
            return _step(
                task,
                "BLOCKED_MISSING_RAW_INPUT",
                raw_data_path=str(source_raw),
                metadata_path=str(metadata_path) if metadata_path is not None else "",
                message=f"Manifest raw_input does not exist: {source_raw}",
            )
        raw_data_path = _materialize_task_raw_input(source_raw, task, paths.artifact_dir / "candidate_raw_inputs")
    elif _is_real_source(task.source) and not request.allow_real_data:
        return _step(
            task,
            "BLOCKED_NEEDS_ALLOW_REAL_DATA",
            message=f"{task.source} requires --allow-real-data when raw_input is not provided.",
        )
    else:
        if _is_real_source(task.source) and request.allow_real_data and backfill_settings.run_health_check:
            health_result = run_data_source_health_check(
                source=task.source,
                dataset_type="market",
                symbol=task.symbol,
                start_date=task.chunk_start_date,
                end_date=task.chunk_end_date,
                requested_upstream=task.preferred_upstream or None,
                allow_real_data=True,
                output_dir=paths.artifact_dir / "data_source_health" / task.task_id,
                config=_real_data_settings(settings),
            )
            if health_result.status == "FAIL":
                return _step(
                    task,
                    "FAIL",
                    health_status=health_result.status,
                    health_report_path=str(health_result.artifact_paths.get("data_source_health_report", "")),
                    message="Data source health check failed; fetch and preflight were skipped.",
                )
        fetch_settings = _real_data_settings(settings) if request.allow_real_data else settings
        fetch_settings = _settings_with_preferred_upstream(fetch_settings, task)
        fetch_result = run_data_source_fetch(
            DataSourceRequest(
                source=task.source,
                dataset_type="market",
                output_dir=Path(request.raw_output_dir) if request.raw_output_dir is not None else paths.artifact_dir / "raw_fetches",
                allow_real_data=request.allow_real_data,
                symbol=task.symbol,
                start_date=task.chunk_start_date,
                end_date=task.chunk_end_date,
            ),
            settings=fetch_settings,
        )
        raw_data_path = fetch_result.artifact_paths["raw_data"]
        metadata_path = fetch_result.artifact_paths["metadata"]

    preflight_result = run_market_cache_preflight(
        raw_data_path,
        metadata_path=metadata_path,
        reference_source=task.reference_source or None,
        cache_path=request.cache_path,
        required_fields=task.required_fields,
        symbol=task.symbol,
        start_date=task.chunk_start_date,
        end_date=task.chunk_end_date,
        strict_provisional=task.strict_provisional,
        output_dir=paths.artifact_dir / "market_cache_preflight" / task.task_id,
        config=settings,
    )
    if preflight_result.status == "REJECT":
        return _step_from_results(
            task,
            "BLOCKED_PREFLIGHT_REJECT",
            raw_data_path=raw_data_path,
            metadata_path=metadata_path,
            health_result=health_result,
            preflight_result=preflight_result,
            cache_result=None,
            message="Preflight rejected candidate rows; cache ingest blocked.",
        )

    if request.accept_cache_write:
        cache_result = ingest_market_cache_csv(
            raw_data_path,
            metadata_path=metadata_path,
            cache_path=request.cache_path,
            output_dir=paths.artifact_dir / "market_data_cache" / task.task_id,
            config=settings,
        )
        message = "Task completed and cache ingest ran because --accept-cache-write was set."
    else:
        message = "Task completed; cache write skipped because --accept-cache-write was not set."

    status = "WARN" if preflight_result.status == "WARN_ACCEPT" else "PASS"
    return _step_from_results(
        task,
        status,
        raw_data_path=raw_data_path,
        metadata_path=metadata_path,
        health_result=health_result,
        preflight_result=preflight_result,
        cache_result=cache_result,
        message=message,
    )


def write_historical_backfill_artifacts(result: HistoricalBackfillResult) -> dict[str, Path]:
    """Write historical backfill report, task CSV, result CSV, and metadata."""

    paths = HistoricalBackfillArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.tasks_frame.to_csv(paths.historical_backfill_tasks, index=False)
    result.results_frame.to_csv(paths.historical_backfill_results, index=False)
    paths.historical_backfill_report.write_text(render_historical_backfill_report(result), encoding="utf-8")
    metadata = {
        "backfill_id": result.backfill_id,
        "status": result.status,
        "manifest_path": str(result.manifest_path),
        "task_count": result.task_count,
        "cache_write_occurred": result.cache_write_occurred,
        "task_result_counts": _result_counts(result.results_frame),
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "created_at": HISTORICAL_BACKFILL_TIMESTAMP,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    return paths.as_dict()


def render_historical_backfill_report(result: HistoricalBackfillResult) -> str:
    """Render a concise historical backfill markdown report."""

    counts = _result_counts(result.results_frame)
    lines = [
        "# Historical Backfill Workflow",
        "",
        f"- backfill_id: {result.backfill_id}",
        f"- status: {result.status}",
        f"- manifest_path: {result.manifest_path}",
        f"- task_count: {result.task_count}",
        f"- pass_count: {counts.get('PASS', 0)}",
        f"- warn_count: {counts.get('WARN', 0)}",
        f"- fail_count: {_failure_count(counts)}",
        f"- skipped_disabled_count: {counts.get('SKIPPED_DISABLED', 0)}",
        f"- blocked_needs_allow_real_data_count: {counts.get('BLOCKED_NEEDS_ALLOW_REAL_DATA', 0)}",
        f"- blocked_missing_raw_input_count: {counts.get('BLOCKED_MISSING_RAW_INPUT', 0)}",
        f"- blocked_preflight_reject_count: {counts.get('BLOCKED_PREFLIGHT_REJECT', 0)}",
        f"- cache_write_occurred: {result.cache_write_occurred}",
        "",
        "No live trading or broker API was invoked.",
        "",
        "## Results",
        "",
        result.results_frame.to_markdown(index=False) if not result.results_frame.empty else "No task results.",
    ]
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in result.known_limitations)
    return "\n".join(lines) + "\n"


def resolve_historical_backfill_artifact_paths(
    output_dir: str | Path,
    backfill_id: str,
) -> HistoricalBackfillArtifactPaths:
    artifact_dir = Path(output_dir) / backfill_id
    return HistoricalBackfillArtifactPaths(
        artifact_dir=artifact_dir,
        historical_backfill_report=artifact_dir / "historical_backfill_report.md",
        historical_backfill_tasks=artifact_dir / "historical_backfill_tasks.csv",
        historical_backfill_results=artifact_dir / "historical_backfill_results.csv",
        metadata=artifact_dir / "metadata.json",
    )


def generate_historical_backfill_id(
    request: HistoricalBackfillRequest,
    plan: HistoricalBackfillPlan,
    settings: HistoricalBackfillSettings,
) -> str:
    payload = {
        "manifest_path": str(request.manifest_path),
        "allow_real_data": request.allow_real_data,
        "dry_run": request.dry_run,
        "accept_cache_write": request.accept_cache_write,
        "fail_fast": request.fail_fast,
        "cache_path": str(request.cache_path) if request.cache_path is not None else "",
        "tasks": [task.as_row() for task in plan.tasks],
        "config_version": settings.config_version,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _task_from_row(
    row: HistoricalBackfillManifestRow,
    chunk_start_date: str,
    chunk_end_date: str,
    *,
    sequence: int,
) -> HistoricalBackfillSymbolTask:
    task_id = f"row{row.manifest_row}_{row.symbol}_{chunk_start_date}_{chunk_end_date}_{sequence}"
    return HistoricalBackfillSymbolTask(
        task_id=task_id.replace("-", ""),
        manifest_row=row.manifest_row,
        symbol=row.symbol,
        source=row.source,
        dataset_type=row.dataset_type,
        start_date=row.start_date,
        end_date=row.end_date,
        chunk_start_date=chunk_start_date,
        chunk_end_date=chunk_end_date,
        enabled=row.enabled,
        security_type=row.security_type,
        preferred_upstream=row.preferred_upstream,
        required_fields=row.required_fields,
        reference_source=row.reference_source,
        strict_provisional=row.strict_provisional,
        chunk_days=row.chunk_days,
        raw_input=row.raw_input,
        metadata_path=row.metadata_path,
        notes=row.notes,
    )


def _split_date_range(start_date: str, end_date: str, chunk_days: int | None) -> list[tuple[str, str]]:
    start = pd.Timestamp(start_date).normalize()
    end = pd.Timestamp(end_date).normalize()
    if end < start:
        raise ValueError(f"Historical backfill end_date precedes start_date: {start_date} > {end_date}")
    if not chunk_days:
        return [(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))]
    ranges: list[tuple[str, str]] = []
    current = start
    while current <= end:
        chunk_end = min(current + pd.Timedelta(days=chunk_days - 1), end)
        ranges.append((current.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")))
        current = chunk_end + pd.Timedelta(days=1)
    return ranges


def _materialize_task_raw_input(
    source_raw: Path,
    task: HistoricalBackfillSymbolTask,
    output_dir: Path,
) -> Path:
    frame = read_csv_preserve_symbol_columns(source_raw, keep_default_na=False)
    output = frame.copy(deep=True)
    if "symbol" in output.columns:
        output["symbol"] = normalize_symbol_series(output["symbol"])
        output = output.loc[output["symbol"] == task.symbol].copy()
    if "trade_date" in output.columns:
        trade_dates = pd.to_datetime(output["trade_date"], errors="coerce").dt.normalize()
        start = pd.Timestamp(task.chunk_start_date).normalize()
        end = pd.Timestamp(task.chunk_end_date).normalize()
        output = output.loc[(trade_dates >= start) & (trade_dates <= end)].copy()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{task.task_id}_raw_data.csv"
    output.to_csv(output_path, index=False)
    return output_path


def _step_from_results(
    task: HistoricalBackfillSymbolTask,
    status: str,
    *,
    raw_data_path: Path,
    metadata_path: Path | None,
    health_result: DataSourceHealthResult | None,
    preflight_result: MarketCachePreflightResult,
    cache_result: MarketDataCacheIngestResult | None,
    message: str,
) -> HistoricalBackfillStepResult:
    return _step(
        task,
        status,
        preflight_status=preflight_result.status,
        health_status=health_result.status if health_result is not None else "",
        cache_write_occurred=cache_result is not None,
        raw_data_path=str(raw_data_path),
        metadata_path=str(metadata_path) if metadata_path is not None else "",
        health_report_path=str(health_result.artifact_paths.get("data_source_health_report", ""))
        if health_result is not None
        else "",
        preflight_report_path=str(preflight_result.artifact_paths["market_cache_preflight_report"]),
        cache_report_path=str(cache_result.artifact_paths["market_cache_report"]) if cache_result is not None else "",
        row_count=preflight_result.row_count,
        issue_count=preflight_result.issue_count,
        warning_count=preflight_result.warning_count,
        error_count=preflight_result.error_count,
        message=message,
    )


def _step(
    task: HistoricalBackfillSymbolTask,
    status: str,
    *,
    preflight_status: str = "",
    health_status: str = "",
    cache_write_occurred: bool = False,
    raw_data_path: str = "",
    metadata_path: str = "",
    health_report_path: str = "",
    preflight_report_path: str = "",
    cache_report_path: str = "",
    row_count: int = 0,
    issue_count: int = 0,
    warning_count: int = 0,
    error_count: int = 0,
    message: str = "",
) -> HistoricalBackfillStepResult:
    return HistoricalBackfillStepResult(
        task=task,
        status=status,
        preflight_status=preflight_status,
        health_status=health_status,
        cache_write_occurred=cache_write_occurred,
        raw_data_path=raw_data_path,
        metadata_path=metadata_path,
        health_report_path=health_report_path,
        preflight_report_path=preflight_report_path,
        cache_report_path=cache_report_path,
        row_count=row_count,
        issue_count=issue_count,
        warning_count=warning_count,
        error_count=error_count,
        message=message,
    )


def _overall_status(results_frame: pd.DataFrame) -> str:
    if results_frame.empty:
        return "WARN"
    statuses = set(results_frame["status"].astype(str))
    if statuses & BACKFILL_FAILURE_STATUSES:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"


def _result_warnings(results_frame: pd.DataFrame) -> list[str]:
    if results_frame.empty:
        return ["Historical backfill produced no task results."]
    warnings: list[str] = []
    for row in results_frame.to_dict("records"):
        if str(row.get("status", "")) in BACKFILL_FAILURE_STATUSES | {"WARN"}:
            warnings.append(f"{row.get('symbol')} {row.get('status')}: {row.get('message')}")
    return warnings


def _result_counts(results_frame: pd.DataFrame) -> dict[str, int]:
    if results_frame.empty or "status" not in results_frame.columns:
        return {}
    return {str(key): int(value) for key, value in results_frame["status"].astype(str).value_counts().items()}


def _failure_count(counts: dict[str, int]) -> int:
    return sum(int(counts.get(status, 0)) for status in BACKFILL_FAILURE_STATUSES)


def _coerce_request(
    request: HistoricalBackfillRequest | None,
    **kwargs: Any,
) -> HistoricalBackfillRequest:
    if request is not None:
        return request
    manifest = kwargs.get("manifest")
    if manifest is None:
        raise ValueError("historical-backfill requires --manifest")
    return HistoricalBackfillRequest(
        manifest_path=manifest,
        allow_real_data=bool(kwargs.get("allow_real_data")),
        dry_run=bool(kwargs.get("dry_run")),
        accept_cache_write=bool(kwargs.get("accept_cache_write")),
        fail_fast=bool(kwargs.get("fail_fast")),
        cache_path=kwargs.get("cache_path"),
        output_dir=kwargs.get("output_dir"),
        raw_output_dir=kwargs.get("raw_output_dir"),
    )


def _real_data_settings(settings: Settings) -> Settings:
    return settings.model_copy(
        update={
            "data_sources": settings.data_sources.model_copy(
                update={"allow_network_sources": True, "allow_real_data_fetch": True}
            )
        }
    )


def _settings_with_preferred_upstream(settings: Settings, task: HistoricalBackfillSymbolTask) -> Settings:
    upstream = str(task.preferred_upstream or "").strip().upper()
    if not upstream or _normalize_source(task.source) != "AKSHARE_OPTIONAL":
        return settings
    security_type = str(task.security_type or "").strip().upper() or _infer_security_type_from_symbol(task.symbol)
    updates: dict[str, Any] = {}
    if security_type == "ETF":
        updates["akshare_market_etf_fallback_order"] = [upstream]
    elif security_type == "INDEX":
        updates["akshare_market_index_fallback_order"] = [upstream]
    else:
        updates["akshare_market_stock_fallback_order"] = [upstream]
    return settings.model_copy(update={"data_sources": settings.data_sources.model_copy(update=updates)})


def _infer_security_type_from_symbol(symbol: str) -> str:
    text = normalize_symbol_value(symbol)
    if text.startswith(("510", "511", "512", "513", "515", "516", "159")):
        return "ETF"
    return "STOCK"


def _is_real_source(source: str) -> bool:
    return _normalize_source(source) in REAL_DATA_SOURCES


def _normalize_source(source: Any) -> str:
    return str(source or "").strip().upper()


def _normalize_required_fields(value: list[str] | str | None, settings: HistoricalBackfillSettings) -> list[str]:
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


def _coerce_bool(value: Any) -> bool:
    text = str(value or "").strip().lower()
    if text in {"true", "1", "yes", "y", "enabled"}:
        return True
    if text in {"false", "0", "no", "n", "disabled", ""}:
        return False
    raise ValueError(f"Invalid boolean value in historical backfill manifest: {value}")


def _optional_positive_int(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    parsed = int(float(text))
    if parsed <= 0:
        raise ValueError(f"chunk_days must be positive when supplied: {value}")
    return parsed


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
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.isoformat()
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _resolve_settings(
    config: Settings | HistoricalBackfillSettings | dict[str, Any] | None,
) -> tuple[Settings, HistoricalBackfillSettings]:
    if config is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.historical_backfill
    if isinstance(config, Settings):
        return config, config.historical_backfill
    project = load_settings(Path("config/default.yaml"))
    if isinstance(config, HistoricalBackfillSettings):
        return project, config
    if isinstance(config, dict):
        payload = dict(project.historical_backfill.model_dump())
        project_updates: dict[str, Any] = {}
        for key, value in config.items():
            if key == "historical_backfill" and isinstance(value, dict):
                payload.update(value)
            elif key == "market_data_cache" and isinstance(value, dict):
                project_updates["market_data_cache"] = project.market_data_cache.model_copy(update=value)
            elif key == "market_cache_preflight" and isinstance(value, dict):
                project_updates["market_cache_preflight"] = project.market_cache_preflight.model_copy(update=value)
            elif key == "market_data_comparison" and isinstance(value, dict):
                project_updates["market_data_comparison"] = project.market_data_comparison.model_copy(update=value)
            elif key in payload:
                payload[key] = value
        if project_updates:
            project = project.model_copy(update=project_updates)
        return project, HistoricalBackfillSettings(**payload)
    raise TypeError("config must be Settings, HistoricalBackfillSettings, dict, or None")
