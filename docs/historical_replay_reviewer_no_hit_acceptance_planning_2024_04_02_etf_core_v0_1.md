# Historical Replay Reviewer No-Hit Acceptance Planning for 2024-04-02 etf_core v0.1

## A. Decision / Status

phase = historical_replay_reviewer_no_hit_acceptance_planning_2024_04_02_etf_core
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
current_checkpoint = v1.87.0
current_checkpoint_commit = 85348df
current_checkpoint_tag = v1.87.0
current_repo_head = d0d4c44
external_project_source_version = v1.87.0_user_reported
no_hit_acceptance_planning_created = yes
no_hit_context_accepted = no
selected_next_route = Historical Replay Reviewer No-Hit Acceptance Contract / Fixture Report-Only v0.1

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

This is a docs-only reviewer no-hit acceptance planning report for the selected historical replay sample `2024-04-02 / etf_core`. It defines future policy and contract boundaries only. It does not accept a no-hit row, collect evidence, fill templates, close evidence, score source reliability, approve point-in-time admissibility, create replay input, expand paper authority, approve buy-review, or authorize trading.

## B. Current Git / Tag / Source State

Preflight matched the expected current state:

| Check | Result |
| --- | --- |
| Branch/status | `main...origin/main`, clean before this report |
| HEAD | `d0d4c44 Harden official manual evidence collection template fixture post-v1.87 next action wording` |
| `git describe --tags --always` | `v1.87.0-3-gd0d4c44` |
| Tag at HEAD | no output |
| Tag at `85348df` | `v1.87.0` |
| Tag at `69f98eb` | `v1.86.0` |
| v1.87.0 tag exists | yes |
| `git show --check d0d4c44` | exit 0 |
| `git diff --check` before report | exit 0 |

External ChatGPT Project Source is user-reported updated to `v1.87.0`. This report does not create a Project Source package and does not create a repository project-source tree.

Known historical context is preserved: the duplicate post-v1.87 governance audit commits remain in history, and the historical whitespace artifact on `9728367` was not rewritten, amended, reset, retagged, or otherwise modified.

## C. Current v1.87 No-Hit Context

v1.87.0 created a report-only official manual evidence collection template fixture for the selected sample:

| Field | Value |
| --- | ---: |
| row_count | 9 |
| stock_row_count | 7 |
| etf_row_count | 2 |
| evidence_collection_template_row_count | 72 |
| source_lineage_template_row_count | 72 |
| no_hit_template_row_count | 9 |
| survivorship_template_row_count | 9 |
| reviewer_notes_template_row_count | 9 |
| profile_conflict_count | 7 |
| survivorship_warning_count | 9 |
| safety_true_count | 0 |

Selected symbols remain:

```text
000001,000002,159915,300750,510300,600000,600519,601318,688981
```

Current no-hit defaults are conservative:

| Current fixture field | Current value |
| --- | --- |
| no_hit_review_needed | `true` |
| no_hit_source_family | `official_manual_evidence_collection_template` |
| no_hit_query_window_start | `missing` |
| no_hit_query_window_end | `missing` |
| no_hit_query_terms | `template_placeholder_only` |
| no_hit_result | `missing` |
| no_hit_acceptance_status | `not_accepted` |
| no_hit_reviewer_required | `true` |
| reviewer_id_or_alias | `missing` |
| reviewer_role | `missing` |
| reviewer_scope | `missing` |
| no_hit_acceptance_rationale | `missing` |
| no_hit_limitation_note | `template_placeholder_only` |

No current no-hit row is accepted. The current no-hit template is a reviewer handoff surface only.

## D. Reviewer No-Hit Acceptance Meaning

Reviewer no-hit acceptance, if implemented later under a separate report-only contract, should mean:

1. a reviewer documents that a specific source family or evidence family was searched;
2. the query window, query terms, method, and result reference are recorded;
3. the reviewer records why the absence of a hit is relevant to manual follow-up;
4. the row remains review context only unless a later workflow explicitly approves evidence sufficiency;
5. the row keeps a limitation note visible to downstream reviewers.

A future accepted no-hit context may help a human see what was searched and what was not found. It must not silently convert absence of a hit into positive evidence.

## E. What No-Hit Acceptance Is Not

No-hit acceptance is not:

| Not this | Reason |
| --- | --- |
| source reliability scoring | A no-hit query records a search outcome, not source quality or completeness. |
| official evidence | Absence of a hit is not the same as an official source record. |
| evidence closure | A no-hit row cannot close listed, delisted, ST, suspension, universe, survivorship, or profile-policy evidence. |
| point-in-time approval | A no-hit row cannot prove that required evidence was available before decision time. |
| source lineage replacement | It cannot replace source id, permission class, raw reference, source hash, revision id, available time, quality status, or limitation note. |
| survivorship rationale | It cannot prove survivorship or replace survivorship source review. |
| profile conflict resolution | It cannot resolve STOCK rows appearing under the legacy `etf_core` label. |
| universe membership proof | It cannot prove that a symbol belonged to the intended universe on `2024-04-02`. |
| status proof | It cannot prove listed or active status, delisted or not-delisted status, ST or no-ST status, ETF ST not-applicable policy, or suspension and trading status. |
| downstream authority | It cannot authorize replay input, replay execution, labels, metrics, training, model work, stock-profile validation, paper expansion, buy-review, or trading. |

## F. Required No-Hit Field Design

A future reviewer no-hit acceptance contract should require these fields:

| Field | Required purpose |
| --- | --- |
| no_hit_review_needed | States whether a no-hit review path is still required. |
| no_hit_source_family | Names the source family searched. |
| no_hit_evidence_family | Names the evidence family the query attempted to support. |
| no_hit_query_window_start | Starts the search window. |
| no_hit_query_window_end | Ends the search window. |
| no_hit_query_window_timezone | Defines the query window timezone. |
| no_hit_query_terms | Records query terms or a reviewed query description. |
| no_hit_query_method | Records search method, such as official-site search, archive lookup, exchange query, or reviewed local handoff. |
| no_hit_result | Controlled result such as no hit, hit found, conflicting hit, or inconclusive. |
| no_hit_result_reference | Pointer to the query log or reviewed search reference, without private credentials or source bytes. |
| no_hit_acceptance_status | Controlled planning status. |
| no_hit_reviewer_required | States that reviewer accountability is required. |
| reviewer_id_or_alias | Uses a non-private reviewer alias. |
| reviewer_role | Records reviewer role. |
| reviewer_scope | Defines what the reviewer was authorized to review. |
| reviewer_private_identity_disclosed | Must remain `no`. |
| no_hit_acceptance_rationale | Required for any future review-context acceptance. |
| no_hit_limitation_note | Required for every no-hit row. |
| no_hit_decision_time_policy | States how the query window relates to `2024-04-02`. |
| no_hit_conflict_policy | States what happens if a conflicting hit is found. |
| no_hit_downstream_use_policy | States that downstream use is review context only unless separately approved. |

Future status vocabulary may include:

| Status | Meaning |
| --- | --- |
| not_accepted | Default; no no-hit context is accepted. |
| proposed_for_review_context_only | Candidate context for reviewer inspection only. |
| rejected_by_scope | Search scope is insufficient or mismatched. |
| rejected_by_missing_query_window | Query window is absent or incomplete. |
| rejected_by_post_decision_source | Query depends on a source not available by decision time. |
| rejected_by_conflicting_hit | A hit or conflicting evidence was found. |
| rejected_by_missing_reviewer_scope | Reviewer scope is missing or insufficient. |
| accepted_for_review_context_only_not_evidence | Future context-only acceptance, not evidence. |
| accepted_for_manual_followup_only_not_pit_approved | Future manual follow-up context, not point-in-time approval. |

This task does not set any accepted status.

## G. Reviewer / Privacy Policy

Reviewer accountability must use aliases and roles, not private legal identity disclosure. A future no-hit workflow should require:

| Reviewer field | Policy |
| --- | --- |
| reviewer_id_or_alias | Required alias; private identity must not be printed. |
| reviewer_role | Required role such as reviewer, maintainer, or evidence auditor. |
| reviewer_scope | Required scope that names the source family, evidence family, and selected sample. |
| reviewed_at | Required if review occurs later, with timezone if applicable. |
| reviewer_private_identity_disclosed | Must be `no`; `yes` is a blocker. |
| no_hit_acceptance_rationale | Required for any future non-default status. |
| no_hit_limitation_note | Required for every row, including rejected rows. |

Reviewer judgment cannot override missing source lineage, missing availability timing, source conflicts, survivorship warnings, profile conflicts, or official evidence requirements.

## H. Query Window and Decision-Time Policy

No-hit query windows must be tied to the historical decision time:

1. Query windows must include start, end, and timezone.
2. Query windows must be bounded to sources and archives that are relevant to `2024-04-02`.
3. A query run after the decision date may be documented only as manual follow-up context.
4. A source reference first available after the decision date cannot support point-in-time context.
5. A query window without timezone blocks acceptance.
6. A query result without reference blocks acceptance.
7. A post-decision source reference blocks acceptance unless future Pro review designs a strictly bounded historical archive policy.
8. Query terms must be reproducible enough for a reviewer to understand scope without exposing credentials, private paths, or source bytes.

The future contract should distinguish:

| Case | Future behavior |
| --- | --- |
| Complete query window before decision time | May be proposed for review context if all other fields are present. |
| Query window crosses decision time | Block until reviewed and split or rejected. |
| Query window after decision time | Block as evidence; may be manual follow-up context only. |
| Unknown timezone | Block. |
| Missing result reference | Block. |
| Conflicting hit found | Block no-hit acceptance and route to evidence review. |

## I. Conflict and Limitation Policy

Conflict policy:

- A conflicting hit always blocks no-hit acceptance.
- A later official hit cannot be ignored because an earlier query produced no hit.
- A no-hit row cannot override required source lineage or survivorship fields.
- A no-hit row cannot override the STOCK profile conflict under legacy `etf_core`.
- A no-hit row cannot override ETF policy requirements.

Limitation policy:

- Every no-hit row requires a limitation note.
- Warning or context-only acceptance requires a reviewer-visible rationale.
- Missing query scope, missing reviewer scope, or missing decision-time policy remains a blocker.
- No-hit context should be shown as bounded reviewer context, not as evidence sufficiency.

## J. Blocker Vocabulary

A future no-hit acceptance contract should include at least these blockers:

| Blocker | Meaning |
| --- | --- |
| blocker_missing_no_hit_source_family | Source family searched is missing. |
| blocker_missing_no_hit_evidence_family | Evidence family is missing. |
| blocker_missing_no_hit_query_window | Query start or end is missing. |
| blocker_missing_no_hit_timezone | Query timezone is missing. |
| blocker_missing_no_hit_query_terms | Query terms or reviewed query description are missing. |
| blocker_missing_no_hit_result_reference | Result reference is missing. |
| blocker_missing_reviewer_alias | Reviewer alias is missing. |
| blocker_missing_reviewer_role | Reviewer role is missing. |
| blocker_missing_reviewer_scope | Reviewer scope is missing. |
| blocker_private_reviewer_identity_disclosed | Private reviewer identity disclosure is present. |
| blocker_post_decision_query_window | Query window falls after the decision time. |
| blocker_post_decision_source_reference | Source reference was not available by decision time. |
| blocker_conflicting_hit_found | A hit or conflicting source result was found. |
| blocker_no_hit_used_as_source_reliability_score | No-hit context is being used as source scoring. |
| blocker_no_hit_used_as_official_evidence | No-hit context is being used as official evidence. |
| blocker_no_hit_used_as_pit_approval | No-hit context is being used as point-in-time approval. |
| blocker_no_hit_used_to_override_source_lineage | No-hit context is being used to bypass lineage fields. |
| blocker_no_hit_used_to_override_survivorship | No-hit context is being used to bypass survivorship rationale. |
| blocker_no_hit_used_to_override_profile_conflict | No-hit context is being used to bypass profile conflict. |
| blocker_forbidden_downstream_flag | Any downstream readiness or authority flag is true. |

## K. STOCK / ETF and Selected-Sample Implications

All nine selected symbols remain in scope.

| Symbol | Instrument | Legacy universe label | Required profile context | Profile conflict |
| --- | --- | --- | --- | --- |
| 000001 | STOCK | etf_core | stock_core | true |
| 000002 | STOCK | etf_core | stock_core | true |
| 159915 | ETF | etf_core | etf_core | false |
| 300750 | STOCK | etf_core | stock_core | true |
| 510300 | ETF | etf_core | etf_core | false |
| 600000 | STOCK | etf_core | stock_core | true |
| 600519 | STOCK | etf_core | stock_core | true |
| 601318 | STOCK | etf_core | stock_core | true |
| 688981 | STOCK | etf_core | stock_core | true |

Planning implications:

- No-hit planning applies to all 9 symbols.
- Seven STOCK rows remain profile-conflict review context under the legacy `etf_core` label.
- Two ETF rows remain non-conflict rows but still require ETF-specific status and policy evidence.
- STOCK rows still need STOCK-specific official-status evidence, including ST or no-ST status.
- ETF rows still need ETF ST not-applicable policy if stock ST evidence does not apply.
- No-hit context cannot prove universe membership for any row.

## L. Future Validation Rules

A later contract or fixture should validate:

1. each selected symbol has one no-hit planning row;
2. no-hit default status remains `not_accepted`;
3. reviewer private identity disclosure remains `no`;
4. query window start, end, timezone, method, terms, and result reference are required before any future proposed status;
5. a post-decision query window blocks acceptance;
6. a post-decision source reference blocks acceptance;
7. a conflicting hit blocks acceptance;
8. missing limitation note blocks acceptance;
9. no-hit rows cannot set official evidence, point-in-time approval, replay, buy-review, or trading authority;
10. no-hit rows cannot reduce profile conflict count, survivorship warning count, or required official status evidence count.

## M. Future Focused Test Plan

Future focused tests should cover:

| Test area | Expected assertion |
| --- | --- |
| default no-hit rows | 9 rows, all `not_accepted` |
| selected symbols | exact 9-symbol set preserved |
| reviewer privacy | private identity disclosure remains `no` |
| missing query window | blocker emitted |
| missing timezone | blocker emitted |
| missing query terms | blocker emitted |
| missing result reference | blocker emitted |
| post-decision query window | blocker emitted |
| post-decision source reference | blocker emitted |
| conflicting hit found | no-hit context rejected |
| accepted context status | context-only and not evidence |
| limitation note | required for every row |
| STOCK profile conflict | 7 profile conflicts remain |
| ETF policy | 2 ETF rows require ETF policy path |
| downstream flags | all authority flags remain false |
| research-status priority | context cannot override paper workflow priority |

Suggested future focused command for a later implementation task:

```text
.venv\Scripts\python.exe -m pytest tests/test_historical_replay_reviewer_no_hit_acceptance_fixture.py tests/test_historical_replay_reviewer_no_hit_acceptance_fixture_views.py tests/test_historical_replay_reviewer_no_hit_acceptance_fixture_cli.py -q
```

This command was not run in this docs-only planning task.

## N. Future Temp-Root Smoke Plan

A later contract or fixture task should use a repository-external temp root and verify:

| Smoke item | Expected |
| --- | --- |
| core fixture | writes report-only no-hit planning artifacts only |
| index | discovers exactly the generated report-only artifacts |
| health | passes only when no forbidden authority flags are true |
| status | reports context-only next task |
| research-status | exposes context without overriding paper workflow priority |
| protected paths | no protected data writes |
| project-source tree | not created |
| evidence collection | not started |
| no-hit acceptance | default remains not accepted unless specifically testing a future context-only fixture row |

No temp-root smoke was run in this docs-only planning task.

## O. Safety and Non-Approval Boundary

This planning report does not:

- collect official evidence;
- fetch official sources;
- read websites or external APIs;
- create filled evidence templates;
- create accepted evidence packets;
- close official evidence;
- close point-in-time evidence;
- run a validator;
- create active replay input;
- execute replay;
- freeze replay decisions;
- create forward labels;
- compute metrics;
- train or evaluate models;
- create stock-profile validation;
- expand paper workflow authority;
- approve buy-review;
- authorize trading;
- run current-candidates;
- build snapshots;
- mutate signal semantics;
- call brokers, place orders, send messages, call LLM systems, or call external APIs;
- write protected data directories.

## P. Candidate Next Routes Reviewed

| Route | Decision | Reason |
| --- | --- | --- |
| A. Historical Replay Reviewer No-Hit Acceptance Contract / Fixture Report-Only v0.1 | selected | Planning is coherent and remains report-only; a contract fixture is the smallest safe next step. |
| B. Historical Replay Mixed STOCK/ETF Universe Profile Policy Planning for legacy etf_core Report-Only v0.1 | not selected | Profile conflict is important, but no-hit contract boundaries can preserve profile blockers without resolving mixed-universe policy. |
| C. Historical Replay Official Manual Evidence Collection Fill Protocol Design Report-Only v0.1 | not selected | Fill protocol should wait until no-hit acceptance fields and blockers are contractually stable. |
| D. Historical Replay Reviewer No-Hit Acceptance Planning Hardening Report-Only v0.1 | not selected | No unresolved field, blocker, or semantic ambiguity remains in this planning report. |
| E. Pause repo work and manually collect official source/status evidence outside the repo | not selected | Repo-side report-only contract work can proceed without evidence collection. |
| F. Continue next historical replay governance feature outside no-hit branch | not selected | The current branch has a clear next report-only contract step. |

## Q. Selected Next Route

Historical Replay Reviewer No-Hit Acceptance Contract / Fixture Report-Only v0.1

## R. Why Selected Route Is Safe

The selected route is safe because it can remain synthetic, report-only, and diagnostic-only. It can encode fields, statuses, blockers, and safety checks without collecting official evidence or accepting any no-hit context as evidence. It can also preserve all existing v1.87 boundaries: selected sample counts, STOCK/ETF profile context, no-hit default `not_accepted`, survivorship warnings, reviewer privacy defaults, and all downstream authority flags false.

## S. What Must Not Be Bundled

The next route must not bundle:

- official source collection;
- website reads or API calls;
- source content reads;
- filled evidence templates;
- accepted evidence packets;
- evidence closure;
- point-in-time approval;
- replay input;
- replay execution;
- replay decision freeze;
- labels;
- metrics;
- training or evaluation;
- model work;
- stock-profile validation;
- paper authority expansion;
- buy-review;
- trading;
- current-candidates;
- snapshots;
- signal semantics mutation;
- broker, order, message, external API, or LLM behavior;
- Project Source package files;
- Source update notes;
- protected data writes.

## T. ChatGPT / Codex Mode Recommendation

Codex high is sufficient for the selected report-only no-hit contract fixture if it stays synthetic and does not introduce source authority adjudication or evidence sufficiency.

Use ChatGPT Pro or Pro Extended before any task introduces official evidence collection, source authority policy, no-hit sufficiency as evidence, ETF not-applicable authority, mixed-universe production policy, source reliability scoring, point-in-time adjudication, replay input readiness, replay execution, labels, metrics, training, model work, stock-profile validation, paper expansion, buy-review, performance validation, broker integration, order placement, message delivery, external API or LLM calls, or trading authority.

## U. Commit / Tag / Source Recommendation

Recommended commit message if accepted:

```text
docs: plan historical replay reviewer no-hit acceptance policy
```

Recommended tag decision: no tag for this no-hit planning report.

Recommended Source update decision: no Source update for this no-hit planning report.

## V. Recommended Next Task

Historical Replay Reviewer No-Hit Acceptance Contract / Fixture Report-Only v0.1

Final classification:

```text
HISTORICAL_REPLAY_REVIEWER_NO_HIT_ACCEPTANCE_PLANNING_CREATED_REPORT_ONLY
```

Final verdict:

```text
HISTORICAL_REPLAY_REVIEWER_NO_HIT_ACCEPTANCE_PLANNING_READY_FOR_CONTRACT_FIXTURE_REPORT_ONLY
```
