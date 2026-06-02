# Quant Replay System Project Source Pack Index

> Status: working memory document  
> Last generated: 2026-06-02  
> Intended use: replace previous Project Source Pack after v1.6.0 PIT universe evidence review worklist checkpoint.  
> Permanence: temporary and replaceable. Refresh when the project changes stage.

## Purpose

This pack condenses the current `quant-replay-system` direction, engineering state, artifact governance rules, and roadmap for ChatGPT Project Sources.

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
- China A-share event-driven and industry-chain factor taxonomy sources.

## Current Project Source Set

Replace these after v1.6.0:

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

The project has reached a PIT universe evidence review worklist checkpoint:

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
→ index / health / status / research-status context
```

Current active PIT universe state:

```text
PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_NEEDS_REVIEW
```

Latest known active artifacts:

```text
review_id: 7bc8ba08bf5a
export_readiness_id: 75c6975e93e4
helper_id: 4cf008a09f04
staging_id: 41bfd31a9e2c
worklist_id: 1c7972988f59

approved rows: 0
export-ready rows: 0
staged rows: 0
worklist rows: 72
needs evidence rows: 72
future-dated hints: 72
authoritative hints: 0
```

Diagnostic synthetic tests proved a complete reviewed row with required metadata can become `export_ready=true` in isolated diagnostics, but real active artifacts remain blocked because there are no real approved rows.

## Current Recommended Next Branch

```text
Reviewed PIT Universe Evidence Update Ingestion Read-only Audit v0.1
```

This branch should audit how a reviewer-completed worklist update CSV can be validated and transformed into a review-updates artifact.

Do not approve rows automatically, export usable universe files, write `data/raw` or `data/processed`, run `current-candidates`, build snapshots, compute forward returns, mutate cache, send messages, or connect to brokers.

## Do Not Use This Pack To

- justify live trading;
- treat worklist rows as reviewed evidence;
- treat staging preview files as accepted local universe input;
- treat approved PIT universe rows as exported usable universe files unless a future accepted export workflow says so;
- skip point-in-time checks;
- skip data/snapshot quality;
- approve real message delivery or broker automation;
- commit generated cache/raw/output artifacts.
