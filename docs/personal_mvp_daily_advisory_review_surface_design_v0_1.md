# Personal MVP Daily Advisory Review Surface Design v0.1

## A. Decision / Status

phase = personal_mvp_daily_advisory_review_surface_design  
decision = ready  
privacy_issue_stop = no  
docs_only = yes  
source_code_changed = no  
tests_changed = no  
runtime_changed = no  
selected_next_route = personal_mvp_daily_advisory_review_surface_implementation_planning_report_only

daily_advisory_review_surface_designed = yes  
single_symbol_drill_down_surface_designed = yes  
manual_review_checklist_designed = yes  
future_runtime_implementation_approved = no  
real_buy_review_approved = no  
buy_review_allowed = no  
trading_allowed = no  
broker_api_approved = no  
order_placement_approved = no  
message_delivery_approved = no  
active_replay_input_approved = no  
real_replay_execution_approved = no  
labels_training_model_stock_profile_paper_expansion_approved = no  
data_raw_processed_cache_writes_approved = no

Final design classification: `PERSONAL_MVP_DAILY_ADVISORY_REVIEW_SURFACE_DESIGN_READY_REPORT_ONLY`.

Final design verdict: `PERSONAL_MVP_DAILY_ADVISORY_REVIEW_SURFACE_DESIGN_READY_FOR_IMPLEMENTATION_PLANNING_REPORT_ONLY`.

## B. Current Accepted State

The current local state after the accepted personal MVP acceleration planning is:

- latest checkpoint anchor: `v1.82.0`;
- latest planning route: personal MVP advisory surface acceleration;
- selected next route: daily advisory review surface design;
- current emphasis: make existing advisory and paper-context artifacts easier to review before adding deeper Tiny PIT or source-package capability;
- current boundary: local, report-only planning with no new runtime behavior.

The existing advisory stack already includes signal semantics, signal advisory, single-symbol advisory, question-style single-symbol answers, advisory conversation, current-to-paper handoff, paper review workflow context, and research-status navigation. This design reuses those surfaces as review context only.

## C. Daily Advisory Review Purpose

The daily advisory review surface is a proposed local human review report for the personal/family MVP. Its purpose is to answer:

- what should be reviewed today;
- which symbols are watch, manual-review, blocked, demo, stale, or missing;
- why each symbol appeared;
- which local artifacts produced the context;
- what caveats, validity windows, and invalidation conditions apply;
- which manual checks remain before any downstream workflow.

It is not a decision engine. It is not a buy, sell, paper, broker, message, or trading authorization surface.

## D. Target User Journey

The intended local journey is:

```text
local artifacts
-> daily advisory review
-> single-symbol drill-down
-> manual notes / watch decision
-> optional paper workflow context
-> human confirmation
```

The daily review should be the first human-facing readout. It should summarize the latest available context and then route the user to deeper artifacts only when needed. It should reduce artifact sprawl without hiding safety flags or source caveats.

## E. Daily Review Report Schema

A future report-only daily review artifact may contain these top-level fields:

- `review_date`: date the user intends to review.
- `generated_at`: local report generation timestamp.
- `review_surface_version`: daily review contract version.
- `reviewer_id`: optional local reviewer label.
- `source_root`: local artifact root inspected by the future implementation.
- `latest_research_status_path`: path to the latest research-status report when present.
- `signal_run_id`: latest signal advisory run used for daily action grouping.
- `single_symbol_answer_run_ids`: answer artifacts referenced by the report.
- `advisory_conversation_run_ids`: conversation artifacts referenced by the report.
- `current_to_paper_handoff_id`: optional paper-context handoff reference.
- `paper_workflow_status_id`: optional paper workflow status reference.
- `artifact_freshness_status`: `CURRENT`, `STALE`, `MISSING`, or `MIXED`.
- `daily_review_status`: `READY_FOR_MANUAL_REVIEW`, `NO_LOCAL_ADVISORY_CONTEXT`, `STALE_CONTEXT_REVIEW_REQUIRED`, or `BLOCKED_CONTEXT_REVIEW_REQUIRED`.
- `advisory_action_counts`: counts by advisory label.
- `blocked_count`: count of rows requiring blocker review.
- `demo_count`: count of workflow-validation-only rows.
- `not_found_count`: count of requested symbols not found in local artifacts.
- `manual_confirmation_required`: always true for rows with reviewable context.
- `safety_flags`: all non-approval and no-side-effect flags.

Each symbol row should include:

- `symbol`;
- `name`;
- `instrument_type`;
- `universe_name`;
- `signal_date`;
- `decision_date`;
- `advisory_action`;
- `review_bucket`;
- `reason_summary`;
- `confidence_level_or_context`;
- `entry_condition_if_already_present`;
- `exit_condition_if_already_present`;
- `invalidation_condition`;
- `valid_until`;
- `risk_notes`;
- `data_source_notes`;
- `demo_mode`;
- `blocked_reason`;
- `stale_context_reason`;
- `source_artifact_paths`;
- `linked_single_symbol_answer_path`;
- `linked_conversation_report_path`;
- `linked_paper_context_path`;
- `next_manual_check`;
- `manual_note_placeholder`;
- `non_approval_statement`.

## F. Daily Review Section Layout

The report should be readable in this order:

1. Header and safety banner.
2. Current artifact snapshot.
3. Daily action bucket summary.
4. Manual-review candidates.
5. Watch-only symbols.
6. Blocked, stale, demo, and not-found context.
7. Single-symbol drill-down links.
8. Optional paper workflow context.
9. Manual checklist.
10. Explicit non-approvals and limitations.

The report should keep the first page compact. Deeper paths and raw artifact links belong after the summary tables.

## G. Single-Symbol Drill-Down Schema

A drill-down section should show one symbol at a time with:

- `symbol`;
- `name`;
- `user_question` when present;
- `parsed_intent` when sourced from advisory conversation;
- `latest_advisory_action`;
- `concise_answer`;
- `detailed_answer_path`;
- `source_artifact_type`;
- `source_artifact_path`;
- `source_run_id`;
- `decision_date`;
- `validity_context`;
- `invalidation_condition`;
- `reason_summary`;
- `risk_notes`;
- `data_source_notes`;
- `paper_context_summary`;
- `manual_confirmation_required`;
- `manual_note_placeholder`;
- `next_manual_check`;
- no-order, no-broker, no-message, and no-trading safety flags.

If the symbol is absent from local artifacts, the drill-down must render a not-found result and avoid inventing any recommendation.

## H. Manual Review Checklist

The daily review should include a compact manual checklist:

- Confirm the artifact date and source run.
- Confirm whether the row is demo, stale, blocked, or not found.
- Read the reason summary, caveats, risk notes, validity, and invalidation condition.
- Open the single-symbol answer when the daily row is not enough.
- Check optional paper workflow context only as local audit context.
- Record a manual note.
- Choose a local review bucket such as watch, continue review, reject for now, or no local action.
- Do not place orders, send messages, call brokers, or treat the report as trading permission.

The checklist is designed for human discipline, not automation.

## I. Advisory Action Wording Rules

The daily review must use conservative wording:

- `DEMO_ONLY`: workflow validation context only.
- `WATCH`: observe and review, not an instruction to buy or sell.
- `REVIEW_BUY_CANDIDATE`: manual review candidate only.
- `REVIEW_SELL_CANDIDATE`: manual review candidate only.
- `HOLD_REVIEW`: continue local review, not an instruction to hold a position.
- `NO_ACTION`: no local advisory action from the current artifact.
- `BLOCKED`: stop until the blocker is understood.
- `NOT_FOUND`: insufficient local evidence for the requested symbol.

No label should be rendered as a command, order, portfolio decision, or strategy-performance claim.

## J. Demo, Blocked, Not-Found, And Stale Handling

Demo rows should be visually separated and described as workflow validation only.

Blocked rows should show blocker reasons before any human interpretation. A blocked row should not be promoted into a review candidate by wording.

Not-found rows should say that no local artifact supports a review for the symbol. They should not infer a buy, sell, watch, or hold view.

Stale artifacts should remain visible with date context. The next action should be to refresh or inspect the relevant local artifact, not to act on stale context.

## K. Artifact Lineage And Report Links

The surface should prefer links over copied raw content. Useful lineage references include:

- latest research-status summary;
- signal advisory report and `signals.csv`;
- signal semantics provenance;
- single-symbol advisory report, JSON, CSV, and answer markdown;
- advisory conversation report;
- current-to-paper handoff metadata;
- paper workflow status report;
- paper review template or reviewed decision context when present.

The daily surface should not duplicate full source artifacts, secrets, private paths beyond already-local report references, or raw protected data.

## L. Research-Status Reuse

Research-status should remain the navigation layer for latest local artifact context. A future daily review implementation may read it to locate current advisory and paper-context outputs.

Research-status must not be treated as a trading decision engine. Its later workflow priority should remain intact, and the daily review should not overwrite broader workflow state.

## M. Signal Advisory Reuse

Signal advisory provides the best existing row-level source for the daily review. It already records advisory action, reason summary, validity, invalidation, risk notes, data notes, local alert preview path, and safety flags.

The daily surface should reuse these fields instead of creating new signal semantics. It should not reinterpret advisory labels into stronger language.

## N. Single-Symbol Advisory And Conversation Reuse

Single-symbol advisory and question-style answers provide the drill-down layer. They should be linked from daily rows where a matching answer exists.

Advisory conversation can be reused as a deterministic local question facade. It should remain a local parser and router, not a chat model, message sender, or execution layer.

## O. Paper Workflow Reuse

Paper workflow context should be optional and downstream. The daily review may show whether a row has paper-context artifacts, manual review notes, or watch-only local context.

Paper workflow context must not be described as strategy validation, real buy-review eligibility, or trading permission.

## P. Safety And Non-Approval Wording

Every daily review report should include these statements:

- This report is local advisory review context.
- Manual confirmation is required.
- No broker API is approved or invoked.
- No order placement is approved or invoked.
- No message delivery is approved or invoked.
- No active replay input is approved or emitted.
- No real replay execution is approved.
- No labels, training, model, stock_profile, or paper expansion is approved.
- No real buy-review is approved.
- `buy_review_allowed` remains false.
- `trading_allowed` remains false.
- No strategy performance validation is claimed.
- No writes to `data/raw`, `data/processed`, or `data/cache` are approved.

## Q. Future Implementation Boundary

A later implementation planning task may propose a local report-only daily readout command and focused tests. That later task should still be bounded to:

- reading existing local report artifacts;
- generating a local review report;
- preserving string symbols;
- showing stale, demo, blocked, and not-found context;
- preserving existing safety flags;
- avoiding any runtime side effects outside the approved report output path.

It must not implement broker integration, order placement, message delivery, real buy-review eligibility, active replay input, real replay execution, labels, training, model outputs, stock_profile validation, strategy-performance validation, or protected data writes.

## R. Bundlable Follow-Up Tasks

The smallest safe follow-up is implementation planning only. It may bundle:

- proposed future command contract;
- proposed future output files;
- exact row schema;
- artifact discovery rules;
- focused tests;
- CLI smoke plan;
- wording acceptance rules.

Runtime implementation should remain a separate task after the implementation plan is reviewed.

## S. Non-Bundlable Safety Gates

Do not bundle the following with the daily review surface:

- real buy-review approval;
- any change to `buy_review_allowed`;
- trading authorization;
- broker, order, message, or external API integration;
- active replay input;
- real replay execution;
- forward labels or future-label joins;
- training, model, active weights, active thresholds, stock_profile, or strategy-performance validation;
- source_hash, available_time, PIT, reviewer authority, or real package admissibility expansion;
- writes to `data/raw`, `data/processed`, or `data/cache`;
- Project Source package creation.

## T. Open Blockers

No blocker was found for moving to a report-only implementation planning task.

The main unresolved implementation details are:

- which artifact root a future daily readout should scan by default;
- whether daily review should require a latest signal advisory artifact or allow research-status-only navigation;
- how to display optional paper-context paths without implying downstream approval;
- whether a future implementation should create a single Markdown report only or Markdown plus CSV/JSON summary artifacts.

## U. Non-Blocking Notes

- The daily surface should optimize for a calm morning review: concise summary first, detail by link.
- Single-symbol drill-down should preserve existing answer wording instead of generating a stronger interpretation.
- Missing artifacts are normal in early MVP use and should be displayed clearly.
- The report should keep Chinese A-share and ETF symbols as text to preserve leading zeros.

## V. Project Source Recommendation

No immediate Project Source update is required for this design file alone unless it becomes the accepted planning anchor for the next milestone.

Do not create `docs/project_sources`. Do not mirror the repository. Do not upload `src/`, `tests/`, `outputs/`, `data/`, manual diagnostics, secrets, or virtual environments as ChatGPT Project Source.

## W. Recommended Next Task

`Personal MVP Daily Advisory Review Surface Implementation Planning Report-Only v0.1`

The next task should define the smallest future report-only implementation plan, proposed command shape, artifact schema, tests, safety checks, and validation commands. It should not implement runtime behavior unless a later task separately approves implementation.
