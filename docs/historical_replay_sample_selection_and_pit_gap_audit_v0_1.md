# Historical Replay Sample Selection and PIT Gap Audit v0.1

## A. Decision / Status

```text
phase = historical_replay_sample_selection_and_pit_gap_audit
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_checkpoint = v1.83.0
latest_checkpoint_commit = 46f634b
latest_repo_commit = 6347f94
historical_replay_mainline_active = yes
personal_mvp_advisory_refresh_branch_paused = yes
selected_historical_decision_date_or_window = 2024-04-02
selected_universe = etf_core
selected_next_route = Historical Replay PIT Evidence Gap Closure Plan for Selected Sample Report-Only v0.1

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

Final verdict: the project has enough local report and fixture context to select a first historical replay audit sample, but the selected sample is not replay-ready. The safe next move is a focused PIT evidence gap closure plan for the selected sample, not replay execution, labels, training, paper expansion, buy-review, or trading.

## B. Current Accepted State

The current formal checkpoint is v1.83.0 at commit `46f634b`. The current repo head inspected for this audit is `6347f94`, described as `v1.83.0-6-g6347f94`.

The recent personal MVP daily advisory review branch is useful for user-facing review surface work, but it is paused for this historical replay mainline decision. That advisory branch does not establish historical replay input readiness, PIT admissibility, forward-label readiness, model readiness, paper validation, buy-review readiness, or trading permission.

## C. Historical Replay Mainline Reminder

The historical replay mainline should move in this order:

1. Select a small historical sample.
2. Close PIT source, raw-document, source-hash, revision, available-time, reviewer, and quality gaps for that sample.
3. Assemble replay evidence only after the PIT gaps are explicit and reviewed.
4. Freeze replay decisions only after replay input readiness is separately approved.
5. Create forward-return labels only after the decision-time input is frozen.
6. Train, evaluate, and model only after labels and training datasets are governed.

This audit only covers the first step and the gap map around the second step.

## D. Candidate Historical Dates/Windows Found

| candidate date or window | universe | local evidence found | readiness read | audit note |
|---|---|---|---|---|
| 2024-04-02 | etf_core | Current-candidates backfill plans, execution manifest samples, PIT universe evidence worklists, overlay planning, and staging previews reference this date and universe. | Best first audit sample. | Most repeated concrete date with broad local workflow evidence. |
| 2024-04-09 and 2024-04-11 | etf_core | Backfill planning and PIT evidence worklist samples include these dates. | Secondary candidates. | Useful as follow-on dates after the first sample. |
| 2024-01-02 through 2024-05-06 | etf_core | A broader backfill planning range exists. | Too broad for the first gap audit. | Better kept as a later window after one-date handling is proven. |
| 2024-04-02 | stock_core / 000001 | One-row material evidence and checklist-pass preview artifacts exist for this target. | Useful one-row comparison only. | Strict requirement gaps remain, so this is not the first broad sample. |
| 2024-05-20 | mixed advisory display context | Signal/advisory artifacts exist, including stale review context. | Not selected. | This belongs to the personal MVP advisory display branch, not the historical replay training mainline. |

## E. Candidate Universes Found

`etf_core` is the best first universe candidate because it appears across backfill plans, execution manifests, PIT universe evidence worklists, and overlay planning. The evidence is still not sufficient for execution, but it is the most coherent sample surface for a gap audit.

`stock_core` appears in the one-row `000001` material-evidence and checklist preview flow. It is valuable as a targeted evidence-quality comparison, but current strict gaps make it less suitable as the first replay sample universe.

Synthetic fixture universes appear in schema fixture artifacts for replay decisions, labels, events, exposures, and evidence bundles. They are contract references only and must not be selected as real historical replay samples.

## F. Candidate Sample Comparison Table

| sample | strengths | blocking gaps | recommendation |
|---|---|---|---|
| 2024-04-02 / etf_core | Broadest local evidence footprint, repeated across planning and PIT review artifacts. | PIT source completeness, official date-specific evidence, active/delisted/ST checks, survivorship rationale, source lineage, available-time proof. | Select for gap closure planning. |
| 2024-04-09 or 2024-04-11 / etf_core | Same workflow family as 2024-04-02. | Less central as the first audit anchor. | Reserve as follow-on validation dates. |
| 2024-01-02 through 2024-05-06 / etf_core | Useful future training window. | Too broad before single-date PIT closure is proven. | Defer. |
| 2024-04-02 / stock_core / 000001 | Strong one-row diagnostics context. | Existing strict gaps and remaining blockers. | Use as comparison, not first selected sample. |
| 2024-05-20 advisory context | User-facing display branch context. | Stale/demo advisory context and not historical replay mainline. | Exclude from replay sample selection. |

## G. Selected Audit Sample

Selected sample:

```text
historical_decision_date = 2024-04-02
universe = etf_core
selection_reason = strongest repeated local evidence footprint and smallest safe first sample
```

This selection is for audit and planning only. It does not create replay input, active input, replay execution, replay decisions, frozen decisions, forward labels, training data, metric results, model outputs, stock-profile readiness, paper validation, buy-review permission, or trading permission.

## H. Why the Selected Sample Is or Is Not Ready

The selected sample is ready for PIT gap closure planning. It is not ready for replay execution.

It is attractive because a single date and universe can be traced through multiple local planning and PIT worklist artifacts. It is blocked because the available artifacts are not yet a closed, accepted, date-specific PIT evidence package with complete source lineage, raw-document lineage, available-time evidence, revision controls, reviewer acceptance, and downstream safety boundaries.

## I. PIT Source / Raw-Document / Available-Time Gap Audit

Known gap categories for the selected sample:

| gap area | current state | blocker |
|---|---|---|
| Accepted PIT universe input | Planning and evidence worklist context exists. | Needs explicit accepted PIT universe evidence for the selected date and universe. |
| Source registry | Schema and fixture history exists. | No production source registry state or real source permission state is established by this audit. |
| Raw documents | Raw-document schema fixture history exists. | No selected-sample raw-document bundle is accepted as PIT-valid. |
| Source hashes and revision ids | Several contract and preflight layers exist. | Selected-sample source hashes, revision ids, and local-file hashes still need a closed gap plan. |
| Available time | Contract, planning, and preflight history exists. | Date-specific available-time proof still needs review and closure. |
| Active/delisted/ST status | Prior one-row and PIT evidence tasks identified strict status needs. | Selected sample still needs official date-specific evidence. |
| Survivorship | Prior planning identified survivorship as a strict gap family. | Selected sample still needs survivorship rationale. |
| Reviewer no-hit acceptance | Prior artifacts define reviewer no-hit context. | Selected sample still needs accepted reviewer no-hit handling where official sources have no hit. |

## J. Factor Definition Readiness

Factor definition schema fixture work exists and supports the broader eight-layer taxonomy direction. That work is a contract and governance surface only. For the selected sample, no active factor-definition library has been accepted as decision-time input. The next gap closure plan should identify the exact factor definitions needed for the first replay evidence bundle and keep them separate from factor observations, labels, model weights, and advisory scores.

## K. Factor Observation Readiness

Factor observation schema fixture artifacts exist, including synthetic rows around April 2024. Those fixtures are not selected-sample observations and do not prove that factor values for `2024-04-02 / etf_core` were available at the replay decision time. The blocker is PIT-valid factor observation evidence with source lineage, available-time proof, revision information, and no future-label leakage.

## L. Event Structured Readiness

Event structured schema fixture artifacts exist as report-only contract surfaces. They do not create production event ingestion, accepted event rows, source permission, event publish-time proof, or selected-sample replay evidence. The blocker is a selected-sample event evidence plan that distinguishes event date, publish time, available time, fetched time, review time, and revision history.

## M. Company Exposure Readiness

Company exposure schema fixture work exists, including synthetic April 2024 examples. It does not create production exposure mappings, active company exposure state, or selected-sample admissible exposures. The blocker is date-specific exposure lineage and a rule for how exposure records may enter a replay evidence bundle without implying stock-profile validation or buy-review readiness.

## N. Replay Evidence Bundle Readiness

Replay evidence bundle schema fixture work exists as a contract. No real selected-sample replay evidence bundle is accepted by this audit. A future bundle must be assembled only after the selected sample has accepted PIT universe, source, raw-document, factor, event, exposure, reviewer, and quality evidence.

## O. Replay Decision / Freeze Readiness

Replay decision schema fixture and replay decision freeze workflows exist in the repository history, but this audit does not create a replay decision or freeze any decision. A replay decision freeze would be unsafe until a selected-sample evidence bundle is accepted through a separate exact approval path.

## P. Forward-Return Label Readiness

Forward-return label schema fixture and later label workflow history exist. This audit does not create labels. Forward labels must remain downstream of a frozen decision-time input and must not be joined into decision-time inputs.

## Q. Training / Evaluation / Model Timing Guard

Training, evaluation, metric computation, model weight/versioning, and active-model governance history exists. None of it should be advanced from this audit. The selected sample is still at the PIT evidence gap stage. Training, metrics, model weights, thresholds, probabilities, and advisory predictions must remain blocked until decision-time inputs are frozen and labels are separately approved.

## R. Stock Profile / Paper / Buy-Review Boundary

The selected sample does not create stock profiles, stock-profile validation, paper validation, real buy-review eligibility, user recommendation authority, broker authority, order authority, message authority, or trading authority. Personal MVP advisory review surfaces are user-facing review tools and do not replace replay evidence, model validation, or buy-review governance.

## S. Open Blockers

1. Accepted PIT universe evidence for `2024-04-02 / etf_core`.
2. Date-specific official/public evidence for active, delisted, ST, suspension, and similar eligibility constraints.
3. Source registry and raw-document lineage for selected-sample evidence.
4. Source hash, local file hash, revision id, and available-time closure.
5. Reviewer authority and reviewer no-hit acceptance where official sources are unavailable.
6. Survivorship rationale for the selected date and universe.
7. PIT-valid factor definitions and factor observations.
8. PIT-valid event and company exposure evidence.
9. Replay evidence bundle assembly policy for the selected sample.
10. Explicit separation from forward labels, training data, model artifacts, stock profiles, paper validation, buy-review, and trading.

## T. Non-Blocking Notes

The repository has a large amount of useful fixture and governance context. That context is valuable for designing the next gap-closure report, but fixture readiness should not be read as real input readiness.

The one-row `2024-04-02 / stock_core / 000001` evidence flow remains useful as a comparison case because it has explicit strict-gap language. It should not displace `2024-04-02 / etf_core` as the first universe-level audit sample.

## U. Candidate Next Routes

| route | description | risk | decision |
|---|---|---|---|
| A. Historical Replay Closed-Loop Design for selected sample | Design the whole replay loop from evidence to labels and training. | Too broad while PIT gaps remain. | Defer. |
| B. Historical Replay PIT Evidence Gap Closure Plan for selected sample | Plan exactly how to close source, raw-document, available-time, reviewer, quality, and eligibility gaps for `2024-04-02 / etf_core`. | Low if kept report-only. | Select. |
| C. Factor/Event/Exposure Readiness Drilldown | Focus only on factor, event, and exposure schema-to-real-input gaps. | Useful but downstream of PIT source closure. | Reserve. |
| D. One-row stock_core comparison audit | Use `000001` one-row artifacts to compare strict-gap language. | Too narrow for first universe sample. | Reserve. |

## V. Selected Next Route

Selected next route:

```text
Historical Replay PIT Evidence Gap Closure Plan for Selected Sample Report-Only v0.1
```

This should stay report-only and should focus on closing the evidence map for `2024-04-02 / etf_core`.

## W. Why the Selected Route Is Safe

The selected route is safe because it remains at the planning and gap-closure layer. It does not ask for replay execution, decision freeze, labels, training, metrics, models, stock-profile validation, paper validation, buy-review permission, current-candidates execution, snapshot creation, signal semantic changes, broker calls, orders, messages, or trading.

## X. What Must Not Be Bundled

The next task must not bundle any of the following:

1. Active replay input creation.
2. Replay execution.
3. Replay decision freeze.
4. Forward-return label creation.
5. Training or evaluation dataset creation.
6. Metric computation.
7. Model training, weights, thresholds, predictions, or probabilities.
8. Stock-profile validation.
9. Paper validation expansion.
10. Real buy-review eligibility.
11. Current-candidates execution.
12. Snapshot creation.
13. Signal semantic mutation.
14. Broker, order, message, external API, LLM, or trading behavior.
15. Writes to raw, processed, or cache data areas.

## Y. ChatGPT / Codex Mode Recommendation

Use ChatGPT review or Codex high for the next report-only gap closure plan. Pro Extended is not required unless the next task introduces subjective available-time adjudication, source reliability scoring, reviewer authority policy, or any downstream status that could be confused with replay input readiness.

## Z. Commit / Tag / Source Recommendation

This audit creates one docs-only report. If review accepts it, a normal docs commit is reasonable. A tag is not recommended for this single planning audit unless it becomes part of a broader checkpoint package. A Project Source update is not immediately recommended unless this report changes the active roadmap or source boundaries after review.

## AA. Recommended Next Task

Recommended next task:

```text
Historical Replay PIT Evidence Gap Closure Plan for Selected Sample Report-Only v0.1
```

Scope for that task: selected sample `2024-04-02 / etf_core`; report-only; no runtime changes; no data writes; no replay execution; no labels; no training; no model; no stock-profile, paper, buy-review, or trading expansion.
