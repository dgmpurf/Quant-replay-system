# System Architecture and Workflow Map

> Status: working memory document  
> Last generated: 2026-06-04  
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
  └─ activated-replacement-worklist-evidence-update-plan

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

### Multi-Date Candidate Planning, PIT Universe Review, Staging, Universe Profile Governance, Replacement Planning, Acceptance, Activation, and Evidence Planning

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
→ index / health / status
→ research-status
```

Current active preparation state:

```text
ACTIVATED_REPLACEMENT_WORKLIST_EVIDENCE_UPDATE_PLAN_READY
```

The system has not generated multi-date current-candidates, per-date snapshots, forward-return labels, accepted universe exports, active accepted PIT universe inputs, clean real review updates, or live trades.

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

### Legacy etf_core Meaning

Existing `etf_core` artifacts are not ETF-only.

Current 72-row legacy worklist distribution:

```text
STOCK rows: 56
ETF rows: 16
legacy mixed-demo rows: 72
profile conflicts: 56
```

Therefore existing `etf_core` artifacts should be treated as:

```text
legacy_mixed_demo_universe
POLICY_AMBIGUOUS_DEMO_MIXED_UNIVERSE
```

They should not be mutated in place.

### Replacement / Acceptance / Activation Fields

Replacement planning, acceptance, and activation are all outputs-only planning context.

They preserve lineage to:

```text
legacy_worklist_id
policy_audit_id
split_plan_id
replacement_plan_id
acceptance_id
activation_id
```

They must preserve safety flags:

```text
active_worklist_mutated=false
should_approve=false
should_reject=false
no_universe_export=true
no_data_raw_write=true
no_data_processed_write=true
plan_only=true
```

Activation artifacts may produce activated replacement templates under `outputs/reports`, but they must not mutate the active legacy worklist or imply PIT approval/export.

### Activated Replacement Evidence Update Plan Fields

Activated replacement evidence update planning is report-only and should preserve:

```text
plan_id, activation_id, acceptance_id, replacement_plan_id, split_plan_id,
policy_audit_id, legacy_worklist_id, recommended_future_universe,
signal_date, symbol, resolved_instrument_type, review_status,
include_flag=false, valid_for_signal_date=false,
survivorship_bias_resolved=false, manual_review_required=true,
evidence_gap_summary, required_next_evidence_fields,
suggested_next_review_action, hint_authoritative_for_pit=false,
clean_review_updates_created=false, no_universe_export=true,
no_data_raw_write=true, no_data_processed_write=true,
no_current_candidates_generated=true, no_snapshot_built=true,
no_forward_labels=true, plan_only=true
```

Evidence update plans may produce profile-specific worklists and update templates for:

```text
stock_core
etf_core
mixed_demo_core
```

They are not clean `review_updates.csv` artifacts and must not be fed directly as applied approvals.

### PIT Evidence Update Ingestion Fields

Evidence update ingestion validates reviewer-completed rows and may write a clean `review_updates.csv` artifact under `outputs/reports`.

It must not:

```text
apply approvals
export universe files
write data/raw or data/processed
run current-candidates
build snapshots
compute forward labels
```

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
```

## Current Next Technical Branch

```text
Codex-Driven Profile-Specific PIT Evidence Discovery and Draft Update Validation v0.1
```

Purpose:

- use Codex to perform local and public evidence discovery for first-batch stock_core / etf_core rows;
- create evidence source records and draft completed update CSVs if evidence is found;
- run diagnostics-only `pit-universe-evidence-update-ingestion` validation;
- keep the branch diagnostics-only before any applied PIT review.

Do not skip directly to PIT review application, accepted universe export, snapshot preparation, or current-candidates backfill runner.
