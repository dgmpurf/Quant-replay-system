# Reviewer Material Evidence Fill Guidance v0.1

`reviewer-material-evidence-fill-guidance` converts the material PIT evidence gate closure plan into human-readable reviewer guidance packages.

This workflow is report-only. It does not approve rows, reject rows, create clean `review_updates.csv`, run PIT review, run export-readiness, run staging, export universe files, write `data/raw`, write `data/processed`, mutate active worklists, mutate cache, run `current-candidates`, build snapshots, compute forward labels, call paid/private APIs, send messages, connect to brokers, or place orders.

## Command

```bash
python -m quant_replay_system.cli reviewer-material-evidence-fill-guidance
```

Default inputs use the current first-batch material gate closure lineage:

- material PIT evidence gate closure plan `2d6ab8e7f9f8`
- first-batch reviewer evidence completion plan `c630522f235a`
- first-batch partial completion impact `ea81f81ae764`
- checklist validator `62e9eb747197`
- official evidence enrichment `cb5f323d3c8c`
- reviewer no-hit acceptance `2e05e4b74794`
- reviewer no-hit downstream impact `9e164963455e`

## Artifacts

Artifacts are written under:

```text
outputs/reports/reviewer_material_evidence_fill_guidance/<guidance_id>/
```

Expected files:

- `reviewer_material_evidence_fill_guidance.csv`
- `recommended_fill_order.csv`
- `symbol_level_fill_guidance.csv`
- `date_specific_fill_guidance.csv`
- `no_hit_acceptance_fill_guidance.csv`
- `survivorship_rationale_fill_guidance.csv`
- `metadata_fill_guidance.csv`
- `reviewer_risk_controls.csv`
- `reviewer_fill_template_safe_defaults.csv`
- `source_lineage_summary.csv`
- `report.md`
- `metadata.json`

## Fill Groups

The guidance is grouped by:

- `SAFETY_BASELINE`
- `REUSABLE_SYMBOL_LEVEL`
- `DATE_SPECIFIC_PIT_STATUS`
- `REVIEWER_NO_HIT_ACCEPTANCE`
- `SURVIVORSHIP_RATIONALE`
- `PIT_METADATA`
- `DIAGNOSTICS_VALIDATION`

The recommended order starts with diagnostics-only safety, then reusable symbol-level evidence, date-specific PIT status evidence, reviewer no-hit acceptance as supporting context, survivorship rationale, metadata completion, and diagnostics validation.

## Safety Defaults

Reviewer fill templates are intentionally non-approved:

- `review_status=NEEDS_MORE_EVIDENCE`
- `include_flag=false`
- `valid_for_signal_date=false`
- `survivorship_bias_resolved=false`
- `approval_applied=false`

SZSE 1815 quotation context must not be treated as complete not-delisted, no-ST, or no-suspension proof by itself. No-hit context remains supporting context only unless a later explicit reviewer acceptance and validation workflow uses it.

## Current Expected Result

The active first-batch state remains blocked:

- `row_count=16`
- `symbol_level_guidance_count=2`
- `date_specific_guidance_count=16`
- `no_hit_acceptance_guidance_count=64`
- `survivorship_rationale_guidance_count=16`
- `metadata_guidance_count=16`
- `checklist_pass_candidate_count=0`
- `remaining_blocked_count=16`
- `clean_review_updates_created=false`
- `approval_applied=false`

## Artifact Views

Use these report-only views to discover, safety-check, and summarize guidance artifacts:

```bash
python -m quant_replay_system.cli reviewer-material-evidence-fill-guidance-index
python -m quant_replay_system.cli reviewer-material-evidence-fill-guidance-health
python -m quant_replay_system.cli reviewer-material-evidence-fill-guidance-status
```

Expected current status:

- `status=WARN`
- `workflow_stage=REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_NEEDS_FILL`
- `row_count=16`
- `reviewer_guidance_row_count=114`
- `checklist_pass_candidate_count=0`
- `remaining_blocked_count=16`
- `clean_review_updates_created=false`
- `approval_applied=false`

Health fails if a guidance artifact becomes approval-like, including `APPROVED_FOR_PIT_UNIVERSE`, `include_flag=true`, `valid_for_signal_date=true`, clean `review_updates.csv`, `approval_applied=true`, data writes, PIT review/export/staging/current-candidates outputs, snapshots, forward labels, or missing safety flags.

## Research Status

`research-status` includes the latest reviewer material evidence fill guidance as reviewer planning context:

- latest guidance id
- status, stage, and health
- guidance row counts by fill group
- checklist-pass candidate count
- remaining blocked count
- clean review updates / approval flags
- report path and next action

`REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_NEEDS_FILL` is visible as manual PIT evidence preparation work. It is not a strategy failure, candidate-generation failure, PIT approval, export-readiness, staging, snapshot build, current-candidates generation, or trading signal. Later paper workflow priority is preserved.
