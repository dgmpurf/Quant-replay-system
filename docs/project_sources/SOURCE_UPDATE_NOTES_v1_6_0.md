# Source Update Notes v1.6.0

## Why This Update Exists

The previous Project Source set reflected the v1.5.0 guarded PIT universe export-staging checkpoint.

The project has now completed the PIT Universe Evidence Review Worklist v0.1 milestone:

```text
pit-universe-evidence-review-worklist
→ index / health / status
→ research-status integration
→ v1.6.0 checkpoint
```

## Replace These Project Source Files

```text
00_PROJECT_SOURCE_INDEX.md
02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md
03_ROADMAP_AND_NEXT_DECISION_POINTS.md
06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md
07_CURRENT_STATE_SNAPSHOT.md
```

## Keep These Existing Source Files

```text
01_PROJECT_VISION_AND_BOUNDARIES.md
04_FREE_FIRST_DATA_SOURCE_STRATEGY.md
05_CODEX_OPERATING_PROTOCOL.md
FACTOR_TAXONOMY_SUMMARY.md
FACTOR_TAXONOMY_V2_CANONICAL.md
FACTOR_TAXONOMY_V2_RAW_EXCEL_EXPORT.md
中国事件驱动与产业链量化系统的因子分层框架研究.md
```

## New Current State

```text
worklist_id: 1c7972988f59
review_id: 7bc8ba08bf5a
helper_id: 4cf008a09f04
export_readiness_id: 75c6975e93e4
staging_id: 41bfd31a9e2c

worklist rows: 72
symbols: 9
signal dates: 8
needs evidence rows: 72
future-dated hints: 72
authoritative hints: 0
approved rows: 0
export-ready rows: 0
staged rows: 0
```

## New Recommended Next Branch

```text
Reviewed PIT Universe Evidence Update Ingestion Read-only Audit v0.1
```

This branch should remain read-only first.

It should not approve rows automatically, export universe files, write `data/raw`, write `data/processed`, run `current-candidates`, build snapshots, compute forward labels, send messages, or connect to brokers.
