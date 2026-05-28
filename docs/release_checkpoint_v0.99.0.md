# Release Checkpoint v0.99.0

## Milestone

Current-Candidates Backfill Execution Manifest Research Status Integration v0.1.

Recommended tag: `v0.99.0`

## Completed Capabilities

- Integrated `current-candidates-backfill-execution-manifest-status` into unified `research-status`.
- Exposed the latest execution manifest id in `research-status`.
- Exposed the linked warmup-aware plan id in `research-status`.
- Exposed execution manifest status, stage, health status, row counts, ready count, blocked count, blocker counts, report path, and next action.
- Made `BLOCKED_UNIVERSE_AS_OF` visible at the top-level dashboard.
- Preserved plan-only and manifest-only semantics.
- Preserved later paper workflow priority.
- Kept execution manifest blockers visible as planning/readiness context, not as strategy failure or candidate-generation failure.

Latest local dry-run:

- latest execution manifest: `f98279630ce6`
- linked warmup-aware plan: `aadd86db24a1`
- status: `WARN`
- stage: `CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_BLOCKED`
- health: `PASS`
- row_count: `8`
- ready_count: `0`
- blocked_count: `8`
- blocked_universe_as_of_count: `8`

Latest `research-status` dry-run:

- final workflow_stage: `PAPER_WORKFLOW_READY`
- latest execution manifest visible: `f98279630ce6`
- blocked universe-as-of count visible: `8`
- later paper workflow priority preserved
- next manual action stayed on the WATCH_ONLY paper workflow path

## Workflow Impact

The multi-date current-candidates preparation path now has dashboard visibility through execution readiness:

```text
current-candidates-backfill-plan
-> current-candidates-backfill-execution-manifest
-> execution-manifest index / health / status
-> research-status
-> human review of blockers
-> future point-in-time universe / snapshot preparation
-> future reviewed current-candidates generation
```

The warmup-aware plan is market-data, warmup, and forward-horizon feasible, but execution readiness is blocked. The blocker is point-in-time validity of the universe artifact, not candidate generation.

## Key Blocker

- `BLOCKED_UNIVERSE_AS_OF=8`
- The existing universe artifact has `as_of_date=2024-05-20`.
- Planned signal dates include earlier dates such as `2024-04-02`.
- That universe artifact is too late to be point-in-time valid for those earlier signal dates.
- The next engineering step should be point-in-time universe / snapshot preparation planning before any candidate generation.

## Validation Baseline

- Backend tests: `1262 passed, 2 warnings`
- Quick tests: `1153 passed, 109 deselected, 2 warnings`

## Safety Guarantees

- No `current-candidates` generation was run by this milestone.
- No snapshot manifests were built.
- No `data-pipeline` run was invoked.
- No forward-return labels were computed.
- No market cache mutation was performed.
- No external API, network API, or LLM API calls were made.
- No real messages were sent.
- No broker API was connected.
- No live trading was implemented or invoked.
- No automated order placement was implemented or invoked.
- No strategy performance validation or market-edge claim is implied.
- Generated outputs remain ignored local artifacts and must not be committed unless explicitly reviewed.

## Known Limitations

- The latest execution manifest is blocked for all eight selected dates.
- The blocker is universe point-in-time validity, not market-cache horizon feasibility.
- The workflow still does not create per-date universe overlays.
- The workflow still does not create per-date snapshot manifests.
- The workflow still does not execute current-candidates.
- The workflow still does not compute forward-return labels or outcome evidence.
- No strategy performance, slippage, transaction-cost, benchmark, or paper-outcome evidence is produced.

## Recommended Next Engineering Tasks

- Design a point-in-time universe / snapshot preparation plan for the selected backfill signal dates.
- Keep the next step plan-only or manifest-only until required inputs are reviewed.
- Add explicit reviewed universe artifact requirements for earlier signal dates.
- Only after point-in-time inputs are ready, consider a separate reviewed current-candidates backfill execution task.
- Keep forward-return labels separate until candidate generation artifacts exist and are reviewed.
