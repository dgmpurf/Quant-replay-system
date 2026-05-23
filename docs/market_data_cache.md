# Local Market Data Cache v0.1

The local market data cache stores canonical daily market bars from successful local `raw_data.csv` outputs.

It is local-only. It does not fetch data by itself, call broker APIs, place orders, automate execution, print secrets, or modify `.env`.

## Purpose

The project now has working non-Eastmoney AKShare fallback routes for market data. The cache reduces repeated calls to public endpoints and gives the user a repeatable local source for downstream workflows.

The cache is not data certification. Cached rows must still pass:

```text
data-pipeline -> data-quality -> snapshot-quality -> current-candidates
```

## Storage

Default cache path:

```text
data/cache/market/daily_bars.csv
```

`data/cache/` is ignored by Git. Do not commit cached vendor data.

## Cache Columns

The cache stores:

```text
symbol,trade_date,open,high,low,close,volume,amount,pre_close,adj_factor,is_suspended,limit_up,limit_down,event_time,publish_time,ingest_time,available_time,revision_id,source,upstream_source,successful_function,fetched_at,cache_ingested_at
```

Symbols are read and written as strings. Six-digit China symbols such as `000001`, `510300`, and `159915` must keep their leading zeros.

## Ingest

Ingest a successful raw market file:

```cmd
python -m quant_replay_system.cli market-cache-ingest --input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\AKSHARE_OPTIONAL\market\<run_id>\metadata.json
```

BaoStock market output uses the same canonical raw market schema and can be cached the same way:

```cmd
python -m quant_replay_system.cli market-cache-ingest --input data\raw\BAOSTOCK_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\BAOSTOCK_OPTIONAL\market\<run_id>\metadata.json
```

The optional metadata file fills cache provenance fields such as:

- `upstream_source`
- `successful_function`
- `fetched_at`

The ingest command validates:

- required canonical market columns exist
- `trade_date` is parseable
- `available_time` is parseable when configured
- OHLC values are non-negative
- `high >= low`
- `volume` and `amount` are non-negative
- symbol, source, and revision fields are present

Duplicates are deduplicated by:

```text
symbol + trade_date + source + upstream_source + revision_id
```

The default duplicate policy is `keep_latest`, which keeps the latest incoming row deterministically.

## Query

Query cached bars into a local CSV that can be used by `LOCAL_CSV` pipeline mode:

```cmd
python -m quant_replay_system.cli market-cache-query --symbol 510300 --start-date 2024-01-01 --end-date 2024-05-20 --output data\raw\manual_cache\510300_market.csv
```

Then use the output path in `data-pipeline`:

```cmd
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data\raw\manual_cache\510300_market.csv
```

For current candidates, use a manifest with market, universe, and trading-calendar paths.

## Status

Summarize the cache:

```cmd
python -m quant_replay_system.cli market-cache-status
```

The CLI prints:

- cache path
- row count
- symbol count
- date range
- source counts
- upstream counts
- report path

## Artifacts

Reports are written under:

```text
outputs/reports/market_data_cache/<cache_run_id>/
```

Files:

- `market_cache_report.md`
- `market_cache_summary.csv`
- `market_cache_ingested_rows.csv`
- `metadata.json`

Metadata includes no-live-trading and no-broker-api audit fields.

## Recommended Workflow

```text
data-source-health
-> data-source-fetch
-> market-cache-ingest
-> market-cache-query
-> data-pipeline
-> data-quality
-> snapshot-quality
-> current-candidates
```

For AKShare, run health checks first so the route report identifies whether Tencent, Sina, or Eastmoney is usable. For BaoStock, run `data-source-health` first to confirm the market route is available. If an upstream fails, use a successful fallback route or reviewed `LOCAL_CSV`.

## Safety

- No real network calls are made by the cache itself.
- Automated tests use local/fake CSV data only.
- Cached files are ignored by Git.
- Cache outputs are not trading recommendations.
- No live trading is implemented.
- No broker API is invoked.
- No automated order placement is added.

## Known MVP Limitations

- CSV storage is simple and local; there is no database or parquet dependency.
- Cache deduplication is schema-light and designed for canonical daily bars.
- The cache does not merge or validate universe/trading-calendar data.
- Upstream sources can differ in adjustment, amount, volume, and date coverage semantics.
- BaoStock, AKShare, and Tushare may represent adjustment and amount semantics differently; compare sources before relying on cross-source cache rows.
- Cached market data must still be reviewed through data quality and snapshot quality before research use.
