# Data Source Strategy v0.1

This document describes the project data-source roadmap for `quant-replay-system`.

The project remains local-first and research-only. Data source work must not add live trading, broker integration, automated order placement, GitHub Actions, secret printing, or real network calls in automated tests.

## Core Position

AKShare is a wrapper over many upstream sources, not a single data vendor. Depending on the function, AKShare may call Eastmoney, Sina, Tencent, exchange pages, CNInfo, fund sources, or other public endpoints.

That means AKShare success or failure should be interpreted by upstream route:

- Eastmoney market history endpoints can be unstable in the current environment.
- AKShare universe and trading-calendar routes may succeed while Eastmoney kline market routes fail.
- Sina and Tencent AKShare interfaces can be useful non-Eastmoney fallback paths.
- A robust local data strategy should not depend on one AKShare endpoint family.

Every raw data path, regardless of source, must still pass:

```text
data-pipeline -> data-quality -> snapshot-quality -> current-candidates
```

Before importing from optional real-data routes, run `data-source-health` to verify route availability and fallback behavior. Successful market outputs can be ingested into the [local market data cache](market_data_cache.md) to reduce repeated public endpoint calls. Health checks and cache hits are diagnostics only; they do not replace data quality or snapshot quality.

When multiple sources overlap in the cache, run `market-cache-compare` before using combined rows. The comparison highlights OHLC, volume, amount, adjustment, coverage, and likely unit/semantic differences without declaring either source as truth.

Use `market-source-policy` for machine-readable field reliability hints by source, upstream route, security type, and field. Health checks answer whether a route can fetch, comparisons answer whether overlapping rows agree, and the policy answers which fields are currently reliable, provisional, unavailable, unstable, or caveated.

Use `market-cache-preflight` before cache ingestion when a raw market file needs an explicit local acceptance decision. The preflight combines schema sanity, source field policy, optional health metadata, and optional cache comparison into `ACCEPT`, `WARN_ACCEPT`, or `REJECT`. It does not mutate cache data and does not replace data-pipeline, data-quality, or snapshot-quality.

Use `market-daily-update` for dry-run-first incremental local cache maintenance. It orchestrates health, fetch-or-existing-raw input, preflight, optional cache ingest, and cache status. It is not a scheduler or trading workflow, and cache writes require explicit `--accept-cache-write`.

For reviewed batches, use a local CSV symbol manifest with `market-daily-update --symbol-manifest`. Disabled rows are skipped, rows that need real fetches are blocked unless `--allow-real-data` is supplied, and cache writes remain explicit. This is controlled local data maintenance, not scheduling or automation.

## Source Categories

### Permanent Local Safety Path

`LOCAL_CSV` remains permanent.

Use it when:

- an upstream API is unavailable,
- a manual reviewed CSV is preferred,
- a vendor response changed schema,
- the workflow needs deterministic local verification,
- automated tests need safe mock/local data.

Reviewed local CSVs should be stored under ignored local paths such as `data/raw/manual_*` or copied through `data-source-fetch --source LOCAL_CSV`.

### AKShare Public Wrapper Route

AKShare remains useful, but should be treated as a route family.

Current role:

- universe snapshots,
- trading calendars,
- some market history where upstream routes work,
- public data exploration and manual local dry runs.

Risk:

- Eastmoney kline endpoints may disconnect or fail with TLS/proxy/network behavior.
- Function names and columns can change.
- Different AKShare functions may return different schemas.

Recommended next AKShare engineering work:

- keep non-Eastmoney market fallback routes healthy where practical,
- prefer Sina/Tencent paths for stock/index market backup and Sina paths for ETF backup before giving up,
- record attempted upstream family and failure reason,
- keep `LOCAL_CSV` fallback first-class.

### BaoStock Free Historical Backup

BaoStock is now available as a guarded optional free backup source for historical market data.

Current role:

- daily historical market backup through `BAOSTOCK_OPTIONAL`,
- local research data preparation,
- cross-checking AKShare market history.

Known considerations:

- coverage and fields may differ from AKShare/Tushare,
- login/session handling is manual-safe and test-mocked,
- v0.1 is market-only; universe and trading calendar are not implemented,
- automated tests must never call real BaoStock/network.

Recommended use:

```cmd
python -m quant_replay_system.cli data-source-health --source BAOSTOCK_OPTIONAL --dataset-type market --symbol 000001 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
python -m quant_replay_system.cli data-source-fetch --source BAOSTOCK_OPTIONAL --dataset-type market --symbol 000001 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
python -m quant_replay_system.cli market-cache-preflight --input data\raw\BAOSTOCK_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\BAOSTOCK_OPTIONAL\market\<run_id>\metadata.json --require-fields close,volume,amount
python -m quant_replay_system.cli market-cache-ingest --input data\raw\BAOSTOCK_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\BAOSTOCK_OPTIONAL\market\<run_id>\metadata.json
python -m quant_replay_system.cli market-cache-compare --symbol 000001 --source-a AKSHARE_OPTIONAL --source-b BAOSTOCK_OPTIONAL
```

If prices match but volume or amount differ, review the comparison diagnostics before deciding whether a source-specific normalization rule is justified. Stable ratios can suggest a unit scale, while unstable ratios usually point to source semantics, adjustment, or field-definition differences. Do not auto-correct cached data from diagnostics alone.

AKShare/Tencent market history has a known source-specific field semantic: `stock_zh_a_hist_tx` exposes the sixth kline field as `amount`, and AKShare documents that field as volume in hands. The adapter maps that field to canonical volume in shares and records mapping warnings. For real manual runs, it also tries a guarded raw Tencent kline path before AKShare's truncated DataFrame path; if the raw turnover field is present, it maps turnover amount from 10k yuan into canonical yuan. If raw turnover is unavailable, the adapter leaves amount unavailable rather than fabricating it. Continue to compare Tencent against BaoStock/Sina when amount or liquidity features depend on turnover value.

Current field reliability policy:

- AKShare/Tencent stock `open`, `high`, `low`, `close`, `volume`, and `amount` are recorded as `RELIABLE` after representative local stock comparisons against BaoStock.
- AKShare/Tencent stock `pre_close` is `CAVEAT_FIRST_WINDOW_ROW` because `600000` showed a first-row source/window-boundary difference.
- BaoStock stock `open`, `high`, `low`, `close`, `volume`, and `amount` are recorded as `RELIABLE` for tested stock cases.
- AKShare/Sina ETF fields are `PROVISIONAL` until compared with another ETF reference source.
- BaoStock ETF fields are `UNAVAILABLE` in the current local run because `510300` and `159915` returned 0 rows.

### Tushare Optional API Route

Tushare can be used later as a token-based optional API source.

Potential role:

- market history,
- universe/security master,
- trading calendar,
- benchmark/index data,
- cross-vendor validation.

Constraints:

- requires `TUSHARE_TOKEN`,
- permissions and point/cost requirements vary by account,
- token must never be printed or written to metadata,
- automated tests must use fake clients and fake tokens only.

### Professional Research Data Route

JQData and RQData are professional research-data candidates.

Potential role:

- cleaner and more consistent research data,
- broader factor and corporate-action coverage,
- more reliable backtesting data contracts.

Constraints:

- account setup, permissions, and cost,
- vendor SDK contracts,
- no real network calls in automated tests,
- no secrets in metadata, logs, or docs.

### Future Live/Broker Channels

QMT and PTrade are future broker/live-trading channels, not current research-data priorities.

They should not be implemented until the research workflow, data source health checks, and manual paper workflow are mature. Any future QMT/PTrade work must be scoped separately and must not silently add order automation.

### Institutional Data Vendors

Wind, iFinD, and Choice are institutional-grade sources.

Potential role:

- high-quality reference data,
- professional data validation,
- institutional research workflows.

Constraints:

- expensive,
- license restricted,
- not needed for current MVP local workflow.

## Recommended Roadmap

1. Free route:
   BaoStock + AKShare Sina/Tencent + `LOCAL_CSV` + local market data cache.
2. Low-cost API route:
   Tushare if permissions and cost make sense.
3. Professional route:
   JQData/RQData for stronger research data contracts.
4. Live route:
   QMT/PTrade later, only after explicit live/broker planning.

## Next Engineering Sequence

Recommended next source-related tasks:

1. BaoStock local dry-run coverage expansion for more representative stock symbols.
2. Tushare permissioned dry-run if cost and account permissions are acceptable.
3. Professional data adapter evaluation for JQData/RQData if local workflow needs stronger coverage.

## Required Data Preparation Path

Every source should produce local raw files first:

```text
data/raw/<source>/<dataset_type>/<run_id>/raw_data.csv
data/raw/<source>/<dataset_type>/<run_id>/metadata.json
```

For market data, successful canonical daily bars may then be cached locally:

```cmd
python -m quant_replay_system.cli market-cache-preflight --input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\AKSHARE_OPTIONAL\market\<run_id>\metadata.json --require-fields close,volume,amount --reference-source BAOSTOCK_OPTIONAL
python -m quant_replay_system.cli market-daily-update --symbol 000001 --start-date 2024-05-20 --end-date 2024-05-20 --source AKSHARE_OPTIONAL --raw-input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\AKSHARE_OPTIONAL\market\<run_id>\metadata.json --dry-run
python -m quant_replay_system.cli market-daily-update --symbol-manifest data\raw\manual_manifests\daily_market_symbols_example.csv --dry-run
python -m quant_replay_system.cli market-cache-ingest --input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\AKSHARE_OPTIONAL\market\<run_id>\metadata.json
python -m quant_replay_system.cli market-cache-compare --symbol 000001 --source-a AKSHARE_OPTIONAL --source-b BAOSTOCK_OPTIONAL
python -m quant_replay_system.cli market-cache-query --symbol 510300 --start-date 2024-01-01 --end-date 2024-05-20 --output data\raw\manual_cache\510300_market.csv
```

Then it must go through:

```cmd
python -m quant_replay_system.cli data-pipeline --manifest <local_manifest.json>
python -m quant_replay_system.cli snapshot-quality --manifest outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date <YYYY-MM-DD> --universe <name> --snapshot-manifest outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json
```

Do not use raw vendor output directly for replay, current candidates, or paper workflow.

## Safety Rules

- Real-data fetches are manual-only.
- `--allow-real-data` is required for optional real-data adapters.
- Automated tests must not call real network APIs.
- `.env` must not be modified or committed.
- Tokens must not be printed or written to metadata.
- Generated `data/raw`, `data/processed`, and `outputs` artifacts must stay untracked.
- No broker API is involved.
- No live trading or automated order placement is implemented.

## Known MVP Limitations

- Current AKShare market history can fail because Eastmoney kline endpoints are unstable in this environment.
- Existing optional adapters are safe manual MVPs, not production data downloaders.
- Cross-vendor reconciliation is not yet implemented.
- BaoStock is implemented as a guarded optional market-only adapter; it is not a workflow default.
- JQData/RQData routes are strategy candidates, not implemented workflow defaults.
- Raw data quality is source-dependent and must always be checked locally.
- Sina/Tencent/Eastmoney AKShare routes can differ in adjustment, amount, volume, and date coverage semantics; compare and quality-check outputs before research use.
- Cache comparison is diagnostic only; it does not resolve which source should be trusted or mutate cached data.
