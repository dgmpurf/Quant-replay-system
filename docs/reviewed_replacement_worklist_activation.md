# Reviewed Replacement Worklist Activation

`reviewed-replacement-worklist-activation` creates a guarded, report-only activated planning copy of accepted replacement worklist templates.

Activation means the accepted replacement worklists are acknowledged as the current planning context for future manual evidence work. It does not make them active worklists, approve or reject PIT universe rows, export universe files, write `data/raw`, write `data/processed`, run current-candidates, build snapshots, compute forward labels, mutate cache, call APIs, place orders, or send messages.

## Command

```powershell
python -m quant_replay_system.cli reviewed-replacement-worklist-activation `
  --acceptance outputs/reports/reviewed_replacement_worklist_acceptance/c723c0c476b1/reviewed_replacement_worklist_acceptance.csv `
  --activated-by <reviewer_id> `
  --activated-at <timestamp> `
  --activation-reason "<planning reason>" `
  --manual-activation
```

The command requires explicit manual activation metadata. Missing `--manual-activation`, `--activated-by`, `--activated-at`, or `--activation-reason` blocks the run.

## Artifacts

The workflow writes only under `outputs/reports/reviewed_replacement_worklist_activation/<activation_id>/`:

- `reviewed_replacement_worklist_activation.csv`
- `activated_replacement_worklist_stock_core.csv`
- `activated_replacement_worklist_etf_core.csv`
- `activated_replacement_worklist_mixed_demo_core.csv`
- `activated_update_template_stock_core.csv`
- `activated_update_template_etf_core.csv`
- `activated_update_template_mixed_demo_core.csv`
- `report.md`
- `metadata.json`

All rows remain conservative:

- `review_status=NEEDS_MANUAL_REVIEW`
- `include_flag=false`
- `valid_for_signal_date=false`
- `manual_review_required=true`

## Artifact Views

Use:

```powershell
python -m quant_replay_system.cli reviewed-replacement-worklist-activation-index
python -m quant_replay_system.cli reviewed-replacement-worklist-activation-health
python -m quant_replay_system.cli reviewed-replacement-worklist-activation-status
```

Health checks verify required files, manual activation metadata, safety flags, and that no approval, rejection, export, active mutation, data write, current-candidates generation, snapshot build, or forward labeling was recorded.

## Research-status

`research-status` includes reviewed replacement worklist activation context. It shows the latest activation id, lineage to the acceptance/replacement/split/policy/worklist artifacts, row counts, health status, and whether the active legacy worklist was mutated.

Later workflow stages, including `PAPER_WORKFLOW_READY`, remain higher priority. Activation is planning context only.
