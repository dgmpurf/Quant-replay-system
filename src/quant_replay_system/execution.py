"""T+1 execution rules and eligibility checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from quant_replay_system.calendar import TradingCalendar
from quant_replay_system.config import ExecutionSettings


PASS = "PASS"
WARN = "WARN"
BLOCK = "BLOCK"
BUY = "BUY"
SELL = "SELL"


@dataclass(frozen=True)
class ExecutionEligibility:
    status: str
    reason: str
    execution_date: pd.Timestamp
    side: str
    symbol: str


def get_buy_execution_date(signal_date: str | pd.Timestamp, calendar: TradingCalendar) -> pd.Timestamp:
    """A signal after close on T executes on the next trading day."""

    return calendar.next_trading_day(signal_date)


def get_sellable_date(buy_date: str | pd.Timestamp, calendar: TradingCalendar) -> pd.Timestamp:
    """China A-share T+1 rule: positions become sellable next trading day."""

    return calendar.next_trading_day(buy_date)


def get_planned_sell_date(
    buy_date: str | pd.Timestamp,
    holding_horizon: int,
    calendar: TradingCalendar,
) -> pd.Timestamp:
    """Return the sell date after holding_horizon trading days."""

    if holding_horizon <= 0:
        raise ValueError("holding_horizon must be positive")
    return calendar.nth_next_trading_day(buy_date, holding_horizon)


def is_position_sellable(
    position_buy_date: str | pd.Timestamp,
    current_date: str | pd.Timestamp,
    calendar: TradingCalendar,
) -> bool:
    """Return whether a position bought on buy_date is sellable on current_date."""

    sellable_date = get_sellable_date(position_buy_date, calendar)
    current = _normalize_date(current_date)
    return current >= sellable_date


def check_execution_eligibility(
    symbol: str,
    execution_date: str | pd.Timestamp,
    side: str,
    market_data: pd.DataFrame,
    calendar: TradingCalendar,
    *,
    block_buy_on_limit_up: bool = True,
    block_sell_on_limit_down: bool = True,
) -> ExecutionEligibility:
    """Check whether a buy or sell can execute at the open."""

    normalized_side = side.upper()
    if normalized_side not in {BUY, SELL}:
        raise ValueError("side must be BUY or SELL")

    execution_timestamp = _normalize_date(execution_date)
    calendar.assert_trading_day(execution_timestamp)
    row = _market_row_for(symbol, execution_timestamp, market_data)

    if row is None:
        return ExecutionEligibility(BLOCK, "missing market data", execution_timestamp, normalized_side, symbol)
    if bool(row.get("is_suspended", False)):
        return ExecutionEligibility(BLOCK, "symbol suspended on execution date", execution_timestamp, normalized_side, symbol)

    open_price = row.get("open")
    if pd.isna(open_price):
        return ExecutionEligibility(BLOCK, "missing open price", execution_timestamp, normalized_side, symbol)

    limit_up = row.get("limit_up")
    limit_down = row.get("limit_down")
    if normalized_side == BUY and block_buy_on_limit_up and pd.notna(limit_up) and float(open_price) >= float(limit_up):
        return ExecutionEligibility(BLOCK, "limit-up open blocks buy", execution_timestamp, normalized_side, symbol)
    if normalized_side == SELL and block_sell_on_limit_down and pd.notna(limit_down) and float(open_price) <= float(limit_down):
        return ExecutionEligibility(BLOCK, "limit-down open blocks sell", execution_timestamp, normalized_side, symbol)

    return ExecutionEligibility(PASS, "eligible", execution_timestamp, normalized_side, symbol)


def simulate_t_plus_1_execution(
    candidates: pd.DataFrame,
    prices: pd.DataFrame,
    decision_date: str | pd.Timestamp,
    settings: ExecutionSettings,
    calendar: TradingCalendar | None = None,
) -> pd.DataFrame:
    """Simulate T+1 buy execution and planned sell execution."""

    if candidates.empty:
        return candidates.assign(execution_date=pd.NaT, execution_price=pd.Series(dtype="float64"))

    if calendar is None:
        return _simulate_without_calendar(candidates, prices, decision_date, settings)

    signal_date = _normalize_date(decision_date)
    buy_date = get_buy_execution_date(signal_date, calendar)
    holding_horizon = settings.default_holding_horizon_trading_days
    slippage_bps = _effective_slippage_bps(settings)
    rows: list[dict[str, Any]] = []

    for candidate in candidates.to_dict("records"):
        symbol = str(candidate["symbol"])
        row = dict(candidate)
        row.update(
            {
                "signal_date": signal_date,
                "execution_date": buy_date,
                "buy_date": buy_date,
                "buy_status": None,
                "buy_reason": None,
                "buy_price": pd.NA,
                "execution_price": pd.NA,
                "sellable_date": pd.NaT,
                "planned_sell_date": pd.NaT,
                "sell_date": pd.NaT,
                "sell_status": None,
                "sell_reason": None,
                "sell_price": pd.NA,
                "sell_delay_trading_days": pd.NA,
                "sell_attempts": [],
                "trade_status": None,
            }
        )

        buy_check = check_execution_eligibility(
            symbol,
            buy_date,
            BUY,
            prices,
            calendar,
            block_buy_on_limit_up=settings.block_buy_on_limit_up,
            block_sell_on_limit_down=settings.block_sell_on_limit_down,
        )
        row["buy_status"] = buy_check.status
        row["buy_reason"] = buy_check.reason

        if buy_check.status == BLOCK:
            row["trade_status"] = "SKIPPED_BUY"
            rows.append(row)
            continue

        buy_market_row = _market_row_for(symbol, buy_date, prices)
        buy_open = float(buy_market_row["open"])
        buy_price = buy_open * (1.0 + slippage_bps / 10_000.0)
        sellable_date = get_sellable_date(buy_date, calendar)
        planned_sell_date = get_planned_sell_date(buy_date, holding_horizon, calendar)
        row["buy_price"] = buy_price
        row["execution_price"] = buy_price
        row["sellable_date"] = sellable_date
        row["planned_sell_date"] = planned_sell_date

        sell_result = _simulate_sell_with_delay(
            symbol=symbol,
            planned_sell_date=planned_sell_date,
            prices=prices,
            calendar=calendar,
            settings=settings,
            slippage_bps=slippage_bps,
        )
        row.update(sell_result)
        rows.append(row)

    return pd.DataFrame(rows)


def _simulate_without_calendar(
    candidates: pd.DataFrame,
    prices: pd.DataFrame,
    decision_date: str | pd.Timestamp,
    settings: ExecutionSettings,
) -> pd.DataFrame:
    """Fallback used by callers that have not loaded a calendar."""

    date_column = "trade_date" if "trade_date" in prices.columns else "date"
    cutoff = pd.Timestamp(decision_date).normalize()
    future_dates = sorted(prices.loc[prices[date_column] > cutoff, date_column].unique())
    if not future_dates:
        return candidates.assign(execution_date=pd.NaT, execution_price=pd.NA)

    execution_date = future_dates[0]
    execution_rows = prices.loc[prices[date_column] == execution_date, ["symbol", settings.price_field]].copy()
    execution_rows = execution_rows.drop_duplicates(subset=["symbol"], keep="last")
    execution_rows = execution_rows.rename(columns={settings.price_field: "execution_price"})

    filled = candidates.merge(execution_rows, on="symbol", how="left")
    filled["execution_date"] = execution_date
    slippage_bps = _effective_slippage_bps(settings)
    if slippage_bps:
        filled["execution_price"] = filled["execution_price"] * (1.0 + slippage_bps / 10_000.0)
    return filled


def _simulate_sell_with_delay(
    symbol: str,
    planned_sell_date: pd.Timestamp,
    prices: pd.DataFrame,
    calendar: TradingCalendar,
    settings: ExecutionSettings,
    slippage_bps: float,
) -> dict[str, Any]:
    current_sell_date = planned_sell_date
    attempts: list[dict[str, Any]] = []

    for delay in range(settings.max_exit_delay_trading_days + 1):
        sell_check = check_execution_eligibility(
            symbol,
            current_sell_date,
            SELL,
            prices,
            calendar,
            block_buy_on_limit_up=settings.block_buy_on_limit_up,
            block_sell_on_limit_down=settings.block_sell_on_limit_down,
        )
        attempts.append(asdict(sell_check))
        if sell_check.status == PASS:
            sell_market_row = _market_row_for(symbol, current_sell_date, prices)
            sell_open = float(sell_market_row["open"])
            sell_price = sell_open * (1.0 - slippage_bps / 10_000.0)
            return {
                "sell_date": current_sell_date,
                "sell_status": sell_check.status,
                "sell_reason": sell_check.reason,
                "sell_price": sell_price,
                "sell_delay_trading_days": delay,
                "sell_attempts": attempts,
                "trade_status": "FILLED",
            }

        if delay == settings.max_exit_delay_trading_days:
            return {
                "sell_date": current_sell_date,
                "sell_status": sell_check.status,
                "sell_reason": sell_check.reason,
                "sell_price": pd.NA,
                "sell_delay_trading_days": delay,
                "sell_attempts": attempts,
                "trade_status": "EXIT_BLOCKED",
            }

        current_sell_date = calendar.next_trading_day(current_sell_date)

    raise RuntimeError("unreachable sell-delay branch")


def _market_row_for(
    symbol: str,
    execution_date: str | pd.Timestamp,
    market_data: pd.DataFrame,
) -> pd.Series | None:
    date_column = "trade_date" if "trade_date" in market_data.columns else "date"
    execution_timestamp = _normalize_date(execution_date)
    rows = market_data.loc[
        (market_data["symbol"] == symbol) & (market_data[date_column] == execution_timestamp)
    ]
    if rows.empty:
        return None

    sort_columns = [column for column in ["available_time", "revision_id"] if column in rows.columns]
    if sort_columns:
        rows = rows.sort_values(sort_columns)
    return rows.iloc[-1]


def _normalize_date(date: str | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(date)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_localize(None)
    return timestamp.normalize()


def _effective_slippage_bps(settings: ExecutionSettings) -> float:
    return settings.slippage_bps if settings.slippage_bps else settings.default_slippage_bps
