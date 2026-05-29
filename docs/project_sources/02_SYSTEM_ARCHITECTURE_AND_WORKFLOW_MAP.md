# System Architecture and Workflow Map

> Status: working memory document  
> Last generated: 2026-05-28  
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

This pattern is intentionally repetitive. It makes local workflows auditable and prevents hidden state transitions.

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

### 7. Multi-Date Candidate Planning

```text
market cache coverage
→ current-candidates-backfill-plan
→ warmup-aware plan
→ execution manifest
→ execution manifest index / health / status
→ research-status
```

Current blocker:

```text
BLOCKED_UNIVERSE_AS_OF
```

The market data and forward-horizon feasibility are present, but the available universe artifact is too late for earlier signal dates.

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

### Safety Fields

Most user-facing artifacts should keep:

- `requires_manual_confirmation=true`
- `auto_order_allowed=false`
- `no_live_trading=true`
- `no_broker_api=true`
- `no_message_sent=true`
- `llm_api_called=false` when relevant

### Signal Semantics Provenance

Downstream advisory artifacts now carry or should carry:

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

Known current state from the conversation:

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

Next technical blocker: point-in-time universe overlay / snapshot preparation.
