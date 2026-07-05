# Personal MVP Advisory Surface Acceleration Planning v0.1

## A. Decision / Status

phase = personal_mvp_advisory_surface_acceleration_planning  
decision = ready  
privacy_issue_stop = no  
docs_only = yes  
source_code_changed = no  
tests_changed = no  
runtime_changed = no  
selected_next_route = personal_mvp_daily_advisory_review_surface_design_report_only

personal_mvp_focus = yes  
advisory_surface_acceleration = yes  
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

Final planning classification: `PERSONAL_MVP_ADVISORY_SURFACE_ACCELERATION_PLANNING_READY_REPORT_ONLY`.

Final planning verdict: `PERSONAL_MVP_ADVISORY_SURFACE_READY_FOR_DAILY_REVIEW_SURFACE_DESIGN`.

## B. Current Accepted State

The latest checkpoint tag is `v1.82.0` at commit `e247ab6`. The latest accepted planning commit is `1ff7064`, which selected `personal_mvp_advisory_surface_acceleration_planning_report_only` as the next route.

The Source Artifact Byte-Hash boundary is complete for its narrow report-only scope, and Tiny PIT deepening is paused for now. The project should now prioritize a clearer personal/family advisory review path using existing local artifacts before adding new high-risk PIT/source/package capabilities.

## C. Existing Advisory Surface Inventory

The repo already has several advisory and review surfaces that can be reused:

- `signal_semantics`: deterministic mapping from local candidate or scored rows into advisory labels such as `WATCH`, `REVIEW_BUY_CANDIDATE`, `REVIEW_SELL_CANDIDATE`, `HOLD_REVIEW`, `NO_ACTION`, `BLOCKED`, and `DEMO_ONLY`.
- `signal_advisory`: converts a local `current-candidates` artifact into auditable advisory signal rows and local alert preview markdown. It records manual-confirmation and no-auto-order safety fields.
- `single_symbol_advisory`: answers a focused local symbol review question from existing candidate, scored, or signal artifacts, preserving leading-zero symbols and returning safe `NOT_FOUND` when the symbol is absent.
- `single_symbol_advisory` question-style answers: render a deterministic local answer with reasons, caveats, validity, invalidation, and safety fields.
- `advisory_conversation`: deterministic local facade that extracts a six-digit symbol and simple intent from a user-style question, then routes to single-symbol advisory answer artifacts.
- `current_to_paper`: connects selected current-candidates artifacts to local paper decision logs while recording handoff metadata.
- `current_to_paper_review`: creates a review update template from paper decisions for manual review.
- `paper_review_decisions`: applies explicit manual review updates and preserves audit logs.
- `paper_workflow_status`: summarizes local paper workflow state and keeps safety/actionability visible.
- `research-status`: unifies local artifact context and preserves later workflow priority while keeping earlier advisory context visible for audit.

These surfaces are local and advisory. They are not execution systems.

## D. Personal/Family MVP User Journey

The desired personal/family MVP journey is:

```text
local artifacts -> daily advisory review -> single-symbol drill-down -> manual notes / watch decision -> optional paper workflow review -> human confirmation
```

The user should be able to answer:

- What should I review today?
- Which symbols are watch-only, blocked, or manual-review candidates?
- Why did each item appear?
- What is the caveat, validity, and invalidation condition?
- Which artifacts and dates produced the context?
- Is this demo-only, stale, blocked, or missing?
- What still requires manual confirmation?

This journey improves review clarity. It does not approve buying, selling, paper execution, broker use, messages, or trading.

## E. Daily Review Surface Target

A daily personal/family advisory review should show:

- latest candidate/advisory/paper workflow context;
- decision date and artifact lineage;
- top symbols grouped by advisory action;
- `WATCH` and manual-review labels with reason summaries;
- blocked or demo-only rows clearly separated;
- data quality, risk, and source caveats;
- validity and invalidation notes;
- whether a local alert preview exists;
- whether a single-symbol answer exists;
- paper workflow status, if present;
- manual confirmation required;
- no-auto-order, no-live-trading, no-broker, and no-message boundaries;
- next safe manual action.

The daily surface should prefer concise human review text over raw artifact sprawl.

## F. Single-Symbol Review Surface Target

A single-symbol personal/family review should show:

- symbol and name;
- latest available advisory action;
- source artifact type and decision date;
- answer to the user question in concise and detailed forms;
- score/action context where available;
- reason summary;
- risk notes and source caveats;
- entry/exit considerations, if already present in local advisory artifacts;
- invalidation condition and valid-until context;
- demo/not-found/blocked handling;
- manual confirmation requirement;
- explicit no-order/no-broker/no-message boundaries.

`REVIEW_BUY_CANDIDATE` remains human-review-only. It must not be rendered as an instruction.

## G. Research-Status Role

`research-status` should remain the local overview surface. It should answer which latest artifacts exist, which stage has priority, which safety flags are false, and which report paths can be opened for review.

For the personal MVP, `research-status` is a navigation and audit layer, not a decision engine. It should help locate the latest signal advisory, single-symbol answer, advisory conversation, current-to-paper handoff, and paper workflow status without turning any label into an order.

## H. Paper Workflow Role

Paper workflow remains a reviewed local workflow after advisory review. It can help validate handoff, manual review, and reconciliation mechanics, but it does not create real trading permission.

Near-term personal/family usability should treat paper workflow as optional downstream context:

- use it to see whether an advisory candidate has a local paper review path;
- use review templates for manual notes;
- keep `WATCH_ONLY` and rejected cases visible;
- avoid treating paper workflow as strategy performance validation.

Any future paper approval expansion requires separate governance.

## I. What Can Be Reused Now

Without new runtime implementation, the project can reuse:

- existing docs for signal semantics, signal advisory, single-symbol advisory, advisory conversation, current-to-paper, current-to-paper-review, and paper review workflow;
- existing status/index/health conventions;
- existing report-only safety fields;
- local alert preview markdown artifacts;
- single-symbol question-style answer artifacts;
- advisory conversation reports;
- `research-status` as the central audit summary;
- current paper workflow docs and review templates.

The immediate improvement can be a clear runbook/design for how these pieces form one daily personal review routine.

## J. Gaps Blocking Usability

The main blockers are usability blockers, not safety blockers:

- no single daily review surface specification;
- fragmented commands across advisory, single-symbol, conversation, and paper workflow docs;
- no compact daily runbook that tells the user what to inspect first;
- no explicit personal/family review checklist;
- no consolidated wording for demo, blocked, watch, manual-review, and paper-context outcomes;
- no single recommended next implementation path for daily review readout;
- too many governance prompts spent on narrow infrastructure before the personal review surface is easier to use.

## K. Bundlable Near-Term Tasks

The following can be bundled safely if scoped clearly:

- docs-only daily review surface design plus single-symbol surface design;
- runbook/checklist drafting plus research-status navigation guidance;
- report-only daily readout implementation planning plus acceptance criteria;
- bounded docs update plus post-docs governance note;
- focused status/readout tests plus CLI smoke only after a later implementation is explicitly approved.

The bundled prompt must still keep explicit non-approvals, allowed files, STOP conditions, validation commands, and final reporting.

## L. Non-Bundlable Safety Gates

Do not bundle or approve:

- real buy-review eligibility;
- `buy_review_allowed`;
- broker/API/order/message automation;
- real message delivery;
- active replay input;
- real replay execution;
- forward labels or future-label joins;
- training, model, stock_profile, or performance validation;
- paper workflow expansion beyond explicit planning;
- Tiny PIT source_hash, available_time, PIT gate, reviewer authority, or real package candidate semantics;
- protected data writes to `data/raw`, `data/processed`, or `data/cache`;
- Project Source synthesis or cross-document source-pack curation.

These require separate prompts and higher review where appropriate.

## M. Recommended Near-Term Route

Recommended route: design a Personal MVP Daily Advisory Review Surface before implementing new capability.

The next design should produce a precise report-only spec for:

- daily review summary fields;
- single-symbol drill-down fields;
- artifact lineage and report links;
- demo/not-found/blocked/manual-review wording;
- manual note and review checklist expectations;
- how to reuse `research-status`, signal advisory, single-symbol answer, advisory conversation, and paper workflow context;
- the smallest future implementation that would generate a daily readout without trading behavior.

This route makes the system more usable for personal/family review while preserving all current safety boundaries.

## N. Suggested Next Task

`Personal MVP Daily Advisory Review Surface Design Report-Only v0.1`

The task should define the daily review report schema, single-symbol drill-down schema, source artifact references, safety wording, manual checklist, no-order boundaries, and validation strategy. It should not implement runtime behavior unless a later task separately approves implementation.

## O. Explicit Non-Approvals

This planning document does not approve:

- real buy-review;
- `buy_review_allowed`;
- trading;
- broker API;
- order placement;
- message delivery;
- active replay input;
- real replay execution;
- labels/training/model/stock_profile/paper expansion;
- strategy performance validation;
- data/raw, data/processed, or data/cache writes;
- Project Source package creation;
- `docs/project_sources`;
- any new high-risk Tiny PIT source/PIT/package semantics.

## P. Open Blockers

No blocker was found for moving to daily advisory review surface design.

## Q. Non-Blocking Notes

- A daily review surface can start as a report-only design and later become a bounded local readout if approved.
- The next implementation, when approved, should prefer existing local artifact paths and status views instead of creating new data dependencies.
- The daily review surface should be explicit about stale/missing artifacts and avoid inventing advice.
- Prompt compression remains useful: daily and single-symbol surface design can be handled together, but implementation should stay bounded.

## R. Project Source Recommendation

No immediate Project Source update is required solely for this docs-only planning file unless it becomes the accepted next-decision anchor. If committed, include it later in a curated external Project Source refresh as planning context only.

Do not create `docs/project_sources`. Do not mirror the repo. Do not upload `src/`, `tests/`, `outputs/`, `data/`, manual diagnostics, secrets, or virtual environments as ChatGPT Project Source.
