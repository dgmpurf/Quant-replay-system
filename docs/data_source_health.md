# Data Source Health Check v0.1

The data source health check is a local pre-import diagnostic layer. It helps decide which local data-source route is available before running `data-source-fetch`, `data-pipeline`, `data-quality`, `snapshot-quality`, or `current-candidates`.

It does not certify data quality, call broker APIs, place orders, or implement live trading.

## What It Checks

Supported MVP checks:

- `LOCAL_CSV`: verifies the CSV path exists, is readable by pandas, and reports row count.
- `MOCK`: verifies the configured mock dataset can be loaded.
- `AKSHARE_OPTIONAL` market routes: checks the configured AKShare fallback route and, by default, individual upstream probes such as Tencent, Sina, and Eastmoney where supported by the symbol type.
- `BAOSTOCK_OPTIONAL` market route: checks guarded BaoStock login/query/logout behavior and whether `query_history_k_data_plus` can return canonical market rows.

The health result records:

- source and dataset type
- symbol and date range
- requested upstream
- attempted upstreams and functions
- successful upstream and function
- PASS / WARN / FAIL
- row count
- latency in milliseconds
- safe error type and message
- recommended fallback
- report and metadata paths
- no-live-trading / no-broker-api flags

## AKShare Route Semantics

For AKShare market checks, the configured route row is the active availability result. Individual upstream probes remain visible in the report.

For example, if Eastmoney fails but Tencent or Sina succeeds through the configured fallback order, the active route can still be PASS. The Eastmoney failure stays visible as a route diagnostic so the user can understand why fallback was needed.

Real AKShare checks require:

```cmd
python -m quant_replay_system.cli data-source-health --source AKSHARE_OPTIONAL --dataset-type market --symbol 000001 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

ETF example:

```cmd
python -m quant_replay_system.cli data-source-health --source AKSHARE_OPTIONAL --dataset-type market --symbol 510300 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

Without `--allow-real-data`, AKShare health returns a blocked WARN result and does not import or call AKShare.

## BaoStock Route Semantics

BaoStock health checks are manual-only and market-only in v0.1. The check uses the same guarded fetch path as `data-source-fetch`, including lazy import and no-live-trading/no-broker guardrails.

Example:

```cmd
python -m quant_replay_system.cli data-source-health --source BAOSTOCK_OPTIONAL --dataset-type market --symbol 000001 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

Without `--allow-real-data`, BaoStock health returns a blocked WARN result and does not import or call BaoStock.

If BaoStock succeeds, the health result reports:

- `successful_upstream=BAOSTOCK`
- `successful_function=query_history_k_data_plus`
- row count and latency
- raw artifact and metadata paths

If BaoStock fails, use the safe diagnostic message to decide whether to retry later, use AKShare Tencent/Sina routes, or fall back to reviewed `LOCAL_CSV`.

## LOCAL_CSV Example

```cmd
python -m quant_replay_system.cli data-source-health --source LOCAL_CSV --dataset-type market --input data\raw\manual_market.csv
```

Use `LOCAL_CSV` when upstream APIs are unavailable, schemas have changed, or a reviewed vendor export is preferred.

## Outputs

Artifacts are written under:

```text
outputs/reports/data_source_health/<health_check_id>/
```

Files:

- `data_source_health_report.md`
- `data_source_health_results.csv`
- `data_source_health_summary.csv`
- `metadata.json`

Metadata never stores API tokens or secrets.

## Recommended Use

Run health checks before importing real or manually reviewed data:

```text
data-source-health -> data-source-fetch -> market-cache-ingest -> market-cache-query -> data-pipeline -> data-quality -> snapshot-quality -> current-candidates
```

If a route fails, use the recommended fallback from the report. For AKShare market data, Eastmoney instability should trigger Sina/Tencent fallback or reviewed `LOCAL_CSV` fallback. For BaoStock failures, retry later, use AKShare routes that are healthy, or use reviewed `LOCAL_CSV`.

For market data that succeeds, use [market_data_cache.md](market_data_cache.md) to cache the canonical `raw_data.csv` locally before building repeatable pipeline inputs.

## Safety

- Real network checks are manual-only.
- `--allow-real-data` is required for AKShare and BaoStock real checks.
- Automated tests use fake/local data only.
- No live trading is implemented.
- No broker API is invoked.
- No automated order placement is added.
- Secrets are not printed or written to metadata.

## Known MVP Limitations

- Health checks prove route availability for the requested small sample only.
- Different upstreams can differ in adjustment, amount, volume, and date coverage semantics.
- A PASS health check is not data quality certification.
- All raw outputs still need `data-pipeline`, `data-quality`, and `snapshot-quality`.
- Tushare, JQData, or RQData adapters should continue to plug into the same local health-check pattern.
