# System Architecture and Workflow Map

> Status: working memory document  
> Last generated: 2026-06-06  
> Permanence: temporary; update after major architecture or workflow additions.

## High-Level Architecture

```text
Data Sources
  ├─ LOCAL_CSV
  ├─ AKShare optional
  ├─ BaoStock optional
  ├─ future Tushare optional
  └─ future public announcement/news/fundamental sources

Raw Artifacts
  └─ data/raw/<SOURCE>/<dataset>/<run_id>/

Local Caches
  ├─ data/cache/market/daily_bars.csv
  └─ future fundamental/event caches

Quality and Policy
  ├─ data-source-health
  ├─ market-cache-preflight
  ├─ market-cache-compare
  ├─ market-source-policy
  ├─ data-quality
  └─ snapshot-quality

Candidate and Signal Layer
  ├─ current-candidates
  ├─ signal-semantics
  ├─ signal-advisory
  ├─ single-symbol-advisory
  ├─ question-style answer
  └─ advisory-conversation

Multi-Date Evidence Preparation
  ├─ current-candidates-backfill-plan
  ├─ current-candidates-backfill-execution-manifest
  ├─ point-in-time-universe-overlay-plan
  ├─ point-in-time-universe-overlay-review
  ├─ point-in-time-universe-overlay-export-readiness
  ├─ point-in-time-universe-evidence-completion-helper
  ├─ point-in-time-universe-export-staging
  ├─ point-in-time-universe-evidence-review-worklist
  ├─ point-in-time-universe-evidence-update-ingestion
  ├─ universe-profile-policy-audit
  ├─ universe-profile-split-worklist-plan
  ├─ reviewed-replacement-worklist-plan
  ├─ reviewed-replacement-worklist-acceptance
  ├─ reviewed-replacement-worklist-activation
  ├─ activated-replacement-worklist-evidence-update-plan
  ├─ pit-evidence-checklist-validator
  ├─ pit-evidence-policy-profile-comparison
  ├─ pit-official-status-evidence-packet
  ├─ pit-official-status-evidence-packet-enrichment
  ├─ reviewer-no-hit-source-coverage-acceptance
  ├─ reviewer-no-hit-acceptance-downstream-impact
  ├─ first-batch-reviewer-evidence-completion-plan
  ├─ first-batch-partial-completion-impact
  ├─ material-pit-evidence-gate-closure-plan
  └─ reviewer-material-evidence-fill-guidance

Dashboards and Status
  ├─ index / health / status for most artifacts
  └─ unified research-status
```

## Established Design Pattern

Important modules follow:

```text
artifact-producing command
→ index
→ health
→ status
→ research-status integration
→ checkpoint doc
```

## Key Completed Workflow Chains

### Market Data to Candidate Snapshot

```text
market data source
→ raw artifact
→ market cache
→ reviewed export
→ data-pipeline
→ data-quality
→ snapshot-quality
→ current-candidates
```

### Candidate to Paper Workflow

```text
current-candidates
→ current-to-paper
→ current-to-paper-review
→ WATCH_ONLY review
→ paper-daily
→ paper-workflow-status
→ research-status
```

### Multi-Date Candidate Planning, PIT Evidence, Policy Comparison, and Reviewer Guidance

```text
market cache coverage
→ current-candidates-backfill-plan
→ warmup-aware plan
→ execution manifest
→ PIT universe overlay plan/template
→ PIT universe overlay review workflow
→ PIT universe export-readiness
→ PIT universe evidence completion helper
→ PIT universe required metadata support
→ guarded PIT universe export staging
→ PIT universe evidence review worklist
→ PIT universe evidence update ingestion
→ universe profile policy audit
→ universe profile split-worklist plan
→ reviewed replacement worklist plan
→ reviewed replacement worklist acceptance
→ reviewed replacement worklist activation
→ activated replacement worklist evidence update plan
→ Codex diagnostics evidence discovery / gap closure
→ strict PIT evidence checklist
→ pit-evidence-checklist-validator
→ EOD_POST_CLOSE_LOW_BUDGET_PIT policy audit
→ pit-evidence-policy-profile-comparison
→ PIT official status evidence packet
→ SZSE 1815 quotation diagnostics
→ SZSE/CNInfo exception no-hit diagnostics
→ official no-hit evidence policy audit
→ EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT policy profile
→ PIT official status evidence packet enrichment
→ reviewer-no-hit-source-coverage-acceptance
→ reviewer-no-hit-acceptance-downstream-impact
→ first-batch-reviewer-evidence-completion-plan
→ first-batch-partial-completion-impact
→ material-pit-evidence-gate-closure-plan
→ reviewer-material-evidence-fill-guidance
→ index / health / status
→ research-status
```

Current active preparation state:

```text
REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_NEEDS_FILL
```

The system has not generated multi-date current-candidates, per-date snapshots, forward-return labels, accepted universe exports, active accepted PIT universe inputs, clean real approval updates, or live trades.

## Important Data Contracts

### Current-Candidates Universe Input Fields

A usable universe input for `current-candidates` requires:

```text
as_of_date
symbol
name
instrument_type
exchange
listed_date
delisted_date
is_active
is_st
is_suspended
industry
min_lot
t_plus_rule
available_time
revision_id
source
```

### PIT Evidence and Reviewer Context Contracts

PIT checklist validator outputs are gate reports, not approvals. A checklist-pass row would only be an approval-candidate preview until an explicit PIT review workflow is run.

Known policy profiles:

```text
STRICT_PIT
EOD_POST_CLOSE_LOW_BUDGET_PIT
EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT
```

None of these profiles changes strict defaults, applies approval, runs PIT review, exports universe files, or creates usable current-candidates input.

### SZSE 1815 Quotation Diagnostics

Diagnostics have shown:

```text
000001: 8/8 official same-date quotation rows found
159915: 8/8 official same-date quotation rows found
STRONG_OFFICIAL_DATE_SPECIFIC for quotation/traded presence: 16/16
```

This is strong date-specific evidence for quotation/traded presence only. It does not automatically prove not-delisted, no-ST, no-suspension, or survivorship-bias resolution.

### Material PIT Evidence Gate Closure Plan

The material gate closure plan identifies exact reviewed evidence needed to close material PIT gates for first-batch rows.

Current plan state:

```text
plan_id: 2d6ab8e7f9f8
stage: MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_NEEDS_EVIDENCE
row_count: 16
checklist_pass_candidate_count: 0
remaining_blocked_count: 16
reusable_symbol_level_closure_count: 2
date_specific_closure_required_count: 16
reviewer_no_hit_acceptance_required_count: 16
survivorship_rationale_required_count: 16
metadata_closure_required_count: 16
stock_st_no_st_required_count: 8
clean_review_updates_created: false
approval_applied: false
```

### Reviewer Material Evidence Fill Guidance

The fill guidance workflow converts material gate closure requirements into human-readable reviewer guidance.

Current guidance state:

```text
guidance_id: 94f5ff204662
stage: REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_NEEDS_FILL
row_count: 16
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

This guidance is not approval, not export-readiness, not staging, and not current-candidates input.

## Current Next Technical Branch

```text
Reviewer Fill Fixture Impact Validation v0.1
```

Purpose:

- create a diagnostics-only reviewer fill fixture from the guidance template;
- validate it against partial-completion/material-gate impact reporting;
- prove completed fields reduce only intended blockers;
- keep `checklist_pass_candidate_count=0` unless strict gates are truly satisfied;
- prevent clean review updates, PIT approval, export, current-candidates, snapshots, forward labels, cache mutation, messages, broker, or orders.
