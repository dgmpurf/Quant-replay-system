# Quant Research Design Pack v0.1

## Purpose

This design pack records the research substrate boundaries needed before the project moves from report-only fixture governance toward real point-in-time source, raw-document, factor, replay, model, stock_profile, paper, and buy-review workflows. It is a normal repository document, not a ChatGPT Project Source package, and it does not create runtime behavior.

The current Raw Document Store Schema Fixture checkpoint is synthetic/report-only. `RAW_DOCUMENT_STORE_SCHEMA_FIXTURE_CREATED` is not production raw_document_store, not real data fetch, not raw document ingestion, and not real source permission.

It does not write data/raw, does not write data/processed, does not write data/cache, does not create factor observations, does not create event ingestion, does not create company exposure, does not create replay evidence bundles, does not create buy-review eligibility, does not set buy_review_allowed, is not strategy performance validation, and does not authorize broker/order/message/API/trading.

## Part 1: Evidence / Source / Raw Document / Available-Time / Revision / LOCAL_CSV Contract

Source and raw document records must preserve source identity, permission scope, access method, source URL or local path, available_time, retrieval time, source_hash, revision_id, document type, entity linkage, and report-only or production flags.

For LOCAL_CSV inputs, a future production workflow must record who prepared the file, the source of each row, when the data was available, how revisions are tracked, and whether the file can be used for decision-time replay. A file name alone is not source permission and not PIT evidence.

The current fixture does not write data/raw, does not write data/processed, and does not write data/cache.

## Part 2: Factor Definition / Factor Observation / Event Structured / Company Exposure

Factor definitions should use the 8-layer taxonomy as the primary structure and keep the broader factor universe expandable. A factor definition needs field names, units, directionality, source requirements, update cadence, PIT timing policy, and leakage guards.

Factor observations must wait for PIT-valid source and raw-document evidence. They need entity id, symbol, observation date, available_time, value, source lineage, source_hash, revision_id, and quality status.

Event structured records must preserve event type, event time, publish time, available_time, source lineage, entity linkage, and revision history.

Company exposure records must preserve entity, exposure type, source lineage, available_time, revision_id, and review status.

The current fixture does not create factor observations, does not create event ingestion, does not create company exposure, and does not create replay evidence bundles.

## Part 3: Market Regime / Sentiment / Risk / Market Confirmation / Signal Score / Risk Veto

Market regime, sentiment, risk, and market confirmation layers are design areas only until PIT-valid observations exist. They may be documented as proposed fields, but they must not be interpreted as live signals, advisory predictions, current-candidates inputs, or trading permission.

Signal score and risk veto concepts are allowed as design references only. They must preserve source lineage, available_time, revision_id, and leakage guards before any future replay or model workflow can consume them.

## Part 4: Replay Labels / Metrics / Model Governance / Stock Profile / Buy-Review Ladder

Replay labels must wait for frozen replay decisions and forward-return label governance. Metric work remains bounded and descriptive until separate evaluation approval exists.

Model governance must keep model-weight-versioning, active-model, stock_profile, paper workflow, APPROVED_FOR_PAPER, and buy-review decisions separated. Each promotion step needs exact approval and evidence.

stock_profile is a validation dossier, not a trade instruction. Paper workflow must precede real buy-review. buy-review does not equal trading.

## Algorithm Timing Guard

- signal_score formula is design reference only.
- real weights are not calibrated yet.
- thresholds are not active yet.
- ML training must wait until PIT-valid factor observations and forward labels exist.
- factor IC / Rank IC / CAR / event study metrics are evaluation methods, not strategy performance validation by themselves.
- stock_profile is a validation dossier, not a trade instruction.
- paper workflow must precede real buy-review.
- buy-review does not equal trading.
- no broker/order/API/trading integration is allowed in current scope.

## What May Be Implemented Now

Report-only schema fixtures, artifact views, health/status checks, research-status context, design audits, and checkpoint docs may be implemented when they preserve safety flags and do not create production data, active models, paper approvals, buy-review, or trading permission.

## What Must Wait For PIT-Valid Observations

Factor observations, structured events, company exposures, replay evidence bundles, and source-backed feature rows must wait until source registry, raw document store, available_time, source_hash, revision_id, and quality-status requirements are satisfied by real reviewed evidence.

## What Must Wait For Frozen Replay Decisions And Forward Labels

Replay labels, training datasets, metric computation, training results, model weight research, threshold planning, prediction rows, probability calibration, and feature importance must wait for frozen replay decisions and governed forward labels.

## What Must Wait For OOS / Walk-Forward Evaluation

Strategy performance validation, benchmark outperformance claims, robustness claims, active threshold decisions, and production-readiness claims must wait for explicit out-of-sample and walk-forward evaluation workflows. Metric evidence by itself is not profitability proof.

## What Must Wait For stock_profile And Paper Workflow Validation

Symbol-level validation, stock_profile readiness, paper workflow validation, APPROVED_FOR_PAPER, and real buy-review eligibility must wait for separately approved stock_profile and paper workflow governance.

## What Requires Exact Human Approval Before Real Buy-Review

Real buy-review requires explicit human approval after source, raw-document, factor, replay, label, metric, model, stock_profile, and paper workflow boundaries are satisfied. No fixture or report-only artifact grants real buy-review eligibility or sets buy_review_allowed.

## What Is Still Forbidden: Broker/Order/API/Trading Automation

Broker integration, order placement, real messages, external API calls, LLM API calls, automated trading, active stock_profile, promoted model, production model, active thresholds, advisory predictions, active probabilities, current-candidates integration, snapshot integration, signal_semantics mutation, and trading automation remain forbidden in the current scope.
# Event Structured Schema Fixture Checkpoint Note

`EVENT_STRUCTURED_SCHEMA_FIXTURE_CREATED` means synthetic/report-only event structured fixture rows exist for schema governance only. This note preserves the Algorithm Timing Guard and clarifies that the fixture is not production event ingestion, not active event library, not real raw document ingestion, not real source adapter, not factor observation, not production company exposure mapping, not replay evidence bundle, not signal_score implementation, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, and does not authorize broker/order/message/API/trading.

The v1.59 Algorithm Timing Guard remains active: signal_score formula is design reference only; real weights are not calibrated yet; thresholds are not active yet; ML training must wait until PIT-valid factor observations and forward labels exist; factor IC / Rank IC / CAR / event study metrics are evaluation methods, not strategy performance validation by themselves; stock_profile is a validation dossier, not a trade instruction; paper workflow must precede real buy-review; buy-review does not equal trading; no broker/order/API/trading integration is allowed in current scope.

# Factor Observation Schema Fixture Checkpoint Note

`FACTOR_OBSERVATION_SCHEMA_FIXTURE_CREATED` means synthetic/report-only factor observation fixture rows exist for schema governance only. This note preserves the Algorithm Timing Guard and clarifies that the fixture is not real factor observations, not production factor registry, not active factor library, not production event ingestion, not production company exposure mapping, not real raw document ingestion, not replay evidence bundle, not replay decisions, not forward labels, not signal_score implementation, not normalization/winsorization/direction-adjusted runtime, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, and does not authorize broker/order/message/API/trading.

The v1.59 Algorithm Timing Guard remains active: signal_score formula is design reference only; real weights are not calibrated yet; thresholds are not active yet; ML training must wait until PIT-valid factor observations and forward labels exist; normalization, winsorization, and direction-adjusted values are inactive; factor IC / Rank IC / CAR / event study metrics are evaluation methods, not strategy performance validation by themselves; stock_profile is a validation dossier, not a trade instruction; paper workflow must precede real buy-review; buy-review does not equal trading; no broker/order/API/trading integration is allowed in current scope.

# Replay Decision Schema Fixture Checkpoint Note

`REPLAY_DECISION_SCHEMA_FIXTURE_CREATED` means synthetic/report-only replay decision fixture rows exist for schema governance only. This note preserves the Algorithm Timing Guard and clarifies that the fixture is not real replay decisions, not real replay evidence bundle consumption, not forward labels, not future labels joined, not signal_score input authorization, not model training input, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, and does not authorize broker/order/message/API/trading.

The v1.59 Algorithm Timing Guard remains active: signal_score formula is design reference only; real weights are not calibrated yet; thresholds are not active yet; ML training must wait until PIT-valid factor observations and forward labels exist; normalization, winsorization, and direction-adjusted values are inactive; factor IC / Rank IC / CAR / event study metrics are evaluation methods, not strategy performance validation by themselves; stock_profile is a validation dossier, not a trade instruction; paper workflow must precede real buy-review; buy-review does not equal trading; no broker/order/API/trading integration is allowed in current scope.

# Forward Return Label Schema Fixture Checkpoint Note

`FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED` means synthetic/report-only forward return label fixture rows exist for schema governance only. This note preserves the Algorithm Timing Guard and clarifies that the fixture is not real forward labels, not future labels joined to decision inputs, not signal_score input authorization, not model training input authorization, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, and does not authorize broker/order/message/API/trading.

The v1.59 Algorithm Timing Guard remains active: signal_score formula is design reference only; real weights are not calibrated yet; thresholds are not active yet; ML training must wait until PIT-valid factor observations and real governed forward labels exist; normalization, winsorization, and direction-adjusted values are inactive; factor IC / Rank IC / CAR / event study metrics are evaluation methods, not strategy performance validation by themselves; stock_profile is a validation dossier, not a trade instruction; paper workflow must precede real buy-review; buy-review does not equal trading; no broker/order/API/trading integration is allowed in current scope.

# Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture Checkpoint Note

`REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED` means synthetic/report-only reviewed LOCAL_CSV replay prototype input contract fixture rows exist for schema governance only. This note preserves the Algorithm Timing Guard and clarifies that the fixture is not real reviewed CSV packages, not active reviewed input candidates, not PIT admissibility validation, not real replay inputs, not replay evidence bundles, not replay decisions, not replay decision freezes, not forward labels, not future-label joins, not training datasets, not metric computation, not signal_score input authorization, not model training input authorization, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, and does not authorize broker/order/message/API/trading.

The v1.59 Algorithm Timing Guard remains active: signal_score formula is design reference only; real weights are not calibrated yet; thresholds are not active yet; ML training must wait until PIT-valid factor observations and real governed forward labels exist; normalization, winsorization, and direction-adjusted values are inactive; factor IC / Rank IC / CAR / event study metrics are evaluation methods, not strategy performance validation by themselves; stock_profile is a validation dossier, not a trade instruction; paper workflow must precede real buy-review; buy-review does not equal trading; no broker/order/API/trading integration is allowed in current scope.

# Tiny PIT Admissibility Validator Contract Fixture Checkpoint Note

`TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED` means synthetic/report-only Tiny PIT admissibility validator contract fixture rows exist for schema governance only. This note preserves the Algorithm Timing Guard and clarifies that the fixture is not a real PIT validator, not real reviewed CSV packages, not active reviewed input candidates, not real replay inputs, not replay evidence bundles, not replay decisions, not replay decision freezes, not forward labels, not future-label joins, not training datasets, not metric computation, not signal_score input authorization, not model training input authorization, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, and does not authorize broker/order/message/API/trading.

The v1.59 Algorithm Timing Guard remains active: signal_score formula is design reference only; real weights are not calibrated yet; thresholds are not active yet; ML training must wait until PIT-valid factor observations and real governed forward labels exist; normalization, winsorization, and direction-adjusted values are inactive; factor IC / Rank IC / CAR / event study metrics are evaluation methods, not strategy performance validation by themselves; stock_profile is a validation dossier, not a trade instruction; paper workflow must precede real buy-review; buy-review does not equal trading; no broker/order/API/trading integration is allowed in current scope.

# Replay Evidence Bundle Schema Fixture Checkpoint Note

`REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED` means synthetic/report-only replay evidence bundle fixture rows exist for schema governance only. This note preserves the Algorithm Timing Guard and clarifies that the fixture is not real replay evidence bundles, not replay decisions, not forward labels, not future labels, not production factor observations, not real factor observations, not production factor registry, not active factor library, not production event ingestion, not active event library, not production company exposure mapping, not real raw document ingestion, not signal_score implementation, not authorized signal_score input, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, and does not authorize broker/order/message/API/trading.

The v1.59 Algorithm Timing Guard remains active: signal_score formula is design reference only; real weights are not calibrated yet; thresholds are not active yet; ML training must wait until PIT-valid factor observations and forward labels exist; normalization, winsorization, and direction-adjusted values are inactive; factor IC / Rank IC / CAR / event study metrics are evaluation methods, not strategy performance validation by themselves; stock_profile is a validation dossier, not a trade instruction; paper workflow must precede real buy-review; buy-review does not equal trading; no broker/order/API/trading integration is allowed in current scope.
