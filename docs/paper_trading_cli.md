# Paper Trading CLI v0.1

Paper Trading CLI provides local-only command wrappers for manual paper trading workflows.

It does not place orders, connect to brokers, automate execution, or call broker APIs. It only reads local CSV files and writes local paper-trading artifacts.

## Commands

Run commands with:

```cmd
python -m quant_replay_system.cli <command> ...
```

## paper-daily

Generate a daily paper trading report from either a candidates CSV or a reviewed decisions CSV, plus optional manual fills CSV.

```cmd
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --candidates outputs\reports\replay_runs\example\candidates.csv
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --reviewed-decisions outputs\reports\paper_trading\reviews\example\reviewed_decisions.csv --fills data\paper\fills.csv
```

Options:

- `--date` required paper date.
- `--candidates` optional candidates CSV.
- `--reviewed-decisions` optional reviewed decisions CSV.
- `--fills` optional manual fills CSV.
- `--mark-prices` optional local mark-to-market price CSV.
- `--output-dir` optional artifact output directory.
- `--journal-id` optional explicit journal ID.
- `--config` optional config YAML path.

At least one of `--candidates` or `--reviewed-decisions` is required. If both are supplied, reviewed decisions are preferred by default and a warning is printed.

The command prints artifact paths, row counts, reviewed decision usage, warnings, and the no-live-trading statement.

If `--fills` points to a missing file, the command records a warning and continues with an empty fills ledger.

## paper-validate-fills

Validate a manual fills CSV before using it in the daily runner.

```cmd
python -m quant_replay_system.cli paper-validate-fills --fills data\paper\fills.csv
```

Validation checks:

- required columns are present,
- `side` is `BUY` or `SELL`,
- `quantity` is positive,
- `fill_price` is positive,
- `fill_date` can be parsed.

The command exits with status `0` on success and non-zero on validation failure.

## paper-reconcile-fills

Reconcile a manual fills CSV against a paper decisions CSV and write reconciliation artifacts.

```cmd
python -m quant_replay_system.cli paper-reconcile-fills --decisions outputs\reports\paper_trading\daily\example\decisions.csv --fills data\paper\fills.csv
```

Options:

- `--decisions` required paper decisions CSV.
- `--fills` required manual fills CSV.
- `--output-dir` optional reconciliation artifact output directory.
- `--config` optional config YAML path.
- `--allow-fail` exits with status `0` even if reconciliation status is `FAIL`.

The command checks decision/fill matching, approval status, side, quantity, price, gross notional, cash-flow sign, oversells, negative cash, duplicate fill IDs, and required fill columns.

It exits non-zero on `FAIL` unless `--allow-fail` is passed.

## paper-review-decisions

Apply manual approve/reject/watch updates to a paper decisions CSV and write review artifacts.

```cmd
python -m quant_replay_system.cli paper-review-decisions --decisions outputs\reports\paper_trading\daily\example\decisions.csv --updates data\paper\review_updates.csv --reviewer-id msj
```

Options:

- `--decisions` required paper decisions CSV.
- `--updates` required review updates CSV.
- `--output-dir` optional review artifact output directory.
- `--reviewer-id` optional default reviewer ID.
- `--allow-pending` allows decisions to remain pending review.
- `--config` optional config YAML path.

The command validates update rows, applies review status and notes, writes `reviewed_decisions.csv`, `review_audit_log.csv`, `review_summary.csv`, `paper_review_report.md`, and `metadata.json`, then prints the review summary.

## paper-index

Build a consolidated local index for daily, review, and reconciliation artifacts.

```cmd
python -m quant_replay_system.cli paper-index --root outputs\reports\paper_trading
```

Options:

- `--root` optional paper trading artifact root.
- `--output-dir` optional index output directory.
- `--artifact-type` optional `daily`, `review`, `reconciliation`, or `all`.
- `--include-missing-metadata` includes folders without `metadata.json` as warning rows.
- `--config` optional config YAML path.

The command writes `paper_artifact_index.md`, `paper_artifact_index.csv`, `paper_artifact_index.json`, and `metadata.json`, then prints the index report path and artifact count.

## paper-template-fills

Write an empty fills CSV template.

```cmd
python -m quant_replay_system.cli paper-template-fills --output data\paper\fills_template.csv
```

The command does not overwrite an existing file unless `--overwrite` is passed.

## Expected Fills Schema

The fills template contains:

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

Only these manual hypothetical records are consumed. They are not broker confirmations.

## Local-Only Guarantee

The CLI imports only local project modules and pandas. It does not import broker modules or live trading integrations.

Every successful command prints:

```text
No live trading or broker API was invoked.
```

## Known MVP Limitations

- Uses local CSV/mock data only.
- Does not provide interactive fill entry.
- Does not place or route orders.
- Does not connect to brokers.
- Does not model corporate actions, dividends, financing, or complete exchange fee schedules.
