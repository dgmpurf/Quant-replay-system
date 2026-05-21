# Paper Trading End-to-End Workflow v0.1

This document shows the local-only manual paper trading workflow from candidates to reviewed decisions, fills reconciliation, and final daily paper reports.

It is not live trading. It does not connect to brokers, submit orders, automate order placement, or call broker APIs.

## Purpose

The workflow is designed to test reviewed paper signals before any real-money process exists:

1. generate a paper decision log from candidates,
2. manually review the decisions,
3. run the daily paper report with reviewed decisions,
4. enter manual hypothetical fills,
5. reconcile fills against reviewed decisions,
6. generate final daily paper artifacts.

## Example Inputs

Tiny mock inputs are available under:

```text
data/mock/paper_trading/
  candidates_example.csv
  review_updates_example.csv
  fills_example.csv
```

The example review and fill files use deterministic decision IDs generated from `candidates_example.csv`.

## Step 1: Generate Decisions From Candidates

```cmd
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --candidates data\mock\paper_trading\candidates_example.csv --output-dir outputs\reports\paper_trading\e2e_initial --journal-id example_initial
```

Expected output:

```text
outputs/reports/paper_trading/e2e_initial/2024-05-20_example_initial/
  decisions.csv
  paper_report.md
  metadata.json
```

The initial `decisions.csv` is the input to review.

## Step 2: Review Decisions

```cmd
python -m quant_replay_system.cli paper-review-decisions --decisions outputs\reports\paper_trading\e2e_initial\2024-05-20_example_initial\decisions.csv --updates data\mock\paper_trading\review_updates_example.csv --reviewer-id example-reviewer --output-dir outputs\reports\paper_trading\e2e_reviews
```

Expected output:

```text
outputs/reports/paper_trading/e2e_reviews/<review_id>/
  reviewed_decisions.csv
  review_audit_log.csv
  review_summary.csv
  paper_review_report.md
  metadata.json
```

The reviewed decisions preserve:

- `manual_review_status`
- `manual_review_notes`
- `reviewer_id`
- `review_reason_code`
- `review_time`

## Step 3: Run Daily Paper Report With Reviewed Decisions

```cmd
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --reviewed-decisions outputs\reports\paper_trading\e2e_reviews\<review_id>\reviewed_decisions.csv --output-dir outputs\reports\paper_trading\e2e_reviewed --journal-id example_reviewed
```

When `--reviewed-decisions` is supplied, the daily runner uses it directly and does not recreate review status from raw candidates.

## Step 4: Enter Manual Fills

Manual fills are local CSV rows only. The example fill records one hypothetical BUY for the approved `AAA` decision:

```text
data/mock/paper_trading/fills_example.csv
```

Fills against `REJECTED`, `WATCH_ONLY`, or `PENDING_REVIEW` decisions fail reconciliation by default.

## Step 5: Reconcile Fills

```cmd
python -m quant_replay_system.cli paper-reconcile-fills --decisions outputs\reports\paper_trading\e2e_reviews\<review_id>\reviewed_decisions.csv --fills data\mock\paper_trading\fills_example.csv --output-dir outputs\reports\paper_trading\e2e_reconciliation
```

Expected output:

```text
outputs/reports/paper_trading/e2e_reconciliation/<reconciliation_id>/
  reconciliation_report.md
  reconciliation_issues.csv
  reconciliation_summary.csv
  metadata.json
```

The approved example fill should reconcile with `PASS`.

## Step 6: Generate Final Daily Artifacts

```cmd
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --reviewed-decisions outputs\reports\paper_trading\e2e_reviews\<review_id>\reviewed_decisions.csv --fills data\mock\paper_trading\fills_example.csv --output-dir outputs\reports\paper_trading\e2e_final --journal-id example_final
```

Expected output:

```text
outputs/reports/paper_trading/e2e_final/2024-05-20_example_final/
  paper_report.md
  decisions.csv
  fills.csv
  open_positions.csv
  closed_trades.csv
  daily_summary.csv
  metadata.json
```

`metadata.json` records the `reviewed_decisions_path` used for the run.

## No-Live-Trading Guarantee

All reports in this workflow include a no-live-trading statement.

The workflow:

- reads local CSV files,
- writes local reports and metadata,
- does not import broker modules,
- does not call broker APIs,
- does not automate order placement.

## Known MVP Limitations

- Uses local CSV/mock data only.
- Does not provide an interactive review or fill-entry UI.
- Does not model corporate actions, dividends, financing, or full exchange fee schedules.
- Does not fetch real market data.
- Does not guarantee paper results will match future live execution.
