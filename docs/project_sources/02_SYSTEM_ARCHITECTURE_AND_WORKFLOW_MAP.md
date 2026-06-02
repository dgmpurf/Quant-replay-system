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
  ├─ point-in-time-universe-overlay-review
  ├─ point-in-time-universe-overlay-export-readiness
  ├─ point-in-time-universe-evidence-completion-helper
  └─ point-in-time-universe-export-staging

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

### 7. Multi-Date Candidate Planning, PIT Universe Review, and Staging

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
→ PIT universe export staging index / health / status
→ research-status
```

Current active preparation state:

```text
PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS
```

The system has not generated multi-date current-candidates, per-date snapshots, forward-return labels, or usable universe exports yet.

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

### Current-Candidates Universe Input Fields

A usable universe input for `current-candidates` requires:

- `as_of_date`
- `symbol`
- `name`
- `instrument_type`
- `exchange`
- `listed_date`
- `delisted_date`
- `is_active`
- `is_st`
- `is_suspended`
- `industry`
- `min_lot`
- `t_plus_rule`
- `available_time`
- `revision_id`
- `source`

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

Review rows now also support current-candidates universe metadata fields such as `as_of_date`, `name`, `instrument_type`, `exchange`, `industry`, `min_lot`, `t_plus_rule`, `available_time`, `revision_id`, and `source` when a reviewer explicitly supplies them.

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
- `staging_only=true` for staging workflows

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
- Export readiness:
  - export readiness id: `75c6975e93e4`.
  - 0 approved rows.
  - 0 export-ready rows.
  - 72 blocked rows.
- Evidence completion helper:
  - helper id: `4cf008a09f04`.
  - 72 rows need evidence.
  - base universe hints are non-authoritative and future-dated.
- Export staging:
  - staging id: `41bfd31a9e2c`.
  - 0 export-ready input rows.
  - 0 staged rows.
  - 72 blocked rows.
  - stage: `PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS`.

Diagnostic synthetic metadata tests proved that a complete reviewed row with required metadata can become export-ready in diagnostics, but those diagnostic rows do not become active workflow artifacts.

## Current Next Technical Branch

```text
PIT Universe Evidence Review Worklist / Real Evidence Completion Plan
```

Purpose:

- help the user complete real PIT evidence fields safely;
- keep future universe hints non-authoritative;
- preserve survivorship-bias warnings until resolved;
- prepare real review updates without automatically approving rows.

Do not skip directly to accepted universe export, snapshot preparation, or current-candidates backfill runner.
