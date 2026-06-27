# Factor Observation Schema Fixture

The Factor Observation Schema Fixture is a synthetic/report-only schema-governance workflow. It creates tiny `factor_observation` fixture artifacts only, so future source-backed factor observation work can review PIT timing, source lineage, factor-definition linkage, company/event context, calculation metadata, quality state, and safety boundaries before real factor observations exist.

`factor_observation` means a stable, versioned, PIT-governed observed or derived value for one factor definition, one entity/instrument/context, and one observation time. A real future observation must be backed by source/raw-document/dataset lineage, optional company exposure or event structured context, calculation/version metadata, quality/review state, and governance flags.

The fixture rows are not real factor observations, not production factor registry state, not active factor library state, not production event ingestion, not production company exposure mapping, not real raw document ingestion, not replay evidence bundle, not replay decisions, not forward labels, not signal_score implementation, not normalization/winsorization/direction-adjusted runtime, not model training input, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, not strategy performance validation, and not trading permission.

## Commands

- `factor-observation-schema-fixture`
- `factor-observation-schema-fixture-index`
- `factor-observation-schema-fixture-health`
- `factor-observation-schema-fixture-status`

Default report-only outputs live under:

```text
outputs/reports/manual_diagnostics/factor_observation_schema_fixture_v0_1/<fixture_id>/
```

## Research-Status Context

`research-status` exposes the latest Factor Observation Schema Fixture run id, status/stage, health status, artifact path, observation count, validation issue count, report-only flags, report path, next action, and downstream safety fields while preserving existing `PAPER_WORKFLOW_READY` priority.

`FACTOR_OBSERVATION_SCHEMA_FIXTURE_CREATED` means synthetic/report-only factor observation fixture rows exist for schema governance only.

## Timing And Semantics

`observation_date`, `period_end`, `source_publish_time`, `available_time`, and `as_of_date` are distinct. `available_time` controls future replay eligibility. In plain terms, available_time controls future replay eligibility.

The formula design reference is:

```text
x_{i,j,t} = O_j(E_{<=t}, exposure_{i,<=t}, event_{<=t})
```

This formula is design reference only. It does not create signal_score, active weights, active thresholds, model training inputs, or trading logic.

`factor_definition` defines the rule. `factor_observation` is the time-specific observed value produced under that rule. Put plainly, factor_definition defines the rule.

`event_structured` may provide context, but no factor observation is created from event rows without a separate PIT-valid factor observation workflow. Put plainly, event_structured may provide context.

`company_exposure` may inform context or future direction review, but this fixture does not create active weights, trading direction, or signal semantics. Put plainly, company_exposure may inform context.

`confidence` is evidence/calculation confidence, not return probability. Put plainly, confidence is evidence/calculation confidence, not return probability.

`raw_value` is not a signal score and is not a normalized active model input. Put plainly, raw_value is not a signal score.

Normalization, winsorization, and direction adjustment are inactive in this checkpoint. Normalized, winsorized, and direction-adjusted fields remain placeholders unless a future approved workflow creates PIT-valid transformed observations.

Risk veto can block actionability in future governance, but it does not create positive alpha or buy permission.

Fixture rows are not buy/sell signals.

## Safety Boundary

The Factor Observation Schema Fixture is synthetic/report-only.

It is not real factor observations, not production factor registry, not active factor library, not production event ingestion, not production company exposure mapping, not real raw document ingestion, not replay evidence bundle, not replay decisions, not forward labels, not normalization, not winsorization, not direction-adjusted values, not signal_score implementation, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, and does not authorize broker/order/message/API/trading.

It does not write data/raw, data/processed, or data/cache.

Any real factor observation workflow, production factor registry, active factor library, production event ingestion, production company exposure mapping, real raw document ingestion, replay evidence bundle, replay decisions, forward labels, normalization, winsorization, direction-adjusted values, signal_score, model training input, active weights, active thresholds, stock_profile validation, paper validation, real buy-review, performance validation, or trading workflow requires separate exact approval, lineage, PIT validity, and validation.

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

## Recommended Next Task

Factor Observation Schema Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
