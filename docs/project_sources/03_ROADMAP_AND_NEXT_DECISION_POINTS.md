# Roadmap and Next Decision Points

> Status: working memory document  
> Last generated: 2026-05-29  
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
- PIT universe overlay preparation,
- unified `research-status`.

The project is now preparing for true multi-date evidence collection, but it is not yet ready to generate multi-date candidates, compute forward returns, change non-demo thresholds, or produce validated buy/sell signals.

## Immediate Technical State

Completed or largely complete:

- `signal_semantics` unified classifier.
- Signal advisory and single-symbol advisory wired through shared semantics.
- Semantics provenance metadata.
- Advisory profile calibration analyzer.
- Calibration-to-signal-semantics proposal report.
- Warmup-aware current-candidates backfill plan.
- Current-candidates execution manifest.
- PIT universe overlay plan/template.
- Index / health / status for PIT universe overlay plans.
- Research-status integration for most status layers, including PIT universe overlay plan.

Current active preparation state:

```text
PIT_UNIVERSE_OVERLAY_PLAN_NEEDS_REVIEW
```

Latest known PIT overlay plan:

```text
overlay_plan_id: 38a254c54024
rows: 72
signal dates: 8
symbols: 9
needs manual review: 72
valid_for_signal_date: 0
survivorship_bias_warning: 72
```

## Recommended Next Branch

### Branch: Reviewed PIT Universe Overlay Approval Workflow

Suggested sequence:

1. Reviewed PIT Universe Overlay Approval Workflow Read-only Audit.
2. Review template/update schema.
3. Approval command that consumes the template plus review updates.
4. Approved overlay artifact index / health / status.
5. Research-status integration.
6. Checkpoint.
7. Only then consider per-date snapshot preparation.
8. Only then consider current-candidates backfill runner.

Do not skip directly to multi-date candidate generation.

## What Reviewed PIT Approval Must Solve

The approval workflow should answer:

- Which symbols were valid universe members on each historical signal date?
- What evidence supports each symbol/date row?
- Was the evidence available at or before the signal date?
- Is survivorship-bias risk resolved or still flagged?
- Who reviewed the row and when?
- Is the row approved, rejected, or waiting for more evidence?

Suggested approval statuses:

```text
NEEDS_MANUAL_REVIEW
APPROVED_FOR_PIT_UNIVERSE
REJECTED
NEEDS_MORE_EVIDENCE
```

Suggested required evidence fields:

- `listed_date_evidence`
- `delisted_date_evidence`
- `is_active_evidence`
- `evidence_path`
- `evidence_source`
- `reviewer`
- `reviewed_at`
- `review_reason`
- `survivorship_bias_resolved`

## After Reviewed PIT Universe Approval

Next likely branches:

### 1. Per-Date Snapshot Manifest Preparation

Need to prepare or verify, per signal date:

- market dataset,
- reviewed PIT universe dataset,
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

Start after the current multi-date evidence path is stable enough that the project can benefit from fundamentals.

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
- run current-candidates backfill without reviewed PIT universe rows,
- compute forward returns without multi-date candidates,
- change `signal_semantics` defaults based on synthetic fixtures,
- turn `REVIEW_BUY_CANDIDATE` into orders,
- send real alerts,
- add broker integration.
