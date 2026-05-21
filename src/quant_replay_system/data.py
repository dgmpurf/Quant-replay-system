"""Point-in-time data contract and local CSV access helpers."""

from __future__ import annotations

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
        nullable_date_columns=["delisted_date"],
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

    market = filter_available_records(market_data, decision_timestamp)
    market = market.loc[market["trade_date"] <= as_of_timestamp].copy()
    market = _latest_revisions(market, ["symbol", "trade_date"])

    universe = filter_available_records(universe_snapshot, decision_timestamp)
    universe = universe.loc[universe["as_of_date"] <= as_of_timestamp].copy()
    universe = _latest_revisions(universe, ["symbol", "as_of_date"])
    universe = (
        universe.sort_values(["symbol", "as_of_date", "available_time", "revision_id"])
        .drop_duplicates(subset=["symbol"], keep="last")
        .reset_index(drop=True)
    )

    active_mask = (
        universe["is_active"]
        & (universe["listed_date"] <= as_of_timestamp)
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
    frame = pd.read_csv(path)
    _require_columns(frame, required_columns)

    for column in datetime_columns:
        frame[column] = _parse_timestamp_series(frame[column])
        if frame[column].isna().any():
            raise ValueError(f"{column} contains missing or invalid timestamps")

    nullable_dates = set(nullable_date_columns)
    for column in date_columns:
        frame[column] = _parse_timestamp_series(frame[column]).dt.normalize()
        if column not in nullable_dates and frame[column].isna().any():
            raise ValueError(f"{column} contains missing or invalid dates")

    for column in bool_columns:
        frame[column] = _parse_bool_series(frame[column], column)

    _validate_available_time(frame)
    return frame


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
