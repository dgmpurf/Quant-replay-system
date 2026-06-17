# Forward Return Label

`forward-return-label` is a report-only workflow for creating audited forward-return label context after a frozen replay decision artifact exists. It is designed to make future outcome windows visible for later research review while keeping decision-time replay inputs, model training, stock profiles, paper approval, and trading strictly separate.

The workflow can create local report artifacts such as label rows, label metadata, validation summaries, and safety reports under `outputs/reports/manual_diagnostics/forward_return_label_v0_1/`. It is not training, not stock_profile creation, not buy-review eligibility, not paper approval, not performance validation, and not trading.

## Commands

```powershell
python -m quant_replay_system.cli forward-return-label
python -m quant_replay_system.cli forward-return-label-index
python -m quant_replay_system.cli forward-return-label-health
python -m quant_replay_system.cli forward-return-label-status
python -m quant_replay_system.cli research-status
```

The artifact view commands discover, health-check, and summarize existing report-only label artifacts. `research-status` exposes the latest forward-return label context without changing the final paper workflow priority.

## Research-Status Fields

The unified dashboard records the latest label run id, status, health status, workflow stage, artifact path, source replay-decision-freeze lineage, replay-decision counts, label row counts, label names, symbol counts, next action, and safety flags.

The forward label fields are namespaced in the dashboard, for example:

- `latest_forward_return_label_run_id`
- `latest_forward_return_label_status`
- `latest_forward_return_label_health_status`
- `latest_forward_return_label_workflow_stage`
- `forward_return_label_forward_labels_allowed`
- `forward_return_label_forward_labels_exist`
- `forward_return_label_forward_return_labels_created`
- `forward_return_label_label_row_count`
- `forward_return_label_report_path`

These fields are context only. They do not imply that a replay was run, that training happened, that weights were calibrated, that an active stock profile exists, or that a buy review is allowed.

## Safety Boundaries

Forward-return labels are future outcome records and must not leak into decision-time replay input. The workflow and dashboard integration preserve these boundaries:

- no active replay input mutation,
- no current-candidates run,
- no snapshot build,
- no training,
- no training_result creation,
- no stock_profile creation,
- no buy-review eligibility,
- no paper approval,
- no performance validation,
- no trading,
- no broker integration,
- no order placement,
- no message sending,
- no LLM or external API call,
- no cache mutation,
- no `data/raw`, `data/processed`, or `data/cache` write.

If a forward-return label artifact ever claims unsafe side effects, its health/status layer should surface that as a blocker before downstream use.

## Interpretation

`FORWARD_RETURN_LABEL_READY` means label reports exist and are reviewable. It does not mean the labels are approved training targets, does not validate a strategy, and does not authorize paper or live actions.

The recommended next step after reviewing labels is a separate, explicit report-only design or governance task for any future label acceptance, model training, or evaluation workflow.
