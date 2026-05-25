# Data Quality Summary Reports v0.1

Data Quality Summary Reports check canonical and processed local data before replay, calibration, and paper candidate generation use it.

It is local-only. It does not call market data APIs, require API tokens, connect to brokers, place orders, or automate execution.

## Purpose

Point-in-time replay only works if the data is complete, consistent, and safe to use.

Data quality reports help identify:

- missing required columns,
- missing values,
- duplicate business keys,
- suspicious timestamps,
- bad OHLC data,
- negative volume or amount,
- missing `source` and `revision_id`,
- trading calendar gaps,
- source/revision coverage.

## Supported Dataset Types

The `dataset_type` values are:

- `market`
- `benchmark`
- `universe`
- `corporate_actions`
- `trading_calendar`

## Checks

### Market And Benchmark

- Required columns exist.
- Row counts by `trade_date`.
- Row counts by `source`.
- Missingness by column.
- Duplicate `symbol` / `trade_date` rows.
- Negative or zero OHLC prices.
- Negative `volume` or `amount`.
- OHLC consistency:
  - `high >= low`
  - `high >= open`
  - `high >= close`
  - `low <= open`
  - `low <= close`
- Missing or non-positive `pre_close`.
- Missing `available_time`.
- `available_time` before `trade_date`.
- Missing `source` or `revision_id`.

### Universe

- Required columns exist.
- Row counts by `as_of_date`.
- Duplicate `as_of_date` / `symbol` rows.
- Missing `symbol`, `name`, `instrument_type`, or `exchange`.
- `listed_date` after `as_of_date`.
- `delisted_date` before `listed_date`.
- Non-positive `min_lot`.
- Missing `available_time`.
- Missing `source` or `revision_id`.

### Corporate Actions

- Required columns exist.
- Missing `available_time`.
- Invalid or implausible `ex_date`.
- Negative `cash_dividend`.
- Non-positive `split_ratio` when present.
- Duplicate `symbol` / `action_type` / `ex_date` rows.
- Missing `source` or `revision_id`.

### Trading Calendar

- Required columns exist.
- Duplicate `trade_date` rows.
- Missing `is_trading_day`.
- Trading day missing `session_open`, `session_close`, or `decision_time`.
- Non-trading day with session fields present.

## Severity Levels

- `INFO`: notable but not dangerous.
- `WARN`: review before using the dataset.
- `ERROR`: unsafe for replay.

Status rules:

- Any `ERROR` gives `FAIL`.
- Only `WARN` issues gives `WARN`.
- No `WARN` or `ERROR` gives `PASS`.

## Artifacts

Reports are written to:

```text
outputs/reports/data_quality/<dataset_type>/<quality_run_id>/
```

Each run writes:

- `data_quality_report.md`
- `data_quality_issues.csv`
- `row_counts.csv`
- `missingness_summary.csv`
- `duplicate_summary.csv`
- `source_revision_summary.csv`
- `metadata.json`

The `quality_run_id` is deterministic from dataset type, row count, date range, source/revision coverage, and quality settings.

## CLI Usage

Market data:

```cmd
python -m quant_replay_system.cli data-quality --dataset-type market --input data\processed\market\market_cleaned.csv
```

Universe:

```cmd
python -m quant_replay_system.cli data-quality --dataset-type universe --input data\processed\universe\universe_cleaned.csv
```

Trading calendar:

```cmd
python -m quant_replay_system.cli data-quality --dataset-type trading_calendar --input data\processed\trading_calendar\calendar_cleaned.csv
```

Strict mode escalates configurable warnings to errors:

```cmd
python -m quant_replay_system.cli data-quality --dataset-type market --input data\processed\market\market_cleaned.csv --strict
```

The command prints status, issue counts, report path, and:

```text
No live trading or broker API was invoked.
```

It exits non-zero on `FAIL`.

## How This Protects Replay

Replay and calibration assume input files obey the point-in-time contract.

Data quality reports provide a checkpoint between ingestion and replay so bad files can be caught before:

- technical indicators are calculated,
- factor datasets are built,
- candidates are scored,
- batch replays are calibrated,
- paper trading decisions are reviewed.

For market data exported from the local market cache, duplicate `symbol + trade_date` rows can appear when multiple source variants are queried together. Use `market-cache-query --source ... --upstream-source ...` for a single-symbol slice, or `market-cache-export` for a reviewed multi-row export manifest, before `data-pipeline`. Data quality should continue to warn on duplicate business keys rather than silently choosing a source.

## Known MVP Limitations

- Checks are summary-level and do not repair data.
- Missingness checks do not infer whether all missing values are unacceptable.
- No exchange-specific corporate action validation yet.
- No full benchmark/universe coverage cross-check yet.
- No network/API checks are performed.
- It is not live trading and never invokes broker APIs.
