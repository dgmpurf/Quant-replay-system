# Historical Replay Official Source Hierarchy and Evidence Collection Worklist Design for 2024-04-02 / etf_core v0.1

phase = historical_replay_official_source_hierarchy_and_evidence_collection_worklist_design_2024_04_02_etf_core
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_checkpoint = v1.85.0
latest_checkpoint_commit = d83a92e
latest_checkpoint_tag = v1.85.0
latest_repo_commit = ed938ee
selected_historical_decision_date = 2024-04-02
selected_universe = etf_core
official_source_hierarchy_worklist_design_created = yes
source_hierarchy_core_approved = no
official_evidence_collection_approved = no
selected_next_route = Historical Replay Official Source Hierarchy and Evidence Collection Worklist Core Report-Only v0.1

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

## A. Decision / Status

This docs-only design report is ready. It defines a future deterministic, report-only worklist contract for official source hierarchy and evidence collection for the selected historical replay sample `2024-04-02 / etf_core`.

This design does not implement the worklist. It does not fetch, download, query, read, collect, accept, or close official evidence. It does not approve point-in-time admissibility, create active replay input, run replay, freeze replay decisions, create labels, compute metrics, train models, expand stock profile or paper authority, approve real buy-review, or authorize trading.

Selected next route:

`Historical Replay Official Source Hierarchy and Evidence Collection Worklist Core Report-Only v0.1`

The selected route is a deterministic blocked/report-only core scaffold, not evidence collection and not evidence closure.

## B. Current Accepted State

The current accepted checkpoint is `v1.85.0` at commit `d83a92e`. The current repository head for this design task is `ed938ee`, which committed the official source hierarchy and evidence collection planning report.

The prior v1.85 official-status worklist and generated artifact review established these stable selected-sample facts:

| Field | Value |
| --- | ---: |
| row_count | 9 |
| stock_row_count | 7 |
| etf_row_count | 2 |
| blocked_count | 9 |
| missing_official_evidence_count | 9 |
| needs_manual_review_count | 9 |
| no_hit_review_needed_count | 9 |
| no_hit_accepted_context_count | 0 |
| packet_row_ready_not_pit_approved_count | 0 |
| profile_conflict_count | 7 |
| survivorship_warning_count | 9 |

Artifact hardening is complete. The current source hierarchy planning layer selected this worklist design as the next safe route. External Project Source is updated to v1.85.0 and is not mirrored into the repository.

## C. Selected Sample and Row Identity Contract

The future worklist must preserve the exact selected row set and all symbols as strings, including leading zeros.

| Symbol | Instrument type | Legacy universe label | Recommended profile | Profile conflict |
| --- | --- | --- | --- | --- |
| `000001` | STOCK | `etf_core` | `stock_core` | true |
| `000002` | STOCK | `etf_core` | `stock_core` | true |
| `159915` | ETF | `etf_core` | `etf_core` | false |
| `300750` | STOCK | `etf_core` | `stock_core` | true |
| `510300` | ETF | `etf_core` | `etf_core` | false |
| `600000` | STOCK | `etf_core` | `stock_core` | true |
| `600519` | STOCK | `etf_core` | `stock_core` | true |
| `601318` | STOCK | `etf_core` | `stock_core` | true |
| `688981` | STOCK | `etf_core` | `stock_core` | true |

Required row identity fields:

| Field | Rule |
| --- | --- |
| `source_hierarchy_worklist_id` | Required deterministic worklist id. |
| `historical_decision_date` | Required and fixed to `2024-04-02`. |
| `universe_name` | Required and fixed to `etf_core`. |
| `symbol` | Required string; leading zeros preserved. |
| `instrument_type` | Required controlled value, `STOCK` or `ETF`. |
| `legacy_universe_label` | Required and fixed to `etf_core`. |
| `recommended_profile` | Required row-specific recommendation. |
| `profile_conflict` | Required boolean. |
| `profile_conflict_reason` | Required for STOCK rows under the legacy ETF label. |
| `selected_sample_context_only` | Required true. |

No future worklist row may infer universe membership from the legacy label alone.

## D. Source Hierarchy Worklist Purpose

The worklist purpose is to organize what official evidence must later be collected manually, not to collect it now. The future worklist should separate:

- row identity;
- instrument family;
- source class;
- evidence family;
- raw reference requirement;
- source permission requirement;
- source revision requirement;
- decision-time availability requirement;
- reviewer no-hit handoff;
- survivorship rationale;
- blocker status;
- non-approval safety fields.

The worklist should make every unresolved gap explicit. A complete-looking source hierarchy row is still only a manual collection scaffold until a separate future task collects, reviews, and accepts evidence under an approved scope.

## E. Evidence-Family Requirement Design

Each selected row should have one or more worklist rows per evidence family. The future core should generate the missing evidence surface without pretending evidence exists.

| Evidence family | Required for | Purpose | Default state |
| --- | --- | --- | --- |
| listed_active_status | STOCK and ETF | Show listed or active instrument context for the decision date. | collection_required |
| delisted_not_delisted_status | STOCK and ETF | Reduce survivor-only inclusion risk. | collection_required |
| st_no_st_status | STOCK | Show special-treatment context for STOCK rows. | collection_required |
| etf_st_not_applicable_policy | ETF | Explain why stock ST evidence is not applicable while retaining ETF status review. | manual_review_required |
| suspension_trading_status | STOCK and ETF | Show suspension or trading-status context for the decision date. | collection_required |
| universe_membership | STOCK and ETF | Show selected universe membership as of or before the decision date. | collection_required |
| source_lineage | All source-family rows | Require source id, raw reference, permission, revision, timing, and quality fields. | lineage_fields_missing |
| reviewer_no_hit_handoff | Rows without source hits | Define searched-source and query-window handoff fields. | no_hit_query_required |
| survivorship_rationale | STOCK and ETF | Explain why the row is not present only because it survived later. | collection_required |

Same-day quotation presence is context only. It cannot automatically prove listed status, not-delisted status, no-ST status, not-suspended status, universe membership, or survivorship rationale.

## F. Source-Class Hierarchy Design

The future worklist should contain source-class rows even before evidence is collected. Each source class must be explicit about authority, permission, revision, and timing requirements.

| Rank | Source class | Source id pattern | Source type | Evidence families | Permission class | Raw reference type | Revision id type | Available-time requirement | Missing blocker |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Exchange official listing and trading-status source | `exchange_official_listing_status_{market}` | official_exchange | listed_active_status, delisted_not_delisted_status, suspension_trading_status | public_review_allowed | official page, file, bulletin, or notice reference | file date, notice id, publication id, or archived source revision | publication or file availability not after decision time | blocker_missing_source_class |
| 2 | Exchange disclosure or issuer announcement source | `exchange_disclosure_{market}_{symbol}` | official_disclosure | st_no_st_status, delisted_not_delisted_status, suspension_trading_status | public_review_allowed | announcement id or disclosure record | announcement id plus publish timestamp | publish and availability time not after decision time | blocker_missing_raw_reference |
| 3 | Official quotation or trading-status publication source | `official_market_quote_{market}` | official_market_data | suspension_trading_status supporting context | public_review_allowed | official daily file or quote page | file date, data batch id, publication timestamp | publication availability not after decision time | blocker_missing_available_time |
| 4 | ETF issuer or fund company disclosure source | `etf_issuer_disclosure_{fund_code}` | official_fund_issuer | listed_active_status, delisted_not_delisted_status, etf_st_not_applicable_policy, suspension_trading_status | public_review_allowed | fund announcement, product page, or filing | announcement id, filing id, or page revision | publish and availability time not after decision time | blocker_missing_etf_st_not_applicable_policy |
| 5 | Index or provider membership source | `index_or_universe_membership_{provider}_{universe}` | official_or_reviewed_provider | universe_membership | public_or_reviewed_context | constituent page, membership file, or reviewed export | effective date, publication id, file revision, or provider snapshot | effective and publication availability not after decision time | blocker_missing_universe_membership_source |
| 6 | Reviewed local manual evidence metadata source | `reviewed_local_csv_official_status_{review_id}` | reviewed_local_artifact | source_lineage, reviewed metadata handoff | local_review_only | reviewed metadata row | package version and reviewer revision id | source available_time plus reviewed_at; reviewed_at alone is insufficient | blocker_missing_reviewer_handoff |
| 7 | Reviewer no-hit query log source | `reviewer_no_hit_official_status_{review_id}` | reviewed_no_hit_log | reviewer_no_hit_handoff, survivorship_rationale context | local_review_only | query log or reviewer attestation | review log id | reviewed_at plus query-window timing; cannot override source/timing gaps | blocker_missing_no_hit_query_window |

Ranks are design priorities only. They do not approve source authority, source reliability, or evidence sufficiency.

## G. STOCK Row Source/Evidence Policy

STOCK rows are `000001`, `000002`, `300750`, `600000`, `600519`, `601318`, and `688981`.

Every STOCK row should receive worklist rows for:

| Evidence family | Preferred source classes | Required default blockers |
| --- | --- | --- |
| listed_active_status | exchange official listing and trading-status source | blocker_missing_source_id, blocker_missing_raw_reference, blocker_missing_revision_id, blocker_missing_available_time |
| delisted_not_delisted_status | exchange listing/delisting source or disclosure source | blocker_missing_source_id, blocker_missing_raw_reference, blocker_missing_revision_id, blocker_missing_available_time |
| st_no_st_status | exchange disclosure or official ST source | blocker_missing_stock_st_source |
| suspension_trading_status | exchange trading-status source and official quotation source | blocker_missing_source_id, blocker_missing_available_time |
| universe_membership | index/provider membership source or reviewed universe source | blocker_missing_universe_membership_source |
| survivorship_rationale | source-backed status plus reviewer rationale | blocker_missing_survivorship_rationale |
| profile_conflict_review | reviewed local metadata source | blocker_profile_conflict_unreviewed |

The STOCK rows remain `recommended_profile=stock_core` and `profile_conflict=true` until a separate mixed universe policy or evidence review resolves the mismatch.

## H. ETF Row Source/Evidence Policy

ETF rows are `159915` and `510300`.

Every ETF row should receive worklist rows for:

| Evidence family | Preferred source classes | Required default blockers |
| --- | --- | --- |
| listed_active_status | exchange ETF listing/trading source or ETF issuer source | blocker_missing_source_id, blocker_missing_revision_id, blocker_missing_available_time |
| delisted_not_delisted_status | exchange ETF listing/delisting source or ETF issuer source | blocker_missing_source_id, blocker_missing_raw_reference, blocker_missing_revision_id |
| etf_st_not_applicable_policy | ETF issuer source, exchange rule context, or reviewed policy metadata | blocker_missing_etf_st_not_applicable_policy |
| suspension_trading_status | exchange ETF trading-status source and official quotation source | blocker_missing_source_id, blocker_missing_available_time |
| universe_membership | ETF/index/provider membership source or reviewed universe source | blocker_missing_universe_membership_source |
| survivorship_rationale | source-backed ETF status plus reviewer rationale | blocker_missing_survivorship_rationale |

ETF rows should not be forced into stock ST/no-ST evidence. The not-applicable policy is itself a required review field; it does not skip ETF status review.

## I. Source Lineage / Permission / Revision / Available-Time Schema

Every future source-family row should include these fields:

| Field | Required behavior |
| --- | --- |
| `source_family_row_id` | Deterministic id joining symbol, evidence family, and source class. |
| `source_class_rank` | Proposed hierarchy rank. |
| `source_id` | Required controlled source id or missing blocker. |
| `source_name` | Human-readable name without private credentials or secrets. |
| `source_type` | Controlled source class type. |
| `permission_class` | Required permission context; source name alone is not permission. |
| `raw_reference_type` | Required page, file, announcement, filing, archive, reviewed metadata, or no-hit log type. |
| `raw_reference` | Required stable reference field; may be missing in scaffold rows. |
| `source_hash_preview` | Optional preview only; never a full hash disclosure requirement in docs. |
| `source_hash_disclosure_policy` | Required when hash preview is present or intentionally hidden. |
| `local_file_hash_preview` | Optional reviewed local identity preview; not PIT evidence by itself. |
| `revision_id` | Required source revision, publication id, announcement id, effective date, or reviewed package version. |
| `revision_id_type` | Required controlled meaning of revision id. |
| `available_time` | Required decision-time availability timestamp or missing blocker. |
| `available_time_timezone` | Required timezone or reviewed default policy. |
| `available_time_policy` | Required rule explaining source availability, not event date alone. |
| `quality_status` | Required controlled quality state. |
| `limitation_note` | Required for warning, no-hit, inferred, partial, or not-applicable context. |

Available time after the decision boundary must block the row. Event date, period end, file creation time, and reviewer time alone are not sufficient available-time evidence.

## J. Reviewer No-Hit Query Handoff Schema

The current sample has nine no-hit review-needed rows and zero no-hit accepted-context rows. The future worklist should preserve no-hit as a handoff surface only.

| Field | Requirement |
| --- | --- |
| `no_hit_review_needed` | Required boolean. |
| `no_hit_source_family` | Required source or evidence family searched. |
| `no_hit_query_window_start` | Required for any no-hit review-needed row. |
| `no_hit_query_window_end` | Required for any no-hit review-needed row. |
| `no_hit_query_terms` | Required query terms or controlled query description. |
| `no_hit_result` | Required controlled result: missing, found, conflicting, inconclusive. |
| `no_hit_acceptance_status` | Required and default `not_accepted`. |
| `no_hit_reviewer_required` | Required true when no-hit is unresolved. |
| `reviewer_id` | Required before accepted reviewer context. |
| `reviewer_role` | Required before accepted reviewer context. |
| `reviewer_scope` | Required before accepted reviewer context. |
| `no_hit_acceptance_rationale` | Required only for later accepted supporting context. |
| `limitation_note` | Required for any no-hit context. |

No-hit query context is not source reliability scoring. Reviewer no-hit acceptance cannot override missing source, permission, revision, timing, quality, survivorship, or profile-conflict blockers.

## K. Survivorship Rationale Schema

Every selected row should include survivorship rationale fields:

| Field | Requirement |
| --- | --- |
| `survivorship_warning_flag` | Required and true for all nine default rows. |
| `survivorship_evidence_family` | Required. |
| `survivorship_source_id` | Required source id or missing blocker. |
| `survivorship_raw_reference` | Required raw reference or missing blocker. |
| `survivorship_revision_id` | Required revision id or missing blocker. |
| `survivorship_available_time` | Required decision-time availability or missing blocker. |
| `survivorship_rationale` | Required narrative or controlled rationale. |
| `survivorship_review_status` | Required controlled review status. |
| `survivorship_limitation_note` | Required while evidence remains partial or uncollected. |

Survivorship rationale cannot be inferred from current listing status, later symbol availability, later universe files, same-day quotation presence, or no-hit context alone.

## L. Status Vocabulary

Allowed future source hierarchy worklist statuses:

| Status | Meaning |
| --- | --- |
| source_hierarchy_worklist_created_report_only | The future report-only worklist exists as a scaffold. |
| collection_required | Official evidence still needs manual collection. |
| manual_review_required | Human review is needed before any supporting context can be accepted. |
| no_hit_query_required | Reviewer no-hit query fields must be filled or reviewed. |
| context_only_not_evidence | Row has context only, not evidence closure. |
| source_family_missing | Required source family is missing. |
| lineage_fields_missing | Source id, raw reference, permission, revision, or timing fields are missing. |
| blocked | One or more blockers remain. |
| row_ready_for_manual_collection_not_pit_approved | Row may be structurally ready for manual collection, but is not PIT approval. |

No status may imply evidence closure, PIT approval, replay input readiness, buy-review readiness, performance validation, or trading permission.

## M. Blocker Vocabulary

Allowed blocker vocabulary:

| Blocker | Meaning |
| --- | --- |
| blocker_missing_source_class | Required source class row is missing. |
| blocker_missing_source_id | Source id is missing. |
| blocker_missing_raw_reference | Raw evidence reference is missing. |
| blocker_missing_permission_class | Permission class is missing. |
| blocker_missing_revision_id | Revision id is missing. |
| blocker_missing_available_time | Available-time field is missing. |
| blocker_available_time_after_decision | Available time is after the decision boundary. |
| blocker_missing_timezone_policy | Timezone policy is missing. |
| blocker_missing_quality_status | Quality status is missing. |
| blocker_missing_limitation_note | Limitation note is missing where required. |
| blocker_missing_reviewer_handoff | Reviewer handoff fields are missing. |
| blocker_missing_no_hit_query_window | No-hit query window is missing. |
| blocker_missing_survivorship_rationale | Survivorship rationale is missing. |
| blocker_missing_universe_membership_source | Universe membership source is missing. |
| blocker_missing_stock_st_source | STOCK ST/no-ST source is missing. |
| blocker_missing_etf_st_not_applicable_policy | ETF not-applicable policy is missing. |
| blocker_profile_conflict_unreviewed | Mixed STOCK/ETF profile conflict is unresolved. |
| blocker_forbidden_downstream_flag | A forbidden downstream field is true. |

Future implementation may add stricter blockers only if it stays report-only and tests prove the blockers do not create evidence closure.

## N. Future Artifact Contract

A future report-only worklist core may create only manual diagnostic artifacts under its own output root. Proposed files:

| Future artifact | Purpose |
| --- | --- |
| `metadata.json` | Aggregate ids, counts, status, workflow stage, report-only flags, and safety fields. |
| `official_source_hierarchy_matrix.csv` | Source class hierarchy, source id patterns, permission, raw reference, revision, and timing requirements. |
| `official_evidence_collection_worklist.csv` | Row-by-source-family collection rows for the exact nine selected symbols. |
| `official_evidence_family_requirement_matrix.csv` | Evidence families by instrument type and required source classes. |
| `official_source_lineage_requirement_matrix.csv` | Shared source id, permission, revision, available-time, hash-preview, reviewer, and limitation fields. |
| `official_no_hit_query_handoff_matrix.csv` | No-hit query windows, reviewer handoff, and acceptance placeholders. |
| `official_collection_blocker_matrix.csv` | Blocker vocabulary and row/source-family blocker mapping. |
| `official_collection_safety_flags.json` | Required false downstream safety flags. |
| `official_source_hierarchy_and_evidence_collection_worklist_report.md` | Human-readable report and limitations. |

The future root should be separate from the existing official-status evidence packet closure worklist root so the source hierarchy worklist does not mutate v1.85 artifacts.

## O. Field-Level Validation Rules

Future implementation should validate:

1. Exactly nine selected symbols exist.
2. Symbols are strings and leading zeros are preserved.
3. Instrument type matches the selected sample table.
4. `historical_decision_date` equals `2024-04-02`.
5. `universe_name` and `legacy_universe_label` equal `etf_core`.
6. STOCK rows carry `recommended_profile=stock_core` and `profile_conflict=true`.
7. ETF rows carry `recommended_profile=etf_core` and `profile_conflict=false`.
8. Every row has all required evidence-family worklist rows.
9. STOCK rows require `st_no_st_status` family rows.
10. ETF rows require `etf_st_not_applicable_policy` family rows.
11. Every source-family row carries or blocks on source id, raw reference, permission class, revision id, available time, timezone policy, quality status, and limitation note.
12. Any available time after decision time creates `blocker_available_time_after_decision`.
13. Any no-hit row defaults to `not_accepted`.
14. No-hit context cannot clear source, timing, revision, quality, profile, or survivorship blockers by itself.
15. Any warning requires a limitation note.
16. Any forbidden downstream safety field set true creates `blocker_forbidden_downstream_flag`.
17. No forward labels or future-return fields may appear in decision-time worklist rows.

## P. Focused Test Plan for Later Implementation

Later focused tests should cover:

| Test area | Expected assertion |
| --- | --- |
| row set | Exact nine symbols and leading zeros preserved. |
| row families | Seven STOCK rows and two ETF rows. |
| profile context | STOCK rows have profile conflicts; ETF rows do not. |
| evidence family coverage | All required evidence-family rows exist. |
| source class coverage | Source hierarchy matrix includes all proposed source classes. |
| lineage requirements | Missing source id, raw reference, permission, revision, available time, timezone, quality, and limitation fields block. |
| STOCK ST policy | STOCK rows require ST/no-ST source family. |
| ETF ST policy | ETF rows require not-applicable policy. |
| no-hit handoff | All default no-hit rows require review and none are accepted. |
| survivorship | All rows expose survivorship warning and missing-rationale blocker. |
| safety flags | All downstream approval/trading/data-write fields remain false. |
| static wording | No worklist status implies PIT approval, replay readiness, buy-review, performance validation, or trading. |
| output root guard | Future implementation writes only manual diagnostic artifacts. |

Suggested focused commands for the later implementation task, not this design task:

```text
.venv\Scripts\python.exe -m pytest tests/test_historical_replay_official_source_hierarchy_and_evidence_collection_worklist.py -q
.venv\Scripts\python.exe -m pytest tests/test_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_views.py -q
```

## Q. Safety and Non-Approval Boundary

This design does not:

- implement the worklist;
- fetch, download, query, scrape, read, or collect official source data;
- open official websites or call web/API systems;
- create official evidence packets with accepted evidence;
- close official evidence;
- close PIT evidence;
- approve PIT admissibility;
- create active replay input;
- execute replay;
- freeze replay decisions;
- create forward labels;
- compute metrics;
- train models or adjust weights, formulas, thresholds, or parameters;
- create stock profile validation;
- expand paper workflow authority;
- approve real buy-review;
- authorize trading;
- call broker, order, message, external API, or LLM systems;
- write `data/raw`, `data/processed`, or `data/cache`;
- run current-candidates or build snapshots.

A worklist row is not PIT approval. `row_ready_for_manual_collection_not_pit_approved` is not PIT admissible. `no_hit_query_required` is not source reliability scoring. `source_hash_preview` is not source hash validation. `local_file_hash_preview` is not PIT evidence by itself. Forward returns remain future information. The 8-layer factor taxonomy remains the primary structure, and fixed 12 factors are not final.

## R. Candidate Next Routes

| Route | Decision | Reason |
| --- | --- | --- |
| A. Historical Replay Official Source Hierarchy and Evidence Collection Worklist Core Report-Only v0.1 | Selected | The design is deterministic, blocked by default, and can be safely implemented as a report-only source hierarchy worklist. |
| B. Historical Replay Official Manual Evidence Collection Template Docs-Only v0.1 | Not selected | Human-fill templates are useful, but the deterministic core scaffold should establish the row/source/evidence contract first. |
| C. Historical Replay Reviewer No-Hit Acceptance Planning for 2024-04-02 etf_core Report-Only v0.1 | Reserve | No-hit remains open for all rows, but source-family and evidence-family worklist rows should exist before acceptance policy. |
| D. Historical Replay Mixed STOCK/ETF Universe Policy Planning for legacy etf_core Report-Only v0.1 | Reserve | Mixed universe policy matters, but profile conflict can be carried as blocked report-only context first. |
| E. Pause repo work and manually collect official status evidence outside the repo | Not selected | Repo-side deterministic worklist design/core remains safe before manual evidence collection. |
| F. Historical Replay Official Source Hierarchy Worklist Design Hardening Report-Only v0.1 | Not selected | No design hardening blocker was found. |

## S. Selected Next Route

`Historical Replay Official Source Hierarchy and Evidence Collection Worklist Core Report-Only v0.1`

Goal for that task: implement a deterministic report-only source hierarchy worklist scaffold for the exact nine `2024-04-02 / etf_core` rows, generating only manual diagnostic artifacts and keeping every row blocked or manual-review-required by default.

## T. Why Selected Route Is Safe

The selected route is safe because it can create structure without collecting evidence. It can prove row coverage, source hierarchy coverage, evidence-family coverage, lineage-field blockers, no-hit handoff fields, and safety flags while preserving all downstream non-approval boundaries.

It is smaller than no-hit acceptance, mixed-universe production policy, manual evidence collection, evidence closure, or PIT approval. It keeps source hierarchy work explicit and auditable before any human-filled evidence template is used.

## U. What Must Not Be Bundled

The selected next route must not bundle source fetching, source content reads, official evidence collection, accepted evidence packets, evidence closure, PIT approval, active replay input, replay execution, replay decision freeze, labels, metrics, training/model work, stock profile validation, paper expansion, buy-review approval, trading, current-candidates, snapshots, signal semantics mutation, broker/API/order/message behavior, protected data writes, checkpoint docs, or Project Source package files.

It must not mutate the v1.85 official-status evidence packet closure worklist artifacts. It should create a separate source hierarchy worklist surface if implementation is later approved.

## V. ChatGPT/Codex Mode Recommendation

Use Codex high for the selected report-only core scaffold because the design is deterministic, local, blocked by default, and does not require subjective source authority adjudication.

Escalate to ChatGPT Pro / Pro Extended before any task decides official source authority ranking, source reliability scoring, no-hit sufficiency, available-time adjudication, ETF not-applicable policy authority, mixed-universe production policy, evidence-to-readiness conversion, PIT approval, replay readiness, label creation, metric computation, model gating, stock-profile gating, paper expansion, buy-review, or trading authority.

## W. Commit/Tag/Source Recommendation

Recommended commit message if ready:

`docs: design official source hierarchy worklist for replay sample`

Recommended tag: no tag for this design report alone.

Recommended Source update: no immediate Project Source update for this design report alone.

## X. Recommended Next Task

`Historical Replay Official Source Hierarchy and Evidence Collection Worklist Core Report-Only v0.1`

Implementation boundary for that task: create only a deterministic report-only source hierarchy worklist core, focused tests, and manual diagnostic artifacts if explicitly scoped. Keep all evidence collection, evidence closure, PIT approval, replay, labels, metrics, training, stock profile, paper expansion, buy-review, trading, external API/LLM, current-candidates, snapshots, signal semantics mutation, and protected data writes out of scope.

Final classification:

`HISTORICAL_REPLAY_OFFICIAL_SOURCE_HIERARCHY_AND_EVIDENCE_COLLECTION_WORKLIST_DESIGN_CREATED_REPORT_ONLY`

Final verdict:

`HISTORICAL_REPLAY_OFFICIAL_SOURCE_HIERARCHY_WORKLIST_DESIGN_READY_FOR_CORE_REPORT_ONLY_IMPLEMENTATION`
