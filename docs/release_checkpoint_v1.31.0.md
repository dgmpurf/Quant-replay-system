# Release Checkpoint v1.31.0

## Scope

v1.31.0 completes `research-status` integration and checkpoint documentation for the report-only active replay input promotion workflow.

## Current State

- promotion command: `active-replay-input-promotion`
- artifact views: `active-replay-input-promotion-index`, `active-replay-input-promotion-health`, `active-replay-input-promotion-status`
- expected reviewable stage: `PROMOTION_READY_FOR_HUMAN_REVIEW`
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
python -m quant_replay_system.cli active-replay-input-promotion
python -m quant_replay_system.cli active-replay-input-promotion-index
python -m quant_replay_system.cli active-replay-input-promotion-health
python -m quant_replay_system.cli active-replay-input-promotion-status
python -m quant_replay_system.cli research-status
```

## Research-Status Integration

`research-status` now surfaces the latest active replay input promotion context. It exports the promotion run id, status, health, workflow stage, promotion artifact path, ready-for-human-review flag, active-ready flags, report-only safety booleans, report path, and next action.

`PROMOTION_READY_FOR_HUMAN_REVIEW` is not active replay input and is not `ACTIVE_REPLAY_INPUT_READY`. It is a reviewable planning milestone only. Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; promotion fields remain visible as context.

## Safety

This checkpoint does not implement live trading, add broker integration, automate orders, send real messages, call LLM/API or external APIs, mutate cache, write `data/raw`, write `data/processed`, write `data/cache`, run current-candidates, build snapshots, compute forward labels, train weights, create active stock profiles, create real buy-review eligibility, apply `APPROVED_FOR_PAPER`, change signal semantics, or claim strategy performance is validated.

Validator, smoke, and promotion artifacts remain non-active. `REPLAY_INPUT_GATE_PASS_CANDIDATE`, `SMOKE_PASS_CANDIDATE_READY`, and `PROMOTION_READY_FOR_HUMAN_REVIEW` must not be treated as `ACTIVE_REPLAY_INPUT_READY`.

## Test Results

Targeted validation:

```powershell
python -m pytest tests/test_active_replay_input_promotion.py
python -m pytest tests/test_minimal_replay_input_package_fixture_smoke.py
python -m pytest tests/test_historical_replay_input_gate_validator.py
python -m pytest tests/test_local_research_dashboard.py
```

Full non-slow validation should be run before tagging:

```powershell
python -m pytest -m "not slow"
```

## Tag Recommendation

After validation and review, tag `v1.31.0`. No tag is created by this checkpoint document.

## Next Branch

Recommended next branch: design a report-only active replay input promotion acceptance audit that explains what explicit human governance would be required before any future workflow could promote review context into active replay input. It should still avoid replay execution, current-candidates generation, snapshot builds, forward labels, training, active stock profiles, buy-review eligibility, broker integration, messages, API calls, and cache mutation.
