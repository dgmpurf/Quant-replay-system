# Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Pre-Tag Readiness Wording Hardening Report-Only v0.1

## A. Decision / Status

```text
phase = historical_replay_source_evidence_sufficiency_policy_contract_fixture_pre_tag_readiness_wording_hardening
decision = ready
privacy_issue_stop = no
docs_only = no
wording_hardening_report_created = yes
wording_hardening_performed = yes
source_code_changed = yes
tests_changed = yes
runtime_semantics_changed = no
runtime_output_wording_changed = yes
formal_checkpoint = v1.89.0
formal_checkpoint_commit = 7ca9c4d
formal_checkpoint_tag = v1.89.0
candidate_checkpoint_version = v1.90.0
candidate_checkpoint_approved = no
candidate_tag_exists = no
tag_approved = no
Source_update_approved = no
business_checkpoint_changed = no
current_repo_head = f173710
full_non_slow_validation_commit = f173710
full_non_slow_passed = yes
full_non_slow_passed_count = 6304
full_non_slow_deselected_count = 109
full_non_slow_warning_count = 5
full_non_slow_exit_code = 0
old_live_next_task = Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Checkpoint Documentation Bundle Report-Only v0.1
new_live_next_task = Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Tag And Source Readiness Planning Report-Only v0.1
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
selected_next_route = Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Tag And Source Readiness Planning Report-Only v0.1
```

Decision: the bounded stale pre-tag route is corrected. All live surfaces now point forward to Tag And Source Readiness Planning without changing runtime semantics or authority.

## B. Current Git / Tag / Candidate Checkpoint State

- Start branch: `main`.
- Start HEAD and `origin/main`: `f173710f29f46172dbe2f038d0941437b7b425fc`.
- Parent: `f0a31a112b11cd716269b6e4485d36b882d891fb`.
- Start describe: `v1.89.0-11-gf173710`.
- Initial worktree: clean.
- No tag points at HEAD.
- Formal checkpoint/tag `v1.89.0` remains at `7ca9c4d`.
- Candidate `v1.90.0` remains unapproved and untagged.
- No Source update or business-checkpoint change is approved.
- The accepted full non-slow report is tracked and is the only file in commit `f173710`.

## C. Goal Identity And Acceptance Artifact

Goal:

`Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Pre-Tag Readiness Wording Hardening Report-Only v0.1`

Acceptance artifact:

`docs/historical_replay_source_evidence_sufficiency_policy_contract_fixture_pre_tag_readiness_wording_hardening_v0_1.md`

The previous Full Non-Slow Pre-Tag Validation Goal was not repeated. This Goal changes only live output wording and focused expectations.

## D. Previous Full Non-Slow Result

The accepted formal full-suite evidence remains:

```text
6304 passed, 109 deselected, 5 warnings in 1487.84s (0:24:47)
exit_code = 0
failed = 0
errors = 0
```

Commit `f173710` records that result. All five warnings remain the already reviewed known, non-blocking existing warning inventory. Full non-slow was not rerun because this one-string wording change does not alter test or runtime semantics.

## E. Old And New Live Next-Task Contract

Old completed route:

`Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Checkpoint Documentation Bundle Report-Only v0.1`

Required forward route:

`Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Tag And Source Readiness Planning Report-Only v0.1`

The single owner is `RECOMMENDED_NEXT_TASK` in the core fixture module. Core metadata and Markdown use it directly; index, status, CLI, and research-status/dashboard inherit it. No other production module contains an independent route value.

## F. Files Inspected

Read-only evidence included the design, generated-artifact review, earlier wording-hardening report, candidate checkpoint, checkpoint commit review, full non-slow validation report, formal v1.89 checkpoint, core/index/health/status/CLI/dashboard implementation, and four focused tests.

Inspected but unmodified production modules:

- Index.
- Health.
- Status.
- CLI.
- Local research dashboard.

All existing documentation remained unmodified.

## G. TDD RED Evidence

Tests were changed before production source. They required the new route and rejected the completed checkpoint-documentation route.

Command:

```powershell
$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest tests/test_historical_replay_source_evidence_sufficiency_policy_contract_fixture.py tests/test_historical_replay_source_evidence_sufficiency_policy_contract_fixture_views.py tests/test_historical_replay_source_evidence_sufficiency_policy_contract_fixture_cli.py tests/test_local_research_dashboard.py -q
```

Result:

```text
6 failed, 401 passed in 320.56s (0:05:20)
exit_code = 1
```

The six failures covered core metadata, index, status, core CLI, status CLI, and research-status CLI. Every failure was exactly `Checkpoint Documentation Bundle` versus `Tag And Source Readiness Planning`. There were no unrelated failures.

## H. Minimal Source And Test Changes

Production:

- Changed only the value of `RECOMMENDED_NEXT_TASK` in `src/quant_replay_system/historical_replay_source_evidence_sufficiency_policy_contract_fixture.py`.

Tests:

- Core metadata expects the new route and rejects the old route.
- Index/status views expect the inherited new route and reject the old route.
- Core/status CLI output expects the new route and rejects the old route.
- Research-status output expects the new route and rejects the old route.

No schema, field, artifact, count, format, CLI argument, path, health, research-status transformation, priority, privacy, or authority behavior changed.

## I. Preserved Contract

- Decision date `2024-04-02`, timezone `Asia/Shanghai`, legacy universe `etf_core`.
- Ordered symbols `000001`, `000002`, `159915`, `300750`, `510300`, `600000`, `600519`, `601318`, `688981`.
- 9 rows: 7 STOCK and 2 ETF.
- 7 profile conflicts, 2 aligned contexts, 7 unresolved conflicts, and 9 selected rows with blockers.
- 17 evidence families, 153 row-family contracts, 144 applicable rows, and 9 explicit instrument-not-applicable contexts.
- 10 artifacts, 15 selected-row fields, 30 family-contract fields, and 45 required-field rows.
- 17 statuses, 28 blockers, 18 timing/revision rules, and 4 STOCK/ETF matrix rows.
- 0 sufficiency candidates, accepted evidence, closed evidence, PIT-admissible rows, replay-ready rows, and safety true states.

Semantic separation remains:

`source eligibility != evidence presence != evidence sufficiency candidate != evidence acceptance != evidence closure != PIT admissibility != replay readiness`

Health PASS/WARN/FAIL behavior, output-root guards, relative references, leading-zero handling, and every negative-proof field remain unchanged.

## J. Focused GREEN Validation

All commands used `PYTHONPATH=src` and the repository virtual environment.

| Scope | Result | Duration | Exit |
|---|---|---:|---:|
| Core | 10 passed; 0 failed/skipped/deselected; 0 warnings | 0.45s | 0 |
| Views | 6 passed; 0 failed/skipped/deselected; 0 warnings | 0.54s | 0 |
| CLI | 7 passed; 0 failed/skipped/deselected; 0 warnings | 6.49s | 0 |
| Dashboard | 384 passed; 0 failed/skipped/deselected; 0 warnings | 259.09s | 0 |
| Combined focused | 407 passed; 0 failed/skipped/deselected; 0 warnings | 264.31s | 0 |

Full non-slow was not rerun. The accepted `6304 / 109 / 5` evidence remains the formal full-suite gate.

## K. Fresh Temp-Root CLI Smoke

One fresh repository-external root was used. Sanitized label:

`qr_source_evidence_pre_tag_wording_b065eaefbbaa`

| Command | Exit | Result |
|---|---:|---|
| Core fixture | 0 | Exactly ten core artifacts |
| Index | 0 | Output exists |
| Health | 0 | PASS; issue count 0 |
| Status | 0 | Output exists; new route visible |
| Research status | 0 | Fixture context and new route visible |

All exact counts and ordered symbols matched Section I. The old route had zero matches in the 29 temporary files. The new route appeared in core metadata/Markdown, index metadata/CSV, status metadata/CSV/Markdown, research-status metadata/CSV, and core/status/research CLI logs.

The isolated research-status stage remained benign `WARN / DATA_PREPARATION_READY` because no paper artifact was supplied. Focused tests preserve `PAPER_WORKFLOW_READY` when paper context exists.

No repository output, protected directory, or Project Source file was created.

## L. Live Route Scan

After hardening:

- Production old-route matches: 0.
- Fresh generated old-route matches: 0.
- Authorized-test old-route matches: 4, all explicit negative regression expectations.
- Production new-route matches: the single owning core constant.
- Test new-route matches: core, views, CLI, and research-status expectations.
- Fresh generated new-route matches: all 13 expected exposing files/logs.

No stale live value remains.

## M. Privacy / Safety / Disclosure Review

The changed diff has zero unsafe affirmative-state matches and zero disclosure-pattern matches. Fresh artifacts had zero private absolute-path, full-hash, sensitive-assignment, source-payload, source-byte, or real-CSV-content matches.

No runtime surface creates or claims evidence collection, sufficiency assignment, acceptance, closure, PIT approval, active replay input, replay execution, labels, metrics, model/threshold promotion, stock-profile validation, paper expansion, buy-review, external calls, broker/order/message/trading, current-candidates, snapshots, signal-semantics mutation, or protected writes.

## N. Protected / Project-Source / Repository-Output Checks

Protected tracked inventory remains:

```text
data/processed/.gitkeep
data/raw/.gitkeep
outputs/reports/.gitkeep
```

Project Source tracked/status scans are empty. Fresh outputs remained outside the repository. Pre-report `git diff --check` exited 0.

Final checks after report creation confirm:

- Report hygiene, unsafe-affirmative, and disclosure matches are all 0.
- Route text identifies the old route only as historical/negative context and selects the new forward route.
- Final Git scope is exactly one core production file, four focused tests, and this untracked report.
- The tracked diff is 20 insertions and 16 deletions across the five authorized tracked files.
- `git diff --check` exits 0; line-ending advisories are non-blocking workspace normalization notices.
- HEAD and `origin/main` remain `f173710f29f46172dbe2f038d0941437b7b425fc`; parent remains `f0a31a112b11cd716269b6e4485d36b882d891fb`.
- Describe remains `v1.89.0-11-gf173710`; no tag points at HEAD; `v1.89.0` remains at `7ca9c4d`; `v1.90.0` remains absent.

## O. Full Non-Slow Evidence Preservation

The change is one output-string constant plus focused expectations. It does not alter executable semantics, schemas, health, or authority. Therefore the accepted full-suite evidence remains valid and was not repeated:

```text
passed = 6304
failed = 0
errors = 0
deselected = 109
warnings = 5
exit_code = 0
duration_seconds = 1487.84
```

## P. Candidate Next Routes

| Route | Decision | Reason |
|---|---|---|
| A. Tag And Source Readiness Planning Report-Only v0.1 | selected | Live wording is coherent; RED/GREEN, smoke, contracts, privacy, and safety pass. |
| B. Additional Pre-Tag Wording Hardening Report-Only v0.1 | not selected | No live wording issue remains. |
| C. Implementation Corrective Milestone Bundle Report-Only v0.1 | not selected | No implementation defect was found. |
| D. Validation Report Hardening Report-Only v0.1 | not selected | The committed validation report remains accurate. |
| E. Pause for manual official evidence research | not selected | Safe tag/source readiness planning is available. |

## Q. Selected Next Route

Exactly one route is selected:

`Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Tag And Source Readiness Planning Report-Only v0.1`

The route is not executed in this Goal.

## R. Current / Next Mode Recommendation

Current and next task mode:

```text
surface = Codex
environment = Local
model = GPT-5.6 Sol
effort = High
speed = Standard
task mode = Goal
```

The next Goal must identify this Pre-Tag Readiness Wording Hardening Goal as the previous Goal that must not be repeated.

## S. Commit / Tag / Source Recommendation

- Commit recommendation after ChatGPT/user review: `Harden historical replay source evidence sufficiency policy contract fixture pre-tag readiness wording`.
- Tag recommendation: no tag in this Goal.
- Source recommendation: no Source update in this Goal.
- Tag And Source Readiness Planning is the separate selected next route.
- The approved Master Plan freeze proposal remains deferred. No Master Plan baseline file is created before manual `v1.90.0` tagging, external Source update, and separate explicit approval.

## T. Final Classification And Verdict

Final classification:

`HISTORICAL_REPLAY_SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_PRE_TAG_READINESS_WORDING_HARDENED_REPORT_ONLY`

Final verdict:

`HISTORICAL_REPLAY_SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_READY_FOR_TAG_AND_SOURCE_READINESS_PLANNING_REPORT_ONLY`

This hardening is complete, bounded, and non-authorizing.
