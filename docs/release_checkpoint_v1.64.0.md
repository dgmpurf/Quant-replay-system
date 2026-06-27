# Release Checkpoint v1.64.0

v1.64.0 completes Replay Evidence Bundle Schema Fixture research-status integration and checkpoint documentation.

## Included Work

- Replay Evidence Bundle Schema Fixture core context remains available through `replay-evidence-bundle-schema-fixture`.
- Replay Evidence Bundle Schema Fixture artifact views remain available through `replay-evidence-bundle-schema-fixture-index`, `replay-evidence-bundle-schema-fixture-health`, and `replay-evidence-bundle-schema-fixture-status`.
- `research-status` now exposes latest Replay Evidence Bundle Schema Fixture context while preserving existing `PAPER_WORKFLOW_READY` priority.
- `docs/replay_evidence_bundle_schema_fixture.md` documents fixture semantics and safety boundaries.
- Existing `docs/quant_research_design_pack_v0_1.md` and the Algorithm Timing Guard remain preserved.
- `SOURCE_UPDATE_NOTES_v1_64_0.md` records changed files and future ChatGPT Project Source update guidance.

## Expected Current Fixture State

- Latest workflow stage: `REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED`
- Runtime status: `PASS`
- Health status: `PASS`
- Bundle count: `10`
- Validation issue count: `0`
- Report-only: `true`
- Diagnostic-only: `true`
- Replay evidence bundle fixture rows created: `true`
- Real replay evidence bundles created: `false`
- Replay decisions created: `false`
- Forward labels created: `false`
- Future labels joined: `false`

## Safety Boundary

This checkpoint is synthetic/report-only. Replay evidence bundle rows are schema fixture rows, not real replay evidence bundles, not replay decisions, not forward labels, not future labels, and not replay-ready evidence.

It is not production factor observations, not real factor observations, not production factor registry state, not active factor library state, not production event ingestion, not active event library state, not production company exposure mapping, not real raw document ingestion, not normalization, not winsorization, not direction-adjusted runtime, not signal_score implementation, not authorized signal_score input, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, active stock_profile, promoted/production models, active thresholds, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes.

It does not authorize broker/order/message/API/trading.

## Algorithm Timing Guard

The v1.59 Algorithm Timing Guard remains active:

- signal_score formula is design reference only.
- real weights are not calibrated yet.
- thresholds are not active yet.
- ML training must wait until PIT-valid factor observations and forward labels exist.
- normalization, winsorization, and direction-adjusted values are inactive.
- factor IC / Rank IC / CAR / event study metrics are evaluation methods, not strategy performance validation by themselves.
- stock_profile is a validation dossier, not a trade instruction.
- paper workflow must precede real buy-review.
- buy-review does not equal trading.
- no broker/order/API/trading integration is allowed in current scope.

## Validation

Required validation for this checkpoint:

- `python -m pytest tests/test_replay_evidence_bundle_schema_fixture.py -q`
- `python -m pytest tests/test_replay_evidence_bundle_schema_fixture_views.py -q`
- `python -m pytest tests/test_factor_observation_schema_fixture.py -q`
- `python -m pytest tests/test_factor_observation_schema_fixture_views.py -q`
- `python -m pytest tests/test_event_structured_schema_fixture.py -q`
- `python -m pytest tests/test_event_structured_schema_fixture_views.py -q`
- `python -m pytest tests/test_company_exposure_schema_fixture.py -q`
- `python -m pytest tests/test_company_exposure_schema_fixture_views.py -q`
- `python -m pytest tests/test_factor_definition_schema_fixture.py -q`
- `python -m pytest tests/test_factor_definition_schema_fixture_views.py -q`
- `python -m pytest tests/test_raw_document_store_schema_fixture.py -q`
- `python -m pytest tests/test_raw_document_store_schema_fixture_views.py -q`
- `python -m pytest tests/test_source_registry_schema_fixture.py -q`
- `python -m pytest tests/test_source_registry_schema_fixture_views.py -q`
- `python -m pytest tests/test_operational_global_approved_for_paper.py -q`
- `python -m pytest tests/test_operational_global_approved_for_paper_views.py -q`
- `python -m pytest tests/test_local_research_dashboard.py -q`
- `python -m pytest -m "not slow" -q`

Required CLI validation:

- `replay-evidence-bundle-schema-fixture`
- `replay-evidence-bundle-schema-fixture-index`
- `replay-evidence-bundle-schema-fixture-health`
- `replay-evidence-bundle-schema-fixture-status`
- `factor-observation-schema-fixture-status`
- `event-structured-schema-fixture-status`
- `company-exposure-schema-fixture-status`
- `factor-definition-schema-fixture-status`
- `raw-document-store-schema-fixture-status`
- `source-registry-schema-fixture-status`
- `operational-global-approved-for-paper-status`
- `research-status`

## Known Limitations

- The fixture is synthetic and does not contain real replay evidence bundles.
- No replay decisions, forward labels, future labels, production factor observations, real factor observations, production factor registry, active factor library, production event ingestion, active event library, production company exposure mapping, real raw document ingestion, normalization, winsorization, direction-adjusted values, signal_score, model training input, active weight, active threshold, stock_profile validation, paper validation, real buy-review, performance validation, or trading workflow is implemented by this checkpoint.
- ChatGPT Project Source files are not created in Git, and `docs/project_sources/` remains intentionally absent.

## Recommended Next Task

Replay Evidence Bundle Schema Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
