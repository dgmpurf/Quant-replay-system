# Data Preparation Workflow Status Dashboard v0.1

The Data Preparation Workflow Status Dashboard is a local-only overview report for the data preparation chain.

It answers:

- What is the latest data-pipeline run?
- Did data-quality pass?
- Did snapshot-quality pass?
- Did current-candidates run successfully?
- Did data-prep-index run?
- Did data-prep-health pass?
- Are there missing artifacts, warnings, or errors?
- What is the next manual action?

No broker or live trading integration is invoked.

## Scanned Components

The dashboard scans local metadata under:

- `outputs/reports/data_pipeline/`
- `outputs/reports/data_quality/`
- `outputs/reports/snapshot_quality/`
- `outputs/reports/current_candidates/`
- `outputs/reports/data_preparation/index/`
- `outputs/reports/data_preparation/health/`

It reads existing `metadata.json` files and report paths only. It does not rerun data preparation workflows.

## Stage Meanings

- `NO_DATA_PIPELINE`: no local data-pipeline artifact was found.
- `DATA_PIPELINE_READY`: a data-pipeline artifact exists; data-quality is next.
- `DATA_QUALITY_READY`: data-quality exists; snapshot-quality is next.
- `SNAPSHOT_READY`: a snapshot manifest appears available; snapshot-quality is next.
- `SNAPSHOT_QUALITY_READY`: snapshot-quality exists; current-candidates is next.
- `CURRENT_CANDIDATES_READY`: current-candidates exists; data-prep-index is next.
- `DATA_PREP_INDEX_READY`: data-prep-index exists; data-prep-health is next.
- `DATA_PREP_HEALTH_READY`: health metadata exists and the workflow can move forward.
- `DATA_PREP_WORKFLOW_COMPLETE`: the local data-prep chain is indexed and healthy.
- `DATA_PREP_NEEDS_ATTENTION`: a warning or error needs review.

## Next Manual Action Logic

The dashboard recommends one next action based on the inferred stage:

- Run `data-pipeline`.
- Run `data-quality`.
- Run `snapshot-quality`.
- Run `current-candidates`.
- Run `data-prep-index`.
- Run `data-prep-health`.
- Review warnings/errors.
- Proceed to `current-to-paper`.

The recommendation is intentionally conservative. A `FAIL` or material warning keeps the workflow in `DATA_PREP_NEEDS_ATTENTION` until the user reviews the artifact reports.

## CLI Usage

```powershell
python -m quant_replay_system.cli data-prep-status --root outputs/reports
```

With filters:

```powershell
python -m quant_replay_system.cli data-prep-status --root outputs/reports --decision-date 2024-01-08 --universe etf_core
```

With explicit component roots:

```powershell
python -m quant_replay_system.cli data-prep-status `
  --data-pipeline-root outputs/reports/data_pipeline `
  --data-quality-root outputs/reports/data_quality `
  --snapshot-quality-root outputs/reports/snapshot_quality `
  --current-candidates-root outputs/reports/current_candidates
```

Strict mode exits non-zero when the dashboard status is `WARN`:

```powershell
python -m quant_replay_system.cli data-prep-status --root outputs/reports --strict
```

## Outputs

The default output folder is:

```text
outputs/reports/data_preparation/workflow_status/<workflow_status_id>/
```

It writes:

- `data_preparation_workflow_status_report.md`
- `data_preparation_workflow_status.csv`
- `data_preparation_workflow_summary.csv`
- `metadata.json`

## Relationship To Other Modules

- `data-pipeline` creates processed canonical files and optional snapshot manifests.
- `data-quality` validates individual canonical data files.
- `snapshot-quality` gates the snapshot as a whole.
- `current-candidates` generates paper-trading candidate inputs from local snapshots.
- `data-prep-index` consolidates artifact discovery.
- `data-prep-health` verifies indexed artifact files still exist and are readable.
- `data-prep-status` summarizes the chain and tells the user what to do next.

## Known MVP Limitations

- The dashboard scans local metadata only.
- It does not rerun pipeline, quality, snapshot, or current-candidate generation.
- It does not repair missing or broken artifact paths.
- It does not fetch real data, call APIs, connect to brokers, or place orders.
