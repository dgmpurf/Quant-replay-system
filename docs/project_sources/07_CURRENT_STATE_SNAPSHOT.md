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
- Guarded reviewed replacement worklist activation.
- Activated replacement worklist evidence update planning.
- PIT evidence checklist validator.
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
review_id: 7bc8ba08bf5a
export_readiness_id: 75c6975e93e4
helper_id: 4cf008a09f04
staging_id: 41bfd31a9e2c
legacy_worklist_id: 1c7972988f59
ingestion_id: 284058e7f1e4
policy_audit_id: 844794b3aae1
split_plan_id: db2c09268c14
replacement_plan_id: 0774d0a1fdb9
acceptance_id: c723c0c476b1
activation_id: a8e74161f9bb
evidence_update_plan_id: 4e268d67bd7d
latest_diagnostics_ingestion_id: 734f3a722ddf
validator_id: 62e9eb747197
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
reviewed replacement activation planning context created: true
active legacy worklist mutated: false

activated evidence update planning:
stock_core evidence rows: 56
etf_core evidence rows: 16
mixed_demo_core evidence rows: 0
stock_core first batch rows: 8
etf_core first batch rows: 8
clean_review_updates_created: false

Codex diagnostics evidence discovery / gap closure:
inspected rows: 16
ingestion ready_for_review_update_count: 16
ingestion blocked_count: 0
approval_requested_count: 0
approved_ready_count: 0
all rows remain NEEDS_MORE_EVIDENCE

PIT evidence checklist validator:
validator_id: 62e9eb747197
row_count: 16
checklist_pass_count: 0
blocked_count: 16
stock_core_blocked_count: 8
etf_core_blocked_count: 8
```

Current PIT evidence checklist validation stage:

```text
PIT_EVIDENCE_CHECKLIST_VALIDATION_BLOCKED
```

Meaning:

The project has moved from “profile-specific evidence update packages exist” to “strict evidence checklist validation now blocks all current first-batch rows.”

The 16 diagnostics rows can pass evidence ingestion as `NEEDS_MORE_EVIDENCE`, but no row currently satisfies the strict PIT evidence checklist. There are no approval candidates.

Existing `etf_core` artifacts should remain legacy mixed/demo context, not ETF-only context.

The next blocker is Codex-driven acquisition of official/public evidence for the exact checklist blockers: active/not-delisted status, ST/no-ST status for stock rows, survivorship-bias resolution, and PIT-safe timing.

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
Codex-Driven Official Evidence Acquisition for Checklist Blockers v0.1
```

Purpose:

- use Codex to target the exact blockers from `pit-evidence-checklist-validator`;
- inspect local artifacts first;
- use browser/web/plugin access only for light official/public evidence discovery;
- gather official source evidence for active/not-delisted, ST/no-ST, suspension, survivorship, and PIT-safe timing;
- update draft completed CSVs only when real evidence exists;
- rerun diagnostics-only ingestion and checklist validation;
- avoid automatic approval, rejection, export, or candidate generation.

Do not yet:

- approve or reject rows;
- run PIT overlay review;
- run export-readiness;
- run staging;
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
- v1.12.0: guarded reviewed replacement worklist activation.
- v1.13.0: activated replacement worklist evidence update planning.
- v1.14.0: PIT evidence checklist validator.

## What to Ask ChatGPT Next

```text
Give me Codex tasks for Codex-Driven Official Evidence Acquisition for Checklist Blockers v0.1.
```
