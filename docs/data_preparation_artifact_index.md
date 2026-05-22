# Data Preparation Artifact Index v0.1

The Data Preparation Artifact Index is a local-only navigation layer for artifacts produced before replay or current-candidate generation.

It scans existing report folders and builds one consolidated index across:

- `outputs/reports/data_pipeline/`
- `outputs/reports/data_quality/`
- `outputs/reports/snapshot_quality/`
- `outputs/reports/current_candidates/`

No broker or live trading integration is invoked.

## Why It Exists

The data preparation workflow now creates many folders: raw-to-processed pipeline reports, per-file data quality reports, snapshot quality gate reports, and current-candidate outputs. The index gives the user one stable place to find these artifacts before running replay, generating current candidates, or handing candidates into paper trading.

## Indexed Fields

The index writes rows with fields such as:

- `artifact_type`
- `artifact_id`
- `created_at`
- `status`
- `dataset_type`
- `snapshot_id`
- `decision_date`
- `universe_name`
- `report_path`
- `metadata_path`
- `snapshot_manifest_path`
- `processed_path`
- `candidates_path`
- `issue_count`
- `warning_count`
- `error_count`
- `row_count`
- `no_live_trading_statement_present`

Supported `artifact_type` values are:

- `DATA_PIPELINE`
- `DATA_QUALITY`
- `SNAPSHOT_QUALITY`
- `CURRENT_CANDIDATES`

## Outputs

The default output folder is:

```text
outputs/reports/data_preparation/index/
```

It writes:

- `data_preparation_artifact_index.md`
- `data_preparation_artifact_index.csv`
- `data_preparation_artifact_index.json`
- `metadata.json`

## CLI Usage

```powershell
python -m quant_replay_system.cli data-prep-index --root outputs/reports
```

Filter by artifact type:

```powershell
python -m quant_replay_system.cli data-prep-index --root outputs/reports --artifact-type current_candidates
```

Include folders that are missing `metadata.json`:

```powershell
python -m quant_replay_system.cli data-prep-index --root outputs/reports --include-missing-metadata
```

## Relationship To Other Modules

- `data-pipeline` creates processed paths and optional snapshot manifests.
- `data-quality` checks individual canonical data files.
- `snapshot-quality` gates full snapshot manifests.
- `current-candidates` produces paper-trading candidate inputs.
- `data-prep-index` discovers all of these local artifacts in one place.

## Known MVP Limitations

- The index reads existing metadata and report files only.
- It does not rerun ingestion, data quality, snapshot quality, or candidate generation.
- It does not repair stale paths.
- It does not fetch real data, call APIs, connect to brokers, or place orders.
