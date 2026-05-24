# Release Checkpoint v0.64.0

## Release Summary

`v0.64.0` marks the reviewed offline market update to unified `research-status` integration checkpoint.

This milestone proves that reviewed local market data files can be validated offline, handed into the local snapshot/current-candidates workflow, smoke-tested through the manual paper workflow, indexed and health-checked, and summarized in the unified local research dashboard.

It is a research infrastructure checkpoint. It is not a live trading release, broker integration, order automation system, strategy-quality proof, or profit guarantee.

## Completed Capabilities

This checkpoint includes:

- Market cache acceptance preflight with `ACCEPT` / `WARN_ACCEPT` / `REJECT`.
- Dry-run-first daily market update skeleton.
- Reviewed online and offline symbol manifests for batch market updates.
- Offline `raw_input` / `metadata_path` manifest rows that do not require network access.
- Reviewed offline market update handoff into a local batch market CSV and data-pipeline manifest.
- Cache-free handoff validation through `data-pipeline`, `snapshot-quality`, and `current-candidates --selection-profile demo`.
- Market update handoff artifact index, health check, and status dashboard.
- Unified `research-status` integration for latest market-update-handoff status as a pre-paper workflow component.
- Regression coverage for `research-status` exported CSV and metadata market-update-handoff fields.
- Paper workflow leading-zero symbol preservation across CSV boundaries.
- Demo paper workflow validation with `WATCH_ONLY` / `SKIP` decisions and no approvals.

## Local Workflow Chain

The reviewed offline update workflow is:

```text
offline reviewed symbol manifest
-> market-daily-update dry-run
-> market-cache-preflight
-> market-update-handoff
-> data-pipeline
-> snapshot-quality
-> current-candidates --selection-profile demo
-> current-to-paper
-> current-to-paper-review
-> paper-review-decisions WATCH_ONLY
-> paper-daily --reviewed-decisions
-> paper-workflow-status
-> research-status
```

Supporting discovery and status commands:

```text
market-update-handoff-index
-> market-update-handoff-health
-> market-update-handoff-status
-> research-status
```

## Validation Baseline

Latest validation baseline for this checkpoint:

- Backend tests: `python -m pytest`, 880 passed.
- Quick tests: `python -m pytest -m "not slow"`, 771 passed.
- No live trading.
- No broker integration.
- No automated orders.
- No scheduler, cron job, or GitHub Actions workflow.
- No secrets printed or stored.
- No real network/API calls in automated tests.

## Safety Boundaries

The checkpoint preserves these boundaries:

- No live trading is implemented.
- No broker API is invoked.
- No automated order placement is implemented.
- Demo candidates are explicitly not strategy recommendations.
- Cache writes require explicit `--accept-cache-write`.
- Real data fetches require explicit `--allow-real-data`.
- Generated `data/cache`, `data/raw`, `data/processed`, and `outputs` artifacts are local and should not be committed.
- Tokens remain in local `.env` only and are not printed or written to reports.
- Paper workflow smoke tests use `WATCH_ONLY` / `SKIP`, not `APPROVED_FOR_PAPER`.

## Known Limitations

- AKShare/Sina ETF field reliability remains `PROVISIONAL` until another ETF reference source is available.
- BaoStock returned 0 ETF rows for 510300 and 159915 in local checks.
- Daily market update remains local/manual and is not a scheduler.
- Demo current candidates validate artifacts and workflow wiring only; they are not strategy recommendations.
- The paper workflow smoke path uses `WATCH_ONLY` / `SKIP`, not approved trading.
- Broader representative symbol comparison is still needed before source preference policy becomes stronger.
- Historical backfill workflow is not yet implemented.
- Cache acceptance preflight and data-quality gates help catch issues but do not certify strategy quality.

## Recommended Next Engineering Tasks

1. Add a historical backfill workflow skeleton that reuses data-source health, preflight, cache ingest, comparison, and status artifacts.
2. Expand representative source comparisons across more A-share stock and ETF symbols.
3. Add a second ETF reference source or optional Tushare/JQData/RQData ETF comparison path if permissions and cost are acceptable.
4. Add a reviewed source preference policy for cache-backed research inputs after broader comparison evidence.
5. Add dashboard docs for the complete data-source/cache/update/handoff/paper workflow map if the workflow expands further.

## Git Tag

Recommended milestone tag:

```text
v0.64.0 = Reviewed Offline Update To Research Status Integration
```

Before tagging, run validation and inspect the working tree:

```cmd
python -m pytest
python -m pytest -m "not slow"
git status --short
```

Create the tag only after ChatGPT or the user confirms the checkpoint:

```cmd
git tag -a v0.64.0 -m "Reviewed Offline Update To Research Status Integration"
git push origin v0.64.0
```
