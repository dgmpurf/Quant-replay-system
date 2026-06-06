# Roadmap and Next Decision Points

> Status: working memory document  
> Last generated: 2026-06-06  
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
- first-batch partial completion impact;
- material PIT evidence gate closure planning;
- reviewer material evidence fill guidance;
- unified `research-status`.

The project is preparing for true multi-date evidence collection, but it is not ready to generate multi-date candidates, compute forward returns, change non-demo thresholds, or produce validated buy/sell signals.

## Immediate Technical State

Current reviewer material evidence fill guidance state:

```text
REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_NEEDS_FILL
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
first_batch_partial_completion_impact_id: ea81f81ae764
material_pit_evidence_gate_closure_plan_id: 2d6ab8e7f9f8
reviewer_material_evidence_fill_guidance_id: 94f5ff204662
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
accepted replacement planning context: true
activation planning context created: true
stock_core first-batch rows: 8
etf_core first-batch rows: 8
checklist_pass_count: 0
remaining_blocked_count: 16
clean_review_updates_created: false
approval_applied: false

Material PIT evidence gate closure plan:
plan_id: 2d6ab8e7f9f8
checklist_pass_candidate_count: 0
remaining_blocked_count: 16
reusable_symbol_level_closure_count: 2
date_specific_closure_required_count: 16
reviewer_no_hit_acceptance_required_count: 16
survivorship_rationale_required_count: 16
metadata_closure_required_count: 16
stock_st_no_st_required_count: 8

Reviewer material evidence fill guidance:
guidance_id: 94f5ff204662
reviewer_guidance_row_count: 114
symbol_level_guidance_count: 2
date_specific_guidance_count: 16
no_hit_acceptance_guidance_count: 64
survivorship_rationale_guidance_count: 16
metadata_guidance_count: 16
checklist_pass_candidate_count: 0
remaining_blocked_count: 16
clean_review_updates_created: false
approval_applied: false
```

A synthetic diagnostic fixture proved that a complete reviewed row with all required current-candidates universe metadata can become `export_ready=true`, but real active artifacts remain blocked because there are no real approved rows.

## Recommended Next Branch

### Branch: Reviewer Fill Fixture Impact Validation

Suggested sequence:

1. Use the reviewer material evidence fill guidance artifact as the base.
2. Create a diagnostics-only reviewer fill fixture from the safe template.
3. Run impact validation through partial completion / material gate reporting.
4. Verify completed fields reduce only intended blockers.
5. Verify all approval/export/current-candidates boundaries remain intact.
6. Report exactly which blockers remain after the fixture.

## What Reviewer Fill Fixture Impact Validation Must Solve

It should answer:

- Can a reviewer fill fixture be created from the guidance template without breaking schema or leading-zero symbols?
- Does the fixture keep all default safety flags false?
- Which blockers are reduced by the fixture?
- Which material blockers remain?
- Does `checklist_pass_candidate_count` remain 0 unless all strict material gates are satisfied?
- Does the workflow avoid clean `review_updates.csv`, PIT review, export-readiness, staging, snapshots, current-candidates, forward labels, messages, broker, and orders?

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

### 5. Current-Candidates Backfill Runner

Only after reviewed healthy plan/manifest and accepted PIT universe input exist.

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
- treat first-batch completion plans, partial completion impacts, material gate closure plans, or reviewer fill guidance as clean review updates or applied approvals;
- treat checklist validator output as approval;
- treat policy comparison output as approval or strict validator default behavior;
- treat evidence packet output as approval, date-specific proof, or strict validator default behavior;
- treat reviewer no-hit acceptance or downstream impact as PIT approval, export-readiness, or usable universe input;
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

## Recent Important Checkpoints

Recent milestone direction:

- v1.20.0: reviewer no-hit acceptance downstream impact.
- v1.21.0: first-batch reviewer evidence completion planning.
- v1.22.0: first-batch partial completion impact.
- v1.23.0: material PIT evidence gate closure plan.
- v1.24.0: reviewer material evidence fill guidance.

## What to Ask ChatGPT Next

```text
Give me Codex tasks for Reviewer Fill Fixture Impact Validation v0.1.
```
