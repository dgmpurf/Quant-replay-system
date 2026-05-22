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

For the standard reusable Codex prompt structure for future tasks, see [docs/CODEX_PROMPT_STANDARD.md](docs/CODEX_PROMPT_STANDARD.md).

For local CSV ingestion, validation, and processed snapshot manifests, see [docs/data_ingestion.md](docs/data_ingestion.md).

For processed data quality summaries before replay, see [docs/data_quality.md](docs/data_quality.md).

For full-snapshot PASS/WARN/FAIL quality gates before replay, see [docs/snapshot_quality_gate.md](docs/snapshot_quality_gate.md).

For optional snapshot quality preflight checks inside replay, batch, calibration, and walk-forward flows, see [docs/snapshot_quality_preflight.md](docs/snapshot_quality_preflight.md).

For CLI flags that enable snapshot preflight on replay-like workflows, see [docs/snapshot_quality_preflight_cli.md](docs/snapshot_quality_preflight_cli.md).

For current/as-of-date candidate generation from local snapshots, see [docs/current_candidate_generation.md](docs/current_candidate_generation.md).

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

```powershell
python -m quant_replay_system.cli data-source-fetch --source LOCAL_CSV --dataset-type market --input data/mock/prices.csv
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
python -m quant_replay_system.cli current-candidates-index --root outputs/reports/current_candidates
python -m quant_replay_system.cli current-candidates-health --index outputs/reports/current_candidates/index/current_candidate_artifact_index.csv
python -m quant_replay_system.cli current-to-paper --index outputs/reports/current_candidates/index/current_candidate_artifact_index.csv --decision-date 2024-05-20
python -m quant_replay_system.cli current-to-paper-review --handoff-dir outputs/reports/current_to_paper_handoff/example
python -m quant_replay_system.cli paper-review-template-health --updates outputs/reports/current_to_paper_review_handoff/example/review_updates_template.csv --decisions outputs/reports/paper_trading/daily/example/decisions.csv
python -m quant_replay_system.cli replay-run --date 2024-01-03 --horizon 2 --snapshot-manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli batch-replay --dates 2024-01-03,2024-01-04 --horizon 2 --snapshot-manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli paper-validate-fills --fills data/paper/fills.csv
python -m quant_replay_system.cli paper-template-fills --output data/paper/fills_template.csv
```

## Current Candidate To Paper Workflow

```powershell
python -m quant_replay_system.cli data-source-fetch --source LOCAL_CSV --dataset-type market --input data/raw/market.csv
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
```

## Local Data Source Workflow

```powershell
python -m quant_replay_system.cli data-source-fetch --source LOCAL_CSV --dataset-type market --input data/mock/prices.csv
python -m quant_replay_system.cli ingest-market --input data/raw/LOCAL_CSV/market/example/raw_data.csv --output-dir data/processed/market
python -m quant_replay_system.cli data-quality --dataset-type market --input data/processed/market/raw_data_cleaned.csv
python -m quant_replay_system.cli snapshot-quality --manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --snapshot-manifest data/snapshots/example_snapshot_manifest.json
```

## Project Layout

```text
quant-replay-system/
  config/
    default.yaml
    universe.yaml
  data/
    mock/
      corporate_actions.csv
      prices.csv
      trading_calendar.csv
      universe_snapshots.csv
  docs/
    CODEX_PROMPT_STANDARD.md
    batch_replay.md
    current_candidate_artifact_health.md
    current_candidate_artifact_index.md
    current_candidate_generation.md
    current_to_paper_handoff.md
    current_to_paper_review_handoff.md
    data_contract.md
    data_ingestion.md
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
