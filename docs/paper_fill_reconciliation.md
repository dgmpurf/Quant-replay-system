# Paper Trading Fill Reconciliation v0.1

Paper fill reconciliation validates local manual paper fills against the paper decision log before daily paper reports are generated.

It is not live trading. It does not connect to brokers, submit orders, automate order placement, or call broker APIs.

## Why Reconciliation Is Needed

Manual fills are editable CSV records. Before accounting uses them, the system checks that each fill still matches a reviewed decision and that basic cash, side, quantity, and notional rules are internally consistent.

This prevents invalid fills from creating paper positions, phantom cash, or misleading daily reports.

## Matching Rules

Each fill is checked against the decision log by `decision_id`.

The reconciliation verifies:

- the decision exists,
- the fill symbol matches the decision symbol,
- the decision is `APPROVED_FOR_PAPER`,
- `side` is `BUY` or `SELL`,
- `quantity` and `fill_price` are positive,
- `gross_notional` approximately equals `fill_price * quantity`,
- BUY cash flow is negative,
- SELL cash flow is positive,
- SELL quantity does not exceed available paper position when short selling is disabled,
- paper cash does not become negative when negative-cash prevention is enabled,
- `fill_id` values are unique,
- required fill columns exist.

Use `reviewed_decisions.csv` from the paper trading review workflow as the preferred decisions input, so reconciliation can enforce the latest manual approval status.

## Issue Codes

- `UNKNOWN_DECISION_ID`
- `SYMBOL_MISMATCH`
- `DECISION_NOT_APPROVED`
- `INVALID_SIDE`
- `NON_POSITIVE_QUANTITY`
- `NON_POSITIVE_FILL_PRICE`
- `GROSS_NOTIONAL_MISMATCH`
- `BUY_CASH_FLOW_SIGN_ERROR`
- `SELL_CASH_FLOW_SIGN_ERROR`
- `OVERSELL`
- `NEGATIVE_CASH`
- `DUPLICATE_FILL_ID`
- `MISSING_REQUIRED_COLUMN`

## Status

- `PASS`: no reconciliation issues.
- `WARN`: warning-level issues exist, but no errors.
- `FAIL`: one or more error-level issues exist.

By default, duplicate `fill_id` is a warning and negative cash is an error.

## Daily Runner Integration

`run_daily_paper_trading(...)` runs reconciliation before building open positions, closed trades, and daily summaries.

If reconciliation fails:

- the reconciliation report is still written,
- the daily report continues by default,
- invalid fills are not used for accounting,
- a warning is recorded in the daily report metadata.

Set this to stop daily report generation on reconciliation errors:

```yaml
paper_trading:
  fail_daily_report_on_reconciliation_error: true
```

## CLI Usage

```cmd
python -m quant_replay_system.cli paper-reconcile-fills --decisions outputs\reports\paper_trading\daily\example\decisions.csv --fills data\paper\fills.csv
```

The command prints the reconciliation status and issue counts, writes artifacts, and exits non-zero on `FAIL`.

Use `--allow-fail` to write a failure report but return exit code `0`:

```cmd
python -m quant_replay_system.cli paper-reconcile-fills --decisions outputs\reports\paper_trading\daily\example\decisions.csv --fills data\paper\fills.csv --allow-fail
```

## Artifacts

Default output folder:

```text
outputs/reports/paper_trading/reconciliation/<reconciliation_id>/
  reconciliation_report.md
  reconciliation_issues.csv
  reconciliation_summary.csv
  metadata.json
```

The reconciliation ID is deterministic from decision IDs, fill IDs, symbols, and config version.

## Known MVP Limitations

- Uses local CSV/mock data only.
- Reconciles manual hypothetical fills, not broker confirmations.
- Cash checks are simplified and single-currency.
- Corporate actions, dividends, financing, and complete exchange fee schedules are not modeled.
- Trading-day holding calculations are not part of reconciliation.
