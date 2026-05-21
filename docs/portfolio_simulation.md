# Portfolio Simulation v0.1

Portfolio Simulation turns replay-level trade outcomes into account-level research ledgers.

Replay answers: "Would this candidate have bought and sold under the replay rules?"

Portfolio simulation answers: "What would an account-level equity curve look like after sizing, cash constraints, fees, slippage, and mark-to-market valuation?"

## Purpose

The module consumes existing replay outputs. It does not change:

- point-in-time filtering,
- trading calendar logic,
- T+1 execution rules,
- technical indicators,
- score formulas,
- candidate selection formulas.

It does not place orders or call broker APIs.

## Equal-Weight Sizing

MVP sizing uses `equal_weight`.

For each buy date, the simulator:

1. Computes current equity.
2. Applies `reserve_cash_pct`.
3. Applies `max_gross_exposure`.
4. Divides deployable capital across replay-filled candidates.
5. Caps each position by `max_position_weight`.
6. Rounds down to `lot_size` when `round_lots=true`.
7. Skips trades whose quantity becomes zero after lot rounding.
8. Prevents negative cash by default.

Skipped or blocked replay trades do not open positions.

## Cash Ledger

The cash ledger records daily cash movement:

- `date`
- `starting_cash`
- `trade_cash_flow`
- `fees`
- `taxes`
- `ending_cash`

Cash reconciliation is:

```text
ending_cash = starting_cash + trade_cash_flow - fees - taxes
```

## Trade Ledger

The trade ledger records simulated account-level buy and sell rows:

- `trade_id`
- `decision_date`
- `symbol`
- `side`
- `order_date`
- `execution_date`
- `execution_price`
- `quantity`
- `gross_notional`
- `fees`
- `taxes`
- `slippage`
- `net_cash_flow`
- `status`
- `reason`

Replay-blocked trades are preserved as skipped ledger rows for auditability.

## Position Ledger

The position ledger records end-of-day position state:

- `date`
- `symbol`
- `quantity`
- `average_cost`
- `market_price`
- `market_value`
- `unrealized_pnl`
- `realized_pnl`
- `status`

Closed positions are recorded on the sell date with realized PnL.

## Equity Curve

The equity curve records:

- `date`
- `cash`
- `market_value`
- `total_equity`
- `daily_return`
- `drawdown`

When `mark_to_market=true`, open positions are valued using local market close prices on or before each ledger date.

## Portfolio Metrics

MVP metrics include:

- initial cash,
- final equity,
- total return,
- annualized return when enough dates exist,
- max drawdown,
- win rate,
- average/median/best/worst trade return,
- turnover,
- average and maximum gross exposure,
- cash utilization,
- number of trades,
- number of positions,
- skipped trades caused by cash or lot constraints.

## Artifacts

Default output path:

```text
outputs/reports/portfolio_simulations/<portfolio_run_id>/
  portfolio_report.md
  trade_ledger.csv
  position_ledger.csv
  cash_ledger.csv
  equity_curve.csv
  portfolio_metrics.csv
  metadata.json
```

The `portfolio_run_id` is deterministic from source replay IDs when available, symbols, decision dates, and portfolio settings.

## Known MVP Limitations

- Uses local CSV/mock data only.
- Equal-weight sizing is the only sizing method.
- Multiple overlapping lots in the same symbol are simplified.
- Corporate actions, dividends, and financing are not modeled.
- Tax handling is a simple basis-points estimate.
- Portfolio accounting is for research review, not brokerage reconciliation.
- No live trading or broker API integration is implemented.
