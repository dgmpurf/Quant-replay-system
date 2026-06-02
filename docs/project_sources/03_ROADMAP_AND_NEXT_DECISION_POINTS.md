# Roadmap and Next Decision Points

> Status: working memory document  
> Last generated: 2026-06-02  
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
- PIT universe export-readiness,
- PIT universe evidence completion helper,
- guarded PIT universe export staging,
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
- PIT universe export-readiness.
- PIT universe evidence completion helper.
- PIT universe required metadata support.
- Guarded PIT universe export staging.
- Index / health / status for export staging artifacts.
- Research-status integration for most status layers, including export staging.

Current active preparation state:

```text
PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS
```

Latest known PIT universe state:

```text
review_id: 7bc8ba08bf5a
export_readiness_id: 75c6975e93e4
helper_id: 4cf008a09f04
staging_id: 41bfd31a9e2c
approved rows: 0
export-ready rows: 0
staged rows: 0
blocked rows: 72
```

A synthetic diagnostic fixture proved that a complete reviewed row with all required current-candidates universe metadata can become `export_ready=true` in a readiness artifact, but real active artifacts remain blocked because there are no real approved rows.

## Recommended Next Branch

### Branch: PIT Universe Evidence Review Worklist / Real Evidence Completion Plan

Suggested sequence:

1. Read-only audit for real evidence completion workflow.
2. Define reviewer worklist schema and evidence source policy.
3. Build a local worklist/template that helps fill real evidence fields.
4. Keep base-universe hints as `suggested_*` and non-authoritative.
5. Do not auto-approve rows.
6. Do not export universe files.
7. After real evidence rows are filled, rerun review → export-readiness → staging.
8. Only after real export-ready rows exist, consider accepted export design.

Do not skip directly to accepted universe export or multi-date candidate generation.

## What Real Evidence Completion Must Solve

It should help answer:

- Which symbol/date/universe rows can be supported by evidence available at or before the signal date?
- What listed-date / delisted-date evidence exists?
- What active/ST/suspension evidence exists?
- What evidence source and path/reference supports the review?
- Who reviewed it and when?
- Is survivorship-bias risk resolved?
- Are required current-candidates universe metadata fields supplied by the reviewer rather than inferred from future-dated hints?

Relevant fields include:

- `reviewer`
- `reviewed_at`
- `review_reason`
- `evidence_source`
- `evidence_path`
- `evidence_reference`
- `listed_date_evidence`
- `delisted_date_evidence`
- `is_active_evidence`
- `survivorship_bias_resolved`
- `as_of_date`
- `available_time`
- `name`
- `instrument_type`
- `exchange`
- `industry`
- `min_lot`
- `t_plus_rule`
- `revision_id`
- `source`

## After Real Evidence Completion

Next likely branches:

### 1. Rerun Review / Export-Readiness / Staging

Use real reviewer-supplied evidence updates to rerun:

```text
pit-universe-overlay-review
→ pit-universe-overlay-export-readiness
→ pit-universe-export-staging
```

Expected safe outcomes:

- no rows approved if evidence remains incomplete;
- export readiness blocked until all gates pass;
- staging blocked until export-ready rows exist;
- no `data/raw` / `data/processed` write.

### 2. Accepted PIT Universe Export Workflow

Only after real export-ready rows exist.

Scope should remain:

- explicit accept flag required;
- dry-run first;
- no current-candidates generation;
- no snapshot build;
- no forward labels;
- no messages;
- no broker;
- no cache mutation.

### 3. Per-Date Snapshot Manifest Preparation

Only after accepted PIT universe inputs exist.

Need to prepare or verify, per signal date:

- market dataset,
- reviewed/exported PIT universe dataset,
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
- treat suggested base-universe hints as authoritative PIT evidence,
- export PIT universe input without real approved/export-ready rows,
- write `data/raw` or `data/processed` from PIT staging,
- run current-candidates backfill without reviewed/exported PIT universe rows,
- compute forward returns without multi-date candidates,
- change `signal_semantics` defaults based on synthetic fixtures,
- turn `REVIEW_BUY_CANDIDATE` into orders,
- send real alerts,
- add broker integration.
