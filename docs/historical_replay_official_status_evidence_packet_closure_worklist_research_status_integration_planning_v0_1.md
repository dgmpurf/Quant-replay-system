# Historical Replay Official Status Evidence Packet Closure Worklist Research-Status Integration Planning v0.1

phase = historical_replay_official_status_evidence_packet_closure_worklist_research_status_integration_planning
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_checkpoint = v1.84.0
latest_checkpoint_commit = 94775cf
latest_repo_commit = 07a97ee
research_status_integration_approved = no
selected_next_route = Historical Replay Official Status Evidence Packet Closure Worklist Research-Status Integration Report-Only v0.1

official_status_evidence_closure_approved = no
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

This docs-only planning report is ready. It defines the minimum safe plan for a later report-only `research-status` integration that exposes Historical Replay Official Status Evidence Packet Closure Worklist context.

The selected next route is:

`Historical Replay Official Status Evidence Packet Closure Worklist Research-Status Integration Report-Only v0.1`

The selected route is implementation of context visibility only. It must not close official status evidence, close PIT evidence, approve PIT admissibility, create replay input, run replay, freeze decisions, create forward labels, compute metrics, train models, expand stock_profile or paper authority, create buy-review eligibility, or authorize trading.

## B. Current Accepted State

The current accepted checkpoint is `v1.84.0` at commit `94775cf`. The latest repository commit for this planning report is expected to be `07a97ee`, which added the official-status worklist CLI family.

External ChatGPT Project Source is updated to v1.84.0 and is not mirrored into the repository.

Current official-status worklist command family:

- `historical-replay-official-status-evidence-packet-closure-worklist`
- `historical-replay-official-status-evidence-packet-closure-worklist-index`
- `historical-replay-official-status-evidence-packet-closure-worklist-health`
- `historical-replay-official-status-evidence-packet-closure-worklist-status`

Existing core and views expose the selected `2024-04-02 / etf_core` sample as a report-only, diagnostic-only, local-only worklist with these expected counts:

| Field | Expected value |
| --- | ---: |
| row_count | 9 |
| stock_row_count | 7 |
| etf_row_count | 2 |
| blocked_count | 9 |
| missing_official_evidence_count | 9 |
| needs_manual_review_count | 9 |
| no_hit_review_needed_count | 9 |
| no_hit_accepted_context_count | 0 |
| packet_row_ready_not_pit_approved_count | 0 |
| profile_conflict_count | 7 |
| survivorship_warning_count | 9 |

## C. Existing Research-Status Pattern Summary

Existing `research-status` integration lives in `src/quant_replay_system/local_research_dashboard.py`, with CLI display through `src/quant_replay_system/cli.py`.

The adjacent Historical Replay PIT Evidence Closure Worklist pattern uses this shape:

1. Define a component name, workflow area, latest-field lists, integer count fields, safety fields, and result fields.
2. Scan a status artifact root by calling the status view function.
3. Convert the status result into a summary dictionary.
4. Encode summary fields into a note string on a dashboard record.
5. Parse notes back into summary fields.
6. Convert parsed summary fields into `LocalResearchDashboardResult` kwargs.
7. Emit summary CSV, metadata JSON, and CLI `research-status` lines.
8. Keep the worklist component lower priority than paper workflow evidence, preserving `PAPER_WORKFLOW_READY`.

The official-status integration should reuse this pattern and avoid bespoke discovery logic where the existing status module already exposes a summary contract.

## D. Official-Status Worklist Status Artifact Discovery Plan

The later implementation should discover the latest official-status worklist by calling:

`run_historical_replay_official_status_evidence_packet_closure_worklist_status`

Default status root should remain derived from:

`outputs/reports/manual_diagnostics/historical_replay_official_status_evidence_packet_closure_worklist_v0_1/`

The scanner should treat `root/status` as a status view directory and otherwise treat `root` as the worklist artifact root, matching the adjacent PIT evidence worklist scanner.

The implementation should not run the core worklist command from `research-status`. It should only read/summarize existing status artifacts through the status API. If no artifacts exist, the official-status context should be absent or explicitly no-artifacts context, not a trigger to generate worklist outputs.

## E. Proposed Fields

Recommended context field:

- `historical_replay_official_status_evidence_packet_closure_worklist_context_visible`

Recommended latest fields:

- `latest_historical_replay_official_status_evidence_packet_closure_worklist_run_id`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_signal_date`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_universe_name`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_status`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_health_status`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_workflow_stage`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_report_path`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_recommended_next_task`

Recommended count fields:

- `latest_historical_replay_official_status_evidence_packet_closure_worklist_row_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_stock_row_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_etf_row_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_blocked_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_missing_official_evidence_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_needs_manual_review_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_no_hit_review_needed_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_no_hit_accepted_context_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_packet_row_ready_not_pit_approved_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_profile_conflict_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_survivorship_warning_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_listed_status_missing_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_delisted_status_missing_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_st_status_missing_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_st_not_applicable_policy_missing_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_suspension_or_trading_status_missing_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_universe_membership_missing_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_source_id_missing_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_permission_class_missing_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_revision_id_missing_count`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_available_time_missing_count`

These fields are context fields only. Counts are evidence-gap counts, not closure counts.

## F. Proposed Safety / Negative Proof Fields

The later implementation should expose these fields and keep them false:

- `latest_historical_replay_official_status_evidence_packet_closure_worklist_official_status_evidence_closed`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_pit_evidence_closed`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_pit_admissibility_approved`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_active_replay_input`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_replay_execution_allowed`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_replay_decision_freeze_allowed`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_forward_labels_created`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_training_dataset_created`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_metric_computation_performed`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_model_training_performed`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_stock_profile_validation_created`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_paper_expansion_allowed`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_buy_review_allowed`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_trading_allowed`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_broker_api_called`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_order_placed`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_message_sent`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_external_api_called`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_llm_api_called`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_current_candidates_executed`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_snapshot_built`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_signal_semantics_mutated`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_data_raw_written`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_data_processed_written`
- `latest_historical_replay_official_status_evidence_packet_closure_worklist_data_cache_written`

These fields should be parsed from status summary values when available and should default to false when no artifact exists.

## G. Workflow Priority Rule

Official-status worklist context is lower-priority research context only. It should be visible in `research-status`, summary CSV, metadata JSON, and CLI output, but it must not control the final workflow stage when higher-priority evidence exists.

Priority rules:

- Preserve `PAPER_WORKFLOW_READY` when paper workflow evidence exists.
- Do not override future valid active replay, replay execution, decision freeze, labels, metric, model, stock_profile, paper, buy-review, or trading statuses.
- Use official-status worklist stage only as a component stage and note, not as global readiness.
- Treat WARN health as manual-review context, not workflow failure, unless the health status is unsafe fail.

## H. Forbidden Meanings and Wording

The integration must not expose or imply the following as positive readiness:

- `PIT_ADMISSIBLE`
- `PIT_APPROVED`
- `READY_FOR_REPLAY`
- `ACTIVE_REPLAY_INPUT_READY`
- `BUY_REVIEW_READY`
- `TRADING_READY`
- `APPROVED_FOR_PAPER`
- `PERFORMANCE_VALIDATED`

Forbidden interpretations:

- `packet_row_ready_not_pit_approved_count` does not mean PIT approved.
- `no_hit_accepted_context_count` does not mean source reliability scoring.
- `official_status_evidence_closed=false` cannot be overridden by reviewer no-hit context.
- Same-day quotation presence does not prove listed status, not-delisted status, no-ST status, not-suspended status, universe membership, or survivorship safety.
- A status artifact is not an evidence packet and not evidence closure.

Risky status words may appear only in negative or non-approval policy text.

## I. Research-Status CLI Display Plan

The later implementation should make `quant_replay_system.cli research-status` print:

- context visibility;
- latest run id;
- signal date and universe;
- status, health status, workflow stage;
- report path;
- all count fields listed above;
- recommended next task;
- all negative proof fields.

CLI output should use field names exactly as the summary/metadata fields so ChatGPT review can compare output, CSV, and metadata directly.

## J. Focused Test Plan

Add or update focused tests in:

- `tests/test_local_research_dashboard.py`

Required tests:

1. Research-status includes official-status worklist context when status artifacts exist.
2. Summary CSV includes context fields, latest fields, count fields, and safety fields.
3. Metadata JSON includes the same fields with safe bool/int typing.
4. CLI `research-status` prints official-status fields.
5. `PAPER_WORKFLOW_READY` remains final workflow stage when paper workflow evidence exists.
6. Official-status worklist context stays visible even when paper priority is preserved.
7. All safety / negative proof fields remain false.
8. Forbidden readiness words are absent from positive output.
9. `packet_row_ready_not_pit_approved_count` is displayed as non-approval context.
10. `no_hit_accepted_context_count` is displayed as no-hit context only.

Implementation should reuse existing official-status worklist core/view test helpers where possible, but should not run official evidence closure or create accepted evidence.

## K. CLI Smoke Plan

Later implementation smoke commands should use a temporary output root:

```text
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-official-status-evidence-packet-closure-worklist --root <temp_reports> --output-dir <temp_worklist> --run-id smoke_official_status
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-official-status-evidence-packet-closure-worklist-index --root <temp_worklist> --output-dir <temp_worklist>\index
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-official-status-evidence-packet-closure-worklist-health --root <temp_worklist> --output-dir <temp_worklist>\health
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-official-status-evidence-packet-closure-worklist-status --root <temp_worklist> --output-dir <temp_worklist>\status
.venv\Scripts\python.exe -m quant_replay_system.cli research-status --root <temp_parent_reports> --output-dir <temp_dashboard>
```

Expected smoke outcome:

- all command exit codes are 0 unless an intentionally unsafe fixture is used;
- worklist context is visible in `research-status`;
- row_count is 9;
- stock_row_count is 7;
- etf_row_count is 2;
- blocked_count is 9;
- `official_status_evidence_closed` remains false;
- `pit_evidence_closed` remains false;
- `pit_admissibility_approved` remains false;
- `active_replay_input` remains false;
- `replay_execution_allowed` remains false;
- `buy_review_allowed` remains false;
- `trading_allowed` remains false.

## L. Static Safety Scan Plan

Later implementation should run static scans on changed source/test docs and temp outputs for:

- affirmative unsafe approval flags;
- forbidden readiness words outside negative policy context;
- `docs/project_sources`;
- unresolved placeholder markers;
- protected data paths and generated tracked outputs.

The current planning document may include risky readiness words only in negative policy context.

## M. Open Blockers

No blocking issue was found for a small report-only research-status integration.

The status module currently exposes many required fields, but the later implementation should verify whether `latest_listed_status_missing_count`, `latest_delisted_status_missing_count`, `latest_st_status_missing_count`, `latest_st_not_applicable_policy_missing_count`, `latest_suspension_or_trading_status_missing_count`, and `latest_universe_membership_missing_count` are present in the status summary before wiring dashboard fields. If any are absent, the later task may add those fields to the status view only if the implementation prompt explicitly permits it.

## N. Non-Blocking Notes

- Existing status `NEXT_TASK` still points to CLI in the status module; CLI no-input output may already point to research-status planning. The later implementation should decide whether status view next-action wording needs a narrow update, but only if scoped.
- WARN health is expected because all rows remain blocked or review-required. It should not be treated as unsafe failure.
- The mixed STOCK/ETF profile context is important because seven STOCK rows are under a legacy `etf_core` label.

## O. Candidate Next Routes

| Route | Decision |
| --- | --- |
| A. Historical Replay Official Status Evidence Packet Closure Worklist Research-Status Integration Report-Only v0.1 | Recommended. Existing patterns are compatible with a small safe integration. |
| B. Historical Replay Official Status Evidence Packet Closure Worklist Checkpoint Planning Report-Only v0.1 | Not yet. Checkpoint planning should follow implementation and validation. |
| C. Historical Replay Official Status Evidence Packet Closure Worklist Artifact Views / CLI Hardening Report-Only v0.1 | Not selected. Core/views/CLI exist and are enough for integration planning. |
| D. Pause and review generated official-status worklist artifacts manually before integration | Not selected. No blocking artifact semantic issue was found for context-only integration. |

## P. Selected Next Route

Selected route:

`Historical Replay Official Status Evidence Packet Closure Worklist Research-Status Integration Report-Only v0.1`

## Q. Why Selected Route Is Safe

The selected route is safe because it only exposes already-created report-only status context through `research-status`. It does not generate evidence, close evidence gaps, approve PIT admissibility, run replay, create labels, compute metrics, train models, modify source data, or change trading-related behavior.

The route preserves lower-priority context semantics and keeps all negative proof fields false.

## R. What Must Not Be Bundled

The later implementation must not bundle:

- checkpoint docs;
- README updates;
- Project Source updates;
- `docs/project_sources`;
- evidence packet generation with accepted evidence;
- official evidence closure;
- PIT evidence closure;
- PIT admissibility approval;
- current-candidates execution;
- snapshot build;
- active replay input;
- replay execution;
- replay decision freeze;
- forward label creation;
- metric computation;
- training/model/stock_profile/paper expansion;
- weight, threshold, formula, or model adjustment;
- real buy-review;
- broker API, orders, messages, external API, or LLM calls;
- writes to `data/raw`, `data/processed`, or `data/cache`.

## S. ChatGPT/Codex Mode Recommendation

Codex high is sufficient for the next implementation task if the prompt stays within the existing status-view and dashboard patterns.

Use Pro or Pro Extended before implementation only if the next task tries to change official evidence semantics, source reliability scoring, reviewer no-hit acceptance meaning, PIT admissibility, replay readiness, paper authority, buy-review, or trading boundaries.

## T. Commit/Tag/Source Recommendation

This planning document can be reviewed for a normal manual commit if accepted.

Do not tag a checkpoint for this planning document alone. Do not update ChatGPT Project Source for this planning document alone. Do not create `docs/project_sources`.

Checkpoint planning and Source update should wait until a later research-status integration is implemented, validated, and accepted.

## U. Recommended Next Task

`Historical Replay Official Status Evidence Packet Closure Worklist Research-Status Integration Report-Only v0.1`
