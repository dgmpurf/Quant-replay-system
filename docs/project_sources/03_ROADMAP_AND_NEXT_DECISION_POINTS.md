# Roadmap and Next Decision Points

> Status: working memory document  
> Last generated: 2026-06-05  
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
- PIT official status evidence packet;
- reviewed no-hit support policy profile;
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
- PIT official status evidence packet;
- reviewed no-hit support policy profile;
- index / health / status and research-status integration for these stages.

Current PIT evidence policy comparison state:

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
packet_id: 8efabe2ffe62
packet_rerun_ingestion_id: ac6846aef520
packet_rerun_validator_id: 498a3d0786af
packet_rerun_policy_comparison_id: b7e7ec8f66f5
reviewed_no_hit_policy_comparison_id: c1a75d1091c6
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

PIT official status evidence packet:
packet_id: 8efabe2ffe62
evidence_packet_row_count: 72
strong official date-specific: 0
supporting official symbol-level: 16
supporting local EOD cache: 16
missing: 40
checklist_pass_count: 0
blocked_count: 16

SZSE 1815 same-date quotation diagnostics:
rows found for 000001: 8 / 8
rows found for 159915: 8 / 8
strong official date-specific quotation/traded-presence evidence: 16 / 16

reviewed no-hit support profile:
comparison_id: c1a75d1091c6
profile: EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT
reviewed_no_hit_support_pass_count: 0
no_hit_context_supported_count: 16
reviewer_acceptance_required_count: 16
remaining_blocked_count: 16
```

A synthetic diagnostic fixture proved that a complete reviewed row with all required current-candidates universe metadata can become `export_ready=true`, but real active artifacts remain blocked because there are no real approved rows.

## Recommended Next Branch

### Branch: PIT Official Status Evidence Packet Enrichment

Suggested sequence:

1. Use the existing official status evidence packet as the base.
2. Add SZSE 1815 same-date quotation diagnostics as `STRONG_OFFICIAL_DATE_SPECIFIC` for quotation/traded presence only.
3. Add reviewed no-hit support policy context as reviewer-accepted support only, not approval.
4. Preserve existing official symbol-level context and local EOD cache context.
5. Keep evidence categories distinct:
   - `STRONG_OFFICIAL_DATE_SPECIFIC_QUOTATION`
   - `REVIEWED_NO_HIT_SUPPORT_CONTEXT`
   - `SUPPORTING_OFFICIAL_SYMBOL_LEVEL`
   - `SUPPORTING_LOCAL_EOD_CACHE`
   - `MISSING`
6. Generate updated draft completed updates only where evidence exists.
7. Rerun diagnostics-only:
   - `pit-universe-evidence-update-ingestion`
   - `pit-evidence-checklist-validator`
   - `pit-evidence-policy-profile-comparison`
8. Report whether any rows become approval-candidate previews.
9. Do not run PIT overlay review, export-readiness, staging, snapshot, or current-candidates.

## What Packet Enrichment Must Solve

It should answer:

- Can the evidence packet now show 16/16 official date-specific quotation/traded presence?
- Which rows still lack not-delisted evidence?
- Which rows still lack ST/no-ST evidence for 000001?
- Which rows still require survivorship-bias rationale?
- Does reviewed no-hit support reduce context gaps without creating approval?
- Can any first-batch row become a strict or reviewed-no-hit policy checklist-pass approval candidate?
- If no row passes, which exact blockers remain?
- Which blockers require user judgment or explicit reviewer acceptance?

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
- treat evidence packet output as approval, date-specific proof, or strict validator default behavior;
- treat SZSE 1815 quotation presence as not-delisted / no-ST / no-suspension / survivorship evidence by itself;
- treat no-hit observations as approval-grade without reviewer acceptance and source coverage documentation;
- export PIT universe input without real approved/export-ready rows;
- write `data/raw` or `data/processed` from PIT staging;
- run current-candidates backfill without reviewed/exported PIT universe rows;
- compute forward returns without multi-date candidates;
- change `signal_semantics` defaults based on synthetic fixtures;
- turn `REVIEW_BUY_CANDIDATE` into orders;
- send real alerts;
- add broker integration.
