# Source Update Notes v1.63.0

v1.63.0 is the Factor Observation Schema Fixture report-only checkpoint. It adds Factor Observation Schema Fixture core/views/research-status/checkpoint documentation context and preserves Quant Research Design Pack v0.1 / Algorithm Timing Guard.

## Changed Or New Repo Files

- `src/quant_replay_system/factor_observation_schema_fixture.py`
- `src/quant_replay_system/factor_observation_schema_fixture_index.py`
- `src/quant_replay_system/factor_observation_schema_fixture_health.py`
- `src/quant_replay_system/factor_observation_schema_fixture_status.py`
- `src/quant_replay_system/local_research_dashboard.py`
- `src/quant_replay_system/cli.py`
- `tests/test_factor_observation_schema_fixture.py`
- `tests/test_factor_observation_schema_fixture_views.py`
- `tests/test_local_research_dashboard.py`
- `README.md`
- `docs/local_research_dashboard.md`
- `docs/factor_observation_schema_fixture.md`
- `docs/release_checkpoint_v1.63.0.md`
- `SOURCE_UPDATE_NOTES_v1_63_0.md`

## Semantics

`FACTOR_OBSERVATION_SCHEMA_FIXTURE_CREATED` means synthetic/report-only factor observation fixture artifacts exist for schema governance only.

Factor observation rows are stable, versioned, PIT-governed observed or derived values for one factor definition, one entity/instrument/context, and one observation time. In this checkpoint they are schema fixture rows only. They are not real factor observations, not production factor registry state, not active factor library state, not production event ingestion, not production company exposure mapping, not real raw document ingestion, not replay evidence bundle, not replay decisions, not forward labels, not signal_score implementation, not normalization/winsorization/direction-adjusted runtime, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, not strategy performance validation, and not trading permission.

`observation_date`, `period_end`, `source_publish_time`, `available_time`, and `as_of_date` remain distinct; `available_time` controls future replay eligibility. `confidence` is evidence/calculation confidence, not return probability. `raw_value` is not signal_score and is not normalized active model input.

This checkpoint does not create production factor observations, real factor observations, production factor registry, active factor library, production event ingestion, production company exposure mapping, real raw document ingestion, replay evidence bundle, replay decisions, forward labels, normalization, winsorization, direction-adjusted values, signal_score implementation, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review, broker integration, API integration, order placement, message sending, or trading.

It does not write data/raw, does not write data/processed, and does not write data/cache.

It does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, active stock_profile, promoted/production models, active thresholds, advisory predictions/probabilities, buy_review_allowed, real buy-review eligibility, or strategy performance validation. It does not set buy_review_allowed.

It does not authorize broker/order/message/API/trading.

## Quant Research Design Pack / Algorithm Timing Guard

v1.63.0 preserves `docs/quant_research_design_pack_v0_1.md` and the Algorithm Timing Guard:

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

## Intended ChatGPT Project Source Update After Tag

After the user manually commits and tags v1.63.0, ChatGPT should generate the external Project Source update package. Do not create that package in Git during this checkpoint.

ChatGPT should generate the external Project Source update after user tags v1.63.0.

The external update should include curated project-source documents only. It should not include runtime code or tests.

do not include src/ or tests/ in ChatGPT Project Source upload lists.

`docs/project_sources/` is intentionally absent from Git and must not be recreated.

docs/project_sources/ is intentionally absent from Git.

## Files Likely Relevant For Future Curated Source Update

- `00_PROJECT_SOURCE_INDEX.md`
- `02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md`
- `03_ROADMAP_AND_NEXT_DECISION_POINTS.md`
- `05_CODEX_OPERATING_PROTOCOL.md`
- `06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md`
- `07_CURRENT_STATE_SNAPSHOT.md`
- `08_HISTORICAL_REPLAY_TRAINING_STRATEGY.md`
- `10_RESEARCH_METHOD_STACK_AND_MODEL_GOVERNANCE.md`
- `SOURCE_UPDATE_NOTES_v1_63_0.md`

## Recommended Next Task

Factor Observation Schema Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
