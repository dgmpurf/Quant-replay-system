# Local Daily Market Update Workflow Skeleton v0.1

The local daily market update workflow is a preflight-gated wrapper for maintaining the local market cache.

It is local-only. It is not a scheduler, broker integration, live trading path, or automated order-placement workflow.

## Purpose

The workflow orchestrates the safe data-maintenance steps that are normally run by hand:

```text
data-source-health
-> data-source-fetch or existing raw input
-> market-cache-preflight
-> optional market-cache-ingest
-> market-cache-status
```

The default posture is dry-run-first. Cache writes require the explicit `--accept-cache-write` flag.

## Relationship To Other Tools

- `data-source-health` checks whether a source/upstream route is reachable.
- `market-cache-preflight` checks candidate raw rows against schema sanity, source field policy, optional health metadata, and optional cache comparison.
- `market-cache-ingest` writes accepted rows into the local cache.
- `market-cache-status` summarizes the cache after the attempted update.
- `market-update-handoff` converts accepted or warn-accepted offline update rows into a local data-pipeline snapshot dry run.
- `data-pipeline`, `data-quality`, and `snapshot-quality` are still required before research use.

## CLI

Dry-run using an existing raw file:

```cmd
python -m quant_replay_system.cli market-daily-update --symbol 000001 --start-date 2024-01-01 --end-date 2024-05-20 --source AKSHARE_OPTIONAL --raw-input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\AKSHARE_OPTIONAL\market\<run_id>\metadata.json --dry-run
```

Dry-run with a reference source already in the local cache:

```cmd
python -m quant_replay_system.cli market-daily-update --symbol 000001 --start-date 2024-01-01 --end-date 2024-05-20 --source AKSHARE_OPTIONAL --raw-input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\AKSHARE_OPTIONAL\market\<run_id>\metadata.json --reference-source BAOSTOCK_OPTIONAL --dry-run
```

Manual real fetch, still without cache write:

```cmd
python -m quant_replay_system.cli market-daily-update --symbol 000001 --start-date 2024-05-20 --end-date 2024-05-20 --source AKSHARE_OPTIONAL --allow-real-data --dry-run
```

Ingest accepted rows into the cache:

```cmd
python -m quant_replay_system.cli market-daily-update --symbol 000001 --start-date 2024-05-20 --end-date 2024-05-20 --source AKSHARE_OPTIONAL --raw-input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\AKSHARE_OPTIONAL\market\<run_id>\metadata.json --accept-cache-write
```

Without `--accept-cache-write`, accepted rows are not ingested.

Reviewed symbol manifest dry-run:

```cmd
python -m quant_replay_system.cli market-daily-update --symbol-manifest data\raw\manual_manifests\daily_market_symbols_example.csv --dry-run
```

Manual real fetch for manifest rows, still without cache write:

```cmd
python -m quant_replay_system.cli market-daily-update --symbol-manifest data\raw\manual_manifests\daily_market_symbols_example.csv --allow-real-data --dry-run
```

Manifest cache writes are also explicit:

```cmd
python -m quant_replay_system.cli market-daily-update --symbol-manifest data\raw\manual_manifests\daily_market_symbols_example.csv --allow-real-data --accept-cache-write
```

`--fail-fast` stops after the first failed manifest row. Without it, enabled rows continue independently and row-level failures are recorded in the symbol results CSV.

Offline reviewed symbol manifest dry-run:

```cmd
python -m quant_replay_system.cli market-daily-update --symbol-manifest data\raw\manual_manifests\daily_market_symbols_offline_example.csv --dry-run
```

An offline manifest supplies `raw_input` and optional `metadata_path` for each row. It can run without `--allow-real-data` because no source fetch is needed. It still runs `market-cache-preflight`, still applies source policy, and still does not write cache unless `--accept-cache-write` is supplied.

After an offline manifest dry-run, use `market-update-handoff` to merge accepted rows into a local batch market CSV and run:

```text
data-pipeline -> snapshot-quality -> current-candidates --selection-profile demo
```

That handoff remains cache-free and local-only.

## Symbol Manifest

The v0.1 manifest format is CSV.

Required columns:

```text
symbol,source,dataset_type,start_date,end_date,enabled
```

Optional reviewed columns:

```text
security_type,preferred_upstream,require_fields,reference_source,strict_provisional,notes
```

Optional local dry-run columns:

```text
raw_input,metadata_path,raw_output_dir,revision_id
```

When `raw_input` is present, the row uses that existing canonical raw market CSV and does not need a real fetch. When `raw_input` is absent for a real source such as `AKSHARE_OPTIONAL` or `BAOSTOCK_OPTIONAL`, `--allow-real-data` is required or the row is recorded as `BLOCKED_NEEDS_ALLOW_REAL_DATA`.

If `raw_input` is present but missing on disk, the row is recorded as `BLOCKED_MISSING_RAW_INPUT`. If `metadata_path` is supplied but missing, the row is recorded as `BLOCKED_MISSING_METADATA`. Metadata is optional, but when present it is used for source/upstream provenance in preflight and cache ingest.

Example:

```csv
symbol,source,dataset_type,start_date,end_date,enabled,security_type,preferred_upstream,require_fields,reference_source,strict_provisional,notes
000001,AKSHARE_OPTIONAL,market,2024-05-20,2024-05-20,true,STOCK,TENCENT,"close,volume,amount",BAOSTOCK_OPTIONAL,false,Shenzhen stock demo
600000,AKSHARE_OPTIONAL,market,2024-05-20,2024-05-20,true,STOCK,TENCENT,"close,volume,amount",BAOSTOCK_OPTIONAL,false,Shanghai stock demo
510300,AKSHARE_OPTIONAL,market,2024-05-20,2024-05-20,true,ETF,SINA,"close,volume,amount",,false,ETF provisional demo
159915,AKSHARE_OPTIONAL,market,2024-05-20,2024-05-20,true,ETF,SINA,"close,volume,amount",,false,ETF provisional demo
```

See `docs/examples/daily_market_symbols_example.csv`.

Offline example with reviewed local raw files:

```csv
symbol,source,dataset_type,start_date,end_date,enabled,security_type,preferred_upstream,require_fields,reference_source,strict_provisional,raw_input,metadata_path,notes
000001,AKSHARE_OPTIONAL,market,2024-05-20,2024-05-20,true,STOCK,TENCENT,"close,volume,amount",BAOSTOCK_OPTIONAL,false,data/raw/example_reviewed_market/000001/raw_data.csv,data/raw/example_reviewed_market/000001/metadata.json,Offline reviewed Shenzhen stock demo path
510300,AKSHARE_OPTIONAL,market,2024-05-20,2024-05-20,true,ETF,SINA,"close,volume,amount",,false,data/raw/example_reviewed_market/510300/raw_data.csv,data/raw/example_reviewed_market/510300/metadata.json,Offline reviewed ETF provisional demo path
```

See `docs/examples/daily_market_symbols_offline_example.csv`. The paths are illustrative; for a local dry run, copy the file to `data/raw/manual_manifests/` and replace paths with ignored local raw artifacts.

Row-level statuses:

- `PASS`: row completed without warnings.
- `WARN`: row completed with warnings, such as provisional source policy.
- `FAIL`: row failed for an unexpected reason.
- `SKIPPED_DISABLED`: manifest row has `enabled=false`.
- `BLOCKED_NEEDS_ALLOW_REAL_DATA`: row needs a real fetch and `--allow-real-data` was not supplied.
- `BLOCKED_MISSING_RAW_INPUT`: row references a missing offline `raw_input` path.
- `BLOCKED_MISSING_METADATA`: row references a missing offline `metadata_path`.
- `BLOCKED_PREFLIGHT_REJECT`: preflight rejected the candidate rows and cache ingest was blocked.

## Safety Gates

- Real network fetches require `--allow-real-data`.
- Cache writes require `--accept-cache-write`.
- If preflight returns `REJECT`, cache ingest is skipped even when `--accept-cache-write` is supplied.
- Manifest rows continue after failures by default; use `--fail-fast` to stop on the first failed row.
- Automated tests use fake/local CSV data only.
- No live trading, broker API, or order automation is invoked.

## Artifacts

Artifacts are written under:

```text
outputs/reports/market_daily_update/<update_id>/
```

Files:

- `market_daily_update_report.md`
- `market_daily_update_steps.csv`
- `market_daily_update_symbol_results.csv`
- `metadata.json`

The metadata records input paths, row-level statuses, preflight status, whether any cache write occurred, and no-live-trading/no-broker audit fields.

## Recommended Use

Use this workflow for incremental local market data maintenance after the initial historical backfill is already understood.

For a new source or source route, first run targeted health checks and comparison reports manually. Then use the daily update workflow to keep the cache write decision auditable.

After cache query, research inputs still need:

```text
data-pipeline -> data-quality -> snapshot-quality -> current-candidates
```

## Known MVP Limitations

- v0.1 is a local skeleton, not a scheduler.
- It does not automatically build pipeline manifests by itself; use [market_update_handoff.md](market_update_handoff.md) for the reviewed offline batch to snapshot dry-run.
- It does not choose a universal trusted source.
- It does not certify strategy quality.
- It does not rewrite existing cache rows unless `--accept-cache-write` is explicitly supplied and preflight accepts the input.
