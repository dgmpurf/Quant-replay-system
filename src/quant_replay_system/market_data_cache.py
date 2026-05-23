"""Local CSV cache for canonical daily market bars."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketDataCacheSettings, Settings, load_settings
from quant_replay_system.data import normalize_symbol_series, read_csv_preserve_symbol_columns


CACHE_TIMESTAMP = "1970-01-01T00:00:00+00:00"

MARKET_CACHE_COLUMNS = [
    "symbol",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "pre_close",
    "adj_factor",
    "is_suspended",
    "limit_up",
    "limit_down",
    "event_time",
    "publish_time",
    "ingest_time",
    "available_time",
    "revision_id",
    "source",
    "upstream_source",
    "successful_function",
    "fetched_at",
    "cache_ingested_at",
]

INPUT_REQUIRED_COLUMNS = [
    "symbol",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "pre_close",
    "adj_factor",
    "is_suspended",
    "limit_up",
    "limit_down",
    "event_time",
    "publish_time",
    "ingest_time",
    "available_time",
    "revision_id",
    "source",
]

CACHE_KEY_COLUMNS = ["symbol", "trade_date", "source", "upstream_source", "revision_id"]

MARKET_CACHE_LIMITATIONS = [
    "The cache stores local canonical daily bars only.",
    "The cache reduces repeated public data-source calls but does not certify data quality.",
    "Cached rows must still pass data-pipeline, data-quality, and snapshot-quality before research use.",
    "The cache does not connect to brokers, place orders, or automate execution.",
]


@dataclass(frozen=True)
class MarketDataCacheArtifactPaths:
    artifact_dir: Path
    market_cache_report: Path
    market_cache_summary: Path
    market_cache_ingested_rows: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_cache_report": self.market_cache_report,
            "market_cache_summary": self.market_cache_summary,
            "market_cache_ingested_rows": self.market_cache_ingested_rows,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MarketDataCacheIngestResult:
    cache_run_id: str
    status: str
    cache_path: Path
    input_path: Path
    metadata_path: Path | None
    ingested_rows: pd.DataFrame
    cache_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]

    @property
    def row_count(self) -> int:
        return len(self.ingested_rows)

    @property
    def cache_row_count(self) -> int:
        return len(self.cache_frame)

    @property
    def symbol_count(self) -> int:
        return int(self.cache_frame["symbol"].nunique()) if not self.cache_frame.empty else 0


@dataclass(frozen=True)
class MarketDataCacheQueryResult:
    status: str
    cache_path: Path
    symbol: str
    start_date: str | None
    end_date: str | None
    result_frame: pd.DataFrame
    output_path: Path | None
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]

    @property
    def row_count(self) -> int:
        return len(self.result_frame)


@dataclass(frozen=True)
class MarketDataCacheStatusResult:
    cache_run_id: str
    status: str
    cache_path: Path
    cache_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]

    @property
    def row_count(self) -> int:
        return len(self.cache_frame)

    @property
    def symbol_count(self) -> int:
        return int(self.cache_frame["symbol"].nunique()) if not self.cache_frame.empty else 0


def load_market_cache(
    cache_path: str | Path | None = None,
    *,
    config: Settings | MarketDataCacheSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Load the local market cache, returning an empty canonical frame when absent."""

    _project_settings, cache_settings = _resolve_settings(config)
    path = Path(cache_path) if cache_path is not None else cache_settings.cache_path
    if not path.exists():
        return pd.DataFrame(columns=MARKET_CACHE_COLUMNS)
    frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    return _finalize_cache_frame(frame)


def ingest_market_cache_csv(
    input_path: str | Path,
    *,
    metadata_path: str | Path | None = None,
    cache_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    config: Settings | MarketDataCacheSettings | dict[str, Any] | None = None,
) -> MarketDataCacheIngestResult:
    """Ingest one canonical market CSV into the local cache."""

    project_settings, cache_settings = _resolve_settings(config)
    if cache_settings.enable_live_trading or cache_settings.enable_broker_api:
        raise ValueError("Market data cache cannot enable live trading or broker API access")

    source_path = Path(input_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Market cache input CSV not found: {source_path}")
    metadata_file = Path(metadata_path) if metadata_path is not None else None
    metadata = _load_optional_metadata(metadata_file)
    raw = read_csv_preserve_symbol_columns(source_path, keep_default_na=False)
    incoming = _prepare_market_cache_rows(raw, metadata=metadata, settings=cache_settings)
    existing = load_market_cache(cache_path, config=project_settings)
    merged = merge_market_cache(existing, incoming, settings=cache_settings)
    path = Path(cache_path) if cache_path is not None else cache_settings.cache_path
    cache_run_id = generate_market_cache_run_id(
        source_path,
        metadata_file,
        path,
        operation="ingest",
        settings=cache_settings,
    )
    summary = build_market_cache_summary_frame(
        merged,
        cache_run_id=cache_run_id,
        cache_path=path,
        status="PASS",
        ingested_row_count=len(incoming),
    )
    artifact_paths = resolve_market_cache_artifact_paths(
        Path(output_dir) if output_dir is not None else cache_settings.output_dir,
        cache_run_id,
    )
    result = MarketDataCacheIngestResult(
        cache_run_id=cache_run_id,
        status="PASS",
        cache_path=path,
        input_path=source_path,
        metadata_path=metadata_file,
        ingested_rows=incoming,
        cache_frame=merged,
        summary_frame=summary,
        artifact_paths=artifact_paths.as_dict(),
        warnings=[],
        known_limitations=MARKET_CACHE_LIMITATIONS,
        audit_metadata={
            "cache_run_id": cache_run_id,
            "operation": "ingest",
            "cache_path": path,
            "input_path": source_path,
            "metadata_path": metadata_file,
            "ingested_row_count": len(incoming),
            "cache_row_count": len(merged),
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "market_data_cache_only": True,
            "config_version": cache_settings.config_version,
        },
    )
    if cache_settings.write_artifacts:
        write_market_cache_artifacts(result)
    _write_cache_frame(merged, path)
    _ = project_settings
    return result


def validate_market_cache_frame(
    frame: pd.DataFrame,
    *,
    settings: MarketDataCacheSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Validate and normalize a market cache frame."""

    cache_settings = _coerce_cache_settings(settings)
    output = frame.copy(deep=True)
    missing = [column for column in INPUT_REQUIRED_COLUMNS if column not in output.columns]
    if missing:
        raise ValueError(f"Market cache input missing required columns: {', '.join(missing)}")
    output["symbol"] = normalize_symbol_series(output["symbol"])
    if output["symbol"].eq("").any():
        raise ValueError("Market cache input contains missing symbol values")

    output["trade_date"] = _parse_date_column(output["trade_date"], "trade_date")
    if cache_settings.require_available_time:
        output["available_time"] = _parse_timestamp_column(output["available_time"], "available_time")
    else:
        output["available_time"] = _parse_optional_timestamp_column(output["available_time"], "available_time")

    for column in ["event_time", "publish_time", "ingest_time"]:
        output[column] = _parse_optional_timestamp_column(output[column], column)

    for column in ["open", "high", "low", "close", "volume", "amount"]:
        output[column] = _parse_required_numeric_column(output[column], column)
        if (output[column] < 0).any():
            raise ValueError(f"{column} contains negative values")
    for column in ["pre_close", "adj_factor", "limit_up", "limit_down"]:
        output[column] = _parse_optional_numeric_column(output[column], column)
        non_missing = output[column].notna()
        if (output.loc[non_missing, column] < 0).any():
            raise ValueError(f"{column} contains negative values")
    if (output["high"] < output["low"]).any():
        raise ValueError("Market cache input violates OHLC sanity: high is less than low")

    output["is_suspended"] = output["is_suspended"].map(_normalize_bool_text)
    output["revision_id"] = output["revision_id"].map(_string_or_empty)
    output["source"] = output["source"].map(_string_or_empty)
    if output["revision_id"].eq("").any():
        raise ValueError("Market cache input contains missing revision_id values")
    if output["source"].eq("").any():
        raise ValueError("Market cache input contains missing source values")
    return output


def merge_market_cache(
    existing: pd.DataFrame,
    incoming: pd.DataFrame,
    *,
    settings: MarketDataCacheSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Merge incoming rows into an existing cache frame."""

    cache_settings = _coerce_cache_settings(settings)
    if cache_settings.duplicate_policy != "keep_latest":
        raise ValueError(f"Unsupported market cache duplicate_policy: {cache_settings.duplicate_policy}")
    existing_frame = _finalize_cache_frame(existing)
    incoming_frame = _finalize_cache_frame(incoming)
    if existing_frame.empty:
        merged = incoming_frame.copy(deep=True)
        if merged.empty:
            return pd.DataFrame(columns=MARKET_CACHE_COLUMNS)
        merged = merged.drop_duplicates(subset=CACHE_KEY_COLUMNS, keep="last")
        return _sort_cache_frame(merged)
    merged = pd.concat([existing_frame, incoming_frame], ignore_index=True)
    if merged.empty:
        return pd.DataFrame(columns=MARKET_CACHE_COLUMNS)
    merged = merged.drop_duplicates(subset=CACHE_KEY_COLUMNS, keep="last")
    return _sort_cache_frame(merged)


def query_market_cache(
    *,
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    cache_path: str | Path | None = None,
    output_path: str | Path | None = None,
    config: Settings | MarketDataCacheSettings | dict[str, Any] | None = None,
) -> MarketDataCacheQueryResult:
    """Query cached market bars by symbol and optional date range."""

    project_settings, cache_settings = _resolve_settings(config)
    if cache_settings.enable_live_trading or cache_settings.enable_broker_api:
        raise ValueError("Market data cache cannot enable live trading or broker API access")
    path = Path(cache_path) if cache_path is not None else cache_settings.cache_path
    if not path.exists():
        raise FileNotFoundError(f"Market cache file not found: {path}")
    frame = load_market_cache(path, config=project_settings)
    normalized_symbol = normalize_symbol_series(pd.Series([symbol])).iloc[0]
    result = frame.loc[frame["symbol"] == normalized_symbol].copy()
    if start_date:
        start = pd.to_datetime(start_date, errors="raise").normalize()
        result = result.loc[pd.to_datetime(result["trade_date"], errors="coerce") >= start]
    if end_date:
        end = pd.to_datetime(end_date, errors="raise").normalize()
        result = result.loc[pd.to_datetime(result["trade_date"], errors="coerce") <= end]
    result = _sort_cache_frame(result)
    output = Path(output_path) if output_path is not None else None
    if output is not None:
        _write_cache_frame(result, output)
    return MarketDataCacheQueryResult(
        status="PASS" if not result.empty else "WARN",
        cache_path=path,
        symbol=normalized_symbol,
        start_date=start_date,
        end_date=end_date,
        result_frame=result,
        output_path=output,
        warnings=[] if not result.empty else [f"No cached rows matched symbol={normalized_symbol}"],
        known_limitations=MARKET_CACHE_LIMITATIONS,
        audit_metadata={
            "operation": "query",
            "cache_path": path,
            "symbol": normalized_symbol,
            "start_date": start_date or "",
            "end_date": end_date or "",
            "row_count": len(result),
            "output_path": output,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "market_data_cache_only": True,
            "config_version": cache_settings.config_version,
        },
    )


def summarize_market_cache_status(
    *,
    cache_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    config: Settings | MarketDataCacheSettings | dict[str, Any] | None = None,
) -> MarketDataCacheStatusResult:
    """Summarize the current cache contents and write status artifacts."""

    project_settings, cache_settings = _resolve_settings(config)
    if cache_settings.enable_live_trading or cache_settings.enable_broker_api:
        raise ValueError("Market data cache cannot enable live trading or broker API access")
    path = Path(cache_path) if cache_path is not None else cache_settings.cache_path
    frame = load_market_cache(path, config=project_settings)
    status = "PASS" if path.exists() else "WARN"
    cache_run_id = generate_market_cache_run_id(
        path,
        None,
        path,
        operation="status",
        settings=cache_settings,
    )
    summary = build_market_cache_summary_frame(
        frame,
        cache_run_id=cache_run_id,
        cache_path=path,
        status=status,
        ingested_row_count=0,
    )
    warnings = [] if path.exists() else [f"Market cache file does not exist yet: {path}"]
    artifact_paths = resolve_market_cache_artifact_paths(
        Path(output_dir) if output_dir is not None else cache_settings.output_dir,
        cache_run_id,
    )
    result = MarketDataCacheStatusResult(
        cache_run_id=cache_run_id,
        status=status,
        cache_path=path,
        cache_frame=frame,
        summary_frame=summary,
        artifact_paths=artifact_paths.as_dict(),
        warnings=warnings,
        known_limitations=MARKET_CACHE_LIMITATIONS,
        audit_metadata={
            "cache_run_id": cache_run_id,
            "operation": "status",
            "cache_path": path,
            "cache_row_count": len(frame),
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "market_data_cache_only": True,
            "config_version": cache_settings.config_version,
        },
    )
    if cache_settings.write_artifacts:
        write_market_cache_artifacts(result)
    return result


def write_market_cache_artifacts(
    result: MarketDataCacheIngestResult | MarketDataCacheStatusResult,
) -> dict[str, Path]:
    """Write market cache report, summary CSV, ingested rows, and metadata."""

    paths = MarketDataCacheArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths.market_cache_summary, index=False)
    ingested = getattr(result, "ingested_rows", pd.DataFrame(columns=MARKET_CACHE_COLUMNS))
    ingested.to_csv(paths.market_cache_ingested_rows, index=False)
    paths.market_cache_report.write_text(render_market_cache_report(result), encoding="utf-8")
    metadata = {
        "cache_run_id": result.cache_run_id,
        "status": result.status,
        "cache_path": str(result.cache_path),
        "row_count": int(result.row_count),
        "symbol_count": int(result.symbol_count),
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
        "summary": result.summary_frame.to_dict("records"),
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "created_at": CACHE_TIMESTAMP,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    return paths.as_dict()


def render_market_cache_report(result: MarketDataCacheIngestResult | MarketDataCacheStatusResult) -> str:
    """Render a market cache markdown report."""

    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    lines = [
        "# Local Market Data Cache",
        "",
        f"- cache_run_id: {result.cache_run_id}",
        f"- status: {result.status}",
        f"- cache_path: {result.cache_path}",
        f"- row_count: {summary.get('cache_row_count', 0)}",
        f"- symbol_count: {summary.get('symbol_count', 0)}",
        f"- date_range: {summary.get('min_trade_date', '')} to {summary.get('max_trade_date', '')}",
        "",
        "No live trading or broker API was invoked.",
        "",
        "## Summary",
        "",
        result.summary_frame.to_markdown(index=False) if not result.summary_frame.empty else "No cache rows.",
    ]
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in result.known_limitations)
    return "\n".join(lines) + "\n"


def build_market_cache_summary_frame(
    frame: pd.DataFrame,
    *,
    cache_run_id: str,
    cache_path: Path,
    status: str,
    ingested_row_count: int,
) -> pd.DataFrame:
    cache_frame = _finalize_cache_frame(frame)
    if cache_frame.empty:
        min_trade_date = ""
        max_trade_date = ""
        symbol_count = 0
        source_counts: dict[str, int] = {}
        upstream_counts: dict[str, int] = {}
    else:
        min_trade_date = str(cache_frame["trade_date"].min())
        max_trade_date = str(cache_frame["trade_date"].max())
        symbol_count = int(cache_frame["symbol"].nunique())
        source_counts = {str(key): int(value) for key, value in cache_frame["source"].value_counts().sort_index().items()}
        upstream_counts = {
            str(key): int(value)
            for key, value in cache_frame["upstream_source"].fillna("").value_counts().sort_index().items()
        }
    return pd.DataFrame(
        [
            {
                "cache_run_id": cache_run_id,
                "status": status,
                "cache_path": str(cache_path),
                "ingested_row_count": int(ingested_row_count),
                "cache_row_count": int(len(cache_frame)),
                "symbol_count": symbol_count,
                "min_trade_date": min_trade_date,
                "max_trade_date": max_trade_date,
                "source_counts": json.dumps(source_counts, sort_keys=True),
                "upstream_counts": json.dumps(upstream_counts, sort_keys=True),
                "no_live_trading": True,
                "no_broker_api": True,
            }
        ]
    )


def resolve_market_cache_artifact_paths(
    output_dir: str | Path,
    cache_run_id: str,
) -> MarketDataCacheArtifactPaths:
    artifact_dir = Path(output_dir) / cache_run_id
    return MarketDataCacheArtifactPaths(
        artifact_dir=artifact_dir,
        market_cache_report=artifact_dir / "market_cache_report.md",
        market_cache_summary=artifact_dir / "market_cache_summary.csv",
        market_cache_ingested_rows=artifact_dir / "market_cache_ingested_rows.csv",
        metadata=artifact_dir / "metadata.json",
    )


def generate_market_cache_run_id(
    input_path: str | Path,
    metadata_path: str | Path | None,
    cache_path: str | Path,
    *,
    operation: str,
    settings: MarketDataCacheSettings,
) -> str:
    payload = {
        "operation": operation,
        "input_path": str(input_path),
        "metadata_path": str(metadata_path) if metadata_path is not None else "",
        "cache_path": str(cache_path),
        "duplicate_policy": settings.duplicate_policy,
        "config_version": settings.config_version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _prepare_market_cache_rows(
    raw: pd.DataFrame,
    *,
    metadata: dict[str, Any],
    settings: MarketDataCacheSettings,
) -> pd.DataFrame:
    validated = validate_market_cache_frame(raw, settings=settings)
    metadata_fields = _market_metadata_fields(metadata)
    for column, value in metadata_fields.items():
        if column not in validated.columns or validated[column].map(_is_missing_token).all():
            validated[column] = value
        else:
            validated[column] = validated[column].map(lambda item: value if _is_missing_token(item) else item)
    validated["cache_ingested_at"] = CACHE_TIMESTAMP
    for column in MARKET_CACHE_COLUMNS:
        if column not in validated.columns:
            validated[column] = ""
    return _finalize_cache_frame(validated)


def _market_metadata_fields(metadata: dict[str, Any]) -> dict[str, str]:
    adapter_metadata = metadata.get("audit_metadata", {}).get("adapter_metadata", {})
    return {
        "upstream_source": _string_or_empty(metadata.get("upstream_source") or adapter_metadata.get("upstream_source")),
        "successful_function": _string_or_empty(
            metadata.get("successful_function") or adapter_metadata.get("successful_function")
        ),
        "fetched_at": _string_or_empty(metadata.get("created_at") or metadata.get("fetched_at") or CACHE_TIMESTAMP),
    }


def _load_optional_metadata(metadata_path: Path | None) -> dict[str, Any]:
    if metadata_path is None:
        return {}
    if not metadata_path.exists():
        raise FileNotFoundError(f"Market cache metadata JSON not found: {metadata_path}")
    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Market cache metadata JSON is unreadable: {metadata_path}") from exc


def _finalize_cache_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=MARKET_CACHE_COLUMNS)
    output = frame.copy(deep=True)
    for column in MARKET_CACHE_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    output = output[MARKET_CACHE_COLUMNS]
    output["symbol"] = normalize_symbol_series(output["symbol"])
    output["trade_date"] = _parse_date_column(output["trade_date"], "trade_date")
    for column in ["event_time", "publish_time", "ingest_time", "available_time", "fetched_at", "cache_ingested_at"]:
        output[column] = output[column].map(_string_or_empty)
    for column in ["revision_id", "source", "upstream_source", "successful_function"]:
        output[column] = output[column].map(_string_or_empty)
    return _sort_cache_frame(output)


def _sort_cache_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=MARKET_CACHE_COLUMNS)
    return frame.sort_values(["symbol", "trade_date", "source", "upstream_source", "revision_id"]).reset_index(drop=True)


def _write_cache_frame(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    export = frame.copy(deep=True)
    export.to_csv(path, index=False)


def _parse_date_column(series: pd.Series, column: str) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce").dt.normalize()
    if parsed.isna().any():
        raise ValueError(f"{column} contains missing or invalid dates")
    return parsed.dt.strftime("%Y-%m-%d")


def _parse_timestamp_column(series: pd.Series, column: str) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    if parsed.isna().any():
        raise ValueError(f"{column} contains missing or invalid timestamps")
    return parsed.dt.strftime("%Y-%m-%d %H:%M:%S")


def _parse_optional_timestamp_column(series: pd.Series, column: str) -> pd.Series:
    text = series.map(_string_or_empty)
    missing = text.map(_is_missing_token)
    parsed = pd.to_datetime(text.mask(missing, ""), errors="coerce")
    invalid = parsed.isna() & ~missing
    if invalid.any():
        raise ValueError(f"{column} contains invalid non-empty timestamps")
    output = parsed.dt.strftime("%Y-%m-%d %H:%M:%S")
    return output.mask(missing, "")


def _parse_required_numeric_column(series: pd.Series, column: str) -> pd.Series:
    parsed = pd.to_numeric(series, errors="coerce")
    if parsed.isna().any():
        raise ValueError(f"{column} contains missing or invalid numeric values")
    return parsed


def _parse_optional_numeric_column(series: pd.Series, column: str) -> pd.Series:
    text = series.map(_string_or_empty)
    missing = text.map(_is_missing_token)
    parsed = pd.to_numeric(text.mask(missing, ""), errors="coerce")
    invalid = parsed.isna() & ~missing
    if invalid.any():
        raise ValueError(f"{column} contains invalid non-empty numeric values")
    return parsed


def _normalize_bool_text(value: Any) -> str:
    text = _string_or_empty(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return "true"
    if text in {"false", "0", "no", "n", ""}:
        return "false"
    raise ValueError("is_suspended contains invalid boolean values")


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _is_missing_token(value: Any) -> bool:
    return _string_or_empty(value).strip().lower() in {"", "nan", "nat", "none", "null", "-", "--"}


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


def _coerce_cache_settings(settings: MarketDataCacheSettings | dict[str, Any] | None) -> MarketDataCacheSettings:
    if settings is None:
        return load_settings(Path("config/default.yaml")).market_data_cache
    if isinstance(settings, MarketDataCacheSettings):
        return settings
    if isinstance(settings, dict):
        base = load_settings(Path("config/default.yaml")).market_data_cache.model_dump()
        base.update(settings)
        return MarketDataCacheSettings(**base)
    raise TypeError("settings must be MarketDataCacheSettings, dict, or None")


def _resolve_settings(
    settings: Settings | MarketDataCacheSettings | dict[str, Any] | None,
) -> tuple[Settings, MarketDataCacheSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.market_data_cache
    if isinstance(settings, Settings):
        return settings, settings.market_data_cache
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, MarketDataCacheSettings):
        return project, settings
    if isinstance(settings, dict):
        cache_payload = dict(project.market_data_cache.model_dump())
        for key, value in settings.items():
            if key == "market_data_cache" and isinstance(value, dict):
                cache_payload.update(value)
            elif key in cache_payload:
                cache_payload[key] = value
        return project, MarketDataCacheSettings(**cache_payload)
    raise TypeError("settings must be Settings, MarketDataCacheSettings, dict, or None")
