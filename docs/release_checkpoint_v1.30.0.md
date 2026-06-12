# Release Checkpoint v1.30.0

## Scope

v1.30.0 completes `research-status` integration and checkpoint documentation for the report-only minimal replay input package fixture smoke.

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

## Commands

```powershell
python -m quant_replay_system.cli minimal-replay-input-package-fixture-smoke
python -m quant_replay_system.cli minimal-replay-input-package-fixture-smoke-index
python -m quant_replay_system.cli minimal-replay-input-package-fixture-smoke-health
python -m quant_replay_system.cli minimal-replay-input-package-fixture-smoke-status
python -m quant_replay_system.cli research-status
```

## Research-Status Integration

`research-status` now surfaces the latest minimal replay input package fixture smoke as report-only replay-input context. It exports smoke run id, smoke status, health, `SMOKE_PASS_CANDIDATE_READY`, input package path, linked validator run id, `REPLAY_INPUT_GATE_PASS_CANDIDATE`, pass-candidate flag, active-ready flag, non-active safety booleans, report path, and next action.

This checkpoint does not emit `ACTIVE_REPLAY_INPUT_READY`. The smoke pass-candidate state is not active replay input and must not be promoted without a future explicit workflow.

Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; smoke fields remain visible only as context.

## Safety

This checkpoint does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, and does not create real buy-review eligibility.

It also does not run current-candidates, build snapshots, mutate cache, write `data/raw`, write `data/processed`, write `data/cache`, call LLM/API or external APIs, send messages, connect to brokers, place orders, apply `APPROVED_FOR_PAPER`, change signal semantics, or claim strategy performance is validated.

## Test Results

Targeted validation:

```powershell
python -m pytest tests/test_minimal_replay_input_package_fixture_smoke.py tests/test_historical_replay_input_gate_validator.py tests/test_local_research_dashboard.py
```

Full non-slow validation should be run before tagging:

```powershell
python -m pytest -m "not slow"
```

## Tag Recommendation

After validation and review, tag `v1.30.0`. No tag is created by this checkpoint document.

## Next Branch

Recommended next branch: design the smallest report-only promotion-planning workflow that can explain what extra review would be required before a smoke pass-candidate could ever become active replay input. It should still avoid replay execution, current-candidates generation, snapshot builds, forward labels, training, stock profiles, buy-review eligibility, broker integration, messages, API calls, and cache mutation.
