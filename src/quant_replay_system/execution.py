"""Execution simulation placeholders."""

from __future__ import annotations

import pandas as pd

from quant_replay_system.config import ExecutionSettings


def simulate_t_plus_1_execution(
    candidates: pd.DataFrame,
    prices: pd.DataFrame,
    decision_date: str | pd.Timestamp,
    settings: ExecutionSettings,
) -> pd.DataFrame:
    """Attach next-trading-day execution prices to selected candidates."""

    if candidates.empty:
        return candidates.assign(execution_date=pd.NaT, execution_price=pd.Series(dtype="float64"))

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
    if settings.slippage_bps:
        filled["execution_price"] = filled["execution_price"] * (1.0 + settings.slippage_bps / 10_000.0)
    return filled
