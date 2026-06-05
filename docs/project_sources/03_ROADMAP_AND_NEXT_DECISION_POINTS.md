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
- PIT official status evidence packet enrichment;
- reviewer no-hit source coverage acceptance;
- reviewer no-hit acceptance downstream impact;
- first-batch reviewer evidence completion planning;
- unified `research-status`.

The project is preparing for true multi-date evidence collection, but it is not ready to generate multi-date candidates, compute forward returns, change non-demo thresholds, or produce validated buy/sell signals.

## Immediate Technical State

Current first-batch reviewer evidence completion planning state:

```text
FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_NEEDS_REVIEW
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
reviewed_no_hit_policy_comparison_id: c1a75d1091c6
enrichment_id: cb5f323d3c8c
reviewer_no_hit_acceptance_id: 2e05e4b74794
reviewer_no_hit_downstream_impact_id: 9e164963455e
first_batch_reviewer_evidence_completion_plan_id: c630522f235a
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

reviewed no-hit support profile:
comparison_id: c1a75d1091c6
profile: EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT
reviewed_no_hit_support_pass_count: 0
no_hit_context_supported_count: 16
reviewer_acceptance_required_count: 16
remaining_blocked_count: 16

PIT official status evidence packet enrichment:
enrichment_id: cb5f323d3c8c
source_packet_id: 8efabe2ffe62
policy_comparison_id: c1a75d1091c6
strong_official_same_date_quotation_count: 16
reviewed_no_hit_context_supported_count: 16
reviewer_acceptance_required_count: 16
checklist_pass_count: 0
remaining_blocked_count: 16

Reviewer no-hit source coverage acceptance:
acceptance_id: 2e05e4b74794
row_count: 64
accepted_count: 0
needs_review_count: 64
reviewer_acceptance_required_count: 64
survivorship_rationale_required_count: 16
checklist_pass_count: 0
remaining_blocked_count: 16

Reviewer no-hit downstream impact:
impact_id: 9e164963455e
accepted_no_hit_context_count: 0
packet_context_gap_reduced_count: 0
checklist_pass_count: 0
remaining_blocked_count: 16
approval_applied: false

First-batch reviewer evidence completion plan:
plan_id: c630522f235a
row_count: 16
stock_core_row_count: 8
etf_core_row_count: 8
reviewer_completion_required_count: 16
no_hit_acceptance_required_count: 16
survivorship_rationale_required_count: 16
metadata_completion_required_count: 16
checklist_pass_count: 0
remaining_blocked_count: 16
clean_review_updates_created: false
approval_applied: false
```

A synthetic diagnostic fixture proved that a complete reviewed row with all required current-candidates universe metadata can become `export_ready=true`, but real active artifacts remain blocked because there are no real approved rows.

## Recommended Next Branch

### Branch: Tiny Manual Reviewer Completion Smoke

Suggested sequence:

1. Use the first-batch reviewer evidence completion plan artifact as the base.
2. Create a tiny diagnostics-only reviewer-completed evidence row from the generated reviewer completion template.
3. Validate that the row flows through planning validation without becoming PIT approval.
4. Verify that the row remains non-approved unless a future explicit PIT review workflow is run.
5. Verify no clean review updates, export readiness, staging, snapshot, forward labels, current-candidates, cache mutation, messages, broker, or orders are triggered.
6. Report exactly which blockers remain after the smoke.

## What Tiny Manual Reviewer Completion Smoke Must Solve

It should answer:

- Can the generated reviewer completion template be filled for a single row without breaking schema or leading-zero symbols?
- Does a completed row still avoid `APPROVED_FOR_PIT_UNIVERSE` and `include_flag=true`?
- Does the smoke avoid creating clean `review_updates.csv` unless a future explicit ingestion workflow says so?
- Does the planning layer keep checklist_pass_count at 0 unless all strict evidence gates are satisfied?
- Which fields remain missing after a partial/manual completion fixture?
- Does the workflow preserve all safety boundaries?

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
- treat reviewer no-hit acceptance or downstream impact as PIT approval, export-readiness, or usable universe input;
- treat reviewer evidence completion plans or templates as clean review updates or applied approvals;
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
