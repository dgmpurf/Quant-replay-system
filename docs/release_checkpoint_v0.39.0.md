# Release Checkpoint v0.39.0

## Release Summary

`v0.39.0` is the first complete local-only research workflow checkpoint for `quant-replay-system`.

This checkpoint proves that tiny local/mock data can move through the full auditable workflow:

```text
local data preparation -> snapshot quality -> current candidates -> paper handoff -> manual review -> daily paper report -> fill reconciliation -> research-status dashboard
```

It is a research infrastructure milestone. It is not a live trading release, broker integration, order automation system, strategy-quality proof, or profit guarantee.

## Completed Capabilities

The checkpoint includes these completed areas:

- Point-in-time data contract.
- Trading calendar and T+1 execution calendar.
- Technical indicators.
- Point-in-time factor dataset builder.
- Explainable scoring and candidate selection.
- Replay, batch replay, parameter calibration, and walk-forward validation.
- Portfolio simulation.
- Local data ingestion and data source to ingestion pipeline.
- Data quality reports and snapshot quality gate.
- Current candidate generation.
- Current candidate artifact index and health check.
- Manual paper trading journal.
- Paper trading review workflow.
- Fill reconciliation.
- Paper trading artifact index and health check.
- Data preparation workflow dashboard.
- Paper trading workflow dashboard.
- Unified local research dashboard.
- Unified local research workflow E2E smoke test.

## Main Local Workflow

The main local workflow now has a complete command path:

```text
data-pipeline
-> snapshot-quality
-> current-candidates
-> current-candidates-index
-> current-candidates-health
-> current-to-paper
-> current-to-paper-review
-> paper-review-decisions --health-check
-> paper-daily --reviewed-decisions
-> paper-reconcile-fills
-> research-status
```

The full E2E smoke test also exercises paper artifact index/health, data preparation index/health, `data-prep-status`, and `paper-workflow-status` so the dashboard chain can see the expected status artifacts.

## Example Commands

These examples use Windows CMD syntax and local/mock paths. Replace placeholder folders such as `<pipeline_id>`, `<run_folder>`, `<handoff_id>`, and `<review_id>` with the artifact IDs from your local run.

Activate the environment:

```cmd
cd /d "G:\AICODING\Quantitative Trading\quant-replay-system"
.venv\Scripts\activate.bat
```

Run the test suite:

```cmd
python -m pytest
```

Run the local data pipeline with the mock manifest:

```cmd
python -m quant_replay_system.cli data-pipeline --manifest data\mock\data_pipeline_manifest.json
```

Run snapshot quality on the generated snapshot manifest:

```cmd
python -m quant_replay_system.cli snapshot-quality --manifest outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json
```

Generate current candidates from the snapshot manifest:

```cmd
python -m quant_replay_system.cli current-candidates --date 2024-01-08 --universe etf_core --top 5 --snapshot-manifest outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json
```

Index and health-check current candidate artifacts:

```cmd
python -m quant_replay_system.cli current-candidates-index --root outputs\reports\current_candidates
python -m quant_replay_system.cli current-candidates-health --index outputs\reports\current_candidates\index\current_candidate_artifact_index.csv
```

Hand current candidates to the paper workflow:

```cmd
python -m quant_replay_system.cli current-to-paper --index outputs\reports\current_candidates\index\current_candidate_artifact_index.csv --decision-date 2024-01-08 --universe etf_core
```

Create a manual review update template:

```cmd
python -m quant_replay_system.cli current-to-paper-review --handoff-dir outputs\reports\current_to_paper_handoff\<handoff_id> --reviewer-id msj
```

Manually edit the generated `review_updates_template.csv`, then apply review decisions with the template health preflight:

```cmd
python -m quant_replay_system.cli paper-review-decisions --decisions outputs\reports\paper_trading\daily\<daily_journal_id>\decisions.csv --updates outputs\reports\current_to_paper_review_handoff\<review_handoff_id>\review_updates_template.csv --health-check --reviewer-id msj
```

Run daily paper reporting with reviewed decisions:

```cmd
python -m quant_replay_system.cli paper-daily --date 2024-01-08 --reviewed-decisions outputs\reports\paper_trading\reviews\<review_id>\reviewed_decisions.csv --fills data\paper\fills.csv
```

Reconcile manual paper fills:

```cmd
python -m quant_replay_system.cli paper-reconcile-fills --decisions outputs\reports\paper_trading\reviews\<review_id>\reviewed_decisions.csv --fills data\paper\fills.csv
```

Build supporting artifact indexes and health reports:

```cmd
python -m quant_replay_system.cli paper-index --root outputs\reports\paper_trading
python -m quant_replay_system.cli paper-health-check --index outputs\reports\paper_trading\index\paper_artifact_index.csv
python -m quant_replay_system.cli data-prep-index --root outputs\reports
python -m quant_replay_system.cli data-prep-health --index outputs\reports\data_preparation\index\data_preparation_artifact_index.csv
```

Write the workflow dashboards:

```cmd
python -m quant_replay_system.cli data-prep-status --root outputs\reports --decision-date 2024-01-08 --universe etf_core
python -m quant_replay_system.cli paper-workflow-status --root outputs\reports --decision-date 2024-01-08 --universe etf_core
python -m quant_replay_system.cli research-status --root outputs\reports --decision-date 2024-01-08 --universe etf_core
```

## Safety Guarantees

The v0.39.0 checkpoint keeps the project inside the local research boundary:

- No live trading.
- No broker API.
- No order automation.
- No GitHub Actions CI recreated.
- No secrets printed or stored.
- No real network/API calls in automated tests.
- Local/mock data only unless a future task explicitly enables a guarded real-data workflow.

## Known Limitations

- No real data adapter is fully enabled yet.
- `AKSHARE_OPTIONAL` is guarded/placeholder unless explicitly implemented later.
- No true current market auto-refresh exists yet.
- No LLM, news, or event extraction exists yet.
- No live trading is implemented.
- No broker integration is implemented.
- No interactive review UI exists yet.
- The full test suite is getting close to 60 seconds.
- Mock data is tiny and validates workflow wiring, not strategy quality.

## Recommended Next Steps

1. Add test suite tiering or slow test markers if full test runtime exceeds 60 seconds.
2. Implement Real Data Adapter v0.1, likely an AKShare optional adapter with strict no-network tests and manual `--allow-real-data` guardrails.
3. Exercise a local real-data CSV workflow: `data-source-fetch -> data-pipeline -> data-quality -> snapshot-quality -> current-candidates`.
4. Later, add a Tushare optional adapter if a token is available and the same guardrails are preserved.
5. Later, add LLM event/news extraction, still disabled by default and kept out of automated tests that require network calls.

## Git Tag

Recommended milestone tag:

```text
v0.39.0 = Unified Local Research Workflow E2E Smoke Test v0.1
```

Before tagging, run validation and inspect the working tree:

```cmd
python -m pytest
git status --short
```

Create the tag only after ChatGPT or the user confirms the checkpoint:

```cmd
git tag -a v0.39.0 -m "Unified Local Research Workflow E2E Smoke Test v0.1"
git push origin v0.39.0
```
