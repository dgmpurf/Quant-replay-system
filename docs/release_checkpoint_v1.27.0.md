# Release Checkpoint v1.27.0

## Scope

v1.27.0 completes `research-status` integration and checkpoint documentation for
the report-only replay substrate schema fixture workflow.

## Current State

- latest fixture_id: `5f9a393ce90d`
- fixture status: PASS
- workflow_stage: `REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY`
- health_status: PASS
- entity_count: 14
- validation_issue_count: 0
- overclaim_guard_pass_count: 8
- overclaim_guard_total_count: 8
- active_replay_input: false
- forward_labels_exist: false
- weights_trained: false
- active_stock_profile_exists: false
- real_buy_review_eligible: false
- report_only: true
- diagnostic_only: true
- no_live_trading: true
- no_broker_api: true
- no_order_placement: true

## Commands

```powershell
python -m quant_replay_system.cli replay-substrate-schema-fixture
python -m quant_replay_system.cli replay-substrate-schema-fixture-index
python -m quant_replay_system.cli replay-substrate-schema-fixture-health
python -m quant_replay_system.cli replay-substrate-schema-fixture-status
python -m quant_replay_system.cli research-status
```

## Artifact Paths

- `outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1/5f9a393ce90d/`
- `outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1/index/`
- `outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1/health/`
- `outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1/status/`
- `outputs/reports/local_research_dashboard/<dashboard_id>/`

## Research-Status Integration

`research-status` now surfaces the latest replay substrate schema fixture as
replay/training preparation context. It exports the fixture id, stage, health,
entity count, validation issue count, overclaim guard counts, report-only flags,
and non-active safety booleans.

Later paper workflow priority remains preserved. A passing fixture is ready
context only, not active replay readiness. A failed fixture appears as a
schema-fixture blocker without implying trading, paper workflow, replay, labels,
training, stock-profile validation, or buy-review readiness.

## Schema-Fixture Semantics

Replay substrate schema fixture is report-only.
It proves schema/fixture contracts only.
It is not real replay.
It is not forward-label computation.
It is not model training.
It is not stock-profile validation.
It is not real buy-review eligibility.

## Safety

This checkpoint does not validate strategy performance.
This checkpoint does not compute forward labels.
This checkpoint does not train model weights.
This checkpoint does not create active stock profiles.
This checkpoint does not create real buy-review eligibility.
This checkpoint does not approve live trading or broker integration.

This checkpoint also confirms:

- no live trading
- no broker API
- no order placement
- no real messages
- no LLM or external API calls
- no market cache mutation
- no `data/raw` write
- no `data/processed` write
- no `data/cache` write
- no current-candidates generation
- no snapshot build
- no `APPROVED_FOR_PAPER`
- no signal semantics change
- schema fixtures remain non-active

## Test Results

Targeted tests:

```powershell
python -m pytest tests/test_replay_substrate_schema_fixture.py tests/test_local_research_dashboard.py -k "replay_substrate_schema_fixture"
```

Full non-slow validation should be run before tagging:

```powershell
python -m pytest -m "not slow"
```

## Next Branch

Recommended next branch: design the report-only historical replay substrate
readiness plan that consumes these schema contracts as context only and still
does not run replay, compute forward labels, train model weights, create active
stock profiles, or create real buy-review eligibility.
