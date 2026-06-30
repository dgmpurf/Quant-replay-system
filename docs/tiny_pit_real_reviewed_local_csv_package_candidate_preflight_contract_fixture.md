# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Contract Fixture

The Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Contract Fixture is a synthetic, report-only fixture for future reviewed LOCAL_CSV package-candidate preflight governance.

It is not a real reviewed CSV package. It does not read real CSV files, discover real package directories, create real package candidates, create active reviewed input candidates, create real replay input, create active replay input, emit `ACTIVE_REPLAY_INPUT_READY`, run replay, create replay decisions, freeze replay decisions, create forward labels, join future labels to decision-time inputs, create training datasets, compute metrics, implement signal_score, train models, create active weights, create active thresholds, validate stock_profile, validate paper workflow, create real buy-review eligibility, set buy_review_allowed, validate strategy performance, create current-candidates, build snapshots, mutate signal_semantics, call broker/API/order/message/trading systems, or write `data/raw`, `data/processed`, or `data/cache`.

## Purpose

The fixture records the expected contract for a future real reviewed LOCAL_CSV package candidate preflight. It exercises package manifest requirements, section contracts, field-family contracts, available_time semantics, source hash and revision semantics, reviewer authority, quality and limitation handling, safe status vocabulary, forbidden downstream flags, and report-only limitations.

Expected deterministic fixture state:

- 56 cases.
- 1 pass-candidate case.
- 3 warning cases.
- 49 failure cases.
- 69 blockers.
- 3 warnings.
- report-only, diagnostic-only, and synthetic-only flags true.
- real_csv_required and real_csv_consumed false.
- all downstream activation, replay, model, paper, buy-review, trading, and protected data-write flags false.

## CLI Flow

Use these report-only commands:

- `tiny-pit-real-reviewed-local-csv-package-candidate-preflight-contract-fixture`
- `tiny-pit-real-reviewed-local-csv-package-candidate-preflight-contract-fixture-index`
- `tiny-pit-real-reviewed-local-csv-package-candidate-preflight-contract-fixture-health`
- `tiny-pit-real-reviewed-local-csv-package-candidate-preflight-contract-fixture-status`
- `research-status`

Expected status context:

- Runtime status: `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_CONTRACT_FIXTURE_CREATED_REPORT_ONLY`
- Health status: `PASS`
- Next action: `Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Contract Fixture Post-Checkpoint Governance Audit Report-Only v0.1`

## Artifact Root

Default artifact root:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_v0_1/
```

The fixture remains under manual diagnostics and must not create `docs/project_sources/`, real CSV packages, active replay inputs, current-candidates, snapshots, or protected data writes.

## Safe Status Vocabulary

The safe status vocabulary is report-only and diagnostic-only. `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY` means the preflight contract surface exists as synthetic governance context only.

Forbidden interpretations include package approval, PIT admissibility, replay readiness, active replay input readiness, buy-review readiness, trading readiness, paper approval, strategy performance validation, and any broker/API/order/message actionability.

## Artifact Views

The index view discovers completed synthetic fixture runs and ignores view folders. The health view verifies required artifacts, required metadata, safe status vocabulary, report-only flags, and forbidden downstream flags. The status view selects the latest valid artifact and reports bounded counts, health, paths, safety flags, and the post-checkpoint governance audit next action.

## Research-Status Context

`research-status` exposes the latest fixture id, status, health, workflow stage, artifact path, report path, case counts, pass-candidate/warn/fail counts, blocker/warning counts, report-only flags, diagnostic-only flags, synthetic-only flags, recommended next task, and safety flags.

The fixture is context only. It must not override later workflow priority; `PAPER_WORKFLOW_READY` remains the final workflow stage when paper workflow context exists.

## Safety Boundary

All activation and downstream flags remain false:

- no real CSV required or consumed;
- no real reviewed CSV package;
- no real package candidate;
- no active reviewed input candidate;
- no real or active replay input;
- no `ACTIVE_REPLAY_INPUT_READY`;
- no replay execution or replay decisions;
- no forward labels or future-label joins;
- no training dataset, metric computation, signal_score, model training, active weights, or active thresholds;
- no stock_profile validation, paper validation, real buy-review eligibility, buy_review_allowed, or strategy performance validation;
- no current-candidates, snapshots, signal_semantics mutation, broker/API/order/message/trading, or data/raw, data/processed, data/cache writes.

## Recommended Next Task

Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Contract Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
