# Historical Replay Official Source Hierarchy and Evidence Collection Worklist Research-Status Integration Planning v0.1

phase = historical_replay_official_source_hierarchy_and_evidence_collection_worklist_research_status_integration_planning
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_checkpoint = v1.85.0
latest_checkpoint_commit = d83a92e
latest_checkpoint_tag = v1.85.0
latest_repo_commit = 9a10a95
research_status_integration_approved = no
selected_next_route = Historical Replay Official Source Hierarchy and Evidence Collection Worklist Research-Status Integration Report-Only v0.1

official_source_hierarchy_approved = no
official_evidence_collection_approved = no
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

This docs-only planning report is ready. It defines the smallest safe route for integrating the Historical Replay Official Source Hierarchy and Evidence Collection Worklist into local `research-status`.

This report does not implement research-status integration. It does not run the source hierarchy worklist, index, health, status, research-status, pytest, or any CLI smoke. It does not collect official evidence, close evidence, approve point-in-time admissibility, create active replay input, run replay, freeze decisions, create labels, compute metrics, train models, expand stock profiles, expand paper authority, approve real buy-review, or authorize trading.

Selected next route:

`Historical Replay Official Source Hierarchy and Evidence Collection Worklist Research-Status Integration Report-Only v0.1`

## B. Current Accepted State

The current stable checkpoint is `v1.85.0` at commit `d83a92e`, with tag `v1.85.0`. The repository head for this planning task is `9a10a95`, described as `v1.85.0-8-g9a10a95`.

The source hierarchy worklist chain currently exists through CLI:

- Design: `304a504`
- Core: `8ca1071`
- Artifact views: `78f3ac9`
- CLI: `9a10a95`

Existing command family:

- `historical-replay-official-source-hierarchy-and-evidence-collection-worklist`
- `historical-replay-official-source-hierarchy-and-evidence-collection-worklist-index`
- `historical-replay-official-source-hierarchy-and-evidence-collection-worklist-health`
- `historical-replay-official-source-hierarchy-and-evidence-collection-worklist-status`

Selected sample:

| Field | Value |
| --- | --- |
| historical_decision_date | `2024-04-02` |
| universe | `etf_core` |
| row_count | 9 |
| stock_row_count | 7 |
| etf_row_count | 2 |
| source_class_count | 7 |
| evidence_family_count | 9 |
| evidence_collection_worklist_row_count | 72 |
| no_hit_handoff_row_count | 9 |
| blocked_count | 72 |
| profile_conflict_count | 7 |
| survivorship_warning_count | 9 |
| safety_true_count | 0 |

External ChatGPT Project Source is updated to `v1.85.0`; this task does not create or update Project Source files.

## C. Existing Research-Status Pattern Summary

The adjacent Historical Replay Official Status Evidence Packet Closure Worklist already provides the most relevant pattern in `src/quant_replay_system/local_research_dashboard.py`.

Observed integration shape:

1. Dashboard imports the workflow status view runner.
2. Dashboard scans the status artifact root and calls the status runner against existing local status artifacts.
3. A component record is created with workflow area, component, status, stage, latest artifact id, report path, metadata path, warning count, error count, next action, and semicolon-delimited notes.
4. Notes carry context fields, count fields, safety fields, and compact semantics.
5. Summary helpers parse notes back into top-level `research-status` fields.
6. Result kwargs convert latest fields to strings, count fields to integers, and safety fields to booleans.
7. Metadata export and CLI print paths expose the same fields.
8. Workflow priority remains lower than paper workflow, preserving `PAPER_WORKFLOW_READY` when paper evidence exists.

The source hierarchy worklist should follow this same pattern rather than introducing a new dashboard architecture.

## D. Source Hierarchy Worklist Status Artifact Discovery Plan

Future implementation should discover latest source hierarchy worklist status artifacts under:

```text
outputs/reports/manual_diagnostics/historical_replay_official_source_hierarchy_and_evidence_collection_worklist_v0_1/status/
```

The dashboard should use the existing status runner:

```text
run_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_status
```

The status runner already composes index and health context from existing local artifacts. Research-status integration should not run the core worklist and should not create new source hierarchy worklist rows. It should only summarize status artifacts already present under the expected report-only root.

If the root is missing or the status result has no latest status, the dashboard should return no component record and leave the context-visible flag false or empty. Missing source hierarchy worklist context must not be treated as a failure for the global research dashboard.

## E. Proposed Fields

Recommended context field:

- `historical_replay_official_source_hierarchy_and_evidence_collection_worklist_context_visible`

Recommended latest identity/status/path fields:

- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_run_id`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_historical_decision_date`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_universe_name`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_status`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health_status`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_workflow_stage`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_report_path`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_recommended_next_task`

Recommended count fields:

- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_row_count`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_stock_row_count`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_etf_row_count`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_source_class_count`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_evidence_family_count`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_evidence_collection_worklist_row_count`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_no_hit_handoff_row_count`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_blocked_count`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_profile_conflict_count`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_survivorship_warning_count`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_safety_true_count`

Recommended note semantics:

```text
historical_replay_official_source_hierarchy_and_evidence_collection_worklist_semantics=report_only_context_no_official_source_hierarchy_approval_no_evidence_collection_no_pit_approval_replay_labels_training_buy_review_or_trading
```

## F. Proposed Safety / Negative Proof Fields

Expose these as booleans and require false values for safe context:

- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_official_source_hierarchy_approved`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_official_evidence_collection_approved`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_official_status_evidence_closed`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_pit_evidence_closed`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_pit_admissibility_approved`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_active_replay_input`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_replay_execution_allowed`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_replay_decision_freeze_allowed`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_forward_labels_created`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_training_dataset_created`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_metric_computation_performed`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_model_training_performed`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_stock_profile_validation_created`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_paper_expansion_allowed`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_buy_review_allowed`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_trading_allowed`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_broker_api_called`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_order_placed`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_message_sent`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_external_api_called`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_llm_api_called`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_current_candidates_executed`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_snapshot_built`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_signal_semantics_mutated`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_data_raw_written`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_data_processed_written`
- `latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_data_cache_written`

These fields are visibility and negative-proof fields only. They do not approve future state transitions.

## G. Workflow Priority Rule

Official source hierarchy worklist context is lower-priority research context only. It should be visible in metadata and CLI output, but it must not become the final top-level workflow stage when later higher-priority workflow evidence exists.

Required priority behavior:

- Preserve `PAPER_WORKFLOW_READY` when paper workflow evidence exists.
- Do not override future valid active replay, replay execution, decision freeze, label, metric, model, stock_profile, paper, buy-review, or trading statuses.
- Do not mark missing source hierarchy worklist context as dashboard failure.
- Do not convert warning or blocker counts into workflow readiness.

Suggested component stage is the latest source hierarchy worklist workflow stage only inside the component record and latest field, not necessarily as final dashboard workflow stage.

## H. Forbidden Meanings and Wording

Research-status must not expose these as positive readiness meanings:

- `PIT_ADMISSIBLE`
- `PIT_APPROVED`
- `READY_FOR_REPLAY`
- `ACTIVE_REPLAY_INPUT_READY`
- `BUY_REVIEW_READY`
- `TRADING_READY`
- `APPROVED_FOR_PAPER`
- `PERFORMANCE_VALIDATED`

These phrases may appear only as forbidden wording or non-approval guard text.

Additional forbidden interpretations:

- `row_ready_for_manual_collection_not_pit_approved` must not mean PIT approval.
- `no_hit_query_required` must not mean source reliability scoring.
- `official_source_hierarchy_approved=false` and `official_evidence_collection_approved=false` must not be overrideable by no-hit context.
- Same-day quotation presence must not prove listed status, not-delisted status, no-ST status, not-suspended status, or universe membership.
- `source_hash_preview` must not mean source hash validation.
- `local_file_hash_preview` must not mean PIT evidence by itself.

## I. Research-Status CLI Display Plan

The future `research-status` CLI should print a compact block of source hierarchy context fields after the integration is implemented.

Minimum visible lines:

```text
historical_replay_official_source_hierarchy_and_evidence_collection_worklist_context_visible: True
latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_run_id: <run_id>
latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_status: <status>
latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health_status: <health_status>
latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_workflow_stage: <workflow_stage>
latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_report_path: <report_path>
latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_row_count: 9
latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_evidence_collection_worklist_row_count: 72
latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_safety_true_count: 0
latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_buy_review_allowed: False
latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_trading_allowed: False
latest_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_recommended_next_task: Historical Replay Official Source Hierarchy and Evidence Collection Worklist Checkpoint Planning Report-Only v0.1
```

The CLI display should avoid printing source content, raw evidence, full hashes, private paths, source bytes, official website contents, reviewer private notes, or any fetched-source payload.

## J. Focused Test Plan

Future implementation should update or add focused tests in:

- `tests/test_local_research_dashboard.py`

Required test cases:

1. No source hierarchy worklist status artifacts exist: context-visible field is false or empty, no final workflow regression.
2. Source hierarchy worklist status artifacts exist: latest run id, decision date, universe, status, health, workflow stage, report path, and recommended next task are exported.
3. Count fields parse as integers and match expected values: 9, 7, 2, 7, 9, 72, 9, 72, 7, 9, 0.
4. Safety fields parse as booleans and remain false.
5. Final workflow stage preserves `PAPER_WORKFLOW_READY` when paper workflow evidence exists.
6. Research-status CLI output includes the source hierarchy worklist latest fields.
7. Research-status metadata includes the same fields as the CLI.
8. No forbidden readiness wording appears as a positive final stage or positive readiness field.
9. Existing official-status worklist fields remain unchanged.

Suggested combined focused suite for implementation:

```text
set PYTHONPATH=src
.venv\Scripts\python.exe -m pytest tests/test_local_research_dashboard.py tests/test_historical_replay_official_source_hierarchy_and_evidence_collection_worklist.py tests/test_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_views.py tests/test_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_cli.py -q
```

## K. CLI Smoke Plan

For the future implementation task only, run CLI smoke from a temporary output root:

```text
set PYTHONPATH=src
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-official-source-hierarchy-and-evidence-collection-worklist --root <temp_repo_context> --output-dir <temp_worklist_root> --run-id smoke_official_source_hierarchy
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-official-source-hierarchy-and-evidence-collection-worklist-index --root <temp_worklist_root> --output-dir <temp_worklist_root>\index
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-official-source-hierarchy-and-evidence-collection-worklist-health --root <temp_worklist_root> --output-dir <temp_worklist_root>\health
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-official-source-hierarchy-and-evidence-collection-worklist-status --root <temp_worklist_root> --output-dir <temp_worklist_root>\status
.venv\Scripts\python.exe -m quant_replay_system.cli research-status --root <temp_dashboard_root> --output-dir <temp_dashboard_output>
```

Expected smoke behavior:

- All commands exit safely.
- Source hierarchy worklist health remains report-only warning context unless all blockers are cleared by a separately approved workflow.
- Research-status exposes latest source hierarchy context as lower-priority context.
- `buy_review_allowed` remains false.
- `trading_allowed` remains false.
- No protected data directories are written.

## L. Static Safety Scan Plan

Future implementation should scan changed source and tests for unsafe approvals:

```text
rg -n "official_source_hierarchy_approved.*true|official_evidence_collection_approved.*true|official_status_evidence_closed.*true|pit_evidence_closed.*true|pit_admissibility_approved.*true|active_replay_input.*true|replay_execution_allowed.*true|replay_decision_freeze_allowed.*true|forward_labels_created.*true|metric_computation_performed.*true|model_training_performed.*true|stock_profile_validation_created.*true|buy_review_allowed.*true|trading_allowed.*true|broker_api_called.*true|order_placed.*true|message_sent.*true|data_raw_written.*true|data_processed_written.*true|data_cache_written.*true|PIT_ADMISSIBLE|PIT_APPROVED|READY_FOR_REPLAY|ACTIVE_REPLAY_INPUT_READY|BUY_REVIEW_READY|TRADING_READY|APPROVED_FOR_PAPER|PERFORMANCE_VALIDATED" src\quant_replay_system\local_research_dashboard.py src\quant_replay_system\cli.py tests\test_local_research_dashboard.py
```

Expected result:

- No affirmative unsafe true flags.
- Risky readiness wording appears only in negative assertions, forbidden wording lists, or non-approval policy text.

Protected tracked scan:

```text
git ls-files data/raw data/processed data/cache outputs/reports
```

Expected tracked files only:

- `data/processed/.gitkeep`
- `data/raw/.gitkeep`
- `outputs/reports/.gitkeep`

## M. Open Blockers

No blocking issue was found for a small report-only research-status integration.

The only implementation caution is that the status module's current `NEXT_TASK` still points to CLI phase in artifact status semantics, while the CLI layer points to research-status planning. The research-status implementation may either surface the status result's current next task or define a dashboard-level next task pointing to checkpoint planning after integration. This should be explicit in the implementation task.

## N. Non-Blocking Notes

- The field prefix is long but consistent with adjacent official-status naming.
- The count set is larger than the prior official-status packet worklist because it includes source-class and evidence-family counts.
- `safety_true_count` should be exposed to make false safety fields easier to audit.
- The integration should keep source hierarchy and official-status packet fields separate; do not merge the two worklist contexts.

## O. Candidate Next Routes

| Route | Decision | Reason |
| --- | --- | --- |
| A. Historical Replay Official Source Hierarchy and Evidence Collection Worklist Research-Status Integration Report-Only v0.1 | selected | Existing dashboard patterns are compatible with a small safe integration. |
| B. Historical Replay Official Source Hierarchy and Evidence Collection Worklist Checkpoint Planning Report-Only v0.1 | not selected | Checkpoint planning should come after research-status integration exists and is validated. |
| C. Historical Replay Official Source Hierarchy and Evidence Collection Worklist Artifact/CLI Hardening Report-Only v0.1 | not selected | No current blocker was found in artifact/view/CLI shape for integration planning. |
| D. Pause and manually inspect generated source hierarchy worklist artifacts before integration | not selected | Existing core/views/CLI focused tests and prior artifact design are enough for planning a report-only context integration. |

## P. Selected Next Route

Selected route:

`Historical Replay Official Source Hierarchy and Evidence Collection Worklist Research-Status Integration Report-Only v0.1`

This route should implement only dashboard/research-status visibility, focused tests, and CLI display updates. It should not modify worklist core semantics.

## Q. Why Selected Route Is Safe

The route is safe because it only exposes existing report-only status artifacts as lower-priority context. It does not collect official evidence, approve source hierarchy, approve evidence collection, close PIT evidence, create replay input, execute replay, create labels, compute metrics, train models, validate stock_profile, expand paper workflow authority, allow buy-review, or authorize trading.

The adjacent official-status worklist already proves the pattern: status artifacts can be visible in research-status without overriding `PAPER_WORKFLOW_READY` or implying readiness.

## R. What Must Not Be Bundled

Do not bundle any of the following into the implementation task:

- checkpoint docs;
- SOURCE_UPDATE_NOTES;
- Project Source package or `docs/project_sources`;
- core worklist redesign;
- artifact view redesign;
- CLI command redesign;
- official evidence collection;
- official evidence closure;
- PIT evidence closure;
- PIT admissibility approval;
- replay input creation;
- replay execution;
- replay decision freeze;
- forward label creation;
- metric computation;
- model training;
- stock_profile validation;
- paper workflow expansion;
- real buy-review;
- broker, order, message, external API, or LLM calls;
- current-candidates execution;
- snapshot build;
- signal semantics mutation;
- `data/raw`, `data/processed`, or `data/cache` writes.

## S. ChatGPT/Codex Mode Recommendation

Use Codex high for the implementation because the integration follows an established local pattern and does not introduce new source semantics.

Use ChatGPT Pro or Pro Extended before implementation only if the scope changes to evidence collection, source authority adjudication, PIT admissibility, real source-fetching, no-hit acceptance policy, or downstream replay readiness.

## T. Commit/Tag/Source Recommendation

No commit or tag is recommended by this planning task itself.

Recommended later sequence:

1. Implement report-only research-status integration.
2. Run focused dashboard/worklist tests and temporary-root CLI smoke.
3. Send for ChatGPT review.
4. Commit only after review.
5. Prepare checkpoint planning only after integration is committed or otherwise accepted.
6. Do not update Project Source until a later accepted checkpoint or explicit source-update task.

## U. Recommended Next Task

`Historical Replay Official Source Hierarchy and Evidence Collection Worklist Research-Status Integration Report-Only v0.1`

This next task should modify only the minimum local research dashboard and focused tests required to expose source hierarchy worklist context safely.
