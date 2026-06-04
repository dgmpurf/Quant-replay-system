# Activated Replacement Worklist Evidence Update Plan

`activated-replacement-worklist-evidence-update-plan` creates profile-specific manual evidence update packages from a guarded activated replacement worklist artifact.

The workflow is planning-only. It does not apply approvals, reject rows, mutate active worklists, export universe files, write `data/raw`, write `data/processed`, run current-candidates, build snapshots, compute forward labels, mutate cache, call APIs, place orders, or send messages.

## Command

```powershell
python -m quant_replay_system.cli activated-replacement-worklist-evidence-update-plan `
  --activation outputs/reports/reviewed_replacement_worklist_activation/a8e74161f9bb/reviewed_replacement_worklist_activation.csv
```

The command reads an activation artifact and writes manual evidence planning packages under:

```text
outputs/reports/activated_replacement_worklist_evidence_update_plan/<plan_id>/
```

## Artifacts

- `activated_replacement_worklist_evidence_update_plan.csv`
- `stock_core_evidence_worklist.csv`
- `etf_core_evidence_worklist.csv`
- `mixed_demo_core_evidence_worklist.csv`
- `stock_core_update_template.csv`
- `etf_core_update_template.csv`
- `mixed_demo_core_update_template.csv`
- `stock_core_first_batch_package.csv`
- `etf_core_first_batch_package.csv`
- `evidence_source_checklist.md`
- `report.md`
- `metadata.json`

The current activation lineage produces 72 planning rows: 56 `stock_core`, 16 `etf_core`, and 0 `mixed_demo_core`.

## Template Semantics

The profile-specific update templates are starting points for manual evidence collection. They preserve lineage to the legacy worklist, policy audit, split plan, replacement plan, acceptance artifact, and activation artifact.

All rows remain non-approved:

- `review_status=NEEDS_MANUAL_REVIEW`
- `include_flag=false`
- `valid_for_signal_date=false`
- `survivorship_bias_resolved=false`
- `manual_review_required=true`

Hint fields are non-authoritative until a reviewer supplies evidence. The generated templates are not clean `review_updates.csv` files and must not be treated as PIT universe input.

## Artifact Views

Use:

```powershell
python -m quant_replay_system.cli activated-replacement-worklist-evidence-update-plan-index
python -m quant_replay_system.cli activated-replacement-worklist-evidence-update-plan-health
python -m quant_replay_system.cli activated-replacement-worklist-evidence-update-plan-status
```

Health checks verify required artifacts, profile-specific row counts, non-approval flags, safety flags, and that no active mutation, export, data write, current-candidates generation, snapshot build, or forward labeling was recorded.

## Research-status

`research-status` includes activated replacement evidence-update planning context. It shows the latest plan id, activation id, replacement plan id, source worklist id, profile row counts, valid-for-signal-date count, clean-review-updates flag, health status, report path, and next manual action.

Later workflow stages, including `PAPER_WORKFLOW_READY`, remain higher priority. Evidence update plans are manual evidence collection context only.
