# Unified Local Research Workflow E2E Smoke Test v0.1

The Unified Local Research Workflow E2E smoke test proves the local research path can run from data preparation through current candidates, paper review, paper reporting, reconciliation, and the top-level `research-status` dashboard.

It is local-only. It does not connect to brokers, submit orders, automate order placement, require API tokens, print secrets, or call network APIs.

## Purpose

The project has separate local workflows for:

- data source to ingestion pipeline,
- snapshot quality,
- current candidate generation,
- current-candidate artifact index and health checks,
- current-to-paper handoff,
- review template generation and health preflight,
- manual paper review,
- daily paper reports,
- fill reconciliation,
- data-prep and paper workflow dashboards,
- unified local research dashboard.

The E2E smoke test verifies that these pieces can hand artifacts to each other without manual path stitching.

## Local-Only Workflow

The automated test uses `tmp_path`, the tiny local manifest at `data/mock/data_pipeline_manifest.json`, and temporary review/fill CSVs created inside the test.

It exercises CLI-style calls equivalent to:

```powershell
python -m quant_replay_system.cli data-pipeline --manifest data/mock/data_pipeline_manifest.json
python -m quant_replay_system.cli snapshot-quality --manifest <generated_snapshot_manifest>
python -m quant_replay_system.cli current-candidates --date 2024-01-08 --universe etf_core --snapshot-manifest <generated_snapshot_manifest>
python -m quant_replay_system.cli current-candidates-index --root <current_candidates_root>
python -m quant_replay_system.cli current-candidates-health --index <current_candidate_artifact_index.csv>
python -m quant_replay_system.cli current-to-paper --index <current_candidate_artifact_index.csv> --decision-date 2024-01-08 --universe etf_core
python -m quant_replay_system.cli current-to-paper-review --handoff-dir <handoff_dir>
python -m quant_replay_system.cli paper-review-decisions --decisions <decisions.csv> --updates <edited_review_updates.csv> --health-check
python -m quant_replay_system.cli paper-daily --date 2024-01-08 --reviewed-decisions <reviewed_decisions.csv> --fills <fills.csv>
python -m quant_replay_system.cli paper-reconcile-fills --decisions <reviewed_decisions.csv> --fills <fills.csv>
python -m quant_replay_system.cli paper-workflow-status --root <reports_root>
python -m quant_replay_system.cli data-prep-status --root <reports_root>
python -m quant_replay_system.cli research-status --root <reports_root>
```

The test also runs paper and data-prep artifact index/health commands so the dashboards can see the expected health artifacts.

## Expected Outputs

The temporary test run writes local artifacts under a temporary `reports` directory:

- `data_pipeline/<pipeline_id>/snapshot_manifest.json`
- `snapshot_quality/<snapshot_id>_<quality_gate_id>/snapshot_quality_gate_report.md`
- `current_candidates/<date>_<universe>_<run_id>/candidates.csv`
- `current_candidates/index/current_candidate_artifact_index.csv`
- `current_candidates/health/<health_id>/current_candidate_artifact_health_report.md`
- `current_to_paper_handoff/<handoff_id>/handoff_report.md`
- `current_to_paper_review_handoff/<review_handoff_id>/review_updates_template.csv`
- `paper_trading/reviews/<review_id>/reviewed_decisions.csv`
- `paper_trading/daily/<date>_<journal_id>/paper_report.md`
- `paper_trading/reconciliation/<reconciliation_id>/reconciliation_report.md`
- `paper_trading/workflow_status/<workflow_status_id>/paper_workflow_status_report.md`
- `data_preparation/workflow_status/<workflow_status_id>/data_preparation_workflow_status_report.md`
- `local_research_dashboard/<dashboard_id>/local_research_dashboard.md`

## Automated Test

The smoke test lives at:

```text
tests/test_local_research_workflow_e2e.py
```

It verifies:

- `data-pipeline` writes a snapshot manifest,
- `snapshot-quality` passes for the generated snapshot,
- `current-candidates` writes `candidates.csv`,
- `current-to-paper` writes initial paper decisions,
- `current-to-paper-review` writes a review update template,
- `paper-review-decisions --health-check` writes reviewed decisions,
- `paper-daily --reviewed-decisions` writes daily paper artifacts,
- `paper-reconcile-fills` writes reconciliation artifacts,
- `paper-workflow-status` writes a workflow report,
- `research-status` writes the unified dashboard report,
- CLI output includes the no-live-trading statement,
- no broker module or network/API path is invoked.

## No-Live-Trading Guarantee

This E2E path uses local CSV/mock inputs and temporary files only.

It does not:

- place live orders,
- connect to brokers,
- automate order placement,
- auto-approve trades,
- use real market-data APIs,
- require or print secrets.

Review updates and fills in the test are tiny deterministic fixtures created in `tmp_path`.

## Known MVP Limitations

- The smoke test verifies workflow wiring, not strategy quality.
- The market data is tiny mock data, not production data.
- It uses one approved paper fill and does not model a full trading lifecycle.
- It does not repair missing artifacts; dashboard and health modules report those separately.
