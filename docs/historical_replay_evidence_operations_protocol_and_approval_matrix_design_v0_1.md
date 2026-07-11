# S5-WP01 Evidence Operations Protocol And Approval Matrix Design Report-Only v0.1

## A. Decision And Status

```text
phase = S5_WP01_EVIDENCE_OPERATIONS_PROTOCOL_AND_APPROVAL_MATRIX_DESIGN
decision = ready
privacy_issue_stop = no
docs_only = yes
design_only = yes
report_only = yes

acceptance_artifact_id = S5_WP01_EVIDENCE_OPERATIONS_PROTOCOL_ACCEPTED
acceptance_artifact_status = CANDIDATE_PENDING_HUMAN_REVIEW
report_created = yes

formal_checkpoint = v1.90.0
formal_checkpoint_commit = 8792dbc66349a2f76139d9e0885d7182bacaf859
formal_checkpoint_tag = v1.90.0
Master_Plan_baseline = V1.0
current_stage = Stage 5
current_work_package = S5-WP01

real_evidence_read = no
external_source_accessed = no
website_fetched = no
external_API_called = no
real_evidence_collected = no
evidence_template_filled = no
sufficiency_assigned = no
evidence_accepted = no
evidence_closed = no
profile_conflict_resolved = no
official_status_resolved = no
universe_membership_approved = no
PIT_admissibility_approved = no
replay_input_promoted = no
replay_executed = no
forward_labels_created = no
metrics_computed = no
model_trained_or_promoted = no
stock_profile_promoted = no
paper_promoted = no
real_buy_review_created = no
trading_allowed = no
protected_data_written = no

baseline_prompt_delta = 1
selected_next_route = Manual S5-WP01 Design Artifact Review And Commit Decision
```

Decision: this report provides a complete candidate protocol and approval matrix for human review. It converts the accepted `v1.90.0` contract into operational design without accessing a source, handling evidence, changing an evidence state, or authorizing S5-WP02.

## B. Formal Anchor And Baseline Authority

Preflight verified the following before this file was created:

| Item | State |
|---|---|
| Branch | `main` |
| Initial worktree | clean; `main...origin/main` |
| HEAD | `8792dbc66349a2f76139d9e0885d7182bacaf859` |
| `origin/main` | `8792dbc66349a2f76139d9e0885d7182bacaf859` |
| Describe | `v1.90.0` |
| Tag at HEAD | `v1.90.0` |
| Previous tag | `v1.89.0` at `7ca9c4d` |
| Tracked/status Project Source scans | empty |
| Initial `git diff --check` | passed |

Baseline authority supplied for this work package:

```text
approval_phrase = APPROVE_QUANT_S5_WP01_EVIDENCE_OPERATIONS_PROTOCOL_AND_APPROVAL_MATRIX_DESIGN_V0_1
work_package_id = S5-WP01
planned_codex_prompts = 4
conditional_risk_reserve = 1
this_goal_prompt_accounting_delta = 1
real_evidence_read_or_collection_authorized = no
S5_WP02_authorized = no
```

The `v1.90.0` checkpoint and Master Plan V1.0 baseline are authority anchors, not evidence. This Goal consumes one planned S5-WP01 prompt but does not change the external Project Source or canonical Master Plan burn-down.

Repository governance reviewed read-only included:

- the `v1.90.0` Source / Evidence Sufficiency Policy design, checkpoint, validation, and tag/source readiness reports;
- the mixed STOCK/ETF profile policy planning and checkpoint chain;
- official source hierarchy and evidence collection planning/worklist design;
- official manual evidence collection template design and fixture governance;
- reviewer no-hit planning and fixture governance;
- reviewer authority, quality, limitation, permission, disclosure, hash, revision, and available-time policies;
- the quantitative research design pack and checkpoint/artifact conventions.

No historical recommended-next-task text was treated as current authority.

## C. Goal Identity, Acceptance Artifact, And Non-Goals

Goal identity:

`S5-WP01 Evidence Operations Protocol And Approval Matrix Design Report-Only v0.1`

Required acceptance artifact:

`docs/historical_replay_evidence_operations_protocol_and_approval_matrix_design_v0_1.md`

Candidate acceptance record:

```text
acceptance_artifact_id = S5_WP01_EVIDENCE_OPERATIONS_PROTOCOL_ACCEPTED
acceptance_artifact_status = CANDIDATE_PENDING_HUMAN_REVIEW
```

The previous Master Plan creation/freeze Goal is not repeated. This report designs future controls only. It does not:

- access, browse, fetch, read, collect, copy, parse, hash, or store real evidence;
- select a real source, host, URL, file, row, date subset, or evidence family for S5-WP02;
- populate a template or assign presence, sufficiency, acceptance, closure, profile/status/membership, PIT, or replay state;
- implement code, tests, CLI behavior, data writes, Project Source, or Master Plan changes;
- create labels, metrics, models, stock_profile promotion, paper promotion, buy-review, messages, orders, or trading behavior.

## D. Definitions And Semantic Separation

| Term | Protocol meaning | Explicitly not |
|---|---|---|
| Source eligibility | Policy-level determination that a source class and proposed use may be considered. | Access, permission, reliability, evidence, or approval. |
| Source access authorization | Exact approval to perform a bounded read operation. | Collection, storage, evidence presence, or open-ended access. |
| Evidence collection authorization | Exact approval to capture specified metadata or content within an approved envelope. | Acceptance, closure, PIT, or replay. |
| Evidence presence | A captured record exists and remains unreviewed. | Sufficiency, truth, authority, or decision-time validity. |
| Sufficiency candidate | A separately proposed evidence set appears complete enough for review. | Acceptance, closure, PIT, or replay readiness. |
| Evidence acceptance | An authorized reviewer accepts bounded evidence for an exact family/row/date scope. | Closure, profile resolution, PIT, or downstream execution. |
| Evidence closure | An authorized decision records that the evidence question is closed for a versioned scope. | Immutable truth, PIT approval, or replay permission. |
| Profile/status/membership resolution | Separate domain decisions supported by accepted evidence. | Automatic effects of collection or closure. |
| PIT admissibility | Separate determination that inputs were available and valid at the historical decision boundary. | Source quality, evidence acceptance alone, or replay execution. |
| Replay-input eligibility | Separate promotion decision for a bounded, PIT-approved input package. | Replay execution or labels. |
| Replay execution | Separately authorized deterministic run. | Evidence review, trading, or production authority. |

Controlling separation:

```text
source eligibility
!= source access authorization
!= evidence collection authorization
!= evidence presence
!= evidence sufficiency candidate
!= evidence acceptance
!= evidence closure
!= profile/status/membership resolution
!= PIT admissibility
!= replay readiness
!= replay execution
```

No status, reviewer role, source rank, no-hit, quotation, hash, revision, available-time field, or audit receipt may collapse these gates.

## E. Canonical Source-Access Classes

All classes are design vocabulary only in S5-WP01. Except for reading tracked synthetic/governance repository material for this report, real access and collection remain unauthorized.

| Class ID | Name | Current role | Eligibility assessment | Access/read default | Capture approval | Storage policy | Authentication and access-control rule | Permission, privacy, audit, and stop rule | Downstream authority |
|---|---|---|---|---|---|---|---|---|---|
| `SRC-01` | Repository-local synthetic/governance material | Read-only design reference. | Policy classification allowed for tracked synthetic material only. | Allowed only for tracked repository governance within task scope. | Separate approval required for any evidence-like capture; synthetic report creation follows exact file scope. | Synthetic text may remain in approved docs; no real content or private paths. | No authentication material may be used or inspected. | Confirm tracked path and synthetic status; receipt required for future operations; stop on real/private/protected content. | None. |
| `SRC-02` | User-provided reviewed local material | Future reviewed handoff class. | May be proposed, not adjudicated here. | Not allowed by default. | Exact source/file class, purpose, row/date/family, and retention approval required. | Reference plus safe metadata by default; content/bytes require separate storage approval. | Never reuse credentials; private identity mapping stays outside Git and Project Source. | Verify user authority, permission, lineage, revision, timing, privacy, and approved root; stop on private-path disclosure or scope drift. | None. |
| `SRC-03` | Public official or exchange source, read-only | Preferred future official evidence class. | May be assessed after exact registration. | Not allowed by default in S5-WP01. | Separate bounded reading and capture approvals required. | Stable reference plus provenance metadata by default. | No login, bypass, evasion, undocumented endpoint, or access-control circumvention. | Public access is not permission; record terms, rate limit, revision, available time, and receipt; stop if any is unknown. | None. |
| `SRC-04` | Public non-official contextual source | Corroboration or context only. | May be assessed with explicit limitation. | Not allowed by default. | Separate exact approval; cannot substitute for required official evidence. | Reference-only by default; excerpt/content requires separate approval. | Respect access controls and publisher terms; no automated expansion. | Require source tier, limitations, corroboration rule, and receipt; stop if presented as official authority. | None. |
| `SRC-05` | Explicitly authorized API or paid source | Future bounded licensed-access class. | Only after permission and license review. | Not allowed by default. | Exact endpoint/operation, fields, limits, time, retention, and actor approval required. | Store only approved metadata or content under an approved retention class. | Authentication material remains outside artifacts; no credential reuse; honor quotas and access controls. | Terms/version, redistribution, privacy, rate limit, and receipt mandatory; stop on license ambiguity or scope expansion. | None. |
| `SRC-06` | Login-restricted, paywalled, CAPTCHA-gated, rate-limit-protected, or otherwise restricted source | Restricted proposal class only. | May be classified as restricted; usability is not established. | No. | Not eligible for capture without a separate high-risk approval and lawful access proof. | Reference to restriction category only until separately approved. | No bypass, paywall/CAPTCHA evasion, undocumented endpoint, credential borrowing, private-group access, or rate-limit evasion. | Mandatory stop by default; privacy/permission review and dual approval required before any future reconsideration. | None. |
| `SRC-07` | Private, insider, illegally obtained, non-public, or prohibited source | Prohibited class. | Only prohibition classification is allowed. | Never. | Never. | No content, bytes, excerpts, private identifiers, or paths stored; retain only a safe stop receipt if needed. | No authentication, access, copying, sharing, or transformation. | Immediate stop, quarantine safe metadata if necessary, escalate to human governance, and do not inspect content. | None. |

Common rules:

1. Source class rank is not reliability or sufficiency.
2. Public accessibility is not permission.
3. A source name is not access authorization.
4. Restricted or prohibited sources cannot be made usable through technical workarounds.
5. Rate limits, terms, approved operations, and time windows are hard boundaries.
6. Every future real operation requires an exact scope and append-only receipt.
7. Every class grants zero PIT, replay, model, paper, buy-review, or trading authority.

## F. Evidence Capture Field Contract

Every future evidence record must use a versioned schema. Missing timing, revision, permission, privacy, reviewer, blocker, or audit fields block promotion beyond `present_unreviewed`.

### Identity and scope

| Field | Requirement |
|---|---|
| `evidence_record_id` | Immutable unique record id; never reused after correction. |
| `evidence_family_id` | Controlled evidence-family identifier. |
| `selected_row_id` | Exact selected-row identifier; required when row-scoped. |
| `symbol` | String identifier with leading zeroes preserved; required when symbol-scoped. |
| `instrument_type` | Controlled `STOCK`, `ETF`, or separately approved type. |
| `historical_decision_date` | Exact date within the approval envelope. |
| `decision_timezone` | Required decision timezone. |
| `collection_scope_id` | Links the record to the exact approved pilot envelope. |
| `source_access_class` | One canonical `SRC-*` class. |

### Source and permission

| Field | Requirement |
|---|---|
| `source_id` | Stable controlled id, not a credential or private path. |
| `source_name` | Safe human-readable name. |
| `source_type` | Controlled source type. |
| `source_tier` | Governance priority only; not authority or reliability. |
| `official_or_exchange_flag` | Declared classification requiring review. |
| `public_access_flag` | Access observation only; not permission. |
| `permission_class` | Required controlled permission state. |
| `legality_status` | Required reviewed legality state; unknown blocks. |
| `authentication_required` | Boolean/context field; secrets never enter the record. |
| `terms_or_permission_review_status` | Required terms/license review state and version reference. |
| `access_operation_authorized` | Must link to an exact approval; default false. |
| `collection_operation_authorized` | Must link to a separate exact approval; default false. |

### Time and revision

| Field | Requirement |
|---|---|
| `event_time` | Fact/event time when applicable; cannot replace availability. |
| `publish_time` | Stated publication time; cannot alone prove availability. |
| `available_time` | Earliest supported usable time; required for decision-time use. |
| `fetch_time` | Acquisition time only. |
| `decision_time` | Exact historical cutoff with timezone. |
| `timezone_policy` | Source and decision timezone interpretation. |
| `revision_id` | Required version/publication/announcement/package identifier; filename alone is invalid. |
| `revision_time` | Time the revision became available. |
| `supersedes_record_id` | Link to prior record without overwriting it. |
| `future_information_check` | Controlled result showing whether post-decision information is present. |
| `original_available_time` | Preserved for corrected/revised records. |
| `revision_lineage_status` | Complete, incomplete, conflicting, or blocked. |

### Content and storage

| Field | Requirement |
|---|---|
| `url_or_reference_id` | Stable reference identifier; no real value is selected here. |
| `local_reference_id` | Opaque approved id only; no private absolute path. |
| `reference_only_or_stored_content` | Controlled retention mode. |
| `content_retention_class` | Required before any content is stored. |
| `source_hash_metadata_policy` | Preview/hidden policy; full private hash excluded from public surfaces. |
| `local_file_hash_metadata_policy` | Separate from source hash and not PIT evidence. |
| `parser_or_extraction_version` | Required for transformed/extracted observations. |
| `copied_excerpt_policy` | Explicit size/purpose/retention approval; default none. |
| `copyright_and_bulk_copy_restriction` | Required before excerpt/full-content handling. |
| `private_path_disclosure_rule` | Must prohibit private absolute path disclosure. |
| `parent_reference_id` | Required for transformed or derived records. |
| `transformation_notes` | Versioned, reproducible, and non-sensitive. |

### Review and quality

| Field | Requirement |
|---|---|
| `reviewer_alias` | Stable non-identifying alias. |
| `reviewer_role` | Controlled role. |
| `reviewer_scope` | Exact source/family/row/date/operation scope. |
| `reviewer_attestation` | Versioned statement tied to decision time. |
| `conflict_of_interest_status` | Required declaration; unresolved conflicts block. |
| `quality_status` | Controlled quality state; does not equal acceptance. |
| `limitations` | Required for missing, partial, inferred, warning, conflict, no-hit, or not-applicable context. |
| `blocker_codes` | Controlled blockers; cannot be overridden by reviewer authority. |
| `warning_codes` | Controlled warnings requiring visible disposition. |
| `reviewer_notes_policy` | Safe, bounded notes; no identity, source content, or private path. |
| `dual_review_status` | Required when the operation policy calls for separation. |

### Evidence state

| Field | Requirement |
|---|---|
| `evidence_presence_status` | Defaults to `not_collected`; capture can move only to `present_unreviewed`. |
| `sufficiency_candidate_status` | Separate proposal state; default none. |
| `acceptance_status` | Separate accept/reject state; default not reviewed. |
| `closure_status` | Separate closure state; default open/not closed. |
| `reopen_status` | Separate controlled reopen/supersede state. |
| `profile_status_membership_effect` | Must remain none unless separately approved. |
| `PIT_effect` | Must remain none unless separately approved. |
| `replay_effect` | Must remain none unless separately approved. |

### Audit

| Field | Requirement |
|---|---|
| `created_at` | Timestamp with timezone. |
| `created_by_alias` | Non-identifying actor alias. |
| `approval_record_id` | Exact approval authorizing the operation. |
| `operation_receipt_id` | Append-only receipt identifier. |
| `previous_state` | State before the proposed operation. |
| `new_state` | Proposed/final state, never silently substituted. |
| `reason` | Bounded rationale. |
| `protocol_version` | Exact protocol version. |
| `schema_version` | Exact evidence record schema version. |

## G. Reference Versus Stored-Content Policy

Default policy: prefer stable reference plus provenance metadata. Full content or opaque bytes require a separate future collection-and-storage approval.

| Retention class | Allowed representation | S5-WP01 status | Future minimum gate | Forbidden interpretation |
|---|---|---|---|---|
| `RET-00_DESIGN_ONLY` | Schema and policy text only. | Allowed for this report. | Exact docs-only scope. | Evidence presence. |
| `RET-01_PUBLIC_REFERENCE_ONLY` | Stable public reference id plus source metadata. | Not populated here. | Bounded read approval and permission review. | Content collection or acceptance. |
| `RET-02_REFERENCE_PLUS_SAFE_PREVIEW` | Reference plus non-sensitive hash/id preview. | Not populated here. | Disclosure policy and exact capture approval. | Full-hash verification, truth, or PIT validity. |
| `RET-03_LOCAL_METADATA_ONLY` | Structured metadata under approved local root. | Not authorized here. | Collection approval, root, retention, reviewer, and receipt. | Source content storage. |
| `RET-04_LOCAL_BOUNDED_EXCERPT` | Minimum excerpt needed for review. | Not authorized. | Copyright, permission, size, purpose, retention, and dual review. | Bulk copying or redistribution. |
| `RET-05_LOCAL_FULL_CONTENT` | Full approved document content. | Not authorized. | Separate high-risk content-storage approval and legal/privacy review. | Project Source or repository inclusion. |
| `RET-06_LOCAL_OPAQUE_BYTES` | Exact approved opaque bytes. | Not authorized. | Separate high-risk byte-storage approval, approved root, lifecycle, and dual review. | Evidence acceptance, source authority, or disclosure. |
| `RET-07_RESTRICTED_OR_PRIVATE` | Safe stop/quarantine metadata only. | Content prohibited. | Separate legal/privacy escalation; prohibited content is not inspected. | Usable evidence. |

Surface rules:

- Project Source: policy, checkpoint, safe counts, references, and previews only; never full content, private paths, private identity mapping, authentication material, or full private source hash.
- Repository: synthetic governance and approved code/tests/docs only; no filled evidence template, real source content, opaque bytes, or private evidence package.
- Local diagnostics: only within an explicitly approved root and retention class; still subject to privacy, permission, receipt, and deletion policy.
- Copyrighted/restricted content: reference-only unless an exact future approval states lawful excerpt/full-content handling.
- Personal/private information: minimize, redact, quarantine, and stop; never enter Git or Project Source.
- Source hash and local-file hash are separate identity metadata and never truth, permission, timing, or sufficiency.

## H. Reviewer Alias, Role, Privacy, And Conflict Policy

### Identity and scope

- Use a stable non-identifying `reviewer_alias`.
- Keep any alias-to-private-identity mapping outside Git, Project Source, generated reports, and evidence artifacts.
- Do not record a full name, email, account id, phone number, address, or private identifier.
- Require `reviewer_role`, exact `reviewer_scope`, `reviewer_attestation`, `reviewed_at`, timezone, and `conflict_of_interest_status`.
- Reviewer notes must follow the safe bounded notes policy and must not reproduce source content or private paths.

### Approval separation

One exact human approval may be sufficient only for a low-risk, bounded, read-only operation against an already reviewed public official source when:

- the approval names source class, source/host placeholder, operation, family, row/date scope, maximum records, time/rate limit, reference-only handling, and stop conditions;
- the approver is not the collection actor;
- permission, privacy, and conflicts are clear;
- no content storage or state transition is requested.

Dual review or equivalent actor/decision separation is required for:

- restricted, paid, login-controlled, or permission-sensitive access;
- excerpt, full-content, or opaque-byte storage;
- sufficiency-candidate assignment when evidence is contested or incomplete;
- evidence acceptance, closure, correction after closure, or reopen;
- profile conflict, official status, universe membership, PIT, or replay-input decisions;
- conflicting sources, material limitations, survivorship concerns, or reviewer conflict of interest;
- every downstream promotion after evidence closure.

### Non-override rule

Reviewer authority, attestation, seniority, agreement, or dual review cannot override:

- prohibited source class or unknown permission;
- missing source identity, revision lineage, available time, or timezone;
- post-decision information, source conflict, quality failure, or material limitation;
- privacy, access-control, retention, copyright, or protected-path blockers;
- a requirement for a separate PIT, replay, model, paper, buy-review, or trading approval.

Disagreement routes to `disputed` or `unresolved_conflict`; it never silently selects the more permissive result.

## I. Operation-Level Approval Matrix

Global S5-WP01 rule: the only authorized operation is designing and documenting this matrix. Every real operation A-Z below is `NOT_AUTHORIZED`. Every row grants downstream authority `NONE`.

| ID | Operation | S5-WP01 permission | Minimum future prerequisite and exact scope | Human approval / actor separation | Receipt and state transition | Mandatory stop / explicitly not granted |
|---|---|---|---|---|---|---|
| A | Register or classify a source | `NOT_AUTHORIZED` | Source class, safe source id, proposed use, permission class, owner, jurisdiction, and no-access classification scope. | Exact registrar approval; registrar alias recorded; reviewer separate if restricted. | Registration receipt; `unregistered -> registered_unapproved`. | Stop on private/prohibited content or unknown class; no access, collection, or reliability. |
| B | Assess source eligibility | `NOT_AUTHORIZED` | Registered source, proposed evidence family/use, permission, terms, privacy, and access-control review. | Exact eligibility approval; reviewer not collection actor; dual review for contested/restricted sources. | Eligibility receipt; `registered_unapproved -> eligible_candidate` or `ineligible`. | Stop on unknown permission/legality; no access, evidence, sufficiency, or authority. |
| C | Authorize read-only source access | `NOT_AUTHORIZED` | Exact class/source/host placeholder, operation, actor, time/rate limit, network method, and reference-only rule. | One exact human approval only for low-risk public official access; otherwise dual review. | Access-approval receipt; no evidence-state change. | Stop on bypass, host drift, authentication ambiguity, or rate-limit conflict; no collection. |
| D | Authorize bounded source reading | `NOT_AUTHORIZED` | Approved access plus exact documents/records maximum, family, row/date scope, and observation limits. | Approver separate from reader; dual review for restricted/paid access. | Read-operation receipt; no evidence-state change. | Stop on content outside envelope or private data; no capture, storage, or evidence presence. |
| E | Authorize evidence collection or capture | `NOT_AUTHORIZED` | Approved bounded reading, exact fields, maximum records, family/row/date, retention class, root, and reviewer. | Separate collection approval; actor and reviewer separated. | Capture receipt; `not_collected -> present_unreviewed` only. | Stop on permission/timing/revision/scope defects; no sufficiency or acceptance. |
| F | Authorize content storage rather than reference-only handling | `NOT_AUTHORIZED` | Exact retention class, content type/size, lawful basis, root, lifecycle, redaction, and deletion rule. | Dual approval including privacy/permission review; storage actor separate. | Storage receipt; content state only, no evidence promotion. | Stop on copyright, private data, protected paths, or excess content; no acceptance/PIT. |
| G | Populate an evidence template | `NOT_AUTHORIZED` | Approved collected records, exact template/schema version, rows/families/dates, and actor. | Exact population approval; reviewer separate from preparer. | Population receipt; remains `present_unreviewed`. | Stop on missing lineage or unapproved fields; no presence adjudication or sufficiency. |
| H | Assign evidence presence | `NOT_AUTHORIZED` | Populated record, source/reference existence check, lineage, permission, and scope match. | Exact review approval; reviewer separate from collector when practical. | Presence receipt; `present_unreviewed` recorded, not promoted. | Stop on absent/ambiguous source or scope mismatch; no sufficiency/acceptance. |
| I | Assign a sufficiency candidate | `NOT_AUTHORIZED` | Presence reviewed, required fields complete, blockers zero or explicitly unresolved, limitations visible, corroboration policy met. | Separate exact approval; dual review for contested/material cases. | Candidate receipt; `present_unreviewed -> sufficiency_candidate`. | Stop on any hard blocker; no acceptance, closure, PIT, or replay. |
| J | Accept or reject evidence | `NOT_AUTHORIZED` | Candidate set, exact family/row/date, source/revision/time evidence, quality, limitations, and conflict disposition. | Dual review; acceptance decision-maker separate from collector/preparer. | Decision receipt; `sufficiency_candidate -> accepted` or `rejected`. | Stop on disagreement or unresolved blocker; no closure/profile/PIT. |
| K | Close evidence | `NOT_AUTHORIZED` | Accepted evidence, closure criteria/version, open issues zero or explicitly retained, and downstream effects fixed none. | Separate dual-review closure approval. | Closure receipt; `accepted -> closed`. | Stop on unresolved conflict/revision/limitation; no PIT or replay readiness. |
| L | Reopen or correct closed evidence | `NOT_AUTHORIZED` | Closed record id, correction reason, new source/revision/time context, preservation plan, and supersession link. | Dual review with authority equal to or above closure; prior actor cannot silently self-correct. | Append-only correction/reopen receipt; `closed -> reopened` or `superseded`. | Stop on destructive mutation or missing prior state; no automatic reacceptance. |
| M | Resolve profile conflict | `NOT_AUTHORIZED` | Accepted/closed relevant evidence, profile policy, exact symbols/date, limitations, and separate domain review. | Dual domain review; independent from evidence collector. | Profile receipt; parallel profile state only. | Stop on legacy-label inference or no-hit substitution; no status/membership/PIT. |
| N | Resolve official status | `NOT_AUTHORIZED` | Accepted official status evidence for exact status/family/symbol/date and revision. | Dual domain review. | Status receipt; parallel official-status state only. | Stop on quotation-only inference or missing official lineage; no membership/PIT. |
| O | Approve universe membership | `NOT_AUTHORIZED` | Accepted historical constituent/version evidence, provider, effective/available times, exact universe/symbol/date. | Dual domain review. | Membership receipt; parallel membership state only. | Stop on legacy label or current list substitution; no PIT/replay. |
| P | Approve PIT admissibility | `NOT_AUTHORIZED` | Closed evidence plus independently reviewed availability, revision, leakage, decision cutoff, and all parallel prerequisites. | Separate exact PIT approval with independent reviewer. | PIT receipt; `not_assessed -> PIT_candidate -> approved/rejected`. | Stop on missing/after-decision/conflicting timing; no replay execution. |
| Q | Promote replay-input eligibility | `NOT_AUTHORIZED` | PIT-approved bounded package, immutable lineage, exact schema/version, negative downstream flags, and human review. | Separate dual approval; no collector self-promotion. | Promotion receipt; replay-input eligibility parallel state only. | Stop on any mutation or scope drift; no replay execution or `ACTIVE_REPLAY_INPUT_READY`. |
| R | Execute replay | `NOT_AUTHORIZED` | Eligible immutable input, exact replay config/version, output root, side-effect guard, and run approval. | Separate execution approval; operator distinct from evidence/PIT approver. | Execution receipt; `not_authorized -> authorized_run -> executed`. | Stop on current-data/network/trading side effects; no freeze, labels, or model authority. |
| S | Freeze replay decisions | `NOT_AUTHORIZED` | Completed deterministic replay, reviewed outputs, exact decision ids, immutable hash/lineage, and freeze approval. | Separate dual review. | Freeze receipt; replay-decision state only. | Stop on mutable inputs or unresolved review; no labels/training. |
| T | Generate forward labels | `NOT_AUTHORIZED` | Frozen decisions, approved horizon/benchmark/calendar policy, future-data separation, and label approval. | Separate exact approval and leakage review. | Label receipt; label state only. | Stop on decision-time join leakage; no metric/model authority. |
| U | Compute evaluation metrics | `NOT_AUTHORIZED` | Governed labels/dataset, predefined metric plan, sample counts, benchmark/industry policy, and evaluation approval. | Separate exact approval; evaluator independent where material. | Metric receipt; descriptive evaluation state only. | Stop on unplanned metrics or overclaim; no performance validation. |
| V | Train or promote models | `NOT_AUTHORIZED` | Approved dataset/evaluation, leakage controls, OOS/walk-forward plan, model/parameter/version governance. | Separate model training and separate promotion approvals. | Training/promotion receipts; model states remain distinct. | Stop on weak evaluation or hidden refit; no production/trading authority. |
| W | Promote stock_profile | `NOT_AUTHORIZED` | Approved model/evidence dossier, symbol-level validation, limitations, and exact stock_profile approval. | Separate dual domain review. | stock_profile receipt; dossier state only. | Stop on feature-importance substitution; no paper/buy-review. |
| X | Promote paper workflow | `NOT_AUTHORIZED` | Validated stock_profile, paper protocol, monitoring, limits, and exact paper approval. | Separate exact paper approval. | Paper receipt; paper state only. | Stop on missing validation; no real buy-review or trading. |
| Y | Create a real buy-review candidate | `NOT_AUTHORIZED` | Separately approved paper evidence, human review protocol, current-data authorization, risk controls, and exact candidate scope. | Exact human approval for each candidate; no automation. | Buy-review receipt; candidate review state only. | Stop on stale/insufficient evidence; no order or trading permission. |
| Z | Broker, order, message, or trading behavior | `NOT_AUTHORIZED` | Outside S5-WP01 and outside this protocol's authority; would require separate legal, operational, security, risk, and human approvals. | Explicit separate authorization at each irreversible action. | Dedicated operational receipt, never an evidence receipt. | Stop by default; no broker/API/order/message/trading authority is granted. |

The matrix is not a blanket future approval. A future operation is unauthorized unless its exact approval record exists and all prerequisites are independently satisfied.

## J. Evidence And Governance State-Transition Model

### Evidence lifecycle

```text
not_collected
  -> present_unreviewed
  -> sufficiency_candidate
  -> accepted | rejected | disputed
  -> closed
  -> reopened | superseded
```

| From | Allowed next state | Required gate | Forbidden shortcut |
|---|---|---|---|
| `not_collected` | `present_unreviewed` | Approved bounded capture and receipt. | Source eligibility directly to accepted. |
| `present_unreviewed` | `sufficiency_candidate`, `rejected`, or `disputed` | Separate scoped review. | Presence directly to closed. |
| `sufficiency_candidate` | `accepted`, `rejected`, or `disputed` | Separate evidence decision. | Candidate directly to PIT. |
| `accepted` | `closed`, `disputed`, or correction-pending | Separate closure or dispute decision. | Accepted directly to replay ready. |
| `rejected` | `reopened` only with new basis | Reopen approval and append-only link. | Silent replacement with accepted. |
| `closed` | `reopened` or `superseded` | Equal-or-higher authority and preserved prior record. | Destructive mutation or automatic PIT. |
| `disputed` | `rejected`, `accepted`, or `unresolved_conflict` | Escalation, conflict record, and dual review. | More-permissive default. |
| `reopened` | `present_unreviewed` or `superseded` | New version and lineage. | Reuse of closed receipt. |

Additional forbidden shortcuts:

- no-hit directly to accepted evidence;
- legacy universe label directly to membership;
- recommended profile directly to stock_profile validation;
- quotation presence directly to official status;
- reviewer authority directly overriding a blocker.

### Independent parallel governance states

| State family | Default | Candidate path | Approved terminal choices | Automatic effect from evidence lifecycle |
|---|---|---|---|---|
| Profile conflict | `unresolved` | `profile_resolution_candidate` | `resolved` or `retained_unresolved` | None. |
| Official status | `unknown` | `status_resolution_candidate` | `resolved` or `rejected` | None. |
| Universe membership | `not_approved` | `membership_candidate` | `approved` or `rejected` | None. |
| PIT admissibility | `not_assessed` | `PIT_candidate` | `approved` or `rejected` | None. |
| Replay-input eligibility | `not_eligible` | `eligibility_candidate` | `eligible` or `rejected` | None. |
| Replay execution | `not_authorized` | `authorized_run` | `executed`, `failed`, or `cancelled` | None. |

Closing evidence does not move any parallel state. Each requires its own exact approval and receipt.

## K. Current Sample-Scope Contract

The current accepted sample is design reference only:

```text
historical_decision_date = 2024-04-02
decision_timezone = Asia/Shanghai
legacy_universe_lineage = etf_core
row_count = 9
stock_row_count = 7
etf_row_count = 2
evidence_family_count = 17
row_evidence_family_contract_count = 153
```

Seven STOCK rows remain unresolved profile conflicts. Two ETF rows remain aligned context only. All nine selected rows retain blockers.

This protocol:

- assigns no real evidence to any row;
- changes no row or evidence-family status;
- approves no source or source-access operation;
- does not select the S5-WP02 source, host, evidence family, row/symbol, or date scope;
- does not create a sufficiency candidate, acceptance, closure, PIT result, replay input, or replay run.

## L. Future S5-WP02 Pilot-Envelope Template

This is an unpopulated template. It is not an approval and must not be filled with a real source in S5-WP01.

| Envelope field | Mandatory future value |
|---|---|
| `pilot_id` | Unique bounded pilot id. |
| `protocol_version` | Accepted S5-WP01 protocol version. |
| `approval_phrase` | Exact separately authorized S5-WP02 phrase. |
| `source_access_class` | One exact `SRC-*` class. |
| `source_name_or_host` | One exact reviewed source/host; no wildcard. |
| `source_id` | One stable registered source id. |
| `evidence_family_id` | One exact family unless multiple are individually enumerated. |
| `selected_row_id_or_symbol` | Exact enumerated row/symbol scope. |
| `historical_date_scope` | Exact date or closed interval. |
| `decision_timezone` | Exact timezone. |
| `maximum_records_or_documents` | Positive hard cap. |
| `permitted_network_operation` | Exact read-only method; no unspecified endpoints. |
| `reference_or_storage_policy` | Exact `RET-*` class. |
| `permitted_local_root` | Approved local root; never a protected data path unless separately authorized. |
| `reviewer_alias` | Non-identifying reviewer alias. |
| `reviewer_role_and_scope` | Exact operation/source/family/row/date scope. |
| `actor_alias` | Exact non-identifying operator alias. |
| `time_limit` | Start/end and timezone. |
| `rate_limit` | Hard request/document/time cap. |
| `permission_class` | Reviewed permission state and terms version. |
| `privacy_rule` | Data minimization, identity, path, and disclosure controls. |
| `expected_output_receipt` | Exact receipt schema and destination. |
| `stop_conditions` | Applicable Section N conditions plus source-specific conditions. |
| `explicit_prohibited_expansions` | No new source/host/family/row/date/content/storage/network/downstream scope. |

Any missing field blocks activation. `all`, wildcard, open-ended, best-effort, browse-as-needed, or equivalent scope is invalid.

## M. Audit Receipt And Versioning Contract

Every future operation produces an immutable or append-only receipt before any downstream state can rely on it.

| Receipt field | Contract |
|---|---|
| `operation_receipt_id` | Unique immutable id. |
| `protocol_version` | Exact accepted protocol version. |
| `approval_record_id` | Exact human approval record. |
| `actor_alias` | Non-identifying operation actor. |
| `reviewer_alias` | Non-identifying reviewer/decision-maker. |
| `operation_id` | One A-Z operation id. |
| `scope` | Exact source/family/row/date/network/storage/time/rate envelope. |
| `source_class` | Canonical source class. |
| `evidence_ids` | Exact record ids, possibly empty for access-only operations. |
| `previous_state` | State observed before operation. |
| `proposed_state` | Requested state. |
| `final_state` | Approved/rejected/blocked/cancelled result. |
| `decision_time` | Timestamp and timezone. |
| `reason` | Bounded rationale. |
| `blockers` | Controlled blockers retained visibly. |
| `warnings` | Controlled warnings and disposition. |
| `limitation_status` | Required limitation state. |
| `source_revision_time_references` | Safe references/previews only. |
| `superseded_receipt` | Link to prior receipt when applicable. |
| `correction_or_reopen_link` | Required for correction/reopen. |
| `downstream_authority_granted` | Exact authority; `none` unless separately approved. |
| `downstream_authority_denied` | Explicit list of boundaries that remain denied. |

Versioning rules:

1. Receipts are append-only; prior values are never silently edited.
2. Corrections create a new receipt and link the prior receipt.
3. Evidence records use new ids or explicit supersession links after material correction.
4. Protocol/schema versions are immutable references.
5. A later protocol does not retroactively broaden an earlier approval.
6. Audit receipts record authority; they do not create authority without a valid approval record.

## N. Stop Conditions

Future evidence work must stop immediately when:

1. Source permission is unknown, prohibited, expired, or inconsistent with proposed use.
2. Access requires bypass, evasion, undocumented endpoints, borrowed credentials, or private-group access.
3. The source class, source/host, operation, evidence family, row/symbol, or date differs from approval.
4. Maximum records, time limit, rate limit, network method, retention class, or local root would be exceeded.
5. Publish time or available time is missing, ambiguous, unusable, or lacks timezone.
6. Content appears after the historical decision time when decision-time use is proposed.
7. Revision id, revision time, original/revised lineage, or source identity is missing or conflicting.
8. A source conflicts with another source and conflict handling is not separately approved.
9. Reviewer authority/scope is missing, conflicted, or would override a blocker.
10. A private identity, private path, secret, credential, authentication value, personal data, source payload, or prohibited content appears.
11. Requested storage exceeds reference-only or approved retention authority.
12. Copied content exceeds approved purpose, size, copyright, or retention bounds.
13. An operation would change evidence state without the exact approval and receipt.
14. An operation would resolve profile/status/membership or PIT without a separate approval.
15. An operation would imply replay, labels, metrics, model, stock_profile, paper, buy-review, or trading authority.
16. An operation would write `data/raw`, `data/processed`, `data/cache`, `outputs`, or `docs/project_sources` without separate exact scope.
17. Another repository file, implementation change, test change, CLI command, Source update, or Master Plan change becomes necessary.
18. Privacy-safe reporting or append-only audit preservation cannot be maintained.

On stop: perform no further read/capture/state change, create only a safe bounded stop receipt if authorized, quarantine references without inspecting prohibited content, and escalate to human governance.

## O. Rejection, Dispute, Correction, Reopen, And Quarantine Policy

| Condition | Required state/action | Preservation rule | Authority boundary |
|---|---|---|---|
| Evidence fails scope, lineage, timing, permission, or quality review | `rejected` with reason and blockers. | Preserve record and decision receipt. | Rejection grants no positive authority. |
| Reviewers disagree or sources conflict | `disputed` or `unresolved_conflict`. | Preserve all positions, safe references, and limitations. | More permissive state is forbidden by default. |
| A newer source version replaces an earlier version | `superseded`; link old/new records and availability histories. | Keep original decision-time record immutable. | New version does not rewrite history. |
| Correctable metadata error | New correction receipt and versioned record. | Prior record remains visible. | No silent mutation or automatic reacceptance. |
| Closed evidence needs reconsideration | `reopened` after equal-or-higher approval. | Preserve closure and reopen rationale. | No automatic PIT/replay rollback or promotion. |
| Prohibited/private content encountered | Stop and safe quarantine metadata only. | Do not copy, inspect further, or disclose content. | Human privacy/legal escalation required. |
| Operation exceeded approval | Cancel/blocked receipt and quarantine affected output. | Preserve audit evidence without normalizing excess scope. | New approval cannot be backdated. |

Reopen authority must be independent of the actor requesting the change when the prior state was accepted or closed. Rollback means restoring downstream reliance to the last valid approved state; it never deletes the audit trail.

## P. Future Approval-Phrase Templates

Every phrase below is a non-active template. It must be instantiated with exact values, reviewed, and separately authorized. Placeholders cannot be `ALL`, wildcard, omitted, or open-ended.

### S5-WP02 bounded evidence pilot

```text
TEMPLATE_ONLY_NOT_ACTIVE: APPROVE_QUANT_S5_WP02_BOUNDED_OFFICIAL_EVIDENCE_PILOT_V0_1__SOURCE_CLASS_<SOURCE_CLASS>__SOURCE_<SOURCE_ID_OR_HOST>__FAMILY_<EVIDENCE_FAMILY_ID>__ROW_<ROW_OR_SYMBOL>__DATE_<DATE_SCOPE>__MAX_<MAX_RECORDS>__NETWORK_<READ_ONLY_OPERATION>__RETENTION_<RET_CLASS>__ROOT_<APPROVED_ROOT_ID>__REVIEWER_<REVIEWER_ALIAS>__TIME_<TIME_LIMIT>__RATE_<RATE_LIMIT>__PERMISSION_<PERMISSION_CLASS>__NO_SCOPE_EXPANSION
```

### Evidence template population

```text
TEMPLATE_ONLY_NOT_ACTIVE: APPROVE_QUANT_EVIDENCE_TEMPLATE_POPULATION_V0_1__SOURCE_<SOURCE_ID>__FAMILY_<EVIDENCE_FAMILY_ID>__ROW_<ROW_OR_SYMBOL>__DATE_<DATE_SCOPE>__TEMPLATE_<SCHEMA_VERSION>__RECORDS_<EXACT_RECORD_IDS>__PREPARER_<ACTOR_ALIAS>__REVIEWER_<REVIEWER_ALIAS>__NO_STATE_PROMOTION
```

### Sufficiency-candidate assignment

```text
TEMPLATE_ONLY_NOT_ACTIVE: APPROVE_QUANT_EVIDENCE_SUFFICIENCY_CANDIDATE_ASSIGNMENT_V0_1__SOURCE_<SOURCE_ID>__FAMILY_<EVIDENCE_FAMILY_ID>__ROW_<ROW_OR_SYMBOL>__DATE_<DATE_SCOPE>__RECORDS_<EXACT_RECORD_IDS>__REVIEWERS_<REVIEWER_ALIASES>__LIMITATIONS_<LIMITATION_STATUS>__NO_ACCEPTANCE_OR_PIT
```

### Evidence acceptance

```text
TEMPLATE_ONLY_NOT_ACTIVE: APPROVE_QUANT_EVIDENCE_ACCEPTANCE_V0_1__SOURCE_<SOURCE_ID>__FAMILY_<EVIDENCE_FAMILY_ID>__ROW_<ROW_OR_SYMBOL>__DATE_<DATE_SCOPE>__RECORDS_<EXACT_RECORD_IDS>__CANDIDATE_RECEIPT_<RECEIPT_ID>__DUAL_REVIEW_<REVIEWER_ALIASES>__NO_CLOSURE_OR_PIT
```

### Evidence closure

```text
TEMPLATE_ONLY_NOT_ACTIVE: APPROVE_QUANT_EVIDENCE_CLOSURE_V0_1__SOURCE_<SOURCE_ID>__FAMILY_<EVIDENCE_FAMILY_ID>__ROW_<ROW_OR_SYMBOL>__DATE_<DATE_SCOPE>__ACCEPTANCE_RECEIPTS_<RECEIPT_IDS>__CLOSURE_CRITERIA_<VERSION>__DUAL_REVIEW_<REVIEWER_ALIASES>__NO_PIT_OR_REPLAY
```

### Profile, status, or membership resolution

```text
TEMPLATE_ONLY_NOT_ACTIVE: APPROVE_QUANT_PROFILE_STATUS_MEMBERSHIP_RESOLUTION_V0_1__RESOLUTION_TYPE_<PROFILE_OR_STATUS_OR_MEMBERSHIP>__SOURCE_<SOURCE_ID>__FAMILY_<EVIDENCE_FAMILY_ID>__ROW_<ROW_OR_SYMBOL>__DATE_<DATE_SCOPE>__CLOSED_EVIDENCE_<RECORD_IDS>__DUAL_REVIEW_<REVIEWER_ALIASES>__NO_PIT_OR_REPLAY
```

### PIT admissibility

```text
TEMPLATE_ONLY_NOT_ACTIVE: APPROVE_QUANT_PIT_ADMISSIBILITY_V0_1__SOURCE_<SOURCE_ID>__FAMILY_<EVIDENCE_FAMILY_ID>__ROW_<ROW_OR_SYMBOL>__DATE_<DATE_SCOPE>__DECISION_TIME_<TIMESTAMP_AND_TIMEZONE>__CLOSED_EVIDENCE_<RECORD_IDS>__TIMING_REVISION_RECEIPTS_<RECEIPT_IDS>__PIT_REVIEWER_<REVIEWER_ALIAS>__NO_REPLAY_EXECUTION
```

### Replay-input promotion

```text
TEMPLATE_ONLY_NOT_ACTIVE: APPROVE_QUANT_REPLAY_INPUT_PROMOTION_V0_1__SOURCE_<SOURCE_ID>__FAMILY_<EVIDENCE_FAMILY_ID>__ROW_<ROW_OR_SYMBOL>__DATE_<DATE_SCOPE>__PIT_RECEIPTS_<RECEIPT_IDS>__PACKAGE_<PACKAGE_ID_AND_VERSION>__REVIEWERS_<REVIEWER_ALIASES>__NO_REPLAY_EXECUTION_LABELS_TRAINING_OR_TRADING
```

No template grants access or state change by appearing in this report. Each future approval must name exact scope, actor, reviewer, prerequisites, receipt, stop conditions, and denied downstream authority.

## Q. Privacy, Security, Permission, And Disclosure Review

Protocol requirements:

- use aliases and roles, not private identities;
- keep identity mappings and authentication material outside Git, Project Source, reports, and receipts;
- record permission and legality separately from public access and source rank;
- prohibit bypass, evasion, borrowed access, private-group material, non-public/insider information, and rate-limit circumvention;
- expose safe references and hash previews only;
- keep full private source hashes, private absolute paths, source content, source bytes, excerpts, and personal data out of Project Source;
- keep real evidence packages, filled templates, and collected content out of this repository;
- stop on private/prohibited content without further inspection;
- treat Git commit ids used for repository audit as governance identifiers, not private source hashes.

This report selects no real source, host, URL, file, evidence record, reviewer identity, or private path. It contains no real evidence content or excerpt. Every real operation remains `NOT_AUTHORIZED`.

Direct candidate-report checks after creation found:

- 21 required Sections A-U;
- all seven canonical source classes;
- all 26 A-Z operation rows, with exactly 26 `NOT_AUTHORIZED` permissions;
- all 65 required capture-field names checked by the local audit;
- all eight required future approval templates;
- zero trailing-whitespace or unfinished-marker matches;
- zero real URL, private Windows path, email-address, 64-character private-hash, sensitive-assignment, unsafe affirmative-operation, or active broad-approval matches.

Final repository checks found:

- `HEAD == origin/main == 8792dbc66349a2f76139d9e0885d7182bacaf859`;
- describe and tag at HEAD remained `v1.90.0`;
- `git diff --name-status` and `git diff --stat` were empty;
- final `git diff --check` passed;
- status contained exactly this one untracked report;
- tracked/status scans for `docs/project_sources` were empty;
- protected tracked inventory remained `data/processed/.gitkeep`, `data/raw/.gitkeep`, and `outputs/reports/.gitkeep`;
- no tests or CLI smoke were run.

## R. Prompt Accounting And Change-Control Note

```text
baseline_version = V1.0
work_package = S5-WP01
planned_prompts = 4
conditional_risk_reserve = 1
this_goal_prompt_delta = 1
expected_actual_prompts_consumed_after_activation = 1
expected_remaining_baseline_prompts = 127
expected_S5_WP01_remaining_base_prompts = 3
```

This report records the local accounting expectation only. It does not update external Project Source, the canonical Master Plan, or its formal burn-down. Reconciliation occurs only at the next approved checkpoint, burn-down update, change request, or required recalculation event.

Any implementation, S5-WP02 pilot, additional design hardening, or unplanned approval work consumes a separately authorized prompt and must follow change control. The conditional risk reserve is not automatic scope.

## S. Candidate Next Routes

| Route | Decision | Reason |
|---|---|---|
| A. Manual S5-WP01 Design Artifact Review And Commit Decision | selected | The report covers every required protocol surface, preserves privacy and semantic separation, and authorizes no real operation. |
| B. S5-WP01 Design Hardening Report-Only v0.1 | not selected | No bounded defect is known after direct report checks. |
| C. Pause And Investigate A Concrete Privacy, Permission, Or Semantic Defect | not selected | No concrete unresolved defect was found. |
| D. S5-WP02 Bounded Official Evidence Collection Pilot | prohibited now | S5-WP02 requires report acceptance, commit, and a separate exact approval with a populated bounded envelope. |

Exactly one route is selected. It is not executed in this Goal.

## T. Selected Next Route

`Manual S5-WP01 Design Artifact Review And Commit Decision`

Human review must determine whether the candidate acceptance artifact becomes accepted and may be committed. This selection does not authorize S5-WP02, evidence access, collection, or any state transition.

## U. Final Classification And Verdict

Final classification:

`S5_WP01_EVIDENCE_OPERATIONS_PROTOCOL_AND_APPROVAL_MATRIX_DESIGN_CREATED_REPORT_ONLY`

Final verdict:

`S5_WP01_READY_FOR_HUMAN_REVIEW_AND_COMMIT_DECISION_NO_REAL_EVIDENCE`

Recommended commit message after human acceptance:

`docs: design S5-WP01 evidence operations protocol and approval matrix`

Recommendations:

- tag: no tag;
- Source update: no Source update;
- S5-WP02: not authorized;
- next action mode: ChatGPT/user manual review and commit decision;
- Codex execution: none unless separately authorized.

The acceptance artifact remains `CANDIDATE_PENDING_HUMAN_REVIEW`. No real source or evidence operation, protected write, downstream research promotion, buy-review action, or trading behavior occurred.
