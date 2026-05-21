# Paper Trading CLI v0.1

Paper Trading CLI provides local-only command wrappers for manual paper trading workflows.

It does not place orders, connect to brokers, automate execution, or call broker APIs. It only reads local CSV files and writes local paper-trading artifacts.

## Commands

Run commands with:

```cmd
python -m quant_replay_system.cli <command> ...
```

## paper-daily

Generate a daily paper trading report from a candidates CSV and optional manual fills CSV.

```cmd
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --candidates outputs\reports\replay_runs\example\candidates.csv
```

Options:

- `--date` required paper date.
- `--candidates` required candidates CSV.
- `--fills` optional manual fills CSV.
- `--mark-prices` optional local mark-to-market price CSV.
- `--output-dir` optional artifact output directory.
- `--journal-id` optional explicit journal ID.
- `--config` optional config YAML path.

The command prints artifact paths, row counts, warnings, and the no-live-trading statement.

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
