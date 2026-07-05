# Personal MVP Daily Advisory Review Surface Runbook / User Review Checklist v0.1

## A. Decision / Status

phase = personal_mvp_daily_advisory_review_runbook_user_review_checklist  
decision = ready  
privacy_issue_stop = no  
docs_only = yes  
source_code_changed = no  
tests_changed = no  
runtime_changed = no  
latest_checkpoint = v1.83.0  
latest_checkpoint_commit = 46f634b  
latest_post_checkpoint_commit = bcf0d01  
selected_next_route = personal_mvp_daily_advisory_review_first_local_run_feedback_review_report_only

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

Final runbook classification: `PERSONAL_MVP_DAILY_ADVISORY_REVIEW_RUNBOOK_READY_REPORT_ONLY`.

Final runbook verdict: `PERSONAL_MVP_DAILY_ADVISORY_REVIEW_RUNBOOK_READY_FOR_FIRST_LOCAL_RUN_FEEDBACK_REVIEW`.

## B. Audience and Purpose

This runbook is for the local personal/family MVP reviewer using the existing v1.83.0 Personal MVP Daily Advisory Review Surface.

It explains how to:

- run the existing daily review command family;
- open the right artifacts in the right order;
- interpret daily review rows safely;
- check safety flags before taking any manual note;
- decide when to stop and ask for deeper review;
- paste a concise summary back to ChatGPT after a daily run.

## C. What This Runbook Is and Is Not

This runbook is:

- a local operating guide;
- a user review checklist;
- a report-only interpretation guide;
- a way to reduce artifact sprawl during daily review.

This runbook is not:

- a new runtime implementation;
- a new CLI command;
- a trading signal;
- an order;
- broker, order, message, or trading authorization;
- real buy-review eligibility;
- paper approval;
- strategy performance validation;
- replay, labels, training, model, or stock_profile expansion.

Personal MVP Daily Advisory Review is local advisory review context only.

## D. Before Running the Daily Review

Before running a daily review, confirm:

- you are in the repo root;
- the review date is the date you intend to review;
- the local report root is the expected report root;
- you are not expecting the command to fetch data, place orders, send messages, or call brokers;
- existing upstream advisory artifacts are already present if you expect rows;
- no private secrets, account files, broker files, or protected data paths are involved.

Use a review date placeholder until you choose the real date:

```cmd
YYYY-MM-DD
```

## E. Standard Command Sequence

Use Windows CMD-style commands:

```cmd
cd /d "G:\AICODING\Quantitative Trading\quant-replay-system"
```

Create the daily review packet:

```cmd
.venv\Scripts\python.exe -m quant_replay_system.cli personal-mvp-daily-advisory-review --root outputs\reports --review-date YYYY-MM-DD
```

Optional arguments supported by the existing CLI:

```cmd
.venv\Scripts\python.exe -m quant_replay_system.cli personal-mvp-daily-advisory-review --root outputs\reports --review-date YYYY-MM-DD --max-symbols 20
.venv\Scripts\python.exe -m quant_replay_system.cli personal-mvp-daily-advisory-review --root outputs\reports --review-date YYYY-MM-DD --stale-after-days 7
.venv\Scripts\python.exe -m quant_replay_system.cli personal-mvp-daily-advisory-review --root outputs\reports --review-date YYYY-MM-DD --no-include-paper-context
```

Build the artifact views:

```cmd
.venv\Scripts\python.exe -m quant_replay_system.cli personal-mvp-daily-advisory-review-index --root outputs\reports\personal_mvp_daily_advisory_review
.venv\Scripts\python.exe -m quant_replay_system.cli personal-mvp-daily-advisory-review-health --root outputs\reports\personal_mvp_daily_advisory_review
.venv\Scripts\python.exe -m quant_replay_system.cli personal-mvp-daily-advisory-review-status --root outputs\reports\personal_mvp_daily_advisory_review
```

Refresh the local research dashboard view:

```cmd
.venv\Scripts\python.exe -m quant_replay_system.cli research-status --root outputs\reports
```

Do not treat these commands as approval, order, message, broker, replay, or trading commands.

## F. Output Artifacts and Reading Order

Default daily review root:

```text
outputs/reports/personal_mvp_daily_advisory_review/<daily_review_run_id>/
```

Read artifacts in this order:

1. `daily_advisory_review_report.md`  
   Start here. It is the human-facing daily readout.

2. `daily_advisory_review_summary.csv`  
   Use this for row counts, bucket counts, and quick health context.

3. `metadata.json`  
   Confirm status, health status, review date, run id, and safety flags.

4. `safety_flags.json`  
   Confirm all non-approval and no-side-effect flags remain safe.

5. `daily_advisory_review_rows.csv`  
   Open only when row-level details are needed.

6. `single_symbol_drilldown_index.csv`  
   Use for symbol-level follow-up links.

7. `manual_review_checklist.csv`  
   Use as the final manual discipline checklist.

8. `index/`, `health/`, and `status/` view outputs  
   Use for artifact discovery, integrity checks, and compact status summaries.

## G. Five-Minute Daily Review Flow

1. Confirm review date and latest run id.
2. Confirm status and health status.
3. Open `daily_advisory_review_report.md`.
4. Read the safety banner and non-approval statement.
5. Check row count and bucket counts.
6. Review `BLOCKED`, `STALE`, `DEMO_ONLY`, and `NOT_FOUND` sections before manual-review candidates.
7. Review `WATCH` rows as observe/review only.
8. Review `REVIEW_BUY_CANDIDATE` and `REVIEW_SELL_CANDIDATE` as manual-review-only.
9. Open single-symbol drill-down links only when the daily row is not enough.
10. Check `safety_flags.json`.
11. Record manual notes outside any automated trading system.
12. Stop and ask for deeper review if any row is confusing or appears stronger than manual review.

## H. Daily Row Interpretation Guide

`WATCH` means observe and review only. It is not a buy, sell, hold, order, or trading instruction.

`REVIEW_BUY_CANDIDATE` means manual-review-only. It is not real buy-review eligibility and does not allow a buy order.

`REVIEW_SELL_CANDIDATE` means manual-review-only. It is not a sell instruction and does not allow a sell order.

`HOLD_REVIEW` means continue local review. It is not an instruction to hold a live position.

`NO_ACTION` means no local advisory action from the current artifact.

`DEMO_ONLY` is workflow validation only. Do not use it for portfolio decisions.

`BLOCKED` must not be promoted. Inspect the blocker first.

`NOT_FOUND` must not invent advice. It means local evidence was not found for the symbol.

`STALE` means artifact freshness requires review before use. Refresh or inspect the source artifact before interpreting the row.

## I. Manual Review Checklist

For every daily run:

- Confirm review date.
- Confirm artifact root and latest run id.
- Confirm health status.
- Confirm row count.
- Confirm stale, demo, blocked, and not-found counts.
- Open the daily report first.
- Open rows CSV only if details are needed.
- Open drill-down index for symbol-level follow-up.
- Check safety flags.
- Record manual notes outside automated trading.
- Do not place orders from the report.
- Do not send messages from the report.
- Ask for ChatGPT review if any row is confusing, stale, blocked, or appears to imply a stronger action than manual review.

For every row you care about:

- Read the review bucket.
- Read the reason summary.
- Read risk notes and data source notes.
- Check validity and invalidation context when present.
- Check linked drill-down or conversation artifacts when present.
- Confirm `manual_confirmation_required`.
- Confirm `auto_order_allowed` is not true.
- Confirm the row remains local review context only.

## J. Single-Symbol Drill-Down Checklist

Use `single_symbol_drilldown_index.csv` when a row needs deeper inspection.

For a symbol-level follow-up:

- Confirm the symbol and name.
- Confirm the latest advisory action.
- Open linked single-symbol answer only if present.
- Open linked conversation report only if present.
- Compare the drill-down explanation with the daily row.
- Check validity, invalidation, risk notes, and data source notes.
- If the drill-down is missing, do not infer a stronger action.
- If the drill-down conflicts with the daily row, stop and ask for deeper review.

## K. Optional Paper-Context Interpretation

Paper context is optional audit context only.

If paper context is linked:

- use it to understand local workflow history;
- do not treat it as paper approval;
- do not treat it as real buy-review eligibility;
- do not treat it as performance validation;
- do not treat it as broker, order, message, or trading authority.

If paper context is absent, the daily review may still be valid as local advisory review context, but no paper conclusion should be inferred.

## L. Demo / Stale / Blocked / Not-Found Handling

Handle these rows first:

- `DEMO_ONLY`: workflow validation only; do not interpret as market advice.
- `STALE`: inspect freshness before interpretation.
- `BLOCKED`: do not promote; inspect blocker and stop if unclear.
- `NOT_FOUND`: do not invent advice; confirm whether the symbol exists in local artifacts.

If any of these appear in a row you care about, paste the row summary back to ChatGPT before taking further manual review action.

## M. Required Safety Flag Checks

These must remain false:

- `real_buy_review_approved`
- `buy_review_allowed`
- `trading_allowed`
- `broker_api_called`
- `broker_api_approved`
- `order_placed`
- `order_placement_approved`
- `message_sent`
- `message_delivery_approved`
- `external_api_called`
- `llm_api_called`
- `active_replay_input_created`
- `active_replay_input_approved`
- `real_replay_execution_approved`
- `current_candidates_run`
- `snapshot_built`
- `signal_semantics_mutated`
- `labels_created`
- `training_dataset_created`
- `model_training_performed`
- `stock_profile_created`
- `strategy_performance_validated`
- `data_raw_written`
- `data_processed_written`
- `data_cache_written`

These should remain true:

- `report_only`
- `diagnostic_only`
- `local_only`
- `manual_confirmation_required`

If any required false flag is true, stop and ask for governance review.

## N. Stop Conditions

Stop and ask for deeper review if:

- health status is `FAIL`;
- the report contains command-like buy/sell/order wording;
- any required false safety flag is true;
- a row is `BLOCKED`;
- a row is stale and you care about it;
- a row is `NOT_FOUND` but seems to imply advice;
- a `DEMO_ONLY` row appears in a real review path;
- paper context appears to imply approval;
- the row appears to be stronger than manual review;
- a linked drill-down contradicts the daily row;
- any artifact path points to protected data, secrets, broker files, or account files.

## O. What Not To Do After Reading The Report

Do not:

- place orders;
- submit orders;
- send messages;
- call brokers;
- call external APIs;
- ask an LLM to trade;
- treat `WATCH` as an instruction;
- treat manual-review candidates as approved;
- treat optional paper context as paper approval;
- treat this report as strategy performance validation;
- run current-candidates because of this report alone;
- build snapshots because of this report alone;
- mutate signal semantics because of this report alone;
- write protected data paths because of this report.

## P. What To Paste Back To ChatGPT

After a daily run, paste a short summary like this:

```text
Daily review date:
daily_review_run_id:
status:
health_status:
row_count:
watch_count:
review_buy_candidate_count:
review_sell_candidate_count:
blocked_count:
demo_count:
not_found_count:
stale_artifact_count:
safety flags all safe: yes/no
rows needing review:
questions / confusing rows:
```

For a symbol-specific question, paste:

```text
symbol:
review_bucket:
advisory_action:
reason_summary:
risk_notes:
data_source_notes:
validity / invalidation:
linked drill-down available: yes/no
why I am unsure:
```

Do not paste secrets, broker/account details, private tokens, or protected data contents.

## Q. Troubleshooting

If no rows appear:

- confirm `--root outputs\reports`;
- confirm upstream local advisory artifacts exist;
- run the status command to see whether a daily artifact exists;
- treat `DAILY_ADVISORY_REVIEW_NO_LOCAL_CONTEXT` as safe no-context, not a recommendation.

If health is `WARN`:

- inspect the health report;
- decide whether the warning is stale, no-context, or blocked-context review;
- do not promote warning context into action.

If health is `FAIL`:

- stop;
- do not interpret rows;
- paste the health issue summary back to ChatGPT.

If the report path is hard to find:

- run `personal-mvp-daily-advisory-review-index`;
- open the latest `report_path`;
- confirm the latest run id in `personal-mvp-daily-advisory-review-status`.

## R. Non-Approvals and Hard Boundaries

This runbook does not approve:

- real buy-review;
- `buy_review_allowed`;
- trading;
- broker API use;
- order placement;
- message delivery;
- external API or LLM calls;
- active replay input;
- real replay execution;
- labels, training, model, stock_profile, or paper expansion;
- strategy performance validation;
- current-candidates execution;
- snapshot build;
- signal semantics mutation;
- protected data writes.

Personal MVP Daily Advisory Review is local advisory review context only. It is not a trading signal. It is not an order. It is not broker, order, message, or trading authorization.

## S. Recommended Next Task

Recommended next task:

`Personal MVP Daily Advisory Review Surface First Local Run Feedback Review Report-Only v0.1`

The next task should review one user-provided daily run summary, classify any confusing rows, and recommend whether a docs-only usability refinement is needed. It should not implement runtime behavior, add commands, run current-candidates, build snapshots, mutate signal semantics, create buy-review eligibility, approve paper or trading, or write protected data paths.
