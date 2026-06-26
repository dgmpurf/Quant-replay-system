# Source Update Notes v1.60.0

v1.60.0 is the Factor Definition Schema Fixture report-only checkpoint. It adds Factor Definition Schema Fixture core/views/research-status/checkpoint documentation context and preserves Quant Research Design Pack v0.1 / Algorithm Timing Guard.

## Changed Or New Repo Files

- `src/quant_replay_system/factor_definition_schema_fixture.py`
- `src/quant_replay_system/factor_definition_schema_fixture_index.py`
- `src/quant_replay_system/factor_definition_schema_fixture_health.py`
- `src/quant_replay_system/factor_definition_schema_fixture_status.py`
- `src/quant_replay_system/local_research_dashboard.py`
- `src/quant_replay_system/cli.py`
- `tests/test_factor_definition_schema_fixture.py`
- `tests/test_factor_definition_schema_fixture_views.py`
- `tests/test_local_research_dashboard.py`
- `README.md`
- `docs/local_research_dashboard.md`
- `docs/factor_definition_schema_fixture.md`
- `docs/release_checkpoint_v1.60.0.md`
- `SOURCE_UPDATE_NOTES_v1_60_0.md`

## Semantics

`FACTOR_DEFINITION_SCHEMA_FIXTURE_CREATED` means synthetic/report-only factor definition observation-rule fixture artifacts exist for schema governance only.

Factor definitions are stable, versioned observation-rule registry rows. They are not factor observations, not live signals, not signal_score implementation, not model training input, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, not strategy performance validation, and not trading permission.

The 8-layer taxonomy is the primary classification. The fixed 12-factor framework is only a coverage checklist and must not be treated as final.

This checkpoint does not create factor observations, real factor observations, event ingestion, company exposure, replay evidence bundle, signal_score implementation, active factor library, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review, broker integration, API integration, order placement, message sending, or trading.

It does not write data/raw, does not write data/processed, and does not write data/cache.

It does not authorize current-candidates, snapshots, signal_semantics mutation, active stock_profile, promoted/production models, active thresholds, advisory predictions/probabilities, buy_review_allowed, real buy-review eligibility, or strategy performance validation.

## Quant Research Design Pack / Algorithm Timing Guard

v1.60.0 preserves `docs/quant_research_design_pack_v0_1.md` and the Algorithm Timing Guard:

- signal_score formula is design reference only.
- real weights are not calibrated.
- thresholds are not active.
- ML training must wait until PIT-valid factor observations and forward labels exist.
- factor IC / Rank IC / CAR / event study metrics are evaluation methods, not strategy performance validation by themselves.
- stock_profile is a validation dossier, not a trade instruction.
- paper workflow must precede real buy-review.
- buy-review does not equal trading.
- no broker/order/API/trading integration is allowed in current scope.

## Intended ChatGPT Project Source Update After Tag

After the user manually commits and tags v1.60.0, ChatGPT should generate the external Project Source update package. Do not create that package in Git during this checkpoint.

ChatGPT should generate the external Project Source update after user tags v1.60.0.

The external update should include curated project-source documents only. It should not include runtime code or tests.

Do not include `src/` or `tests/` in ChatGPT Project Source upload lists.

`docs/project_sources/` is intentionally absent from Git and must not be recreated.

## Files Likely Relevant For Future Curated Source Update

- `00_PROJECT_SOURCE_INDEX.md`
- `02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md`
- `03_ROADMAP_AND_NEXT_DECISION_POINTS.md`
- `05_CODEX_OPERATING_PROTOCOL.md`
- `06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md`
- `07_CURRENT_STATE_SNAPSHOT.md`
- `08_HISTORICAL_REPLAY_TRAINING_STRATEGY.md`
- `10_RESEARCH_METHOD_STACK_AND_MODEL_GOVERNANCE.md`
- `SOURCE_UPDATE_NOTES_v1_60_0.md`

## Recommended Next Task

Factor Definition Schema Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
