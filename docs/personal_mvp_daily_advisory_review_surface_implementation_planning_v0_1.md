# Personal MVP Daily Advisory Review Surface Implementation Planning v0.1

## A. Decision / Status

phase = personal_mvp_daily_advisory_review_surface_implementation_planning  
decision = ready  
privacy_issue_stop = no  
docs_only = yes  
source_code_changed = no  
tests_changed = no  
runtime_changed = no  
selected_next_route = personal_mvp_daily_advisory_review_surface_core_report_only

future_runtime_implementation_approved = no  
future_report_only_command_planned = yes  
proposed_command_name = personal-mvp-daily-advisory-review  
proposed_output_root = outputs/reports/personal_mvp_daily_advisory_review/<daily_review_run_id>/  
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

Final planning classification: `PERSONAL_MVP_DAILY_ADVISORY_REVIEW_SURFACE_IMPLEMENTATION_PLANNING_READY_REPORT_ONLY`.

Final planning verdict: `PERSONAL_MVP_DAILY_ADVISORY_REVIEW_SURFACE_READY_FOR_CORE_REPORT_ONLY_IMPLEMENTATION`.

## B. Current Accepted State

The current accepted state is:

- latest stable checkpoint tag: `v1.82.0`;
- latest checkpoint commit/tag: `e247ab6` / `v1.82.0`;
- latest accepted design commit: `ec0e217`;
- latest accepted design route: `personal_mvp_daily_advisory_review_surface_implementation_planning_report_only`;
- current branch expected for this planning task: `main`;
- current HEAD expected for this planning task: `ec0e217`;
- current `git describe` expected for this planning task: `v1.82.0-4-gec0e217`.

The previous design file established the daily advisory review surface as a local, human-facing review report that reuses existing local advisory and paper-context artifacts without creating any new buy, sell, paper, broker, message, replay, label, training, model, stock_profile, performance, or trading authority.

## C. Future Implementation Purpose

The future implementation should create one local report-only daily advisory review command. It should make the existing personal/family MVP review path easier to use by aggregating local advisory artifacts into a compact daily readout.

The future command should answer:

- what local advisory context exists today;
- which symbols are watch, manual-review, blocked, demo, stale, or not found;
- why each visible symbol appears;
- which local artifacts support each row;
- which single-symbol or conversation report can be opened for drill-down;
- what manual checklist remains.

The future command should not create new investment advice. It should not rerun signal semantics, current-candidates, paper workflows, replay workflows, PIT validators, hash checks, labels, training, models, or stock_profile workflows.

## D. Proposed CLI Command

Proposed future command:

```cmd
python -m quant_replay_system.cli personal-mvp-daily-advisory-review --root outputs\reports --review-date 2024-05-20
```

Proposed arguments:

- `--root`: local report root to inspect; default `outputs/reports`.
- `--review-date`: optional daily review date used for freshness and report labeling.
- `--output-dir`: optional output directory; default under `outputs/reports/personal_mvp_daily_advisory_review/`.
- `--max-symbols`: optional display cap for large advisory artifacts.
- `--include-paper-context`: optional flag to include paper workflow references when present.
- `--stale-after-days`: optional integer freshness threshold for human review warnings.

The command should print:

- daily review run id;
- daily review status;
- review date;
- row count;
- action bucket counts;
- stale or missing artifact counts;
- report path;
- explicit no-broker, no-order, no-message, no-trading statement.

Do not add index, health, status, research-status, or dashboard integration in the first implementation unless a later prompt explicitly scopes that work. That keeps the first command local, testable, and small.

## E. Proposed Input / Discovery Model

The future command should read existing local report artifacts only. Preferred discovery order:

1. Use `research-status` artifacts if present to find latest advisory and paper-context paths.
2. Fall back to latest signal advisory status under `outputs/reports/signals/status/`.
3. Fall back to latest signal advisory run under `outputs/reports/signals/`.
4. Discover latest single-symbol answer status under `outputs/reports/single_symbol_advisory_answer/status/`.
5. Discover latest advisory conversation status under `outputs/reports/advisory_conversation/status/`.
6. Discover optional current-to-paper and paper workflow status artifacts.

Allowed local inputs:

- `metadata.json` files from existing report artifacts;
- advisory status summary CSV files;
- signal advisory `signals.csv`;
- single-symbol advisory JSON/CSV/markdown paths;
- single-symbol answer metadata and markdown path;
- advisory conversation metadata and linked answer path;
- current-to-paper handoff metadata;
- paper workflow status metadata and summary CSV.

Forbidden inputs:

- protected raw market data;
- protected processed data;
- cache files;
- target reviewed CSV package files;
- source artifact bytes;
- source content;
- private secrets or environment files;
- broker, order, message, API, or account files.

If no local advisory artifacts exist, the command should create a no-context report that says no local daily advisory review can be produced from existing artifacts.

## F. Proposed Output Artifact Root

Default future output root:

```text
outputs/reports/personal_mvp_daily_advisory_review/<daily_review_run_id>/
```

The first implementation should write only under this report root or a caller-supplied `--output-dir`. It should reject output paths under:

- `data/raw`;
- `data/processed`;
- `data/cache`;
- `docs/project_sources`;
- `.env`;
- `secrets`;
- any path outside the requested output root after resolution.

## G. Proposed Output Files

Recommended future files:

- `metadata.json`: run metadata, safety flags, source paths, action counts, freshness status.
- `daily_advisory_review_report.md`: human-facing daily readout.
- `daily_advisory_review_rows.csv`: one row per visible symbol or requested symbol context.
- `daily_advisory_review_summary.csv`: one-row summary for quick checks.
- `single_symbol_drilldown_index.csv`: links to single-symbol answers and conversation reports.
- `manual_review_checklist.csv`: checklist rows for human review.
- `safety_flags.json`: explicit negative proof and no-side-effect fields.

Do not create paper review update CSVs, reviewed decisions, fills, replay inputs, current-candidates outputs, snapshots, labels, metrics, model artifacts, or stock_profile artifacts.

## H. Daily Review Metadata Schema

Recommended `metadata.json` fields:

- `daily_review_run_id`;
- `review_surface_version`;
- `review_date`;
- `generated_at`;
- `root`;
- `status`;
- `workflow_stage`;
- `report_only`;
- `diagnostic_only`;
- `local_only`;
- `source_discovery_mode`;
- `latest_research_status_path`;
- `latest_signal_run_id`;
- `latest_signal_status`;
- `latest_single_symbol_advisory_run_id`;
- `latest_single_symbol_answer_run_id`;
- `latest_advisory_conversation_run_id`;
- `latest_current_to_paper_handoff_id`;
- `latest_paper_workflow_status_id`;
- `row_count`;
- `watch_count`;
- `review_buy_candidate_count`;
- `review_sell_candidate_count`;
- `hold_review_count`;
- `no_action_count`;
- `blocked_count`;
- `demo_count`;
- `not_found_count`;
- `stale_artifact_count`;
- `missing_artifact_count`;
- `manual_confirmation_required`;
- `artifact_paths`;
- `recommended_next_manual_action`;
- `recommended_next_task`;
- safety and negative proof fields from section L.

Recommended statuses:

- `DAILY_ADVISORY_REVIEW_READY_FOR_MANUAL_REVIEW`;
- `DAILY_ADVISORY_REVIEW_NO_LOCAL_CONTEXT`;
- `DAILY_ADVISORY_REVIEW_STALE_CONTEXT_REVIEW_REQUIRED`;
- `DAILY_ADVISORY_REVIEW_BLOCKED_CONTEXT_REVIEW_REQUIRED`;
- `DAILY_ADVISORY_REVIEW_DEMO_ONLY_CONTEXT`;
- `DAILY_ADVISORY_REVIEW_FAILED_SAFETY_CHECK`.

## I. Daily Review Row Schema

Recommended `daily_advisory_review_rows.csv` fields:

- `daily_review_run_id`;
- `review_date`;
- `symbol`;
- `name`;
- `instrument_type`;
- `universe_name`;
- `signal_date`;
- `decision_date`;
- `source_component`;
- `source_run_id`;
- `source_artifact_path`;
- `advisory_action`;
- `review_bucket`;
- `reason_summary`;
- `confidence_level`;
- `final_score`;
- `risk_notes`;
- `data_source_notes`;
- `entry_condition`;
- `exit_condition`;
- `invalidation_condition`;
- `valid_until`;
- `demo_mode`;
- `not_strategy_recommendation`;
- `blocked_reason`;
- `not_found_reason`;
- `stale_context_reason`;
- `linked_single_symbol_answer_path`;
- `linked_conversation_report_path`;
- `linked_paper_context_path`;
- `manual_confirmation_required`;
- `auto_order_allowed`;
- `no_live_trading`;
- `no_broker_api`;
- `no_message_sent`;
- `next_manual_check`;
- `manual_note_placeholder`;
- `non_approval_statement`.

Symbols must be read and written as strings. Leading zeros must be preserved.

## J. Single-Symbol Drill-Down Schema

Recommended `single_symbol_drilldown_index.csv` fields:

- `daily_review_run_id`;
- `symbol`;
- `name`;
- `latest_advisory_action`;
- `single_symbol_advisory_run_id`;
- `single_symbol_answer_run_id`;
- `answer_markdown_path`;
- `answer_status`;
- `answer_health_status`;
- `answer_question`;
- `answer_style`;
- `conversation_run_id`;
- `conversation_original_question`;
- `conversation_parsed_intent`;
- `conversation_status`;
- `conversation_report_path`;
- `source_artifact_path`;
- `validity_context`;
- `invalidation_condition`;
- `risk_notes`;
- `data_source_notes`;
- `manual_confirmation_required`;
- `not_found`;
- `demo_mode`;
- `blocked`;
- `next_manual_check`.

When a symbol is not found in local artifacts, the future command must record a not-found row instead of inventing a recommendation.

## K. Manual Checklist Schema

Recommended `manual_review_checklist.csv` fields:

- `daily_review_run_id`;
- `symbol`;
- `check_id`;
- `check_label`;
- `check_status`;
- `source_field`;
- `source_artifact_path`;
- `manual_note_placeholder`;
- `blocking_if_unchecked`;

Recommended checklist rows per symbol:

- confirm artifact date and run id;
- confirm advisory label and review bucket;
- confirm demo, blocked, not-found, and stale context;
- read reason summary;
- read risk notes and data source notes;
- read validity and invalidation condition;
- open single-symbol answer when present;
- inspect optional paper-context link when present;
- record manual note;
- confirm no order, no broker, no message, and no trading action follows from the report.

## L. Safety And Negative Proof Fields

Every output should include:

- `report_only = true`;
- `diagnostic_only = true`;
- `local_only = true`;
- `manual_confirmation_required = true`;
- `real_buy_review_approved = false`;
- `buy_review_allowed = false`;
- `trading_allowed = false`;
- `broker_api_called = false`;
- `broker_api_approved = false`;
- `order_placed = false`;
- `order_placement_approved = false`;
- `message_sent = false`;
- `message_delivery_approved = false`;
- `external_api_called = false`;
- `llm_api_called = false`;
- `active_replay_input_created = false`;
- `active_replay_input_approved = false`;
- `real_replay_execution_approved = false`;
- `current_candidates_run = false`;
- `snapshot_built = false`;
- `signal_semantics_mutated = false`;
- `labels_created = false`;
- `training_dataset_created = false`;
- `model_training_performed = false`;
- `stock_profile_created = false`;
- `strategy_performance_validated = false`;
- `data_raw_written = false`;
- `data_processed_written = false`;
- `data_cache_written = false`.

The future implementation should fail or mark health unsafe if any forbidden flag is true.

## M. Report Wording Rules

Required wording:

- "local advisory review context";
- "manual confirmation required";
- "not an order";
- "not broker, order, message, or trading authorization";
- "does not create real buy-review eligibility";
- "does not validate strategy performance";
- "does not mutate signal semantics";
- "does not run current-candidates or snapshots";
- "does not write protected data paths".

Action wording:

- `DEMO_ONLY`: workflow validation context only.
- `WATCH`: observe and review only.
- `REVIEW_BUY_CANDIDATE`: manual review candidate only.
- `REVIEW_SELL_CANDIDATE`: manual review candidate only.
- `HOLD_REVIEW`: continue review only.
- `NO_ACTION`: no local action from artifact.
- `BLOCKED`: inspect blocker before any downstream interpretation.
- `NOT_FOUND`: no local evidence for the requested symbol.
- `STALE`: artifact date or freshness requires review before use.

The report should not use command-like wording such as "buy now", "sell now", "trade", "execute", "submit", "send alert", or "place order" except inside explicit negative safety statements.

## N. Artifact Freshness And Stale Handling

Freshness should be conservative:

- If `review_date` is missing, mark freshness as `REVIEW_DATE_NOT_SUPPLIED`.
- If artifact date is missing, mark row as `STALE_CONTEXT_REVIEW_REQUIRED`.
- If artifact date is older than `--stale-after-days`, mark row as stale.
- If signal advisory is newer than single-symbol answer, show the answer as potentially stale.
- If paper context is older than advisory context, show paper context as optional stale context.
- If only research-status exists and no advisory rows are found, create a no-context report.

Stale does not mean rejected. It means human review is required before relying on the context.

## O. Existing Artifact Reuse Plan

Reuse in this order:

1. `research-status` for navigation and latest context when present.
2. `signal-advisory-status` and signal advisory artifacts for daily rows.
3. `single-symbol-advisory-status` and `single-symbol-advisory-answer-status` for drill-down links.
4. `advisory-conversation-status` for user-question context.
5. `current-to-paper` and paper workflow status for optional downstream context.

Do not rerun any of these workflows. The daily review should summarize what already exists.

## P. Focused Test Plan

Future implementation should create:

- `tests/test_personal_mvp_daily_advisory_review.py`;
- `tests/test_personal_mvp_daily_advisory_review_cli.py`.

Recommended focused tests:

- no local advisory artifacts creates no-context report;
- signal advisory rows create daily review rows;
- leading-zero symbols remain strings;
- demo rows remain `DEMO_ONLY`;
- blocked rows remain blocked;
- not-found single-symbol context does not invent a recommendation;
- stale signal artifact marks stale context;
- stale single-symbol answer is flagged against newer signal context;
- paper context is optional and does not alter advisory label;
- manual checklist is written for each visible row;
- all safety fields are false or true as required;
- output root rejects `data/raw`, `data/processed`, `data/cache`, and `docs/project_sources`;
- report wording contains non-approval statements;
- no source hash, PIT, replay, label, training, model, stock_profile, broker, order, message, or trading fields are promoted.

Recommended future focused commands:

```cmd
set PYTHONPATH=src
.venv\Scripts\python.exe -m pytest tests/test_personal_mvp_daily_advisory_review.py -q
.venv\Scripts\python.exe -m pytest tests/test_personal_mvp_daily_advisory_review_cli.py -q
```

If the future task touches `local_research_dashboard.py`, also run:

```cmd
.venv\Scripts\python.exe -m pytest tests/test_local_research_dashboard.py -q
```

The first implementation should avoid touching dashboard integration, so this third command should not be required.

## Q. CLI Smoke Plan

Future CLI smoke should use temporary or ignored local report roots only.

Recommended no-context smoke:

```cmd
set PYTHONPATH=src
.venv\Scripts\python.exe -m quant_replay_system.cli personal-mvp-daily-advisory-review --root outputs\reports --output-dir outputs\reports\personal_mvp_daily_advisory_review\manual_smoke
```

Recommended fixture smoke in tests:

```cmd
set PYTHONPATH=src
.venv\Scripts\python.exe -m quant_replay_system.cli personal-mvp-daily-advisory-review --root <tmp_reports_root> --review-date 2024-05-20 --output-dir <tmp_output_dir>
```

Expected CLI output should include:

- `daily_review_run_id`;
- `status`;
- `row_count`;
- `report_path`;
- `No broker API was invoked.`;
- `No orders were placed.`;
- `No messages were sent.`;
- `No trading was authorized.`;
- `No protected data paths were written.`

## R. Static / Disclosure Scan Plan

Future implementation validation should include:

```cmd
rg -n "buy now|sell now|place order|submit order|broker_api_called: true|order_placed: true|message_sent: true|trading_allowed: true|buy_review_allowed: true" outputs\reports\personal_mvp_daily_advisory_review
```

Expected result:

- no command-like buy/sell/order wording outside explicit negative statements;
- no unsafe side-effect flags true;
- no private source content copied into reports;
- no full protected data content copied into reports.

For code review, scan the new module and tests for protected path writes:

```cmd
rg -n "data/raw|data/processed|data/cache|docs/project_sources|broker|order_placed|message_sent|trading_allowed" src\quant_replay_system\personal_mvp_daily_advisory_review.py tests\test_personal_mvp_daily_advisory_review*.py
```

Occurrences must be guards, safety fields, or negative assertions only.

## S. STOP Conditions

The future implementation task must stop before editing if:

- worktree is dirty and changes are unrelated;
- expected checkpoint or planning anchor is missing;
- `docs/project_sources` exists or is requested as an output;
- the implementation would need to read protected raw or processed data;
- the implementation would need to parse source artifact bytes or target reviewed CSV package files;
- the implementation would need to run current-candidates, snapshots, replay, labels, training, model, stock_profile, or paper workflows;
- the implementation would need broker/API/order/message behavior;
- the implementation would need to modify signal semantics;
- the implementation would need to approve real buy-review, paper expansion, performance validation, or trading.

The future implementation task must stop after editing if:

- tests reveal any unsafe flag true;
- report wording turns a review label into an instruction;
- leading-zero symbols are lost;
- output root guards fail;
- generated artifacts appear under protected data paths.

## T. Non-Goals And Explicit Non-Approvals

This planning file does not approve:

- runtime implementation in this task;
- source code changes in this task;
- test changes in this task;
- current-candidates execution;
- snapshot creation;
- signal semantics mutation;
- source hash validation;
- available-time validation;
- PIT admissibility;
- real reviewed package creation;
- active replay input;
- real replay execution;
- forward labels;
- training or model workflows;
- stock_profile validation;
- paper workflow expansion;
- real buy-review;
- `buy_review_allowed`;
- strategy performance validation;
- broker integration;
- order placement;
- message delivery;
- trading;
- writes to `data/raw`, `data/processed`, or `data/cache`;
- Project Source package creation.

## U. Bundling Recommendation For Next Implementation Prompt

Recommended next prompt should bundle only:

- core module;
- CLI command;
- focused core tests;
- focused CLI tests;
- docs update only if the prompt explicitly allows a short user-facing docs page.

Do not bundle:

- index/health/status views;
- research-status integration;
- local dashboard integration;
- checkpoint docs;
- Project Source updates.

Keeping the first runtime slice small gives the user an actual daily readout quickly while preserving the option to add views and research-status later.

## V. Open Blockers

No blocker was found for a future local report-only implementation.

Open implementation choices:

- whether no-context output should be `PASS` with no rows or `WARN` with missing artifacts;
- whether to include `signals.csv` row parsing in the first version or rely only on status metadata when `signals.csv` is absent;
- whether `--review-date` should default to local date or remain blank when omitted;
- whether `--include-paper-context` should default true or false.

Recommended default choices:

- no-context output should be `WARN` but safe;
- first version should read `signals.csv` when present and status metadata otherwise;
- `--review-date` should default to local date;
- paper context should default true when present but remain optional context only.

## W. Non-Blocking Notes

- This feature is primarily a usability layer.
- The report should be useful even when only one of signal advisory, single-symbol answer, or advisory conversation exists.
- Paper context should be displayed as downstream local workflow context, not a stronger decision.
- The future implementation should keep row schema simple enough to read in a spreadsheet.

## X. Project Source Recommendation

No immediate Project Source update is required for this planning file alone unless it becomes the accepted anchor for the next implementation milestone.

Do not create `docs/project_sources`. Do not mirror the repository. Do not upload `src/`, `tests/`, `outputs/`, `data/`, manual diagnostics, secrets, or virtual environments as ChatGPT Project Source.

## Y. Recommended Next Task

`Personal MVP Daily Advisory Review Surface Core Report-Only v0.1`

Recommended future implementation scope:

- create `src/quant_replay_system/personal_mvp_daily_advisory_review.py`;
- add `personal-mvp-daily-advisory-review` to `src/quant_replay_system/cli.py`;
- add `tests/test_personal_mvp_daily_advisory_review.py`;
- add `tests/test_personal_mvp_daily_advisory_review_cli.py`;
- write artifacts only under `outputs/reports/personal_mvp_daily_advisory_review/` or a safe `tmp_path` output root;
- preserve all non-approval and no-side-effect boundaries.
