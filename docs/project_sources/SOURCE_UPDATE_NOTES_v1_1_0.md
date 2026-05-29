# Source Update Notes v1.1.0

> Generated for the Quantitative Trading Project Source set after the reviewed PIT universe overlay approval workflow checkpoint.

## Replace These Project Source Files

Replace the previous versions with the files in this update package:

```text
00_PROJECT_SOURCE_INDEX.md
02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md
03_ROADMAP_AND_NEXT_DECISION_POINTS.md
06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md
07_CURRENT_STATE_SNAPSHOT.md
```

## Keep Existing Files

These do not need replacement for this update:

```text
01_PROJECT_VISION_AND_BOUNDARIES.md
04_FREE_FIRST_DATA_SOURCE_STRATEGY.md
05_CODEX_OPERATING_PROTOCOL.md
FACTOR_TAXONOMY_SUMMARY.md
FACTOR_TAXONOMY_V2_CANONICAL.md
FACTOR_TAXONOMY_V2_RAW_EXCEL_EXPORT.md
中国事件驱动与产业链量化系统的因子分层框架研究.md
```

## Why This Update Is Needed

The previous source set described the next branch as Reviewed PIT Universe Overlay Approval Workflow.

That workflow is now implemented:

```text
pit-universe-overlay-review
→ index / health / status
→ research-status integration
→ v1.1.0 checkpoint
```

The current active state is now:

```text
PIT_UNIVERSE_OVERLAY_REVIEW_NEEDS_MORE_EVIDENCE
```

Latest known review:

```text
review_id: 7bc8ba08bf5a
rows: 72
approved rows: 0
valid_for_signal_date rows: 0
unresolved survivorship warnings: 72
```

The next branch is now:

```text
Reviewed PIT Universe Overlay Export Readiness Read-only Audit v0.1
```

## What Did Not Change

The project is still not a live trading system.

No source update should imply:

- current-candidates were generated,
- snapshot manifests were built,
- forward labels were computed,
- usable universe files were exported,
- non-demo signal thresholds changed,
- real messages were sent,
- broker integration exists.

## Next Source Refresh Trigger

Refresh Project Source again after one of these happens:

- PIT universe export readiness workflow is implemented and integrated;
- approved PIT universe rows are produced;
- usable universe export is implemented;
- per-date snapshot preparation starts;
- multi-date current-candidates runner starts;
- forward-return labels start;
- external fundamental/news/event schema work starts.
