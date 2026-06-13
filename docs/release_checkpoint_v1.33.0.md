# Release Checkpoint v1.33.0

## Scope

v1.33.0 completes `research-status` integration and checkpoint documentation for the report-only Active Replay Input Active-Ready workflow.

## Current State

- active-ready command: `active-replay-input-active-ready`
- artifact views: `active-replay-input-active-ready-index`, `active-replay-input-active-ready-health`, `active-replay-input-active-ready-status`
- latest no-input CLI run id: `89a328ee13f7`
- latest no-input status stage: `ACTIVE_READY_NO_INPUT`
- latest health: `PASS`
- happy-path fixture stage: `ACTIVE_READY_READY_FOR_FINAL_REVIEW`
- ready for final review: true in test context only
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
python -m quant_replay_system.cli active-replay-input-active-ready
python -m quant_replay_system.cli active-replay-input-active-ready-index
python -m quant_replay_system.cli active-replay-input-active-ready-health
python -m quant_replay_system.cli active-replay-input-active-ready-status
python -m quant_replay_system.cli research-status
```

## Research-Status Integration

`research-status` now surfaces the latest active replay input active-ready context. It exports the active-ready run id, status, health, workflow stage, artifact path, final-review flag, non-active safety booleans, report path, and next action.

`ACTIVE_READY_READY_FOR_FINAL_REVIEW` is not active replay input and is not `ACTIVE_REPLAY_INPUT_READY`. It is a report-only final-review governance milestone. Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; active-ready fields remain visible as context.

## Safety

This checkpoint does not implement live trading, add broker integration, automate orders, send real messages, call LLM/API or external APIs, mutate cache, write `data/raw`, write `data/processed`, write `data/cache`, run current-candidates, build snapshots, create active replay input, run replay, compute forward labels, train weights, create active stock profiles, create real buy-review eligibility, apply `APPROVED_FOR_PAPER`, change signal semantics, or claim strategy performance is validated.

Validator, smoke, promotion, acceptance, and active-ready artifacts remain non-active. `REPLAY_INPUT_GATE_PASS_CANDIDATE`, `SMOKE_PASS_CANDIDATE_READY`, `PROMOTION_READY_FOR_HUMAN_REVIEW`, `ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW`, and `ACTIVE_READY_READY_FOR_FINAL_REVIEW` must not be treated as `ACTIVE_REPLAY_INPUT_READY`.

The active-ready checkpoint does not create active replay input. It does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not authorize trading.

## Test Results

Targeted validation:

```powershell
python -m pytest tests/test_active_replay_input_active_ready.py
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

After validation and review, tag `v1.33.0`. No tag is created by this checkpoint document.

## Next Branch

Recommended next branch: report-only Active Replay Input Active-Ready final review / emission design. It should still avoid real replay execution, current-candidates generation, snapshot builds, forward labels, training, active stock profiles, buy-review eligibility, broker integration, messages, API calls, and cache mutation.
