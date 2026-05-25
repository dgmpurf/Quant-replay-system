# Historical Backfill Workflow Skeleton v0.1

The historical backfill workflow is a local-only skeleton for building or validating historical market data over a reviewed symbol/date manifest.

It is not a scheduler, broker integration, live trading path, or automated order-placement workflow.

## Purpose

Use `historical-backfill` when the project needs to backfill a reviewed symbol list over a broader date range before relying on local cache-backed research inputs.

The workflow reuses the existing safety chain:

```text
reviewed historical backfill manifest
-> optional date chunks
-> data-source-health when real fetch is explicitly allowed
-> data-source-fetch or reviewed raw_input
-> market-cache-preflight
-> optional market-cache-ingest
```

Cache writes require `--accept-cache-write`. Real network fetches require `--allow-real-data`.

## Relationship To Daily Update

`market-daily-update` is for small incremental local maintenance, often one symbol/day or a short reviewed batch.

`historical-backfill` is for a reviewed historical symbol list and date range. It can split rows into chunks, produce per-symbol/per-chunk task results, and keep failures auditable without turning the project into a scheduler.

Both workflows are preflight-gated and local/manual.

## CLI

Offline dry-run using reviewed local raw files:

```cmd
python -m quant_replay_system.cli historical-backfill --manifest data\raw\manual_manifests\historical_backfill_offline_example.csv --dry-run
```

Manual real fetch dry-run:

```cmd
python -m quant_replay_system.cli historical-backfill --manifest data\raw\manual_manifests\historical_backfill_example.csv --allow-real-data --dry-run
```

Explicit cache write:

```cmd
python -m quant_replay_system.cli historical-backfill --manifest data\raw\manual_manifests\historical_backfill_example.csv --allow-real-data --accept-cache-write
```

Without `--accept-cache-write`, accepted rows do not mutate `data/cache`.

## Manifest

The v0.1 manifest format is CSV.

Required columns:

```text
symbol,source,dataset_type,start_date,end_date,enabled
```

Optional columns:

```text
security_type,preferred_upstream,require_fields,reference_source,strict_provisional,chunk_days,raw_input,metadata_path,notes
```

Example:

```csv
symbol,source,dataset_type,start_date,end_date,enabled,security_type,preferred_upstream,require_fields,reference_source,strict_provisional,chunk_days,raw_input,metadata_path,notes
000001,AKSHARE_OPTIONAL,market,2024-01-01,2024-01-10,true,STOCK,TENCENT,"close,volume,amount",BAOSTOCK_OPTIONAL,false,5,,,AKShare Tencent stock historical backfill demo
600000,BAOSTOCK_OPTIONAL,market,2024-01-01,2024-01-10,true,STOCK,BAOSTOCK,"close,volume,amount",AKSHARE_OPTIONAL,false,5,,,BaoStock stock historical backfill demo
510300,AKSHARE_OPTIONAL,market,2024-01-01,2024-01-10,true,ETF,SINA,"close,volume,amount",,false,5,,,AKShare Sina ETF provisional backfill demo
```

See `docs/examples/historical_backfill_example.csv`.

For deterministic offline verification, fill `raw_input` and optional `metadata_path` with reviewed local raw artifacts. Offline rows do not need `--allow-real-data`, but they still run `market-cache-preflight`.

## Task Statuses

- `PASS`: task completed without warnings.
- `WARN`: task completed with warnings, such as provisional source policy.
- `FAIL`: task failed for an unexpected or unsupported path.
- `SKIPPED_DISABLED`: manifest row has `enabled=false`.
- `BLOCKED_NEEDS_ALLOW_REAL_DATA`: row needs a real fetch and `--allow-real-data` was not supplied.
- `BLOCKED_PREFLIGHT_REJECT`: preflight rejected candidate rows and cache ingest was blocked.
- `BLOCKED_MISSING_RAW_INPUT`: offline row references a missing `raw_input` path.

Rows continue after failures by default. Use `--fail-fast` to stop after the first failed task.

## Artifacts

Artifacts are written under:

```text
outputs/reports/historical_backfill/<backfill_id>/
```

Files:

- `historical_backfill_report.md`
- `historical_backfill_tasks.csv`
- `historical_backfill_results.csv`
- `metadata.json`

The metadata records the manifest path, task result counts, cache write flag, safety audit fields, and known limitations.

## Index, Health, And Status

Historical backfill can produce many per-symbol/per-chunk artifacts. Use the local artifact views before scaling a backfill or approving any cache write:

```cmd
python -m quant_replay_system.cli historical-backfill-index
python -m quant_replay_system.cli historical-backfill-health
python -m quant_replay_system.cli historical-backfill-status
```

`historical-backfill-index` scans `outputs/reports/historical_backfill/` and writes:

```text
outputs/reports/historical_backfill/index/historical_backfill_index_report.md
outputs/reports/historical_backfill/index/historical_backfill_index.csv
outputs/reports/historical_backfill/index/historical_backfill_index.json
outputs/reports/historical_backfill/index/metadata.json
```

The index records `backfill_id`, status, manifest path, task counts, pass/warn/fail/skipped counts, cache-write flag, symbols, date coverage, and report/metadata paths.

`historical-backfill-health` checks artifact completeness:

- `metadata.json` readable
- report exists and includes the no-live-trading/no-broker statement
- task/result CSVs exist and are readable
- referenced reviewed manifest exists when the local path is available
- task/result counts match the metadata summary
- cache-write and local-only safety metadata are present

Health checks artifact integrity only. They do not certify strategy quality or market data correctness.

`historical-backfill-status` summarizes the latest backfill into a workflow stage and next manual action. Stages include:

- `NO_BACKFILL_ARTIFACTS`
- `BACKFILL_DRY_RUN_READY`
- `BACKFILL_WARNINGS_NEED_REVIEW`
- `BACKFILL_PARTIAL_WITH_REJECTIONS`
- `BACKFILL_FAILED`
- `BACKFILL_CACHE_WRITE_READY`
- `BACKFILL_COMPLETED`

A dry-run with expected provisional or known-caveat warnings should be reviewed as `BACKFILL_WARNINGS_NEED_REVIEW`; it is not automatically approved for cache write. Only rerun with `--accept-cache-write` after manual review.

An explicit cache-write run can be classified as `BACKFILL_PARTIAL_WITH_REJECTIONS` when some tasks were accepted and written while other rows were blocked by protective preflight rejection, such as `COMPARISON_FAIL`. The rejected rows remain failures and must be reviewed, but accepted rows are not treated as corrupt merely because the batch also blocked unsafe source rows. The status metadata and reports preserve `accepted_task_count`, `rejected_task_count`, `preflight_rejected_count`, `comparison_failed_count`, `cache_write_partial`, rejected symbols, rejected sources, and rejected issue categories.

If all rows are rejected, no cache write occurs when one was expected, artifacts are unreadable, metadata is missing, or a runtime failure occurred, the status remains `BACKFILL_FAILED`.

`research-status` includes the latest `historical-backfill-status` as a history/cache-building component. It exposes the latest backfill id, stage, task counts, cache-write flag, partial cache-write/rejection fields, and next manual action. Later reviewed export, data-preparation, market-update-handoff, current-candidates, or paper workflow artifacts can take priority for the final unified workflow stage, but historical backfill remains visible as context.

## Safety Boundaries

- No live trading is implemented.
- No broker API is invoked.
- No automated order placement is implemented.
- No scheduler, cron job, background service, or GitHub Actions workflow is added.
- Real fetches require `--allow-real-data`.
- Cache writes require `--accept-cache-write`.
- Generated raw/cache/output artifacts are local and ignored by Git.
- Backfilled data still needs `data-pipeline`, `data-quality`, and `snapshot-quality` before research use.

## Known MVP Limitations

- v0.1 does not optimize source selection or retry policy across symbols.
- It does not run current-candidates or paper workflow.
- It does not certify strategy quality.
- Optional cross-source comparison only runs through `market-cache-preflight` when reference rows already exist in the local cache.
- ETF/Sina fields remain provisional until a second reliable ETF reference source is available.
