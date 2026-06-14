# Release Checkpoint v1.37.0

v1.37.0 is a report-only `ACTIVE_REPLAY_INPUT_READY` workflow checkpoint.

## Completed Scope

- `active-replay-input-ready` core workflow exists.
- `active-replay-input-ready-index`, `active-replay-input-ready-health`, and `active-replay-input-ready-status` exist.
- `research-status` exposes active-ready workflow context while preserving later `PAPER_WORKFLOW_READY` priority.
- The latest local active-ready run id observed before checkpoint preparation was `ac0d55bd52b2`, with no-input status context and health `PASS`.

## Safety Boundary

This checkpoint does not emit ACTIVE_REPLAY_INPUT_READY. It does not create active replay input. It does not run replay. It does not create replay decisions. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading.

It also does not call broker APIs, place orders, send messages, call LLM APIs, call external APIs, mutate cache, write `data/raw`, write `data/processed`, write `data/cache`, run current-candidates, build snapshots, change signal semantics, apply `APPROVED_FOR_PAPER`, or claim strategy performance is validated.

`READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY` remains a report-only review milestone. It is not `ACTIVE_REPLAY_INPUT_READY`.

## Research-Status

`research-status` now includes the latest active-ready workflow run id, status, health status, workflow stage, artifact path, ready-to-emit flag, report path, next action, and safety flags proving no active replay input, replay, replay decisions, labels, training, active stock profiles, buy-review eligibility, broker/order/message/API/cache/data side effects, current-candidates, snapshots, or signal semantics changes occurred.

## Validation

The v1.37.0 validation target is:

- active-ready workflow tests;
- ready-decision, emission, final-review, active-ready, acceptance, promotion, smoke, validator, and local dashboard regression tests;
- full `python -m pytest -m "not slow" -q`;
- active-ready CLI and `research-status` dry-runs.

No git tag is created by this checkpoint document.
