"""Exchange trading calendar helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


TRADING_CALENDAR_SCHEMA = [
    "trade_date",
    "is_trading_day",
    "session_open",
    "session_close",
    "decision_time",
    "reason",
]


@dataclass(frozen=True)
class TradingCalendar:
    """Trading-day lookup table backed by local calendar data."""

    frame: pd.DataFrame

    def __post_init__(self) -> None:
        missing = sorted(set(TRADING_CALENDAR_SCHEMA).difference(self.frame.columns))
        if missing:
            raise ValueError(f"Trading calendar missing required columns: {missing}")

    def is_trading_day(self, date: str | pd.Timestamp) -> bool:
        row = self._row_for(date)
        return bool(row["is_trading_day"])

    def assert_trading_day(self, date: str | pd.Timestamp) -> None:
        if not self.is_trading_day(date):
            day = _normalize_date(date)
            reason = self._row_for(day)["reason"]
            raise ValueError(f"{day.date()} is not a trading day: {reason}")

    def next_trading_day(self, date: str | pd.Timestamp) -> pd.Timestamp:
        day = _normalize_date(date)
        future = self.frame.loc[(self.frame["trade_date"] > day) & self.frame["is_trading_day"]]
        if future.empty:
            raise ValueError(f"No next trading day covered after {day.date()}")
        return pd.Timestamp(future.iloc[0]["trade_date"])

    def previous_trading_day(self, date: str | pd.Timestamp) -> pd.Timestamp:
        day = _normalize_date(date)
        previous = self.frame.loc[(self.frame["trade_date"] < day) & self.frame["is_trading_day"]]
        if previous.empty:
            raise ValueError(f"No previous trading day covered before {day.date()}")
        return pd.Timestamp(previous.iloc[-1]["trade_date"])

    def nth_next_trading_day(self, date: str | pd.Timestamp, n: int) -> pd.Timestamp:
        if n < 0:
            raise ValueError("n must be non-negative")
        day = _normalize_date(date)
        if n == 0:
            self.assert_trading_day(day)
            return day

        future = self.frame.loc[(self.frame["trade_date"] > day) & self.frame["is_trading_day"]]
        if len(future) < n:
            raise ValueError(f"No {n}th next trading day covered after {day.date()}")
        return pd.Timestamp(future.iloc[n - 1]["trade_date"])

    def nth_previous_trading_day(self, date: str | pd.Timestamp, n: int) -> pd.Timestamp:
        if n < 0:
            raise ValueError("n must be non-negative")
        day = _normalize_date(date)
        if n == 0:
            self.assert_trading_day(day)
            return day

        previous = self.frame.loc[(self.frame["trade_date"] < day) & self.frame["is_trading_day"]]
        if len(previous) < n:
            raise ValueError(f"No {n}th previous trading day covered before {day.date()}")
        return pd.Timestamp(previous.iloc[-n]["trade_date"])

    def decision_time_for(self, date: str | pd.Timestamp) -> pd.Timestamp:
        self.assert_trading_day(date)
        row = self._row_for(date)
        time_text = str(row["decision_time"]).strip()
        if not time_text:
            raise ValueError(f"Trading day {row['trade_date'].date()} is missing decision_time")
        return pd.Timestamp(f"{row['trade_date'].date()} {time_text}")

    def trading_days_between(self, start_date: str | pd.Timestamp, end_date: str | pd.Timestamp) -> list[pd.Timestamp]:
        start = _normalize_date(start_date)
        end = _normalize_date(end_date)
        if end < start:
            raise ValueError("end_date must be on or after start_date")
        days = self.frame.loc[
            (self.frame["trade_date"] >= start)
            & (self.frame["trade_date"] <= end)
            & self.frame["is_trading_day"],
            "trade_date",
        ]
        return [pd.Timestamp(day) for day in days]

    def _row_for(self, date: str | pd.Timestamp) -> pd.Series:
        day = _normalize_date(date)
        row = self.frame.loc[self.frame["trade_date"] == day]
        if row.empty:
            raise ValueError(f"{day.date()} is outside the loaded trading calendar")
        return row.iloc[0]


def load_trading_calendar(path: str | Path) -> TradingCalendar:
    """Load a local trading calendar CSV."""

    frame = pd.read_csv(path, keep_default_na=False)
    missing = sorted(set(TRADING_CALENDAR_SCHEMA).difference(frame.columns))
    if missing:
        raise ValueError(f"Trading calendar missing required columns: {missing}")

    frame["trade_date"] = pd.to_datetime(frame["trade_date"], errors="coerce").dt.normalize()
    if frame["trade_date"].isna().any():
        raise ValueError("Trading calendar contains missing or invalid trade_date values")

    frame["is_trading_day"] = _parse_bool_series(frame["is_trading_day"], "is_trading_day")
    for column in ["session_open", "session_close", "decision_time", "reason"]:
        frame[column] = frame[column].astype(str).str.strip()

    trading_days_missing_decision = frame.loc[frame["is_trading_day"] & (frame["decision_time"] == "")]
    if not trading_days_missing_decision.empty:
        dates = trading_days_missing_decision["trade_date"].dt.date.astype(str).tolist()
        raise ValueError(f"Trading days missing decision_time: {dates}")

    frame = frame.sort_values("trade_date").reset_index(drop=True)
    if frame["trade_date"].duplicated().any():
        duplicates = frame.loc[frame["trade_date"].duplicated(), "trade_date"].dt.date.astype(str).tolist()
        raise ValueError(f"Trading calendar contains duplicate trade_date values: {duplicates}")

    return TradingCalendar(frame=frame)


def is_trading_day(date: str | pd.Timestamp, calendar: TradingCalendar) -> bool:
    return calendar.is_trading_day(date)


def assert_trading_day(date: str | pd.Timestamp, calendar: TradingCalendar) -> None:
    calendar.assert_trading_day(date)


def next_trading_day(date: str | pd.Timestamp, calendar: TradingCalendar) -> pd.Timestamp:
    return calendar.next_trading_day(date)


def previous_trading_day(date: str | pd.Timestamp, calendar: TradingCalendar) -> pd.Timestamp:
    return calendar.previous_trading_day(date)


def nth_next_trading_day(date: str | pd.Timestamp, n: int, calendar: TradingCalendar) -> pd.Timestamp:
    return calendar.nth_next_trading_day(date, n)


def nth_previous_trading_day(date: str | pd.Timestamp, n: int, calendar: TradingCalendar) -> pd.Timestamp:
    return calendar.nth_previous_trading_day(date, n)


def decision_time_for(date: str | pd.Timestamp, calendar: TradingCalendar) -> pd.Timestamp:
    return calendar.decision_time_for(date)


def trading_days_between(
    start_date: str | pd.Timestamp,
    end_date: str | pd.Timestamp,
    calendar: TradingCalendar,
) -> list[pd.Timestamp]:
    return calendar.trading_days_between(start_date, end_date)


def _normalize_date(date: str | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(date)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_localize(None)
    return timestamp.normalize()


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
