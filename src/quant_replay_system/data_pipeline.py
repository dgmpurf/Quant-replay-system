"""Local data source to ingestion and quality handoff pipeline."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from quant_replay_system.config import DataPipelineSettings, Settings, load_settings
from quant_replay_system.data_ingestion import (
    IngestionResult,
    ingest_benchmark_data_csv,
    ingest_corporate_actions_csv,
    ingest_market_data_csv,
    ingest_trading_calendar_csv,
    ingest_universe_snapshot_csv,
)
from quant_replay_system.data_quality import DataQualityResult, run_data_quality_checks
from quant_replay_system.data_sources import DataSourceRequest, DataSourceResult, run_data_source_fetch


DATA_PIPELINE_LIMITATIONS = [
    "Uses local CSV/mock data only in automated tests.",
    "Does not call market data APIs or require API tokens.",
    "Does not connect to brokers, place orders, or automate execution.",
    "Runs existing ingestion and data quality modules; it does not repair source data.",
    "Snapshot manifests are generated from processed files present in the same pipeline run.",
]

SUPPORTED_DATASET_TYPES = {"market", "universe", "benchmark", "corporate_actions", "trading_calendar"}


@dataclass(frozen=True)
class DataPipelineDatasetRequest:
    dataset_type: str
    source: str = "LOCAL_CSV"
    input_path: str | Path | None = None
    revision_id: str | None = None
    source_name: str | None = None
    allow_real_data: bool = False
    symbol: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DataPipelineArtifactPaths:
    artifact_dir: Path
    data_pipeline_report: Path
    dataset_results: Path
    processed_paths: Path
    data_quality_summary: Path
    snapshot_manifest: Path
    metadata: Path

    def as_dict(self, *, include_quality: bool = True, include_snapshot: bool = True) -> dict[str, Path]:
        paths = {
            "artifact_dir": self.artifact_dir,
            "data_pipeline_report": self.data_pipeline_report,
            "dataset_results": self.dataset_results,
            "processed_paths": self.processed_paths,
            "metadata": self.metadata,
        }
        if include_quality:
            paths["data_quality_summary"] = self.data_quality_summary
        if include_snapshot:
            paths["snapshot_manifest"] = self.snapshot_manifest
        return paths


@dataclass(frozen=True)
class DataPipelineDatasetResult:
    dataset_type: str
    source: str
    raw_data_path: Path | None
    processed_data_path: Path | None
    validation_report_path: Path | None
    data_quality_status: str | None
    data_quality_report_path: Path | None
    row_count: int
    status: str
    warnings: list[str]
    source_result: DataSourceResult | None = None
    ingestion_result: IngestionResult | None = None
    quality_result: DataQualityResult | None = None


@dataclass(frozen=True)
class DataPipelineResult:
    pipeline_id: str
    dataset_results: list[DataPipelineDatasetResult]
    processed_paths: dict[str, Path]
    quality_results: dict[str, DataQualityResult]
    snapshot_manifest_path: Path | None
    status: str
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]
    config_summary: dict[str, Any]


def run_data_source_ingestion_pipeline(
    datasets: Iterable[dict[str, Any] | DataPipelineDatasetRequest | DataSourceRequest],
    *,
    config: Settings | DataPipelineSettings | str | Path | dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    run_data_quality: bool | None = None,
    build_snapshot_manifest: bool | None = None,
) -> DataPipelineResult:
    """Run data source fetch, ingestion, optional quality checks, and optional snapshot manifest."""

    project_settings, pipeline_settings = _resolve_settings(config)
    if pipeline_settings.enable_live_trading or pipeline_settings.enable_broker_api:
        raise ValueError("Data pipeline cannot enable live trading or broker API access")
    if output_dir is not None:
        pipeline_settings = pipeline_settings.model_copy(update={"output_dir": Path(output_dir)})
    effective_run_quality = pipeline_settings.run_data_quality if run_data_quality is None else bool(run_data_quality)
    effective_build_snapshot = (
        pipeline_settings.build_snapshot_manifest
        if build_snapshot_manifest is None
        else bool(build_snapshot_manifest)
    )

    requests = _coerce_dataset_requests(datasets, pipeline_settings)
    pipeline_id = generate_data_pipeline_id(
        requests,
        pipeline_settings,
        run_data_quality=effective_run_quality,
        build_snapshot_manifest=effective_build_snapshot,
    )
    paths = resolve_data_pipeline_artifact_paths(pipeline_settings.output_dir, pipeline_id)

    dataset_results = [
        run_single_dataset_pipeline(
            request,
            config=project_settings,
            pipeline_settings=pipeline_settings,
            pipeline_id=pipeline_id,
            artifact_dir=paths.artifact_dir,
            run_data_quality=effective_run_quality,
        )
        for request in requests
    ]
    processed_paths = {
        result.dataset_type: result.processed_data_path
        for result in dataset_results
        if result.processed_data_path is not None
    }
    quality_results = {
        result.dataset_type: result.quality_result
        for result in dataset_results
        if result.quality_result is not None
    }
    snapshot_manifest_path = None
    if effective_build_snapshot and len(processed_paths) > 1:
        snapshot_manifest_path = build_pipeline_snapshot_manifest(
            pipeline_id,
            processed_paths,
            paths.snapshot_manifest,
            dataset_results=dataset_results,
            settings=pipeline_settings,
        )

    status = _pipeline_status(dataset_results)
    warnings = _collect_warnings(dataset_results)
    artifact_paths = paths.as_dict(
        include_quality=effective_run_quality,
        include_snapshot=snapshot_manifest_path is not None,
    )
    audit_metadata = {
        "pipeline_id": pipeline_id,
        "dataset_count": len(dataset_results),
        "status": status,
        "run_data_quality": effective_run_quality,
        "build_snapshot_manifest": effective_build_snapshot,
        "snapshot_manifest_path": snapshot_manifest_path,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "network_api_calls_used_in_tests": False,
        "data_pipeline_only": True,
        "config_version": pipeline_settings.config_version,
    }
    result = DataPipelineResult(
        pipeline_id=pipeline_id,
        dataset_results=dataset_results,
        processed_paths=processed_paths,
        quality_results=quality_results,
        snapshot_manifest_path=snapshot_manifest_path,
        status=status,
        artifact_paths=artifact_paths,
        warnings=warnings,
        known_limitations=DATA_PIPELINE_LIMITATIONS,
        audit_metadata=audit_metadata,
        config_summary=_config_summary(pipeline_settings),
    )
    if pipeline_settings.write_artifacts:
        write_data_pipeline_artifacts(result)
    return result


def run_single_dataset_pipeline(
    dataset: dict[str, Any] | DataPipelineDatasetRequest | DataSourceRequest,
    *,
    config: Settings | str | Path | None = None,
    pipeline_settings: DataPipelineSettings | None = None,
    pipeline_id: str | None = None,
    artifact_dir: str | Path | None = None,
    run_data_quality: bool | None = None,
) -> DataPipelineDatasetResult:
    """Run the pipeline for one dataset request."""

    project_settings = _load_project_settings(config)
    cfg = pipeline_settings or project_settings.data_pipeline
    request = _coerce_dataset_request(dataset, cfg)
    effective_pipeline_id = pipeline_id or generate_data_pipeline_id(
        [request],
        cfg,
        run_data_quality=cfg.run_data_quality if run_data_quality is None else bool(run_data_quality),
        build_snapshot_manifest=False,
    )
    effective_artifact_dir = Path(artifact_dir) if artifact_dir is not None else (
        cfg.output_dir / effective_pipeline_id
    )
    source_result = run_data_source_fetch(
        DataSourceRequest(
            source=request.source,
            dataset_type=request.dataset_type,
            input_path=request.input_path,
            output_dir=cfg.raw_output_dir,
            revision_id=request.revision_id,
            allow_real_data=bool(request.allow_real_data or cfg.allow_real_data),
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            params=request.params,
        ),
        settings=_settings_for_data_source(project_settings, cfg),
    )
    try:
        ingestion_result = _run_ingestion(
            request,
            source_result.artifact_paths["raw_data"],
            project_settings,
            cfg,
            effective_pipeline_id,
        )
    except Exception as exc:
        if cfg.fail_on_ingestion_error:
            raise
        return DataPipelineDatasetResult(
            dataset_type=request.dataset_type,
            source=request.source,
            raw_data_path=source_result.artifact_paths["raw_data"],
            processed_data_path=None,
            validation_report_path=None,
            data_quality_status=None,
            data_quality_report_path=None,
            row_count=source_result.row_count,
            status="FAIL",
            warnings=[*source_result.warnings, f"Ingestion failed for {request.dataset_type}: {exc}"],
            source_result=source_result,
            ingestion_result=None,
            quality_result=None,
        )

    quality_result = None
    warnings = [*source_result.warnings, *ingestion_result.warnings]
    data_quality_status = None
    data_quality_report_path = None
    effective_run_quality = cfg.run_data_quality if run_data_quality is None else bool(run_data_quality)
    if effective_run_quality:
        quality_result = run_data_quality_checks(
            ingestion_result.artifact_paths["cleaned_csv"],
            ingestion_result.dataset_type,
            output_dir=effective_artifact_dir / "data_quality",
            settings=project_settings,
        )
        data_quality_status = quality_result.status
        data_quality_report_path = quality_result.artifact_paths["data_quality_report"]
        if quality_result.status == "FAIL":
            message = f"Data quality failed for {request.dataset_type}: {data_quality_report_path}"
            if cfg.fail_on_data_quality_fail:
                warnings.append(message)
            else:
                warnings.append(f"Non-blocking {message}")
        elif quality_result.status == "WARN":
            warnings.append(f"Data quality warning for {request.dataset_type}: {data_quality_report_path}")

    status = _dataset_status(
        ingestion_result,
        quality_result,
        settings=cfg,
    )
    return DataPipelineDatasetResult(
        dataset_type=request.dataset_type,
        source=request.source,
        raw_data_path=source_result.artifact_paths["raw_data"],
        processed_data_path=ingestion_result.artifact_paths["cleaned_csv"],
        validation_report_path=ingestion_result.artifact_paths["validation_report"],
        data_quality_status=data_quality_status,
        data_quality_report_path=data_quality_report_path,
        row_count=ingestion_result.row_count,
        status=status,
        warnings=warnings,
        source_result=source_result,
        ingestion_result=ingestion_result,
        quality_result=quality_result,
    )


def run_multi_dataset_pipeline(
    datasets: Iterable[dict[str, Any] | DataPipelineDatasetRequest | DataSourceRequest],
    *,
    config: Settings | DataPipelineSettings | str | Path | dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    run_data_quality: bool | None = None,
    build_snapshot_manifest: bool | None = None,
) -> DataPipelineResult:
    """Run the pipeline for multiple dataset requests."""

    return run_data_source_ingestion_pipeline(
        datasets,
        config=config,
        output_dir=output_dir,
        run_data_quality=run_data_quality,
        build_snapshot_manifest=build_snapshot_manifest,
    )


def load_data_pipeline_manifest(path: str | Path) -> list[DataPipelineDatasetRequest]:
    """Load a local JSON data pipeline manifest."""

    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Data pipeline manifest not found: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if "datasets" not in payload or not isinstance(payload["datasets"], list):
        raise ValueError("Data pipeline manifest must contain a 'datasets' list")
    return [_coerce_dataset_request(item, DataPipelineSettings()) for item in payload["datasets"]]


def build_pipeline_snapshot_manifest(
    pipeline_id: str,
    processed_paths: dict[str, Path],
    manifest_path: str | Path,
    *,
    dataset_results: list[DataPipelineDatasetResult],
    settings: DataPipelineSettings,
) -> Path:
    """Write a snapshot manifest compatible with Snapshot Quality Gate."""

    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_counts = {
        dataset_type: _safe_row_count(file_path)
        for dataset_type, file_path in sorted(processed_paths.items())
    }
    payload = {
        "snapshot_id": f"pipeline_{pipeline_id}",
        "snapshot_name": f"data_pipeline_{pipeline_id}",
        "created_at": "1970-01-01T00:00:00+00:00",
        "processed_files": {key: str(value) for key, value in sorted(processed_paths.items())},
        "row_counts": row_counts,
        "source": "DATA_PIPELINE",
        "revision_id": settings.config_version,
        "dataset_status": {
            result.dataset_type: result.status
            for result in dataset_results
        },
        "warnings": _collect_warnings(dataset_results),
        "known_limitations": DATA_PIPELINE_LIMITATIONS,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "data_pipeline_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }
    path.write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_data_pipeline_artifacts(result: DataPipelineResult) -> dict[str, Path]:
    """Write data pipeline markdown, CSV, JSON, and metadata artifacts."""

    paths = DataPipelineArtifactPaths(
        artifact_dir=result.artifact_paths["artifact_dir"],
        data_pipeline_report=result.artifact_paths["data_pipeline_report"],
        dataset_results=result.artifact_paths["dataset_results"],
        processed_paths=result.artifact_paths["processed_paths"],
        data_quality_summary=result.artifact_paths.get(
            "data_quality_summary",
            result.artifact_paths["artifact_dir"] / "data_quality_summary.csv",
        ),
        snapshot_manifest=result.artifact_paths.get(
            "snapshot_manifest",
            result.artifact_paths["artifact_dir"] / "snapshot_manifest.json",
        ),
        metadata=result.artifact_paths["metadata"],
    )
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    dataset_frame = _dataset_results_frame(result.dataset_results)
    processed_frame = _processed_paths_frame(result.processed_paths)
    quality_frame = _data_quality_summary_frame(result.dataset_results)
    _export_dataframe(dataset_frame, paths.dataset_results)
    _export_dataframe(processed_frame, paths.processed_paths)
    if not quality_frame.empty:
        _export_dataframe(quality_frame, paths.data_quality_summary)
    metadata = build_data_pipeline_metadata(result)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.data_pipeline_report.write_text(render_data_pipeline_report(result, metadata), encoding="utf-8")
    return result.artifact_paths


def build_data_pipeline_metadata(result: DataPipelineResult) -> dict[str, Any]:
    """Build metadata.json content for a data pipeline run."""

    return {
        "pipeline_id": result.pipeline_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "dataset_count": len(result.dataset_results),
        "dataset_results": _dataset_results_frame(result.dataset_results).to_dict("records"),
        "processed_paths": {key: str(value) for key, value in result.processed_paths.items()},
        "snapshot_manifest_path": str(result.snapshot_manifest_path) if result.snapshot_manifest_path else "",
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "config_summary": result.config_summary,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_data_pipeline_report(result: DataPipelineResult, metadata: dict[str, Any] | None = None) -> str:
    """Render a markdown data pipeline report."""

    _ = metadata
    lines = [
        f"# Data Pipeline Report: {result.pipeline_id}",
        "",
        "No broker or live trading integration was invoked. This pipeline uses local/mock CSV data only.",
        "",
        "## Summary",
        "",
        _dict_table(
            {
                "pipeline_id": result.pipeline_id,
                "status": result.status,
                "dataset_count": len(result.dataset_results),
                "snapshot_manifest_path": result.snapshot_manifest_path or "",
            }
        ),
        "",
        "## Dataset Results",
        "",
        _markdown_table(
            _dataset_results_frame(result.dataset_results),
            [
                "dataset_type",
                "source",
                "status",
                "row_count",
                "raw_data_path",
                "processed_data_path",
                "data_quality_status",
                "data_quality_report_path",
            ],
        ),
        "",
        "## Processed Paths",
        "",
        _markdown_table(_processed_paths_frame(result.processed_paths), ["dataset_type", "processed_data_path"]),
        "",
        "## Data Quality Summary",
        "",
        _markdown_table(
            _data_quality_summary_frame(result.dataset_results),
            [
                "dataset_type",
                "status",
                "row_count",
                "issue_count",
                "warning_count",
                "error_count",
                "data_quality_report_path",
            ],
        ),
        "",
        "## Warnings",
        "",
        _warnings_section(result.warnings),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in result.known_limitations),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def generate_data_pipeline_id(
    requests: list[DataPipelineDatasetRequest],
    settings: DataPipelineSettings,
    *,
    run_data_quality: bool,
    build_snapshot_manifest: bool,
) -> str:
    """Generate a deterministic short id for a pipeline run."""

    payload = {
        "datasets": [
            {
                "dataset_type": request.dataset_type,
                "source": request.source,
                "input_path": str(request.input_path) if request.input_path is not None else "",
                "revision_id": request.revision_id or "",
                "source_name": request.source_name or "",
                "allow_real_data": bool(request.allow_real_data),
                "symbol": request.symbol or "",
                "start_date": request.start_date or "",
                "end_date": request.end_date or "",
                "params": request.params,
            }
            for request in requests
        ],
        "run_data_quality": bool(run_data_quality),
        "build_snapshot_manifest": bool(build_snapshot_manifest),
        "config_version": settings.config_version,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def resolve_data_pipeline_artifact_paths(output_dir: str | Path, pipeline_id: str) -> DataPipelineArtifactPaths:
    """Resolve stable artifact paths for a data pipeline run."""

    artifact_dir = Path(output_dir) / pipeline_id
    return DataPipelineArtifactPaths(
        artifact_dir=artifact_dir,
        data_pipeline_report=artifact_dir / "data_pipeline_report.md",
        dataset_results=artifact_dir / "dataset_results.csv",
        processed_paths=artifact_dir / "processed_paths.csv",
        data_quality_summary=artifact_dir / "data_quality_summary.csv",
        snapshot_manifest=artifact_dir / "snapshot_manifest.json",
        metadata=artifact_dir / "metadata.json",
    )


def _run_ingestion(
    request: DataPipelineDatasetRequest,
    raw_data_path: Path,
    project_settings: Settings,
    pipeline_settings: DataPipelineSettings,
    pipeline_id: str,
) -> IngestionResult:
    output_dir = pipeline_settings.processed_output_dir / request.dataset_type / pipeline_id
    ingestion_settings = project_settings.data_ingestion.model_copy(
        update={
            "output_dir": pipeline_settings.processed_output_dir,
            "snapshot_dir": pipeline_settings.snapshot_output_dir,
            "default_source": request.source_name or request.source,
            "default_revision_id": request.revision_id or project_settings.data_ingestion.default_revision_id,
        }
    )
    settings = project_settings.model_copy(update={"data_ingestion": ingestion_settings})
    ingestion_func = _ingestion_function(request.dataset_type)
    return ingestion_func(raw_data_path, output_dir=output_dir, settings=settings)


def _ingestion_function(dataset_type: str):
    mapping = {
        "market": ingest_market_data_csv,
        "universe": ingest_universe_snapshot_csv,
        "benchmark": ingest_benchmark_data_csv,
        "corporate_actions": ingest_corporate_actions_csv,
        "trading_calendar": ingest_trading_calendar_csv,
    }
    normalized = _normalize_dataset_type(dataset_type)
    return mapping[normalized]


def _settings_for_data_source(project_settings: Settings, pipeline_settings: DataPipelineSettings) -> Settings:
    real_data_updates = {}
    if pipeline_settings.allow_real_data:
        real_data_updates = {
            "allow_network_sources": True,
            "allow_real_data_fetch": True,
        }
    data_source_settings = project_settings.data_sources.model_copy(
        update={
            "raw_output_dir": pipeline_settings.raw_output_dir,
            **real_data_updates,
        }
    )
    return project_settings.model_copy(update={"data_sources": data_source_settings})


def _dataset_status(
    ingestion_result: IngestionResult,
    quality_result: DataQualityResult | None,
    *,
    settings: DataPipelineSettings,
) -> str:
    if quality_result is not None:
        if quality_result.status == "FAIL":
            return "FAIL" if settings.fail_on_data_quality_fail else "WARN"
        if quality_result.status == "WARN" and not settings.allow_data_quality_warn:
            return "FAIL"
        if quality_result.status == "WARN":
            return "WARN"
    if ingestion_result.validation.warning_count > 0:
        return "WARN"
    return "PASS"


def _pipeline_status(dataset_results: list[DataPipelineDatasetResult]) -> str:
    statuses = {result.status for result in dataset_results}
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"


def _coerce_dataset_requests(
    datasets: Iterable[dict[str, Any] | DataPipelineDatasetRequest | DataSourceRequest],
    settings: DataPipelineSettings,
) -> list[DataPipelineDatasetRequest]:
    requests = [_coerce_dataset_request(item, settings) for item in datasets]
    if not requests:
        raise ValueError("At least one dataset request is required")
    return requests


def _coerce_dataset_request(
    value: dict[str, Any] | DataPipelineDatasetRequest | DataSourceRequest,
    settings: DataPipelineSettings,
) -> DataPipelineDatasetRequest:
    if isinstance(value, DataPipelineDatasetRequest):
        return DataPipelineDatasetRequest(
            dataset_type=_normalize_dataset_type(value.dataset_type),
            source=str(value.source).strip().upper(),
            input_path=Path(value.input_path) if value.input_path is not None else None,
            revision_id=value.revision_id,
            source_name=value.source_name,
            allow_real_data=bool(value.allow_real_data or settings.allow_real_data),
            symbol=value.symbol,
            start_date=value.start_date,
            end_date=value.end_date,
            params=dict(value.params or {}),
        )
    if isinstance(value, DataSourceRequest):
        return DataPipelineDatasetRequest(
            dataset_type=_normalize_dataset_type(value.dataset_type),
            source=str(value.source).strip().upper(),
            input_path=Path(value.input_path) if value.input_path is not None else None,
            revision_id=value.revision_id,
            source_name=None,
            allow_real_data=bool(value.allow_real_data or settings.allow_real_data),
            symbol=value.symbol,
            start_date=value.start_date,
            end_date=value.end_date,
            params=dict(value.params or {}),
        )
    if isinstance(value, dict):
        if "dataset_type" not in value:
            raise ValueError("Dataset request is missing dataset_type")
        return DataPipelineDatasetRequest(
            dataset_type=_normalize_dataset_type(str(value["dataset_type"])),
            source=str(value.get("source") or "LOCAL_CSV").strip().upper(),
            input_path=Path(value["input_path"]) if value.get("input_path") is not None else None,
            revision_id=value.get("revision_id"),
            source_name=value.get("source_name"),
            allow_real_data=bool(value.get("allow_real_data", False) or settings.allow_real_data),
            symbol=value.get("symbol"),
            start_date=value.get("start_date"),
            end_date=value.get("end_date"),
            params=dict(value.get("params") or {}),
        )
    raise TypeError("Dataset requests must be dict, DataPipelineDatasetRequest, or DataSourceRequest")


def _normalize_dataset_type(dataset_type: str) -> str:
    normalized = str(dataset_type).strip().lower()
    if normalized not in SUPPORTED_DATASET_TYPES:
        raise ValueError(f"dataset_type must be one of: {', '.join(sorted(SUPPORTED_DATASET_TYPES))}")
    return normalized


def _load_project_settings(config: Settings | str | Path | None) -> Settings:
    if config is None:
        return load_settings(Path("config/default.yaml"))
    if isinstance(config, Settings):
        return config
    return load_settings(Path(config))


def _resolve_settings(
    config: Settings | DataPipelineSettings | str | Path | dict[str, Any] | None,
) -> tuple[Settings, DataPipelineSettings]:
    if config is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.data_pipeline
    if isinstance(config, Settings):
        return config, config.data_pipeline
    project = load_settings(Path("config/default.yaml"))
    if isinstance(config, DataPipelineSettings):
        return project, config
    if isinstance(config, (str, Path)):
        loaded = load_settings(config)
        return loaded, loaded.data_pipeline
    if isinstance(config, dict):
        payload = dict(project.data_pipeline.model_dump())
        for key, value in config.items():
            if key == "data_pipeline" and isinstance(value, dict):
                payload.update(value)
            elif key in payload:
                payload[key] = value
        return project, DataPipelineSettings(**payload)
    raise TypeError("config must be Settings, DataPipelineSettings, path, dict, or None")


def _collect_warnings(dataset_results: list[DataPipelineDatasetResult]) -> list[str]:
    warnings: list[str] = []
    for result in dataset_results:
        warnings.extend(result.warnings)
    return warnings


def _dataset_results_frame(dataset_results: list[DataPipelineDatasetResult]) -> pd.DataFrame:
    columns = [
        "dataset_type",
        "source",
        "raw_data_path",
        "processed_data_path",
        "validation_report_path",
        "data_quality_status",
        "data_quality_report_path",
        "row_count",
        "status",
        "warnings",
    ]
    rows = [
        {
            "dataset_type": result.dataset_type,
            "source": result.source,
            "raw_data_path": result.raw_data_path,
            "processed_data_path": result.processed_data_path,
            "validation_report_path": result.validation_report_path,
            "data_quality_status": result.data_quality_status or "",
            "data_quality_report_path": result.data_quality_report_path or "",
            "row_count": result.row_count,
            "status": result.status,
            "warnings": result.warnings,
        }
        for result in dataset_results
    ]
    return _order_columns(pd.DataFrame(rows), columns)


def _processed_paths_frame(processed_paths: dict[str, Path]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"dataset_type": dataset_type, "processed_data_path": path}
            for dataset_type, path in sorted(processed_paths.items())
        ],
        columns=["dataset_type", "processed_data_path"],
    )


def _data_quality_summary_frame(dataset_results: list[DataPipelineDatasetResult]) -> pd.DataFrame:
    rows = []
    for result in dataset_results:
        if result.quality_result is None:
            continue
        quality = result.quality_result
        rows.append(
            {
                "dataset_type": result.dataset_type,
                "status": quality.status,
                "row_count": quality.row_count,
                "issue_count": quality.issue_count,
                "warning_count": quality.warning_count,
                "error_count": quality.error_count,
                "data_quality_report_path": quality.artifact_paths["data_quality_report"],
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "dataset_type",
            "status",
            "row_count",
            "issue_count",
            "warning_count",
            "error_count",
            "data_quality_report_path",
        ],
    )


def _safe_row_count(path: Path) -> int:
    try:
        return int(len(pd.read_csv(path)))
    except Exception:
        return 0


def _config_summary(settings: DataPipelineSettings) -> dict[str, Any]:
    return {
        "output_dir": settings.output_dir,
        "raw_output_dir": settings.raw_output_dir,
        "processed_output_dir": settings.processed_output_dir,
        "snapshot_output_dir": settings.snapshot_output_dir,
        "run_data_quality": settings.run_data_quality,
        "build_snapshot_manifest": settings.build_snapshot_manifest,
        "fail_on_ingestion_error": settings.fail_on_ingestion_error,
        "fail_on_data_quality_fail": settings.fail_on_data_quality_fail,
        "allow_data_quality_warn": settings.allow_data_quality_warn,
        "allow_real_data": settings.allow_real_data,
        "config_version": settings.config_version,
    }


def _order_columns(frame: pd.DataFrame, preferred: list[str]) -> pd.DataFrame:
    output = frame.copy(deep=True)
    for column in preferred:
        if column not in output.columns:
            output[column] = ""
    remaining = [column for column in output.columns if column not in preferred]
    return output[[*preferred, *remaining]]


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        rows.append(f"| {key} | {_format_markdown_value(value)} |")
    return "\n".join(rows)


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 50) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "_No rows._"
    table = frame[available].head(max_rows).copy()
    rows = [
        "| " + " | ".join(available) + " |",
        "| " + " | ".join("---" for _ in available) + " |",
    ]
    for record in table.to_dict("records"):
        rows.append("| " + " | ".join(_format_markdown_value(record[column]) for column in available) + " |")
    return "\n".join(rows)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)


def _format_markdown_value(value: Any) -> str:
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        return f"{value:.6f}"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True).replace("|", "\\|")
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).replace("|", "\\|").replace("\n", " ")


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    export = _sanitize_dataframe_for_export(frame)
    path.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(path, index=False)


def _sanitize_dataframe_for_export(frame: pd.DataFrame) -> pd.DataFrame:
    export = frame.copy(deep=True)
    for column in export.columns:
        if pd.api.types.is_datetime64_any_dtype(export[column]):
            export[column] = export[column].dt.strftime("%Y-%m-%d %H:%M:%S")
        elif export[column].dtype == "object":
            export[column] = export[column].map(_cell_to_export_value)
    return export


def _cell_to_export_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True)
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return value


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
