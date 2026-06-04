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
- guarded reviewed replacement worklist activation;
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
- guarded reviewed replacement worklist activation;
- index / health / status and research-status integration for these stages.

Current reviewed replacement worklist activation state:

```text
REVIEWED_REPLACEMENT_WORKLIST_ACTIVATED_AS_PLANNING_CONTEXT
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
activation_id: a8e74161f9bb

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
activation planning context created: true
```

A synthetic diagnostic fixture proved that a complete reviewed row with all required current-candidates universe metadata can become `export_ready=true`, but real active artifacts remain blocked because there are no real approved rows.

## Recommended Next Branch

### Branch: Activated Replacement Worklist Evidence Update Planning

Suggested sequence:

1. Read-only audit for activated replacement worklist evidence update planning.
2. Define how activated stock_core and etf_core templates should be used for manual PIT evidence work.
3. Decide whether to generate profile-specific evidence work packages, diagnostics-only templates, or both.
4. Keep current active legacy `etf_core` worklist unchanged.
5. Do not approve/reject rows.
6. Do not export universe files.
7. Do not run current-candidates or snapshot workflows.
8. If implementation proceeds later, add index / health / status and research-status integration.
9. Checkpoint.

Do not skip directly to accepted universe export or multi-date candidate generation.

## What Activated Replacement Evidence Planning Must Solve

It should answer:

- Should future evidence update work start from the activated stock_core and etf_core templates rather than the legacy `etf_core` worklist?
- What fields should profile-specific update templates preserve?
- How should activated templates preserve lineage to legacy worklist, policy audit, split plan, replacement plan, acceptance, and activation artifacts?
- Should stock_core and etf_core evidence update planning happen separately?
- Should the system generate first-batch evidence packs per profile?
- How should research-status distinguish activated planning context from actual clean review updates?
- How should the system prevent activated templates from being treated as approved PIT rows or current-candidates universe input?

## After Activated Replacement Evidence Planning

### 1. Real Evidence Completion on Correct Profile

Use activated replacement worklist templates to fill real evidence for the appropriate profile:

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
- treat reviewed replacement activation as PIT row approval or usable universe input;
- export PIT universe input without real approved/export-ready rows;
- write `data/raw` or `data/processed` from PIT staging;
- run current-candidates backfill without reviewed/exported PIT universe rows;
- compute forward returns without multi-date candidates;
- change `signal_semantics` defaults based on synthetic fixtures;
- turn `REVIEW_BUY_CANDIDATE` into orders;
- send real alerts;
- add broker integration.
