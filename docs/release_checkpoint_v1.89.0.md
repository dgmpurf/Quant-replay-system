# Release Checkpoint v1.89.0

## A. Decision / Status

```text
phase = historical_replay_mixed_stock_etf_universe_profile_policy_checkpoint_documentation
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_previous_checkpoint = v1.88.0
latest_previous_checkpoint_commit = 67af8d7
latest_previous_checkpoint_tag = v1.88.0
latest_repo_commit_at_start = 92b91f9
candidate_checkpoint_version = v1.89.0
checkpoint_documentation_created = yes
checkpoint_docs_approved = no
tag_approved = no
source_update_approved = no
selected_next_route = Historical Replay Mixed STOCK/ETF Universe Profile Policy Checkpoint Commit Review Report-Only v0.1
```

This checkpoint documentation records the completed report-only Historical Replay Mixed STOCK/ETF Universe Profile Policy Contract / Fixture chain. It documents the synthetic fixture, artifact views, CLI surface, research-status integration, next-task wording hardening, focused validation, temp-root smoke, and safety boundaries.

This checkpoint documentation does not create or approve official evidence, no-hit evidence acceptance, profile conflict resolution, universe membership approval, stock_profile validation, PIT admissibility, replay input, replay execution, forward labels, metrics, training, model changes, paper expansion, buy-review, broker integration, orders, messages, external calls, or trading.

## B. Current Accepted State

The previous formal checkpoint is `v1.88.0` at commit `67af8d7`. The repository start state for this checkpoint documentation was commit `92b91f9`, described as `v1.88.0-7-g92b91f9`, with no tag pointing at `HEAD`.

External ChatGPT Project Source is user-reported as updated to `v1.88.0`.

Accepted mixed profile chain state before this documentation task:

- Planning created at `106450b`.
- Core fixture implementation created at `530f268`.
- Generated artifact review created at `4e741ab`.
- Next-action wording hardening created at `92b91f9`.
- Existing command family:
  - `historical-replay-mixed-stock-etf-universe-profile-policy`
  - `historical-replay-mixed-stock-etf-universe-profile-policy-index`
  - `historical-replay-mixed-stock-etf-universe-profile-policy-health`
  - `historical-replay-mixed-stock-etf-universe-profile-policy-status`
- Current live recommended next task:
  - `Historical Replay Mixed STOCK/ETF Universe Profile Policy Checkpoint Documentation Bundle Report-Only v0.1`

Known historical context is preserved: duplicate post-v1.87 governance audit commits `9728367` and `b1ef749` remain in history, and the known historical whitespace artifact on `9728367` is not rewritten. This task does not amend, reset, retag, or rewrite history.

## C. Completed Chain Summary

The completed mixed profile chain remains report-only, diagnostic-only, local-only, and synthetic-only:

- Planning defined the mixed STOCK/ETF universe profile policy boundary for the selected `2024-04-02 / etf_core` sample.
- Core fixture writes deterministic synthetic mixed profile policy artifacts only.
- Artifact views provide index, health, and status wrapping for those artifacts.
- CLI exposes the same bounded core/index/health/status surfaces.
- Research-status integration makes mixed profile context visible without overriding later paper workflow priority.
- Generated artifact review confirmed artifact content, counts, STOCK/ETF rows, health/status, research-status fields, and safety flags were coherent.
- Next-action wording hardening moved live outputs from the completed generated artifact review route to this checkpoint documentation route.

## D. Selected Sample And Mixed STOCK/ETF Count Contract

```text
selected_historical_decision_date = 2024-04-02
selected_universe = etf_core
selected_symbols = 000001, 000002, 159915, 300750, 510300, 600000, 600519, 601318, 688981
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
report_only = yes
diagnostic_only = yes
local_only = yes
synthetic_only = yes
mixed_stock_etf_profile_policy_fixture_only = yes
profile_conflict_resolved = no
universe_membership_approved = no
stock_profile_validated = no
official_evidence_collection_started = no
official_evidence_accepted = no
official_evidence_closed = no
buy_review_allowed = no
trading_allowed = no
```

Seven STOCK rows remain visible profile-policy conflicts under the legacy `etf_core` sample context:

```text
000001, 000002, 300750, 600000, 600519, 601318, 688981
```

Two ETF rows are profile-aligned context only, not universe proof:

```text
159915, 510300
```

## E. Mixed Profile Policy Artifact Contract

The core fixture artifact contract contains exactly eight report-only artifacts:

- `metadata.json`
- `mixed_stock_etf_universe_profile_policy_rows.csv`
- `mixed_stock_etf_universe_profile_policy_required_fields.csv`
- `mixed_stock_etf_universe_profile_policy_status_vocabulary.csv`
- `mixed_stock_etf_universe_profile_policy_blocker_vocabulary.csv`
- `mixed_stock_etf_universe_profile_policy_matrix.csv`
- `mixed_stock_etf_universe_profile_policy_safety_flags.json`
- `mixed_stock_etf_universe_profile_policy_report.md`

The artifacts preserve:

- selected symbol order and leading zeros;
- STOCK versus ETF row separation;
- legacy `etf_core` sample context;
- recommended profile as a routing hint only;
- visible profile conflicts for STOCK rows;
- aligned ETF context without official universe proof;
- blocker visibility on every selected row;
- false downstream safety flags.

Generated artifacts are not committed by this checkpoint documentation task and must not be bundled into Project Source.

## F. Files And Modules In Scope

Created by this task:

- `docs/release_checkpoint_v1.89.0.md`

Read-only context inspected:

- `docs/historical_replay_mixed_stock_etf_universe_profile_policy_planning_legacy_etf_core_v0_1.md`
- `docs/historical_replay_mixed_stock_etf_universe_profile_policy_generated_artifact_review_v0_1.md`
- `docs/historical_replay_mixed_stock_etf_universe_profile_policy_next_task_wording_hardening_v0_1.md`
- `docs/release_checkpoint_v1.88.0.md`
- `src/quant_replay_system/historical_replay_mixed_stock_etf_universe_profile_policy.py`
- `src/quant_replay_system/historical_replay_mixed_stock_etf_universe_profile_policy_index.py`
- `src/quant_replay_system/historical_replay_mixed_stock_etf_universe_profile_policy_health.py`
- `src/quant_replay_system/historical_replay_mixed_stock_etf_universe_profile_policy_status.py`
- `src/quant_replay_system/cli.py`
- `src/quant_replay_system/local_research_dashboard.py`
- `tests/test_historical_replay_mixed_stock_etf_universe_profile_policy.py`
- `tests/test_historical_replay_mixed_stock_etf_universe_profile_policy_views.py`
- `tests/test_historical_replay_mixed_stock_etf_universe_profile_policy_cli.py`
- `tests/test_local_research_dashboard.py`

No feature-specific checkpoint note was created. Existing release checkpoint style is sufficient for this bundle, and the task explicitly preferred creating only `docs/release_checkpoint_v1.89.0.md` unless a stronger convention required another file.

## G. Validation Results

Preflight:

```text
git status --short --branch
## main...origin/main

git describe --tags --always
v1.88.0-7-g92b91f9

git tag --points-at HEAD
<no output>

git tag --points-at 67af8d7
v1.88.0

git tag --points-at 85348df
v1.87.0

git tag --points-at 69f98eb
v1.86.0

git show --check 92b91f9
exit 0

git diff --check
exit 0
```

Focused mixed profile fixture/views/CLI tests:

```text
.venv\Scripts\python.exe -m pytest tests/test_historical_replay_mixed_stock_etf_universe_profile_policy.py tests/test_historical_replay_mixed_stock_etf_universe_profile_policy_views.py tests/test_historical_replay_mixed_stock_etf_universe_profile_policy_cli.py -q
19 passed in 5.35s
```

Dashboard/research-status focused:

```text
.venv\Scripts\python.exe -m pytest tests/test_local_research_dashboard.py -q
382 passed in 283.00s (0:04:43)
```

Combined focused suite:

```text
.venv\Scripts\python.exe -m pytest tests/test_local_research_dashboard.py tests/test_historical_replay_mixed_stock_etf_universe_profile_policy.py tests/test_historical_replay_mixed_stock_etf_universe_profile_policy_views.py tests/test_historical_replay_mixed_stock_etf_universe_profile_policy_cli.py tests/test_historical_replay_reviewer_no_hit_acceptance_fixture.py tests/test_historical_replay_reviewer_no_hit_acceptance_fixture_views.py tests/test_historical_replay_reviewer_no_hit_acceptance_fixture_cli.py tests/test_historical_replay_official_manual_evidence_collection_template_fixture.py tests/test_historical_replay_official_manual_evidence_collection_template_fixture_views.py tests/test_historical_replay_official_manual_evidence_collection_template_fixture_cli.py -q
447 passed in 287.20s (0:04:47)
```

## H. Temp-Root CLI Smoke Result

Temp-root CLI smoke used a repo-external temp root only. It ran:

- `historical-replay-mixed-stock-etf-universe-profile-policy`
- `historical-replay-mixed-stock-etf-universe-profile-policy-index`
- `historical-replay-mixed-stock-etf-universe-profile-policy-health`
- `historical-replay-mixed-stock-etf-universe-profile-policy-status`
- `research-status`

Observed:

```text
core_exit = 0
index_exit = 0
health_exit = 0
status_exit = 0
research_status_exit = 0
health_output_contains_PASS = true
research_status_context_visible = true
artifact_file_count = 8
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
profile_conflict_resolved = false
universe_membership_approved = false
stock_profile_validated = false
buy_review_allowed = false
trading_allowed = false
```

Temp artifacts stayed outside the repository worktree. No repo `outputs/`, protected data directory, or `docs/project_sources` tree was written.

## I. Research-Status Integration Result

Research-status integration is visible through the local dashboard and CLI output:

- mixed profile context is visible when `--root` points to the temp reports root;
- latest run id is reported for the mixed profile fixture context;
- status remains `MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_FIXTURE_CREATED_REPORT_ONLY`;
- health status remains PASS in the focused smoke;
- recommended next task points to checkpoint documentation bundle;
- counts and safety flags surface as context only.

The research-status fields do not convert mixed profile policy context into official evidence, universe membership approval, stock_profile validation, PIT approval, replay readiness, buy-review, or trading permission.

## J. Workflow Priority And PAPER_WORKFLOW_READY Preservation

Dashboard-focused tests verify that mixed profile policy context does not override later paper workflow priority. The local research dashboard preserves `PAPER_WORKFLOW_READY` when paper workflow context is present.

The mixed profile policy context is informational and lower priority. It must not regress final workflow priority or imply that any downstream active replay, paper expansion, buy-review, or trading gate is open.

## K. Safety And Non-Approval Boundary

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

No no-hit context is accepted as evidence. No official evidence is collected, accepted, or closed. No PIT admissibility approval is granted. No profile conflict is resolved. No universe membership is approved. No stock_profile validation is created. No buy-review or trading permission exists.

## L. Static Safety Scan Result

Static safety scan was run after creating this checkpoint document. Observed interpretation:

- no affirmative unsafe `yes` approval flags;
- true-flag matches are limited to existing negative health tests that intentionally patch unsafe fixture state;
- risky readiness wording appears only in guard lists, negative assertions, future vocabulary rows that explicitly say not evidence, or explicit non-approval policy text;
- no unresolved placeholder markers;
- `docs/project_sources` appears only in negative policy context.

## M. Protected Tracked And docs/project_sources Scan Result

Protected tracked scan result:

```text
data/processed/.gitkeep
data/raw/.gitkeep
outputs/reports/.gitkeep
```

`git status --short -- docs/project_sources` result:

```text
<no output>
```

## N. Full Non-Slow Decision

Full non-slow was not run in this checkpoint documentation task.

Focused + dashboard + combined focused + temp-root CLI smoke are sufficient to create checkpoint documentation for this report-only mixed profile fixture chain. Full non-slow should be considered before tag/source update if this candidate checkpoint is promoted to a release-like Project Source update.

## O. Candidate Tag Plan

Candidate checkpoint version is `v1.89.0`, but this task does not create or approve a tag.

Tag `v1.89.0` should only be considered after:

- checkpoint documentation is reviewed;
- checkpoint commit review passes;
- full non-slow pre-tag validation is explicitly approved and passes;
- manual tag readiness is confirmed.

## P. Source Update Timing Plan

No Project Source update is approved by this task.

Source update should be considered only after:

- checkpoint documentation is committed and reviewed;
- full non-slow pre-tag validation passes;
- the manual tag is created;
- a separate source-readiness or source-update task explicitly scopes the changed Project Source files.

`docs/project_sources` must not be recreated in the repository.

## Q. Open Blockers

No blocker is identified for checkpoint documentation review and commit review.

This does not mean profile policy is accepted, universe membership is approved, official evidence is accepted, PIT is approved, replay is ready, buy-review is allowed, or trading is allowed.

## R. Non-Blocking Notes

- The fixture remains synthetic-only.
- The seven STOCK rows remain unresolved profile conflicts under legacy `etf_core` context.
- The two ETF rows are context-aligned only and not official universe proof.
- Generated artifacts are reviewed but not committed as repo outputs.
- Full non-slow remains deferred to a later explicitly scoped validation task before any tag/source update.

## S. Recommended Next Routes

Candidate next routes:

A. `Historical Replay Mixed STOCK/ETF Universe Profile Policy Checkpoint Commit Review Report-Only v0.1`

B. `Historical Replay Mixed STOCK/ETF Universe Profile Policy Full Non-Slow Pre-Tag Validation Report-Only v0.1`

C. `Historical Replay Mixed STOCK/ETF Universe Profile Policy Additional Wording Hardening Report-Only v0.1`

D. `Historical Replay Official Manual Evidence Collection Fill Protocol Design Report-Only v0.1`

E. Pause repo work and manually collect official source/status evidence outside the repo

F. `Historical Replay Mixed STOCK/ETF Universe Profile Policy Generated Artifact Review Hardening Report-Only v0.1`

## T. Selected Next Route

Selected next route:

```text
Historical Replay Mixed STOCK/ETF Universe Profile Policy Checkpoint Commit Review Report-Only v0.1
```

This is selected because checkpoint documentation and validation are clean, and no further wording hardening or artifact-review correction is required before commit review.

## U. Why Selected Route Is Safe

The selected route is safe because it is a review-only commit-readiness step. It does not approve evidence, profile conflict resolution, universe membership, PIT admissibility, replay execution, labels, metrics, training, stock_profile, paper expansion, buy-review, or trading.

It keeps the repo moving toward a possible `v1.89.0` checkpoint without creating a tag or Project Source update in this task.

## V. What Must Not Be Bundled

The checkpoint documentation bundle must not include:

- generated repo artifacts under `outputs/`;
- official source fetches;
- filled evidence templates;
- accepted no-hit evidence;
- accepted official evidence packets;
- official evidence closure;
- PIT evidence closure;
- active replay input;
- replay execution;
- replay decision freeze;
- forward labels;
- metric computation outside tests;
- model training;
- stock_profile validation;
- paper workflow expansion;
- current-candidates output;
- snapshot output;
- broker/API/order/message/LLM calls;
- protected data writes;
- Project Source packages;
- `docs/project_sources`.

## W. ChatGPT/Codex Mode Recommendation

Recommended next mode: Codex high for checkpoint commit review.

Use a separate explicit task for full non-slow pre-tag validation. Use ChatGPT review before tag/source update decisions if the checkpoint is promoted toward `v1.89.0`.

## X. Commit/Tag/Source Recommendation

Recommended commit message if ready:

```text
docs: document historical replay mixed stock ETF universe profile policy checkpoint v1.89.0
```

Recommended tag decision:

```text
No tag in this task. Tag v1.89.0 is not approved by this task.
```

Recommended Source update decision:

```text
No Source update in this task. Source update should be considered only after checkpoint documentation is committed, reviewed, full non-slow pre-tag validation passes, and a manual tag is created.
```

## Y. Recommended Next Task

```text
Historical Replay Mixed STOCK/ETF Universe Profile Policy Checkpoint Commit Review Report-Only v0.1
```

Final classification:

```text
HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_CHECKPOINT_DOCUMENTATION_CREATED_REPORT_ONLY
```

Final verdict:

```text
HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_CHECKPOINT_DOCUMENTATION_READY_FOR_REVIEW_AND_COMMIT_REPORT_ONLY
```
