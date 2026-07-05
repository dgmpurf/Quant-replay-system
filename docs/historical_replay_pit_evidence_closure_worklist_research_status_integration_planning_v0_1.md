# Historical Replay PIT Evidence Closure Worklist Research-Status Integration Planning v0.1

phase = historical_replay_pit_evidence_closure_worklist_research_status_integration_planning
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_checkpoint = v1.83.0
latest_checkpoint_commit = 46f634b
latest_repo_commit = 472f5d4
research_status_integration_approved = no
selected_next_route = Historical Replay PIT Evidence Closure Worklist Research-Status Integration Report-Only v0.1

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

Decision: ready for a separate report-only research-status integration implementation task.

This planning report only defines how the Historical Replay PIT Evidence Closure Worklist status should be surfaced in `research-status`. It does not implement research-status integration, does not close PIT evidence, does not approve PIT admissibility, does not create active replay input, and does not authorize replay, labels, training, model, stock_profile, paper expansion, buy-review, or trading.

## B. Current Accepted State

The current checkpoint anchor remains `v1.83.0` at commit `46f634b`. The local repository head inspected for this plan is `472f5d4`, which added the Historical Replay PIT Evidence Closure Worklist CLI family:

- `historical-replay-pit-evidence-closure-worklist`
- `historical-replay-pit-evidence-closure-worklist-index`
- `historical-replay-pit-evidence-closure-worklist-health`
- `historical-replay-pit-evidence-closure-worklist-status`

The selected sample remains `2024-04-02 / etf_core`. Worklist artifacts are report-only context for evidence closure planning. A worklist row is not PIT approval. `closure_ready_not_pit_approved` is not PIT admissible. Reviewer no-hit acceptance is not source reliability scoring.

## C. Existing Research-Status Pattern Summary

The existing `local_research_dashboard` pattern scans local status artifacts, creates a context record, encodes detail in semicolon-separated `notes`, then maps those notes into `research-status` fields. Adjacent patterns use:

- a `*_context_visible` boolean;
- `latest_*_run_id`, `latest_*_status`, `latest_*_health_status`, and `latest_*_workflow_stage`;
- artifact/report/metadata paths;
- count fields and review-state fields;
- explicit negative proof and safety flags;
- a `recommended_next_task`;
- final workflow priority preservation so later paper workflow evidence can keep `PAPER_WORKFLOW_READY`.

The Source Artifact Byte-Hash, Preflight, Reviewer Authority / Quality / Limitation, and Source Hash / Revision ID / Available-Time sections in `docs/local_research_dashboard.md` all follow this context-only pattern. They explicitly prevent contextual artifacts from becoming package approval, PIT admissibility, replay readiness, buy-review readiness, performance validation, or trading readiness.

## D. Worklist Status Artifact Discovery Plan

The implementation should scan the existing status artifact root:

```text
outputs/reports/manual_diagnostics/historical_replay_pit_evidence_closure_worklist_v0_1/status/
```

The preferred implementation should reuse `run_historical_replay_pit_evidence_closure_worklist_status` and read its `summary` fields, matching adjacent dashboard patterns that call status APIs rather than parsing arbitrary files first. If no status artifacts exist, research-status should set context visibility to false or use empty/default no-artifact fields without changing top-level workflow priority.

The status summary currently exposes `latest_worklist_run_id`, status, health, workflow stage, signal date, universe name, artifact/report/metadata paths, review counts, `report_only`, `diagnostic_only`, and `latest_*` safety fields.

## E. Proposed Fields

Add these research-status fields:

- `historical_replay_pit_evidence_closure_worklist_context_visible`
- `latest_historical_replay_pit_evidence_closure_worklist_run_id`
- `latest_historical_replay_pit_evidence_closure_worklist_signal_date`
- `latest_historical_replay_pit_evidence_closure_worklist_universe_name`
- `latest_historical_replay_pit_evidence_closure_worklist_status`
- `latest_historical_replay_pit_evidence_closure_worklist_health_status`
- `latest_historical_replay_pit_evidence_closure_worklist_workflow_stage`
- `latest_historical_replay_pit_evidence_closure_worklist_report_path`
- `latest_historical_replay_pit_evidence_closure_worklist_row_count`
- `latest_historical_replay_pit_evidence_closure_worklist_blocked_count`
- `latest_historical_replay_pit_evidence_closure_worklist_missing_evidence_count`
- `latest_historical_replay_pit_evidence_closure_worklist_context_only_count`
- `latest_historical_replay_pit_evidence_closure_worklist_needs_manual_review_count`
- `latest_historical_replay_pit_evidence_closure_worklist_no_hit_review_needed_count`
- `latest_historical_replay_pit_evidence_closure_worklist_no_hit_accepted_context_count`
- `latest_historical_replay_pit_evidence_closure_worklist_closure_ready_not_pit_approved_count`
- `latest_historical_replay_pit_evidence_closure_worklist_profile_conflict_count`
- `latest_historical_replay_pit_evidence_closure_worklist_survivorship_warning_count`
- `latest_historical_replay_pit_evidence_closure_worklist_recommended_next_task`

All proposed fields are visible context only. They do not promote evidence, approve PIT status, or authorize downstream workflows.

## F. Proposed Safety / Negative Proof Fields

Expose these safety fields exactly as negative proof context and keep them false:

- `latest_historical_replay_pit_evidence_closure_worklist_pit_evidence_closed`
- `latest_historical_replay_pit_evidence_closure_worklist_pit_admissibility_approved`
- `latest_historical_replay_pit_evidence_closure_worklist_active_replay_input`
- `latest_historical_replay_pit_evidence_closure_worklist_replay_execution_allowed`
- `latest_historical_replay_pit_evidence_closure_worklist_replay_decision_freeze_allowed`
- `latest_historical_replay_pit_evidence_closure_worklist_forward_labels_created`
- `latest_historical_replay_pit_evidence_closure_worklist_training_dataset_created`
- `latest_historical_replay_pit_evidence_closure_worklist_metric_computation_performed`
- `latest_historical_replay_pit_evidence_closure_worklist_model_training_performed`
- `latest_historical_replay_pit_evidence_closure_worklist_stock_profile_validation_created`
- `latest_historical_replay_pit_evidence_closure_worklist_paper_expansion_allowed`
- `latest_historical_replay_pit_evidence_closure_worklist_buy_review_allowed`
- `latest_historical_replay_pit_evidence_closure_worklist_trading_allowed`
- `latest_historical_replay_pit_evidence_closure_worklist_broker_api_called`
- `latest_historical_replay_pit_evidence_closure_worklist_order_placed`
- `latest_historical_replay_pit_evidence_closure_worklist_message_sent`
- `latest_historical_replay_pit_evidence_closure_worklist_external_api_called`
- `latest_historical_replay_pit_evidence_closure_worklist_llm_api_called`
- `latest_historical_replay_pit_evidence_closure_worklist_current_candidates_executed`
- `latest_historical_replay_pit_evidence_closure_worklist_snapshot_built`
- `latest_historical_replay_pit_evidence_closure_worklist_signal_semantics_mutated`
- `latest_historical_replay_pit_evidence_closure_worklist_data_raw_written`
- `latest_historical_replay_pit_evidence_closure_worklist_data_processed_written`
- `latest_historical_replay_pit_evidence_closure_worklist_data_cache_written`

If any safety field is true, future implementation should surface a warning or fail-safe health context and must not convert the worklist into approval.

## G. Workflow Priority Rule

Worklist context is lower-priority research context. It must not override `PAPER_WORKFLOW_READY` when later paper workflow evidence exists. It also must not override future valid active replay, replay execution, decision freeze, label, model, stock_profile, paper, buy-review, or trading statuses.

For now, the final research-status workflow stage should remain the existing higher-priority stage. Worklist status may be visible through fields and notes only.

## H. Forbidden Meanings and Wording

Research-status must not expose or imply these meanings as positive readiness:

- `PIT_ADMISSIBLE`
- `PIT_APPROVED`
- `READY_FOR_REPLAY`
- `ACTIVE_REPLAY_INPUT_READY`
- `BUY_REVIEW_READY`
- `TRADING_READY`
- `APPROVED_FOR_PAPER`
- `PERFORMANCE_VALIDATED`

These strings may appear only in negative policy context such as this section. `closure_ready_not_pit_approved` must remain a non-approval term. Reviewer no-hit acceptance must remain context and must not become source reliability scoring.

## I. Research-Status CLI Display Plan

Future `research-status` output should print a compact block similar to adjacent context blocks:

- `historical_replay_pit_evidence_closure_worklist_context_visible`
- latest run id, status, health, workflow stage;
- signal date and universe name;
- report path;
- row and blocker counts;
- no-hit and manual-review counts;
- closure-ready-not-PIT-approved count;
- profile conflict and survivorship warning counts;
- recommended next task;
- all safety fields as false.

The CLI output should include an explicit sentence that this is worklist context only and not PIT approval, replay readiness, buy-review readiness, performance validation, or trading permission.

## J. Focused Test Plan

Future implementation should add or update focused tests in `tests/test_local_research_dashboard.py` and any existing research-status tests that cover dashboard field export.

Required test points:

1. A status artifact makes `historical_replay_pit_evidence_closure_worklist_context_visible` true.
2. Latest run id, signal date, universe name, status, health, workflow stage, and report path are exported.
3. Row, blocker, missing-evidence, context-only, manual-review, no-hit, profile-conflict, and survivorship counts are exported.
4. `closure_ready_not_pit_approved_count` is exported without any PIT approval field turning true.
5. Every safety field remains false.
6. Final workflow priority preserves `PAPER_WORKFLOW_READY` when paper workflow evidence is present.
7. No forbidden positive readiness wording appears in exported research-status fields.
8. The recommended next task points to checkpoint planning or the accepted next planning step after integration.
9. No `docs/project_sources` folder is created.
10. No data/raw, data/processed, or data/cache paths are written.

## K. CLI Smoke Plan

The later implementation task should run a focused CLI smoke from temporary roots:

```text
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-pit-evidence-closure-worklist --root <tmp_reports> --output-dir <tmp_worklist> --run-id smoke
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-pit-evidence-closure-worklist-index --root <tmp_worklist> --output-dir <tmp_worklist>\index
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-pit-evidence-closure-worklist-health --root <tmp_worklist> --output-dir <tmp_worklist>\health
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-pit-evidence-closure-worklist-status --root <tmp_worklist> --output-dir <tmp_worklist>\status
.venv\Scripts\python.exe -m quant_replay_system.cli research-status
```

Expected CLI smoke result: worklist commands exit according to existing style, research-status exits 0, context fields are visible, final priority remains safe, and all non-approval fields remain false.

## L. Static Safety Scan Plan

Future implementation should run a scan over changed source, tests, and docs for:

- forbidden positive readiness strings;
- approval flags set to yes or true;
- `docs/project_sources`;
- protected data writes;
- current-candidates and snapshot execution wording;
- broker, order, message, external API, and LLM side effects.

Any forbidden string should be allowed only in negative assertions, guard lists, or explicit non-approval policy.

## M. Open Blockers

No blocking issue was found for a small, safe research-status integration plan.

One implementation detail remains: the live status module currently has `recommended_next_task = Historical Replay PIT Evidence Closure Worklist CLI Report-Only v0.1`, while the CLI already prints research-status planning as the next task. Future implementation should decide whether to preserve status-module history or update that next-action string after integration, without changing worklist semantics.

## N. Non-Blocking Notes

The existing status summary lacks an explicit `context_only_count` column, while the proposed research-status field list includes it. A future implementation can derive it from indexed metadata if available, default it to 0/empty when absent, or add it in a separate status hardening task. This should not block research-status integration if it is documented as derived or absent-safe.

The selected sample remains a planning/worklist context for `2024-04-02 / etf_core`; it is not a replay-ready input package.

## O. Candidate Next Routes

A. Historical Replay PIT Evidence Closure Worklist Research-Status Integration Report-Only v0.1

B. Historical Replay PIT Evidence Closure Worklist Checkpoint Planning Report-Only v0.1

C. Historical Replay PIT Evidence Closure Worklist Artifact Views Hardening Report-Only v0.1

D. Pause and review generated worklist artifacts manually before integration

## P. Selected Next Route

Selected route: A. Historical Replay PIT Evidence Closure Worklist Research-Status Integration Report-Only v0.1.

## Q. Why Selected Route Is Safe

The existing dashboard architecture already supports lower-priority context blocks with safety fields and priority preservation. The worklist status artifacts expose bounded metadata, counts, report paths, and negative proof fields. No source content, raw evidence bytes, full hash, package payload, replay input, label, training, model, stock_profile, paper approval, buy-review, or trading surface is required for this integration.

## R. What Must Not Be Bundled

The next task must not bundle checkpoint docs, Project Source updates, source package generation, worklist evidence closure, PIT admissibility approval, active replay input creation, replay execution, decision freeze, forward labels, training/evaluation, metric computation, model work, stock_profile validation, paper expansion, buy-review, trading, current-candidates, snapshots, signal_semantics mutation, broker/API/order/message behavior, or protected data writes.

## S. ChatGPT/Codex Mode Recommendation

Use Codex high for the next implementation task. The implementation is a bounded dashboard/research-status field mapping with focused tests. Escalation to a broader design mode is not required unless field-priority behavior conflicts with existing `PAPER_WORKFLOW_READY` preservation.

## T. Commit/Tag/Source Recommendation

No tag is recommended for this planning report alone unless the user wants a planning-only checkpoint. No immediate Project Source update is recommended. If the following research-status integration is implemented and accepted, checkpoint docs and Source update decisions can be considered in a later dedicated task.

Recommended commit message if this planning report is accepted:

```text
docs: plan PIT evidence closure worklist research-status integration
```

## U. Recommended Next Task

Historical Replay PIT Evidence Closure Worklist Research-Status Integration Report-Only v0.1

