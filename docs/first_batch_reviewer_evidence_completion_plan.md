# First-Batch Reviewer Evidence Completion Plan v0.1

`first-batch-reviewer-evidence-completion-plan` creates report-only manual evidence completion planning artifacts for the first PIT review batch.

It reads the activated replacement evidence update plan first-batch packages, reviewer no-hit downstream impact, official status packet enrichment, checklist validator, and policy comparison artifacts. It does not approve PIT universe rows, reject rows, create clean `review_updates.csv`, run PIT review, run export-readiness, run staging, export universe files, write `data/raw`, write `data/processed`, mutate active worklists, mutate cache, run `current-candidates`, build snapshots, compute forward labels, call APIs, send messages, connect to brokers, or place orders.

## Command

```text
python -m quant_replay_system.cli first-batch-reviewer-evidence-completion-plan
```

Defaults:

- `--evidence-update-plan outputs/reports/activated_replacement_worklist_evidence_update_plan/4e268d67bd7d`
- `--downstream-impact outputs/reports/reviewer_no_hit_acceptance_downstream_impact/9e164963455e`
- `--enrichment outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c`
- `--validator outputs/reports/pit_evidence_checklist_validator/62e9eb747197`
- `--policy-comparison outputs/reports/pit_evidence_policy_profile_comparison/c1a75d1091c6`
- `--output-dir outputs/reports/first_batch_reviewer_evidence_completion_plan`

Artifact views:

```text
python -m quant_replay_system.cli first-batch-reviewer-evidence-completion-plan-index
python -m quant_replay_system.cli first-batch-reviewer-evidence-completion-plan-health
python -m quant_replay_system.cli first-batch-reviewer-evidence-completion-plan-status
```

## Outputs

Artifacts are written under:

```text
outputs/reports/first_batch_reviewer_evidence_completion_plan/<plan_id>/
```

Files:

- `first_batch_reviewer_evidence_completion_plan.csv`
- `row_level_missing_evidence_matrix.csv`
- `reusable_symbol_level_evidence_plan.csv`
- `date_specific_evidence_plan.csv`
- `reviewer_completion_template.csv`
- `reviewer_no_hit_acceptance_todo.csv`
- `survivorship_rationale_todo.csv`
- `metadata_completion_todo.csv`
- `source_lineage_summary.csv`
- `report.md`
- `metadata.json`

## Semantics

The active first batch is expected to contain 16 rows:

- `000001` in `stock_core` across 8 signal dates.
- `159915` in `etf_core` across 8 signal dates.

The planner keeps every row non-approved:

- `review_status=NEEDS_MORE_EVIDENCE`
- `include_flag=false`
- `valid_for_signal_date=false`
- `survivorship_bias_resolved=false`

Official same-date quotation evidence remains quotation/traded context only. It does not prove not-delisted status, ST/no-ST status, or survivorship-bias resolution by itself.

Reviewer no-hit source coverage remains supporting context only. It does not create checklist pass rows or clean review updates.

## Status and Research Dashboard

`first-batch-reviewer-evidence-completion-plan-status` reports one of:

- `NO_FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN`
- `FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_NEEDS_REVIEW`
- `FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_READY_FOR_MANUAL_FILL`
- `FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_FAILED`

`research-status` exposes the latest first-batch completion plan as planning context with row counts, reviewer completion requirements, no-hit acceptance requirements, survivorship rationale requirements, metadata completion requirements, checklist pass count, remaining blocked count, clean-review-update flag, approval-applied flag, report path, and next action.

This context does not imply PIT approval, export readiness, export staging, universe export, snapshot build, current-candidates generation, or trading. Later paper workflow artifacts keep final workflow priority while first-batch completion fields remain visible.

Partial reviewer completions can be inspected with `first-batch-partial-completion-impact`. That workflow compares diagnostics-only completed fields against the completion plan and reports blocker deltas, but it still does not create clean `review_updates.csv`, set `include_flag=true`, set `valid_for_signal_date=true`, or approve rows. See [first_batch_partial_completion_impact.md](first_batch_partial_completion_impact.md).

## Health Checks

Health fails if required artifacts are missing, required columns are missing, rows claim `APPROVED_FOR_PIT_UNIVERSE`, rows set `include_flag=true`, rows set `valid_for_signal_date=true`, metadata claims approval, a clean `review_updates.csv` is created, PIT review/export/staging/current-candidates are run, `data/raw` or `data/processed` is written, snapshots or forward labels are created, or the report-only flag is missing.

## Known Limitations

- The workflow does not fill real evidence.
- It does not change strict checklist validation.
- It does not apply reviewer no-hit acceptance.
- It does not create a clean review update file for ingestion.
- The latest active first batch is expected to remain blocked until a human completes evidence and a later workflow validates it.
