# Current State Snapshot

> Status: working memory document  
> Last generated: 2026-06-12  
> Permanence: temporary; refresh after the next major checkpoint or when source state changes.

## Summary

The project is a local quantitative research, signal semantics, advisory, calibration, paper workflow, PIT evidence preparation, and historical replay training preparation system for China A-share stocks and ETFs.

It is not a live trading system.

## Strategic State

The project goal is:

```text
Personal-first, institution-grade-core.
```

The first usable version should support personal/family A-share/ETF advisory. The core must still be built for historical replay training, point-in-time validity, factor universe expansion, stock-level profiles, forward-return evaluation, research-method governance, and paper workflow validation before real buy-review eligibility.

This means:

```text
PIT universe evidence work = validity foundation for replay training.
Factor taxonomy = expandable factor universe under 8-layer skeleton.
Research method stack = broader than ML/DL/data mining or formulas/weights.
Stock profile = required before real buy-review eligibility.
Historical replay + labels + paper workflow = required before real buy-review eligibility.
```

The fixed 12-factor structure should not be treated as final. It remains a coverage checklist only.

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
- One-row material evidence fill package.
- One-row checklist-pass candidate preview.
- Reviewer-supplied material evidence candidate fixture audit.

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

### Replay Substrate Preparation

Completed as of v1.27.0:

- Historical Replay Training Substrate Read-only Architecture Audit.
- `replay-substrate-schema-fixture` report-only workflow.
- `replay-substrate-schema-fixture-index`.
- `replay-substrate-schema-fixture-health`.
- `replay-substrate-schema-fixture-status`.
- Research-status integration for replay-substrate schema fixture context.
- `docs/release_checkpoint_v1.27.0.md`.

## v1.27.0 Replay Substrate Schema Fixture State

Latest known state:

```text
fixture_id: 5f9a393ce90d
fixture_status: PASS
fixture_stage: REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY
health_status: PASS
entity_count: 14
validation_issue_count: 0
overclaim_guard_pass_count: 8
overclaim_guard_total_count: 8
active_replay_input: false
forward_labels_exist: false
weights_trained: false
active_stock_profile_exists: false
real_buy_review_eligible: false
report_only: true
diagnostic_only: true
no_live_trading: true
no_broker_api: true
no_order_placement: true
```

Research-status summary:

```text
final workflow_stage: PAPER_WORKFLOW_READY
replay substrate schema fixture appears as preparation context only
```

Interpretation:

```text
schema fixture ready
≠ active replay input
≠ real replay decision dataset
≠ forward labels
≠ weights trained
≠ active stock profile
≠ real buy-review eligibility
```

## Current Quantitative Evidence Status

Current evidence is not enough to validate non-demo buy signals.

Known gaps:

- too few dates;
- only limited symbols in local cache in prior evidence context;
- demo-only current-candidates;
- no accepted PIT universe export;
- no active accepted PIT universe input;
- no generated multi-date current-candidates from accepted PIT universe;
- no real historical replay decision dataset;
- no real factor observation dataset;
- no structured event dataset;
- no forward-return labels;
- no multi-date outcome dataset;
- no training/evaluation result dataset;
- no validated stock-level profiles;
- no real buy-review eligibility gates active;
- no linked paper outcome history for replay-trained signals.

## Current Multi-Date Backfill / PIT Evidence State

Known active / planning artifacts from the previous source pack remain context only unless later explicit workflows make them active.

Important known state:

```text
approved rows: 0
export-ready rows: 0
staged rows: 0
clean ready review updates: 0
worklist rows: 72
needs evidence rows: 72
stock_core first-batch rows: 8
etf_core first-batch rows: 8
checklist_pass_count: 0
remaining_blocked_count: 16
clean_review_updates_created: false
approval_applied: false
```

One-row checklist-pass candidate preview state from the previous source pack:

```text
ONE_ROW_CHECKLIST_PASS_CANDIDATE_PREVIEW_CONTEXT_ONLY
```

The preview is context-only and not approval.

Reviewer-supplied material evidence candidate fixture audit result reported by user:

```text
future reviewer-supplied evidence could reduce some strict gaps only as report-only preview
target row remains blocked
row_checklist_pass_candidate=false
strict_requirement_gap_count=10
remaining_blocked=true
clean_review_updates_created=false
approval_applied=false
```

## Current External Data Strategy

Budget constraint:

- free-first;
- paid vendors are future backups only.

Current recommendation:

- fundamentals before news sentiment;
- LOCAL_CSV first;
- AKShare / BaoStock / Tushare free/low-quota optional later;
- public announcement metadata later;
- news as event/risk context first, not score driver;
- raw document store and available_time metadata before historical news replay.

## Current Research Method Strategy

The project should not be framed only as:

```text
ML / DL / data mining
```

or only as:

```text
algorithms / weights / formulas
```

The future research core should combine:

```text
statistics
econometrics
financial engineering
factor research
event study
causal inference
knowledge graph / industry-chain modeling
NLP / IR / RAG
data mining
ML / DL
optimization
risk management
portfolio construction
execution modeling
replay evaluation
explainability
model governance
```

All research methods remain gated by PIT validity, source provenance, forward-label separation, out-of-sample validation, paper workflow, and human confirmation.

## Recommended Next Branch

```text
Historical Replay Substrate Readiness Plan Report-Only v0.1
```

Purpose:

- connect v1.27.0 schema fixture contracts to the next readiness plan;
- define what is required before true replay can run;
- define minimum one-stock / one-ETF replay prerequisites;
- remain diagnostics/report-only.

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
- train weights;
- create stock profiles as active eligibility artifacts;
- change non-demo thresholds;
- add news scraping;
- call LLM APIs;
- add broker integration;
- send real messages.

## Recent Important Checkpoints

Recent milestone direction:

- v1.20.0: reviewer no-hit acceptance downstream impact.
- v1.21.0: first-batch reviewer evidence completion planning.
- v1.22.0: first-batch partial completion impact.
- v1.23.0: material PIT evidence gate closure plan.
- v1.24.0: reviewer material evidence fill guidance.
- v1.25.0: one-row material evidence fill package.
- v1.26.0: one-row checklist-pass candidate preview.
- v1.27.0: replay substrate schema fixture, artifact views, research-status integration, and checkpoint docs.

## What to Ask ChatGPT Next

```text
Give me the Codex prompt for Historical Replay Substrate Readiness Plan Report-Only v0.1.
```
