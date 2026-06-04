# Quant Replay System Project Source Pack Index

> Status: working memory document  
> Last generated: 2026-06-04  
> Intended use: replace previous Project Source Pack after v1.14.0 PIT evidence checklist validator checkpoint.  
> Permanence: temporary and replaceable. Refresh only after major checkpoint / stage changes, not after every small audit.

## Purpose

This pack condenses the current `quant-replay-system` direction, engineering state, artifact governance rules, and roadmap for ChatGPT Project Sources.

It is designed to reduce reliance on a very long chat transcript and help future ChatGPT/Codex sessions recover the current project state quickly.

## Source Basis

This pack is based on:

- the long ChatGPT/Codex collaboration history;
- repository docs for `dgmpurf/Quant-replay-system`;
- v1.0.0 research infrastructure;
- v1.1.0 reviewed PIT universe overlay approval workflow;
- v1.2.0 PIT universe export-readiness;
- v1.3.0 PIT universe evidence completion helper;
- v1.4.0 PIT universe required metadata support;
- v1.5.0 guarded PIT universe export staging;
- v1.6.0 PIT universe evidence review worklist;
- v1.7.0 PIT universe evidence update ingestion validator;
- v1.8.0 universe profile policy audit;
- v1.9.0 universe profile split-worklist planning;
- v1.10.0 reviewed replacement worklist planning;
- v1.11.0 reviewed replacement worklist acceptance;
- v1.12.0 guarded reviewed replacement worklist activation;
- v1.13.0 activated replacement worklist evidence update planning;
- v1.14.0 PIT evidence checklist validator;
- China A-share event-driven and industry-chain factor taxonomy sources.

## Accuracy Note

This pack does not replace source code, formal repository docs, or actual local artifacts.

Many local outputs under `outputs/`, `data/raw/`, `data/cache`, and `data/processed` are intentionally ignored by Git and may not be available to ChatGPT. When local artifact state matters, the user should paste Codex summaries or run local CLI/status checks.

## Current Project Source Set

Replace these after v1.14.0:

```text
00_PROJECT_SOURCE_INDEX.md
02_SYSTEM_ARCHITECTURE_AND_WORKFLOW_MAP.md
03_ROADMAP_AND_NEXT_DECISION_POINTS.md
06_CHECKPOINT_AND_ARTIFACT_GOVERNANCE.md
07_CURRENT_STATE_SNAPSHOT.md
```

Keep unless changed:

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

The project has reached a PIT evidence checklist validator checkpoint:

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
→ PIT universe evidence review worklist
→ PIT universe evidence update ingestion
→ universe profile policy audit
→ universe profile split-worklist plan
→ reviewed replacement worklist plan
→ reviewed replacement worklist acceptance
→ guarded reviewed replacement worklist activation
→ activated replacement worklist evidence update plan
→ Codex-driven diagnostics evidence discovery and gap closure
→ strict PIT evidence checklist
→ pit-evidence-checklist-validator
→ index / health / status / research-status context
```

Current PIT evidence checklist validation state:

```text
PIT_EVIDENCE_CHECKLIST_VALIDATION_BLOCKED
```

Latest known active / planning artifacts:

```text
review_id: 7bc8ba08bf5a
export_readiness_id: 75c6975e93e4
helper_id: 4cf008a09f04
staging_id: 41bfd31a9e2c
legacy_worklist_id: 1c7972988f59
ingestion_id: 284058e7f1e4
policy_audit_id: 844794b3aae1
split_plan_id: db2c09268c14
replacement_plan_id: 0774d0a1fdb9
acceptance_id: c723c0c476b1
activation_id: a8e74161f9bb
evidence_update_plan_id: 4e268d67bd7d
latest_diagnostics_ingestion_id: 734f3a722ddf
validator_id: 62e9eb747197
```

Current evidence and validator counts:

```text
approved rows: 0
export-ready rows: 0
staged rows: 0
clean ready review updates: 0
worklist rows: 72
needs evidence rows: 72
future-dated hints: 72
authoritative hints: 0

legacy mixed-demo rows: 72
STOCK rows: 56
ETF rows: 16
future stock_core replacement rows: 56
future etf_core replacement rows: 16
future mixed_demo_core rows: 0
active legacy worklist mutated: false
acceptance_acknowledged: true
activation_created_as_planning_context: true

activated evidence update plan:
  stock_core rows: 56
  etf_core rows: 16
  mixed_demo_core rows: 0
  stock first-batch package rows: 8
  ETF first-batch package rows: 8
  clean_review_updates_created: false

Codex diagnostics first batch:
  inspected rows: 16
  diagnostics ingestion ready_for_review_update_count: 16
  diagnostics ingestion blocked_count: 0
  approval_requested_count: 0
  approved_ready_count: 0

strict checklist validator:
  validator_id: 62e9eb747197
  row_count: 16
  checklist_pass_count: 0
  blocked_count: 16
  stock_core_blocked_count: 8
  etf_core_blocked_count: 8
```

Key conclusion:

```text
Existing etf_core artifacts are legacy_mixed_demo_universe / POLICY_AMBIGUOUS_DEMO_MIXED_UNIVERSE.
They are not ETF-only artifacts.
They should not be mutated in place.
Replacement worklist planning creates future stock_core and etf_core templates under outputs/reports only.
Reviewed replacement worklist acceptance acknowledges those templates as planning context only.
Guarded activation creates separate planning artifacts for stock_core and etf_core evidence work, but still does not approve rows, export universe files, or replace the legacy active worklist.
Activated replacement worklist evidence update planning creates profile-specific evidence packages and first-batch packages, but does not create clean review_updates.csv or apply approvals.
Codex diagnostics can create NEEDS_MORE_EVIDENCE draft updates and validate ingestion schema, but no row currently passes the strict PIT evidence checklist.
```

## Current Recommended Next Branch

```text
Codex-Driven Official Evidence Acquisition for Checklist Blockers v0.1
```

This branch should use Codex to target the exact blockers exposed by `pit-evidence-checklist-validator`:

```text
official/public source discovery for active/not-delisted/ST/survivorship/timing evidence
→ evidence source records
→ updated draft completed CSV only if evidence is real
→ diagnostics-only ingestion validation
→ checklist validator rerun
```

It should remain diagnostics/report-only first. It must not approve rows, reject rows, mutate active worklists, export usable universe files, write `data/raw` or `data/processed`, run `current-candidates`, build snapshots, compute forward returns, mutate cache, send messages, or connect to brokers.

User preference: if a step looks manual, first try to make Codex perform local/public evidence discovery, draft artifact generation, and validation. The user should only intervene for final evidence acceptance, credentials, CAPTCHA/login/paywall, or subjective judgment.

## When to Add or Replace Source Documents

Do not update Source after every audit or small implementation.

Add or replace Source when:

- a full milestone/checkpoint/tag is accepted;
- a new artifact workflow lands with index/health/status/research-status;
- current stage or next branch changes;
- artifact governance or safety boundaries change;
- major external data, alert, broker, snapshot, or forward-label semantics are introduced.

Add a new source document when a topic becomes too important to live only in chat, such as:

- official evidence acquisition and PIT checklist satisfaction semantics;
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

- justify live trading;
- treat worklist rows as reviewed evidence;
- treat policy audit, split guidance, replacement worklist plans, replacement acceptance artifacts, activation artifacts, evidence update plans, evidence packages, or checklist validator outputs as usable universe input;
- treat evidence packages as clean `review_updates.csv`;
- treat checklist pass as applied approval;
- treat staging preview files as accepted local universe input;
- treat approved PIT universe rows as exported usable universe files unless a future accepted export workflow says so;
- treat legacy `etf_core` artifacts as ETF-only;
- mutate active worklists without an explicit guarded workflow;
- skip point-in-time checks;
- skip data/snapshot quality;
- approve real message delivery or broker automation;
- commit generated cache/raw/output artifacts.
