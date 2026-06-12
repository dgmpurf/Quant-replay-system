# Release Checkpoint v1.29.0

## Scope

v1.29.0 completes `research-status` integration and checkpoint documentation for the report-only real historical replay input gate validator.

## Current State

- latest validator_run_id: `f541e3d477f7`
- validator status: `NO_INPUT`
- workflow_stage: `INPUT_GATE_VALIDATOR_NO_INPUT`
- health_status: PASS
- gate_count: 13
- passed_gate_count: 12
- blocked_gate_count: 1
- blocker_count: 1
- pass_candidate: false
- active_replay_input_ready: false
- active_replay_input: false
- forward_labels_exist: false
- weights_trained: false
- active_stock_profile_exists: false
- real_buy_review_eligible: false

## Commands

```powershell
python -m quant_replay_system.cli historical-replay-input-gate-validator
python -m quant_replay_system.cli historical-replay-input-gate-validator-index
python -m quant_replay_system.cli historical-replay-input-gate-validator-health
python -m quant_replay_system.cli historical-replay-input-gate-validator-status
python -m quant_replay_system.cli research-status
```

## Research-Status Integration

`research-status` now surfaces the latest real historical replay input gate validator as report-only replay-input context. It exports validator run id, status, stage, health, pass-candidate flag, active-ready flag, non-active safety booleans, report path, and next action.

The final workflow priority remains conservative. Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`. A validator `NO_INPUT` or pass-candidate context must not be interpreted as `ACTIVE_REPLAY_INPUT_READY`.

## Safety

This checkpoint does not run replay, compute forward labels, train model weights, create active stock profiles, create real buy-review eligibility, run current-candidates, build snapshots, mutate cache, write data inputs, call APIs, send messages, connect to brokers, place orders, apply `APPROVED_FOR_PAPER`, change signal semantics, or claim strategy performance is validated.

## Test Results

Targeted validation:

```powershell
python -m pytest tests/test_historical_replay_input_gate_validator.py tests/test_local_research_dashboard.py
```

Full non-slow validation should be run before tagging:

```powershell
python -m pytest -m "not slow"
```

## Next Branch

Recommended next branch: design a minimal real replay input package fixture for a future validator pass-candidate smoke. It should remain report-only and still avoid replay execution, current-candidates generation, snapshot builds, forward labels, training, stock profiles, buy-review eligibility, broker integration, messages, API calls, and cache mutation.

