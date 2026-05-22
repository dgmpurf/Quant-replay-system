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

`AKSHARE_OPTIONAL` is registered as a manual-only placeholder for future real-data work.

It is disabled by default, imports `akshare` lazily, and must not be used in automated tests. A manual run must explicitly allow real data and set config guardrails before any future implementation can fetch data.

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

Real-data adapters are blocked unless explicitly and manually allowed:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type market --allow-real-data
```

The command prints raw artifact paths, row count, and:

```text
No live trading or broker API was invoked.
```

## Relationship To Data Ingestion

`data-source-fetch` writes raw local artifacts. Next, run the existing ingestion commands to normalize and validate canonical point-in-time schemas:

```cmd
python -m quant_replay_system.cli ingest-market --input data\raw\LOCAL_CSV\market\...\raw_data.csv --output-dir data\processed\market
python -m quant_replay_system.cli data-quality --dataset-type market --input data\processed\market\raw_data_cleaned.csv
python -m quant_replay_system.cli snapshot-quality --manifest data\snapshots\example_snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --snapshot-manifest data\snapshots\example_snapshot_manifest.json
```

## Known MVP Limitations

- Only `LOCAL_CSV` and `MOCK` fetch local data in v0.1.
- `AKSHARE_OPTIONAL` is a guarded placeholder, not a production data downloader.
- No source-specific symbol mapping is implemented.
- No automatic ingestion handoff is performed yet.
- No snapshot manifest is created by the data source adapter itself.
- It uses local/mock CSV data only in automated tests.
- It is not live trading and never invokes broker APIs.
