# Replay Decision Schema Fixture

The Replay Decision Schema Fixture is a synthetic/report-only schema-governance workflow. It creates tiny `replay_decision` fixture artifacts only, so future replay decision work can review decision identity, replay evidence bundle references, PIT timing, available-time eligibility, source lineage, manual review state, risk veto state, freeze fields, and safety boundaries before real replay decisions exist.

`replay_decision` means a future PIT-governed decision context produced from an accepted replay evidence bundle. A real future decision must be backed by accepted replay evidence bundle lineage, accepted source registry entries, raw document or dataset lineage, PIT-valid factor observations, PIT-valid structured events and company exposures, available_time and revision checks, source hashes, quality state, manual review state, decision-time eligibility, and safety flags.

The fixture rows are not real replay decisions, not real replay evidence bundle consumption, not forward labels, not future labels joined, not signal_score inputs, not model training inputs, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, not strategy performance validation, and not trading permission.

## Commands

- `replay-decision-schema-fixture`
- `replay-decision-schema-fixture-index`
- `replay-decision-schema-fixture-health`
- `replay-decision-schema-fixture-status`

Default report-only outputs live under:

```text
outputs/reports/manual_diagnostics/replay_decision_schema_fixture_v0_1/<fixture_id>/
```

## Research-Status Context

`research-status` exposes the latest Replay Decision Schema Fixture run id, status/stage, health status, artifact path, decision count, validation issue count, report-only flags, report path, next action, and downstream safety fields while preserving existing `PAPER_WORKFLOW_READY` priority.

`REPLAY_DECISION_SCHEMA_FIXTURE_CREATED` means synthetic/report-only replay decision fixture rows exist for schema governance only.

## Timing And Semantics

`replay_decision_time`, `replay_as_of_date`, evidence-bundle `available_time_max`, `available_time_max`, source `revision_id`, and `all_inputs_available_lte_decision_time` are distinct. All future decision inputs must be available no later than the replay decision time before a real decision can become eligible.

The fixture links upstream schema fixture concepts only:

- replay evidence bundle references are schema references, not real replay evidence bundle consumption.
- decision labels are schema placeholders, not buy/sell signals.
- decision actionability is review context only, not real buy-review or trading permission.
- freeze fields are schema placeholders, not real replay decision freeze artifacts.
- risk veto fields are governance placeholders and can only block future actionability.

Fixture rows are not signal_score inputs and are not model-training inputs.

## Safety Boundary

The Replay Decision Schema Fixture is synthetic/report-only.

It is not real replay decisions, not real replay evidence bundle consumption, not forward labels, not future labels joined, not signal_score implementation, not authorized signal_score input, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, and does not authorize broker/order/message/API/trading.

It does not write data/raw, data/processed, or data/cache.

Any real replay decision workflow, real replay evidence bundle consumption, replay decision freeze, forward label, future label join, signal_score input, model training input, active weight, active threshold, stock_profile validation, paper validation, real buy-review, performance validation, or trading workflow requires separate exact approval, lineage, PIT validity, decision-time validation, and safety validation.

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

Replay Decision Schema Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
