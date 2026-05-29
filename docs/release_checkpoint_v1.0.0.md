# Release Checkpoint v1.0.0: PIT Universe Overlay Preparation Path

## Milestone Name

Point-in-Time Universe Overlay Preparation Path v1.0.0.

## Completed Capabilities

- Warmup-aware multi-date current-candidates backfill planning.
- Current-candidates backfill execution manifest readiness checks.
- Execution manifest index, health, and status views.
- Research-status visibility for execution manifest readiness and `BLOCKED_UNIVERSE_AS_OF`.
- Point-in-time universe overlay preparation plan.
- PIT universe overlay plan index, health, and status views.
- Research-status visibility for PIT universe overlay preparation context.
- Manual-review templates for signal dates blocked by future universe artifacts.
- Survivorship-bias warning visibility for rows derived from a later universe.
- Local-only safety metadata across the plan and artifact views.

The project now has a plan-only path:

```text
warmup-aware current-candidates backfill plan
-> current-candidates backfill execution manifest
-> PIT universe overlay preparation plan
-> PIT universe overlay plan index / health / status
-> unified research-status PIT universe preparation context
-> later manual review and snapshot preparation
```

## Workflow Impact

The workflow can now identify that a multi-date backfill plan is market/warmup/forward-horizon feasible while still blocking execution when the available universe artifact is not point-in-time valid for selected signal dates.

For the latest local path:

- warmup-aware plan id: `aadd86db24a1`
- execution manifest id: `f98279630ce6`
- execution manifest blocker: `BLOCKED_UNIVERSE_AS_OF=8`
- PIT overlay plan id: `38a254c54024`
- PIT overlay plan rows: 72
- signal dates: 8
- symbols: 9
- `NEEDS_MANUAL_REVIEW=72`
- `survivorship_bias_warning_count=72`
- `valid_for_signal_date_count=0`

The PIT overlay plan is a review surface only. It does not make the universe valid and does not permit candidate generation.

Unified `research-status` now shows the latest PIT overlay plan id, review counts, valid-for-signal-date count, survivorship-bias warning count, health status, and report path while preserving later paper workflow priority.

## Validation Baseline

- Backend tests: 1276 passed, 2 warnings.
- Quick tests: 1167 passed, 109 deselected, 2 warnings.

## Safety Guarantees

- No multi-date current-candidates generation.
- No snapshot manifest build.
- No data-pipeline execution.
- No forward-return labels.
- No market cache mutation.
- No live trading.
- No broker API.
- No automated order placement.
- No real message delivery.
- No LLM/API calls.
- No strategy performance validation.
- Generated output artifacts remain ignored and must not be committed.

## Known Limitations

- PIT universe overlay rows remain templates until manually reviewed.
- The workflow does not verify listing/delisting evidence.
- The workflow does not approve `include_flag=true` automatically.
- The workflow does not build per-date snapshots.
- The workflow does not run current-candidates from the generated templates.
- Forward-return labels and multi-date outcome evidence remain future work.
- v1.0.0 is research infrastructure, not trading automation.

## Recommended Next Engineering Tasks

1. Add a reviewed PIT universe overlay approval workflow with explicit evidence fields.
2. Add snapshot-preparation planning that consumes reviewed PIT universe overlays without building snapshots automatically.
3. Add point-in-time universe health checks for listing/delisting dates and available-time evidence.
4. Only after reviewed PIT inputs exist, plan a separate reviewed multi-date current-candidates execution workflow.
5. Continue exposing PIT preparation progress in `research-status` without changing trading behavior.

## Recommended Tag

`v1.0.0`
