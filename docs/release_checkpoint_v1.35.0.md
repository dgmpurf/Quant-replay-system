# Release Checkpoint v1.35.0

## Scope

v1.35.0 completes `research-status` integration and checkpoint documentation for the report-only Active Replay Input Emission workflow.

## Current State

- emission command: `active-replay-input-emission`
- artifact views: `active-replay-input-emission-index`, `active-replay-input-emission-health`, `active-replay-input-emission-status`
- expected active emission run id: `96fae2783877`
- expected emission stage: `EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW`
- ready for active replay input ready review: true in report-only context
- active replay input ready: false
- active replay input: false
- active-ready emitted: false
- replay execution allowed: false
- forward labels allowed: false
- training allowed: false
- stock profile allowed: false
- buy review allowed: false
- trading allowed: false
- forward labels exist: false
- weights trained: false
- active stock profile exists: false
- real buy-review eligible: false
- approval applied: false

## Commands

```powershell
python -m quant_replay_system.cli active-replay-input-emission
python -m quant_replay_system.cli active-replay-input-emission-index
python -m quant_replay_system.cli active-replay-input-emission-health
python -m quant_replay_system.cli active-replay-input-emission-status
python -m quant_replay_system.cli research-status
```

## Research-Status Integration

`research-status` now surfaces the latest active replay input emission context. It exports the emission run id, status, health, workflow stage, artifact path, active-ready-review flag, non-active safety booleans, report path, and next action.

`EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW` is not active replay input and is not `ACTIVE_REPLAY_INPUT_READY`. It is a report-only emission governance milestone. Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; emission fields remain visible as context.

## Safety

This checkpoint does not implement live trading, add broker integration, automate orders, send real messages, call LLM/API or external APIs, mutate cache, write `data/raw`, write `data/processed`, write `data/cache`, run current-candidates, build snapshots, create active replay input, run replay, compute forward labels, train weights, create active stock profiles, create real buy-review eligibility, apply `APPROVED_FOR_PAPER`, change signal semantics, or claim strategy performance is validated.

Validator, smoke, promotion, acceptance, active-ready, final-review, and emission artifacts remain non-active. `REPLAY_INPUT_GATE_PASS_CANDIDATE`, `SMOKE_PASS_CANDIDATE_READY`, `PROMOTION_READY_FOR_HUMAN_REVIEW`, `ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW`, `ACTIVE_READY_READY_FOR_FINAL_REVIEW`, `FINAL_REVIEW_READY_FOR_EMISSION_REVIEW`, and `EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW` must not be treated as `ACTIVE_REPLAY_INPUT_READY`.

The emission checkpoint does not emit ACTIVE_REPLAY_INPUT_READY. It does not create active replay input. It does not run replay. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading.

## Test Results

Targeted validation:

```powershell
python -m pytest tests/test_active_replay_input_emission.py -q
python -m pytest tests/test_active_replay_input_final_review.py -q
python -m pytest tests/test_active_replay_input_active_ready.py -q
python -m pytest tests/test_active_replay_input_acceptance.py -q
python -m pytest tests/test_active_replay_input_promotion.py -q
python -m pytest tests/test_minimal_replay_input_package_fixture_smoke.py -q
python -m pytest tests/test_historical_replay_input_gate_validator.py -q
python -m pytest tests/test_local_research_dashboard.py -q
```

Full non-slow validation should be run before tagging:

```powershell
python -m pytest -m "not slow" -q
```

## Tag Recommendation

After validation and review, tag `v1.35.0`. No tag is created by this checkpoint document.

## Next Branch

Recommended next branch: report-only active replay input emission acceptance or promotion planning. It should still avoid real replay execution, current-candidates generation, snapshot builds, forward labels, training, active stock profiles, buy-review eligibility, broker integration, messages, API calls, and cache mutation.
