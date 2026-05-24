# Market Cache Acceptance Preflight v0.1

The market cache acceptance preflight is a local-only gate to run before `market-cache-ingest`.

It does not fetch data, mutate `data/cache`, certify strategy quality, call broker APIs, place orders, automate execution, print secrets, or modify `.env`.

## Purpose

Market rows can now come from multiple optional sources and upstream routes. The preflight checks one candidate `raw_data.csv` against:

- canonical market schema and basic sanity rules,
- source field reliability policy,
- optional data-source health metadata,
- optional cross-source cache comparison,
- known caveats such as first-window `pre_close` differences.

The result is one of:

- `ACCEPT`: candidate rows passed the requested checks.
- `WARN_ACCEPT`: candidate rows can be locally accepted with warnings or known caveats.
- `REJECT`: candidate rows should not be ingested into the market cache.

## Relationship To Other Tools

- `data-source-health` checks whether a route can fetch.
- `market-cache-compare` checks whether overlapping cached rows agree.
- `market-source-policy` records field reliability by source, upstream, security type, and field.
- `market-cache-preflight` combines schema sanity, policy, optional health, and optional comparison into an acceptance decision before cache ingest.
- `market-daily-update` can call the preflight as part of a dry-run-first local update workflow; cache writes still require explicit `--accept-cache-write`.
- `data-pipeline`, `data-quality`, and `snapshot-quality` are still required after cache query before research use.

## CLI

Basic preflight:

```cmd
python -m quant_replay_system.cli market-cache-preflight --input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\AKSHARE_OPTIONAL\market\<run_id>\metadata.json --require-fields close,volume,amount
```

With cross-source reference rows already in cache:

```cmd
python -m quant_replay_system.cli market-cache-preflight --input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\AKSHARE_OPTIONAL\market\<run_id>\metadata.json --require-fields close,volume,amount --reference-source BAOSTOCK_OPTIONAL
```

ETF example:

```cmd
python -m quant_replay_system.cli market-cache-preflight --input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\AKSHARE_OPTIONAL\market\<run_id>\metadata.json --require-fields close,volume,amount
```

AKShare/Sina ETF fields are currently `PROVISIONAL`, so this path should return `WARN_ACCEPT` unless `--strict-provisional` is used.

## Checks

Schema and sanity checks:

- required canonical market columns are present,
- `symbol` is preserved as a string,
- `trade_date` is parseable,
- `available_time` is parseable when required,
- OHLC values are non-negative,
- `high >= low`,
- `volume` and `amount` are non-negative,
- source/upstream metadata can be read from `metadata.json` or existing columns.

Policy checks:

- `RELIABLE` required fields pass.
- `PROVISIONAL` required fields produce `WARN_ACCEPT`, or `REJECT` with `--strict-provisional`.
- `UNAVAILABLE` and `DO_NOT_USE` required fields produce `REJECT`.
- `UNSTABLE` fields warn or reject according to config.
- `CAVEAT_FIRST_WINDOW_ROW` is reported as `KNOWN_CAVEAT`.

Optional comparison:

- If `--reference-source` is supplied and matching cache rows exist, the preflight compares candidate rows to that reference source in memory.
- Comparison PASS supports `ACCEPT`.
- Comparison WARN supports `WARN_ACCEPT`.
- Comparison FAIL produces `REJECT` unless all failures are the configured first-window `pre_close` caveat.

## Artifacts

Artifacts are written under:

```text
outputs/reports/market_cache_preflight/<preflight_id>/
```

Files:

- `market_cache_preflight_report.md`
- `market_cache_preflight_issues.csv`
- `market_cache_preflight_summary.csv`
- `metadata.json`

Metadata includes `cache_mutated=false`, `no_live_trading=true`, and `no_broker_api=true`.

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

For local incremental updates, `market-daily-update` wraps the health/fetch-or-raw/preflight/status steps and only calls `market-cache-ingest` when `--accept-cache-write` is supplied.

`market-daily-update --symbol-manifest <csv>` applies the same preflight gate to each enabled reviewed symbol row. A row with `BLOCKED_PREFLIGHT_REJECT` is not ingested, even if the batch was run with `--accept-cache-write`.

## Known Limitations

- v0.1 preflight is an acceptance aid, not data certification.
- Optional comparison only runs when reference rows already exist in local cache.
- ETF fields remain provisional until compared against another reliable ETF source.
- Health metadata is only evaluated when explicitly supplied.
- The preflight does not rewrite or normalize existing cached rows.
