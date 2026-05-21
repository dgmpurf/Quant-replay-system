# Trading Calendar and T+1 Execution v0.1

Historical replay must use exchange trading days, not calendar days. Weekends, holidays, suspensions, and price-limit opens can change whether a signal can actually be executed.

## Trading Calendar

The mock calendar lives at `data/mock/trading_calendar.csv` with:

```text
trade_date, is_trading_day, session_open, session_close, decision_time, reason
```

`next_trading_day(date)` returns the next valid trading day after `date`, skipping weekends and holidays marked as non-trading days. `decision_time_for(date)` returns the configured replay decision time for a trading day and raises for weekends or holidays.

## T+1 Buy Date

A signal generated after the close on signal date `T` executes on:

```text
buy_date = next_trading_day(signal_date)
```

This prevents a Friday signal from incorrectly executing on Saturday, and it prevents a pre-holiday signal from executing on a closed market day.

## T+1 Sellable Date

For China A-share T+1 behavior, units bought on `buy_date` become sellable on:

```text
sellable_date = next_trading_day(buy_date)
```

A position bought today is not sellable today.

## Holding Horizon

Holding horizon is counted in trading days:

```text
planned_sell_date = nth_next_trading_day(buy_date, holding_horizon_trading_days)
```

For example, a one-trading-day horizon from a Friday buy date sells on the next Monday if the weekend is closed.

## Execution Eligibility

At the execution open, replay checks `is_suspended`, `open`, `limit_up`, and `limit_down`.

Buy is blocked when:

- the symbol is suspended,
- the open price is missing,
- `open >= limit_up` and limit-up buy blocking is enabled.

Sell is blocked when:

- the symbol is suspended,
- the open price is missing,
- `open <= limit_down` and limit-down sell blocking is enabled.

Blocked buys are skipped with a reason. Blocked sells are retried on the next trading day until the configured `max_exit_delay_trading_days` is reached.

## MVP Limitations

- The calendar is a local mock CSV, not an official exchange feed.
- Intraday execution windows are not modeled.
- Price-limit logic uses the open only.
- Partial fills are not modeled.
- Delayed exits use a simple retry loop without portfolio-level risk handling.
