# Historical Replay Training Loop Re-Anchor / Next Execution Planning v0.1

phase = historical_replay_training_loop_reanchor_next_execution_planning  
decision = ready  
privacy_issue_stop = no  
docs_only = yes  
source_code_changed = no  
tests_changed = no  
runtime_changed = no  
latest_checkpoint = v1.83.0  
latest_checkpoint_commit = 46f634b  
latest_repo_commit = 4b80d87  
personal_mvp_advisory_refresh_branch_paused = yes  
historical_replay_mainline_reanchored = yes  
selected_next_route = historical_replay_sample_selection_and_pit_gap_audit_report_only

real_replay_execution_approved = no  
active_replay_input_approved = no  
forward_labels_created = no  
training_dataset_created = no  
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

This report re-anchors planning to the historical replay training mainline. It is docs-only and does not approve or run replay, labels, training, model, stock_profile, paper, current-candidates, snapshot, advisory, broker, order, message, API, or trading workflows.

Decision: ready for a report-only sample selection and point-in-time gap audit.

## B. Current Accepted State

The latest accepted checkpoint is v1.83.0 at 46f634b. The latest repository commit for this planning task is 4b80d87. External ChatGPT Project Source is updated to v1.83.0.

The Personal MVP Daily Advisory Review surface exists and works as a local report-only readout layer. The first local run succeeded as plumbing, but its upstream context was stale and DEMO_ONLY. The advisory refresh branch has now produced planning and command-guide context, but it is paused before execution.

## C. User Mainline Clarification

The project owner clarified the true mainline:

1. Historical data.
2. Point-in-time valid factors and events.
3. Prediction or replay decision.
4. Comparison against later actual stock returns.
5. Repeated evaluation.
6. Only later adjust factor weights, formulas, thresholds, or models.
7. Only after that test current, paper, and advisory workflows.

This report accepts that clarification as the controlling planning direction.

## D. Branch Map: Foundation / Engine / Display

Foundation:

- source registry;
- raw document store;
- reviewed local package metadata;
- point-in-time admissibility;
- factor definitions;
- event, company exposure, and factor observation contracts;
- replay evidence bundle contracts.

Engine:

- active replay input governance;
- replay decision generation or review-only decision formation;
- decision freeze;
- forward-return label creation after freeze;
- training/evaluation dataset creation;
- metric computation and error analysis;
- model or weight governance after evidence exists.

Display:

- Personal MVP Daily Advisory Review;
- signal advisory;
- single-symbol advisory;
- advisory conversation;
- optional paper workflow context.

The display layer is downstream of research evidence. It is not the training engine.

## E. Paused Branch: Personal MVP Advisory Refresh

The current/daily advisory refresh branch is paused, not abandoned. It remains useful later as a personal/family review surface after the historical replay loop produces reliable, governed context.

Paused means:

- do not run current-candidates from this branch now;
- do not build snapshots for advisory refresh now;
- do not mutate signal semantics now;
- do not refresh daily advisory artifacts now;
- keep the docs as future display-layer guidance.

## F. Historical Replay Training Mainline Definition

The historical replay training mainline is the path that asks:

Given only information available by a historical decision time, what decision would the system have made, and how did that decision compare with later realized returns and risks?

The mainline must preserve time ordering. Forward returns can only be attached after the decision is frozen. Model or formula changes can only be proposed after repeated evaluation evidence, not before.

## G. Minimum Closed-Loop Training Concept

Minimum loop:

1. Choose a historical decision date or window.
2. Choose a universe.
3. Confirm point-in-time valid data available by that date.
4. Confirm factor definitions are governed by the 8-layer taxonomy.
5. Confirm factor observations, events, and company exposures are available and time-valid.
6. Assemble a replay evidence bundle.
7. Generate a replay decision or review-only decision label.
8. Freeze the decision.
9. Join forward-return labels only after freeze.
10. Evaluate accuracy, payoff, drawdown, false positives, false negatives, and benchmark-relative performance.
11. Accumulate enough cases for error analysis.
12. Only later consider weights, thresholds, formulas, or models.

## H. Existing Workflow Inventory

Relevant command families observed in the repository:

- historical replay input gate validator and fixture views;
- minimal replay input package fixture smoke;
- active replay input promotion, acceptance, active-ready, final-review, emission, ready decision, and create flows;
- real and actual replay execution flows;
- replay decision freeze;
- forward-return label;
- training evaluation;
- metric evaluation, computation, and extension;
- training result planning and training result;
- model weight versioning;
- active model;
- stock_profile;
- source registry schema fixture;
- raw document store schema fixture;
- factor definition schema fixture;
- company exposure schema fixture;
- event structured schema fixture;
- factor observation schema fixture;
- replay evidence bundle schema fixture;
- replay decision schema fixture;
- forward return label schema fixture;
- reviewed local CSV replay prototype input contract fixture;
- Tiny PIT admissibility and reviewed package governance flows.

These workflows provide a broad scaffold, but this report does not claim they are ready for real closed-loop execution.

## I. Current Evidence and PIT Blockers

Current blockers before real replay training can start:

- a concrete historical date/window has not been selected for the next loop;
- a concrete universe has not been selected;
- point-in-time source and raw-document evidence may still be incomplete for selected rows;
- real factor observations are not yet proven ready for the selected sample;
- event and company exposure observations are not yet proven ready for the selected sample;
- replay evidence bundle readiness is not yet audited for the selected sample;
- active replay input must not be assumed from fixtures;
- forward-return labels must not be created before decisions are frozen;
- training and model adjustment must not start before governed labels and evaluation evidence exist.

## J. Factor Universe and 8-Layer Taxonomy Role

The 8-layer factor taxonomy remains the primary structure. Fixed 12 factors are not final.

For the next mainline step, the taxonomy should be used to:

- identify which factor families are needed for the selected sample;
- distinguish factor definitions from factor observations;
- prevent premature weights or thresholds;
- ensure event and company exposure features are represented as governed observations;
- support later error analysis across factor families.

The next audit should not optimize formulas. It should ask whether the selected historical sample has enough point-in-time valid observations to run a minimal closed loop later.

## K. Forward-Return Label Boundary

Forward-return labels are future information. They must be joined only after:

- replay input is accepted;
- decision evidence is assembled;
- replay decision or review-only label is produced;
- the decision is frozen;
- label horizon and benchmark rules are explicit.

This task does not create labels. It does not approve label creation.

## L. Evaluation and Error-Analysis Boundary

Evaluation should compare frozen decisions with later outcomes. Minimum evaluation families:

- directional accuracy;
- payoff or loss distribution;
- drawdown context;
- false positives;
- false negatives;
- benchmark-relative performance;
- industry or peer-relative context where available;
- sample-size and regime caveats.

Evaluation evidence is not strategy performance validation by itself. It is research feedback for repeated closed-loop learning.

## M. Weight / Formula / Model Timing Guard

Any future weight, threshold, formula, or model adjustment must wait for:

- point-in-time valid observations;
- frozen replay decisions;
- governed forward-return labels;
- evaluation evidence across enough samples;
- documented error analysis.

No weight changes, threshold changes, formula changes, model training, promoted model, production model, or active stock_profile expansion is approved here.

## N. Stock_Profile / Paper / Buy-Review Ladder

The ladder remains:

1. Historical replay evidence.
2. Frozen decisions and labels.
3. Evaluation and error analysis.
4. Governed weight/model proposals.
5. Stock_profile governance.
6. Paper workflow validation.
7. Real buy-review governance.
8. Separate trading/broker decisions, if ever approved.

The Personal MVP daily review surface belongs after earlier research governance. It is a display/readout layer, not authority.

## O. Candidate Next Routes

A. Historical Replay Training Minimal Closed-Loop Design Report-Only v0.1  
Defines the eventual minimal loop architecture.

B. Historical Replay Sample Selection and PIT Gap Audit Report-Only v0.1  
Selects a candidate historical date/window and universe, then audits whether point-in-time valid inputs and labels are sufficient.

C. Historical Factor/Event Observation Readiness Audit Report-Only v0.1  
Focuses on factor, event, and company exposure observation readiness before selecting a full replay sample.

D. Historical Replay Forward-Return Label Boundary Planning Report-Only v0.1  
Focuses only on label timing and leakage controls.

E. Pause engineering and manually define the first historical training experiment  
Defers repo work until the owner selects the first experiment manually.

## P. Selected Next Route

Selected route: B. Historical Replay Sample Selection and PIT Gap Audit Report-Only v0.1.

## Q. Why Selected Route Is Safe

This route is the smallest useful mainline step. It does not run replay or create labels. It asks the necessary prior question: which historical date/window and universe should be tested, and what point-in-time input gaps block a real closed loop?

It avoids premature formula or model work.

## R. What Must Not Be Bundled

The next task must not bundle:

- active replay input creation;
- replay execution;
- replay decision freeze;
- forward-label creation;
- training dataset creation;
- metric computation;
- model training;
- weight, threshold, or formula adjustment;
- stock_profile expansion;
- paper workflow expansion;
- real buy-review;
- current-candidates execution;
- snapshot build;
- signal semantics mutation;
- broker, order, message, API, or trading behavior;
- protected data writes.

## S. ChatGPT / Codex Mode Recommendation

ChatGPT Think is sufficient to review the next report-only prompt if it remains a bounded sample-selection and gap-audit task.

Codex high is appropriate to execute the next docs-only audit because it must inspect many existing workflow contracts and artifacts without running them.

Pro or Pro Extended should be used before any task that changes algorithmic semantics, selects live advisory behavior, starts model-training design, changes weights or thresholds, or blurs the boundary between research evaluation and trading decisions.

## T. Commit / Tag / Source Recommendation

Commit recommendation: commit this re-anchor document after review if accepted.

Tag recommendation: no tag for this standalone planning report.

Source update recommendation: no immediate Project Source update. A future update may be warranted after a selected historical sample and point-in-time gap audit becomes the accepted next mainline.

## U. Recommended Next Task

Historical Replay Sample Selection and PIT Gap Audit Report-Only v0.1.

Suggested goal:

Choose one or more candidate historical decision dates/windows and a universe, inspect only existing local artifacts and docs, and report whether point-in-time valid source, raw-document, factor, event, company exposure, replay evidence bundle, decision, and forward-label prerequisites are sufficient for a later minimal closed-loop replay training run.

