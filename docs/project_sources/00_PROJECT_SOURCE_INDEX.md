# Quant Replay System Project Source Pack Index

> Status: working memory document  
> Last generated: 2026-05-28  
> Intended use: add to ChatGPT Project Sources or keep under a local planning folder.  
> Permanence: temporary and replaceable. These documents should be refreshed as the project changes.

## Purpose

This pack condenses the long ChatGPT/Codex collaboration history, current GitHub project shape, and active product direction into a small set of Markdown files.

The goal is to make future sessions easier by giving ChatGPT and Codex stable project context without relying on a long chat transcript.

## Source Basis

This pack is based on:

- The long project conversation in this ChatGPT thread.
- The GitHub repository discovered as `dgmpurf/Quant-replay-system`.
- The GitHub README, which describes the project as a point-in-time historical replay quant research system for China A-share ETFs and stocks and explicitly states that it is not an automatic trading bot or broker auto-order system.
- The GitHub `docs/product_vision.md`, which states that the near-term goal is quantitative research plus signal advisory plus human-confirmed execution.
- The GitHub `docs/PROCESS.md`, which defines the Codex/ChatGPT workflow, testing standards, checkpoint documentation rules, Git safety rules, and safety boundaries.

## Important Accuracy Note

This pack does not replace the repository source code or official project docs. It is a high-level project memory layer.

It may not include every local ignored artifact because many local files under `outputs/`, `data/raw/`, `data/cache/`, and `data/processed/` are intentionally ignored and not available through GitHub. Those local artifacts should remain untracked unless explicitly reviewed.

## Documents in This Pack

| File | Purpose |
|---|---|
| `00_PROJECT_SOURCE_INDEX.md` | Index, usage guidance, and update triggers. |
| `01_PROJECT_VISION_AND_BOUNDARIES.md` | Product north star, stages, safety boundaries, and what “full automation” means. |
| `02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md` | Current architecture from data sources to cache, candidates, semantics, advisory, paper workflow, dashboards, and backfill planning. |
| `03_ROADMAP_AND_NEXT_DECISION_POINTS.md` | Near-term roadmap, current blockers, likely next branches, and what should happen before external data/news/fundamentals. |
| `04_FREE_FIRST_DATA_SOURCE_STRATEGY.md` | Free-first data source plan for market data, fundamentals, announcements, and news/event context. |
| `05_CODEX_OPERATING_PROTOCOL.md` | How to queue Codex tasks, how to split large tasks, validation expectations, and Git safety. |
| `06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md` | Checkpoint/tag philosophy, artifact health/status rules, legacy/stale artifact treatment, and when to refresh docs. |
| `07_CURRENT_STATE_SNAPSHOT.md` | Condensed current-state snapshot at the time this pack was generated. |

## How to Use

Recommended options:

1. Add these files to ChatGPT Project Sources.
2. Keep them in a local folder such as `docs/project_sources/`.
3. Do not treat them as permanent truth. Treat them as a compact memory snapshot.

## When to Replace This Pack

Replace or regenerate this pack when any of these happen:

- A major release checkpoint is completed.
- The project moves from planning-only to actual multi-date candidate generation.
- Fundamental data ingestion starts.
- News/event ingestion starts.
- Real alert delivery is introduced.
- Broker integration or execution automation is discussed.
- The project changes from demo/synthetic validation to non-demo research signals.
- `research-status` semantics change materially.
- Data source strategy changes because a paid vendor is purchased or abandoned.
- The GitHub repository has changed significantly from the state summarized here.

## When to Add a New Source Document

Add a new project source document when a topic becomes too important to live only in the chat, for example:

- Fundamental data schema and quality gates.
- News/event data schema and risk context.
- Forward-return labeling.
- Historical signal outcome datasets.
- Real alert delivery safety.
- Broker integration readiness.
- International market expansion.

## Do Not Use This Pack To

- Justify live trading.
- Treat demo artifacts as strategy recommendations.
- Skip point-in-time checks.
- Skip data quality or snapshot quality.
- Ignore source policy and provenance.
- Approve real message delivery or broker automation.
- Commit generated cache/raw/output artifacts.
