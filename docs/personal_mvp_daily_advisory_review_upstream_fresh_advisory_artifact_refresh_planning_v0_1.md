# Personal MVP Daily Advisory Review Upstream Fresh Advisory Artifact Refresh Planning v0.1

phase = personal_mvp_daily_advisory_review_upstream_fresh_advisory_artifact_refresh_planning  
decision = ready  
privacy_issue_stop = no  
docs_only = yes  
source_code_changed = no  
tests_changed = no  
runtime_changed = no  
latest_checkpoint = v1.83.0  
latest_checkpoint_commit = 46f634b  
latest_post_runbook_commit = 43554f0  
first_local_run_id = 1f972084211d  
first_local_run_status = DAILY_ADVISORY_REVIEW_STALE_CONTEXT_REVIEW_REQUIRED  
first_local_run_health_status = WARN  
first_local_run_row_count = 9  
first_local_run_all_rows_demo_only = yes  
first_local_run_all_rows_stale = yes  
selected_next_route = personal_mvp_upstream_advisory_artifact_refresh_command_guide_report_only

real_buy_review_approved = no  
buy_review_allowed = no  
trading_allowed = no  
broker_api_approved = no  
order_placement_approved = no  
message_delivery_approved = no  
external_api_or_llm_approved = no  
active_replay_input_approved = no  
real_replay_execution_approved = no  
labels_training_model_stock_profile_paper_expansion_approved = no  
strategy_performance_validation_approved = no  
current_candidates_execution_approved = no  
snapshot_build_approved = no  
signal_semantics_mutation_approved = no  
data_raw_processed_cache_writes_approved = no  
docs_project_sources_created = no

## A. Decision / Status

This is a docs-only planning report. It plans how to refresh upstream local advisory artifacts before another Personal MVP Daily Advisory Review run. It does not execute any upstream workflow, create fresh candidates, build snapshots, mutate advisory semantics, expand paper workflow scope, or change any runtime behavior.

Decision: ready for a separate report-only command guide task.

## B. Current Accepted State

The accepted checkpoint is v1.83.0 at commit 46f634b. Two post-checkpoint documentation commits are present, ending at 43554f0. The Personal MVP Daily Advisory Review surface is report-only, diagnostic-only, local-only human review context. It aggregates existing local advisory artifacts into a daily readout, manual review checklist, and drilldown index.

The daily review surface is not an upstream data refresh workflow. It must not be treated as a command that repairs stale artifacts, creates non-demo signals, changes advisory labels, expands paper workflow authority, or approves real actions.

## C. First Local Run Interpretation

The first local run inspected in this planning task is `1f972084211d`.

- status: DAILY_ADVISORY_REVIEW_STALE_CONTEXT_REVIEW_REQUIRED
- health_status: WARN
- review_date: 2026-07-05
- row_count: 9
- demo_count: 9
- stale_artifact_count: 9
- review_buy_candidate_count: 0
- review_sell_candidate_count: 0
- watch_count: 0
- warning_count: 1
- recommended next manual action: Review stale artifact context before relying on this daily readout.

Interpretation: the daily review command succeeded as a workflow surface, but its advisory content is stale and demo-only. It validates display and review plumbing. It does not provide fresh non-demo advisory context.

## D. Upstream Artifact Lineage Found

The daily review rows point to a signal advisory artifact:

- source_run_id: `2921a18906bf`
- source_artifact_path: `outputs\reports\signals\2921a18906bf\signals.csv`
- decision_date / signal_date: 2024-05-20
- valid_until: 2024-05-21
- row actions: DEMO_ONLY
- stale reason: Artifact freshness requires review before use.

Optional linked paper context is present:

- `outputs\reports\paper_trading\workflow_status\6f3a1d037792\paper_workflow_status_report.md`

The dashboard snapshot also shows the same advisory family as stale context: current-candidates health, signal semantics status, signal advisory status, single-symbol advisory, advisory conversation, market-update handoff, current-to-paper handoff, and paper workflow status all remain local context, not authority.

## E. Why WARN / Stale Happened

The daily review was run on 2026-07-05 while the linked signal rows are dated 2024-05-20 and valid only through 2024-05-21. With a freshness threshold, that context is stale. The rows are also explicitly demo-only. Therefore WARN is the correct status: the local review packet exists, but the upstream content cannot be interpreted as fresh advisory context.

## F. Demo-Only Interpretation

DEMO_ONLY remains workflow validation only. It does not mean a symbol is attractive, eligible, approved, ready for paper action, or suitable for trading.

WATCH means observe/review only. REVIEW_BUY_CANDIDATE remains manual-review-only. REVIEW_SELL_CANDIDATE remains manual-review-only.

Fresh local advisory context, if later produced, still must not be trading authorization.

## G. Existing Command / Workflow Inventory

Existing command families relevant to an upstream refresh are:

- `current-candidates`: generate local current/as-of-date candidates from point-in-time data.
- `current-candidates-index`, `current-candidates-health`: discover and safety-check current-candidate artifacts.
- `signal-semantics`: map local candidate or scored rows to advisory semantics labels.
- `signal-semantics-index`, `signal-semantics-health`, `signal-semantics-status`: inspect semantics artifacts.
- `signal-advisory`: build local advisory signals and optional alert preview from a candidates CSV.
- `signal-advisory-index`, `signal-advisory-health`, `signal-advisory-status`: inspect signal advisory artifacts.
- `single-symbol-advisory`: build focused local symbol review from existing artifacts.
- `single-symbol-advisory-index`, `single-symbol-advisory-health`, `single-symbol-advisory-status`: inspect focused advisory artifacts.
- `advisory-conversation`: build local advisory conversation context from existing artifacts.
- `advisory-conversation-index`, `advisory-conversation-health`, `advisory-conversation-status`: inspect conversation artifacts.
- `current-to-paper`, `current-to-paper-review`, and paper workflow status commands: optional paper-context plumbing only, not a requirement for fresh daily advisory display.
- `personal-mvp-daily-advisory-review`: aggregate existing artifacts into the daily surface.

The command inventory suggests that refreshing upstream local advisory artifacts can likely be documented using existing commands. Running those commands is a separate task because candidate generation and any snapshot dependency must be explicitly scoped.

## H. Fresh Artifact Requirements

A future fresh advisory refresh must define:

1. Target review date and universe.
2. Whether the goal is demo workflow validation or non-demo local review context.
3. Required candidate source, including snapshot and data-quality preconditions.
4. Candidate artifact health requirements before advisory generation.
5. Advisory semantics profile and provenance requirements.
6. Signal advisory output requirements, including no auto-order and no broker flags.
7. Optional single-symbol advisory or conversation drilldowns.
8. Optional paper context, limited to manual workflow context.
9. Daily review rerun inputs and stale threshold.
10. Manual reviewer checklist for interpreting the refreshed packet.

Fresh artifacts must include clear source lineage, review date, decision date, validity window, manual-confirmation requirement, and safety flags.

## I. Non-Demo Advisory Boundary

Non-demo local advisory context can only mean structural human-review labels. It must not become real buy-review eligibility, automatic approval, model performance validation, paper expansion, message delivery, or trading authorization.

If non-demo labels appear later, they still require manual review. They must preserve no-live-trading, no-broker, no-auto-order, no-message-sent, and manual-confirmation-required semantics.

## J. Data / Source / Output Boundary

This planning task does not approve data preparation, cache mutation, snapshot creation, candidate generation, or any protected data write. A later execution task must state exactly which local inputs it reads and which report-only outputs it writes.

Protected writes remain closed for `data/raw`, `data/processed`, and `data/cache`. Current-candidates execution and snapshot building remain unapproved here.

## K. Safety and Non-Approval Audit

This planning task does not approve current-candidates execution. This planning task does not approve snapshot building. This planning task does not approve signal_semantics mutation. This planning task does not approve real buy-review.

No broker API, order placement, message sending, external API call, LLM call, replay execution, labels/training/model workflow, stock_profile workflow, paper expansion, strategy-performance validation, active replay input, or trading workflow is approved.

## L. Candidate Next Routes

A. Personal MVP Upstream Advisory Artifact Refresh Command Guide Report-Only v0.1  
Purpose: document the exact existing-command sequence, prerequisites, and stop gates for refreshing local upstream advisory artifacts without executing it.

B. Personal MVP Fresh Local Advisory Artifact Refresh Implementation Planning Report-Only v0.1  
Purpose: plan new implementation only if existing commands are insufficient or if a safer orchestration wrapper is required.

C. Personal MVP Daily Advisory Review First Local Run Feedback Note Report-Only v0.1  
Purpose: document user-facing interpretation of the first stale/demo run.

D. Pause and manually collect/prepare current upstream artifacts outside the system  
Purpose: defer system changes and rely on manual artifact preparation.

E. Defer fresh/non-demo advisory and continue using daily review only as demo plumbing validation  
Purpose: avoid refresh complexity entirely.

## M. Selected Next Route

Selected route: A. Personal MVP Upstream Advisory Artifact Refresh Command Guide Report-Only v0.1.

This is the smallest safe next route because existing commands appear to cover the component workflows, but the system needs a precise, reviewed command guide before any execution. The guide should separate planning, safety checks, candidate generation, advisory generation, optional drilldown, optional paper context, and daily review rerun.

## N. Why Selected Route Is Safe

The selected route is docs-only. It does not run current-candidates, build snapshots, mutate signal semantics, generate advisory signals, or rerun the daily review. It narrows ambiguity before execution and helps prevent stale/demo artifacts from being mistaken for fresh local advisory context.

## O. What Must Not Be Bundled

The next route must not bundle:

- current-candidates execution;
- snapshot building;
- signal_semantics mutation;
- signal advisory generation;
- single-symbol advisory generation;
- advisory conversation generation;
- paper workflow execution or expansion;
- daily advisory review execution;
- data/raw, data/processed, or data/cache writes;
- real buy-review, strategy-performance validation, broker/API/order/message behavior, or trading.

## P. ChatGPT / Codex Mode Recommendation

ChatGPT Think is sufficient to review the command-guide prompt because the next step is a bounded report-only planning guide. Codex high is appropriate to create the guide from local docs and CLI inspection. Pro or Pro Extended is only needed if the scope expands into non-demo advisory semantics, active candidate generation policy, snapshot/data refresh policy, or any real buy-review/trading boundary.

## Q. Commit / Tag / Source Recommendation

Commit recommendation: commit this planning document only after user/ChatGPT review if the content is accepted.

Tag recommendation: no tag for this docs-only planning report unless it becomes part of a later accepted checkpoint package.

Source update recommendation: no immediate Project Source update. A future source update may be useful only after an accepted refresh guide or implementation checkpoint changes the durable roadmap.

## R. Recommended Next Task

Personal MVP Upstream Advisory Artifact Refresh Command Guide Report-Only v0.1.

The next task should create a docs-only command guide that lists exact existing commands, required inputs, expected outputs, stop gates, and safety confirmations for refreshing local upstream advisory artifacts before a future daily advisory review rerun. It must not execute the refresh.

