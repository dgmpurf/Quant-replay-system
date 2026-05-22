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

Supported dataset types:

- `market`
- `universe`
- `benchmark`
- `corporate_actions`
- `trading_calendar`

The matching ingestion function is selected automatically.

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
- Snapshot manifest creation is limited to datasets processed in the same run.
- It does not merge with or update an existing snapshot manifest.
- It is not live trading and never invokes broker APIs.
