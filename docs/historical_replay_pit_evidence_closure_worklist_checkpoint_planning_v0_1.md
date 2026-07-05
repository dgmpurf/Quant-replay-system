# Historical Replay PIT Evidence Closure Worklist Checkpoint Planning v0.1

phase = historical_replay_pit_evidence_closure_worklist_checkpoint_planning
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_checkpoint = v1.83.0
latest_checkpoint_commit = 46f634b
latest_repo_commit = 3e96ab0
proposed_checkpoint = v1.84.0
selected_historical_decision_date = 2024-04-02
selected_universe = etf_core
checkpoint_docs_approved = no
checkpoint_tag_approved = no
source_update_approved = no
selected_next_route = Historical Replay PIT Evidence Closure Worklist Checkpoint Docs and Validation Report-Only v0.1

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

## A. Decision / Status

Decision: ready for a separate checkpoint docs and validation task.

This document is checkpoint planning only. It verifies that the Historical Replay PIT Evidence Closure Worklist chain appears internally coherent and ready for a future checkpoint documentation task if validation passes. It does not create checkpoint docs, approve a checkpoint tag, approve a Project Source update, close PIT evidence, approve PIT admissibility, create active replay input, run replay, freeze decisions, create forward labels, compute metrics, adjust weights/formulas/thresholds/models, validate stock profiles, expand paper workflow authority, approve buy-review, or authorize trading.

## B. Current Accepted State

The latest accepted checkpoint remains `v1.83.0` at commit `46f634b`. The current repository head inspected for this planning report is `3e96ab0`, described as `v1.83.0-14-g3e96ab0`.

External ChatGPT Project Source is updated to `v1.83.0`. Historical Replay Training Loop is now the active mainline, and the Personal MVP advisory refresh branch is paused, not abandoned.

The selected historical replay audit sample remains:

```text
historical_decision_date = 2024-04-02
universe = etf_core
```

The selected sample is worklist and PIT gap context only. It is not replay-ready input.

## C. Implementation Chain Summary

The completed chain inspected for this planning report is:

| commit | summary | checkpoint meaning |
|---|---|---|
| `6347f94` | docs: reanchor historical replay training loop | Re-established historical replay as the active mainline. |
| `25dec8f` | docs: audit historical replay sample selection and PIT gaps | Selected `2024-04-02 / etf_core` as the first audit sample. |
| `61e7f00` | docs: plan PIT evidence closure for selected replay sample | Mapped source, timing, reviewer, quality, survivorship, and downstream blockers. |
| `c0ca318` | docs: design PIT evidence closure worklist for selected replay sample | Defined row-level worklist schema, closure vocabulary, and non-approval fields. |
| `87be2f5` | Add historical replay PIT evidence closure worklist core | Added deterministic report-only worklist artifacts. |
| `6848df4` | Add historical replay PIT evidence closure worklist artifact views | Added index, health, and status views. |
| `472f5d4` | Add historical replay PIT evidence closure worklist CLI | Added core/index/health/status CLI family. |
| `3e0336d` | docs: plan PIT evidence closure worklist research-status integration | Planned lower-priority dashboard exposure. |
| `3e96ab0` | Integrate historical replay PIT evidence closure worklist research status | Exposed worklist context through `research-status` while preserving paper workflow priority. |

The chain is coherent: it moves from mainline re-anchor to sample selection, evidence gap plan, worklist design, report-only implementation, views, CLI, and research-status integration.

## D. Selected Sample and Scope

The worklist scope is a selected historical replay evidence closure worklist for:

```text
signal_date = 2024-04-02
universe_name = etf_core
```

The scope is local, report-only, diagnostic-only, and selected-sample-specific. It organizes missing and context-only evidence families such as official status, source/raw-document lineage, source hash and local hash context, revision id, available-time metadata, reviewer/no-hit context, quality/limitation fields, profile conflict, and survivorship rationale.

It does not collect or close new evidence. It does not create active replay input. It does not run current-candidates or snapshots. It does not read protected raw data areas. It does not execute replay or create labels.

## E. Feature Boundary

The feature is a worklist, not an adjudicator.

Allowed meaning:

- row-level evidence collection scaffold;
- blocker and warning visibility;
- manual review context;
- no-hit context visibility;
- `closure_ready_not_pit_approved` as an explicit non-approval state;
- lower-priority dashboard context.

Forbidden meaning:

- PIT evidence closure;
- PIT admissibility;
- replay readiness;
- active replay input;
- replay execution;
- replay decision freeze;
- forward labels;
- metric computation;
- model training or parameter adjustment;
- stock_profile validation;
- paper expansion approval;
- real buy-review;
- trading permission.

A worklist row is not PIT approval. `closure_ready_not_pit_approved` is not PIT admissible. Reviewer no-hit acceptance is not source reliability scoring. Forward returns remain future information. The 8-layer factor taxonomy remains the primary structure; fixed 12 factors are not final.

## F. Core / Views / CLI / Research-Status Readiness

Core readiness: the core module emits report-only artifacts with row-level worklist, summary, metadata, safety flags, and non-approval fields. The core guards protected output roots and keeps safety flags false.

Views readiness: index, health, and status modules expose navigation, health checks, status summaries, closure counts, and safety fields. Health checks fail unsafe flags and preserve the non-approval distinction for closure-ready context.

CLI readiness: the command family is present:

- `historical-replay-pit-evidence-closure-worklist`
- `historical-replay-pit-evidence-closure-worklist-index`
- `historical-replay-pit-evidence-closure-worklist-health`
- `historical-replay-pit-evidence-closure-worklist-status`

Research-status readiness: `research-status` exposes latest worklist context through fields prefixed with `latest_historical_replay_pit_evidence_closure_worklist_`, including run id, date, universe, status, health, workflow stage, report path, count fields, recommended next task, and negative safety fields.

## G. Research-Status Priority Audit

The worklist context is lower-priority research context only. It is visible in the dashboard and CLI, but it must not override later paper workflow priority.

The integration includes focused dashboard tests confirming that `PAPER_WORKFLOW_READY` remains the final workflow stage when paper workflow context exists. The worklist status appears as contextual metadata and negative proof fields only.

The planned checkpoint task should re-run the dashboard tests and CLI smoke to verify:

- worklist context is visible when status artifacts exist;
- all worklist safety fields remain false;
- `PAPER_WORKFLOW_READY` remains preserved;
- no field names or wording imply PIT approval, replay readiness, buy-review readiness, performance validation, or trading readiness.

## H. Safety and Non-Approval Audit

The chain remains report-only / diagnostic-only / local-only. The future checkpoint task must verify that these fields remain false or unapproved:

| area | required state |
|---|---|
| PIT closure | `pit_evidence_closed=false`, `pit_evidence_closure_approved=no` |
| PIT admissibility | `pit_admissibility_approved=false/no` |
| Replay input | `active_replay_input=false`, `active_replay_input_approved=no` |
| Replay execution | `replay_execution_allowed=false`, `real_replay_execution_approved=no` |
| Decision freeze | `replay_decision_freeze_allowed=false`, `replay_decision_freeze_approved=no` |
| Labels | `forward_labels_created=false/no`, `forward_label_creation_approved=no` |
| Training and metrics | `training_dataset_created=false/no`, `metric_computation_performed=false`, `metric_computation_approved=no` |
| Model and parameters | `model_training_performed=false`, `model_training_approved=no`, `weights_or_thresholds_adjustment_approved=no` |
| Stock profile and paper | `stock_profile_validation_created=false`, `stock_profile_expansion_approved=no`, `paper_expansion_allowed=false/no` |
| Buy-review and trading | `buy_review_allowed=false/no`, `trading_allowed=false/no` |
| Side effects | broker/order/message/API/current-candidates/snapshot/signal/data-write flags remain false/no |

## I. Disclosure and Wording Audit

The checkpoint task should keep all risky words in negative policy context only. It must not use positive readiness terms such as `PIT_ADMISSIBLE`, `PIT_APPROVED`, `READY_FOR_REPLAY`, `ACTIVE_REPLAY_INPUT_READY`, `BUY_REVIEW_READY`, `TRADING_READY`, `APPROVED_FOR_PAPER`, or `PERFORMANCE_VALIDATED` to describe the worklist state.

Acceptable wording:

- "not PIT admissible";
- "not PIT approval";
- "not replay-ready";
- "not buy-review";
- "not trading";
- "context only";
- "lower-priority research context".

The future checkpoint docs should avoid implying that a closure-ready count can be consumed by replay workflows. It is a review organization signal only.

## J. Validation Plan for Checkpoint Task

The future checkpoint docs and validation task should run:

```text
set PYTHONPATH=src
.venv\Scripts\python.exe -m pytest tests/test_historical_replay_pit_evidence_closure_worklist.py -q
.venv\Scripts\python.exe -m pytest tests/test_historical_replay_pit_evidence_closure_worklist_views.py -q
.venv\Scripts\python.exe -m pytest tests/test_historical_replay_pit_evidence_closure_worklist_cli.py -q
.venv\Scripts\python.exe -m pytest tests/test_local_research_dashboard.py -q
.venv\Scripts\python.exe -m pytest tests/test_historical_replay_pit_evidence_closure_worklist.py tests/test_historical_replay_pit_evidence_closure_worklist_views.py tests/test_historical_replay_pit_evidence_closure_worklist_cli.py tests/test_local_research_dashboard.py -q
.venv\Scripts\python.exe -m pytest -m "not slow" -q
```

The future checkpoint task should also run a temporary-root CLI smoke:

```text
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-pit-evidence-closure-worklist
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-pit-evidence-closure-worklist-index
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-pit-evidence-closure-worklist-health
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-pit-evidence-closure-worklist-status
.venv\Scripts\python.exe -m quant_replay_system.cli research-status
```

The CLI smoke should use temporary output roots and must not write `data/raw`, `data/processed`, or `data/cache`.

Required static checks:

```text
git diff --check
git status --short --branch
git status --short -- docs\project_sources
git ls-files data/raw data/processed data/cache outputs/reports
```

Expected protected tracked scan:

```text
data/processed/.gitkeep
data/raw/.gitkeep
outputs/reports/.gitkeep
```

## K. Proposed Checkpoint Docs Scope

The future checkpoint task should create or update only checkpoint documentation and accepted project docs needed for the checkpoint.

Expected future docs scope:

- create `docs/release_checkpoint_v1.84.0.md`;
- create or update a worklist feature doc only if not already sufficiently documented;
- update `README.md` with the v1.84.0 summary only if checkpoint review accepts it;
- update `docs/local_research_dashboard.md` only if the research-status context is not already documented sufficiently;
- create `SOURCE_UPDATE_NOTES_v1_84_0.md` only after checkpoint documentation is accepted for manual Source update planning.

The checkpoint task must not create `docs/project_sources`, a Project Source package, or a repository mirror of external Project Source files.

## L. Source Update Rule

No Project Source update is approved by this planning report.

If the future checkpoint docs and validation task passes and the user manually commits/tags `v1.84.0`, a separate changed-files-only external Project Source update task may be considered. That task must remain curated and must not recreate `docs/project_sources`.

## M. Open Blockers

No blocking issue was found for moving to a checkpoint docs and validation task.

The checkpoint task remains conditional on validation:

- focused worklist tests pass;
- dashboard tests pass;
- full non-slow tests pass;
- CLI smoke passes from temporary roots;
- static safety scan shows no positive approval wording or unsafe flags;
- protected tracked scan remains limited to placeholders;
- `docs/project_sources` remains absent.

If any of those fail, the route should switch to a focused hardening task before checkpoint docs are finalized.

## N. Non-Blocking Notes

The status view and research-status integration use a recommended next task string. The next checkpoint task should review whether the post-checkpoint recommended next task should point to governance audit / next decision planning after v1.84.0, but this wording review must not change worklist semantics.

The selected sample remains a single-date `2024-04-02 / etf_core` evidence organization surface. It should not be generalized into production evidence closure during the checkpoint.

The worklist may include mixed stock/ETF profile context under a legacy `etf_core` label. That is a warning/review dimension, not approval or rejection by itself.

## O. Candidate Next Routes

| route | description | decision |
|---|---|---|
| A. Historical Replay PIT Evidence Closure Worklist Checkpoint Docs and Validation Report-Only v0.1 | Create checkpoint docs, run focused and full validation, and prepare for manual review/commit/tag. | Selected if no blockers. |
| B. Historical Replay PIT Evidence Closure Worklist Research-Status Hardening Report-Only v0.1 | Fix field, priority, or wording issues if research-status integration is not checkpoint-ready. | Reserve. |
| C. Historical Replay PIT Evidence Closure Worklist Artifact Views / CLI Hardening Report-Only v0.1 | Fix core/view/CLI issues if validation finds status, health, or smoke failures. | Reserve. |
| D. Pause and manually inspect generated worklist artifacts before checkpoint docs | Use if a human wants to review generated artifacts before committing a checkpoint. | Reserve. |
| E. Project Source update now | Not selected; Source update should wait until after checkpoint commit/tag. | Rejected for now. |

## P. Selected Next Route

Selected route:

```text
Historical Replay PIT Evidence Closure Worklist Checkpoint Docs and Validation Report-Only v0.1
```

Proposed checkpoint version:

```text
v1.84.0
```

The version is proposed only. This planning report does not approve checkpoint docs, does not approve a checkpoint tag, and does not approve Source update.

## Q. Why Selected Route Is Safe

The selected route is safe because the implementation chain has already separated worklist context from PIT closure and downstream replay authority. The checkpoint task can be limited to documentation and validation. It does not need new runtime behavior, source registry mutation, evidence collection, PIT adjudication, replay execution, label creation, model work, stock_profile validation, paper expansion, buy-review, or trading behavior.

## R. What Must Not Be Bundled

The future checkpoint task must not bundle:

1. Worklist evidence closure.
2. PIT admissibility approval.
3. Current-candidates execution.
4. Snapshot build.
5. Active replay input creation.
6. Replay execution.
7. Replay decision freeze.
8. Forward-return label creation.
9. Training, evaluation, metric computation, or model work.
10. Weight, formula, threshold, or model adjustment.
11. Stock-profile validation.
12. Paper workflow expansion.
13. Buy-review approval.
14. Broker, order, message, external API, LLM, or trading behavior.
15. Protected data writes.
16. Project Source package generation.
17. `docs/project_sources` creation.

## S. ChatGPT/Codex Mode Recommendation

Use Codex high for the next checkpoint docs and validation task. The task is mostly documentation, validation, and safety scan execution.

Use ChatGPT review before manual commit/tag if the user wants an additional review gate.

Use Pro or Pro Extended only before any task that adjudicates ambiguous available-time evidence, source reliability, reviewer authority, mixed production universe policy, PIT admissibility, replay readiness, label creation, metric methodology, model changes, paper expansion, buy-review, or trading.

## T. Commit/Tag/Source Recommendation

Commit recommendation for this planning report, if accepted:

```text
docs: plan PIT evidence closure worklist checkpoint
```

Tag recommendation: no tag for this planning report alone.

Checkpoint recommendation: consider `v1.84.0` only in the separate checkpoint docs and validation task after focused tests, full non-slow validation, CLI smoke, static scan, protected tracked scan, and ChatGPT/user review pass.

Source recommendation: no Source update now. Consider a separate curated external Source update only after `v1.84.0` is manually committed and tagged.

## U. Recommended Next Task

Recommended next task:

```text
Historical Replay PIT Evidence Closure Worklist Checkpoint Docs and Validation Report-Only v0.1
```

Goal for that task: create v1.84.0 checkpoint documentation, run the required validation plan, confirm all non-approval and safety boundaries, and report whether manual commit/tag is safe. It must not update Project Source, create `docs/project_sources`, close PIT evidence, approve PIT admissibility, run replay, create labels, train models, expand paper workflow, approve buy-review, or authorize trading.
