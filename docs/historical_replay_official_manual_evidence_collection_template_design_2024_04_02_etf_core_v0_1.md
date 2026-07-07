# Historical Replay Official Manual Evidence Collection Template Design for 2024-04-02 / etf_core v0.1

## A. Decision / Status

phase = historical_replay_official_manual_evidence_collection_template_design_2024_04_02_etf_core
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
current_checkpoint = v1.86.0
current_checkpoint_commit = 69f98eb
current_checkpoint_tag = v1.86.0
current_repo_head = 30ee59f
external_project_source_version = v1.86.0_user_reported
manual_evidence_collection_template_design_created = yes
official_evidence_collection_started = no
selected_next_route = Historical Replay Official Manual Evidence Collection Template Contract / Fixture Report-Only v0.1

official_source_hierarchy_approved = no
official_evidence_collection_approved = no
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

This document is a docs-only template design for a future human-fillable official manual evidence collection template. It translates the v1.86.0 official source hierarchy worklist contract into template requirements. It does not create template CSV files, filled evidence templates, source files, accepted evidence packets, evidence closure, point-in-time approval, replay input, replay execution, buy-review permission, or trading permission.

## B. Current accepted state

The current accepted checkpoint is `v1.86.0` at commit `69f98eb`, tagged `v1.86.0`. The repository head for this design task is `30ee59f`, which hardened the official source hierarchy worklist recommended next action wording.

User-reported external ChatGPT Project Source is updated to `v1.86.0`. This document does not create, inspect, or update repository `docs/project_sources` or any Project Source package.

Accepted selected-sample count contract:

| Field | Value |
| --- | ---: |
| row_count | 9 |
| stock_row_count | 7 |
| etf_row_count | 2 |
| source_class_count | 7 |
| evidence_family_count | 9 |
| evidence_collection_worklist_row_count | 72 |
| no_hit_handoff_row_count | 9 |
| blocked_count | 72 |
| profile_conflict_count | 7 |
| survivorship_warning_count | 9 |
| safety_true_count | 0 |

The current live recommended next task after hardening is:

`Historical Replay Official Manual Evidence Collection Template Design Report-Only v0.1`

## C. Selected sample and row identity

The future template contract must preserve the exact selected sample:

| Field | Required value |
| --- | --- |
| `historical_decision_date` | `2024-04-02` |
| `universe_name` | `etf_core` |
| `selected_sample_context_only` | `yes` |

The selected symbols must remain strings, with leading zeros preserved:

| Symbol | Instrument type | Legacy universe label | Recommended profile | Profile conflict |
| --- | --- | --- | --- | --- |
| `000001` | STOCK | `etf_core` | `stock_core` | yes |
| `000002` | STOCK | `etf_core` | `stock_core` | yes |
| `159915` | ETF | `etf_core` | `etf_core` | no |
| `300750` | STOCK | `etf_core` | `stock_core` | yes |
| `510300` | ETF | `etf_core` | `etf_core` | no |
| `600000` | STOCK | `etf_core` | `stock_core` | yes |
| `600519` | STOCK | `etf_core` | `stock_core` | yes |
| `601318` | STOCK | `etf_core` | `stock_core` | yes |
| `688981` | STOCK | `etf_core` | `stock_core` | yes |

Universe membership cannot be inferred from the legacy `etf_core` label alone. STOCK rows under legacy `etf_core` remain profile-conflict review context until a separately approved policy resolves that conflict.

## D. Purpose of manual evidence collection templates

The future manual evidence collection templates should make human collection work structured and auditable. They should help a reviewer fill source lineage, evidence observation, no-hit handoff, survivorship rationale, and reviewer limitation fields for the selected sample.

The templates are not evidence collection by themselves. A blank template row is not point-in-time approval. `row_ready_for_manual_fill_not_pit_approved` is not point-in-time admissible. A filled row would still require separate review, validation, and approval before any downstream workflow could consume it.

## E. Template artifact family design

Future template artifact names, not created by this task:

| Future template artifact | Purpose | Created now |
| --- | --- | --- |
| `official_evidence_collection_template.csv` | Human-fill row/evidence-family template for the 72 expected collection rows. | no |
| `official_source_lineage_template.csv` | Source identity, permission, hash-preview, revision, available-time, quality, and limitation fields. | no |
| `official_no_hit_query_handoff_template.csv` | No-hit query windows, query terms, reviewer handoff, and no-hit limitation fields. | no |
| `official_survivorship_rationale_template.csv` | Survivorship warning, source-backed rationale, revision, timing, and review status fields. | no |
| `official_reviewer_notes_template.csv` | Reviewer alias, role, scope, attestation, limitation note, and privacy flags. | no |
| `official_template_validation_checklist.md` | Human-readable validation checklist for later template implementation. | no |

The future template fixture should create empty or synthetic report-only templates only after a separate implementation task approves that scope. It must not include collected official evidence, copied official source contents, source bytes, full hashes, private local paths, or private reviewer identities.

## F. Row/evidence-family template fields

Required row identity fields:

| Field | Required value or rule |
| --- | --- |
| `template_row_id` | Deterministic id joining date, universe, symbol, and evidence family. |
| `historical_decision_date` | `2024-04-02`. |
| `universe_name` | `etf_core`. |
| `symbol` | Required string; leading zeros preserved. |
| `instrument_type` | `STOCK` or `ETF`. |
| `legacy_universe_label` | `etf_core`. |
| `recommended_profile` | `stock_core` for STOCK rows, `etf_core` for ETF rows. |
| `profile_conflict` | `yes` for STOCK rows under this legacy label, `no` for ETF rows. |
| `evidence_family` | Controlled evidence family name. |
| `template_status` | Controlled status from this report's vocabulary. |
| `blocker_reason` | Semicolon-separated controlled blocker ids while incomplete. |
| `limitation_note` | Required for any missing, warning, no-hit, partial, or not-applicable context. |

Required evidence fields:

| Field | Requirement |
| --- | --- |
| `evidence_collection_status` | Controlled value; default `evidence_collection_required`. |
| `evidence_observation_value` | Human-filled observation or `missing`. |
| `evidence_observation_scope` | Scope such as symbol-level, instrument-level, ETF-policy-level, source-family-level. |
| `evidence_observation_date` | Observation date when applicable; cannot replace available time. |
| `evidence_publication_time` | Source publication timestamp when available. |
| `evidence_available_time` | Required decision-time availability timestamp or blocker. |
| `evidence_available_time_timezone` | Required timezone or reviewed default policy. |
| `evidence_raw_reference` | Stable reference to source record, not copied source content. |
| `evidence_revision_id` | Source revision, announcement id, publication id, file revision, or package version. |
| `evidence_limitation_note` | Required for partial, no-hit, inferred, or not-applicable context. |

Expected evidence families:

| Evidence family | Required for |
| --- | --- |
| `listed_active_status` | STOCK and ETF |
| `delisted_not_delisted_status` | STOCK and ETF |
| `st_no_st_status` | STOCK only |
| `etf_st_not_applicable_policy` | ETF only |
| `suspension_trading_status` | STOCK and ETF |
| `universe_membership` | STOCK and ETF |
| `source_lineage` | all source-family rows |
| `reviewer_no_hit_handoff` | all selected symbols until resolved |
| `survivorship_rationale` | all selected symbols |

## G. Source lineage template fields

Required source lineage fields:

| Field | Requirement |
| --- | --- |
| `source_id` | Required controlled id or blocker. |
| `source_name` | Human-readable source name without credentials or secrets. |
| `source_type` | Controlled source type. |
| `source_class` | One of the seven source classes from v1.86.0. |
| `permission_class` | Required permission context; source name alone is not permission. |
| `raw_reference_type` | Page, file, announcement, filing, archive snapshot, reviewed metadata row, or no-hit log. |
| `raw_reference` | Stable source reference; no copied copyrighted content or private source bytes. |
| `source_hash_preview` | Optional preview only; never a full hash in user-facing surfaces. |
| `source_hash_disclosure_policy` | Required when a hash preview is present or intentionally hidden. |
| `local_file_hash_preview` | Optional local reviewed file preview; not point-in-time evidence by itself. |
| `local_file_hash_disclosure_policy` | Required when a local file hash preview is present or hidden. |
| `revision_id` | Required revision id, announcement id, publication id, effective date, file revision, or package version. |
| `revision_id_type` | Controlled meaning of `revision_id`. |
| `available_time` | Required decision-time availability timestamp or blocker. |
| `available_time_timezone` | Required timezone or reviewed default policy. |
| `available_time_policy` | Required rule explaining why availability is decision-time valid. |
| `quality_status` | Controlled quality state. |
| `limitation_note` | Required while incomplete, partial, warning, inferred, local-only, or no-hit. |

Source hierarchy source classes:

| Source class | Primary purpose |
| --- | --- |
| exchange official listing and trading-status source | listed, delisted, suspension, and trading-status context |
| exchange disclosure or issuer announcement source | ST/no-ST, delisting, suspension, issuer notice context |
| official quotation or trading-status publication source | supporting same-day quote/trading context |
| index or provider membership source | universe membership context |
| ETF issuer or fund company disclosure source | ETF-specific status and policy context |
| reviewed local manual evidence metadata source | local reviewed metadata packaging, not official authority |
| reviewer no-hit query log source | searched-source handoff, not reliability scoring |

## H. STOCK-specific template rules

STOCK rows: `000001`, `000002`, `300750`, `600000`, `600519`, `601318`, `688981`.

Rules:

1. STOCK rows require `st_no_st_status`.
2. STOCK rows require listed, delisted/not-delisted, suspension/trading, universe membership, source lineage, no-hit handoff, and survivorship rationale fields.
3. STOCK rows keep `profile_conflict = yes` under legacy `etf_core`.
4. `blocker_profile_conflict_unreviewed` remains until separately resolved.
5. Same-day quotation presence is not official status proof by itself.
6. ST/no-ST status must not be inferred from quotation alone.
7. A reviewer note cannot override missing source id, raw reference, permission, revision, available time, quality, or limitation fields.

Required STOCK blockers while incomplete:

| Blocker | Applies when |
| --- | --- |
| `blocker_missing_stock_st_source` | ST/no-ST source is missing. |
| `blocker_profile_conflict_unreviewed` | STOCK row remains under legacy `etf_core`. |
| `blocker_missing_survivorship_rationale` | survivorship rationale source and note are missing. |

## I. ETF-specific template rules

ETF rows: `159915`, `510300`.

Rules:

1. ETF rows require `etf_st_not_applicable_policy`.
2. ETF rows still require listed, delisted/not-delisted, suspension/trading, universe membership, source lineage, no-hit handoff, and survivorship rationale fields.
3. ETF rows keep `profile_conflict = no`.
4. ETF rows should not be forced into stock ST/no-ST evidence.
5. ETF ST not-applicable policy is required if stock ST evidence does not apply.
6. ETF ST not-applicable policy does not skip ETF status review.
7. ETF status evidence should prefer exchange ETF status or ETF issuer/fund company disclosure where possible.

Required ETF blocker while incomplete:

| Blocker | Applies when |
| --- | --- |
| `blocker_missing_etf_st_not_applicable_policy` | ETF not-applicable policy is missing. |

## J. No-hit handoff template rules

The current v1.86.0 worklist has `no_hit_handoff_row_count = 9`. No no-hit context is accepted by default.

Required no-hit fields:

| Field | Requirement |
| --- | --- |
| `no_hit_review_needed` | Required; default `yes`. |
| `no_hit_source_family` | Required source or evidence family searched. |
| `no_hit_query_window_start` | Required before any no-hit context can be reviewed. |
| `no_hit_query_window_end` | Required before any no-hit context can be reviewed. |
| `no_hit_query_terms` | Required query terms or reviewed query description. |
| `no_hit_result` | Controlled result: missing, found, conflicting, inconclusive. |
| `no_hit_acceptance_status` | Required; default `not_accepted`. |
| `no_hit_reviewer_required` | Required; default `yes`. |
| `reviewer_id_or_alias` | Required before accepted reviewer context; no private identity. |
| `reviewer_role` | Required before accepted reviewer context. |
| `reviewer_scope` | Required before accepted reviewer context. |
| `no_hit_acceptance_rationale` | Required for any later accepted context. |
| `no_hit_limitation_note` | Required for every no-hit row. |

No-hit query required is not source reliability scoring. No-hit context cannot override source, permission, revision, available-time, quality, survivorship, or profile-conflict blockers.

## K. Survivorship rationale template rules

All nine rows carry survivorship warning context. Required survivorship fields:

| Field | Requirement |
| --- | --- |
| `survivorship_warning_flag` | Required; default `yes`. |
| `survivorship_source_id` | Required source id or blocker. |
| `survivorship_raw_reference` | Required source reference or blocker. |
| `survivorship_revision_id` | Required revision id or blocker. |
| `survivorship_available_time` | Required decision-time availability or blocker. |
| `survivorship_rationale` | Required reviewer-visible rationale. |
| `survivorship_review_status` | Required controlled review status. |
| `survivorship_limitation_note` | Required while partial, missing, or no-hit. |

Survivorship rationale cannot be inferred from later symbol availability, current listing status, later universe files, same-day quotation presence, or no-hit context alone.

## L. Reviewer/privacy/disclosure policy

Reviewer fields should support accountability without collecting private identity.

Required reviewer fields:

| Field | Requirement |
| --- | --- |
| `reviewer_id_or_alias` | Alias or stable reviewer id; no private legal identity required. |
| `reviewer_role` | Controlled reviewer role. |
| `reviewer_scope` | What the reviewer is allowed to review. |
| `reviewed_at` | Review timestamp; cannot replace source available time. |
| `reviewer_attestation_status` | Controlled status such as missing, attested, rejected, scope-limited. |
| `reviewer_limitation_note` | Required for partial, inferred, no-hit, or scope-limited review. |
| `reviewer_private_identity_disclosed` | Required and default `no`. |

Privacy and disclosure rules:

1. No secrets, credentials, auth files, tokens, or private reviewer identity.
2. No full source hashes in user-facing surfaces; use previews and disclosure-policy fields.
3. No copied copyrighted source contents.
4. No raw official source bytes.
5. No private local paths in committed docs.
6. No filled manual evidence files committed to the repository.

## M. Status vocabulary

Allowed template status vocabulary:

| Status | Meaning |
| --- | --- |
| `template_row_created_report_only` | Template row exists as report-only structure. |
| `evidence_collection_required` | Official evidence still needs manual collection. |
| `manual_review_required` | Human review is required before any context can be accepted. |
| `no_hit_query_required` | No-hit query fields must be filled or reviewed. |
| `source_lineage_required` | Source id, permission, raw reference, revision, and timing are incomplete. |
| `survivorship_rationale_required` | Survivorship rationale remains missing. |
| `context_only_not_evidence` | Row has context only, not accepted evidence. |
| `blocked` | One or more blockers remain. |
| `row_ready_for_manual_fill_not_pit_approved` | Row can be manually filled, but is not point-in-time approval. |

No status may imply evidence closure, source approval, point-in-time admissibility, replay readiness, buy-review readiness, performance validation, or trading permission.

## N. Blocker vocabulary

Allowed blocker vocabulary:

| Blocker | Meaning |
| --- | --- |
| `blocker_missing_source_id` | Source id is missing. |
| `blocker_missing_raw_reference` | Raw reference is missing. |
| `blocker_missing_permission_class` | Permission class is missing. |
| `blocker_missing_revision_id` | Revision id is missing. |
| `blocker_missing_available_time` | Available time is missing. |
| `blocker_available_time_after_decision` | Available time is after `2024-04-02` decision boundary. |
| `blocker_missing_timezone_policy` | Timezone policy is missing. |
| `blocker_missing_quality_status` | Quality status is missing. |
| `blocker_missing_limitation_note` | Required limitation note is missing. |
| `blocker_missing_no_hit_query_window` | No-hit query window is missing. |
| `blocker_missing_survivorship_rationale` | Survivorship rationale is missing. |
| `blocker_missing_stock_st_source` | STOCK ST/no-ST source is missing. |
| `blocker_missing_etf_st_not_applicable_policy` | ETF not-applicable policy is missing. |
| `blocker_profile_conflict_unreviewed` | Mixed STOCK/ETF profile conflict is unresolved. |
| `blocker_forbidden_downstream_flag` | A forbidden downstream field is true. |

Future implementation may add stricter blockers only if it remains report-only and tests prove no approval semantics are introduced.

## O. Future validation rules

Future template implementation should validate:

1. Exactly nine selected symbols are present.
2. Symbols are strings and leading zeros are preserved.
3. `historical_decision_date` equals `2024-04-02`.
4. `universe_name` equals `etf_core`.
5. Seven STOCK rows and two ETF rows are present.
6. STOCK rows include `st_no_st_status`.
7. ETF rows include `etf_st_not_applicable_policy`.
8. STOCK rows remain `profile_conflict = yes`.
9. ETF rows remain `profile_conflict = no`.
10. Required source lineage fields exist for every source-family row.
11. Missing source id, raw reference, permission, revision id, available time, timezone policy, quality status, or limitation note creates blockers.
12. Available time after the decision date creates `blocker_available_time_after_decision`.
13. No-hit rows default to `not_accepted`.
14. No-hit rows require query windows before review.
15. Survivorship rationale fields exist for every selected symbol.
16. Warning or partial status requires limitation note.
17. Full hashes, private paths, source bytes, and copied source contents are absent from committed template outputs.
18. Any forbidden downstream safety field set true creates `blocker_forbidden_downstream_flag`.
19. Forward returns remain future information and must not appear in decision-time template rows.
20. The 8-layer factor taxonomy remains the primary structure; fixed 12 factors are not final.

## P. Future focused test plan

Future focused tests for a template contract/fixture implementation should cover:

| Test area | Expected assertion |
| --- | --- |
| row identity | exact nine symbols, string type, leading zeros preserved |
| STOCK/ETF split | seven STOCK rows and two ETF rows |
| evidence families | expected family rows per instrument type |
| source lineage fields | required fields are present and missing values block |
| no-hit handoff | nine no-hit rows default to not accepted |
| survivorship rationale | nine survivorship rows require rationale |
| privacy | no private reviewer identity, no secrets, no full hashes, no raw source bytes |
| status vocabulary | no status implies evidence closure or replay readiness |
| blocker vocabulary | required blockers are visible and controlled |
| safety flags | all downstream approval, buy-review, trading, and data-write fields remain false |
| output boundary | writes only future approved report-only template artifacts |

Suggested later test commands, not run in this docs-only task:

```text
.venv\Scripts\python.exe -m pytest tests/test_historical_replay_official_manual_evidence_collection_template_fixture.py -q
.venv\Scripts\python.exe -m pytest tests/test_historical_replay_official_manual_evidence_collection_template_fixture_views.py -q
```

## Q. Future temp-root smoke plan

Future implementation temp-root smoke should:

1. Create a repository-external temp root.
2. Run the future template fixture command against that temp root only.
3. Confirm future template artifacts are empty or synthetic report-only templates.
4. Confirm no official evidence is collected or accepted.
5. Confirm row counts remain `9 / 7 / 2`.
6. Confirm evidence-family/template rows preserve the `72` worklist-row expectation or a documented template-row equivalent.
7. Confirm no-hit rows remain not accepted.
8. Confirm survivorship rationale remains required.
9. Confirm safety true count remains `0`.
10. Confirm no `data/raw`, `data/processed`, or `data/cache` writes.
11. Confirm no filled evidence template files are written to the repository.
12. Confirm the recommended next task points to the next same-boundary report-only step.

No CLI smoke is run in this docs-only design task.

## R. Safety and non-approval boundary

Template design is not evidence collection. Template design is not evidence acceptance. A blank template row is not point-in-time approval. `row_ready_for_manual_fill_not_pit_approved` is not point-in-time admissible.

This design does not:

- collect official evidence;
- fetch official sources;
- read websites or call APIs;
- copy official source content;
- create accepted evidence packets;
- close official evidence;
- close point-in-time evidence;
- approve point-in-time admissibility;
- create replay input;
- run replay;
- freeze replay decisions;
- create forward labels;
- compute metrics;
- train models;
- adjust formulas, weights, thresholds, or model parameters;
- validate stock profile;
- expand paper workflow authority;
- approve real buy-review;
- allow buy-review;
- authorize trading;
- call brokers, place orders, send messages, or call external API or LLM systems;
- run current-candidates;
- build snapshots;
- mutate signal semantics;
- write protected data directories.

## S. What must remain outside repo

The following must remain outside the repository unless a later exact task separately approves a safe path:

- filled manual evidence templates;
- collected official evidence;
- source PDFs, web pages, downloaded files, or copied source contents;
- raw official source bytes;
- full source hashes;
- private local paths;
- private reviewer identities;
- credentials, tokens, auth files, or `.env` files;
- manual diagnostics generated from real evidence collection;
- raw evidence payloads;
- files under `data/raw`, `data/processed`, or `data/cache`.

## T. Candidate next routes

| Route | Decision | Reason |
| --- | --- | --- |
| A. Historical Replay Official Manual Evidence Collection Template Contract / Fixture Report-Only v0.1 | selected | The design is coherent, report-only, and ready to become a deterministic empty/synthetic template contract fixture. |
| B. Historical Replay Reviewer No-Hit Acceptance Planning for 2024-04-02 etf_core Report-Only v0.1 | reserved | No-hit policy matters, but the template contract should first define no-hit fields and blockers. |
| C. Historical Replay Mixed STOCK/ETF Universe Profile Policy Planning for legacy etf_core Report-Only v0.1 | reserved | Profile conflict matters, but the template contract can preserve conflict fields without resolving policy. |
| D. Pause repo work and manually collect official source/status evidence outside the repo | not selected | Manual collection is premature before a structured template contract exists. |
| E. Historical Replay Official Manual Evidence Collection Template Design Hardening Report-Only v0.1 | not selected | No design ambiguity requires a hardening-only follow-up. |

## U. Selected next route

Selected next route:

`Historical Replay Official Manual Evidence Collection Template Contract / Fixture Report-Only v0.1`

## V. Why selected route is safe

The selected route is safe because it can remain a deterministic report-only contract fixture. It can create empty or synthetic template artifacts and focused tests without collecting evidence, validating official source content, closing blockers, approving point-in-time admissibility, creating replay input, or authorizing downstream workflows.

It is smaller and safer than no-hit acceptance, mixed-universe policy resolution, manual evidence collection, evidence closure, or point-in-time approval.

## W. What must not be bundled

The selected next route must not bundle:

- official evidence collection;
- source fetching;
- source content reads;
- official evidence acceptance;
- official evidence closure;
- point-in-time evidence closure;
- point-in-time approval;
- active replay input;
- replay execution;
- replay decision freeze;
- forward label creation;
- metric computation;
- training/model work;
- stock profile validation;
- paper expansion;
- real buy-review;
- trading;
- current-candidates;
- snapshots;
- signal semantics mutation;
- broker/API/order/message behavior;
- protected data writes;
- checkpoint docs;
- Project Source files;
- Source update notes.

## X. ChatGPT/Codex mode recommendation

Codex high is sufficient for the selected template contract/fixture task if it stays deterministic, empty or synthetic, report-only, and local-only.

Use ChatGPT Pro or Pro Extended before any task introduces official evidence collection, source authority adjudication, no-hit sufficiency, ETF not-applicable authority, mixed-universe production policy, source reliability scoring, point-in-time approval, replay input readiness, replay execution, labels, metrics, model work, stock profile validation, paper expansion, buy-review, performance validation, broker integration, order placement, message delivery, external API or LLM calls, or trading authority.

## Y. Commit/tag/Source recommendation

Recommended commit message if ready:

```text
docs: design official manual evidence collection template
```

Recommended tag decision: no tag for this template design.

Recommended Source update decision: no Source update for this template design.

## Z. Recommended next task

Historical Replay Official Manual Evidence Collection Template Contract / Fixture Report-Only v0.1

Expected final classification:

`HISTORICAL_REPLAY_OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_DESIGN_CREATED_REPORT_ONLY`

Expected final verdict:

`HISTORICAL_REPLAY_OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_DESIGN_READY_FOR_TEMPLATE_CONTRACT_FIXTURE_REPORT_ONLY`
