# Data Preparation E2E Smoke Test v0.1

The Data Preparation E2E smoke test proves the local data preparation path can produce a snapshot that downstream candidate generation can consume without manual stitching.

It is local-only. It does not call market data APIs, require API tokens, connect to brokers, place orders, automate execution, or use network calls in automated tests.

## Purpose

The project now has separate modules for:

- local data source adapters,
- canonical ingestion,
- data quality reports,
- snapshot quality gates,
- current candidate generation.

The smoke test checks the complete handoff:

```text
local CSV manifest -> data-pipeline -> snapshot_manifest.json -> snapshot-quality -> current-candidates
```

## Local Data Preparation Workflow

Use the tiny mock manifest:

```cmd
python -m quant_replay_system.cli data-pipeline --manifest data\mock\data_pipeline_manifest.json
```

That manifest points to:

- `data/mock/prices.csv`
- `data/mock/universe_snapshots.csv`
- `data/mock/trading_calendar.csv`

The pipeline writes processed canonical CSV files and a generated `snapshot_manifest.json`.

## Snapshot Quality Step

Run the generated snapshot manifest through the snapshot quality gate:

```cmd
python -m quant_replay_system.cli snapshot-quality --manifest outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json
```

For the bundled mock files, the required datasets should pass structural quality checks:

- `market`
- `universe`
- `trading_calendar`

## Current Candidates Step

Generate current/as-of-date candidates from the same generated snapshot:

```cmd
python -m quant_replay_system.cli current-candidates --date 2024-01-08 --universe etf_core --top 5 --snapshot-manifest outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json
```

The current-candidate command runs snapshot preflight by default when a manifest is supplied, then writes:

- `current_candidates_report.md`
- `factor_dataset.csv`
- `scored_dataset.csv`
- `candidates.csv`
- `metadata.json`

The automated smoke test loosens candidate-selection thresholds in temporary settings so it verifies workflow wiring and artifact compatibility. A normal CLI run uses the configured production-like thresholds and may produce an empty `candidates.csv` on the tiny mock dataset.

The generated `candidates.csv` is compatible with the manual paper trading workflow:

```cmd
python -m quant_replay_system.cli paper-daily --date 2024-01-08 --candidates outputs\reports\current_candidates\...\candidates.csv
```

## Automated Smoke Test

The automated test `tests/test_data_preparation_e2e.py` uses temporary output folders and local mock CSVs only.

It verifies:

- manifest-mode `data-pipeline` writes `snapshot_manifest.json`,
- the snapshot manifest includes market, universe, and trading calendar processed paths,
- `snapshot-quality` returns `PASS`,
- `current-candidates` can consume the generated manifest,
- `candidates.csv` is readable by pandas,
- `current_candidates_report.md` is written,
- no broker, live trading, or network/API calls are used.

## Expected Outputs

Pipeline artifacts:

```text
outputs/reports/data_pipeline/<pipeline_id>/
```

Snapshot quality artifacts:

```text
outputs/reports/snapshot_quality/<snapshot_id>_<quality_gate_id>/
```

Current candidate artifacts:

```text
outputs/reports/current_candidates/<decision_date>_<universe_name>_<run_id>/
```

## Local-Only Guarantee

This workflow uses `LOCAL_CSV` with mock files. It does not enable real data sources and does not call external services in tests.

Every report in this path includes a no-live-trading statement. The outputs are research and paper-trading inputs only.

## Known MVP Limitations

- The smoke test uses tiny mock CSVs, not full production market data.
- It verifies workflow wiring and artifact compatibility, not strategy quality.
- It does not repair data quality issues.
- It does not include optional benchmark or corporate action datasets.
- It does not run live trading, broker APIs, or real network data fetches.
