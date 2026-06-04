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
  └─ reviewed-replacement-worklist-acceptance

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

### Multi-Date Candidate Planning, PIT Universe Review, Staging, Universe Profile Governance, Replacement Planning, and Acceptance

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
→ index / health / status
→ research-status
```

Current active preparation state:

```text
REVIEWED_REPLACEMENT_WORKLIST_ACCEPTED_AS_PLANNING_CONTEXT
```

The system has not generated multi-date current-candidates, per-date snapshots, forward-return labels, accepted universe exports, activated replacement worklists, or live trades.

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

### Reviewed Replacement Worklist Plan Fields

Replacement worklist planning is report-only and should preserve:

```text
replacement_plan_id, source_worklist_id, source_policy_audit_id, source_split_plan_id,
source_universe_name, recommended_future_universe, signal_date, symbol,
resolved_instrument_type, current_review_status, replacement_review_status,
include_flag, valid_for_signal_date, survivorship_bias_warning,
survivorship_bias_resolved, legacy_classification, profile_rule_applied,
profile_conflict, evidence_gap_summary, required_next_evidence_fields,
suggested_next_review_action, should_mutate_active_worklist=false,
should_approve=false, should_reject=false, plan_only=true
```

Replacement plans create future templates under `outputs/reports` only. They are not active review artifacts and do not replace the active legacy worklist.

### Reviewed Replacement Worklist Acceptance Fields

Replacement acceptance is a report-only planning acknowledgement. It should preserve:

```text
acceptance_id, replacement_plan_id, policy_audit_id, split_plan_id,
legacy_worklist_id, accepted_by, accepted_at, acceptance_reason,
acceptance_acknowledged=true, active_worklist_mutated=false,
should_activate=false, should_approve=false, should_reject=false,
no_universe_export=true, no_data_raw_write=true, no_data_processed_write=true,
plan_only=true, acceptance_only=true
```

Acceptance artifacts acknowledge replacement templates as reviewed planning context only. They do not activate a worklist, approve PIT rows, reject rows, or export universe files.

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
```

## Current Next Technical Branch

```text
Guarded Replacement Worklist Activation Read-only Audit v0.1
```

Purpose:

- inspect whether accepted replacement worklists should ever become the active evidence worklist;
- define explicit activation flags / manual confirmation requirements;
- keep the active legacy worklist untouched;
- keep the branch read-only before any implementation.

Do not skip directly to accepted universe export, snapshot preparation, or current-candidates backfill runner.
