# Release Checkpoint v1.86.0

v1.86.0 documents the Historical Replay Official Source Hierarchy and Evidence Collection Worklist report-only chain for the selected historical replay audit sample `2024-04-02 / etf_core`.

This checkpoint documentation is report-only. It does not create a tag, does not update Project Source, does not create Source update notes, and does not approve official evidence collection, official evidence closure, PIT evidence closure, PIT admissibility, replay, labels, metrics, training, models, stock_profile expansion, paper expansion, buy-review, broker integration, order placement, message delivery, external API or LLM calls, protected data writes, or trading.

## A. Decision / Status

phase = historical_replay_official_source_hierarchy_and_evidence_collection_worklist_checkpoint_documentation
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_previous_checkpoint = v1.85.0
latest_previous_checkpoint_commit = d83a92e
latest_previous_checkpoint_tag = v1.85.0
latest_repo_commit_at_start = cd0d94b
candidate_checkpoint_version = v1.86.0
checkpoint_documentation_created = yes
checkpoint_docs_approved = no
tag_approved = no
source_update_approved = no
selected_next_route = Historical Replay Official Source Hierarchy and Evidence Collection Worklist Checkpoint Commit Review Report-Only v0.1

Non-approval fields:

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

Required checkpoint facts:

selected_historical_decision_date = 2024-04-02
selected_universe = etf_core
row_count = 9
stock_row_count = 7
etf_row_count = 2
source_class_count = 7
evidence_family_count = 9
evidence_collection_worklist_row_count = 72
no_hit_handoff_row_count = 9
blocked_count = 72
profile_conflict_count = 7
survivorship_warning_count = 9
safety_true_count = 0
report_only = yes
diagnostic_only = yes
local_only = yes
selected_sample_context_only = yes

Final classification:
HISTORICAL_REPLAY_OFFICIAL_SOURCE_HIERARCHY_AND_EVIDENCE_COLLECTION_WORKLIST_CHECKPOINT_DOCUMENTATION_CREATED_REPORT_ONLY

Final verdict:
HISTORICAL_REPLAY_OFFICIAL_SOURCE_HIERARCHY_WORKLIST_CHECKPOINT_DOCUMENTATION_READY_FOR_REVIEW_AND_COMMIT_REPORT_ONLY

## B. Current Accepted State

The previous stable checkpoint is v1.85.0 at commit `d83a92e`, tag `v1.85.0`. The repository head at the start of this documentation task was `cd0d94b`, with `git describe` reporting `v1.85.0-11-gcd0d94b`.

External ChatGPT Project Source is current to v1.85.0. This checkpoint documentation does not change Project Source and does not create `docs/project_sources`.

## C. Completed Chain Summary

The v1.86.0 candidate chain includes:

- Official source hierarchy planning for `2024-04-02 / etf_core`.
- Official source hierarchy and evidence collection worklist design for the selected sample.
- Report-only worklist core module: `historical_replay_official_source_hierarchy_and_evidence_collection_worklist`.
- Artifact view modules: `historical_replay_official_source_hierarchy_and_evidence_collection_worklist_index`, `historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health`, and `historical_replay_official_source_hierarchy_and_evidence_collection_worklist_status`.
- CLI commands: `historical-replay-official-source-hierarchy-and-evidence-collection-worklist`, `historical-replay-official-source-hierarchy-and-evidence-collection-worklist-index`, `historical-replay-official-source-hierarchy-and-evidence-collection-worklist-health`, and `historical-replay-official-source-hierarchy-and-evidence-collection-worklist-status`.
- Research-status planning and integration for lower-priority worklist context.
- Checkpoint planning documentation.
- This release checkpoint documentation.

Relevant commits before this checkpoint documentation:

- `ed938ee docs: plan official source hierarchy for replay sample`
- `304a504 docs: design official source hierarchy worklist for replay sample`
- `8ca1071 Add official source hierarchy worklist core`
- `78f3ac9 Add official source hierarchy worklist artifact views`
- `9a10a95 Add official source hierarchy worklist CLI`
- `a207261 docs: plan official source hierarchy worklist research-status integration`
- `533b1fa Integrate official source hierarchy worklist into research status`
- `cd0d94b Add official source hierarchy worklist checkpoint planning`

## D. Selected Sample And Count Contract

Selected sample:

```text
historical_decision_date = 2024-04-02
universe = etf_core
```

Default count contract:

| Field | Value |
|---|---:|
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

The selected sample remains context only. The 72 blocked rows are expected because the worklist identifies evidence that still requires manual collection or review. A blocked row is not approval to proceed.

## E. Files And Modules In Scope

Documentation and planning:

- `docs/historical_replay_official_source_hierarchy_and_evidence_collection_planning_2024_04_02_etf_core_v0_1.md`
- `docs/historical_replay_official_source_hierarchy_and_evidence_collection_worklist_design_2024_04_02_etf_core_v0_1.md`
- `docs/historical_replay_official_source_hierarchy_and_evidence_collection_worklist_research_status_integration_planning_v0_1.md`
- `docs/historical_replay_official_source_hierarchy_and_evidence_collection_worklist_checkpoint_planning_v0_1.md`
- `docs/release_checkpoint_v1.86.0.md`

Runtime modules and tests inspected or validated:

- `src/quant_replay_system/historical_replay_official_source_hierarchy_and_evidence_collection_worklist.py`
- `src/quant_replay_system/historical_replay_official_source_hierarchy_and_evidence_collection_worklist_index.py`
- `src/quant_replay_system/historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health.py`
- `src/quant_replay_system/historical_replay_official_source_hierarchy_and_evidence_collection_worklist_status.py`
- `src/quant_replay_system/cli.py`
- `src/quant_replay_system/local_research_dashboard.py`
- `tests/test_historical_replay_official_source_hierarchy_and_evidence_collection_worklist.py`
- `tests/test_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_views.py`
- `tests/test_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_cli.py`
- `tests/test_local_research_dashboard.py`

No runtime, source, test, README, Project Source, data, or generated-output file is modified by this checkpoint documentation task.

## F. Validation Results

Preflight:

- `git status --short --branch`: `## main...origin/main`
- `git describe --tags --always`: `v1.85.0-11-gcd0d94b`
- `git tag --points-at d83a92e`: `v1.85.0`

Focused worklist tests:

```text
46 passed in 8.81s
```

Dashboard and research-status focused tests:

```text
374 passed in 252.07s (0:04:12)
```

Combined focused suite:

```text
420 passed in 249.20s (0:04:09)
```

## G. CLI Smoke Result

CLI smoke was run with a temporary output root outside the repository. The final smoke used:

- temp output root under `C:\Users\msjpurf\AppData\Local\Temp`
- worklist root under that temp root's `outputs/reports/manual_diagnostics/historical_replay_official_source_hierarchy_and_evidence_collection_worklist_v0_1`
- `research-status --root` pointed at the temp root's `outputs/reports`

Command exit results:

- core command: exit 0
- index command: exit 0
- health command: exit 0
- status command: exit 0
- research-status command: exit 0

The smoke confirmed:

- worklist_run_id: `checkpoint_smoke_rs_reportsroot`
- row_count: 9
- stock_row_count: 7
- etf_row_count: 2
- source_class_count: 7
- evidence_family_count: 9
- evidence_collection_worklist_row_count: 72
- no_hit_handoff_row_count: 9
- blocked_count: 72
- profile_conflict_count: 7
- survivorship_warning_count: 9
- safety_true_count: 0
- buy_review_allowed: false
- trading_allowed: false
- no repository worklist output root was written

The worklist health command returned `OFFICIAL_SOURCE_HIERARCHY_WORKLIST_HEALTH_WARN_REVIEW_REQUIRED`, with one expected warning and no errors. This is acceptable because the report-only worklist intentionally contains blocked evidence collection rows.

Standalone core/status CLI output still reports the earlier research-status planning next task, while the aggregated research-status output reports:

```text
Historical Replay Official Source Hierarchy and Evidence Collection Worklist Checkpoint Planning Report-Only v0.1
```

This is a non-blocking wording note for checkpoint documentation because the focused tests currently codify the standalone core/status wording, and research-status exposes the checkpoint planning route.

## H. Research-Status Integration Result

The focused dashboard tests confirmed the source hierarchy worklist context is visible when artifacts exist. The temp-root CLI smoke confirmed research-status can see the context when `--root` points at the reports root that contains the manual diagnostics tree.

Research-status exposed:

- context_visible: true
- latest run id
- selected historical decision date and universe
- status, health status, workflow stage, report path
- row, stock, ETF, source class, evidence family, worklist row, no-hit handoff, blocked, profile-conflict, survivorship-warning, and safety-true counts
- safety fields remaining false
- recommended next task pointing to checkpoint planning

The temp-root research-status stage was `DATA_PREPARATION_READY` because the temporary root contained only this isolated worklist context. The full local dashboard focused test preserves PAPER_WORKFLOW_READY when the broader repository context is present.

## I. Workflow Priority And PAPER_WORKFLOW_READY Preservation

The worklist context is lower-priority research context. It must not override paper workflow priority. The focused local research dashboard suite confirmed PAPER_WORKFLOW_READY preservation in the integrated repository test context.

## J. Safety And Non-Approval Boundary

This checkpoint remains report-only, diagnostic-only, and local-only. It does not:

- approve an official source hierarchy;
- collect official evidence;
- close official status evidence;
- close PIT evidence;
- approve PIT admissibility;
- create active replay input;
- run replay execution;
- freeze replay decisions;
- create forward labels;
- create training datasets;
- compute metrics;
- train models;
- adjust formulas, weights, thresholds, or model parameters;
- create stock_profile validation;
- expand paper authority;
- create real buy-review eligibility;
- keep `buy_review_allowed` false;
- authorize trading;
- call brokers, place orders, send messages, or call external API or LLM systems;
- run current-candidates;
- build snapshots;
- mutate `signal_semantics`;
- write `data/raw`, `data/processed`, or `data/cache`.

No trading is authorized.

## K. Static Safety Scan Result

Static safety scans were run after this checkpoint document was created.

The unsafe-flag and placeholder scan found no affirmative unsafe approvals. It matched only existing negative assertions in tests that check unsafe trading and buy-review literals are absent from CLI output.

The broader risky-wording scan found 523 matches. The matches are existing guard lists, negative assertions, status names for older report-only workflows, or explicit non-approval policy context. The new checkpoint document only matched `docs/project_sources` in negative policy context.

No placeholder markers were found.

## L. Protected Tracked And docs/project_sources Scan Result

The protected tracked scan remained limited to:

```text
data/processed/.gitkeep
data/raw/.gitkeep
outputs/reports/.gitkeep
```

The `docs/project_sources` status scan had no output.

## M. Full Non-Slow Decision

Full non-slow was not run in this checkpoint documentation task. Focused worklist tests, focused dashboard tests, combined focused tests, and temp-root CLI smoke are sufficient to create checkpoint documentation for this report-only chain.

Full non-slow should be considered before tag/source update if this candidate checkpoint is promoted to release-like Project Source update work, or if a later review requests broader regression evidence.

## N. Candidate Tag Plan

No tag is created in this task. Tag `v1.86.0` is not approved by this checkpoint documentation task.

If ChatGPT review and manual commit review accept this documentation, tag planning can be handled by a separate explicitly scoped task.

## O. Source Update Timing Plan

No immediate Project Source update is performed or recommended in this task. Project Source update planning should happen only after checkpoint documentation is committed and reviewed.

This task does not create Source update notes and does not create `docs/project_sources`.

## P. Open Blockers

No blocker was found for creating this checkpoint documentation.

Non-blocking wording note: standalone core/status CLI output still references the earlier research-status planning task, while research-status points to checkpoint planning. Because this is already covered by focused tests and does not change safety semantics, it does not block checkpoint documentation. It can be considered during a later hardening pass if desired.

## Q. Non-Blocking Notes

- The worklist health warning is expected because all 72 evidence collection rows remain blocked pending manual collection or review.
- The selected sample includes 7 stock rows and 2 ETF rows under the legacy `etf_core` universe context; stock rows remain profile-conflict review context.
- The checkpoint documentation does not prove official evidence availability, source authority, PIT admissibility, or replay readiness.
- The 8-layer taxonomy remains the primary factor structure; fixed 12 factors are not final.

## R. Recommended Next Routes

Route A: Historical Replay Official Source Hierarchy and Evidence Collection Worklist Checkpoint Commit Review Report-Only v0.1.

Route B: Historical Replay Official Source Hierarchy and Evidence Collection Worklist Source Update Planning Report-Only v0.1.

Route C: Historical Replay Official Source Hierarchy and Evidence Collection Worklist v1.86.0 Tag Planning Report-Only v0.1.

Route D: Run full non-slow before checkpoint commit.

Route E: Integration hardening before checkpoint commit.

## S. Selected Next Route

Selected route: Route A.

Recommended next task:

```text
Historical Replay Official Source Hierarchy and Evidence Collection Worklist Checkpoint Commit Review Report-Only v0.1
```

## T. Why Selected Route Is Safe

Route A is safe because this task created only checkpoint documentation, focused validation passed, temp-root CLI smoke passed, research-status context remained report-only, and all safety boundaries remained false. Commit review is the smallest next step before any manual commit or tag decision.

## U. What Must Not Be Bundled

The next route must not bundle:

- official evidence files;
- official source fetches;
- source artifact bytes;
- raw source content;
- real evidence closure;
- PIT closure or approval;
- replay input creation;
- replay execution;
- labels, metrics, training, model, stock_profile, paper expansion, buy-review, or trading work;
- current-candidates or snapshot outputs;
- Project Source files;
- Source update notes unless separately scoped;
- `data/raw`, `data/processed`, or `data/cache` writes.

## V. ChatGPT/Codex Mode Recommendation

Codex high is sufficient for checkpoint commit review if it stays limited to documentation, validation evidence, and git hygiene.

Use ChatGPT Pro or Pro Extended before any step that introduces official evidence collection, source authority policy, PIT adjudication, replay input readiness, replay execution, labels, metrics, training, model, stock_profile, paper expansion, buy-review, performance validation, broker integration, order placement, message delivery, external API or LLM calls, or trading.

## W. Commit/Tag/Source Recommendation

Recommended commit message if ready:

```text
docs: document official source hierarchy worklist checkpoint v1.86.0
```

Recommended tag decision: no tag in this task. Tag `v1.86.0` is not approved here.

Recommended Source update decision: no immediate Project Source update in this task. Source update should be considered only after checkpoint documentation is committed and reviewed.

## X. Recommended Next Task

Historical Replay Official Source Hierarchy and Evidence Collection Worklist Checkpoint Commit Review Report-Only v0.1
