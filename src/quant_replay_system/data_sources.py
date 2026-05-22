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
    as_of_date: str | None = None
    market_type: str | None = None
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
    """Manual-only AKShare data source adapter.

    The adapter intentionally imports akshare only after all real-data guardrails
    pass so automated tests can assert the blocked path stays fully offline.
    """

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
        if request.dataset_type not in {"market", "benchmark", "trading_calendar", "universe"}:
            raise NotImplementedError(
                f"AKSHARE_OPTIONAL does not support dataset_type={request.dataset_type!r} in v0.1. "
                "Supported dataset types: market, benchmark, trading_calendar, universe."
            )
        akshare = _import_akshare()
        if request.dataset_type == "universe":
            frame, adapter_metadata = _fetch_akshare_universe(akshare, request)
        elif request.dataset_type == "trading_calendar":
            frame, adapter_metadata = _fetch_akshare_trading_calendar(akshare, request)
        else:
            frame, adapter_metadata = _fetch_akshare_market_like(akshare, request)
        return frame, adapter_metadata, [
            "AKSHARE_OPTIONAL is manual-only and should be passed through ingestion and data quality before use."
        ]


def _import_akshare():
    try:
        import akshare  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "AKSHARE_OPTIONAL requires akshare to be installed for manual real-data fetches. "
            "Install it in your local environment with: python -m pip install akshare"
        ) from exc
    return akshare


def _fetch_akshare_market_like(
    akshare,
    request: DataSourceRequest,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not request.symbol:
        raise ValueError("AKSHARE_OPTIONAL market/benchmark fetch requires --symbol")
    if not request.start_date or not request.end_date:
        raise ValueError("AKSHARE_OPTIONAL market/benchmark fetch requires --start-date and --end-date")
    function_name = _akshare_market_function_name(request)
    function = getattr(akshare, function_name, None)
    if function is None:
        raise RuntimeError(f"akshare function not available: {function_name}")
    kwargs = _akshare_market_kwargs(request, function_name)
    raw = function(**kwargs)
    frame = _normalize_akshare_market_frame(
        pd.DataFrame(raw),
        symbol=request.symbol,
        dataset_type=request.dataset_type,
        start_date=request.start_date,
        end_date=request.end_date,
        source=request.source,
        revision_id=request.revision_id,
    )
    adapter_metadata = {
        "adapter": request.source,
        "adapter_status": "SUCCESS",
        "akshare_function": function_name,
        "symbol": request.symbol,
        "start_date": request.start_date,
        "end_date": request.end_date,
    }
    return frame, adapter_metadata


def _fetch_akshare_trading_calendar(
    akshare,
    request: DataSourceRequest,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not request.start_date or not request.end_date:
        raise ValueError("AKSHARE_OPTIONAL trading_calendar fetch requires --start-date and --end-date")
    function_name = str(request.params.get("akshare_function") or "tool_trade_date_hist_sina")
    function = getattr(akshare, function_name, None)
    if function is None:
        raise RuntimeError(f"akshare function not available: {function_name}")
    raw = function()
    frame = _normalize_akshare_calendar_frame(
        pd.DataFrame(raw),
        start_date=request.start_date,
        end_date=request.end_date,
    )
    adapter_metadata = {
        "adapter": request.source,
        "adapter_status": "SUCCESS",
        "akshare_function": function_name,
        "start_date": request.start_date,
        "end_date": request.end_date,
    }
    return frame, adapter_metadata


def _fetch_akshare_universe(
    akshare,
    request: DataSourceRequest,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    as_of_date = _resolve_akshare_as_of_date(request)
    market_type = _normalize_akshare_market_type(request.market_type or request.params.get("market_type") or "all")
    frames: list[pd.DataFrame] = []
    function_names: list[str] = []
    for instrument_type, function_name in _akshare_universe_function_specs(request, market_type):
        function = getattr(akshare, function_name, None)
        if function is None:
            raise RuntimeError(f"akshare function not available: {function_name}")
        raw = function()
        frame = pd.DataFrame(raw)
        frame["_akshare_instrument_type"] = instrument_type
        frame["_akshare_function"] = function_name
        frames.append(frame)
        function_names.append(function_name)
    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    raw_columns = [str(column) for column in combined.columns]
    normalized, mapping_warnings = _normalize_akshare_universe_frame(
        combined,
        as_of_date=as_of_date,
        market_type=market_type,
        source=request.source,
        revision_id=request.revision_id,
    )
    adapter_metadata = {
        "adapter": request.source,
        "adapter_status": "SUCCESS",
        "akshare_functions": function_names,
        "as_of_date": as_of_date,
        "market_type": market_type,
        "raw_columns": raw_columns,
        "normalized_columns": list(normalized.columns),
        "mapping_warnings": mapping_warnings,
        "row_count": len(normalized),
    }
    return normalized, adapter_metadata


def _akshare_universe_function_specs(request: DataSourceRequest, market_type: str) -> list[tuple[str, str]]:
    configured = request.params.get("akshare_function")
    if configured:
        instrument_type = "UNKNOWN" if market_type == "all" else market_type.upper()
        return [(instrument_type, str(configured))]
    if market_type == "stock":
        return [("STOCK", "stock_info_a_code_name")]
    if market_type == "etf":
        return [("ETF", "fund_etf_spot_em")]
    if market_type == "all":
        return [("STOCK", "stock_info_a_code_name"), ("ETF", "fund_etf_spot_em")]
    raise ValueError("AKSHARE_OPTIONAL universe market_type must be one of: stock, etf, all")


def _normalize_akshare_market_type(value: Any) -> str:
    normalized = str(value or "all").strip().lower()
    aliases = {
        "stocks": "stock",
        "a_share": "stock",
        "ashare": "stock",
        "a-share": "stock",
        "fund": "etf",
        "fund_etf": "etf",
        "etfs": "etf",
    }
    return aliases.get(normalized, normalized)


def _akshare_market_function_name(request: DataSourceRequest) -> str:
    configured = request.params.get("akshare_function")
    if configured:
        return str(configured)
    if request.dataset_type == "benchmark":
        return "stock_zh_index_daily"
    asset_type = str(request.params.get("asset_type") or "").strip().upper()
    symbol = str(request.symbol or "")
    if asset_type == "ETF" or symbol.startswith(("1", "5")):
        return "fund_etf_hist_em"
    return "stock_zh_a_hist"


def _akshare_market_kwargs(request: DataSourceRequest, function_name: str) -> dict[str, Any]:
    if function_name == "stock_zh_index_daily":
        return {"symbol": request.symbol}
    kwargs = {
        "symbol": request.symbol,
        "period": request.params.get("period", "daily"),
        "start_date": _akshare_date(request.start_date),
        "end_date": _akshare_date(request.end_date),
    }
    if function_name in {"fund_etf_hist_em", "stock_zh_a_hist"}:
        kwargs["adjust"] = request.params.get("adjust", "")
    return kwargs


def _normalize_akshare_market_frame(
    frame: pd.DataFrame,
    *,
    symbol: str,
    dataset_type: str,
    start_date: str,
    end_date: str,
    source: str,
    revision_id: str | None,
) -> pd.DataFrame:
    if frame.empty:
        return _canonical_market_frame(pd.DataFrame(), symbol=symbol, source=source, revision_id=revision_id)
    normalized = frame.rename(
        columns={column: _AKSHARE_MARKET_COLUMN_ALIASES.get(str(column), column) for column in frame.columns}
    )
    if "trade_date" not in normalized.columns:
        raise ValueError("AKSHARE_OPTIONAL market data did not include a date/trade_date column")
    normalized["trade_date"] = pd.to_datetime(normalized["trade_date"], errors="coerce")
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    normalized = normalized.loc[
        normalized["trade_date"].notna()
        & (normalized["trade_date"] >= start)
        & (normalized["trade_date"] <= end)
    ].copy()
    normalized["symbol"] = symbol
    normalized = normalized.sort_values(["symbol", "trade_date"]).reset_index(drop=True)
    return _canonical_market_frame(normalized, symbol=symbol, source=source, revision_id=revision_id)


def _canonical_market_frame(
    frame: pd.DataFrame,
    *,
    symbol: str,
    source: str,
    revision_id: str | None,
) -> pd.DataFrame:
    output = pd.DataFrame(index=frame.index)
    output["symbol"] = frame.get("symbol", symbol)
    output["trade_date"] = pd.to_datetime(frame.get("trade_date", pd.Series(dtype="datetime64[ns]")), errors="coerce")
    for column in ["open", "high", "low", "close", "volume", "amount"]:
        output[column] = pd.to_numeric(frame.get(column, pd.Series(0, index=frame.index)), errors="coerce").fillna(0)
    pre_close = pd.to_numeric(frame.get("pre_close", pd.Series(index=frame.index, dtype="float64")), errors="coerce")
    if pre_close.isna().all() and not output.empty:
        pre_close = output.groupby("symbol")["close"].shift(1)
    output["pre_close"] = pre_close.fillna(output["open"]).fillna(output["close"]).fillna(0)
    output["adj_factor"] = pd.to_numeric(frame.get("adj_factor", pd.Series(1.0, index=frame.index)), errors="coerce").fillna(1.0)
    output["is_suspended"] = frame.get("is_suspended", False)
    output["limit_up"] = pd.to_numeric(frame.get("limit_up", output["pre_close"] * 1.10), errors="coerce").fillna(output["pre_close"] * 1.10)
    output["limit_down"] = pd.to_numeric(frame.get("limit_down", output["pre_close"] * 0.90), errors="coerce").fillna(output["pre_close"] * 0.90)
    trade_dates = pd.to_datetime(output["trade_date"], errors="coerce")
    output["event_time"] = trade_dates + pd.Timedelta(hours=15)
    output["publish_time"] = trade_dates + pd.Timedelta(hours=15, minutes=20)
    output["ingest_time"] = trade_dates + pd.Timedelta(hours=15, minutes=30)
    output["available_time"] = trade_dates + pd.Timedelta(hours=15, minutes=30)
    output["revision_id"] = revision_id or "v1"
    output["source"] = source
    return output[
        [
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
    ]


def _normalize_akshare_calendar_frame(
    frame: pd.DataFrame,
    *,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            columns=["trade_date", "is_trading_day", "session_open", "session_close", "decision_time", "reason"]
        )
    normalized = frame.rename(
        columns={column: _AKSHARE_CALENDAR_COLUMN_ALIASES.get(str(column), column) for column in frame.columns}
    )
    if "trade_date" not in normalized.columns:
        first_column = normalized.columns[0]
        normalized = normalized.rename(columns={first_column: "trade_date"})
    normalized["trade_date"] = pd.to_datetime(normalized["trade_date"], errors="coerce")
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    normalized = normalized.loc[
        normalized["trade_date"].notna()
        & (normalized["trade_date"] >= start)
        & (normalized["trade_date"] <= end)
    ].copy()
    if "is_trading_day" not in normalized.columns:
        normalized["is_trading_day"] = True
    output = pd.DataFrame(
        {
            "trade_date": normalized["trade_date"],
            "is_trading_day": normalized["is_trading_day"].astype(bool),
            "session_open": "09:30",
            "session_close": "15:00",
            "decision_time": "15:30",
            "reason": "akshare_trading_day",
        }
    )
    return output.reset_index(drop=True)


def _normalize_akshare_universe_frame(
    frame: pd.DataFrame,
    *,
    as_of_date: str,
    market_type: str,
    source: str,
    revision_id: str | None,
) -> tuple[pd.DataFrame, list[str]]:
    mapping_warnings: list[str] = []
    if frame.empty:
        return pd.DataFrame(columns=_UNIVERSE_COLUMNS), mapping_warnings

    symbol = normalize_symbol_series(
        get_first_series(
            frame,
            _UNIVERSE_FIELD_CANDIDATES["symbol"],
            conceptual_field="symbol",
            mapping_warnings=mapping_warnings,
        )
    )
    if symbol.eq("").all():
        raise _akshare_universe_mapping_error(frame, ["symbol"])

    valid_mask = symbol.ne("")
    source_frame = frame.loc[valid_mask].copy()
    symbol = symbol.loc[valid_mask]
    if source_frame.empty:
        raise _akshare_universe_mapping_error(frame, ["symbol"])

    name = normalize_text_series(
        get_first_series(
            source_frame,
            _UNIVERSE_FIELD_CANDIDATES["name"],
            conceptual_field="name",
            default=symbol,
            mapping_warnings=mapping_warnings,
        )
    ).replace("", pd.NA).fillna(symbol)
    as_of = pd.Timestamp(as_of_date).normalize()
    output = pd.DataFrame(index=source_frame.index)
    output["as_of_date"] = as_of
    output["symbol"] = symbol
    output["name"] = name.astype(str)
    instrument_type = normalize_text_series(
        get_first_series(
            source_frame,
            _UNIVERSE_FIELD_CANDIDATES["instrument_type"],
            conceptual_field="instrument_type",
            default="",
            mapping_warnings=mapping_warnings,
        )
    )
    output["instrument_type"] = [
        _infer_universe_instrument_type(symbol, row_type, market_type)
        for symbol, row_type in zip(output["symbol"], instrument_type)
    ]
    exchange = normalize_text_series(
        get_first_series(
            source_frame,
            _UNIVERSE_FIELD_CANDIDATES["exchange"],
            conceptual_field="exchange",
            default="",
            mapping_warnings=mapping_warnings,
        )
    )
    output["exchange"] = [
        _infer_exchange(symbol, exchange)
        for symbol, exchange in zip(output["symbol"], exchange)
    ]
    output["listed_date"] = _date_or_blank(
        source_frame,
        _UNIVERSE_FIELD_CANDIDATES["listed_date"],
        conceptual_field="listed_date",
        mapping_warnings=mapping_warnings,
    )
    output["delisted_date"] = _date_or_blank(
        source_frame,
        _UNIVERSE_FIELD_CANDIDATES["delisted_date"],
        conceptual_field="delisted_date",
        mapping_warnings=mapping_warnings,
    )
    output["is_active"] = _bool_series(
        source_frame,
        _UNIVERSE_FIELD_CANDIDATES["is_active"],
        default=True,
        conceptual_field="is_active",
        mapping_warnings=mapping_warnings,
    )
    raw_st = _bool_series(
        source_frame,
        _UNIVERSE_FIELD_CANDIDATES["is_st"],
        default=False,
        conceptual_field="is_st",
        mapping_warnings=mapping_warnings,
    )
    output["is_st"] = raw_st | output["name"].str.upper().str.contains("ST", na=False)
    output["is_suspended"] = _bool_series(
        source_frame,
        _UNIVERSE_FIELD_CANDIDATES["is_suspended"],
        default=False,
        conceptual_field="is_suspended",
        mapping_warnings=mapping_warnings,
    )
    output["industry"] = normalize_text_series(
        get_first_series(
            source_frame,
            _UNIVERSE_FIELD_CANDIDATES["industry"],
            conceptual_field="industry",
            default="UNKNOWN",
            mapping_warnings=mapping_warnings,
        )
    ).replace("", "UNKNOWN")
    min_lot = pd.to_numeric(
        get_first_series(
            source_frame,
            _UNIVERSE_FIELD_CANDIDATES["min_lot"],
            conceptual_field="min_lot",
            default=100,
            mapping_warnings=mapping_warnings,
        ),
        errors="coerce",
    )
    output["min_lot"] = min_lot.where(min_lot > 0, 100).fillna(100).astype(int)
    output["t_plus_rule"] = normalize_text_series(
        get_first_series(
            source_frame,
            _UNIVERSE_FIELD_CANDIDATES["t_plus_rule"],
            conceptual_field="t_plus_rule",
            default="T+1",
            mapping_warnings=mapping_warnings,
        )
    ).replace("", "T+1")
    available = pd.to_datetime(
        get_first_series(
            source_frame,
            _UNIVERSE_FIELD_CANDIDATES["available_time"],
            conceptual_field="available_time",
            default=pd.NaT,
            mapping_warnings=mapping_warnings,
        ),
        errors="coerce",
    )
    output["available_time"] = available.fillna(as_of + pd.Timedelta(hours=8))
    output["revision_id"] = revision_id or "v1"
    output["source"] = source
    return output[_UNIVERSE_COLUMNS].sort_values(["as_of_date", "symbol"]).reset_index(drop=True), mapping_warnings


def _resolve_akshare_as_of_date(request: DataSourceRequest) -> str:
    value = request.as_of_date or request.params.get("as_of_date") or request.end_date or request.start_date
    if value is None:
        value = pd.Timestamp.today().normalize()
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def get_first_series(
    frame: pd.DataFrame,
    candidate_columns: list[str] | tuple[str, ...],
    *,
    conceptual_field: str,
    default: Any = "",
    mapping_warnings: list[str] | None = None,
) -> pd.Series:
    """Return the first Series matching any candidate column, tolerating duplicate names."""

    for candidate in candidate_columns:
        matches = [index for index, column in enumerate(frame.columns) if str(column) == candidate]
        if matches:
            if len(matches) > 1 and mapping_warnings is not None:
                mapping_warnings.append(
                    f"Duplicate AKShare universe columns for {conceptual_field}: {candidate}; using first occurrence."
                )
            return _ensure_series(frame.iloc[:, matches[0]], frame.index)
    if isinstance(default, pd.Series):
        return default.reindex(frame.index)
    return pd.Series(default, index=frame.index)


def normalize_text_series(series: pd.Series | pd.DataFrame) -> pd.Series:
    """Normalize a pandas text column as a Series before using .str accessors."""

    return _ensure_series(series).fillna("").astype(str).str.strip()


def normalize_symbol_series(series: pd.Series | pd.DataFrame) -> pd.Series:
    """Normalize AKShare symbol/code values to uppercase strings."""

    return (
        normalize_text_series(series)
        .str.replace(r"\.0$", "", regex=True)
        .str.upper()
    )


def _ensure_series(value: pd.Series | pd.DataFrame, index: pd.Index | None = None) -> pd.Series:
    if isinstance(value, pd.DataFrame):
        if value.shape[1] == 0:
            return pd.Series("", index=index)
        return value.iloc[:, 0]
    if index is not None:
        return value.reindex(index)
    return value


def _date_or_blank(
    frame: pd.DataFrame,
    candidate_columns: list[str] | tuple[str, ...],
    *,
    conceptual_field: str,
    mapping_warnings: list[str] | None = None,
) -> pd.Series:
    raw = get_first_series(
        frame,
        candidate_columns,
        conceptual_field=conceptual_field,
        default="",
        mapping_warnings=mapping_warnings,
    )
    parsed = pd.to_datetime(raw.replace("", pd.NA), errors="coerce")
    return parsed.dt.normalize()


def _bool_series(
    frame: pd.DataFrame,
    candidate_columns: list[str] | tuple[str, ...],
    *,
    default: bool,
    conceptual_field: str,
    mapping_warnings: list[str] | None = None,
) -> pd.Series:
    raw = get_first_series(
        frame,
        candidate_columns,
        conceptual_field=conceptual_field,
        default=default,
        mapping_warnings=mapping_warnings,
    )
    normalized = normalize_text_series(raw).str.lower()
    true_values = {"true", "1", "yes", "y", "active", "\u662f"}
    false_values = {"false", "0", "no", "n", "inactive", "\u5426"}
    return normalized.map(lambda value: True if value in true_values else False if value in false_values else default)


def _akshare_universe_mapping_error(frame: pd.DataFrame, missing_fields: list[str]) -> ValueError:
    raw_columns = [str(column) for column in frame.columns]
    return ValueError(
        "AKSHARE_OPTIONAL universe mapping failed; "
        "dataset_type=universe; "
        f"raw_shape={frame.shape}; "
        f"raw_columns={raw_columns}; "
        f"missing_required_conceptual_fields={missing_fields}; "
        "suggested_action=save the raw AKShare output if available, update the universe field mapping, "
        "or use a reviewed LOCAL_CSV universe snapshot fallback."
    )


def _infer_universe_instrument_type(symbol: str, source_type: str, market_type: str) -> str:
    normalized_type = str(source_type or "").strip().upper()
    if normalized_type in {"STOCK", "ETF"}:
        return normalized_type
    if market_type in {"stock", "etf"}:
        return market_type.upper()
    code = str(symbol).split(".", 1)[0]
    if code.startswith(("1", "5")):
        return "ETF"
    if code:
        return "STOCK"
    return "UNKNOWN"


def _infer_exchange(symbol: str, exchange: str) -> str:
    normalized_exchange = str(exchange or "").strip().upper()
    if normalized_exchange in {"SSE", "SH", "SHSE", "SHANGHAI"}:
        return "SSE"
    if normalized_exchange in {"SZSE", "SZ", "SHENZHEN"}:
        return "SZSE"
    if normalized_exchange in {"BSE", "BJ", "BEIJING"}:
        return "BSE"
    upper_symbol = str(symbol).strip().upper()
    if upper_symbol.endswith(".SH"):
        return "SSE"
    if upper_symbol.endswith(".SZ"):
        return "SZSE"
    code = upper_symbol.split(".", 1)[0]
    if code.startswith(("5", "6", "9")):
        return "SSE"
    if code.startswith(("0", "1", "2", "3")):
        return "SZSE"
    if code.startswith(("4", "8")):
        return "BSE"
    return "UNKNOWN"


def _akshare_date(value: str | None) -> str:
    if value is None:
        return ""
    return pd.Timestamp(value).strftime("%Y%m%d")


_AKSHARE_MARKET_COLUMN_ALIASES = {
    "\u65e5\u671f": "trade_date",
    "date": "trade_date",
    "trade_date": "trade_date",
    "\u5f00\u76d8": "open",
    "open": "open",
    "\u6700\u9ad8": "high",
    "high": "high",
    "\u6700\u4f4e": "low",
    "low": "low",
    "\u6536\u76d8": "close",
    "close": "close",
    "\u6210\u4ea4\u91cf": "volume",
    "volume": "volume",
    "\u6210\u4ea4\u989d": "amount",
    "amount": "amount",
    "\u524d\u6536\u76d8": "pre_close",
    "pre_close": "pre_close",
}


_AKSHARE_CALENDAR_COLUMN_ALIASES = {
    "trade_date": "trade_date",
    "\u65e5\u671f": "trade_date",
    "calendarDate": "trade_date",
    "isOpen": "is_trading_day",
}


_UNIVERSE_COLUMNS = [
    "as_of_date",
    "symbol",
    "name",
    "instrument_type",
    "exchange",
    "listed_date",
    "delisted_date",
    "is_active",
    "is_st",
    "is_suspended",
    "industry",
    "min_lot",
    "t_plus_rule",
    "available_time",
    "revision_id",
    "source",
]


_AKSHARE_UNIVERSE_COLUMN_ALIASES = {
    "symbol": "symbol",
    "code": "symbol",
    "\u4ee3\u7801": "symbol",
    "\u8bc1\u5238\u4ee3\u7801": "symbol",
    "\u80a1\u7968\u4ee3\u7801": "symbol",
    "\u57fa\u91d1\u4ee3\u7801": "symbol",
    "name": "name",
    "\u540d\u79f0": "name",
    "\u7b80\u79f0": "name",
    "\u8bc1\u5238\u7b80\u79f0": "name",
    "\u80a1\u7968\u7b80\u79f0": "name",
    "\u57fa\u91d1\u7b80\u79f0": "name",
    "instrument_type": "instrument_type",
    "asset_type": "instrument_type",
    "exchange": "exchange",
    "\u4ea4\u6613\u6240": "exchange",
    "listed_date": "listed_date",
    "\u4e0a\u5e02\u65e5\u671f": "listed_date",
    "\u80a1\u7968\u4e0a\u5e02\u65e5\u671f": "listed_date",
    "\u57fa\u91d1\u4e0a\u5e02\u65e5\u671f": "listed_date",
    "delisted_date": "delisted_date",
    "\u9000\u5e02\u65e5\u671f": "delisted_date",
    "is_active": "is_active",
    "is_st": "is_st",
    "is_suspended": "is_suspended",
    "\u662f\u5426ST": "is_st",
    "\u662f\u5426\u505c\u724c": "is_suspended",
    "industry": "industry",
    "\u884c\u4e1a": "industry",
    "\u6240\u5c5e\u884c\u4e1a": "industry",
    "min_lot": "min_lot",
    "t_plus_rule": "t_plus_rule",
    "available_time": "available_time",
}


_UNIVERSE_FIELD_CANDIDATES = {
    "symbol": (
        "symbol",
        "code",
        "\u4ee3\u7801",
        "\u8bc1\u5238\u4ee3\u7801",
        "\u80a1\u7968\u4ee3\u7801",
        "\u57fa\u91d1\u4ee3\u7801",
    ),
    "name": (
        "name",
        "\u540d\u79f0",
        "\u7b80\u79f0",
        "\u8bc1\u5238\u7b80\u79f0",
        "\u80a1\u7968\u7b80\u79f0",
        "\u57fa\u91d1\u7b80\u79f0",
    ),
    "instrument_type": ("_akshare_instrument_type", "instrument_type", "asset_type"),
    "exchange": ("exchange", "\u4ea4\u6613\u6240"),
    "listed_date": (
        "listed_date",
        "\u4e0a\u5e02\u65e5\u671f",
        "\u80a1\u7968\u4e0a\u5e02\u65e5\u671f",
        "\u57fa\u91d1\u4e0a\u5e02\u65e5\u671f",
    ),
    "delisted_date": ("delisted_date", "\u9000\u5e02\u65e5\u671f"),
    "is_active": ("is_active",),
    "is_st": ("is_st", "\u662f\u5426ST"),
    "is_suspended": ("is_suspended", "\u662f\u5426\u505c\u724c"),
    "industry": ("industry", "\u884c\u4e1a", "\u6240\u5c5e\u884c\u4e1a"),
    "min_lot": ("min_lot",),
    "t_plus_rule": ("t_plus_rule",),
    "available_time": ("available_time",),
}


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
        "adapter_status": adapter_metadata.get("adapter_status", "SUCCESS"),
        "request": _request_metadata(normalized_request),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading": True,
        "no_broker_api": True,
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
        "as_of_date": request.as_of_date or "",
        "market_type": request.market_type or "",
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

    adapter_metadata = result.audit_metadata.get("adapter_metadata", {})
    return {
        "source": result.source,
        "dataset_type": result.dataset_type,
        "run_id": result.run_id,
        "row_count": result.row_count,
        "symbol": result.audit_metadata.get("request", {}).get("symbol", ""),
        "start_date": result.audit_metadata.get("request", {}).get("start_date", ""),
        "end_date": result.audit_metadata.get("request", {}).get("end_date", ""),
        "as_of_date": result.audit_metadata.get("request", {}).get("as_of_date", ""),
        "market_type": result.audit_metadata.get("request", {}).get("market_type", ""),
        "allow_real_data": bool(result.audit_metadata.get("request", {}).get("allow_real_data", False)),
        "adapter_status": result.audit_metadata.get("adapter_status", ""),
        "raw_columns": adapter_metadata.get("raw_columns", []),
        "normalized_columns": adapter_metadata.get("normalized_columns", []),
        "mapping_warnings": adapter_metadata.get("mapping_warnings", []),
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
        as_of_date=request.as_of_date,
        market_type=request.market_type,
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
        "as_of_date": request.as_of_date or "",
        "market_type": request.market_type or "",
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
