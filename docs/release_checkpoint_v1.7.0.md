# Release Checkpoint v1.7.0

## Milestone

PIT Universe Evidence Update Ingestion Artifact Views and Research Status Integration.

## Completed Capabilities

- Added local artifact views for `pit-universe-evidence-update-ingestion`:
  - `pit-universe-evidence-update-ingestion-index`
  - `pit-universe-evidence-update-ingestion-health`
  - `pit-universe-evidence-update-ingestion-status`
- Indexed ingestion artifacts with row counts, ready-for-review-update counts, blocked counts, approval-request counts, approved-ready counts, duplicate identity counts, suggested-copy-risk counts, report paths, clean review-updates paths, and local-only safety flags.
- Added health checks for metadata, ingestion CSVs, clean review-updates CSVs, required columns, count consistency, blocked-row exclusion from clean review updates, and safety metadata.
- Added status stages for no-ready-updates, partial-ready updates, ready-for-review-apply context, health warnings, and failures.
- Integrated latest evidence update ingestion status into unified `research-status`.
- Preserved later paper workflow priority: evidence update ingestion context remains visible, while final `workflow_stage` can stay on the active paper workflow path.

## Workflow Impact

The PIT universe evidence chain is now observable through:

```text
pit-universe-evidence-review-worklist
-> reviewer-completed local update CSV
-> pit-universe-evidence-update-ingestion
-> clean pit_universe_review_updates.csv
-> ingestion index / health / status
-> research-status context
-> later explicit pit-universe-overlay-review
```

The current local ingestion run remains blocked/no-ready context:

- latest ingestion id: `284058e7f1e4`
- status: `WARN`
- stage: `PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_NO_READY_UPDATES`
- health: `PASS`
- row count: `72`
- ready-for-review-update count: `0`
- blocked count: `72`
- approval-request count: `0`
- approved-ready count: `0`
- duplicate identity count: `0`
- suggested-copy-risk count: `0`

`research-status` shows those fields while preserving the final `PAPER_WORKFLOW_READY` stage.

## Validation Baseline

Local dry-runs completed:

```powershell
python -m quant_replay_system.cli pit-universe-evidence-update-ingestion-index
python -m quant_replay_system.cli pit-universe-evidence-update-ingestion-health
python -m quant_replay_system.cli pit-universe-evidence-update-ingestion-status
python -m quant_replay_system.cli research-status
```

Focused validation completed during implementation:

```powershell
python -m pytest tests/test_point_in_time_universe_evidence_update_ingestion_artifact_views.py
python -m pytest tests/test_local_research_dashboard.py -k "evidence_update_ingestion"
```

Final full validation should use:

```powershell
python -m pytest
python -m pytest -m "not slow"
```

## Safety Guarantees

- Evidence update ingestion is validation-only.
- No approval is applied.
- No `pit-universe-overlay-review` run is triggered automatically.
- No usable universe export is produced.
- No `data/raw` write occurs.
- No `data/processed` write occurs.
- No current-candidates generation occurs.
- No snapshot manifest is built.
- No forward labels are computed.
- No market cache mutation occurs.
- No live trading is enabled.
- No broker API is called.
- No order placement is automated.
- No real message delivery occurs.
- No LLM/API or external API call is required by this workflow.
- Generated outputs remain under `outputs/reports` and must not be committed.

## Known Limitations

- The latest local ingestion artifact has zero clean ready-for-review-update rows.
- Blocked reviewer update rows still require manual evidence completion.
- Clean `pit_universe_review_updates.csv` rows, if produced later, are only inputs for a separate explicit manual review workflow.
- The artifact views do not verify external evidence documents.
- The workflow does not create point-in-time valid universe files.
- The workflow does not validate strategy performance or market edge.

## Recommended Next Engineering Tasks

- Complete local reviewer evidence fields for selected PIT universe rows.
- Re-run `pit-universe-evidence-update-ingestion` with reviewer-completed updates.
- If clean rows appear, run a separate explicit `pit-universe-overlay-review` using the clean review-updates artifact.
- Keep export/readiness/staging workflows blocked until approved PIT rows are available with evidence.
- Continue preserving dashboard priority so later paper workflow context is not regressed by earlier evidence-preparation warnings.

## Recommended Tag

`v1.7.0`
