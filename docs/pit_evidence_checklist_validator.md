# PIT Evidence Checklist Validator v0.1

`pit-evidence-checklist-validator` validates completed or draft PIT universe evidence update rows against strict `stock_core` and `etf_core` evidence checklists.

This workflow is report-only. It does not apply approvals, set `APPROVED_FOR_PIT_UNIVERSE`, rerun `pit-universe-overlay-review`, run export readiness, run export staging, export universe files, write `data/raw`, write `data/processed`, run current-candidates, build snapshots, compute forward labels, mutate cache, call APIs, send messages, connect to brokers, or place orders.

## Purpose

The validator sits after evidence update ingestion and before any explicit PIT overlay review:

```text
profile-specific evidence package
-> reviewer update CSV
-> pit-universe-evidence-update-ingestion
-> pit-evidence-checklist-validator
-> manual approval-candidate review only
-> later explicit pit-universe-overlay-review, if chosen
```

It answers:

- Which rows are missing strict PIT evidence?
- Which rows are blocked by active/not-delisted evidence gaps?
- Which rows are blocked by unresolved survivorship risk?
- Which stock rows are missing ST/no-ST evidence?
- Which rows are blocked by conservative PIT timing rules such as post-close local cache evidence?
- Which rows use context-only or rejected source hints?
- Are any rows complete enough to appear in an approval-candidate preview?

An approval-candidate preview is not an approval. It is only a local review aid.

## CLI Usage

```cmd
python -m quant_replay_system.cli pit-evidence-checklist-validator --completed-updates outputs\reports\manual_diagnostics\codex_pit_evidence_gap_closure_v0_2\combined_approval_candidate_updates.csv --stock-checklist outputs\reports\manual_diagnostics\pit_strict_evidence_checklist_v0_3\stock_core_strict_evidence_checklist.csv --etf-checklist outputs\reports\manual_diagnostics\pit_strict_evidence_checklist_v0_3\etf_core_strict_evidence_checklist.csv --source-acceptance outputs\reports\manual_diagnostics\pit_strict_evidence_checklist_v0_3\source_acceptance_matrix.csv
```

Options:

- `--completed-updates`: completed or draft reviewer update rows.
- `--stock-checklist`: strict checklist for `stock_core`.
- `--etf-checklist`: strict checklist for `etf_core`.
- `--source-acceptance`: optional source acceptance matrix.
- `--output-dir`: destination root for validator artifacts.

Symbols are preserved as strings so leading zeros such as `000001` remain intact.

## Required Evidence

The validator checks for reviewer and evidence fields:

- `reviewer`
- `reviewed_at`
- `review_reason`
- `evidence_source`
- `evidence_path` or `evidence_reference`
- `listed_date`
- `listed_date_evidence`

It also checks PIT universe metadata and state fields:

- `is_active`
- `is_active_evidence`
- `is_suspended`
- `as_of_date`
- `name`
- `instrument_type`
- `exchange`
- `industry`
- `min_lot`
- `t_plus_rule`
- `available_time`
- `revision_id`
- `source`
- `survivorship_bias_resolved=true`

For `stock_core`, `is_st` is required as ST/no-ST evidence. ETF rows do not require `is_st` by default.

## Conservative Blockers

Rows remain blocked when:

- required evidence fields are blank;
- active/not-delisted evidence is missing;
- survivorship bias is unresolved;
- a stock row lacks ST/no-ST evidence;
- `as_of_date` or `available_time` is missing or later than the signal date;
- `available_time` is post-close such as `15:30` without an explicit reviewed EOD policy;
- evidence appears to come from a future-dated processed universe hint, blog, forum, unknown source, or context-only local cache hint for active-status proof.

The validator is intentionally conservative. A local same-day market row can be useful context, but it does not by itself resolve listing, active, ST/no-ST, not-delisted, or survivorship evidence requirements.

## Artifacts

Artifacts are written under:

```text
outputs/reports/pit_evidence_checklist_validator/<validator_id>/
```

Files:

- `pit_evidence_checklist_validation.csv`
- `pit_evidence_checklist_validation_summary.csv`
- `missing_evidence_matrix.csv`
- `approval_candidate_preview.csv`
- `report.md`
- `metadata.json`

The approval-candidate preview contains only rows that pass the checklist. It does not apply approval and should not be copied directly into active review artifacts without a separate explicit review step.

## Artifact Views

Use:

```cmd
python -m quant_replay_system.cli pit-evidence-checklist-validator-index
python -m quant_replay_system.cli pit-evidence-checklist-validator-health
python -m quant_replay_system.cli pit-evidence-checklist-validator-status
```

The index discovers validator artifacts and safety flags. The health check verifies required files, required columns, and local-only safety boundaries. The status command summarizes the latest validator run with stages:

- `NO_PIT_EVIDENCE_CHECKLIST_VALIDATION`
- `PIT_EVIDENCE_CHECKLIST_VALIDATION_BLOCKED`
- `PIT_EVIDENCE_CHECKLIST_VALIDATION_HAS_APPROVAL_CANDIDATES`
- `PIT_EVIDENCE_CHECKLIST_VALIDATION_HEALTH_WARN`
- `PIT_EVIDENCE_CHECKLIST_VALIDATION_FAILED`

## Research Status

`research-status` includes the latest `pit-evidence-checklist-validator-status` as PIT evidence quality-gate context. The unified summary exposes validator id, status/stage, health status, row count, checklist-pass count, blocked count, `stock_core` blocked count, `etf_core` blocked count, report path, and next manual action.

When the validator reports `PIT_EVIDENCE_CHECKLIST_VALIDATION_BLOCKED`, the dashboard treats it as expected reviewable evidence work, not as candidate-generation failure or strategy failure. If later paper workflow artifacts exist, final `workflow_stage` remains on the later paper workflow path and validator fields remain visible as audit context.

## Safety Boundaries

The workflow records:

- `approval_applied=false`
- `universe_exported=false`
- `would_write_data_raw=false`
- `would_write_data_processed=false`
- `current_candidates_executed=false`
- `snapshot_manifest_built=false`
- `forward_returns_computed=false`
- `cache_mutated=false`
- `network_api_called=false`
- `llm_api_called=false`
- `live_trading_enabled=false`
- `broker_api_invoked=false`
- `order_placement_enabled=false`
- `message_delivery_enabled=false`
- `checklist_validation_only=true`

## Known Limitations

- The validator does not verify external evidence documents.
- The source acceptance matrix is applied conservatively from row text and checklist context.
- Post-close local cache timing remains blocked unless a future reviewed EOD policy is added.
- Checklist passes do not prove strategy performance, market edge, or universe export readiness.
- A separate explicit `pit-universe-overlay-review` run is still required before any row can become a reviewed PIT universe row.

## Policy Profile Comparison

`pit-evidence-policy-profile-comparison` can compare strict validator output with the opt-in `EOD_POST_CLOSE_LOW_BUDGET_PIT` profile. The comparison is report-only: it does not change the strict validator default, does not apply approvals, and does not create approval updates. See [pit_evidence_policy_profile_comparison.md](pit_evidence_policy_profile_comparison.md).
