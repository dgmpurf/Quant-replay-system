# Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Design Report-Only v0.1

## A. Decision / Status

    phase = historical_replay_source_evidence_sufficiency_policy_contract_fixture_design
    decision = ready
    privacy_issue_stop = no
    docs_only = yes
    design_created = yes
    fixture_implemented = no
    fixture_artifacts_generated = no
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
    current_repo_head = cef7cdf
    business_checkpoint_changed = no
    selected_historical_decision_date = 2024-04-02
    selected_legacy_universe_label = etf_core
    row_count = 9
    stock_row_count = 7
    etf_row_count = 2
    evidence_family_count = 17
    row_evidence_family_contract_count = 153
    applicable_contract_row_count = 144
    instrument_not_applicable_context_row_count = 9
    profile_conflict_count = 7
    profile_aligned_context_count = 2
    unresolved_profile_conflict_count = 7
    sufficiency_candidate_count = 0
    evidence_accepted_count = 0
    evidence_closed_count = 0
    pit_admissible_count = 0
    replay_ready_count = 0
    selected_row_with_blocker_count = 9
    safety_true_count = 0
    selected_next_route = Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Core / Views / CLI / Research-Status Milestone Bundle Report-Only v0.1

This report designs one future deterministic synthetic contract fixture. It does not implement or execute that fixture.

Final classification:

    HISTORICAL_REPLAY_SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_DESIGN_CREATED_REPORT_ONLY

Final verdict:

    HISTORICAL_REPLAY_SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_DESIGN_READY_FOR_MILESTONE_BUNDLE_IMPLEMENTATION_REPORT_ONLY

## B. Current Git / Tag / External Source State

The required hard preflight passed before this file was created:

| Check | Observed result |
| --- | --- |
| Branch and worktree | main, clean |
| HEAD | cef7cdffc76a07953f7bd30acac18607d4655f81 |
| Describe | v1.89.0-4-gcef7cdf |
| Tag at HEAD | none |
| Formal checkpoint | v1.89.0 at 7ca9c4d |
| Previous checkpoint | v1.88.0 at 67af8d7 |
| cef7cdf content | only the accepted source/evidence sufficiency planning report |
| git show check | passed |
| Initial diff check | passed |

The external Project Source remains user-reported as v1.89.0 plus externally maintained Sol-only and Goal-lifecycle overlays. Those overlays do not change the business checkpoint. This task does not inspect or update the external package and does not create docs/project_sources.

Read-only documents inspected:

- docs/historical_replay_source_evidence_sufficiency_policy_planning_without_evidence_collection_v0_1.md
- docs/release_checkpoint_v1.89.0.md
- docs/historical_replay_mixed_stock_etf_universe_profile_policy_post_v1_89_next_task_wording_hardening_v0_1.md
- docs/historical_replay_official_source_hierarchy_and_evidence_collection_planning_2024_04_02_etf_core_v0_1.md
- docs/historical_replay_official_source_hierarchy_and_evidence_collection_worklist_design_2024_04_02_etf_core_v0_1.md
- docs/historical_replay_official_status_evidence_packet_closure_planning_2024_04_02_etf_core_v0_1.md
- docs/historical_replay_official_status_evidence_packet_closure_worklist_design_2024_04_02_etf_core_v0_1.md
- docs/historical_replay_official_manual_evidence_collection_template_design_2024_04_02_etf_core_v0_1.md
- docs/historical_replay_reviewer_no_hit_acceptance_planning_2024_04_02_etf_core_v0_1.md
- docs/historical_replay_mixed_stock_etf_universe_profile_policy_planning_legacy_etf_core_v0_1.md
- docs/historical_replay_pit_evidence_gap_closure_plan_2024_04_02_etf_core_v0_1.md
- docs/historical_replay_pit_evidence_closure_worklist_design_2024_04_02_etf_core_v0_1.md

Read-only source and test conventions inspected:

- the mixed STOCK/ETF core, index, health, and status modules;
- the official source hierarchy, official manual template, and reviewer no-hit core modules;
- src/quant_replay_system/cli.py;
- src/quant_replay_system/local_research_dashboard.py;
- the focused mixed-profile core, views, and CLI tests;
- the official manual template and reviewer no-hit core tests;
- tests/test_local_research_dashboard.py.

## C. Goal Identity And Acceptance Artifact

Goal identity:

    Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Design Report-Only v0.1

Required acceptance artifact:

    docs/historical_replay_source_evidence_sufficiency_policy_contract_fixture_design_v0_1.md

Previous Goal that is not repeated:

    Historical Replay Source / Evidence Sufficiency Policy Planning Without Evidence Collection Report-Only v0.1

The planning report is accepted lineage. This design translates it into an implementable synthetic contract. Completion requires this exact new design report, all A through AC sections, required status fields, exact counts, and passing static and Git checks.

ChatGPT and the user must review this report before commit and before any future fixture implementation milestone bundle.

## D. Purpose And Non-Goals

The purpose is to freeze a deterministic future fixture contract for:

- component names and CLI names;
- output roots and output-root guards;
- selected rows and leading-zero symbols;
- 17 evidence families and 153 row-family contract rows;
- exact applicability, default statuses, blockers, and negative proof;
- core, index, health, status, and research-status surfaces;
- privacy-safe disclosure and lower-priority dashboard integration;
- focused tests and repository-external temp-root smoke.

The design does not implement modules, modify tests, register CLI commands, generate artifacts, run tests, read real evidence, fill templates, apply sufficiency, accept or close evidence, resolve profile conflicts, approve membership, validate PIT, create replay input, execute replay, create labels, compute metrics, train models, expand paper authority, approve buy-review, or authorize trading.

## E. Planning-to-Fixture Traceability

| Accepted planning concept | Future fixture representation | Default fixture value | Guard |
| --- | --- | --- | --- |
| Source eligibility | source_eligibility_context and eligible_source_classes | vocabulary/context only | Never evidence presence or authority. |
| Evidence presence | evidence_presence on every contract row | false | Cannot imply sufficiency. |
| Evidence sufficiency candidate | sufficiency_candidate on family rows and selected_row_sufficiency_candidate on selected rows | false | No current selected row may use a candidate status. |
| Evidence acceptance | evidence_accepted fields and counts | false / 0 | Requires a separate human/governance workflow. |
| Evidence closure | evidence_closed fields and counts | false / 0 | Requires accepted required families. |
| PIT admissibility | pit_admissible fields and counts | false / 0 | Requires a separate decision-time adjudication. |
| Replay readiness | replay_ready fields and counts | false / 0 | Requires a later governed PIT-valid promotion. |

Required separation:

    source eligibility
    != evidence presence
    != evidence sufficiency candidate
    != evidence acceptance
    != evidence closure
    != PIT admissibility
    != replay readiness

Count derivation:

- 17 evidence families multiplied by 9 selected rows equals 153 contract rows.
- 15 common families multiplied by 9 rows equals 135 applicable rows.
- STOCK ST/no-ST contributes 7 applicable STOCK rows and 2 explicit ETF not-applicable context rows.
- ETF ST-not-applicable contributes 2 applicable ETF rows and 7 explicit STOCK not-applicable context rows.
- The two instrument-specific families therefore contribute 9 applicable and 9 not-applicable context rows.
- Total applicable rows equal 135 plus 9, or 144.
- Total explicit instrument-not-applicable context rows equal 9.
- No family row is silently omitted.

## F. Component And Naming Contract

Future modules:

| Component | Proposed module | Responsibility |
| --- | --- | --- |
| Core | historical_replay_source_evidence_sufficiency_policy_contract_fixture.py | Build deterministic synthetic contract artifacts under a guarded root. |
| Index | historical_replay_source_evidence_sufficiency_policy_contract_fixture_index.py | Discover valid runs and expose safe summary rows. |
| Health | historical_replay_source_evidence_sufficiency_policy_contract_fixture_health.py | Validate artifact presence, schema, counts, safety, disclosure, and status boundaries. |
| Status | historical_replay_source_evidence_sufficiency_policy_contract_fixture_status.py | Summarize the latest valid run and wrap index/health results. |

Future CLI command family:

- historical-replay-source-evidence-sufficiency-policy-contract-fixture
- historical-replay-source-evidence-sufficiency-policy-contract-fixture-index
- historical-replay-source-evidence-sufficiency-policy-contract-fixture-health
- historical-replay-source-evidence-sufficiency-policy-contract-fixture-status

Proposed root:

    outputs/reports/manual_diagnostics/historical_replay_source_evidence_sufficiency_policy_contract_fixture_v0_1/

Proposed view roots:

- index under the proposed root at index/
- health under the proposed root at health/
- status under the proposed root at status/

The output-root guard must reject data/raw, data/processed, data/cache, docs/project_sources, any path escaping the requested root, and any path that is not local report-only diagnostics or a test temp path.

Proposed core status:

    SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_CREATED_REPORT_ONLY

Proposed workflow stage:

    HISTORICAL_REPLAY_SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_CREATED_REPORT_ONLY

## G. Artifact Inventory And Row Counts

### Core artifacts

| Artifact | Purpose | Primary key | Required fields | Deterministic size | Safe disclosure | Surface | Forbidden interpretation |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| metadata.json | Run identity, counts, paths, status, health, next task, and negative proof. | run_id | all A-section counts, relative artifact filenames, safety fields | 1 object | Relative filenames only; no source content, private path, or full hash. | Core; index/status input; research-status context | Not an approval record. |
| source_evidence_sufficiency_policy_rows.csv | One selected-row summary per symbol. | row_id | 15 selected-row fields from section K | 9 rows | Symbols remain strings; no evidence payload. | Core and summary views | Not membership, sufficiency, acceptance, PIT, or replay approval. |
| source_evidence_sufficiency_policy_evidence_family_contract.csv | One row for every selected-row/evidence-family pair. | contract_row_id | 30 contract fields from section K | 153 rows | Vocabulary and false/default flags only. | Core; index/health count source | Not real evidence or a filled template. |
| source_evidence_sufficiency_policy_required_fields.csv | Machine-readable field contract. | field_scope plus field_name | field_scope, field_name, type, required, default, blocker_if_invalid, disclosure | 45 rows | Schema text only. | Core and health | Not a collected evidence schema instance. |
| source_evidence_sufficiency_policy_status_vocabulary.csv | Bounded family/row status vocabulary. | status | status, scope, allowed_for_selected_fixture, meaning, forbidden_interpretation | 17 rows | Policy text only. | Core and health | Candidate vocabulary is not a candidate assignment. |
| source_evidence_sufficiency_policy_blocker_vocabulary.csv | Bounded blocker vocabulary. | blocker_id | blocker_id, category, trigger, applies_to, meaning | 28 rows | Policy text only. | Core and health | Blocker absence would not imply approval. |
| source_evidence_sufficiency_policy_timing_revision_matrix.csv | Timing and revision rules. | rule_id | rule_id, category, required_fields, safe_default, blocker, forbidden_interpretation | 18 rows | No real timestamps or source values. | Core and health | Not PIT validation. |
| source_evidence_sufficiency_policy_stock_etf_matrix.csv | Four instrument-specific applicability rules. | applicability_rule_id | instrument_type, evidence_family_id, applicability, policy_required, status, notes | 4 rows | Policy text only. | Core and health | Not instrument or membership approval. |
| source_evidence_sufficiency_policy_safety_flags.json | Explicit negative downstream and side-effect proof. | run_id | required non-approval booleans, disclosure booleans, safety_true_count | 1 object | All authority and side-effect flags false. | Core, health, status, research-status | Not capability authorization. |
| source_evidence_sufficiency_policy_contract_fixture_report.md | Human-readable fixture summary and limitations. | run_id | counts, status, blockers, terminology, safety, next task | 1 document | Upload-safe wording; no full hash, source payload, identity, secret, or local path. | Core report and status link | Not evidence or approval. |

Core artifact count is exactly 10.

### View artifacts

| Surface | Proposed files | Single-run deterministic size | Contract |
| --- | --- | ---: | --- |
| Index | index CSV, index Markdown, metadata JSON | 1 index row, 1 document, 1 object | One row per valid discovered core run; relative/safe paths only. |
| Health | health CSV, health Markdown, metadata JSON | 0 issue rows for a clean PASS fixture, 1 document, 1 object | Header-only issue CSV is valid for PASS; WARN/FAIL rows are deterministic from issues. |
| Status | status CSV, status Markdown, metadata JSON | 1 latest-status row, 1 document, 1 object | No-artifact mode emits a benign zero-count summary; one valid run emits one latest row. |
| Research-status | Existing dashboard/research-status outputs only | No feature-specific file | Dedicated latest_* fields summarize status context without rereading source content. |

No artifacts are generated by this design task.

## H. Selected Sample Contract

Deterministic row_id format:

    20240402_etf_core_<six-character-symbol>

| row_id | symbol | instrument_type | recommended_profile | profile_conflict | profile_policy_status | selected_row_blockers | candidate / accepted / closed / PIT / replay |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20240402_etf_core_000001 | 000001 | STOCK | stock_core | true | unresolved_profile_conflict | missing evidence; profile conflict; membership; timing; revision; permission; survivorship | all false |
| 20240402_etf_core_000002 | 000002 | STOCK | stock_core | true | unresolved_profile_conflict | missing evidence; profile conflict; membership; timing; revision; permission; survivorship | all false |
| 20240402_etf_core_159915 | 159915 | ETF | etf_core | false | profile_aligned_context_only_not_universe_proof | missing evidence; membership; timing; revision; permission; survivorship | all false |
| 20240402_etf_core_300750 | 300750 | STOCK | stock_core | true | unresolved_profile_conflict | missing evidence; profile conflict; membership; timing; revision; permission; survivorship | all false |
| 20240402_etf_core_510300 | 510300 | ETF | etf_core | false | profile_aligned_context_only_not_universe_proof | missing evidence; membership; timing; revision; permission; survivorship | all false |
| 20240402_etf_core_600000 | 600000 | STOCK | stock_core | true | unresolved_profile_conflict | missing evidence; profile conflict; membership; timing; revision; permission; survivorship | all false |
| 20240402_etf_core_600519 | 600519 | STOCK | stock_core | true | unresolved_profile_conflict | missing evidence; profile conflict; membership; timing; revision; permission; survivorship | all false |
| 20240402_etf_core_601318 | 601318 | STOCK | stock_core | true | unresolved_profile_conflict | missing evidence; profile conflict; membership; timing; revision; permission; survivorship | all false |
| 20240402_etf_core_688981 | 688981 | STOCK | stock_core | true | unresolved_profile_conflict | missing evidence; profile conflict; membership; timing; revision; permission; survivorship | all false |

Every row also records historical_decision_date = 2024-04-02, decision_timezone = Asia/Shanghai, and legacy_universe_label = etf_core.

## I. Seventeen Evidence-Family Contract

All 153 contract rows set evidence_presence, sufficiency_candidate, evidence_accepted, evidence_closed, pit_admissible, and replay_ready to false.

| ID | Evidence family | Applicability | Eligible-source policy context | Required structural field families | Default status | Default blocker categories |
| --- | --- | --- | --- | --- | --- | --- |
| EF01 | instrument-type identity | common to all 9 | exchange security master; official issuer/fund context | identity, source, timing, version, reviewer | evidence_family_missing_required_fields | source eligibility; fields; provenance; timing; revision |
| EF02 | listed / active status | common to all 9 | exchange listing/status records | status, covered date, source, timing, version | evidence_family_missing_required_fields | source; fields; reference; timing; revision |
| EF03 | delisted / not-delisted status | common to all 9 | exchange delisting and issuer/fund notices | status, covered period, source, version, limitation | evidence_family_missing_required_fields | source; historical version; survivorship; no-hit misuse |
| EF04 | STOCK ST / no-ST status | applies to 7 STOCK; explicit N/A context for 2 ETF | exchange disclosure/status records | ST status, effective period, announcement, timing | evidence_family_missing_required_fields or instrument_not_applicable_policy_context_only | source; effective time; revision; quotation misuse |
| EF05 | ETF ST-not-applicable policy | applies to 2 ETF; explicit N/A context for 7 STOCK | exchange rule/status taxonomy; ETF issuer/fund policy | policy basis, effective period, source, version, limitation | evidence_family_missing_required_fields or instrument_not_applicable_policy_context_only | source; policy scope; version; current-page misuse |
| EF06 | suspension / trading status | common to all 9 | exchange trading-status records; official quote as corroboration only | session/date, status, source, timing, version | evidence_family_missing_required_fields | reference; timing; quotation misuse |
| EF07 | universe membership | common to all 9 | official index/provider constituent publication | universe id, symbol, membership, effective date, version | evidence_family_missing_required_fields | membership; constituent version; timing; provenance |
| EF08 | universe definition and constituent version | common to all 9 | official methodology and constituent publication | definition, methodology version, constituent version, effective period | evidence_family_missing_required_fields | source; version; timing; corroboration |
| EF09 | source lineage / provenance | common to all 9 | source registry and governed reference classes | source id/name/type, reference, parent, transformation | evidence_family_missing_required_fields | provenance; reference; permission; unsafe path |
| EF10 | publish_time / available_time / timezone | common to all 9 | timestamped official publication or governed archive | decision, publish, available, effective, retrieval/archive times, timezone | evidence_family_missing_required_fields | undated; timezone; post-decision; backfill |
| EF11 | revision_id / effective version | common to all 9 | official revision history or governed archive | revision id/type, version state, effective time, supersession | evidence_family_missing_required_fields | revision; historical version; superseded evidence |
| EF12 | permission_class / legality | common to all 9 | terms, license, public disclosure, local-review policy | permission class, allowed use, retention, disclosure, legal limitation | evidence_family_missing_required_fields | permission missing/restricted |
| EF13 | survivorship rationale | common to all 9 | historical status and membership lineage | warning, source ids, covered period, rationale, limitation | evidence_family_missing_required_fields | historical version; membership; survivorship |
| EF14 | reviewer scope / quality / limitation | common to all 9 | governed reviewer attestation | alias, role, scope, reviewed_at, quality, limitation | evidence_family_missing_required_fields | reviewer scope; privacy; quality; limitation |
| EF15 | no-hit query context | common to all 9 | reviewed query logs only | source/evidence family, terms, window, timezone, result reference, reviewer | evidence_family_missing_required_fields | no-hit misuse; timing; reference; scope |
| EF16 | profile conflict context | common to all 9 | fixture lineage and future policy authority | instrument, legacy label, recommendation, conflict, limitation | evidence_family_missing_required_fields | profile conflict; membership; official status |
| EF17 | cross-source corroboration | common to all 9 | independently sourced eligible references | source ids, fact, agreement/conflict, timing, versions, rationale | evidence_family_missing_required_fields | corroboration; circular lineage; timing/version conflict |

Source eligibility may be populated as controlled vocabulary context. It never changes evidence_presence from false in this fixture.

## J. STOCK / ETF Applicability Matrix

| applicability_rule_id | instrument_type | evidence family | selected rows | instrument_applicability | not_applicable_policy_required | status |
| --- | --- | --- | ---: | --- | --- | --- |
| APP_STOCK_ST | STOCK | EF04 STOCK ST/no-ST | 7 | applies | false | evidence_family_missing_required_fields |
| APP_ETF_ST | ETF | EF04 STOCK ST/no-ST | 2 | not_applicable_context_only | true | instrument_not_applicable_policy_context_only |
| APP_STOCK_ETF_NA | STOCK | EF05 ETF ST-not-applicable | 7 | not_applicable_context_only | true | instrument_not_applicable_policy_context_only |
| APP_ETF_ETF_NA | ETF | EF05 ETF ST-not-applicable | 2 | applies | false | evidence_family_missing_required_fields |

The 15 common families create 135 applicable rows. EF04 and EF05 create 9 applicable and 9 not-applicable context rows. Total contract rows remain 153, with 144 applicable and 9 not-applicable context rows.

The seven STOCK profile conflicts remain true. The two ETF profile alignments remain context only. No applicability row resolves a conflict or proves universe membership.

## K. Required Field Contract

### Selected-row fields

| Field | Type | Required default | Contract |
| --- | --- | --- | --- |
| row_id | string | deterministic id | Primary key. |
| historical_decision_date | date string | 2024-04-02 | Context only. |
| decision_timezone | string | Asia/Shanghai | Required decision-time policy. |
| legacy_universe_label | string | etf_core | Lineage only, not membership proof. |
| symbol | six-character string | selected symbol | Leading zeros preserved. |
| instrument_type | enum | STOCK or ETF | Routing context only. |
| recommended_profile | enum | stock_core or etf_core | Routing context only. |
| profile_conflict | boolean | true for 7 STOCK, false for 2 ETF | Never silently resolved. |
| profile_policy_status | enum | unresolved or aligned context | Not approval. |
| selected_row_blockers | delimiter-safe blocker list | non-empty | Every selected row remains blocked. |
| selected_row_sufficiency_candidate | boolean | false | Must remain false. |
| selected_row_evidence_accepted | boolean | false | Must remain false. |
| selected_row_evidence_closed | boolean | false | Must remain false. |
| selected_row_pit_admissible | boolean | false | Must remain false. |
| selected_row_replay_ready | boolean | false | Must remain false. |

### Evidence-family contract fields

| Field | Type/default | Contract |
| --- | --- | --- |
| contract_row_id | deterministic string | Primary key combining row_id and evidence_family_id. |
| row_id | string | Foreign key to selected row. |
| evidence_family_id | EF01 through EF17 | Controlled family id. |
| evidence_family_name | controlled string | Exact family name. |
| instrument_applicability | enum | applies or not_applicable_context_only. |
| not_applicable_policy_required | boolean | True for the 9 opposite instrument-specific rows. |
| purpose | text | Family purpose only. |
| eligible_source_classes | controlled list | Eligibility context only. |
| authoritative_source_class_policy | text | Family-specific authority rule, not source approval. |
| required_structural_fields | controlled list | Future completeness contract. |
| evidence_presence | boolean false | False on every selected contract row. |
| source_eligibility_context | controlled text | Vocabulary context only. |
| publish_time_required | boolean by family | Never populated with real evidence here. |
| available_time_required | boolean by family | Never adjudicated here. |
| effective_time_required | boolean by family | Never adjudicated here. |
| timezone_required | boolean by family | Policy requirement only. |
| revision_id_required | boolean by family | Policy requirement only. |
| historical_version_required | boolean by family | Policy requirement only. |
| source_reference_required | boolean by family | Policy requirement only. |
| source_hash_policy | preview_only_or_absent | No full hash value. |
| permission_class_required | boolean by family | Policy requirement only. |
| corroboration_policy | controlled text | Independent-lineage rule. |
| reviewer_scope_required | boolean by family | Does not grant authority. |
| no_hit_allowed_as_context_only | boolean | True only as bounded query context. |
| insufficiency_blockers | controlled blocker list | Non-empty for applicable default rows. |
| sufficiency_candidate | boolean false | Must remain false. |
| evidence_accepted | boolean false | Must remain false. |
| evidence_closed | boolean false | Must remain false. |
| pit_admissible | boolean false | Must remain false. |
| replay_ready | boolean false | Must remain false. |

The required-fields artifact contains exactly 45 rows: 15 selected-row field definitions plus 30 evidence-family contract field definitions.

## L. Safe Status Vocabulary

The status-vocabulary artifact contains exactly 17 rows:

| Status | Scope | Allowed on selected fixture | Meaning |
| --- | --- | --- | --- |
| evidence_family_context_only | family | no by default | Descriptive context only. |
| evidence_family_missing_required_fields | family | yes | Applicable family is structurally incomplete. |
| evidence_family_blocked_by_source_eligibility | family | yes | Eligible source-class context is missing or invalid. |
| evidence_family_blocked_by_timing | family | yes | Timing or timezone requirement blocks. |
| evidence_family_blocked_by_revision | family | yes | Revision or historical-version requirement blocks. |
| evidence_family_blocked_by_permission | family | yes | Permission or legality requirement blocks. |
| evidence_family_blocked_by_survivorship | family | yes | Survivorship rationale blocks. |
| evidence_family_sufficiency_candidate_not_accepted | family | no | Future vocabulary only; never assigned here. |
| row_has_sufficiency_candidates_not_closed | row | no | Future vocabulary only; never assigned here. |
| row_blocked_by_missing_evidence | row | yes | Required families are absent/incomplete. |
| row_blocked_by_profile_conflict | row | yes for 7 STOCK | Profile conflict remains unresolved. |
| row_blocked_by_universe_membership | row | yes | Membership/version evidence missing. |
| row_blocked_by_timing | row | yes | Timing evidence missing/unsafe. |
| row_blocked_by_revision | row | yes | Revision/history evidence missing/unsafe. |
| row_blocked_by_permission | row | yes | Permission/legal context missing/unsafe. |
| row_blocked_by_survivorship | row | yes | Survivorship rationale missing. |
| instrument_not_applicable_policy_context_only | family | yes for 9 N/A rows | Explicit opposite-instrument context; not omission or approval. |

No current selected row or family row uses either sufficiency-candidate status.

## M. Blocker Vocabulary

The blocker-vocabulary artifact contains exactly 28 rows:

| Blocker id | Category | Trigger |
| --- | --- | --- |
| blocker_missing_eligible_source_class | source | No family-eligible source class is defined. |
| blocker_missing_required_structural_fields | schema | Required future evidence fields are incomplete. |
| blocker_missing_source_reference | provenance | Stable reference is missing. |
| blocker_missing_publish_time | timing | Required publication time is missing. |
| blocker_missing_available_time | timing | Required availability time is missing. |
| blocker_missing_effective_time | timing | Required effective time is missing. |
| blocker_missing_timezone | timing | Required timezone is missing. |
| blocker_post_decision_evidence | timing | Availability is after the decision cutoff. |
| blocker_undated_evidence | timing | Evidence lacks a supported date/time. |
| blocker_timezone_ambiguity | timing | Timezone is unknown or conflicting. |
| blocker_missing_revision_id | revision | Revision id/type is missing. |
| blocker_missing_historical_version | revision | Historical version or archive is missing. |
| blocker_superseded_evidence_unresolved | revision | Supersession chain is unresolved. |
| blocker_missing_source_provenance | provenance | Parent/transformation lineage is incomplete. |
| blocker_unsafe_full_hash_disclosure | privacy | Full hash appears on a public/report surface. |
| blocker_missing_permission_class | permission | Permission context is absent. |
| blocker_forbidden_or_restricted_permission | permission | Planned use is forbidden or restricted. |
| blocker_missing_corroboration | corroboration | Required independent support is absent. |
| blocker_missing_reviewer_scope | reviewer | Reviewer role/scope is absent. |
| blocker_reviewer_private_identity_disclosed | privacy | Private reviewer identity is exposed. |
| blocker_no_hit_misuse | no-hit | No-hit is used as affirmative evidence or override. |
| blocker_same_day_quotation_misuse | status | Quote presence/absence is used as official status proof. |
| blocker_current_webpage_used_as_historical_proof | history | Current page substitutes for historical version. |
| blocker_unresolved_profile_conflict | profile | STOCK profile conflict remains unresolved. |
| blocker_missing_universe_membership_evidence | membership | Historical membership evidence is missing. |
| blocker_missing_constituent_version_evidence | membership | Constituent-list version/effective period is missing. |
| blocker_missing_survivorship_rationale | survivorship | Non-survivor-only rationale is missing. |
| blocker_forbidden_downstream_flag | safety | Any forbidden authority or side-effect flag is true. |

## N. Timing And Decision-Cutoff Contract

The timing/revision matrix contains these timing rules:

| Rule | Contract | Failure behavior |
| --- | --- | --- |
| Decision timestamp | Exact timestamp and Asia/Shanghai timezone are required for later adjudication. | Missing cutoff blocks. |
| publish_time | Records stated publication; does not alone prove availability. | Missing when required blocks. |
| available_time | Earliest supported usable time; controls knowledge boundary. | Missing or after-decision blocks. |
| effective_time | Records when the fact/rule applies. | Missing when family requires it blocks. |
| retrieval/fetch time | Acquisition time only. | Cannot substitute for available_time. |
| archive/snapshot time | Preservation time only. | Cannot silently prove historical availability. |
| Undated evidence | Never a candidate. | blocker_undated_evidence. |
| Timezone ambiguity | Must be explicit and coherent. | blocker_timezone_ambiguity. |
| Post-decision evidence | May be retrospective context only. | blocker_post_decision_evidence. |
| Revised/backfilled records | Original and revised availability histories required. | Blocks until lineage is explicit. |

The fixture stores requirements and blockers only. It stores no real timestamps and performs no PIT comparison.

## O. Revision And Historical-Version Contract

The timing/revision matrix also contains eight version rules:

| Version state | Required design behavior |
| --- | --- |
| original release | Preserve exact id, publication, availability, effective time, and reference. |
| revised release | Link to original and preserve both availability histories. |
| correction | Identify corrected fields and first availability of correction. |
| restatement | Preserve original and restated states; do not rewrite decision-time context. |
| constituent-list version | Require provider/version/effective date and exact historical list. |
| current-state page versus historical version | Current page is retrospective unless archive/version proves historical content. |
| revision_id | Required with revision_id_type; filename alone is insufficient. |
| superseded evidence | Retain in lineage and mark unresolved until a later authorized review. |

The 10 timing rules plus 8 revision rules produce exactly 18 timing/revision matrix rows.

## P. Provenance / Hash / Reference Contract

Future synthetic rows contain policy text only, never source payloads.

- Stable source references and artifact ids are required by contract.
- Transformed or local-reviewed references require parent lineage and transformation notes.
- Core metadata stores relative artifact filenames only.
- Index, status, CLI, reports, research-status, and Source-facing material expose no full hashes.
- Hash disclosure is preview-only or absent.
- Hash identity/integrity is not truth, authority, timing, permission, or sufficiency.
- Local-file hash and source hash remain distinct concepts.
- Local absolute paths must remain local implementation state and are not written to upload-safe artifacts.
- Source bytes, copied documents, target CSV values, secrets, tokens, and credentials are forbidden.

## Q. Permission / Legality Contract

permission_class is mandatory context for every family that can reference evidence.

Required policy fields include:

- allowed review use;
- storage and retention rule;
- citation/reference rule;
- transformation rule;
- disclosure/redistribution rule;
- legal limitation;
- terms/license version and effective date.

Missing permission blocks. Forbidden or restricted planned use blocks. Public accessibility is not permission. Permission never converts a source into authority or sufficiency.

## R. Reviewer / Privacy / Limitation Contract

Future reviewer context requires:

- non-private reviewer alias;
- reviewer role;
- evidence-family and sample scope;
- reviewed_at with timezone;
- quality status;
- rationale and limitation note;
- privacy-disclosure flag fixed false.

Reviewer declarations cannot override source eligibility, source reference, timing, revision, permission, survivorship, profile conflict, membership, constituent version, or corroboration blockers.

No private identity, secret, credential, token, source payload, source byte content, or private local path may enter upload-safe artifacts.

## S. No-Hit Context Contract

No-hit remains context only. Required future fields are:

- source family and evidence family;
- query terms and method;
- query-window start/end and timezone;
- query result and stable result reference;
- reviewer alias, role, scope, and reviewed_at;
- rationale and limitation.

No-hit cannot prove not-delisted, no-ST, not-suspended, universe membership, PIT validity, replay readiness, profile-conflict resolution, or survivorship closure. Post-decision query windows or source references remain blockers. A hit or conflict routes to evidence review and invalidates no-hit treatment.

## T. Profile Conflict And Universe-Membership Contract

Seven STOCK rows retain profile_conflict = true and recommended_profile = stock_core as routing context only. Two ETF rows retain profile_conflict = false and recommended_profile = etf_core as profile-aligned context only.

The fixture must preserve:

- legacy_universe_label = etf_core on all rows;
- the seven unresolved STOCK conflicts;
- the two ETF aligned-context rows;
- universe-membership blockers on all nine rows;
- constituent-version blockers on all nine rows;
- no profile-policy acceptance;
- no universe-membership approval.

Legacy labels, recommended profiles, same-day quotes, current webpages, and no-hit context are not universe proof.

## U. Health PASS / WARN / FAIL Contract

PASS requires all of the following:

- all 10 expected core artifacts exist;
- every expected schema and deterministic count matches;
- all nine leading-zero symbols are exact strings;
- 153 contract rows split into 144 applicable and 9 explicit not-applicable context rows;
- every selected row retains one or more blockers;
- no selected row or family row is a sufficiency candidate;
- evidence accepted, evidence closed, PIT admissible, replay ready, and downstream authority counts remain zero;
- every safety and side-effect flag is false;
- public/report surfaces expose no private identity, secret, source payload, full hash, or unsafe path.

WARN is reserved for review-only conditions that do not violate safety:

- optional source-eligibility vocabulary context is absent;
- optional descriptive vocabulary is incomplete;
- synthetic limitations are visible and require later review;
- an instrument-not-applicable context row is explicitly marked as requiring policy review.

Expected synthetic absence of evidence is not itself unhealthy when it is explicit, blocked, and count-correct.

FAIL applies to:

- unsafe output root or root escape;
- missing artifact, schema mismatch, or count mismatch;
- leading-zero symbol loss;
- a selected row marked candidate, accepted, closed, PIT-admissible, or replay-ready;
- forbidden/restricted permission interpreted as sufficient;
- post-decision evidence treated as valid;
- private identity, secret, source payload, full hash, or unsafe path exposure;
- forbidden downstream flag true;
- protected data write.

Health validates fixture safety and contract integrity only. PASS is not evidence sufficiency.

## V. Research-Status Integration Design

Future research-status fields use the dedicated prefix:

    latest_historical_replay_source_evidence_sufficiency_policy_contract_fixture_*

Minimum fields:

- run_id, status, health_status, workflow_stage;
- artifact path represented safely, report path, and metadata path;
- row, STOCK, ETF, evidence-family, contract-row, applicable-row, and not-applicable-row counts;
- profile conflict, aligned-context, unresolved-conflict, blocker-row, and safety counts;
- sufficiency-candidate, accepted, closed, PIT-admissible, and replay-ready counts;
- recommended_next_task;
- every required negative proof and downstream safety field.

Research-status must summarize current fixture artifacts only. It must not read external evidence, source payloads, or optional external references.

The fixture component is lower-priority report-only research context. If later paper workflow context exists, final workflow priority remains PAPER_WORKFLOW_READY. No fixture field may promote evidence, PIT, replay, paper, buy-review, or trading readiness.

## W. Future Test And CLI Smoke Design

Required future focused test files:

- tests/test_historical_replay_source_evidence_sufficiency_policy_contract_fixture.py
- tests/test_historical_replay_source_evidence_sufficiency_policy_contract_fixture_views.py
- tests/test_historical_replay_source_evidence_sufficiency_policy_contract_fixture_cli.py
- tests/test_local_research_dashboard.py

Required test groups:

| Test group | Required assertions |
| --- | --- |
| Core deterministic contract | Exact 10 artifacts, 9 rows, 17 families, 153 contracts, 144 applicable, 9 N/A context rows. |
| Leading-zero identity | Exact ordered symbol strings remain unchanged. |
| STOCK/ETF applicability | EF04 and EF05 produce the exact 7/2 applicability and 9 N/A split. |
| Default state | Evidence presence and all candidate/acceptance/closure/PIT/replay fields false. |
| Blocked selected rows | All nine selected rows retain blockers; seven STOCK conflicts remain. |
| Vocabulary | Exactly 17 statuses and 28 blockers; future candidate statuses not assigned. |
| Timing/revision | Exactly 18 rules and all unsafe cases map to blockers. |
| Output-root safety | Protected roots and path escapes rejected. |
| Privacy/disclosure | No private identity, source payload, full hash, secret, credential, or unsafe path. |
| Index | Single synthetic run yields one safe index row. |
| Health | Safe fixture PASS; warning-only context WARN; unsafe mutation FAIL. |
| Status | Latest valid run summarized; no-artifact mode benign and zero-count. |
| CLI | Four commands registered, safe arguments only, FAIL returns nonzero. |
| Research-status | Dedicated latest_* fields visible and PAPER_WORKFLOW_READY priority preserved. |
| Next-task wording | New route appears on all live surfaces; completed route remains only in negative regression expectations. |
| Side effects | No protected data, project-source tree, external call, replay, or downstream authority. |

Future temp-root smoke must run all four command-family members plus research-status under a repository-external temporary root. It must verify exact counts, artifact existence, PASS health for the safe fixture, safe disclosure, and no protected writes.

Future repository checks include the protected tracked scan, docs/project_sources scan, and git diff --check.

Full non-slow remains a later checkpoint or pre-tag gate. It is not part of this design task.

## X. Future Implementation File Scope

Proposed implementation files:

- src/quant_replay_system/historical_replay_source_evidence_sufficiency_policy_contract_fixture.py
- src/quant_replay_system/historical_replay_source_evidence_sufficiency_policy_contract_fixture_index.py
- src/quant_replay_system/historical_replay_source_evidence_sufficiency_policy_contract_fixture_health.py
- src/quant_replay_system/historical_replay_source_evidence_sufficiency_policy_contract_fixture_status.py
- src/quant_replay_system/cli.py
- src/quant_replay_system/local_research_dashboard.py
- tests/test_historical_replay_source_evidence_sufficiency_policy_contract_fixture.py
- tests/test_historical_replay_source_evidence_sufficiency_policy_contract_fixture_views.py
- tests/test_historical_replay_source_evidence_sufficiency_policy_contract_fixture_cli.py
- tests/test_local_research_dashboard.py

This is a future proposal only. None of these files is created or modified by this design task.

## Y. Safety And Forbidden Interpretations

This design and any future synthetic fixture must not be interpreted as:

- real evidence collection, reading, retrieval, or template filling;
- evidence presence on selected contract rows;
- a sufficiency candidate assigned to any current row;
- evidence acceptance or closure;
- source truth, source reliability scoring, or universal source authority;
- profile-conflict resolution, universe approval, or stock-profile validation;
- PIT approval, active replay input, replay execution, decision freeze, or labels;
- metrics, training, model, weights, thresholds, or signal-score authority;
- paper expansion, buy-review eligibility, or buy-review permission;
- current-candidates, snapshots, signal-semantics mutation, broker, API, LLM, orders, messages, or trading;
- protected data writes;
- a checkpoint, tag, Source update, or upload package.

## Z. Candidate Next Routes

| Route | Decision | Reason |
| --- | --- | --- |
| A. Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Core / Views / CLI / Research-Status Milestone Bundle Report-Only v0.1 | selected | Counts, applicability, vocabulary, artifacts, health, privacy, tests, and research-status behavior are deterministic and internally coherent. |
| B. Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Design Hardening Report-Only v0.1 | not selected | No material ambiguity remains in counts, status semantics, applicability, privacy, health, or research-status behavior. |
| C. Historical Replay Official Manual Evidence Collection Fill Protocol Design Report-Only v0.1 | not selected | Collection preparation remains premature before the synthetic fixture contract is implemented and reviewed. |
| D. Pause repository work and manually research official source/status evidence outside the repository | not selected | Safe repository-side fixture implementation remains available; evidence collection is not authorized. |
| E. Continue another historical replay governance branch | not selected | Source/evidence sufficiency remains the current blocking governance branch. |

## AA. Selected Next Route

Exactly one route is selected:

    Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Core / Views / CLI / Research-Status Milestone Bundle Report-Only v0.1

The design is deterministic and implementable without high-risk semantic adjudication. The future bundle may encode only synthetic contract rows, views, CLI wiring, health checks, research-status context, and tests. It must not collect or apply evidence.

## AB. Current / Next Mode Recommendation

Current task ChatGPT review:

- surface: Chat
- model: GPT-5.6 Sol
- ChatGPT mode: Extra High
- speed: Standard

Current execution side:

- surface: Codex
- environment: Local
- model: GPT-5.6 Sol
- effort: Extra High
- speed: Standard
- task mode: Goal

Next Goal identity:

    Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Core / Views / CLI / Research-Status Milestone Bundle Report-Only v0.1

Required next acceptance artifact set:

- the four proposed fixture modules;
- CLI command-family registration;
- local dashboard/research-status integration;
- the four proposed focused test files;
- a repository-external temp-root smoke bundle containing all 10 core artifacts and index/health/status outputs;
- exact count, safety, disclosure, priority, protected-path, and Git proof.

Previous Goal that the next task must not repeat:

    Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Design Report-Only v0.1

Next execution recommendation:

- surface: Codex
- environment: Local
- model: GPT-5.6 Sol
- effort: Extra High
- speed: Standard
- task mode: Goal

ChatGPT and the user must approve this design before that Goal is created or implementation begins. Model strength and Goal activation do not expand evidence, PIT, replay, paper, buy-review, or trading authority.

## AC. Commit / Tag / Source Recommendation

Recommended commit message if reviewed and ready:

    docs: design historical replay source evidence sufficiency policy contract fixture

Recommended tag:

    No tag.

Recommended Source update:

    No Source update.

Recommended next task:

    Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Core / Views / CLI / Research-Status Milestone Bundle Report-Only v0.1

No git add, commit, push, or tag is authorized by this task.
