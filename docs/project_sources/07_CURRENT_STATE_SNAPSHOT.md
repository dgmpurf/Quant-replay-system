# Current State Snapshot

> Status: working memory document  
> Last generated: 2026-06-04  
> Permanence: temporary; refresh after the next major checkpoint or when source state changes.

## Summary

The project is a local quantitative research, signal semantics, advisory, calibration, paper workflow, and multi-date evidence preparation system for China A-share stocks and ETFs.

It is not a live trading system.

## Major Completed Capabilities

### Data and Market Cache

- Optional AKShare and BaoStock market data adapters.
- Local market cache.
- Cache query with source/upstream filters.
- Market source comparison.
- Reviewed cache export and policy-aware export planning.

### Data Quality and Snapshot Quality

- `data-pipeline`.
- `data-quality`.
- `snapshot-quality`.
- Snapshot warning actionability.
- Active snapshot linkage.

### Candidate Generation and Multi-Date Preparation

- `current-candidates`.
- Demo selection profile.
- Current-candidates index/health/status.
- Warmup-aware backfill plan.
- Current-candidates execution manifest.
- PIT overlay plan/template.
- PIT overlay review.
- PIT export-readiness.
- PIT evidence completion helper.
- PIT required metadata support.
- Guarded export staging.
- PIT evidence review worklist.
- PIT evidence update ingestion.
- Universe profile policy audit.
- Universe profile registry and split-worklist planning.
- Reviewed replacement worklist planning.
- Reviewed replacement worklist acceptance.
- Research-status integration for these layers.

### Signal Semantics and Advisory

- Deterministic advisory action labels.
- Shared semantics wired into advisory layers.
- Signal advisory, single-symbol advisory, question-style answer, and local advisory conversation.
- Semantics provenance metadata and visibility.
- No LLM in deterministic advisory logic.

### Paper Workflow

- Current-to-paper and current-to-paper-review.
- WATCH_ONLY workflow.
- Paper daily reviewed decisions.
- Synthetic fill rejection.
- Diagnostic reconciliation scoping.

### Calibration

- Advisory profile calibration analyzer.
- Calibration-to-signal-semantics proposal.
- Research-status integration.
- Current recommendation: keep defaults, do not expand buy review, collect more evidence.

### Factor Taxonomy Sources

- Canonical China A-share factor taxonomy exists.
- Event-driven/industry-chain framework exists.
- These are design sources, not executable signal logic.

## Current Quantitative Evidence Status

Current evidence is not enough to validate non-demo buy signals.

Known gaps:

- too few dates;
- only 9 symbols in local cache;
- demo-only current-candidates;
- no forward-return labels;
- no multi-date outcome dataset;
- no accepted PIT universe export;
- no corporate action adjustment policy validation;
- no linked paper outcome history for signals.

## Current Multi-Date Backfill State

Market/cache feasibility:

```text
local market cache has enough data for selected warmup-aware signal dates
60 trading day warmup modeled
1d/3d/5d/10d forward horizon modeled
```

PIT universe active / planning artifacts:

```text
overlay_plan_id: 38a254c54024
review_id: 7bc8ba08bf5a
export_readiness_id: 75c6975e93e4
helper_id: 4cf008a09f04
staging_id: 41bfd31a9e2c
worklist_id: 1c7972988f59
ingestion_id: 284058e7f1e4
policy_audit_id: 844794b3aae1
split_plan_id: db2c09268c14
replacement_plan_id: 0774d0a1fdb9
acceptance_id: c723c0c476b1
```

Current counts:

```text
selected signal dates: 8
symbols: 9
PIT rows: 72
approved rows: 0
valid-for-signal-date rows: 0
export-ready rows: 0
staged rows: 0
clean ready review updates: 0
needs evidence rows: 72
future-dated hints: 72
authoritative hints: 0

STOCK rows: 56
ETF rows: 16
legacy mixed-demo rows: 72
recommended future stock_core rows: 56
recommended future etf_core rows: 16
recommended future mixed_demo_core rows: 0
profile conflicts: 56

reviewed replacement stock_core rows: 56
reviewed replacement etf_core rows: 16
reviewed replacement mixed_demo_core rows: 0
reviewed replacement acceptance acknowledged: true
active legacy worklist mutated: false
```

Current reviewed replacement worklist acceptance stage:

```text
REVIEWED_REPLACEMENT_WORKLIST_ACCEPTED_AS_PLANNING_CONTEXT
```

Meaning:

The project has moved from “future stock_core and etf_core replacement templates exist as planning artifacts” to “those replacement templates are acknowledged as reviewed planning context.”

Existing `etf_core` artifacts should remain legacy mixed/demo context, not ETF-only context.

Replacement worklist templates and acceptance artifacts exist under `outputs/reports`, but they are not activated active worklists yet.

The next blocker is designing guarded activation. Without an activation design, accepted replacement templates should not be treated as the active evidence review worklist.

## Current External Data Strategy

Budget constraint:

- free-first;
- paid vendors are future backups only.

Current recommendation:

- fundamentals before news sentiment;
- LOCAL_CSV first;
- AKShare / BaoStock / Tushare free/low-quota optional later;
- public announcement metadata later;
- news as event/risk context first, not score driver.

## Recommended Next Branch

```text
Guarded Replacement Worklist Activation Read-only Audit v0.1
```

Purpose:

- inspect how accepted replacement worklists might become activated as the user's evidence review working set;
- define explicit activation flags and manual confirmation requirements;
- preserve lineage from legacy worklist, policy audit, split plan, replacement plan, and acceptance artifact;
- keep active legacy worklist unchanged unless a future activation artifact is explicitly created;
- avoid automatic approval, rejection, export, or candidate generation.

Do not yet:

- activate replacement worklists automatically;
- mutate active worklists;
- approve or reject rows;
- write usable universe files;
- write `data/raw` or `data/processed`;
- generate multi-date candidates;
- build per-date snapshot manifests;
- compute forward returns;
- change non-demo thresholds;
- add news scraping;
- add broker integration;
- send real messages.

## Recent Important Checkpoints

Recent milestone direction:

- v1.0.0: research infrastructure with PIT universe overlay planning/status.
- v1.1.0: reviewed PIT universe overlay approval workflow.
- v1.2.0: PIT universe export-readiness.
- v1.3.0: PIT universe evidence completion helper.
- v1.4.0: PIT universe required metadata support.
- v1.5.0: guarded PIT universe export staging.
- v1.6.0: PIT universe evidence review worklist.
- v1.7.0: PIT universe evidence update ingestion.
- v1.8.0: universe profile policy audit.
- v1.9.0: universe profile split-worklist planning.
- v1.10.0: reviewed replacement worklist planning.
- v1.11.0: reviewed replacement worklist acceptance.

## What to Ask ChatGPT Next

```text
Give me Codex tasks for Guarded Replacement Worklist Activation Read-only Audit v0.1.
```
