# Release Checkpoint v1.40.0

v1.40.0 is a report-only Active Replay Input Creation workflow checkpoint.

## Completed Scope

- `active-replay-input-create` core workflow exists.
- `active-replay-input-create-index`, `active-replay-input-create-health`, and `active-replay-input-create-status` exist.
- `research-status` exposes active replay input creation context while preserving later `PAPER_WORKFLOW_READY` priority.
- Latest no-input dry-run during checkpoint validation: `7fa0242a730b`, status `NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT`, health `PASS`, workflow stage `ACTIVE_REPLAY_INPUT_CREATE_NO_INPUT`.
- Known pre-creation happy path without explicit allow flag: `2e23b1b3a055`, status `READY_FOR_ACTIVE_REPLAY_INPUT_CREATION`, active replay input created `false`.
- Known report-only active-input-created happy path with explicit allow flag: `293deb5f459a`, status `ACTIVE_REPLAY_INPUT_CREATED`, active replay input created `true`.

## Report-Only Boundary

`ACTIVE_REPLAY_INPUT_CREATED` may exist in manual diagnostics when the explicit allow flag is used. It creates a governed report-only `active_replay_input.json` artifact for a future separate replay execution workflow.

It does not run replay. It does not create replay decisions. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading.

It also does not call broker APIs, place orders, send messages, call LLM APIs, call external APIs, mutate cache, write `data/raw`, write `data/processed`, write `data/cache`, run current-candidates, build snapshots, change signal semantics, apply `APPROVED_FOR_PAPER`, or claim strategy performance is validated.

## Research-Status

`research-status` now includes the latest active replay input creation run id, status, health status, workflow stage, artifact path, active replay input flags, marker lineage fields, PIT/source/evidence/taxonomy coverage, report path, next action, and safety flags.

Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; active input creation fields remain visible as context and do not create replay execution permission, replay decisions, forward labels, training, active stock profiles, real buy-review eligibility, or trading authorization.

## Validation

The v1.40.0 validation target is:

- active replay input creation workflow, artifact-view, research-status, and documentation tests;
- active-ready actual emission, ready emission, active-ready, ready-decision, emission, final-review, active-ready governance, acceptance, promotion, smoke, validator, and local dashboard regression tests;
- full `python -m pytest -m "not slow" -q`;
- full `python -m pytest -q`;
- active input creation CLI and `research-status` dry-runs.

No git tag is created by this checkpoint document.
