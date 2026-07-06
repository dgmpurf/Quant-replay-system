# Historical Replay Official Source Hierarchy and Evidence Collection Planning for 2024-04-02 / etf_core v0.1

phase = historical_replay_official_source_hierarchy_and_evidence_collection_planning_2024_04_02_etf_core
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_checkpoint = v1.85.0
latest_checkpoint_commit = d83a92e
latest_checkpoint_tag = v1.85.0
latest_repo_commit = 73965bc
selected_historical_decision_date = 2024-04-02
selected_universe = etf_core
official_source_hierarchy_approved = no
official_evidence_collection_approved = no
selected_next_route = Historical Replay Official Source Hierarchy and Evidence Collection Worklist Design for 2024-04-02 etf_core Report-Only v0.1

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

This docs-only planning report is ready. It defines a source hierarchy and manual evidence collection plan for the selected historical replay official-status worklist sample `2024-04-02 / etf_core`.

This report does not fetch, download, query, collect, accept, or close official evidence. It does not approve point-in-time admissibility, create replay input, run replay, freeze decisions, create labels, compute metrics, train models, expand stock profile or paper authority, approve buy-review, or authorize trading.

Selected next route:

`Historical Replay Official Source Hierarchy and Evidence Collection Worklist Design for 2024-04-02 etf_core Report-Only v0.1`

## B. Current Accepted State

The accepted checkpoint is `v1.85.0` at commit `d83a92e`. Current planning starts from commit `73965bc`, where artifact hardening aligned the official-status worklist next action to this source hierarchy planning route.

The selected sample remains:

| Field | Value |
| --- | --- |
| historical_decision_date | `2024-04-02` |
| universe | `etf_core` |
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

The prior generated artifact review found the artifact shape, counts, and safety fields coherent. The hardening follow-up fixed stale next-action wording. This planning report now defines the next source hierarchy layer.

## C. Selected Sample and Row Families

The selected row set must remain exactly:

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

Leading-zero symbols must remain strings in every future worklist, template, review packet, and status surface.

The seven STOCK rows remain profile-conflict review context under the legacy `etf_core` label. The two ETF rows remain ETF-profile context but still need ETF-specific official status and membership evidence.

## D. Official Evidence Families

Each row needs these evidence families before any future closure work can be considered:

| Evidence family | Required for | Minimum evidence purpose | Missing blocker |
| --- | --- | --- | --- |
| Listed / active status | STOCK and ETF | Show that the instrument existed and was listed or active for the decision date context. | `blocker_missing_listed_status_evidence` |
| Delisted / not-delisted status | STOCK and ETF | Reduce survivorship leakage risk by documenting delisted or not-delisted context as of the decision date. | `blocker_missing_delisted_status_evidence` |
| ST / no-ST status | STOCK only | Show whether each STOCK row had special-treatment status as of the decision date. | `blocker_missing_st_status_evidence` |
| ETF ST not-applicable policy | ETF only | Document why stock ST/no-ST evidence does not apply to ETF rows while preserving ETF-specific status review. | `blocker_missing_st_not_applicable_policy` |
| Suspension / trading status | STOCK and ETF | Show whether the instrument was suspended, tradable, or otherwise restricted as of the decision date. | `blocker_missing_suspension_or_trading_status` |
| Universe membership | STOCK and ETF | Show source-backed membership or selection context as of or before the decision date. | `blocker_missing_universe_membership_evidence` |
| Survivorship rationale | STOCK and ETF | Explain why the row is not included only because it survived into a later source universe. | `blocker_missing_survivorship_rationale` |
| Source lineage metadata | All evidence families | Provide source identity, raw reference, permission, revision, and timing context. | source, permission, revision, and available-time blockers |
| Reviewer no-hit handoff | Rows without source hits | Document searched-source context for later manual reviewer decisions. | `blocker_no_hit_unaccepted` |

No single evidence family closes the row by itself. Same-day quotation presence is useful context only and does not prove listed status, not-delisted status, no-ST status, suspension status, universe membership, or survivorship rationale.

## E. Source Hierarchy Proposal

The future source hierarchy should be ordered by official status specificity, decision-time availability, and auditability. This report proposes source classes only; it does not read or verify any source.

| Rank | Source class | Source id pattern | Source type | Primary use | Permission class | Raw reference type | Revision id type | Available-time requirement | Missing blocker |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Exchange official listing / trading-status files | `exchange_official_listing_status_{market}` | official_exchange | listed, delisted, suspension, trading status | public_review_allowed | official page, file, or notice reference | publication id, file date, notice id, or archive snapshot | publication or file availability time not after decision time | listed/delisted/suspension blockers |
| 2 | Exchange disclosure / issuer announcement systems | `exchange_disclosure_{market}_{symbol}` | official_disclosure | ST, no-ST, suspension, delisting notices, material status notices | public_review_allowed | announcement id or disclosure record | announcement id and publish timestamp | publish time and available time not after decision time | ST, delisting, suspension blockers |
| 3 | Official market-data or quotation publication | `official_market_quote_{market}` | official_market_data | supporting same-day traded presence and trading status context | public_review_allowed | daily quote file or official quote page | file date, data batch id, or publication timestamp | file/publication availability time not after decision time | supporting context only |
| 4 | ETF issuer or fund company public disclosure | `etf_issuer_disclosure_{fund_code}` | official_fund_issuer | ETF listed/trading status, ETF ST not-applicable policy, fund status | public_review_allowed | fund announcement, product page, or filing | announcement id, filing id, or page revision | publish time and available time not after decision time | ETF policy and ETF status blockers |
| 5 | Index / provider membership references | `index_or_universe_membership_{provider}_{universe}` | official_or_reviewed_provider | universe membership evidence if the selected universe maps to an index/provider source | public_or_reviewed_context | membership file, index constituent page, or reviewed export | effective date, file revision, publication id | effective/publication availability not after decision time | membership blockers |
| 6 | Reviewed local CSV / manual evidence metadata | `reviewed_local_csv_official_status_{review_id}` | reviewed_local_artifact | local reviewer packaging of collected public evidence metadata | local_review_only | reviewed metadata row, not raw evidence acceptance | package version and reviewer revision id | reviewed_at plus source available_time; reviewed_at alone is insufficient | metadata and reviewer blockers |
| 7 | Reviewer no-hit search log | `reviewer_no_hit_official_status_{review_id}` | reviewed_no_hit_log | searched-source context when no official hit is found | local_review_only | query log or reviewer attestation | review log id | reviewed_at plus query-window timing; cannot override source/timing gaps | no-hit blockers |

Rank 1 and Rank 2 should be preferred for status families because they are closest to official status authority. Rank 3 can support trading-presence context, but it must not be treated as complete status proof. Rank 4 is ETF-specific and should be used for ETF rows and ETF not-applicable policy. Rank 5 should be used only when universe membership can be tied to a specific provider, file, or reviewed source. Rank 6 and Rank 7 are local packaging and reviewer context, not independent official source authority.

## F. Source Lineage / Permission / Revision / Available-Time Requirements

Every future collected evidence row should include these fields:

| Field | Requirement |
| --- | --- |
| `source_id` | Controlled id matching the source hierarchy class. |
| `source_name` | Human-readable source name. |
| `source_type` | Controlled class such as `official_exchange`, `official_disclosure`, `official_market_data`, `official_fund_issuer`, `official_or_reviewed_provider`, `reviewed_local_artifact`, or `reviewed_no_hit_log`. |
| `permission_class` | Explicit public-review or local-review permission context; source name alone is not permission. |
| `raw_reference_type` | Page, file, announcement, filing, archive snapshot, reviewed metadata row, or no-hit query log. |
| `raw_reference` | Stable reference to the reviewed evidence location or record id; no secret or private path should be exposed in docs. |
| `source_hash_preview` | Preview only or hidden full hash policy; not source-hash validation. |
| `local_file_hash_preview` | Preview only for reviewed local files; not PIT evidence by itself. |
| `revision_id` | Source revision, announcement id, publication id, file date, package version, or reviewed revision id. |
| `revision_id_type` | Controlled type explaining what the revision id means. |
| `available_time` | Time at which the evidence was available to a decision-time process. |
| `available_time_timezone` | Explicit timezone or reviewed default policy. |
| `quality_status` | Review status such as missing, needs manual review, source-backed context, no-hit review needed, or rejected. |
| `reviewer_id` | Required for accepted reviewer context or no-hit handoff. |
| `reviewer_scope` | Scope of manual review authority; cannot override PIT/source/revision blockers. |
| `limitation_note` | Required for inferred, partial, no-hit, ETF not-applicable, or local reviewed context. |

Available-time must be specific enough to avoid future leakage. Event date, period end, local file creation time, or reviewer time alone is not enough. If the source publication or file availability is unknown, the row must remain blocked or review-needed.

## G. STOCK Row Evidence Policy

STOCK rows are:

`000001`, `000002`, `300750`, `600000`, `600519`, `601318`, `688981`

For each STOCK row, future source hierarchy worklists should require:

| Evidence family | Preferred source class | Review note |
| --- | --- | --- |
| Listed / active status | Exchange official listing / trading-status files | Must be as of the decision date context. |
| Delisted / not-delisted status | Exchange official listing / delisting files or disclosure notices | Must reduce survivorship leakage risk. |
| ST / no-ST status | Exchange disclosure or official ST status source | Must not be inferred from quotation alone. |
| Suspension / trading status | Exchange trading-status files and official quotation context | Same-day quotation can support, but not replace, status evidence. |
| Universe membership | Index/provider or reviewed universe source | Legacy `etf_core` label is not enough. |
| Survivorship rationale | Source-backed status plus reviewer rationale | Must explain why inclusion is not survivor-only. |

The seven STOCK rows keep `recommended_profile=stock_core` and `profile_conflict=true` until a separate mixed-universe policy or replacement-worklist step resolves the legacy `etf_core` mismatch.

## H. ETF Row Evidence Policy and ST Not-Applicable Policy

ETF rows are:

`159915`, `510300`

ETF rows should not be forced into stock ST/no-ST evidence. They need an explicit not-applicable policy and ETF-specific public evidence:

| Evidence family | Preferred source class | Review note |
| --- | --- | --- |
| Listed / active status | Exchange ETF listing/trading files or ETF issuer disclosure | Must show ETF status context as of the decision date. |
| Delisted / not-delisted status | Exchange ETF listing/delisting context or ETF issuer disclosure | Must reduce survivorship leakage risk. |
| ETF ST not-applicable policy | ETF issuer, exchange rules/context, or reviewed policy note | Must explain why stock ST status is not applicable; it does not skip ETF status review. |
| Suspension / trading status | Exchange trading-status files and official quotation context | Must be ETF-specific where possible. |
| Universe membership | ETF/index/provider membership source or reviewed universe source | Legacy universe label alone is insufficient. |
| Survivorship rationale | Source-backed ETF status plus reviewer rationale | Must remain explicit and visible. |

`159915` and `510300` keep `recommended_profile=etf_core` and `profile_conflict=false`, but they still remain blocked until required source, timing, revision, and reviewer fields exist.

## I. Universe Membership Evidence Policy

Universe membership evidence should answer whether the row belongs in the selected replay universe as of or before `2024-04-02`. It must not be inferred from a later file or from the legacy `etf_core` label alone.

Future worklist design should include:

| Field | Requirement |
| --- | --- |
| `universe_membership_evidence` | Source-backed membership or reviewed universe context. |
| `universe_membership_source_id` | Source hierarchy id. |
| `universe_membership_raw_reference` | Stable reviewed reference. |
| `universe_membership_revision_id` | Effective date, file revision, provider snapshot, or reviewed package version. |
| `universe_membership_available_time` | Must not be after the decision-time boundary. |
| `legacy_universe_label` | Preserve `etf_core` for audit lineage. |
| `recommended_profile` | Preserve `stock_core` or `etf_core` recommendation. |
| `profile_conflict_flag` | Preserve mixed-profile review context. |

If membership evidence comes from a manually reviewed local CSV, the local file metadata must preserve original source lineage, reviewed package version, reviewer id, source available time, and limitations.

## J. Suspension / Trading Status Evidence Policy

Suspension or trading status evidence should be date-specific. It can use exchange trading-status records, official daily quotation publications, or issuer/exchange notices, but it must remain separate from listed and delisted status evidence.

Rules:

- A traded quote can support traded-presence context but does not automatically prove not-suspended status.
- A missing quotation does not automatically prove suspension.
- For ETFs, the evidence should be ETF-specific when possible.
- Source revision and available-time fields are required.
- If only same-day market data is available, the row should remain review-needed unless a later accepted policy allows supporting context.

## K. Delisted / Not-Delisted Evidence Policy

Delisted or not-delisted evidence is required for all rows because historical replay must avoid survivor-only inclusion.

Preferred source classes:

1. Exchange listing/delisting official records.
2. Exchange disclosure or issuer announcements for delisting or major status changes.
3. ETF issuer or fund company status disclosures for ETF rows.
4. Reviewed no-hit search logs only as supporting context after explicit reviewer acceptance.

No-hit context cannot become source reliability scoring and cannot close the family by itself. It can only record that a reviewer searched defined sources and found no evidence of a delisting event within a defined query window.

## L. Reviewer No-Hit Handoff Policy

All nine rows currently require no-hit review and have zero accepted no-hit context.

A future no-hit handoff should record:

| Field | Requirement |
| --- | --- |
| `no_hit_source_family` | Evidence family being searched. |
| `no_hit_query_window` | Date and source window searched. |
| `no_hit_result` | Missing, found, conflicting, or inconclusive. |
| `no_hit_acceptance_status` | Not accepted until explicit reviewer action. |
| `no_hit_reviewer_required` | True for every unresolved row. |
| `reviewer_id` | Required before any accepted context. |
| `reviewer_scope` | Must define authority boundary. |
| `no_hit_acceptance_rationale` | Required for accepted supporting context. |
| `limitation_note` | Required to prevent overclaim. |

Reviewer no-hit acceptance cannot override missing source id, missing permission class, missing revision id, missing available-time proof, failed quality status, profile conflict, or survivorship warnings. It also cannot approve rows or create replay inputs.

## M. Survivorship Rationale Policy

All nine rows carry survivorship warning context. A future source hierarchy worklist should require survivorship rationale for every row:

- Which source establishes that the instrument was in-scope as of the decision date?
- Which source or reviewed package establishes that inclusion is not survivor-only?
- Which revision id and available-time record support that source?
- Which limitation remains if evidence is partial or no-hit based?

Survivorship rationale should be reviewer-visible and cannot be inferred from later availability of a symbol, from a current market listing, or from a later universe file.

## N. Collection Staging Plan

Collection should be staged without prematurely accepting evidence:

| Stage | Name | Allowed output | Forbidden interpretation |
| ---: | --- | --- | --- |
| 1 | Source registry / source hierarchy planning | Source hierarchy proposal and required fields | Not source approval or evidence collection. |
| 2 | Manual evidence collection checklist | Human-fill checklist outside repo or report-only template design | Not accepted evidence. |
| 3 | Source lineage metadata package planning | Metadata schema for source id, permission, revision, time, hash preview, reviewer, and limitations | Not validated PIT evidence. |
| 4 | Reviewer no-hit acceptance planning | No-hit query checklist and reviewer authority plan | Not source reliability scoring. |
| 5 | Mixed universe policy planning if needed | Policy plan for STOCK/ETF profile conflict | Not row approval or worklist activation. |
| 6 | Evidence packet closure worklist update planning | Future update design after source hierarchy and manual evidence evidence packages exist | Not closure by itself. |

Manual collection can happen outside the repo later, but repo-side work should first define a structured worklist design so that collected evidence is traceable and not accidentally treated as approval.

## O. Future Artifact / Template Design Scope

A future report-only implementation may create:

| Future artifact | Purpose |
| --- | --- |
| `official_source_hierarchy_matrix.csv` | Map source classes to evidence families, permission, revision, and available-time requirements. |
| `evidence_collection_checklist.csv` | Row-by-row human collection checklist for the nine selected rows. |
| `manual_collection_template.csv` | Empty or synthetic template for reviewer-filled source metadata. |
| `source_lineage_requirement_matrix.csv` | Required fields and blockers for source identity, permission, revision, hash-preview, and timing. |
| `official_source_no_hit_query_checklist.csv` | Structured query windows and reviewer no-hit handoff fields. |
| `review_blocker_map.csv` | Map missing evidence families to blockers and next manual action. |
| `limitations.md` | Non-approval wording and limitations. |

All future artifacts should remain report-only unless a later task separately approves a different scope.

## P. Safety and Non-Approval Boundary

This planning report does not:

- fetch, download, query, scrape, or collect official source data;
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

A packet row is not PIT approval. `packet_row_ready_not_pit_approved` is not PIT admissible. Source hash preview is not source-hash validation. Local file hash preview is not PIT evidence by itself. Forward returns remain future information. The 8-layer factor taxonomy remains the primary structure, and fixed 12 factors are not final.

## Q. Candidate Next Routes

| Route | Decision | Reason |
| --- | --- | --- |
| A. Historical Replay Official Source Hierarchy and Evidence Collection Worklist Design for 2024-04-02 etf_core Report-Only v0.1 | Selected | A structured repo-side worklist design is the smallest safe next step before manual evidence collection. |
| B. Historical Replay Official Source Manual Evidence Collection Template Docs-Only v0.1 | Not selected | A template would be useful, but source hierarchy and row-level evidence family mapping should be designed first. |
| C. Historical Replay Reviewer No-Hit Acceptance Planning for 2024-04-02 etf_core Report-Only v0.1 | Reserve | No-hit is open for all rows, but source hierarchy design should define query windows and source families first. |
| D. Historical Replay Mixed STOCK/ETF Universe Policy Planning for legacy etf_core Report-Only v0.1 | Reserve | Mixed profile conflict is important, but source hierarchy can preserve profile flags while planning evidence collection. |
| E. Pause repo work and manually collect official status evidence outside the repo | Not selected | Repo-side work can still safely define the worklist design before manual evidence collection. |
| F. Historical Replay Official Status Evidence Packet Closure Worklist Source-Hierarchy Hardening Report-Only v0.1 | Not selected | No source-hierarchy field hardening blocker was found in the existing v1.85 artifact before planning. |

## R. Selected Next Route

`Historical Replay Official Source Hierarchy and Evidence Collection Worklist Design for 2024-04-02 etf_core Report-Only v0.1`

## S. Why Selected Route Is Safe

The selected route is safe because it remains one step before evidence collection. It can design source hierarchy matrices, row-level checklist fields, no-hit query windows, and source-lineage requirements without fetching sources, accepting evidence, closing blockers, or changing runtime behavior.

It also preserves the mixed STOCK/ETF profile context, leading-zero symbol strings, survivorship warnings, no-hit boundaries, and source/timing/revision requirements.

## T. What Must Not Be Bundled

The next task must not bundle source fetching, official evidence collection, accepted evidence packets, evidence closure, PIT approval, active replay input, replay execution, replay decision freeze, labels, metrics, training/model work, stock profile validation, paper expansion, buy-review approval, trading, current-candidates, snapshots, signal semantics mutation, broker/API/order/message behavior, protected data writes, checkpoint docs, or Project Source package files.

## U. ChatGPT/Codex Mode Recommendation

Use Codex high for the worklist design if it stays limited to schema, row mapping, source-class definitions, manual checklist columns, and non-approval safety wording.

Escalate to ChatGPT Pro / Pro Extended before any subjective decision about source authority ranking, no-hit sufficiency, available-time adjudication, ETF not-applicable policy authority, mixed-universe production policy, evidence-to-readiness conversion, or downstream replay/training/model/buy-review/trading gates.

## V. Commit / Tag / Source Recommendation

Recommended commit message if ready:

`docs: plan official source hierarchy for replay sample`

Recommended tag: no tag for this planning report alone.

Recommended Source update: no immediate Project Source update for this planning report alone.

## W. Recommended Next Task

`Historical Replay Official Source Hierarchy and Evidence Collection Worklist Design for 2024-04-02 etf_core Report-Only v0.1`

Goal for that task: design a row-level, report-only source hierarchy and manual evidence collection worklist for the nine selected rows, including source-class hierarchy, evidence-family fields, source lineage requirements, no-hit query checklist fields, mixed STOCK/ETF profile handling, survivorship rationale fields, and non-approval safety boundaries, without fetching or collecting official evidence.

Final classification:

`HISTORICAL_REPLAY_OFFICIAL_SOURCE_HIERARCHY_AND_EVIDENCE_COLLECTION_PLANNING_CREATED_REPORT_ONLY`

Final verdict:

`HISTORICAL_REPLAY_OFFICIAL_SOURCE_HIERARCHY_READY_FOR_WORKLIST_DESIGN_OR_MANUAL_TEMPLATE_PLANNING_REPORT_ONLY`
