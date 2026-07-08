# Release Checkpoint v1.87.0

v1.87.0 documents the Historical Replay Official Manual Evidence Collection Template Fixture report-only chain for the selected historical replay audit sample `2024-04-02 / etf_core`.

This checkpoint documentation is report-only. It does not create a tag, does not update Project Source, does not create Source update notes, and does not approve official evidence collection, filled evidence templates, accepted evidence packets, official evidence closure, PIT evidence closure, PIT admissibility, replay input, replay execution, labels, metrics, training, models, stock_profile expansion, paper expansion, buy-review, broker integration, order placement, message delivery, external API or LLM calls, protected data writes, or trading.

## A. Decision / Status

phase = historical_replay_official_manual_evidence_collection_template_fixture_checkpoint_documentation
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_previous_checkpoint = v1.86.0
latest_previous_checkpoint_commit = 69f98eb
latest_previous_checkpoint_tag = v1.86.0
latest_repo_commit_at_start = 6f7ea10
candidate_checkpoint_version = v1.87.0
checkpoint_documentation_created = yes
checkpoint_docs_approved = no
tag_approved = no
source_update_approved = no
selected_next_route = Historical Replay Official Manual Evidence Collection Template Fixture Checkpoint Commit Review Report-Only v0.1

Required checkpoint facts:

selected_historical_decision_date = 2024-04-02
selected_universe = etf_core
row_count = 9
stock_row_count = 7
etf_row_count = 2
evidence_collection_template_row_count = 72
source_lineage_template_row_count = 72
no_hit_template_row_count = 9
survivorship_template_row_count = 9
reviewer_notes_template_row_count = 9
profile_conflict_count = 7
survivorship_warning_count = 9
safety_true_count = 0
report_only = yes
diagnostic_only = yes
local_only = yes
empty_or_synthetic_template_only = yes
filled_evidence_template_created = no
official_evidence_collection_started = no
official_evidence_accepted = no
official_evidence_closed = no
buy_review_allowed = no
trading_allowed = no

Non-approval fields:

official_source_hierarchy_approved = no
official_evidence_collection_started = no
official_evidence_collection_approved = no
official_evidence_accepted = no
official_evidence_closed = no
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

`HISTORICAL_REPLAY_OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_CHECKPOINT_DOCUMENTATION_CREATED_REPORT_ONLY`

Final verdict:

`HISTORICAL_REPLAY_OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_CHECKPOINT_DOCUMENTATION_READY_FOR_REVIEW_AND_COMMIT_REPORT_ONLY`

## B. Current Accepted State

The latest actual checkpoint is v1.86.0 at commit `69f98eb`, tag `v1.86.0`. The repository head at the start of this checkpoint documentation task was `6f7ea10`, with `git describe` reporting `v1.86.0-6-g6f7ea10`.

External ChatGPT Project Source is user-reported current to `v1.86.0`. This checkpoint documentation does not change Project Source and does not create `docs/project_sources`.

The completed template fixture chain follows:

- Template design commit: `edcab22`.
- Template fixture implementation commit: `8418d75`.
- Template generated artifact review commit: `6f7ea10`.

Accepted context:

- historical decision date: `2024-04-02`
- universe: `etf_core`
- selected symbols: `000001`, `000002`, `159915`, `300750`, `510300`, `600000`, `600519`, `601318`, `688981`

## C. Completed Chain Summary

The v1.87.0 candidate chain includes:

- Official manual evidence collection template design for `2024-04-02 / etf_core`.
- Report-only template fixture core module: `historical_replay_official_manual_evidence_collection_template_fixture`.
- Artifact view modules: `historical_replay_official_manual_evidence_collection_template_fixture_index`, `historical_replay_official_manual_evidence_collection_template_fixture_health`, and `historical_replay_official_manual_evidence_collection_template_fixture_status`.
- CLI commands: `historical-replay-official-manual-evidence-collection-template-fixture`, `historical-replay-official-manual-evidence-collection-template-fixture-index`, `historical-replay-official-manual-evidence-collection-template-fixture-health`, and `historical-replay-official-manual-evidence-collection-template-fixture-status`.
- Research-status and local dashboard integration for lower-priority fixture context.
- Generated artifact review documentation.
- This release checkpoint documentation.

Relevant commits before this checkpoint documentation:

- `edcab22 docs: design official manual evidence collection template`
- `8418d75 Add official manual evidence collection template fixture`
- `6f7ea10 docs: review official manual evidence collection template artifacts`

## D. Selected Sample And Count Contract

Selected sample:

```text
historical_decision_date = 2024-04-02
universe = etf_core
```

Default count contract:

| Field | Value |
| --- | ---: |
| row_count | 9 |
| stock_row_count | 7 |
| etf_row_count | 2 |
| evidence_collection_template_row_count | 72 |
| source_lineage_template_row_count | 72 |
| no_hit_template_row_count | 9 |
| survivorship_template_row_count | 9 |
| reviewer_notes_template_row_count | 9 |
| profile_conflict_count | 7 |
| survivorship_warning_count | 9 |
| safety_true_count | 0 |

The selected sample remains context only. STOCK rows under the legacy `etf_core` universe label remain profile-conflict review context. ETF rows require ETF ST not-applicable policy when stock ST evidence does not apply. Universe membership cannot be inferred from the legacy `etf_core` label alone.

## E. Template Fixture Artifact Contract

The fixture creates empty or synthetic report-only templates only. The expected core files are:

- `metadata.json`
- `official_evidence_collection_template.csv`
- `official_source_lineage_template.csv`
- `official_no_hit_query_handoff_template.csv`
- `official_survivorship_rationale_template.csv`
- `official_reviewer_notes_template.csv`
- `official_template_validation_checklist.md`
- `official_manual_evidence_collection_template_report.md`
- `official_manual_evidence_collection_template_safety_flags.json`

The artifact contract preserves:

- exact selected symbols with leading zeros;
- 7 STOCK rows and 2 ETF rows;
- STOCK `st_no_st_status` template rows;
- ETF `etf_st_not_applicable_policy` template rows;
- source lineage placeholders, hash-preview disclosure fields, revision placeholders, available-time placeholders, and limitation placeholders;
- no-hit handoff rows with `not_accepted` defaults;
- survivorship warning rows for all nine selected symbols;
- reviewer notes with `reviewer_private_identity_disclosed=no`;
- all downstream approval and trading safety fields false.

Empty template rows are not filled evidence. A blank template row is not PIT approval. `row_ready_for_manual_fill_not_pit_approved` is not PIT admissible. `no_hit_query_required` is not source reliability scoring. `source_hash_preview` is not source-hash validation. `local_file_hash_preview` is not PIT evidence by itself. Same-day quotation presence is not official status proof by itself.

## F. Files And Modules In Scope

Documentation and planning:

- `docs/historical_replay_official_manual_evidence_collection_template_design_2024_04_02_etf_core_v0_1.md`
- `docs/historical_replay_official_manual_evidence_collection_template_generated_artifact_review_v0_1.md`
- `docs/release_checkpoint_v1.87.0.md`

Runtime modules and tests inspected or validated:

- `src/quant_replay_system/historical_replay_official_manual_evidence_collection_template_fixture.py`
- `src/quant_replay_system/historical_replay_official_manual_evidence_collection_template_fixture_index.py`
- `src/quant_replay_system/historical_replay_official_manual_evidence_collection_template_fixture_health.py`
- `src/quant_replay_system/historical_replay_official_manual_evidence_collection_template_fixture_status.py`
- `src/quant_replay_system/cli.py`
- `src/quant_replay_system/local_research_dashboard.py`
- `tests/test_historical_replay_official_manual_evidence_collection_template_fixture.py`
- `tests/test_historical_replay_official_manual_evidence_collection_template_fixture_views.py`
- `tests/test_historical_replay_official_manual_evidence_collection_template_fixture_cli.py`
- `tests/test_local_research_dashboard.py`

No runtime, source, test, README, Project Source, data, or generated-output file is modified by this checkpoint documentation task.

## G. Validation Results

Preflight:

- `git status --short --branch`: `## main...origin/main`
- HEAD: `6f7ea10 docs: review official manual evidence collection template artifacts`
- `git describe --tags --always`: `v1.86.0-6-g6f7ea10`
- `git tag --points-at HEAD`: no output
- `git tag --points-at 69f98eb`: `v1.86.0`
- `git tag --points-at d83a92e`: `v1.85.0`

Focused template fixture, views, and CLI tests:

```text
24 passed in 8.23s
```

Dashboard and research-status focused tests:

```text
377 passed in 260.57s (0:04:20)
```

Combined focused suite:

```text
447 passed in 262.98s (0:04:22)
```

## H. Temp-Root CLI Smoke Result

CLI smoke was run with a repository-external temporary output root under the user temp directory. Generated artifacts stayed outside the repository.

Commands and exit results:

- core fixture command: exit 0
- index command: exit 0
- health command: exit 0
- status command: exit 0
- research-status command with temp `--root` and temp `--output-dir`: exit 0

The smoke confirmed:

- run id: `checkpoint_smoke`
- core file count: 9
- all 9 expected fixture artifacts present
- row_count: 9
- stock_row_count: 7
- etf_row_count: 2
- evidence_collection_template_row_count: 72
- source_lineage_template_row_count: 72
- no_hit_template_row_count: 9
- survivorship_template_row_count: 9
- reviewer_notes_template_row_count: 9
- profile_conflict_count: 7
- survivorship_warning_count: 9
- safety_true_count: 0
- filled_evidence_template_created: false
- official_evidence_collection_started: false
- official_evidence_accepted: false
- official_evidence_closed: false
- pit_admissibility_approved: false
- buy_review_allowed: false
- trading_allowed: false
- non-approval true count: 0
- no temp `docs/project_sources`, `data/raw`, `data/processed`, or `data/cache` paths were created

The health command returned `OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_HEALTH_PASS_REPORT_ONLY`.

## I. Research-Status Integration Result

The temp-root CLI smoke confirmed research-status can see the fixture context when `--root` points at the reports root containing the temp manual diagnostics tree.

Research-status exposed:

- `historical_replay_official_manual_evidence_collection_template_fixture_context_visible: True`
- latest run id: `checkpoint_smoke`
- latest status: `OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_CREATED_REPORT_ONLY`
- latest health status: `OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_HEALTH_PASS_REPORT_ONLY`
- latest workflow stage: `HISTORICAL_REPLAY_OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_CREATED_REPORT_ONLY`
- all count fields matching the checkpoint contract
- official evidence collection, acceptance, closure, PIT approval, buy-review, and trading fields false
- recommended next task: `Historical Replay Official Manual Evidence Collection Template Generated Artifact Review Report-Only v0.1`

The isolated temp-root research-status stage was `DATA_PREPARATION_READY` because the temporary root contained only this isolated context. This is acceptable for smoke validation and does not change full repository workflow priority.

## J. Workflow Priority And PAPER_WORKFLOW_READY Preservation

The fixture context is lower-priority research context. It must not override paper workflow priority. The focused local research dashboard suite confirmed integrated dashboard behavior and preserved the broader workflow priority in repository-context tests.

The fixture does not emit active replay input readiness, replay execution permission, label creation permission, training permission, stock_profile validation, buy-review permission, or trading permission.

## K. Safety And Non-Approval Boundary

This checkpoint remains report-only, diagnostic-only, local-only, and empty-or-synthetic-template-only. It does not:

- approve an official source hierarchy;
- collect official evidence;
- create filled evidence templates;
- accept official evidence;
- close official evidence;
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
- allow buy-review;
- authorize trading;
- call brokers, place orders, send messages, call external APIs, or call LLM systems;
- run current-candidates;
- build snapshots;
- mutate `signal_semantics`;
- write `data/raw`, `data/processed`, or `data/cache`.

No trading is authorized.

Forward returns remain future information. The 8-layer factor taxonomy remains the primary structure. Fixed 12 factors are not final.

## L. Static Safety Scan Result

Static safety scan was run after this checkpoint document was created across the fixture modules, CLI, dashboard integration, focused tests, dashboard tests, and this checkpoint document.

The scan found no affirmative unsafe approvals, no TODO/TBD/FIXME placeholders, and no unexpected protected-output policy issue. Matches for risky readiness wording are limited to guard lists, negative assertions, status names from older report-only workflows, or explicit non-approval policy context. The `docs/project_sources` literal appears only in negative policy context.

## M. Protected Tracked And docs/project_sources Scan Result

The protected tracked scan remained limited to:

```text
data/processed/.gitkeep
data/raw/.gitkeep
outputs/reports/.gitkeep
```

The `docs/project_sources` status scan had no output.

## N. Full Non-Slow Decision

Full non-slow was not run in this checkpoint documentation task. Focused fixture, views, CLI, dashboard, combined focused validation, and temp-root CLI smoke are sufficient to create checkpoint documentation for this report-only empty/synthetic fixture chain.

Full non-slow should be considered before tag/source update if this candidate checkpoint is promoted to a release-like Project Source update.

## O. Candidate Tag Plan

No tag is created in this task. Tag `v1.87.0` is not approved by this checkpoint documentation task.

If ChatGPT review and manual commit review accept this documentation, tag planning can be handled by a separate explicitly scoped task after broader validation as needed.

## P. Source Update Timing Plan

No immediate Project Source update is performed or recommended in this task. Source update should be considered only after checkpoint documentation is committed, reviewed, full non-slow pre-tag validation passes if requested, and a manual tag is created.

This task does not create Source update notes and does not create `docs/project_sources`.

## Q. Open Blockers

No blocker was found for creating this checkpoint documentation.

## R. Non-Blocking Notes

- The standalone fixture command family still reports `Historical Replay Official Manual Evidence Collection Template Generated Artifact Review Report-Only v0.1` as its recommended next task. This is consistent across core/status/research-status surfaces and does not create a safety issue. A later wording hardening task can be considered after checkpoint documentation if a stricter post-checkpoint next-action is desired.
- The selected sample includes 7 STOCK rows and 2 ETF rows under the legacy `etf_core` universe context; STOCK rows remain profile-conflict review context.
- No-hit handoff rows remain not accepted by default.
- Survivorship warning remains true for all selected symbols.
- This checkpoint does not prove official evidence availability, source authority, PIT admissibility, or replay readiness.

## S. Recommended Next Routes

Route A: Historical Replay Official Manual Evidence Collection Template Fixture Checkpoint Commit Review Report-Only v0.1.

Route B: Historical Replay Official Manual Evidence Collection Template Fixture Full Non-Slow Pre-Tag Validation Report-Only v0.1.

Route C: Historical Replay Official Manual Evidence Collection Template Fixture Artifact / Next-Task Wording Hardening Report-Only v0.1.

Route D: Historical Replay Reviewer No-Hit Acceptance Planning for 2024-04-02 etf_core Report-Only v0.1.

Route E: Historical Replay Mixed STOCK/ETF Universe Profile Policy Planning for legacy etf_core Report-Only v0.1.

Route F: Pause repo work and manually collect official source/status evidence outside the repo.

## T. Selected Next Route

Selected route: Route A.

Recommended next task:

```text
Historical Replay Official Manual Evidence Collection Template Fixture Checkpoint Commit Review Report-Only v0.1
```

## U. Why Selected Route Is Safe

Route A is safe because this task created only checkpoint documentation, focused validation passed, temp-root CLI smoke passed, research-status context remained report-only, all non-approval fields remained false, and no hardening blocker was found.

Checkpoint commit review is the smallest next step before any manual commit or tag decision.

## V. What Must Not Be Bundled

The next route must not bundle:

- official evidence files;
- official source fetches;
- source artifact bytes;
- raw source content;
- filled manual evidence templates;
- accepted evidence packets;
- real evidence closure;
- PIT closure or approval;
- replay input creation;
- replay execution;
- labels, metrics, training, model, stock_profile, paper expansion, buy-review, or trading work;
- current-candidates or snapshot outputs;
- Project Source files;
- Source update notes unless separately scoped;
- `data/raw`, `data/processed`, or `data/cache` writes.

## W. ChatGPT / Codex Mode Recommendation

Codex high is sufficient for checkpoint commit review if it stays limited to documentation, validation evidence, and git hygiene.

Use ChatGPT Pro or Pro Extended before any step that introduces official evidence collection, source authority policy, no-hit sufficiency, ETF not-applicable authority, mixed-universe production policy, source reliability scoring, PIT adjudication, replay input readiness, replay execution, labels, metrics, training, model work, stock_profile, paper expansion, buy-review, performance validation, broker integration, order placement, message delivery, external API or LLM calls, or trading.

## X. Commit / Tag / Source Recommendation

Recommended commit message if ready:

```text
docs: document official manual evidence collection template fixture checkpoint v1.87.0
```

Recommended tag decision: no tag in this task. Tag `v1.87.0` is not approved here.

Recommended Source update decision: no immediate Project Source update in this task. Source update should be considered only after checkpoint documentation is committed, reviewed, full non-slow pre-tag validation passes if requested, and a manual tag is created.

## Y. Recommended Next Task

Historical Replay Official Manual Evidence Collection Template Fixture Checkpoint Commit Review Report-Only v0.1
