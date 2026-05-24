# Release Checkpoint v0.67.0

## Release Summary

`v0.67.0` marks the Historical Backfill Status Integration checkpoint.

This milestone proves that local historical backfill dry-runs can be discovered, health-checked, summarized through a dedicated status view, and surfaced in the unified `research-status` dashboard without overriding later paper workflow state.

It is a local research infrastructure checkpoint. It is not a live trading release, broker integration, order automation system, scheduler, strategy-quality proof, or profit guarantee.

## Completed Capabilities

This checkpoint includes:

- Historical backfill workflow skeleton for reviewed symbol/date manifests.
- Historical backfill dry-run behavior with no cache mutation by default.
- Historical backfill artifact index for discovering backfill runs.
- Historical backfill artifact health check for metadata, report, task/result CSV, count consistency, and safety statements.
- Historical backfill status view with latest backfill stage, reviewable warning state, cache-write flag, and next manual action.
- Unified `research-status` integration for historical backfill as a history/cache-building component.
- `research-status` exported fields for:
  - `latest_historical_backfill_id`
  - `historical_backfill_status`
  - `historical_backfill_stage`
  - `historical_backfill_cache_write_occurred`
- Preservation of later workflow priority when market-update-handoff, current-candidates, or paper workflow artifacts are more advanced.
- Reviewable warning classification for expected dry-run caveats such as provisional ETF/Sina policy and first-window `pre_close` caveats.

## Workflow Chain

The historical backfill artifact/status chain is:

```text
historical-backfill
-> historical-backfill-index
-> historical-backfill-health
-> historical-backfill-status
-> research-status
```

The broader local research chain now has two local data-maintenance entry points:

```text
data source / cache
-> backfill or daily update
-> preflight
-> cache / handoff
-> data-pipeline
-> snapshot-quality
-> current-candidates
-> paper workflow
-> research-status
```

Backfill remains a history/cache-building workflow. Daily update remains the reviewed local incremental update workflow. Both remain separate from paper workflow review and never approve trades.

## Latest Local Dry-Run Baseline

Historical backfill status:

- Status: `WARN`
- Stage: `BACKFILL_WARNINGS_NEED_REVIEW`
- Latest backfill ID: `45025c3312b5`
- Cache write occurred: `False`
- Next action: review WARN tasks before rerunning with `--accept-cache-write`.

Unified research status:

- Status: `WARN`
- Final stage: `PAPER_WORKFLOW_READY`
- Latest historical backfill ID: `45025c3312b5`
- Historical backfill stage: `BACKFILL_WARNINGS_NEED_REVIEW`
- Historical backfill cache write occurred: `False`
- Later paper workflow priority preserved.

## Validation Baseline

Latest validation baseline for this checkpoint:

- Backend tests: `python -m pytest`, 912 passed, 2 warnings.
- Quick tests: `python -m pytest -m "not slow"`, 803 passed, 109 deselected, 2 warnings.
- No live trading.
- No broker integration.
- No automated orders.
- No scheduler, cron job, background job, or GitHub Actions workflow.
- No secrets printed or stored.
- No real network/API calls in automated tests.

## Safety Boundaries

The checkpoint preserves these boundaries:

- No live trading is implemented.
- No broker API is invoked.
- No automated order placement is implemented.
- No scheduler, cron job, background job, or GitHub Actions workflow is added.
- Cache writes require explicit `--accept-cache-write`.
- Real data fetches require explicit `--allow-real-data`.
- Generated `data/cache`, `data/raw`, `data/processed`, and `outputs` artifacts are local/ignored and must not be committed.
- Tokens remain in local `.env` only and are not printed or written to reports.
- Historical backfill status is informational and review-gated; it does not certify strategy quality.
- Paper workflow smoke tests remain manual review workflows and do not apply `APPROVED_FOR_PAPER` unless a separate explicit manual review task does so.

## Known Limitations

- Historical backfill is still a skeleton/MVP.
- Historical backfill is local/manual and is not a scheduler.
- Cache write verification for historical backfill has not yet been performed.
- Backfill health reports dry-run WARNs as reviewable `WARN`, not `PASS`.
- ETF/Sina reliability remains `PROVISIONAL` until another ETF reference source is available.
- BaoStock returned 0 ETF rows in local ETF checks.
- Broader historical universe selection and backfill strategy are still needed.
- Larger backfills still need reviewed symbol manifests, chunk sizing, artifact inspection, and manual approval before cache writes.
- Data still needs `data-pipeline`, `data-quality`, and `snapshot-quality` before research use.

## Recommended Next Engineering Tasks

1. Add a reviewed historical backfill cache-write verification dry-run with tiny local/fake data and explicit `--accept-cache-write` in a controlled ignored cache path if supported.
2. Add historical backfill to any higher-level release/status checklist used before broader data maintenance work.
3. Expand historical backfill manifest examples for representative stock and ETF symbols, while keeping real-data fetches manual and guarded.
4. Add broader historical source comparison coverage before treating any source preference policy as production-like.
5. Design a reviewed historical universe/backfill strategy for symbols, chunks, retries, and source fallback without adding a scheduler.

## Git Tag

Recommended milestone tag:

```text
v0.67.0 = Historical Backfill Status Integration
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
git tag -a v0.67.0 -m "Historical Backfill Status Integration"
git push origin v0.67.0
```
