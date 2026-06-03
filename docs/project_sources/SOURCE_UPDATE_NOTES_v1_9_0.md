# Source Update Notes v1.9.0

This update refreshes Project Sources after the Universe Profile Split-Worklist Planning v0.1 milestone.

## Replace in ChatGPT Project Source

```text
00_PROJECT_SOURCE_INDEX.md
02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md
03_ROADMAP_AND_NEXT_DECISION_POINTS.md
06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md
07_CURRENT_STATE_SNAPSHOT.md
```

## Keep Existing

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
UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_HAS_PROFILE_CONFLICTS
```

Latest known active artifacts:

```text
review_id: 7bc8ba08bf5a
export_readiness_id: 75c6975e93e4
helper_id: 4cf008a09f04
staging_id: 41bfd31a9e2c
worklist_id: 1c7972988f59
ingestion_id: 284058e7f1e4
policy_audit_id: 844794b3aae1
split_plan_id: db2c09268c14
```

Important counts:

```text
STOCK rows: 56
ETF rows: 16
legacy mixed-demo rows: 72
recommended future stock_core rows: 56
recommended future etf_core rows: 16
profile conflicts: 56
approved rows: 0
export-ready rows: 0
staged rows: 0
```

## New Recommended Next Branch

```text
Reviewed Replacement Worklist Planning Read-only Audit v0.1
```

This next branch should remain read-only first. It should not mutate active worklists, approve/reject rows, export universe files, write data/raw or data/processed, run current-candidates, build snapshots, compute forward returns, or change strategy semantics.
