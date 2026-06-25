# Source Update Notes v1.59.0

v1.59.0 is the Raw Document Store Schema Fixture report-only checkpoint. It adds Raw Document Store Schema Fixture core/views/research-status/checkpoint documentation context and records Quant Research Design Pack v0.1 / Algorithm Timing Guard.

## Changed Or New Repo Files

- `src/quant_replay_system/local_research_dashboard.py`
- `src/quant_replay_system/cli.py`
- `tests/test_local_research_dashboard.py`
- `README.md`
- `docs/local_research_dashboard.md`
- `docs/raw_document_store_schema_fixture.md`
- `docs/release_checkpoint_v1.59.0.md`
- `docs/quant_research_design_pack_v0_1.md`
- `SOURCE_UPDATE_NOTES_v1_59_0.md`

## Semantics

`RAW_DOCUMENT_STORE_SCHEMA_FIXTURE_CREATED` means synthetic/report-only raw document and dataset-reference fixture artifacts exist for schema governance only.

It is not production raw_document_store, not real data fetch, not raw document ingestion, and not real source permission.

This checkpoint does not create production raw_document_store, real source permission, real data fetch, raw document ingestion, factor observations, event ingestion, company exposure, replay evidence bundle, buy-review, performance validation, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review, broker integration, API integration, order placement, message sending, or trading.

It does not write data/raw, does not write data/processed, and does not write data/cache.

It does not create factor observations, does not create event ingestion, does not create company exposure, does not create replay evidence bundles, does not create buy-review eligibility, does not set buy_review_allowed, is not strategy performance validation, and does not authorize broker/order/message/API/trading.

It does not authorize current-candidates, snapshots, signal_semantics mutation, active stock_profile, promoted/production models, active thresholds, advisory predictions/probabilities, buy_review_allowed, real buy-review eligibility, or strategy performance validation.

## Quant Research Design Pack / Algorithm Timing Guard

v1.59.0 adds `docs/quant_research_design_pack_v0_1.md` so future work keeps the timing boundary visible:

- signal_score formula is design reference only.
- real weights are not calibrated yet.
- thresholds are not active yet.
- ML training must wait until PIT-valid factor observations and forward labels exist.
- factor IC / Rank IC / CAR / event study metrics are evaluation methods, not strategy performance validation by themselves.
- stock_profile is a validation dossier, not a trade instruction.
- paper workflow must precede real buy-review.
- buy-review does not equal trading.
- no broker/order/API/trading integration is allowed in current scope.

## Intended ChatGPT Project Source Update After Tag

After the user manually commits and tags v1.59.0, ChatGPT should generate the external Project Source update package. Do not create that package in Git during this checkpoint.

ChatGPT should generate the external Project Source update after user tags v1.59.0.

The external update should include curated project-source documents only. It should not include runtime code or tests.

do not include src/ or tests/ in ChatGPT Project Source upload lists.

docs/project_sources/ is intentionally absent from Git and must not be recreated.

## Files Likely Relevant For Future Curated Source Update

- `00_PROJECT_SOURCE_INDEX.md`
- `02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md`
- `03_ROADMAP_AND_NEXT_DECISION_POINTS.md`
- `05_CODEX_OPERATING_PROTOCOL.md`
- `06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md`
- `07_CURRENT_STATE_SNAPSHOT.md`
- `08_HISTORICAL_REPLAY_TRAINING_STRATEGY.md`
- `10_RESEARCH_METHOD_STACK_AND_MODEL_GOVERNANCE.md`
- `SOURCE_UPDATE_NOTES_v1_59_0.md`

## Recommended Next Task

Raw Document Store Schema Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
