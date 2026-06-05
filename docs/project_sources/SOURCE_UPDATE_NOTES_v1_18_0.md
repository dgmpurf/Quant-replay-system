# Source Update Notes v1.18.0

> Generated for Project Source replacement after the PIT official status evidence packet enrichment checkpoint.

## Replace These Files

```text
00_PROJECT_SOURCE_INDEX.md
02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md
03_ROADMAP_AND_NEXT_DECISION_POINTS.md
06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md
07_CURRENT_STATE_SNAPSHOT.md
```

## Keep These Files

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
PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_ENRICHMENT_BLOCKED
```

Latest enrichment context:

```text
enrichment_id: cb5f323d3c8c
source_packet_id: 8efabe2ffe62
reviewed_no_hit_policy_comparison_id: c1a75d1091c6
strong_official_same_date_quotation_count: 16
reviewed_no_hit_context_supported_count: 16
reviewer_acceptance_required_count: 16
checklist_pass_count: 0
remaining_blocked_count: 16
```

## Meaning

The enrichment milestone folds SZSE 1815 same-date quotation evidence and reviewed no-hit support context into a report-only evidence packet enrichment.

It does not approve PIT rows, does not run PIT review, does not export universe files, does not write `data/raw` or `data/processed`, and does not generate current-candidates.

## Next Branch

```text
Reviewer No-Hit Source Coverage Acceptance Read-only Audit v0.1
```

Purpose:

- define how a reviewer can explicitly accept no-hit source coverage and query windows;
- define survivorship rationale requirements;
- keep acceptance separate from PIT row approval;
- remain read-only / diagnostics-first before any implementation.
