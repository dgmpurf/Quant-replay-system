# Data Source To Ingestion Handoff Pipeline v0.1

The Data Source To Ingestion Handoff Pipeline connects raw local data source artifacts to canonical ingestion, data quality checks, and optional snapshot manifest creation.

It is local-only. It does not call market data APIs in automated tests, require API tokens, connect to brokers, place orders, or automate execution.

## Purpose

The project now has separate modules for:

- raw data source adapters,
- canonical CSV ingestion,
- data quality reports,
- snapshot quality gates.

The pipeline ties those modules together into one auditable local preparation flow:

```text
data source adapter -> raw_data.csv -> canonical ingestion -> data quality -> snapshot manifest
```

This prepares local files for replay, current candidate generation, batch replay, and calibration without weakening point-in-time data contracts.

## Single Dataset Mode

Single dataset mode runs one source request through ingestion and optional quality checks.

Example:

```cmd
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data\mock\prices.csv
```

For market data fetched from optional public sources, the recommended repeatable path is to cache the successful canonical `raw_data.csv` first, then query a local CSV for pipeline input:

```cmd
python -m quant_replay_system.cli market-cache-ingest --input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\AKSHARE_OPTIONAL\market\<run_id>\metadata.json
python -m quant_replay_system.cli market-cache-query --symbol 510300 --start-date 2024-01-01 --end-date 2024-05-20 --output data\raw\manual_cache\510300_market.csv
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data\raw\manual_cache\510300_market.csv
```

When the local cache contains multiple source variants for the same `symbol + trade_date`, export a single selected source/upstream for pipeline use:

```cmd
python -m quant_replay_system.cli market-cache-query --symbol 000001 --start-date 2024-01-02 --end-date 2024-01-05 --source AKSHARE_OPTIONAL --upstream-source TENCENT --output data\raw\manual_cache\000001_tencent_market.csv
```

For reviewed multi-symbol exports, use `market-cache-export` with a reviewed source/upstream manifest:

```cmd
python -m quant_replay_system.cli market-cache-export --manifest data\raw\manual_manifests\reviewed_cache_export_example.csv --build-pipeline-manifest --universe data\raw\LOCAL_CSV\universe_overlay\<overlay_id>\raw_data.csv --trading-calendar data\raw\AKSHARE_OPTIONAL\trading_calendar\<run_id>\raw_data.csv
```

The pipeline and data-quality checks intentionally keep the duplicate `symbol + trade_date` warning. Cache query filters and reviewed cache export are the explicit v0.1 ways to choose source paths before building pipeline inputs; the project does not silently choose a trusted source.

See [market_data_cache.md](market_data_cache.md) and [market_cache_export.md](market_cache_export.md). The cache reduces repeated public endpoint calls but does not replace data-quality or snapshot-quality gates.

Supported dataset types:

- `market`
- `universe`
- `benchmark`
- `corporate_actions`
- `trading_calendar`

The matching ingestion function is selected automatically.

For `universe` inputs, the pipeline inherits ingestion's optional date handling: `listed_date` and `delisted_date` may be missing, including AKShare-style blank/`NaN`/`NaT`/`--` values. Non-empty invalid dates are still rejected, and parseable `listed_date` / `delisted_date` values still go through universe date-order checks.

The pipeline also preserves symbol columns as strings. Six-digit China symbols such as `000001`, `510300`, and `159915` must remain six-character strings through raw and processed files. If market data is for an ETF, the universe input must include the same ETF symbol, for example `symbol=510300` with `instrument_type=ETF`; otherwise the downstream factor dataset will be empty for that symbol even when market and snapshot quality checks pass.

If your base universe is stock-only, create a reviewed ETF overlay first:

```cmd
python -m quant_replay_system.cli universe-overlay --base-universe data\raw\AKSHARE_OPTIONAL\universe\<run_id>\raw_data.csv --overlay data\raw\manual_overlays\etf_universe_overlay.csv
```

Then use the merged `data\raw\LOCAL_CSV\universe_overlay\<overlay_run_id>\raw_data.csv` path as the manifest's `universe` input.

## Manifest Mode

Manifest mode runs multiple datasets in one pipeline.

Example manifest:

```json
{
  "datasets": [
    {"dataset_type": "market", "source": "LOCAL_CSV", "input_path": "data/raw/market.csv"},
    {"dataset_type": "universe", "source": "LOCAL_CSV", "input_path": "data/raw/universe.csv"},
    {"dataset_type": "trading_calendar", "source": "LOCAL_CSV", "input_path": "data/raw/trading_calendar.csv"}
  ]
}
```

Run it with:

```cmd
python -m quant_replay_system.cli data-pipeline --manifest data\mock\data_pipeline_manifest.json
```

Reviewed offline market-update batches can generate this manifest automatically:

```cmd
python -m quant_replay_system.cli market-update-handoff --symbol-manifest data\raw\manual_manifests\daily_market_symbols_offline_example.csv --universe data\raw\LOCAL_CSV\universe_overlay\<overlay_id>\raw_data.csv --trading-calendar data\raw\AKSHARE_OPTIONAL\trading_calendar\<run_id>\raw_data.csv --decision-date 2024-05-20 --universe-name etf_core --selection-profile demo --dry-run
```

The generated manifest is still local `LOCAL_CSV` input and still runs through the same ingestion, data-quality, and snapshot manifest path.

When more than one processed dataset is present and snapshot manifest generation is enabled, the pipeline writes a local `snapshot_manifest.json` compatible with Snapshot Quality Gate.

## Data Quality Integration

Data quality checks run by default after canonical ingestion:

```yaml
data_pipeline:
  run_data_quality: true
  fail_on_data_quality_fail: false
  allow_data_quality_warn: true
```

Default behavior:

- ingestion errors fail the pipeline,
- data quality `PASS` keeps the dataset `PASS`,
- data quality `WARN` makes the dataset `WARN`,
- data quality `FAIL` makes the dataset `WARN` unless `fail_on_data_quality_fail=true`.

Skip quality checks with:

```cmd
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data\mock\prices.csv --skip-data-quality
```

## Snapshot Manifest Output

For multi-dataset runs, the pipeline can write:

```text
outputs/reports/data_pipeline/<pipeline_id>/snapshot_manifest.json
```

The manifest includes:

- `snapshot_id`
- `processed_files`
- row counts
- dataset statuses
- warnings
- local-only audit metadata

Run Snapshot Quality Gate afterward:

```cmd
python -m quant_replay_system.cli snapshot-quality --manifest outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json
```

## Artifacts

Pipeline artifacts are written to:

```text
outputs/reports/data_pipeline/<pipeline_id>/
```

Files:

- `data_pipeline_report.md`
- `dataset_results.csv`
- `processed_paths.csv`
- `data_quality_summary.csv` when quality checks run
- `snapshot_manifest.json` when built
- `metadata.json`

The `pipeline_id` is deterministic from dataset requests, source/revision fields, quality/snapshot flags, and config version.

## CLI Usage

Run a market file through the full local pipeline:

```cmd
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data\mock\prices.csv
```

Run configured mock data:

```cmd
python -m quant_replay_system.cli data-pipeline --dataset-type market --source MOCK
```

Run a multi-dataset manifest:

```cmd
python -m quant_replay_system.cli data-pipeline --manifest data\mock\data_pipeline_manifest.json
```

Manifest files may be UTF-8 or UTF-8 with BOM. This keeps local Windows tooling such as PowerShell and Notepad from breaking dry-run manifests, while invalid JSON still fails during manifest loading.

Skip snapshot manifest creation:

```cmd
python -m quant_replay_system.cli data-pipeline --manifest data\mock\data_pipeline_manifest.json --skip-snapshot-manifest
```

The CLI prints pipeline status, processed paths, report path, snapshot manifest path when available, and:

```text
No live trading or broker API was invoked.
```

## Relationship To Current Candidates And Replay

The pipeline prepares clean local data before downstream workflows:

```text
data-pipeline -> snapshot-quality -> current-candidates -> paper review / paper daily
data-pipeline -> snapshot-quality preflight -> replay / batch replay / calibration
```

It does not change point-in-time filtering, trading calendar logic, T+1 execution logic, technical indicator formulas, or scoring formulas.

## Known MVP Limitations

- Real/network data sources remain disabled by default.
- No real API calls are used in automated tests.
- The pipeline does not repair failed source data.
- AKShare universe output may not include complete `listed_date` coverage; missing optional universe dates are allowed, but invalid non-empty values still fail ingestion.
- Market/universe joins require exact normalized symbol overlap. A market ETF such as `510300` needs matching universe coverage; the pipeline does not create missing universe rows.
- Use [universe_overlay.md](universe_overlay.md) to merge reviewed ETF rows into a stock-only universe before the pipeline.
- Snapshot manifest creation is limited to datasets processed in the same run.
- It does not merge with or update an existing snapshot manifest.
- Reviewed update handoff manifests are local dry-run inputs; they do not mutate the market cache.
- It is not live trading and never invokes broker APIs.
