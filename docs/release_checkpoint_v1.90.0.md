# Release Checkpoint v1.90.0

## A. Decision / Status

```text
phase = historical_replay_source_evidence_sufficiency_policy_contract_fixture_checkpoint_documentation
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
checkpoint_documentation_created = yes
checkpoint_docs_approved = no
candidate_checkpoint_version = v1.90.0
candidate_checkpoint_declared = yes
candidate_checkpoint_approved = no
tag_approved = no
source_update_approved = no
latest_previous_checkpoint = v1.89.0
latest_previous_checkpoint_commit = 7ca9c4d
latest_previous_checkpoint_tag = v1.89.0
latest_repo_commit_at_start = 81866c8
business_checkpoint_changed = no
selected_historical_decision_date = 2024-04-02
decision_timezone = Asia/Shanghai
selected_legacy_universe_label = etf_core
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
full_non_slow_run = no
selected_next_route = Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Checkpoint Commit Review Report-Only v0.1
```

Required non-approval fields remain no:

```text
official_source_hierarchy_approved = no
official_evidence_collection_started = no
evidence_read_from_external_sources = no
evidence_template_filled = no
evidence_sufficiency_applied_to_selected_rows = no
evidence_accepted = no
evidence_closed = no
no_hit_accepted_as_evidence = no
profile_conflict_resolved = no
universe_membership_approved = no
stock_profile_validated = no
pit_admissibility_approved = no
active_replay_input_approved = no
replay_execution_approved = no
replay_decision_freeze_approved = no
forward_labels_created = no
metric_computation_approved = no
model_training_approved = no
weights_or_thresholds_adjustment_approved = no
paper_expansion_approved = no
real_buy_review_approved = no
buy_review_allowed = no
broker_api_approved = no
order_placement_approved = no
message_delivery_approved = no
trading_allowed = no
external_api_or_llm_approved = no
current_candidates_execution_approved = no
snapshot_build_approved = no
signal_semantics_mutation_approved = no
data_raw_processed_cache_writes_approved = no
docs_project_sources_created = no
```

This document records a coherent candidate checkpoint. It does not approve a checkpoint, tag, Source update, evidence workflow, or downstream authority.

## B. Current Git / Tag / External Source State

- Start branch: `main`.
- Start HEAD and `origin/main`: `81866c89ab7e050d74a4149539830047c1d24593`.
- Start describe: `v1.89.0-8-g81866c8`.
- Initial worktree: clean.
- No tag points at start HEAD.
- Formal tag `v1.89.0` remains at `7ca9c4d`.
- Candidate tag `v1.90.0` does not exist.
- No Source update is approved or performed. No Source package or `docs/project_sources` content is created.
- The formal business checkpoint remains `v1.89.0` until separately reviewed and approved.

## C. Goal Identity And Acceptance Artifact

Goal:

`Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Checkpoint Documentation Bundle Report-Only v0.1`

Acceptance artifact:

`docs/release_checkpoint_v1.90.0.md`

The previous Artifact / Next-Task Wording Hardening Goal was not repeated. This Goal is docs-only and creates exactly one repository file.

## D. Candidate v1.90.0 Checkpoint Meaning

`v1.90.0` is a candidate checkpoint identity in this document only. It describes the completed synthetic Source / Evidence Sufficiency Policy Contract Fixture chain and its validation state.

It does not create or approve a tag, designate the current HEAD as a final tag target, change the formal `v1.89.0` checkpoint, or authorize evidence collection, PIT approval, replay, models, paper expansion, buy-review, or trading.

## E. Completed Post-v1.89 Chain Summary

| Commit | Completed report-only milestone |
|---|---|
| `cef7cdf` | Source / Evidence Sufficiency Policy Planning Without Evidence Collection |
| `d78dc9c` | Source / Evidence Sufficiency Policy Contract Fixture Design |
| `ee3876f` | Contract Fixture Core / Views / CLI / Research-Status Milestone Bundle |
| `8dd2001` | Contract Fixture Generated Artifact Review |
| `81866c8` | Contract Fixture Artifact / Next-Task Wording Hardening |

The normative design, generated-artifact review, and wording-hardening report are tracked. `81866c8` contains exactly the accepted wording-hardening scope: its report, one owning runtime wording change, and four focused expectation updates.

## F. Selected Sample And Exact Count Contract

- Historical decision date: `2024-04-02`.
- Decision timezone: `Asia/Shanghai`.
- Legacy universe label: `etf_core`.
- Ordered symbols: `000001`, `000002`, `159915`, `300750`, `510300`, `600000`, `600519`, `601318`, `688981`.

| Contract | Value |
|---|---:|
| Row count | 9 |
| STOCK / ETF | 7 / 2 |
| Profile conflicts | 7 |
| Profile-aligned ETF contexts | 2 |
| Unresolved profile conflicts | 7 |
| Selected rows with blockers | 9 |
| Safety true count | 0 |

Leading-zero symbols remain strings. Every selected row remains blocked and non-authorizing.

## G. Evidence-Family / STOCK-ETF Applicability Contract

The 17 families remain:

1. Instrument-type identity.
2. Listed/active status.
3. Delisted/not-delisted status.
4. STOCK ST/no-ST status.
5. ETF ST-not-applicable policy.
6. Suspension/trading status.
7. Universe membership.
8. Universe definition and constituent version.
9. Source lineage/provenance.
10. Publish time, available time, and timezone.
11. Revision identity and effective version.
12. Permission class and legality.
13. Survivorship rationale.
14. Reviewer scope, quality, and limitation.
15. No-hit query context.
16. Profile-conflict context.
17. Cross-source corroboration.

Exact contract sizes remain:

- 153 row-family contract rows.
- 144 applicable rows.
- 9 explicit instrument-not-applicable context rows.
- 15 selected-row required fields.
- 30 evidence-family contract fields.
- 45 required-field rows.
- 17 status-vocabulary rows.
- 28 blocker-vocabulary rows.
- 18 timing/revision rules.
- 4 STOCK/ETF applicability-matrix rows.

Semantic separation remains:

`source eligibility != evidence presence != evidence sufficiency candidate != evidence acceptance != evidence closure != PIT admissibility != replay readiness`

Sufficiency candidates, accepted evidence, closed evidence, PIT-admissible rows, and replay-ready rows all remain 0.

## H. Core Artifact / Index / Health / Status / CLI Contract

The ten core artifacts are:

1. `metadata.json`
2. `source_evidence_sufficiency_policy_rows.csv`
3. `source_evidence_sufficiency_policy_evidence_family_contract.csv`
4. `source_evidence_sufficiency_policy_required_fields.csv`
5. `source_evidence_sufficiency_policy_status_vocabulary.csv`
6. `source_evidence_sufficiency_policy_blocker_vocabulary.csv`
7. `source_evidence_sufficiency_policy_timing_revision_matrix.csv`
8. `source_evidence_sufficiency_policy_stock_etf_matrix.csv`
9. `source_evidence_sufficiency_policy_safety_flags.json`
10. `source_evidence_sufficiency_policy_contract_fixture_report.md`

The command family remains:

- `historical-replay-source-evidence-sufficiency-policy-contract-fixture`
- `historical-replay-source-evidence-sufficiency-policy-contract-fixture-index`
- `historical-replay-source-evidence-sufficiency-policy-contract-fixture-health`
- `historical-replay-source-evidence-sufficiency-policy-contract-fixture-status`
- `research-status`

Core status remains `SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_CREATED_REPORT_ONLY`. Health behavior remains PASS/WARN/FAIL with no change to validation rules. Status and index retain safe relative references.

## I. Generated Artifact Review Result

The accepted generated-artifact review found the fixture inventory, counts, leading-zero handling, evidence-family applicability, required fields, vocabularies, timing/revision matrix, health, status, CLI, research-status, privacy, and non-approval boundaries coherent.

Its only selected issue was a bounded live next-task wording problem: once the review existed, the route to that review became self-referential. It did not identify a schema, runtime, health, privacy, or authority defect.

## J. Next-Task Wording Hardening Result

The accepted wording-hardening milestone changed the single owning live value from the completed Generated Artifact Review route to:

`Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Checkpoint Documentation Bundle Report-Only v0.1`

Core metadata/Markdown, index, status, CLI, and research-status inherit that one value. The hardening preserved every schema, count, semantic, health, privacy, and authority boundary. The route was live and coherent before this checkpoint document was created; this docs-only Goal does not rewrite runtime wording.

## K. Focused Validation Results

All runs used the repository virtual environment with `PYTHONPATH=src`.

| Scope | Result | Duration | Exit |
|---|---|---:|---:|
| Core fixture tests | 10 passed; 0 failed/skipped/deselected; 0 warnings | 1.88s | 0 |
| Views tests | 6 passed; 0 failed/skipped/deselected; 0 warnings | 0.67s | 0 |
| CLI tests | 7 passed; 0 failed/skipped/deselected; 0 warnings | 4.79s | 0 |
| Local research dashboard tests | 384 passed; 0 failed/skipped/deselected; 0 warnings | 281.07s | 0 |
| Combined focused set | 407 passed; 0 failed/skipped/deselected; 0 warnings | 264.96s | 0 |

The combined set used all four focused files in one pytest command. No source or test file was modified.

## L. Fresh Temp-Root CLI Smoke Result

One fresh repository-external system-temp root was used. Sanitized label:

`qr_source_evidence_checkpoint_cff401319955`

| Command | Exit | Result |
|---|---:|---|
| Core fixture | 0 | Ten artifacts; created report-only; health PASS |
| Index | 0 | Index output exists and references the fixture safely |
| Health | 0 | Health PASS; issue count 0 |
| Status | 0 | Created report-only status output exists |
| Research status | 0 | Fixture context and live route visible |

Every exact count in Sections F and G matched. The live Checkpoint Documentation Bundle route appeared in core, status, and research-status surfaces; the completed Generated Artifact Review route had zero temp-output matches.

All 29 temporary files remained under the external temp root. No repository output, protected data directory, or Project Source directory was created.

## M. Research-Status Integration And PAPER_WORKFLOW_READY Priority

The isolated smoke reported `WARN / DATA_PREPARATION_READY` because no paper-workflow artifact was supplied. This is benign and does not represent a priority regression.

The focused dashboard test supplies paper context and confirms the fixture remains visible while final workflow priority stays `PAPER_WORKFLOW_READY`. No research-status field grants evidence acceptance, PIT approval, replay readiness, active replay input, paper expansion, buy-review, or trading authority.

## N. Privacy / Disclosure / Safety And Non-Approval Boundary

Fresh temp artifacts and logs had zero matches for private Windows absolute paths, full 64-character hashes, sensitive assignment patterns, source payloads, source bytes, real CSV content, or private reviewer identity.

All runtime safety defaults and generated safe artifacts remain false/zero. Existing test-only true mutations are limited to explicit negative health tests. This checkpoint does not collect evidence, call external services, run replay, create labels or metrics, train models, validate stock profiles, expand paper authority, allow buy-review, or enable broker/order/message/trading behavior.

## O. Static / Protected / Project-Source / Git Check Results

Before creating this document:

- The worktree remained clean.
- Live production source contained only the Checkpoint Documentation Bundle route.
- `git diff --check` exited 0.
- The protected tracked scan contained only the three expected placeholders.
- Project Source tracked/status scans were empty.

Expected protected tracked inventory:

```text
data/processed/.gitkeep
data/raw/.gitkeep
outputs/reports/.gitkeep
```

Final checks after document creation confirm:

- The document exists and has zero trailing-whitespace, unfinished-marker, or disallowed model-name matches.
- The document has zero unsafe affirmative-state matches and zero private-path, full-hash, sensitive-assignment, source-payload, or private-reviewer disclosure matches.
- The only two focused-test unsafe-true matches are the existing explicit negative health mutations for `selected_row_evidence_accepted` and `trading_allowed`.
- Live production source still points to the Checkpoint Documentation Bundle route; the document selects the forward Checkpoint Commit Review route without changing runtime wording.
- Protected tracked output remains exactly the three placeholders above; Project Source scans remain empty.
- Final status contains exactly one untracked file: `docs/release_checkpoint_v1.90.0.md`.
- `git diff --name-status` and `git diff --stat` are empty because no tracked file changed; `git diff --check` exits 0.
- HEAD and `origin/main` remain `81866c89ab7e050d74a4149539830047c1d24593`; describe remains `v1.89.0-8-g81866c8`.
- No tag points at HEAD; `v1.89.0` remains at `7ca9c4d`; `v1.90.0` remains absent.

## P. Full Non-Slow Decision

```text
full_non_slow_run = no
```

Focused tests and the fresh external-temp smoke are sufficient for candidate checkpoint documentation. Full non-slow remains required only in a later, separately authorized Full Non-Slow Pre-Tag Validation Goal before any candidate `v1.90.0` tag or Source update.

## Q. Candidate Tag Plan

- No tag is created or approved here.
- Current HEAD is not declared the final tag target.
- A future target must include the complete reviewed pre-tag evidence chain.
- A manual tag decision may occur only after this checkpoint document is committed and reviewed, full non-slow passes, any pre-tag wording issue is hardened, and a separate tag/source readiness report is accepted.

## R. Project Source Update Timing Plan

- No Source update or Source package is created here.
- `docs/project_sources` remains absent.
- A Source update may be considered only after checkpoint documentation is committed/reviewed, full non-slow passes, a manual tag is created, and a separately scoped Source update is approved.

## S. Open Blockers And Non-Blocking Notes

No blocker prevents review and manual commit of this candidate checkpoint document.

Non-blocking notes:

- The formal checkpoint remains `v1.89.0` until separate approval.
- Full non-slow, tag readiness, tag creation, and Source update remain deferred.
- The isolated smoke intentionally had no paper artifact; `PAPER_WORKFLOW_READY` preservation is proven by focused tests.
- Evidence collection and every downstream approval remain outside scope.

## T. Candidate Next Routes

| Route | Decision | Reason |
|---|---|---|
| A. Checkpoint Commit Review Report-Only v0.1 | selected | Document, focused tests, smoke, counts, semantics, safety, privacy, and Git scope are coherent. |
| B. Additional Checkpoint Documentation Hardening Report-Only v0.1 | not selected | No bounded document defect is known. |
| C. Implementation Corrective Milestone Bundle Report-Only v0.1 | not selected | No implementation defect was found. |
| D. Design Hardening Report-Only v0.1 | not selected | The accepted design remains coherent. |
| E. Full Non-Slow Pre-Tag Validation Report-Only v0.1 | not selected | Protocol requires checkpoint commit review first. |
| F. Official Manual Evidence Collection Fill Protocol Design Report-Only v0.1 | not selected | Evidence collection remains unauthorized. |
| G. Pause repository work for manual official evidence research | not selected | Safe checkpoint commit review is available. |

## U. Selected Next Route

Exactly one route is selected:

`Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Checkpoint Commit Review Report-Only v0.1`

The route is not executed in this Goal.

## V. Current / Next Mode Recommendation

Current task:

```text
surface = Codex
environment = Local
model = GPT-5.6 Sol
effort = High
speed = Standard
task mode = Goal
```

Next task after successful review:

```text
surface = Codex
environment = Local
model = GPT-5.6 Sol
effort = High
speed = Standard
task mode = Goal
route = Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Checkpoint Commit Review Report-Only v0.1
```

The next Goal must identify this Checkpoint Documentation Bundle as the previous Goal that must not be repeated.

## W. Commit / Tag / Source Recommendation

- Commit recommendation after ChatGPT/user review: `docs: document historical replay source evidence sufficiency policy contract fixture checkpoint v1.90.0`.
- Tag recommendation: no tag.
- Source recommendation: no Source update.
- No staging, commit, push, or tag command is run in this Goal.

## X. Final Classification And Verdict

Final classification:

`HISTORICAL_REPLAY_SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_CHECKPOINT_DOCUMENTATION_CREATED_REPORT_ONLY`

Final verdict:

`HISTORICAL_REPLAY_SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_CHECKPOINT_DOCUMENTATION_READY_FOR_REVIEW_AND_COMMIT_REPORT_ONLY`

This candidate checkpoint documentation grants no evidence, PIT, replay, model, paper, buy-review, performance-validation, broker, order, message, or trading authority.
