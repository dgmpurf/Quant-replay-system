# One-Row Checklist-Pass Candidate Preview

`one-row-checklist-pass-candidate-preview` creates a report-only preview for the
target row `2024-04-02 / 000001 / stock_core`.

The workflow consumes the one-row material evidence fill package plus the
checklist-pass candidate preview audit artifacts. It copies the strict gap,
context reuse, requirement-plan, PIT timing, no-hit acceptance, survivorship, and
overclaim-risk matrices into a new preview artifact folder.

It does not approve the row and does not create clean `review_updates.csv`.

## Command

```powershell
python -m quant_replay_system.cli one-row-checklist-pass-candidate-preview
```

Artifact views:

```powershell
python -m quant_replay_system.cli one-row-checklist-pass-candidate-preview-index
python -m quant_replay_system.cli one-row-checklist-pass-candidate-preview-health
python -m quant_replay_system.cli one-row-checklist-pass-candidate-preview-status
```

Default inputs:

- `outputs/reports/manual_diagnostics/one_row_checklist_pass_candidate_preview_audit_v0_1/`
- `outputs/reports/one_row_material_evidence_fill_package/136cbd739ca1/`
- `outputs/reports/reviewer_material_evidence_fill_guidance/94f5ff204662/`
- `outputs/reports/material_pit_evidence_gate_closure_plan/2d6ab8e7f9f8/`
- `outputs/reports/first_batch_reviewer_evidence_completion_plan/c630522f235a/`
- `outputs/reports/pit_evidence_checklist_validator/62e9eb747197/`
- `outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c/`
- `outputs/reports/reviewer_no_hit_source_coverage_acceptance/2e05e4b74794/`
- `outputs/reports/reviewer_no_hit_acceptance_downstream_impact/9e164963455e/`

Output root:

`outputs/reports/one_row_checklist_pass_candidate_preview/<preview_id>/`

## Outputs

- `one_row_checklist_pass_candidate_preview.csv`
- `strict_requirement_gap_matrix.csv`
- `context_field_reuse_assessment.csv`
- `active_not_delisted_requirement_plan.csv`
- `stock_no_st_requirement_plan.csv`
- `survivorship_resolution_requirement_plan.csv`
- `reviewer_no_hit_acceptance_requirement_plan.csv`
- `pit_timing_requirement_plan.csv`
- `candidate_preview_required_fields.csv`
- `overclaim_risk_matrix.csv`
- `preview_safety_validation.json`
- `source_lineage_summary.csv`
- `report.md`
- `metadata.json`

## Safety

The preview is diagnostics/report-only. It keeps:

- `review_status=NEEDS_MORE_EVIDENCE`
- `include_flag=false`
- `valid_for_signal_date=false`
- `survivorship_bias_resolved=false`
- `row_checklist_pass_candidate=false`
- `approval_applied=false`
- `clean_review_updates_created=false`

The workflow does not run PIT review, export-readiness, staging,
current-candidates, snapshot builds, forward labels, data writes, cache
mutation, broker APIs, order placement, or message delivery.

## Status Integration

`research-status` includes the latest one-row checklist-pass candidate preview
as context when artifacts exist. The summary exposes the latest preview id,
status/stage, health status, target row, preview row count, reusable context
field count, strict requirement gap count, row checklist-pass-candidate flag,
checklist-pass candidate count, remaining blocked count, clean-review-updates
flag, approval-applied flag, report path, and next manual action.

Current blocked/context-only previews are expected review context. They do not
mean PIT approval, clean review update readiness, export-readiness, staging,
current-candidates generation, snapshot build, forward labels, or trading
readiness.
