# Current State Snapshot

> Status: working memory document  
> Last generated: 2026-06-06  
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
- PIT evidence policy profile comparison.
- PIT official status evidence packet.
- Reviewed no-hit support policy profile.
- PIT official status evidence packet enrichment.
- Reviewer no-hit source coverage acceptance.
- Reviewer no-hit acceptance downstream impact.
- First-batch reviewer evidence completion planning.
- First-batch partial completion impact.
- Material PIT evidence gate closure planning.
- Reviewer material evidence fill guidance.
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

Known active / planning artifacts:

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

Current counts:

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
```

PIT evidence / planning details:

```text
selected signal dates: 8
symbols: 9
PIT rows: 72
stock_core first batch rows: 8
etf_core first batch rows: 8
PIT evidence checklist validator: 16 rows blocked, 0 checklist-pass approval candidates
SZSE 1815 quotation diagnostics: 16/16 same-date official quotation/traded-presence rows found
Reviewer no-hit acceptance: 64 rows, accepted_count=0, needs_review_count=64
Reviewer no-hit downstream impact: accepted_no_hit_context_count=0, remaining_blocked_count=16, approval_applied=false
First-batch reviewer evidence completion plan: 16 rows, all require reviewer completion, no-hit acceptance, survivorship rationale, and metadata completion
First-batch partial completion impact: active plan has 0 completed rows, 0 blockers reduced, 0 material blockers reduced, 0 checklist pass, 16 blocked
Material PIT evidence gate closure plan: 16 rows, 0 checklist-pass candidates, 16 blocked
Reviewer material evidence fill guidance: 16 rows, 114 guidance rows, 0 checklist-pass candidates, 16 blocked
```

Current reviewer material evidence fill guidance stage:

```text
REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_NEEDS_FILL
```

Meaning:

The project has moved from “material gate closure plan enumerates what reviewed evidence is needed” to “reviewer-oriented fill guidance exists for how to fill the remaining material evidence.”

The guidance is report-only. It does not make any row approval-ready, does not create clean `review_updates.csv`, and does not apply PIT approval.

The `EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT` profile remains opt-in and report-only. It supports no-hit observations only as reviewer-accepted context. The fill guidance can list no-hit acceptance and survivorship rationale steps, but it still does not change strict defaults or create PIT approvals.

The SZSE 1815 probe produced official same-date quotation/traded-presence evidence for all 16 first-batch rows. The enrichment, acceptance, downstream impact, first-batch planning, partial impact, material gate closure, and fill guidance milestones organize this evidence and no-hit context, but they still do not prove not-delisted, no-ST, no-suspension, or survivorship-bias resolution by themselves.

Existing `etf_core` artifacts should remain legacy mixed/demo context, not ETF-only context.

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
Reviewer Fill Fixture Impact Validation v0.1
```

Purpose:

- use the reviewer material evidence fill guidance template;
- create a tiny diagnostics-only reviewer fill fixture;
- verify the completed fields reduce only intended blockers;
- verify the fixture can flow through impact validation without becoming approval;
- keep all rows non-approved unless a future explicit PIT review workflow is run.

Do not yet:

- approve or reject rows;
- run PIT overlay review;
- run export-readiness;
- run staging;
- create clean review updates;
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

- v1.20.0: reviewer no-hit acceptance downstream impact.
- v1.21.0: first-batch reviewer evidence completion planning.
- v1.22.0: first-batch partial completion impact.
- v1.23.0: material PIT evidence gate closure plan.
- v1.24.0: reviewer material evidence fill guidance.

## What to Ask ChatGPT Next

```text
Give me Codex tasks for Reviewer Fill Fixture Impact Validation v0.1.
```
