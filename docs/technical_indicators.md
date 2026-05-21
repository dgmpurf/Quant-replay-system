# Technical Indicators v0.1

Technical Indicators v0.1 adds point-in-time-safe timing features for ETF and stock replay. These indicators are research inputs, not direct profit predictions and not final scoring logic.

## Implemented Indicators

Moving averages:

- `ma5`
- `ma10`
- `ma20`
- `ma60`

MACD:

- `macd_dif`: fast EMA minus slow EMA
- `macd_dea`: signal line
- `macd_histogram`: DIF minus DEA

Defaults are fast `12`, slow `26`, and signal `9`.

RSI:

- `rsi_14` by default
- Values are clipped between `0` and `100`

ATR:

- `atr_14` by default
- Uses high, low, close, and previous close
- Values are non-negative

Volume:

- `volume_ma5`
- `volume_ma10`
- `volume_ma20`
- `volume_ratio_20 = volume / volume_ma20`

Relative strength:

- `return_5d`, `return_10d`, `return_20d`
- `benchmark_return_5d`, `benchmark_return_10d`, `benchmark_return_20d`
- `relative_return_5d`, `relative_return_10d`, `relative_return_20d`

## Point-in-Time Filtering

`compute_technical_indicators(df, decision_time=...)` calls the existing `filter_available_records` function before any indicator is calculated.

The rule is unchanged:

```text
available_time <= decision_time
```

Rows that became available after the replay decision time are excluded and cannot affect rolling windows, EMA values, benchmark returns, or technical score helpers.

## TechnicalScore v0.1

`compute_technical_score(indicator_df)` is an optional helper and is not wired into final scoring.

The MVP helper rewards:

- `close > ma20`
- `ma5 > ma20`
- `volume_ratio_20 > 1.2`

It penalizes:

- `rsi_14 > 80`
- `close < ma20`

This is intentionally simple so later strategy scoring can decide whether to use it.

## Known MVP Limitations

- Rolling windows count available rows, not official trading-calendar sessions.
- EMA uses pandas `ewm` defaults with `adjust=False`.
- RSI uses a simple rolling average, not Wilder smoothing.
- ATR uses a simple rolling mean of true range.
- Relative strength assumes one benchmark series and aligns by `trade_date`.
- Indicators support timing and regime context; they should not be treated as standalone predictions.
