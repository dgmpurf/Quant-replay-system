# Quant Replay System Project Source Pack Index

> Status: working memory document  
> Last generated: 2026-06-06  
> Intended use: replace previous Project Source Pack after v1.24.0 Reviewer Material Evidence Fill Guidance checkpoint.  
> Permanence: temporary and replaceable. Refresh only after major checkpoint / stage changes, not after every small audit.

## Purpose

This pack condenses the current `quant-replay-system` direction, engineering state, artifact governance rules, and roadmap for ChatGPT Project Sources.

It is designed to reduce reliance on the long chat transcript and help future ChatGPT/Codex sessions recover the current project state quickly.

## Source Basis

This pack is based on:

- the long ChatGPT/Codex collaboration history;
- repository docs for `dgmpurf/Quant-replay-system`;
- v1.0.0 through v1.22.0 research, PIT evidence, reviewer no-hit, first-batch completion, and partial completion impact checkpoints;
- v1.23.0 Material PIT Evidence Gate Closure Plan checkpoint;
- v1.24.0 Reviewer Material Evidence Fill Guidance checkpoint;
- diagnostics for SZSE 1815 same-date quotation, exception/no-hit probes, official no-hit policy audit, reviewer acceptance smoke tests, downstream impact smoke tests, tiny manual reviewer completion smoke, partial completion impact, and material gate closure / fill guidance audits;
- China A-share event-driven and industry-chain factor taxonomy sources.

## Accuracy Note

This pack does not replace source code, formal repository docs, or actual local artifacts.

Many local outputs under `outputs/`, `data/raw/`, `data/cache`, and `data/processed` are intentionally ignored by Git and may not be available to ChatGPT. When local artifact state matters, the user should paste Codex summaries or run local CLI/status checks.

## Current Project Source Set

Replace these after v1.24.0:

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

The project has reached a Reviewer Material Evidence Fill Guidance checkpoint:

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
→ material-pit-evidence-gate-closure-plan
→ reviewer-material-evidence-fill-guidance
→ index / health / status / research-status context
```

Current reviewer material evidence fill guidance state:

```text
REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_NEEDS_FILL
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
policy_comparison_id: 0ef6d2f3bae6
packet_id: 8efabe2ffe62
reviewed_no_hit_policy_comparison_id: c1a75d1091c6
enrichment_id: cb5f323d3c8c
reviewer_no_hit_acceptance_id: 2e05e4b74794
reviewer_no_hit_downstream_impact_id: 9e164963455e
first_batch_reviewer_evidence_completion_plan_id: c630522f235a
first_batch_partial_completion_impact_id: ea81f81ae764
material_pit_evidence_gate_closure_plan_id: 2d6ab8e7f9f8
reviewer_material_evidence_fill_guidance_id: 94f5ff204662
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
STOCK rows: 56
ETF rows: 16
legacy mixed-demo rows: 72
profile conflicts: 56
stock_core replacement rows: 56
etf_core replacement rows: 16
mixed_demo_core replacement rows: 0
active legacy worklist mutated: false
accepted replacement planning context: true
activation planning context created: true
stock_core first-batch rows: 8
etf_core first-batch rows: 8
checklist_pass_count: 0
remaining_blocked_count: 16
clean_review_updates_created: false
approval_applied: false

Material PIT evidence gate closure plan:
  plan_id: 2d6ab8e7f9f8
  row_count: 16
  checklist_pass_candidate_count: 0
  remaining_blocked_count: 16
  reusable_symbol_level_closure_count: 2
  date_specific_closure_required_count: 16
  reviewer_no_hit_acceptance_required_count: 16
  survivorship_rationale_required_count: 16
  metadata_closure_required_count: 16
  stock_st_no_st_required_count: 8
  clean_review_updates_created: false
  approval_applied: false

Reviewer material evidence fill guidance:
  guidance_id: 94f5ff204662
  row_count: 16
  reviewer_guidance_row_count: 114
  symbol_level_guidance_count: 2
  date_specific_guidance_count: 16
  no_hit_acceptance_guidance_count: 64
  survivorship_rationale_guidance_count: 16
  metadata_guidance_count: 16
  checklist_pass_candidate_count: 0
  remaining_blocked_count: 16
  clean_review_updates_created: false
  approval_applied: false
```

## Key Conclusions

```text
Existing etf_core artifacts are legacy_mixed_demo_universe / POLICY_AMBIGUOUS_DEMO_MIXED_UNIVERSE.
They are not ETF-only artifacts.
They should not be mutated in place.
```

```text
The SZSE 1815 same-date quotation probe is the strongest current evidence breakthrough: it produced official date-specific quotation/traded-presence evidence for all 16 first-batch rows.
It still does not prove not-delisted, no-ST, no-suspension, or survivorship resolution by itself.
```

```text
The reviewer material evidence fill guidance milestone converts material gate closure requirements into human-readable reviewer fill guidance. It is still planning/guidance only.
All rows remain blocked. There are no checklist-pass candidates, no clean review_updates.csv, no PIT approvals, no export-ready rows, no accepted PIT universe inputs, and no current-candidates generated from these artifacts.
```

## Current Recommended Next Branch

```text
Reviewer Fill Fixture Impact Validation v0.1
```

This branch should create a diagnostics-only reviewer fill fixture from the guidance template and run impact validation to prove completed fields reduce only intended blockers without creating clean review updates or approval.

```text
reviewer-material-evidence-fill-guidance
→ diagnostics-only reviewer fill fixture
→ first-batch-partial-completion-impact / material gate closure validation
→ no PIT approval / no export / no current-candidates
```

It should remain diagnostics-only first. It must not approve rows, reject rows, mutate active worklists, export usable universe files, write `data/raw` or `data/processed`, run `current-candidates`, build snapshots, compute forward returns, mutate cache, send messages, or connect to brokers.

## When to Add or Replace Source Documents

Do not update Source after every audit or small implementation.

Add or replace Source when:

- a full milestone/checkpoint/tag is accepted;
- a new artifact workflow lands with index/health/status/research-status;
- current stage or next branch changes;
- artifact governance or safety boundaries change;
- major external data, alert, broker, snapshot, or forward-label semantics are introduced.

## Do Not Use This Pack To

- justify live trading;
- treat worklist rows as reviewed evidence;
- treat policy audit, split guidance, replacement worklist plans, replacement acceptance artifacts, activation artifacts, evidence update plans, evidence packages, checklist validator outputs, policy comparison outputs, official status evidence packets, official status evidence packet enrichment outputs, reviewer no-hit acceptance artifacts, reviewer no-hit downstream impact artifacts, first-batch reviewer evidence completion plans, partial completion impact artifacts, material gate closure plans, reviewer material evidence fill guidance, SZSE 1815 quotation diagnostics, exception no-hit diagnostics, or reviewed no-hit profile outputs as usable universe input;
- treat guidance templates, evidence packages, reviewer completion templates, or partial completion impact artifacts as clean `review_updates.csv`;
- treat checklist pass or policy comparison candidate preview as applied approval;
- treat supporting official symbol-level evidence as date-specific daily status proof;
- treat local EOD cache context as official date-specific status proof;
- treat SZSE 1815 same-date quotation presence as not-delisted, no-ST, no-suspension, or survivorship resolution by itself;
- treat no-hit observations, reviewed no-hit support context, reviewer no-hit acceptance rows, downstream impact rows, reviewer completion planning rows, partial completion impact rows, material gate closure rows, or fill guidance rows as PIT approval, export readiness, or usable universe input;
- mutate active worklists without an explicit guarded workflow;
- skip point-in-time checks;
- skip data/snapshot quality;
- approve real message delivery or broker integration.
