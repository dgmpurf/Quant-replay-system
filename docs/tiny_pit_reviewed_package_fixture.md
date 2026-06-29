# Tiny PIT Reviewed Package Fixture

The Tiny PIT Reviewed Package Fixture is a synthetic, report-only fixture for future reviewed LOCAL_CSV package admissibility governance.

It is not a real reviewed CSV package. It does not create active reviewed input candidates, real replay input, active replay input, `ACTIVE_REPLAY_INPUT_READY`, replay execution, replay decisions, replay evidence bundles, replay decision freezes, forward labels, future-label joins, training datasets, metric computation, signal_score inputs, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review eligibility, buy_review_allowed, strategy performance validation, current-candidates, snapshots, signal_semantics mutation, broker/API/order/message behavior, or trading. It does not write `data/raw`, `data/processed`, or `data/cache`.

## Purpose

The fixture exercises the future package shape around package manifests, reviewed source/file manifests, section manifests, evidence lineage, timing, reviewer attestation, quality review, forbidden downstream flags, and package limitations.

Expected deterministic fixture state:

- 15 cases.
- 9 PASS-health cases.
- 2 WARN-health cases.
- 4 FAIL-health cases.
- 13 blockers.
- 2 warnings.
- report-only, diagnostic-only, and synthetic-only flags true.
- all downstream activation and trading flags false.

## CLI Flow

Use these report-only commands:

- `tiny-pit-reviewed-package-fixture`
- `tiny-pit-reviewed-package-fixture-index`
- `tiny-pit-reviewed-package-fixture-health`
- `tiny-pit-reviewed-package-fixture-status`
- `research-status`

Expected status context:

- Runtime status: `TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY`
- Workflow stage: `TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY`
- Health status: `PASS`
- Next action: `Tiny PIT Reviewed Package Fixture Post-Checkpoint Governance Audit Report-Only v0.1`

## Research-Status Fields

`research-status` exposes the latest fixture id, status, health, workflow stage, artifact path, report path, case counts, pass/warn/fail counts, blocker/warning counts, report-only flags, diagnostic-only flags, synthetic-only flags, recommended next task, and safety flags.

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

Tiny PIT Reviewed Package Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
