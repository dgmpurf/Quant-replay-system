# Release Checkpoint v1.39.0

v1.39.0 is a report-only actual `ACTIVE_REPLAY_INPUT_READY` marker-only emission workflow checkpoint.

## Completed Scope

- `active-replay-input-ready-actual-emission` core workflow exists.
- `active-replay-input-ready-actual-emission-index`, `active-replay-input-ready-actual-emission-health`, and `active-replay-input-ready-actual-emission-status` exist.
- `research-status` exposes actual marker-only emission context while preserving later `PAPER_WORKFLOW_READY` priority.
- Latest no-input dry-run during checkpoint validation: `bb050d0e41f4`, status `NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT`, health `PASS`, workflow stage `ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_NO_INPUT`.
- Known marker-only happy-path dry-run with explicit allow flag: `c5c065f6437a`, status `ACTIVE_REPLAY_INPUT_READY`, marker emitted `true`.

## Marker-Only Boundary

Marker-only `ACTIVE_REPLAY_INPUT_READY` may exist in manual diagnostics when the explicit allow flag is used. It does not create active replay input. It does not run replay. It does not create replay decisions. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading.

It also does not call broker APIs, place orders, send messages, call LLM APIs, call external APIs, mutate cache, write `data/raw`, write `data/processed`, write `data/cache`, run current-candidates, build snapshots, change signal semantics, apply `APPROVED_FOR_PAPER`, or claim strategy performance is validated.

## Research-Status

`research-status` now includes the latest actual marker-only emission run id, status, health status, workflow stage, artifact path, marker-emitted flag, marker-file flag, marker-only-semantics flag, report path, next action, and safety flags.

Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; marker-only actual emission fields remain visible as context and do not create active replay input or replay permission.

## Validation

The v1.39.0 validation target is:

- actual marker-only emission workflow and artifact-view tests;
- active-ready emission, active-ready, ready-decision, emission, final-review, active-ready governance, acceptance, promotion, smoke, validator, and local dashboard regression tests;
- full `python -m pytest -m "not slow" -q`;
- full `python -m pytest -q`;
- actual marker-only emission CLI and `research-status` dry-runs.

No git tag is created by this checkpoint document.
