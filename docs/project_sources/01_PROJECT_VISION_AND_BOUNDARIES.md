# Project Vision and Boundaries

> Status: working memory document  
> Last generated: 2026-05-28  
> Permanence: temporary; refresh after major roadmap or safety-boundary changes.

## Product North Star

`quant-replay-system` is a quantitative research and signal advisory system first.

The near-term product is not an automatic trading robot. The default path is:

```text
local data
→ research artifacts
→ signal semantics
→ advisory signals
→ human confirmation
→ reviewed paper workflow
```

The long-term product may eventually support full automation, but only after the data, signal, review, risk, reconciliation, and audit layers are mature.

## What the System Should Eventually Do

The system should help answer:

- What should I watch?
- What might be a buy-review candidate?
- What might be a sell-review candidate?
- Why does the signal exist?
- What data supports it?
- What risks oppose it?
- When is it valid?
- What invalidates it?
- Is manual confirmation required?
- Was the data available at that time?

The system should support both batch advisory workflows and single-symbol questions such as:

```text
000001 现在能不能买？
Should I sell 510300?
```

But these question-style workflows are only product-layer entry points. The project’s core remains quantitative data, quality gates, scoring, signal semantics, and auditable advisory artifacts.

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

### Stage 5: Multi-Date Evidence and Non-Demo Calibration

Currently beginning:

- Warmup-aware current-candidates backfill planning.
- Execution readiness manifests.
- Blocker discovered: point-in-time universe as-of validity.
- Future: multi-date candidate generation, forward-return labels, signal outcome datasets, backtest/paper evidence.

### Stage 6: External Data Expansion

Future:

- Fundamental data schema.
- Fundamental LOCAL_CSV ingestion.
- Free/low-cost optional sources.
- Announcement/event metadata.
- News/event context.
- Later, paid data vendor adapters if budget allows.

### Stage 7: Alert Delivery

Future:

- Local alert delivery preview.
- Only later: email/SMS/Telegram/WeChat or webhook delivery.
- All delivery must have dry-run, logging, safety flags, and manual confirmation controls.

### Stage 8: Semi-Automation and Full Automation

Much later:

- Broker integration.
- Account state.
- Order placement.
- Real fills.
- Execution risk controls.
- Operational monitoring.
- Explicit user approval and separate safety design required.

### Stage 9: International Market Expansion

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

## Full Automation Meaning

Full automation is the complete future version, not the current development baseline.

A fully automated version would require:

- validated non-demo signal profiles,
- multi-date evidence,
- forward-return labels,
- backtest and paper performance evidence,
- fill reconciliation,
- risk controls,
- broker integration,
- alert/action audit logs,
- kill switches,
- user approval for operational mode.

Until then, automation is allowed for data collection, quality checks, local reports, and advisory artifacts, not for orders.
