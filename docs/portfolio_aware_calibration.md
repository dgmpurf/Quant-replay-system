# Portfolio-Aware Batch Replay and Calibration v0.1

Portfolio-aware replay adds account-level simulation metrics to Batch Replay and Parameter Calibration.

It does not change point-in-time filtering, trading calendar logic, T+1 execution rules, technical indicators, scoring formulas, or replay execution outcomes. It only consumes existing replay outputs and links them to portfolio-level ledgers and metrics.

## Why Trade-Level Returns Are Not Enough

Trade-level replay metrics answer whether individual selected candidates would have made or lost money.

They do not answer account-level questions:

- Was there enough cash to take all trades?
- Did lot rounding prevent small trades?
- How much capital was actually deployed?
- What was the drawdown of the account?
- Was turnover too high?
- Did a parameter set look good only because it ignored sizing constraints?

Portfolio-aware metrics help compare parameter sets more realistically.

## Portfolio Metrics Used

Batch Replay can run `simulate_portfolio(...)` after collecting replay runs.

When enabled, batch outputs include:

- `portfolio_initial_cash`
- `portfolio_final_equity`
- `portfolio_total_return`
- `portfolio_max_drawdown`
- `portfolio_turnover`
- `portfolio_average_gross_exposure`
- `portfolio_max_gross_exposure`
- `portfolio_cash_utilization`
- `portfolio_number_of_trades`
- `portfolio_number_of_positions`
- `portfolio_skipped_trades`

Batch artifacts also link to portfolio files:

- `portfolio_report_path`
- `trade_ledger_path`
- `position_ledger_path`
- `cash_ledger_path`
- `equity_curve_path`
- `portfolio_metrics_path`

## Batch Replay Integration

Batch Replay runs the normal replay workflow for each decision date.

If portfolio simulation is enabled, it then runs one portfolio simulation across the full batch result. This avoids duplicating portfolio artifacts per replay date and keeps one account-level equity curve for the batch.

The batch report includes a portfolio performance section, and `metadata.json` records whether portfolio simulation was enabled.

## Portfolio-Aware Calibration Objective

Calibration can rank parameter sets using portfolio metrics.

The MVP portfolio-aware objective is:

```text
portfolio_objective_score =
  0.35 * normalized_portfolio_total_return
- 0.20 * normalized_max_drawdown_penalty
+ 0.15 * normalized_win_rate
+ 0.10 * normalized_cash_utilization
- 0.10 * normalized_turnover_penalty
- 0.10 * low_trade_count_penalty
```

The ranked output keeps both:

- `objective_score`: the existing trade-level objective
- `portfolio_objective_score`: the account-level objective
- `ranking_score`: the score actually used for sorting
- `objective_metric_mode_used`: `portfolio_aware` or `trade_level_fallback`

## Fallback Behavior

If portfolio metrics are requested but unavailable, calibration falls back to the existing trade-level objective.

The fallback is recorded through:

- `objective_metric_mode_used = trade_level_fallback`
- calibration warnings
- metadata fields

This keeps older batch outputs readable and avoids blocking research when portfolio artifacts are missing.

## Configuration

Batch replay fields:

```yaml
batch_replay:
  enable_portfolio_simulation: true
  portfolio_initial_cash: 10000
  portfolio_max_gross_exposure: 0.60
  portfolio_max_position_weight: 0.20
  portfolio_reserve_cash_pct: 0.40
```

Calibration fields:

```yaml
calibration:
  use_portfolio_metrics: true
  objective_metric_mode: portfolio_aware
```

## Known MVP Limitations

- Uses local CSV/mock data only.
- Portfolio simulation is equal-weight only.
- Portfolio metrics are research approximations, not broker reconciliation.
- Calibration still uses explicit small grids.
- Walk-forward validation is not enforced yet.
- Corporate actions and dividends are not modeled in portfolio accounting.
- No live trading or broker API integration is implemented.
