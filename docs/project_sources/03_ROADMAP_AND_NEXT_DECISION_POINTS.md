# Roadmap and Next Decision Points

> Status: working memory document  
> Last generated: 2026-06-04  
> Permanence: temporary; update after each major checkpoint.

## Current Position

The project is now a broad local research system with:

- source comparison and market cache;
- reviewed exports and quality gates;
- current-candidates and signal semantics;
- advisory products and paper workflow;
- calibration tooling;
- multi-date backfill planning;
- PIT universe overlay preparation;
- reviewed PIT universe approval workflow;
- export-readiness;
- evidence completion helper;
- required metadata support;
- guarded export staging;
- evidence review worklist;
- evidence update ingestion;
- universe profile policy audit;
- universe profile split-worklist planning;
- reviewed replacement worklist planning;
- reviewed replacement worklist acceptance;
- unified `research-status`.

The project is preparing for true multi-date evidence collection, but it is not ready to generate multi-date candidates, compute forward returns, change non-demo thresholds, or produce validated buy/sell signals.

## Immediate Technical State

Completed or largely complete:

- shared `signal_semantics`;
- advisory and single-symbol products;
- calibration and proposal reporting;
- warmup-aware current-candidates backfill plan;
- current-candidates execution manifest;
- PIT universe overlay plan/template;
- PIT universe overlay review/approval workflow;
- PIT universe export-readiness;
- evidence completion helper;
- required PIT universe metadata support;
- guarded export staging;
- evidence review worklist;
- evidence update ingestion validator;
- universe profile policy audit;
- universe profile registry and split-worklist plan;
- reviewed replacement worklist plan;
- reviewed replacement worklist acceptance;
- index / health / status and research-status integration for these stages.

Current reviewed replacement worklist acceptance state:

```text
REVIEWED_REPLACEMENT_WORKLIST_ACCEPTED_AS_PLANNING_CONTEXT
```

Latest known state:

```text
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

approved rows: 0
export-ready rows: 0
staged rows: 0
clean ready review updates: 0
worklist rows: 72
needs evidence rows: 72
future-dated hints: 72
authoritative hints: 0
STOCK rows: 56
ETF rows: 16
legacy mixed-demo rows: 72
profile conflicts: 56
stock_core replacement rows: 56
etf_core replacement rows: 16
mixed_demo_core replacement rows: 0
active legacy worklist mutated: false
acceptance acknowledged: true
```

A synthetic diagnostic fixture proved that a complete reviewed row with all required current-candidates universe metadata can become `export_ready=true`, but real active artifacts remain blocked because there are no real approved rows.

## Recommended Next Branch

### Branch: Guarded Replacement Worklist Activation

Suggested sequence:

1. Read-only audit for guarded replacement worklist activation.
2. Define what “activating” replacement worklists means.
3. Decide whether activation should create a new active worklist artifact, a routing pointer, or only an accepted planning context.
4. Require explicit activation flags and manual confirmation before any activated artifact exists.
5. Keep current active legacy `etf_core` worklist unchanged unless a future workflow explicitly creates a separate activated artifact.
6. Do not approve/reject rows.
7. Do not export universe files.
8. Do not run current-candidates or snapshot workflows.
9. If implementation proceeds later, add index / health / status and research-status integration.
10. Checkpoint.

Do not skip directly to accepted universe export or multi-date candidate generation.

## What Replacement Worklist Activation Must Solve

It should answer:

- Should accepted replacement worklists ever become active evidence worklists?
- What exact manual activation flag is required?
- Does activation create an active artifact, or only a routing pointer?
- How should activated replacement artifacts preserve lineage to the legacy worklist, policy audit, split plan, replacement plan, and acceptance artifact?
- How should research-status distinguish planned replacement worklists, accepted replacement worklists, and activated replacement worklists?
- How should stock_core and etf_core activated templates remain non-approved and evidence-incomplete until separately reviewed?
- How should the system prevent accidental mutation of the legacy worklist?
- How should the system prevent replacement templates from being treated as current-candidates universe input?

## After Replacement Worklist Activation Design

### 1. Real Evidence Completion on Correct Profile

Use activated or accepted replacement worklist templates to fill real evidence for the appropriate profile:

```text
stock_core for STOCK symbols
etf_core for ETF symbols
mixed_demo_core only for demo/mixed work
```

### 2. Evidence Update Ingestion

Use reviewer-supplied completed update CSVs to run:

```text
pit-universe-evidence-update-ingestion
```

Expected safe outcomes:

- no rows ready if evidence remains incomplete;
- ready clean review updates only when reviewer fields, PIT dates, metadata, and evidence pass validation;
- no approval applied automatically.

### 3. Rerun Review / Export-Readiness / Staging

Only with validated real review updates:

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

### 4. Accepted PIT Universe Export Workflow

Only after real export-ready rows exist.

Scope should remain:

- explicit accept flag required;
- dry-run first;
- no current-candidates generation;
- no snapshot build;
- no forward returns;
- no messages;
- no broker;
- no cache mutation.

### 5. Per-Date Snapshot Manifest Preparation

Only after accepted PIT universe inputs exist.

Need to prepare or verify:

- market dataset;
- reviewed/exported PIT universe dataset;
- trading calendar;
- snapshot manifest;
- snapshot-quality status.

### 6. Current-Candidates Backfill Runner

Only after reviewed healthy plan/manifest and accepted PIT universe input exist.

Scope should remain:

- no forward returns;
- no execution;
- no messages;
- no broker;
- no cache mutation.

### 7. Forward Return Label Dataset

Only after multi-date candidates exist.

## External Data Roadmap

Use free-first strategy:

1. Fundamental Data Strategy and Schema.
2. Fundamental LOCAL_CSV ingestion.
3. Fundamental quality gate.
4. Optional AKShare/BaoStock/free Tushare.
5. Announcement/event LOCAL_CSV.
6. Public announcement metadata.
7. News/event risk context.
8. Paid vendors later.

Fundamental data should come before news sentiment.

## Current Do Not Do Yet List

Do not yet:

- use paid APIs as required dependencies;
- parse all news with LLM;
- treat suggested base-universe hints as authoritative PIT evidence;
- treat worklist rows as reviewed evidence;
- treat evidence update ingestion as approval application;
- treat universe profile split guidance as active worklist replacement;
- treat reviewed replacement worklist plans as accepted active replacement worklists;
- treat reviewed replacement acceptance as activation;
- export PIT universe input without real approved/export-ready rows;
- write `data/raw` or `data/processed` from PIT staging;
- run current-candidates backfill without reviewed/exported PIT universe rows;
- compute forward returns without multi-date candidates;
- change `signal_semantics` defaults based on synthetic fixtures;
- turn `REVIEW_BUY_CANDIDATE` into orders;
- send real alerts;
- add broker integration.
