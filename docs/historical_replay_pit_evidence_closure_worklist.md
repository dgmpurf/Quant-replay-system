# Historical Replay PIT Evidence Closure Worklist

The Historical Replay PIT Evidence Closure Worklist is a report-only, diagnostic-only, local-only selected-sample evidence organization workflow for the historical replay training mainline.

Checkpoint `v1.84.0` covers the selected sample:

```text
historical_decision_date = 2024-04-02
universe = etf_core
```

The worklist organizes missing or context-only evidence for row-level review. It does not close PIT evidence, approve PIT admissibility, create active replay input, run replay, freeze decisions, create forward labels, compute metrics, train models, validate stock_profile, expand paper workflow authority, create buy-review eligibility, or authorize trading.

## Command Family

Core command:

```text
historical-replay-pit-evidence-closure-worklist
```

Artifact views:

```text
historical-replay-pit-evidence-closure-worklist-index
historical-replay-pit-evidence-closure-worklist-health
historical-replay-pit-evidence-closure-worklist-status
```

The core module is:

```text
historical_replay_pit_evidence_closure_worklist
```

The artifact view modules are:

```text
historical_replay_pit_evidence_closure_worklist_index
historical_replay_pit_evidence_closure_worklist_health
historical_replay_pit_evidence_closure_worklist_status
```

## Artifact Roots

Default artifact root:

```text
outputs/reports/manual_diagnostics/historical_replay_pit_evidence_closure_worklist_v0_1/
```

Default status root:

```text
outputs/reports/manual_diagnostics/historical_replay_pit_evidence_closure_worklist_v0_1/status/
```

Core artifact files:

- `metadata.json`
- `historical_replay_pit_evidence_closure_worklist.csv`
- `historical_replay_pit_evidence_closure_worklist_report.md`
- `historical_replay_pit_evidence_closure_worklist_summary.csv`
- `blocker_summary.csv`
- `safety_flags.json`

View files are generated under `index/`, `health/`, and `status/`.

## Status Semantics

Expected core statuses include:

- `PIT_EVIDENCE_CLOSURE_WORKLIST_CREATED_REPORT_ONLY`
- `PIT_EVIDENCE_CLOSURE_WORKLIST_WARN_NO_CONTEXT`
- `PIT_EVIDENCE_CLOSURE_WORKLIST_WARN_NEEDS_REVIEW`
- `PIT_EVIDENCE_CLOSURE_WORKLIST_BLOCKED_BY_UNSAFE_OUTPUT_ROOT`
- `PIT_EVIDENCE_CLOSURE_WORKLIST_BLOCKED_BY_UNSAFE_INPUT`
- `PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_FAILED`

Expected workflow stage:

```text
HISTORICAL_REPLAY_PIT_EVIDENCE_CLOSURE_WORKLIST_CREATED_REPORT_ONLY
```

Expected health view statuses include:

- `PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_PASS_REPORT_ONLY`
- `PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_WARN_REVIEW_REQUIRED`
- `PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_FAIL_UNSAFE`

These statuses are evidence organization context only. WARN or blocked context is local actionable context, not replay package rejection from a real PIT validator.

## Worklist Boundary

A worklist row is not PIT approval.

`closure_ready_not_pit_approved` is not PIT admissible. It means row-level fields appear organized enough for later review context, while PIT approval remains absent.

Reviewer no-hit acceptance is not source reliability scoring. It can document searched-source context and manual review context, but it cannot override source, timing, revision, quality, survivorship, or downstream safety blockers.

`source_hash_preview` is not source_hash validation. It is disclosure-safe identity context only.

`local_file_hash_preview` is not PIT evidence by itself. It is local file identity context and must not substitute for source lineage, revision id, or available-time evidence.

Forward returns remain future information. They must not be joined to decision-time input before a separate decision-freeze and label workflow is approved.

The 8-layer factor taxonomy remains the primary structure. Fixed 12 factors are not final and must not be treated as the complete factor universe.

## Research-Status Integration

`research-status` exposes the latest worklist context when status artifacts exist. It may expose:

- latest run id;
- selected signal date and universe;
- latest status, health status, and workflow stage;
- report path;
- row, blocker, missing-evidence, context-only, manual-review, no-hit, profile-conflict, survivorship, and closure-ready-not-PIT-approved counts;
- recommended next task;
- negative proof and safety fields.

The worklist context is lower-priority research context. It must preserve later `PAPER_WORKFLOW_READY` priority when later paper workflow evidence exists.

## Safety Fields

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

## Safety Boundary

The worklist does not:

- close PIT evidence;
- approve PIT admissibility;
- create active replay input;
- run replay execution;
- create replay evidence bundles, replay decisions, or replay decision freezes;
- create forward labels or future-label joins;
- create training/evaluation datasets;
- compute metrics;
- train models or adjust weights, formulas, thresholds, or model parameters;
- create active weights or thresholds;
- validate stock_profile;
- expand paper workflow authority;
- create real buy-review eligibility;
- authorize trading;
- call brokers, place orders, or send messages;
- call external APIs or LLM APIs;
- run current-candidates;
- build snapshots;
- mutate `signal_semantics`;
- write `data/raw`, `data/processed`, or `data/cache`.

No trading is authorized.

## Known Limitations

- The selected sample remains `2024-04-02 / etf_core` only.
- No selected-sample PIT evidence is closed by this checkpoint.
- No real PIT validator is invoked.
- No active replay input exists because of this worklist.
- Mixed stock/ETF profile context under the legacy `etf_core` label remains manual review context.
- Reviewer no-hit context remains bounded evidence context and is not source reliability scoring.
- Source and local hash previews are disclosure-safe context only.

## Recommended Next Task

After `v1.84.0` checkpoint review and manual commit/tag, the next task should be:

```text
Historical Replay PIT Evidence Closure Worklist Post-v1.84 Governance Audit / Next Decision Planning Report-Only v0.1
```
