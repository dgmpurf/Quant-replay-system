# Tiny PIT Real Reviewed Package Candidate Contract Fixture

The Tiny PIT Real Reviewed Package Candidate Contract Fixture is a synthetic, report-only fixture for future reviewed LOCAL_CSV package-candidate governance.

It is not a real reviewed CSV package. It does not create active reviewed input candidates, real replay input, active replay input, `ACTIVE_REPLAY_INPUT_READY`, replay execution, replay decisions, replay evidence bundles, replay decision freezes, forward labels, future-label joins, training datasets, metric computation, signal_score inputs, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review eligibility, buy_review_allowed, strategy performance validation, current-candidates, snapshots, signal_semantics mutation, broker/API/order/message behavior, or trading. It does not write `data/raw`, `data/processed`, or `data/cache`.

## Purpose

The fixture exercises the future candidate-package contract around package sections, field families, available_time, source hash and revision semantics, reviewer authority, quality and limitation handling, status vocabulary, forbidden downstream flags, and report-only limitations.

Expected deterministic fixture state:

- 63 cases.
- 5 pass-candidate cases.
- 10 warning cases.
- 48 failure cases.
- 63 blockers.
- 11 warnings.
- report-only, diagnostic-only, and synthetic-only flags true.
- all downstream activation and trading flags false.

## CLI Flow

Use these report-only commands:

- `tiny-pit-real-reviewed-package-candidate-contract-fixture`
- `tiny-pit-real-reviewed-package-candidate-contract-fixture-index`
- `tiny-pit-real-reviewed-package-candidate-contract-fixture-health`
- `tiny-pit-real-reviewed-package-candidate-contract-fixture-status`
- `research-status`

Expected status context:

- Runtime status: `REAL_REVIEWED_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_PACKAGE_CANDIDATE_CONTRACT_FIXTURE_CREATED_REPORT_ONLY`
- Health status: `PASS`
- Next action: `Tiny PIT Real Reviewed Package Candidate Contract Fixture Post-Checkpoint Governance Audit Report-Only v0.1`

## Research-Status Fields

`research-status` exposes the latest fixture id, status, health, workflow stage, artifact path, report path, case counts, pass-candidate/warn/fail counts, blocker/warning counts, report-only flags, diagnostic-only flags, synthetic-only flags, recommended next task, and safety flags.

The fixture is context only. It must not override later workflow priority; `PAPER_WORKFLOW_READY` remains the final workflow stage when paper workflow context exists.

## Safety Boundary

All activation and downstream flags remain false:

- no real reviewed CSV package;
- no active reviewed input candidate;
- no real or active replay input;
- no `ACTIVE_REPLAY_INPUT_READY`;
- no replay execution or replay decisions;
- no forward labels or future-label joins;
- no training dataset, metric computation, signal_score, model training, active weights, or active thresholds;
- no stock_profile validation, paper validation, real buy-review eligibility, buy_review_allowed, or strategy performance validation;
- no current-candidates, snapshots, signal_semantics mutation, broker/API/order/message/trading, or data/raw, data/processed, data/cache writes.

## Recommended Next Task

Tiny PIT Real Reviewed Package Candidate Contract Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
