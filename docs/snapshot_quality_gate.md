# Snapshot Quality Gate v0.1

Snapshot Quality Gate runs data quality checks across a full processed snapshot manifest and decides whether the snapshot is safe to use for replay, batch replay, calibration, or current candidate generation.

It is local-only. It does not call market data APIs, require API tokens, connect to brokers, place orders, or automate execution.

## Purpose

Data Quality Summary Reports check one file at a time. Snapshot Quality Gate checks whether the snapshot works as a complete unit.

The gate protects downstream research from starting with missing or failed required inputs. For MVP v0.1, the required datasets are:

- `market`
- `universe`
- `trading_calendar`

Optional datasets are:

- `benchmark`
- `corporate_actions`

## Snapshot Manifest

The gate expects a local `snapshot_manifest.json` with fields such as:

```json
{
  "snapshot_id": "snapshot_2024_05_20",
  "created_at": "2024-05-20T00:00:00",
  "market_path": "data/processed/market/market_cleaned.csv",
  "universe_path": "data/processed/universe/universe_cleaned.csv",
  "trading_calendar_path": "data/processed/trading_calendar/calendar_cleaned.csv",
  "benchmark_path": "data/processed/benchmark/benchmark_cleaned.csv",
  "corporate_actions_path": "data/processed/corporate_actions/corporate_actions_cleaned.csv",
  "source": "LOCAL_CSV",
  "revision_id": "v1",
  "notes": "local processed snapshot"
}
```

The loader also supports the processed snapshot shape produced by the ingestion module:

```json
{
  "snapshot_id": "snapshot_2024_05_20",
  "processed_files": {
    "market": "data/processed/market/market_cleaned.csv",
    "universe": "data/processed/universe/universe_cleaned.csv",
    "trading_calendar": "data/processed/trading_calendar/calendar_cleaned.csv"
  }
}
```

## PASS / WARN / FAIL

Gate status is calculated from dataset quality results and required/optional dataset rules.

- `PASS`: all required datasets pass and no configured warnings are present.
- `WARN`: required datasets pass, but optional datasets are missing or fail, or non-blocking warnings exist.
- `FAIL`: any required dataset is missing or fails quality checks.

Default behavior:

- A required dataset `FAIL` makes the whole snapshot `FAIL`.
- A required dataset `WARN` makes the whole snapshot `WARN`.
- An optional dataset `FAIL` makes the snapshot `WARN`.
- Missing optional datasets are allowed and recorded as `INFO`.

Strict settings can escalate warnings or optional failures.

## Configuration

Default settings live in `config/default.yaml`:

```yaml
snapshot_quality_gate:
  output_dir: outputs/reports/snapshot_quality
  required_datasets:
    - market
    - universe
    - trading_calendar
  optional_datasets:
    - benchmark
    - corporate_actions
  fail_on_required_dataset_warn: false
  fail_on_optional_dataset_fail: false
  allow_missing_optional_datasets: true
  missing_optional_dataset_severity: INFO
  block_replay_on_fail: true
```

The helper `assert_snapshot_quality_passed(result)` raises a clear error when the gate status is `FAIL`. Replay is not fully wired to call this automatically yet.

## Artifacts

Reports are written to:

```text
outputs/reports/snapshot_quality/<snapshot_id>_<quality_gate_id>/
```

Each run writes:

- `snapshot_quality_gate_report.md`
- `snapshot_quality_summary.csv`
- `dataset_quality_results.csv`
- `dataset_issue_counts.csv`
- `metadata.json`

The `quality_gate_id` is deterministic from the snapshot id, dataset paths, dataset statuses, row counts, issue counts, and gate settings.

## CLI Usage

Run a snapshot gate:

```cmd
python -m quant_replay_system.cli snapshot-quality --manifest data\snapshots\example_snapshot_manifest.json
```

Write artifacts to a custom folder:

```cmd
python -m quant_replay_system.cli snapshot-quality --manifest data\snapshots\example_snapshot_manifest.json --output-dir outputs\reports\snapshot_quality
```

Strict mode exits non-zero on `WARN` as well as `FAIL`:

```cmd
python -m quant_replay_system.cli snapshot-quality --manifest data\snapshots\example_snapshot_manifest.json --strict
```

The command prints status, failed required datasets, report path, and:

```text
No live trading or broker API was invoked.
```

It exits non-zero on `FAIL` by default.

## How This Protects Replay

Replay, batch replay, calibration, walk-forward validation, and candidate generation should only use coherent point-in-time snapshots.

The snapshot quality gate gives the project a clear preflight decision:

- required market rows are present and usable,
- the universe snapshot is structurally valid,
- the trading calendar is available,
- optional benchmark and corporate action data are reviewed without blocking by default.

This creates a single artifact-backed checkpoint before expensive research runs.

## Research Status Linkage

`research-status` may see several historical `snapshot-quality` artifacts under `outputs/reports/snapshot_quality/`. It keeps those artifacts visible, but it now distinguishes standalone snapshot warnings from the snapshot linked to the active workflow chain.

If a reviewed cache export, market-update-handoff, current-candidates run, or paper workflow carries linked snapshot metadata and that linked snapshot status is `PASS`, older standalone snapshot `WARN` artifacts are treated as stale or unrelated context rather than active blockers. If the linked active snapshot is `WARN` or `FAIL`, the warning/error remains actionable and can drive the unified dashboard to `LOCAL_RESEARCH_NEEDS_ATTENTION`.

When no active chain exposes snapshot linkage, `research-status` falls back to the latest standalone snapshot-quality artifact.

## Known MVP Limitations

- The gate reports status; it does not repair bad data.
- Replay orchestration does not automatically block on this gate yet.
- Optional benchmark and corporate action coverage is not cross-checked against the universe yet.
- Missing optional datasets are allowed by default.
- It uses local CSV/mock data only.
- It never invokes live trading or broker APIs.
