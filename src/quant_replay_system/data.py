"""Point-in-time data contract and local CSV access helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


MARKET_DATA_SCHEMA = [
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

UNIVERSE_SNAPSHOT_SCHEMA = [
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

CORPORATE_ACTION_SCHEMA = [
    "symbol",
    "action_type",
    "ex_date",
    "record_date",
    "cash_dividend",
    "split_ratio",
    "rights_issue",
    "event_time",
    "publish_time",
    "ingest_time",
    "available_time",
    "revision_id",
    "source",
]

MARKET_TIMESTAMP_COLUMNS = ["event_time", "publish_time", "ingest_time", "available_time"]
CORPORATE_ACTION_TIMESTAMP_COLUMNS = ["event_time", "publish_time", "ingest_time", "available_time"]
MISSING_DATE_TOKENS = {"", "nan", "nat", "none", "null", "-", "--"}
SYMBOL_STRING_COLUMNS = {
    "symbol",
    "code",
    "ts_code",
    "证券代码",
    "股票代码",
    "基金代码",
    "代码",
}


@dataclass(frozen=True)
class ReplayDataset:
    """Point-in-time eligible data for a single replay decision."""

    as_of_date: pd.Timestamp
    decision_time: pd.Timestamp
    market_data: pd.DataFrame
    universe: pd.DataFrame
    corporate_actions: pd.DataFrame


def load_market_data(path: str | Path) -> pd.DataFrame:
    """Load local market data and validate the point-in-time schema."""

    frame = _read_contract_csv(
        path=path,
        required_columns=MARKET_DATA_SCHEMA,
        datetime_columns=MARKET_TIMESTAMP_COLUMNS,
        date_columns=["trade_date"],
        nullable_date_columns=[],
        bool_columns=["is_suspended"],
    )
    return frame.sort_values(["trade_date", "symbol", "available_time", "revision_id"]).reset_index(drop=True)


def load_price_data(path: str | Path) -> pd.DataFrame:
    """Backward-compatible alias for MVP code that still says price data."""

    return load_market_data(path)


def load_universe_snapshot(path: str | Path) -> pd.DataFrame:
    """Load local universe snapshots and validate the point-in-time schema."""

    frame = _read_contract_csv(
        path=path,
        required_columns=UNIVERSE_SNAPSHOT_SCHEMA,
        datetime_columns=["available_time"],
        date_columns=["as_of_date", "listed_date", "delisted_date"],
        nullable_date_columns=["listed_date", "delisted_date"],
        bool_columns=["is_active", "is_st", "is_suspended"],
    )
    return frame.sort_values(["as_of_date", "symbol", "available_time", "revision_id"]).reset_index(drop=True)


def load_corporate_actions(path: str | Path) -> pd.DataFrame:
    """Load local corporate actions and validate the point-in-time schema."""

    frame = _read_contract_csv(
        path=path,
        required_columns=CORPORATE_ACTION_SCHEMA,
        datetime_columns=CORPORATE_ACTION_TIMESTAMP_COLUMNS,
        date_columns=["ex_date", "record_date"],
        nullable_date_columns=[],
        bool_columns=["rights_issue"],
    )
    return frame.sort_values(["ex_date", "symbol", "available_time", "revision_id"]).reset_index(drop=True)


def decision_time_for_as_of_date(as_of_date: str | pd.Timestamp) -> pd.Timestamp:
    """Return the daily replay decision time: 15:30 local exchange time."""

    return _normalize_timestamp(as_of_date).normalize() + pd.Timedelta(hours=15, minutes=30)


def filter_available_records(df: pd.DataFrame, decision_time: str | pd.Timestamp) -> pd.DataFrame:
    """Keep only records whose available_time is at or before decision_time."""

    frame = _prepare_available_time_frame(df)
    cutoff = _normalize_timestamp(decision_time)
    return frame.loc[frame["available_time"] <= cutoff].copy().reset_index(drop=True)


def assert_no_future_leak(df: pd.DataFrame, decision_time: str | pd.Timestamp) -> None:
    """Raise if any record is unavailable at the replay decision time."""

    frame = _prepare_available_time_frame(df)
    cutoff = _normalize_timestamp(decision_time)
    future = frame.loc[frame["available_time"] > cutoff]
    if not future.empty:
        context_columns = [
            column
            for column in ["symbol", "trade_date", "as_of_date", "action_type", "ex_date", "available_time"]
            if column in future.columns
        ]
        examples = future[context_columns].head(5).to_dict("records")
        raise ValueError(
            f"Future data leak detected: {len(future)} records have available_time after "
            f"decision_time {cutoff}. Examples: {examples}"
        )


def build_replay_dataset(
    as_of_date: str | pd.Timestamp,
    decision_time: str | pd.Timestamp,
    market_data: pd.DataFrame,
    universe_snapshot: pd.DataFrame,
    corporate_actions: pd.DataFrame | None = None,
    *,
    exclude_st: bool = True,
    exclude_suspended: bool = True,
) -> ReplayDataset:
    """Build a deterministic point-in-time dataset for one replay decision."""

    as_of_timestamp = _normalize_timestamp(as_of_date).normalize()
    decision_timestamp = _normalize_timestamp(decision_time)

    market_data = normalize_symbol_column(market_data)
    universe_snapshot = normalize_symbol_column(universe_snapshot)

    market = filter_available_records(market_data, decision_timestamp)
    market = market.loc[market["trade_date"] <= as_of_timestamp].copy()
    market = _latest_revisions(market, ["symbol", "trade_date"])

    universe = filter_available_records(universe_snapshot, decision_timestamp)
    universe = normalize_optional_universe_dates_for_eligibility(universe)
    universe = universe.loc[universe["as_of_date"] <= as_of_timestamp].copy()
    universe = _latest_revisions(universe, ["symbol", "as_of_date"])
    universe = (
        universe.sort_values(["symbol", "as_of_date", "available_time", "revision_id"])
        .drop_duplicates(subset=["symbol"], keep="last")
        .reset_index(drop=True)
    )

    active_mask = (
        universe["is_active"]
        & optional_date_before_or_equal(universe["listed_date"], as_of_timestamp, missing_is_valid=True)
        & (universe["delisted_date"].isna() | (universe["delisted_date"] > as_of_timestamp))
    )
    if exclude_st:
        active_mask &= ~universe["is_st"]
    if exclude_suspended:
        active_mask &= ~universe["is_suspended"]
    universe = universe.loc[active_mask].sort_values("symbol").reset_index(drop=True)

    eligible_symbols = set(universe["symbol"])
    market = market.loc[market["symbol"].isin(eligible_symbols)].sort_values(["trade_date", "symbol"]).reset_index(drop=True)

    if corporate_actions is None:
        actions = pd.DataFrame(columns=CORPORATE_ACTION_SCHEMA)
    else:
        corporate_actions = normalize_symbol_column(corporate_actions)
        actions = filter_available_records(corporate_actions, decision_timestamp)
        actions = actions.loc[
            (actions["symbol"].isin(eligible_symbols)) & (actions["ex_date"] <= as_of_timestamp)
        ].copy()
        actions = _latest_revisions(actions, ["symbol", "action_type", "ex_date", "record_date"])
        actions = actions.sort_values(["ex_date", "symbol", "action_type"]).reset_index(drop=True)

    for frame in [market, universe, actions]:
        assert_no_future_leak(frame, decision_timestamp)

    return ReplayDataset(
        as_of_date=as_of_timestamp,
        decision_time=decision_timestamp,
        market_data=market,
        universe=universe,
        corporate_actions=actions,
    )


def point_in_time_prices(prices: pd.DataFrame, decision_date: str | pd.Timestamp) -> pd.DataFrame:
    """Return market rows available by the daily replay decision time."""

    as_of_timestamp = _normalize_timestamp(decision_date).normalize()
    decision_time = decision_time_for_as_of_date(as_of_timestamp)
    frame = filter_available_records(prices, decision_time)
    date_column = "trade_date" if "trade_date" in frame.columns else "date"
    return frame.loc[frame[date_column] <= as_of_timestamp].copy().reset_index(drop=True)


def _read_contract_csv(
    path: str | Path,
    required_columns: Iterable[str],
    datetime_columns: Iterable[str],
    date_columns: Iterable[str],
    nullable_date_columns: Iterable[str],
    bool_columns: Iterable[str],
) -> pd.DataFrame:
    frame = read_csv_preserve_symbol_columns(path)
    _require_columns(frame, required_columns)
    frame = normalize_symbol_column(frame)

    for column in datetime_columns:
        frame[column] = _parse_timestamp_series(frame[column])
        if frame[column].isna().any():
            raise ValueError(f"{column} contains missing or invalid timestamps")

    nullable_dates = set(nullable_date_columns)
    for column in date_columns:
        if column in nullable_dates:
            frame[column] = parse_optional_universe_date(frame[column], column)
        else:
            frame[column] = _parse_timestamp_series(frame[column]).dt.normalize()
        if column not in nullable_dates and frame[column].isna().any():
            raise ValueError(f"{column} contains missing or invalid dates")

    for column in bool_columns:
        frame[column] = _parse_bool_series(frame[column], column)

    _validate_available_time(frame)
    return frame


def read_csv_preserve_symbol_columns(path: str | Path, **kwargs) -> pd.DataFrame:
    """Read CSVs with symbol-like columns as strings so leading zeros survive."""

    dtype = dict(kwargs.pop("dtype", {}) or {})
    for column in SYMBOL_STRING_COLUMNS:
        dtype.setdefault(column, str)
    return pd.read_csv(path, dtype=dtype, **kwargs)


def normalize_symbol_column(frame: pd.DataFrame, column: str = "symbol") -> pd.DataFrame:
    """Normalize a symbol column without mutating the input frame."""

    output = frame.copy(deep=True)
    if column in output.columns:
        output[column] = normalize_symbol_series(output[column])
    return output


def normalize_symbol_series(series: pd.Series) -> pd.Series:
    """Normalize China market symbol values while preserving significant zeros."""

    return series.map(normalize_symbol_value)


def normalize_symbol_value(value: object) -> str:
    """Return a stable string symbol, padding numeric China symbols to six digits."""

    if _is_missing_date_token(value):
        return ""
    text = str(value).strip().upper()
    if not text:
        return ""
    if re_match := re.match(r"^(\d+)\.0+$", text):
        text = re_match.group(1)
    if "." in text:
        code, suffix = text.split(".", 1)
        if code.isdigit() and 0 < len(code) <= 6 and suffix and not suffix.isdigit():
            return f"{code.zfill(6)}.{suffix}"
        return text
    if text.isdigit() and 0 < len(text) <= 6:
        return text.zfill(6)
    return text


def normalize_optional_universe_dates_for_eligibility(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize optional universe date columns before point-in-time eligibility checks."""

    output = frame.copy()
    for column in ["listed_date", "delisted_date"]:
        if column in output.columns:
            output[column] = parse_optional_universe_date(output[column], column)
    return output


def optional_date_before_or_equal(
    series: pd.Series,
    timestamp: str | pd.Timestamp,
    *,
    missing_is_valid: bool = False,
) -> pd.Series:
    """Return a mask for optional dates at or before a timestamp."""

    parsed = parse_optional_universe_date(series, getattr(series, "name", "optional_date"))
    mask = parsed <= _normalize_timestamp(timestamp).normalize()
    if missing_is_valid:
        mask = mask | parsed.isna()
    return mask.fillna(False)


def parse_optional_universe_date(series: pd.Series, column: str) -> pd.Series:
    """Parse an optional universe date column and reject invalid non-empty tokens."""

    missing = series.map(_is_missing_date_token)
    parse_input = series.where(~missing, pd.NA)
    parsed = _parse_timestamp_series(parse_input).dt.normalize()
    invalid = parsed.isna() & ~missing
    if invalid.any():
        examples = sorted({str(value) for value in series.loc[invalid].head(5)})
        raise ValueError(f"{column} contains invalid non-empty universe dates: {examples}")
    return parsed


def _is_missing_date_token(value: object) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip().lower() in MISSING_DATE_TOKENS


def _require_columns(frame: pd.DataFrame, required_columns: Iterable[str]) -> None:
    missing = sorted(set(required_columns).difference(frame.columns))
    if missing:
        raise ValueError(f"Data contract violation: missing required columns {missing}")


def _prepare_available_time_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    if "available_time" not in frame.columns:
        raise ValueError("Data contract violation: missing required available_time column")
    frame["available_time"] = _parse_timestamp_series(frame["available_time"])
    _validate_available_time(frame)
    return frame


def _validate_available_time(frame: pd.DataFrame) -> None:
    if "available_time" not in frame.columns:
        raise ValueError("Data contract violation: missing required available_time column")
    if frame["available_time"].isna().any():
        raise ValueError("Data contract violation: available_time contains missing values")


def _parse_timestamp_series(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    if hasattr(parsed.dt, "tz") and parsed.dt.tz is not None:
        parsed = parsed.dt.tz_localize(None)
    return parsed


def _normalize_timestamp(value: str | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_localize(None)
    return timestamp


def _parse_bool_series(series: pd.Series, column: str) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series

    normalized = series.astype(str).str.strip().str.lower()
    true_values = {"true", "1", "yes", "y"}
    false_values = {"false", "0", "no", "n"}
    valid_values = true_values | false_values
    invalid = sorted(set(normalized.loc[~normalized.isin(valid_values)]))
    if invalid:
        raise ValueError(f"{column} contains invalid boolean values: {invalid}")
    return normalized.isin(true_values)


def _latest_revisions(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if frame.empty:
        return frame.copy().reset_index(drop=True)

    sort_columns = [column for column in [*keys, "available_time", "revision_id"] if column in frame.columns]
    return (
        frame.sort_values(sort_columns)
        .drop_duplicates(subset=keys, keep="last")
        .reset_index(drop=True)
    )
