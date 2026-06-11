# Source Changelog: 2026-06-12

> Status: helper document  
> Purpose: summarize the source-pack changes after v1.27.0 replay substrate schema fixture checkpoint and research method stack clarification.

## Why This Source Pack Was Updated

The previous source pack captured the 2026-06-11 strategic correction:

```text
personal-first, institution-grade-core
historical replay training
factor universe
stock-level profiles before real buy-review
```

Since then, Codex completed a full report-only replay-substrate schema fixture milestone:

```text
replay-substrate-schema-fixture
→ index
→ health
→ status
→ research-status integration
→ docs/release_checkpoint_v1.27.0.md
```

The user also clarified that the research core should not be described only as ML/DL/data mining or algorithms/weights/formulas. It needs a broader quant research method stack.

## Main Changes

### 1. Project Source Index Updated

`00_PROJECT_SOURCE_INDEX.md` now records:

- v1.27.0 checkpoint state;
- `REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY` as schema-fixture preparation context;
- Codex recommendation rule: Codex next task is reference only;
- current recommended next branch: `Historical Replay Substrate Readiness Plan Report-Only v0.1`.

### 2. Architecture Updated

`02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md` now includes:

- Research Method Stack Layer;
- replay-substrate schema fixture chain;
- v1.27.0 fixture status;
- explicit distinction between schema fixture and real replay/labels/training/stock profiles.

### 3. Roadmap Updated

`03_ROADMAP_AND_NEXT_DECISION_POINTS.md` now marks v1.27.0 as completed and updates the next branch to:

```text
Historical Replay Substrate Readiness Plan Report-Only v0.1
```

### 4. Current State Snapshot Updated

`07_CURRENT_STATE_SNAPSHOT.md` now records:

```text
fixture_id: 5f9a393ce90d
stage: REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY
health: PASS
entity_count: 14
validation_issue_count: 0
overclaim guards: 8 / 8
active_replay_input=false
forward_labels_exist=false
weights_trained=false
active_stock_profile_exists=false
real_buy_review_eligible=false
```

It also records the completed reviewer-supplied material evidence audit summary provided by the user.

### 5. Historical Replay Strategy Updated

`08_HISTORICAL_REPLAY_TRAINING_STRATEGY.md` now includes:

- current implemented v1.27.0 schema fixture state;
- broader research method stack;
- explicit statement that schema fixture readiness does not mean real replay readiness.

### 6. New Research Method Stack Source Added

`10_RESEARCH_METHOD_STACK_AND_MODEL_GOVERNANCE.md` has been added.

It explains that the project requires:

- data engineering;
- PIT evidence governance;
- statistics;
- econometrics;
- financial engineering;
- factor research;
- event study;
- causal inference;
- knowledge graph / industry-chain modeling;
- NLP / IR / RAG;
- data mining;
- ML / DL;
- optimization;
- risk management;
- portfolio construction;
- execution modeling;
- replay evaluation;
- explainability;
- DataOps / MLOps / model governance.

## What Did Not Change

The following core safety boundaries remain unchanged:

- no live trading;
- no broker API;
- no automated orders;
- no real message delivery;
- no LLM/API calls in deterministic advisory logic;
- no cache mutation unless explicitly allowed;
- no generated raw/processed/cache/output files committed;
- `REVIEW_BUY_CANDIDATE` is human-review only, not a buy instruction;
- schema fixtures are not real replay inputs;
- training/evaluation artifacts are research-only unless later validated.

## Suggested Next User Prompt

```text
Give me the Codex task for Historical Replay Substrate Readiness Plan Report-Only v0.1.
```
