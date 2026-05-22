# Testing Strategy v0.1

This document defines the local test tiers for `quant-replay-system`.

The goal is to keep day-to-day validation fast while preserving full coverage before commits, checkpoints, and tags.

## Test Markers

Pytest markers are configured in `pyproject.toml`:

- `unit`: fast isolated tests with narrow module scope.
- `integration`: multi-module tests or artifact/report workflow checks.
- `e2e`: end-to-end workflow smoke tests.
- `slow`: tests that write many artifacts, run long workflows, or are expected to be slower.

Current E2E smoke tests are marked with both `e2e` and `slow`. Artifact-heavy index and health tests are marked with both `integration` and `slow`.

Not every fast test is explicitly marked `unit` yet. Unmarked tests are still part of the default full suite and the quick `not slow` suite.

## What Belongs In Slow

Use `slow` for tests that are valuable before checkpoints but too heavy for every quick development pass:

- full E2E workflow smoke tests,
- artifact index and health suites that scan or write many local files,
- repeated deterministic workflow checks,
- calibration or walk-forward tests that run multiple replay-like workflows,
- batch replay artifact export checks,
- tests whose main purpose is validating report/CSV/JSON artifact wiring.

Keep lightweight correctness tests out of `slow`, especially tests for:

- pure scoring or ranking formulas,
- small validation helpers,
- point-in-time contract behavior,
- no-live-trading and no-broker safety metadata,
- narrow regression checks that run quickly.

## Recommended Commands

Run the full backend suite before commits, checkpoints, and tags:

```cmd
python -m pytest
```

Run the quick development suite by excluding slow tests:

```cmd
python -m pytest -m "not slow"
```

Run only end-to-end smoke tests:

```cmd
python -m pytest -m "e2e"
```

Run the slow tier explicitly:

```cmd
python -m pytest -m "slow"
```

Profile slow tests when runtime grows:

```cmd
python -m pytest --durations=30
```

Run a focused file while developing a narrow change:

```cmd
python -m pytest tests\test_data_pipeline.py
```

Run integration-marked artifact checks, including slow artifact suites:

```cmd
python -m pytest -m "integration"
```

## When Codex Should Run Which Tests

For narrow implementation work, Codex should run the relevant focused tests first, then run the full suite before reporting completion unless the user explicitly scopes validation differently.

For documentation-only work, Codex should still run the requested validation command from the task prompt. In this project, that is usually:

```cmd
python -m pytest
```

For E2E, workflow, or artifact-heavy changes, Codex should include:

```cmd
python -m pytest -m "e2e"
```

For checkpoint or tag candidates, Codex or the user should always run:

```cmd
python -m pytest
```

For iterative work where the changed area is not artifact-heavy, `not slow` is the preferred broad smoke pass:

```cmd
python -m pytest -m "not slow"
```

If the full suite exceeds 60 seconds, also run:

```cmd
python -m pytest --durations=30
```

and include the slowest tests in the task summary.

## Checkpoint Rule

`python -m pytest -m "not slow"` is a useful development shortcut, but it is not enough for a checkpoint or tag.

Before committing a stable module or creating a tag:

1. Run `python -m pytest`.
2. Check `git status --short`.
3. Verify no cache, `.env`, secrets, raw vendor data, or generated local outputs are tracked.
4. Review any slow-test output if the suite is over the runtime threshold.

## Local-Only Guarantee

The test suite uses local/mock CSV data. Automated tests must not:

- connect to brokers,
- place orders,
- automate order placement,
- print secrets,
- require real API tokens,
- call real network APIs.

Real data adapters, if added later, should remain guarded and excluded from automated network-dependent tests by default.

## Known MVP Limitations

- The `unit` marker exists for future refinement but is not exhaustively applied to every fast test.
- `not slow` is a speed tier, not a correctness guarantee.
- E2E tests use tiny mock data and validate workflow wiring, not strategy quality.
- Runtime thresholds are advisory; full validation remains required before checkpoints.
