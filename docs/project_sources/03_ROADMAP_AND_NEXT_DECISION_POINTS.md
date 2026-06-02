# Roadmap and Next Decision Points

> Status: working memory document  
> Last generated: 2026-06-02  
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
- index / health / status and research-status integration for these stages.

Current active preparation state:

```text
PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_NEEDS_REVIEW
```

Latest known PIT universe state:

```text
review_id: 7bc8ba08bf5a
export_readiness_id: 75c6975e93e4
helper_id: 4cf008a09f04
staging_id: 41bfd31a9e2c
worklist_id: 1c7972988f59
approved rows: 0
export-ready rows: 0
staged rows: 0
worklist rows: 72
needs evidence rows: 72
future-dated hints: 72
authoritative hints: 0
```

A synthetic diagnostic fixture proved that a complete reviewed row with all required current-candidates universe metadata can become `export_ready=true`, but real active artifacts remain blocked because there are no real approved rows.

## Recommended Next Branch

### Branch: Reviewed PIT Universe Evidence Update Ingestion

Suggested sequence:

1. Read-only audit for evidence update ingestion.
2. Define reviewer-completed update schema and validation rules.
3. Build a local validator that consumes worklist update CSVs and writes review-updates artifacts.
4. Keep suggested base-universe hints non-authoritative.
5. Do not auto-approve rows.
6. Do not export universe files.
7. After validated updates exist, rerun review → export-readiness → staging.
8. Only after real export-ready rows exist, consider accepted export design.

Do not skip directly to accepted universe export or multi-date candidate generation.

## What Evidence Update Ingestion Must Solve

It should answer:

- Which rows did the reviewer fill?
- Are identity keys present and unique?
- Did the reviewer explicitly choose a review status?
- Are reviewer and reviewed_at present?
- Are evidence source/path/reference fields present?
- Is survivorship risk explicitly resolved before approval?
- Are required universe metadata fields provided by the reviewer, not copied blindly from `suggested_*` hints?
- Are PIT dates valid?
- Can a clean `review_updates.csv` be produced for `pit-universe-overlay-review`?

Suggested identity keys:

```text
signal_date
symbol
universe_name
```

Potential blockers:

- missing identity key;
- duplicate identity key;
- missing reviewer;
- missing reviewed_at;
- missing evidence_source;
- missing evidence_path/evidence_reference;
- approval requested while `survivorship_bias_resolved` is not true;
- `listed_date > signal_date`;
- `delisted_date < signal_date`;
- future `available_time`;
- suggested fields copied into authoritative fields without review reason.

## After Evidence Update Ingestion

### 1. Rerun Review / Export-Readiness / Staging

Use validated real reviewer-supplied review updates to rerun:

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
- no forward returns;
- no messages;
- no broker;
- no cache mutation.

### 3. Per-Date Snapshot Manifest Preparation

Only after accepted PIT universe inputs exist.

Need to prepare or verify:

- market dataset;
- reviewed/exported PIT universe dataset;
- trading calendar;
- snapshot manifest;
- snapshot-quality status.

### 4. Current-Candidates Backfill Runner

Only after reviewed healthy plan/manifest and accepted PIT universe input exist.

Scope should remain:

- no forward returns;
- no execution;
- no messages;
- no broker;
- no cache mutation.

### 5. Forward Return Label Dataset

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
- export PIT universe input without real approved/export-ready rows;
- write `data/raw` or `data/processed` from PIT staging;
- run current-candidates backfill without reviewed/exported PIT universe rows;
- compute forward returns without multi-date candidates;
- change `signal_semantics` defaults based on synthetic fixtures;
- turn `REVIEW_BUY_CANDIDATE` into orders;
- send real alerts;
- add broker integration.
