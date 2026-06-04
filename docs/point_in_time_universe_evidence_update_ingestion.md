# PIT Universe Evidence Update Ingestion Validator v0.1

`pit-universe-evidence-update-ingestion` validates reviewer-completed PIT universe evidence update CSVs created from the evidence review worklist update template.

It is ingestion-validation-only. It does not apply approval, rerun `pit-universe-overlay-review`, export usable universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshot manifests, compute forward labels, mutate cache files, call APIs, send messages, connect to brokers, or place orders.

## Purpose

The validator sits after the reviewer fills a worklist update CSV:

```text
pit-universe-evidence-review-worklist
-> reviewer-completed update CSV
-> pit-universe-evidence-update-ingestion
-> clean pit_universe_review_updates.csv
-> later explicit pit-universe-overlay-review run
```

It answers:

- Did the reviewer provide valid row identity keys?
- Are duplicate updates present?
- Did approval-request rows include reviewer and evidence fields?
- Are point-in-time dates valid for the signal date?
- Did any approval-request row appear to copy non-authoritative `suggested_*` hints without evidence?
- Which rows are clean enough to be passed manually to `pit-universe-overlay-review` later?

## CLI Usage

```cmd
python -m quant_replay_system.cli pit-universe-evidence-update-ingestion --completed-updates outputs\reports\point_in_time_universe_evidence_review_worklist\1c7972988f59\pit_universe_evidence_review_update_template.csv --worklist outputs\reports\point_in_time_universe_evidence_review_worklist\1c7972988f59\pit_universe_evidence_review_worklist.csv
```

Optional:

- `--worklist`: cross-checks identity coverage and `suggested_*` hint copy risk.
- `--output-dir`: destination root for ingestion artifacts.

## Inputs

The completed update CSV must include:

- `signal_date`
- `symbol`
- `universe_name`
- `review_status`

The validator preserves `symbol` as a string so leading zeros such as `000001` remain intact.

Identity keys are:

```text
signal_date + symbol + universe_name
```

## Approval-request Requirements

Rows with `review_status=APPROVED_FOR_PIT_UNIVERSE` must include:

- `include_flag=true`
- `reviewer`
- `reviewed_at`
- `review_reason`
- `evidence_source`
- `evidence_path` or `evidence_reference`
- `listed_date_evidence`
- `is_active_evidence`
- `survivorship_bias_resolved=true`
- `as_of_date`
- `name`
- `instrument_type`
- `exchange`
- `listed_date`
- `is_active`
- `is_st`
- `is_suspended`
- `industry`
- `min_lot`
- `t_plus_rule`
- `available_time`
- `revision_id`
- `source`

Point-in-time date checks:

- `listed_date <= signal_date`
- `delisted_date` blank or `delisted_date >= signal_date`
- `as_of_date <= signal_date`
- `available_time` on or before the conservative signal-date decision time

## Non-approval Rows

`REJECTED` rows must include:

- `reviewer`
- `reviewed_at`
- `review_reason`

`NEEDS_MORE_EVIDENCE` rows can be emitted as clean review updates when they include a review reason.

`NEEDS_MANUAL_REVIEW` rows pass identity parsing but are not treated as clean review updates. A blank template therefore remains blocked instead of being written into `pit_universe_review_updates.csv`.

## Suggested Hint Protection

When `--worklist` is supplied, the validator compares authoritative fields such as `name`, `instrument_type`, `exchange`, `industry`, `min_lot`, `t_plus_rule`, `available_time`, `revision_id`, and `source` against `suggested_*` hints.

Hints remain non-authoritative. If an approval-request row appears to copy suggested values without reviewer evidence, it is blocked with `UPDATE_BLOCKED_SUGGESTED_HINT_COPY_RISK`.

## Outputs

Artifacts are written under:

```text
outputs/reports/point_in_time_universe_evidence_update_ingestion/<ingestion_id>/
```

Files:

- `pit_universe_evidence_update_ingestion.csv`
- `pit_universe_review_updates.csv`
- `pit_universe_evidence_update_ingestion_report.md`
- `metadata.json`

`pit_universe_review_updates.csv` includes only rows that passed ingestion validation. It preserves reviewer-supplied `review_status` and is suitable for later manual use with `pit-universe-overlay-review`.

Generating this file does not mean approval was applied to the active workflow.

## Artifact Views

Use the artifact-view commands to make ingestion runs discoverable and safety-checkable:

```cmd
python -m quant_replay_system.cli pit-universe-evidence-update-ingestion-index
python -m quant_replay_system.cli pit-universe-evidence-update-ingestion-health
python -m quant_replay_system.cli pit-universe-evidence-update-ingestion-status
```

The index records ingestion ids, row counts, clean `review_updates` counts, blocked counts, duplicate identity counts, suggested-copy-risk counts, safety flags, and artifact paths.

The health check verifies metadata, the ingestion CSV, the clean review-updates CSV, required columns, count consistency, blocked-row exclusion from clean updates, and local-only safety flags. A blank or incomplete reviewer update set can still be a healthy blocked-readiness artifact when no unsafe writes or approvals occurred.

The status command summarizes the latest ingestion run with stages such as:

- `PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_NO_READY_UPDATES`
- `PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_PARTIAL_READY`
- `PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_READY_FOR_REVIEW_APPLY`
- `PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_HEALTH_WARN`
- `PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_FAILED`

Status remains context only. `READY_FOR_REVIEW_APPLY` means a clean local review-updates file exists for a later explicit manual `pit-universe-overlay-review` run; it does not apply approval.

## Strict Checklist Validation

After ingestion creates or blocks clean review updates, use `pit-evidence-checklist-validator` to compare completed or draft rows against the strict `stock_core` and `etf_core` evidence checklists:

```cmd
python -m quant_replay_system.cli pit-evidence-checklist-validator --completed-updates outputs\reports\manual_diagnostics\codex_pit_evidence_gap_closure_v0_2\combined_approval_candidate_updates.csv --stock-checklist outputs\reports\manual_diagnostics\pit_strict_evidence_checklist_v0_3\stock_core_strict_evidence_checklist.csv --etf-checklist outputs\reports\manual_diagnostics\pit_strict_evidence_checklist_v0_3\etf_core_strict_evidence_checklist.csv --source-acceptance outputs\reports\manual_diagnostics\pit_strict_evidence_checklist_v0_3\source_acceptance_matrix.csv
```

The checklist validator is report-only. It can produce an approval-candidate preview, but it does not apply approval, rerun PIT overlay review, run export readiness, stage or export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, compute forward labels, or mutate cache. See [pit_evidence_checklist_validator.md](pit_evidence_checklist_validator.md).

## Research Status

`research-status` includes the latest `pit-universe-evidence-update-ingestion-status` as PIT universe evidence-preparation context. The dashboard exposes the latest ingestion id, status/stage, health status, row count, ready-for-review-update count, blocked count, approval-request count, approved-ready count, duplicate identity count, suggested-copy-risk count, report path, clean review-updates path, and next manual action.

If later paper workflow artifacts exist, the final `workflow_stage` does not regress to evidence update ingestion. Ingestion fields remain visible as audit context.

## Status Values

Row-level ingestion statuses include:

- `UPDATE_READY_FOR_REVIEW_APPLY`
- `UPDATE_BLOCKED_MISSING_IDENTITY`
- `UPDATE_BLOCKED_DUPLICATE_IDENTITY`
- `UPDATE_BLOCKED_INVALID_STATUS`
- `UPDATE_BLOCKED_MISSING_REVIEWER`
- `UPDATE_BLOCKED_MISSING_EVIDENCE`
- `UPDATE_BLOCKED_UNRESOLVED_SURVIVORSHIP`
- `UPDATE_BLOCKED_MISSING_UNIVERSE_METADATA`
- `UPDATE_BLOCKED_INVALID_PIT_DATES`
- `UPDATE_BLOCKED_SUGGESTED_HINT_COPY_RISK`

## Safety Boundaries

The workflow records:

- `approval_applied=false`
- `no_universe_export=true`
- `no_data_raw_write=true`
- `no_data_processed_write=true`
- `no_current_candidates_generated=true`
- `no_snapshot_built=true`
- `no_forward_labels=true`
- `cache_mutated=false`
- `network_api_called=false`
- `llm_api_called=false`
- `no_live_trading=true`
- `no_broker_api=true`
- `no_order_placement=true`
- `no_message_sent=true`
- `ingestion_only=true`

## Known Limitations

- The validator does not approve rows in the active PIT review workflow.
- It does not rerun `pit-universe-overlay-review`.
- It does not export usable universe files.
- It does not verify external evidence documents.
- It does not build snapshot manifests or generate multi-date candidates.
- A clean `pit_universe_review_updates.csv` still requires a separate explicit manual review workflow before any reviewed PIT universe row can exist.
