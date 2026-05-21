"""Forward performance evaluation placeholders."""

from __future__ import annotations

import pandas as pd


def evaluate_forward_return(executions: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """Compute a simple last-available close return after execution."""

    if executions.empty:
        return executions.assign(forward_return=pd.Series(dtype="float64"))

    date_column = "trade_date" if "trade_date" in prices.columns else "date"
    latest_close = (
        prices.sort_values(["symbol", date_column])
        .groupby("symbol", as_index=False)
        .tail(1)[["symbol", "close"]]
        .rename(columns={"close": "future_close"})
    )
    evaluated = executions.merge(latest_close, on="symbol", how="left")
    evaluated["forward_return"] = evaluated["future_close"] / evaluated["execution_price"] - 1.0
    return evaluated
