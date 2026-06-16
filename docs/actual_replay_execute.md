# Actual Replay Execute

`actual-replay-execute` creates report-only actual replay execution artifacts after an active replay input and real replay precheck have already passed their own governance checks.

This workflow is deliberately narrow. `ACTUAL_REPLAY_EXECUTED` means execution artifacts only. It is not replay_decision creation, no forward labels are computed, no training runs, no active stock_profile is created, no real buy-review eligibility is created, and no trading is authorized.

## Commands

```powershell
python -m quant_replay_system.cli actual-replay-execute
python -m quant_replay_system.cli actual-replay-execute-index
python -m quant_replay_system.cli actual-replay-execute-health
python -m quant_replay_system.cli actual-replay-execute-status
python -m quant_replay_system.cli research-status
```

The index, health, and status commands make the latest execution artifact visible to the local dashboard. `research-status` includes the actual replay execution context while preserving later `PAPER_WORKFLOW_READY` priority when paper workflow artifacts are already more advanced.

## Status Meaning

- `NO_ACTUAL_REPLAY_EXECUTION_INPUT`: no execution inputs were supplied.
- `READY_FOR_ACTUAL_REPLAY_EXECUTION`: the artifact is ready for report-only execution review but execution was not explicitly allowed.
- `ACTUAL_REPLAY_EXECUTED`: report-only execution artifacts were written after explicit local allow flags and preconditions.

`ACTUAL_REPLAY_EXECUTED` does not create replay decisions. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading, broker access, order placement, messages, API calls, cache mutation, current-candidates generation, or snapshot builds.

## Research Status Fields

Unified `research-status` exports the latest actual replay execution id, status, health status, workflow stage, artifact path, source active input creation id, source real replay precheck id, execution booleans, report path, next action, and safety fields.

The safety fields stay false for replay decisions, forward labels, training, stock profiles, buy-review eligibility, trading, orders, broker API calls, messages, LLM/API calls, external API calls, cache mutation, `data/raw`, `data/processed`, `data/cache`, current-candidates, snapshots, and signal semantics changes.

## Safety Boundary

This workflow is still report-only. It is suitable for local audit of replay execution artifacts, not for trading or strategy performance validation. Any future replay_decision, label, training, stock-profile, or buy-review workflow must be separate and explicitly governed.
