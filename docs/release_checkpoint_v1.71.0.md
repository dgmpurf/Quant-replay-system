# Release Checkpoint v1.71.0

v1.71.0 completes Tiny PIT Real Reviewed Package Candidate Contract Fixture research-status integration and checkpoint documentation.

## Included Work

- Tiny PIT Real Reviewed Package Candidate Contract Fixture core remains available through `tiny-pit-real-reviewed-package-candidate-contract-fixture`.
- Artifact views remain available through `tiny-pit-real-reviewed-package-candidate-contract-fixture-index`, `tiny-pit-real-reviewed-package-candidate-contract-fixture-health`, and `tiny-pit-real-reviewed-package-candidate-contract-fixture-status`.
- `research-status` exposes the latest real reviewed package candidate contract fixture context while preserving `PAPER_WORKFLOW_READY` priority.
- `docs/tiny_pit_real_reviewed_package_candidate_contract_fixture.md` documents fixture semantics and safety boundaries.
- `docs/quant_research_design_pack_v0_1.md` preserves the Algorithm Timing Guard and records Tiny PIT real reviewed package candidate contract fixture as report-only governance.
- `SOURCE_UPDATE_NOTES_v1_71_0.md` records changed files and future ChatGPT Project Source update guidance.

## Lineage

- Previous checkpoint tag: `v1.70.0` at commit `b078bfb`.
- Current implementation base: `bbb3388`.
- v1.71.0 is intended to be created after ChatGPT review and manual commit/tag of this research-status/checkpoint package.

## Expected Current Fixture State

- Latest fixture id: `37a5cf3ed744`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_PACKAGE_CANDIDATE_CONTRACT_FIXTURE_CREATED_REPORT_ONLY`
- Runtime status: `REAL_REVIEWED_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY`
- Health status: `PASS`
- Case count: `63`
- Pass-candidate count: `5`
- Warn count: `10`
- Fail count: `48`
- Blocker count: `63`
- Warning count: `11`
- Report-only: `true`
- Diagnostic-only: `true`
- Synthetic-only: `true`
- Active replay input: `false`
- Active replay ready: `false`
- Trading allowed: `false`

## Safety Boundary

This checkpoint is synthetic/report-only. The Tiny PIT Real Reviewed Package Candidate Contract Fixture does not create real reviewed CSV packages, active reviewed input candidates, real replay input, active replay input, `ACTIVE_REPLAY_INPUT_READY`, replay execution, replay evidence bundles, replay decisions, replay decision freezes, forward labels, future-label joins, training datasets, metric computation, signal_score implementation, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review eligibility, buy_review_allowed, or strategy performance validation.

It does not authorize current-candidates, snapshots, signal_semantics mutation, active stock_profile, promoted/production models, active thresholds, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes. No trading is authorized.

## Research-Status Boundary

`research-status` exposes the Tiny PIT Real Reviewed Package Candidate Contract Fixture as context only. It must not override later paper workflow priority and must not emit or imply `ACTIVE_REPLAY_INPUT_READY`.

The final research-status workflow stage must remain `PAPER_WORKFLOW_READY` when later paper workflow context exists.

## Algorithm Timing Guard

The v1.59 Algorithm Timing Guard remains active:

- signal_score formula is design reference only.
- real weights are not calibrated yet.
- thresholds are not active yet.
- ML training must wait until PIT-valid factor observations and real governed forward labels exist.
- normalization, winsorization, and direction-adjusted values are inactive.
- factor IC / Rank IC / CAR / event study metrics are evaluation methods, not strategy performance validation by themselves.
- stock_profile is a validation dossier, not a trade instruction.
- paper workflow must precede real buy-review.
- buy-review does not equal trading.
- no broker/order/API/trading integration is allowed in current scope.

## Validation

Required validation for this checkpoint:

- `python -m pytest tests/test_tiny_pit_real_reviewed_package_candidate_contract_fixture.py -q`
- `python -m pytest tests/test_tiny_pit_real_reviewed_package_candidate_contract_fixture_views.py -q`
- `python -m pytest tests/test_local_research_dashboard.py -q`
- `python -m pytest -m "not slow" -q`

Required CLI validation:

- `tiny-pit-real-reviewed-package-candidate-contract-fixture`
- `tiny-pit-real-reviewed-package-candidate-contract-fixture-index`
- `tiny-pit-real-reviewed-package-candidate-contract-fixture-health`
- `tiny-pit-real-reviewed-package-candidate-contract-fixture-status`
- `research-status`

Observed validation evidence:

- `tests/test_tiny_pit_real_reviewed_package_candidate_contract_fixture.py`: 32 passed.
- `tests/test_tiny_pit_real_reviewed_package_candidate_contract_fixture_views.py`: 11 passed.
- `tests/test_local_research_dashboard.py`: 315 passed.
- Full non-slow suite: 5327 passed, 109 deselected, 5 warnings.

Observed CLI evidence:

- `tiny-pit-real-reviewed-package-candidate-contract-fixture`: `REAL_REVIEWED_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY`, `PASS` health, 63 cases, 5 pass candidates, 10 warn, 48 fail, 63 blockers, 11 warnings.
- `tiny-pit-real-reviewed-package-candidate-contract-fixture-index`: 1 artifact discovered, latest fixture id `37a5cf3ed744`.
- `tiny-pit-real-reviewed-package-candidate-contract-fixture-health`: `PASS`, 0 issues.
- `tiny-pit-real-reviewed-package-candidate-contract-fixture-status`: `PASS`, `PASS` health, post-checkpoint governance audit next action.
- `research-status`: Tiny PIT real reviewed package candidate contract fixture context visible while final workflow stage remains `PAPER_WORKFLOW_READY`.

## Known Limitations

- The fixture is synthetic and does not contain real reviewed CSV packages.
- No real PIT admissibility package, active reviewed input candidate, real replay input, active replay input, replay evidence bundle, replay decision, replay decision freeze, forward label, future-label join, training dataset, metric computation, signal_score input, model training, active weight, active threshold, stock_profile validation, paper validation, real buy-review, performance validation, or trading workflow is implemented by this checkpoint.
- ChatGPT Project Source files are not created in Git, and `docs/project_sources/` remains intentionally absent.

## Recommended Next Task

Tiny PIT Real Reviewed Package Candidate Contract Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
