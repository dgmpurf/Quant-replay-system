# Release Checkpoint v0.71.0

## Release Summary

`v0.71.0` marks the Active Snapshot Warning Actionability checkpoint.

This milestone refines the unified `research-status` dashboard so snapshot-quality warnings are interpreted through the active linked workflow chain. Older standalone snapshot WARN artifacts remain visible as context, but they no longer override an active linked PASS chain from market-cache-export, market-update-handoff, current-candidates, or paper workflow artifacts.

It is a local research workflow and dashboard-semantics checkpoint. It is not a live trading release, broker integration, order automation system, scheduler, strategy-quality proof, or profit guarantee.

## Completed Capabilities

This checkpoint includes:

- Active snapshot chain selection in `research-status`.
- Linked snapshot-quality status handling for reviewed cache export, market update handoff, current candidates, and paper workflow paths.
- Stale and unrelated snapshot warning classification.
- Active linked snapshot PASS handling that prevents older standalone WARN artifacts from driving the final workflow stage.
- Active linked snapshot WARN/FAIL handling that remains actionable or blocking.
- Market-cache-export snapshot integration through `snapshot_quality_status`, snapshot manifest, and snapshot report linkage.
- Paper workflow priority preservation over snapshot/export stages.
- Exported CSV, metadata JSON, Markdown, and CLI fields for snapshot actionability:
  - `active_snapshot_chain`
  - `linked_snapshot_quality_status`
  - `active_snapshot_warning_count`
  - `active_snapshot_error_count`
  - `stale_snapshot_warning_count`
  - `unrelated_snapshot_warning_count`
- Regression coverage for active linked PASS, active linked WARN, active linked FAIL, standalone fallback behavior, paper priority, and exported dashboard fields.

## Workflow Impact

The active snapshot actionability chain is:

```text
market cache export / market update handoff / current candidates / paper workflow
-> linked snapshot-quality status
-> active snapshot chain selection
-> research-status actionability
-> next manual action
```

The dashboard now distinguishes between:

- Active linked snapshot PASS: not actionable.
- Active linked snapshot WARN: actionable warning.
- Active linked snapshot FAIL: blocking error.
- Stale or unrelated snapshot WARN: visible context, not a final blocker when an active linked PASS chain exists.
- No linked active chain: fallback to latest standalone snapshot-quality behavior.

This keeps real active warnings visible while avoiding false regressions to `LOCAL_RESEARCH_NEEDS_ATTENTION` from older unrelated snapshot artifacts.

## Latest Local Verification Baseline

Latest reviewed cache export status:

- Market-cache-export-status: `PASS`
- Export ID: `ddfc7d148813`
- Stage: `SNAPSHOT_READY_FROM_EXPORT`
- Linked pipeline ID: `ffe6d69c79e8`
- Linked snapshot quality: `PASS`

Latest unified research status:

- Status: `WARN`
- Final workflow stage: `PAPER_WORKFLOW_READY`
- Active snapshot chain: `CURRENT_CANDIDATES`
- Linked snapshot quality status: `PASS`
- Active snapshot warnings/errors: `0 / 0`
- Stale/unrelated snapshot warnings: `0 / 2`
- Next manual action stayed on the paper workflow path instead of stale snapshot warning review.

## Validation Baseline

Latest validation baseline for this checkpoint:

- Focused dashboard tests: `python -m pytest tests/test_local_research_dashboard.py`, 51 passed.
- Export artifact tests: `python -m pytest tests/test_market_cache_export_artifact_views.py`, 10 passed.
- Backend tests: `python -m pytest`, 952 passed, 2 warnings.
- Quick tests: `python -m pytest -m "not slow"`, 843 passed, 109 deselected, 2 warnings.
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
- No secrets are printed or written to reports.
- No real network calls are required in automated tests.
- Generated `data/cache`, `data/raw`, `data/processed`, and `outputs` artifacts are local/ignored and must not be committed.
- Stale snapshot warnings are not deleted or hidden; they are classified separately from active linked workflow warnings.
- Data-quality and snapshot-quality gates remain required before research use.
- Demo candidates and paper workflow outputs remain workflow-validation artifacts, not strategy recommendations.

## Known Limitations

- Snapshot actionability depends on available linkage metadata.
- If future artifacts omit snapshot linkage, `research-status` falls back conservatively.
- Stale warnings remain visible in dashboard context and should still be reviewed during cleanup.
- This checkpoint does not certify data quality by itself.
- Data-pipeline, data-quality, and snapshot-quality remain required for research-ready snapshots.
- The dashboard distinguishes actionability; it does not delete, rewrite, or repair older artifacts.

## Recommended Next Engineering Tasks

1. Add a small artifact cleanup or archival guidance document for stale local snapshot-quality artifacts, without deleting user data automatically.
2. Extend active-chain linkage tests as new workflow artifact types are added.
3. Add a dashboard field reference table for downstream consumers that read `research-status` CSV/metadata.
4. Continue cache-export-to-current-candidates smoke verification using the reviewed export snapshot manifest.
5. Continue policy-aware but explicitly gated source-selection design for reviewed cache exports.

## Git Tag

Recommended milestone tag:

```text
v0.71.0 = Active Snapshot Warning Actionability
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
git tag -a v0.71.0 -m "Active Snapshot Warning Actionability"
git push origin v0.71.0
```
