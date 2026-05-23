# quant-replay-system

A point-in-time historical replay quant research system for China A-share ETFs and stocks.

The first goal is to build an explainable scoring workflow, replay historical decision dates using only data available at that time, select candidates, simulate T+1 execution, evaluate forward performance, and later calibrate weights, thresholds, and risk rules.

This project is research infrastructure. It is not an automatic trading bot, high-frequency system, broker auto-order system, insider-information system, or profit guarantee.

## MVP v0.1

Included now:

- Python 3.10+ project skeleton.
- Local YAML configuration.
- Local CSV mock data.
- Local CSV ingestion and processed snapshot builder.
- Data quality summary reports for processed replay inputs.
- Snapshot quality gate for full processed snapshot manifests.
- Optional snapshot quality preflight for replay-like workflows.
- Data preparation artifact index and health check for pipeline, quality, snapshot, and current-candidate outputs.
- Data preparation workflow status dashboard for the latest local data-prep stage and next manual action.
- Current/as-of-date candidate generation from local snapshots for paper-trading review.
- Current candidate artifact index and health check for local candidate run navigation.
- Current-candidate to paper-trading handoff helper for healthy local candidate artifacts.
- Current-candidate to paper-review handoff helper for manual review update templates.
- Placeholder modules for data, scoring, replay, execution, evaluation, calibration, and risk.
- Point-in-time data contract for market data, universe snapshots, and corporate actions.
- Trading calendar and T+1 execution calendar for daily replay.
- Point-in-time-safe technical indicators for timing research.
- Point-in-time factor dataset builder for research features.
- Explainable score engine and candidate selector for ranked research candidates.
- Replay run orchestrator for end-to-end auditable single-date replays.
- Hardened replay report artifacts with markdown, CSV exports, and metadata JSON.
- Batch replay orchestration for multi-date replay runs and aggregate reports.
- Parameter calibration over explicit small grids using batch replay outputs.
- Portfolio simulation with cash, trade, position, and equity ledgers.
- Portfolio-aware batch replay and calibration using account-level metrics.
- Walk-forward validation for train/validation/test parameter checks.
- Manual paper trading journal for reviewed candidates and hypothetical fills.
- Paper trading review workflow for local approve/reject/watch audit decisions.
- Paper trading review template health check before applying edited review updates.
- Daily paper trading runner for local decision logs, fills, and paper reports.
- Paper trading CLI for daily reports, fills validation, and fills templates.
- Paper trading fill reconciliation for decision/fill audit checks before daily reports.
- Paper trading artifact index for local report and CSV navigation.
- Paper trading artifact health check for stale or unreadable local files.
- Paper trading workflow status dashboard for latest stage and next manual action.
- Unified local research workflow dashboard from data preparation through paper trading.
- Baseline pytest setup.

Not included:

- Live broker trading.
- Real market data ingestion.
- Production strategy logic.
- Auto-order placement.

## Quick Start

```powershell
cd "G:\AICODING\Quantitative Trading\quant-replay-system"
python -m pip install -e ".[dev]"
python -m pytest
```

## Development Setup

For a clean Windows CMD setup with a virtual environment, `.env` file, test command, and sample replay command, see [docs/environment_setup.md](docs/environment_setup.md).

For quick, full, E2E, and duration-profiled test commands, see [docs/testing_strategy.md](docs/testing_strategy.md).

For the standard reusable Codex prompt structure for future tasks, see [docs/CODEX_PROMPT_STANDARD.md](docs/CODEX_PROMPT_STANDARD.md).

For local CSV ingestion, validation, and processed snapshot manifests, see [docs/data_ingestion.md](docs/data_ingestion.md).

For processed data quality summaries before replay, see [docs/data_quality.md](docs/data_quality.md).

For full-snapshot PASS/WARN/FAIL quality gates before replay, see [docs/snapshot_quality_gate.md](docs/snapshot_quality_gate.md).

For optional snapshot quality preflight checks inside replay, batch, calibration, and walk-forward flows, see [docs/snapshot_quality_preflight.md](docs/snapshot_quality_preflight.md).

For CLI flags that enable snapshot preflight on replay-like workflows, see [docs/snapshot_quality_preflight_cli.md](docs/snapshot_quality_preflight_cli.md).

For current/as-of-date candidate generation from local snapshots, see [docs/current_candidate_generation.md](docs/current_candidate_generation.md).

`current-candidates --selection-profile demo` is available for tiny local artifact/workflow validation only. The default selection profile and research thresholds remain unchanged, and demo candidates are marked as not strategy recommendations.

For indexing generated current-candidate runs, see [docs/current_candidate_artifact_index.md](docs/current_candidate_artifact_index.md).

For checking generated current-candidate artifact health, see [docs/current_candidate_artifact_health.md](docs/current_candidate_artifact_health.md).

For handing a healthy current-candidate `candidates.csv` into daily paper trading, see [docs/current_to_paper_handoff.md](docs/current_to_paper_handoff.md).

For creating manual review update templates from paper decisions, see [docs/current_to_paper_review_handoff.md](docs/current_to_paper_review_handoff.md).

For validating edited paper review templates before applying them, see [docs/paper_review_template_health.md](docs/paper_review_template_health.md).

For multi-date replay runs and batch-level artifacts, see [docs/batch_replay.md](docs/batch_replay.md).

For explainable parameter comparison using batch replay outputs, see [docs/parameter_calibration.md](docs/parameter_calibration.md).

For account-level portfolio ledgers and equity-curve simulation, see [docs/portfolio_simulation.md](docs/portfolio_simulation.md).

For portfolio-aware batch replay and calibration ranking, see [docs/portfolio_aware_calibration.md](docs/portfolio_aware_calibration.md).

For train/validation/test calibration checks and overfitting diagnostics, see [docs/walk_forward_validation.md](docs/walk_forward_validation.md).

For reviewed candidate decision logs and manual hypothetical paper fills, see [docs/manual_paper_trading.md](docs/manual_paper_trading.md).

For manual approve/reject/watch review updates before fills, see [docs/paper_trading_review_workflow.md](docs/paper_trading_review_workflow.md).

For daily local paper-trading reports from candidate CSVs and manual fills, see [docs/daily_paper_trading_runner.md](docs/daily_paper_trading_runner.md).

For local paper-trading CLI commands, see [docs/paper_trading_cli.md](docs/paper_trading_cli.md).

For paper decision/fill reconciliation, see [docs/paper_fill_reconciliation.md](docs/paper_fill_reconciliation.md).

For the full local paper trading workflow smoke-test example, see [docs/paper_trading_e2e_workflow.md](docs/paper_trading_e2e_workflow.md).

For a consolidated local index of daily, review, and reconciliation artifacts, see [docs/paper_trading_artifact_index.md](docs/paper_trading_artifact_index.md).

For checking indexed artifact paths and metadata health, see [docs/paper_trading_artifact_health_check.md](docs/paper_trading_artifact_health_check.md).

For a one-page local workflow status dashboard and next manual action, see [docs/paper_trading_workflow_status.md](docs/paper_trading_workflow_status.md).

For local-safe raw data source adapters before ingestion, see [docs/data_sources.md](docs/data_sources.md).

For the project data-source roadmap across AKShare upstream routes, BaoStock, Tushare, professional vendors, and permanent `LOCAL_CSV` fallback, see [docs/data_source_strategy.md](docs/data_source_strategy.md).

For checking local source and upstream route availability before import, see [docs/data_source_health.md](docs/data_source_health.md).

For caching successful canonical daily market bars and querying them into local pipeline inputs, see [docs/market_data_cache.md](docs/market_data_cache.md).

`AKSHARE_OPTIONAL` is available for guarded manual local market, benchmark, trading-calendar, and universe snapshot fetches; it requires `--allow-real-data`, is never called by automated tests, tries non-Eastmoney Sina/Tencent market routes before Eastmoney where supported, includes stock/ETF/index routing diagnostics plus a manual-only `curl_cffi` Eastmoney kline fallback, and should be followed by `data-pipeline`, `data-quality`, and `snapshot-quality`.

`BAOSTOCK_OPTIONAL` is available as a guarded manual market-only historical data backup; it requires `--allow-real-data`, imports BaoStock lazily, is never called by automated tests, writes canonical daily market bars, and can be followed by `market-cache-ingest`, `data-pipeline`, `data-quality`, and `snapshot-quality`.

`TUSHARE_OPTIONAL` is available as a second guarded manual source for market, benchmark, trading-calendar, and universe snapshot fetches; it requires `--allow-real-data` and a local `TUSHARE_TOKEN`, never writes the token to metadata, is never called by automated tests, and should also be followed by `data-pipeline`, `data-quality`, and `snapshot-quality`.

For the guarded Windows CMD workflow from manual AKShare fetch to current candidates, see [docs/akshare_manual_workflow.md](docs/akshare_manual_workflow.md).

For the AKShare universe + market real-data dry-run checklist, see [docs/akshare_real_data_dry_run.md](docs/akshare_real_data_dry_run.md).

For using a manually reviewed market CSV when AKShare market history is unstable, see [docs/local_csv_market_fallback_workflow.md](docs/local_csv_market_fallback_workflow.md).

For merging reviewed ETF rows into a stock-only universe snapshot before `data-pipeline`, see [docs/universe_overlay.md](docs/universe_overlay.md).

For the local data source to ingestion and quality handoff pipeline, see [docs/data_pipeline.md](docs/data_pipeline.md).

For the end-to-end local data preparation smoke-test workflow, see [docs/data_preparation_e2e.md](docs/data_preparation_e2e.md).

For indexing local data preparation artifacts, see [docs/data_preparation_artifact_index.md](docs/data_preparation_artifact_index.md).

For checking indexed data preparation artifact health, see [docs/data_preparation_artifact_health.md](docs/data_preparation_artifact_health.md).

For the local data preparation workflow status dashboard, see [docs/data_preparation_workflow_status.md](docs/data_preparation_workflow_status.md).

For the unified local research workflow dashboard, see [docs/local_research_dashboard.md](docs/local_research_dashboard.md).

For the end-to-end local research workflow smoke-test path, see [docs/local_research_workflow_e2e.md](docs/local_research_workflow_e2e.md).

For the v0.39.0 local research workflow checkpoint summary, see [docs/release_checkpoint_v0.39.0.md](docs/release_checkpoint_v0.39.0.md).

For Codex local CLI verification and artifact diagnostics delegation rules, see [docs/PROCESS.md#codex-local-cli-verification-and-artifact-diagnostics](docs/PROCESS.md#codex-local-cli-verification-and-artifact-diagnostics).

Recommended next data-source engineering sequence:

1. BaoStock local dry-run coverage expansion and AKShare/BaoStock cache comparison.
2. Tushare permissioned dry-run if cost and account permissions are acceptable.
3. Professional data adapter evaluation for JQData/RQData if local workflow needs stronger coverage.

```powershell
python -m quant_replay_system.cli data-source-fetch --source LOCAL_CSV --dataset-type market --input data/mock/prices.csv
python -m quant_replay_system.cli data-source-health --source AKSHARE_OPTIONAL --dataset-type market --symbol 510300 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
python -m quant_replay_system.cli data-source-health --source BAOSTOCK_OPTIONAL --dataset-type market --symbol 000001 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
python -m quant_replay_system.cli data-source-fetch --source BAOSTOCK_OPTIONAL --dataset-type market --symbol 000001 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
python -m quant_replay_system.cli market-cache-ingest --input data/raw/AKSHARE_OPTIONAL/market/<run_id>/raw_data.csv --metadata data/raw/AKSHARE_OPTIONAL/market/<run_id>/metadata.json
python -m quant_replay_system.cli market-cache-query --symbol 510300 --start-date 2024-01-01 --end-date 2024-05-20 --output data/raw/manual_cache/510300_market.csv
python -m quant_replay_system.cli universe-overlay --base-universe data/raw/AKSHARE_OPTIONAL/universe/<run_id>/raw_data.csv --overlay data/raw/manual_overlays/etf_universe_overlay.csv
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data/mock/prices.csv
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --candidates outputs/reports/replay_runs/example/candidates.csv
python -m quant_replay_system.cli paper-review-decisions --decisions outputs/reports/paper_trading/daily/example/decisions.csv --updates data/paper/review_updates.csv --health-check --reviewer-id msj
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --reviewed-decisions outputs/reports/paper_trading/reviews/example/reviewed_decisions.csv --fills data/paper/fills.csv
python -m quant_replay_system.cli paper-reconcile-fills --decisions outputs/reports/paper_trading/daily/example/decisions.csv --fills data/paper/fills.csv
python -m quant_replay_system.cli paper-index --root outputs/reports/paper_trading
python -m quant_replay_system.cli paper-health-check --index outputs/reports/paper_trading/index/paper_artifact_index.csv
python -m quant_replay_system.cli paper-workflow-status --root outputs/reports
python -m quant_replay_system.cli ingest-market --input data/raw/market.csv --output-dir data/processed/market
python -m quant_replay_system.cli data-quality --dataset-type market --input data/processed/market/market_cleaned.csv
python -m quant_replay_system.cli snapshot-quality --manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --top 5 --snapshot-manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --top 5 --snapshot-manifest data/snapshots/example_snapshot_manifest.json --selection-profile demo
python -m quant_replay_system.cli current-candidates-index --root outputs/reports/current_candidates
python -m quant_replay_system.cli current-candidates-health --index outputs/reports/current_candidates/index/current_candidate_artifact_index.csv
python -m quant_replay_system.cli current-to-paper --index outputs/reports/current_candidates/index/current_candidate_artifact_index.csv --decision-date 2024-05-20
python -m quant_replay_system.cli current-to-paper-review --handoff-dir outputs/reports/current_to_paper_handoff/example
python -m quant_replay_system.cli paper-review-template-health --updates outputs/reports/current_to_paper_review_handoff/example/review_updates_template.csv --decisions outputs/reports/paper_trading/daily/example/decisions.csv
python -m quant_replay_system.cli data-prep-index --root outputs/reports
python -m quant_replay_system.cli data-prep-health --index outputs/reports/data_preparation/index/data_preparation_artifact_index.csv
python -m quant_replay_system.cli data-prep-status --root outputs/reports
python -m quant_replay_system.cli research-status --root outputs/reports
python -m quant_replay_system.cli replay-run --date 2024-01-03 --horizon 2 --snapshot-manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli batch-replay --dates 2024-01-03,2024-01-04 --horizon 2 --snapshot-manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli paper-validate-fills --fills data/paper/fills.csv
python -m quant_replay_system.cli paper-template-fills --output data/paper/fills_template.csv
```

## Current Candidate To Paper Workflow

```powershell
python -m quant_replay_system.cli data-source-fetch --source LOCAL_CSV --dataset-type market --input data/raw/market.csv
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data/raw/market.csv
python -m quant_replay_system.cli ingest-market --input data/raw/market.csv --output-dir data/processed/market
python -m quant_replay_system.cli snapshot-quality --manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --top 5 --snapshot-manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli current-candidates-index --root outputs/reports/current_candidates
python -m quant_replay_system.cli current-candidates-health --index outputs/reports/current_candidates/index/current_candidate_artifact_index.csv
python -m quant_replay_system.cli current-to-paper --index outputs/reports/current_candidates/index/current_candidate_artifact_index.csv --decision-date 2024-05-20 --universe etf_core
python -m quant_replay_system.cli current-to-paper-review --handoff-dir outputs/reports/current_to_paper_handoff/example --reviewer-id msj
# Manually edit outputs\reports\current_to_paper_review_handoff\example\review_updates_template.csv
python -m quant_replay_system.cli paper-review-template-health --updates outputs/reports/current_to_paper_review_handoff/example/review_updates_template.csv --decisions outputs/reports/paper_trading/daily/example/decisions.csv
python -m quant_replay_system.cli paper-review-decisions --decisions outputs/reports/paper_trading/daily/example/decisions.csv --updates outputs/reports/current_to_paper_review_handoff/example/review_updates_template.csv --health-check --reviewer-id msj
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --reviewed-decisions outputs/reports/paper_trading/reviews/example/reviewed_decisions.csv --fills data/paper/fills.csv
python -m quant_replay_system.cli paper-reconcile-fills --decisions outputs/reports/paper_trading/daily/example/decisions.csv --fills data/paper/fills.csv
python -m quant_replay_system.cli paper-workflow-status --root outputs/reports --decision-date 2024-05-20 --universe etf_core
python -m quant_replay_system.cli research-status --root outputs/reports --decision-date 2024-05-20 --universe etf_core
```

## Local Data Source Workflow

```powershell
python -m quant_replay_system.cli data-source-fetch --source LOCAL_CSV --dataset-type market --input data/mock/prices.csv
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data/mock/prices.csv
python -m quant_replay_system.cli data-quality --dataset-type market --input data/processed/market/<pipeline_id>/raw_data_cleaned.csv
python -m quant_replay_system.cli snapshot-quality --manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --snapshot-manifest data/snapshots/example_snapshot_manifest.json
```

## Local Data Preparation E2E Workflow

```powershell
python -m quant_replay_system.cli data-pipeline --manifest data/mock/data_pipeline_manifest.json
python -m quant_replay_system.cli data-prep-status --root outputs/reports
python -m quant_replay_system.cli snapshot-quality --manifest outputs/reports/data_pipeline/<pipeline_id>/snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-01-08 --universe etf_core --top 5 --snapshot-manifest outputs/reports/data_pipeline/<pipeline_id>/snapshot_manifest.json
python -m quant_replay_system.cli data-prep-index --root outputs/reports
python -m quant_replay_system.cli data-prep-health --index outputs/reports/data_preparation/index/data_preparation_artifact_index.csv
python -m quant_replay_system.cli data-prep-status --root outputs/reports --decision-date 2024-01-08 --universe etf_core
python -m quant_replay_system.cli current-to-paper --candidates outputs/reports/current_candidates/<run_folder>/candidates.csv --paper-date 2024-01-08
# Continue with the manual paper workflow: current-to-paper-review, paper-review-decisions, paper-daily, and paper-reconcile-fills.
```

## Data Preparation Status Workflow

```powershell
python -m quant_replay_system.cli data-pipeline --manifest data/mock/data_pipeline_manifest.json
python -m quant_replay_system.cli data-prep-status --root outputs/reports
python -m quant_replay_system.cli snapshot-quality --manifest outputs/reports/data_pipeline/<pipeline_id>/snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-01-08 --universe etf_core --snapshot-manifest outputs/reports/data_pipeline/<pipeline_id>/snapshot_manifest.json
python -m quant_replay_system.cli current-to-paper --candidates outputs/reports/current_candidates/<run_folder>/candidates.csv --paper-date 2024-01-08
```

## Unified Local Research Workflow

```powershell
python -m quant_replay_system.cli data-pipeline --manifest data/mock/data_pipeline_manifest.json
python -m quant_replay_system.cli data-prep-status --root outputs/reports
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --snapshot-manifest outputs/reports/data_pipeline/<pipeline_id>/snapshot_manifest.json
python -m quant_replay_system.cli current-to-paper --candidates outputs/reports/current_candidates/<run_folder>/candidates.csv --paper-date 2024-05-20
python -m quant_replay_system.cli current-to-paper-review --handoff-dir outputs/reports/current_to_paper_handoff/example
# Manually edit review_updates_template.csv.
python -m quant_replay_system.cli paper-review-decisions --decisions outputs/reports/paper_trading/daily/example/decisions.csv --updates outputs/reports/current_to_paper_review_handoff/example/review_updates_template.csv --health-check
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --reviewed-decisions outputs/reports/paper_trading/reviews/example/reviewed_decisions.csv
python -m quant_replay_system.cli paper-reconcile-fills --decisions outputs/reports/paper_trading/daily/example/decisions.csv --fills data/paper/fills.csv
python -m quant_replay_system.cli research-status --root outputs/reports --decision-date 2024-05-20 --universe etf_core
```

The automated smoke-test version of this flow is documented in [docs/local_research_workflow_e2e.md](docs/local_research_workflow_e2e.md) and covered by `tests/test_local_research_workflow_e2e.py`.

## Local Research Workflow Checkpoint

`v0.39.0` marks the first complete local-only research workflow checkpoint, covering local data preparation, snapshot quality, current candidates, paper review, paper reporting, fill reconciliation, and the unified `research-status` dashboard.

See [docs/release_checkpoint_v0.39.0.md](docs/release_checkpoint_v0.39.0.md) for the milestone summary, local command sequence, safety guarantees, known limitations, and recommended tag.

## Project Layout

```text
quant-replay-system/
  config/
    default.yaml
    universe.yaml
  data/
    mock/
      corporate_actions.csv
      data_pipeline_manifest.json
      prices.csv
      trading_calendar.csv
      universe_snapshots.csv
  docs/
    CODEX_PROMPT_STANDARD.md
    akshare_manual_workflow.md
    akshare_real_data_dry_run.md
    batch_replay.md
    current_candidate_artifact_health.md
    current_candidate_artifact_index.md
    current_candidate_generation.md
    current_to_paper_handoff.md
    current_to_paper_review_handoff.md
    data_contract.md
    data_ingestion.md
    data_pipeline.md
    data_preparation_artifact_health.md
    data_preparation_artifact_index.md
    data_preparation_e2e.md
    data_preparation_workflow_status.md
    data_quality.md
    data_sources.md
    daily_paper_trading_runner.md
    execution_calendar.md
    factor_dataset.md
    manual_paper_trading.md
    parameter_calibration.md
    paper_fill_reconciliation.md
    paper_review_template_health.md
    paper_trading_artifact_health_check.md
    paper_trading_artifact_index.md
    paper_trading_e2e_workflow.md
    paper_trading_workflow_status.md
    paper_trading_cli.md
    paper_trading_review_workflow.md
    portfolio_aware_calibration.md
    portfolio_simulation.md
    report_generation.md
    replay_run_orchestrator.md
    scoring_engine.md
    snapshot_quality_gate.md
    snapshot_quality_preflight.md
    snapshot_quality_preflight_cli.md
    technical_indicators.md
    testing_strategy.md
    walk_forward_validation.md
  src/
    quant_replay_system/
      calibration.py
      cli.py
      config.py
      current_candidate_artifact_health.py
      current_candidate_artifact_index.py
      current_candidates.py
      current_to_paper_handoff.py
      current_to_paper_review_handoff.py
      data.py
      data_ingestion.py
      data_pipeline.py
      data_preparation_artifact_health.py
      data_preparation_artifact_index.py
      data_preparation_workflow_status.py
      data_quality.py
      data_sources.py
      daily_paper_runner.py
      evaluation.py
      execution.py
      paper_artifact_health.py
      paper_artifact_index.py
      paper_reconciliation.py
      paper_review.py
      paper_trading.py
      replay.py
      risk.py
      scoring.py
      snapshot_quality_gate.py
      snapshot_quality_preflight.py
      walk_forward.py
  tests/
```

## Design Principles

- Point-in-time safety first.
- Explainable scores before complex models.
- T+1 execution assumptions are explicit.
- Local files and mock data are the default for MVP.
- Paper trading and small manual live workflows can be added later, without broker automation.

## Example Baseline Flow

```python
from pathlib import Path

from quant_replay_system.config import load_settings
from quant_replay_system.calendar import load_trading_calendar
from quant_replay_system.data import load_corporate_actions, load_market_data, load_universe_snapshot
from quant_replay_system.replay import replay_decision_date

settings = load_settings(Path("config/default.yaml"))
prices = load_market_data(settings.data.mock_prices)
universe = load_universe_snapshot(settings.data.mock_universe_snapshots)
actions = load_corporate_actions(settings.data.mock_corporate_actions)
calendar = load_trading_calendar(settings.data.mock_trading_calendar)
result = replay_decision_date("2024-01-03", prices, settings, universe, actions, calendar)

print(result.candidates)
```
