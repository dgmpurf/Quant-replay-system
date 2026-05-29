# Roadmap and Next Decision Points

> Status: working memory document  
> Last generated: 2026-05-28  
> Permanence: temporary; update after each major checkpoint.

## Current Position

The project has progressed from local mock data and replay scaffolding into a broad local research system with:

- source comparison,
- market cache,
- reviewed exports,
- candidate generation,
- signal semantics,
- advisory products,
- paper workflow,
- calibration tooling,
- multi-date backfill planning,
- unified `research-status`.

The project is now preparing for true multi-date evidence collection. It is not yet ready to change non-demo thresholds or produce validated buy/sell signals.

## Immediate Technical State

Completed or largely complete:

- `signal_semantics` unified classifier.
- Signal advisory and single-symbol advisory wired through shared semantics.
- Semantics provenance metadata.
- Advisory profile calibration analyzer.
- Calibration-to-signal-semantics proposal report.
- Warmup-aware current-candidates backfill plan.
- Current-candidates execution manifest.
- Research-status integration for most status layers.

Known current blocker:

```text
BLOCKED_UNIVERSE_AS_OF
```

The selected multi-date signal dates require point-in-time valid universe inputs. The existing universe artifact is dated 2024-05-20, which is too late for earlier dates.

## Recommended Next Branch

### Branch: Point-in-Time Universe and Snapshot Preparation

Suggested sequence:

1. Point-in-Time Universe and Snapshot Preparation Read-only Audit.
2. PIT Universe Overlay Plan v0.1.
3. PIT Universe Overlay Plan Index / Health / Status.
4. Research-status integration.
5. Checkpoint.
6. Only then consider per-date snapshot preparation.
7. Only then consider current-candidates backfill runner.

Do not skip directly to multi-date candidate generation.

## After PIT Universe Is Solved

Next likely branches:

### 1. Per-Date Snapshot Manifest Preparation

Need to produce or verify, per signal date:

- market dataset,
- universe dataset,
- trading calendar,
- snapshot manifest,
- snapshot-quality status.

### 2. Current-Candidates Backfill Runner

Should consume a reviewed healthy plan/manifest and produce candidate artifacts for selected dates.

Scope should remain:

- no forward returns,
- no execution,
- no messages,
- no broker,
- no cache mutation.

### 3. Forward Return Label Dataset

Only after multi-date candidates exist.

Potential labels:

- forward_return_1d,
- forward_return_3d,
- forward_return_5d,
- forward_return_10d,
- max_drawdown_after_signal,
- benchmark-relative return,
- hit/miss labels.

### 4. Historical Signal Outcome Dataset

Combine:

- signal_date,
- symbol,
- scores,
- semantics_action,
- risk gates,
- quality status,
- forward outcomes.

### 5. Non-Demo Semantics Calibration

Only after enough multi-date evidence.

Likely early direction:

- keep buy-review conservative,
- expand WATCH before buy-review,
- require quality gates,
- require risk gates,
- require liquidity gates,
- use paper/backtest evidence before threshold changes.

## External Data Roadmap

The project should use a free-first strategy.

Recommended order:

1. Fundamental Data Strategy and Schema.
2. Fundamental LOCAL_CSV ingestion.
3. Fundamental quality gate.
4. Free/low-cost optional adapters:
   - AKShare,
   - BaoStock,
   - Tushare free/low-quota if available.
5. Announcement/event LOCAL_CSV.
6. Public announcement metadata.
7. News/event risk context.
8. Paid vendors only later.

Fundamental data should come before news sentiment.

## When to Add News and Financial Reports

### Financial Reports

Start after the current calibration/multi-date plan work is stable.

First step should be schema, not API implementation.

Core fields:

- symbol,
- report_period,
- announcement_date,
- available_time,
- revenue,
- net_profit,
- ROE,
- gross_margin,
- debt ratio,
- operating cash flow,
- source,
- revision_id.

### News and Events

Start later than fundamentals.

First role:

- event context,
- risk notes,
- human-review context.

Not first role:

- direct buy/sell scoring.

## Medium-Term Decision Points

### Decision: When to change signal semantics defaults?

Do not change until:

- multiple signal dates exist,
- forward outcomes exist,
- quality gates are proven,
- risk gates are proven,
- synthetic-only evidence is replaced with real local evidence.

### Decision: When to enable real message delivery?

Do not enable until:

- alert preview format is stable,
- delivery adapter has dry-run mode,
- no secrets are printed,
- manual confirmation remains explicit,
- delivery does not change trading state.

### Decision: When to add broker integration?

Much later.

Prerequisites:

- non-demo signal evidence,
- paper workflow maturity,
- approved synthetic fills,
- reconciliation confidence,
- risk controls,
- explicit user approval.

## Current “Do Not Do Yet” List

Do not yet:

- use paid APIs as required dependencies,
- parse all news with LLM,
- run current-candidates backfill without PIT universe,
- compute forward returns without multi-date candidates,
- change signal_semantics defaults based on synthetic fixtures,
- turn `REVIEW_BUY_CANDIDATE` into orders,
- send real alerts,
- add broker integration.
