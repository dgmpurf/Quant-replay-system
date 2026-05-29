# Quant Replay System Project Source Pack Index

> Status: working memory document  
> Last generated: 2026-05-29  
> Intended use: replace the previous Project Source Pack after the v1.1.0 reviewed PIT-universe approval checkpoint.  
> Permanence: temporary and replaceable. Refresh when the project changes stage.

## Purpose

This pack condenses the current `quant-replay-system` project direction, engineering state, artifact governance rules, and near-term roadmap into a small set of Markdown files for ChatGPT Project Sources.

It is designed to reduce reliance on a very long chat transcript and help future ChatGPT/Codex sessions recover the current project state quickly.

## Source Basis

This pack is based on:

- the long ChatGPT/Codex collaboration history;
- the GitHub repository `dgmpurf/Quant-replay-system`;
- the project README and docs;
- the v1.0.0 research-infrastructure milestone;
- the v1.1.0 reviewed PIT universe overlay approval workflow milestone;
- factor taxonomy source materials for China A-share event-driven and industry-chain quantitative research.

## Accuracy Note

This pack does not replace the source code, formal repository docs, or actual local artifacts.

Many local outputs under `outputs/`, `data/raw/`, `data/cache/`, and `data/processed/` are intentionally ignored by Git and are not always available to ChatGPT. When local artifact state matters, the user should paste Codex summaries or run local CLI/status checks.

## Current Pack Documents

| File | Purpose | Replace When |
|---|---|---|
| `00_PROJECT_SOURCE_INDEX.md` | Index and update rules for Project Sources. | Any major Project Source structure change. |
| `01_PROJECT_VISION_AND_BOUNDARIES.md` | Product north star, stages, and safety boundaries. | Product boundary changes, real delivery, broker, automation, or international expansion begins. |
| `02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md` | Architecture map and completed workflow chains. | New major workflow chain added. |
| `03_ROADMAP_AND_NEXT_DECISION_POINTS.md` | Current roadmap and decision gates. | Next major blocker or branch changes. |
| `04_FREE_FIRST_DATA_SOURCE_STRATEGY.md` | Free-first external data strategy. | Paid source purchased, free source fails, or external data plan changes materially. |
| `05_CODEX_OPERATING_PROTOCOL.md` | Codex/ChatGPT workflow and safety protocol. | User workflow preferences or validation rules change. |
| `06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md` | Artifact, checkpoint, active/legacy, plan-only, review-only, and export-readiness governance. | New artifact category or status/actionability semantics change. |
| `07_CURRENT_STATE_SNAPSHOT.md` | Current project status snapshot. | Every major checkpoint or stage transition. |
| `FACTOR_TAXONOMY_SUMMARY.md` | Concise factor-taxonomy guide for future schema/event/factor work. | Factor taxonomy changes materially. |
| `FACTOR_TAXONOMY_V2_CANONICAL.md` | Full canonical factor taxonomy, if included separately. | Canonical taxonomy version changes. |
| `FACTOR_TAXONOMY_V2_RAW_EXCEL_EXPORT.md` | Optional raw Excel-conversion reference. | Raw reference is regenerated. |
| `中国事件驱动与产业链量化系统的因子分层框架研究.md` | Strategic rationale for China event-driven/industry-chain factor layering. | Strategy framework changes materially. |

## Recommended Project Source Set After v1.1.0

Replace or add these now:

```text
00_PROJECT_SOURCE_INDEX.md
02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md
03_ROADMAP_AND_NEXT_DECISION_POINTS.md
06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md
07_CURRENT_STATE_SNAPSHOT.md
```

Keep existing unless changed:

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

The project has reached a reviewed PIT-universe approval workflow checkpoint:

```text
local market data / reviewed exports / quality gates
→ current-candidates
→ signal semantics / advisory layers
→ calibration tooling
→ multi-date backfill planning
→ execution readiness manifest
→ PIT universe overlay preparation plan
→ reviewed PIT universe overlay approval workflow
→ index / health / status / research-status context
```

The current PIT universe state is:

```text
PIT_UNIVERSE_OVERLAY_REVIEW_NEEDS_MORE_EVIDENCE
```

Latest known PIT universe overlay review:

```text
review_id: 7bc8ba08bf5a
rows: 72
approved rows: 0
valid_for_signal_date rows: 0
needs manual review rows: 72
unresolved survivorship warnings: 72
```

## Current Recommended Next Branch

```text
Reviewed PIT Universe Overlay Export Readiness Read-only Audit v0.1
```

This branch should remain read-only first. It should not export usable universe files, run `current-candidates`, build snapshots, compute forward returns, mutate cache, send messages, or connect to brokers.

## When to Add a New Source Document

Add a new source document when a topic becomes too important to live only in chat, such as:

- reviewed PIT universe export readiness and export workflow;
- per-date snapshot preparation;
- forward-return labels;
- historical signal outcomes;
- fundamental data schema and quality gates;
- news/event context;
- alert delivery safety;
- broker integration readiness;
- international market expansion.

## Do Not Use This Pack To

- Justify live trading.
- Treat demo artifacts as strategy recommendations.
- Treat review templates or reviewed artifacts as generated candidates.
- Treat approved PIT universe rows as exported usable universe files unless an explicit export workflow says so.
- Skip point-in-time checks.
- Skip data quality or snapshot quality.
- Ignore source policy and provenance.
- Approve real message delivery or broker automation.
- Commit generated cache/raw/output artifacts.
