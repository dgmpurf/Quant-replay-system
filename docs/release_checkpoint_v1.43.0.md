# Release Checkpoint v1.43.0

## Scope

v1.43.0 integrates report-only Replay Decision Freeze context into unified `research-status`.

Implemented context:

- `replay-decision-freeze`
- `replay-decision-freeze-index`
- `replay-decision-freeze-health`
- `replay-decision-freeze-status`
- `research-status` fields for the latest replay decision freeze artifact
- `docs/replay_decision_freeze.md`
- `SOURCE_UPDATE_NOTES_v1_43_0.md`

## Current Semantics

`REPLAY_DECISION_FROZEN` means report-only frozen decision-time review rows only.

It may exist in diagnostics after explicit allow. It does not compute forward labels. It does not compute future returns. It does not create forward_return_label artifacts. It does not train weights. It does not create training_result artifacts. It does not create active stock_profile artifacts. It does not create real buy-review eligibility. It does not apply paper approval. It does not validate strategy performance. It does not authorize trading.

The unified dashboard exposes replay decision freeze lineage, freeze booleans, decision row counts, report path, next action, and safety fields while preserving later `PAPER_WORKFLOW_READY` priority.

Known status paths:

- no input: `NO_REPLAY_DECISION_FREEZE_INPUT`
- no-allow ready path: `READY_FOR_REPLAY_DECISION_FREEZE`
- explicit-allow report-only path: `REPLAY_DECISION_FROZEN`

Known latest view validation before checkpoint:

- `replay-decision-freeze` can create a no-input artifact.
- `replay-decision-freeze-index` discovers freeze artifacts.
- `replay-decision-freeze-health` reports PASS for valid artifacts.
- `replay-decision-freeze-status` summarizes the latest artifact.

## Safety State

- no forward labels;
- no forward_return_label artifacts;
- no future returns computed;
- no training;
- no weights;
- no training_result;
- no active stock_profile;
- no real buy-review eligibility;
- no paper approval;
- no strategy performance validation claim;
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
- no signal semantics change.

## Validation

Run before tagging:

```powershell
python -m pytest tests/test_replay_decision_freeze.py -q
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

Run a final local validation sweep, then update ChatGPT Project Source manually after tag v1.43.0. Do not add `docs/project_sources/` to Git.

Recommended next task: Forward Return Label Planning Report-Only v0.1, unless code/docs clearly suggest a safer preceding audit.
