# Release Checkpoint v0.74.0

## Release Summary

`v0.74.0` marks the Partial Historical Backfill Cache-Write Actionability checkpoint.

This milestone refines historical-backfill status semantics so a guarded cache-write run with accepted rows and protective preflight-rejected rows can be reported as a partial, reviewable cache-write outcome instead of a generic corrupt or blocking backfill failure.

It is a local research workflow and dashboard actionability checkpoint. It is not a live trading release, broker integration, automated order system, scheduler, cache-write approval shortcut, data-quality certification, strategy-quality proof, or profit guarantee.

## Completed Capabilities

This checkpoint includes:

- Partial historical backfill actionability classification.
- Protective preflight rejection classification for rows blocked before cache ingestion.
- `BACKFILL_PARTIAL_WITH_REJECTIONS` workflow stage for explicit cache-write runs where accepted rows were written and rejected rows were blocked.
- Rejected row counts, preflight-rejected counts, comparison-failed counts, rejected symbols, rejected sources, and rejected issue categories in status/report/metadata.
- `cache_write_partial` tracking.
- `research-status` integration of partial backfill context.
- Preservation of later reviewed export, snapshot, current-candidates, market-update-handoff, and paper workflow priority.
- Blocking behavior remains for all-fail backfills, missing/unreadable artifacts, metadata failures, runtime failures, or cache-write attempts where no rows were safely accepted.

## Workflow Chain

The completed local workflow chain is:

```text
historical-backfill
-> market-cache-preflight
-> explicit --accept-cache-write
-> partial accepted/rejected row classification
-> historical-backfill-status
-> research-status
-> reviewed export / snapshot / current-candidates / paper workflow as later stages
```

Rejected rows remain failed and review-required. Accepted cache-written rows can still be used through later reviewed export and snapshot validation paths when those downstream gates pass.

## Workflow Impact

`historical-backfill-status` can now distinguish:

- successful cache-write backfills,
- dry-run or provisional warnings needing review,
- partial cache-write runs with protective preflight rejections,
- truly blocking failed backfills.

Latest local dry-run behavior:

- Latest backfill ID: `2ef39da025e4`
- Status: `WARN`
- Stage: `BACKFILL_PARTIAL_WITH_REJECTIONS`
- Accepted / rejected / preflight rejected / comparison failed: `8 / 2 / 2 / 2`
- `cache_write_occurred`: `True`
- `cache_write_partial`: `True`
- Rejected symbols: `300750,688981`
- Next action: review rejected rows; accepted rows were cache-written; use reviewed export/snapshot path if downstream validation passed.

Unified `research-status` behavior:

- Status: `WARN`
- Final workflow stage: `PAPER_WORKFLOW_READY`
- Active snapshot chain: `CURRENT_CANDIDATES`
- Linked snapshot quality: `PASS`
- Historical backfill stage: `BACKFILL_PARTIAL_WITH_REJECTIONS`
- Later paper workflow priority preserved.

## Validation Baseline

Latest validation baseline for this checkpoint:

- Backend tests: `python -m pytest`, 995 passed, 2 warnings.
- Quick tests: `python -m pytest -m "not slow"`, 886 passed, 109 deselected, 2 warnings.
- No live trading.
- No broker integration.
- No automated orders.
- No scheduler, cron job, background job, or GitHub Actions workflow.
- No secrets printed or stored.
- No real network/API calls in automated tests.
- No market cache mutation during status, dashboard reporting, checkpoint documentation, or validation.

## Safety Boundaries

The checkpoint preserves these boundaries:

- No live trading is implemented.
- No broker API is invoked.
- No automated order placement is implemented.
- No scheduler, cron job, background job, or GitHub Actions workflow is added.
- Cache writes still require explicit `--accept-cache-write`.
- Rejected rows are not hidden.
- Rejected rows are not marked successful.
- Preflight gates are not weakened.
- Data-quality and snapshot-quality gates are not weakened.
- Generated `data/cache`, `data/raw`, `data/processed`, and `outputs` artifacts are local/ignored and must not be committed.
- Partial cache-write status is an audit/actionability classification, not source approval or data certification.

## Known Limitations

- Rejected row review is still manual.
- Partial classification depends on readable result rows and preflight issue metadata.
- `300750` and `688981` BaoStock rows still need separate rejection diagnostics before rerun or approval.
- ETF/Sina remains provisional until another ETF reference source is validated.
- Downstream validation can pass only for reviewed exports that exclude rejected source rows.
- Broader symbol universe expansion still needs staged validation.
- Partial cache-write actionability does not certify strategy quality or source truth.

## Recommended Next Engineering Tasks

1. Add focused rejection diagnostics for the blocked BaoStock `300750` and `688981` rows.
2. Add a reviewed rejected-row decision log so future reruns can document keep/drop/source-retry decisions.
3. Run another staged policy-plan/export smoke after rejected-row review, keeping cache writes explicit.
4. Expand ETF reference-source validation before changing ETF/Sina provisional policy.
5. Add checkpoint docs after the next major actionability or dashboard-semantics change.

## Git Tag

Recommended milestone tag:

```text
v0.74.0 = Partial Historical Backfill Cache-Write Actionability
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
git tag -a v0.74.0 -m "Partial Historical Backfill Cache-Write Actionability"
git push origin v0.74.0
```
