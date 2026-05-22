"""Local-safe market data source adapter framework."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import DataSourceSettings, Settings, load_settings


SUPPORTED_DATASET_TYPES = {"market", "universe", "benchmark", "corporate_actions", "trading_calendar"}
REAL_DATA_SOURCES = {"AKSHARE_OPTIONAL"}

DATA_SOURCE_LIMITATIONS = [
    "LOCAL_CSV and MOCK adapters use local files only.",
    "Real/network adapters are disabled by default and require explicit manual opt-in.",
    "Automated tests must not call real market data APIs or require API tokens.",
    "This module prepares raw local files; canonical validation remains in data_ingestion.",
    "It does not connect to brokers, place orders, or automate execution.",
]


@dataclass(frozen=True)
class DataSourceRequest:
    source: str
    dataset_type: str
    input_path: str | Path | None = None
    output_dir: str | Path | None = None
    revision_id: str | None = None
    allow_real_data: bool = False
    symbol: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DataSourceArtifactPaths:
    artifact_dir: Path
    raw_data: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "raw_data": self.raw_data,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class DataSourceResult:
    source: str
    dataset_type: str
    run_id: str
    row_count: int
    raw_data: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


class BaseDataSourceAdapter:
    """Base class for local-safe data source adapters."""

    source: str = ""
    is_real_data_source: bool = False

    def fetch(
        self,
        request: DataSourceRequest,
        settings: DataSourceSettings,
        project_settings: Settings,
    ) -> tuple[pd.DataFrame, dict[str, Any], list[str]]:
        raise NotImplementedError


class LocalCsvDataSourceAdapter(BaseDataSourceAdapter):
    """Load a caller-supplied local CSV and prepare it as a raw artifact."""

    source = "LOCAL_CSV"
    is_real_data_source = False

    def fetch(
        self,
        request: DataSourceRequest,
        settings: DataSourceSettings,
        project_settings: Settings,
    ) -> tuple[pd.DataFrame, dict[str, Any], list[str]]:
        _ = settings
        _ = project_settings
        if request.input_path is None:
            raise ValueError("LOCAL_CSV requires --input or DataSourceRequest.input_path")
        input_path = Path(request.input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Local CSV input not found: {input_path}")
        frame = pd.read_csv(input_path)
        return frame, {"input_path": input_path, "adapter": self.source}, []


class MockDataSourceAdapter(BaseDataSourceAdapter):
    """Load configured mock CSV data for demos and automated tests."""

    source = "MOCK"
    is_real_data_source = False

    def fetch(
        self,
        request: DataSourceRequest,
        settings: DataSourceSettings,
        project_settings: Settings,
    ) -> tuple[pd.DataFrame, dict[str, Any], list[str]]:
        _ = settings
        mock_path = _mock_path_for_dataset(request.dataset_type, project_settings)
        if not mock_path.exists():
            raise FileNotFoundError(f"Mock CSV not found for {request.dataset_type}: {mock_path}")
        frame = pd.read_csv(mock_path)
        warnings: list[str] = []
        if request.dataset_type == "benchmark":
            warnings.append("MOCK benchmark uses the configured mock market price file.")
        return frame, {"input_path": mock_path, "adapter": self.source}, warnings


class OptionalAkshareDataSourceAdapter(BaseDataSourceAdapter):
    """Manual-only placeholder for future AkShare-style data source fetching."""

    source = "AKSHARE_OPTIONAL"
    is_real_data_source = True

    def fetch(
        self,
        request: DataSourceRequest,
        settings: DataSourceSettings,
        project_settings: Settings,
    ) -> tuple[pd.DataFrame, dict[str, Any], list[str]]:
        _enforce_real_data_guardrails(self, request, settings)
        _ = project_settings
        try:
            import akshare  # type: ignore  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "AKSHARE_OPTIONAL requires akshare to be installed and must be run manually with "
                "--allow-real-data plus config data_sources.allow_real_data_fetch=true."
            ) from exc
        raise NotImplementedError(
            "AKSHARE_OPTIONAL is registered for future manual use but does not fetch data in v0.1."
        )


def list_data_source_adapters(*, include_real: bool = True) -> list[str]:
    """List registered adapter names."""

    names = sorted(_adapter_registry().keys())
    if include_real:
        return names
    return [name for name in names if name not in REAL_DATA_SOURCES]


def get_data_source_adapter(source: str) -> BaseDataSourceAdapter:
    """Return a registered data source adapter by name."""

    normalized = _normalize_source(source)
    registry = _adapter_registry()
    if normalized not in registry:
        raise ValueError(f"Unknown data source adapter: {source}. Available: {', '.join(sorted(registry))}")
    return registry[normalized]


def run_data_source_fetch(
    request: DataSourceRequest,
    *,
    settings: Settings | DataSourceSettings | dict[str, Any] | None = None,
) -> DataSourceResult:
    """Run one local-safe data source fetch and write raw artifacts when enabled."""

    project_settings, source_settings = _resolve_settings(settings)
    if source_settings.enable_live_trading or source_settings.enable_broker_api:
        raise ValueError("Data source adapters cannot enable live trading or broker API access")

    normalized_request = _normalize_request(request, source_settings)
    adapter = get_data_source_adapter(normalized_request.source)
    if adapter.is_real_data_source:
        _enforce_real_data_guardrails(adapter, normalized_request, source_settings)

    frame, adapter_metadata, adapter_warnings = adapter.fetch(
        normalized_request,
        source_settings,
        project_settings,
    )
    run_id = generate_data_source_run_id(normalized_request, source_settings, adapter_metadata)
    paths = resolve_data_source_artifact_paths(
        normalized_request.output_dir or source_settings.raw_output_dir,
        normalized_request.source,
        normalized_request.dataset_type,
        run_id,
    )
    audit_metadata = {
        "source": normalized_request.source,
        "dataset_type": normalized_request.dataset_type,
        "run_id": run_id,
        "row_count": len(frame),
        "revision_id": normalized_request.revision_id,
        "adapter_metadata": adapter_metadata,
        "request": _request_metadata(normalized_request),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "real_data_allowed": bool(normalized_request.allow_real_data),
        "network_api_calls_used_in_tests": False,
        "data_source_fetch_only": True,
        "config_version": source_settings.config_version,
    }
    result = DataSourceResult(
        source=normalized_request.source,
        dataset_type=normalized_request.dataset_type,
        run_id=run_id,
        row_count=len(frame),
        raw_data=frame.copy(deep=True),
        artifact_paths=paths.as_dict(),
        warnings=list(adapter_warnings),
        known_limitations=DATA_SOURCE_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if source_settings.write_artifacts:
        write_raw_data_source_artifacts(result)
    return result


def generate_data_source_run_id(
    request: DataSourceRequest,
    settings: DataSourceSettings,
    adapter_metadata: dict[str, Any] | None = None,
) -> str:
    """Generate a deterministic id for a raw data source request."""

    payload = {
        "source": request.source,
        "dataset_type": request.dataset_type,
        "input_path": str(request.input_path) if request.input_path is not None else "",
        "revision_id": request.revision_id or settings.default_revision_id,
        "symbol": request.symbol or "",
        "start_date": request.start_date or "",
        "end_date": request.end_date or "",
        "params": request.params,
        "adapter_input_path": str((adapter_metadata or {}).get("input_path", "")),
        "config_version": settings.config_version,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def resolve_data_source_artifact_paths(
    output_dir: str | Path,
    source: str,
    dataset_type: str,
    run_id: str,
) -> DataSourceArtifactPaths:
    """Resolve stable raw data source artifact paths."""

    artifact_dir = Path(output_dir) / _normalize_source(source) / _normalize_dataset_type(dataset_type) / run_id
    return DataSourceArtifactPaths(
        artifact_dir=artifact_dir,
        raw_data=artifact_dir / "raw_data.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_raw_data_source_artifacts(result: DataSourceResult) -> dict[str, Path]:
    """Write raw CSV and metadata artifacts for a data source fetch."""

    paths = DataSourceArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.raw_data, paths.raw_data)
    metadata = build_data_source_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    return paths.as_dict()


def build_data_source_metadata(result: DataSourceResult, paths: DataSourceArtifactPaths) -> dict[str, Any]:
    """Build metadata.json content for a data source fetch."""

    return {
        "source": result.source,
        "dataset_type": result.dataset_type,
        "run_id": result.run_id,
        "row_count": result.row_count,
        "created_at": "1970-01-01T00:00:00+00:00",
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "real_data_allowed": bool(result.audit_metadata.get("real_data_allowed", False)),
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def _adapter_registry() -> dict[str, BaseDataSourceAdapter]:
    return {
        "LOCAL_CSV": LocalCsvDataSourceAdapter(),
        "MOCK": MockDataSourceAdapter(),
        "AKSHARE_OPTIONAL": OptionalAkshareDataSourceAdapter(),
    }


def _normalize_request(request: DataSourceRequest, settings: DataSourceSettings) -> DataSourceRequest:
    source = _normalize_source(request.source or settings.default_source)
    dataset_type = _normalize_dataset_type(request.dataset_type)
    return DataSourceRequest(
        source=source,
        dataset_type=dataset_type,
        input_path=Path(request.input_path) if request.input_path is not None else None,
        output_dir=Path(request.output_dir) if request.output_dir is not None else None,
        revision_id=request.revision_id or settings.default_revision_id,
        allow_real_data=bool(request.allow_real_data),
        symbol=request.symbol,
        start_date=request.start_date,
        end_date=request.end_date,
        params=dict(request.params or {}),
    )


def _normalize_source(source: str) -> str:
    return str(source).strip().upper()


def _normalize_dataset_type(dataset_type: str) -> str:
    normalized = str(dataset_type).strip().lower()
    if normalized not in SUPPORTED_DATASET_TYPES:
        raise ValueError(f"dataset_type must be one of: {', '.join(sorted(SUPPORTED_DATASET_TYPES))}")
    return normalized


def _mock_path_for_dataset(dataset_type: str, settings: Settings) -> Path:
    mapping = {
        "market": settings.data.mock_prices,
        "benchmark": settings.data.mock_prices,
        "universe": settings.data.mock_universe_snapshots,
        "corporate_actions": settings.data.mock_corporate_actions,
        "trading_calendar": settings.data.mock_trading_calendar,
    }
    return Path(mapping[_normalize_dataset_type(dataset_type)])


def _enforce_real_data_guardrails(
    adapter: BaseDataSourceAdapter,
    request: DataSourceRequest,
    settings: DataSourceSettings,
) -> None:
    if not adapter.is_real_data_source:
        return
    if settings.require_manual_real_data_flag and not request.allow_real_data:
        raise ValueError(f"{adapter.source} requires explicit --allow-real-data for manual real-data access")
    if not settings.allow_real_data_fetch or not settings.allow_network_sources:
        raise ValueError(
            f"{adapter.source} is disabled by config. Set data_sources.allow_real_data_fetch=true "
            "and data_sources.allow_network_sources=true for a manual run."
        )


def _resolve_settings(
    settings: Settings | DataSourceSettings | dict[str, Any] | None,
) -> tuple[Settings, DataSourceSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.data_sources
    if isinstance(settings, Settings):
        return settings, settings.data_sources
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, DataSourceSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.data_sources.model_dump())
        for key, value in settings.items():
            if key == "data_sources" and isinstance(value, dict):
                payload.update(value)
            elif key in payload:
                payload[key] = value
        return project, DataSourceSettings(**payload)
    raise TypeError("settings must be Settings, DataSourceSettings, dict, or None")


def _request_metadata(request: DataSourceRequest) -> dict[str, Any]:
    return {
        "source": request.source,
        "dataset_type": request.dataset_type,
        "input_path": str(request.input_path) if request.input_path is not None else "",
        "output_dir": str(request.output_dir) if request.output_dir is not None else "",
        "revision_id": request.revision_id,
        "allow_real_data": request.allow_real_data,
        "symbol": request.symbol or "",
        "start_date": request.start_date or "",
        "end_date": request.end_date or "",
        "params": request.params,
    }


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
    if isinstance(value, Path):
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
