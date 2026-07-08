# Historical Replay Official Manual Evidence Collection Template Fixture Full Non-Slow Pre-Tag Validation v0.1

## A. Decision / Status

phase = historical_replay_official_manual_evidence_collection_template_fixture_full_non_slow_pre_tag_validation
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
latest_previous_checkpoint = v1.86.0
latest_previous_checkpoint_commit = 69f98eb
latest_previous_checkpoint_tag = v1.86.0
validation_start_commit = 59f7c4c
candidate_checkpoint_version = v1.87.0
full_non_slow_run = yes
full_non_slow_passed = yes
tag_approved = no
source_update_approved = no
selected_next_route = Historical Replay Official Manual Evidence Collection Template Fixture v1.87.0 Tag and Source Readiness Report-Only v0.1

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

This is a docs-only full non-slow pre-tag validation report for the v1.87.0 candidate checkpoint chain. It does not create a tag, does not update Project Source, does not create Source update notes, and does not approve evidence collection, PIT admissibility, replay input, buy-review, or trading.

## B. Current Git / Tag / Source State

Preflight matched the expected state:

- Branch/status before validation: `main...origin/main`, clean.
- HEAD: `59f7c4c docs: review official manual evidence collection template fixture checkpoint commit`.
- `git describe --tags --always`: `v1.86.0-8-g59f7c4c`.
- `git tag --points-at HEAD`: no output.
- `git tag --points-at 69f98eb`: `v1.86.0`.
- `git tag --points-at d83a92e`: `v1.85.0`.

The latest actual tag remains `v1.86.0` at commit `69f98eb`. External ChatGPT Project Source remains user-reported at `v1.86.0`. Candidate v1.87.0 is not tagged by this report.

## C. Full Non-Slow Validation Result

Command run:

```text
.venv\Scripts\python.exe -m pytest -m "not slow" -q
```

Result:

```text
6233 passed, 109 deselected, 5 warnings in 1496.84s (0:24:56)
```

Warnings observed:

- `tests/test_data_ingestion.py::test_universe_ingestion_fails_with_invalid_non_empty_listed_date`: pandas could not infer format before falling back to `dateutil`.
- `tests/test_factor_dataset.py::test_invalid_non_empty_listed_date_raises_clear_factor_dataset_error`: pandas could not infer format before falling back to `dateutil`.
- `tests/test_forward_return_label.py::test_missing_start_or_end_price_blocks[price_patch0]`: pandas future warning for assigning an empty string into an integer column.
- `tests/test_metric_evaluation.py::test_gate_failures_block[training_evaluation_sample_rows_path-patch5-METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED]`: pandas future warning for assigning an empty string into a float column.
- `tests/test_metric_extension.py::test_metric_extension_health_fails_for_invalid_artifact_boundaries[missing_counts-RESULT_ROW_NUMERATOR_DENOMINATOR_MISSING]`: pandas future warning for assigning an empty string into an integer column.

No test failures occurred. No xdist or parallel pytest mode was used.

## D. Temp-Root CLI Smoke Result

CLI smoke was run with a repository-external temporary output root under the user temp directory. Generated artifacts stayed outside the repository.

Commands and exit results:

- `historical-replay-official-manual-evidence-collection-template-fixture`: exit 0
- `historical-replay-official-manual-evidence-collection-template-fixture-index`: exit 0
- `historical-replay-official-manual-evidence-collection-template-fixture-health`: exit 0
- `historical-replay-official-manual-evidence-collection-template-fixture-status`: exit 0
- `research-status` with temp `--root` and temp `--output-dir`: exit 0

The smoke confirmed:

- run id: `full_non_slow_pre_tag_smoke`
- health: `OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_HEALTH_PASS_REPORT_ONLY`
- research-status context visible: true
- core file count: 9
- all 9 expected fixture artifacts present
- no temp `docs/project_sources`, `data/raw`, `data/processed`, or `data/cache` paths were created

## E. Selected Sample and Count Contract Validation

The temp-root CLI smoke confirmed the selected sample count contract:

| Field | Observed |
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

The selected context remains:

```text
historical_decision_date = 2024-04-02
universe = etf_core
```

The selected sample remains context only. STOCK rows under legacy `etf_core` remain profile-conflict review context. ETF rows still require ETF ST not-applicable policy if stock ST evidence does not apply. Universe membership cannot be inferred from the legacy `etf_core` label alone.

## F. Research-Status Visibility Validation

The temp-root research-status run saw the fixture context:

- `historical_replay_official_manual_evidence_collection_template_fixture_context_visible: True`
- latest run id: `full_non_slow_pre_tag_smoke`
- latest status: `OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_CREATED_REPORT_ONLY`
- latest health status: `OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_HEALTH_PASS_REPORT_ONLY`
- latest workflow stage: `HISTORICAL_REPLAY_OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_CREATED_REPORT_ONLY`
- all count fields matched the checkpoint contract
- official evidence collection, evidence acceptance, evidence closure, PIT approval, buy-review, and trading fields remained false

The isolated temp-root research-status stage was `DATA_PREPARATION_READY` because the temporary root contained only this fixture context. This does not alter full repository workflow priority.

## G. Safety and Non-Approval Boundary Validation

The temp-root safety flags confirmed:

- official_evidence_collection_started = false
- official_evidence_accepted = false
- official_evidence_closed = false
- pit_admissibility_approved = false
- buy_review_allowed = false
- trading_allowed = false
- non-approval true count = 0

This validation did not:

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
- compute metrics outside tests;
- run training or evaluation outside tests;
- train models;
- adjust formulas, weights, thresholds, or model parameters;
- expand stock_profile or paper authority;
- create real buy-review eligibility;
- allow buy-review;
- authorize trading;
- call brokers, place orders, send messages, call external APIs, or call LLM systems;
- run current-candidates;
- build snapshots;
- mutate `signal_semantics`;
- write `data/raw`, `data/processed`, or `data/cache`.

No trading is authorized.

## H. Static Safety Scan Result

Static safety scan was run after this validation report was created across `src`, `tests`, the v1.87.0 checkpoint doc, the checkpoint commit review doc, and this validation report.

Expected interpretation:

- no affirmative unsafe approval fields should be set true;
- risky readiness wording may appear in guard lists, negative assertions, old report-only workflow names, or explicit non-approval policy text;
- `docs/project_sources` may appear only in negative policy context;
- this validation report must not contain unresolved placeholder markers.

Final scan result is recorded in the task response.

## I. Protected Tracked and docs/project_sources Scan Result

Protected tracked scan expected output:

```text
data/processed/.gitkeep
data/raw/.gitkeep
outputs/reports/.gitkeep
```

The `docs/project_sources` status scan is expected to have no output.

Final scan outputs are recorded in the task response.

## J. Failure Triage If Any Failure Occurs

No full non-slow failure occurred. No failure triage route is selected.

The 5 warnings are existing pandas parsing or dtype-assignment warnings observed during passing tests. They do not block this validation report, but they remain useful future cleanup candidates.

## K. Tag and Source Readiness Boundary

This report does not approve or create tag `v1.87.0`.

This report does not approve or create a Project Source update. Tag and Source readiness must remain a separate report-only decision step after this validation report is reviewed and committed.

## L. Candidate Next Routes

| Route | Decision | Reason |
| --- | --- | --- |
| A. Historical Replay Official Manual Evidence Collection Template Fixture v1.87.0 Tag and Source Readiness Report-Only v0.1 | selected | Full non-slow passed, temp-root smoke passed, and the safety boundary remained false. |
| B. Historical Replay Official Manual Evidence Collection Template Fixture Full Non-Slow Failure Triage Report-Only v0.1 | not selected | Full non-slow passed. |
| C. Historical Replay Official Manual Evidence Collection Template Fixture Checkpoint Documentation Hardening Report-Only v0.1 | not selected | No checkpoint documentation blocker was found during this validation. |
| D. Historical Replay Official Manual Evidence Collection Template Fixture Artifact / Next-Task Wording Hardening Report-Only v0.1 | not selected | Live recommended next-task wording remains non-blocking for validation. |
| E. Historical Replay Reviewer No-Hit Acceptance Planning for 2024-04-02 etf_core Report-Only v0.1 | reserved | No-hit policy remains later work and is not the immediate post-validation route. |
| F. Pause repo work and manually collect official source/status evidence outside the repo | not selected | Validation did not indicate repo work should pause. |

## M. Selected Next Route

Selected next route:

`Historical Replay Official Manual Evidence Collection Template Fixture v1.87.0 Tag and Source Readiness Report-Only v0.1`

## N. Why Selected Route Is Safe

The selected route is safe because it remains report-only and decision-oriented. It can review whether v1.87.0 is ready for manual tag/source planning without creating a tag, updating Project Source, collecting evidence, creating replay inputs, or approving buy-review or trading.

## O. What Must Not Be Bundled

The selected route must not bundle:

- official evidence collection;
- source fetching;
- source content reads;
- filled manual evidence templates;
- evidence acceptance;
- evidence closure;
- PIT evidence closure;
- PIT approval;
- replay input;
- replay execution;
- replay decision freeze;
- forward labels;
- metric computation outside tests;
- training or evaluation outside tests;
- model work;
- stock_profile expansion;
- paper expansion;
- real buy-review;
- trading;
- current-candidates;
- snapshots;
- signal semantics mutation;
- broker/API/order/message behavior;
- Project Source package files;
- Source update notes unless explicitly scoped;
- protected data writes.

## P. ChatGPT / Codex Mode Recommendation

Codex high is sufficient for the selected tag/source readiness report if it remains limited to reviewing validation evidence, tag readiness, Source readiness timing, and git hygiene.

Use ChatGPT Pro or Pro Extended before any step that introduces official evidence collection, source authority policy, no-hit sufficiency, ETF not-applicable authority, mixed-universe production policy, source reliability scoring, PIT adjudication, replay input readiness, replay execution, labels, metrics, training, model work, stock_profile, paper expansion, buy-review, performance validation, broker integration, order placement, message delivery, external API or LLM calls, or trading.

## Q. Commit / Tag / Source Recommendation

Recommended commit message if ready:

```text
docs: record official manual evidence collection template fixture full non-slow pre-tag validation
```

Recommended tag decision: no tag for this validation report.

Recommended Source update decision: no Source update for this validation report.

## R. Recommended Next Task

Historical Replay Official Manual Evidence Collection Template Fixture v1.87.0 Tag and Source Readiness Report-Only v0.1

Expected final classification:

`HISTORICAL_REPLAY_OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_FULL_NON_SLOW_PRE_TAG_VALIDATION_CREATED_REPORT_ONLY`

Expected final verdict:

`HISTORICAL_REPLAY_OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_FULL_NON_SLOW_PRE_TAG_VALIDATION_READY_FOR_TAG_SOURCE_READINESS_REPORT_ONLY`
