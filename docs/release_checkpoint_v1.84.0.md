# Release Checkpoint v1.84.0

v1.84.0 documents the Historical Replay PIT Evidence Closure Worklist report-only chain for the selected historical replay audit sample `2024-04-02 / etf_core`.

## Included Work

- Historical replay training mainline re-anchor and selected-sample PIT gap audit context.
- PIT evidence gap closure planning for `2024-04-02 / etf_core`.
- PIT evidence closure worklist design for the selected sample.
- Report-only worklist core module: `historical_replay_pit_evidence_closure_worklist`.
- Artifact view modules: `historical_replay_pit_evidence_closure_worklist_index`, `historical_replay_pit_evidence_closure_worklist_health`, and `historical_replay_pit_evidence_closure_worklist_status`.
- CLI commands: `historical-replay-pit-evidence-closure-worklist`, `historical-replay-pit-evidence-closure-worklist-index`, `historical-replay-pit-evidence-closure-worklist-health`, and `historical-replay-pit-evidence-closure-worklist-status`.
- `research-status` integration exposing the latest worklist context as lower-priority research context while preserving `PAPER_WORKFLOW_READY` priority.
- `docs/historical_replay_pit_evidence_closure_worklist.md` documents command usage, artifact roots, status semantics, report-only boundaries, safety fields, and research-status policy.
- `README.md` and `docs/local_research_dashboard.md` describe the v1.84.0 report-only workflow and dashboard visibility.

## Lineage

- Previous stable checkpoint: `v1.83.0` at commit `46f634b`, tag `v1.83.0`.
- Post-v1.83.0 commits included before this checkpoint documentation:
  - `6347f94 docs: reanchor historical replay training loop`
  - `25dec8f docs: audit historical replay sample selection and PIT gaps`
  - `61e7f00 docs: plan PIT evidence closure for selected replay sample`
  - `c0ca318 docs: design PIT evidence closure worklist for selected replay sample`
  - `87be2f5 Add historical replay PIT evidence closure worklist core`
  - `6848df4 Add historical replay PIT evidence closure worklist artifact views`
  - `472f5d4 Add historical replay PIT evidence closure worklist CLI`
  - `3e0336d docs: plan PIT evidence closure worklist research-status integration`
  - `3e96ab0 Integrate historical replay PIT evidence closure worklist research status`
  - `9a7c0d1 docs: plan PIT evidence closure worklist checkpoint`
- v1.84.0 is intended to be created only after ChatGPT review and manual commit/tag of this checkpoint documentation package.

## Selected Sample

```text
historical_decision_date = 2024-04-02
universe = etf_core
```

The selected sample remains evidence organization context only. It is not replay-ready input.

## Expected Statuses

Core statuses:

- `PIT_EVIDENCE_CLOSURE_WORKLIST_CREATED_REPORT_ONLY`
- `PIT_EVIDENCE_CLOSURE_WORKLIST_WARN_NO_CONTEXT`
- `PIT_EVIDENCE_CLOSURE_WORKLIST_WARN_NEEDS_REVIEW`
- `PIT_EVIDENCE_CLOSURE_WORKLIST_BLOCKED_BY_UNSAFE_OUTPUT_ROOT`
- `PIT_EVIDENCE_CLOSURE_WORKLIST_BLOCKED_BY_UNSAFE_INPUT`
- `PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_FAILED`

Workflow stage:

```text
HISTORICAL_REPLAY_PIT_EVIDENCE_CLOSURE_WORKLIST_CREATED_REPORT_ONLY
```

Health statuses:

- `PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_PASS_REPORT_ONLY`
- `PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_WARN_REVIEW_REQUIRED`
- `PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_FAIL_UNSAFE`

These statuses are report-only worklist context. They are not PIT approval, replay readiness, active input readiness, buy-review readiness, strategy-performance validation, or trading permission.

## Artifact Contract

Default artifact root:

```text
outputs/reports/manual_diagnostics/historical_replay_pit_evidence_closure_worklist_v0_1/
```

Default status root:

```text
outputs/reports/manual_diagnostics/historical_replay_pit_evidence_closure_worklist_v0_1/status/
```

Core files:

- `metadata.json`
- `historical_replay_pit_evidence_closure_worklist.csv`
- `historical_replay_pit_evidence_closure_worklist_report.md`
- `historical_replay_pit_evidence_closure_worklist_summary.csv`
- `blocker_summary.csv`
- `safety_flags.json`

View files are generated under `index/`, `health/`, and `status/`.

## Required Negative Proof Fields

These fields must remain false unless a separately approved future workflow explicitly changes scope:

- `pit_evidence_closed=false`
- `pit_admissibility_approved=false`
- `active_replay_input=false`
- `replay_execution_allowed=false`
- `replay_decision_freeze_allowed=false`
- `forward_labels_created=false`
- `training_dataset_created=false`
- `metric_computation_performed=false`
- `model_training_performed=false`
- `stock_profile_validation_created=false`
- `paper_expansion_allowed=false`
- `buy_review_allowed=false`
- `trading_allowed=false`
- `broker_api_called=false`
- `order_placed=false`
- `message_sent=false`
- `external_api_called=false`
- `llm_api_called=false`
- `current_candidates_executed=false`
- `snapshot_built=false`
- `signal_semantics_mutated=false`
- `data_raw_written=false`
- `data_processed_written=false`
- `data_cache_written=false`
- `source_hash_validated=false`

The required positive flags are `report_only=true`, `diagnostic_only=true`, `local_only=true`, and `selected_sample_context_only=true`.

## Research-Status Boundary

`research-status` exposes Historical Replay PIT Evidence Closure Worklist context only. It may expose latest run id, selected date, universe, status, health status, workflow stage, report path, row counts, blocker counts, no-hit counts, profile-conflict counts, survivorship-warning counts, closure-ready-not-PIT-approved counts, safety fields, and recommended next task.

The worklist context is lower-priority research context. It must not override `PAPER_WORKFLOW_READY` when later paper workflow evidence exists.

Research-status must not expose or imply PIT evidence closure, PIT admissibility, active replay input, replay execution, decision freeze, forward-label creation, metric computation, model training, stock_profile validation, paper expansion, real buy-review, broker integration, order placement, message delivery, external API or LLM calls, protected data writes, or trading readiness.

## Safety Boundary

This checkpoint is report-only, diagnostic-only, and local-only. It does not:

- close PIT evidence;
- approve PIT admissibility;
- create active replay input;
- run replay execution;
- create replay evidence bundles, replay decisions, or replay decision freezes;
- create forward labels or future-label joins;
- create training/evaluation datasets;
- compute metrics;
- train models or adjust weights, formulas, thresholds, or model parameters;
- create active weights or active thresholds;
- validate stock_profile;
- expand paper workflow authority;
- create real buy-review eligibility;
- set `buy_review_allowed=true`;
- authorize trading;
- call brokers, place orders, or send messages;
- call external APIs or LLM APIs;
- run current-candidates;
- build snapshots;
- mutate `signal_semantics`;
- write `data/raw`, `data/processed`, or `data/cache`.

No trading is authorized.

## Interpretation Boundaries

- A worklist row is not PIT approval.
- `closure_ready_not_pit_approved` is not PIT admissible.
- Reviewer no-hit acceptance is not source reliability scoring.
- `source_hash_preview` is not source_hash validation.
- `local_file_hash_preview` is not PIT evidence by itself.
- Forward returns remain future information.
- The 8-layer factor taxonomy remains the primary structure; fixed 12 factors are not final.

## Validation

Required validation for this checkpoint:

- `.venv\Scripts\python.exe -m pytest tests/test_historical_replay_pit_evidence_closure_worklist.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_historical_replay_pit_evidence_closure_worklist_views.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_historical_replay_pit_evidence_closure_worklist_cli.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_local_research_dashboard.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_historical_replay_pit_evidence_closure_worklist.py tests/test_historical_replay_pit_evidence_closure_worklist_views.py tests/test_historical_replay_pit_evidence_closure_worklist_cli.py tests/test_local_research_dashboard.py -q`
- `.venv\Scripts\python.exe -m pytest -m "not slow" -q`

Observed validation evidence for this documentation package:

- Focused core suite: 26 passed.
- Focused views suite: 28 passed.
- Focused CLI suite: 9 passed.
- Focused local dashboard suite: 366 passed.
- Combined focused suite: 429 passed.
- Full non-slow suite: 6099 passed, 109 deselected, 5 warnings.
- CLI smoke from a temporary output root: core/index/health/status/research-status commands exited 0. The smoke confirmed worklist context visibility in research-status, latest run id `smoke_worklist`, status `PIT_EVIDENCE_CLOSURE_WORKLIST_WARN_NO_CONTEXT`, health `PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_WARN_REVIEW_REQUIRED`, workflow stage `HISTORICAL_REPLAY_PIT_EVIDENCE_CLOSURE_WORKLIST_CREATED_REPORT_ONLY`, `pit_evidence_closed=false`, `pit_admissibility_approved=false`, `active_replay_input=false`, `replay_execution_allowed=false`, `buy_review_allowed=false`, and `trading_allowed=false`.
- Static safety scan on the temporary outputs and changed docs found risky readiness words only in negative/non-approval policy context and found no affirmative unsafe true flags.
- Protected tracked scan: `data/processed/.gitkeep`, `data/raw/.gitkeep`, and `outputs/reports/.gitkeep` only.
- `docs/project_sources` scan: no output.
- `git diff --check`: no whitespace errors.

## Known Limitations

- The worklist organizes evidence gaps for `2024-04-02 / etf_core`; it does not collect or close evidence.
- No real PIT validator is invoked.
- No replay-ready or active replay input is created.
- Mixed stock/ETF profile context under the legacy `etf_core` label remains manual review context.
- Reviewer no-hit context remains evidence context and is not source reliability scoring.
- Source and local hash previews are not validation.
- The status module's recommended next task remains a live next-action string and should be reviewed after checkpoint acceptance if future wording needs to move to post-checkpoint governance.

## Tag Plan

Create tag `v1.84.0` only after ChatGPT review and manual commit/tag. This task does not run `git add`, `git commit`, `git push`, or `git tag`.

## Source Update Note

After v1.84.0 is committed and tagged, prepare a curated external ChatGPT Project Source update if accepted. Do not create `docs/project_sources`, a Source package, or any Project Source mirror in this checkpoint docs task.

## Recommended Next Task

After checkpoint review and manual commit/tag, the next task should be:

```text
Historical Replay PIT Evidence Closure Worklist Post-v1.84 Governance Audit / Next Decision Planning Report-Only v0.1
```
