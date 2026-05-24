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

## Safety Gates

- Real network fetches require `--allow-real-data`.
- Cache writes require `--accept-cache-write`.
- If preflight returns `REJECT`, cache ingest is skipped even when `--accept-cache-write` is supplied.
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
- `metadata.json`

The metadata records the input raw path, preflight status, whether a cache write occurred, and no-live-trading/no-broker audit fields.

## Recommended Use

Use this workflow for incremental local market data maintenance after the initial historical backfill is already understood.

For a new source or source route, first run targeted health checks and comparison reports manually. Then use the daily update workflow to keep the cache write decision auditable.

After cache query, research inputs still need:

```text
data-pipeline -> data-quality -> snapshot-quality -> current-candidates
```

## Known MVP Limitations

- v0.1 is a local skeleton, not a scheduler.
- It does not automatically build pipeline manifests.
- It does not choose a universal trusted source.
- It does not certify strategy quality.
- It does not rewrite existing cache rows unless `--accept-cache-write` is explicitly supplied and preflight accepts the input.
