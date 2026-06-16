# Release Checkpoint v1.42.0

## Scope

v1.42.0 integrates report-only actual replay execution context into unified `research-status`.

Implemented context:

- `actual-replay-execute`
- `actual-replay-execute-index`
- `actual-replay-execute-health`
- `actual-replay-execute-status`
- `research-status` fields for the latest actual replay execution artifact
- `docs/actual_replay_execute.md`
- `SOURCE_UPDATE_NOTES_v1_42_0.md`

## Current Semantics

`ACTUAL_REPLAY_EXECUTED` means report-only execution artifacts only.

It is not replay_decision creation. It does not create replay decisions. It does not compute forward labels. It does not train weights. It does not create active stock_profile artifacts. It does not create real buy-review eligibility. It does not authorize trading.

The unified dashboard exposes actual replay execution lineage, execution booleans, report path, next action, and safety fields while preserving later `PAPER_WORKFLOW_READY` priority.

## Safety State

- no replay_decision creation;
- no replay decisions;
- no forward labels;
- no training;
- no weights;
- no active stock_profile;
- no real buy-review eligibility;
- no paper approval;
- no trading;
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
- no signal semantics change;
- no strategy performance validation claim.

## Validation

Run before tagging:

```powershell
python -m pytest tests/test_actual_replay_execute.py -q
python -m pytest tests/test_real_replay_execute.py -q
python -m pytest tests/test_active_replay_input_create.py -q
python -m pytest tests/test_historical_replay_input_gate_validator.py -q
python -m pytest tests/test_local_research_dashboard.py -q
python -m pytest tests/test_paper_workflow_status.py -q
python -m pytest -m "not slow" -q
python -m pytest -q
```

## Recommended Next Task

Run a final local validation sweep, then update ChatGPT Project Source manually after tag v1.42.0. Do not add `docs/project_sources/` to Git.

Recommended next task: Replay Decision Freeze Planning Report-Only v0.1.
