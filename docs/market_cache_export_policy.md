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
-> attach source-comparison diagnostics when another cache source exists
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

## Index, Health, And Status

Recommendation plan artifacts can be discovered and checked before larger reviewed exports:

```cmd
python -m quant_replay_system.cli market-cache-export-plan-index
python -m quant_replay_system.cli market-cache-export-plan-health
python -m quant_replay_system.cli market-cache-export-plan-status
```

`market-cache-export-plan-index` scans `outputs/reports/market_cache_export_policy/` and writes:

```text
outputs/reports/market_cache_export_policy/index/market_cache_export_policy_index.csv
outputs/reports/market_cache_export_policy/index/market_cache_export_policy_index_report.md
outputs/reports/market_cache_export_policy/index/metadata.json
```

The index records plan id, status, recommendation counts, generated reviewed manifest path, symbols, date range, and linked downstream export/pipeline/snapshot fields when a later export can be discovered.

`market-cache-export-plan-health` checks that metadata, report, recommendations CSV, issues CSV, and generated reviewed manifest are readable. It also checks that enabled generated manifest rows preserve symbol strings and include explicit `source` and `upstream_source`.

`RECOMMENDED_WITH_WARNINGS` rows, such as ETF/Sina `PROVISIONAL` recommendations, are reported as `WARN`, not hidden and not upgraded to `PASS`. Missing generated manifests or enabled rows without explicit source/upstream are `FAIL`.

`market-cache-export-plan-status` summarizes the latest plan and next manual action. Typical stages include:

- `NO_POLICY_PLAN_ARTIFACTS`
- `POLICY_PLAN_READY_FOR_REVIEW`
- `POLICY_PLAN_WARNINGS_NEED_REVIEW`
- `POLICY_PLAN_FAILED`
- `REVIEWED_MANIFEST_READY`
- `EXPORT_READY_FROM_POLICY_PLAN`
- `SNAPSHOT_READY_FROM_POLICY_PLAN`

These views do not run exports, mutate cache, fetch data, or automate source selection.

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

## Source Comparison Diagnostics

Policy-plan recommendations include comparison diagnostics when another cache source/upstream is available for the same symbol and date range. These diagnostics reuse the market cache comparison logic and are written into:

```text
outputs/reports/market_cache_export_policy/<plan_id>/market_cache_export_policy_recommendations.csv
outputs/reports/market_cache_export_policy/<plan_id>/metadata.json
outputs/reports/market_cache_export_policy/<plan_id>/market_cache_export_policy_report.md
```

Recommendation fields include:

- `comparison_available`
- `comparison_reference_source`
- `comparison_reference_upstream`
- `comparison_status`
- `comparison_matched_rows`
- `comparison_source_only_rows`
- `comparison_max_close_diff_pct`
- `comparison_median_volume_ratio`
- `comparison_median_amount_ratio`
- `comparison_diagnostic_classification`
- `comparison_warning_reason`

The policy-plan `comparison_status` is evaluated against the request's `required_fields`. Broader comparison context can still show caveats for non-required fields such as `pre_close`, but those caveats do not downgrade a `close,volume,amount` recommendation by themselves.

For stock rows with multiple reliable cached candidates, a passing comparison keeps the recommendation as `RECOMMENDED`. A `WARN` or `FAIL` comparison downgrades the row to `RECOMMENDED_WITH_WARNINGS` so the generated manifest remains reviewable but not silently approved.

For ETF rows where only AKShare/Sina exists, `comparison_status=UNAVAILABLE` records that no second source is present. This is expected while BaoStock ETF coverage is unavailable locally. The recommendation remains `RECOMMENDED_WITH_WARNINGS` because ETF/Sina field reliability is still `PROVISIONAL`.

Comparison diagnostics are evidence only. They do not certify source truth, mutate cache, auto-approve the generated manifest, bypass data-quality, or bypass snapshot-quality.

## Artifact Views

Use the policy-plan artifact views to review recommendation plans before scaling them:

```powershell
python -m quant_replay_system.cli market-cache-export-plan-index
python -m quant_replay_system.cli market-cache-export-plan-health
python -m quant_replay_system.cli market-cache-export-plan-status
```

The index and status summaries include comparison counts:

- `comparison_pass_count`
- `comparison_warn_count`
- `comparison_fail_count`
- `comparison_unavailable_count`
- `comparison_required_but_missing_count`
- `comparison_supported_recommendation_count`
- `comparison_unsupported_recommendation_count`

`comparison_status=PASS` is healthy. `comparison_status=UNAVAILABLE` for `PROVISIONAL` ETF/Sina rows is a reviewable warning, not a system failure, when no second ETF reference source exists locally. A comparison `FAIL` for a recommended stock source is actionable and must be reviewed before the generated manifest is used.

## Safety

- Source selection is recommendation-only by default.
- The generated manifest requires explicit `source` and `upstream_source` values for recommended rows.
- No cache mutation occurs.
- No live trading, broker API, automated order placement, scheduler, or GitHub Actions workflow is involved.
- No real network calls are used by the planner.
- Generated `data/raw`, `data/processed`, `data/cache`, and `outputs` artifacts should remain ignored and uncommitted.

## Relationship To Other Checks

- `market-source-policy` records field reliability.
- `market-cache-export-plan` recommends reviewed selections from local cache rows and policy, with comparison diagnostics when a viable reference source exists.
- `market-cache-export-plan-index`, `market-cache-export-plan-health`, and `market-cache-export-plan-status` make recommendation plans discoverable and reviewable.
- `research-status` includes the latest policy-plan status as recommendation context.
- `market-cache-export` exports reviewed selections into one market CSV.
- `data-quality` still enforces duplicate-key checks.
- `snapshot-quality` still gates the processed snapshot.
- `research-status` reports downstream workflow readiness and keeps policy-plan warnings visible without letting them override newer reviewed export, current-candidate, or paper workflow states.

## Research Status Integration

`research-status` reads the latest `market-cache-export-plan-status` artifact and exports policy-plan context fields such as:

- `latest_market_cache_export_plan_id`
- `market_cache_export_plan_status`
- `market_cache_export_plan_stage`
- `market_cache_export_plan_recommendation_count`
- `market_cache_export_plan_comparison_pass_count`
- `market_cache_export_plan_comparison_warn_count`
- `market_cache_export_plan_comparison_fail_count`
- `market_cache_export_plan_comparison_unavailable_count`
- `market_cache_export_plan_comparison_supported_recommendation_count`
- `market_cache_export_plan_comparison_unsupported_recommendation_count`
- `market_cache_export_plan_generated_manifest_path`
- `market_cache_export_plan_downstream_export_id`
- `market_cache_export_plan_downstream_snapshot_quality_status`

If the plan stage is `SNAPSHOT_READY_FROM_POLICY_PLAN`, the unified dashboard can recommend using the linked snapshot/export outputs for `current-candidates`. Comparison unavailable for provisional ETF/Sina recommendations remains visible as review context, while comparison failures for recommended stock sources remain actionable when the policy plan is the active stage. If a reviewed cache export, current-candidate run, market-update-handoff, historical-backfill context, or paper workflow is already more advanced, those later states keep priority and the policy plan remains visible as context.

`PROVISIONAL` recommendations stay visible as reviewable warnings. They do not automatically approve an export, mutate cache, or become trading recommendations.

## Known Limitations

- v0.1 uses simple reliability ranking and configured source preference order.
- It compares recommended rows against one available reference source when practical; it does not perform exhaustive pairwise source comparison during planning.
- It does not certify that a source is true or strategy-ready.
- It does not automatically run `market-cache-export` in the default path.
- It does not implement automatic policy-aware source selection for production workflows.
