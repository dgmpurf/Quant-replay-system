# Quant Replay System Project Source Pack Index

> Status: working memory document  
> Last generated: 2026-06-05  
> Intended use: replace previous Project Source Pack after v1.19.0 reviewer no-hit source coverage acceptance checkpoint.  
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
- v1.15.0 PIT evidence policy profile comparison;
- v1.16.0 PIT official status evidence packet;
- v1.17.0 reviewed no-hit support policy profile;
- v1.18.0 PIT official status evidence packet enrichment;
- v1.19.0 reviewer no-hit source coverage acceptance;
- diagnostics for SZSE 1815 same-date quotation, exception/no-hit probes, and official no-hit policy audit;
- China A-share event-driven and industry-chain factor taxonomy sources.

## Accuracy Note

This pack does not replace source code, formal repository docs, or actual local artifacts.

Many local outputs under `outputs/`, `data/raw/`, `data/cache`, and `data/processed` are intentionally ignored by Git and may not be available to ChatGPT. When local artifact state matters, the user should paste Codex summaries or run local CLI/status checks.

## Current Project Source Set

Replace these after v1.19.0:

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

The project has reached a reviewer no-hit source coverage acceptance checkpoint:

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
→ EOD_POST_CLOSE_LOW_BUDGET_PIT policy audit
→ pit-evidence-policy-profile-comparison
→ PIT official status evidence packet
→ SZSE 1815 same-date quotation probe
→ SZSE/CNInfo exception no-hit probe
→ official no-hit evidence policy audit
→ EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT policy profile
→ PIT official status evidence packet enrichment
→ reviewer-no-hit-source-coverage-acceptance
→ index / health / status / research-status context
```

Current reviewer no-hit source coverage acceptance state:

```text
REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTANCE_NEEDS_REVIEW
```

Latest known active / planning artifacts and diagnostics:

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
policy_comparison_id: 0ef6d2f3bae6
packet_id: 8efabe2ffe62
packet_rerun_ingestion_id: ac6846aef520
packet_rerun_validator_id: 498a3d0786af
packet_rerun_policy_comparison_id: b7e7ec8f66f5
reviewed_no_hit_policy_comparison_id: c1a75d1091c6
enrichment_id: cb5f323d3c8c
reviewer_no_hit_acceptance_id: 2e05e4b74794
```

Current evidence / validator / packet / policy counts:

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

EOD low-budget policy comparison:
  comparison_id: 0ef6d2f3bae6
  profile: EOD_POST_CLOSE_LOW_BUDGET_PIT
  row_count: 16
  strict_checklist_pass_count: 0
  eod_low_budget_checklist_pass_count: 0
  relaxed_blocker_count: 16
  remaining_blocked_count: 16

PIT official status evidence packet:
  packet_id: 8efabe2ffe62
  row_count: 16
  evidence_packet_row_count: 72
  strong_official_date_specific_count: 0
  supporting_official_symbol_level_count: 16
  supporting_local_eod_cache_count: 16
  missing_count: 40
  checklist_pass_count: 0
  blocked_count: 16

SZSE 1815 same-date quotation diagnostics:
  target_rows: 16
  http_200_json_parse_count: 16
  rows_found_for_000001: 8 / 8
  rows_found_for_159915: 8 / 8
  strong_official_date_specific_for_quotation_traded_presence: 16 / 16

Exception / no-hit diagnostics:
  strong_date_specific_exception_evidence_found: 0
  no_hit_observations: policy-dependent only

Reviewed no-hit support profile:
  comparison_id: c1a75d1091c6
  profile: EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT
  row_count: 16
  strict_checklist_pass_count: 0
  eod_low_budget_checklist_pass_count: 0
  reviewed_no_hit_support_pass_count: 0
  no_hit_context_supported_count: 16
  reviewer_acceptance_required_count: 16
  remaining_blocked_count: 16

PIT official status evidence packet enrichment:
  enrichment_id: cb5f323d3c8c
  source_packet_id: 8efabe2ffe62
  reviewed_no_hit_policy_comparison_id: c1a75d1091c6
  row_count: 16
  strong_official_same_date_quotation_count: 16
  reviewed_no_hit_context_supported_count: 16
  reviewer_acceptance_required_count: 16
  checklist_pass_count: 0
  remaining_blocked_count: 16

Reviewer no-hit source coverage acceptance:
  acceptance_id: 2e05e4b74794
  row_count: 64
  accepted_count: 0
  needs_review_count: 64
  reviewer_acceptance_required_count: 64
  survivorship_rationale_required_count: 16
  checklist_pass_count: 0
  remaining_blocked_count: 16
```

## Key Conclusions

```text
Existing etf_core artifacts are legacy_mixed_demo_universe / POLICY_AMBIGUOUS_DEMO_MIXED_UNIVERSE.
They are not ETF-only artifacts.
They should not be mutated in place.
```

```text
Replacement worklist planning creates future stock_core and etf_core templates under outputs/reports only.
Reviewed replacement worklist acceptance acknowledges those templates as planning context only.
Guarded activation creates separate planning artifacts for stock_core and etf_core evidence work, but still does not approve rows, export universe files, or replace the legacy active worklist.
Activated replacement worklist evidence update planning creates profile-specific evidence packages and first-batch packages, but does not create clean review_updates.csv or apply approvals.
```

```text
Codex diagnostics can create NEEDS_MORE_EVIDENCE draft updates and validate ingestion schema, but no row currently passes the strict PIT evidence checklist.
The EOD_POST_CLOSE_LOW_BUDGET_PIT profile is opt-in and report-only. It relaxes timing/cache-support context only; it does not change strict defaults or create approvals.
The EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT profile is opt-in and report-only. It treats no-hit evidence only as reviewer-accepted supporting context; it does not create approvals or checklist-pass rows automatically.
```

```text
The SZSE 1815 same-date quotation probe is the strongest current evidence breakthrough: it produced official date-specific quotation/traded-presence evidence for all 16 first-batch rows.
The v1.18.0 enrichment milestone incorporated quotation evidence and reviewed no-hit support context into a report-only evidence packet enrichment. The v1.19.0 reviewer no-hit source coverage acceptance milestone adds a report-only acceptance layer for source coverage, query windows, and survivorship rationale. All rows remain blocked: quotation presence, no-hit support, and acceptance templates still do not prove not-delisted, ST/no-ST, suspension status, or survivorship-bias resolution by themselves, and no PIT approval has been applied.
```

## Current Recommended Next Branch

```text
Tiny Reviewer-Completed No-Hit Acceptance Update Smoke v0.1
```

This branch should create a tiny diagnostics-only reviewer-completed no-hit acceptance fixture for one row and verify that it becomes `ACCEPTED_AS_SUPPORTING_CONTEXT` only. It must not create checklist-pass rows, PIT approvals, export-ready rows, usable universe inputs, or current-candidates.

```text
one-row reviewer no-hit acceptance fixture
→ acceptance validation
→ supporting-context-only result
→ no PIT approval / no export / no current-candidates
```

It should remain diagnostics-only first. It must not approve rows, reject rows, mutate active worklists, export usable universe files, write `data/raw` or `data/processed`, run `current-candidates`, build snapshots, compute forward returns, mutate cache, send messages, or connect to brokers.

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

- official date-specific evidence acquisition, reviewed no-hit support semantics, reviewer no-hit source coverage acceptance semantics, and accepted-supporting-context validation semantics;
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
- treat policy audit, split guidance, replacement worklist plans, replacement acceptance artifacts, activation artifacts, evidence update plans, evidence packages, checklist validator outputs, policy comparison outputs, official status evidence packets, official status evidence packet enrichment outputs, reviewer no-hit acceptance artifacts, SZSE 1815 quotation diagnostics, exception no-hit diagnostics, or reviewed no-hit profile outputs as usable universe input;
- treat evidence packages as clean `review_updates.csv`;
- treat checklist pass or policy comparison candidate preview as applied approval;
- treat supporting official symbol-level evidence as date-specific daily status proof;
- treat local EOD cache context as official date-specific status proof;
- treat SZSE 1815 same-date quotation presence as not-delisted, no-ST, no-suspension, or survivorship resolution by itself;
- treat no-hit observations, reviewed no-hit support context, or reviewer no-hit acceptance rows as PIT approval, export readiness, or usable universe input;
- treat staging preview files as accepted local universe input;
- treat approved PIT universe rows as exported usable universe files unless a future accepted export workflow says so;
- treat legacy `etf_core` artifacts as ETF-only;
- mutate active worklists without an explicit guarded workflow;
- skip point-in-time checks;
- skip data/snapshot quality;
- approve real message delivery or broker automation;
- commit generated cache/raw/output artifacts.
