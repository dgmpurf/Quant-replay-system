# Reviewed Cache Export Workflow v0.1

`market-cache-export` creates a pipeline-ready local market CSV from the market cache using an explicit reviewed source/upstream manifest.

It is local-only. It does not fetch data, mutate the market cache, call broker APIs, place orders, automate execution, or choose a trusted source silently.

## Purpose

The market cache can intentionally store multiple source variants for the same `symbol + trade_date`, such as AKShare/Tencent and BaoStock stock rows. `data-pipeline` and `data-quality` require one canonical market row per `symbol + trade_date`.

The reviewed export layer is the bridge:

```text
market cache
-> reviewed cache export manifest
-> market-cache-export
-> data/raw/manual_cache_exports/<export_id>/market_raw_data.csv
-> data-pipeline
-> data-quality
-> snapshot-quality
```

## Manifest

CSV format is used in v0.1.

Required columns:

```text
symbol,start_date,end_date,source,upstream_source,enabled
```

Optional columns:

```text
security_type,require_fields,notes
```

Example:

```csv
symbol,start_date,end_date,source,upstream_source,enabled,security_type,require_fields,notes
000001,2024-01-02,2024-01-05,AKSHARE_OPTIONAL,TENCENT,true,STOCK,"close,volume,amount",Tencent reviewed stock source
510300,2024-01-02,2024-05-20,AKSHARE_OPTIONAL,SINA,true,ETF,"close,volume,amount",Sina ETF provisional source
```

Symbols are loaded and written as strings. `000001` must remain `000001`, not `1` or `1.0`.

## CLI

Export reviewed cache rows:

```cmd
python -m quant_replay_system.cli market-cache-export --manifest data\raw\manual_manifests\reviewed_cache_export_example.csv
```

Build a local data-pipeline manifest at the same time:

```cmd
python -m quant_replay_system.cli market-cache-export --manifest data\raw\manual_manifests\reviewed_cache_export_example.csv --build-pipeline-manifest --universe data\raw\LOCAL_CSV\universe_overlay\<overlay_id>\raw_data.csv --trading-calendar data\raw\AKSHARE_OPTIONAL\trading_calendar\<run_id>\raw_data.csv
```

The generated manifest uses `LOCAL_CSV` entries for:

- `market`: exported cache CSV
- `universe`: provided universe CSV
- `trading_calendar`: provided trading calendar CSV

`market-cache-export` does not run `data-pipeline` automatically in v0.1.

## Policy-aware Planning

Use `market-cache-export-plan` when you want the system to inspect local cache coverage and `market-source-policy` before drafting a reviewed export manifest:

```cmd
python -m quant_replay_system.cli market-cache-export-plan --manifest data\raw\manual_manifests\market_cache_export_policy_request_example.csv
```

The planner is recommendation-only by default. It writes `data\raw\manual_manifests\market_cache_export_recommended_<plan_id>.csv`, which is compatible with `market-cache-export`, but the user must review the generated source/upstream selections before using it.

`PROVISIONAL` recommendations, such as AKShare/Sina ETF rows, remain warnings. Strict mode is available with `--strict-reliable`. See [market_cache_export_policy.md](market_cache_export_policy.md).

After generating policy plans, use the plan artifact views before larger reviewed exports:

```cmd
python -m quant_replay_system.cli market-cache-export-plan-index
python -m quant_replay_system.cli market-cache-export-plan-health
python -m quant_replay_system.cli market-cache-export-plan-status
```

These commands inspect recommendation artifacts and generated reviewed manifests. They do not run export automatically or mutate cache.

## Index, Health, And Status

Reviewed export artifacts can be discovered and checked before downstream snapshot workflows:

```cmd
python -m quant_replay_system.cli market-cache-export-index
python -m quant_replay_system.cli market-cache-export-health
python -m quant_replay_system.cli market-cache-export-status
```

`market-cache-export-index` scans `outputs/reports/market_cache_export/` and writes:

```text
outputs/reports/market_cache_export/index/market_cache_export_index.csv
outputs/reports/market_cache_export/index/market_cache_export_index_report.md
outputs/reports/market_cache_export/index/metadata.json
```

The index records export id, exported market CSV path, row count, duplicate-key count, source/upstream selections, linked pipeline/data-quality/snapshot-quality statuses when available, and report paths.

`market-cache-export-health` checks that metadata and reports are readable, the exported market CSV exists, required canonical market columns are present, and duplicate `symbol + trade_date` keys are absent. Linked pipeline, data-quality, and snapshot-quality reports are checked when the export index records those links.

`market-cache-export-status` summarizes the latest export and next manual action. Typical stages include:

- `CACHE_EXPORT_READY`
- `PIPELINE_READY_FROM_EXPORT`
- `DATA_QUALITY_READY_FROM_EXPORT`
- `SNAPSHOT_READY_FROM_EXPORT`
- `CACHE_EXPORT_HEALTH_WARN`
- `CACHE_EXPORT_FAILED`

These views check artifact completeness and duplicate-key safety. They do not certify source truth, alter cache data, choose a trusted source automatically, or run paper/live trading.

`research-status` also includes the latest `market-cache-export-status` fields as reviewed cache-to-snapshot context. If the latest export is `SNAPSHOT_READY_FROM_EXPORT`, the unified dashboard can recommend `current-candidates`; if later current-candidates or paper workflow artifacts already exist, those later stages keep priority and the export remains visible as context.

The export's linked `snapshot_quality_status` is also used for snapshot warning actionability. A linked `PASS` prevents older unrelated standalone snapshot warnings from blocking the active reviewed export path; a linked `WARN` or `FAIL` remains actionable.

## Validation

Before writing the reviewed export, the workflow checks:

- required canonical market columns exist,
- symbols and dates parse correctly,
- `available_time` is parseable,
- OHLC values are sane,
- `volume` and `amount` are non-negative,
- required fields are present,
- duplicate `symbol + trade_date` rows are rejected by default.

Missing rows for a reviewed manifest row are reported as errors. Disabled rows are skipped.

## Artifacts

Report artifacts are written under:

```text
outputs/reports/market_cache_export/<export_id>/
```

Files:

- `market_cache_export_report.md`
- `market_cache_export_rows.csv`
- `market_cache_export_issues.csv`
- `metadata.json`

The exported market CSV is written under:

```text
data/raw/manual_cache_exports/<export_id>/market_raw_data.csv
```

If requested, the generated pipeline manifest is written under:

```text
data/raw/manual_manifests/market_cache_export_<export_id>.json
```

Generated `data/raw`, `data/processed`, `data/cache`, and `outputs` artifacts should remain ignored and uncommitted.

## Relationship To Other Checks

- `market-cache-query` can export a single symbol/source/upstream slice.
- `market-cache-export` exports a reviewed multi-row manifest into one market CSV.
- `data-quality` still owns duplicate-key detection for processed data.
- `snapshot-quality` still checks the full processed snapshot.
- Source policy may inform the review, but v0.1 requires explicit source/upstream selection.
- `market-cache-export-plan` can draft explicit selections from source policy and cache coverage, but the generated manifest remains reviewed input and should be inspected before export.

## Safety

- No live trading.
- No broker API.
- No automated order placement.
- No scheduler.
- No real network calls.
- No cache mutation.
- No automatic source preference.
