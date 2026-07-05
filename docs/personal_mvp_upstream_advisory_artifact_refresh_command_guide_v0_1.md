# Personal MVP Upstream Advisory Artifact Refresh Command Guide v0.1

phase = personal_mvp_upstream_advisory_artifact_refresh_command_guide  
decision = ready  
privacy_issue_stop = no  
docs_only = yes  
source_code_changed = no  
tests_changed = no  
runtime_changed = no  
latest_checkpoint = v1.83.0  
latest_checkpoint_commit = 46f634b  
latest_upstream_refresh_planning_commit = ce1ae31  
first_local_run_id = 1f972084211d  
first_local_run_all_rows_demo_only = yes  
first_local_run_all_rows_stale = yes  
selected_next_route = personal_mvp_upstream_advisory_artifact_refresh_execution_plan_report_only

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

This guide is ready as docs-only command guidance. It does not approve execution. It does not run, trigger, or validate any upstream refresh workflow.

Any command sequence below is a future template only and must not be run until separately approved by the user after ChatGPT review.

## B. Audience and Purpose

This guide is for a future operator who wants to refresh upstream local advisory artifacts before rerunning the Personal MVP Daily Advisory Review surface.

The purpose is to make the future refresh path explicit: prerequisites, command families, expected outputs, stop gates, and safety confirmations. The guide is not implementation and not execution.

## C. Why This Guide Exists

The first local daily advisory review run proved that the daily review surface can aggregate local advisory context into a compact review packet. It also showed that the current upstream context is stale and demo-only.

The daily review command does not repair stale upstream artifacts. A separate reviewed refresh path is needed before any future daily readout can be interpreted as fresh local advisory context.

## D. First Local Run Summary

First local run:

- run id: `1f972084211d`
- status: `DAILY_ADVISORY_REVIEW_STALE_CONTEXT_REVIEW_REQUIRED`
- health status: `WARN`
- row count: 9
- all rows demo-only: yes
- all rows stale: yes
- source signal run: `2921a18906bf`
- source signal date: `2024-05-20`
- source valid-until date: `2024-05-21`

Interpretation: technically successful surface generation, but stale demo-only context. DEMO_ONLY remains workflow validation only.

## E. Upstream Refresh Concept

A future refresh should create or select fresh upstream local advisory artifacts, inspect their health, then rerun the daily review surface against those refreshed artifacts.

The conceptual flow is:

1. Confirm snapshot/data prerequisites.
2. Generate or select current local candidates.
3. Inspect candidate artifacts.
4. Generate advisory semantics context if needed.
5. Generate local signal advisory artifacts.
6. Optionally generate single-symbol or conversation drilldowns.
7. Optionally refresh paper-context artifacts.
8. Rerun the daily advisory review surface.
9. Inspect the daily review output.

This guide does not approve any of those steps for execution.

## F. Existing Command Inventory

Observed command families:

- `current-candidates`: generate local current/as-of-date candidates from point-in-time data.
- `current-candidates-index`: discover candidate artifact folders.
- `current-candidates-health`: check candidate artifact health.
- `signal-semantics`: map candidate or scored rows to advisory semantics labels.
- `signal-semantics-index`, `signal-semantics-health`, `signal-semantics-status`: inspect semantics artifacts.
- `signal-advisory`: build local advisory signals and optional alert preview from `candidates.csv`.
- `signal-advisory-index`, `signal-advisory-health`, `signal-advisory-status`: inspect advisory artifacts.
- `single-symbol-advisory`: build focused local review for one symbol.
- `single-symbol-advisory-index`, `single-symbol-advisory-health`, `single-symbol-advisory-status`: inspect single-symbol artifacts.
- `advisory-conversation`: build deterministic local conversation context over existing advisory artifacts.
- `advisory-conversation-index`, `advisory-conversation-health`, `advisory-conversation-status`: inspect conversation artifacts.
- `current-to-paper`: optional local handoff to paper-context plumbing.
- `paper-workflow-status`: optional local paper workflow status context.
- `personal-mvp-daily-advisory-review`: aggregate existing local advisory artifacts into a daily review packet.
- `personal-mvp-daily-advisory-review-index`, `personal-mvp-daily-advisory-review-health`, `personal-mvp-daily-advisory-review-status`: inspect daily review artifacts.

## G. Prerequisites Before Any Execution

Before a future operator runs any refresh command, collect and paste back to ChatGPT:

- target review date;
- target universe;
- intended mode: demo validation or non-demo local review context;
- latest git status and commit;
- local data/snapshot source intended for candidate generation;
- whether existing snapshot-quality and data-quality artifacts are current;
- whether any command would write to protected data locations;
- whether the user explicitly approves running current-candidates;
- whether the user explicitly approves any snapshot build or snapshot usage;
- whether the user explicitly approves advisory generation;
- whether paper context is needed or should be excluded;
- required stop-gate responses.

If any prerequisite is unknown, stop before execution planning becomes execution.

## H. Proposed Command Sequence Template

Future template only. Do not run until separately approved.

```text
1. Confirm repository and local data state.
2. Confirm snapshot/data prerequisites and stop gates.
3. If approved, run current-candidates for the target date and universe.
4. If approved, run current-candidates index and health checks.
5. If approved, run signal-semantics only when an explicit semantics artifact is needed.
6. If approved, run signal-advisory on the selected candidates.csv.
7. If approved, run signal-advisory index and health checks.
8. If approved, optionally run single-symbol-advisory for selected symbols.
9. If approved, optionally run advisory-conversation for selected questions.
10. If approved, optionally refresh paper-context status.
11. If approved, rerun personal-mvp-daily-advisory-review.
12. Inspect daily review rows, checklist, summary, metadata, and safety flags.
```

The future command guide should use concrete paths only after an approved execution plan identifies the actual artifacts.

## I. Current-Candidates Stage Guidance

Future template only. Do not run until separately approved.

Potential command form:

```text
python -m quant_replay_system.cli current-candidates --date <YYYY-MM-DD> --universe <universe_name> --top <N> --selection-profile <default-or-demo>
```

Optional flags include `--output-dir` and `--config`.

Expected outputs, if later approved and run:

- a current-candidates artifact folder;
- `candidates.csv`;
- metadata;
- report artifacts;
- possible scored or factor context depending on existing workflow behavior.

Stop before this stage unless the user explicitly approves current-candidates execution for the target date and universe.

## J. Snapshot / Data Prerequisite Guidance

Current-candidates may depend on local snapshot/data prerequisites. This guide does not approve snapshot building, data preparation, cache mutation, or protected data writes.

Before any future current-candidates run, verify:

- target date is correct;
- universe name is correct;
- snapshot-quality status is acceptable;
- data-quality status is acceptable;
- required local data already exists;
- no step would write to protected data locations without separate approval;
- no external data, broker, order, message, or API behavior is involved.

If snapshot-quality is missing, stale, failed, or unclear, stop. If a snapshot build would be needed, stop and request a separate snapshot/data planning task.

## K. Signal-Semantics Stage Guidance

Future template only. Do not run until separately approved.

`signal-advisory` can use shared semantics internally, so a standalone `signal-semantics` run is optional unless an explicit semantics audit artifact is needed.

Potential command form:

```text
python -m quant_replay_system.cli signal-semantics --input <candidates.csv> --input-type candidates --metadata <metadata.json> --profile <profile>
```

Optional flags include `--snapshot-quality-status`, `--data-quality-status`, `--output-dir`, and `--config`.

Stop before this stage if the semantics profile is unclear, if data/snapshot quality is failed or unknown, or if anyone expects semantics output to approve trades. REVIEW_BUY_CANDIDATE and REVIEW_SELL_CANDIDATE remain manual-review-only labels.

## L. Signal-Advisory Stage Guidance

Future template only. Do not run until separately approved.

Potential command form:

```text
python -m quant_replay_system.cli signal-advisory --candidates <candidates.csv> --candidate-report <current_candidates_report.md> --metadata <metadata.json> --alert-preview
```

Optional flags include `--output-dir` and `--config`.

Expected outputs, if later approved and run:

- `signals.csv`;
- signal advisory report;
- metadata;
- optional local alert preview markdown.

The alert preview is local markdown only. It is not sent as a message. Signal advisory artifacts must preserve manual confirmation, no-auto-order, no-live-trading, and no-broker semantics.

## M. Single-Symbol / Advisory-Conversation Optional Stage Guidance

Future template only. Do not run until separately approved.

Single-symbol command form:

```text
python -m quant_replay_system.cli single-symbol-advisory --symbol <symbol> --signals <signals.csv> --metadata <metadata.json> --alert-preview --question-style --question "<local question>"
```

Alternative inputs include `--candidates`, `--scored-dataset`, or `--factor-dataset`.

Conversation command form:

```text
python -m quant_replay_system.cli advisory-conversation --question "<local question>" --signals <signals.csv> --metadata <metadata.json>
```

These stages are optional local review aids. They do not call an LLM, send a message, fetch data, place orders, connect to brokers, or convert review labels into executable guidance.

## N. Optional Paper-Context Guidance

Future template only. Do not run until separately approved.

Paper context is optional for the daily advisory review. If included, it should remain manual workflow context only.

Potential command forms:

```text
python -m quant_replay_system.cli current-to-paper --candidates <candidates.csv> --paper-date <YYYY-MM-DD>
python -m quant_replay_system.cli paper-workflow-status --root outputs/reports --decision-date <YYYY-MM-DD> --universe <universe_name>
```

Stop before paper context if the goal is only to refresh advisory artifacts. Do not bundle paper workflow expansion into a simple advisory refresh.

## O. Daily Review Rerun Guidance

Future template only. Do not run until separately approved.

Potential command form:

```text
python -m quant_replay_system.cli personal-mvp-daily-advisory-review --root outputs/reports --review-date <YYYY-MM-DD> --stale-after-days <N>
```

Optional flags include `--output-dir`, `--max-symbols`, `--include-paper-context`, and `--no-include-paper-context`.

Expected outputs, if later approved and run:

- daily review report;
- daily review rows CSV;
- summary CSV;
- manual review checklist;
- metadata;
- safety flags;
- single-symbol drilldown index.

After rerun, inspect the status, health status, row counts, demo count, stale count, blocked count, manual-confirmation flag, and all safety flags.

## P. STOP Gates

Stop before current-candidates if:

- user has not explicitly approved execution;
- target date or universe is unclear;
- snapshot/data prerequisites are unknown;
- a snapshot build appears required;
- protected data writes appear required;
- data-quality or snapshot-quality is failed or unknown.

Stop before snapshot usage/building if:

- snapshot source is unclear;
- snapshot-quality status is missing, failed, or stale;
- the task would write to protected data locations;
- the task would fetch external data or mutate cache without separate approval.

Stop before signal semantics or advisory generation if:

- selected candidates artifact is missing or unhealthy;
- semantics profile is unclear;
- generated labels could be misread as orders;
- required no-live/no-broker/no-auto-order fields are missing;
- manual confirmation is not required.

Stop before optional paper context if:

- the task is only advisory refresh;
- manual paper context would imply approval;
- any fill, order, broker, or execution behavior is expected.

Stop before daily review rerun if:

- upstream artifacts are still stale or demo-only and the user expects fresh non-demo context;
- linked artifact paths are unclear;
- safety flags are missing or unsafe.

## Q. Safety Flag Checklist

Before and after any separately approved future execution, confirm:

- `real_buy_review_approved=false`
- `buy_review_allowed=false`
- `trading_allowed=false`
- `broker_api_approved=false`
- `order_placement_approved=false`
- `message_delivery_approved=false`
- `external_api_or_llm_approved=false`
- `active_replay_input_approved=false`
- `real_replay_execution_approved=false`
- `labels_training_model_stock_profile_paper_expansion_approved=false`
- `strategy_performance_validation_approved=false`
- `current_candidates_execution_approved=false` unless the separate execution task explicitly approves that exact run
- `snapshot_build_approved=false` unless a separate snapshot task explicitly approves it
- `signal_semantics_mutation_approved=false`
- `data_raw_processed_cache_writes_approved=false`

In advisory artifacts, also confirm manual confirmation is required, auto-order is disabled, no live trading is enabled, no broker API is enabled, and no message is sent.

## R. What To Paste Back To ChatGPT Before Execution

Before any future execution, paste:

```text
Target review date:
Target universe:
Intended mode: demo validation / non-demo local review context
Current git status:
Current git describe:
Candidate source plan:
Snapshot/data prerequisite status:
Current-candidates approval requested: yes/no
Snapshot build or usage approval requested: yes/no
Signal advisory approval requested: yes/no
Paper context needed: yes/no
Protected data write expected: yes/no
External API/LLM/broker/message/order expected: no
Stop gates reviewed: yes/no
```

Do not execute until the user separately approves the exact execution prompt.

## S. What To Paste Back To ChatGPT After Execution

After any separately approved future execution, paste:

```text
Commands actually run:
Artifacts created:
Current-candidates run id:
Candidate health status:
Signal advisory run id:
Signal advisory health status:
Single-symbol/conversation artifacts, if any:
Paper context artifacts, if any:
Daily review run id:
Daily review status:
Daily review health status:
Row count:
Demo count:
Stale count:
Manual-review candidate counts:
Blocked/not-found counts:
Safety flags summary:
Git status:
Unexpected warnings or blockers:
Confirmation no broker/order/message/trading behavior occurred:
```

If any warning or blocker appears, do not reinterpret it as success. Report it as review-required context.

## T. Non-Approvals and Hard Boundaries

This guide does not approve execution. This guide does not approve current-candidates execution. This guide does not approve snapshot building. This guide does not approve signal_semantics mutation. This guide does not approve real buy-review. This guide does not approve trading.

REVIEW_BUY_CANDIDATE remains manual-review-only. REVIEW_SELL_CANDIDATE remains manual-review-only. WATCH means observe/review only. DEMO_ONLY remains workflow validation only.

Fresh local advisory context, if later produced, still must not be trading authorization.

This guide creates no runtime behavior, no generated artifacts, no Project Source package, no source code changes, no test changes, no protected data writes, no replay, no labels, no training, no model workflow, no stock_profile workflow, no paper expansion, no broker behavior, no order placement, no message delivery, and no external API or LLM calls.

## U. Recommended Next Task

Personal MVP Upstream Advisory Artifact Refresh Execution Plan Report-Only v0.1.

That next task should remain report-only. It should select a target date/universe, resolve prerequisites, decide whether execution should remain demo-only or proceed as non-demo local review context, and ask for explicit user approval before any command is run.

