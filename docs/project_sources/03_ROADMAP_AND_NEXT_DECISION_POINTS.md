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
- activated replacement worklist evidence update planning;
- PIT evidence checklist validator;
- PIT evidence policy profile comparison;
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
- activated replacement worklist evidence update plan;
- PIT evidence checklist validator;
- PIT evidence policy profile comparison;
- index / health / status and research-status integration for these stages.

Current PIT evidence policy profile comparison state:

```text
PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_ALL_BLOCKED
```

Latest known state:

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
policy_comparison_id: 0ef6d2f3bae6
```

```text
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
stock_core evidence package rows: 56
etf_core evidence package rows: 16
stock_core first-batch rows: 8
etf_core first-batch rows: 8
clean_review_updates_created: false

Codex diagnostics evidence discovery / gap closure:
inspected rows: 16
ready_for_review_update_count: 16
approval_requested_count: 0
approved_ready_count: 0
all rows remain NEEDS_MORE_EVIDENCE

strict checklist validator:
validator_id: 62e9eb747197
checklist_pass_count: 0
blocked_count: 16
stock_core_blocked_count: 8
etf_core_blocked_count: 8

policy profile comparison:
comparison_id: 0ef6d2f3bae6
profile: EOD_POST_CLOSE_LOW_BUDGET_PIT
strict_checklist_pass_count: 0
eod_low_budget_checklist_pass_count: 0
relaxed_blocker_count: 16
remaining_blocked_count: 16
```

A synthetic diagnostic fixture proved that a complete reviewed row with all required current-candidates universe metadata can become `export_ready=true`, but real active artifacts remain blocked because there are no real approved rows.

## Recommended Next Branch

### Branch: Codex-Driven Non-Relaxed PIT Evidence Gap Acquisition

Suggested sequence:

1. Use the strict validator report and policy comparison remaining blockers as the driver.
2. Search local artifacts first.
3. Use browser/web/plugin access only for light official/public evidence discovery.
4. Target the non-relaxed blocking categories:
   - not-delisted evidence;
   - stock ST/no-ST evidence;
   - survivorship-bias resolution basis;
   - reviewer / reviewed_at / evidence-reference completeness;
   - official active/status evidence.
5. Record evidence URLs / files / source type / fetch time / PIT suitability.
6. Generate updated draft completed update CSVs only when evidence is actually found.
7. Keep draft rows non-applied and diagnostics-only.
8. Run `pit-universe-evidence-update-ingestion` against draft updates in a diagnostics output directory.
9. Rerun `pit-evidence-checklist-validator`.
10. Rerun `pit-evidence-policy-profile-comparison` if useful.
11. Report checklist-pass candidates and blocked rows.
12. Do not run PIT overlay review application, export-readiness, staging, snapshot, or current-candidates in this branch.

## What Non-Relaxed Evidence Acquisition Must Solve

It should answer:

- Can Codex find official/public evidence for not-delisted status?
- Can Codex find official/public evidence for ST/no-ST status for 000001 over the selected dates?
- Can Codex support survivorship-bias resolution without relying on future-dated universe hints?
- Which evidence fields are symbol-level and reusable across all 8 dates?
- Which evidence fields must remain date-specific?
- Can any first-batch row become a strict or EOD low-budget checklist-pass approval candidate?
- If no row passes, which exact blockers remain?
- Which blockers require user judgment, credentials, CAPTCHA/login/paywall, or a practical-low-budget policy decision?

## Current Preference for Manual Steps

The user prefers that Codex automate evidence preparation whenever possible.

Default handling:

```text
If a step looks manual, first try to make Codex do it as:
local evidence discovery
public source discovery
source checklist generation
draft update CSV generation
diagnostics-only validation
```

User intervention should be required only for:

- credentials;
- CAPTCHA/login/paywall;
- final acceptance of evidence sufficiency;
- subjective judgment;
- explicit approval/export/activation decisions.

## After Checklist-Pass Evidence Candidates Exist

### 1. Evidence Update Ingestion

Use reviewer-supplied or Codex-drafted completed update CSVs to run:

```text
pit-universe-evidence-update-ingestion
```

Expected safe outcomes:

- no rows ready if evidence remains incomplete;
- ready clean review updates only when reviewer fields, PIT dates, metadata, and evidence pass validation;
- no approval applied automatically.

### 2. PIT Review / Export-Readiness / Staging

Only with validated real review updates and explicit user approval:

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

### 3. Accepted PIT Universe Export Workflow

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

### 4. Per-Date Snapshot Manifest Preparation

Only after accepted PIT universe inputs exist.

Need to prepare or verify:

- market dataset;
- reviewed/exported PIT universe dataset;
- trading calendar;
- snapshot manifest;
- snapshot-quality status.

### 5. Current-Candidates Backfill Runner

Only after reviewed healthy plan/manifest and accepted PIT universe input exist.

Scope should remain:

- no forward returns;
- no execution;
- no messages;
- no broker;
- no cache mutation.

### 6. Forward Return Label Dataset

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
- treat activated evidence update plans or evidence packages as clean review updates;
- treat checklist validator output as approval;
- treat policy comparison output as approval or strict validator default behavior;
- export PIT universe input without real approved/export-ready rows;
- write `data/raw` or `data/processed` from PIT staging;
- run current-candidates backfill without reviewed/exported PIT universe rows;
- compute forward returns without multi-date candidates;
- change `signal_semantics` defaults based on synthetic fixtures;
- turn `REVIEW_BUY_CANDIDATE` into orders;
- send real alerts;
- add broker integration.
