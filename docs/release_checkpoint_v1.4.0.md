# Release Checkpoint v1.4.0

## Milestone

PIT Universe Export Readiness Required Metadata Consolidation and Gate-Ordering Validation.

Recommended tag: `v1.4.0`.

## Completed Capabilities

- Required PIT universe metadata support for `pit-universe-overlay-review` is implemented and preserved in reviewed artifacts (`as_of_date`, `name`, `instrument_type`, `exchange`, `industry`, `min_lot`, `t_plus_rule`, `available_time`, `revision_id`, `source`).
- `pit-universe-overlay-export-readiness` evaluates reviewed rows with metadata-presence gates, PIT date gates, survivorship gates, evidence gates, and duplicate key gates.
- `pit-universe-overlay-export-readiness` supports `EXPORT_READY_REVIEW_ONLY` when at least one row is export-ready and others remain blocked.
- A narrow integration test now covers mixed ready/blocked rows and status-stage stability with duplicate-key blocking, missing metadata, unresolved survivorship, and PIT date invalidity in one fixture.
- Synthetic artifact smoke run confirms readiness behavior remains planning-only and visible-only:
  - synthetic review id: `155f7fb4d097`
  - synthetic export-readiness id: `b8f749d41076`
  - `export_ready_count=1`
  - `blocked_count=71`
  - `missing_required_columns_count=70`
  - `unresolved_survivorship_warning_count=70`
  - readiness status: `PASS`
  - stage: `EXPORT_READY_REVIEW_ONLY`
- Active workflow artifact context remains unchanged:
  - active review id: `7bc8ba08bf5a`
  - active export-readiness id: `75c6975e93e4`
  - `readiness_status: EXPORT_BLOCKED_NO_APPROVED_ROWS`
  - `export_ready_count=0`
  - unresolved survivorship warnings remain visible but not exported.

## Workflow Impact

The PIT universe pipeline now has a stricter evidence boundary before export:

```text
pit-universe-overlay-plan
-> pit-universe-overlay-review
-> pit-universe-overlay-export-readiness
-> reviewed export-readiness status + stage checks
-> reviewer-driven evidence completion
-> later explicit universe export workflow (future)
```

`EXPORT_READY_REVIEW_ONLY` is a non-blocking reviewable context when at least one row clears all checks and others do not.
It is not a candidate-generation result and does not trigger any current-candidates execution.

## Validation Baseline

- `python -m pytest`: 1347 passed, 2 warnings.
- `python -m pytest -m "not slow"`: 1238 passed, 109 deselected, 2 warnings.

## Safety Guarantees

- No universe export or usable universe export artifact was written.
- No write to `data/raw`.
- No write to `data/processed`.
- No `current-candidates` execution.
- No snapshot manifest build.
- No forward-label computation.
- No market cache mutation.
- No external network/API usage.
- No LLM/API workflow.
- No live trading.
- No broker API usage.
- No automated order placement.
- No real message delivery.

## Known Limitations

- The current active review still has zero approved export-ready rows (`0`), so active stage remains blocked for no-approved rows.
- Synthetic readiness progress and synthetic artifacts are diagnostics only and do not become active workflow context.
- Ready status can still be review-only until a complete, survivorship-safe and required-column-complete reviewed dataset exists.
- No per-date universe export workflow has been implemented yet.
- No snapshot-preparation execution workflow has been implemented yet.
- No strategy-performance claims are made by this checkpoint.

## Recommended Next Engineering Task

- Build a dedicated reviewed-export workflow that reads `export_ready=true` rows, outputs explicit date-scoped PIT universe files under an output-safe staging area, and keeps these writes out of `data/raw`/`data/processed` until explicitly approved.
- Add explicit end-to-end fixture where one row reaches true export-readiness after evidence completion and verify duplicate-key handling and stage transitions end-to-end.
- Keep `research-status` context-only behavior while surfacing explicit `PIT_UNIVERSE_EXPORT_READY_FOR_DRY_RUN` blockers and recommended human actions.
