# Historical Replay Official Manual Evidence Collection Template Fixture Post-v1.87 Governance Audit / Next Decision Planning v0.1

## A. Decision / Status

phase = historical_replay_official_manual_evidence_collection_template_fixture_post_v1_87_governance_audit_next_decision_planning  
decision = ready  
privacy_issue_stop = no  
docs_only = yes  
source_code_changed = no  
tests_changed = no  
runtime_changed = no  
current_checkpoint = v1.87.0  
current_checkpoint_commit = 85348df  
current_checkpoint_tag = v1.87.0  
previous_checkpoint = v1.86.0  
previous_checkpoint_commit = 69f98eb  
previous_checkpoint_tag = v1.86.0  
external_project_source_version = v1.87.0_user_reported  
post_checkpoint_governance_audit_created = yes  
selected_next_route = Historical Replay Official Manual Evidence Collection Template Fixture Post-v1.87 Generated Artifact Review / Wording Hardening Report-Only v0.1

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

This is a docs-only post-checkpoint governance audit and next-decision planning bundle for v1.87.0. It does not modify source, tests, runtime behavior, generated repository outputs, Project Source files, release checkpoint files, Source update notes, or protected data directories.

## B. Current Git / Tag / Source State

Preflight matched the expected post-v1.87 state:

- Branch/status: `main...origin/main`, clean before this report.
- HEAD: `85348df docs: plan official manual evidence collection template fixture v1.87 tag and source readiness`.
- `git describe --tags --always`: `v1.87.0`.
- `git tag --points-at HEAD`: `v1.87.0`.
- `git tag --points-at 85348df`: `v1.87.0`.
- `git tag --points-at 69f98eb`: `v1.86.0`.
- `git tag --points-at d83a92e`: `v1.85.0`.
- `git tag --list v1.87.0`: `v1.87.0`.

User-reported external ChatGPT Project Source is updated to `v1.87.0`. This report treats that as external context only and does not create any repository-side Source package or `docs/project_sources` tree.

## C. v1.87 Checkpoint Chain Audit

The v1.87.0 checkpoint chain is coherent and tagged:

| Chain item | Evidence |
| --- | --- |
| Template design | `docs/historical_replay_official_manual_evidence_collection_template_design_2024_04_02_etf_core_v0_1.md` |
| Template fixture core/views/CLI/research-status | `src/quant_replay_system/historical_replay_official_manual_evidence_collection_template_fixture*.py`, `src/quant_replay_system/cli.py`, and `src/quant_replay_system/local_research_dashboard.py` |
| Generated artifact review | `docs/historical_replay_official_manual_evidence_collection_template_generated_artifact_review_v0_1.md` |
| Checkpoint documentation | `docs/release_checkpoint_v1.87.0.md` at `34b2d4e` |
| Checkpoint commit review | `docs/historical_replay_official_manual_evidence_collection_template_fixture_checkpoint_commit_review_v0_1.md` at `59f7c4c` |
| Full non-slow pre-tag validation | `docs/historical_replay_official_manual_evidence_collection_template_fixture_full_non_slow_pre_tag_validation_v0_1.md` at `dd143fa` |
| Tag/source readiness | `docs/historical_replay_official_manual_evidence_collection_template_fixture_v1_87_tag_source_readiness_v0_1.md` at `85348df` |
| Manual tag | `v1.87.0` points at `85348df` |

The chain preserves the selected historical replay audit sample `2024-04-02 / etf_core` and remains an empty or synthetic manual evidence collection template fixture, not collected evidence.

## D. Validation Evidence Audit

Committed v1.87.0 validation evidence records:

- focused fixture/views/CLI tests: `24 passed`;
- dashboard/research-status tests: `377 passed`;
- combined focused suite: `447 passed`;
- temp-root CLI smoke: core, index, health, status, and research-status exited `0`;
- health: `OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_HEALTH_PASS_REPORT_ONLY`;
- research-status context visible: true;
- full non-slow: `6233 passed, 109 deselected, 5 warnings`;
- `safety_true_count = 0`;
- `buy_review_allowed = false`;
- `trading_allowed = false`.

This post-checkpoint audit did not rerun pytest, full non-slow, or CLI smoke. It only reviewed the committed evidence and current git/tag state.

## E. Source Update Acknowledgement

External ChatGPT Project Source is user-reported updated to `v1.87.0`. This audit acknowledges that as external context only.

This audit does not create a Project Source package, does not create Source update notes, does not create repository `docs/project_sources`, and does not add `src/`, `tests/`, `outputs/`, `data/`, manual diagnostics, secrets, credentials, `.env`, virtual environments, or build artifacts to any Source surface.

## F. Milestone Bundle Preference Acknowledgement

The milestone bundle preference remains active: governance audit and next-decision planning can be bundled when the task is docs-only and does not mutate runtime, tests, source, data, Source packages, or checkpoint docs.

This report follows that preference by combining post-v1.87 governance review with exactly one selected next safe route.

## G. Current Capability and Count Contract

v1.87.0 is a report-only official manual evidence collection template fixture checkpoint. It provides structured empty or synthetic template scaffolding for manual review. It does not collect official evidence and does not create filled evidence templates.

Expected count contract remains:

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

Important interpretation boundaries:

- A blank template row is not PIT approval.
- `row_ready_for_manual_fill_not_pit_approved` is not PIT admissible.
- `no_hit_query_required` is not source reliability scoring.
- `source_hash_preview` is not source hash validation.
- `local_file_hash_preview` is not PIT evidence by itself.
- Same-day quotation presence is not official status proof by itself.
- ETF ST not-applicable policy is required for ETF rows if no ST evidence applies.
- STOCK rows under legacy `etf_core` remain profile-conflict review context until separately resolved.
- Universe membership cannot be inferred from the legacy `etf_core` label alone.
- Forward returns remain future information.
- The 8-layer factor taxonomy remains the primary structure.
- Fixed 12 factors are not final.

## H. Research-Status and Workflow Priority Audit

The fixture context is lower-priority governance context. It may be visible in research-status and local dashboard summaries, but it must not override broader paper workflow priority or imply downstream authority.

The recorded validation evidence confirms research-status context visibility and safety fields remaining false. The fixture does not emit replay execution permission, forward label creation permission, training permission, stock_profile validation, buy-review permission, or trading permission.

## I. Safety and Non-Approval Boundary Audit

The v1.87.0 checkpoint remains report-only, diagnostic-only, local-only, and empty-or-synthetic-template-only.

It does not:

- collect official evidence;
- create filled evidence templates;
- accept evidence;
- close evidence;
- approve PIT admissibility;
- create active replay input;
- execute replay;
- create labels or metrics;
- train models;
- validate stock_profile;
- expand paper authority;
- approve buy-review;
- authorize trading;
- call brokers, place orders, send messages, call external APIs, or call LLM systems;
- run current-candidates;
- build snapshots;
- mutate `signal_semantics`;
- write `data/raw`, `data/processed`, or `data/cache`.

No buy-review or trading authority is created by v1.87.0 or by this audit.

## J. Candidate Next Routes Reviewed

| Route | Decision | Reason |
| --- | --- | --- |
| A. Historical Replay Official Manual Evidence Collection Template Fixture Post-v1.87 Generated Artifact Review / Wording Hardening Report-Only v0.1 | selected | Post-checkpoint artifact and live next-task/status wording review is the smallest safe step before no-hit, mixed-universe, or manual-fill policy work. |
| B. Historical Replay Reviewer No-Hit Acceptance Planning for 2024-04-02 etf_core Report-Only v0.1 | not selected | No-hit policy is important, but artifact and wording surfaces should be checked first after the v1.87 tag. |
| C. Historical Replay Mixed STOCK/ETF Universe Profile Policy Planning for legacy etf_core Report-Only v0.1 | not selected | Mixed STOCK/ETF policy remains visible, but it is not the immediate post-tag governance step. |
| D. Historical Replay Official Manual Evidence Collection Fill Protocol Design Report-Only v0.1 | not selected | Manual-fill protocol should wait until post-checkpoint artifact/wording review confirms the fixture surfaces are ready. |
| E. Pause repo work and manually collect official source/status evidence outside the repo | not selected | Repo-side governance can continue without collecting official evidence. |
| F. Continue next historical replay governance feature outside the template fixture branch | not selected | The template fixture branch should receive post-checkpoint artifact/wording review first. |

## K. Selected Next Route

Selected next route:

`Historical Replay Official Manual Evidence Collection Template Fixture Post-v1.87 Generated Artifact Review / Wording Hardening Report-Only v0.1`

## L. Why Selected Route Is Safe

The selected route is safe because it remains report-only and post-checkpoint bounded. It can review generated template artifacts and live next-task/status wording without collecting official evidence, filling templates, accepting or closing evidence, approving PIT admissibility, creating replay input, running replay, creating labels or metrics, training models, validating stock_profile, expanding paper authority, approving buy-review, or authorizing trading.

It is also smaller than no-hit acceptance policy, mixed-universe policy, or manual-fill protocol design.

## M. What Must Not Be Bundled

The selected route must not bundle:

- official evidence collection;
- official source fetching;
- website reads or web/API calls;
- source content reads;
- filled evidence templates;
- accepted evidence packets;
- evidence closure;
- PIT evidence closure;
- PIT approval;
- replay input;
- replay execution;
- replay decision freeze;
- forward labels;
- metric computation;
- training or evaluation;
- model work;
- stock_profile validation;
- paper expansion;
- real buy-review;
- trading;
- current-candidates;
- snapshots;
- signal semantics mutation;
- broker/API/order/message behavior;
- Project Source package files;
- Source update notes unless separately scoped;
- protected data writes.

## N. ChatGPT / Codex Mode Recommendation

Codex high is sufficient for the selected post-v1.87 generated artifact review / wording hardening task if it remains docs-only or report-only and does not run official evidence collection.

Use ChatGPT Pro or Pro Extended before any task introduces official evidence collection, source authority policy, no-hit sufficiency, ETF not-applicable authority, mixed-universe production policy, source reliability scoring, PIT adjudication, replay input readiness, replay execution, labels, metrics, training, model work, stock_profile, paper expansion, buy-review, performance validation, broker integration, order placement, message delivery, external API or LLM calls, or trading.

## O. Commit / Tag / Source Recommendation

Recommended commit message if ready:

```text
docs: audit official manual evidence collection template fixture post-v1.87 governance
```

Recommended tag decision: no tag for this post-v1.87 audit.

Recommended Source update decision: no Source update for this post-v1.87 audit.

## P. Recommended Next Task

Historical Replay Official Manual Evidence Collection Template Fixture Post-v1.87 Generated Artifact Review / Wording Hardening Report-Only v0.1

Expected final classification:

`HISTORICAL_REPLAY_OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_POST_V1_87_GOVERNANCE_AUDIT_CREATED_REPORT_ONLY`

Expected final verdict:

`HISTORICAL_REPLAY_OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_POST_V1_87_GOVERNANCE_READY_FOR_SELECTED_NEXT_ROUTE_REPORT_ONLY`
