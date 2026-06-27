# Replay Evidence Bundle Schema Fixture

The Replay Evidence Bundle Schema Fixture is a synthetic/report-only schema-governance workflow. It creates tiny `replay_evidence_bundle` fixture artifacts only, so future replay input work can review source registry, raw document store, factor definition, company exposure, event structured, factor observation, PIT timing, source lineage, evidence admissibility, risk veto, review state, and safety boundaries before real replay evidence bundles exist.

`replay_evidence_bundle` means a future PIT-governed bundle of evidence assembled for one replay decision context. A real future bundle must be backed by accepted source registry entries, raw document or dataset lineage, PIT-valid factor definitions, company exposure context, event structured context, factor observations, available_time and revision checks, source hashes, quality state, manual review state, and safety flags.

The fixture rows are not real replay evidence bundles, not replay decisions, not forward labels, not future labels, not production factor observations, not real factor observations, not production factor registry state, not active factor library state, not production event ingestion, not active event library state, not production company exposure mapping, not real raw document ingestion, not normalization, not winsorization, not direction-adjusted runtime, not signal_score implementation, not authorized signal_score input, not model training input, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, not strategy performance validation, and not trading permission.

## Commands

- `replay-evidence-bundle-schema-fixture`
- `replay-evidence-bundle-schema-fixture-index`
- `replay-evidence-bundle-schema-fixture-health`
- `replay-evidence-bundle-schema-fixture-status`

Default report-only outputs live under:

```text
outputs/reports/manual_diagnostics/replay_evidence_bundle_schema_fixture_v0_1/<fixture_id>/
```

## Research-Status Context

`research-status` exposes the latest Replay Evidence Bundle Schema Fixture run id, status/stage, health status, artifact path, bundle count, validation issue count, report-only flags, report path, next action, and downstream safety fields while preserving existing `PAPER_WORKFLOW_READY` priority.

`REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED` means synthetic/report-only replay evidence bundle fixture rows exist for schema governance only.

## Timing And Semantics

`replay_decision_time`, `replay_as_of_date`, `available_time_max`, and source `revision_id` coverage are distinct. `available_time_max` must be less than or equal to the future replay decision time before a real bundle can become replay-input evidence. Put plainly, available_time_max must be less than or equal to the future replay decision time.

The fixture links upstream schema fixture concepts only:

- source registry references are schema references, not real source permissions.
- raw document references are schema references, not real raw document ingestion.
- factor definition references are schema references, not active factor library state.
- company exposure references are schema references, not production exposure mappings.
- event structured references are schema references, not production event ingestion.
- factor observation references are schema references, not real factor observations.

Evidence admissibility and risk veto fields are governance placeholders. They can block future actionability, but they do not create positive alpha, buy permission, replay readiness, or trading readiness.

Fixture rows are not buy/sell signals.

## Safety Boundary

The Replay Evidence Bundle Schema Fixture is synthetic/report-only.

It is not real replay evidence bundles, not replay decisions, not forward labels, not future labels, not production factor observations, not real factor observations, not production factor registry, not active factor library, not production event ingestion, not active event library, not production company exposure mapping, not real raw document ingestion, not normalization, not winsorization, not direction-adjusted values, not signal_score implementation, not authorized signal_score input, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, and does not authorize broker/order/message/API/trading.

It does not write data/raw, data/processed, or data/cache.

Any real replay evidence bundle workflow, replay decision, forward label, future label join, production factor observation, real factor observation, production factor registry, active factor library, production event ingestion, active event library, production company exposure mapping, real raw document ingestion, normalization, winsorization, direction-adjusted value, signal_score, model training input, active weight, active threshold, stock_profile validation, paper validation, real buy-review, performance validation, or trading workflow requires separate exact approval, lineage, PIT validity, and validation.

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

Replay Evidence Bundle Schema Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
