# Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture

The Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture is a synthetic/report-only schema-governance workflow. It creates tiny reviewed LOCAL_CSV replay prototype input contract fixture artifacts only, so future reviewed local CSV replay input work can review package metadata, symbol/date identity, local CSV provenance, review attestations, PIT admissibility expectations, safety flags, and downstream exclusion boundaries before any real reviewed input package exists.

`REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED` means report-only input contract fixture rows exist for governance only.

The fixture rows are not real reviewed CSV packages, not active reviewed input candidates, not a PIT admissibility validator, not real replay inputs, not replay evidence bundles, not replay decisions, not decision freezes, not forward labels, not future-label joins, not training datasets, not metric computation, not signal_score inputs, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, not strategy performance validation, and not trading permission.

## Commands

- `reviewed-local-csv-replay-prototype-input-contract-fixture`
- `reviewed-local-csv-replay-prototype-input-contract-fixture-index`
- `reviewed-local-csv-replay-prototype-input-contract-fixture-health`
- `reviewed-local-csv-replay-prototype-input-contract-fixture-status`

Default report-only outputs live under:

```text
outputs/reports/manual_diagnostics/reviewed_local_csv_replay_prototype_input_contract_fixture_v0_1/<fixture_id>/
```

## Research-Status Context

`research-status` exposes the latest Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture run id, status/stage, health status, artifact path, contract count, validation issue count, report-only flags, report path, next action, and downstream safety fields while preserving existing `PAPER_WORKFLOW_READY` priority.

The expected post-checkpoint next action is:

```text
Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture Post-Checkpoint Governance Audit Report-Only v0.1
```

## Input Contract Semantics

The fixture is a future-facing contract example for reviewed local CSV replay prototype inputs. It may describe expected metadata and safety fields for a future local CSV package, but it does not create or approve such a package.

Any future real reviewed LOCAL_CSV replay prototype input workflow must separately validate local CSV provenance, reviewer authority, PIT timing, source lineage, admissibility boundaries, no future-label leakage, no signal_score input authorization, and no downstream active workflow side effects.

## Safety Boundary

The Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture is synthetic/report-only.

It does not create real reviewed input packages, active reviewed input candidates, PIT validators, real replay inputs, replay evidence bundles, replay decisions, frozen replay decisions, forward labels, future-label joins, training datasets, metric computations, signal_score inputs, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review eligibility, buy_review_allowed, or strategy performance validation.

It does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, and does not authorize broker/order/message/API/trading.

It does not write data/raw, data/processed, or data/cache.

Any real reviewed input package, PIT admissibility validator, replay input, replay evidence bundle, replay decision, decision freeze, forward label, future-label join, training dataset, metric computation, signal_score input, model training, stock_profile validation, paper validation, real buy-review, performance validation, or trading workflow requires separate exact approval, PIT validity, leakage validation, and safety validation.

## Algorithm Timing Guard

The v1.59 Algorithm Timing Guard remains active:

- signal_score formula is design reference only.
- real weights are not calibrated yet.
- thresholds are not active yet.
- ML training must wait until PIT-valid factor observations and real governed forward labels exist.
- normalization, winsorization, and direction-adjusted values are inactive.
- factor IC / Rank IC / CAR / event study metrics are evaluation methods, not strategy performance validation by themselves.
- stock_profile is a validation dossier, not a trade instruction.
- paper workflow must precede real buy-review.
- buy-review does not equal trading.
- no broker/order/API/trading integration is allowed in current scope.

## Recommended Next Task

Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
