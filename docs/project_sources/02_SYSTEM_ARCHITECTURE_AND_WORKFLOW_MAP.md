# System Architecture and Workflow Map

> Status: working memory document  
> Last generated: 2026-06-05  
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
  └─ first-batch-reviewer-evidence-completion-plan

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

### Advisory and Semantics

```text
current-candidates
→ signal-semantics
→ signal-advisory / single-symbol-advisory / advisory-conversation
→ index / health / status
→ research-status
```

### Multi-Date Candidate Planning, PIT Evidence, Policy Comparison, and Evidence Context

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
→ index / health / status
→ research-status
```

Current active preparation state:

```text
FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_NEEDS_REVIEW
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

### Universe Profile Registry

The initial profile registry lives in:

```text
config/universe_profiles.yaml
```

Initial profile intent:

```text
stock_core:
  allowed_instrument_types: STOCK
  mixed_allowed: false

etf_core:
  allowed_instrument_types: ETF
  mixed_allowed: false

mixed_demo_core:
  allowed_instrument_types: STOCK, ETF
  mixed_allowed: true
  profile_type: demo_mixed
```

Existing `etf_core` artifacts remain legacy mixed-demo context and should not be treated as ETF-only or mutated in place.

## PIT Evidence and Reviewer Context Contracts

### PIT Evidence Checklist Validator

The checklist validator reports:

```text
validator_id
row_count
checklist_pass_count
blocked_count
stock_core_blocked_count
etf_core_blocked_count
missing_evidence_matrix
approval_candidate_preview
```

Validator outputs are gate reports, not approvals. A checklist-pass row would only be an approval-candidate preview until a later explicit PIT review workflow is run.

### PIT Evidence Policy Profile Comparison

Known profiles:

```text
STRICT_PIT
EOD_POST_CLOSE_LOW_BUDGET_PIT
EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT
```

Neither profile changes strict defaults, applies approval, runs PIT review, exports universe files, or creates usable current-candidates input.

### SZSE 1815 Quotation Diagnostics

Diagnostics have shown:

```text
000001: 8/8 official same-date quotation rows found
159915: 8/8 official same-date quotation rows found
STRONG_OFFICIAL_DATE_SPECIFIC for quotation/traded presence: 16/16
```

This is strong date-specific evidence for quotation/traded presence only. It does not automatically prove not-delisted, no-ST, no-suspension, or survivorship-bias resolution.

### Reviewer No-Hit Acceptance and Downstream Impact

Reviewer no-hit source coverage acceptance records source coverage, query-window acceptance, no-hit inference limits, and survivorship rationale as report-only context.

The downstream impact workflow links accepted no-hit supporting context back to packet, checklist, and policy context while preserving approval boundaries.

Current active downstream impact state:

```text
impact_id: 9e164963455e
accepted_no_hit_context_count: 0
packet_context_gap_reduced_count: 0
checklist_pass_count: 0
remaining_blocked_count: 16
approval_applied: false
```

### First-Batch Reviewer Evidence Completion Plan

The first-batch reviewer evidence completion plan converts active evidence context into a concrete reviewer fill plan for the 16 first-batch rows.

It reports:

```text
plan_id
row_count
stock_core_row_count
etf_core_row_count
reviewer_completion_required_count
no_hit_acceptance_required_count
survivorship_rationale_required_count
metadata_completion_required_count
checklist_pass_count
remaining_blocked_count
clean_review_updates_created
approval_applied
```

Current plan state:

```text
plan_id: c630522f235a
stage: FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_NEEDS_REVIEW
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

Plan artifacts may include:

```text
first_batch_reviewer_evidence_completion_plan.csv
row_level_missing_evidence_matrix.csv
reusable_symbol_level_evidence_plan.csv
date_specific_evidence_plan.csv
reviewer_completion_template.csv
reviewer_no_hit_acceptance_todo.csv
survivorship_rationale_todo.csv
metadata_completion_todo.csv
source_lineage_summary.csv
report.md
metadata.json
```

These artifacts are reviewer planning context only. They are not clean review updates, applied approvals, accepted universe files, or current-candidates inputs.

## Current Multi-Date Planning State

Known current state:

```text
Market cache: 1335 rows, 9 symbols, 2024-01-02 to 2024-05-20
Warmup-aware signal dates: 2024-04-02 to 2024-05-06
Execution manifest: 8 rows, all blocked by BLOCKED_UNIVERSE_AS_OF
PIT overlay plan: 72 rows, 8 dates, 9 symbols
PIT review: 72 rows, 0 approved, 72 unresolved survivorship warnings
Export readiness: 0 approved, 0 export-ready, 72 blocked
Evidence helper: 72 needs evidence, 72 future-dated hints, 0 authoritative hints
Export staging: 0 staged rows, 72 blocked
Evidence review worklist: 72 rows, 9 symbols, 8 dates, 72 needs evidence
Evidence update ingestion: 72 rows, 0 ready clean updates, 72 blocked
Universe profile policy audit: 72 ambiguous legacy mixed-demo rows
Split-worklist plan: 56 future stock_core rows, 16 future etf_core rows, 0 mixed_demo_core rows, 56 profile conflicts
Reviewed replacement worklist plan: 56 stock_core replacement rows, 16 etf_core replacement rows, 0 mixed_demo_core rows, active legacy worklist untouched
Reviewed replacement worklist acceptance: acknowledged as planning context, active legacy worklist untouched
Reviewed replacement worklist activation: activation planning context, 56 stock_core rows, 16 etf_core rows, active legacy worklist untouched
Activated replacement evidence update plan: 56 stock_core rows, 16 etf_core rows, 0 mixed_demo_core rows, stock first batch 8 rows, ETF first batch 8 rows, no clean review updates
PIT evidence checklist validator: 16 rows blocked, 0 checklist-pass approval candidates
PIT evidence policy profile comparison: EOD low-budget profile relaxes 16 timing/context blockers but still leaves 16 rows blocked, 0 pass candidates
PIT official status evidence packet: 72 evidence packet rows, 0 strong official date-specific, 16 supporting official symbol-level, 16 supporting local EOD cache, 40 missing, 16 blocked rows
SZSE 1815 quotation diagnostics: 16/16 same-date official quotation/traded-presence rows found
Reviewer no-hit downstream impact: 0 accepted active context, 0 packet gaps reduced, 0 checklist pass, 16 blocked, approval_applied=false
First-batch reviewer evidence completion plan: 16 rows, 16 reviewer-completion required, 16 no-hit acceptance required, 16 survivorship rationale required, 16 metadata completion required, 0 checklist pass, 16 blocked
```

## Current Next Technical Branch

```text
Tiny Manual Reviewer Completion Smoke v0.1
```

Purpose:

- use the generated first-batch reviewer completion template;
- create a one-row diagnostics-only manual completion fixture;
- verify the fixture can flow through planning validation without becoming PIT approval;
- confirm checklist_pass_count and remaining blockers behave as expected;
- confirm no clean review updates, export, snapshot, forward labels, current-candidates, messages, broker, orders, or cache mutation.
