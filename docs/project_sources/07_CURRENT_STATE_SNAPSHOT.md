# Current State Snapshot

> Status: working memory document  
> Last generated: 2026-06-02  
> Permanence: temporary; refresh after the next major checkpoint or when source state changes.

## Summary

The project is currently a local quantitative research, signal semantics, advisory, calibration, paper workflow, and multi-date evidence preparation system for China A-share stocks and ETFs.

It has not become a live trading system.

## Major Completed Capabilities

### Data and Market Cache

- Optional AKShare and BaoStock market data adapters.
- Local market cache.
- Cache query with source/upstream filters.
- Market source comparison.
- Tencent field semantics fixes.
- Tencent STAR Market 688xxx volume fix.
- Market source reliability policy.
- Reviewed cache export and policy-aware export planning.

### Data Quality and Snapshot Quality

- `data-pipeline`.
- `data-quality`.
- `snapshot-quality`.
- Snapshot warning actionability.
- Active snapshot linkage.

### Candidate Generation

- `current-candidates`.
- Demo selection profile.
- Current-candidates index, health, status.
- Multi-date backfill planning:
  - warmup-aware plan,
  - execution manifest,
  - execution manifest index/health/status,
  - research-status integration.
- PIT universe overlay preparation:
  - PIT overlay plan/template,
  - PIT overlay index/health/status,
  - research-status integration.
- PIT universe overlay review:
  - review workflow,
  - review index/health/status,
  - research-status integration.
- PIT universe export preparation:
  - export-readiness,
  - evidence completion helper,
  - required metadata support,
  - guarded export staging,
  - export staging index/health/status,
  - research-status integration.

### Signal Semantics

- Deterministic advisory action labels.
- Artifact index/health/status.
- Research-status integration.
- Shared semantics wired into advisory layers.
- Semantics provenance metadata.
- Provenance visibility in artifacts and research-status.

### Signal Advisory and Product Layer

- `signal-advisory`.
- `single-symbol-advisory`.
- Question-style single-symbol answer.
- Local-only advisory conversation facade.
- Index/health/status for each major advisory artifact type.
- Research-status integration for advisory layers.
- Deterministic local parsing; no LLM.

### Paper Workflow

- Current-to-paper handoff.
- Current-to-paper-review handoff.
- Paper review template health.
- Paper review decisions.
- WATCH_ONLY paper workflow.
- Paper daily reviewed decisions.
- Paper workflow status.
- Synthetic fill rejection.
- Diagnostic reconciliation scoping.

### Calibration

- Advisory profile calibration analyzer.
- Calibration artifact index/health/status.
- Calibration-to-signal-semantics proposal report.
- Proposal artifact index/health/status.
- Research-status integration.
- Current recommendation:
  - keep defaults,
  - do not expand buy review,
  - consider watch expansion only after more evidence,
  - collect more symbols/dates/backtest/paper evidence.

### Factor Taxonomy Sources

- Canonical China A-share factor taxonomy source exists.
- Event-driven/industry-chain factor framework source exists.
- Factor taxonomy normalization produced a registry seed and summary in local/docs outputs.
- These are design sources, not executable signal logic.

## Current Quantitative Evidence Status

Current evidence is not enough to validate non-demo buy signals.

Known gaps:

- too few dates,
- only 9 symbols in local cache,
- demo-only current-candidates,
- no forward-return labels,
- no multi-date outcome dataset,
- no benchmark-relative outcomes,
- no transaction cost/slippage model,
- no accepted PIT universe export yet,
- no corporate action adjustment policy validation,
- no linked paper outcome history for signals.

## Current Multi-Date Backfill Status

Market/cache feasibility:

- local market cache has enough data for selected warmup-aware signal dates.
- 60 trading day warmup modeled.
- 1d/3d/5d/10d forward horizon modeled.

Execution readiness:

- 8 selected signal dates.
- 0 execution-ready.
- 8 blocked by `BLOCKED_UNIVERSE_AS_OF` at execution manifest stage.

PIT universe overlay preparation:

- latest overlay plan id: `38a254c54024`.
- 72 rows.
- 8 signal dates.
- 9 symbols.
- 72 rows require manual review.
- 0 rows valid for signal date.
- 72 survivorship-bias warnings.

PIT universe overlay review:

- latest active review id: `7bc8ba08bf5a`.
- 72 rows.
- approved rows: 0.
- valid-for-signal-date rows: 0.
- needs manual review rows: 72.
- unresolved survivorship warnings: 72.
- stage: `PIT_UNIVERSE_OVERLAY_REVIEW_NEEDS_MORE_EVIDENCE`.

PIT universe export readiness:

- latest active export readiness id: `75c6975e93e4`.
- approved rows: 0.
- export-ready rows: 0.
- blocked rows: 72.
- stage: `PIT_UNIVERSE_EXPORT_BLOCKED_NO_APPROVED_ROWS`.

PIT universe evidence completion helper:

- latest helper id: `4cf008a09f04`.
- 72 rows need evidence.
- 72 rows have base-universe hints.
- 72 future-dated hints.
- authoritative hints: 0.
- approved rows: 0.
- valid-for-signal-date rows: 0.

PIT universe export staging:

- latest active staging id: `41bfd31a9e2c`.
- linked export readiness id: `75c6975e93e4`.
- export-ready input count: 0.
- staged row count: 0.
- blocked count: 72.
- stage: `PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS`.

Diagnostic result:

- Synthetic required-metadata diagnostics proved that a complete reviewed row with all required universe metadata can become `export_ready=true` in isolated diagnostics.
- Diagnostic artifacts remain under `manual_diagnostics` and are not active workflow artifacts.

Meaning:

The project has moved from “can we design PIT universe review/export-readiness?” to “the guarded staging path exists, but the real active workflow has no approved/export-ready rows.”

The next blocker is real evidence completion. Without real approved PIT universe rows, there is nothing to export or stage.

## Current External Data Strategy

Budget constraint:

- free-first.
- paid vendors are future backups only.

Current recommendation:

- Fundamentals before news sentiment.
- LOCAL_CSV first.
- AKShare / BaoStock / Tushare free/low-quota optional later.
- Public announcement metadata later.
- News as event/risk context first, not score driver.

## Recommended Next Branch

```text
PIT Universe Evidence Review Worklist / Real Evidence Completion Plan
```

Purpose:

- help the user complete real PIT evidence fields;
- keep future-dated base universe hints non-authoritative;
- preserve survivorship warnings until resolved;
- prepare real review updates for rerunning review/export-readiness/staging;
- avoid writing usable universe files until accepted export is explicitly designed.

Do not yet:

- write usable universe files,
- write `data/raw` or `data/processed`,
- generate multi-date candidates,
- build per-date snapshot manifests,
- compute forward returns,
- change non-demo thresholds,
- add news scraping,
- add broker integration,
- send real messages.

## Recent Important Checkpoints

Recent milestone direction, not necessarily exhaustive:

- v0.90.0: shared signal semantics advisory wiring.
- v0.91.0: shared signal semantics provenance metadata.
- v0.92.0: provenance visibility.
- v0.93.0: advisory profile calibration analyzer.
- v0.94.0: advisory profile calibration dashboard.
- v0.96.0: calibration-to-signal-semantics research-status integration.
- v0.97.0: warmup-aware current-candidates backfill plan.
- v0.98.0: current-candidates backfill execution manifest.
- v0.99.0: execution manifest research-status integration.
- v1.0.0: research-infrastructure milestone with PIT universe overlay planning and status visibility.
- v1.1.0: reviewed PIT universe overlay approval workflow and research-status visibility.
- v1.2.0: PIT universe export-readiness.
- v1.3.0: PIT universe evidence completion helper.
- v1.4.0: PIT universe required metadata support.
- v1.5.0: guarded PIT universe export staging.

## What to Ask ChatGPT Next

For next development:

```text
Give me Codex tasks for PIT Universe Evidence Review Worklist / Real Evidence Completion Plan.
```

Expected split:

1. read-only audit,
2. worklist/template implementation,
3. index/health/status and research-status/checkpoint if implementation proceeds.
