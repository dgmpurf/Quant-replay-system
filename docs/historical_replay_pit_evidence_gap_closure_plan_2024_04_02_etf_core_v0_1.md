# Historical Replay PIT Evidence Gap Closure Plan for 2024-04-02 / etf_core v0.1

## A. Decision / Status

```text
phase = historical_replay_pit_evidence_gap_closure_plan_selected_sample
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_checkpoint = v1.83.0
latest_checkpoint_commit = 46f634b
latest_repo_commit = 25dec8f
selected_historical_decision_date = 2024-04-02
selected_universe = etf_core
selected_next_route = Historical Replay PIT Evidence Closure Worklist Design for 2024-04-02 etf_core Report-Only v0.1

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

This document is a closure plan only. It does not close PIT evidence, approve PIT admissibility, create replay input, execute replay, freeze decisions, create labels, compute metrics, adjust weights/formulas/thresholds/models, validate stock profiles, expand paper workflow authority, approve buy-review, or authorize trading.

## B. Current Accepted State

The accepted checkpoint is v1.83.0 at `46f634b`. The current repository head for this report is `25dec8f`, described as `v1.83.0-7-g25dec8f`.

The historical replay training loop has been re-anchored as the mainline. The selected sample from the prior audit is:

```text
historical_decision_date = 2024-04-02
universe = etf_core
```

The personal MVP advisory review branch remains downstream display context and is paused for this evidence-closure step.

## C. Selected Sample

The selected sample is one historical decision date and one universe label:

| field | value |
|---|---|
| Decision date | 2024-04-02 |
| Universe label | etf_core |
| Intended use | PIT evidence closure planning |
| Not intended for | Replay execution, label creation, training, model work, paper expansion, buy-review, or trading |

Important nuance: existing local artifacts indicate that the legacy `etf_core` label may contain both STOCK and ETF rows. The closure worklist must therefore preserve instrument type, symbol, and universe-profile context instead of treating the label as self-validating.

## D. Existing Local Evidence Footprint

| artifact family | path / id | observed context | closure meaning |
|---|---|---|---|
| Current-candidates backfill plan | `outputs/reports/current_candidates_backfill_plan/aadd86db24a1/metadata.json` | `status=PASS`, `universe=etf_core`, first signal date `2024-04-02`, selected date count `8`, current-candidates not executed. | Good date-selection context only; not PIT closure. |
| Broader backfill plan | `outputs/reports/current_candidates_backfill_plan/b52c41c864ad/metadata.json` | `status=PASS`, range starts `2024-01-02`, universe `etf_core`. | Confirms broader planning window, not selected first sample. |
| Execution manifest | `outputs/reports/current_candidates_backfill_execution_manifest/f98279630ce6/current_candidates_backfill_execution_manifest.csv` | 8 planned dates for `etf_core`; all rows have `readiness_status=BLOCKED_UNIVERSE_AS_OF`; for `2024-04-02`, universe as-of date is later than signal date. | Strong blocker evidence. |
| PIT overlay plan | `outputs/reports/point_in_time_universe_overlay_plan/38a254c54024/metadata.json` | `status=WARN`, 72 rows, 8 signal dates, 9 symbols, 0 valid-for-signal-date rows, 72 survivorship warnings. | Main local source for closure worklist design. |
| PIT overlay row plan | `outputs/reports/point_in_time_universe_overlay_plan/38a254c54024/point_in_time_universe_overlay_plan.csv` | For `2024-04-02`, 9 rows; all need manual review; template rows are not reviewed and not valid for execution. | Supplies row grain and starting fields. |
| PIT evidence review date summary | `outputs/reports/point_in_time_universe_evidence_review_worklist/1c7972988f59/pit_universe_evidence_review_date_summary.csv` | `2024-04-02 / etf_core` has 9 rows, 9 symbols, 9 needs-evidence rows, 9 future-dated hints, 0 authoritative hints, 0 valid rows. | Confirms full-date blocker. |
| PIT evidence review symbol summary | `outputs/reports/point_in_time_universe_evidence_review_worklist/1c7972988f59/pit_universe_evidence_review_symbol_summary.csv` | 9 symbols, each with 8 rows across the date range; first date `2024-04-02`; needs evidence and future-dated hints remain. | Provides symbol-level closure grouping. |
| Checklist validator | `outputs/reports/pit_evidence_checklist_validator/62e9eb747197/metadata.json` | `status=WARN`, 16 rows, 16 blocked, 0 checklist pass rows, no approvals applied. | Prior strict-checklist context, not selected-sample closure. |
| Official status packet enrichment | `outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c/metadata.json` | `status=WARN`, 16 remaining blocked, 16 reviewer acceptance required. | Useful evidence-family guidance, not accepted closure. |
| Reviewer no-hit acceptance | `outputs/reports/reviewer_no_hit_source_coverage_acceptance/2e05e4b74794/metadata.json` | 64 no-hit contexts need review, 0 accepted. | Reviewer no-hit remains open. |
| Reviewer no-hit downstream impact | `outputs/reports/reviewer_no_hit_acceptance_downstream_impact/9e164963455e/metadata.json` | 0 accepted no-hit contexts; remaining blocked count remains 16. | No downstream gap reduction yet. |
| One-row material evidence package | `outputs/reports/one_row_material_evidence_fill_package/136cbd739ca1/metadata.json` | `2024-04-02 / stock_core / 000001`, `status=WARN`, 16 remaining blocked. | Comparison case only. |
| One-row checklist preview | `outputs/reports/one_row_checklist_pass_candidate_preview/3d3bcc2f95cf/metadata.json` | `2024-04-02 / stock_core / 000001`, strict gap count `10`, not pass-candidate. | Comparison case only. |

## E. PIT Universe Gap Map

| gap | observed state | closure requirement |
|---|---|---|
| Universe as-of date | Execution manifest says the universe as-of date is later than the selected signal date. | Replace or review with a date-valid universe reference for `2024-04-02`. |
| Valid-for-signal-date flag | Overlay metadata reports 0 valid rows. | Each row needs explicit valid-for-signal-date evidence after manual review. |
| Include flag | Overlay plan template rows do not carry accepted inclusion decisions. | Later review-update rows must set inclusion context only after evidence is sufficient. |
| Instrument-type policy | Legacy `etf_core` may include STOCK and ETF rows. | Worklist must capture instrument type and universe-profile policy; do not infer ETF-only validity from the label. |
| Row grain | `2024-04-02` has 9 symbols. | Closure worklist should be row-level: date, universe, symbol, instrument type, source evidence, status fields, reviewer fields. |

## F. Official Status Evidence Gap Map

| evidence family | why needed | closure requirement |
|---|---|---|
| Active/listed status | The row must be eligible as of the decision date. | Official or accepted public evidence proving listed/active state as of `2024-04-02`. |
| Delisted/not-delisted status | Avoid survivorship leakage from later universe membership. | Date-specific evidence or rationale showing the row was not selected only because it survived later. |
| ST/no-ST status where applicable | A-share eligibility and risk filters need explicit state. | Stock rows require no-ST or ST status evidence; ETF rows need a documented not-applicable rule if appropriate. |
| Suspension/trading status where applicable | Suspended or non-tradable rows may not be valid candidates. | Date-specific trading/suspension context for each symbol or an accepted not-applicable rule. |
| Universe membership evidence | The row must belong to the selected universe by decision time. | Source-backed membership proof as of or before `2024-04-02`. |
| Survivorship rationale | Existing overlay metadata shows survivorship warnings. | Row-level survivorship rationale must be visible before any evidence bundle design. |

## G. Source / Raw-Document Lineage Gap Map

| field family | needed fields | current risk |
|---|---|---|
| Source identity | source id, source name, source type, permission class | Current artifacts mention source context but do not close source permission or production registry state. |
| Raw reference | raw document or raw dataset reference, row locator, artifact id | Existing references are planning context and may point to later-dated local files. |
| Review lineage | reviewer id, reviewer role, reviewed time, manual review status | Needs future review-update design; no accepted selected-sample review updates exist here. |
| Limitation lineage | limitation note, quality status, warning reason, blocker reason | Existing plans contain blocker reasons; closure worklist must carry them forward row by row. |

The next route should design a worklist that records lineage fields without reading or regenerating raw data.

## H. Source Hash / Local Hash / Revision / Available-Time Gap Map

| gap | closure requirement |
|---|---|
| Source hash | Record source-hash metadata or source-artifact hash preview according to existing disclosure policy; do not treat preview as validation. |
| Local file hash | Distinguish local file byte identity from source hash. |
| Revision id | Record revision id and revision type; file name alone is insufficient. |
| Available time | Prove the evidence was available by the selected decision time, or mark the row blocked/review-needed. |
| Fetch/review time | Record fetch time and review time where relevant, but do not let them replace available-time evidence. |
| Backfill risk | A file created or reviewed after `2024-04-02` can still be context only unless historical availability is separately proven. |

## I. Reviewer Authority / No-Hit Acceptance Gap Map

Existing reviewer no-hit artifacts show 64 no-hit contexts needing review and zero accepted no-hit contexts. Therefore the selected sample still needs a reviewer acceptance path for:

1. Which official/public source was searched.
2. What no-hit result was observed.
3. Why no-hit is acceptable or not acceptable for the field.
4. Reviewer identity, role, scope, and attestation.
5. Why reviewer acceptance does not override PIT timing, source lineage, revision, or quality blockers.

Reviewer no-hit acceptance is evidence context, not an approval to run replay.

## J. Quality / Limitation / Permission Gap Map

| gap | closure requirement |
|---|---|
| Permission class | Record allowed local use of the source/reference. |
| Quality status | Use accepted, needs-review, or blocked status per row; do not leave unknown status for closure. |
| Limitation note | Any warning must carry a visible limitation note. |
| Context-only evidence | Mark context-only fields so they cannot be mistaken for closure. |
| Review-update separation | Future review-update CSVs can draft closure fields, but this report does not create them. |

## K. Survivorship Rationale Gap Map

The overlay plan reports survivorship warnings for all 72 rows. For the selected date, 9 rows inherit that concern.

Closure needs:

1. Source evidence showing the symbol was eligible as of `2024-04-02`.
2. A reason why the row is not merely present because it survived until a later local cache date.
3. A row-level survivorship field and limitation note.
4. A policy for stock versus ETF rows under the legacy `etf_core` label.

## L. Factor Definition and Factor Observation Dependency Note

Factor definitions and factor observations are downstream of PIT universe/source closure for this selected sample. The 8-layer factor taxonomy remains the controlling structure; fixed 12 factors are not final.

The next worklist design may include placeholders for later factor dependency linkage, but it should not require factor observation closure before selected-sample universe and source evidence are organized.

## M. Event and Company Exposure Dependency Note

Event structured records and company exposure records are also downstream of the first PIT universe/source closure step. Existing schema fixtures are useful contract references, but they do not close evidence for `2024-04-02 / etf_core`.

The next worklist design should avoid blending event/exposure readiness into universe membership closure.

## N. Replay Evidence Bundle Preconditions

Before any replay evidence bundle design, the selected sample needs:

1. Row-level universe membership evidence.
2. Official status evidence or accepted not-applicable policy per field.
3. Source and raw-document lineage fields.
4. Hash, revision, and available-time metadata.
5. Reviewer authority and no-hit acceptance where needed.
6. Quality and limitation metadata.
7. Survivorship rationale.
8. Explicit separation from labels, training, models, stock-profile validation, paper expansion, buy-review, and trading.

## O. Row-Level Closure Checklist

For each `2024-04-02 / etf_core / symbol` row:

| checklist item | required |
|---|---|
| signal date | yes |
| universe label | yes |
| symbol | yes |
| instrument type | yes |
| exchange or market identifier | yes |
| source id and source type | yes |
| permission class | yes |
| raw reference or artifact reference | yes |
| source hash or source artifact hash preview policy | yes |
| local file hash if local file is used | yes |
| revision id | yes |
| evidence available time | yes |
| source publish/fetch/review times where relevant | yes |
| active/listed status evidence | yes |
| delisted/not-delisted evidence | yes |
| ST/no-ST or not-applicable policy | yes |
| suspension/trading status or not-applicable policy | yes |
| universe membership evidence | yes |
| survivorship rationale | yes |
| reviewer id, role, scope, and attestation | yes |
| quality status | yes |
| limitation note for every warning | yes |
| blocker reason for every blocked field | yes |

## P. Manual Review-Update Fields Needed Later

Later review-update CSVs may need fields such as:

```text
signal_date
universe_name
symbol
instrument_type
source_id
source_type
permission_class
raw_reference
source_hash_preview
source_hash_disclosure_level
local_file_hash_preview
revision_id
revision_id_type
available_time
available_time_timezone
listed_status_evidence
delisted_status_evidence
st_status_evidence
suspension_status_evidence
universe_membership_evidence
survivorship_rationale
reviewer_id
reviewer_role
reviewer_scope
reviewer_attestation
manual_review_status
quality_status
limitation_note
blocker_reason
```

Those fields are future review design context only. They are not created here.

## Q. What Can Be Handled by Later Report-Only Worklist Design

The selected next task can safely design:

1. A row-level evidence closure worklist schema.
2. Required fields and allowed statuses.
3. How to carry existing overlay/worklist blocker reasons forward.
4. How to separate stock and ETF policy rows under the legacy universe label.
5. How to mark context-only evidence versus closure-ready evidence.
6. How to preserve hash disclosure boundaries.
7. How to preserve reviewer no-hit boundaries.

## R. What Must Wait for Separate Pro / Pro Extended Design

Use a higher-level design review before:

1. Adjudicating ambiguous available-time evidence.
2. Creating source reliability scoring.
3. Defining subjective reviewer authority thresholds.
4. Deciding mixed stock/ETF universe policy for production use.
5. Turning review-update fields into a real validator.
6. Treating any row as PIT-admissible.
7. Moving toward replay input, replay execution, labels, training, model work, stock-profile validation, paper expansion, buy-review, or trading.

## S. Candidate Next Routes

| route | description | decision |
|---|---|---|
| A. Historical Replay PIT Evidence Closure Worklist Design for 2024-04-02 etf_core Report-Only v0.1 | Design a row-level worklist that organizes all missing evidence families without approving ingestion or replay. | Selected. |
| B. Historical Replay Selected Sample Official Status Evidence Packet Planning Report-Only v0.1 | Isolate listed/delisted/ST/suspension/universe membership evidence first. | Reserve if worklist design proves too broad. |
| C. Historical Replay Reviewer No-Hit Acceptance Planning for 2024-04-02 etf_core Report-Only v0.1 | Focus on no-hit acceptance policy. | Reserve because no-hit is one evidence family, not the whole closure surface. |
| D. Historical Replay Factor/Event/Exposure Readiness Audit for 2024-04-02 etf_core Report-Only v0.1 | Audit downstream factor/event/exposure readiness. | Defer until universe/source closure is organized. |
| E. Manual evidence collection outside the system before more engineering | Pause repo work for manual collection. | Not selected because clear local artifact lineage exists. |

## T. Selected Next Route

Selected route:

```text
Historical Replay PIT Evidence Closure Worklist Design for 2024-04-02 etf_core Report-Only v0.1
```

## U. Why Selected Route Is Safe

The worklist design route is safe because it organizes missing evidence without deciding that evidence is closed. It can define row-level fields, statuses, and blockers while preserving all downstream non-approval boundaries.

## V. What Must Not Be Bundled

The next task must not bundle:

1. PIT evidence closure.
2. PIT admissibility approval.
3. Active replay input creation.
4. Replay execution.
5. Replay decision freeze.
6. Forward-return label creation.
7. Training or evaluation dataset creation.
8. Metric computation.
9. Weight, formula, threshold, or model adjustment.
10. Stock-profile validation.
11. Paper expansion.
12. Buy-review approval.
13. Current-candidates execution.
14. Snapshot build.
15. Signal semantic mutation.
16. Broker, order, message, external API, LLM, or trading behavior.
17. Protected data writes.

## W. ChatGPT / Codex Mode Recommendation

Codex high is appropriate for the selected report-only worklist design because it must inspect existing local artifacts and write a bounded docs-only or manual-diagnostics-only design.

Use Pro or Pro Extended before any task that adjudicates ambiguous available-time evidence, source reliability, reviewer authority, production universe-profile policy, or any status that could be confused with replay input readiness.

## X. Commit / Tag / Source Recommendation

If accepted, this single docs-only plan can be committed normally. A tag is not recommended for this standalone report. A Project Source update is not recommended immediately unless the user accepts this as a roadmap-changing mainline decision.

## Y. Recommended Next Task

Recommended next task:

```text
Historical Replay PIT Evidence Closure Worklist Design for 2024-04-02 etf_core Report-Only v0.1
```

Scope: design a row-level closure worklist for the selected sample using existing local context only. It should not close evidence, approve PIT admissibility, run replay, create labels, train models, expand paper workflow, approve buy-review, or authorize trading.
