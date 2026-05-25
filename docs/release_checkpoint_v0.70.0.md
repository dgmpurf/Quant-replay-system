# Release Checkpoint v0.70.0

## Release Summary

`v0.70.0` marks the Reviewed Market Cache Export to Research Status Integration checkpoint.

This milestone proves that a reviewed, explicit source/upstream selection can export a pipeline-ready market CSV from the multi-source local market cache, validate it through data-pipeline, data-quality, and snapshot-quality, and surface the latest export state in the unified `research-status` dashboard without overriding later current-candidate or paper workflow stages.

It is a local research infrastructure checkpoint. It is not a live trading release, broker integration, order automation system, scheduler, strategy-quality proof, or profit guarantee.

## Completed Capabilities

This checkpoint includes:

- Reviewed market cache export from the local multi-source market cache.
- Explicit source/upstream selection for each reviewed symbol/date range.
- Duplicate `symbol + trade_date` key protection before data-pipeline use.
- Exported market CSV generation under ignored local paths.
- Optional data-pipeline manifest generation for reviewed exports.
- Local validation through data-pipeline, data-quality, and snapshot-quality.
- Market-cache-export artifact index, health, and status views.
- Unified `research-status` integration for market-cache-export as the reviewed cache-to-snapshot preparation component.
- Exported research-status CSV and metadata fields for:
  - `latest_market_cache_export_id`
  - `market_cache_export_status`
  - `market_cache_export_stage`
  - `market_cache_export_next_action`
  - `market_cache_export_pipeline_id`
  - `market_cache_export_data_pipeline_status`
  - `market_cache_export_data_quality_status`
  - `market_cache_export_snapshot_quality_status`
  - `market_cache_export_snapshot_manifest_path`
  - `market_cache_export_report_path`
- Regression tests for market-cache-export dashboard fields, CLI output, later workflow priority, failed export actionability, and stale export handling.

## Workflow Chain

The reviewed market cache export chain is:

```text
market cache
-> reviewed cache export
-> data-pipeline
-> data-quality
-> snapshot-quality
-> research-status
-> current-candidates / paper workflow as later stages
```

The broader local research chain now supports these reviewed data-maintenance paths:

```text
data source / cache
-> historical backfill or daily update or reviewed cache export
-> preflight / explicit source selection
-> cache / handoff / pipeline-ready export
-> data-pipeline
-> data-quality
-> snapshot-quality
-> current-candidates
-> paper workflow
-> research-status
```

`market-cache-export` is the reviewed bridge from local cache variants to a single data-pipeline-ready market dataset. It does not choose a trusted source automatically.

## Latest Local Verification Baseline

Latest reviewed cache export:

- Export ID: `ddfc7d148813`
- Exported row count: `93`
- Duplicate key count: `0`
- Linked pipeline ID: `ffe6d69c79e8`
- Data-pipeline status: `PASS`
- Data-quality status: `PASS`
- Snapshot-quality status: `PASS`
- Market-cache-export-health status: `PASS`
- Market-cache-export-status: `PASS`
- Market-cache-export stage: `SNAPSHOT_READY_FROM_EXPORT`

Unified research status:

- Includes latest market-cache-export fields.
- Keeps later workflow artifacts visible and prioritized.
- Does not introduce actionable warnings when export health and snapshot quality are `PASS`.
- Surfaces export health failures or duplicate-key failures as actionable when the export is the active stage.

## Validation Baseline

Latest validation baseline for this checkpoint:

- Focused tests: `python -m pytest tests/test_local_research_dashboard.py`, 46 passed.
- Backend tests: `python -m pytest`, 946 passed, 2 warnings.
- Quick tests: `python -m pytest -m "not slow"`, 837 passed, 109 deselected, 2 warnings.
- No live trading.
- No broker integration.
- No automated orders.
- No scheduler, cron job, background job, or GitHub Actions workflow.
- No secrets printed or stored.
- No real network/API calls in automated tests.
- No market cache mutation during status/dashboard verification.

## Safety Boundaries

The checkpoint preserves these boundaries:

- No live trading is implemented.
- No broker API is invoked.
- No automated order placement is implemented.
- No scheduler, cron job, background job, or GitHub Actions workflow is added.
- Cache writes remain explicit and separate from reviewed export.
- Real data fetches require explicit `--allow-real-data`.
- Generated `data/cache`, `data/raw`, `data/processed`, and `outputs` artifacts are local/ignored and must not be committed.
- Tokens remain in local `.env` only and are not printed or written to reports.
- Source/upstream selection is explicit in v0.1.
- Policy-aware source selection is not automatic yet.
- Data-quality and snapshot-quality remain required before research use.
- Demo candidates and paper workflow outputs are not strategy recommendations.

## Known Limitations

- Policy-aware automatic source selection is not implemented.
- Reviewed cache export does not mutate the market cache.
- Cache export is local/manual and is not a scheduler.
- ETF/Sina reliability remains `PROVISIONAL` until another ETF reference source is available.
- BaoStock returned 0 ETF rows in local ETF checks.
- Broader historical universe/backfill strategy is still in progress.
- Larger reviewed exports still need manual source/upstream review, artifact inspection, and downstream quality checks.
- A clean export snapshot does not certify strategy quality; it only establishes local data artifact readiness.

## Recommended Next Engineering Tasks

1. Clean or classify stale/actionable snapshot-quality artifacts so `research-status` can focus on the latest active reviewed export or paper workflow chain.
2. Add a policy-aware but explicitly gated cache export selection proposal, without making automatic trusted-source decisions by default.
3. Expand reviewed cache export manifests across a broader representative stock and ETF universe.
4. Add cache-export-to-current-candidates smoke verification using the generated snapshot manifest.
5. Continue historical backfill strategy design for chunking, coverage, retry policy, and reviewed source fallback.

## Git Tag

Recommended milestone tag:

```text
v0.70.0 = Reviewed Market Cache Export to Research Status Integration
```

Before tagging, run validation and inspect the working tree:

```cmd
python -m pytest
python -m pytest -m "not slow"
git status --short
git ls-files | findstr /R /C:"^data/cache" /C:"^data/raw" /C:"^data/processed" /C:"^outputs" /C:"^\.env" /C:"^\.venv" /C:"^secrets"
```

Create the tag only after ChatGPT or the user confirms the checkpoint:

```cmd
git tag -a v0.70.0 -m "Reviewed Market Cache Export to Research Status Integration"
git push origin v0.70.0
```
