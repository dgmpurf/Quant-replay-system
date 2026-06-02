# Release Checkpoint v1.5.0

## Milestone

PIT Universe Export Staging Artifact Views and Research Status Integration.

Recommended tag: `v1.5.0`

## Completed Capabilities

- `pit-universe-export-staging` creates guarded staging previews under `outputs/reports` only.
- `pit-universe-export-staging-index` discovers staging artifacts and records linked export-readiness/review ids, row counts, staged rows, blocked rows, diagnostic-source flags, no-ready-row flags, safety flags, and paths.
- `pit-universe-export-staging-health` verifies staging artifacts did not claim `data/raw` writes, `data/processed` writes, current-candidates generation, snapshot builds, forward labels, API calls, broker access, order placement, message delivery, or cache mutation.
- `pit-universe-export-staging-status` summarizes the latest staging artifact into dashboard-ready stages.
- Unified `research-status` now exposes PIT universe export staging context while preserving later paper workflow priority.

## Workflow Impact

The local PIT universe preparation path now includes:

```text
PIT universe overlay review
-> export readiness
-> guarded export staging
-> future explicit accepted universe export
-> future snapshot preparation
-> future current-candidates generation
```

The current active staging context is expected to remain blocked when no export-ready PIT universe rows exist. That is planning context, not a failed universe export.

## Validation Baseline

- Focused staging/dashboard validation: `161 passed`
- Full validation should run before tagging:
  - `python -m pytest`
  - `python -m pytest -m "not slow"`

## Safety Guarantees

- No usable universe export occurred.
- No `data/raw` write occurred.
- No `data/processed` write occurred.
- No current-candidates generation occurred.
- No snapshot manifest was built.
- No forward labels were computed.
- No market cache mutation occurred.
- No live trading, broker API, automated order placement, or real message delivery was implemented.
- No LLM/API or external network call is required by the staging views.
- Staged previews are review artifacts only and must not be treated as accepted universe inputs.

## Known Limitations

- The active local review still has no approved export-ready rows, so staging can remain blocked with `PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS`.
- Staging does not accept previews into `data/raw` or `data/processed`.
- Staging does not build snapshot manifests or generate multi-date current-candidates.
- Staging does not validate strategy performance or prove market edge.
- Diagnostic-source staging is blocked by default for active workflows.

## Recommended Next Engineering Tasks

- Complete manual PIT universe evidence for selected rows before expecting export-ready rows.
- Add an explicit accepted universe export workflow only after reviewed rows are fully approved and export-ready.
- Keep accepted export separate from staging so `data/raw` or `data/processed` writes require explicit manual acceptance.
- Add snapshot-preparation planning after accepted universe export exists.
- Continue preserving paper workflow priority in `research-status`.
