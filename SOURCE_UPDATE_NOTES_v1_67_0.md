# Source Update Notes v1.67.0

v1.67.0 is the Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture report-only checkpoint. It adds Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture core/views/research-status/checkpoint documentation context and preserves Quant Research Design Pack v0.1 / Algorithm Timing Guard.

## Changed Or New Repo Files

- `src/quant_replay_system/reviewed_local_csv_replay_prototype_input_contract_fixture_status.py`
- `src/quant_replay_system/local_research_dashboard.py`
- `src/quant_replay_system/cli.py`
- `tests/test_reviewed_local_csv_replay_prototype_input_contract_fixture_views.py`
- `tests/test_local_research_dashboard.py`
- `README.md`
- `docs/local_research_dashboard.md`
- `docs/quant_research_design_pack_v0_1.md`
- `docs/reviewed_local_csv_replay_prototype_input_contract_fixture.md`
- `docs/release_checkpoint_v1.67.0.md`
- `SOURCE_UPDATE_NOTES_v1_67_0.md`

## Semantics

`REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED` means synthetic/report-only Reviewed LOCAL_CSV replay prototype input contract fixture artifacts exist for schema governance only.

Reviewed LOCAL_CSV replay prototype input contract rows are future governed input contract examples. In this checkpoint they are schema fixture rows only. They are not real reviewed input packages, not active reviewed input candidates, not PIT admissibility validators, not real replay inputs, not replay evidence bundles, not replay decisions, not replay decision freezes, not forward labels, not future-label joins, not training datasets, not metric computation, not signal_score input authorization, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, not strategy performance validation, and not trading permission.

This checkpoint does not create real reviewed CSV packages, replay inputs, evidence bundles, replay decisions, decision freezes, forward labels, future-label joins, training datasets, metric results, signal_score implementation, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review, broker integration, API integration, order placement, message sending, or trading.

It does not write data/raw, does not write data/processed, and does not write data/cache.

It does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, active stock_profile, promoted/production models, active thresholds, advisory predictions/probabilities, buy_review_allowed, real buy-review eligibility, or strategy performance validation. It does not set buy_review_allowed.

It does not authorize broker/order/message/API/trading.

## Quant Research Design Pack / Algorithm Timing Guard

v1.67.0 preserves `docs/quant_research_design_pack_v0_1.md` and the Algorithm Timing Guard:

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

## Intended ChatGPT Project Source Update After Tag

After the user manually commits and tags v1.67.0, ChatGPT should generate the external Project Source update package. Do not create that package in Git during this checkpoint.

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
- `SOURCE_UPDATE_NOTES_v1_67_0.md`

## Recommended Next Task

Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture Post-Checkpoint Governance Audit Report-Only v0.1.
