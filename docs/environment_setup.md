# Development Environment Setup

This project supports Python 3.10+ and uses local CSV/mock data for MVP research.

The commands below use Windows CMD, not PowerShell.

## Enter the Project Directory

```bat
cd /d "G:\AICODING\Quantitative Trading\quant-replay-system"
```

## Create a Virtual Environment

```bat
python -m venv .venv
```

## Activate the Virtual Environment with CMD

```bat
.venv\Scripts\activate.bat
```

After activation, your prompt should show `(.venv)`.

## Upgrade pip

```bat
python -m pip install --upgrade pip
```

## Install the Project

```bat
pip install -e .
```

## Install Dev Dependencies

For local testing, install the dev extras:

```bat
pip install -e ".[dev]"
```

## Configure Local Environment Variables

Copy the example file and edit local values as needed:

```bat
copy .env.example .env
```

Keep these disabled for this research MVP:

```text
ENABLE_LIVE_TRADING=false
ENABLE_BROKER_API=false
```

## Run Tests

```bat
python -m pytest
```

## Run a Sample Replay Command

```bat
python -c "from pathlib import Path; from quant_replay_system.config import load_settings; from quant_replay_system.calendar import load_trading_calendar; from quant_replay_system.data import load_corporate_actions, load_market_data, load_universe_snapshot; from quant_replay_system.replay import replay_decision_date; settings = load_settings(Path('config/default.yaml')); market = load_market_data(settings.data.mock_prices); universe = load_universe_snapshot(settings.data.mock_universe_snapshots); actions = load_corporate_actions(settings.data.mock_corporate_actions); calendar = load_trading_calendar(settings.data.mock_trading_calendar); result = replay_decision_date('2024-01-03', market, settings, universe, actions, calendar); print(result.candidates); print(result.executions[['symbol', 'trade_status', 'buy_reason', 'sell_reason']])"
```

## Never Commit

Do not commit local secrets, credentials, raw vendor data, generated outputs, or machine-specific editor files.

Ignored examples:

- `.env` and `.env.*`
- `secrets/`
- `*.pem` and `*.key`
- `.venv/`, `venv/`, and `env/`
- `__pycache__/`, `*.pyc`, `.pytest_cache/`, and `.benchmarks/`
- `data/raw/`, `data/processed/`, and `data/snapshots/`
- `outputs/` and `reports/`
- `.vscode/`, `.idea/`, `.DS_Store`, and `Thumbs.db`
