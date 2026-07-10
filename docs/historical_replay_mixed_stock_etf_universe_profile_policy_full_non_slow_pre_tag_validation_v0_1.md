# Historical Replay Mixed STOCK/ETF Universe Profile Policy Full Non-Slow Pre-Tag Validation v0.1

## A. Decision / Status

```text
phase = historical_replay_mixed_stock_etf_universe_profile_policy_full_non_slow_pre_tag_validation
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_previous_checkpoint = v1.88.0
latest_previous_checkpoint_commit = 67af8d7
latest_previous_checkpoint_tag = v1.88.0
candidate_checkpoint_version = v1.89.0
validation_report_created = yes
full_non_slow_run = yes
full_non_slow_passed = yes
tag_approved = no
source_update_approved = no
selected_next_route = Historical Replay Mixed STOCK/ETF Universe Profile Policy Pre-Tag Readiness Wording Hardening Report-Only v0.1
```

This report records full non-slow pre-tag validation for candidate checkpoint `v1.89.0`.
It does not create a tag, update Project Source, create Project Source files in the repository, modify source/test/runtime code, collect official evidence, accept evidence, approve PIT, create replay inputs, or authorize buy-review or trading.

Required non-approval fields remain:

```text
official_source_hierarchy_approved = no
official_evidence_collection_started = no
official_evidence_collection_approved = no
official_evidence_accepted = no
official_evidence_closed = no
official_status_evidence_closure_approved = no
pit_evidence_closure_approved = no
pit_admissibility_approved = no
active_replay_input_approved = no
real_replay_execution_approved = no
replay_decision_freeze_approved = no
forward_labels_created = no
forward_label_creation_approved = no
training_dataset_created = no
metric_computation_approved = no
model_training_approved = no
weights_or_thresholds_adjustment_approved = no
stock_profile_expansion_approved = no
paper_expansion_approved = no
real_buy_review_approved = no
buy_review_allowed = no
trading_allowed = no
broker_api_approved = no
order_placement_approved = no
message_delivery_approved = no
external_api_or_llm_approved = no
current_candidates_execution_approved = no
snapshot_build_approved = no
signal_semantics_mutation_approved = no
data_raw_processed_cache_writes_approved = no
docs_project_sources_created = no
```

## B. Git / Tag State

Preflight matched the expected state:

```text
git status --short --branch = ## main...origin/main
HEAD = d5fb9b6 docs: review historical replay mixed stock ETF universe profile policy checkpoint commit
git describe --tags --always = v1.88.0-9-gd5fb9b6
git tag --points-at HEAD = <no output>
git tag --points-at 67af8d7 = v1.88.0
git tag --list v1.89.0 = <no output>
git tag --list v1.88.0 = v1.88.0
git show --check d5fb9b6 = clean
git diff --check = clean
```

The latest formal checkpoint remains `v1.88.0`. Candidate checkpoint `v1.89.0` remains untagged.

## C. Focused Sanity Validation

Command:

```text
$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest tests/test_historical_replay_mixed_stock_etf_universe_profile_policy.py tests/test_historical_replay_mixed_stock_etf_universe_profile_policy_views.py tests/test_historical_replay_mixed_stock_etf_universe_profile_policy_cli.py -q
```

Result:

```text
19 passed in 5.14s
```

Focused core/views/CLI sanity passed.

## D. Full Non-Slow Validation Result

Dashboard/research-status sanity command:

```text
$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest tests/test_local_research_dashboard.py -q
```

Dashboard/research-status result:

```text
382 passed in 280.40s (0:04:40)
```

Full non-slow command:

```text
$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest -m "not slow" -q
```

Full non-slow result:

```text
6279 passed, 109 deselected, 5 warnings in 1587.73s (0:26:27)
```

No failures occurred.

Warnings observed:

- `tests/test_data_ingestion.py::test_universe_ingestion_fails_with_invalid_non_empty_listed_date`
  - pandas date format inference warning in `src/quant_replay_system/data_ingestion.py`.
- `tests/test_factor_dataset.py::test_invalid_non_empty_listed_date_raises_clear_factor_dataset_error`
  - pandas date format inference warning in `src/quant_replay_system/data.py`.
- `tests/test_forward_return_label.py::test_missing_start_or_end_price_blocks[price_patch0]`
  - pandas future dtype-assignment warning in the test patch.
- `tests/test_metric_evaluation.py::test_gate_failures_block[training_evaluation_sample_rows_path-patch5-METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED]`
  - pandas future dtype-assignment warning in the test patch.
- `tests/test_metric_extension.py::test_metric_extension_health_fails_for_invalid_artifact_boundaries[missing_counts-RESULT_ROW_NUMERATOR_DENOMINATOR_MISSING]`
  - pandas future dtype-assignment warning in the test patch.

The warnings are non-blocking for this pre-tag validation because the full non-slow suite exited 0 and produced no failures.

## E. Temp-Root CLI Smoke Result

Temp-root CLI smoke was run under a repository-external temp reports root, represented here as `<TEMP_REPORTS_ROOT>`.

Commands:

```text
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-mixed-stock-etf-universe-profile-policy --output-dir <TEMP_REPORTS_ROOT>\manual_diagnostics\historical_replay_mixed_stock_etf_universe_profile_policy_legacy_etf_core_v0_1
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-mixed-stock-etf-universe-profile-policy-index --root <TEMP_REPORTS_ROOT>\manual_diagnostics\historical_replay_mixed_stock_etf_universe_profile_policy_legacy_etf_core_v0_1 --output-dir <TEMP_REPORTS_ROOT>\manual_diagnostics\historical_replay_mixed_stock_etf_universe_profile_policy_legacy_etf_core_v0_1\index
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-mixed-stock-etf-universe-profile-policy-health --root <TEMP_REPORTS_ROOT>\manual_diagnostics\historical_replay_mixed_stock_etf_universe_profile_policy_legacy_etf_core_v0_1 --output-dir <TEMP_REPORTS_ROOT>\manual_diagnostics\historical_replay_mixed_stock_etf_universe_profile_policy_legacy_etf_core_v0_1\health
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-mixed-stock-etf-universe-profile-policy-status --root <TEMP_REPORTS_ROOT>\manual_diagnostics\historical_replay_mixed_stock_etf_universe_profile_policy_legacy_etf_core_v0_1 --output-dir <TEMP_REPORTS_ROOT>\manual_diagnostics\historical_replay_mixed_stock_etf_universe_profile_policy_legacy_etf_core_v0_1\status
.venv\Scripts\python.exe -m quant_replay_system.cli research-status --root <TEMP_REPORTS_ROOT> --output-dir <TEMP_REPORTS_ROOT>\research_status
```

Exit results:

```text
core = 0
index = 0
health = 0
status = 0
research-status = 0
```

Health result:

```text
health_status = MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_HEALTH_PASS_REPORT_ONLY
checked_artifact_count = 1
issue_count = 0
error_count = 0
warning_count = 0
```

The smoke generated the expected eight core mixed-policy artifact files plus index/health/status files under the temp root only.

## F. Count And Selected Sample Confirmation

Selected sample:

```text
historical_decision_date = 2024-04-02
universe_name = etf_core
selected_symbols = 000001, 000002, 159915, 300750, 510300, 600000, 600519, 601318, 688981
```

Temp-root smoke count contract:

```text
row_count = 9
stock_row_count = 7
etf_row_count = 2
profile_conflict_count = 7
profile_aligned_context_count = 2
unresolved_profile_conflict_count = 7
profile_policy_accepted_count = 0
universe_membership_approved_count = 0
official_status_evidence_accepted_count = 0
row_with_blocker_count = 9
safety_true_count = 0
```

Safety flags remained false:

```text
profile_conflict_resolved = false
universe_membership_approved = false
stock_profile_validated = false
buy_review_allowed = false
trading_allowed = false
```

## G. Research-Status Confirmation

Temp-root research-status exited 0 and exposed the mixed policy context:

```text
Research status = WARN
workflow_stage = DATA_PREPARATION_READY
historical_replay_mixed_stock_etf_universe_profile_policy_context_visible = True
latest_historical_replay_mixed_stock_etf_universe_profile_policy_status = MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_FIXTURE_CREATED_REPORT_ONLY
latest_historical_replay_mixed_stock_etf_universe_profile_policy_health_status = MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_HEALTH_PASS_REPORT_ONLY
latest_historical_replay_mixed_stock_etf_universe_profile_policy_workflow_stage = HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_FIXTURE_CREATED_REPORT_ONLY
latest_historical_replay_mixed_stock_etf_universe_profile_policy_row_count = 9
latest_historical_replay_mixed_stock_etf_universe_profile_policy_stock_row_count = 7
latest_historical_replay_mixed_stock_etf_universe_profile_policy_etf_row_count = 2
latest_historical_replay_mixed_stock_etf_universe_profile_policy_profile_conflict_count = 7
latest_historical_replay_mixed_stock_etf_universe_profile_policy_profile_aligned_context_count = 2
latest_historical_replay_mixed_stock_etf_universe_profile_policy_unresolved_profile_conflict_count = 7
latest_historical_replay_mixed_stock_etf_universe_profile_policy_profile_policy_accepted_count = 0
latest_historical_replay_mixed_stock_etf_universe_profile_policy_universe_membership_approved_count = 0
latest_historical_replay_mixed_stock_etf_universe_profile_policy_official_status_evidence_accepted_count = 0
latest_historical_replay_mixed_stock_etf_universe_profile_policy_row_with_blocker_count = 9
latest_historical_replay_mixed_stock_etf_universe_profile_policy_safety_true_count = 0
latest_historical_replay_mixed_stock_etf_universe_profile_policy_profile_conflict_resolved = False
latest_historical_replay_mixed_stock_etf_universe_profile_policy_universe_membership_approved = False
latest_historical_replay_mixed_stock_etf_universe_profile_policy_stock_profile_validated = False
latest_historical_replay_mixed_stock_etf_universe_profile_policy_buy_review_allowed = False
latest_historical_replay_mixed_stock_etf_universe_profile_policy_trading_allowed = False
```

The temp-root workflow status is expected to be `WARN` because the isolated temp reports root intentionally lacks broader live dashboard artifacts. It is not a mixed-policy artifact health failure.

## H. Live Recommended-Next-Task Wording Review

Current live mixed policy core/status/research-status recommended next task still points to:

```text
Historical Replay Mixed STOCK/ETF Universe Profile Policy Checkpoint Documentation Bundle Report-Only v0.1
```

This wording is stale after checkpoint documentation and checkpoint commit review have been completed. Because full non-slow passed but the live recommended-next-task wording remains stale, the selected next route is:

```text
Historical Replay Mixed STOCK/ETF Universe Profile Policy Pre-Tag Readiness Wording Hardening Report-Only v0.1
```

Do not skip the wording hardening and go straight to tag/source readiness planning.

## I. Static Safety Scan Result

Static safety scan was run against:

```text
docs\historical_replay_mixed_stock_etf_universe_profile_policy_full_non_slow_pre_tag_validation_v0_1.md
docs\release_checkpoint_v1.89.0.md
docs\historical_replay_mixed_stock_etf_universe_profile_policy_checkpoint_commit_review_v0_1.md
src\quant_replay_system\historical_replay_mixed_stock_etf_universe_profile_policy.py
src\quant_replay_system\historical_replay_mixed_stock_etf_universe_profile_policy_index.py
src\quant_replay_system\historical_replay_mixed_stock_etf_universe_profile_policy_health.py
src\quant_replay_system\historical_replay_mixed_stock_etf_universe_profile_policy_status.py
src\quant_replay_system\cli.py
src\quant_replay_system\local_research_dashboard.py
tests\test_historical_replay_mixed_stock_etf_universe_profile_policy.py
tests\test_historical_replay_mixed_stock_etf_universe_profile_policy_views.py
tests\test_historical_replay_mixed_stock_etf_universe_profile_policy_cli.py
tests\test_local_research_dashboard.py
```

Actual interpretation:

- the new validation report produced no static-scan matches when scanned alone;
- the full scan produced expected matches in existing guard lists, parser/help surfaces, and negative tests;
- one existing negative health-view test intentionally mutates a guarded boolean and verifies that health fails;
- existing docs matches are limited to negative Project Source repository policy context;
- no affirmative approval `yes` fields were found;
- no safety fields are set to true outside guard or negative-test contexts;
- risky readiness wording appears only in explicit non-approval, guard, parser help, or historical/negative-test contexts;
- no unresolved placeholder markers were found.

## J. Protected Tracked And docs_project_sources Scan Result

Protected tracked scan remains limited to placeholders:

```text
data/processed/.gitkeep
data/raw/.gitkeep
outputs/reports/.gitkeep
```

`git status --short -- docs\project_sources` produced no output.

## K. Failure Analysis If Applicable

No failure-analysis route is selected because focused sanity, dashboard sanity, full non-slow, temp-root CLI smoke, protected tracked scan, and final whitespace check passed.

The only issue found is stale live recommended-next-task wording, which is a bounded wording/readiness issue and not a validation failure.

## L. Candidate Next Routes Reviewed

Candidate next routes:

A. `Historical Replay Mixed STOCK/ETF Universe Profile Policy Pre-Tag Readiness Wording Hardening Report-Only v0.1`

B. `Historical Replay Mixed STOCK/ETF Universe Profile Policy Tag and Source Readiness Planning Report-Only v0.1`

C. `Historical Replay Mixed STOCK/ETF Universe Profile Policy Full Non-Slow Failure Analysis Report-Only v0.1`

D. `Historical Replay Mixed STOCK/ETF Universe Profile Policy Full Non-Slow Validation Report Hardening Report-Only v0.1`

E. `Historical Replay Official Manual Evidence Collection Fill Protocol Design Report-Only v0.1`

F. Pause repo work and manually collect official source/status evidence outside the repo

## M. Selected Next Route

Selected next route:

```text
Historical Replay Mixed STOCK/ETF Universe Profile Policy Pre-Tag Readiness Wording Hardening Report-Only v0.1
```

## N. Why Selected Route Is Safe

The selected route is safe because validation passed, but live recommended-next-task wording still points to the already-completed checkpoint documentation step. A narrow wording hardening task can update next-action text before any tag/source readiness planning is considered.

This route does not approve evidence collection, evidence acceptance, PIT, replay, labels, metrics, training, model work, stock_profile validation, paper expansion, buy-review, or trading.

## O. What Must Not Be Bundled

Do not bundle any of the following into this validation report:

- tag creation;
- Project Source update;
- Source update notes;
- Project Source repository files;
- source/test/runtime edits;
- generated repository artifacts;
- official source fetching;
- filled evidence templates;
- no-hit context acceptance;
- official evidence acceptance;
- evidence closure;
- PIT validation as approval;
- active replay input;
- replay execution;
- replay decision freeze;
- forward label creation;
- metric computation outside tests;
- training/evaluation outside tests;
- model work;
- stock_profile validation;
- paper workflow expansion;
- current-candidates execution;
- snapshot build;
- broker/API/order/message/LLM calls;
- protected data writes.

## P. ChatGPT/Codex Mode Recommendation

Recommended next mode: Codex high for the narrow pre-tag readiness wording hardening task.

ChatGPT review should occur before any later tag or Project Source update decision.

## Q. Commit/Tag/Source Recommendation

Recommended commit message if ready:

```text
docs: record historical replay mixed stock ETF universe profile policy full non-slow pre-tag validation
```

Recommended tag decision:

```text
No tag for this validation report.
```

Recommended Source update decision:

```text
No Source update for this validation report.
```

## R. Recommended Next Task

```text
Historical Replay Mixed STOCK/ETF Universe Profile Policy Pre-Tag Readiness Wording Hardening Report-Only v0.1
```

Final classification:

```text
HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_FULL_NON_SLOW_PRE_TAG_VALIDATION_CREATED_REPORT_ONLY
```

Final verdict:

```text
HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_FULL_NON_SLOW_PRE_TAG_VALIDATION_READY_FOR_PRE_TAG_READINESS_WORDING_HARDENING_REPORT_ONLY
```
