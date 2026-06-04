# Reviewed Replacement Worklist Acceptance

`reviewed-replacement-worklist-acceptance` acknowledges reviewed replacement worklist templates as planning artifacts only.

It consumes a reviewed replacement worklist plan and writes accepted planning copies under `outputs/reports/reviewed_replacement_worklist_acceptance/<acceptance_id>/`. It does not make those worklists active, approve PIT universe rows, reject rows, export universe files, write `data/raw`, write `data/processed`, run current-candidates, build snapshots, compute forward labels, mutate cache, call APIs, place orders, or send messages.

## Command

```powershell
python -m quant_replay_system.cli reviewed-replacement-worklist-acceptance `
  --replacement-plan outputs/reports/reviewed_replacement_worklist_plan/0774d0a1fdb9/reviewed_replacement_worklist_plan.csv `
  --accepted-by <reviewer_id> `
  --accepted-at <timestamp> `
  --acceptance-reason "<planning reason>" `
  --manual-acceptance
```

The command requires explicit manual acceptance metadata. Missing `--manual-acceptance`, `--accepted-by`, `--accepted-at`, or `--acceptance-reason` blocks the run.

## Artifacts

The workflow writes:

- `reviewed_replacement_worklist_acceptance.csv`
- `accepted_replacement_worklist_stock_core.csv`
- `accepted_replacement_worklist_etf_core.csv`
- `accepted_replacement_worklist_mixed_demo_core.csv`
- `accepted_update_template_stock_core.csv`
- `accepted_update_template_etf_core.csv`
- `accepted_update_template_mixed_demo_core.csv`
- `report.md`
- `metadata.json`

All outputs are report-only planning artifacts.

## Safety Semantics

Acceptance means the replacement templates have been acknowledged as planning context. It does not mean:

- active worklists were replaced
- rows were approved for PIT universe use
- rows became valid for signal dates
- universe files were exported
- candidate generation was run
- strategy performance was validated

Rows remain conservative:

- `review_status=NEEDS_MANUAL_REVIEW`
- `include_flag=false`
- `valid_for_signal_date=false`
- `manual_review_required=true`

## Artifact Views

Use:

```powershell
python -m quant_replay_system.cli reviewed-replacement-worklist-acceptance-index
python -m quant_replay_system.cli reviewed-replacement-worklist-acceptance-health
python -m quant_replay_system.cli reviewed-replacement-worklist-acceptance-status
```

Health checks verify required files, acceptance metadata, safety flags, and that no approval/rejection/export/active mutation was recorded.

## Research-status

`research-status` includes reviewed replacement worklist acceptance context. It shows the latest acceptance id, row counts, lineage, health status, and whether the active legacy worklist was mutated.

Later workflow stages, including `PAPER_WORKFLOW_READY`, remain higher priority. Acceptance is planning context only.

## Next Planning Step

After acceptance, `reviewed-replacement-worklist-activation` can create a separate activated planning artifact under `outputs/reports` only. Activation still does not mutate active worklists, approve/reject rows, export universe files, run current-candidates, build snapshots, or compute labels. See [reviewed_replacement_worklist_activation.md](reviewed_replacement_worklist_activation.md).
