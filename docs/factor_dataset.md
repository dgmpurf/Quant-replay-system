# Factor Dataset Builder v0.1

The factor dataset is the research table between raw point-in-time data and future scoring logic. It produces one row per eligible symbol for a replay decision date.

## Purpose

For a decision date `T`, the builder combines:

- eligible universe snapshot rows,
- market rows available at or before `decision_time`,
- technical indicators,
- benchmark-relative features when benchmark data is supplied,
- basic decision-date execution precheck fields,
- point-in-time audit columns.

The output is meant for explainable scoring and later calibration. It is not a final trading signal and does not perform live trading.

## Point-in-Time Safety

The builder reuses existing project rules instead of implementing its own shortcut:

- `build_replay_dataset(...)` handles universe and market eligibility.
- `compute_technical_indicators(..., decision_time=...)` filters records by `available_time <= decision_time`.
- Future market revisions and future universe snapshots are excluded.
- Benchmark data, if supplied, is also filtered by `available_time <= decision_time`.

## Output Grain

One row per:

```text
decision_date, symbol
```

Default config excludes inactive, ST, and suspended symbols. ST and suspended symbols can be included explicitly for research diagnostics.

Universe listing dates are handled conservatively:

- missing `listed_date` means the listing date is unknown, not automatically invalid,
- present `listed_date` values after the decision date keep the symbol ineligible,
- present `delisted_date` values on or before the decision date keep the symbol ineligible,
- `is_active`, ST/suspension flags, `available_time`, `as_of_date`, and revision ordering still apply.

Invalid non-empty optional universe dates should have been rejected by ingestion. If such a value appears in already-processed data, the factor path raises a clear optional-date validation error instead of continuing ambiguously.

Symbols are normalized before market/universe eligibility joins. Leading zeros are significant and preserved: `000001`, `510300`, and `159915` are treated as string identifiers, not numbers. A market symbol must have matching universe coverage after normalization. For example, ETF market data for `510300` requires a universe row with `symbol=510300`, normally with `instrument_type=ETF`; a stock-only universe will leave the factor dataset empty for that ETF.

## Main Columns

Universe columns include:

```text
decision_date, decision_time, symbol, name, instrument_type, exchange,
industry, is_active, is_st, is_suspended, min_lot, t_plus_rule
```

Market columns include:

```text
close, open, high, low, volume, amount, pre_close, limit_up, limit_down, adj_factor
```

Technical columns include:

```text
ma5, ma10, ma20, ma60, macd_dif, macd_dea, macd_hist,
rsi14, atr14, volume_ma5, volume_ma10, volume_ma20, volume_ratio_20,
rel_return_5, rel_return_10, rel_return_20
```

Audit and eligibility columns include:

```text
latest_market_available_time, universe_available_time, data_revision_id, source,
universe_eligible, market_data_available, execution_data_available,
risk_precheck_status, risk_precheck_reason
```

## Configuration

Default settings:

```yaml
factor_dataset:
  exclude_st: true
  exclude_suspended: true
  require_market_data: true
  include_technical_score: true
```

`technical_score_v01` is optional and remains separate from final scoring.

## Known MVP Limitations

- Execution precheck uses decision-date available market fields only; it does not use future T+1 open data as a factor.
- No portfolio, cash, or position sizing is included.
- No machine learning or final score is included.
- Relative strength assumes one benchmark series aligned by `trade_date`.
- Rolling indicator windows count available rows, consistent with Technical Indicators v0.1.
- Missing universe `listed_date` values are treated as unknown listing dates; this supports vendor snapshots with incomplete listing-date coverage, but users should still review universe quality before research use.
- ETF rows are preserved when present, but missing ETF universe coverage is not inferred from market data.
