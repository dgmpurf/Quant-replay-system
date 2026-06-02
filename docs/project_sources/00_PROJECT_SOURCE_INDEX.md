# Quant Replay System Project Source Pack Index

> Status: working memory document  
> Last generated: 2026-06-02  
> Intended use: replace the previous Project Source Pack after the v1.5.0 PIT universe export-staging checkpoint.  
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
- the v1.2.0 PIT universe export-readiness milestone;
- the v1.3.0 PIT universe evidence completion helper milestone;
- the v1.4.0 PIT universe required metadata support milestone;
- the v1.5.0 guarded PIT universe export staging milestone;
- factor taxonomy source materials for China A-share event-driven and industry-chain quantitative research.

## Accuracy Note

This pack does not replace the source code, formal repository docs, or actual local artifacts.

Many local outputs under `outputs/`, `data/raw/`, `data/cache`, and `data/processed` are intentionally ignored by Git and are not always available to ChatGPT. When local artifact state matters, the user should paste Codex summaries or run local CLI/status checks.

## Current Pack Documents

| File | Purpose | Replace When |
|---|---|---|
| `00_PROJECT_SOURCE_INDEX.md` | Index and update rules for Project Sources. | Any major Project Source structure change. |
| `01_PROJECT_VISION_AND_BOUNDARIES.md` | Product north star, stages, and safety boundaries. | Product boundary changes, real delivery, broker, automation, or international expansion begins. |
| `02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md` | Architecture map and completed workflow chains. | New major workflow chain added. |
| `03_ROADMAP_AND_NEXT_DECISION_POINTS.md` | Current roadmap and decision gates. | Next major blocker or branch changes. |
| `04_FREE_FIRST_DATA_SOURCE_STRATEGY.md` | Free-first external data strategy. | Paid source purchased, free source fails, or external data plan changes materially. |
| `05_CODEX_OPERATING_PROTOCOL.md` | Codex/ChatGPT workflow and safety protocol. | User workflow preferences or validation rules change. |
| `06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md` | Artifact, checkpoint, active/legacy, plan-only, review-only, export-readiness, and staging governance. | New artifact category or status/actionability semantics change. |
| `07_CURRENT_STATE_SNAPSHOT.md` | Current project status snapshot. | Every major checkpoint or stage transition. |
| `FACTOR_TAXONOMY_SUMMARY.md` | Concise factor-taxonomy guide for future schema/event/factor work. | Factor taxonomy changes materially. |
| `FACTOR_TAXONOMY_V2_CANONICAL.md` | Full canonical factor taxonomy, if included separately. | Canonical taxonomy version changes. |
| `FACTOR_TAXONOMY_V2_RAW_EXCEL_EXPORT.md` | Optional raw Excel-conversion reference. | Raw reference is regenerated. |
| `中国事件驱动与产业链量化系统的因子分层框架研究.md` | Strategic rationale for China event-driven/industry-chain factor layering. | Strategy framework changes materially. |

## Recommended Project Source Set After v1.5.0

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

The project has reached a guarded PIT universe export-staging checkpoint:

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
→ index / health / status / research-status context
```

The current PIT universe state is:

```text
PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS
```

Latest known active PIT universe artifacts:

```text
review_id: 7bc8ba08bf5a
export_readiness_id: 75c6975e93e4
helper_id: 4cf008a09f04
staging_id: 41bfd31a9e2c
approved rows: 0
export-ready rows: 0
staged rows: 0
blocked rows: 72
```

A diagnostic synthetic path proved that a complete reviewed row with required metadata can become `export_ready=true` in an isolated readiness artifact, but the active workflow remains blocked because the real active review has zero approved rows.

## Current Recommended Next Branch

```text
PIT Universe Evidence Review Worklist / Real Evidence Completion Plan
```

The next branch should help the user fill real PIT evidence fields safely. It should remain local and reviewed. It should not export usable universe files, run `current-candidates`, build snapshots, compute forward returns, mutate cache, send messages, or connect to brokers.

## When to Add a New Source Document

Add a new source document when a topic becomes too important to live only in chat, such as:

- real PIT universe evidence review workflow;
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

- Justify live trading.
- Treat demo artifacts as strategy recommendations.
- Treat review templates, reviewed artifacts, export-readiness artifacts, or staging artifacts as generated candidates.
- Treat approved PIT universe rows as exported usable universe files unless an explicit accepted export workflow says so.
- Treat staging preview files under `outputs/reports` as accepted local universe input.
- Skip point-in-time checks.
- Skip data quality or snapshot quality.
- Ignore source policy and provenance.
- Approve real message delivery or broker automation.
- Commit generated cache/raw/output artifacts.
