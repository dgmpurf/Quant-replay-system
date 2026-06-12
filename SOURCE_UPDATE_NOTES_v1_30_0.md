# Source Update Notes v1.30.0

## Purpose

Use this note when refreshing the ChatGPT Project Source after tag v1.30.0 for the minimal replay input package fixture smoke checkpoint.

`docs/project_sources/ is intentionally absent from Git`. ChatGPT Project Source is maintained separately and should be refreshed manually from the files listed below after tag v1.30.0.

## Files To Include

- `docs/minimal_replay_input_package_fixture_smoke.md`
- `docs/release_checkpoint_v1.30.0.md`
- `SOURCE_UPDATE_NOTES_v1_30_0.md`
- `docs/local_research_dashboard.md`
- `README.md`

## Current State

- latest smoke_run_id: `b5528887de2a`
- latest validator_run_id: `a574688b3b95`
- validator status: `REPLAY_INPUT_GATE_PASS_CANDIDATE`
- smoke workflow_stage: `SMOKE_PASS_CANDIDATE_READY`
- health_status: PASS
- pass_candidate: true
- active_replay_input_ready: false
- active_replay_input: false
- forward_labels_exist: false
- weights_trained: false
- active_stock_profile_exists: false
- real_buy_review_eligible: false
- approval_applied: false

## Source Summary

The minimal replay input package fixture smoke is now visible in `research-status` as report-only context. It can produce `REPLAY_INPUT_GATE_PASS_CANDIDATE` and `SMOKE_PASS_CANDIDATE_READY`, but it is not active replay input and it is not `ACTIVE_REPLAY_INPUT_READY`.

Commands now documented for Project Source refresh:

- `minimal-replay-input-package-fixture-smoke`
- `minimal-replay-input-package-fixture-smoke-index`
- `minimal-replay-input-package-fixture-smoke-health`
- `minimal-replay-input-package-fixture-smoke-status`

The smoke does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, and does not create real buy-review eligibility.

It also does not run current-candidates, build snapshots, mutate cache, call LLM/API or external APIs, write `data/raw`, write `data/processed`, write `data/cache`, send messages, connect to brokers, place orders, apply `APPROVED_FOR_PAPER`, change signal semantics, or validate strategy performance.

## Safety Boundaries

- no live trading
- no broker API
- no order placement
- no real messages
- no LLM/API calls
- no external API calls
- no cache mutation
- no data/raw write
- no data/processed write
- no data/cache write
- no current-candidates generation
- no snapshot build
- no forward labels
- no training
- no active stock profile
- no real buy-review eligibility
- no active replay input
- no `ACTIVE_REPLAY_INPUT_READY`
- no git tag or commit implied by this note

## Recommended Next Branch

Design the smallest report-only active-replay-input promotion planning audit. It should explain required manual review gates without promoting any smoke, validator, fixture, or design artifact into active replay input.
