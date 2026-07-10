# Historical Replay Mixed STOCK/ETF Universe Profile Policy Post-v1.89 Next-Task Wording Hardening Report-Only v0.1

## Decision / Status

phase = historical_replay_mixed_stock_etf_universe_profile_policy_post_v1_89_next_task_wording_hardening
decision = ready
docs_only_report_created = yes
wording_only_source_change = yes
schema_changed = no
row_contract_changed = no
count_contract_changed = no
status_vocabulary_changed = no
blocker_vocabulary_changed = no
safety_semantics_changed = no
research_status_priority_changed = no
current_checkpoint = v1.89.0
current_checkpoint_commit = 7ca9c4d
implementation_start_head = 4d31477
current_task_model = GPT-5.6 Sol
current_task_mode = Goal
selected_next_route = Historical Replay Source / Evidence Sufficiency Policy Planning Without Evidence Collection Report-Only v0.1

Final classification:

`HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_POST_V1_89_NEXT_TASK_WORDING_HARDENED_REPORT_ONLY`

Final verdict:

`HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_READY_FOR_SOURCE_EVIDENCE_SUFFICIENCY_POLICY_PLANNING_REPORT_ONLY`

The live next-task wording now advances from the completed tag/source readiness phase to a report-only source/evidence sufficiency policy planning phase without authorizing evidence collection.

## Preflight

- Branch: `main`.
- Worktree: clean before changes.
- HEAD: `4d314772f7fc216ee0fb3965b0721f323081ce23`.
- Describe: `v1.89.0-2-g4d31477`.
- Tags at HEAD: none.
- `v1.89.0`: remains at `7ca9c4d`.
- `v1.88.0`: remains at `67af8d7`.
- Commit `4d31477` contains only the post-v1.89 generated artifact review / wording audit report.
- `git show --check 4d31477`: clean.
- Initial `git diff --check`: clean.

## Stale Wording and RED-Equivalent Evidence

Before the fix, the old route appeared in seven current positive locations:

- core `RECOMMENDED_NEXT_TASK`;
- mixed-policy CLI next-task constant;
- local research dashboard next-task constant;
- positive core test expectation;
- positive views/status test expectation;
- positive CLI test expectation;
- positive dashboard/research-status test expectation.

The old live route was:

`Historical Replay Mixed STOCK/ETF Universe Profile Policy Tag and Source Readiness Planning Report-Only v0.1`

A read-only assertion required the three live source constants to equal the new route and exited 1 with `AssertionError`. This proved the pre-change implementation had not advanced beyond the completed tag/source phase.

## Hardening Summary

The new live route is:

`Historical Replay Source / Evidence Sufficiency Policy Planning Without Evidence Collection Report-Only v0.1`

Only three live constants changed:

- core metadata/report source constant;
- CLI stdout source constant;
- local research dashboard/research-status source constant.

Four positive test expectations were updated. The previous tag/source route now remains only in four explicit `OLD_*` negative regression constants. Index and status continue to inherit the core constant; no separate logic branch was added.

No artifact filename, row schema, symbol, date, universe, count, status, blocker, safety flag, health rule, or workflow-priority rule changed.

No schema, count-contract, profile-policy status, blocker vocabulary, safety authority, evidence, PIT, replay, model-governance, paper, buy-review, or trading semantics changed.

The authorized change updates live report-only `recommended_next_task` output wording across current surfaces. It does not change business execution behavior or downstream authority.

## Focused Validation Results

| Validation | Result |
| --- | --- |
| Mixed profile core/views/CLI | 19 passed in 7.36s |
| Dashboard/research-status | 382 passed in 291.93s |
| Combined focused suite | 447 passed in 283.17s |
| Full non-slow | Not rerun; accepted record remains 6279 passed, 109 deselected, 5 warnings, 0 failures |

The dashboard suite confirms mixed-profile context remains visible and `PAPER_WORKFLOW_READY` priority preservation is unchanged. The combined suite confirms no adjacent regression in reviewer no-hit or official manual evidence template flows.

## Repo-External Temp-Root CLI Smoke

Five allowed commands ran under a repository-external `%TEMP%` root:

1. core;
2. index;
3. health;
4. status;
5. research-status.

All five exited 0. All 21 generated text artifacts remained under the temp root, and all eight expected core artifacts existed.

The new route was confirmed in:

- core metadata;
- generated core Markdown report;
- core CLI stdout;
- index artifact;
- status artifact;
- status CLI stdout;
- research-status.

The new route appeared in nine generated files. The old route appeared in zero generated files.

Health remained `MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_HEALTH_PASS_REPORT_ONLY` with issue count 0. The isolated research-status result remained the expected report-only `WARN / DATA_PREPARATION_READY`, with mixed-profile context visible.

## Count and Sample Confirmation

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

Seven STOCK rows remain unresolved profile conflicts, and two ETF rows remain context-aligned only. No selected row is accepted.

## Safety and Non-Approval Confirmation

profile_conflict_resolved = no
universe_membership_approved = no
stock_profile_validated = no
official_evidence_collection_started = no
official_evidence_accepted = no
official_evidence_closed = no
pit_admissibility_approved = no
active_replay_input = no
replay_execution_allowed = no
forward_labels_created = no
metric_computation_performed = no
model_training_performed = no
stock_profile_validation_created = no
buy_review_allowed = no
trading_allowed = no
broker_api_called = no
order_placed = no
message_sent = no
data_raw_written = no
data_processed_written = no
data_cache_written = no
docs_project_sources_created = no

The new wording is a planning pointer only. It does not declare evidence sufficient, collect evidence, resolve conflicts, approve membership, validate stock profile, approve PIT, run replay, create labels, compute metrics, train models, or authorize buy-review or trading.

## Current-Task Mode Recommendation

Current task:

- surface: Codex
- environment: Local
- model: GPT-5.6 Sol
- effort: High
- speed: Standard
- task mode: Goal
- primary acceptance artifact:
  - live wording updated across current mixed-profile surfaces;
  - focused tests;
  - repo-external temp-root smoke;
  - old-route and safety scans.
- reason: bounded local repository change whose completion evidence is diff, tests, CLI output, and Git scope proof.
- human approval gate: ChatGPT/user review is required before commit and before the next repository task.

Model strength or effort does not grant additional authority.

## Next-Executable-Task Mode Recommendation

Next executable task:

- task: `Historical Replay Source / Evidence Sufficiency Policy Planning Without Evidence Collection Report-Only v0.1`

ChatGPT recommendation:

- surface: Chat
- model: GPT-5.6 Sol
- ChatGPT mode: Extra High
- speed: Standard

Execution-side recommendation:

- surface: Work only if a formal cross-document governance deliverable is required
- entry: Web
- model: GPT-5.6 Sol
- effort: Extra High or Max
- speed: Standard

- reason: evidence sufficiency is high-risk semantic governance, but it must not collect or accept evidence.
- stop conditions:
  - real evidence collection;
  - official evidence acceptance or closure;
  - profile conflict resolution;
  - universe membership approval;
  - PIT, replay, labels, metrics, model, stock profile, paper, buy-review, or trading authority.

The escalated review mode improves semantic scrutiny only and does not grant authority to collect evidence or advance downstream workflows.

## Commit / Tag / Source Recommendation

Recommended commit message if reviewed and ready:

`Harden historical replay mixed stock ETF universe profile policy post-v1.89 next action wording`

Recommended tag decision:

No tag for this wording hardening. Existing `v1.89.0` remains unchanged.

Recommended Source update decision:

No Source update for this wording hardening. External Project Source remains user-reported at `v1.89.0`.

### Verification Checks

- Full static scan: matches are limited to existing safety guards, negative tests, and historical dashboard/parser contexts.
- Tracked added-line unsafe match count: 0.
- New report unsafe match count: 0.
- Old route in live source: 0; old route remains only in four explicit negative regression constants.
- New route in live source: core, CLI, and dashboard constants; index and status inherit the core value.
- Protected tracked scan: only `data/processed/.gitkeep`, `data/raw/.gitkeep`, and `outputs/reports/.gitkeep`.
- Repository Source-path status: no output; direct directory existence check: false.
- `git diff --check`: clean, with only existing line-ending conversion notices.
- Final describe remains `v1.89.0-2-g4d31477`; no tag points at HEAD and `v1.89.0` remains at `7ca9c4d`.

## Recommended Next Task

`Historical Replay Source / Evidence Sufficiency Policy Planning Without Evidence Collection Report-Only v0.1`
