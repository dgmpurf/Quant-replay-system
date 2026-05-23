# Market Data Ingestion and Snapshot Builder v0.1

Market Data Ingestion imports local CSV files into the project’s canonical point-in-time schemas and writes processed artifacts for replay, batch research, and future current-candidate generation.

It is local-only. It does not call market data APIs, require API tokens, connect to brokers, place orders, or automate execution.

## Purpose

Early mock data is useful, but replay research needs a repeatable way to clean local files before they enter the point-in-time pipeline.

The ingestion layer:

- validates required columns,
- normalizes symbols,
- parses date and timestamp fields,
- assigns safe default `available_time` values only when configured,
- adds default `source` and `revision_id` fields when missing,
- validates numeric fields,
- detects duplicates,
- writes cleaned processed CSVs,
- writes validation reports and metadata,
- builds snapshot manifests over processed files.

## Supported Inputs

v0.1 supports local CSV files for:

- market daily data,
- universe snapshots,
- benchmark daily data,
- corporate actions,
- trading calendars.

## Canonical Schemas

Market and benchmark daily data use:

```text
symbol, trade_date, open, high, low, close, volume, amount, pre_close,
adj_factor, is_suspended, limit_up, limit_down, event_time, publish_time,
ingest_time, available_time, revision_id, source
```

Universe snapshots use:

```text
as_of_date, symbol, name, instrument_type, exchange, listed_date,
delisted_date, is_active, is_st, is_suspended, industry, min_lot,
t_plus_rule, available_time, revision_id, source
```

For universe snapshots, `listed_date` and `delisted_date` are optional date fields. Missing values such as blank strings, `NaN`, `NaT`, `None`, `null`, `-`, and `--` are accepted and preserved as missing dates in the canonical output. Non-empty invalid values, such as `not-a-date`, still fail ingestion. When dates are present and parseable, ingestion still rejects `listed_date` after `as_of_date` and `delisted_date` before `listed_date`. Downstream eligibility treats a missing `listed_date` as an unknown listing date rather than rejecting the symbol solely for missing listing-date coverage.

## Symbol Normalization

Symbol columns are read as strings. Leading zeros are significant and must be preserved across raw input, ingestion, processed CSVs, factor datasets, and current-candidate generation.

Examples:

- `000001` remains `000001`, not `1`.
- `510300` remains `510300`.
- `159915` remains `159915`.
- Tushare-style symbols such as `000001.SZ` preserve the exchange suffix.

If a reviewed CSV was previously saved with stripped numeric symbols, ingestion pads six-digit China market symbols where it can do so safely. This is a recovery guard, not a substitute for reviewing the source file.

Universe snapshots may include both stock and ETF rows. If a market file contains ETF `510300`, the universe snapshot must also include a matching `symbol=510300` row, usually with `instrument_type=ETF`, or downstream factor datasets will have no joinable row for that ETF.

Corporate actions use:

```text
symbol, action_type, ex_date, record_date, cash_dividend, split_ratio,
rights_issue, event_time, publish_time, ingest_time, available_time,
revision_id, source
```

Trading calendars use:

```text
trade_date, is_trading_day, session_open, session_close, decision_time, reason
```

## available_time Rules

`available_time` is the earliest time a replay is allowed to use a record.

Rules:

- If `available_time` exists, it must parse as a valid timestamp.
- If `available_time` is missing and defaulting is enabled:
  - market daily rows default to `trade_date 15:30`,
  - benchmark daily rows default to `trade_date 15:30`,
  - universe rows default to `as_of_date 08:00`.
- Corporate actions do not default silently unless `allow_default_corporate_action_available_time=true`.
- If defaulting is disabled, missing `available_time` fails ingestion.

The MVP writes naive local exchange timestamps for compatibility with the existing replay loaders.

## Validation Rules

Validation fails on:

- missing required columns,
- invalid dates,
- invalid non-empty optional universe dates,
- universe `listed_date` after `as_of_date`,
- universe `delisted_date` before `listed_date`,
- invalid timestamps,
- invalid booleans,
- missing `available_time` when defaulting is disabled,
- negative prices,
- negative volume or amount.

Duplicate business keys produce a warning by default. Set:

```yaml
data_ingestion:
  duplicate_key_severity: ERROR
```

to fail ingestion on duplicates.

## Output Folders

Default processed folders:

```text
data/processed/market/
data/processed/universe/
data/processed/benchmark/
data/processed/corporate_actions/
data/processed/trading_calendar/
```

Snapshot manifests are written to:

```text
data/snapshots/
```

These folders are ignored by Git for local generated data.

## Artifacts

Each ingestion run writes:

- cleaned CSV,
- `validation_report.csv`,
- `metadata.json`.

Snapshot builds write:

- `snapshot_manifest.json` with processed file paths,
- row counts,
- validation warnings,
- local-only audit metadata.

## CLI Usage

Market daily data:

```cmd
python -m quant_replay_system.cli ingest-market --input data\raw\market.csv --output-dir data\processed\market
```

Universe snapshots:

```cmd
python -m quant_replay_system.cli ingest-universe --input data\raw\universe.csv --output-dir data\processed\universe
```

Benchmark data:

```cmd
python -m quant_replay_system.cli ingest-benchmark --input data\raw\benchmark.csv --output-dir data\processed\benchmark
```

Corporate actions:

```cmd
python -m quant_replay_system.cli ingest-corporate-actions --input data\raw\corporate_actions.csv --output-dir data\processed\corporate_actions
```

Trading calendar:

```cmd
python -m quant_replay_system.cli ingest-calendar --input data\raw\trading_calendar.csv --output-dir data\processed\trading_calendar
```

Each command prints the cleaned CSV path, validation report path, metadata path, warning count, and:

```text
No live trading or broker API was invoked.
```

## How This Prepares Real Data Ingestion

The v0.1 module does not fetch real data. It creates the local processing contract that future Tushare, Akshare, vendor exports, or manually downloaded CSVs must satisfy before replay.

That keeps the replay engine insulated from source-specific quirks and protects point-in-time safety before scoring logic sees the data.

## Known MVP Limitations

- No network data fetching.
- No API token handling.
- No full vendor-specific symbol master mapping beyond conservative string preservation, six-digit symbol padding, and suffix preservation.
- AKShare-style universe exports can have incomplete listing-date coverage; missing `listed_date` / `delisted_date` values are allowed, but invalid non-empty values are rejected.
- ETF current-candidate workflows require ETF symbols to be present in the universe snapshot; ingestion preserves ETF rows but does not invent missing universe coverage.
- No corporate action adjustment engine.
- No timezone-aware timestamp storage yet.
- Duplicate handling is validation-only; it does not automatically resolve revisions.
- It is not live trading and never invokes broker APIs.
