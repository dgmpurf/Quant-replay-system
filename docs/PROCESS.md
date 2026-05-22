# Project Process

This document defines the development workflow for `quant-replay-system` when working iteratively with Codex and ChatGPT guidance.

## Codex Prompt Standard

Future Codex development prompts should follow [CODEX_PROMPT_STANDARD.md](CODEX_PROMPT_STANDARD.md).

That document defines the standard prompt structure for scoped implementation tasks, documentation-only tasks, hardening/bugfixes, integrations, CLI work, artifact/reporting work, data ingestion/quality work, and paper trading workflow work.

Codex should use the standard as the task interpretation baseline:

- read relevant files first,
- do not assume previous chat context,
- preserve point-in-time and T+1 contracts unless explicitly instructed,
- keep safety constraints explicit,
- run validation,
- return the required summary fields.

Codex's Next Recommended Task should be sent back to ChatGPT after each task, but ChatGPT decides the final next step, including whether to continue, repair, checkpoint, push, or tag.

## 1. Project Development Principle

- Build one module at a time.
- Every module must be testable.
- Early MVP work must not include live trading or broker automation.
- Point-in-time safety has priority over convenience, speed, or model complexity.
- Risk gates have priority over scoring. A high score must not override a hard risk block.
- Each module should leave behind a clear contract: inputs, outputs, tests, known limitations, and next recommended task.

## 2. Codex Development Loop

For each scoped task, Codex should:

1. Receive a clearly scoped task.
2. Inspect relevant existing files before editing.
3. Modify only files needed for the task.
4. Add or update focused tests.
5. Run:

```bat
python -m pytest
```

6. Return:

- files changed
- tests added
- pytest result
- known limitations
- next recommended task

Codex should not silently broaden scope. If a task is documentation-only, Codex should not change source code, tests, or config.

## Validation Reporting Standard

Every Codex task summary must include a validation block that lists only validation checks that actually exist and were actually run.

```text
Validation:
- Backend tests: passed, python -m pytest, <N> passed in <duration>.
```

For `quant-replay-system`:

- The default validation output should include backend tests only.
- Backend tests command is:

```bat
python -m pytest
```

- Do not report `Frontend build: N/A` when no frontend exists.
- Do not report `Offline benchmarks: N/A` when no benchmark suite exists.
- If a future `frontend/` module or benchmark suite is added, include those validation lines only when they are applicable and were actually run.

## 3. ChatGPT Review Loop

After Codex finishes a task:

1. The user sends Codex's summary to ChatGPT.
2. The user should include Codex's Next Recommended Task.
3. ChatGPT decides the final next step.
4. ChatGPT decides whether to checkpoint, tag, continue, or repair.

ChatGPT is the planning and review layer. Codex is the implementation and local verification layer.

## 4. Git Checkpoint Rules

Commit and push after every stable module when:

- all tests pass,
- the module is complete enough to checkpoint,
- no sensitive files are tracked,
- no raw vendor data or generated outputs are tracked,
- the checkpoint happens before starting the next major task.

Recommended CMD flow:

```bat
cd /d "G:\AICODING\Quantitative Trading\quant-replay-system"
python -m pytest
git status --short
git ls-files | findstr /R /C:"\.pytest_cache" /C:"\.benchmarks" /C:"__pycache__" /C:"\.env" /C:"\.venv"
git add .
git commit -m "..."
git push
```

If the `git ls-files | findstr ...` command prints tracked sensitive/cache/local files, stop and fix `.gitignore` or untrack the files before committing.

## 5. Git Tag Rules

Create annotated tags after stable milestone modules, not after every small edit.

Example milestone tags:

- `v0.1.0`: MVP setup + point-in-time + T+1 + environment
- `v0.2.0`: Technical Indicators
- `v0.3.0`: Factor Dataset Builder
- `v0.4.0`: Score Engine + Candidate Selection
- `v0.5.0`: Replay Integration
- `v1.0.0`: Paper Trading Ready MVP

Recommended CMD flow:

```bat
git tag --list
git tag -a vX.Y.Z -m "message"
git push origin vX.Y.Z
```

Before tagging, run tests and review `git status --short`.

## Milestone Checkpoint Documents

After major E2E workflow milestones, create a concise checkpoint document under `docs/release_checkpoint_<version>.md`.

The checkpoint should summarize completed capabilities, the local command sequence, safety constraints, known limitations, validation expectations, and the recommended tag. These documents support the ChatGPT/user checkpoint decision and do not replace `python -m pytest`, `git status --short`, or secret/cache tracking checks.

## 6. Pro Extended Usage Rules

Pro Extended is not needed for:

- small Codex tasks,
- Git commands,
- simple explanations,
- small documentation edits,
- narrow bug fixes with obvious scope.

Pro Extended is recommended for:

- multi-file code review,
- architecture redesign,
- long project documents,
- complex debugging,
- major module planning,
- decisions that affect point-in-time rules, risk gates, or replay semantics.

## 7. Module Completion Standard

A module is complete only if:

- tests pass,
- docs are updated if needed,
- no live trading is added,
- no future data leakage is introduced,
- no sensitive files are tracked,
- Codex known limitations are recorded,
- ChatGPT confirms the next step.

If any of these are missing, the module should be considered incomplete or checkpointed only as a work-in-progress branch.

## 8. Forbidden Actions

- No broker auto-ordering.
- No live trading automation.
- No GitHub Actions or CI unless explicitly approved.
- No private, insider, or non-public data.
- No committing `.env`.
- No committing raw vendor data.
- No committing secrets, API keys, `.pem`, or `.key` files.
- No changing point-in-time rules without explicit review.
- No scoring shortcut that bypasses risk gates.

## 9. Current Module Roadmap

Completed:

- MVP setup
- Point-in-Time Data Contract
- Trading Calendar / T+1
- Environment Setup
- Technical Indicators
- Factor Dataset Builder
- Score Engine + Candidate Selection

Next:

- Replay Integration
- Report Generation
- Batch Replay
- Parameter Calibration
- Paper Trading

## 10. What User Should Send Back After Each Codex Task

After each Codex task, the user should send ChatGPT:

- Codex summary
- files changed
- tests added
- pytest result
- known limitations
- Codex next recommended task
- `git status --short` output if available

This keeps the planning loop grounded in the actual workspace state.
