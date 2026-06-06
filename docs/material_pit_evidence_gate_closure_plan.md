# Material PIT Evidence Gate Closure Plan v0.1

`material-pit-evidence-gate-closure-plan` creates a report-only planning artifact for closing first-batch material PIT evidence gates.

It reads first-batch partial completion impact, reviewer evidence completion plan, checklist validator, policy comparison, official status evidence enrichment, reviewer no-hit acceptance, reviewer no-hit downstream impact, and optional diagnostics audit artifacts. It does not approve rows, reject rows, create clean `review_updates.csv`, run PIT review, run export-readiness, run staging, export universe files, write `data/raw`, write `data/processed`, mutate active worklists, mutate cache, run `current-candidates`, build snapshots, compute forward labels, call paid/private APIs, send messages, connect to brokers, or place orders.

## Command

```bash
python -m quant_replay_system.cli material-pit-evidence-gate-closure-plan
```

## Artifacts

Artifacts are written under:

```text
outputs/reports/material_pit_evidence_gate_closure_plan/<plan_id>/
```

Expected files:

- `material_pit_evidence_gate_closure_plan.csv`
- `row_level_material_blocker_matrix.csv`
- `reusable_symbol_level_closure_plan.csv`
- `date_specific_closure_plan.csv`
- `reviewer_no_hit_acceptance_closure_plan.csv`
- `survivorship_rationale_closure_plan.csv`
- `metadata_closure_plan.csv`
- `checklist_pass_candidate_requirements.csv`
- `reviewer_fill_template_by_closure_path.csv`
- `source_lineage_summary.csv`
- `report.md`
- `metadata.json`

## Closure Paths

Rows are classified into closure paths:

- `REUSABLE_SYMBOL_LEVEL`
- `DATE_SPECIFIC`
- `REVIEWER_NO_HIT_ACCEPTANCE`
- `SURVIVORSHIP_RATIONALE`
- `PIT_METADATA`
- `STOCK_ONLY_ST_NO_ST`
- `STILL_BLOCKED`

Reusable symbol-level evidence can reduce repeated evidence collection, but it does not close a signal-date row by itself. Date-specific PIT evidence, accepted no-hit context, survivorship rationale, and metadata completion remain required before any later checklist-pass candidate preview.

## Current Expected Result

The active first-batch state is expected to remain blocked:

- `row_count=16`
- `checklist_pass_candidate_count=0`
- `remaining_blocked_count=16`
- `date_specific_closure_required_count=16`
- `reviewer_no_hit_acceptance_required_count=16`
- `survivorship_rationale_required_count=16`
- `metadata_closure_required_count=16`
- `stock_st_no_st_required_count=8`
- `clean_review_updates_created=false`
- `approval_applied=false`

## Artifact Views

Use the local views to discover, safety-check, and summarize plan artifacts:

```bash
python -m quant_replay_system.cli material-pit-evidence-gate-closure-plan-index
python -m quant_replay_system.cli material-pit-evidence-gate-closure-plan-health
python -m quant_replay_system.cli material-pit-evidence-gate-closure-plan-status
```

The index exports the latest plan id, row counts, closure-path counts, safety flags, report path, plan CSV path, and metadata path.

The health check fails if artifacts imply approval, `include_flag=true`, `valid_for_signal_date=true`, clean review updates, PIT review, export-readiness, staging, universe export, `data/raw` or `data/processed` writes, current-candidates generation, snapshot build, forward labels, or missing planning-only safety flags.

The status view uses these stages:

- `NO_MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN`
- `MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_NEEDS_EVIDENCE`
- `MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_READY_FOR_REVIEWER_FILL`
- `MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_FAILED`

## Research Status

`research-status` includes the latest material PIT evidence gate closure plan as reviewer planning context. It exposes the latest plan id, status/stage, health status, row count, checklist-pass candidate count, remaining blocked count, closure-path counts, clean-review-updates flag, approval-applied flag, report path, and next manual action.

The plan is earlier than approval, export readiness, staging, current-candidates, snapshots, and paper workflow. If later paper workflow artifacts exist, final `workflow_stage` remains `PAPER_WORKFLOW_READY`; material-gate fields stay visible as context.

This integration does not approve rows, create clean review updates, export universe files, run current-candidates, build snapshots, compute forward labels, mutate cache, call APIs, send messages, connect to brokers, or place orders.
