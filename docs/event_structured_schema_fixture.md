# Event Structured Schema Fixture

The Event Structured Schema Fixture is a synthetic/report-only schema-governance workflow. It creates tiny `event_structured` fixture artifacts only, so future source-backed event extraction and structured-event work can review fields, PIT timing, event type semantics, direction semantics, source quality, and safety boundaries before any production event ingestion exists.

`event_structured` means a stable, versioned, evidence-backed, PIT-governed record of a public event candidate. It is not production event ingestion, not active event library state, not real raw document ingestion, not real source adapter output, not factor observation, not production company exposure mapping, not replay evidence bundle, not signal_score implementation, not model training input, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, not strategy performance validation, and not trading permission.

## Commands

- `event-structured-schema-fixture`
- `event-structured-schema-fixture-index`
- `event-structured-schema-fixture-health`
- `event-structured-schema-fixture-status`

Default report-only outputs live under:

```text
outputs/reports/manual_diagnostics/event_structured_schema_fixture_v0_1/<fixture_id>/
```

## Research-Status Context

`research-status` exposes the latest Event Structured Schema Fixture run id, status/stage, health status, artifact path, event count, validation issue count, report-only flags, report path, next action, and downstream safety fields while preserving existing `PAPER_WORKFLOW_READY` priority.

`EVENT_STRUCTURED_SCHEMA_FIXTURE_CREATED` means synthetic/report-only event structured fixture rows exist for schema governance only.

## Timing And Semantics

`event_time / publish_time / available_time are distinct`. `available_time controls replay eligibility`.

`confidence is extraction/evidence confidence, not return probability`.

`direction is contextual and may require company exposure`.

Future LLM extraction, if separately approved, must remain evidence-producing and reviewable. `LLM output must not become deterministic advisory logic`.

The fixture rows do not create factor observations; future workflows must `do not create factor observations` from event rows without a separate PIT-valid observation workflow.

## Safety Boundary

The Event Structured Schema Fixture is synthetic/report-only.

It is not production event ingestion, not active event library, not real raw document ingestion, not real source adapter, not factor observation, not production company exposure mapping, not replay evidence bundle, not signal_score implementation, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, and does not authorize broker/order/message/API/trading.

It does not write data/raw, data/processed, or data/cache.

Any production event ingestion, active event library, real raw document ingestion, real source adapter/crawler/connector, LLM extraction runtime, factor observation, production company exposure mapping, replay evidence bundle, signal_score, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review, performance validation, or trading workflow requires separate exact approval and validation.

## Algorithm Timing Guard

The v1.59 Algorithm Timing Guard remains active:

- signal_score formula is design reference only.
- real weights are not calibrated yet.
- thresholds are not active yet.
- ML training must wait until PIT-valid factor observations and forward labels exist.
- factor IC / Rank IC / CAR / event study metrics are evaluation methods, not strategy performance validation by themselves.
- stock_profile is a validation dossier, not a trade instruction.
- paper workflow must precede real buy-review.
- buy-review does not equal trading.
- no broker/order/API/trading integration is allowed in current scope.

## Recommended Next Task

Event Structured Schema Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
