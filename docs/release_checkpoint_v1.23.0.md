# Release Checkpoint v1.23.0

## Milestone

Material PIT Evidence Gate Closure Plan Artifact Views and Research Status Integration.

Recommended tag: `v1.23.0`

## Completed Capabilities

- `material-pit-evidence-gate-closure-plan-index` discovers local material PIT evidence gate closure plan artifacts.
- `material-pit-evidence-gate-closure-plan-health` verifies required files, required columns, planning-only safety flags, and absence of approval/export/current-candidates behavior.
- `material-pit-evidence-gate-closure-plan-status` summarizes the latest plan and reports whether material PIT evidence gates still need evidence.
- `research-status` includes material PIT evidence gate closure plan fields as reviewer planning context while preserving later paper workflow priority.

## Current Active State

- latest plan id: `2d6ab8e7f9f8`
- status: `WARN`
- stage: `MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_NEEDS_EVIDENCE`
- row_count: 16
- checklist_pass_candidate_count: 0
- remaining_blocked_count: 16
- reusable_symbol_level_closure_count: 2
- date_specific_closure_required_count: 16
- reviewer_no_hit_acceptance_required_count: 16
- survivorship_rationale_required_count: 16
- metadata_closure_required_count: 16
- stock_st_no_st_required_count: 8
- clean_review_updates_created: false
- approval_applied: false

## Workflow Impact

The project now exposes material PIT evidence closure requirements in the unified dashboard. The status is visible and reviewable, but it remains planning context only. It does not imply a row is approved, export-ready, staged, or usable for current-candidates.

If later paper workflow artifacts exist, final `workflow_stage` remains `PAPER_WORKFLOW_READY`; material-gate closure plan fields remain visible for audit and reviewer planning.

## Safety Guarantees

- No PIT approval was applied.
- No rows were rejected.
- No `APPROVED_FOR_PIT_UNIVERSE` rows were created.
- No `include_flag=true` or `valid_for_signal_date=true` was set.
- No clean `review_updates.csv` was created.
- No universe export occurred.
- No `data/raw` or `data/processed` write occurred.
- No current-candidates generation occurred.
- No snapshot manifest was built.
- No forward labels were computed.
- No cache mutation occurred.
- No live trading, broker API, automated orders, or real message delivery was added.
- No API/LLM/network workflow is required for this milestone.

## Known Limitations

- All 16 first-batch rows remain blocked under the material evidence gates.
- Reusable symbol-level closure paths reduce planning duplication only; they do not close any row by themselves.
- Date-specific PIT evidence, reviewer no-hit acceptance, survivorship rationale, required PIT metadata, and stock ST/no-ST evidence still require reviewer completion.
- The workflow does not create clean review updates and does not run PIT review.
- Strategy performance is not validated by this milestone.

## Recommended Next Engineering Tasks

1. Build a report-only reviewer fill guidance workflow from the material closure plan.
2. Keep closure-path packages profile-specific for `stock_core` and `etf_core`.
3. Validate any reviewer-completed fixture through diagnostics before creating clean review updates.
4. Continue blocking PIT approval until strict evidence gates are complete.
