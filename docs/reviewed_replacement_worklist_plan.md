# Reviewed Replacement Worklist Plan v0.1

`reviewed-replacement-worklist-plan` is a report-only workflow that consumes a universe profile split-worklist plan and creates future replacement templates for clarified universe profiles.

It is designed for the legacy mixed `etf_core` context where existing rows should be planned into:

- `stock_core` for STOCK rows
- `etf_core` for ETF rows
- `mixed_demo_core` only when a mixed/demo row is explicitly needed

The workflow leaves the active legacy worklist unchanged. It does not approve rows, reject rows, export universe files, write `data/raw`, write `data/processed`, run current-candidates, build snapshots, compute forward labels, mutate cache, call network/API/LLM APIs, connect to brokers, place orders, or send messages.

## CLI Usage

```cmd
python -m quant_replay_system.cli reviewed-replacement-worklist-plan --split-plan outputs\reports\universe_profile_split_worklist_plan\db2c09268c14\universe_profile_split_worklist_plan.csv
```

Inputs:

- `--split-plan`: row-level universe profile split-worklist plan CSV.
- `--output-dir`: report destination. Defaults to `outputs/reports/reviewed_replacement_worklist_plan`.

## Artifacts

The command writes:

```text
outputs/reports/reviewed_replacement_worklist_plan/<replacement_plan_id>/
  reviewed_replacement_worklist_plan.csv
  replacement_worklist_stock_core.csv
  replacement_worklist_etf_core.csv
  replacement_worklist_mixed_demo_core.csv
  replacement_update_template_stock_core.csv
  replacement_update_template_etf_core.csv
  replacement_update_template_mixed_demo_core.csv
  report.md
  metadata.json
```

The replacement templates are future review templates only. They do not replace the active worklist and they do not make any row valid for candidate generation.

## Artifact Views

Use these commands to make replacement-plan artifacts discoverable and dashboard-ready:

```cmd
python -m quant_replay_system.cli reviewed-replacement-worklist-plan-index
python -m quant_replay_system.cli reviewed-replacement-worklist-plan-health
python -m quant_replay_system.cli reviewed-replacement-worklist-plan-status
```

`reviewed-replacement-worklist-plan-index` scans `outputs/reports/reviewed_replacement_worklist_plan/` and records replacement plan ids, source split plan ids, row counts by future universe, safety flags, and artifact paths.

`reviewed-replacement-worklist-plan-health` checks metadata, plan CSVs, per-profile worklists, per-profile update templates, reports, required columns, and local-only safety flags.

`reviewed-replacement-worklist-plan-status` summarizes the latest replacement plan. A healthy plan surfaces as `REVIEWED_REPLACEMENT_WORKLIST_PLAN_READY`.

## Research Status

`research-status` includes the latest reviewed replacement worklist plan as future worklist planning context. The summary CSV, metadata, markdown report, and CLI output expose:

- latest replacement plan id
- replacement plan status/stage/health
- source split plan id
- total row count
- `stock_core`, `etf_core`, and `mixed_demo_core` row counts
- profile-conflict count carried from the split plan
- active worklist mutation flag
- report path
- next action

Replacement-plan status is earlier than generated current-candidates, advisory layers, market-update handoff, and paper workflow. If later paper workflow artifacts exist, the final `workflow_stage` remains on the later workflow while replacement-plan fields stay visible as context.

## Current Expected Counts

For the current split plan `db2c09268c14`, the expected replacement planning result is:

- total rows: 72
- `stock_core` rows: 56
- `etf_core` rows: 16
- `mixed_demo_core` rows: 0
- active worklist mutated: false
- approval/rejection/export: false

## Safety Boundaries

This workflow does not:

- approve rows
- reject rows
- mutate active worklists
- export universe files
- write `data/raw`
- write `data/processed`
- run current-candidates
- build snapshot manifests
- compute forward labels
- mutate market cache
- call network, external APIs, or LLM APIs
- place orders, contact brokers, or send messages

## Known Limitations

- The workflow creates future templates only; it does not activate replacement worklists.
- The workflow does not validate PIT evidence sufficiency.
- The workflow does not make rows eligible for current-candidates.
- The workflow does not enforce profile rules inside candidate generation.

## Recommended Next Step

Review the replacement templates manually. The next safe implementation is `reviewed-replacement-worklist-acceptance`, which acknowledges templates as planning context only. It still does not approve rows, reject rows, export universe files, activate worklists, build snapshots, generate candidates, or perform trading automation.
