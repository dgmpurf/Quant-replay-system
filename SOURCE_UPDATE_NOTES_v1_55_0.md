# SOURCE UPDATE NOTES v1.55.0

v1.55.0 adds APPROVED_FOR_PAPER Phase 1 research-status integration and checkpoint documentation.

Update ChatGPT Project Source after commit/tag with:

- `README.md`
- `docs/local_research_dashboard.md`
- `docs/approved_for_paper_phase1.md`
- `docs/release_checkpoint_v1.55.0.md`
- `SOURCE_UPDATE_NOTES_v1_55_0.md`
- `src/quant_replay_system/local_research_dashboard.py`
- `src/quant_replay_system/cli.py`
- `src/quant_replay_system/approved_for_paper_phase1.py`
- `src/quant_replay_system/approved_for_paper_phase1_index.py`
- `src/quant_replay_system/approved_for_paper_phase1_health.py`
- `src/quant_replay_system/approved_for_paper_phase1_status.py`
- `tests/test_approved_for_paper_phase1.py`
- `tests/test_approved_for_paper_phase1_views.py`
- `tests/test_local_research_dashboard.py`

`APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED` remains scoped report-only context. It is not global APPROVED_FOR_PAPER, not real buy-review, not strategy performance validation, not current-candidates, not snapshot, not signal_semantics, not active stock_profile, not promoted model, not production model, not active thresholds, not advisory predictions, not active probabilities, and not trading.

`docs/project_sources/ is intentionally absent from Git`.

ChatGPT Project Source is maintained separately and should be refreshed only after the local commit/tag is intentionally created by the user or an explicitly approved Git task.
