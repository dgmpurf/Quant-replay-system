# Source Update Notes v1.58.0

v1.58.0 is a report-only governance checkpoint for Source Registry Schema Fixture
core + artifact views + research-status integration + checkpoint docs.

## Repository Files Changed or Added

Changed:

- `src/quant_replay_system/local_research_dashboard.py`
- `src/quant_replay_system/cli.py`
- `tests/test_local_research_dashboard.py`
- `README.md`
- `docs/local_research_dashboard.md`

Added:

- `docs/source_registry_schema_fixture.md`
- `docs/release_checkpoint_v1.58.0.md`
- `SOURCE_UPDATE_NOTES_v1_58_0.md`

## ChatGPT Project Source Upload Guidance

For manual Project Source refresh, upload or replace only curated documentation/source
files. do not include src/ or tests/ in ChatGPT Project Source upload lists.

Recommended changed Project Source files for manual review:

- `00_PROJECT_SOURCE_INDEX.md`
- `02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md`
- `03_ROADMAP_AND_NEXT_DECISION_POINTS.md`
- `05_CODEX_OPERATING_PROTOCOL.md`
- `06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md`
- `07_CURRENT_STATE_SNAPSHOT.md`
- `08_HISTORICAL_REPLAY_TRAINING_STRATEGY.md`
- `SOURCE_UPDATE_NOTES_v1_58_0.md`

Keep unchanged unless separately edited:

- `01_PROJECT_VISION_AND_BOUNDARIES.md`
- `04_FREE_FIRST_DATA_SOURCE_STRATEGY.md`
- `10_RESEARCH_METHOD_STACK_AND_MODEL_GOVERNANCE.md`
- `FACTOR_TAXONOMY_SUMMARY.md`
- `FACTOR_TAXONOMY_V2_CANONICAL.md`
- `FACTOR_TAXONOMY_V2_RAW_EXCEL_EXPORT.md`

`docs/project_sources/` is intentionally absent from Git and must not be recreated.
docs/project_sources/ is intentionally absent from Git.

## Checkpoint Semantics

`SOURCE_REGISTRY_SCHEMA_FIXTURE_CREATED` means synthetic source-registry schema
fixture artifacts were created as report-only governance context.

It does not create real source permissions.
It does not create production source registry state.
It does not verify any API/vendor/source for production use.
It does not fetch real data.
It does not write data/raw.
It does not write data/processed.
It does not write data/cache.
It is not real buy-review eligibility.
It does not set buy_review_allowed.
It is not strategy performance validation.
It does not authorize current-candidates.
It does not authorize snapshots.
It does not authorize signal_semantics mutation.
It does not authorize active stock_profile.
It does not authorize promoted/production models.
It does not authorize active thresholds.
It does not authorize advisory predictions/probabilities.
It does not authorize broker/order/message/API/trading.

Any future real source registry, raw document store, factor observation, event ingestion,
company exposure, replay evidence bundle, real buy-review, performance validation, or
trading workflow requires separate exact approval and separate validation.
