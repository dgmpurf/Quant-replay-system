# Source Update Notes for v1.0.0

## Replace These Project Sources Now

```text
00_PROJECT_SOURCE_INDEX.md
02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md
03_ROADMAP_AND_NEXT_DECISION_POINTS.md
06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md
07_CURRENT_STATE_SNAPSHOT.md
```

## Add This New Project Source

```text
FACTOR_TAXONOMY_SUMMARY.md
```

## Keep Existing Sources Unless You Want to Refresh Everything

```text
01_PROJECT_VISION_AND_BOUNDARIES.md
04_FREE_FIRST_DATA_SOURCE_STRATEGY.md
05_CODEX_OPERATING_PROTOCOL.md
FACTOR_TAXONOMY_V2_CANONICAL.md
FACTOR_TAXONOMY_V2_RAW_EXCEL_EXPORT.md
中国事件驱动与产业链量化系统的因子分层框架研究.md
```

## Do Not Add As Project Sources Unless Needed

```text
factor_taxonomy_generation_report.md
factor_definition_seed.csv
outputs/reports/*
data/cache/*
data/raw/*
data/processed/*
```

`factor_definition_seed.csv` is useful for the repository and future schema work, but Project Source use is optional.

## Why This Update Is Needed

The old source pack described the next branch as PIT universe overlay planning and the current blocker as raw `BLOCKED_UNIVERSE_AS_OF`.

The project has now completed:

```text
PIT universe overlay plan
→ index / health / status
→ research-status integration
```

The next branch is now:

```text
Reviewed PIT Universe Overlay Approval Workflow v0.1
```

## Next Time to Update Sources

Update again after one of these happens:

- reviewed PIT universe approval workflow is implemented;
- per-date snapshot preparation begins;
- current-candidates backfill runner is implemented;
- forward-return labels are introduced;
- fundamental data schema begins;
- news/event context begins;
- real alert delivery or broker integration is discussed.
