# Data Preparation Artifact Health Check v0.1

The Data Preparation Artifact Health Check validates that indexed data preparation artifacts still exist and are readable.

It is local-only and does not call market data APIs, connect to brokers, place orders, or automate execution.

## Why It Exists

After data preparation runs, artifact paths can become stale if folders are moved, files are deleted, or metadata is edited manually. The health check verifies that a consolidated data preparation index still points to usable local files before replay, current-candidate generation, or paper-trading handoff.

## Checks Performed

The health check verifies:

- `metadata_path` exists and is JSON-readable.
- `report_path` exists and is markdown-readable.
- `snapshot_manifest_path` exists and is JSON-readable when present.
- `processed_path` exists and is CSV-readable when present.
- `candidates_path` exists and is CSV-readable for current-candidate artifacts.
- Current-candidate `candidates.csv` is not empty.
- Current-candidate `candidates.csv` contains `symbol`, `final_score`, and `action`.
- Snapshot-quality status is `PASS`, `WARN`, or `FAIL` when present.
- Data-quality issue counts are numeric when present.
- Required metadata fields are present for each artifact type.
- Markdown reports include the no-live-trading safety statement.
- Broken artifact references are reported as errors.

## Status

- `PASS`: no warnings or errors.
- `WARN`: warnings only.
- `FAIL`: one or more errors.

## Issue Codes

- `MISSING_PATH_VALUE`
- `FILE_NOT_FOUND`
- `CSV_UNREADABLE`
- `JSON_UNREADABLE`
- `CSV_EMPTY`
- `MISSING_REQUIRED_METADATA_FIELD`
- `MISSING_NO_LIVE_TRADING_STATEMENT`
- `BROKEN_ARTIFACT_REFERENCE`
- `UNSUPPORTED_ARTIFACT_TYPE`
- `INVALID_STATUS`
- `INVALID_NUMERIC_FIELD`
- `MISSING_REQUIRED_CANDIDATE_COLUMN`

## Outputs

The default output folder is:

```text
outputs/reports/data_preparation/health/<health_check_id>/
```

It writes:

- `data_preparation_artifact_health_report.md`
- `data_preparation_artifact_health_issues.csv`
- `data_preparation_artifact_health_summary.csv`
- `metadata.json`

## CLI Usage

Run from an existing index:

```powershell
python -m quant_replay_system.cli data-prep-health --index outputs/reports/data_preparation/index/data_preparation_artifact_index.csv
```

Scan a reports root if no index has been written yet:

```powershell
python -m quant_replay_system.cli data-prep-health --root outputs/reports
```

Strict mode exits non-zero on `WARN`:

```powershell
python -m quant_replay_system.cli data-prep-health --index outputs/reports/data_preparation/index/data_preparation_artifact_index.csv --strict
```

Allow warnings in strict workflows:

```powershell
python -m quant_replay_system.cli data-prep-health --index outputs/reports/data_preparation/index/data_preparation_artifact_index.csv --strict --allow-warn
```

## Known MVP Limitations

- The health check validates artifact existence/readability and lightweight schemas only.
- It does not rerun the underlying data pipeline or quality checks.
- It does not compare artifact contents against source data.
- It does not fetch real data, call APIs, connect to brokers, or place orders.
