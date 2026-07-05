# Historical Replay PIT Evidence Closure Worklist Design for 2024-04-02 / etf_core v0.1

## A. Decision / Status

```text
phase = historical_replay_pit_evidence_closure_worklist_design_selected_sample
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_checkpoint = v1.83.0
latest_checkpoint_commit = 46f634b
latest_repo_commit = 61e7f00
selected_historical_decision_date = 2024-04-02
selected_universe = etf_core
worklist_design_created = yes
selected_next_route = Historical Replay PIT Evidence Closure Worklist Core Report-Only v0.1

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
```

This report designs a worklist only. It does not implement the worklist, create worklist artifacts, close PIT evidence, approve PIT admissibility, create active replay input, execute replay, freeze decisions, create forward labels, compute metrics, adjust weights/formulas/thresholds/models, validate stock profiles, expand paper workflow authority, approve buy-review, or authorize trading.

## B. Current Accepted State

The latest accepted checkpoint is v1.83.0 at `46f634b`. The current repository head for this design is `61e7f00`, described as `v1.83.0-8-g61e7f00`.

The accepted selected sample is:

```text
historical_decision_date = 2024-04-02
universe = etf_core
```

The accepted prior plan is `Historical Replay PIT Evidence Gap Closure Plan for 2024-04-02 / etf_core v0.1`, which selected this worklist design as the next safe route.

## C. Selected Sample and Blocker Context

Existing local context shows one selected date and 9 symbols under the legacy `etf_core` label:

```text
000001, 000002, 159915, 300750, 510300, 600000, 600519, 601318, 688981
```

Known blockers:

- the backfill execution manifest `f98279630ce6` marks `2024-04-02 / etf_core` as blocked because the universe as-of date is later than the signal date;
- PIT overlay `38a254c54024` has 9 rows for the selected date, all needing manual review, all not valid for signal date, and all carrying survivorship warnings;
- PIT evidence review worklist `1c7972988f59` reports 9 needs-evidence rows, 9 future-dated hints, 0 authoritative hints, and 0 valid-for-signal-date rows for the selected date;
- official/reviewer/no-hit artifacts remain warning/context only;
- legacy `etf_core` contains both STOCK and ETF rows, so instrument type and profile handling must be explicit.

## D. Worklist Purpose

The future worklist should organize missing row-level evidence so a human reviewer or later report-only workflow can see what is missing, context-only, warning-only, blocked, or closure-ready. It must not decide PIT admissibility.

The worklist should:

1. Preserve row identity and source lineage.
2. Carry existing blocker reasons forward.
3. Separate official status evidence from reviewer no-hit acceptance.
4. Separate source hash, local hash, revision, and available-time metadata.
5. Represent mixed stock/ETF universe profile risk.
6. Keep closure-ready context distinct from PIT approval.

## E. Row Identity Schema

Required identity fields:

| field | required | meaning | validation rule |
|---|---|---|---|
| worklist_id | yes | Future worklist run identifier. | Non-empty string. |
| source_artifact_family | yes | Existing artifact family, such as overlay plan or evidence review worklist. | Non-empty controlled value. |
| source_artifact_id | yes | Source artifact id such as `38a254c54024` or `1c7972988f59`. | Non-empty string. |
| signal_date | yes | Historical decision date. | Must equal `2024-04-02` for this selected sample. |
| universe_name | yes | Legacy universe label. | Must equal `etf_core` for this selected sample. |
| symbol | yes | Security identifier. | Non-empty string; keep leading zeros. |
| symbol_name_hint | optional | Display/context name from prior worklist if available. | Context only. |
| row_source_path_preview | optional | Relative source artifact path preview. | Must not expose private absolute paths. |

## F. Universe and Instrument-Type Schema

Required universe/profile fields:

| field | required | meaning |
|---|---|---|
| instrument_type | yes | STOCK, ETF, or needs-review value from existing summaries or reviewer input. |
| exchange_or_market | yes | Exchange or market identifier such as SZSE or SSE when known. |
| legacy_universe_label | yes | Original `etf_core` label. |
| recommended_profile | yes | Future profile guidance, such as stock_core, etf_core, or mixed_demo_core. |
| profile_conflict_flag | yes | True when the legacy label and instrument type create profile ambiguity. |
| profile_conflict_reason | required if flagged | Explanation of why profile handling needs review. |

Rules:

- STOCK rows under legacy `etf_core` must not be treated as ETF-valid by label alone.
- ETF rows still need source, timing, membership, and quality evidence.
- Mixed profile handling is review context only, not row approval or rejection.

## G. Official Status Evidence Schema

Required official status fields:

| field | required | row applicability |
|---|---|---|
| listed_status_evidence | yes | All rows. |
| listed_status_source_id | yes | All rows. |
| listed_status_available_time | yes | All rows. |
| delisted_status_evidence | yes | All rows. |
| delisted_status_source_id | yes | All rows. |
| st_status_evidence | conditional | Required for stock rows; ETF rows need not-applicable policy. |
| st_status_not_applicable_reason | conditional | Required for ETF rows if no ST evidence is used. |
| suspension_status_evidence | conditional | Required where trading eligibility depends on suspension state. |
| trading_status_not_applicable_reason | conditional | Required if suspension/trading status is not applicable. |
| universe_membership_evidence | yes | All rows. |
| universe_membership_source_id | yes | All rows. |

Every official status field must also carry source lineage, revision, available-time, and reviewer/quality context elsewhere in the same row.

## H. Source / Raw-Document Lineage Schema

Required lineage fields:

| field | required | meaning |
|---|---|---|
| source_id | yes | Stable source identifier. |
| source_name | yes | Human-readable source name. |
| source_type | yes | Official, public, local reviewed, manual overlay, or other controlled type. |
| permission_class | yes | Permitted local/report-only use class. |
| raw_reference | yes | Relative raw document or raw dataset reference, or explicit missing value. |
| raw_reference_type | yes | Document, dataset, manual overlay, source packet, or other controlled type. |
| row_locator | recommended | Optional row/document locator for later manual review. |
| source_artifact_lineage_note | yes | Note tying this row back to overlay/worklist context. |

Validation rules:

- `source_name` is not permission.
- `raw_reference` is not evidence closure by itself.
- A missing raw reference blocks closure-ready status.
- A local file created later can only be context until historical availability is proven.

## I. Source Hash / Local Hash / Revision / Available-Time Schema

Required fields:

| field | required | meaning |
|---|---|---|
| source_hash_preview | yes or explicit missing | Preview/disclosure-safe source hash context. |
| source_hash_disclosure_level | yes | Preview-only, redacted, missing, or internal-only. |
| local_file_hash_preview | yes if local file is used | Preview/disclosure-safe local file byte identity. |
| local_file_hash_disclosure_level | yes if local file is used | Preview-only, redacted, missing, or internal-only. |
| revision_id | yes | Source revision identifier. |
| revision_id_type | yes | Publication id, dataset version, archive timestamp, reviewer assigned id, or other controlled type. |
| available_time | yes | Time at which the evidence became available to a decision-maker. |
| available_time_timezone | yes | Timezone or policy for available_time. |
| fetch_time | recommended | Time evidence was fetched or copied into local context. |
| review_time | recommended | Time reviewer inspected the evidence. |
| timing_relation_to_decision | yes | before_decision, after_decision, unknown, or conflict. |

Validation rules:

- Full hashes must not be required for public status surfaces.
- Source hash and local file hash are distinct.
- Revision id cannot be inferred from a file name alone.
- Fetch/review time cannot substitute for available-time evidence.
- `closure_ready` is not PIT admissible.

## J. Reviewer No-Hit Acceptance Schema

Required reviewer/no-hit fields:

| field | required | meaning |
|---|---|---|
| reviewer_id | yes | Reviewer identifier or explicit missing value. |
| reviewer_role | yes | Role or authority class. |
| reviewer_scope | yes | What the reviewer is allowed to assess. |
| reviewer_attestation | yes | Statement that the reviewer inspected the evidence context. |
| searched_source | required for no-hit | Source searched for missing evidence. |
| query_window | required for no-hit | Date/query window used. |
| no_hit_result | required for no-hit | Result observed. |
| no_hit_acceptance_status | required for no-hit | missing, needs_review, accepted_context, rejected_context. |
| no_hit_rationale | required for accepted_context or rejected_context | Why the no-hit context is acceptable or not. |

Rules:

- Reviewer no-hit acceptance is not source reliability scoring.
- Reviewer acceptance cannot override timing, source lineage, revision, or quality blockers.
- Accepted no-hit context can reduce a missing-evidence explanation, but it does not approve PIT admissibility.

## K. Quality / Limitation / Permission Schema

Required fields:

| field | required | meaning |
|---|---|---|
| permission_status | yes | allowed_context, needs_review, blocked, or missing. |
| quality_status | yes | accepted_context, needs_review, warning, blocked, or missing. |
| limitation_note | required for warnings/context-only rows | Human-readable limitation. |
| blocker_reason | required for blocked rows | Main blocker reason. |
| context_only_flag | yes | True when evidence is context only. |
| closure_status | yes | Row closure status from the allowed vocabulary. |
| closure_status_reason | yes | Why the status was assigned. |

Rules:

- Warnings require limitation notes.
- Missing permission blocks closure-ready status.
- Context-only evidence cannot become closure-ready without review.

## L. Survivorship Rationale Schema

Required survivorship fields:

| field | required | meaning |
|---|---|---|
| survivorship_warning_flag | yes | Carry forward warning from overlay context. |
| survivorship_rationale | yes | Explanation showing why the row is not only a later-surviving artifact. |
| survivorship_source_id | yes | Source used for the rationale. |
| survivorship_available_time | yes | Time at which survivorship evidence was available. |
| survivorship_review_status | yes | missing, needs_review, accepted_context, or blocked. |

If survivorship rationale is missing, the row must remain blocked or needs-review.

## M. Closure Status Vocabulary

Allowed closure statuses:

| status | meaning |
|---|---|
| missing_evidence | Required evidence is absent. |
| context_only | Evidence exists but is not sufficient for closure. |
| needs_manual_review | Evidence exists and needs reviewer assessment. |
| no_hit_review_needed | A source search had no hit and needs reviewer handling. |
| no_hit_accepted_context | Reviewer accepted no-hit context, but this is not PIT approval. |
| warning_with_limitation | A warning exists and limitation is visible. |
| closure_ready_not_pit_approved | Required worklist fields appear present for later review, but the row is not PIT-admissible. |
| blocked | One or more blockers remain. |

The vocabulary intentionally avoids any status that implies replay readiness, active input readiness, buy-review readiness, or trading readiness.

## N. Blocker Status Vocabulary

Allowed blocker statuses:

| blocker | trigger |
|---|---|
| blocker_universe_asof_after_signal | Existing universe as-of date is after `2024-04-02`. |
| blocker_missing_authoritative_hint | Existing worklist has no authoritative source hint. |
| blocker_missing_source_id | Source id is missing. |
| blocker_missing_permission_class | Permission class is missing. |
| blocker_missing_raw_reference | Raw reference is missing. |
| blocker_missing_source_hash | Source hash preview or explicit redaction policy is missing. |
| blocker_missing_local_file_hash | Local file hash preview is missing when a local file is used. |
| blocker_missing_revision_id | Revision id is missing. |
| blocker_missing_available_time | Available time is missing. |
| blocker_available_time_after_decision | Available time is after the selected decision date/time. |
| blocker_available_time_conflict | Conflicting available-time evidence exists. |
| blocker_missing_official_status_evidence | Required official status field is missing. |
| blocker_missing_universe_membership_evidence | Membership evidence is missing. |
| blocker_missing_survivorship_rationale | Survivorship rationale is missing. |
| blocker_missing_reviewer_authority | Reviewer identity, role, scope, or attestation is missing. |
| blocker_no_hit_unaccepted | No-hit context exists but is not accepted. |
| blocker_quality_missing_or_failed | Quality status is missing or failed. |
| blocker_warning_without_limitation | Warning lacks a limitation note. |
| blocker_profile_conflict_unreviewed | Mixed stock/ETF profile conflict remains unreviewed. |
| blocker_forbidden_downstream_flag | Any forbidden downstream flag is true. |

## O. Field-Level Validation Rules

Future report-only implementation should validate:

1. `signal_date` equals `2024-04-02`.
2. `universe_name` equals `etf_core`.
3. Symbols preserve leading zeros.
4. Every row has instrument type and exchange/market context.
5. Every STOCK row has ST/no-ST evidence or a blocker.
6. Every ETF row has ETF-specific status handling or a not-applicable policy.
7. `source_id`, `source_type`, and `permission_class` are non-empty for closure-ready rows.
8. Source hash preview and local file hash preview are never treated as validation.
9. `revision_id` is non-empty and not merely the file name.
10. `available_time` is present and has timezone policy.
11. Rows with available-time after the decision date remain blocked.
12. Reviewer no-hit acceptance cannot override blockers.
13. Any warning requires a limitation note.
14. Any forbidden downstream flag true forces blocked status.

## P. Existing Artifact Lineage Carry-Forward Rules

Carry forward these fields from current local artifacts when available:

| source artifact | carry-forward fields |
|---|---|
| Execution manifest `f98279630ce6` | readiness status, blocker reason, universe as-of date, source policy, recommended filters. |
| Overlay plan `38a254c54024` | signal date, symbol, universe, proposed available time, base universe path preview, base universe as-of date, source, upstream source, survivorship warning, manual review required, valid-for-signal-date flag, blocker reason. |
| Evidence review worklist `1c7972988f59` | needs-evidence count, future-dated hint count, authoritative hint count, suggested name, suggested instrument type, suggested exchange, suggested next action. |
| Checklist validator `62e9eb747197` | strict blocker categories for comparison, especially timing, survivorship, ST/no-ST, and unacceptable source context. |
| Reviewer no-hit artifacts | no-hit context status, accepted count, needs-review count, downstream impact context. |

Carry-forward data remains context. It does not become closure.

## Q. Mixed Stock/ETF Universe Profile Handling

The worklist must represent `etf_core` as a legacy label for this sample. It should add explicit profile fields:

```text
legacy_universe_label = etf_core
instrument_type = STOCK / ETF / needs_review
recommended_profile = stock_core / etf_core / mixed_demo_core / needs_review
profile_conflict_flag = true / false
profile_conflict_reason = ...
profile_policy_status = needs_review / accepted_context / blocked
```

Suggested default:

- STOCK rows under legacy `etf_core` start as `profile_conflict_flag=true`.
- ETF rows still require source and timing evidence.
- No row is approved or rejected by profile handling alone.

## R. Safety and Non-Approval Fields

Every future worklist row should include:

```text
pit_evidence_closed = false
pit_admissibility_approved = false
active_replay_input = false
replay_execution_allowed = false
replay_decision_freeze_allowed = false
forward_labels_created = false
training_dataset_created = false
metric_computation_performed = false
model_training_performed = false
stock_profile_validation_created = false
paper_expansion_allowed = false
buy_review_allowed = false
trading_allowed = false
broker_api_called = false
order_placed = false
message_sent = false
external_api_called = false
llm_api_called = false
current_candidates_executed = false
snapshot_built = false
signal_semantics_mutated = false
data_raw_written = false
data_processed_written = false
data_cache_written = false
```

## S. Example Worklist Row Shape

Illustrative row shape only:

```text
worklist_id = future_run_id
source_artifact_family = point_in_time_universe_overlay_plan
source_artifact_id = 38a254c54024
signal_date = 2024-04-02
universe_name = etf_core
symbol = 159915
symbol_name_hint = ChiNext ETF
instrument_type = ETF
exchange_or_market = SZSE
legacy_universe_label = etf_core
recommended_profile = etf_core
profile_conflict_flag = false
listed_status_evidence = missing
delisted_status_evidence = missing
st_status_not_applicable_reason = ETF row, needs policy review
suspension_status_evidence = missing
universe_membership_evidence = missing
source_id = missing
source_type = missing
permission_class = missing
raw_reference = context_only_existing_overlay
source_hash_preview = missing
local_file_hash_preview = missing
revision_id = missing
available_time = missing
reviewer_id = missing
no_hit_acceptance_status = missing
quality_status = needs_review
limitation_note = Existing overlay is later-dated context only.
blocker_reason = blocker_missing_official_status_evidence
closure_status = blocked
```

This example is not a generated artifact and is not evidence closure.

## T. What Future Implementation May Do

A future report-only core may:

1. Read existing report artifacts as inputs.
2. Emit a manual diagnostics worklist design output or docs/report output.
3. Produce a row-level CSV template under an approved report-only path.
4. Carry forward blocker reasons and safety fields.
5. Validate that no row claims PIT approval.
6. Keep all rows review-only unless manually completed later.

## U. What Must Wait for Separate Pro / Pro Extended Design

Separate design review is needed before:

1. Adjudicating real available-time conflicts.
2. Accepting no-hit context as sufficient for any strict field.
3. Defining production mixed-universe policy.
4. Scoring source reliability.
5. Creating a real PIT validator.
6. Turning closure-ready rows into PIT-admissible rows.
7. Creating replay input, replay execution, labels, training data, model artifacts, stock-profile validation, paper expansion, buy-review, or trading behavior.

## V. Candidate Next Routes

| route | description | decision |
|---|---|---|
| A. Historical Replay PIT Evidence Closure Worklist Core Report-Only v0.1 | Implement a report-only core that emits the designed worklist artifact without approving evidence. | Selected. |
| B. Historical Replay Official Status Evidence Packet Planning for 2024-04-02 etf_core Report-Only v0.1 | Isolate official listed/delisted/ST/suspension/membership evidence first. | Reserve. |
| C. Historical Replay Reviewer No-Hit Acceptance Worklist Design for 2024-04-02 etf_core Report-Only v0.1 | Deepen no-hit handling only. | Reserve. |
| D. Historical Replay Mixed Universe Policy Design for etf_core Report-Only v0.1 | Resolve mixed universe policy before implementation. | Reserve if profile ambiguity becomes blocking. |
| E. Manual evidence collection outside the system before implementation | Pause engineering until manual collection exists. | Not selected because a safe report-only worklist can organize the collection. |

## W. Selected Next Route

Selected next route:

```text
Historical Replay PIT Evidence Closure Worklist Core Report-Only v0.1
```

## X. Why Selected Route Is Safe

The selected route is safe because the worklist core can produce a review scaffold, not a closure decision. It can keep every row blocked or needs-review by default, carry forward known blockers, and require explicit future manual evidence before any PIT closure or downstream replay step.

## Y. What Must Not Be Bundled

The next task must not bundle:

1. PIT evidence closure.
2. PIT admissibility approval.
3. Current-candidates execution.
4. Snapshot build.
5. Workflows that create active replay input.
6. Replay execution.
7. Replay decision freeze.
8. Forward-return label creation.
9. Training, evaluation, metric computation, or model work.
10. Weight, formula, threshold, or model adjustment.
11. Stock-profile validation.
12. Paper workflow expansion.
13. Buy-review approval.
14. Broker, order, message, external API, LLM, or trading behavior.
15. Protected data writes.

## Z. ChatGPT / Codex Mode Recommendation

Codex high is appropriate for the next report-only core implementation because the schema is bounded and the intended outputs can default to blocked/review-only rows. Use Pro or Pro Extended before any task that accepts ambiguous evidence, defines production mixed-universe policy, or changes downstream readiness semantics.

## AA. Commit / Tag / Source Recommendation

If accepted, this docs-only design can be committed normally. No tag is recommended for this standalone design report. No immediate Project Source update is recommended unless the user accepts it as a roadmap-changing mainline policy.

## AB. Recommended Next Task

Recommended next task:

```text
Historical Replay PIT Evidence Closure Worklist Core Report-Only v0.1
```

Scope: implement a report-only worklist core that emits row-level blocked/review-only evidence collection scaffolding for `2024-04-02 / etf_core`, preserving all non-approval and downstream safety fields.
