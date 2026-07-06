# Historical Replay Official Status Evidence Packet Closure Worklist

The Historical Replay Official Status Evidence Packet Closure Worklist is a report-only, diagnostic-only, local-only scaffold for the selected historical replay audit sample `2024-04-02 / etf_core`.

It organizes official-status evidence gaps for manual review. It does not fetch official evidence, close evidence, approve PIT admissibility, create active replay input, run replay, freeze replay decisions, create forward labels, compute metrics, train models, validate stock profiles, expand paper authority, create real buy-review eligibility, or authorize trading.

## Scope

```text
historical_decision_date = 2024-04-02
universe = etf_core
```

The default scaffold contains exactly:

| Field | Value |
|---|---:|
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

All rows remain blocked or review-needed by default.

## Modules

Core module:

```text
historical_replay_official_status_evidence_packet_closure_worklist
```

Artifact view modules:

```text
historical_replay_official_status_evidence_packet_closure_worklist_index
historical_replay_official_status_evidence_packet_closure_worklist_health
historical_replay_official_status_evidence_packet_closure_worklist_status
```

## CLI Commands

```text
historical-replay-official-status-evidence-packet-closure-worklist
historical-replay-official-status-evidence-packet-closure-worklist-index
historical-replay-official-status-evidence-packet-closure-worklist-health
historical-replay-official-status-evidence-packet-closure-worklist-status
```

The CLI family creates or summarizes local report-only artifacts. It does not call brokers, place orders, send messages, call external APIs, call LLM APIs, run current-candidates, build snapshots, mutate signal semantics, or write `data/raw`, `data/processed`, or `data/cache`.

## Artifact Roots

Default artifact root:

```text
outputs/reports/manual_diagnostics/historical_replay_official_status_evidence_packet_closure_worklist_v0_1/
```

Default status root:

```text
outputs/reports/manual_diagnostics/historical_replay_official_status_evidence_packet_closure_worklist_v0_1/status/
```

Core files:

- `metadata.json`
- `official_status_evidence_packet_closure_worklist.csv`
- `official_status_evidence_family_matrix.csv`
- `official_status_source_lineage_requirements.csv`
- `official_status_blocker_matrix.csv`
- `official_status_no_hit_handoff_matrix.csv`
- `official_status_safety_flags.json`
- `official_status_evidence_packet_closure_worklist_report.md`

## Research-Status Policy

`research-status` exposes this worklist as lower-priority research context only. It may expose latest run id, selected signal date, universe, status, health status, workflow stage, report path, row counts, blocker counts, no-hit counts, profile-conflict counts, survivorship-warning counts, missing-source/permission/revision/available-time counts, safety fields, and recommended next task.

The final workflow priority must preserve `PAPER_WORKFLOW_READY` when later paper workflow evidence exists.

Research-status must not expose or imply official evidence closure, PIT evidence closure, PIT admissibility approval, active replay input, replay execution, replay decision freeze, forward-label creation, metric computation, model training, stock_profile validation, paper expansion, real buy-review, broker integration, order placement, message delivery, external API or LLM calls, protected data writes, current-candidates execution, snapshot build, signal semantics mutation, or trading permission.

## Interpretation Boundaries

- A packet row is not PIT approval.
- `packet_row_ready_not_pit_approved` is not PIT admissible.
- `no_hit_accepted_context` is not source reliability scoring.
- `source_hash_preview` is not source_hash validation.
- `local_file_hash_preview` is not PIT evidence by itself.
- Same-day quotation presence is not automatically listed/not-delisted/no-ST/not-suspended/universe-membership proof.
- ETF ST not-applicable policy is required for ETF rows if no ST evidence applies.
- STOCK rows under legacy `etf_core` remain profile-conflict review context until separately resolved.
- Universe membership cannot be inferred from the legacy `etf_core` label alone.
- Forward returns remain future information.
- The 8-layer factor taxonomy remains the primary structure; fixed 12 factors are not final.

## Safety Fields

These fields must remain false unless a separate future workflow explicitly changes scope:

- `official_status_evidence_closed=false`
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

Positive scope flags are `report_only=true`, `diagnostic_only=true`, `local_only=true`, and `selected_sample_context_only=true`.

## Known Limitations

- The worklist does not collect official evidence.
- The worklist does not close official status evidence.
- No PIT validator is invoked.
- No replay-ready or active replay input is created.
- Mixed stock/ETF profile context under the legacy `etf_core` label remains manual review context.
- No-hit context remains evidence context and is not source reliability scoring.
- Source and local hash previews are not validation.
