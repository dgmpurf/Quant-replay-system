# quant-replay-system

A point-in-time historical replay quant research system for China A-share ETFs and stocks.

The first goal is to build an explainable scoring workflow, replay historical decision dates using only data available at that time, select candidates, simulate T+1 execution, evaluate forward performance, and later calibrate weights, thresholds, and risk rules.

This project is research infrastructure. It is not an automatic trading bot, high-frequency system, broker auto-order system, insider-information system, or profit guarantee.

## MVP v0.1

Included now:

- Python 3.10+ project skeleton.
- Local YAML configuration.
- Local CSV mock data.
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
- Daily paper trading runner for local decision logs, fills, and paper reports.
- Paper trading CLI for daily reports, fills validation, and fills templates.
- Paper trading fill reconciliation for decision/fill audit checks before daily reports.
- Paper trading artifact index for local report and CSV navigation.
- Paper trading artifact health check for stale or unreadable local files.
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

```powershell
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --candidates outputs/reports/replay_runs/example/candidates.csv
python -m quant_replay_system.cli paper-review-decisions --decisions outputs/reports/paper_trading/daily/example/decisions.csv --updates data/paper/review_updates.csv --reviewer-id msj
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --reviewed-decisions outputs/reports/paper_trading/reviews/example/reviewed_decisions.csv --fills data/paper/fills.csv
python -m quant_replay_system.cli paper-reconcile-fills --decisions outputs/reports/paper_trading/daily/example/decisions.csv --fills data/paper/fills.csv
python -m quant_replay_system.cli paper-index --root outputs/reports/paper_trading
python -m quant_replay_system.cli paper-health-check --index outputs/reports/paper_trading/index/paper_artifact_index.csv
python -m quant_replay_system.cli paper-validate-fills --fills data/paper/fills.csv
python -m quant_replay_system.cli paper-template-fills --output data/paper/fills_template.csv
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
    batch_replay.md
    data_contract.md
    daily_paper_trading_runner.md
    execution_calendar.md
    factor_dataset.md
    manual_paper_trading.md
    parameter_calibration.md
    paper_fill_reconciliation.md
    paper_trading_artifact_health_check.md
    paper_trading_artifact_index.md
    paper_trading_e2e_workflow.md
    paper_trading_cli.md
    paper_trading_review_workflow.md
    portfolio_aware_calibration.md
    portfolio_simulation.md
    report_generation.md
    replay_run_orchestrator.md
    scoring_engine.md
    technical_indicators.md
    walk_forward_validation.md
  src/
    quant_replay_system/
      calibration.py
      cli.py
      config.py
      data.py
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
