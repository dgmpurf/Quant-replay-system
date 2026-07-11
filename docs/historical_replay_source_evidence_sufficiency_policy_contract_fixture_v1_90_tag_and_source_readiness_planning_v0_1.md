# Historical Replay Source / Evidence Sufficiency Policy Contract Fixture v1.90 Tag And Source Readiness Planning Report-Only v0.1

## A. Decision / Status

```text
phase = historical_replay_source_evidence_sufficiency_policy_contract_fixture_v1_90_tag_and_source_readiness_planning
decision = ready
privacy_issue_stop = no
docs_only = yes
readiness_planning_report_created = yes

formal_checkpoint = v1.89.0
formal_checkpoint_commit = 7ca9c4d
formal_checkpoint_tag = v1.89.0

candidate_checkpoint_version = v1.90.0
candidate_chain_complete = yes
candidate_checkpoint_approved = no
candidate_tag_exists = no
candidate_tag_approved = no
Source_update_completed = no
Source_update_approved = no
business_checkpoint_changed = no

current_pre_report_head = dc49241
current_pre_report_head_is_final_tag_target = no
future_tag_target = future accepted commit containing this readiness-planning report
manual_tag_name = v1.90.0
manual_tag_created = no
manual_tag_pushed = no
manual_tag_ready_after_report_commit_and_separate_approval = yes

full_non_slow_passed = yes
full_non_slow_passed_count = 6304
full_non_slow_failed_count = 0
full_non_slow_error_count = 0
full_non_slow_deselected_count = 109
full_non_slow_warning_count = 5
full_non_slow_exit_code = 0

live_next_task_wording_coherent = yes

row_count = 9
stock_row_count = 7
etf_row_count = 2
evidence_family_count = 17
row_evidence_family_contract_count = 153
applicable_contract_row_count = 144
instrument_not_applicable_context_row_count = 9
core_artifact_count = 10
required_field_row_count = 45
status_vocabulary_count = 17
blocker_vocabulary_count = 28
timing_revision_rule_count = 18

sufficiency_candidate_count = 0
evidence_accepted_count = 0
evidence_closed_count = 0
pit_admissible_count = 0
replay_ready_count = 0
safety_true_count = 0

external_source_update_ready_after_verified_tag = yes
master_plan_freeze_approved_but_deferred = yes
master_plan_created = no

selected_next_route = Manual v1.90.0 Tag Creation After Readiness Planning Commit
```

Decision: the candidate `v1.90.0` chain is complete and coherent for review and commit of this report. After that future report commit is pushed and separately approved, the chain is ready for a user-controlled manual tag action. This report neither creates nor approves a tag, Source update, Master Plan, business checkpoint change, or downstream research authority.

## B. Current Git / Tag / Formal And Candidate Checkpoint State

Preflight was completed before this file was created.

| Item | Verified state |
|---|---|
| Branch | `main` |
| Initial worktree | clean; `## main...origin/main` |
| HEAD | `dc492415b144e4db4f907f434ce74a3e32864e07` |
| `origin/main` | `dc492415b144e4db4f907f434ce74a3e32864e07` |
| HEAD parent | `f173710f29f46172dbe2f038d0941437b7b425fc` |
| Describe | `v1.89.0-12-gdc49241` |
| Tag at HEAD | none |
| Formal checkpoint | `v1.89.0` at `7ca9c4d` |
| Candidate tag | local `v1.90.0` absent |
| Project Source repository path | untracked and tracked scans empty |

The formal checkpoint remains `v1.89.0`. Candidate `v1.90.0` is not formal, approved, tagged, pushed, or Source-updated. The repository business checkpoint therefore has not changed.

The current task does not query a remote tag server. Absence of local `v1.90.0` is verified now; a fresh local-and-remote non-duplication check is mandatory in the separately approved manual tag step.

## C. Goal Identity And Acceptance Artifact

Goal identity:

`Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Tag And Source Readiness Planning Report-Only v0.1`

Required acceptance artifact:

`docs/historical_replay_source_evidence_sufficiency_policy_contract_fixture_v1_90_tag_and_source_readiness_planning_v0_1.md`

This Goal is docs-only, report-only, planning-only, local, and non-authorizing. It audits committed evidence. It does not rerun tests or smoke, create a tag, generate a Project Source package, create a Master Plan, collect evidence, or execute any downstream workflow.

The previous Pre-Tag Readiness Wording Hardening Goal is evidence for this report and was not repeated.

## D. Candidate v1.90.0 Checkpoint Chain Audit

The chain is linear from the formal post-`v1.89.0` working state through the current pre-report HEAD.

| Commit | Milestone | Audit result |
|---|---|---|
| `cef7cdf` | Source / Evidence Sufficiency Policy Planning Without Evidence Collection | Tracked one planning report; established the report-only, no-collection boundary. |
| `d78dc9c` | Contract Fixture Design | Tracked one design report; defined the schema, counts, statuses, blockers, timing/revision rules, and negative authority contract. |
| `ee3876f` | Core / Views / CLI / Research-Status Milestone Bundle | Added the bounded fixture modules and focused tests; integrated CLI and dashboard context without downstream authority. |
| `8dd2001` | Generated Artifact Review | Tracked one review report; accepted artifacts and identified only a bounded next-task wording issue. |
| `81866c8` | Artifact / Next-Task Wording Hardening | Added its report and changed one owning route plus focused expectations; no contract semantics changed. |
| `9ce9da5` | Candidate `v1.90.0` Checkpoint Documentation | Added only `docs/release_checkpoint_v1.90.0.md`; retained candidate-only status. |
| `f0a31a1` | Checkpoint Commit Review | Added only the commit-review report; reconciled checkpoint scope and selected full non-slow validation. |
| `f173710` | Full Non-Slow Pre-Tag Validation | Added only the committed validation report recording the authoritative `6304 / 109 / 5` result. |
| `dc49241` | Pre-Tag Readiness Wording Hardening | Added its report and advanced one owning live route plus four focused expectations to this Goal. |

All parent links are consecutive. Every chain commit inspected with `git show --check` passed. No required gate is missing. No later commit reverses the synthetic, report-only, diagnostic, non-authorizing contract.

Checkpoint documentation remains candidate-only. Full non-slow evidence is committed. Live wording now points forward to this readiness Goal. No additional pre-tag validation or wording hardening is required on the evidence currently available.

## E. Commit Scope And Cleanliness Review

| Commit | Scope summary | Cleanliness |
|---|---|---|
| `cef7cdf` | 1 planning document; 479 insertions | `git show --check` passed |
| `d78dc9c` | 1 design document; 747 insertions | `git show --check` passed |
| `ee3876f` | 10 implementation/test files; 3460 insertions | `git show --check` passed |
| `8dd2001` | 1 generated-artifact review; 492 insertions | `git show --check` passed |
| `81866c8` | 6 report/source/test files; 372 insertions, 2 deletions | `git show --check` passed |
| `9ce9da5` | 1 checkpoint document; 404 insertions | `git show --check` passed |
| `f0a31a1` | 1 commit-review document; 307 insertions | `git show --check` passed |
| `f173710` | 1 validation document; 330 insertions | `git show --check` passed |
| `dc49241` | 6 report/source/test files; 333 insertions, 16 deletions | `git show --check` passed |

The exact accepted `dc49241` scope is:

- added the pre-tag wording-hardening report;
- modified the single owning core fixture route;
- modified the core, views, CLI, and dashboard focused expectations.

No configuration, dependency, data, generated output, Project Source, checkpoint document, or unrelated runtime file entered `dc49241`. Initial `git diff --check` passed.

## F. Contract Counts And Semantic Review

The committed chain continues to record:

```text
historical_decision_date = 2024-04-02
decision_timezone = Asia/Shanghai
legacy_universe_label = etf_core

row_count = 9
stock_row_count = 7
etf_row_count = 2
profile_conflict_count = 7
profile_aligned_context_count = 2
unresolved_profile_conflict_count = 7
selected_row_with_blocker_count = 9

evidence_family_count = 17
row_evidence_family_contract_count = 153
applicable_contract_row_count = 144
instrument_not_applicable_context_row_count = 9

core_artifact_count = 10
selected_row_required_field_count = 15
evidence_family_contract_field_count = 30
required_field_row_count = 45
status_vocabulary_count = 17
blocker_vocabulary_count = 28
timing_revision_rule_count = 18
stock_etf_applicability_matrix_row_count = 4

sufficiency_candidate_count = 0
evidence_accepted_count = 0
evidence_closed_count = 0
pit_admissible_count = 0
replay_ready_count = 0
safety_true_count = 0
```

The nine selected symbols remain string identifiers, preserving leading zeroes. Seven STOCK rows remain unresolved profile conflicts and two ETF rows remain aligned context only. Every selected row retains blockers.

The controlling semantic separation remains unchanged:

`source eligibility != evidence presence != evidence sufficiency candidate != evidence acceptance != evidence closure != PIT admissibility != replay readiness`

Definitions, vocabulary, or aligned context do not create a candidate, acceptance, closure, PIT decision, replay permission, or downstream authority.

## G. Full Non-Slow And Warning Evidence Review

The authoritative committed result from `f173710` is:

```text
6304 passed, 109 deselected, 5 warnings in 1487.84s (0:24:47)
failed = 0
errors = 0
skipped reported = 0
exit_code = 0
```

The five warnings are the already reviewed and visible existing inventory:

1. Two pandas invalid-date inference warnings in negative date-validation tests.
2. Three pandas future incompatible-dtype assignment warnings in negative fixture mutations.

All five originating tests passed, the process exited 0, and no runtime semantic failure was found. They are known, non-blocking existing warnings. This classification is not a zero-warning claim and does not hide or suppress them.

The subsequent one-string pre-tag route hardening used TDD evidence:

- RED: 6 failed and 401 passed, with all six failures limited to old-versus-new route wording.
- GREEN core: 10 passed.
- GREEN views: 6 passed.
- GREEN CLI: 7 passed.
- GREEN dashboard: 384 passed.
- GREEN combined: 407 passed.
- GREEN failures and warnings: 0.

Its fresh temp-root smoke had five zero exit codes, ten core artifacts, health PASS, zero health issues, the new route visible, and zero old generated-route matches. Because that change altered one string and no semantics, full non-slow was not rerun. The accepted `6304 / 109 / 5` evidence remains the formal full-suite gate.

No test or smoke command is rerun by this planning Goal.

## H. Pre-Tag Wording And Live-Route Review

Current live recommended next task:

`Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Tag And Source Readiness Planning Report-Only v0.1`

The single production owner is `RECOMMENDED_NEXT_TASK` in the core fixture module. Core metadata and Markdown use it directly; index, status, CLI, and research-status/dashboard inherit it.

Read-only scan results:

- new route in production: one owning constant;
- new route in focused tests: positive core, views, CLI, and dashboard expectations;
- old Checkpoint Documentation Bundle route in production: zero;
- old route in focused tests: four explicit negative regression assertions.

Historical documentation may accurately describe the route that existed at its own checkpoint. Negative regression references are intentional. No stale live route remains, and no additional wording hardening is required before this report is reviewed for commit.

## I. Tag Readiness Decision

```text
tag_readiness_decision = ready_after_report_review_commit_push_and_separate_manual_authorization
current_pre_report_head = dc49241
current_pre_report_head_is_final_tag_target = no
manual_tag_name = v1.90.0
manual_tag_creation_in_this_goal = no
manual_tag_push_in_this_goal = no
manual_tag_approval_in_this_goal = no
```

The candidate chain is ready for a later user-controlled manual tag action only after this report becomes part of an accepted commit. Readiness is a repository-governance conclusion, not tag approval and not business authority.

## J. Future Tag-Target Rule

The future manual `v1.90.0` tag must point to:

`the future accepted commit that commits this readiness-planning report`

It must not point to the pre-report HEAD `dc49241` merely because that commit was current during preflight. The readiness report is the final governance record for tag timing, Source sequencing, validation reconciliation, and non-approval boundaries; omitting it from the tag target would exclude the tag's own readiness decision.

The future commit hash does not yet exist and is not manufactured here. The only valid placeholder is:

`<READINESS_REPORT_COMMIT_FULL_HASH>`

## K. Future Manual Tag And Verification Plan

Manual tag creation becomes eligible only after all of these conditions hold:

1. ChatGPT and the user accept this report.
2. This report is committed and pushed without unrelated scope.
3. The worktree is clean.
4. `HEAD` equals `origin/main`.
5. The committed HEAD contains this exact report.
6. No local or remote `v1.90.0` tag exists.
7. `v1.89.0` remains unchanged at `7ca9c4d`.
8. The user separately authorizes manual tag creation.

Future command template, for user-controlled review only:

```text
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
git tag --list v1.90.0
git ls-remote --tags origin refs/tags/v1.90.0 refs/tags/v1.90.0^{}
git tag -a v1.90.0 <READINESS_REPORT_COMMIT_FULL_HASH> -m "v1.90.0"
git rev-parse v1.90.0^{}
git push origin v1.90.0
git ls-remote --tags origin refs/tags/v1.90.0 refs/tags/v1.90.0^{}
```

Local verification must prove that the annotated tag resolves to the exact readiness-report commit. Remote verification after push must prove that the remote peeled target is the same commit.

If any prerequisite differs, the manual operator must stop. Do not overwrite, force-update, duplicate, delete, or move an existing tag as an automatic repair. Any rollback or tag correction requires a separate explicit review because published tag history is governance evidence.

No command in the template is executed by this Goal.

## L. External Project Source Update Readiness Plan

No Project Source file or package is created or approved here. External Source update work may begin only after:

1. `v1.90.0` is manually created at the readiness-report commit.
2. The tag is pushed.
3. Local and remote tag targets are verified equal.
4. The repository remains clean.
5. A separate external Project Source update task is approved.

The minimum external update must record:

### Formal checkpoint transition

- previous formal checkpoint `v1.89.0` at `7ca9c4d`;
- new formal checkpoint `v1.90.0`;
- the exact future readiness-report/tag-target commit;
- verified local and remote annotated tag targets.

### Completed v1.90.0 chain

- planning;
- contract fixture design;
- core/views/CLI/research-status implementation;
- generated artifact review;
- artifact/next-task wording hardening;
- candidate checkpoint documentation;
- checkpoint commit review;
- full non-slow pre-tag validation;
- pre-tag readiness wording hardening;
- this tag/source readiness planning report.

### Contract meaning

- 9 selected rows split into 7 STOCK and 2 ETF;
- 17 families, 153 row-family contracts, 144 applicable contracts, and 9 explicit not-applicable contexts;
- ten core artifacts;
- all candidate, acceptance, closure, PIT, replay, and safety authority counts remain zero;
- the seven-step semantic separation remains unchanged.

### Validation evidence

- 6304 passed;
- 109 deselected;
- five known non-blocking existing warnings;
- focused wording GREEN of 407 passed;
- no additional full-suite run after the one-string wording hardening.

### Governance

- no evidence acceptance or closure;
- no PIT approval, active replay input, replay execution, or freeze;
- no labels, metrics, models, stock_profile validation, paper expansion, real buy-review, broker, orders, messages, APIs, or trading;
- the external update records state but does not expand business authority.

### Continuity

- latest textual Git output remains authoritative for repository facts;
- the old post-`v1.89.0` overlay becomes historical after the `v1.90.0` Source update;
- a post-`v1.90.0` current-state anchor must be explicit;
- no Source file may claim that the approved Master Plan baseline already exists.

The update must remain an external curated Source operation. It must not recreate `docs/project_sources` or copy a Project Source mirror into Git.

## M. Required Versus Conditional Source-Control Updates

Exact external filenames and replacement rules must be confirmed against the live external Source set in the later post-tag task. The following control categories are the minimum planning scope.

| Source control category | Planned disposition | Minimum content |
|---|---|---|
| Project master control | required update | Formal `v1.90.0` anchor, exact tag-target commit, and unchanged authority boundary. |
| Roadmap and next decision points | required update | Completed candidate chain, verified checkpoint transition, and approved-but-deferred Master Plan freeze timing. |
| Current state snapshot | required update | Exact Git/tag facts, contract counts, validation evidence, zero-authority state, and current next decision. |
| Project Source index | required update | Active Source set, replacements, and retirement of the old post-`v1.89.0` overlay as current context. |
| Latest checkpoint/update notes | required update | `v1.90.0` checkpoint meaning, complete chain, validation, tag verification, and non-approval statements. |
| Update manifest | required update | Upload/replace list, unchanged files, retired historical overlay, and active set after update. |
| Post-checkpoint working-state overlay | conditional | Create or replace only if current Source governance requires an overlay after the formal anchor. |
| Checkpoint/artifact governance control | conditional | Update only if the active Source copy must record a new checkpoint-specific governance rule. |
| Codex operating protocol | conditional | Update only if accepted operating protocol changed; this chain does not itself change it. |
| Dedicated fixture summary | conditional | Add only if the external Source taxonomy requires a concise checkpoint-specific reference. |

No repository runtime source, tests, generated outputs, raw data, private evidence, or full repository diff belongs in the external curated Source upload.

## N. Master Plan Freeze Deferral

The task-provided governance proposal remains approved but deferred:

```text
proposal = APPROVE_QUANT_V1_MASTER_PLAN_FREEZE_POST_V1_90_V0_1
freeze_timing = AFTER_V1_90_TAG_AND_SOURCE_UPDATE
V1_completion_boundary = STAGE_8
full_roadmap_boundary = STAGE_11
freeze_granularity = STAGE_5_TO_8_WORK_PACKAGE_LEVEL
stages_9_to_11 = DEFERRED_EPICS

repo_change_for_master_plan_now = no
Source_change_for_master_plan_now = no
master_plan_created_now = no
```

`QUANT_MASTER_PLAN_BASELINE_V1_0.md` is not created. Master Plan creation becomes eligible only after:

1. `v1.90.0` is created, pushed, and locally/remotely verified.
2. The external Project Source update is completed.
3. A separate Master Plan creation Goal is explicitly approved.

This report does not convert an approved future governance proposal into a present repository or Source artifact.

## O. Privacy / Disclosure / Safety Review

This report contains no private reviewer identity, secret, credential, bearer value, API key, private Windows absolute path, source payload, source bytes, real CSV content, evidence content, full private source hash, or unsafe local path.

Git commit IDs are required repository audit evidence. They are not source-artifact hashes and must not be misclassified as private source-hash disclosure.

All non-approval boundaries remain no or false:

- real evidence collection, external evidence reading, template filling, sufficiency assignment, acceptance, or closure;
- no-hit acceptance as evidence, profile-conflict resolution, universe-membership approval, or stock_profile validation;
- PIT admissibility, active replay input, replay execution, replay freeze, or forward labels;
- metric computation outside tests, model training/promotion, active weights, or threshold adjustment;
- paper expansion, real buy-review, `buy_review_allowed`, performance validation, or trading;
- broker/API calls, order placement, message delivery, current-candidates execution, snapshot build, or signal-semantics mutation;
- writes to protected data paths or creation of `docs/project_sources`.

Tag readiness, tag creation, and Source update are repository-state operations only. None is evidence sufficiency, PIT admissibility, replay readiness, or financial authorization.

## P. Protected / Project-Source / Git Checks

Pre-report checks passed:

- clean `main` worktree at `dc49241`;
- `HEAD == origin/main`;
- no tag at HEAD;
- `v1.89.0` unchanged at `7ca9c4d`;
- local `v1.90.0` absent;
- all four required terminal checkpoint-chain documents tracked;
- all audited chain commits passed `git show --check`;
- initial `git diff --check` passed;
- tracked and status scans for `docs/project_sources` were empty;
- `QUANT_MASTER_PLAN_BASELINE_V1_0.md` was absent.

Protected tracked inventory is limited to:

```text
data/processed/.gitkeep
data/raw/.gitkeep
outputs/reports/.gitkeep
```

Final direct checks are recorded after this report is created. The expected final state is one untracked readiness report, no tracked modifications, unchanged HEAD/origin/tag state, empty Project Source scans, and a clean report static scan.

Observed final direct checks:

- the acceptance artifact exists, is non-empty, and contains every required Section A through U;
- direct report scan found zero trailing-whitespace, unfinished-marker, private Windows path, sensitive-assignment, 64-character private-hash, unsafe affirmative checkpoint/tag/Source/Master-Plan, or obsolete model-name matches;
- `git status --short --branch` showed `main...origin/main` plus exactly this one untracked report;
- `git diff --name-status` and `git diff --stat` were empty because no tracked file changed;
- final `git diff --check` passed;
- describe remained `v1.89.0-12-gdc49241`;
- `HEAD` and `origin/main` remained equal to `dc492415b144e4db4f907f434ce74a3e32864e07`;
- no tag pointed at HEAD, `v1.89.0` remained at `7ca9c4d`, and local `v1.90.0` remained absent;
- protected tracked inventory remained exactly the three placeholders;
- tracked and status scans for `docs/project_sources` remained empty;
- no Master Plan baseline file existed;
- no tests or smoke were rerun.

## Q. Candidate Next Routes

| Route | Decision | Reason |
|---|---|---|
| A. Manual v1.90.0 Tag Creation After Readiness Planning Commit | selected | The chain, committed validation, live wording, tag-target rule, Source timing, privacy, safety, and Git state are coherent. |
| B. Tag And Source Readiness Planning Hardening Report-Only v0.1 | not selected | No bounded defect in this report is known after direct checks. |
| C. Additional Pre-Tag Validation Report-Only v0.1 | not selected | The committed full-suite and focused wording evidence are complete and reconciled. |
| D. External Project Source Update Before Tag | prohibited | Source update must follow creation, push, and verification of the manual tag. |
| E. Defer v1.90.0 And Continue Repository Mainline | not selected | No concrete readiness blocker justifies bypassing the checkpoint transition. |
| F. Pause Repository Work And Investigate A Concrete Readiness Inconsistency | not selected | No unresolved inconsistency was found. |

Exactly one route is selected and is not executed in this Goal.

## R. Selected Next Route

`Manual v1.90.0 Tag Creation After Readiness Planning Commit`

This means human review first, then report commit and push, then a separate manual authorization. It does not authorize Codex to create or push the tag now.

## S. Current / Next Mode Recommendation

Current task:

```text
surface = Codex
environment = Local
model = GPT-5.6 Sol
effort = High
speed = Standard
task mode = Goal
```

Expected next action after a clean report, human review, and report commit:

```text
surface = ChatGPT/user-controlled manual Git
action = create and push annotated v1.90.0 tag at the future readiness-report commit
Codex task = none unless separately authorized
```

## T. Commit / Tag / Source Recommendation

Recommended report commit message after ChatGPT/user acceptance:

`docs: plan historical replay source evidence sufficiency policy contract fixture v1.90 tag and source readiness`

Tag recommendation:

No tag in this Goal. A separately authorized manual `v1.90.0` tag may be created only at the future accepted readiness-report commit after all Section K prerequisites pass.

Source recommendation:

No Source update in this Goal. Plan and execute a curated external update only after the manual tag is pushed and locally/remotely verified.

Master Plan recommendation:

No Master Plan creation in this Goal. Preserve the approved freeze proposal as deferred until after verified tag and external Source update.

## U. Final Classification And Verdict

Final classification:

`HISTORICAL_REPLAY_SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_V1_90_TAG_AND_SOURCE_READINESS_PLANNING_CREATED_REPORT_ONLY`

Final verdict:

`HISTORICAL_REPLAY_SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_V1_90_READY_FOR_MANUAL_TAG_CREATION_AFTER_READINESS_PLANNING_COMMIT_REPORT_ONLY`

The acceptance artifact exists and the candidate chain is planning-ready for the selected manual route after human review and report commit. Candidate `v1.90.0` remains unapproved and untagged in this Goal. No Project Source update, Master Plan, evidence action, PIT/replay authority, model/paper/buy-review authority, or trading authority is created.
