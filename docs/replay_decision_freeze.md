# Replay Decision Freeze

`replay-decision-freeze` creates report-only replay decision freeze artifacts after actual replay execution context has passed its own governance checks.

This workflow freezes decision-time review rows only. `REPLAY_DECISION_FROZEN` does not compute forward labels, does not train weights, does not create training_result artifacts, does not create active stock_profile artifacts, does not create real buy-review eligibility, does not apply paper approval, does not validate strategy performance, and does not authorize trading.

## Commands

```powershell
python -m quant_replay_system.cli replay-decision-freeze
python -m quant_replay_system.cli replay-decision-freeze-index
python -m quant_replay_system.cli replay-decision-freeze-health
python -m quant_replay_system.cli replay-decision-freeze-status
python -m quant_replay_system.cli research-status
```

The index, health, and status commands make replay decision freeze artifacts visible to the local dashboard. `research-status` includes replay decision freeze context while preserving later `PAPER_WORKFLOW_READY` priority when paper workflow artifacts are already more advanced.

## Artifact Layout

The workflow writes artifacts under the configured report-only output directory, by default:

```text
outputs/reports/manual_diagnostics/replay_decision_freeze_v0_1/<run_id>/
```

Expected files include:

- `metadata.json`
- `replay_decision_freeze_report.md`
- `replay_decision_freeze_summary.csv`
- `replay_decision_metadata.csv`
- `replay_decision_rows.csv`, only when explicit allow freezes rows
- `replay_decision_evidence_index.csv`
- `safety_flags.json`

These artifacts are diagnostics/report artifacts. They are not forward labels, training input, stock profiles, paper approval, strategy performance validation, broker instructions, order instructions, or trading authorization.

## Status Semantics

- `NO_REPLAY_DECISION_FREEZE_INPUT`: no replay decision freeze inputs were supplied.
- `READY_FOR_REPLAY_DECISION_FREEZE`: required inputs are present, but explicit allow has not been provided; no rows are frozen.
- `REPLAY_DECISION_FROZEN`: explicit allow was provided and frozen decision-time review rows were produced.

`REPLAY_DECISION_FROZEN` means frozen decision-time review rows only. It does not compute forward labels. It does not compute future returns. It does not create forward_return_label artifacts. It does not train weights. It does not create training_result artifacts. It does not create active stock_profile artifacts. It does not create real buy-review eligibility. It does not apply paper approval. It does not validate strategy performance. It does not authorize trading, broker access, order placement, messages, API calls, cache mutation, current-candidates generation, or snapshot builds.

## Contract

Replay decision freeze artifacts separate decision-time review rows from later outcome evaluation:

- `replay_decision_metadata` records lineage, status, and freeze safety flags.
- `replay_decision_rows` records frozen review rows only after explicit allow.
- `replay_decision_evidence_index` records the evidence bundle paths and governance inputs used for the freeze.
- `safety_flags` records the non-actionable safety boundary.

Frozen decision rows must exist before any later workflow joins forward labels, because forward labels are outcome data and must remain separate from decision-time input. The freeze is the boundary that preserves decision-time state; it is not the label join itself.

## Research Status Fields

Unified `research-status` exports the latest replay decision freeze id, status, health status, workflow stage, artifact path, source actual replay execution id, source active input creation id, source real replay precheck id, actual replay status, freeze readiness and execution booleans, decision row counts, decision label set, report path, next action, and safety fields.

The safety fields stay false for forward labels, forward return labels, training, weights, training_result, stock_profile, buy-review eligibility, paper approval, strategy performance validation, trading, orders, broker API calls, messages, LLM/API calls, external API calls, cache mutation, `data/raw`, `data/processed`, `data/cache`, current-candidates, snapshots, and signal semantics changes.

## Safety Boundary

Replay decision freeze is a report-only governance checkpoint. It is useful because it freezes decision-time review rows before any future labels are introduced. It is not suitable for trading, performance claims, paper approval, or model training.

Future forward-label, training, stock-profile, buy-review, paper-approval, performance-validation, broker, order, message, or trading workflows must be separate and explicitly governed.
