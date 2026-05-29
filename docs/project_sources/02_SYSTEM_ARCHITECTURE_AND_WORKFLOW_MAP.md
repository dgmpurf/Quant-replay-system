# System Architecture and Workflow Map

> Status: working memory document  
> Last generated: 2026-05-29  
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

Reviewed Exports and Snapshots
  ├─ market-cache-export-plan
  ├─ market-cache-export
  ├─ data-pipeline
  └─ snapshot manifest

Candidate and Signal Layer
  ├─ current-candidates
  ├─ signal-semantics
  ├─ signal-advisory
  ├─ single-symbol-advisory
  ├─ question-style answer
  └─ advisory-conversation

Paper and Review Layer
  ├─ current-to-paper
  ├─ current-to-paper-review
  ├─ paper-review-template-health
  ├─ paper-review-decisions
  ├─ paper-daily
  └─ paper-reconcile-fills

Multi-Date Evidence Preparation
  ├─ current-candidates-backfill-plan
  ├─ current-candidates-backfill-execution-manifest
  ├─ point-in-time-universe-overlay-plan
  └─ point-in-time-universe-overlay-review

Dashboards and Status
  ├─ index / health / status for most artifacts
  └─ unified research-status
```

## Established Design Pattern

Most important modules follow this pattern:

```text
artifact-producing command
→ index
→ health
→ status
→ research-status integration
→ checkpoint doc
```

This repetition is deliberate. It makes local workflows auditable and prevents hidden state transitions.

## Key Completed Workflow Chains

### 1. Market Data to Candidate Snapshot

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

### 2. Candidate to Paper Workflow

```text
current-candidates
→ current-to-paper
→ current-to-paper-review
→ WATCH_ONLY review
→ paper-daily
→ paper-workflow-status
→ research-status
```

### 3. Candidate to Signal Advisory

```text
current-candidates
→ signal-semantics
→ signal-advisory
→ signal-advisory-index / health / status
→ research-status
```

### 4. Single-Symbol Advisory

```text
local candidates / scored dataset
→ single-symbol-advisory
→ question-style answer
→ answer index / health / status
→ research-status
```

### 5. Conversational Advisory Facade

```text
user question
→ deterministic parser
→ parsed symbol / intent
→ single-symbol answer
→ advisory-conversation artifact
→ index / health / status
→ research-status
```

### 6. Signal Semantics Calibration

```text
candidate or scored rows
→ advisory-profile-calibration
→ calibration-to-signal-semantics proposal
→ proposal index / health / status
→ research-status
```

### 7. Multi-Date Candidate Planning, PIT Universe Preparation, and Review

```text
market cache coverage
→ current-candidates-backfill-plan
→ warmup-aware plan
→ execution manifest
→ PIT universe overlay plan/template
→ PIT universe overlay review workflow
→ PIT universe overlay review index / health / status
→ research-status
```

Current active preparation state:

```text
PIT_UNIVERSE_OVERLAY_REVIEW_NEEDS_MORE_EVIDENCE
```

The system has not generated multi-date current-candidates, per-date snapshots, or forward-return labels yet.

## Important Data Contracts

### Point-in-Time Fields

The project should preserve:

- `as_of_date`
- `available_time`
- `report_period` for financials
- `announcement_date` for fundamentals/events
- `source`
- `upstream_source`
- `revision_id`
- `raw_hash` or equivalent where possible

### PIT Universe Review Fields

Reviewed PIT universe rows should preserve:

- `signal_date`
- `symbol`
- `universe_name`
- `include_flag`
- `review_status`
- `valid_for_signal_date`
- `blocker_reason`
- `reviewer`
- `reviewed_at`
- `review_reason`
- `evidence_source`
- `evidence_path` or `evidence_reference`
- `listed_date`
- `delisted_date`
- `is_active`
- `is_st`
- `is_suspended`
- `listed_date_evidence`
- `delisted_date_evidence`
- `is_active_evidence`
- `survivorship_bias_warning`
- `survivorship_bias_resolved`

### Safety Fields

Most user-facing or review-facing artifacts should keep:

- `requires_manual_confirmation=true`
- `auto_order_allowed=false`
- `no_live_trading=true`
- `no_broker_api=true`
- `no_order_placement=true` where applicable
- `no_message_sent=true`
- `llm_api_called=false` when relevant
- `plan_only=true` for planning workflows
- `review_only=true` for review workflows

### Signal Semantics Provenance

Downstream advisory artifacts carry or should carry:

- `semantics_policy_source`
- `semantics_policy_version`
- `semantics_classifier`
- `semantics_settings_profile`
- `semantics_action`
- `semantics_reason`
- `semantics_manual_confirmation_required`
- `semantics_auto_order_allowed`
- `semantics_no_live_trading`
- `semantics_no_broker_api`

## Current Multi-Date Planning State

Known current state:

- Market cache rows: 1335.
- Symbols: 9.
- Date range: 2024-01-02 to 2024-05-20.
- Warmup-aware plan:
  - first selected signal date: 2024-04-02.
  - last selected signal date: 2024-05-06.
  - warmup trading days: 60.
  - 1d/3d/5d/10d forward horizon feasible.
- Execution manifest:
  - 8 rows.
  - 0 ready.
  - 8 blocked by `BLOCKED_UNIVERSE_AS_OF`.
- PIT universe overlay plan:
  - overlay plan id: `38a254c54024`.
  - 72 rows.
  - 8 signal dates.
  - 9 symbols.
  - 72 rows need manual review.
  - 0 rows valid for signal date.
  - 72 survivorship-bias warnings.
- PIT universe overlay review:
  - review id: `7bc8ba08bf5a`.
  - 72 rows.
  - 0 approved rows.
  - 0 valid-for-signal-date rows.
  - 72 rows still need manual review / more evidence.
  - 72 unresolved survivorship warnings.

## Current Next Technical Branch

```text
Reviewed PIT Universe Overlay Export Readiness Read-only Audit v0.1
```

Purpose:

- inspect whether reviewed rows can be exported into a local universe input;
- confirm there are currently no approved rows to export;
- define blockers and export readiness statuses;
- keep the workflow read-only before implementation.

Do not skip directly to universe export, snapshot preparation, or current-candidates backfill runner.
