# Release Checkpoint v1.34.0

## Scope

v1.34.0 completes `research-status` integration and checkpoint documentation for the report-only Active Replay Input Final-Review workflow.

## Current State

- final-review command: `active-replay-input-final-review`
- artifact views: `active-replay-input-final-review-index`, `active-replay-input-final-review-health`, `active-replay-input-final-review-status`
- expected no-package status stage: `FINAL_REVIEW_NO_PACKAGE`
- happy-path fixture stage: `FINAL_REVIEW_READY_FOR_EMISSION_REVIEW`
- ready for emission review: true in test context only
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
python -m quant_replay_system.cli active-replay-input-final-review
python -m quant_replay_system.cli active-replay-input-final-review-index
python -m quant_replay_system.cli active-replay-input-final-review-health
python -m quant_replay_system.cli active-replay-input-final-review-status
python -m quant_replay_system.cli research-status
```

## Research-Status Integration

`research-status` now surfaces the latest active replay input final-review context. It exports the final-review run id, status, health, workflow stage, artifact path, emission-review flag, non-active safety booleans, report path, and next action.

`FINAL_REVIEW_READY_FOR_EMISSION_REVIEW` is not active replay input and is not `ACTIVE_REPLAY_INPUT_READY`. It is a report-only emission-readiness governance milestone. Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; final-review fields remain visible as context.

## Safety

This checkpoint does not implement live trading, add broker integration, automate orders, send real messages, call LLM/API or external APIs, mutate cache, write `data/raw`, write `data/processed`, write `data/cache`, run current-candidates, build snapshots, create active replay input, run replay, compute forward labels, train weights, create active stock profiles, create real buy-review eligibility, apply `APPROVED_FOR_PAPER`, change signal semantics, or claim strategy performance is validated.

Validator, smoke, promotion, acceptance, active-ready, and final-review artifacts remain non-active. `REPLAY_INPUT_GATE_PASS_CANDIDATE`, `SMOKE_PASS_CANDIDATE_READY`, `PROMOTION_READY_FOR_HUMAN_REVIEW`, `ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW`, `ACTIVE_READY_READY_FOR_FINAL_REVIEW`, and `FINAL_REVIEW_READY_FOR_EMISSION_REVIEW` must not be treated as `ACTIVE_REPLAY_INPUT_READY`.

The final-review checkpoint does not create active replay input. It does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not authorize trading.

## Test Results

Targeted validation:

```powershell
python -m pytest tests/test_active_replay_input_final_review.py
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

After validation and review, tag `v1.34.0`. No tag is created by this checkpoint document.

## Next Branch

Recommended next branch: report-only Active Replay Input Final-Review emission workflow design. It should still avoid real replay execution, current-candidates generation, snapshot builds, forward labels, training, active stock profiles, buy-review eligibility, broker integration, messages, API calls, and cache mutation.
