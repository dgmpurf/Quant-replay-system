# Source Update Notes v1.5.0

This package updates Project Sources after the guarded PIT universe export staging milestone.

## Replace These Project Sources

```text
00_PROJECT_SOURCE_INDEX.md
02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md
03_ROADMAP_AND_NEXT_DECISION_POINTS.md
06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md
07_CURRENT_STATE_SNAPSHOT.md
```

## Keep Existing Sources

```text
01_PROJECT_VISION_AND_BOUNDARIES.md
04_FREE_FIRST_DATA_SOURCE_STRATEGY.md
05_CODEX_OPERATING_PROTOCOL.md
FACTOR_TAXONOMY_SUMMARY.md
FACTOR_TAXONOMY_V2_CANONICAL.md
FACTOR_TAXONOMY_V2_RAW_EXCEL_EXPORT.md
中国事件驱动与产业链量化系统的因子分层框架研究.md
```

## Why This Update Exists

The previous source pack described the project around reviewed PIT universe approval and export-readiness. Since then, the project completed:

```text
PIT universe export-readiness
→ evidence completion helper
→ required metadata support
→ guarded export staging
→ staging index / health / status
→ research-status integration
→ v1.5.0 checkpoint
```

The new active PIT universe state is:

```text
PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS
```

## Current Active IDs

```text
review_id: 7bc8ba08bf5a
export_readiness_id: 75c6975e93e4
helper_id: 4cf008a09f04
staging_id: 41bfd31a9e2c
```

## Current Meaning

The staging path exists, but the real active workflow still has:

```text
approved rows: 0
export-ready rows: 0
staged rows: 0
blocked rows: 72
```

A synthetic diagnostic showed that a complete reviewed row with all required metadata can become export-ready, but diagnostics do not activate the workflow.

## Next Recommended Branch

```text
PIT Universe Evidence Review Worklist / Real Evidence Completion Plan
```

This branch should help the user complete real PIT evidence fields. It should not export usable universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, compute forward returns, send messages, or connect to brokers.
