# Factor Definition Schema Fixture

The Factor Definition Schema Fixture is a synthetic/report-only schema-governance workflow. It creates tiny `factor_definition` observation-rule fixture artifacts only, so future factor registry work can review fields, taxonomy coverage, source requirements, timing policies, and safety boundaries before any production factor library exists.

`factor_definition` means a stable, versioned observation-rule registry row. It is not a factor observation, not a live signal, not `signal_score`, not model training input, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, not strategy performance validation, and not trading permission.

## Commands

- `factor-definition-schema-fixture`
- `factor-definition-schema-fixture-index`
- `factor-definition-schema-fixture-health`
- `factor-definition-schema-fixture-status`

Default report-only outputs live under:

```text
outputs/reports/manual_diagnostics/factor_definition_schema_fixture_v0_1/<fixture_id>/
```

## Research-Status Context

`research-status` exposes the latest Factor Definition Schema Fixture run id, status/stage, health status, artifact path, factor count, taxonomy layer count, validation issue count, report-only flags, taxonomy classification flags, report path, next action, and downstream safety fields while preserving existing `PAPER_WORKFLOW_READY` priority.

`FACTOR_DEFINITION_SCHEMA_FIXTURE_CREATED` means synthetic factor definition rows exist for schema governance only.

## Taxonomy Policy

The fixture uses the 8-layer taxonomy as the primary classification:

1. `L1_OPERATIONS_COMPANY_EVENTS`
2. `L2_INDUSTRY_SUPPLY_DEMAND_VALUE_CHAIN_PRICES`
3. `L3_MACRO_LIQUIDITY_POLICY_GLOBAL`
4. `L4_CAPITAL_MARKET_INSTITUTIONS_SUPPLY_DEMAND`
5. `L5_TRADING_BEHAVIOR_MICROSTRUCTURE`
6. `L6_INFORMATION_DISCLOSURE_SENTIMENT_TRANSMISSION`
7. `L7_EXPECTATIONS_VALUATION_PRICING_DEVIATION`
8. `L8_RISK_EVENTS_COMPLIANCE_BOUNDARY`

The fixed 12-factor framework is only a coverage checklist. It is not final, not primary classification, and not a closed factor universe.

Taxonomy rows must not become BUY/SELL signals. They are classification and governance context only.

## Safety Boundary

The Factor Definition Schema Fixture is synthetic/report-only.

It does not create:

- active factor library
- factor observations
- real factor observations
- event ingestion
- company exposure mappings
- replay evidence bundles
- `signal_score` implementation
- live signals
- model training
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

Any real factor observations, event ingestion, company exposure, replay evidence bundle, signal_score, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review, performance validation, or trading workflow requires separate exact approval and validation.

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

Factor Definition Schema Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
