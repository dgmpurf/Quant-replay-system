# Quant Replay System Project Source Pack Index

> Status: working memory document  
> Last generated: 2026-06-02  
> Intended use: replace previous Project Source Pack after v1.9.0 universe profile split-worklist planning checkpoint.  
> Permanence: temporary and replaceable. Refresh when the project changes stage.

## Purpose

This pack condenses the current `quant-replay-system` direction, engineering state, artifact governance rules, and roadmap for ChatGPT Project Sources.

It is designed to reduce reliance on a very long chat transcript and help future ChatGPT/Codex sessions recover the current project state quickly.

## Source Basis

This pack is based on:

- the long ChatGPT/Codex collaboration history;
- repository docs for `dgmpurf/Quant-replay-system`;
- v1.0.0 research infrastructure;
- v1.1.0 reviewed PIT universe overlay approval workflow;
- v1.2.0 PIT universe export-readiness;
- v1.3.0 PIT universe evidence completion helper;
- v1.4.0 PIT universe required metadata support;
- v1.5.0 guarded PIT universe export staging;
- v1.6.0 PIT universe evidence review worklist;
- v1.7.0 PIT universe evidence update ingestion validator;
- v1.8.0 universe profile policy audit;
- v1.9.0 universe profile split-worklist planning;
- China A-share event-driven and industry-chain factor taxonomy sources.

## Accuracy Note

This pack does not replace source code, formal repository docs, or actual local artifacts.

Many local outputs under `outputs/`, `data/raw/`, `data/cache`, and `data/processed` are intentionally ignored by Git and may not be available to ChatGPT. When local artifact state matters, the user should paste Codex summaries or run local CLI/status checks.

## Current Project Source Set

Replace these after v1.9.0:

```text
00_PROJECT_SOURCE_INDEX.md
02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md
03_ROADMAP_AND_NEXT_DECISION_POINTS.md
06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md
07_CURRENT_STATE_SNAPSHOT.md
```

Keep unless changed:

```text
01_PROJECT_VISION_AND_BOUNDARIES.md
04_FREE_FIRST_DATA_SOURCE_STRATEGY.md
05_CODEX_OPERATING_PROTOCOL.md
FACTOR_TAXONOMY_SUMMARY.md
FACTOR_TAXONOMY_V2_CANONICAL.md
FACTOR_TAXONOMY_V2_RAW_EXCEL_EXPORT.md
中国事件驱动与产业链量化系统的因子分层框架研究.md
```

## Current Project State Summary

The project has reached a universe profile split-worklist planning checkpoint:

```text
local market data / reviewed exports / quality gates
→ current-candidates
→ signal semantics / advisory layers
→ calibration tooling
→ multi-date backfill planning
→ execution readiness manifest
→ PIT universe overlay preparation plan
→ reviewed PIT universe overlay approval workflow
→ PIT universe export-readiness
→ PIT universe evidence completion helper
→ required metadata support
→ guarded PIT universe export staging
→ PIT universe evidence review worklist
→ PIT universe evidence update ingestion
→ universe profile policy audit
→ universe profile split-worklist plan
→ index / health / status / research-status context
```

Current universe governance state:

```text
UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_HAS_PROFILE_CONFLICTS
```

Latest known active PIT universe artifacts:

```text
review_id: 7bc8ba08bf5a
export_readiness_id: 75c6975e93e4
helper_id: 4cf008a09f04
staging_id: 41bfd31a9e2c
worklist_id: 1c7972988f59
ingestion_id: 284058e7f1e4
policy_audit_id: 844794b3aae1
split_plan_id: db2c09268c14

approved rows: 0
export-ready rows: 0
staged rows: 0
worklist rows: 72
needs evidence rows: 72
future-dated hints: 72
authoritative hints: 0

legacy mixed-demo rows: 72
STOCK rows: 56
ETF rows: 16
recommended future stock_core rows: 56
recommended future etf_core rows: 16
recommended future mixed_demo_core rows: 0
profile conflicts: 56
```

Key conclusion:

```text
Existing etf_core artifacts are legacy_mixed_demo_universe / POLICY_AMBIGUOUS_DEMO_MIXED_UNIVERSE.
They are not ETF-only artifacts.
They should not be mutated in place.
```

## Current Recommended Next Branch

```text
Reviewed Replacement Worklist Planning Read-only Audit v0.1
```

This branch should audit how to create future replacement worklist templates for `stock_core`, `etf_core`, and possibly `mixed_demo_core` while leaving active artifacts untouched.

It should remain read-only first. It must not approve rows, reject rows, mutate active worklists, export usable universe files, write `data/raw` or `data/processed`, run `current-candidates`, build snapshots, compute forward returns, mutate cache, send messages, or connect to brokers.

## When to Add a New Source Document

Add a new source document when a topic becomes too important to live only in chat, such as:

- accepted PIT universe export workflow;
- per-date snapshot preparation;
- forward-return labels;
- historical signal outcomes;
- fundamental data schema and quality gates;
- news/event context;
- alert delivery safety;
- broker integration readiness;
- international market expansion.

## Do Not Use This Pack To

- justify live trading;
- treat worklist rows as reviewed evidence;
- treat policy audit or split guidance as active universe replacement;
- treat staging preview files as accepted local universe input;
- treat approved PIT universe rows as exported usable universe files unless a future accepted export workflow says so;
- treat legacy `etf_core` artifacts as ETF-only;
- mutate active worklists without an explicit reviewed replacement workflow;
- skip point-in-time checks;
- skip data/snapshot quality;
- approve real message delivery or broker automation;
- commit generated cache/raw/output artifacts.
