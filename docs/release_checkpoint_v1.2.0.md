# Release Checkpoint v1.2.0

## Milestone

PIT Universe Overlay Export Readiness Artifact Views and Research Status Integration.

Recommended tag: `v1.2.0`

## Completed Capabilities

- Added `pit-universe-overlay-export-readiness-index` for discovering local export-readiness artifacts.
- Added `pit-universe-overlay-export-readiness-health` for checking report-only safety and artifact completeness.
- Added `pit-universe-overlay-export-readiness-status` for summarizing latest readiness stage, counts, blockers, and next action.
- Integrated latest export-readiness status into unified `research-status`.
- Exposed latest export-readiness id, linked review id, health status, approved count, export-ready count, blocked count, no-approved-rows flag, missing required-column count, unresolved survivorship-warning count, report path, and next action.
- Preserved later paper workflow priority when export-readiness artifacts are present.
- Kept blocked no-approved-rows readiness visible as PIT universe preparation context, not a candidate-generation failure.

## Workflow Impact

The project now has a visible planning chain:

```text
warmup-aware current-candidates backfill plan
-> current-candidates backfill execution manifest
-> PIT universe overlay plan
-> PIT universe overlay review
-> PIT universe overlay export readiness
-> artifact index / health / status
-> unified research-status
```

The current latest review remains blocked for export because `approved_count=0`; therefore export readiness reports no export-ready rows and no usable universe export has occurred.

## Validation Baseline

- `python -m pytest`: run for this checkpoint validation.
- `python -m pytest -m "not slow"`: run for quick validation.
- Local dry-run checks:
  - `pit-universe-overlay-export-readiness-index`
  - `pit-universe-overlay-export-readiness-health`
  - `pit-universe-overlay-export-readiness-status`
  - `research-status`

## Safety Guarantees

- Export readiness is report-only.
- No usable universe files are exported.
- No `data/raw` write occurs.
- No `data/processed` write occurs.
- No current-candidates generation occurs.
- No snapshot manifest is built.
- No forward labels are computed.
- No market cache mutation occurs.
- No live trading is enabled.
- No broker API is called.
- No automated order placement is performed.
- No real messages are sent.
- No LLM/API or external API calls are required.
- No strategy performance validation is claimed.

## Known Limitations

- The latest reviewed PIT universe overlay has zero approved rows, so export readiness is blocked.
- Readiness artifacts do not fill missing universe columns automatically.
- Readiness artifacts do not write accepted rows into `data/raw` or `data/processed`.
- A later explicit, reviewed universe export workflow is still required.
- No snapshot preparation, multi-date candidate generation, or forward-return labels are implemented yet.
- Export-ready rows, if present later, remain review evidence only until a separate explicit export workflow is implemented.

## Recommended Next Engineering Tasks

- Design a reviewed PIT universe overlay export workflow that remains dry-run-first and writes under `outputs/reports` before any explicit accepted write to `data/raw`.
- Add export workflow gates for complete current-candidates universe schema, reviewer identity, evidence references, duplicate-key checks, and point-in-time date validity.
- Continue preserving `research-status` priority so planning blockers do not override later valid paper workflow artifacts.

