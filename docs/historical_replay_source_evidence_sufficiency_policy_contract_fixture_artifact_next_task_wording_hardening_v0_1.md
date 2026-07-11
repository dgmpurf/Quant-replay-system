# Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Artifact / Next-Task Wording Hardening Report-Only v0.1

## A. Decision / Status

```text
phase = historical_replay_source_evidence_sufficiency_policy_contract_fixture_artifact_next_task_wording_hardening
decision = ready
privacy_issue_stop = no
docs_only = no
wording_hardening_report_created = yes
wording_hardening_performed = yes
source_code_changed = yes
tests_changed = yes
runtime_semantics_changed = no
runtime_output_wording_changed = yes
current_checkpoint = v1.89.0
current_checkpoint_commit = 7ca9c4d
current_checkpoint_tag = v1.89.0
current_repo_head = 8dd2001
implementation_commit = ee3876f
generated_artifact_review_commit = 8dd2001
business_checkpoint_changed = no
old_live_next_task = Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Generated Artifact Review Report-Only v0.1
new_live_next_task = Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Checkpoint Documentation Bundle Report-Only v0.1
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
selected_next_route = Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Checkpoint Documentation Bundle Report-Only v0.1
```

Required non-approval fields remain false/no:

```text
official_source_hierarchy_approved = no
official_evidence_collection_started = no
evidence_read_from_external_sources = no
evidence_template_filled = no
evidence_sufficiency_applied_to_selected_rows = no
evidence_accepted = false
evidence_closed = false
no_hit_accepted_as_evidence = no
profile_conflict_resolved = no
universe_membership_approved = no
stock_profile_validated = no
pit_admissibility_approved = no
active_replay_input_approved = no
replay_execution_approved = no
replay_decision_freeze_approved = no
forward_labels_created = false
metric_computation_approved = no
model_training_approved = no
paper_expansion_approved = no
real_buy_review_approved = no
buy_review_allowed = false
broker_api_approved = no
order_placement_approved = no
message_delivery_approved = no
trading_allowed = false
external_api_or_llm_approved = no
current_candidates_execution_approved = no
snapshot_build_approved = no
signal_semantics_mutation_approved = no
data_raw_processed_cache_writes_approved = no
docs_project_sources_created = false
```

Decision: the bounded wording issue is fixed. The fixture remains synthetic, report-only, local-only, diagnostic-only, and non-authorizing.

## B. Current Git / Tag / External Source State

- Preflight branch: `main`.
- Initial worktree: clean and synchronized as `main...origin/main`.
- HEAD and `origin/main`: `8dd2001cad2e4a83188ef51630829c340b8666b2`.
- Initial describe: `v1.89.0-7-g8dd2001`.
- No tag points at HEAD.
- Formal checkpoint tag `v1.89.0` remains at `7ca9c4d`.
- Candidate tag `v1.90.0` does not exist.
- `8dd2001` contains exactly the accepted generated-artifact review report.
- `git show --check 8dd2001` and preflight `git diff --check` exited 0.
- The normative design and generated-artifact review are tracked.
- No Project Source package or Source update was created. The formal external Source/checkpoint anchor is unchanged by this task.

## C. Goal Identity And Acceptance Artifact

Goal executed:

`Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Artifact / Next-Task Wording Hardening Report-Only v0.1`

Acceptance artifact:

`docs/historical_replay_source_evidence_sufficiency_policy_contract_fixture_artifact_next_task_wording_hardening_v0_1.md`

The previous Generated Artifact Review Goal was not repeated. Completion required a test-first wording change, focused GREEN validation, and a fresh external-temp smoke.

## D. Previous Generated-Artifact Review Finding

The accepted review at `8dd2001` found that the fixture was coherent and safe, but its live next-task value pointed to the review that had just completed. That made the value self-referential rather than forward-looking. The review classified this as a bounded wording/governance issue, not a schema, safety, health, or implementation-semantics defect.

## E. Old And New Live Next-Task Contract

Old completed route:

`Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Generated Artifact Review Report-Only v0.1`

Required forward route:

`Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Checkpoint Documentation Bundle Report-Only v0.1`

The single owning constant is `RECOMMENDED_NEXT_TASK` in the core fixture module. Core metadata and Markdown use it directly; index, status, CLI, and research-status/dashboard inherit it. Index and health CLI output continue to omit the field where that omission is intentional.

## F. Files Inspected

Governance evidence inspected:

- `docs/historical_replay_source_evidence_sufficiency_policy_contract_fixture_design_v0_1.md`
- `docs/historical_replay_source_evidence_sufficiency_policy_contract_fixture_generated_artifact_review_v0_1.md`
- `docs/release_checkpoint_v1.89.0.md`
- Relevant prior wording-hardening reports for the mixed STOCK/ETF, manual evidence template, and post-checkpoint routes.

Implementation inspected:

- Core fixture, index, health, status, CLI, and local research dashboard modules.
- Focused core, views, CLI, and dashboard tests.

Only the owning core module and four focused test files were modified. Index, health, status, CLI, and dashboard production modules were inspected but not modified because they inherit the core value.

## G. TDD RED Evidence

Tests were changed before production source. New expectations required the Checkpoint Documentation Bundle route and rejected the completed Generated Artifact Review route.

Command:

```powershell
$env:PYTHONPATH='src'
.venv\Scripts\python.exe -m pytest tests/test_historical_replay_source_evidence_sufficiency_policy_contract_fixture.py tests/test_historical_replay_source_evidence_sufficiency_policy_contract_fixture_views.py tests/test_historical_replay_source_evidence_sufficiency_policy_contract_fixture_cli.py tests/test_local_research_dashboard.py -q
```

Result: exit 1; `6 failed, 401 passed in 291.67s (0:04:51)`; no skips, deselections, or warnings reported.

The six failures were limited to:

1. Core metadata next-task equality.
2. Index row next-task equality.
3. Status result next-task equality.
4. Core CLI next-task output.
5. Status CLI next-task output.
6. Research-status CLI next-task output.

Every diff was exactly `Generated Artifact Review` versus `Checkpoint Documentation Bundle`. There were no unrelated failures.

## H. Minimal Source And Test Changes

Production change:

- `src/quant_replay_system/historical_replay_source_evidence_sufficiency_policy_contract_fixture.py`: changed only the value of `RECOMMENDED_NEXT_TASK`.

Focused expectations:

- Core test verifies metadata carries the new route and not the completed route.
- Views test verifies index and status inherit the new route and not the completed route.
- CLI test verifies core and status stdout expose the new route and reject the completed route.
- Dashboard test verifies research-status stdout exposes the new route and rejects the completed route.

No schema, count, field, artifact, status, blocker, timing, health, CLI argument, output-root, privacy, or authority logic changed.

## I. Preserved Schema / Count / Semantic Contract

The selected decision date remains `2024-04-02`, timezone remains `Asia/Shanghai`, and legacy universe label remains `etf_core`. The selected symbols and order remain `000001`, `000002`, `159915`, `300750`, `510300`, `600000`, `600519`, `601318`, `688981`; leading zeros remain preserved.

| Contract | Preserved value |
|---|---:|
| Rows / STOCK / ETF | 9 / 7 / 2 |
| Profile conflicts / aligned ETF context / unresolved conflicts | 7 / 2 / 7 |
| Selected rows with blockers | 9 |
| Evidence families / row-family contracts | 17 / 153 |
| Applicable / explicit instrument-not-applicable contracts | 144 / 9 |
| Core artifacts | 10 |
| Selected-row / evidence-family contract fields | 15 / 30 |
| Required-field rows | 45 |
| Status / blocker vocabulary rows | 17 / 28 |
| Timing/revision rules / STOCK-ETF matrix rows | 18 / 4 |
| Sufficiency candidates / accepted / closed | 0 / 0 / 0 |
| PIT-admissible / replay-ready | 0 / 0 |
| Safety true count | 0 |

Semantic separation remains exact:

`source eligibility != evidence presence != evidence sufficiency candidate != evidence acceptance != evidence closure != PIT admissibility != replay readiness`

## J. Focused GREEN Validation

All commands used the repository virtual environment with `PYTHONPATH=src`.

| Command scope | Result | Duration | Exit |
|---|---|---:|---:|
| Core fixture test file | 10 passed; 0 failed/skipped/deselected; 0 warnings | 3.08s | 0 |
| Views test file | 6 passed; 0 failed/skipped/deselected; 0 warnings | 3.41s | 0 |
| CLI test file | 7 passed; 0 failed/skipped/deselected; 0 warnings | 6.68s | 0 |
| Local research dashboard test file | 384 passed; 0 failed/skipped/deselected; 0 warnings | 261.69s | 0 |
| Combined focused set | 407 passed; 0 failed/skipped/deselected; 0 warnings | 257.46s | 0 |

The combined command was the exact four-file command used for RED. Full non-slow pytest was intentionally not run; it remains a later checkpoint/pre-tag gate.

## K. Fresh Temp-Root CLI Smoke

One repository-external system-temp root was created. Sanitized label:

`qr_source_evidence_wording_b0bbfd574423`

All arguments inside the smoke used relative report paths under that root. A copy of the existing default config was used only inside the external temp root.

| Command | Exit | Key result |
|---|---:|---|
| `historical-replay-source-evidence-sufficiency-policy-contract-fixture` | 0 | Created 10 core artifacts; core status created report-only; health PASS |
| `...-index` | 0 | One safe indexed fixture context |
| `...-health` | 0 | Health PASS; issue count 0 |
| `...-status` | 0 | Status created report-only; new route visible |
| `research-status` | 0 | Fixture context visible; new route visible |

The isolated research-status smoke reported `WARN / DATA_PREPARATION_READY` because no paper-workflow artifact was supplied. The focused dashboard test separately supplied paper context and proved the fixture does not override `PAPER_WORKFLOW_READY`.

All count values in Section I matched. Approval/readiness counts and `safety_true_count` remained 0. No `data/raw`, `data/processed`, `data/cache`, or `docs/project_sources` directory was created under the temp root. All generated fixture, view, status, and research-status files stayed outside the repository.

## L. Live Route Scan

Before production change, the old route had one live owner in the core fixture constant; all other production surfaces inherited it.

After hardening:

- Old-route matches in fresh generated outputs and logs: 0.
- New-route matches in fresh outputs: core metadata and Markdown, index CSV and metadata, status CSV/Markdown/metadata, research-status dashboard/summary/metadata, and core/status/research-status CLI logs.
- Old-route matches in authorized tracked scope are limited to this historical report and explicit negative regression expectations in focused tests.
- There is no old-route match in live production source.

No stale live value remains.

## M. Privacy / Disclosure / Safety Review

The changed diff contains no affirmative unsafe state. Existing test-only true values remain limited to explicit negative health cases and were not changed by this task.

Fresh generated artifacts and smoke logs produced zero matches for:

- private Windows absolute paths;
- full 64-character hashes;
- secrets, credentials, bearer tokens, or API keys;
- private reviewer identity;
- source bytes or source content;
- external evidence payload or real CSV content;
- unsafe local paths.

No source or evidence collection occurred. No external API, LLM, broker, order, message, current-candidates, snapshot, signal-semantics, data-write, replay, labels, metrics, training, model, stock-profile, paper-expansion, buy-review, or trading behavior ran.

## N. Research-Status And PAPER_WORKFLOW_READY Priority

Research-status field names and transformation logic were not changed. The fixture context remains visible, report-only, synthetic-only, and non-authorizing. The focused dashboard test proves that when paper context is present, final workflow priority remains `PAPER_WORKFLOW_READY`.

The wording change cannot emit evidence acceptance, PIT approval, replay readiness, active replay input, paper expansion, buy-review, performance validation, or trading authority.

## O. Protected / Project-Source / Git Checks

Protected tracked scan remains exactly:

```text
data/processed/.gitkeep
data/raw/.gitkeep
outputs/reports/.gitkeep
```

`git ls-files docs/project_sources` and `git status --short -- docs/project_sources` produced no output. No repository output was generated by the smoke.

The tracked diff contains one source file and four test files: 38 insertions and 2 deletions. Direct validation of the untracked report found 334 lines, zero trailing-whitespace or unfinished-marker matches, and zero credential-like assignment matches.

Final status contains only the five authorized tracked modifications and this untracked report. `git diff --check` exits 0; HEAD and `origin/main` remain `8dd2001cad2e4a83188ef51630829c340b8666b2`; describe remains `v1.89.0-7-g8dd2001`; no tag points at HEAD; `v1.89.0` remains at `7ca9c4d`; and `v1.90.0` remains absent.

## P. Candidate Next Routes

| Route | Decision | Reason |
|---|---|---|
| A. Checkpoint Documentation Bundle Report-Only v0.1 | selected | Wording is coherent; focused tests and smoke pass; contracts remain unchanged. |
| B. Additional Wording Hardening Report-Only v0.1 | not selected | No bounded live wording issue remains. |
| C. Implementation Corrective Milestone Bundle Report-Only v0.1 | not selected | No implementation defect was found. |
| D. Design Hardening Report-Only v0.1 | not selected | The committed design remains unambiguous. |
| E. Official Manual Evidence Collection Fill Protocol Design Report-Only v0.1 | not selected | Evidence collection remains unauthorized. |
| F. Pause repository work for manual official evidence research | not selected | Safe repository-side checkpoint documentation remains available. |

## Q. Selected Next Route

Exactly one route is selected:

`Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Checkpoint Documentation Bundle Report-Only v0.1`

This route was not executed in this Goal.

## R. Current / Next Mode Recommendation

- Current task: Codex Goal mode, high effort, wording-only implementation and validation.
- Next task: a separate Codex Goal mode task for the report-only checkpoint documentation bundle, only after ChatGPT and user review of this hardening.

## S. Commit / Tag / Source Recommendation

- Commit: recommend human review first, then a manual commit with message `Harden historical replay source evidence sufficiency policy contract fixture next task wording`.
- Tag: no tag for this task.
- Project Source: no Source update for this task.
- Full non-slow validation, checkpoint documentation, tagging, and any Source update remain separate future gates.

No Git staging, commit, push, or tag command was run.

## T. Final Classification And Verdict

Final classification:

`HISTORICAL_REPLAY_SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_ARTIFACT_NEXT_TASK_WORDING_HARDENED_REPORT_ONLY`

Final verdict:

`HISTORICAL_REPLAY_SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_READY_FOR_CHECKPOINT_DOCUMENTATION_BUNDLE_REPORT_ONLY`

The wording-hardening Goal is complete. Final direct report, route, privacy, protected-path, and Git checks passed. It grants no evidence, PIT, replay, model, paper, buy-review, performance-validation, or trading authority.
