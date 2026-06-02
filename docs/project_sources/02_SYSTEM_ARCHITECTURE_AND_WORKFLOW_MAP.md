# System Architecture and Workflow Map

> Status: working memory document  
> Last generated: 2026-06-02  
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
  └─ point-in-time-universe-evidence-review-worklist

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

### Multi-Date Candidate Planning, PIT Universe Review, Staging, and Worklist

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
→ PIT universe evidence review worklist index / health / status
→ research-status
```

Current active preparation state:

```text
PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_NEEDS_REVIEW
```

The system has not generated multi-date current-candidates, per-date snapshots, forward-return labels, accepted universe exports, or live trades.

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

### PIT Universe Review Fields

Reviewed PIT rows should preserve:

```text
signal_date, symbol, universe_name, include_flag, review_status,
valid_for_signal_date, blocker_reason, reviewer, reviewed_at,
review_reason, evidence_source, evidence_path/evidence_reference,
listed_date, delisted_date, is_active, is_st, is_suspended,
listed_date_evidence, delisted_date_evidence, is_active_evidence,
survivorship_bias_warning, survivorship_bias_resolved
```

Review rows also support current-candidates metadata fields such as `as_of_date`, `name`, `instrument_type`, `exchange`, `industry`, `min_lot`, `t_plus_rule`, `available_time`, `revision_id`, and `source` when a reviewer explicitly supplies them.

### PIT Universe Worklist Fields

The worklist is reviewer-facing and should not approve anything.

Important fields:

```text
worklist_id, review_id, helper_id,
signal_date, symbol, universe_name,
current_review_status, current_valid_for_signal_date,
survivorship_bias_warning, survivorship_bias_resolved,
missing_* evidence flags,
suggested_* non-authoritative hints,
required_next_evidence_fields,
suggested_next_review_action,
worklist_only=true
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
```

## Current Next Technical Branch

```text
Reviewed PIT Universe Evidence Update Ingestion Read-only Audit v0.1
```

Purpose:

- inspect how user-completed worklist update CSVs should be validated;
- define identity keys and blocker rules;
- design a safe output review-updates artifact;
- keep the branch read-only before implementation.

Do not skip directly to accepted universe export, snapshot preparation, or current-candidates backfill runner.
