# Historical Replay Source / Evidence Sufficiency Policy Planning Without Evidence Collection Report-Only v0.1

## A. Decision / Status

    phase = historical_replay_source_evidence_sufficiency_policy_planning_without_evidence_collection
    decision = ready
    privacy_issue_stop = no
    docs_only = yes
    source_code_changed = no
    tests_changed = no
    runtime_changed = no
    evidence_collected = no
    evidence_read_from_external_sources = no
    evidence_template_filled = no
    evidence_sufficiency_applied_to_selected_rows = no
    evidence_accepted = no
    evidence_closed = no
    profile_conflict_resolved = no
    universe_membership_approved = no
    stock_profile_validated = no
    pit_admissibility_approved = no
    active_replay_input_approved = no
    replay_execution_approved = no
    forward_labels_created = no
    metric_computation_approved = no
    model_training_approved = no
    paper_expansion_approved = no
    real_buy_review_approved = no
    buy_review_allowed = no
    trading_allowed = no
    docs_project_sources_created = no
    current_checkpoint = v1.89.0
    current_checkpoint_commit = 7ca9c4d
    current_checkpoint_tag = v1.89.0
    current_repo_head = faa65f5
    business_checkpoint_changed = no
    selected_next_route = Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Design Report-Only v0.1

This report creates a policy-planning artifact only. It defines how a future synthetic contract may distinguish eligible sources, structurally present evidence, sufficiency candidates, accepted evidence, closed evidence families, PIT admissibility, and replay readiness.

It does not collect, open, read, accept, close, or apply real evidence. It assigns no evidence status to any current selected row.

Final classification:

    HISTORICAL_REPLAY_SOURCE_EVIDENCE_SUFFICIENCY_POLICY_PLANNING_CREATED_REPORT_ONLY

Final verdict:

    HISTORICAL_REPLAY_SOURCE_EVIDENCE_SUFFICIENCY_POLICY_READY_FOR_CONTRACT_FIXTURE_DESIGN_REPORT_ONLY

## B. Current Git / Tag / External Source State

Preflight matched the required state before this report was created:

| Check | Result |
| --- | --- |
| Branch | main |
| Worktree | clean |
| HEAD | faa65f5128edbdfa908ca722cfd840d9c470910f |
| Describe | v1.89.0-3-gfaa65f5 |
| Tag at HEAD | none |
| Formal checkpoint | v1.89.0 at 7ca9c4d |
| Previous checkpoint | v1.88.0 at 67af8d7 |
| Git show check | faa65f5 passed |
| Initial diff check | passed |

The external ChatGPT Project Source remains user-reported at v1.89.0. This task neither verifies nor updates that external source set. No Source package is created, and the repository path docs/project_sources remains prohibited.

Read-only repository context inspected:

- docs/release_checkpoint_v1.89.0.md
- docs/historical_replay_mixed_stock_etf_universe_profile_policy_post_v1_89_governance_audit_next_decision_planning_v0_1.md
- docs/historical_replay_mixed_stock_etf_universe_profile_policy_post_v1_89_generated_artifact_review_wording_audit_v0_1.md
- docs/historical_replay_mixed_stock_etf_universe_profile_policy_post_v1_89_next_task_wording_hardening_v0_1.md
- docs/historical_replay_mixed_stock_etf_universe_profile_policy_planning_legacy_etf_core_v0_1.md
- docs/historical_replay_pit_evidence_gap_closure_plan_2024_04_02_etf_core_v0_1.md
- docs/historical_replay_official_status_evidence_packet_closure_planning_2024_04_02_etf_core_v0_1.md
- docs/historical_replay_official_source_hierarchy_and_evidence_collection_planning_2024_04_02_etf_core_v0_1.md
- docs/historical_replay_official_manual_evidence_collection_template_design_2024_04_02_etf_core_v0_1.md
- docs/historical_replay_reviewer_no_hit_acceptance_planning_2024_04_02_etf_core_v0_1.md
- docs/source_registry_schema_fixture.md
- docs/tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time.md

Current selected-sample invariants remain:

| Invariant | Value |
| --- | ---: |
| row_count | 9 |
| stock_row_count | 7 |
| etf_row_count | 2 |
| profile_conflict_count | 7 |
| profile_aligned_context_count | 2 |
| unresolved_profile_conflict_count | 7 |
| profile_policy_accepted_count | 0 |
| universe_membership_approved_count | 0 |
| official_status_evidence_accepted_count | 0 |
| row_with_blocker_count | 9 |
| safety_true_count | 0 |

## C. Purpose And Non-Goals

The purpose is to define a conservative policy contract for future evidence-sufficiency review without performing evidence work. The policy is intended to:

- separate source-class eligibility from fact-family authority;
- define structural requirements for each evidence family;
- distinguish context, candidate sufficiency, acceptance, closure, PIT review, and replay promotion;
- preserve instrument-specific STOCK and ETF requirements;
- fail closed on missing timing, revision, permission, provenance, survivorship, reviewer, or conflict context;
- provide a deterministic basis for a later synthetic contract fixture.

This report is not evidence collection, external research, template filling, official-source acceptance, no-hit acceptance, profile adjudication, universe approval, stock-profile validation, PIT approval, replay promotion, label creation, metric computation, model training, paper expansion, buy-review, or trading authority.

## D. Terminology And Governance Separations

| Term | Required meaning | May lead to | Must not mean |
| --- | --- | --- | --- |
| Source eligibility | A source class may be considered for a named fact family. | Structural review of a future source reference. | Authority for every fact family, evidence presence, truth, or approval. |
| Evidence presence | A reference or artifact structurally exists with the required identifying fields. | Completeness checks. | Sufficiency, correctness, historical availability, acceptance, or closure. |
| Evidence sufficiency candidate | A future item appears complete enough for manual sufficiency review under one evidence family. | A separately authorized human sufficiency review. | Acceptance, closure, PIT admissibility, replay readiness, or automatic promotion. |
| Evidence acceptance | A separately authorized reviewer/governance workflow records bounded acceptance for a specific fact family and scope. | Family-level closure review if every other requirement is met. | Whole-row closure, PIT approval, replay readiness, or downstream authority. |
| Evidence closure | All required families for a row have separately accepted evidence and no unresolved family blocker. | A separately authorized PIT review. | PIT admissibility or replay readiness by itself. |
| PIT admissibility | A separately approved review establishes decision-time availability using source, publication, effective, revision, and timezone evidence. | A later governed replay-promotion review. | Evidence acceptance, replay execution, labels, training, or trading. |
| Replay readiness | A later governed workflow promotes a PIT-valid package into the exact replay-input boundary. | Only the actions separately approved by that future workflow. | A status produced by this report or by a sufficiency candidate. |

These stages are monotonic only through separate approvals. A later stage must never be inferred from an earlier stage.

## E. Source Eligibility Principles

1. Authority is evidence-family-specific. A source authoritative for listing status is not automatically authoritative for universe membership, ST status, suspension, survivorship, or instrument identity.
2. Exchange records, issuer disclosures, ETF issuer disclosures, and index/provider constituent publications may be eligible for different families, but eligibility remains a planning classification until a future reviewed reference exists.
3. Aggregators may support discovery or corroboration. They are not automatically primary evidence.
4. Same-day quote presence is traded-presence context only. It is not official listed, not-delisted, no-ST, not-suspended, membership, or PIT proof.
5. A current webpage is not automatically historical proof. Historical version, archive, publication, or version evidence is required.
6. A hash proves identity or integrity context only. It does not prove truth, authority, historical availability, permission, or sufficiency.
7. A reviewer declaration cannot override a missing source, publication time, available time, effective time, revision, permission, survivorship rationale, instrument-specific requirement, or conflict.
8. No-hit records query context only. No-hit does not establish an affirmative fact.
9. Legacy universe labels and recommended profiles are lineage and routing context only.
10. Forward returns are future information and remain outside every decision-time evidence family.

## F. Evidence-Family Sufficiency Matrix

All safe statuses in this matrix are future context-only planning vocabulary. None is applied to a current selected row.

| Evidence family | Purpose and applicable instruments | Eligible or authoritative source classes | Required structural fields | Publish / available / effective time and timezone | Revision or version | Provenance / hash / reference | Permission and legality | Corroboration | Reviewer | Insufficiency blockers | Safe future context-only status | Explicit non-approval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1. Instrument-type identity | Distinguish STOCK from ETF for all rows. | Exchange security master; official issuer/fund disclosure; reviewed provider only as corroboration. | symbol, market, instrument_type, source_id, source_type, raw_reference. | Source must support identity effective at decision time; timezone required for timestamped changes. | Security-master version or notice id required. | Stable reference plus disclosure-safe hash context. | Permission class and permitted review use required. | Second source required when official records conflict. | Scope must include identity classification. | missing source, conflicting type, missing version, timing ambiguity. | evidence_family_context_only. | Not official status, membership, profile validation, PIT, or replay approval. |
| 2. Listed / active status | Establish date-specific listed or active context for STOCK and ETF. | Exchange listing files; official exchange notices; ETF issuer disclosure for ETF corroboration. | symbol, status, status_date, source_id, reference, quality_status. | Publication and availability must not exceed decision cutoff; effective date must cover the decision date; timezone required. | File date, notice id, or archived version required. | Source lineage and stable record reference required; hash is integrity context only. | Public-review or other approved permission class required. | Quote presence may corroborate but never replace official status evidence. | Reviewer scope limited to listed-status family. | missing official source, post-decision availability, date gap, revision ambiguity. | evidence_family_sufficiency_candidate_not_accepted. | Not not-delisted proof, trading-status proof, closure, PIT, or replay readiness. |
| 3. Delisted / not-delisted status | Reduce survivorship leakage for STOCK and ETF. | Exchange delisting records; exchange/issuer notices; ETF issuer/fund status disclosure. | symbol, delisting_status, covered_period, source_id, reference, limitation_note. | Source availability and effective period must cover the decision cutoff; retrospective pages require historical-version proof. | Notice id, file version, correction history, or archive snapshot required. | Provenance chain to official record required. | Permission and archival-use legality required. | No-hit may document a search only; it cannot prove not-delisted. | Reviewer must state coverage window and limitations. | no historical version, no coverage period, no-hit used affirmatively, survivorship gap. | evidence_family_sufficiency_candidate_not_accepted. | Not a blanket survival claim, family acceptance, PIT approval, or membership proof. |
| 4. STOCK ST / no-ST status | Establish special-treatment status for seven STOCK rows. | Exchange disclosure/status records; official issuer notices. | symbol, ST status, effective date, source id, announcement id, reference. | Publish and available time must precede cutoff; effective interval must include decision time; market timezone required. | Announcement/revision id and correction history required. | Direct official reference required; quote or aggregator alone is insufficient. | Permission class must cover reviewed use. | A second official status source is required if records conflict. | STOCK-status review scope required. | missing ST source, effective-period gap, revised notice conflict, quote inference. | evidence_family_sufficiency_candidate_not_accepted. | Not stock-profile validation, profile-conflict resolution, PIT, or replay approval. |
| 5. ETF ST-not-applicable policy | Explain why STOCK ST status is not applicable to ETF rows while preserving ETF status review. | Exchange rules/status taxonomy; ETF issuer/fund disclosure; separately reviewed policy authority. | instrument_type, policy_basis, source_id, reference, effective period, limitation_note. | Rule publication and effective time must cover decision date; timezone required when timestamped. | Rule version or policy revision required. | Stable official policy reference and lineage required. | Permission and legal-use basis required. | ETF issuer evidence may corroborate exchange policy. | Reviewer scope must include ETF policy, not STOCK adjudication. | missing policy basis, wrong instrument scope, current rule used historically, missing version. | evidence_family_sufficiency_candidate_not_accepted. | Not a waiver of ETF listing, suspension, membership, survivorship, or timing review. |
| 6. Suspension / trading status | Establish date-specific suspension or trading restriction context for STOCK and ETF. | Exchange trading-status files; official suspension notices; official quote publication as supporting context. | symbol, session/date, status, source_id, reference, quality_status. | Availability must precede the relevant decision cutoff; session timezone and effective interval required. | Daily file batch, notice id, or archive version required. | Direct reference required; missing quote is not suspension proof. | Permission class required. | Quote presence is corroboration only; conflict requires official status review. | Reviewer scope limited to trading-status family. | missing date-specific source, post-decision file, timezone ambiguity, quote-only inference. | evidence_family_sufficiency_candidate_not_accepted. | Not listed/not-delisted proof, PIT approval, or replay eligibility. |
| 7. Universe membership | Establish whether each row belonged to the selected universe by decision time. | Official index/provider constituent file; governed universe publication; reviewed source tied to an explicit universe definition. | universe_id, symbol, membership status, effective date, source_id, reference. | Publication and availability must precede cutoff; effective membership must cover decision time; timezone required. | Constituent-list version, effective date, or snapshot id required. | Provider lineage and stable reference required. | Provider terms and permission class required. | Independent corroboration required when provider history is incomplete or transformed. | Reviewer scope must name universe and version. | legacy label only, later constituent file, missing effective date/version, transformed list without lineage. | evidence_family_sufficiency_candidate_not_accepted. | Not profile alignment, universe approval, PIT, or replay readiness. |
| 8. Universe definition and constituent version | Define the universe methodology and exact constituent release used. | Official provider methodology and dated constituent publications. | universe_id, definition, inclusion rules, version id, effective period, publication reference. | Publication, available, and effective times must be separately recorded with timezone. | Exact methodology and constituent versions required; superseded versions retained in lineage. | Stable references and transformation lineage required. | Permission and redistribution limits required. | Methodology and constituent files must agree on version/effective scope. | Reviewer scope must cover methodology/version mapping. | undefined universe, missing constituent version, current list substituted for history, version conflict. | evidence_family_context_only. | Not membership acceptance for any row or authority to resolve profile conflicts. |
| 9. Source lineage / provenance | Make every evidence reference traceable across all families. | Source registry entries plus official/reviewed references. | source_id, source_name, source_type, raw_reference_type, raw_reference, parent source, retrieval context. | Source publication/availability retained; retrieval time is separate and cannot substitute. | revision_id and revision_id_type required where applicable. | Reference, provenance chain, hash disclosure policy, and transformation notes required. | permission_class and legal-use note required. | Cross-source link required for transformed or local reviewed artifacts. | Reviewer confirms lineage completeness only. | missing source id/reference/parent, private path exposure, unsupported transformation. | evidence_family_context_only. | Not source truth, authority, sufficiency, acceptance, PIT, or replay approval. |
| 10. Publish_time / available_time / timezone | Establish when information could have entered a decision-time process. | Timestamped official publication, archive, exchange file metadata, or governed historical record. | publish_time, available_time, effective_time when relevant, retrieval_time, timezone, decision cutoff. | Times remain separate; unknown or ambiguous timezone blocks; available time controls knowledge boundary. | Timestamp correction or source revision must be linked. | Timestamp evidence and stable reference required. | Permission for timestamped source review required. | Corroboration required when publication and archive times conflict. | Reviewer cannot infer availability from retrieval time alone. | missing available time, after-decision availability, undated source, timezone conflict, backfill risk. | evidence_family_sufficiency_candidate_not_accepted. | Not PIT admissibility or evidence acceptance. |
| 11. Revision_id / effective version | Identify the exact original, revised, corrected, restated, or constituent version. | Official revision metadata, notice history, provider version records, governed archive. | revision_id, revision_id_type, version status, supersedes, effective time, source id. | Revision availability and effective time must be separate and timezone-aware. | Exact version required; filename alone is not a revision id. | Version lineage and stable reference required; hash may distinguish artifacts only. | Permission for retained historical version required. | Conflicting versions require explicit resolution by a later workflow. | Reviewer records scope and unresolved conflicts. | missing revision, future revision risk, supersession gap, filename-only version, conflict. | evidence_family_sufficiency_candidate_not_accepted. | Not revision validation, historical truth, PIT approval, or closure. |
| 12. Permission_class / legality | Establish whether evidence may be reviewed, retained, referenced, or transformed. | Source terms, license, public disclosure policy, or approved local-review policy. | permission_class, allowed use, retention rule, disclosure rule, legal limitation. | Effective policy date and version required when terms change. | Terms/license version required. | Reference to permission basis; no secret credentials or private content. | Legality is mandatory and cannot be inferred from public accessibility. | Legal conflict requires stop and separate review. | Reviewer must stay within declared scope. | missing permission, prohibited retention, unknown redistribution, conflicting terms. | evidence_family_context_only. | Not source authority, evidence sufficiency, acceptance, or downstream permission. |
| 13. Survivorship rationale | Explain why inclusion is not based only on later survival for all rows. | Historical listing/delisting and membership sources plus reviewer rationale. | warning flag, source ids, covered period, rationale, limitation note. | Evidence must cover decision time; current state and later survival are insufficient. | Historical versions and any corrections required. | Cross-family provenance to listing, delisting, and membership evidence required. | Permission for historical references required. | Multiple families must corroborate; no-hit alone is insufficient. | Reviewer states remaining uncertainty. | later-only source, missing historical membership, no rationale, no-hit used as proof. | evidence_family_sufficiency_candidate_not_accepted. | Not survivorship closure, universe approval, PIT, or replay readiness. |
| 14. Reviewer scope / quality / limitation | Make human review bounded and visible for every family. | Governed reviewer attestation and quality records. | reviewer alias, role, scope, reviewed_at, quality_status, rationale, limitation_note. | reviewed_at has timezone but cannot replace source available time. | Attestation revision required when review changes. | Review record references evidence without exposing private identity or source bytes. | Reviewer authority and privacy policy required. | Second review required for conflicts or scope uncertainty. | Scope cannot override substantive blockers. | missing alias/role/scope, private identity disclosure, missing limitation, quality failure. | evidence_family_context_only. | Not evidence authority, acceptance, PIT, replay, buy-review, or trading authority. |
| 15. No-hit query context | Record what was searched and not found for all unresolved families. | Reviewed query log over declared eligible source families. | source/evidence family, query terms, window, timezone, method, result reference, reviewer scope, limitation. | Query window and timezone required; post-decision search is manual follow-up context only. | Query-log revision required. | Query result reference only; no-hit is not source lineage replacement. | Search and retention permission required. | A hit or conflicting result cancels no-hit status and routes to evidence review. | Reviewer scope and rationale required. | missing window/timezone/reference/scope, conflicting hit, no-hit used affirmatively. | evidence_family_context_only. | Cannot prove not-delisted, no-ST, not-suspended, membership, PIT, or any affirmative fact. |
| 16. Profile conflict context | Preserve seven STOCK conflicts and two ETF aligned-context rows. | Existing fixture lineage plus future instrument-specific policy references. | symbol, instrument_type, legacy label, recommended profile, conflict flag/reason, limitation. | Any future policy reference must have publication/effective timing; current lineage fields remain context only. | Policy/version id required for future adjudication. | Fixture lineage retained; it is not official evidence. | Policy authority and permission required before adjudication. | Instrument identity and universe evidence must be reviewed separately. | Reviewer cannot resolve conflicts in this planning task. | hidden conflict, legacy label used as proof, recommended profile used as validation. | evidence_family_context_only. | Not conflict resolution, membership approval, stock-profile validation, PIT, or replay readiness. |
| 17. Cross-source corroboration | Compare independent eligible sources when one family is incomplete, transformed, or conflicting. | Two or more family-eligible sources with independent provenance. | source ids, fact compared, agreement/conflict result, timing, versions, rationale. | Each source must independently satisfy timing/timezone requirements. | Each source version recorded; newer evidence cannot silently rewrite historical context. | Independent references and provenance chains required. | Permission required for every source. | Corroboration strengthens review context but cannot repair an ineligible primary source. | Reviewer documents conflict and limitations. | circular sourcing, shared upstream source treated as independent, timing/version mismatch. | evidence_family_sufficiency_candidate_not_accepted. | Not automatic truth, acceptance, closure, PIT, or replay promotion. |

## G. STOCK-Specific Policy

The seven STOCK rows remain unresolved profile conflicts:

    000001, 000002, 300750, 600000, 600519, 601318, 688981

For every STOCK row:

- instrument identity must follow a STOCK-specific source path;
- listed/active, delisted/not-delisted, ST/no-ST, suspension/trading, universe membership, lineage, timing, revision, permission, survivorship, reviewer, and limitation families remain required;
- ST/no-ST requires date-effective official status evidence and cannot be inferred from quote presence;
- recommended_profile = stock_core is routing context only;
- legacy_universe_label = etf_core remains lineage context only;
- profile_conflict remains unresolved;
- no evidence family is sufficient, accepted, or closed in this report.

## H. ETF-Specific Policy

The two ETF rows remain profile-aligned context only:

    159915, 510300

For every ETF row:

- listed/active, delisted/not-delisted, suspension/trading, universe membership, lineage, timing, revision, permission, survivorship, reviewer, and limitation families remain required;
- a separately supported ETF ST-not-applicable policy replaces only the STOCK ST/no-ST family;
- ETF ST-not-applicable does not waive any other status family;
- provider, index, exchange, fund, and ETF-issuer sources must be tied to the exact applicable fact family;
- recommended_profile = etf_core and profile alignment do not prove official membership, status, PIT validity, or replay readiness.

## I. Universe Membership And Constituent-Version Policy

Universe membership requires both an explicit universe definition and the exact historical constituent version:

1. Identify universe_id, provider, methodology, inclusion rules, constituent version, publication time, available time, effective time, and timezone.
2. Preserve the exact source release or governed historical snapshot used.
3. Record any transformation from provider output to reviewed local context.
4. Treat later constituent files and current provider pages as retrospective unless a historical version proves otherwise.
5. Require independent review when the constituent file and methodology version disagree.
6. Keep legacy_universe_label and recommended_profile as lineage/routing fields only.

No current row receives universe-membership approval.

## J. Official Status Policy

Official status is a set of separate evidence families, not one generic flag:

- listed/active does not prove not-delisted;
- not-delisted does not prove no-ST or not-suspended;
- quote presence does not prove any official status family;
- missing quote does not prove suspension;
- STOCK rows require STOCK-specific ST/no-ST evidence;
- ETF rows require an explicit ETF ST-not-applicable policy plus ETF-specific status review;
- historical coverage must include the decision cutoff;
- family-level conflicts remain blockers.

## K. Available-Time And Decision-Cutoff Policy

A future contract fixture must model these times separately:

| Time | Policy |
| --- | --- |
| decision timestamp | Exact cutoff for the replay decision, including timezone and trading-session interpretation. |
| publish_time | When the source states it published the information. It does not by itself prove availability. |
| available_time | Earliest supported time the information could be used by the decision process. This controls the knowledge boundary. |
| effective_time | When the fact or rule became effective. It may precede or follow publication and availability. |
| retrieval/fetch time | When a reviewer or system obtained the artifact. It cannot substitute for historical availability. |
| archive/snapshot time | When a preserved version was captured. It supports version lineage but may be after decision time. |

Future handling rules:

- post-decision available_time blocks decision-time use even if effective_time is earlier;
- undated evidence blocks sufficiency candidacy;
- timezone ambiguity blocks until a separately authorized policy resolves it;
- revised or backfilled records require the original and revised availability histories;
- manually reconstructed historical files require source-level availability proof for each represented fact;
- contemporaneous documents may become candidates only when publication, availability, effective time, revision, and timezone are coherent;
- retrospective documents may provide context but cannot silently replace contemporaneous proof;
- current webpages require an archive or version record establishing the historical content;
- a local CSV created after the decision can only package historically available information if each row retains source-level historical availability evidence.

## L. Revision And Historical-Version Policy

The future contract must distinguish:

- original release;
- revised release;
- correction;
- restatement;
- constituent-list version;
- current-state page;
- archived historical version;
- superseded evidence.

Every versioned item requires revision_id, revision_id_type, publication time, available time, effective time where applicable, supersedes/superseded_by links, and a stable reference. A filename alone is not a revision id. A source hash may distinguish artifact versions, but it cannot determine which version was historically valid.

Future revisions first available after the decision cutoff must not rewrite the decision-time record. Superseded evidence remains in lineage and must not disappear from review.

## M. Provenance / Hash / Reference Policy

Every future evidence item requires:

- source_id, source_name, source_type, and evidence family;
- raw_reference_type and stable raw_reference;
- parent/source lineage for transformed or reviewed local artifacts;
- disclosure-safe source_hash preview or explicit hidden-hash policy;
- local-file hash kept distinct from source hash;
- revision and timing fields;
- quality and limitation fields.

Full hashes, source bytes, source content, private paths, credentials, and reviewer private identities must not appear in user-facing reports. Hash equality establishes identity/integrity context only. It does not validate authority, truth, completeness, timing, legality, or sufficiency.

## N. Permission / Legality Policy

Public accessibility is not sufficient permission. A future candidate requires:

- permission_class;
- allowed review, storage, citation, transformation, and disclosure uses;
- retention and redistribution limits;
- legal or terms reference and version;
- privacy and confidential-data classification;
- a fail-closed action when permission is missing, conflicting, or prohibits the planned use.

Permission does not make a source authoritative. Authority, timing, revision, and sufficiency remain separate.

## O. Survivorship Policy

All nine rows retain survivorship warning context. A future sufficiency candidate must explain:

- why the instrument was in scope at the decision time;
- which historical listing/delisting and universe sources support inclusion;
- which exact versions and availability times were used;
- why the row is not present only because it survived into a later source or cache;
- which limitations remain.

Current listing pages, later universe files, same-day quote presence, and no-hit context cannot close survivorship.

## P. Reviewer / Quality / Limitation Policy

Every future non-default candidate requires a non-private reviewer alias, reviewer role, reviewer scope, reviewed_at with timezone, quality_status, rationale, and limitation_note.

Reviewer authority is bounded by evidence family and sample. A reviewer may identify completeness or recommend manual review. A reviewer cannot override missing source, timing, revision, permission, legality, survivorship, instrument-specific, profile-conflict, or corroboration requirements.

Quality states must fail closed:

- missing or failed quality blocks;
- partial, warning, inferred, retrospective, local-only, or no-hit context requires a visible limitation;
- scope uncertainty requires another review;
- private identity disclosure or source-content disclosure is a blocker.

## Q. No-Hit Context Policy

A future no-hit context may record only:

- source family and evidence family searched;
- query terms and method;
- query window and timezone;
- result and result reference;
- reviewer alias, role, scope, and reviewed_at;
- rationale and limitation note.

No-hit cannot establish listed, active, not-delisted, no-ST, not-suspended, universe membership, source reliability, survivorship closure, PIT validity, or any affirmative fact. A later hit or conflicting source invalidates no-hit treatment and routes the item to evidence review.

## R. Profile Conflict Interaction

The seven STOCK profile conflicts remain unresolved. The two ETF rows remain aligned context only.

- legacy_universe_label is not official evidence;
- recommended_profile is not official evidence or stock-profile validation;
- profile policy cannot satisfy membership or official-status families;
- evidence candidates cannot silently resolve profile conflict;
- profile conflict resolution requires a separately authorized governance task.

## S. Cross-Source Corroboration Policy

Corroboration must be fact-family-specific, independently sourced, version-aware, and time-aware.

- Two references sharing the same upstream source are not independent.
- An aggregator and its upstream official source count as one lineage unless independence is proven.
- Corroboration cannot rehabilitate an ineligible or legally unusable source.
- Conflicts must remain visible and block sufficiency candidacy until separately reviewed.
- Agreement may strengthen context but does not produce acceptance or closure.

## T. Row-Level Aggregation And Blocker Planning

A future synthetic contract may aggregate family states using this order:

1. Any missing required family or hard blocker prevents a row-level sufficiency candidate.
2. Family context may use evidence_family_context_only.
3. A structurally complete family may use evidence_family_sufficiency_candidate_not_accepted.
4. A row with every required family at candidate state may use row_has_sufficiency_candidates_not_closed.
5. Warning context always requires a visible limitation note.
6. Family acceptance, row closure, PIT admissibility, and replay readiness remain outside the fixture unless separately authorized.

Required planning blockers:

| Planned blocker | Meaning |
| --- | --- |
| row_blocked_by_missing_evidence | One or more required evidence families are absent or structurally incomplete. |
| row_blocked_by_profile_conflict | Profile conflict remains unresolved. |
| row_blocked_by_universe_membership | Membership source, definition, constituent version, or effective coverage is missing. |
| row_blocked_by_timing | Publication, availability, effective time, decision cutoff, or timezone is missing or unsafe. |
| row_blocked_by_revision | Revision id, historical version, supersession lineage, or conflict handling is missing. |
| row_blocked_by_permission | Permission or legality is missing, conflicting, or prohibits intended use. |
| row_blocked_by_survivorship | Historical inclusion and non-survivor-only rationale are incomplete. |

Current sample state remains unchanged: all nine rows have blockers, seven STOCK rows retain profile conflicts, no row has accepted evidence, no row is closed, and no row is PIT-admissible or replay-ready.

## U. Safe Status Vocabulary Planning

| Planned status | Meaning | Safe boundary |
| --- | --- | --- |
| evidence_family_context_only | Structural or descriptive family context exists. | Not a sufficiency candidate or acceptance. |
| evidence_family_sufficiency_candidate_not_accepted | A family appears complete enough for future manual sufficiency review. | Not accepted or closed. |
| row_has_sufficiency_candidates_not_closed | Required families appear candidate-complete for future review. | Not accepted, closed, PIT-approved, or replay-ready. |
| row_blocked_by_missing_evidence | Required evidence is missing or incomplete. | Fail closed. |
| row_blocked_by_profile_conflict | Profile conflict is unresolved. | Fail closed. |
| row_blocked_by_universe_membership | Membership evidence/version is incomplete. | Fail closed. |
| row_blocked_by_timing | Decision-time timing evidence is incomplete or unsafe. | Fail closed. |
| row_blocked_by_revision | Revision/version lineage is incomplete or conflicting. | Fail closed. |
| row_blocked_by_permission | Permission/legal basis is incomplete or unsafe. | Fail closed. |
| row_blocked_by_survivorship | Survivorship rationale is incomplete. | Fail closed. |

These terms are planning vocabulary only. No current selected row is assigned a sufficiency-candidate status.

## V. Forbidden Interpretations

This report and any future synthetic fixture must not be interpreted as:

- real evidence collection, source retrieval, source reading, or template filling;
- source authority approval or source reliability scoring;
- evidence sufficiency applied to current rows;
- accepted or closed evidence;
- profile-conflict resolution or universe-membership approval;
- stock-profile validation;
- PIT admissibility;
- active replay input, replay execution, decision freeze, or labels;
- metrics, training, model, weights, or thresholds;
- paper expansion, real buy-review eligibility, or buy-review permission;
- current-candidates, snapshots, or signal-semantics mutation;
- broker, API, LLM, order, message, or trading authority;
- protected data writes.

## W. Candidate Next Routes

| Route | Decision | Reason |
| --- | --- | --- |
| A. Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Design Report-Only v0.1 | selected | The policy is coherent enough to encode as a synthetic contract without collecting or applying evidence. |
| B. Historical Replay Official Manual Evidence Collection Fill Protocol Design Report-Only v0.1 | not selected | Existing templates do not justify moving toward filling before the sufficiency contract is tested synthetically. |
| C. Pause repository work and manually research official source/status evidence outside the repository | not selected | No evidence collection is authorized, and safe contract design remains available. |
| D. Historical Replay Source / Evidence Sufficiency Policy Additional Governance Hardening Report-Only v0.1 | not selected | No material unresolved semantic ambiguity requires another planning-only hardening pass. |
| E. Continue another historical replay governance branch | not selected | The current policy branch has a clear bounded next task. |

## X. Selected Next Route

Exactly one route is selected:

    Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Design Report-Only v0.1

The selected route should design a deterministic, synthetic, report-only contract. It must not implement evidence collection, fill templates, adjudicate the selected rows, accept or close evidence, approve PIT, or promote replay input.

Human approval by ChatGPT and the user is required before commit and before the selected next task begins.

## Y. Current / Next Mode Recommendation

Current task:

ChatGPT review:

- surface: Chat
- model: GPT-5.6 Sol
- ChatGPT mode: Extra High
- speed: Standard

Execution side:

- surface: Codex
- environment: Local
- model: GPT-5.6 Sol
- effort: Extra High
- speed: Standard
- task mode: Goal

Next task:

- task: Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Design Report-Only v0.1
- surface: Codex
- environment: Local
- model: GPT-5.6 Sol
- effort: Extra High
- speed: Standard
- task mode: Goal
- primary artifact: one synthetic contract-fixture design report only
- human gate: ChatGPT and user approval before implementation

Model strength and effort improve review depth only. They do not expand evidence, PIT, replay, buy-review, or trading authority.

## Z. Commit / Tag / Source Recommendation

Recommended commit message if reviewed and ready:

    docs: plan historical replay source evidence sufficiency policy

Recommended tag:

    No tag.

Recommended Source update:

    No Source update.

Recommended next task:

    Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Design Report-Only v0.1

No git add, commit, push, or tag is authorized by this task.
