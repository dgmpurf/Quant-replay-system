# Release Checkpoint v0.80.0

## Milestone

Signal Advisory Artifact Views and Research Status Integration.

Recommended tag: `v0.80.0`

## Completed Capabilities

- Added local artifact views for signal advisory runs:
  - `signal-advisory-index`
  - `signal-advisory-health`
  - `signal-advisory-status`
- Integrated `signal-advisory-status` into unified `research-status`.
- Exported signal advisory context in `research-status` summary CSV, metadata, markdown report, and CLI output.
- Surfaced latest signal run id, signal stage, signal health status, signal counts, demo flags, alert preview path, and source candidate run.
- Preserved later paper workflow priority: a validated paper workflow remains the final active stage while signal advisory remains visible as context.
- Kept `DEMO_ONLY` advisory warnings visible as review-only context.
- Preserved the local alert preview boundary without sending real messages.
- Added no live trading, no broker API, and no automated-order behavior.

Latest local dry-run:

- `signal-advisory-status`
  - status: `WARN`
  - stage: `DEMO_SIGNAL_ADVISORY_VALIDATED`
  - latest_signal_run_id: `2921a18906bf`
  - signal_count: `9`
  - health_status: `PASS`
- `research-status`
  - status: `WARN`
  - final workflow_stage: `PAPER_WORKFLOW_READY`
  - latest_signal_run_id: `2921a18906bf`
  - signal stage: `DEMO_SIGNAL_ADVISORY_VALIDATED`
  - signal health: `PASS`
  - demo_signal_count: `9`
  - alert preview: `outputs/reports/signals/2921a18906bf/signal_alert_preview.md`
  - later paper workflow priority preserved

## Product Vision Alignment

This milestone strengthens the project's near-term direction as a quantitative research, signal advisory, and human-confirmed execution assistant.

Signals are advisory artifacts, not orders. `research-status` can now show whether a local advisory signal run exists, whether its safety checks passed, whether an alert preview is available, and whether the latest signal run is demo-only. This gives the user a reproducible advisory layer before any future delivery channel or execution-assistant work.

Full automation and international market expansion remain later-stage goals.

## Workflow Impact

The completed workflow chain is:

```text
current-candidates
-> signal-advisory
-> signal-advisory-index / health / status
-> research-status
-> manual review / future alert preview / paper workflow
```

`research-status` now treats signal advisory as contextual evidence between current-candidates and any human/action layer. If signal advisory is the active stage, health failures remain actionable. If a later paper workflow already exists, paper workflow priority is preserved and signal advisory remains visible as context.

## Validation Baseline

- Backend tests: `1035 passed, 2 warnings`
- Quick tests: `926 passed, 109 deselected, 2 warnings`

The warnings are the existing pandas date-format inference warnings in data ingestion/factor dataset tests.

## Safety Guarantees

- A signal is not an order.
- A demo signal is not a strategy recommendation.
- Alert preview is local markdown only.
- No real SMS, email, Telegram, WeChat, webhook, or broker message delivery was added.
- Manual confirmation remains required.
- `auto_order_allowed=false` remains the default boundary.
- No broker API was implemented or invoked.
- No live trading was implemented or invoked.
- No automated order placement was implemented or invoked.
- No scheduler, cron, or GitHub Actions automation was added.
- Generated `data/cache`, `data/raw`, `data/processed`, and `outputs` artifacts are ignored and must not be committed.

## Known Limitations

- Signal advisory is still local artifact/markdown preview only.
- No real delivery channel exists.
- No single-symbol advisory review exists yet.
- Demo candidates produce `DEMO_ONLY` only.
- Non-demo signal semantics still need future strategy validation.
- No automated execution exists.
- No international market support exists yet.

## Recommended Next Engineering Tasks

1. Add a single-symbol advisory review command that uses local cache/snapshot evidence to answer watch/buy/sell/hold review questions with reasons, validity, invalidation, and risk notes.
2. Add explicit alert-delivery design documentation before any SMS, email, Telegram, WeChat, or webhook implementation.
3. Build a local-only alert delivery dry-run that consumes `signal_alert_preview.md` without sending messages.
4. Add richer signal health checks for non-demo future advisory profiles before treating any advisory output as strategy-review candidate evidence.
5. Preserve the manual-confirmation boundary before any future paper approval or execution-assistant workflow.
