# Active Replay Input Promotion v0.1

`active-replay-input-promotion` is a report-only promotion-readiness workflow for replay input packages that already passed the report-only input gate validator and minimal replay input package fixture smoke.

It can produce `PROMOTION_READY_FOR_HUMAN_REVIEW`, but that state is not active replay input and is not `ACTIVE_REPLAY_INPUT_READY`.

## Commands

```powershell
python -m quant_replay_system.cli active-replay-input-promotion
python -m quant_replay_system.cli active-replay-input-promotion-index
python -m quant_replay_system.cli active-replay-input-promotion-health
python -m quant_replay_system.cli active-replay-input-promotion-status
```

## Scope

The workflow checks local report-only validator, smoke, promotion request, and human review manifests. It preserves lineage and writes promotion readiness artifacts under:

```text
outputs/reports/manual_diagnostics/active_replay_input_promotion_v0_1/
```

It does not create active replay input. It does not run replay. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility.

## Gate Groups

The promotion core is fail-closed around these gate groups:

- Validator and smoke lineage: the validator must be a report-only pass-candidate and the smoke artifact must link to the same validator.
- Promotion request: the request must identify reviewer intent, validator reference, smoke reference, input-package reference, and `PROMOTION_READY_FOR_HUMAN_REVIEW` as the requested status.
- Human review: required review gates must be explicitly acknowledged before readiness can be shown.
- PIT, source, and evidence coverage: review context must exist, but the workflow does not itself approve PIT universe rows.
- Leakage exclusion: active replay input, forward labels, trained weights, active stock profiles, and real buy-review eligibility must remain false.
- Side-effect safety: approvals, orders, API calls, current-candidates runs, snapshot builds, cache mutation, and signal-semantics changes must remain false.

## Status Semantics

- `NO_PROMOTION_INPUT`: no validator/smoke/review input was supplied.
- `PROMOTION_*_BLOCKED`: one or more lineage, review, PIT, source, evidence, leakage, or side-effect gates failed.
- `PROMOTION_READY_FOR_HUMAN_REVIEW`: all local report-only promotion gates passed and the artifact is ready for manual review as planning context.

`PROMOTION_READY_FOR_HUMAN_REVIEW` is deliberately one step below any future active-ready state. Active-ready remains future-only because this workflow does not create accepted active replay inputs, does not run replay, and does not grant trading actionability.

## Research Status

`research-status` surfaces the latest active replay input promotion context with:

- latest promotion run id
- status, health, and workflow stage
- ready-for-human-review flag
- active-ready and active-input flags, which must remain false
- forward-label, training, stock-profile, and buy-review safety flags
- report-only and trading safety flags
- report path and next action

`PROMOTION_READY_FOR_HUMAN_REVIEW` remains review context only. Later paper workflow artifacts preserve `PAPER_WORKFLOW_READY`; promotion fields stay visible as context.

## Safety

The promotion workflow does not run current-candidates, build snapshots, compute forward labels, write `data/raw`, write `data/processed`, write `data/cache`, call LLM/API or external APIs, mutate cache, send messages, connect to brokers, place orders, apply `APPROVED_FOR_PAPER`, change signal semantics, or claim strategy performance is validated.

The health view fails if a promotion artifact emits `ACTIVE_REPLAY_INPUT_READY`, sets active replay input flags true, creates unsafe side effects, or weakens report-only safety flags.

## What Remains Blocked

A promotion artifact does not make replay active. A future, separate active-ready design would still need explicit accepted replay input governance, final active-ready promotion rules, strict leakage checks, and a clear distinction from buy-review or trading permission.
