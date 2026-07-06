# Historical Replay Official Status Evidence Packet Closure Worklist Design for 2024-04-02 / etf_core v0.1

phase = historical_replay_official_status_evidence_packet_closure_worklist_design_selected_sample
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_checkpoint = v1.84.0
latest_checkpoint_commit = 94775cf
latest_repo_commit = eb651b2
selected_historical_decision_date = 2024-04-02
selected_universe = etf_core
official_status_evidence_packet_worklist_design_created = yes
selected_next_route = Historical Replay Official Status Evidence Packet Closure Worklist Core Report-Only v0.1

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

This docs-only worklist design is ready. It defines the selected-sample official status evidence packet closure worklist for `2024-04-02 / etf_core` before any implementation, data fetch, packet creation, evidence closure, PIT approval, replay, labels, metrics, training, model work, stock-profile validation, paper expansion, buy-review, or trading workflow.

The selected next route is:

`Historical Replay Official Status Evidence Packet Closure Worklist Core Report-Only v0.1`

The selected route is implementation of a report-only core scaffold with all rows blocked or review-needed by default. It is not evidence closure and is not row approval.

## B. Current Accepted State

The current accepted checkpoint is `v1.84.0` at commit `94775cf`. The latest repository commit for this design is `eb651b2`, which added the official status evidence packet closure planning report. External ChatGPT Project Source is updated to v1.84.0 and is not mirrored into the repository.

Historical Replay Training Loop remains the active mainline. Personal MVP advisory refresh remains paused, not abandoned.

The accepted generated artifact review for the selected sample recorded:

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

Existing official status packet, enrichment, reviewer no-hit, and checklist-validator docs are useful context only. They do not close the selected sample evidence gaps.

## C. Selected Sample Row Set

Every future row artifact must preserve symbols as strings, including leading-zero symbols.

| Symbol | Instrument type | Recommended profile | Profile conflict | Required row treatment |
| --- | --- | --- | --- | --- |
| `000001` | STOCK | `stock_core` | true | Stock row under legacy `etf_core`; keep profile conflict visible. |
| `000002` | STOCK | `stock_core` | true | Stock row under legacy `etf_core`; keep profile conflict visible. |
| `159915` | ETF | `etf_core` | false | ETF row; require ETF-specific status and membership evidence. |
| `300750` | STOCK | `stock_core` | true | Stock row under legacy `etf_core`; keep profile conflict visible. |
| `510300` | ETF | `etf_core` | false | ETF row; require ETF-specific status and membership evidence. |
| `600000` | STOCK | `stock_core` | true | Stock row under legacy `etf_core`; keep profile conflict visible. |
| `600519` | STOCK | `stock_core` | true | Stock row under legacy `etf_core`; keep profile conflict visible. |
| `601318` | STOCK | `stock_core` | true | Stock row under legacy `etf_core`; keep profile conflict visible. |
| `688981` | STOCK | `stock_core` | true | Stock row under legacy `etf_core`; keep profile conflict visible. |

The legacy universe label remains `etf_core` for all rows. The recommended profile remains row-specific.

## D. Design Purpose and Boundary

This design defines a future selected-sample worklist contract for official status evidence packet closure. It defines row identity fields, evidence-family fields, reviewer no-hit handoff fields, closure statuses, blocker statuses, validation rules, future report-only artifact files, and required non-approval safety fields.

This design does not implement the worklist, create evidence packets, close official evidence, close PIT evidence, approve PIT admissibility, create active replay input, execute replay, freeze replay decisions, create labels, compute metrics, train models, adjust weights, alter thresholds, create stock-profile validation, expand paper authority, approve real buy-review, or authorize trading.

The 8-layer factor taxonomy remains the primary structure. Fixed 12 factors are not final. Forward returns remain future information.

## E. Row Identity and Profile Schema

Future row-level artifacts should include these identity fields:

| Field | Requirement | Validation behavior |
| --- | --- | --- |
| packet_worklist_id | Required stable worklist id. | Block if missing. |
| signal_date | Required; must equal `2024-04-02` for this selected sample. | Block if missing or mismatched. |
| universe_name | Required; must equal selected universe label. | Block if missing. |
| symbol | Required string. | Block if missing; preserve leading zeros. |
| instrument_type | Required controlled value: `STOCK` or `ETF`. | Block if missing or unknown. |
| exchange_or_market | Required if known; otherwise visible missing context. | Warn or block depending on future core policy. |
| legacy_universe_label | Required; preserve `etf_core`. | Block if missing. |
| recommended_profile | Required row-level profile guidance. | Block if missing. |
| profile_conflict_flag | Required boolean. | Block if missing. |
| profile_conflict_reason | Required when conflict flag is true. | Block if missing for STOCK rows in this legacy sample. |
| profile_policy_status | Required controlled status. | Block if unreviewed when profile conflict exists. |

STOCK rows under the legacy `etf_core` label remain profile-conflict review context until a separate policy resolves them.

## F. Listed / Active Status Schema

Listed or active status confirms that the row had an official or accepted public listing/active context at the decision date. It does not prove not-delisted status, ST/no-ST status, suspension status, universe membership, survivorship, or replay readiness.

Required fields:

| Field | Requirement |
| --- | --- |
| listed_status_evidence | Required evidence category or text reference. |
| listed_status_source_id | Required source registry or planned source id. |
| listed_status_source_name | Required human-readable source name. |
| listed_status_source_type | Required controlled source type. |
| listed_status_raw_reference | Required raw document/table/file/page/query reference. |
| listed_status_revision_id | Required source revision or snapshot id. |
| listed_status_available_time | Required decision-time availability timestamp. |
| listed_status_review_status | Required review status. |
| listed_status_limitation_note | Required when evidence is partial, inferred, or source-family limited. |

Missing listed/active status evidence maps to `blocker_missing_listed_status_evidence`.

## G. Delisted / Not-Delisted Status Schema

Delisted/not-delisted evidence reduces survivorship leakage risk. The future worklist must distinguish explicit official not-delisted context from reviewed no-hit support.

Required fields:

| Field | Requirement |
| --- | --- |
| delisted_status_evidence | Required explicit status evidence or no-hit context marker. |
| delisted_status_source_id | Required source id. |
| delisted_status_raw_reference | Required raw reference. |
| delisted_status_revision_id | Required source revision id. |
| delisted_status_available_time | Required availability timestamp. |
| delisted_status_review_status | Required review status. |
| delisted_no_hit_status | Required when no direct delisting record is found. |
| delisted_no_hit_rationale | Required for any no-hit context. |

No-hit context can become supporting context only after reviewer handoff. It is not source reliability scoring and does not approve rows.

## H. ST / No-ST and ETF Not-Applicable Schema

STOCK rows require ST/no-ST evidence as of `2024-04-02`. ETF rows require an ETF not-applicable policy instead of being forced into stock ST/no-ST fields.

Required fields:

| Field | Requirement |
| --- | --- |
| st_status_evidence | Required for STOCK rows; not required for ETF rows with a reviewed not-applicable policy. |
| st_status_source_id | Required for STOCK evidence. |
| st_status_raw_reference | Required for STOCK evidence. |
| st_status_revision_id | Required for STOCK evidence. |
| st_status_available_time | Required for STOCK evidence. |
| st_status_review_status | Required for all rows. |
| st_status_not_applicable_reason | Required for ETF rows. |
| st_policy_status | Required controlled status. |

STOCK rows missing ST evidence map to `blocker_missing_st_status_evidence`. ETF rows missing a not-applicable policy map to `blocker_missing_st_not_applicable_policy`.

## I. Suspension / Trading Status Schema

Suspension or trading status should show whether the instrument had a decision-date trading status context or a reviewed not-applicable policy. Same-day quotation presence may be useful context, but it is not automatically listed, not-delisted, no-ST, not-suspended, membership, or survivorship proof.

Required fields:

| Field | Requirement |
| --- | --- |
| suspension_status_evidence | Required evidence or reviewed policy context. |
| suspension_status_source_id | Required source id. |
| suspension_status_raw_reference | Required raw reference. |
| suspension_status_revision_id | Required revision id. |
| suspension_status_available_time | Required availability timestamp. |
| suspension_status_review_status | Required review status. |
| trading_status_not_applicable_reason | Required when the evidence family is not applicable or not directly available. |

Missing status evidence or policy maps to `blocker_missing_suspension_or_trading_status`.

## J. Universe Membership Schema

Universe membership cannot be inferred from the legacy `etf_core` label alone. It requires row-level source-backed context as of `2024-04-02` or earlier.

Required fields:

| Field | Requirement |
| --- | --- |
| universe_membership_evidence | Required membership evidence or reviewed gap marker. |
| universe_membership_source_id | Required source id. |
| universe_membership_raw_reference | Required raw reference. |
| universe_membership_revision_id | Required source revision or snapshot id. |
| universe_membership_available_time | Required availability timestamp. |
| universe_membership_review_status | Required review status. |
| universe_asof_after_signal_flag | Required boolean. |
| universe_membership_limitation_note | Required when membership evidence is partial or later than signal date. |

The current selected sample has a universe as-of after signal blocker for all nine rows. That must remain visible until separately resolved.

## K. Survivorship Rationale Schema

All nine rows carry survivorship warnings. Future worklist rows must explain why each row is not included only because it survived into a later dataset.

Required fields:

| Field | Requirement |
| --- | --- |
| survivorship_warning_flag | Required boolean. |
| survivorship_rationale | Required narrative or controlled rationale. |
| survivorship_source_id | Required source id when rationale uses source support. |
| survivorship_available_time | Required availability timestamp. |
| survivorship_review_status | Required review status. |
| survivorship_limitation_note | Required when rationale is incomplete or context-only. |

Missing rationale maps to `blocker_missing_survivorship_rationale`.

## L. Source / Permission / Revision / Available-Time Schema

Every official evidence family must carry source lineage and timing fields. The goal is auditable decision-time context, not proof of performance.

Required shared fields:

| Field | Requirement |
| --- | --- |
| permission_class | Required report-only permission context. |
| source_hash_preview | Optional disclosure-safe preview; required if future source family requires hash context. |
| source_hash_disclosure_policy | Required when a hash preview is present or intentionally hidden. |
| local_file_hash_preview | Optional local identity preview; not PIT evidence by itself. |
| revision_id_type | Required controlled type for every revision id. |
| available_time_timezone | Required timezone or reviewed default policy. |
| review_time | Required for manually reviewed context. |
| reviewer_id | Required for accepted context or no-hit handoff. |
| reviewer_role | Required for accepted context or no-hit handoff. |
| reviewer_scope | Required for accepted context or no-hit handoff. |
| reviewer_attestation | Required for accepted context or no-hit handoff. |
| quality_status | Required controlled quality status. |
| limitation_note | Required for any warning, no-hit, inferred, partial, or not-applicable context. |
| blocker_reason | Required when row is blocked. |
| closure_status | Required controlled closure status. |
| closure_status_reason | Required status explanation. |

Missing source id, raw reference, permission class, revision id, or available time must block the row.

## M. Reviewer No-Hit Handoff Schema

Reviewer no-hit fields are handoff fields only. They do not accept no-hit as source reliability scoring and do not override missing source, revision, available-time, reviewer authority, or quality evidence.

Required fields:

| Field | Requirement |
| --- | --- |
| no_hit_review_needed | Required boolean. |
| no_hit_source_family | Required when no-hit review is needed. |
| no_hit_query_window | Required when no-hit review is needed. |
| no_hit_result | Required controlled result. |
| no_hit_acceptance_status | Required controlled status. |
| no_hit_acceptance_rationale | Required if accepted as context. |
| no_hit_reviewer_required | Required boolean. |

The current sample has nine no-hit review-needed rows and zero no-hit accepted-context rows. Future implementation must preserve this as blocked or needs-review by default.

## N. Quality / Limitation / Blocker Schema

Quality and limitation fields must make uncertainty visible.

Required quality rules:

| Rule | Behavior |
| --- | --- |
| Missing quality status | Block. |
| Failed quality status | Block. |
| Warning without limitation note | Block. |
| Any blocker reason present | Closure status remains blocked. |
| Accepted context with limitation | May become warning-with-limitation only. |
| No-hit accepted context | Context only; still not PIT approval. |
| Profile conflict unreviewed | Block affected row. |
| Forbidden downstream flag true | Block affected artifact or row. |

Limitations must be row-specific when the uncertainty is row-specific.

## O. Closure Status Vocabulary

Allowed closure statuses:

| Status | Meaning |
| --- | --- |
| missing_official_evidence | Required official evidence family is missing. |
| context_only | Row has context but no closure. |
| needs_manual_review | Reviewer action is needed. |
| no_hit_review_needed | No-hit handoff is required. |
| no_hit_accepted_context | No-hit was reviewed as supporting context only. |
| warning_with_limitation | Non-blocking warning with visible limitation note. |
| packet_row_ready_not_pit_approved | Packet row may be structurally complete but is not PIT approval. |
| blocked | One or more blocker statuses remain. |

`packet_row_ready_not_pit_approved` is not PIT admissibility. It must not be converted into replay input readiness.

## P. Blocker Status Vocabulary

Allowed blocker statuses:

| Blocker | Meaning |
| --- | --- |
| blocker_missing_listed_status_evidence | Listed/active evidence is missing. |
| blocker_missing_delisted_status_evidence | Delisted/not-delisted evidence is missing. |
| blocker_missing_st_status_evidence | STOCK ST/no-ST evidence is missing. |
| blocker_missing_st_not_applicable_policy | ETF ST not-applicable policy is missing. |
| blocker_missing_suspension_or_trading_status | Suspension/trading status or policy is missing. |
| blocker_missing_universe_membership_evidence | Membership evidence is missing. |
| blocker_universe_asof_after_signal | Universe context is later than signal date. |
| blocker_missing_survivorship_rationale | Survivorship rationale is missing. |
| blocker_missing_source_id | Source id is missing. |
| blocker_missing_raw_reference | Raw reference is missing. |
| blocker_missing_permission_class | Permission class is missing. |
| blocker_missing_revision_id | Revision id is missing. |
| blocker_missing_available_time | Available-time evidence is missing. |
| blocker_available_time_after_decision | Available time is after decision time. |
| blocker_missing_reviewer_authority | Reviewer authority is missing. |
| blocker_no_hit_unaccepted | No-hit context remains unaccepted. |
| blocker_profile_conflict_unreviewed | Mixed profile conflict is unresolved. |
| blocker_quality_missing_or_failed | Quality status is missing or failed. |
| blocker_warning_without_limitation | Warning lacks a limitation note. |
| blocker_forbidden_downstream_flag | Forbidden downstream flag is true. |

Future implementations may add stricter blockers only if they remain report-only and are tested.

## Q. Field-Level Validation Rules

Future report-only implementation should validate:

1. Exactly nine selected rows are present.
2. The symbol set exactly matches the selected sample.
3. Symbols are strings and leading zeros remain intact.
4. `signal_date` equals `2024-04-02`.
5. `legacy_universe_label` equals `etf_core`.
6. `instrument_type` matches the selected row table.
7. Recommended profile and profile-conflict fields match the selected row table.
8. STOCK rows require ST/no-ST evidence fields.
9. ETF rows require ST not-applicable policy fields.
10. Every evidence family has source id, raw reference, permission class, revision id, and available-time fields or explicit blocker reasons.
11. Available time after the decision date blocks the row.
12. No-hit accepted context cannot remove PIT, source, revision, timing, profile, reviewer, quality, or survivorship blockers by itself.
13. Warning statuses require limitation notes.
14. Any forbidden downstream safety field set true blocks the artifact.
15. Forward returns or labels cannot be joined to the decision-time packet.

## R. Example Row Shapes

Example STOCK row shape:

```text
packet_worklist_id = official_status_packet_worklist_2024_04_02_etf_core_v0_1
signal_date = 2024-04-02
universe_name = etf_core
symbol = 000001
instrument_type = STOCK
legacy_universe_label = etf_core
recommended_profile = stock_core
profile_conflict_flag = true
profile_policy_status = needs_manual_review
st_policy_status = st_status_required
closure_status = blocked
blocker_reason = blocker_missing_listed_status_evidence; blocker_missing_delisted_status_evidence; blocker_missing_st_status_evidence; blocker_missing_universe_membership_evidence; blocker_missing_survivorship_rationale; blocker_profile_conflict_unreviewed
```

Example ETF row shape:

```text
packet_worklist_id = official_status_packet_worklist_2024_04_02_etf_core_v0_1
signal_date = 2024-04-02
universe_name = etf_core
symbol = 159915
instrument_type = ETF
legacy_universe_label = etf_core
recommended_profile = etf_core
profile_conflict_flag = false
st_status_not_applicable_reason = ETF row requires reviewed not-applicable policy
st_policy_status = etf_not_applicable_policy_required
closure_status = blocked
blocker_reason = blocker_missing_listed_status_evidence; blocker_missing_delisted_status_evidence; blocker_missing_st_not_applicable_policy; blocker_missing_universe_membership_evidence; blocker_missing_survivorship_rationale
```

Example packet-ready context remains explicitly non-approval:

```text
closure_status = packet_row_ready_not_pit_approved
closure_status_reason = Official evidence packet fields appear complete for review, but this is not PIT approval, replay input readiness, or trading permission.
pit_admissibility_approved = false
active_replay_input = false
buy_review_allowed = false
trading_allowed = false
```

## S. Safety and Non-Approval Fields

Every future artifact must include these false safety fields:

| Field | Required value |
| --- | --- |
| official_status_evidence_closed | false |
| pit_evidence_closed | false |
| pit_admissibility_approved | false |
| active_replay_input | false |
| replay_execution_allowed | false |
| replay_decision_freeze_allowed | false |
| forward_labels_created | false |
| training_dataset_created | false |
| metric_computation_performed | false |
| model_training_performed | false |
| stock_profile_validation_created | false |
| paper_expansion_allowed | false |
| buy_review_allowed | false |
| trading_allowed | false |
| broker_api_called | false |
| order_placed | false |
| message_sent | false |
| external_api_called | false |
| llm_api_called | false |
| current_candidates_executed | false |
| snapshot_built | false |
| signal_semantics_mutated | false |
| data_raw_written | false |
| data_processed_written | false |
| data_cache_written | false |

If any future artifact sets one of these fields true, the artifact must be blocked by `blocker_forbidden_downstream_flag`.

## T. Future Core Artifact Contract

A future report-only core may write only manual diagnostic artifacts, such as:

| Artifact | Purpose |
| --- | --- |
| `metadata.json` | Aggregate ids, counts, status, safety fields, and paths. |
| `official_status_evidence_packet_closure_worklist.csv` | Row-level selected-sample worklist. |
| `official_status_evidence_family_matrix.csv` | Evidence-family requirements by row and instrument type. |
| `official_status_source_lineage_requirements.csv` | Source, permission, raw-reference, revision, and available-time requirements. |
| `official_status_blocker_matrix.csv` | Row blocker statuses. |
| `official_status_no_hit_handoff_matrix.csv` | Reviewer no-hit handoff fields. |
| `official_status_safety_flags.json` | Required false downstream fields. |
| `official_status_evidence_packet_closure_worklist_report.md` | Human-readable report. |

The future core must not mutate the existing PIT evidence closure worklist. It may reference accepted worklist context by path and count, but it must create a separate official-status worklist surface.

## U. Candidate Next Routes

| Route | Decision | Reason |
| --- | --- | --- |
| A. Historical Replay Official Status Evidence Packet Closure Worklist Core Report-Only v0.1 | Selected. | This design can safely become a report-only core scaffold with all rows blocked or review-needed by default. |
| B. Historical Replay Official Status Evidence Packet Closure Worklist Artifact Views / Status Planning Report-Only v0.1 | Not selected. | Views should follow after a core artifact contract exists. |
| C. Historical Replay Reviewer No-Hit Acceptance Planning for 2024-04-02 etf_core Report-Only v0.1 | Reserve. | No-hit is important, but the core worklist can represent no-hit as a blocked handoff first. |
| D. Historical Replay Mixed Universe Policy Planning for legacy etf_core Report-Only v0.1 | Reserve. | Mixed profile context can be carried as row fields before separate policy resolution. |
| E. Pause and manually collect official status evidence outside the repo | Not selected. | Manual collection is not required for a blocked report-only scaffold. |

## V. Selected Next Route

Selected next route:

`Historical Replay Official Status Evidence Packet Closure Worklist Core Report-Only v0.1`

The next task should implement only the deterministic report-only scaffold if approved. It should generate the exact nine-row selected-sample worklist, preserve all blockers by default, and keep all downstream approval fields false.

## W. Why Selected Route Is Safe

The selected route is safe because it can create a structural worklist without fetching official data, accepting no-hit context, resolving mixed universe policy, approving PIT, or creating replay-ready inputs. The future core can prove row coverage, field coverage, blocker vocabulary, and safety boundaries while keeping every row blocked by default.

This reduces implementation risk before any evidence collection or adjudication.

## X. What Must Not Be Bundled

The selected next route must not bundle evidence fetching, source content reads, official packet closure, reviewer no-hit runtime acceptance, mixed universe production policy, source reliability scoring, PIT admissibility, active replay input, replay execution, decision freeze, forward label creation, metric computation, training, model work, weight or threshold changes, formula changes, stock-profile validation, paper expansion, real buy-review, broker/API/order/message behavior, current-candidates execution, snapshot build, signal semantics mutation, Project Source package creation, checkpoint docs, or protected data writes.

## Y. ChatGPT/Codex Mode Recommendation

Use Codex high for the selected core scaffold task because the design is deterministic, report-only, and blocked by default.

Use ChatGPT Pro / Pro Extended before any task decides official source hierarchy, source reliability scoring, reviewer no-hit sufficiency, ambiguous available-time policy, mixed universe production policy, same-day quotation inference, PIT approval, replay readiness, label creation, metric computation, model gating, stock-profile gating, paper expansion, buy-review, or trading authority.

## Z. Commit/Tag/Source Recommendation

If this docs-only design is accepted, a manual commit may use:

`docs: design official status evidence packet closure worklist`

No tag is recommended for this design alone. No immediate Project Source update is recommended unless the user decides this design materially changes the external roadmap.

## AA. Recommended Next Task

Recommended next task:

`Historical Replay Official Status Evidence Packet Closure Worklist Core Report-Only v0.1`

Goal for that task: create a deterministic report-only core scaffold for the exact nine-row `2024-04-02 / etf_core` selected sample, with official evidence family fields, source/timing/revision fields, reviewer no-hit handoff fields, mixed STOCK/ETF profile fields, survivorship fields, closure/blocker vocabularies, and required non-approval safety flags. All rows should remain blocked or review-needed by default.
