# Historical Replay Official Source Hierarchy and Evidence Collection Worklist Checkpoint Planning v0.1

This document is a report-only checkpoint planning note for the completed
Historical Replay Official Source Hierarchy and Evidence Collection Worklist
chain. It plans the smallest safe checkpoint documentation task after the
research-status integration commit. It does not create checkpoint docs, move
tags, update Project Source, approve official evidence collection, approve PIT
admissibility, or authorize any downstream replay, model, buy-review, or trading
workflow.

## A. Decision / Status

phase = historical_replay_official_source_hierarchy_and_evidence_collection_worklist_checkpoint_planning
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_checkpoint = v1.85.0
latest_checkpoint_commit = d83a92e
latest_checkpoint_tag = v1.85.0
latest_repo_commit = 533b1fa
candidate_checkpoint_version = v1.86.0_or_unassigned
checkpoint_planning_created = yes
checkpoint_docs_approved = no
tag_approved = no
source_update_approved = no
selected_next_route = Historical Replay Official Source Hierarchy and Evidence Collection Worklist Checkpoint Documentation Report-Only v0.1

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

Final classification:
HISTORICAL_REPLAY_OFFICIAL_SOURCE_HIERARCHY_AND_EVIDENCE_COLLECTION_WORKLIST_CHECKPOINT_PLANNING_CREATED_REPORT_ONLY

Final verdict:
HISTORICAL_REPLAY_OFFICIAL_SOURCE_HIERARCHY_WORKLIST_CHECKPOINT_PLANNING_READY_FOR_CHECKPOINT_DOCUMENTATION_REPORT_ONLY

## B. Current Accepted State

The current accepted checkpoint remains v1.85.0 at commit d83a92e with tag
v1.85.0. The current repository head is 533b1fa, which integrates the official
source hierarchy worklist into research-status while preserving the final
research-status workflow priority as PAPER_WORKFLOW_READY.

The post-v1.85 worklist chain is still report-only. Its artifacts describe a
manual official-source hierarchy and evidence-collection worklist for a selected
historical replay sample. They do not fetch official records, close official
status evidence, approve PIT admissibility, create replay inputs, execute replay,
create labels, train models, expand stock profiles, approve buy-review, validate
strategy performance, or authorize trading.

## C. Completed Chain Summary

The chain now includes:

- Planning: Historical Replay Official Source Hierarchy and Evidence Collection
  Planning for the 2024-04-02 etf_core replay sample.
- Design: Official Source Hierarchy and Evidence Collection Worklist Design for
  the same selected sample.
- Core: deterministic report-only worklist artifacts under manual diagnostics.
- Artifact views: index, health, and status views for the worklist output.
- CLI: report-only command family for core and views.
- Research-status planning: docs-only integration plan.
- Research-status integration: latest fields surfaced in local research status,
  with PAPER_WORKFLOW_READY preserved as the final workflow stage.

Relevant repository commits:

- ed938ee: planned official source hierarchy for replay sample.
- 304a504: designed official source hierarchy worklist for replay sample.
- 8ca1071: added official source hierarchy worklist core.
- 78f3ac9: added official source hierarchy worklist artifact views.
- 9a10a95: added official source hierarchy worklist CLI.
- a207261: planned official source hierarchy worklist research-status integration.
- 533b1fa: integrated official source hierarchy worklist into research status.

## D. Selected Sample And Count Contract

The selected sample is:

- historical_decision_date: 2024-04-02
- universe: etf_core

The checkpoint documentation should preserve the current count contract:

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

The blocked worklist rows are expected because the worklist is a collection
planning artifact. A blocked row means evidence remains to be manually gathered
or reviewed; it does not mean an operational workflow should proceed.

## E. Checkpoint Candidate Scope

The candidate checkpoint scope is limited to documenting the already completed
report-only worklist chain. A future checkpoint documentation task may create a
release checkpoint document and supporting source update note only if it first
passes the validation ladder in this plan.

The candidate checkpoint must remain:

- report-only;
- manual-diagnostics only;
- no official evidence collection;
- no official source approval;
- no PIT admissibility approval;
- no replay-ready or active input output;
- no labels, training, model, stock profile, paper expansion, buy-review, or
  trading authorization.

The candidate checkpoint version is v1.86.0_or_unassigned. This planning report
does not assign, create, or tag v1.86.0.

## F. Validation Ladder For Checkpoint Documentation

The next checkpoint documentation task should run this focused validation ladder
before creating release checkpoint materials:

1. Focused worklist core tests.
2. Focused worklist view tests.
3. Focused worklist CLI tests.
4. Focused local research dashboard tests that cover the worklist context and
   PAPER_WORKFLOW_READY priority.
5. CLI smoke for core, index, health, status, and research-status commands.
6. Static safety scans for forbidden approval wording.
7. Protected tracked-file scans for generated data and manual diagnostics
   boundaries.
8. Git hygiene checks before any manual commit or tag review.

This planning task intentionally does not run the ladder, because its scope is
docs-only planning and it is not the checkpoint documentation task itself.

## G. Focused Test Plan

The checkpoint documentation task should include focused tests such as:

```cmd
set PYTHONPATH=src
.venv\Scripts\python.exe -m pytest tests/test_historical_replay_official_source_hierarchy_and_evidence_collection_worklist.py -q
.venv\Scripts\python.exe -m pytest tests/test_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_views.py -q
.venv\Scripts\python.exe -m pytest tests/test_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_cli.py -q
.venv\Scripts\python.exe -m pytest tests/test_local_research_dashboard.py -q
```

If these focused tests expose shared dashboard or CLI regressions, the checkpoint
documentation task should stop and fix the blocker in a separate scoped task.

## H. CLI Smoke Plan

The checkpoint documentation task should smoke the report-only commands, using a
temporary output root where possible:

```cmd
set PYTHONPATH=src
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-official-source-hierarchy-and-evidence-collection-worklist
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-official-source-hierarchy-and-evidence-collection-worklist-index
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-official-source-hierarchy-and-evidence-collection-worklist-health
.venv\Scripts\python.exe -m quant_replay_system.cli historical-replay-official-source-hierarchy-and-evidence-collection-worklist-status
.venv\Scripts\python.exe -m quant_replay_system.cli research-status
```

The expected smoke result is report-only context visibility and safety flags
remaining false. Any CLI output that implies official evidence closure, PIT
admissibility approval, replay readiness, buy-review approval, or trading
permission is a blocker.

## I. Static Safety Scan Plan

The checkpoint documentation task should scan all new checkpoint material for
approval wording and stale next-action wording. At minimum, it should check for:

- forbidden approval fields set to yes;
- operational readiness phrases outside negative boundary context;
- stale recommendation text that points backward to research-status planning;
- Project Source file creation language;
- generated-data write claims.

For this planning document, the same scan is expected to show no forbidden
approval fields set to yes and no placeholder markers.

## J. Protected Tracked And docs/project_sources Scan Plan

The checkpoint documentation task should run:

```cmd
git ls-files data/raw data/processed data/cache outputs/reports
git status --short -- docs\project_sources
```

Expected protected tracked entries remain limited to:

- data/processed/.gitkeep
- data/raw/.gitkeep
- outputs/reports/.gitkeep

The `docs/project_sources` path must remain absent or unchanged. A Project
Source package must not be recreated inside the repository.

## K. Workflow Priority And Research-Status Boundary

The research-status integration is contextual and must not override the final
workflow priority. PAPER_WORKFLOW_READY remains the final stage for the local
research dashboard, while the official source hierarchy worklist is a lower
priority context block.

The worklist context may expose run id, selected sample, count contract, report
path, status, health status, workflow stage, and safety false fields. It must
not expose any field that claims official source hierarchy approval, evidence
closure, PIT admissibility approval, replay execution permission, buy-review
eligibility, or trading permission.

## L. Non-Approval Boundary

This chain is a worklist and planning surface only. It does not:

- approve an official source hierarchy;
- collect or close official evidence;
- close PIT evidence;
- approve PIT admissibility;
- create active replay input;
- allow replay execution;
- freeze replay decisions;
- create forward labels;
- create training datasets;
- compute metrics;
- train models;
- adjust weights or thresholds;
- create stock profile validation;
- expand paper workflow approval;
- create real buy-review eligibility;
- allow buy-review;
- allow trading;
- call broker, order, message, external API, or LLM systems;
- run current-candidates;
- build snapshots;
- mutate signal semantics;
- write data/raw, data/processed, or data/cache.

## M. Candidate Checkpoint Version / Tag Plan

The next checkpoint documentation task may propose v1.86.0 only after focused
tests, CLI smoke, static scans, protected tracked scans, docs/project_sources
checks, and git hygiene checks pass. This planning task does not create or move
any tag.

Recommended tag decision for this planning task alone: no tag.

## N. Source Update Timing Plan

No immediate Project Source update is recommended for this planning report. If
checkpoint documentation is later accepted, committed, and tagged, a separate
changed-source update package may be planned under the repository's external
Project Source policy.

This planning task does not create Project Source files and does not recreate
docs/project_sources.

## O. Open Blockers

No blocking issue was identified for proceeding to checkpoint documentation
planning. The next task must still perform the validation ladder before any
checkpoint docs, source notes, manual commit review, or tag review.

## P. Non-Blocking Notes

- The current repository is ahead of v1.85.0 by the completed worklist chain and
  research-status integration.
- The worklist health may warn at the artifact level because all 72 collection
  rows are blocked pending manual evidence work; this is expected and must not
  be interpreted as operational readiness.
- A broad non-slow test run is not required for this docs-only planning task, but
  it can be considered before final checkpoint tagging if shared behavior is
  touched later.

## Q. Candidate Next Routes

Route A: Historical Replay Official Source Hierarchy and Evidence Collection
Worklist Checkpoint Documentation Report-Only v0.1.

Purpose: create checkpoint docs and source note after running the focused
validation ladder.

Route B: Integration Hardening Report-Only v0.1.

Purpose: fix any discovered research-status, CLI, view, or wording issue before
checkpoint docs.

Route C: Manual Artifact Inspection Report-Only v0.1.

Purpose: inspect generated manual-diagnostics artifacts before checkpoint docs
without changing runtime code.

Route D: Pause repo work and prepare external Project Source update plan only
after checkpoint docs.

Purpose: defer source package planning until a checkpoint exists.

Route E: Run broader validation before checkpoint documentation.

Purpose: run a broader suite if focused tests suggest shared regressions.

## R. Selected Next Route

Selected route: Route A.

Recommended next task:
Historical Replay Official Source Hierarchy and Evidence Collection Worklist
Checkpoint Documentation Report-Only v0.1

## S. Why Selected Route Is Safe

Route A is safe because the chain has already reached research-status
integration, the latest status is contextual, the final dashboard priority
remains PAPER_WORKFLOW_READY, and the safety fields remain false. The next
checkpoint documentation task is the smallest coherent step because it can run
focused validation and then document the completed chain without advancing into
real evidence collection or downstream execution.

## T. What Must Not Be Bundled

The next checkpoint documentation task must not bundle:

- real official evidence files;
- real source artifact bytes;
- source content excerpts beyond report-safe summaries;
- live collection scripts;
- runtime source changes unrelated to checkpoint docs;
- tests unrelated to checkpoint validation;
- Project Source package files;
- docs/project_sources files;
- current-candidates outputs;
- snapshot outputs;
- data/raw, data/processed, or data/cache outputs;
- approval claims for replay, labels, training, models, stock profiles,
  buy-review, performance validation, broker, order, message, API, or trading.

## U. ChatGPT/Codex Mode Recommendation

Codex high is sufficient for the next checkpoint documentation task if it stays
within docs-only checkpoint validation and does not introduce new source
authority, PIT adjudication, or real evidence collection semantics.

Use ChatGPT Pro or Pro Extended before implementation if the next step expands
into real official evidence collection, source authority policy, PIT
admissibility adjudication, official status closure, active replay input,
forward labels, model training, stock-profile expansion, paper expansion,
buy-review, performance validation, or trading permission.

## V. Commit/Tag/Source Recommendation

Recommended commit message for this planning report, if accepted for manual
commit review:

```text
docs: plan official source hierarchy worklist checkpoint
```

Recommended tag decision for this planning report alone: no tag.

Recommended Project Source decision for this planning report alone: no immediate
update.

## W. Recommended Next Task

Historical Replay Official Source Hierarchy and Evidence Collection Worklist
Checkpoint Documentation Report-Only v0.1

The next task should run the validation ladder, create only the scoped checkpoint
documentation and source note if validation passes, preserve
PAPER_WORKFLOW_READY priority, keep all non-approval fields false, and avoid any
Project Source package creation until a later explicitly scoped source update
task.
