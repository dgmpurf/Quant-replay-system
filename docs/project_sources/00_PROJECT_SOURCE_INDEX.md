# Quant Replay System Project Source Pack Index

> Status: working memory document  
> Last generated: 2026-06-05  
> Intended use: replace previous Project Source Pack after v1.22.0 First-Batch Partial Completion Impact checkpoint.  
> Permanence: temporary and replaceable. Refresh only after major checkpoint / stage changes, not after every small audit.

## Purpose

This pack condenses the current `quant-replay-system` direction, engineering state, artifact governance rules, and roadmap for ChatGPT Project Sources.

It is designed to reduce reliance on the long chat transcript and help future ChatGPT/Codex sessions recover the current project state quickly.

## Source Basis

This pack is based on:

- the long ChatGPT/Codex collaboration history;
- repository docs for `dgmpurf/Quant-replay-system`;
- v1.0.0 through v1.21.0 research, PIT evidence, reviewer no-hit acceptance, downstream impact, and first-batch reviewer evidence completion planning checkpoints;
- v1.22.0 First-Batch Partial Completion Impact checkpoint;
- diagnostics for SZSE 1815 same-date quotation, exception/no-hit probes, official no-hit policy audit, reviewer acceptance smoke tests, downstream impact smoke tests, and tiny manual reviewer completion smoke;
- China A-share event-driven and industry-chain factor taxonomy sources.

## Accuracy Note

This pack does not replace source code, formal repository docs, or actual local artifacts.

Many local outputs under `outputs/`, `data/raw/`, `data/cache`, and `data/processed` are intentionally ignored by Git and may not be available to ChatGPT. When local artifact state matters, the user should paste Codex summaries or run local CLI/status checks.

## Current Project Source Set

Replace these after v1.22.0:

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

The project has reached a First-Batch Partial Completion Impact checkpoint:

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
→ reviewer-no-hit-acceptance-downstream-impact
→ first-batch-reviewer-evidence-completion-plan
→ first-batch-partial-completion-impact
→ index / health / status / research-status context
```

Current first-batch partial completion impact state:

```text
FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_NO_COMPLETION
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
reviewer_no_hit_downstream_impact_id: 9e164963455e
first_batch_reviewer_evidence_completion_plan_id: c630522f235a
first_batch_partial_completion_impact_id: ea81f81ae764
diagnostics_partial_completion_impact_id: 93a8341407a1
```

Current evidence / validator / planning counts:

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

Reviewer no-hit acceptance downstream impact:
  impact_id: 9e164963455e
  accepted_no_hit_context_count: 0
  packet_context_gap_reduced_count: 0
  checklist_pass_count: 0
  remaining_blocked_count: 16
  approval_applied: false

First-batch reviewer evidence completion plan:
  plan_id: c630522f235a
  row_count: 16
  stock_core_row_count: 8
  etf_core_row_count: 8
  reviewer_completion_required_count: 16
  no_hit_acceptance_required_count: 16
  survivorship_rationale_required_count: 16
  metadata_completion_required_count: 16
  checklist_pass_count: 0
  remaining_blocked_count: 16
  clean_review_updates_created: false
  approval_applied: false

First-batch partial completion impact:
  impact_id: ea81f81ae764
  row_count: 16
  completed_row_count: 0
  completed_field_count: 0
  blocker_reduced_count: 0
  material_blocker_reduced_count: 0
  checklist_pass_count: 0
  remaining_blocked_count: 16
  clean_review_updates_created: false
  approval_applied: false

Diagnostics partial completion fixture:
  impact_id: 93a8341407a1
  completed_row_count: 1
  completed_field_count: 5
  blocker_reduced_count: 1
  material_blocker_reduced_count: 0
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
Codex diagnostics can create NEEDS_MORE_EVIDENCE draft updates and validate ingestion schema, but no row currently passes the strict PIT evidence checklist.
The EOD_POST_CLOSE_LOW_BUDGET_PIT profile is opt-in and report-only. It relaxes timing/cache-support context only; it does not change strict defaults or create approvals.
The EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT profile is opt-in and report-only. It treats no-hit evidence only as reviewer-accepted supporting context; it does not create approvals or checklist-pass rows automatically.
Reviewer no-hit source coverage acceptance, downstream impact, first-batch reviewer evidence completion planning, and partial completion impact workflows are report-only planning/context workflows.
```

```text
The SZSE 1815 same-date quotation probe is the strongest current evidence breakthrough: it produced official date-specific quotation/traded-presence evidence for all 16 first-batch rows.
The v1.18.0 enrichment milestone incorporated quotation evidence and reviewed no-hit support context into a report-only evidence packet enrichment.
The v1.19.0 reviewer no-hit source coverage acceptance milestone added a report-only acceptance layer for source coverage, query windows, and survivorship rationale.
The v1.20.0 downstream impact milestone linked accepted no-hit supporting context back to packet/checklist/policy reporting, while preserving checklist_pass_count=0 and approval_applied=false.
The v1.21.0 first-batch reviewer evidence completion plan converted all prior evidence context into a concrete reviewer fill plan for 16 rows.
The v1.22.0 first-batch partial completion impact workflow reports blocker deltas from partial reviewer completion; the active plan has no completed rows and the diagnostics fixture only reduces metadata/shape blockers, not material PIT evidence blockers.
All rows remain blocked: quotation presence, no-hit support, reviewer acceptance, downstream impact, reviewer completion planning, and partial completion impact still do not prove not-delisted, ST/no-ST, suspension status, survivorship-bias resolution, or full PIT metadata by themselves.
```

## Current Recommended Next Branch

```text
Material PIT Evidence Gate Closure Planning v0.1
```

This branch should identify what exact reviewed evidence is needed to close material PIT gates for at least one first-batch row before any clean review-update candidate preview exists.

Focus blockers:

```text
as_of_date
industry
is_active
is_active_evidence
revision_id
t_plus_rule
000001 is_st / no-ST evidence
survivorship_bias_resolution
reviewer_no_hit_acceptance
```

It should remain read-only / diagnostics-first. It must not approve rows, reject rows, mutate active worklists, export usable universe files, write `data/raw` or `data/processed`, run `current-candidates`, build snapshots, compute forward returns, mutate cache, send messages, or connect to brokers.

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

- material PIT evidence gate closure semantics;
- official date-specific evidence acquisition, reviewed no-hit support semantics, reviewer no-hit source coverage acceptance semantics, accepted-supporting-context validation semantics, downstream impact semantics, first-batch reviewer evidence completion planning semantics, and partial completion impact semantics;
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
- treat policy audit, split guidance, replacement worklist plans, replacement acceptance artifacts, activation artifacts, evidence update plans, evidence packages, checklist validator outputs, policy comparison outputs, official status evidence packets, official status evidence packet enrichment outputs, reviewer no-hit acceptance artifacts, reviewer no-hit downstream impact artifacts, first-batch reviewer evidence completion plans, partial completion impact artifacts, SZSE 1815 quotation diagnostics, exception no-hit diagnostics, or reviewed no-hit profile outputs as usable universe input;
- treat evidence packages, reviewer completion templates, or partial completion impact artifacts as clean `review_updates.csv`;
- treat checklist pass or policy comparison candidate preview as applied approval;
- treat supporting official symbol-level evidence as date-specific daily status proof;
- treat local EOD cache context as official date-specific status proof;
- treat SZSE 1815 same-date quotation presence as not-delisted, no-ST, no-suspension, or survivorship resolution by itself;
- treat no-hit observations, reviewed no-hit support context, reviewer no-hit acceptance rows, downstream impact rows, reviewer completion planning rows, or partial completion impact rows as PIT approval, export readiness, or usable universe input;
- treat staging preview files as accepted local universe input;
- treat approved PIT universe rows as exported usable universe files unless a future accepted export workflow says so;
- treat legacy `etf_core` artifacts as ETF-only;
- mutate active worklists without an explicit guarded workflow;
- skip point-in-time checks;
- skip data/snapshot quality;
- approve real message delivery or broker integration;
- change non-demo thresholds based on synthetic or incomplete evidence.
