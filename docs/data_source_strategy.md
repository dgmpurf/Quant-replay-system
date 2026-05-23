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

BaoStock is a candidate free backup source for historical market data.

Potential role:

- daily stock/index historical market backup,
- local research data preparation,
- cross-checking AKShare market history.

Known considerations:

- coverage and fields may differ from AKShare/Tushare,
- login/session handling must be manual-safe and test-mocked,
- automated tests must never call real BaoStock/network.

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

1. BaoStock Optional Adapter.
2. Tushare Optional Adapter if cost and permission are acceptable.
3. Professional data adapter evaluation for JQData/RQData if local workflow needs stronger coverage.

## Required Data Preparation Path

Every source should produce local raw files first:

```text
data/raw/<source>/<dataset_type>/<run_id>/raw_data.csv
data/raw/<source>/<dataset_type>/<run_id>/metadata.json
```

For market data, successful canonical daily bars may then be cached locally:

```cmd
python -m quant_replay_system.cli market-cache-ingest --input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\AKSHARE_OPTIONAL\market\<run_id>\metadata.json
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
- Local market data caching is not yet implemented.
- BaoStock/JQData/RQData routes are strategy candidates, not implemented workflow defaults.
- Raw data quality is source-dependent and must always be checked locally.
- Sina/Tencent/Eastmoney AKShare routes can differ in adjustment, amount, volume, and date coverage semantics; compare and quality-check outputs before research use.
