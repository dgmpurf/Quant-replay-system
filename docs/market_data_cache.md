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

Before ingesting new rows, run the source-policy-aware preflight:

```cmd
python -m quant_replay_system.cli market-cache-preflight --input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\AKSHARE_OPTIONAL\market\<run_id>\metadata.json --require-fields close,volume,amount
```

The preflight returns `ACCEPT`, `WARN_ACCEPT`, or `REJECT`. It checks schema sanity, field reliability policy, optional health metadata, and optional cross-source comparison. It does not mutate the cache.

For a dry-run-first wrapper around health/fetch-or-raw/preflight/status, use:

```cmd
python -m quant_replay_system.cli market-daily-update --symbol 000001 --start-date 2024-05-20 --end-date 2024-05-20 --source AKSHARE_OPTIONAL --raw-input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\AKSHARE_OPTIONAL\market\<run_id>\metadata.json --dry-run
```

The update workflow does not write to the cache unless `--accept-cache-write` is explicitly supplied and preflight accepts the input.

For reviewed historical ranges, use `historical-backfill`:

```cmd
python -m quant_replay_system.cli historical-backfill --manifest data\raw\manual_manifests\historical_backfill_example.csv --dry-run
```

Historical backfill can split manifest rows into date chunks, use reviewed offline raw files, and optionally ingest accepted chunks when `--accept-cache-write` is supplied. It is for local research history construction, not live trading or scheduling.

For reviewed batches, use a symbol manifest:

```cmd
python -m quant_replay_system.cli market-daily-update --symbol-manifest data\raw\manual_manifests\daily_market_symbols_example.csv --dry-run
```

The manifest workflow records one row per symbol in `market_daily_update_symbol_results.csv`. Disabled rows are skipped, real-fetch rows are blocked without `--allow-real-data`, and cache writes still require `--accept-cache-write`.

For deterministic offline batch smoke tests, use a reviewed manifest with `raw_input` and `metadata_path` columns:

```cmd
python -m quant_replay_system.cli market-daily-update --symbol-manifest data\raw\manual_manifests\daily_market_symbols_offline_example.csv --dry-run
```

Offline rows do not call real data sources, but they still run `market-cache-preflight` and still need `--accept-cache-write` before cache mutation.

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

The cache can intentionally contain multiple source variants for the same `symbol + trade_date`, for example AKShare/Tencent and BaoStock rows for the same stock. `data-pipeline` expects one market row per `symbol + trade_date`, so use explicit source filters when exporting slices for pipeline use:

```cmd
python -m quant_replay_system.cli market-cache-query --symbol 000001 --start-date 2024-01-02 --end-date 2024-01-05 --source AKSHARE_OPTIONAL --upstream-source TENCENT --output data\raw\manual_cache\000001_tencent_market.csv
python -m quant_replay_system.cli market-cache-query --symbol 000001 --start-date 2024-01-02 --end-date 2024-01-05 --source BAOSTOCK_OPTIONAL --upstream-source BAOSTOCK --output data\raw\manual_cache\000001_baostock_market.csv
```

Without `--source` or `--upstream-source`, the query keeps existing behavior and returns all matching cached source variants. It does not silently deduplicate or choose a trusted source.

Then use the output path in `data-pipeline`:

```cmd
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data\raw\manual_cache\510300_market.csv
```

For current candidates, use a manifest with market, universe, and trading-calendar paths.

## Reviewed Export

For multi-symbol or multi-range cache exports, use a reviewed source/upstream manifest instead of stitching together ad hoc queries:

```cmd
python -m quant_replay_system.cli market-cache-export --manifest data\raw\manual_manifests\reviewed_cache_export_example.csv --build-pipeline-manifest --universe data\raw\LOCAL_CSV\universe_overlay\<overlay_id>\raw_data.csv --trading-calendar data\raw\AKSHARE_OPTIONAL\trading_calendar\<run_id>\raw_data.csv
```

`market-cache-export` reads the local cache, requires explicit `source` and `upstream_source` for each enabled manifest row, writes `data\raw\manual_cache_exports\<export_id>\market_raw_data.csv`, and rejects duplicate `symbol + trade_date` rows before pipeline use. It does not mutate the cache or choose a trusted source automatically.

To draft an explicit reviewed manifest from local cache coverage and field reliability policy, use:

```cmd
python -m quant_replay_system.cli market-cache-export-plan --manifest data\raw\manual_manifests\market_cache_export_policy_request_example.csv
```

The planner writes a recommended manifest for review. It does not export, mutate cache, or silently choose a source for downstream workflows.

See [market_cache_export.md](market_cache_export.md).

After creating reviewed exports, use the export artifact views before repeating downstream snapshot work:

```cmd
python -m quant_replay_system.cli market-cache-export-index
python -m quant_replay_system.cli market-cache-export-health
python -m quant_replay_system.cli market-cache-export-status
```

The index discovers reviewed export folders, health verifies exported CSV completeness and duplicate-key safety, and status summarizes whether the latest export is ready for `data-pipeline`, `data-quality`, `snapshot-quality`, or current-candidate use. These commands inspect local artifacts only and do not mutate the market cache.

## Compare Sources

When the cache contains the same symbol/date from multiple sources, compare them before relying on combined cached data:

```cmd
python -m quant_replay_system.cli market-cache-compare --symbol 000001 --start-date 2024-01-01 --end-date 2024-05-20 --source-a AKSHARE_OPTIONAL --source-b BAOSTOCK_OPTIONAL
```

For source/upstream/security-type field reliability policy, run:

```cmd
python -m quant_replay_system.cli market-source-policy
```

The policy complements comparison reports. Health checks show route availability, comparisons show whether overlapping rows agree, and the policy records which fields are reliable, provisional, unavailable, unstable, or caveated.

The comparison performs a full outer join on `symbol + trade_date`, so it reports both overlapping dates and source-only coverage gaps.

Row-level comparison fields include:

- source and upstream source for each side
- OHLC, volume, amount, `pre_close`, and `adj_factor` values for each side
- absolute differences and percentage differences
- source A/source B volume and amount ratios
- `amount / (close * volume)` ratios for each side
- unit/semantic diagnostic flags and reasons
- source field reliability policy hints
- `row_match_status`: `MATCHED`, `SOURCE_A_ONLY`, or `SOURCE_B_ONLY`
- `tolerance_status`: `PASS`, `WARN`, or `FAIL`

Default tolerances:

```yaml
market_data_comparison:
  price_abs_tolerance: 0.0001
  price_pct_tolerance: 0.001
  volume_pct_tolerance: 0.05
  amount_pct_tolerance: 0.05
  unit_ratio_stability_tolerance: 0.05
  unit_ratio_far_from_one_tolerance: 0.05
```

Interpretation:

- Large price differences may indicate adjustment or ex-rights handling mismatch.
- Large volume or amount differences may indicate unit differences or source-specific semantics.
- Stable volume or amount ratios far from `1.0` can indicate a likely source-specific unit scale.
- Matched prices with unstable volume/amount ratios are treated as source semantics differences, not an automatic correction opportunity.
- AKShare/Tencent `stock_zh_a_hist_tx` volume is source-specific: AKShare's DataFrame field named `amount` has unit `手`, so it is mapped to canonical volume in shares.
- For real manual Tencent runs, the adapter attempts a guarded raw Tencent response path before using AKShare's truncated DataFrame. If the verified raw turnover field is present, `turnover_amount_10k_yuan` is mapped to canonical `amount` in yuan; otherwise amount remains unavailable and is reported through mapping warnings.
- Source-only rows indicate coverage gaps.
- The report does not declare either source as truth.
- The comparison never rewrites cached rows. Any source-specific normalization rule must be added explicitly after review.
- Policy hints do not override comparison tolerances, data-quality, or snapshot-quality. They only record current field-level source confidence.

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
- source filter and upstream-source filter when querying
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

Source comparison reports are written under:

```text
outputs/reports/market_data_comparison/<comparison_id>/
```

Files:

- `market_data_comparison_report.md`
- `market_data_comparison_rows.csv`
- `market_data_comparison_summary.csv`
- `metadata.json`

Field reliability policy reports are written under:

```text
outputs/reports/market_source_policy/<policy_report_id>/
```

Files:

- `market_source_policy_report.md`
- `market_source_policy.csv`
- `metadata.json`

## Recommended Workflow

```text
data-source-health
-> data-source-fetch
-> market-cache-preflight
-> market-cache-ingest
-> market-cache-compare
-> market-cache-query
-> data-pipeline
-> data-quality
-> snapshot-quality
-> current-candidates
```

For incremental local maintenance after initial source validation, `market-daily-update` can replace the first four manual steps while preserving the explicit cache-write gate.

For reviewed exports into `data-pipeline`, use `market-cache-export` after cache comparison/source review when multiple cached source variants exist. Use `market-cache-export-plan` first if you want a policy-aware draft manifest, then inspect it before exporting.

For AKShare, run health checks first so the route report identifies whether Tencent, Sina, or Eastmoney is usable. For BaoStock, run `data-source-health` first to confirm the market route is available. If an upstream fails, use a successful fallback route or reviewed `LOCAL_CSV`.

## Safety

- No real network calls are made by the cache itself.
- The daily update wrapper only performs real fetches when `--allow-real-data` is supplied.
- The daily update wrapper only mutates cache when `--accept-cache-write` is supplied.
- Reviewed cache export does not mutate cache.
- Automated tests use local/fake CSV data only.
- Cached files are ignored by Git.
- Cache outputs are not trading recommendations.
- Source comparison reports are diagnostics only and do not certify data quality.
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
