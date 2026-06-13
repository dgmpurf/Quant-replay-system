# Active Replay Input Acceptance v0.1

`active-replay-input-acceptance` is a report-only acceptance workflow for active replay input promotion artifacts that are already ready for human review.

It can produce `ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW`, but that state is not active replay input and is not `ACTIVE_REPLAY_INPUT_READY`.

## Commands

```powershell
python -m quant_replay_system.cli active-replay-input-acceptance
python -m quant_replay_system.cli active-replay-input-acceptance-index
python -m quant_replay_system.cli active-replay-input-acceptance-health
python -m quant_replay_system.cli active-replay-input-acceptance-status
```

## Scope

The workflow checks a local promotion artifact, optional promotion health/status artifacts, an acceptance request, reviewer authority, manual attestation, second-review, and red-team review manifests. It writes report-only artifacts under:

```text
outputs/reports/manual_diagnostics/active_replay_input_acceptance_v0_1/
```

It does not create active replay input. It does not run replay. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility.

## Gate Groups

- Promotion lineage: the source promotion artifact must be `PROMOTION_READY_FOR_HUMAN_REVIEW` and must not claim active-ready state.
- Acceptance request: the request must be explicit, local, report-only, and diagnostic-only.
- Reviewer authority: primary, second, red-team, source, and strategy-owner roles must be present for review-only acceptance.
- Manual attestation: PIT validity, source permission, source hashes/revisions, leakage exclusions, side-effect exclusions, and no-trading authorization must be attested.
- Second review: a separate reviewer must confirm PIT, source, evidence, leakage, side-effect, and overclaim wording checks.
- Red-team review: a reviewer must attempt to find future leakage, permission gaps, overclaim risk, and side-effect risk.
- Leakage exclusion: active replay input, forward labels, trained weights, active stock profiles, and real buy-review eligibility must remain false.
- Side-effect safety: approvals, orders, API calls, current-candidates runs, snapshot builds, cache mutation, and signal-semantics changes must remain false.

## Status Semantics

- `NO_ACCEPTANCE_INPUT`: no promotion or reviewer input was supplied.
- `ACCEPTANCE_*_BLOCKED`: one or more lineage, review, authority, attestation, second-review, red-team, PIT, source, evidence, leakage, or side-effect gates failed.
- `ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW`: all local report-only acceptance gates passed and the artifact is ready for a future active-ready governance review.

`ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW` is deliberately below `ACTIVE_REPLAY_INPUT_READY`. Active-ready remains future-only because this workflow does not create active replay input, does not run replay, and does not grant trading actionability.

## Research Status

`research-status` surfaces the latest active replay input acceptance context with:

- latest acceptance run id
- status, health, and workflow stage
- acceptance artifact path
- ready-for-active-ready-review flag
- active-ready and active-input flags, which must remain false
- forward-label, training, stock-profile, and buy-review safety flags
- approval, order, API, cache, current-candidates, snapshot, and signal-semantics safety flags
- report-only and trading safety flags
- report path and next action

`ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW` remains review context only. Later paper workflow artifacts preserve `PAPER_WORKFLOW_READY`; acceptance fields stay visible as context.

## Authority and Review Boundary

Acceptance requires explicit local reviewer manifests. Those manifests are governance context, not execution permission. They do not promote a replay input package into active use, do not authorize replay execution, and do not authorize trading or advisory buy-review behavior.

Second review and red-team review are designed to catch overclaim, leakage, source-permission, and side-effect risks. Passing them only makes the acceptance artifact reviewable for a future active-ready governance workflow.

## Safety

The acceptance workflow does not run current-candidates, build snapshots, compute forward labels, write `data/raw`, write `data/processed`, write `data/cache`, call LLM/API or external APIs, mutate cache, send messages, connect to brokers, place orders, apply `APPROVED_FOR_PAPER`, change signal semantics, or claim strategy performance is validated.

The health view fails if an acceptance artifact emits `ACTIVE_REPLAY_INPUT_READY`, sets active replay input flags true, creates unsafe side effects, or weakens report-only safety flags.

## What Remains Blocked

An acceptance artifact does not make replay active. A future, separate active-ready governance workflow would still need explicit active-ready rules, strict leakage checks, active input promotion boundaries, and a clear distinction from buy-review or trading permission.
