# Release Checkpoint v1.32.0

## Scope

v1.32.0 completes `research-status` integration and checkpoint documentation for the report-only active replay input acceptance workflow.

## Current State

- acceptance command: `active-replay-input-acceptance`
- artifact views: `active-replay-input-acceptance-index`, `active-replay-input-acceptance-health`, `active-replay-input-acceptance-status`
- latest no-input CLI stage: `ACCEPTANCE_NO_INPUT`
- expected happy-path review stage: `ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW`
- active replay input ready: false
- active replay input: false
- active-ready emitted: false
- forward labels exist: false
- weights trained: false
- active stock profile exists: false
- real buy-review eligible: false
- approval applied: false

## Commands

```powershell
python -m quant_replay_system.cli active-replay-input-acceptance
python -m quant_replay_system.cli active-replay-input-acceptance-index
python -m quant_replay_system.cli active-replay-input-acceptance-health
python -m quant_replay_system.cli active-replay-input-acceptance-status
python -m quant_replay_system.cli research-status
```

## Research-Status Integration

`research-status` now surfaces the latest active replay input acceptance context. It exports the acceptance run id, status, health, workflow stage, acceptance artifact path, ready-for-active-ready-review flag, active-ready flags, report-only safety booleans, report path, and next action.

`ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW` is not active replay input and is not `ACTIVE_REPLAY_INPUT_READY`. It is a reviewable governance milestone only. Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; acceptance fields remain visible as context.

## Safety

This checkpoint does not implement live trading, add broker integration, automate orders, send real messages, call LLM/API or external APIs, mutate cache, write `data/raw`, write `data/processed`, write `data/cache`, run current-candidates, build snapshots, create active replay input, run replay, compute forward labels, train weights, create active stock profiles, create real buy-review eligibility, apply `APPROVED_FOR_PAPER`, change signal semantics, or claim strategy performance is validated.

Validator, smoke, promotion, and acceptance artifacts remain non-active. `REPLAY_INPUT_GATE_PASS_CANDIDATE`, `SMOKE_PASS_CANDIDATE_READY`, `PROMOTION_READY_FOR_HUMAN_REVIEW`, and `ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW` must not be treated as `ACTIVE_REPLAY_INPUT_READY`.

The acceptance checkpoint does not create active replay input. It does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, and does not create real buy-review eligibility.

## Test Results

Targeted validation:

```powershell
python -m pytest tests/test_active_replay_input_acceptance.py
python -m pytest tests/test_active_replay_input_promotion.py
python -m pytest tests/test_minimal_replay_input_package_fixture_smoke.py
python -m pytest tests/test_historical_replay_input_gate_validator.py
python -m pytest tests/test_local_research_dashboard.py
```

Full non-slow validation should be run before tagging:

```powershell
python -m pytest -m "not slow" -q
```

## Tag Recommendation

After validation and review, tag `v1.32.0`. No tag is created by this checkpoint document.

## Next Branch

Recommended next branch: design report-only active-ready governance for accepted replay input context. It should still avoid replay execution, current-candidates generation, snapshot builds, forward labels, training, active stock profiles, buy-review eligibility, broker integration, messages, API calls, and cache mutation.
