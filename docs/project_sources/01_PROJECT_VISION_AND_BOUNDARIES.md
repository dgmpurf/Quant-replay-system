# Project Vision and Boundaries

> Status: working memory document  
> Last generated: 2026-06-11  
> Permanence: temporary; refresh after major roadmap, product-goal, training-core, or safety-boundary changes.

## Product North Star

`quant-replay-system` is a personal-first, institution-grade-core quantitative research, historical replay training, and signal advisory system for China A-share stocks and ETFs.

The first usable product is not an automatic trading robot. It is a local personal/family advisory workflow:

```text
local/free/public data
→ reviewed research artifacts
→ point-in-time valid factor/event observations
→ historical replay and forward-return evaluation
→ signal semantics
→ advisory signals
→ human confirmation
→ reviewed paper workflow
→ only later, real buy-review eligibility for validated stocks
```

The long-term research core must support institution-grade standards:

- point-in-time data validity;
- historical document and market replay;
- expandable factor universe;
- 8-layer factor taxonomy as the primary skeleton;
- stock-level profiles and validation status;
- forward-return labels and outcome datasets;
- model/weight/threshold calibration with audit trails;
- paper workflow validation before real buy-review;
- strict governance over data legality, provenance, survivorship, and overfitting.

## What the System Should Eventually Do

The system should help answer:

- What should I watch today?
- What might be a buy-review candidate?
- What might be a sell-review candidate?
- Why does the signal exist?
- Which factor layers support it?
- Which historical cases look similar?
- What data supports it?
- Was the supporting data available at the decision time?
- What risks oppose it?
- What invalidates it?
- Is manual confirmation required?
- Has this stock profile passed historical replay validation?
- Has this stock profile passed paper workflow validation?

The system should support both batch advisory workflows and single-symbol questions such as:

```text
000001 现在能不能买？
Should I sell 510300?
```

These question-style workflows are product-layer entry points. The core remains data, PIT contracts, factor/event observations, replay, labels, evaluation, signal semantics, risk gates, and auditable advisory artifacts.

## Historical Replay Training Is Core

The core training loop is:

```text
For each historical decision date T:
  use only data available at or before T;
  construct the valid universe for T;
  compute factor observations for each symbol at T;
  structure announcements/news/events available by T;
  generate deterministic review-only advisory labels;
  record the replay decision and all evidence;
  compute future return/drawdown labels after T;
  evaluate accuracy, payoff, drawdown, false positives, false negatives, and benchmark-relative performance;
  update candidate weights, thresholds, horizons, market-regime rules, and risk vetoes only through versioned training artifacts.
```

This makes the project a replay training system, not just a technical-indicator backtester.

## Factor Universe Principle

Do not treat fixed 12 factors as final.

Use:

```text
8-layer taxonomy = primary database/model skeleton.
12-factor framework = coverage checklist and explanation aid.
Factor universe = expandable set of validated factors/events/observations.
```

Future factor coverage can include hundreds or thousands of factors, as long as each factor has source, availability, legality, lag, confidence, impact path, affected entity mapping, backtestability, and trade-usage metadata.

## Stock-Level Validation Principle

A stock should not enter real buy-review eligibility merely because one current signal looks strong.

The target is a validated `stock_profile`:

```text
base market model
+ industry/sector model
+ stock-specific calibration
+ PIT data coverage
+ historical replay decisions
+ forward-return labels
+ error analysis
+ paper workflow evidence
→ stock_profile validation status
```

A stock profile should record:

- symbol and instrument type;
- industry, sector, product, region, value-chain, and style exposures;
- factor sensitivities;
- useful and non-useful factors for that stock;
- valid/invalid signal regimes;
- risk veto rules;
- training window and out-of-sample window;
- benchmark comparisons;
- paper workflow history;
- current eligibility status.

## Real Buy-Review Eligibility Ladder

Use this conceptual ladder. It is not yet fully implemented.

```text
UNTRAINED_OR_UNVALIDATED:
  only WATCH / NO_ACTION / BLOCKED allowed.

PIT_REPLAY_READY:
  historical replay can be run, but no real buy-review eligibility.

HISTORICAL_REPLAY_VALIDATED:
  can produce paper-only REVIEW_BUY_CANDIDATE under strict semantics.

PAPER_VALIDATED:
  can produce REAL_BUY_REVIEW_CANDIDATE for human review.

HUMAN_CONFIRMED:
  user may manually place an order outside the system.
```

Even at the final stage, the system does not place orders.

## Stage Map

### Stage 1: Local Research and Data Quality Foundation

Completed or mostly established:

- Local data ingestion and processed snapshots.
- Market data cache.
- Source comparison and source policy.
- Data-quality and snapshot-quality gates.
- Point-in-time contracts.

### Stage 2: Candidate Generation and Signal Semantics

Completed or in progress:

- Current/as-of-date candidate generation.
- Demo selection profile for workflow validation.
- Deterministic signal semantics labels:
  - `DEMO_ONLY`
  - `WATCH`
  - `REVIEW_BUY_CANDIDATE`
  - `REVIEW_SELL_CANDIDATE`
  - `HOLD_REVIEW`
  - `NO_ACTION`
  - `BLOCKED`
- Advisory profile calibration and calibration-to-semantics proposal reports.

### Stage 3: Signal Advisory and Human-Confirmed Execution Assistance

Completed or in progress:

- Signal advisory artifacts.
- Single-symbol advisory.
- Question-style single-symbol answers.
- Local-only advisory conversation facade.
- Unified `research-status` context for advisory layers.
- No real message delivery yet.

### Stage 4: Paper Workflow and Reconciliation Validation

Completed or in progress:

- Current-to-paper handoff.
- Current-to-paper-review handoff.
- WATCH_ONLY paper workflow.
- Paper-daily reviewed decisions.
- Synthetic fill rejection diagnostics.
- Diagnostic vs active reconciliation artifact scoping.

### Stage 5: Multi-Date PIT Evidence Foundation

Currently active / in progress:

- Warmup-aware current-candidates backfill planning.
- Execution readiness manifests.
- Point-in-time universe validity blocker discovery.
- PIT universe evidence worklists, policy profiles, evidence packets, material guidance, one-row package, and one-row checklist-pass candidate preview.

Purpose:

```text
Prepare the valid historical universe foundation required for replay training.
```

This stage is necessary but not the final product.

### Stage 6: Historical Replay Training Substrate

Next major direction:

- `factor_definition` schema.
- `factor_observation` schema.
- `raw_document_store` and document metadata schema.
- `event_structured` schema.
- `company_exposure` schema.
- `replay_decision` schema.
- `forward_return_label` schema.
- `training_result` schema.
- `stock_profile` schema.

### Stage 7: External Data Expansion

Future:

- Fundamental data schema.
- Fundamental LOCAL_CSV ingestion.
- Free/low-cost optional sources.
- Announcement/event metadata.
- News/event context.
- Later, paid data vendor adapters if budget allows.

### Stage 8: Stock-Level Training and Paper Validation

Future:

- Validated historical replay runs.
- Forward-return labels.
- Factor/weight/threshold calibration.
- Out-of-sample validation.
- Stock-level profiles.
- Paper workflow evaluation before any real buy-review eligibility.

### Stage 9: Alert Delivery

Future:

- Local alert delivery preview.
- Only later: email/SMS/Telegram/WeChat or webhook delivery.
- All delivery must have dry-run, logging, safety flags, and manual confirmation controls.

### Stage 10: Semi-Automation and Full Automation

Much later:

- Broker integration.
- Account state.
- Order placement.
- Real fills.
- Execution risk controls.
- Operational monitoring.
- Explicit user approval and separate safety design required.

### Stage 11: International Market Expansion

Much later:

- Separate symbol model.
- Calendars.
- Data contracts.
- Source policies.
- Tax/trading rules.
- Quality gates.

## Hard Safety Boundaries

These are current project defaults:

- No live trading.
- No broker API.
- No automated order placement.
- No `APPROVED_FOR_PAPER` unless explicitly and manually tested.
- No real message delivery.
- No LLM/API calls for deterministic advisory logic.
- No scheduler/cron/GitHub Actions automation unless explicitly requested.
- No cache mutation except under explicit cache-write commands.
- No generated `data/raw`, `data/processed`, `data/cache`, or `outputs` committed to Git.
- Demo artifacts are workflow validation only, not strategy recommendations.
- `REVIEW_BUY_CANDIDATE` means human-review candidate, not buy instruction.
- Historical replay performance is not real-trading validation until it is PIT-valid, out-of-sample-tested, benchmarked, and paper-validated.
- A trained model or stock profile must not place orders.

## Full Automation Meaning

Full automation is the complete future version, not the current development baseline.

A fully automated version would require:

- validated non-demo signal profiles;
- multi-date PIT evidence;
- historical replay evidence;
- forward-return labels;
- backtest and paper performance evidence;
- stock-level profile validation;
- fill reconciliation;
- risk controls;
- broker integration;
- alert/action audit logs;
- kill switches;
- explicit user approval for operational mode.

Until then, automation is allowed for data collection, quality checks, local reports, replay artifacts, training reports, and advisory artifacts, not for orders.
