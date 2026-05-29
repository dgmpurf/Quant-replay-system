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
- reviewed PIT universe overlay approval workflow,
- unified `research-status`.

The project is preparing for true multi-date evidence collection, but it is not yet ready to generate multi-date candidates, compute forward returns, change non-demo thresholds, or produce validated buy/sell signals.

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
- PIT universe overlay review/approval workflow.
- Index / health / status for PIT universe overlay review artifacts.
- Research-status integration for most status layers, including PIT universe overlay review.

Current active preparation state:

```text
PIT_UNIVERSE_OVERLAY_REVIEW_NEEDS_MORE_EVIDENCE
```

Latest known PIT overlay review:

```text
review_id: 7bc8ba08bf5a
rows: 72
approved rows: 0
valid_for_signal_date rows: 0
needs manual review rows: 72
unresolved survivorship warnings: 72
```

## Recommended Next Branch

### Branch: Reviewed PIT Universe Overlay Export Readiness

Suggested sequence:

1. Reviewed PIT Universe Overlay Export Readiness Read-only Audit.
2. Export readiness planning/status command if audit supports it.
3. Index / health / status for export readiness artifacts.
4. Research-status integration.
5. Checkpoint.
6. Only after approved rows exist, consider a guarded export workflow.
7. Only after exported PIT universe inputs exist, consider per-date snapshot preparation.
8. Only after per-date snapshots pass quality gates, consider current-candidates backfill runner.

Do not skip directly to multi-date candidate generation.

## What Export Readiness Must Solve

The export readiness workflow should answer:

- Are there any `APPROVED_FOR_PIT_UNIVERSE` rows?
- Are approved rows `valid_for_signal_date=true`?
- Are evidence fields complete?
- Are survivorship-bias warnings resolved for approved rows?
- Are required current-candidates universe columns present?
- Should export be blocked, partially ready, or ready?
- Should output be per-signal-date, combined, or both?
- Should any write to `data/raw` require an explicit accept flag?

Current expected result:

```text
export readiness should be BLOCKED because approved_count=0
```

## After Export Readiness

Next likely branches:

### 1. PIT Universe Evidence Completion Helper

If there are no approved rows, the project may need helper workflows for reviewer-supplied evidence, not export.

Potential fields:

- `listed_date_evidence`
- `delisted_date_evidence`
- `is_active_evidence`
- `evidence_source`
- `evidence_path`
- `evidence_reference`
- `reviewer`
- `reviewed_at`
- `review_reason`
- `survivorship_bias_resolved`

### 2. Guarded PIT Universe Export

Only after approved rows exist.

Scope should remain:

- no current-candidates generation,
- no snapshot build,
- no forward returns,
- no messages,
- no broker,
- no cache mutation.

### 3. Per-Date Snapshot Manifest Preparation

Need to prepare or verify, per signal date:

- market dataset,
- reviewed PIT universe dataset,
- trading calendar,
- snapshot manifest,
- snapshot-quality status.

### 4. Current-Candidates Backfill Runner

Should consume a reviewed healthy plan/manifest and produce candidate artifacts for selected dates.

Scope should remain:

- no forward returns,
- no execution,
- no messages,
- no broker,
- no cache mutation.

### 5. Forward Return Label Dataset

Only after multi-date candidates exist.

Potential labels:

- forward_return_1d,
- forward_return_3d,
- forward_return_5d,
- forward_return_10d,
- max_drawdown_after_signal,
- benchmark-relative return,
- hit/miss labels.

### 6. Historical Signal Outcome Dataset

Combine:

- signal_date,
- symbol,
- scores,
- semantics_action,
- risk gates,
- quality status,
- forward outcomes.

### 7. Non-Demo Semantics Calibration

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
- export PIT universe input without approved rows,
- run current-candidates backfill without reviewed/exported PIT universe rows,
- compute forward returns without multi-date candidates,
- change `signal_semantics` defaults based on synthetic fixtures,
- turn `REVIEW_BUY_CANDIDATE` into orders,
- send real alerts,
- add broker integration.
