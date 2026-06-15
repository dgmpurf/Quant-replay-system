# Release Checkpoint v1.41.0

## Scope

v1.41.0 integrates report-only real replay execution precheck context into unified `research-status`.

Implemented context:

- `real-replay-execute`
- `real-replay-execute-index`
- `real-replay-execute-health`
- `real-replay-execute-status`
- `research-status` fields for the latest real replay execution precheck artifact
- `docs/real_replay_execute.md`
- `SOURCE_UPDATE_NOTES_v1_41_0.md`

## Current Semantics

`READY_FOR_REAL_REPLAY_EXECUTION_REVIEW` means pre-execution review only.

It does not run replay. It does not create replay decisions. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading.

The unified dashboard exposes active replay input lineage, replay as-of metadata, source/evidence references, coverage fields, and safety flags while preserving later `PAPER_WORKFLOW_READY` priority.

## Safety State

- no real replay execution;
- no replay decisions;
- no forward labels;
- no training;
- no weights;
- no active stock profiles;
- no real buy-review eligibility;
- no paper approval;
- no live trading;
- no broker API;
- no order placement;
- no messages;
- no LLM/API calls;
- no external API calls;
- no cache mutation;
- no `data/raw` write;
- no `data/processed` write;
- no `data/cache` write;
- no current-candidates generation;
- no snapshot build;
- no signal semantics change.

## Validation

Run before tagging:

```powershell
python -m pytest tests/test_real_replay_execute.py -q
python -m pytest tests/test_active_replay_input_create.py -q
python -m pytest tests/test_active_replay_input_ready_actual_emission.py -q
python -m pytest tests/test_active_replay_input_ready_emission.py -q
python -m pytest tests/test_historical_replay_input_gate_validator.py -q
python -m pytest tests/test_local_research_dashboard.py -q
python -m pytest -m "not slow" -q
python -m pytest -q
```

## Recommended Next Task

Run a final local validation sweep, then update ChatGPT Project Source manually after commit/tag. Do not add `docs/project_sources/` to Git.
