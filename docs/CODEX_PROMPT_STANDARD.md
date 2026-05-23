# Codex Prompt Standard

This document defines the standard reusable prompt structure for future Codex development tasks in `quant-replay-system`.

It is a project-specific guide for writing scoped tasks that Codex can execute safely, testably, and consistently.

## Purpose

`quant-replay-system` is developed iteratively with Codex and ChatGPT guidance. Each task should be clear enough that Codex can read the relevant files, make a narrow change, run validation, and report the result without relying on hidden or stale chat context.

Use this document when drafting future Codex prompts for:

- feature implementation,
- documentation-only work,
- hardening and bug fixes,
- module integration,
- CLI commands,
- artifact and report generation,
- data ingestion and quality checks,
- manual paper trading workflows.

## Core Principles

- Do not assume previous chat context.
- Every Codex task must be scoped.
- Every task must preserve point-in-time safety unless explicitly modifying it.
- Every task must preserve T+1 execution logic unless explicitly modifying it.
- Every task must be testable.
- Every task must report validation results.
- Every task must avoid live trading, broker integration, automated orders, and GitHub Actions unless explicitly requested.
- Every task must avoid secrets, `.env` changes, token printing, and real network/API calls in tests.
- Every task should use mock or local CSV data unless the prompt explicitly says otherwise.
- Every task should record known limitations and the next recommended task.
- When a task explicitly asks for local CLI verification, Codex should perform safe local dry-runs itself when required inputs exist or can be created under ignored local paths. It should inspect generated artifacts, report paths and row counts, and run git safety checks instead of leaving those local verification steps to the user.

## Standard Codex Prompt Template

Copy, paste, and fill in this template for most tasks.

```text
Next task: <short task name>.

Context:
The project quant-replay-system already has:
- <relevant completed module>
- <relevant completed module>
- Tests currently pass: <N> passed

Read first:
- AGENTS.md
- README.md
- docs/PROCESS.md
- docs/CODEX_PROMPT_STANDARD.md
- config/default.yaml
- <relevant docs under docs/>
- <relevant source files under src/quant_replay_system/>
- <relevant tests under tests/>

Do not assume previous chat context.

Important:
Do NOT implement live trading.
Do NOT add broker integration.
Do NOT automate order placement.
Do NOT add GitHub Actions or CI unless explicitly requested.
Do NOT modify .env.
Do NOT print API keys, tokens, account values, or secrets.
Do NOT use real network/API calls in automated tests.
Do NOT change point-in-time filtering rules unless this task explicitly requires it.
Do NOT change trading calendar or T+1 execution logic unless this task explicitly requires it.
Do NOT change scoring formulas unless this task explicitly requires it.
Use mock/local CSV data only unless this task explicitly says otherwise.

Goal:
<one paragraph explaining the desired result>

Reason:
<why this task matters and what risk or workflow it improves>

Tasks:
1. <concrete implementation step>
2. <concrete implementation step>
3. <concrete implementation step>

Tests:
Add or update tests for:
1. <expected behavior>
2. <edge case>
3. <determinism or safety requirement>
4. no live trading or broker integration is invoked
5. no real network/API calls are used in tests

Documentation:
- Create or update <doc path>.
- Update README.md with a short link if this adds a new user-facing module.
- Keep known MVP limitations explicit.

Validation:
Run:
python -m pytest

Final response requirements:
- Files changed
- Functions/classes implemented
- Tests added/updated
- Documentation updated
- Validation
- Known limitations
- Confirm no live trading or broker integration was added
- Confirm no GitHub Actions workflow was created
- Confirm no secrets were printed or stored
- Confirm no real network/API calls were used in tests
- Next recommended task
```

## Read First Section Standard

Every major task should tell Codex what to read before editing. At minimum, include:

- `AGENTS.md`
- `README.md`
- `docs/PROCESS.md`
- `docs/CODEX_PROMPT_STANDARD.md`
- `config/default.yaml`
- relevant docs under `docs/`
- relevant source files under `src/quant_replay_system/`
- relevant tests under `tests/`

The prompt should list specific module files whenever possible. For example:

```text
Read first:
- AGENTS.md
- README.md
- docs/PROCESS.md
- docs/data_quality.md
- docs/snapshot_quality_gate.md
- src/quant_replay_system/data_quality.py
- src/quant_replay_system/snapshot_quality_gate.py
- tests/test_data_quality.py
- tests/test_snapshot_quality_gate.py
```

Reading first matters because Codex should follow the existing architecture, naming, result objects, artifact conventions, and test style.

## Important Constraints Standard

Use this block unless the task explicitly requires a narrow exception.

```text
Important:
Do NOT implement live trading.
Do NOT add broker integration.
Do NOT automate order placement.
Do NOT add GitHub Actions or CI unless explicitly requested.
Do NOT modify .env.
Do NOT print API keys, tokens, account values, or secrets.
Do NOT use real network/API calls in automated tests.
Do NOT change point-in-time filtering rules unless this task explicitly requires it.
Do NOT change trading calendar or T+1 execution logic unless this task explicitly requires it.
Do NOT change scoring formulas unless this task explicitly requires it.
Use mock/local CSV data only unless this task explicitly says otherwise.
```

For documentation-only tasks, add:

```text
Do NOT change source code.
Do NOT change tests.
Do NOT change configs.
Do NOT implement features.
```

## Validation Reporting Standard

Only include validation checks that actually exist and were actually run.

Do not write `Frontend build: N/A` if the project has no frontend.

Do not write `Offline benchmarks: N/A` if the project has no benchmark suite.

For the current project, default validation should be:

```text
Validation:
- Backend tests: passed/failed, python -m pytest, <N> passed in <duration>.
```

If future checks are actually added and run, include them only when applicable. Examples:

```text
Validation:
- Backend tests: passed, python -m pytest, 398 passed in 36.21s.
- Frontend build: passed, npm run build, completed in 12.4s.
```

Do not include placeholder validation lines for checks that do not exist or were not run.

## Final Response Requirements

Codex should always return:

- Files changed
- Functions/classes implemented
- Tests added/updated
- Documentation updated
- Validation
- Known limitations
- Confirm no live trading or broker integration was added
- Confirm no GitHub Actions workflow was created
- Confirm no secrets were printed or stored
- Confirm no real network/API calls were used in tests
- Next recommended task

For documentation-only tasks, Codex should also confirm:

- no source code was changed,
- no tests were changed,
- no configs with behavior changes were modified.

## Prompt Templates

### A. Feature Implementation Prompt Template

```text
Next task: implement <Feature Name> v0.1.

Context:
The project quant-replay-system already has:
- <dependency module>
- <dependency module>
- Tests currently pass: <N> passed

Read first:
- AGENTS.md
- README.md
- docs/PROCESS.md
- docs/CODEX_PROMPT_STANDARD.md
- <relevant docs>
- <relevant source files>
- <relevant tests>

Do not assume previous chat context.

Important:
Do NOT implement live trading.
Do NOT add broker integration.
Do NOT automate order placement.
Do NOT add GitHub Actions or CI.
Do NOT change point-in-time filtering rules unless this task explicitly requires it.
Do NOT change trading calendar or T+1 execution logic unless this task explicitly requires it.
Do NOT change scoring formulas unless this task explicitly requires it.
Use mock/local CSV data only.
Do NOT use real network/API calls in tests.

Goal:
Implement <feature> so that <user-facing or research workflow outcome>.

Reason:
This is needed because <why it matters>.

Tasks:
1. Add or update <module>.
2. Implement <function/class>.
3. Add deterministic artifacts or outputs if applicable.
4. Preserve existing behavior when the feature is disabled.

Tests:
Add or update tests for:
1. normal behavior,
2. edge cases,
3. deterministic output,
4. metadata/audit fields if applicable,
5. no live trading or broker integration,
6. no network calls.

Documentation:
- Create or update docs/<feature>.md.
- Update README.md with a short link if user-facing.

Validation:
Run:
python -m pytest

Final response requirements:
- Files changed
- Functions/classes implemented
- Tests added/updated
- Documentation updated
- Validation
- Known limitations
- Confirm no live trading or broker integration was added
- Confirm no GitHub Actions workflow was created
- Confirm no secrets were printed or stored
- Confirm no real network/API calls were used in tests
- Next recommended task
```

### B. Documentation-Only Prompt Template

```text
Next task: document <topic>.

Context:
The project quant-replay-system already has:
- <relevant module>
- <relevant docs>
- Tests currently pass: <N> passed

Read first:
- AGENTS.md
- README.md
- docs/PROCESS.md
- docs/CODEX_PROMPT_STANDARD.md
- <relevant docs>

Do not assume previous chat context.

Important:
Do NOT change source code.
Do NOT change tests.
Do NOT change configs.
Do NOT implement features.
Do NOT add GitHub Actions or CI.
Do NOT add live trading.
Do NOT add broker integration.

Goal:
Create or update documentation for <topic>.

Reason:
This documentation is needed because <reason>.

Tasks:
1. Create or update <doc path>.
2. Update docs/PROCESS.md if process-facing.
3. Update AGENTS.md if repository rules change.
4. Update README.md with a short link if useful.

Tests:
No new tests are required for documentation-only changes.

Documentation:
- <specific docs to create/update>

Validation:
Run:
python -m pytest

Final response requirements:
- Files changed
- Documentation updated
- Validation
- Known limitations
- Confirm no source code, tests, or configs with behavior changes were modified
- Confirm no GitHub Actions workflow was created
- Confirm no live trading or broker integration was added
- Next recommended task
```

### C. Hardening/Bugfix Prompt Template

```text
Next task: harden/fix <module or behavior>.

Context:
<Summarize the bug, risk, or weak behavior.>

Read first:
- AGENTS.md
- README.md
- docs/PROCESS.md
- docs/CODEX_PROMPT_STANDARD.md
- <affected source files>
- <affected tests>

Do not assume previous chat context.

Important:
Do NOT change unrelated behavior.
Do NOT broaden the fix into a refactor unless needed.
Do NOT change point-in-time filtering rules unless this task explicitly requires it.
Do NOT change trading calendar or T+1 execution logic unless this task explicitly requires it.
Do NOT implement live trading or broker integration.
Use mock/local CSV data only.

Goal:
Fix <specific issue> while preserving existing contracts.

Reason:
This matters because <risk>.

Tasks:
1. Reproduce or identify the failing path.
2. Implement the narrow fix.
3. Add regression tests.
4. Keep deterministic outputs stable unless the bug requires changing them.

Tests:
Add or update tests for:
1. the failing case,
2. the expected successful case,
3. no regression in related behavior.

Documentation:
- Update docs only if user-facing behavior or known limitations change.

Validation:
Run:
python -m pytest

Final response requirements:
- Files changed
- Functions/classes implemented
- Tests added/updated
- Documentation updated
- Validation
- Known limitations
- Confirm no live trading or broker integration was added
- Confirm no GitHub Actions workflow was created
- Confirm no secrets were printed or stored
- Confirm no real network/API calls were used in tests
- Next recommended task
```

### D. Integration Prompt Template

```text
Next task: integrate <module A> with <module B> v0.1.

Context:
The project already has:
- <module A>
- <module B>
- Tests currently pass: <N> passed

Read first:
- AGENTS.md
- README.md
- docs/PROCESS.md
- docs/CODEX_PROMPT_STANDARD.md
- <module A docs/source/tests>
- <module B docs/source/tests>

Do not assume previous chat context.

Important:
Do NOT change core contracts unless explicitly required.
Do NOT duplicate existing logic.
Do NOT change point-in-time filtering, T+1 execution, or scoring formulas unless explicitly required.
Do NOT implement live trading or broker integration.
Use mock/local CSV data only.

Goal:
Wire <module A> into <module B> so that <outcome>.

Reason:
This reduces manual steps and keeps workflow artifacts auditable.

Tasks:
1. Add optional config or function arguments if needed.
2. Reuse existing helper functions.
3. Preserve disabled/default behavior.
4. Attach metadata/audit fields if applicable.
5. Avoid duplicate work inside nested workflows.

Tests:
Add or update tests for:
1. disabled behavior unchanged,
2. enabled behavior works,
3. failure behavior is clear,
4. metadata is recorded,
5. no duplicate execution if nested,
6. deterministic output.

Documentation:
- Create or update docs/<integration>.md.
- Update README.md with a short link if user-facing.

Validation:
Run:
python -m pytest

Final response requirements:
- Files changed
- Functions/classes implemented
- Tests added/updated
- Documentation updated
- Validation
- Known limitations
- Confirm no live trading or broker integration was added
- Confirm no GitHub Actions workflow was created
- Confirm no secrets were printed or stored
- Confirm no real network/API calls were used in tests
- Next recommended task
```

### E. CLI Prompt Template

```text
Next task: implement CLI command <command-name> v0.1.

Context:
The project already has:
- existing CLI in src/quant_replay_system/cli.py
- <related module>
- Tests currently pass: <N> passed

Read first:
- AGENTS.md
- README.md
- docs/PROCESS.md
- docs/CODEX_PROMPT_STANDARD.md
- src/quant_replay_system/cli.py
- <related module files>
- tests/test_*cli*.py

Do not assume previous chat context.

Important:
Use Python standard library argparse unless the project already uses something else.
Do NOT add dependencies unless necessary.
Do NOT implement live trading.
Do NOT add broker integration.
Do NOT automate order placement.
Do NOT print secrets or tokens.
Use mock/local CSV data only.

Goal:
Add a local-only CLI command that <does what>.

Reason:
This makes the workflow usable from Windows CMD without manual Python calls.

Tasks:
1. Add parser options.
2. Add handler function.
3. Validate required input clearly.
4. Print human-readable summary.
5. Return non-zero on failure.
6. Print `No live trading or broker API was invoked.` when relevant.

Tests:
Add or update tests for:
1. command success,
2. missing required input,
3. validation failure,
4. artifact output if applicable,
5. no live trading or broker integration.

Documentation:
- Create or update docs/<cli_doc>.md.
- Update README.md with usage examples.

Validation:
Run:
python -m pytest

Final response requirements:
- Files changed
- Functions/classes implemented
- Tests added/updated
- Documentation updated
- Validation
- Known limitations
- Confirm no live trading or broker integration was added
- Confirm no GitHub Actions workflow was created
- Confirm no secrets were printed or stored
- Confirm no real network/API calls were used in tests
- Next recommended task
```

### F. Artifact/Reporting Prompt Template

```text
Next task: implement <artifact/report> v0.1.

Context:
The project already writes artifacts for:
- <related report>
- <related workflow>

Read first:
- AGENTS.md
- README.md
- docs/PROCESS.md
- docs/CODEX_PROMPT_STANDARD.md
- <related report module>
- <related tests>

Do not assume previous chat context.

Important:
Do NOT change calculations unless explicitly required.
Do NOT change point-in-time rules.
Do NOT implement live trading or broker integration.
Use stable, deterministic artifact naming where possible.

Goal:
Write auditable artifacts for <workflow>.

Reason:
Artifacts make replay/review/calibration repeatable and inspectable.

Tasks:
1. Define artifact directory structure.
2. Write markdown report.
3. Write CSV/JSON artifacts.
4. Preserve stable column ordering.
5. Include metadata and known limitations.
6. Include no-live-trading statement where relevant.

Tests:
Add or update tests for:
1. artifact folder created,
2. markdown report written,
3. CSV files readable by pandas,
4. metadata JSON written,
5. deterministic artifact id/path,
6. report contains required sections.

Documentation:
- Create or update docs/<report>.md.
- Update README.md with a link.

Validation:
Run:
python -m pytest

Final response requirements:
- Files changed
- Functions/classes implemented
- Tests added/updated
- Documentation updated
- Validation
- Known limitations
- Confirm no live trading or broker integration was added
- Confirm no GitHub Actions workflow was created
- Confirm no secrets were printed or stored
- Confirm no real network/API calls were used in tests
- Next recommended task
```

### G. Data Ingestion/Quality Prompt Template

```text
Next task: implement <data ingestion/quality module> v0.1.

Context:
The project already has:
- Point-in-Time Data Contract
- Market Data Ingestion
- Data Quality Summary Reports
- Snapshot Quality Gate

Read first:
- AGENTS.md
- README.md
- docs/PROCESS.md
- docs/CODEX_PROMPT_STANDARD.md
- docs/data_contract.md
- docs/data_ingestion.md
- docs/data_quality.md
- docs/snapshot_quality_gate.md
- src/quant_replay_system/data.py
- src/quant_replay_system/data_ingestion.py
- src/quant_replay_system/data_quality.py
- relevant tests

Do not assume previous chat context.

Important:
Do NOT use real network/API calls in tests.
Do NOT require real API tokens.
Do NOT modify .env.
Do NOT print tokens or secrets.
Do NOT change point-in-time filtering rules unless explicitly required.
Use mock/local CSV data only.
Do NOT implement live trading or broker integration.

Goal:
Improve local data reliability by <specific goal>.

Reason:
Replay quality depends on processed data being complete, consistent, and point-in-time safe.

Tasks:
1. Validate required schemas.
2. Preserve or report `available_time`, `revision_id`, and `source`.
3. Write quality or ingestion artifacts.
4. Keep behavior deterministic.
5. Record warnings/errors clearly.

Tests:
Add or update tests for:
1. clean data passes,
2. missing required columns fail,
3. invalid dates/timestamps fail,
4. duplicate keys warn or fail according to config,
5. artifacts are written and readable,
6. no network calls,
7. no live trading or broker integration.

Documentation:
- Create or update docs/<data_doc>.md.
- Update README.md with a link if user-facing.

Validation:
Run:
python -m pytest

Final response requirements:
- Files changed
- Functions/classes implemented
- Tests added/updated
- Documentation updated
- Validation
- Known limitations
- Confirm no live trading or broker integration was added
- Confirm no GitHub Actions workflow was created
- Confirm no secrets were printed or stored
- Confirm no real network/API calls were used in tests
- Next recommended task
```

### H. Paper Trading Workflow Prompt Template

```text
Next task: implement <paper trading workflow> v0.1.

Context:
The project already has:
- Manual Paper Trading Journal
- Daily Paper Trading Runner
- Paper Trading CLI
- Fill Reconciliation
- Review Workflow
- Artifact Index and Health Check

Read first:
- AGENTS.md
- README.md
- docs/PROCESS.md
- docs/CODEX_PROMPT_STANDARD.md
- docs/manual_paper_trading.md
- docs/daily_paper_trading_runner.md
- docs/paper_fill_reconciliation.md
- docs/paper_trading_review_workflow.md
- related source and tests

Do not assume previous chat context.

Important:
Do NOT implement live trading.
Do NOT add broker integration.
Do NOT automate order placement.
Do NOT print account values, API keys, tokens, or secrets.
Do NOT use real network/API calls in tests.
Use mock/local CSV data only.

Goal:
Improve the local-only manual paper trading workflow by <specific goal>.

Reason:
Manual paper trading should remain auditable and separate from real orders.

Tasks:
1. Preserve manual review and fill validation rules.
2. Preserve no-short-selling and cash safety defaults.
3. Write or update artifacts if applicable.
4. Include no-live-trading statements in reports and CLI output where relevant.
5. Keep output deterministic.

Tests:
Add or update tests for:
1. normal paper workflow,
2. rejected/watch/pending decision handling,
3. invalid fills or reconciliation failures,
4. artifact outputs readable by pandas,
5. no live trading or broker integration,
6. no network calls.

Documentation:
- Create or update docs/<paper_doc>.md.
- Update README.md with a link and local-only usage example if useful.

Validation:
Run:
python -m pytest

Final response requirements:
- Files changed
- Functions/classes implemented
- Tests added/updated
- Documentation updated
- Validation
- Known limitations
- Confirm no live trading or broker integration was added
- Confirm no GitHub Actions workflow was created
- Confirm no secrets were printed or stored
- Confirm no real network/API calls were used in tests
- Next recommended task
```

## Checkpoint and Tag Guidance

After a stable module, use this checkpoint flow:

```bat
cd /d "G:\AICODING\Quantitative Trading\quant-replay-system"
python -m pytest
git status --short
git ls-files | findstr /R /C:"^\.pytest_cache" /C:"^\.benchmarks" /C:"__pycache__" /C:"^\.venv" /C:"^\.env$" /C:"^secrets"
git add .
git commit -m "..."
git push
```

Only tag when ChatGPT recommends it:

```bat
git tag -a vX.Y.Z -m "..."
git push origin vX.Y.Z
```

Before committing or tagging:

- run `python -m pytest`,
- check `git status --short`,
- verify no cache/env/secrets are tracked,
- verify no raw vendor data or generated local outputs are tracked,
- verify known limitations are documented.

## Relationship To PROCESS.md And AGENTS.md

- `docs/PROCESS.md` defines the overall development workflow.
- `docs/CODEX_PROMPT_STANDARD.md` defines the prompt structure for future Codex tasks.
- `AGENTS.md` defines repository-level rules Codex should follow.

Future prompts should follow this standard, but ChatGPT still decides the final next step after reviewing Codex's summary.
