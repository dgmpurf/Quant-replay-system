# Source Update Notes v1.28.0

## Purpose

Use this note when refreshing the ChatGPT Project Source after the v1.28.0 historical replay input gate validator fixture checkpoint.

## Files To Include

- `docs/historical_replay_input_gate_validator_fixture.md`
- `docs/release_checkpoint_v1.28.0.md`
- `SOURCE_UPDATE_NOTES_v1_28_0.md`
- `docs/local_research_dashboard.md`
- `README.md`

## Current State

- latest fixture_run_id: `c76d6f0c41d6`
- stage: `INPUT_GATE_VALIDATOR_FIXTURE_READY`
- status: PASS
- health_status: PASS
- case_count: 68
- blocked_case_count: 67
- pass_candidate_case_count: 1
- active_ready_case_count: 0
- validation_issue_count: 0
- active_replay_input: false
- forward_labels_exist: false
- weights_trained: false
- active_stock_profile_exists: false
- real_buy_review_eligible: false
- validator_implemented: false
- report_only: true
- diagnostic_only: true

## Source Summary

The historical replay input gate validator fixture is now visible in `research-status` as report-only context. It is not the real validator. It is not real replay. It is not active replay input.

The fixture does not compute forward labels, train weights, create active stock profiles, create real buy-review eligibility, run current-candidates, build snapshots, mutate cache, call LLM/API or external APIs, write `data/raw`, write `data/processed`, send messages, connect to brokers, or place orders.

`research-status` exports the latest fixture run id, status, stage, health, case counts, overclaim guard counts, safety booleans, report path, and next action. Later paper workflow, current advisory workflow, v1.27 replay substrate schema fixture, and future paper workflow artifacts retain priority.

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
- no real replay
- no real validator
- no git tag or commit implied by this note

## Recommended Next Branch

Design the real historical replay input gate validator as a report-only preview first. It should consume the v1.27 replay substrate schema fixture and the v1.28 input-gate fixture contracts as context only, and should still not run replay, compute labels, train weights, generate stock profiles, create buy-review eligibility, run current-candidates, build snapshots, mutate cache, call APIs, send messages, or place orders.
