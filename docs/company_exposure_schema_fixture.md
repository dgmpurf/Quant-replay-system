# Company Exposure Schema Fixture

The Company Exposure Schema Fixture is a synthetic/report-only schema-governance workflow. It creates tiny `company_exposure` fixture artifacts only, so future source-backed exposure mapping work can review fields, PIT lineage, exposure types, direction semantics, and safety boundaries before any production company exposure mapping exists.

`company_exposure` means a stable, versioned, evidence-backed, PIT-governed mapping between an entity and an exposure context. It explains why the same factor or event can affect different stocks or ETFs differently. It is not a factor observation, not event ingestion, not replay evidence, not `signal_score`, not model training input, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, not strategy performance validation, and not trading permission.

## Commands

- `company-exposure-schema-fixture`
- `company-exposure-schema-fixture-index`
- `company-exposure-schema-fixture-health`
- `company-exposure-schema-fixture-status`

Default report-only outputs live under:

```text
outputs/reports/manual_diagnostics/company_exposure_schema_fixture_v0_1/<fixture_id>/
```

## Research-Status Context

`research-status` exposes the latest Company Exposure Schema Fixture run id, status/stage, health status, artifact path, exposure count, validation issue count, report-only flags, report path, next action, and downstream safety fields while preserving existing `PAPER_WORKFLOW_READY` priority.

`COMPANY_EXPOSURE_SCHEMA_FIXTURE_CREATED` means synthetic company exposure fixture rows exist for schema governance only.

## Exposure Policy

The fixture supports stocks and ETFs only as schema context. It does not create production mappings for either asset type.

`exposure_strength`, `exposure_measure`, and `mapping_confidence` are descriptive evidence context. They are not model weights, return probabilities, portfolio weights, signal weights, threshold inputs, or trading weights.

Any real company exposure mapping must be source-backed, versioned, PIT-valid, lineage-complete, and separately approved before a future workflow can consume it.

## Safety Boundary

The Company Exposure Schema Fixture is synthetic/report-only.

It does not create:

- production company exposure mappings
- active company exposure mappings
- company knowledge graphs
- real ETF holdings ingestion
- supplier/customer production graphs
- factor observations
- event ingestion
- replay evidence bundles
- `signal_score` implementation
- model training inputs
- active weights
- active thresholds
- stock_profile validation
- paper validation
- real buy-review eligibility
- `buy_review_allowed`
- strategy performance validation
- current-candidates integration
- snapshot integration
- signal_semantics mutation
- advisory predictions
- active probabilities
- broker/order/message/API/trading integration

It does not write data/raw, data/processed, or data/cache.

Any production company exposure mapping, active mapping, knowledge graph, ETF holdings ingestion, supplier/customer graph, factor observation, event ingestion, replay evidence bundle, signal_score, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review, performance validation, or trading workflow requires separate exact approval and validation.

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

## Recommended Next Task

Company Exposure Schema Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
