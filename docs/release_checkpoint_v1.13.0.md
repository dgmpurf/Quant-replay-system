# Release Checkpoint v1.13.0

## Milestone

Activated Replacement Worklist Evidence Update Planning as report-only manual evidence context.

## Completed Capabilities

- Added `activated-replacement-worklist-evidence-update-plan`.
- Added evidence-update plan index, health, and status views.
- Integrated the evidence-update plan status into unified `research-status`.
- Preserved lineage to the legacy worklist, policy audit, split plan, replacement plan, acceptance artifact, and activation artifact.
- Generated profile-specific evidence worklists and update templates for `stock_core`, `etf_core`, and `mixed_demo_core`.
- Generated first-batch evidence packages for `stock_core` and `etf_core`.
- Kept all rows non-approved and evidence-incomplete.
- Kept later paper workflow priority intact in `research-status`.

## Workflow Impact

The project now has a report-only bridge from activated replacement planning context to profile-specific manual evidence work. Evidence collection can start from `stock_core` and `etf_core` packages instead of the ambiguous legacy mixed `etf_core` worklist.

The workflow does not create clean review updates and does not make any row valid for PIT universe use. Manual evidence must still be completed and validated through the separate PIT universe evidence update ingestion and overlay review workflows.

## Validation Baseline

Validation for this checkpoint should run:

```powershell
python -m pytest
python -m pytest -m "not slow"
```

## Safety Guarantees

- No approval or rejection is applied.
- No active worklist is mutated.
- No clean review-updates artifact is created.
- No universe export is produced.
- No `data/raw` or `data/processed` write is performed.
- No current-candidates generation is run.
- No snapshot manifests are built.
- No forward labels are computed.
- No cache mutation is performed.
- No live trading, broker API, order placement, or message delivery is implemented or invoked.
- No network/API/LLM calls are required.
- Generated outputs under `outputs/reports` remain ignored and must not be committed.

## Known Limitations

- Evidence packages are not active worklists.
- Rows remain `NEEDS_MANUAL_REVIEW`.
- Hints are non-authoritative and cannot resolve survivorship or PIT validity by themselves.
- The workflow does not validate strategy performance or market edge.
- Follow-on evidence ingestion, reviewed overlay approval, export readiness, staging, and accepted export remain separate explicit workflows.

## Recommended Next Engineering Tasks

1. Use the profile-specific evidence packages for a small manual evidence fill batch.
2. Validate completed rows with `pit-universe-evidence-update-ingestion`.
3. Keep active legacy worklists unchanged until a separate explicit handoff is designed.
4. Continue preserving paper workflow priority in unified `research-status`.

## Recommended Tag

`v1.13.0`
