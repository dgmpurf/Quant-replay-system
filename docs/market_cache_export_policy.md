# Policy-aware Reviewed Cache Export v0.1

`market-cache-export-plan` creates a policy-aware recommendation for a reviewed cache export manifest.

It is recommendation-only by default. It does not run `market-cache-export`, mutate the market cache, fetch data, call broker APIs, place orders, schedule jobs, or choose a trusted source silently.

## Purpose

The local market cache can contain multiple source variants for the same `symbol + trade_date`, such as AKShare/Tencent and BaoStock stock rows. `market-cache-export` safely exports reviewed explicit source/upstream selections, but hand-authoring those selections is repetitive.

The policy-aware planner bridges that gap:

```text
reviewed policy request manifest
-> inspect local cache coverage
-> inspect market-source-policy field reliability
-> recommend source/upstream selections
-> write a reviewed export manifest
-> user reviews manifest
-> market-cache-export
-> data-pipeline
-> data-quality
-> snapshot-quality
```

The generated manifest is compatible with `market-cache-export`, but the user should inspect it before use.

## Request Manifest

CSV format is used in v0.1.

Required columns:

```text
symbol,start_date,end_date,required_fields,enabled
```

Optional columns:

```text
security_type,preferred_source,preferred_upstream_source,reference_source,notes
```

Example:

```csv
symbol,start_date,end_date,required_fields,enabled,security_type,notes
000001,2024-01-02,2024-01-05,"close,volume,amount",true,STOCK,stock test
510300,2024-01-02,2024-05-20,"close,volume,amount",true,ETF,ETF provisional test
```

Symbols are loaded and written as strings. `000001` must remain `000001`, not `1` or `1.0`.

## CLI

Plan a reviewed export:

```cmd
python -m quant_replay_system.cli market-cache-export-plan --manifest data\raw\manual_manifests\market_cache_export_policy_request_example.csv
```

Strict mode rejects `PROVISIONAL`, `UNKNOWN`, and caveated required fields:

```cmd
python -m quant_replay_system.cli market-cache-export-plan --manifest data\raw\manual_manifests\market_cache_export_policy_request_example.csv --strict-reliable
```

The command writes:

```text
outputs/reports/market_cache_export_policy/<plan_id>/market_cache_export_policy_report.md
outputs/reports/market_cache_export_policy/<plan_id>/market_cache_export_policy_recommendations.csv
outputs/reports/market_cache_export_policy/<plan_id>/market_cache_export_policy_issues.csv
outputs/reports/market_cache_export_policy/<plan_id>/metadata.json
data/raw/manual_manifests/market_cache_export_recommended_<plan_id>.csv
```

Run the reviewed export only after inspecting the generated manifest:

```cmd
python -m quant_replay_system.cli market-cache-export --manifest data\raw\manual_manifests\market_cache_export_recommended_<plan_id>.csv
```

## Recommendation Statuses

- `RECOMMENDED`: cached rows exist and required field reliability is acceptable without warnings.
- `RECOMMENDED_WITH_WARNINGS`: cached rows exist, but at least one required field is provisional, unknown, or caveated.
- `NO_RELIABLE_SOURCE`: cached rows exist, but policy rejects the available source/upstream options.
- `NO_CACHE_ROWS`: no cached rows are available for the request.
- `DISABLED`: request row is disabled and no recommendation is made.

For stock requests, the default preference order is:

```text
AKSHARE_OPTIONAL / TENCENT
BAOSTOCK_OPTIONAL / BAOSTOCK
```

For ETF requests, the default preference is:

```text
AKSHARE_OPTIONAL / SINA
```

ETF/Sina recommendations remain `PROVISIONAL` warnings until another reliable ETF reference source is available. BaoStock ETF rows are not recommended while the policy marks ETF fields `UNAVAILABLE`.

## Safety

- Source selection is recommendation-only by default.
- The generated manifest requires explicit `source` and `upstream_source` values for recommended rows.
- No cache mutation occurs.
- No live trading, broker API, automated order placement, scheduler, or GitHub Actions workflow is involved.
- No real network calls are used by the planner.
- Generated `data/raw`, `data/processed`, `data/cache`, and `outputs` artifacts should remain ignored and uncommitted.

## Relationship To Other Checks

- `market-source-policy` records field reliability.
- `market-cache-export-plan` recommends reviewed selections from local cache rows and policy.
- `market-cache-export` exports reviewed selections into one market CSV.
- `data-quality` still enforces duplicate-key checks.
- `snapshot-quality` still gates the processed snapshot.
- `research-status` reports downstream workflow readiness.

## Known Limitations

- v0.1 uses simple reliability ranking and configured source preference order.
- It does not compare sources during planning.
- It does not certify that a source is true or strategy-ready.
- It does not automatically run `market-cache-export` in the default path.
- It does not implement automatic policy-aware source selection for production workflows.
