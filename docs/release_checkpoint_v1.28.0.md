# Release Checkpoint v1.28.0

## Scope

v1.28.0 completes `research-status` integration and checkpoint documentation for the report-only historical replay input gate validator fixture workflow.

## Current State

- latest fixture_run_id: `c76d6f0c41d6`
- fixture status: PASS
- workflow_stage: `INPUT_GATE_VALIDATOR_FIXTURE_READY`
- health_status: PASS
- artifact_count: 2
- case_count: 68
- blocked_case_count: 67
- pass_candidate_case_count: 1
- active_ready_case_count: 0
- validation_issue_count: 0
- overclaim_guard_pass_count: 14
- overclaim_guard_total_count: 14
- active_replay_input: false
- forward_labels_exist: false
- weights_trained: false
- active_stock_profile_exists: false
- real_buy_review_eligible: false
- validator_implemented: false
- report_only: true
- diagnostic_only: true
- no_live_trading: true
- no_broker_api: true
- no_order_placement: true
- no_message_sent: true
- llm_api_called: false
- external_api_called: false
- cache_mutated: false
- current_candidates_run: false
- snapshot_built: false
- signal_semantics_changed: false

## Commands

```powershell
python -m quant_replay_system.cli historical-replay-input-gate-validator-fixture
python -m quant_replay_system.cli historical-replay-input-gate-validator-fixture-index
python -m quant_replay_system.cli historical-replay-input-gate-validator-fixture-health
python -m quant_replay_system.cli historical-replay-input-gate-validator-fixture-status
python -m quant_replay_system.cli research-status
```

## Artifact Paths

- `outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1/c76d6f0c41d6/`
- `outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1/index/`
- `outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1/health/`
- `outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1/status/`
- `outputs/reports/local_research_dashboard/<dashboard_id>/`

## Research-Status Integration

`research-status` now surfaces the latest historical replay input gate validator fixture as replay-readiness design context. It exports fixture run id, stage, health, case counts, blocked/pass-candidate counts, overclaim guard counts, report-only flags, non-active safety booleans, and the report path.

This fixture is report-only and not the real validator. It is not real replay and it is not active replay input. It does not compute forward labels, train weights, create active stock profiles, or create real buy-review eligibility.

The final workflow priority remains conservative. Later paper workflow, current advisory workflow, v1.27 replay substrate schema fixture, and future paper workflow artifacts remain higher priority. The input-gate validator fixture is visible as context and must not be interpreted as `ACTIVE_REPLAY_INPUT_READY`, `REAL_REPLAY_READY`, `FORWARD_LABEL_READY`, `TRAINING_READY`, `STOCK_PROFILE_READY`, or `REAL_BUY_REVIEW_READY`.

## Safety

This checkpoint does not validate strategy performance.
This checkpoint does not implement the real historical replay input gate validator.
This checkpoint does not run real replay.
This checkpoint does not create active replay input.
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
- no cache mutation
- no `data/raw` write
- no `data/processed` write
- no `data/cache` write
- no current-candidates generation
- no snapshot build
- no `APPROVED_FOR_PAPER`
- no signal semantics change
- fixture outputs remain non-active

## Test Results

Targeted tests:

```powershell
python -m pytest tests/test_historical_replay_input_gate_validator_fixture.py tests/test_local_research_dashboard.py -k "input_gate_validator_fixture or v1_28"
```

Full non-slow validation should be run before tagging:

```powershell
python -m pytest -m "not slow"
```

## Next Branch

Recommended next branch: design the real historical replay input gate validator as a report-only preview first, using this fixture as contract context only. The next branch should still avoid real replay, forward labels, training, active stock profiles, buy-review eligibility, current-candidates generation, snapshots, broker integration, orders, messages, API calls, and cache mutation.
