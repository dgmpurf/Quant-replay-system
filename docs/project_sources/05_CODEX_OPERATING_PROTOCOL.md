# Codex Operating Protocol for This Project

> Status: working memory document  
> Last generated: 2026-06-11  
> Permanence: temporary; update if workflow preferences, safety boundaries, or replay/training priorities change.

## Roles

### ChatGPT

ChatGPT is the planning, review, and decision layer.

ChatGPT should:

- decide the next project task;
- judge Codex output;
- decide whether to accept, reject, narrow, or defer Codex recommendations;
- decide when to checkpoint/tag;
- protect project direction and safety boundaries;
- keep the personal-first / institution-grade-core direction intact;
- keep historical replay training, PIT validity, factor universe expansion, and stock-level profiles visible in roadmap decisions.

### Codex

Codex is the local implementation and verification worker.

Codex should:

- inspect relevant files;
- implement scoped tasks;
- run tests;
- run safe local CLI dry-runs;
- report exact files and artifacts;
- never commit or push;
- never infer strategy validity from synthetic fixtures;
- never turn advisory labels into orders.

## Strategic Context for Every Relevant Codex Task

Include this context when relevant:

```text
This quantitative trading project is personal-first but institution-grade-core.
The first usable version is for personal/family A-share/ETF advisory.
The research core must support historical replay training, point-in-time data validity,
factor universe expansion, stock-level profiles, forward-return evaluation,
and paper workflow validation before any real buy-review candidate.
Do not treat fixed 12 factors as final; use the 8-layer taxonomy as the primary structure
and broader factor universe as expandable coverage.
```

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
  - no live trading;
  - no broker integration;
  - no automated orders;
  - no real messages;
  - no LLM/API calls unless explicitly allowed;
  - no cache mutation unless explicitly allowed;
  - no git add/commit/push;
  - no `APPROVED_FOR_PAPER` unless explicitly requested and manually tested;
  - no strategy performance validation claim;
  - no forward labels unless explicitly in scope;
  - no stock real-buy eligibility changes unless explicitly in scope.
- Next recommended task.

## Extra Return Fields for Replay/Training Tasks

For replay, factor, event, forward-label, training, or stock-profile tasks, also ask Codex to report:

- PIT validity assumptions.
- `available_time` handling.
- Survivorship-bias handling.
- Corporate action adjustment assumptions.
- Source permission assumptions.
- Whether any raw/generated data was written.
- Whether generated data paths are ignored by Git.
- Whether any model weights, thresholds, or metrics are research-only.
- Whether outputs are design-only, diagnostic-only, or active artifacts.

## Validation Rules

Before checkpoint or milestone review:

```bat
python -m pytest
python -m pytest -m "not slow"
```

For documentation-only tasks, narrower validation can be acceptable if the task explicitly says so, but before commit/tag use full tests.

For replay/training schema tasks, prefer dry-run commands and fixture tests first. Do not run broad data generation unless explicitly scoped.

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
Do NOT create real buy-review eligibility.
Do NOT treat historical replay metrics as production validation.
Do NOT treat 12 factors as final or exhaustive.
Do NOT bypass point-in-time availability checks.
Do NOT compute forward returns unless explicitly scoped.
Do NOT train model weights unless valid replay/label inputs exist and the task explicitly requests it.
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

## Historical Replay Constraint

For replay/training tasks, include:

```text
Historical replay must only use data available at the replay decision time.
Every document/factor/event used by replay must have available_time, source, revision_id,
and permission/compliance metadata.
No future universe membership, future ST/delist/suspension status, future announcement,
future financial statement, future news, or future label may leak into replay decisions.
```

## When to Use Read-Only Audits

Use read-only audits before:

- changing signal semantics thresholds;
- adding external data sources;
- building crawlers;
- adding raw document stores;
- adding factor observation builders;
- running multi-date candidates;
- computing forward returns;
- integrating new source data into scoring;
- training model weights;
- creating stock-level profiles;
- changing real buy-review eligibility;
- adding alert delivery;
- adding broker or execution logic.

## When to Add Checkpoint Docs

Add checkpoint docs after:

- major feature completion;
- dashboard/research-status semantics changes;
- safety/actionability changes;
- source-selection or provenance changes;
- paper workflow changes;
- multi-date planning changes;
- product-layer advisory milestones;
- replay/training schema milestones;
- forward-label/evaluation milestones;
- stock-profile validation milestones.

Checkpoint docs are not permanent; they summarize stable milestones for review and tagging.
