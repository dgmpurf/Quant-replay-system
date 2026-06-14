# Release Checkpoint v1.38.0

v1.38.0 is a report-only `ACTIVE_REPLAY_INPUT_READY` emission-decision workflow checkpoint.

## Completed Scope

- `active-replay-input-ready-emission` core workflow exists.
- `active-replay-input-ready-emission-index`, `active-replay-input-ready-emission-health`, and `active-replay-input-ready-emission-status` exist.
- `research-status` exposes emission-decision context while preserving later `PAPER_WORKFLOW_READY` priority.
- The latest local emission-decision run id observed before checkpoint preparation was `600667038f01`.
- Latest observed status was `NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT`.
- Latest observed health was `PASS`.
- Latest observed workflow stage was `ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION_NO_INPUT`.

## Safety Boundary

This checkpoint does not emit ACTIVE_REPLAY_INPUT_READY. It does not create active replay input. It does not run replay. It does not create replay decisions. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading.

It also does not call broker APIs, place orders, send messages, call LLM APIs, call external APIs, mutate cache, write `data/raw`, write `data/processed`, write `data/cache`, run current-candidates, build snapshots, change signal semantics, apply `APPROVED_FOR_PAPER`, or claim strategy performance is validated.

`READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION` remains a report-only review milestone. It is not `ACTIVE_REPLAY_INPUT_READY`.

## Research-Status

`research-status` now includes the latest emission-decision run id, status, health status, workflow stage, artifact path, ready-for-emission-decision flag, report path, next action, and safety flags proving no active-ready emission, active replay input, replay, replay decisions, labels, training, active stock profiles, buy-review eligibility, broker/order/message/API/cache/data side effects, current-candidates, snapshots, or signal semantics changes occurred.

Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; emission-decision fields remain visible as context.

## Validation

The v1.38.0 validation target is:

- active-ready emission workflow and artifact-view tests;
- active-ready, ready-decision, emission, final-review, active-ready, acceptance, promotion, smoke, validator, and local dashboard regression tests;
- full `python -m pytest -m "not slow" -q`;
- full `python -m pytest -q`;
- active-ready emission CLI and `research-status` dry-runs.

No git tag is created by this checkpoint document.
