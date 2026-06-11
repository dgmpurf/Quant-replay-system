# Quant Replay System Project Source Pack Index

> Status: working memory document  
> Last generated: 2026-06-12  
> Intended use: replace the previous ChatGPT Project Source pack after the v1.27.0 replay substrate schema fixture checkpoint.  
> Permanence: temporary and replaceable. Refresh after a major checkpoint, accepted artifact workflow, source-goal change, model-governance change, or safety-boundary change.

## Purpose

This pack condenses the current `quant-replay-system` direction, engineering state, artifact governance rules, factor taxonomy rules, research-method rules, and roadmap for ChatGPT Project Sources.

It is designed to reduce reliance on the long chat transcript and help future ChatGPT/Codex sessions recover the project state quickly.

## 2026-06-12 Current Strategic Position

The project direction is:

```text
Personal-first, institution-grade-core.
```

Meaning:

```text
First usable product:
  personal/family China A-share and ETF advisory.

Research core:
  institution-grade historical replay, point-in-time validity,
  factor universe expansion, stock-level profiles,
  forward-return evaluation, research-method governance,
  and paper workflow validation before any real buy-review candidate.
```

The project is not a fixed-factor screener and not an automatic trading robot. It is a historical replay research and advisory system:

```text
historical date T
→ load only information available at or before T
→ structure market/fundamental/announcement/news/policy/industry data into factor/event observations
→ generate WATCH / review-only buy/sell candidates under deterministic safety gates
→ compare with future realized returns and drawdowns only after decisions are frozen
→ train/calibrate weights, thresholds, horizons, market-regime rules, and risk vetoes
→ build stock-level validation profiles
→ only then allow real buy-review eligibility, still requiring human confirmation
```

This correction does not approve live trading, does not validate strategy performance, and does not relax PIT, paper, review, or human-confirmation gates.

## 2026-06-12 v1.27.0 Checkpoint Update

A report-only replay substrate schema fixture workflow is now implemented and integrated into research-status.

Completed chain:

```text
replay-substrate-schema-fixture
→ replay-substrate-schema-fixture-index
→ replay-substrate-schema-fixture-health
→ replay-substrate-schema-fixture-status
→ research-status integration
→ docs/release_checkpoint_v1.27.0.md
```

Latest known fixture context:

```text
fixture_id: 5f9a393ce90d
fixture_status: PASS
fixture_stage: REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY
health_status: PASS
entity_count: 14
validation_issue_count: 0
overclaim_guard_pass_count: 8
overclaim_guard_total_count: 8
active_replay_input: false
forward_labels_exist: false
weights_trained: false
active_stock_profile_exists: false
real_buy_review_eligible: false
report_only: true
diagnostic_only: true
no_live_trading: true
no_broker_api: true
no_order_placement: true
```

This checkpoint proves only schema/fixture contracts. It is not real replay, not forward-label computation, not model training, not stock-profile validation, and not real buy-review eligibility.

## Source Basis

This pack is based on:

- the long ChatGPT/Codex collaboration history;
- repository docs for `dgmpurf/Quant-replay-system`;
- v1.0.0 through v1.27.0 research, PIT evidence, reviewer no-hit, first-batch completion, material gate closure, reviewer fill guidance, one-row material package, one-row checklist-pass preview, replay-substrate schema fixture, artifact views, research-status integration, and checkpoint docs;
- diagnostics for SZSE 1815 same-date quotation, exception/no-hit probes, official no-hit policy audits, reviewer acceptance smoke tests, downstream impact smoke tests, material gate closure, fill guidance, one-row material package, checklist-pass preview audits, reviewer-supplied material evidence fixture audit, and replay-substrate architecture audit;
- China A-share event-driven and industry-chain factor taxonomy sources;
- the 2026-06-11 clarification that historical replay training, factor-universe expansion, and stock-level validation are central project capabilities;
- the 2026-06-12 clarification that the project requires a broader quant research method stack, not only ML/DL/data mining or formulas/weights.

## Accuracy Note

This pack does not replace source code, formal repository docs, or actual local artifacts.

Many local outputs under `outputs/`, `data/raw/`, `data/cache`, and `data/processed` are intentionally ignored by Git and may not be available to ChatGPT. When local artifact state matters, the user should paste Codex summaries or run local CLI/status checks.

## Current Project Source Set

Use these as the active ChatGPT Project Sources after this refresh:

```text
00_PROJECT_SOURCE_INDEX.md
01_PROJECT_VISION_AND_BOUNDARIES.md
02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md
03_ROADMAP_AND_NEXT_DECISION_POINTS.md
04_FREE_FIRST_DATA_SOURCE_STRATEGY.md
05_CODEX_OPERATING_PROTOCOL.md
06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md
07_CURRENT_STATE_SNAPSHOT.md
08_HISTORICAL_REPLAY_TRAINING_STRATEGY.md
09_SOURCE_CHANGELOG_2026-06-12.md
10_RESEARCH_METHOD_STACK_AND_MODEL_GOVERNANCE.md
FACTOR_TAXONOMY_SUMMARY.md
FACTOR_TAXONOMY_V2_CANONICAL.md
FACTOR_TAXONOMY_V2_RAW_EXCEL_EXPORT.md
中国事件驱动与产业链量化系统的因子分层框架研究.md
```

Optional helper:

```text
MANIFEST.md
```

## Canonical Factor Rule

Use this priority when taxonomy sources overlap:

1. `FACTOR_TAXONOMY_V2_CANONICAL.md` is the canonical factor taxonomy.
2. `中国事件驱动与产业链量化系统的因子分层框架研究.md` explains the China-specific strategic rationale.
3. `FACTOR_TAXONOMY_V2_RAW_EXCEL_EXPORT.md` is a raw Excel-conversion reference.
4. `FACTOR_TAXONOMY_SUMMARY.md` is the operational summary for ChatGPT/Codex usage.
5. Any future `factor_definition_seed.csv` is an engineering seed, not a trading model.

Important:

```text
8-layer taxonomy = primary database/model skeleton.
12-factor framework = coverage checklist only.
Factor universe = expandable and not limited to 12 factors.
```

## Research Method Rule

Do not frame the project as only:

```text
ML / DL / data mining
```

or only:

```text
algorithms / weights / formulas
```

The project needs a broader quant research method stack:

```text
data engineering
PIT evidence governance
statistics
econometrics
financial engineering
factor research
event study
causal inference
knowledge graph / industry-chain modeling
NLP / IR / RAG for public documents
ML / DL / data mining
optimization
risk management
portfolio construction
execution modeling
replay evaluation
explainability
DataOps / MLOps / model governance
```

All methods must be gated by PIT validity, source provenance, forward-label separation, out-of-sample validation, paper workflow, and human confirmation.

## Current Project State Summary

The project has completed a replay-substrate schema fixture checkpoint, but it is still not ready for real replay training or non-demo buy/sell validation.

Current completed / in-progress chains include:

```text
local market data / reviewed exports / quality gates
→ current-candidates
→ signal semantics / advisory layers
→ calibration tooling
→ multi-date backfill planning
→ PIT universe evidence workflows
→ one-row material evidence package
→ one-row checklist-pass candidate preview
→ reviewer-supplied material evidence fixture audit
→ historical replay training substrate architecture audit
→ replay-substrate-schema-fixture
→ replay-substrate-schema-fixture index / health / status
→ research-status integration
→ v1.27.0 checkpoint doc
```

Current replay substrate state:

```text
REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY
```

Current final research-status workflow stage remains:

```text
PAPER_WORKFLOW_READY
```

The replay-substrate schema fixture appears as replay/training preparation context only and must not override paper workflow priority or imply active replay readiness.

## Key Conclusions

```text
PIT evidence is not the final product.
PIT evidence is the validity foundation for historical replay training.
```

```text
A checklist-pass candidate preview is not approval.
A PIT-approved universe input is not a trading signal.
A schema fixture is not real replay.
A replay decision is not performance validation.
A forward label is not strategy validation by itself.
A training result is not production readiness.
A stock profile is not automatic buy permission.
A REVIEW_BUY_CANDIDATE is a human-review candidate, not an order.
```

```text
The project is not ready to validate non-demo buy/sell signals because it still lacks accepted PIT universe exports, generated multi-date candidates, real replay decision datasets, forward-return labels, multi-date outcome datasets, validated stock-level profiles, and linked paper outcome history.
```

## Target Operating Model

The strategic target architecture is:

```text
free/local/public data sources
→ raw artifacts and raw document store
→ source registry and permission policy
→ point-in-time available_time governance
→ market/fundamental/event/news/policy/industry caches
→ quality gates and PIT gates
→ factor_definition and factor_observation
→ event_structured and company_exposure
→ historical replay decisions
→ forward_return_label datasets
→ evaluation / training / calibration artifacts
→ model_version and governance
→ stock_profile validation
→ paper workflow
→ real buy-review eligibility only after validation
→ human confirmation only
```

## Current Recommended Next Decision

Recommended next source-level branch:

```text
Historical Replay Substrate Readiness Plan Report-Only v0.1
```

Purpose:

- consume the schema fixture contracts as context only;
- map what must exist before true replay can run;
- define the minimum one-stock/one-ETF replay readiness gates;
- remain report-only and non-active;
- avoid running real replay, computing labels, training weights, creating active stock profiles, changing signal semantics, or creating buy-review eligibility.

## Codex Recommendation Rule

Codex `recommended next task` is a reference, not a command.

Decision priority:

```text
1. Project Source / safety boundaries
2. User's real project goal
3. ChatGPT planning/review/decision judgment
4. Codex recommended next task as reference only
```

## When to Add or Replace Source Documents

Do not update Source after every audit or small implementation.

Add or replace Source when:

- a full milestone/checkpoint/tag is accepted;
- a new artifact workflow lands with index/health/status/research-status;
- current stage or next branch changes;
- artifact governance or safety boundaries change;
- major external data, raw document, event, factor, replay, forward-label, training, stock-profile, alert, broker, or snapshot semantics are introduced;
- the project goal or method stack changes.

## Do Not Use This Pack To

Do not use this pack to:

- justify live trading;
- justify broker integration;
- automate order placement;
- treat taxonomy rows as strategy performance evidence;
- treat historical news as direct buy/sell signal;
- treat schema fixtures as active replay input;
- treat replay decisions as validated performance;
- treat forward labels as allowed before valid replay decisions exist;
- train model weights without PIT-valid observations and labels;
- create real buy-review eligibility without validated stock_profile and paper workflow;
- bypass human confirmation;
- bypass point-in-time checks;
- skip data/snapshot quality;
- commit generated `outputs`, `data/raw`, `data/processed`, or `data/cache` artifacts.
