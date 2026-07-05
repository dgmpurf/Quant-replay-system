# Personal MVP Upstream Advisory Artifact Refresh Execution Plan v0.1

phase = personal_mvp_upstream_advisory_artifact_refresh_execution_plan  
decision = ready  
privacy_issue_stop = no  
docs_only = yes  
source_code_changed = no  
tests_changed = no  
runtime_changed = no  
latest_checkpoint = v1.83.0  
latest_checkpoint_commit = 46f634b  
latest_refresh_command_guide_commit = 26e21bc  
first_local_run_id = 1f972084211d  
target_review_date_selected = no  
target_universe_selected = no  
execution_approved = no  
selected_next_route = ask_user_to_choose_target_date_universe_mode_before_execution

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

This execution plan is ready as a docs-only planning artifact. It does not approve execution. It does not run any refresh command. It does not implement a new workflow.

No target review date, target universe, or intended mode has been selected. The next step is target selection by the user before any future execution prompt can be drafted.

## B. Purpose and Scope

Purpose: convert the accepted upstream advisory artifact refresh command guide into a future execution planning framework.

Scope:

- define unresolved target fields;
- define approval language required before any future execution;
- define command groups in intended order;
- define prerequisites and stop gates;
- define expected artifacts by stage;
- define paste-back templates;
- preserve all non-approval boundaries.

Out of scope:

- running current-candidates;
- building snapshots;
- running signal-semantics or signal-advisory;
- running single-symbol or advisory-conversation workflows;
- running paper workflow;
- rerunning daily advisory review;
- changing source code, tests, runtime behavior, or generated outputs.

## C. Current Accepted State

Latest checkpoint: v1.83.0 at 46f634b. Latest accepted command guide: 26e21bc.

The first local daily advisory review run was `1f972084211d`. It generated a usable local review surface but all rows were stale DEMO_ONLY context. The accepted command guide selected this execution planning task as the next route.

## D. First Local Run Problem Statement

The first local run was technically successful but not fresh enough for real local advisory review. It showed:

- stale upstream signal context;
- DEMO_ONLY rows only;
- no manual-review candidate rows;
- no trading permission;
- no real buy-review permission;
- no current-candidates refresh;
- no snapshot refresh.

The problem to solve later is not the daily review surface itself. The problem is selecting and refreshing upstream local advisory artifacts before another daily review run.

## E. Target Selection Gate

Execution cannot proceed until the user selects:

- target review date: not selected;
- target universe: not selected;
- intended mode: not selected;
- include paper context: not selected;
- max visible symbols: optional, not selected;
- stale threshold: optional, not selected.

Allowed intended modes:

- demo validation: workflow plumbing validation only;
- non-demo local review context: structural manual-review labels only, still not trading authorization.

Do not infer target values from old artifacts. Dates such as `2024-05-20` may be examples only unless the user explicitly selects them.

## F. Execution Approval Gate

Before any future command is run, require exact user approval text with concrete values:

```text
I approve running only the Personal MVP upstream advisory artifact refresh execution for:
target_review_date = <YYYY-MM-DD>
target_universe = <universe_name>
intended_mode = <demo validation | non-demo local review context>
include_paper_context = <yes | no>
current_candidates_execution = <approved | not approved>
snapshot_build = not approved
signal_semantics_mutation = not approved
protected_data_writes = not approved
broker_api_orders_messages_trading = not approved
```

If current-candidates execution is not explicitly approved in that future text, stop before command group 3. If snapshot build is requested or required, stop and create a separate snapshot/data planning task.

## G. Prerequisites Checklist

Before any future execution prompt:

- repository branch and status are known;
- target review date is selected;
- target universe is selected;
- intended mode is selected;
- paper context inclusion is selected;
- local data and snapshot prerequisite status is known;
- no protected data write is expected;
- current-candidates approval is explicit or command group 3 is excluded;
- snapshot build approval is not bundled;
- advisory generation approval is explicit or excluded;
- no external API, LLM, broker, order, or message behavior is expected;
- safety flags to inspect are listed;
- paste-back template is ready.

## H. Command Group 1: Repository and Status Checks

Future-only command group. Do not run from this plan.

Purpose: establish baseline state before any refresh.

Template:

```text
git status --short --branch
git log --oneline --decorate -n 10
git describe --tags --always
```

Expected artifact: no new artifact. Expected output: clean worktree and known HEAD.

Stop if worktree has unexpected changes, branch is wrong, or HEAD does not match the reviewed execution prompt.

## I. Command Group 2: Current-Candidates Prerequisite Review

Future-only command group. Do not run from this plan.

Purpose: decide whether candidate generation is allowed and feasible.

Inputs to review:

- target review date;
- target universe;
- intended mode;
- local snapshot/data status;
- selection profile;
- configured maximum candidate count if any.

This group may include read-only review of existing docs/artifacts in a separately approved task, but it must not generate candidates unless command group 3 is explicitly approved.

Stop if snapshot/data prerequisites are unknown, stale, failed, or would require a new snapshot build.

## J. Command Group 3: Current-Candidates Execution Gate

Future-only command group. Do not run from this plan.

Potential command form after explicit approval:

```text
python -m quant_replay_system.cli current-candidates --date <YYYY-MM-DD> --universe <universe_name> --top <N> --selection-profile <default-or-demo>
```

Optional flags:

- `--output-dir`
- `--config`

Expected artifacts after approved execution:

- current-candidates artifact folder;
- `candidates.csv`;
- candidate report;
- metadata;
- possible scored or factor context.

Stop if the future approval does not explicitly approve current-candidates execution for the exact target date and universe.

## K. Command Group 4: Candidate Index / Health Review

Future-only command group. Do not run from this plan.

Potential command forms after explicit approval:

```text
python -m quant_replay_system.cli current-candidates-index --root outputs/reports/current_candidates
python -m quant_replay_system.cli current-candidates-health --root outputs/reports/current_candidates
```

Expected artifacts after approved execution:

- candidate index artifacts;
- candidate health report;
- PASS/WARN/FAIL health context;
- selected `candidates.csv` path for advisory generation.

Stop if candidate health is FAIL, if required metadata is missing, if symbols are malformed, if snapshot/data quality is failed, or if stale/unrelated artifacts are selected.

## L. Command Group 5: Signal Semantics / Signal Advisory Gate

Future-only command group. Do not run from this plan.

Standalone semantics is optional because signal advisory can use shared semantics internally. Use it only if explicit semantics audit context is required.

Potential semantics command:

```text
python -m quant_replay_system.cli signal-semantics --input <candidates.csv> --input-type candidates --metadata <metadata.json> --profile <profile>
```

Potential advisory command:

```text
python -m quant_replay_system.cli signal-advisory --candidates <candidates.csv> --candidate-report <current_candidates_report.md> --metadata <metadata.json> --alert-preview
```

Potential advisory inspection commands:

```text
python -m quant_replay_system.cli signal-advisory-index --root outputs/reports/signals
python -m quant_replay_system.cli signal-advisory-health --root outputs/reports/signals
```

Expected artifacts after approved execution:

- signal rows;
- signal report;
- metadata;
- optional local alert preview;
- health context.

Stop if advisory labels are interpreted as orders, if no-live/no-broker/no-auto-order/manual-confirmation fields are missing, or if data/snapshot quality is failed.

## M. Command Group 6: Optional Single-Symbol and Conversation Drilldown Gate

Future-only command group. Do not run from this plan.

Potential single-symbol command:

```text
python -m quant_replay_system.cli single-symbol-advisory --symbol <symbol> --signals <signals.csv> --metadata <metadata.json> --alert-preview --question-style --question "<local question>"
```

Potential conversation command:

```text
python -m quant_replay_system.cli advisory-conversation --question "<local question>" --signals <signals.csv> --metadata <metadata.json>
```

Expected artifacts after approved execution:

- single-symbol report and rows;
- optional local answer markdown;
- optional conversation report;
- no message sent;
- no LLM call.

Stop if the target symbol is not selected, if the source artifact is unhealthy, if a question implies execution advice, or if message delivery is expected.

## N. Command Group 7: Optional Paper-Context Gate

Future-only command group. Do not run from this plan.

Paper context is optional. It should be included only if the user explicitly wants local paper workflow context in the daily review packet.

Potential command forms:

```text
python -m quant_replay_system.cli current-to-paper --candidates <candidates.csv> --paper-date <YYYY-MM-DD>
python -m quant_replay_system.cli paper-workflow-status --root outputs/reports --decision-date <YYYY-MM-DD> --universe <universe_name>
```

Expected artifacts after approved execution:

- current-to-paper handoff report if run;
- paper workflow status report if run;
- local manual workflow context only.

Stop if paper context could be interpreted as approval, if fills/orders are expected, or if the refresh goal does not need paper context.

## O. Command Group 8: Daily Advisory Review Rerun Gate

Future-only command group. Do not run from this plan.

Potential command form:

```text
python -m quant_replay_system.cli personal-mvp-daily-advisory-review --root outputs/reports --review-date <YYYY-MM-DD> --stale-after-days <N>
```

Optional flags:

- `--output-dir`
- `--max-symbols`
- `--include-paper-context`
- `--no-include-paper-context`

Expected artifacts after approved execution:

- daily advisory review report;
- rows CSV;
- summary CSV;
- manual checklist CSV;
- metadata;
- safety flags;
- single-symbol drilldown index.

Stop if upstream artifacts remain stale/demo-only while the user expects fresh non-demo local context.

## P. Expected Artifacts by Stage

Stage expectations:

- group 1: terminal evidence only, no artifacts;
- group 2: prerequisite decision notes only unless separately scoped;
- group 3: current-candidates artifacts;
- group 4: candidate index and health artifacts;
- group 5: semantics/advisory artifacts and local alert preview;
- group 6: optional one-symbol and conversation artifacts;
- group 7: optional paper-context artifacts;
- group 8: daily review packet artifacts.

No stage should create broker/order/message/trading artifacts. No stage should create replay input, labels, training data, model artifacts, stock_profile validation, or strategy-performance validation.

## Q. STOP Gates

Stop before any execution if target review date, universe, or mode is missing.

Stop before current-candidates if explicit approval is missing, data/snapshot prerequisites are unknown, or a snapshot build is required.

Stop before index/health commands if the prior artifact path is unknown.

Stop before signal semantics or advisory if candidate health is failed or safety fields are missing.

Stop before single-symbol or conversation if symbol/question is not selected or if the request expects executable advice.

Stop before paper context if it would expand the task beyond local context.

Stop before daily review rerun if upstream artifacts are not fresh enough for the user's intended mode.

Stop if any artifact claims buy-review permission, trading permission, broker access, order placement, message delivery, protected data writes, active replay input, replay execution, labels, training, model, stock_profile, paper expansion, or performance validation.

## R. Safety Flag Checklist

Required safety posture:

- real_buy_review_approved remains no;
- buy_review_allowed remains no;
- trading_allowed remains no;
- broker_api_approved remains no;
- order_placement_approved remains no;
- message_delivery_approved remains no;
- external_api_or_llm_approved remains no;
- active_replay_input_approved remains no;
- real_replay_execution_approved remains no;
- labels_training_model_stock_profile_paper_expansion_approved remains no;
- strategy_performance_validation_approved remains no;
- snapshot_build_approved remains no unless a separate snapshot task exists;
- signal_semantics_mutation_approved remains no;
- data_raw_processed_cache_writes_approved remains no.

For advisory outputs, also require:

- manual confirmation required;
- auto-order disabled;
- no live trading;
- no broker API;
- no message sent;
- clear stale/demo/manual-review counts.

## S. Paste-Back Template Before Execution

Before any future execution, paste:

```text
Target review date:
Target universe:
Intended mode:
Include paper context:
Max symbols:
Stale threshold:
Current git status:
Current git describe:
Snapshot/data prerequisite status:
Current-candidates exact command proposed:
Advisory exact command proposed:
Optional drilldown symbols/questions:
Optional paper-context command proposed:
Protected data writes expected: no
External API/LLM/broker/order/message/trading expected: no
Exact approval requested:
```

Do not run commands until the user explicitly approves the exact future execution request.

## T. Paste-Back Template After Execution

After any separately approved future execution, paste:

```text
Commands actually run:
Artifacts created:
Current-candidates run id:
Candidate health status:
Signal semantics run id, if any:
Signal advisory run id:
Signal advisory health status:
Single-symbol artifacts, if any:
Conversation artifacts, if any:
Paper context artifacts, if any:
Daily advisory review run id:
Daily advisory review status:
Daily advisory review health status:
Row count:
Demo count:
Stale count:
Manual-review candidate counts:
Blocked count:
Not-found count:
Safety flags summary:
Git status:
Unexpected warnings or blockers:
Confirmation no protected data writes:
Confirmation no broker/order/message/trading:
```

## U. What Would Count as Success

A future execution can be considered useful only if:

- target date and universe match the approved request;
- current-candidates artifacts, if generated, are the selected source;
- health checks are PASS or explicitly reviewed WARN;
- signal advisory artifacts preserve manual confirmation and no-auto-order/no-live/no-broker/no-message boundaries;
- daily review rerun points to the intended refreshed artifacts;
- stale count is acceptable for the selected mode;
- DEMO_ONLY count matches the selected mode;
- manual-review labels are understood as review-only;
- safety flags remain closed.

Success does not mean trading permission.

## V. What Would Count as Warn / Stop

Warn or stop if:

- target fields were inferred instead of selected;
- generated artifacts are stale;
- selected artifacts are unrelated to the target date/universe;
- candidate health is WARN without review;
- candidate health is FAIL;
- signal advisory safety fields are missing;
- DEMO_ONLY appears where non-demo local context was expected;
- daily review has missing artifact links;
- any artifact path points to protected or private locations unexpectedly;
- any artifact implies approval, execution, broker access, message delivery, or trading.

## W. Non-Approvals and Hard Boundaries

This execution plan does not approve execution. This execution plan does not approve current-candidates execution. This execution plan does not approve snapshot building. This execution plan does not approve signal_semantics mutation. This execution plan does not approve real buy-review. This execution plan does not approve trading.

Any command sequence is future-only until the user gives exact approval.

REVIEW_BUY_CANDIDATE remains manual-review-only. REVIEW_SELL_CANDIDATE remains manual-review-only. WATCH means observe/review only. DEMO_ONLY remains workflow validation only.

Fresh local advisory context, if later produced, still must not be trading authorization.

## X. Selected Next Route

Selected next route: A. Ask user to choose target date/universe/mode before execution.

Reason: the current task has no selected target review date, target universe, intended mode, or paper-context choice. Asking for those values is safer than drafting an executable prompt with placeholders that might be misused.

## Y. Commit / Tag / Source Recommendation

Commit recommendation: commit this docs-only execution plan after review if accepted.

Tag recommendation: no tag for this standalone execution plan.

Source update recommendation: no immediate Project Source update. Consider a later update only if an accepted execution checkpoint changes durable project state.

## Z. Recommended Next Task

Ask the user to choose target review date, target universe, intended mode, and paper-context inclusion before execution.

Suggested request:

```text
Please choose:
target_review_date =
target_universe =
intended_mode = demo validation / non-demo local review context
include_paper_context = yes / no
max_symbols =
stale_after_days =
```

Only after those values are selected should a future approval-request or execution prompt be drafted.

