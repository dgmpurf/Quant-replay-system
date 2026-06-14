# Release Checkpoint v1.36.0

v1.36.0 is a report-only Active Replay Input Ready Decision checkpoint.

## Completed Scope

- `active-replay-input-ready-decision` core workflow exists.
- `active-replay-input-ready-decision-index`, `active-replay-input-ready-decision-health`, and `active-replay-input-ready-decision-status` exist.
- `research-status` exposes ready-decision context while preserving later `PAPER_WORKFLOW_READY` priority.
- The latest local ready-decision run id observed before checkpoint preparation was `0e6af6622f83`, with no-input status context and health `PASS`.

## Safety Boundary

This checkpoint does not emit ACTIVE_REPLAY_INPUT_READY. It does not create active replay input. It does not run replay. It does not create replay decisions. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading.

It also does not call broker APIs, place orders, send messages, call LLM APIs, call external APIs, mutate cache, write `data/raw`, write `data/processed`, write `data/cache`, run current-candidates, build snapshots, change signal semantics, or claim strategy performance is validated.

`READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION` remains a report-only review milestone. It is not `ACTIVE_REPLAY_INPUT_READY`.

## Validation

The v1.36.0 validation target is:

- ready-decision tests;
- emission, final-review, active-ready, acceptance, promotion, smoke, validator, and local dashboard regression tests;
- full `python -m pytest -m "not slow" -q`;
- ready-decision CLI and `research-status` dry-runs.

No git tag is created by this checkpoint document.
