# Daily Paper Trading Runner v0.1

Daily Paper Trading Runner is a local-only wrapper around the Manual Paper Trading Journal.

It loads reviewed candidates, loads optional manual paper fills, marks paper positions to local price data, and writes one daily paper journal artifact folder.

It is not live trading. It does not connect to brokers, submit orders, automate order placement, or call broker APIs.

## Purpose

The runner makes the daily paper process repeatable:

1. load candidate output from replay or a candidate CSV,
2. create a paper decision log,
3. load existing manual fills if present,
4. calculate open paper positions,
5. calculate closed paper trades,
6. mark positions to local prices,
7. write a daily summary and report.

## Expected Candidate Input

Candidates can be passed as a DataFrame or CSV path.

Useful columns include:

- `symbol`
- `name`
- `final_score`
- `action`
- `risk_precheck_status`
- `risk_precheck_reason`
- `source_run_id`
- `source_report_path`
- `rank` or `candidate_rank`

Optional columns are handled with defaults. A minimal candidate file only needs `symbol`.

## Expected Manual Fills Input

Manual fills are optional.

If `fills_path` is missing or does not exist, the runner continues with an empty fill ledger and records a warning.

Expected fill columns:

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

Fills are manual hypothetical records only. They are not broker confirmations.

## Local Usage

Callable function:

```python
from quant_replay_system.daily_paper_runner import run_daily_paper_trading

result = run_daily_paper_trading(
    "2024-05-20",
    candidates_path="outputs/reports/replay_runs/example/candidates.csv",
    fills_path="outputs/reports/paper_trading/manual_fills.csv",
)

print(result.daily_summary)
```

No CLI is required for MVP v0.1.

## Artifact Outputs

Default output folder:

```text
outputs/reports/paper_trading/daily/<paper_date>_<journal_id>/
  paper_report.md
  decisions.csv
  fills.csv
  open_positions.csv
  closed_trades.csv
  daily_summary.csv
  metadata.json
```

The daily summary includes:

- `paper_date`
- `decision_count`
- `approved_count`
- `fill_count`
- `open_position_count`
- `closed_trade_count`
- `total_market_value`
- `total_unrealized_pnl`
- `total_realized_pnl`
- `total_pnl`
- `warnings_count`

The report includes an explicit no-live-trading statement.

## Configuration

```yaml
daily_paper_runner:
  output_dir: outputs/reports/paper_trading/daily
  config_version: mvp
  write_artifacts: true
  enable_live_trading: false
  enable_broker_api: false
```

The live trading and broker API flags are constrained to false.

## Known MVP Limitations

- Uses local CSV/mock data only.
- Does not implement a CLI yet.
- Does not update fills interactively.
- Missing fills files are treated as empty paper fill logs.
- Corporate actions, dividends, financing, and full exchange fee schedules are not modeled.
- No live trading or broker API integration is implemented.
