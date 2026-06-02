# Current State Snapshot

> Status: working memory document  
> Last generated: 2026-06-02  
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

PIT universe active artifacts:

```text
overlay_plan_id: 38a254c54024
review_id: 7bc8ba08bf5a
export_readiness_id: 75c6975e93e4
helper_id: 4cf008a09f04
staging_id: 41bfd31a9e2c
worklist_id: 1c7972988f59
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
needs evidence rows: 72
future-dated hints: 72
authoritative hints: 0
```

Current active stage:

```text
PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_NEEDS_REVIEW
```

Meaning:

The project has moved from “can staging be guarded?” to “the reviewer now has a worklist for filling real PIT evidence.”

The next blocker is evidence update ingestion. Without a safe ingestion validator for completed worklist rows, reviewer-filled evidence cannot reliably become a clean review-updates artifact.

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
Reviewed PIT Universe Evidence Update Ingestion Read-only Audit v0.1
```

Purpose:

- inspect how reviewer-completed worklist update CSVs should be validated;
- define identity keys and blocker rules;
- design a safe output review-updates artifact;
- avoid automatic approval or universe export.

Do not yet:

- approve rows automatically;
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

## What to Ask ChatGPT Next

```text
Give me Codex tasks for Reviewed PIT Universe Evidence Update Ingestion Read-only Audit v0.1.
```
