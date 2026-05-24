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
