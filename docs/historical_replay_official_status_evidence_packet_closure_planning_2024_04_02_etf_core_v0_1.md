# Historical Replay Official Status Evidence Packet Closure Planning for 2024-04-02 / etf_core v0.1

phase = historical_replay_official_status_evidence_packet_closure_planning_selected_sample
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_checkpoint = v1.84.0
latest_checkpoint_commit = 94775cf
latest_repo_commit = df7f300
selected_historical_decision_date = 2024-04-02
selected_universe = etf_core
official_status_evidence_closure_approved = no
selected_next_route = Historical Replay Official Status Evidence Packet Closure Worklist Design for 2024-04-02 etf_core Report-Only v0.1

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

## A. Decision / Status

This planning report is ready. It translates the accepted Historical Replay PIT Evidence Closure Worklist generated artifact review into a row-level official status evidence packet closure plan for the selected sample `2024-04-02 / etf_core`.

The selected next route is:

`Historical Replay Official Status Evidence Packet Closure Worklist Design for 2024-04-02 etf_core Report-Only v0.1`

The next step should design the exact row-level packet worklist before implementation. Existing packet and enrichment docs provide useful report-only patterns, but the selected sample has nine blocked rows, mixed stock/ETF profile handling, no accepted no-hit context, and all official status families missing. Direct implementation would be premature without a selected-sample packet design.

## B. Current Accepted State

The current accepted checkpoint remains `v1.84.0` at commit `94775cf`, and the latest repository commit for this planning task is `df7f300`. External ChatGPT Project Source has been updated to v1.84.0 and is not mirrored into the repository.

Historical Replay Training Loop remains the active mainline. The Personal MVP advisory refresh branch remains paused, not abandoned.

The accepted generated artifact review and hardening established that official status evidence gaps dominate all nine rows, while the generated artifact/status next-action now points to this official evidence planning stage.

## C. Selected Sample and 9-Row Scope

The selected sample is one historical decision date and one legacy universe label:

| Field | Value |
| --- | --- |
| historical_decision_date | `2024-04-02` |
| universe | `etf_core` |
| row_count | 9 |
| status | planning only |

Rows in scope:

| Symbol | Instrument type | Current profile guidance | Profile issue |
| --- | --- | --- | --- |
| `000001` | STOCK | `stock_core` | Stock row under legacy `etf_core`; review required. |
| `000002` | STOCK | `stock_core` | Stock row under legacy `etf_core`; review required. |
| `159915` | ETF | `etf_core` | ETF row; profile conflict not flagged. |
| `300750` | STOCK | `stock_core` | Stock row under legacy `etf_core`; review required. |
| `510300` | ETF | `etf_core` | ETF row; profile conflict not flagged. |
| `600000` | STOCK | `stock_core` | Stock row under legacy `etf_core`; review required. |
| `600519` | STOCK | `stock_core` | Stock row under legacy `etf_core`; review required. |
| `601318` | STOCK | `stock_core` | Stock row under legacy `etf_core`; review required. |
| `688981` | STOCK | `stock_core` | Stock row under legacy `etf_core`; review required. |

Leading-zero symbols must remain strings in every future packet, worklist, CSV, and status view.

## D. Generated Worklist Blocker Recap

The accepted generated artifact review recorded:

| Count | Value |
| --- | ---: |
| row_count | 9 |
| blocked_count | 9 |
| missing_evidence_count | 9 |
| context_only_count | 9 |
| needs_manual_review_count | 9 |
| no_hit_review_needed_count | 9 |
| no_hit_accepted_context_count | 0 |
| closure_ready_not_pit_approved_count | 0 |
| profile_conflict_count | 7 |
| survivorship_warning_count | 9 |

Blocker families affecting all nine rows:

- future-dated hint;
- missing authoritative hint;
- missing official status evidence;
- missing permission class;
- missing reviewer authority;
- missing revision id;
- missing source hash;
- missing source id;
- missing survivorship rationale;
- missing universe membership evidence;
- universe as-of date after signal date.

Seven stock rows also carry an unreviewed profile-conflict blocker.

## E. Official Status Evidence Families

Future official status evidence packet work should organize, but not approve, these families:

1. Listed or active status as of `2024-04-02`.
2. Delisted or not-delisted status as of `2024-04-02`.
3. ST or no-ST status for STOCK rows.
4. ETF not-applicable policy for ETF rows where ST does not apply.
5. Suspension or trading-status evidence, or a reviewed not-applicable policy.
6. Universe membership evidence as of `2024-04-02`.
7. Survivorship rationale.
8. Source lineage, raw reference, permission, revision, and available-time context for each evidence family.

Each family must stay row-level and must carry explicit source, timing, reviewer, quality, limitation, and non-approval fields.

## F. Listed / Active Status Evidence Plan

For each row, future packet design should require evidence that the symbol existed and was eligible as a listed or active instrument at the decision date.

Required fields:

| Field | Requirement |
| --- | --- |
| listed_status_evidence | Official or accepted public evidence text/category. |
| listed_status_source_id | Source registry reference or planned source identifier. |
| listed_status_available_time | Time the evidence was available to a decision-time process. |
| listed_status_review_status | Missing, needs review, accepted context, or blocked. |
| limitation_note | Required when evidence is partial, inferred, or source-family limited. |

Listed or active status evidence cannot by itself prove not-delisted status, no-ST status, suspension status, universe membership, or survivorship resolution.

## G. Delisted / Not-Delisted Status Evidence Plan

Each row needs date-specific not-delisted context to reduce survivorship leakage risk. The packet design should distinguish:

- explicit official delisting status;
- no delisting record found within a reviewed source/query window;
- symbol-level listing context without daily delisting proof;
- unsupported no-hit context.

No-hit context must require reviewer acceptance before it can become supporting context, and even accepted no-hit context remains supporting context only. It must not be treated as source reliability scoring or final PIT approval.

## H. ST / No-ST and ETF Not-Applicable Policy Plan

For the seven STOCK rows, future packet design should require ST/no-ST evidence as of `2024-04-02`.

STOCK rows:

| Requirement | Notes |
| --- | --- |
| `st_status_evidence` | Required. |
| `st_status_source_id` | Required. |
| `st_status_available_time` | Required. |
| `st_status_review_status` | Missing, needs review, accepted context, or blocked. |

ETF rows `159915` and `510300` should not be forced into a stock ST/no-ST field. They require an ETF not-applicable policy field, such as `st_status_not_applicable_reason`, and should still require ETF-specific source and universe membership review.

## I. Suspension / Trading Status Evidence Plan

The future packet design should require either:

- official or accepted public suspension/trading-status evidence for the decision date; or
- a reviewed not-applicable policy if the source family cannot provide same-day suspension status.

Local same-day market or quotation presence may be useful traded-presence context, but it does not automatically prove no suspension, not-delisted, no-ST, universe membership, or survivorship resolution.

## J. Universe Membership Evidence Plan

All nine rows have missing universe membership evidence and an inherited universe as-of date that is later than the signal date. Future packet design should require:

| Field | Requirement |
| --- | --- |
| universe_membership_evidence | Row-level source-backed membership context as of `2024-04-02` or before. |
| universe_membership_source_id | Source identifier for membership evidence. |
| universe_membership_available_time | Decision-time availability of membership evidence. |
| universe_membership_revision_id | Revision or snapshot id used for membership evidence. |
| universe_membership_review_status | Missing, needs review, accepted context, or blocked. |
| legacy_universe_label | Preserve `etf_core` as legacy label. |
| recommended_profile | Preserve stock/ETF profile recommendation. |

Membership evidence must not infer ETF validity from the legacy label alone.

## K. Survivorship Rationale Plan

All nine rows carry survivorship warnings and lack survivorship rationale. A future packet design should include:

- `survivorship_warning_flag`;
- `survivorship_rationale`;
- `survivorship_source_id`;
- `survivorship_available_time`;
- `survivorship_review_status`;
- `survivorship_limitation_note`.

Survivorship rationale must explain why the row is not present only because it survived into a later universe file. No-hit context cannot resolve survivorship by itself.

## L. Source / Raw-Reference / Permission / Revision / Available-Time Requirements

Each official evidence family should carry these fields:

| Field | Requirement |
| --- | --- |
| source_id | Stable source registry reference or planned id. |
| source_name | Human-readable source name. |
| source_type | Official, exchange, provider, reviewed local, or manual context. |
| permission_class | Explicit allowed/report-only permission context. |
| raw_reference | Raw document, table, file, query, page, or evidence record reference. |
| raw_reference_type | CSV, HTML, PDF, API-response record, manual note, or other controlled type. |
| source_hash_preview | Disclosure-safe hash preview or explicit missing value. |
| source_hash_disclosure_policy | Preview-only or hidden-full-hash policy. |
| revision_id | Source revision, snapshot, publication, or reviewed version id. |
| revision_id_type | Controlled type explaining revision semantics. |
| available_time | Decision-time availability timestamp. |
| available_time_timezone | Explicit timezone or reviewed default policy. |
| review_time | Human review time, if applicable. |
| reviewer_id | Required for accepted context or no-hit acceptance. |
| limitation_note | Required for inferred, partial, no-hit, or not-applicable evidence. |

`source_hash_preview` is not source hash validation. `local_file_hash_preview` is not PIT evidence by itself.

## M. Reviewer No-Hit Interaction Boundary

Reviewer no-hit context is relevant for missing source hits, delisting/ST/suspension query windows, and survivorship rationale. It must remain a supporting context workflow:

- reviewer no-hit acceptance is not source reliability scoring;
- no-hit acceptance cannot override missing source id, missing revision id, missing available-time proof, or failed quality status;
- no-hit acceptance cannot approve rows;
- no-hit acceptance cannot create replay inputs;
- no-hit acceptance must remain visible as reviewer context only.

The generated worklist has nine `no_hit_review_needed` rows and zero accepted no-hit contexts, so no-hit remains an open family.

## N. Mixed STOCK / ETF Profile Handling

The legacy `etf_core` sample includes seven STOCK rows and two ETF rows. Future official evidence packet design must preserve:

- `legacy_universe_label = etf_core`;
- instrument type;
- recommended profile;
- profile conflict flag;
- profile conflict reason;
- profile policy status.

STOCK rows need stock-specific status evidence, including ST/no-ST handling. ETF rows need ETF-specific not-applicable policy for ST, plus ETF membership and trading-status context. Mixed profile handling is important, but it does not block planning the official status packet worklist.

## O. Row-Level Closure Planning Table

| Symbol | Instrument | Required official families | Current planning status |
| --- | --- | --- | --- |
| `000001` | STOCK | Listed/active, not-delisted, no-ST, suspension/trading, membership, survivorship | Needs row-level packet design. |
| `000002` | STOCK | Listed/active, not-delisted, no-ST, suspension/trading, membership, survivorship | Needs row-level packet design. |
| `159915` | ETF | Listed/active, not-delisted, ETF ST not-applicable policy, suspension/trading, membership, survivorship | Needs row-level packet design. |
| `300750` | STOCK | Listed/active, not-delisted, no-ST, suspension/trading, membership, survivorship | Needs row-level packet design. |
| `510300` | ETF | Listed/active, not-delisted, ETF ST not-applicable policy, suspension/trading, membership, survivorship | Needs row-level packet design. |
| `600000` | STOCK | Listed/active, not-delisted, no-ST, suspension/trading, membership, survivorship | Needs row-level packet design. |
| `600519` | STOCK | Listed/active, not-delisted, no-ST, suspension/trading, membership, survivorship | Needs row-level packet design. |
| `601318` | STOCK | Listed/active, not-delisted, no-ST, suspension/trading, membership, survivorship | Needs row-level packet design. |
| `688981` | STOCK | Listed/active, not-delisted, no-ST, suspension/trading, membership, survivorship | Needs row-level packet design. |

No row is closure-ready in this planning report.

## P. What Future Official Evidence Packet Work May Do

A future report-only official evidence packet worklist design may:

- define selected-sample packet rows and required fields;
- define source family mapping without fetching data;
- define row-level status vocabulary;
- define blocker and warning semantics;
- define not-applicable policies for ETF rows;
- define reviewer no-hit handoff requirements;
- define artifact schemas for a later packet core;
- define focused tests for row coverage and non-approval fields.

It may not close evidence or approve downstream workflows.

## Q. What Must Wait for Separate Pro / Pro Extended Design

Use ChatGPT Pro / Pro Extended before:

- deciding ambiguous official source hierarchy;
- adjudicating source reliability scoring;
- treating no-hit evidence as sufficient support;
- defining production-grade available-time policy;
- resolving mixed stock/ETF production universe policy;
- deciding if market quotation presence can support trading-status inference;
- designing actual PIT admissibility;
- connecting evidence packets to replay input readiness;
- moving toward labels, training, metrics, model, stock-profile, paper, buy-review, or trading gates.

## R. Candidate Next Routes

| Route | Decision | Reason |
| --- | --- | --- |
| A. Historical Replay Official Status Evidence Packet Closure Worklist Design for 2024-04-02 etf_core Report-Only v0.1 | Selected. | The selected sample needs a row-level official evidence packet design before implementation. |
| B. Historical Replay Official Status Evidence Packet Core Report-Only v0.1 | Not selected. | Existing packet docs are useful, but selected-sample fields, mixed profile handling, and no-hit handoff need design first. |
| C. Historical Replay Reviewer No-Hit Acceptance Planning for 2024-04-02 etf_core Report-Only v0.1 | Reserve. | No-hit is open for all rows, but official evidence family mapping should come first. |
| D. Historical Replay Mixed Universe Policy Planning for legacy etf_core Report-Only v0.1 | Reserve. | Mixed profile risk is real, but it can be represented in the packet design. |
| E. Pause and manually collect official status evidence outside the repo | Not selected. | Planning can proceed safely without data fetching or evidence creation. |

## S. Selected Next Route

Selected route:

`Historical Replay Official Status Evidence Packet Closure Worklist Design for 2024-04-02 etf_core Report-Only v0.1`

## T. Why Selected Route Is Safe

The selected route is safe because it remains at the schema and row-design layer. It can define exactly what official evidence packet rows must contain without fetching data, creating packets, closing evidence, approving PIT status, or touching downstream replay/training/trading workflows.

It also reduces risk before implementation by preserving leading-zero symbols, mixed profile flags, no-hit boundaries, survivorship warnings, and source/available-time requirements.

## U. Validation Requirements for Selected Next Task

The selected next task should:

1. Start from a clean worktree.
2. Inspect this planning report, the generated artifact review, worklist docs, existing official packet docs, enrichment docs, no-hit docs, and checklist validator docs.
3. Create only a docs/report design artifact unless explicitly scoped otherwise.
4. Preserve row-level symbols as strings.
5. Include all nine selected rows.
6. Include official evidence families and source/timing/revision fields.
7. Include non-approval safety fields.
8. Run `git status --short --branch`, `git describe --tags --always`, `git diff --check`, static scan, and protected tracked scan.
9. Avoid all runtime packet generation and protected data writes.

## V. What Must Not Be Bundled

The selected next task must not bundle source/test/runtime changes, evidence packet generation, official evidence closure, PIT evidence closure, PIT admissibility approval, current-candidates, snapshots, replay input, replay execution, decision freeze, forward labels, training/evaluation, metric computation, model work, stock-profile validation, paper expansion, buy-review, trading, broker/API/order/message behavior, external API or LLM calls, Project Source files, checkpoint docs, or protected data writes.

## W. ChatGPT / Codex Mode Recommendation

Use Codex high for the selected row-level worklist design. Escalate to ChatGPT Pro / Pro Extended before any subjective source hierarchy, available-time adjudication, no-hit acceptance sufficiency, mixed universe production policy, evidence-to-readiness conversion, or downstream replay/training/model/buy-review/trading gate is introduced.

## X. Commit / Tag / Source Recommendation

If this docs-only planning report is accepted, a manual commit may use:

`docs: plan official status evidence packet closure for replay sample`

No tag is recommended for this planning report alone. No immediate Project Source update is recommended unless the user decides this report materially changes the external Source roadmap.

## Y. Recommended Next Task

Recommended next task:

`Historical Replay Official Status Evidence Packet Closure Worklist Design for 2024-04-02 etf_core Report-Only v0.1`

Goal for that task: design the exact selected-sample official status evidence packet worklist schema, row set, status vocabulary, source/timing/revision requirements, reviewer no-hit handoff, mixed stock/ETF handling, survivorship handling, and non-approval safety fields without generating evidence packets or closing PIT evidence.
