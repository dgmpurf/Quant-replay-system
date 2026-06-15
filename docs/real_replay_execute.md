# Real Replay Execution Precheck v0.1

`real-replay-execute` is a report-only pre-execution review workflow for a governed active replay input artifact.

It answers whether the local evidence package is ready for a separate future human review before real replay execution. It does not run replay and it does not create replay decisions.

## Commands

```powershell
python -m quant_replay_system.cli real-replay-execute
python -m quant_replay_system.cli real-replay-execute-index
python -m quant_replay_system.cli real-replay-execute-health
python -m quant_replay_system.cli real-replay-execute-status
python -m quant_replay_system.cli research-status
```

The default artifact root is:

```text
outputs/reports/manual_diagnostics/real_replay_execute_v0_1/
```

## Status Semantics

`NO_REAL_REPLAY_EXECUTION_INPUT` means no complete pre-execution manifest package was supplied.

`READY_FOR_REAL_REPLAY_EXECUTION_REVIEW` means pre-execution review only. It does not run replay, does not create replay decisions, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not authorize trading.

Blocked statuses identify missing lineage, authority, attestation, PIT/source evidence, taxonomy evidence, leakage/side-effect evidence, or overclaim guard evidence.

## Research Status Fields

`research-status` exposes:

- latest real replay execution run id, status, health status, workflow stage, artifact path, report path, and next action;
- `ready_for_real_replay_execution_review`;
- source active input creation id and source active replay input artifact path;
- replay as-of date, replay calendar, PIT universe, source registry, raw document, factor, event, company exposure, and evidence bundle references;
- source hash coverage, revision id coverage, available-time policy, taxonomy coverage, future-label exclusion, and deterministic-only context;
- safety flags showing that replay execution, replay decisions, labels, training, stock profiles, buy-review eligibility, trading, broker/order/message/API/cache side effects, data writes, current-candidates, snapshots, and signal-semantics changes did not occur.

Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; real replay execution precheck fields remain visible as context only.

## Safety Boundaries

This workflow:

- does not run replay;
- does not create replay decisions;
- does not compute forward labels;
- does not train weights;
- does not create active stock profiles;
- does not create real buy-review eligibility;
- does not authorize trading;
- does not call broker APIs;
- does not place orders;
- does not send messages;
- does not call LLM or external APIs;
- does not mutate cache;
- does not write `data/raw`, `data/processed`, or `data/cache`;
- does not run current-candidates;
- does not build snapshots;
- does not change signal semantics.

## Recommended Next Action

Review `READY_FOR_REAL_REPLAY_EXECUTION_REVIEW` artifacts manually before any separate future replay execution implementation. Do not treat precheck readiness as performance validation or trading permission.
