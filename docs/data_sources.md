# Market Data Source Adapter Framework v0.1

The Market Data Source Adapter Framework is the local-safe raw data entry layer before canonical ingestion.

It does not call broker APIs, place orders, automate execution, require API tokens, or make network calls in automated tests.

## Purpose

The project can already ingest canonical local CSV files. Data source adapters add one step before ingestion:

```text
source adapter -> data/raw/... -> ingestion -> data/processed/... -> snapshot quality -> current candidates
```

The adapter layer gives each future source a consistent contract without mixing vendor-specific fetching into replay, scoring, or paper trading.

## Supported Adapters

### LOCAL_CSV

`LOCAL_CSV` reads a caller-supplied local CSV path, validates that the file exists, loads it with pandas for row-count metadata, and writes a deterministic raw artifact:

```text
data/raw/LOCAL_CSV/<dataset_type>/<run_id>/raw_data.csv
data/raw/LOCAL_CSV/<dataset_type>/<run_id>/metadata.json
```

### MOCK

`MOCK` loads the configured mock files under `data/mock/`.

Dataset mapping:

- `market` -> `data/mock/prices.csv`
- `benchmark` -> `data/mock/prices.csv`
- `universe` -> `data/mock/universe_snapshots.csv`
- `corporate_actions` -> `data/mock/corporate_actions.csv`
- `trading_calendar` -> `data/mock/trading_calendar.csv`

### AKSHARE_OPTIONAL

`AKSHARE_OPTIONAL` is a guarded manual-only adapter for local AKShare fetches.

It is disabled by default, imports `akshare` lazily only after guardrails pass, and must not be used for real network calls in automated tests.

Supported v0.1 dataset types:

- `market`
- `benchmark`
- `trading_calendar`
- `universe`

Unsupported dataset types return a clear not-implemented error.

Manual market and benchmark fetches require:

- `--symbol`
- `--start-date`
- `--end-date`
- `--allow-real-data`

For `market`, the adapter chooses an AKShare daily-history function by default:

- ETF-like symbols, such as `510300`, use `fund_etf_hist_em`.
- Other symbols use `stock_zh_a_hist`.

For `benchmark`, the adapter uses `stock_zh_index_daily` by default and filters dates locally.

For `trading_calendar`, the adapter uses `tool_trade_date_hist_sina` by default and writes trading-day rows with standard MVP session times.

For `universe`, the adapter can fetch stock and ETF symbol/name lists through isolated AKShare helper paths and normalize them into the canonical universe snapshot columns. Use `--as-of-date` to pin the snapshot date and `--market-type stock`, `--market-type etf`, or `--market-type all` to choose the scope. If AKShare does not provide optional fields, the adapter fills conservative MVP defaults such as `min_lot=100`, `t_plus_rule=T+1`, `is_active=true`, and `industry=UNKNOWN`.

The adapter normalizes returned frames into raw CSVs that are compatible with the existing ingestion path where possible. Users should still run `data-pipeline`, `data-quality`, and `snapshot-quality` before using the data for current candidates or replay.

For the guarded manual command sequence from AKShare fetch to current candidates, see [akshare_manual_workflow.md](akshare_manual_workflow.md). For a shorter universe + market dry-run checklist with a copyable manifest template, see [akshare_real_data_dry_run.md](akshare_real_data_dry_run.md).

## Dataset Types

Supported `dataset_type` values are:

- `market`
- `universe`
- `benchmark`
- `corporate_actions`
- `trading_calendar`

The adapter framework writes raw files only. Canonical schema validation remains in `data_ingestion`.

## Real Data Guardrails

Default settings keep real/network sources blocked:

```yaml
data_sources:
  allow_network_sources: false
  allow_real_data_fetch: false
  require_manual_real_data_flag: true
```

Rules:

- Real/network adapters are disabled by default.
- CLI real-data runs require `--allow-real-data`.
- Automated tests must use `LOCAL_CSV` or `MOCK`.
- Automated tests may monkeypatch a fake `akshare` module, but they must not call real AKShare or network APIs.
- No API keys or tokens are required or printed.
- `.env` is not modified.
- Broker/live trading integrations are not invoked.

## CLI Usage

Load a local CSV into raw artifacts:

```cmd
python -m quant_replay_system.cli data-source-fetch --source LOCAL_CSV --dataset-type market --input data\mock\prices.csv
```

Load configured mock data:

```cmd
python -m quant_replay_system.cli data-source-fetch --source MOCK --dataset-type market
```

Use a custom raw output root:

```cmd
python -m quant_replay_system.cli data-source-fetch --source LOCAL_CSV --dataset-type universe --input data\mock\universe_snapshots.csv --output-dir data\raw
```

Manual AKShare market fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type market --symbol 510300 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

Manual AKShare trading calendar fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type trading_calendar --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

Manual AKShare universe snapshot fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type universe --as-of-date 2024-05-20 --market-type all --allow-real-data
```

The command prints raw artifact paths, row count, and:

```text
No live trading or broker API was invoked.
```

For a full Windows CMD example that carries AKShare output through `data-pipeline`, `data-quality`, `snapshot-quality`, and `current-candidates`, see [akshare_manual_workflow.md](akshare_manual_workflow.md). For the universe + market real-data dry-run checklist, see [akshare_real_data_dry_run.md](akshare_real_data_dry_run.md).

## Relationship To Data Ingestion

`data-source-fetch` writes raw local artifacts. The recommended handoff is now `data-pipeline`, which runs source fetch, ingestion, optional data quality, and optional snapshot manifest generation in one local workflow:

```cmd
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data\mock\prices.csv
```

For a manual AKShare fetch, run the raw output through the same local quality path:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type market --symbol 510300 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv
python -m quant_replay_system.cli data-quality --dataset-type market --input data\processed\market\<pipeline_id>\raw_data_cleaned.csv
```

For a manual AKShare universe snapshot:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type universe --as-of-date 2024-05-20 --market-type all --allow-real-data
python -m quant_replay_system.cli data-pipeline --dataset-type universe --source LOCAL_CSV --input data\raw\AKSHARE_OPTIONAL\universe\<run_id>\raw_data.csv
python -m quant_replay_system.cli data-quality --dataset-type universe --input data\processed\universe\<pipeline_id>\raw_data_cleaned.csv
```

You can still run the underlying commands manually:

```cmd
python -m quant_replay_system.cli ingest-market --input data\raw\LOCAL_CSV\market\...\raw_data.csv --output-dir data\processed\market
python -m quant_replay_system.cli data-quality --dataset-type market --input data\processed\market\raw_data_cleaned.csv
python -m quant_replay_system.cli snapshot-quality --manifest data\snapshots\example_snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --snapshot-manifest data\snapshots\example_snapshot_manifest.json
```

## Known MVP Limitations

- `AKSHARE_OPTIONAL` is a guarded MVP adapter, not a production data downloader.
- AKShare function selection is simple and may need manual `params` or later source-specific mapping.
- Universe snapshot support fills conservative defaults when AKShare does not provide optional fields; review data quality before current-candidate use.
- Corporate action AKShare fetches are not implemented in v0.1.
- Data source adapters still only write raw artifacts; use `data-pipeline` for ingestion handoff.
- It uses local/mock CSV data only in automated tests.
- It is not live trading and never invokes broker APIs.
