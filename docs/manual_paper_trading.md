# Manual Paper Trading Journal v0.1

Manual Paper Trading Journal records reviewed candidates, manual hypothetical fills, open paper positions, closed paper trades, and a daily summary.

It is not live trading. It does not connect to a broker, place orders, submit orders, or automate execution. Every fill is a manual paper record entered by the user.

## Purpose

The journal helps test current replay signals before any real-money workflow is considered.

It preserves:

- candidate ranks and final scores,
- component score breakdowns,
- risk precheck status and reason,
- planned holding dates,
- manual review status,
- manual notes,
- hypothetical paper fills,
- open and closed paper positions.

## Decision Log

`create_paper_decision_log(...)` converts selected candidates into a paper decision table.

Each decision includes:

- `decision_id`
- `decision_date`
- `symbol`
- `name`
- `action`
- `intended_side`
- `final_score`
- `component_scores`
- `risk_precheck_status`
- `risk_precheck_reason`
- `candidate_rank`
- `source_run_id`
- `source_report_path`
- `planned_holding_horizon`
- `planned_buy_date`
- `planned_sell_date`
- `manual_review_status`
- `manual_review_notes`
- `created_at`

Decision IDs are deterministic for the same source run, date, symbol, rank, and planned dates.

## Manual Review Workflow

Supported decision actions:

- `WATCH`
- `PAPER_BUY`
- `PAPER_SELL`
- `HOLD`
- `SKIP`

Supported review statuses:

- `PENDING_REVIEW`
- `APPROVED_FOR_PAPER`
- `REJECTED`
- `WATCH_ONLY`

New decisions default to `PENDING_REVIEW`.

By default, fills can only be recorded for decisions whose `manual_review_status` is `APPROVED_FOR_PAPER`. This prevents a pending, rejected, or watch-only candidate from accidentally becoming a paper position.

## Paper Fills

`record_paper_fill(...)` appends a manual hypothetical fill.

Each fill includes:

- `fill_id`
- `decision_id`
- `symbol`
- `side`
- `fill_date`
- `fill_price`
- `quantity`
- `gross_notional`
- `fees`
- `slippage`
- `net_cash_flow`
- `fill_source`
- `manual_notes`

By default:

- fractional shares are rejected,
- quantities are rounded down to the configured lot size,
- short selling is not allowed,
- sell quantity cannot exceed the currently available paper position,
- buy fills cannot make paper cash negative.

## Fill Validation

`validate_paper_fills(fills, decisions=None, settings=None)` validates manual fills before accounting uses them.

It checks:

- required fill columns exist,
- `side` is `BUY` or `SELL`,
- `quantity > 0`,
- `fill_price > 0`,
- `gross_notional` approximately equals `fill_price * quantity`,
- BUY `net_cash_flow` is negative,
- SELL `net_cash_flow` is positive,
- `decision_id` exists when decisions are provided,
- decision status is `APPROVED_FOR_PAPER` by default,
- SELL fills do not exceed available position quantity when short selling is disabled,
- BUY fills do not push paper cash below zero when negative cash prevention is enabled.

For an auditable decision/fill issue report, use paper fill reconciliation before daily reports. See [paper_fill_reconciliation.md](paper_fill_reconciliation.md).

## Open And Closed Positions

`build_open_positions(...)` aggregates buy and sell fills into current open paper positions using FIFO remaining lots.

`build_closed_trades(...)` matches sell fills against prior buy fills using FIFO and calculates realized PnL.

Open positions include market value, unrealized PnL, and unrealized return based on local market data.

Closed trades include realized PnL, realized return, `holding_calendar_days`, legacy `holding_days`, and exit reason.

`holding_calendar_days` is calendar-day elapsed time between open date and close date. It is not a trading-day holding period. A future calendar-aware paper module can add `holding_trading_days`.

## Journal ID Stability

The journal ID is based on decision dates, source run IDs, symbols, and config version.

It does not include fill IDs. Adding or editing manual paper fills should not change the journal ID for the same decision set.

## Daily Report

`generate_paper_trading_report(...)` creates a full journal result and, when artifacts are enabled, writes:

```text
outputs/reports/paper_trading/<journal_id>/
  paper_report.md
  decisions.csv
  fills.csv
  open_positions.csv
  closed_trades.csv
  daily_summary.csv
  metadata.json
```

The daily summary includes:

- `paper_cash`
- `open_position_count`
- `closed_trade_count`
- `total_market_value`
- `total_equity`
- `daily_unrealized_pnl`
- `realized_pnl`
- `total_pnl`
- `win_rate_closed_trades`
- `exposure_pct`
- `warnings`

The markdown report includes an explicit statement that no broker or live trading integration was invoked.

## Configuration

```yaml
paper_trading:
  output_dir: outputs/reports/paper_trading
  initial_paper_cash: 10000
  default_lot_size: 100
  round_lots: true
  allow_fractional_shares: false
  allow_short_selling: false
  require_approved_decision_for_fills: true
  prevent_negative_cash: true
  default_fee_bps: 0
  default_slippage_bps: 0
  enable_live_trading: false
  enable_broker_api: false
```

The live trading and broker API flags are constrained to false in the settings model.

## Preparing For Small Real-Money Testing

This module prepares for later manual review by making the paper process explicit:

- what the signal recommended,
- what the user manually approved,
- what hypothetical fill was recorded,
- how the paper position behaved,
- what warnings or limitations applied.

It does not create live orders. A future real-money workflow should remain manual and separately reviewed.

## Known MVP Limitations

- Uses local CSV/mock data only.
- Fills are manual hypothetical records, not broker confirmations.
- Position accounting is simplified.
- Corporate actions, dividends, financing, and full exchange fee schedules are not modeled.
- No live trading or broker API integration is implemented.
