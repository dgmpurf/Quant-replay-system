# Source Update Notes v1.61.0

v1.61.0 is the Company Exposure Schema Fixture report-only checkpoint. It adds Company Exposure Schema Fixture core/views/research-status/checkpoint documentation context and preserves Quant Research Design Pack v0.1 / Algorithm Timing Guard.

## Changed Or New Repo Files

- `src/quant_replay_system/company_exposure_schema_fixture.py`
- `src/quant_replay_system/company_exposure_schema_fixture_index.py`
- `src/quant_replay_system/company_exposure_schema_fixture_health.py`
- `src/quant_replay_system/company_exposure_schema_fixture_status.py`
- `src/quant_replay_system/local_research_dashboard.py`
- `src/quant_replay_system/cli.py`
- `tests/test_company_exposure_schema_fixture.py`
- `tests/test_company_exposure_schema_fixture_views.py`
- `tests/test_local_research_dashboard.py`
- `README.md`
- `docs/local_research_dashboard.md`
- `docs/company_exposure_schema_fixture.md`
- `docs/release_checkpoint_v1.61.0.md`
- `SOURCE_UPDATE_NOTES_v1_61_0.md`

## Semantics

`COMPANY_EXPOSURE_SCHEMA_FIXTURE_CREATED` means synthetic/report-only company exposure fixture artifacts exist for schema governance only.

Company exposure rows are stable, versioned, evidence-backed, PIT-governed mapping rows between an entity and exposure context. They help explain why the same factor or event can affect different stocks or ETFs differently. They are not production exposure mappings, not active mappings, not company knowledge graph state, not factor observations, not event ingestion, not replay evidence, not signal_score implementation, not model training input, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, not strategy performance validation, and not trading permission.

`exposure_strength`, `exposure_measure`, and `mapping_confidence` are descriptive evidence context. They are not model weights, return probabilities, portfolio weights, signal weights, threshold inputs, or trading weights.

This checkpoint does not create production company exposure mapping, active company exposure mapping, company knowledge graph, real ETF holdings ingestion, supplier/customer graph, factor observations, event ingestion, replay evidence bundle, signal_score implementation, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review, broker integration, API integration, order placement, message sending, or trading.

It does not write data/raw, does not write data/processed, and does not write data/cache.

It does not authorize current-candidates, snapshots, signal_semantics mutation, active stock_profile, promoted/production models, active thresholds, advisory predictions/probabilities, buy_review_allowed, real buy-review eligibility, or strategy performance validation.

## Quant Research Design Pack / Algorithm Timing Guard

v1.61.0 preserves `docs/quant_research_design_pack_v0_1.md` and the Algorithm Timing Guard:

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

After the user manually commits and tags v1.61.0, ChatGPT should generate the external Project Source update package. Do not create that package in Git during this checkpoint.

ChatGPT should generate the external Project Source update after user tags v1.61.0.

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
- `SOURCE_UPDATE_NOTES_v1_61_0.md`

## Recommended Next Task

Company Exposure Schema Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
