# Codex Operating Protocol for This Project

> Status: working memory document  
> Last generated: 2026-05-28  
> Permanence: temporary; update if workflow preferences change.

## Roles

### ChatGPT

ChatGPT is the planning, review, and decision layer.

ChatGPT should:

- decide the next project task,
- judge Codex output,
- decide whether to accept, reject, narrow, or defer Codex recommendations,
- decide when to checkpoint/tag,
- protect project direction and safety boundaries.

### Codex

Codex is the local implementation and verification worker.

Codex should:

- inspect relevant files,
- implement scoped tasks,
- run tests,
- run safe local CLI dry-runs,
- report exact files and artifacts,
- never commit or push.

## User Preference: Split Long Work

Large work should be split into small queueable tasks.

Default structure:

```text
Task 1: Read-only audit
Task 2: Core implementation
Task 3: Artifact views / integration
Task 4: Consolidation / checkpoint docs
```

Each task may include a Next Recommended Task. ChatGPT treats that as reference, not command.

## Standard Codex Return Fields

Ask Codex to return:

- Files changed.
- Functions/classes implemented or updated.
- Tests added/updated.
- Documentation updated.
- Local dry-run result.
- Validation result.
- Git safety summary.
- Known limitations.
- Confirmations:
  - no live trading,
  - no broker integration,
  - no automated orders,
  - no real messages,
  - no LLM/API calls unless explicitly allowed,
  - no cache mutation unless explicitly allowed,
  - no git add/commit/push.
- Next recommended task.

## Validation Rules

Before checkpoint or milestone review:

```bat
python -m pytest
python -m pytest -m "not slow"
```

For documentation-only tasks, narrower validation can be acceptable if the task explicitly says so, but before commit/tag use full tests.

## Git Safety Rules

Codex must not run:

```bat
git add
git commit
git push
git tag
```

The user runs these manually after ChatGPT review.

Before commit/tag, run:

```bat
git status --short
git ls-files | findstr /R /C:"^\.pytest_cache" /C:"^\.benchmarks" /C:"__pycache__" /C:"^\.venv" /C:"^\.env$" /C:"^secrets" /C:"^data/raw" /C:"^data/processed" /C:"^outputs" /C:"^data/cache"
```

Expected tracked local paths should normally be limited to:

```text
.env.example
data/raw/.gitkeep
data/processed/.gitkeep
outputs/reports/.gitkeep
```

## Safety Defaults for Every Codex Prompt

Include unless explicitly irrelevant:

```text
Do NOT implement live trading.
Do NOT add broker integration.
Do NOT automate order placement.
Do NOT send real messages.
Do NOT call LLM APIs or external APIs.
Do NOT mutate market cache.
Do NOT modify .env.
Do NOT print secrets or tokens.
Do NOT run git add / commit / push.
Do NOT apply APPROVED_FOR_PAPER.
Do NOT claim strategy performance is validated.
```

## Free-First Data Source Constraint

For external data work, include:

```text
Current budget constraint:
Prefer free, open-source, public, local, or manually reviewed CSV data sources.
Paid vendors are future backup candidates only.
Do not implement paid vendor adapters unless explicitly requested.
Do not make current workflows depend on paid APIs.
```

## When to Use Read-Only Audits

Use read-only audits before:

- changing signal semantics thresholds,
- adding external data sources,
- building crawlers,
- running multi-date candidates,
- computing forward returns,
- integrating new source data into scoring,
- adding alert delivery,
- adding broker or execution logic.

## When to Add Checkpoint Docs

Add checkpoint docs after:

- major feature completion,
- dashboard/research-status semantics changes,
- safety/actionability changes,
- source-selection or provenance changes,
- paper workflow changes,
- multi-date planning changes,
- product-layer advisory milestones.

Checkpoint docs are not permanent; they summarize stable milestones for review and tagging.
