# Release Checkpoint v1.61.0

v1.61.0 completes Company Exposure Schema Fixture research-status integration and checkpoint documentation.

## Included Work

- Company Exposure Schema Fixture core context remains available through `company-exposure-schema-fixture`.
- Company Exposure Schema Fixture artifact views remain available through `company-exposure-schema-fixture-index`, `company-exposure-schema-fixture-health`, and `company-exposure-schema-fixture-status`.
- `company-exposure-schema-fixture-status` now points to post-checkpoint governance review instead of saying research-status/checkpoint integration still needs to be added.
- `research-status` now exposes latest Company Exposure Schema Fixture context while preserving existing `PAPER_WORKFLOW_READY` priority.
- `docs/company_exposure_schema_fixture.md` documents fixture semantics and safety boundaries.
- Existing `docs/quant_research_design_pack_v0_1.md` and the Algorithm Timing Guard remain preserved.
- `SOURCE_UPDATE_NOTES_v1_61_0.md` records changed files and future ChatGPT Project Source update guidance.

## Expected Current Fixture State

- Latest status: `COMPANY_EXPOSURE_SCHEMA_FIXTURE_CREATED`
- Runtime status: `PASS`
- Health status: `PASS`
- Exposure count: `10`
- Validation issue count: `0`
- Report-only: `true`
- Diagnostic-only: `true`
- Production company exposure mapping created: `false`
- Active company exposure mapping created: `false`

## Safety Boundary

This checkpoint is synthetic/report-only. Company exposure rows are schema fixture rows, not production exposure mappings, not active mappings, not company knowledge graph state, not factor observations, not event ingestion, and not replay-ready evidence.

It does not create production company exposure mappings, active company exposure mappings, company knowledge graphs, real ETF holdings ingestion, supplier/customer production graphs, factor observations, event ingestion, replay evidence bundles, signal_score implementation, model training inputs, active weights, active thresholds, stock_profile validation, paper validation, real buy-review eligibility, buy_review_allowed, strategy performance validation, or trading permission.

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

- `company-exposure-schema-fixture`
- `company-exposure-schema-fixture-index`
- `company-exposure-schema-fixture-health`
- `company-exposure-schema-fixture-status`
- `factor-definition-schema-fixture-status`
- `raw-document-store-schema-fixture-status`
- `source-registry-schema-fixture-status`
- `operational-global-approved-for-paper-status`
- `research-status`

## Known Limitations

- The fixture is synthetic and does not contain production company exposure mappings.
- No active company exposure mapping or company knowledge graph is created.
- No real ETF holdings ingestion, supplier/customer graph, factor observation, event ingestion, replay evidence bundle, signal_score, model training input, active weight, active threshold, stock_profile validation, paper validation, real buy-review, performance validation, or trading workflow is implemented by this checkpoint.
- ChatGPT Project Source files are not created in Git, and `docs/project_sources/` remains intentionally absent.

## Recommended Next Task

Company Exposure Schema Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
