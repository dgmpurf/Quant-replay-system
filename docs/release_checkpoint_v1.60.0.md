# Release Checkpoint v1.60.0

v1.60.0 completes Factor Definition Schema Fixture research-status integration and checkpoint documentation.

## Included Work

- Factor Definition Schema Fixture core context remains available through `factor-definition-schema-fixture`.
- Factor Definition Schema Fixture artifact views remain available through `factor-definition-schema-fixture-index`, `factor-definition-schema-fixture-health`, and `factor-definition-schema-fixture-status`.
- `research-status` now exposes latest Factor Definition Schema Fixture context while preserving existing `PAPER_WORKFLOW_READY` priority.
- `docs/factor_definition_schema_fixture.md` documents fixture semantics and safety boundaries.
- Existing `docs/quant_research_design_pack_v0_1.md` and the Algorithm Timing Guard remain preserved.
- `SOURCE_UPDATE_NOTES_v1_60_0.md` records changed files and future ChatGPT Project Source update guidance.

## Expected Current Fixture State

- Latest status: `FACTOR_DEFINITION_SCHEMA_FIXTURE_CREATED`
- Health status: `PASS`
- Factor count: `8`
- Taxonomy layer count: `8`
- Validation issue count: `0`
- Report-only: `true`
- Diagnostic-only: `true`
- Taxonomy primary classification: `true`
- Legacy 12-factor tags checklist only: `true`

## Safety Boundary

This checkpoint is synthetic/report-only. Factor definitions are observation-rule registry rows, not factor observations, not live signals, and not an active factor library.

It does not create factor observations, real factor observations, event ingestion, company exposure mappings, replay evidence bundles, signal_score implementation, live signals, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review eligibility, buy_review_allowed, strategy performance validation, or trading permission.

It does not authorize current-candidates, snapshots, signal_semantics mutation, active stock_profile, promoted/production models, active thresholds, advisory predictions, active probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes.

## Algorithm Timing Guard

The v1.59 Algorithm Timing Guard remains active:

- signal_score formula is design reference only.
- real weights are not calibrated.
- thresholds are not active.
- ML training must wait for PIT-valid observations and labels.
- factor IC / Rank IC / CAR / event study metrics are evaluation methods, not strategy performance validation by themselves.
- stock_profile is a validation dossier, not a trade instruction.
- paper workflow must precede real buy-review.
- buy-review does not equal trading.
- broker/order/API/trading integration remains forbidden.

## Validation

Required validation for this checkpoint:

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

- `factor-definition-schema-fixture`
- `factor-definition-schema-fixture-index`
- `factor-definition-schema-fixture-health`
- `factor-definition-schema-fixture-status`
- `raw-document-store-schema-fixture-status`
- `source-registry-schema-fixture-status`
- `operational-global-approved-for-paper-status`
- `research-status`

## Known Limitations

- The fixture is synthetic and does not contain production factor definitions.
- No production factor registry is created.
- No real factor observations, event ingestion, company exposure mapping, replay evidence bundle, signal_score, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review, performance validation, or trading workflow is implemented by this checkpoint.
- ChatGPT Project Source files are not created in Git, and `docs/project_sources/` remains intentionally absent.

## Recommended Next Task

Factor Definition Schema Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
