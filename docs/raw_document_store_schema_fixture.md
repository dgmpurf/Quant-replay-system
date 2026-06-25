# Raw Document Store Schema Fixture

The Raw Document Store Schema Fixture is a synthetic/report-only schema-governance workflow. It creates tiny raw document and dataset-reference fixture artifacts only, so future source and document-store work can review expected identifiers, timing fields, hashes, revision fields, and safety flags before any production ingestion exists.

The workflow is available through:

- `raw-document-store-schema-fixture`
- `raw-document-store-schema-fixture-index`
- `raw-document-store-schema-fixture-health`
- `raw-document-store-schema-fixture-status`

`RAW_DOCUMENT_STORE_SCHEMA_FIXTURE_CREATED` means synthetic fixture rows exist for audit context only.

## Research Status

`research-status` exposes the latest Raw Document Store Schema Fixture run id, status, health status, workflow stage, artifact path, document count, validation issue count, report-only flags, next action, and safety fields.

This context is lower priority than the existing paper workflow path. It remains visible for audit, but it does not override `PAPER_WORKFLOW_READY` and does not create replay, buy-review, performance, or trading readiness.

## Safety Boundary

- The Raw Document Store Schema Fixture is synthetic/report-only.
- It is not production raw_document_store.
- It is not real data fetch.
- It is not raw document ingestion.
- It is not real source permission.
- It is not replay-ready evidence from real data.
- It does not write data/raw.
- It does not write data/processed.
- It does not write data/cache.
- It does not create factor observations.
- It does not create event ingestion.
- It does not create company exposure.
- It does not create replay evidence bundles.
- It does not create buy-review eligibility.
- It does not set buy_review_allowed.
- It is not strategy performance validation.
- It does not authorize current-candidates.
- It does not authorize snapshots.
- It does not authorize signal_semantics mutation.
- It does not authorize active stock_profile.
- It does not authorize promoted/production models.
- It does not authorize active thresholds.
- It does not authorize advisory predictions/probabilities.
- It does not authorize broker/order/message/API/trading.

## Future Approval Boundary

Any real raw document store, source adapter, production source registry state, real source permission, data ingestion, factor observation, event ingestion, company exposure, replay evidence bundle, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review, or trading workflow requires separate exact approval and validation.

The fixture rows are examples for schema review only. They must not be treated as production evidence, source approval, replay input, model input, paper approval, strategy performance validation, or trading permission.
