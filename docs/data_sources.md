# Market Data Source Adapter Framework v0.1

The Market Data Source Adapter Framework is the local-safe raw data entry layer before canonical ingestion.

It does not call broker APIs, place orders, automate execution, require API tokens, or make network calls in automated tests.

## Purpose

The project can already ingest canonical local CSV files. Data source adapters add one step before ingestion:

```text
source adapter -> data/raw/... -> ingestion -> data/processed/... -> snapshot quality -> current candidates
```

The adapter layer gives each future source a consistent contract without mixing vendor-specific fetching into replay, scoring, or paper trading.

For the broader source roadmap across AKShare upstream routes, BaoStock, Tushare, JQData/RQData, institutional vendors, and permanent `LOCAL_CSV` fallback, see [data_source_strategy.md](data_source_strategy.md).

Before importing real or reviewed local data, use the local [data source health check](data_source_health.md) to verify route availability, row counts, upstream fallback behavior, and safe diagnostics.

## Supported Adapters

### LOCAL_CSV

`LOCAL_CSV` reads a caller-supplied local CSV path, validates that the file exists, loads it with pandas for row-count metadata, and writes a deterministic raw artifact:

```text
data/raw/LOCAL_CSV/<dataset_type>/<run_id>/raw_data.csv
data/raw/LOCAL_CSV/<dataset_type>/<run_id>/metadata.json
```

Symbol-like columns are read as strings so leading zeros survive the adapter handoff. Reviewed local CSVs should keep China symbols as six-character strings, for example `000001`, `510300`, and `159915`.

### MOCK

`MOCK` loads the configured mock files under `data/mock/`.

Dataset mapping:

- `market` -> `data/mock/prices.csv`
- `benchmark` -> `data/mock/prices.csv`
- `universe` -> `data/mock/universe_snapshots.csv`
- `corporate_actions` -> `data/mock/corporate_actions.csv`
- `trading_calendar` -> `data/mock/trading_calendar.csv`

### AKSHARE_OPTIONAL

`AKSHARE_OPTIONAL` is a guarded manual-only adapter for local AKShare fetches.

It is disabled by default, imports `akshare` lazily only after guardrails pass, and must not be used for real network calls in automated tests.

Supported v0.1 dataset types:

- `market`
- `benchmark`
- `trading_calendar`
- `universe`

Unsupported dataset types return a clear not-implemented error.

Manual market and benchmark fetches require:

- `--symbol`
- `--start-date`
- `--end-date`
- `--allow-real-data`

For `market`, the adapter infers the symbol route and uses configurable AKShare upstream fallback orders. Eastmoney remains available, but it is no longer the only market path:

- Stock-like symbols, such as `000001`, `300xxx`, `600xxx`, `601xxx`, `603xxx`, `605xxx`, and `688xxx`, try Tencent `stock_zh_a_hist_tx`, then Sina `stock_zh_a_daily`, then Eastmoney `stock_zh_a_hist` by default.
- ETF-like symbols, such as `510300`, `512xxx`, `515xxx`, `516xxx`, and `159xxx`, try Sina `fund_etf_hist_sina`, then Eastmoney `fund_etf_hist_em` by default.
- Index-like known codes, such as `000300`, `000905`, and `000852`, try Sina `stock_zh_index_daily`, then Tencent `stock_zh_index_daily_tx`, then the isolated Eastmoney index fallback helper by default.
- Unknown symbols try a small bounded fallback list and report diagnostics if every attempt fails.
- If the Eastmoney AKShare path fails, the adapter can try a final manual-only `eastmoney_curl_cffi_kline` fallback against the same Eastmoney kline API when `akshare_market_enable_curl_cffi_fallback` is enabled.

Successful market metadata includes `inferred_symbol_type`, `attempted_functions`, `attempted_upstreams`, `successful_function`, `upstream_source`, `fallback_used`, `row_count`, `adapter_status`, and `mapping_warnings`. If every market fetch attempt fails, the diagnostic error includes the dataset type, symbol, inferred type, date range, attempted functions, upstream source, exception classes, safe exception messages, and suggested actions. Safe messages redact obvious secret-like values.

Tencent `stock_zh_a_hist_tx` returns a compact daily kline frame where AKShare names the sixth field `amount`; AKShare's public documentation marks that field's unit as `手`, so the adapter treats it as trading volume in hands rather than turnover amount. The adapter first attempts a guarded raw Tencent kline fetch for real manual AKShare runs because Tencent's raw response can include a later turnover-amount field. When raw turnover is verified, the adapter maps `volume_hands * 100` into canonical `volume` and `turnover_amount_10k_yuan * 10000` into canonical `amount`.

Mapping warnings make the path explicit:

- `TENCENT_VOLUME_CONVERTED_FROM_HANDS_TO_SHARES`
- `TENCENT_AMOUNT_CONVERTED_FROM_WAN_YUAN_TO_YUAN`
- `TENCENT_AMOUNT_FIELD_INTERPRETED_AS_VOLUME_HANDS`
- `TENCENT_TURNOVER_AMOUNT_FIELD_UNAVAILABLE`

If only AKShare's six-column DataFrame is available, the turnover amount has already been truncated by AKShare and remains unavailable; the adapter does not fabricate it. For amount-sensitive workflows, compare Tencent against another source such as Sina or BaoStock before using cached rows.

The `curl_cffi` fallback is a recovery attempt, not a guarantee. If Eastmoney closes the kline connection, VPN/proxy routing is unstable, or the upstream endpoint is unavailable, both AKShare and `curl_cffi` can fail. In that case, use a reviewed local CSV through `LOCAL_CSV`.

For `benchmark`, the adapter uses `stock_zh_index_daily` by default and filters dates locally.

For `trading_calendar`, the adapter uses `tool_trade_date_hist_sina` by default and writes trading-day rows with standard MVP session times.

For `universe`, the adapter can fetch stock and ETF symbol/name lists through isolated AKShare helper paths and normalize them into the canonical universe snapshot columns. Use `--as-of-date` to pin the snapshot date and `--market-type stock`, `--market-type etf`, or `--market-type all` to choose the scope. Universe field mapping is best-effort because AKShare raw columns can vary by endpoint and version. The adapter accepts common Chinese and English columns such as `代码`, `股票代码`, `symbol`, `code`, `名称`, `股票简称`, `所属行业`, `行业`, `上市日期`, and `交易所`. If AKShare does not provide optional fields, the adapter fills conservative MVP defaults such as `min_lot=100`, `t_plus_rule=T+1`, `is_active=true`, and `industry=UNKNOWN`.

ETF coverage is source-dependent. If you plan to run current candidates for market symbol `510300`, the resulting universe raw/processed files must contain a matching `510300` row, usually with `instrument_type=ETF`. A stock-only universe can pass data quality and snapshot quality yet still produce an empty factor dataset for ETF market data because there is no joinable universe row.

If universe mapping fails, the error includes `dataset_type`, raw DataFrame shape, raw column names, missing conceptual fields, and a suggestion to update the mapping or use a reviewed `LOCAL_CSV` fallback. Successful universe metadata includes `raw_columns`, `normalized_columns`, `mapping_warnings`, `row_count`, and `adapter_status`.

The adapter normalizes returned frames into raw CSVs that are compatible with the existing ingestion path where possible. Users should still run `data-pipeline`, `data-quality`, and `snapshot-quality` before using the data for current candidates or replay.

For the guarded manual command sequence from AKShare fetch to current candidates, see [akshare_manual_workflow.md](akshare_manual_workflow.md). For a shorter universe + market dry-run checklist with a copyable manifest template, see [akshare_real_data_dry_run.md](akshare_real_data_dry_run.md). If AKShare market history remains unstable, use a reviewed market CSV with the fallback workflow in [local_csv_market_fallback_workflow.md](local_csv_market_fallback_workflow.md).

If a real-data universe output is stock-only and market data contains ETFs such as `510300`, merge reviewed ETF rows through [universe_overlay.md](universe_overlay.md) before running `data-pipeline`.

### BAOSTOCK_OPTIONAL

`BAOSTOCK_OPTIONAL` is a guarded manual-only adapter for local BaoStock historical market fetches.

It is disabled by default, imports `baostock` lazily only after guardrails pass, and must not be used for real network calls in automated tests.

Supported v0.1 dataset types:

- `market`

Unsupported dataset types return a clear not-implemented error.

Manual BaoStock market fetches require:

- `--symbol`
- `--start-date`
- `--end-date`
- `--allow-real-data`
- `baostock` installed in the local virtual environment

Install BaoStock manually only for local real-data dry runs:

```cmd
python -m pip install baostock
```

Example:

```cmd
python -m quant_replay_system.cli data-source-fetch --source BAOSTOCK_OPTIONAL --dataset-type market --symbol 000001 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

BaoStock symbol conversion preserves canonical six-digit project symbols in output while using BaoStock exchange-prefixed codes for the request. Examples:

- `000001` -> `sz.000001`
- `600000` -> `sh.600000`
- `510300` -> `sh.510300`
- `159915` -> `sz.159915`

BaoStock `query_history_k_data_plus` rows are normalized into canonical market columns where possible. The adapter maps `date`, `code`, and `preclose` to `trade_date`, canonical `symbol`, and `pre_close`; it fills `adj_factor=1.0`, derives `is_suspended` from `tradestatus` when available, and uses conservative MVP defaults for unavailable fields such as limit prices and availability timestamps.

Successful metadata includes `baostock_code`, `upstream_source=BAOSTOCK`, `successful_function=query_history_k_data_plus`, `row_count`, `adapter_status`, and no-live-trading/no-broker audit fields. Metadata does not contain secrets.

The raw BaoStock output should still go through `market-cache-ingest` when useful, then `data-pipeline`, `data-quality`, and `snapshot-quality` before current-candidate generation or replay.

### TUSHARE_OPTIONAL

`TUSHARE_OPTIONAL` is a guarded manual-only adapter for local Tushare fetches.

It is disabled by default, imports `tushare` lazily only after guardrails pass, and must not be used for real network calls in automated tests.

Supported v0.1 dataset types:

- `market`
- `benchmark`
- `trading_calendar`
- `universe`

Unsupported dataset types return a clear not-implemented error.

Manual Tushare fetches require:

- `--allow-real-data`
- `TUSHARE_TOKEN` in the current environment or local `.env`
- `tushare` installed in the local virtual environment

Install Tushare manually only for local real-data dry runs:

```cmd
python -m pip install tushare
```

Token rules:

- Store the token only in the local `.env` file or current CMD environment.
- Do not commit `.env`.
- The adapter records `token_present: true/false` but never writes the token value to metadata.
- Error messages redact the token if an upstream exception includes it.
- Automated tests use fake clients and fake tokens only.

Manual market fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source TUSHARE_OPTIONAL --dataset-type market --symbol 000001.SZ --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

Manual universe snapshot fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source TUSHARE_OPTIONAL --dataset-type universe --as-of-date 2024-05-20 --market-type all --allow-real-data
```

Manual trading-calendar fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source TUSHARE_OPTIONAL --dataset-type trading_calendar --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

Tushare market data is normalized into canonical market-style columns where possible. Tushare `daily` / `index_daily` fields such as `ts_code`, `trade_date`, `vol`, and `amount` are mapped to `symbol`, `trade_date`, `volume`, and `amount`; derived fields such as `available_time`, `limit_up`, and `limit_down` use conservative MVP defaults. Universe snapshots use `stock_basic` and, for ETF/all scopes, `fund_basic` with conservative defaults for fields Tushare does not provide. Trading calendars use `trade_cal`.

The raw Tushare output should still go through `data-pipeline`, `data-quality`, and `snapshot-quality` before current-candidate generation or replay.

## Dataset Types

Supported `dataset_type` values are:

- `market`
- `universe`
- `benchmark`
- `corporate_actions`
- `trading_calendar`

The adapter framework writes raw files only. Canonical schema validation remains in `data_ingestion`.

## Real Data Guardrails

Default settings keep real/network sources blocked:

```yaml
data_sources:
  allow_network_sources: false
  allow_real_data_fetch: false
  require_manual_real_data_flag: true
  akshare_market_stock_fallback_order:
    - TENCENT
    - SINA
    - EASTMONEY
  akshare_market_etf_fallback_order:
    - SINA
    - EASTMONEY
  akshare_market_index_fallback_order:
    - SINA
    - TENCENT
    - EASTMONEY
  akshare_market_retry_count: 1
  akshare_market_retry_sleep_seconds: 0
  akshare_market_enable_curl_cffi_fallback: true
  akshare_market_curl_cffi_impersonate: chrome
```

Rules:

- Real/network adapters are disabled by default.
- CLI real-data runs require `--allow-real-data`.
- Automated tests must use `LOCAL_CSV` or `MOCK`.
- Automated tests may monkeypatch fake `akshare`, `baostock`, or `tushare` modules, but they must not call real AKShare, BaoStock, Tushare, or network APIs.
- AKShare requires no token; Tushare requires `TUSHARE_TOKEN` for manual real-data fetches, but the token is never printed or written to metadata.
- `.env` is not modified.
- Broker/live trading integrations are not invoked.

Network availability, VPN/proxy configuration, and upstream endpoint changes can affect AKShare manual fetches. Eastmoney kline requests can fail even when `https://push2his.eastmoney.com` itself returns an HTTP response. Verify local proxy listener ports with `netstat` before setting proxy variables; do not assume ports such as `7890` or `10808` are active. When an upstream request fails or returns unexpected columns, retry later, narrow the request, review the printed diagnostics, or save/use a local CSV through `LOCAL_CSV`.

## CLI Usage

Check source route health before import:

```cmd
python -m quant_replay_system.cli data-source-health --source AKSHARE_OPTIONAL --dataset-type market --symbol 510300 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

For `LOCAL_CSV`, health checks verify the file is readable:

```cmd
python -m quant_replay_system.cli data-source-health --source LOCAL_CSV --dataset-type market --input data\raw\manual_market.csv
```

Load a local CSV into raw artifacts:

```cmd
python -m quant_replay_system.cli data-source-fetch --source LOCAL_CSV --dataset-type market --input data\mock\prices.csv
```

Load configured mock data:

```cmd
python -m quant_replay_system.cli data-source-fetch --source MOCK --dataset-type market
```

Use a custom raw output root:

```cmd
python -m quant_replay_system.cli data-source-fetch --source LOCAL_CSV --dataset-type universe --input data\mock\universe_snapshots.csv --output-dir data\raw
```

Manual AKShare market fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type market --symbol 510300 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

Manual AKShare stock market fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type market --symbol 000001 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

Manual AKShare trading calendar fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type trading_calendar --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

Manual AKShare universe snapshot fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type universe --as-of-date 2024-05-20 --market-type all --allow-real-data
```

Manual BaoStock market fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source BAOSTOCK_OPTIONAL --dataset-type market --symbol 000001 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

Manual Tushare market fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source TUSHARE_OPTIONAL --dataset-type market --symbol 000001.SZ --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

Manual Tushare universe snapshot fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source TUSHARE_OPTIONAL --dataset-type universe --as-of-date 2024-05-20 --market-type all --allow-real-data
```

Manual Tushare trading calendar fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source TUSHARE_OPTIONAL --dataset-type trading_calendar --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

The command prints raw artifact paths, row count, and:

```text
No live trading or broker API was invoked.
```

For a full Windows CMD example that carries AKShare output through `data-pipeline`, `data-quality`, `snapshot-quality`, and `current-candidates`, see [akshare_manual_workflow.md](akshare_manual_workflow.md). For the universe + market real-data dry-run checklist, see [akshare_real_data_dry_run.md](akshare_real_data_dry_run.md).

## Relationship To Data Ingestion

`data-source-fetch` writes raw local artifacts. The recommended handoff is now `data-pipeline`, which runs source fetch, ingestion, optional data quality, and optional snapshot manifest generation in one local workflow:

```cmd
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data\mock\prices.csv
```

For a manual AKShare fetch, run the raw output through the same local quality path:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type market --symbol 510300 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv
python -m quant_replay_system.cli data-quality --dataset-type market --input data\processed\market\<pipeline_id>\raw_data_cleaned.csv
```

For a manual AKShare universe snapshot:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type universe --as-of-date 2024-05-20 --market-type all --allow-real-data
python -m quant_replay_system.cli data-pipeline --dataset-type universe --source LOCAL_CSV --input data\raw\AKSHARE_OPTIONAL\universe\<run_id>\raw_data.csv
python -m quant_replay_system.cli data-quality --dataset-type universe --input data\processed\universe\<pipeline_id>\raw_data_cleaned.csv
```

For a manual Tushare market fetch, use the same local handoff path:

```cmd
python -m quant_replay_system.cli data-source-fetch --source TUSHARE_OPTIONAL --dataset-type market --symbol 000001.SZ --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data\raw\TUSHARE_OPTIONAL\market\<run_id>\raw_data.csv
python -m quant_replay_system.cli data-quality --dataset-type market --input data\processed\market\<pipeline_id>\raw_data_cleaned.csv
```

For a manual BaoStock market fetch, use the same local handoff path:

```cmd
python -m quant_replay_system.cli data-source-fetch --source BAOSTOCK_OPTIONAL --dataset-type market --symbol 000001 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
python -m quant_replay_system.cli market-cache-ingest --input data\raw\BAOSTOCK_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\BAOSTOCK_OPTIONAL\market\<run_id>\metadata.json
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data\raw\BAOSTOCK_OPTIONAL\market\<run_id>\raw_data.csv
python -m quant_replay_system.cli data-quality --dataset-type market --input data\processed\market\<pipeline_id>\raw_data_cleaned.csv
```

You can still run the underlying commands manually:

```cmd
python -m quant_replay_system.cli ingest-market --input data\raw\LOCAL_CSV\market\...\raw_data.csv --output-dir data\processed\market
python -m quant_replay_system.cli data-quality --dataset-type market --input data\processed\market\raw_data_cleaned.csv
python -m quant_replay_system.cli snapshot-quality --manifest data\snapshots\example_snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --snapshot-manifest data\snapshots\example_snapshot_manifest.json
```

## Known MVP Limitations

- `AKSHARE_OPTIONAL` is a guarded MVP adapter, not a production data downloader.
- `BAOSTOCK_OPTIONAL` is a guarded MVP market-only adapter, not a production data downloader.
- `TUSHARE_OPTIONAL` is a guarded MVP adapter and requires a local token; it is not a production data downloader.
- AKShare market routing now attempts non-Eastmoney Sina/Tencent routes first where supported, but route coverage and field semantics can differ by upstream source.
- BaoStock field coverage, adjustment semantics, and available instruments can differ from AKShare/Tushare; review data quality before use.
- Adjustment/factor semantics can differ between Sina, Tencent, and Eastmoney; always run data-quality and snapshot-quality before current candidates.
- AKShare market routing is best-effort and may need manual `params` or later source-specific mapping when upstream endpoints change.
- The `curl_cffi` fallback is manual-only and may still fail when Eastmoney kline, TLS, VPN, or proxy behavior is unstable.
- Tushare field coverage and permissions depend on the user's Tushare account and point balance; review data quality before use.
- Universe snapshot support fills conservative defaults when AKShare does not provide optional fields; review data quality before current-candidate use.
- Universe field mapping is best-effort and may need updates when AKShare changes raw output columns.
- Symbol normalization preserves leading zeros and exchange suffixes where present, but it does not invent missing ETF universe coverage.
- Use the reviewed universe overlay workflow when ETF market symbols need to be added to a stock-only universe snapshot.
- Corporate action AKShare fetches are not implemented in v0.1.
- Data source adapters still only write raw artifacts; use `data-pipeline` for ingestion handoff.
- It uses local/mock CSV data only in automated tests.
- It is not live trading and never invokes broker APIs.
