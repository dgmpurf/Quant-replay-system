# Source Update Notes v1.10.0

## Why this update exists

The previous Project Source pack described v1.9.0 universe profile split-worklist planning as the current milestone. The project has now completed v1.10.0 Reviewed Replacement Worklist Planning.

The updated source pack records:

- `reviewed-replacement-worklist-plan` is implemented;
- replacement plan artifact id: `0774d0a1fdb9`;
- future `stock_core` replacement rows: 56;
- future `etf_core` replacement rows: 16;
- future `mixed_demo_core` rows: 0;
- active legacy worklist remains unchanged;
- no approvals, rejections, exports, snapshots, current-candidates, or forward labels were produced.

## Files to replace

Replace these Project Source files:

```text
00_PROJECT_SOURCE_INDEX.md
02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md
03_ROADMAP_AND_NEXT_DECISION_POINTS.md
06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md
07_CURRENT_STATE_SNAPSHOT.md
```

Keep these unchanged unless independently modified:

```text
01_PROJECT_VISION_AND_BOUNDARIES.md
04_FREE_FIRST_DATA_SOURCE_STRATEGY.md
05_CODEX_OPERATING_PROTOCOL.md
FACTOR_TAXONOMY_SUMMARY.md
FACTOR_TAXONOMY_V2_CANONICAL.md
FACTOR_TAXONOMY_V2_RAW_EXCEL_EXPORT.md
中国事件驱动与产业链量化系统的因子分层框架研究.md
```

## New recommended next branch

```text
Reviewed Replacement Worklist Acceptance Read-only Audit v0.1
```

This next branch should remain read-only first and must not mutate active artifacts.
