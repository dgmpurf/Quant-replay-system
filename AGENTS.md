# AGENTS.md

## Project Mission

`quant-replay-system` is a point-in-time historical replay research system for China A-share ETFs and stocks. It is designed to help build, replay, explain, and calibrate research decisions using only data that would have been available on each historical decision date.

## Non-Goals

- Do not implement live broker trading.
- Do not add automatic order submission.
- Do not use insider, non-public, or future-leaking data.
- Do not present outputs as guaranteed profit.
- Do not optimize for high-frequency trading or intraday execution.

## Engineering Rules

- Python 3.10+ only.
- Prefer simple, auditable modules over clever abstractions.
- Keep all replay logic point-in-time: a decision date must not read data from the future.
- Use local CSV/mock data until a data ingestion layer is explicitly added.
- Keep scoring explainable: every candidate score should be decomposable into named components.
- Model China A-share execution assumptions explicitly, including T+1 execution and practical risk constraints.
- Keep tests small and focused for MVP changes.

## Common Commands

```powershell
python -m pytest
python -m pip install -e ".[dev]"
```

## Current MVP Scope

- Project structure and configuration.
- Placeholder domain modules.
- Mock local data.
- Baseline pytest suite.
- No broker integration.
